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

    staples = (PantryStaple.objects
               .filter(user=request.user)
               .select_related("ingredient")
               .order_by("ingredient__name"))

    staple_ids = list(staples.values_list("ingredient_id", flat=True))
    available_ingredients = (Ingredient.objects
                             .exclude(ingredient_id__in=staple_ids)
                             .order_by("name"))

    context = {
        "staples": staples,
        "available_ingredients": available_ingredients,
        "staples_count": staples.count(),
    }
    return render(request, "pantry_staples.html", context)