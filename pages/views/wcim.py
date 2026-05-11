"""
pages/views/wcim.py

Views for the "What Can I Make?" feature.

Phase 1b (current):
    - pantry_staples_management: manage the user's persistent pantry staples list

Phase 1c will add the matching engine.
Phase 1d will add the new WCIM landing + results pages.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from pages.models import Ingredient, PantryStaple
from pages.services.wcim import DEFAULT_PANTRY_STAPLE_IDS


def _seed_default_staples(user):
    """Create a PantryStaple row for each ID in DEFAULT_PANTRY_STAPLE_IDS.

    Skips IDs that don't resolve to a live Ingredient (defensive against
    deleted ingredients). Returns the number of staples created.
    """
    ingredients = Ingredient.objects.filter(
        ingredient_id__in=DEFAULT_PANTRY_STAPLE_IDS
    )
    staples_to_create = [
        PantryStaple(user=user, ingredient=ing) for ing in ingredients
    ]
    created = PantryStaple.objects.bulk_create(
        staples_to_create, ignore_conflicts=True,
    )
    return len(created)


@login_required
@require_http_methods(["GET", "POST"])
def pantry_staples_management(request):
    """Manage the user's persistent pantry staples list.

    GET: render the page with current staples + a picker for adding more.
         Auto-seeds defaults on first visit (when the user has no staples).
    POST: handle one of three actions via form field 'action':
        - add    + ingredient_id  -> add a single ingredient as a staple
        - remove + staple_id      -> remove a single staple
        - reset                   -> delete all + reseed from defaults
    """
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            try:
                ing_id = int(request.POST.get("ingredient_id", ""))
                ingredient = Ingredient.objects.get(ingredient_id=ing_id)
                _, created = PantryStaple.objects.get_or_create(
                    user=request.user, ingredient=ingredient,
                )
                if created:
                    messages.success(request, f"Added '{ingredient.name}' to your staples.")
                else:
                    messages.info(request, f"'{ingredient.name}' is already in your staples.")
            except (ValueError, TypeError, Ingredient.DoesNotExist):
                messages.error(request, "Couldn't add that ingredient.")

        elif action == "remove":
            try:
                staple_id = int(request.POST.get("staple_id", ""))
                staple = PantryStaple.objects.get(
                    pk=staple_id, user=request.user,
                )
                name = staple.ingredient.name
                staple.delete()
                messages.success(request, f"Removed '{name}' from your staples.")
            except (ValueError, TypeError, PantryStaple.DoesNotExist):
                messages.error(request, "Couldn't remove that staple.")

        elif action == "reset":
            PantryStaple.objects.filter(user=request.user).delete()
            count = _seed_default_staples(request.user)
            messages.success(request, f"Reset to the default {count} staples.")

        return redirect("pantry_staples_management")

    # === GET ===

    # Auto-seed defaults on first visit
    if not PantryStaple.objects.filter(user=request.user).exists():
        count = _seed_default_staples(request.user)
        if count:
            messages.info(
                request,
                f"Seeded your pantry with {count} default staples. "
                "Add or remove items below to make it your own.",
            )

    # Order by category then name — drives the {% regroup %} in the template
    staples = (PantryStaple.objects
               .filter(user=request.user)
               .select_related("ingredient", "ingredient__category")
               .order_by("ingredient__category__name", "ingredient__name"))

    staple_ids = list(staples.values_list("ingredient_id", flat=True))
    available_ingredients = (Ingredient.objects
                             .exclude(ingredient_id__in=staple_ids)
                             .select_related("category")
                             .order_by("category__name", "name"))

    context = {
        "staples": staples,
        "available_ingredients": available_ingredients,
        "staples_count": staples.count(),
    }
    return render(request, "pantry_staples.html", context)

def wcim_landing(request):
    """The "What Can I Make?" anchor picker.

    GET: render the page with selectable anchor buttons.
    POST: save selected anchors to session, redirect to extras picker
          (or directly to results if user picked Skip).
    """
    from pages.services.wcim import ANCHOR_DEFINITIONS

    ANCHOR_ICONS = {
        "chicken":    "fa-drumstick-bite",
        "pork":       "fa-bacon",
        "beef":       "fa-cow",
        "lamb":       "fa-drumstick-bite",
        "fish":       "fa-fish",
        "seafood":    "fa-shrimp",
        "vegetarian": "fa-leaf",
        "dessert":    "fa-cookie-bite",
        "anything":   "fa-utensils",
    }

    if request.method == "POST":
        selected = request.POST.getlist("anchors")
        if not selected:
            selected = ["anything"]
        request.session["wcim_anchors"] = selected
        request.session["wcim_extras"] = []  # reset on new search

        action = request.POST.get("action", "continue")
        if action == "skip":
            return redirect("wcim_results")
        return redirect("wcim_extras")

    selected_anchors = request.session.get("wcim_anchors", [])
    anchors = [
        {**a, "icon": ANCHOR_ICONS.get(a["slug"], "fa-circle")}
        for a in ANCHOR_DEFINITIONS
    ]

    context = {
        "anchors": anchors,
        "selected_anchors": selected_anchors,
    }
    return render(request, "wcim_landing.html", context)

def wcim_extras(request):
    """The "what else do you have?" picker, shown after anchor selection.

    GET: read anchors from session, fetch the suggested extras shortlist,
         render the page.
    POST: save selected extras to session, redirect to results.
    """
    from pages.services.wcim import suggest_extras_for_anchors, ANCHOR_DEFINITIONS

    anchors = request.session.get("wcim_anchors", [])
    if not anchors:
        # User hit this page without going through landing first
        return redirect("wcim_landing")

    if request.method == "POST":
        try:
            selected_int_ids = [int(x) for x in request.POST.getlist("extras")]
        except (ValueError, TypeError):
            selected_int_ids = []
        request.session["wcim_extras"] = selected_int_ids
        return redirect("wcim_results")

    # GET
    extras = suggest_extras_for_anchors(request.user, anchors, top_n=20)
    selected_extras = request.session.get("wcim_extras", [])
    anchor_labels = [
        a["label"] for a in ANCHOR_DEFINITIONS if a["slug"] in anchors
    ]

    context = {
        "anchors": anchors,
        "anchor_labels": anchor_labels,
        "extras": extras,
        "selected_extras": selected_extras,
    }
    return render(request, "wcim_extras.html", context)


def wcim_results(request):
    """Tiered, ranked recipe matches based on the user's anchors + extras.

    Reads anchors and extras from session, runs the matching engine, groups
    results by tier, and renders the page.
    """
    from pages.services.wcim import run_match, ANCHOR_DEFINITIONS
    from pages.models import Ingredient

    anchors = request.session.get("wcim_anchors", [])
    extras = request.session.get("wcim_extras", [])

    if not anchors:
        return redirect("wcim_landing")

    result = run_match(
        request.user,
        anchor_slugs=anchors,
        extra_ingredient_ids=extras,
    )
    matched = result["matched_recipes"]

    # Pre-compute display values + truncate the missing-list so cards stay tidy
    MISSING_VISIBLE = 4
    for r in matched:
        r["score_pct"] = int(round(r["score"] * 100))
        r["missing_short"] = r["missing"][:MISSING_VISIBLE]
        r["missing_more"] = max(0, len(r["missing"]) - MISSING_VISIBLE)

    # Group by tier (preserves the score-desc order from run_match)
    tier_groups = {"make_now": [], "almost_there": [], "worth_shopping": []}
    for r in matched:
        if r["tier"] in tier_groups:
            tier_groups[r["tier"]].append(r)

    # Display labels for the header
    anchor_labels = [
        a["label"] for a in ANCHOR_DEFINITIONS if a["slug"] in anchors
    ]
    extra_names = list(
        Ingredient.objects.filter(ingredient_id__in=extras)
        .values_list("name", flat=True)
    )

    context = {
        "anchor_labels": anchor_labels,
        "extra_names": extra_names,
        "total_filtered": result["total_filtered"],
        "total_matched": len(matched),
        "tier_groups": tier_groups,
    }
    return render(request, "wcim_results.html", context)
