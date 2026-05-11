"""
pages/services/wcim.py
======================

The "What Can I Make?" service module.

Phase 1a + 1c (current):
    - recompute_recipe_stats()       → IDF + weighted_total computation
    - ANCHOR_DEFINITIONS             → list of anchor configs
    - DEFAULT_PANTRY_STAPLE_IDS      → seed list for new users
    - filter_by_anchors()            → hard anchor filter on a Recipe queryset
    - tier_for()                     → score → tier label
    - score_recipe()                 → single-recipe match score
    - run_match()                    → full match pipeline
    - suggest_extras_for_anchors()   → smart secondary-picker shortlist
"""
from __future__ import annotations

import logging
import math
import time

from django.db import transaction
from django.db.models import Count, Q, Sum

logger = logging.getLogger(__name__)


# =============================================================================
# Anchor definitions — used by the UI (Phase 1d) and matching engine
# =============================================================================
# Each anchor has:
#   slug:    short identifier used in URLs and templates
#   label:   user-facing display text
#   filter:  a Django Q object applied to the Recipe queryset, or None for
#            "no filter" (the Anything anchor)
#
# Mapping derived from live data (Pork is #1 by recipe count, hence its
# placement). Edit this list to add or remove anchors as recipe metadata
# evolves.

ANCHOR_DEFINITIONS = [
    {"slug": "chicken",    "label": "Chicken",    "filter": Q(proteins__name="Chicken")},
    {"slug": "pork",       "label": "Pork",       "filter": Q(proteins__name="Pork")},
    {"slug": "beef",       "label": "Beef",       "filter": Q(proteins__name="Beef")},
    {"slug": "lamb",       "label": "Lamb",       "filter": Q(proteins__name="Lamb")},
    {"slug": "fish",       "label": "Fish",       "filter": Q(proteins__name="Fish")},
    {"slug": "seafood",    "label": "Seafood",    "filter": Q(proteins__name__in=["Seafood", "Prawn", "Calamari"])},
    {"slug": "vegetarian", "label": "Vegetarian", "filter": Q(is_vegetarian=True)},
    {"slug": "dessert",    "label": "Dessert",    "filter": Q(courses__name="Dessert")},
    {"slug": "anything",   "label": "Anything",   "filter": None},
]


# =============================================================================
# Default pantry staple seed — locked from §11 of the spec
# =============================================================================
DEFAULT_PANTRY_STAPLE_IDS = [
    # Oils, vinegars, fats
    21,   # Olive Oil
    200,  # Coconut Oil
    122,  # Vinegar, Balsamic
    90,   # Vinegar, White Wine
    30,   # Butter
    178,  # Butter, Unsalted

    # Salts & peppers
    22,   # Salt
    26,   # Pepper, Ground Black
    117,  # Pepper, Cayenne
    112,  # Garlic Salt

    # Aromatics
    32,   # Garlic
    14,   # Water
    312,  # Ice

    # Dried herbs & spices
    102,  # Origanum
    135,  # Thyme, Dried
    266,  # Parsley, Dried
    190,  # Bay Leaf
    46,   # Nutmeg
    36,   # Cinnamon (ground)
    215,  # Cloves, Ground
    157,  # Chilli Flakes, Crushed
    29,   # Paprika
    65,   # Paprika, Smoked
    64,   # Cumin, Ground
    186,  # Ginger Powder
    148,  # Coriander, Ground
    164,  # Garam Masala
    125,  # Turmeric

    # Seasoning blends
    188,  # Curry Powder, Hot
    123,  # Curry Powder, Medium
    303,  # Cajun Seasoning
    306,  # Barbeque Spice

    # Sauces & condiments
    33,   # Mustard, Dijon
    91,   # Worcestershire Sauce
    151,  # Soy Sauce, Light
    88,   # Ketchup
    229,  # Mayonnaise
    208,  # Olives
    264,  # Nando's Lemon & Herb Sauce
    297,  # Nando's Peri-peri Sauce, Extra Hot
    159,  # Nando's Peri-peri Sauce, Hot

    # Stock cubes
    34,   # Stock Cube, Beef
    66,   # Stock Cube, Chicken
    262,  # Stock Cube, Vegetable

    # Baking & sugars
    19,   # Flour, All Purpose
    9,    # Sugar
    2,    # Caster Sugar
    92,   # Sugar, Brown
    131,  # Sugar, Icing
    133,  # Cocoa Powder
    10,   # Corn Flour
    183,  # Golden Syrup
    89,   # Honey
    6,    # Baking Powder
    51,   # Bicarbonate Of Soda
    58,   # Vanilla Extract
    4,    # Vanilla Essence

    # Dairy
    8,    # Milk
    172,  # Egg  (was 1 Eggs — merged 2026-05)

    # Pantry / grains
    119,  # Rice, White

    # Alcohol
    309,  # Sherry
    238,  # Rum
    3,    # Brandy
    272,  # Marsala
    331,  # Ouzo
    270,  # Beer

    # Other
    353,  # Espresso Coffee
    250,  # Briquettes, Charcoal
]


