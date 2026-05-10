"""
pages/services/wcim.py
======================

The "What Can I Make?" service module.

Phase 1a (this file's current scope):
    - recompute_recipe_stats()      → IDF + weighted_total computation
    - ANCHOR_DEFINITIONS            → list of anchor configs (used by Phase 1c/1d)
    - DEFAULT_PANTRY_STAPLE_IDS     → seed list (used by Phase 1b)

Phase 1c will add:
    - score_recipe()
    - run_match()
    - tier_for()
    - filter_by_anchors()
"""
from __future__ import annotations

import logging
import math
import time

from django.db import transaction
from django.db.models import Q, Sum

logger = logging.getLogger(__name__)


# =============================================================================
# Anchor definitions — used by the UI (Phase 1d) and matching engine (Phase 1c)
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
# These are the Ingredient PKs (resolved from live data) that are seeded into
# a new user's PantryStaple list on first visit to the staples management
# page. The user can edit, remove, or add to this set freely; the seed only
# applies at first visit.
#
# Pulled from the user's stated daily-staples list, matched 1:1 against the
# 375-ingredient live database. Comments show the canonical name for clarity.

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
    154,  # Nando's Lemon And Herb Sauce  (duplicate of 264 — see backlog)
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
    1,    # Eggs

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
# IDF and weighted-total recomputation
# =============================================================================
@transaction.atomic
def recompute_recipe_stats() -> dict:
    """
    Recompute document_frequency and idf for every Ingredient, and
    weighted_total for every Recipe.

    Called by:
      - the rebuild_recipe_stats management command (one-off / cron)
      - the post_save/post_delete signal on RecipeIngredient (auto)

    Returns a small stats dict for logging / management-command output.

    Algorithm:
      N           = total recipes
      df(i)       = number of recipes containing ingredient i
      idf(i)      = log(N / df(i))   (0 if df=0)
      weighted_total(r) = sum of idf(i) for every ingredient i in recipe r
    """
    # Imported here to avoid circular imports at module load time
    from pages.models import Recipe, Ingredient, RecipeIngredient

    started = time.monotonic()
    N = Recipe.objects.count()

    if N == 0:
        logger.info("recompute_recipe_stats: no recipes, skipping")
        return {"recipes": 0, "ingredients_updated": 0, "elapsed_ms": 0}

    # ----- Step 1: document frequencies -----
    # Distinct count of recipes per ingredient. The distinct=True is critical
    # since some recipes can list the same ingredient twice (e.g. olive oil
    # for cooking + drizzling).
    from django.db.models import Count

    df_rows = (
        RecipeIngredient.objects
        .values("ingredient_id")
        .annotate(df=Count("recipe_id", distinct=True))
    )
    df_by_ingredient = {row["ingredient_id"]: row["df"] for row in df_rows}

    # ----- Step 2: bulk-update Ingredient with df + idf -----
    ingredients = list(Ingredient.objects.all().only("ingredient_id"))
    for ing in ingredients:
        df = df_by_ingredient.get(ing.ingredient_id, 0)
        ing.document_frequency = df
        ing.idf = math.log(N / df) if df > 0 else 0.0
    Ingredient.objects.bulk_update(ingredients, ["document_frequency", "idf"], batch_size=200)

    # ----- Step 3: weighted_total per recipe -----
    # After step 2, IDFs are fresh. Sum them per recipe via a join through
    # RecipeIngredient → Ingredient.idf. Single aggregate query per recipe
    # is fine for a few hundred recipes.
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