# =============================================================================
# IDF and weighted-total recomputation (Phase 1a)
# =============================================================================
@transaction.atomic
def recompute_recipe_stats() -> dict:
    """
    Recompute document_frequency and idf for every Ingredient, and
    weighted_total for every Recipe.

    Called by:
      - the rebuild_recipe_stats management command (one-off / cron)
      - the post_save/post_delete signal on RecipeIngredient (auto)
    """
    from pages.models import Recipe, Ingredient, RecipeIngredient

    started = time.monotonic()
    N = Recipe.objects.count()

    if N == 0:
        logger.info("recompute_recipe_stats: no recipes, skipping")
        return {"recipes": 0, "ingredients_updated": 0, "elapsed_ms": 0}

    # Step 1: document frequencies
    df_rows = (
        RecipeIngredient.objects
        .values("ingredient_id")
        .annotate(df=Count("recipe_id", distinct=True))
    )
    df_by_ingredient = {row["ingredient_id"]: row["df"] for row in df_rows}

    # Step 2: bulk-update Ingredient with df + idf
    ingredients = list(Ingredient.objects.all().only("ingredient_id"))
    for ing in ingredients:
        df = df_by_ingredient.get(ing.ingredient_id, 0)
        ing.document_frequency = df
        ing.idf = math.log(N / df) if df > 0 else 0.0
    Ingredient.objects.bulk_update(ingredients, ["document_frequency", "idf"], batch_size=200)

    # Step 3: weighted_total per recipe
    recipes = list(Recipe.objects.all().only("recipe_id"))
    for recipe in recipes:
        total = (
            RecipeIngredient.objects
            .filter(recipe_id=recipe.recipe_id)
            .aggregate(total=Sum("ingredient__idf"))["total"]
            or 0.0
        )
        recipe.weighted_total = total
    Recipe.objects.bulk_update(recipes, ["weighted_total"], batch_size=200)

    elapsed_ms = int((time.monotonic() - started) * 1000)
    stats = {
        "recipes": N,
        "ingredients_updated": len(ingredients),
        "recipes_updated": len(recipes),
        "elapsed_ms": elapsed_ms,
    }
    logger.info("recompute_recipe_stats: %s", stats)
    return stats


# =============================================================================
# Matching engine (Phase 1c)
# =============================================================================
def filter_by_anchors(queryset, anchor_slugs):
    """Apply anchor filters to a Recipe queryset.

    Multiple anchors combine with OR (union): selecting Chicken + Pork
    returns recipes tagged with either. The 'anything' anchor (or an empty
    list) returns the queryset unchanged.

    Special case: if any savoury anchor is selected without 'dessert' in the
    mix, desserts are excluded — desserts are almost all vegetarian and
    would otherwise drown the Vegetarian anchor's savoury results.
    """
    if not anchor_slugs or "anything" in anchor_slugs:
        return queryset

    combined = Q()
    matched_any = False
    for slug in anchor_slugs:
        anchor = next((a for a in ANCHOR_DEFINITIONS if a["slug"] == slug), None)
        if anchor and anchor["filter"] is not None:
            combined |= anchor["filter"]
            matched_any = True

    if not matched_any:
        return queryset

    qs = queryset.filter(combined).distinct()

    # If the user picked savoury anchors but didn't include Dessert, strip
    # desserts so the savoury intent comes through cleanly (especially for
    # Vegetarian, where ~109 of 199 vegetarian recipes are desserts).
    if "dessert" not in anchor_slugs:
        qs = qs.exclude(courses__name="Dessert")

    return qs

def tier_for(score: float) -> str:
    """Classify a recipe match score into a tier label.

    Thresholds default to make_now=0.999 / almost_there=0.70 / worth_shopping=0.40.
    Tune via settings.WCIM_TIER_THRESHOLDS once you've seen real results.
    """
    from django.conf import settings
    thresholds = getattr(settings, "WCIM_TIER_THRESHOLDS", {
        "make_now": 0.999,
        "almost_there": 0.70,
        "worth_shopping": 0.40,
    })

    if score >= thresholds["make_now"]:
        return "make_now"
    if score >= thresholds["almost_there"]:
        return "almost_there"
    if score >= thresholds["worth_shopping"]:
        return "worth_shopping"
    return "below_threshold"


def score_recipe(recipe, available_idfs: dict,
                 available_family_ids: set = None,
                 available_by_family: dict = None) -> dict:
    """Score a single recipe against a dict of available ingredients.

    Args:
        recipe: a Recipe instance, ideally with prefetched recipe_ingredients.
        available_idfs: dict mapping ingredient_id -> idf for every ingredient
                        the user has on hand (pantry staples + extras).
        available_family_ids: set of family_ids the user has any ingredient in.
                              If None, no family matching happens.
        available_by_family: dict mapping family_id -> list of ingredient names
                             the user has in that family. Used to populate the
                             "via" hint on substitute matches.

    Returns:
        {
            "score":           float 0..1   weighted match coverage
            "have_exact":      [str, ...]   names of recipe ingredients the user has exactly
            "have_substitute": [dict, ...]  {name, via} for recipe ingredients matched via family
            "missing":         [str, ...]   names of recipe ingredients the user lacks entirely
            "tier":            str          make_now / almost_there / worth_shopping / below_threshold
        }
    """
    from django.conf import settings
    family_weight = getattr(settings, "WCIM_FAMILY_MATCH_WEIGHT", 0.7)
    available_family_ids = available_family_ids or set()
    available_by_family = available_by_family or {}

    recipe_ings = recipe.recipe_ingredients.all()

    total_available_idf = 0.0
    have_exact = []
    have_substitute = []
    missing = []

    for ri in recipe_ings:
        ing_idf = ri.ingredient.idf or 0.0

        if ri.ingredient_id in available_idfs:
            # Exact match — full credit
            total_available_idf += ing_idf
            have_exact.append(ri.ingredient.name)

        elif ri.ingredient.family_id and ri.ingredient.family_id in available_family_ids:
            # Family substitute — partial credit (default 70%)
            total_available_idf += ing_idf * family_weight
            substitutes = available_by_family.get(ri.ingredient.family_id, [])
            have_substitute.append({
                "name": ri.ingredient.name,
                "via": substitutes[0] if substitutes else "",
            })

        else:
            missing.append(ri.ingredient.name)

    score = (total_available_idf / recipe.weighted_total
             if recipe.weighted_total > 0 else 0.0)

    return {
        "score": score,
        "have_exact": have_exact,
        "have_substitute": have_substitute,
        "missing": missing,
        "tier": tier_for(score),
    }


def run_match(user, anchor_slugs=None, extra_ingredient_ids=None) -> dict:
    """Run the full WCIM matching pipeline.

    Args:
        user: the requesting User
        anchor_slugs: list of selected anchor slugs (e.g. ['chicken', 'pork'])
        extra_ingredient_ids: list of ingredient_ids the user has on hand
                              beyond their pantry staples

    Returns:
        {
            "matched_recipes": list of dicts (recipe + score + have_exact +
                              have_substitute + missing + tier),
                              sorted by score desc, tier != below_threshold
            "anchor_slugs":   list, echoed back
            "total_filtered": int — recipes that survived the anchor filter
                                    before scoring
        }
    """
    from pages.models import Recipe, PantryStaple, Ingredient

    anchor_slugs = anchor_slugs or []
    extra_ingredient_ids = extra_ingredient_ids or []

    # Step 1: build the "available" set — staples + extras
    staple_ids = set(
        PantryStaple.objects.filter(user=user).values_list("ingredient_id", flat=True)
    )
    available_ids = staple_ids | set(extra_ingredient_ids)

    # Step 2: fetch IDFs + family memberships for each available ingredient
    available_rows = list(
        Ingredient.objects
        .filter(ingredient_id__in=available_ids)
        .values("ingredient_id", "name", "idf", "family_id")
    )
    available_idfs = {row["ingredient_id"]: row["idf"] for row in available_rows}
    available_family_ids = {
        row["family_id"] for row in available_rows if row["family_id"]
    }
    # family_id -> list of ingredient names the user has in that family
    available_by_family = {}
    for row in available_rows:
        if row["family_id"]:
            available_by_family.setdefault(row["family_id"], []).append(row["name"])

    # Step 3: hard-filter recipes by anchors, then prefetch for scoring
    qs = filter_by_anchors(Recipe.objects.all(), anchor_slugs)
    qs = qs.prefetch_related("recipe_ingredients__ingredient")

    total_filtered = qs.count()

    # Step 4: score each surviving recipe
    matched = []
    for recipe in qs:
        result = score_recipe(
            recipe,
            available_idfs,
            available_family_ids=available_family_ids,
            available_by_family=available_by_family,
        )
        if result["tier"] != "below_threshold":
            matched.append({"recipe": recipe, **result})

    # Step 5: sort by score descending
    matched.sort(key=lambda r: -r["score"])

    return {
        "matched_recipes": matched,
        "anchor_slugs": anchor_slugs,
        "total_filtered": total_filtered,
    }


def suggest_extras_for_anchors(user, anchor_slugs, top_n: int = 20) -> list:
    """Suggest the most useful non-staple ingredients to tick after anchor selection.

    Looks at recipes matching the anchor filter, counts how often each
    non-staple ingredient appears, and returns the top N most common.
    These become the "what else do you have?" shortlist on the picker page.
    """
    from pages.models import Recipe, PantryStaple, RecipeIngredient

    qs = filter_by_anchors(Recipe.objects.all(), anchor_slugs)
    recipe_ids = list(qs.values_list("recipe_id", flat=True))

    if not recipe_ids:
        return []

    staple_ids = set(
        PantryStaple.objects.filter(user=user).values_list("ingredient_id", flat=True)
    )

    counts = (
        RecipeIngredient.objects
        .filter(recipe_id__in=recipe_ids)
        .exclude(ingredient_id__in=staple_ids)
        .values("ingredient_id", "ingredient__name")
        .annotate(usage_count=Count("recipe_id", distinct=True))
        .order_by("-usage_count")[:top_n]
    )

    return list(counts)