"""
Nutrition: ingredient->USDA mapping wizard and recipe nutrition data.

Two related concerns live here:

Ingredient mapping (4 views):
    map_ingredients_wizard       - the wizard page (GET). Shows the queue
                                   of unmapped ingredients with optional
                                   recipe-scoped filtering.
    usda_search                  - AJAX: search the USDA FoodData Central
                                   for matches.
    usda_select_and_preview      - AJAX: fetch full nutrient detail for a
                                   chosen USDA fdc_id.
    save_ingredient_mapping      - AJAX: persist a mapping (USDA or
                                   manual), including optional unit
                                   conversion to grams. Also handles the
                                   clear/remove branch.

Recipe nutrition (3 views/helpers):
    recipe_nutrition_data            - AJAX: compute and return the
                                       nutrition breakdown for a recipe.
    recipe_has_any_mapped_ingredient - predicate used by view_recipe to
                                       decide whether to show the
                                       Nutrition button.
    recipe_unconvertible_ingredients - AJAX: list of (ingredient, unit)
                                       pairs that have nutrition but lack
                                       a conversion to grams. Drives the
                                       "Set unit conversions" mini-modal.

External dependencies (live in pages/, not in views/):
    pages.usda_client.{search_foods, get_food_details, USDAClientError}
    pages.nutrition_calc.calculate_recipe_nutrition

Extracted from pages/views/main.py as part of the modular views
migration (### RECIPE MANAGEMENT ### -> recipes/ sub-package, phase 3).
Two legacy "paste at the bottom of views.py" comment blocks were
replaced with proper section headers since the flat views.py they
referenced no longer exists.
"""

import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from ...models import (
    Ingredient,
    MeasurementUnit,
    Recipe,
    RecipeIngredient,
    UnitConversion,
)
from ...nutrition_calc import calculate_recipe_nutrition
from ...usda_client import USDAClientError, get_food_details, search_foods


# --------------------------------------------------------------------------- #
# 1. Wizard page (GET)
# --------------------------------------------------------------------------- #

@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
def map_ingredients_wizard(request):
    """
    Render the bulk mapping wizard page.

    The page always shows the unmapped queue — there are no tabs. The
    ingredient page now handles individual edits via clickable badges,
    so this view is purely a "queue processor" for getting through the
    unmapped backlog.

    Query params:
        recipe_id = optional; if provided, filters the queue to ingredients
                    used in this specific recipe
        return_to = optional; 'recipe' means the Back button returns to the
                    view_recipe page (and auto-reopens the Nutrition modal)
    """
    recipe_id = request.GET.get('recipe_id')
    return_to = request.GET.get('return_to', 'ingredients')

    # Base queryset: only unmapped ingredients
    qs = (
        Ingredient.objects
        .filter(fdc_id__isnull=True)
        .select_related('default_unit', 'category')
        .order_by('name')
    )

    # Recipe-scoped filtering: limit to ingredients used in a specific recipe
    scoped_recipe = None
    if recipe_id:
        try:
            scoped_recipe = Recipe.objects.get(recipe_id=int(recipe_id))
            ingredient_ids_in_recipe = RecipeIngredient.objects.filter(
                recipe=scoped_recipe
            ).values_list('ingredient_id', flat=True).distinct()
            qs = qs.filter(ingredient_id__in=ingredient_ids_in_recipe)
        except (Recipe.DoesNotExist, ValueError, TypeError):
            scoped_recipe = None

    ingredients = list(qs)

    # Compute the totals for the progress display.
    # Scope-aware: if filtered to a recipe, count against that recipe's
    # ingredient set; otherwise count against the global database.
    if scoped_recipe:
        recipe_ingredient_ids = list(RecipeIngredient.objects.filter(
            recipe=scoped_recipe
        ).values_list('ingredient_id', flat=True).distinct())

        total_in_set = len(recipe_ingredient_ids)
        total_mapped = Ingredient.objects.filter(
            ingredient_id__in=recipe_ingredient_ids,
            fdc_id__isnull=False,
        ).count()
    else:
        total_in_set = Ingredient.objects.count()
        total_mapped = Ingredient.objects.filter(fdc_id__isnull=False).count()

    total_unmapped = total_in_set - total_mapped

    # Find the gram unit ID for unit conversions (case-insensitive match on
    # the unit name or abbreviation).
    gram_unit_id = None
    gram_candidates = MeasurementUnit.objects.filter(
        unit_type='weight'
    ).values('measurement_unit_id', 'name', 'abbreviation')
    for u in gram_candidates:
        name = (u.get('name') or '').strip().lower()
        abbr = (u.get('abbreviation') or '').strip().lower()
        if name in ('gram', 'grams', 'g') or abbr == 'g':
            gram_unit_id = u['measurement_unit_id']
            break

    # Pre-compute existing ingredient-specific conversions to grams.
    # This lets the wizard skip the conversion panel for ingredients that
    # already have a conversion saved (e.g., from a previous mapping session
    # or from the Manage Unit Conversions page).
    existing_conversions = {}
    if gram_unit_id:
        ingredient_ids = [ing.ingredient_id for ing in ingredients]
        if ingredient_ids:
            conversions_qs = UnitConversion.objects.filter(
                specific_ingredient_id__in=ingredient_ids,
                to_unit_id=gram_unit_id,
            ).values(
                'specific_ingredient_id', 'from_unit_id', 'multiplier'
            )
            for c in conversions_qs:
                ing_id = c['specific_ingredient_id']
                existing_conversions.setdefault(ing_id, {})[c['from_unit_id']] = float(c['multiplier'])

    # Serialise the minimal data the JS needs for each ingredient
    ingredient_data = []
    for ing in ingredients:
        unit_type = ing.default_unit.unit_type if ing.default_unit else 'other'
        default_unit_id = ing.default_unit.measurement_unit_id if ing.default_unit else None

        existing_multiplier = None
        if default_unit_id and gram_unit_id and ing.ingredient_id in existing_conversions:
            existing_multiplier = existing_conversions[ing.ingredient_id].get(default_unit_id)

        ingredient_data.append({
            'ingredient_id': ing.ingredient_id,
            'name': ing.name,
            'category': ing.category.name if ing.category else None,
            'default_unit_id': default_unit_id,
            'default_unit_name': ing.default_unit.name if ing.default_unit else None,
            'default_unit_type': unit_type,  # 'volume' / 'weight' / 'count' / 'other'
            'is_mapped': ing.fdc_id is not None,
            'fdc_id': ing.fdc_id,
            'fdc_description': ing.fdc_description,
            'fdc_data_type': ing.fdc_data_type,
            'existing_conversion_to_g': existing_multiplier,
        })

    context = {
        'ingredient_data_json': json.dumps(ingredient_data),
        'total_count': len(ingredients),       # how many are in the queue right now
        'total_in_set': total_in_set,           # denominator for progress display
        'total_mapped': total_mapped,           # numerator at page load
        'total_unmapped': total_unmapped,       # how many still to go
        'gram_unit_id': gram_unit_id,
        # Recipe-scoped wizard support:
        'scoped_recipe': scoped_recipe,
        'return_to': return_to,
    }
    return render(request, 'map_ingredients_nutrition.html', context)

# --------------------------------------------------------------------------- #
# 2. USDA search (AJAX, GET)
# --------------------------------------------------------------------------- #

@login_required
@require_GET
def usda_search(request):
    """
    AJAX: search USDA FoodData Central for matches.

    GET params:
        query     = search string (required)
        page_size = how many results (default 5, max 10)

    Returns JSON:
        {
            "success": true,
            "query": "flour",
            "results": [
                {
                    "fdc_id": 2003586,
                    "description": "Flour, 00",
                    "data_type": "Foundation",
                    "brand_owner": null,
                    "calories_per_100g": "356.88"
                },
                ...
            ]
        }
    """
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse({
            'success': False,
            'error': 'Query is required.',
        }, status=400)

    try:
        page_size = int(request.GET.get('page_size', 5))
    except (TypeError, ValueError):
        page_size = 5
    page_size = max(1, min(page_size, 10))

    try:
        results = search_foods(query, page_size=page_size)
    except USDAClientError as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=502)

    # Decimal -> string for JSON
    serialised = []
    for r in results:
        serialised.append({
            'fdc_id': r['fdc_id'],
            'description': r['description'],
            'data_type': r['data_type'],
            'brand_owner': r['brand_owner'],
            'calories_per_100g': str(r['calories_per_100g']) if r['calories_per_100g'] is not None else None,
        })

    return JsonResponse({
        'success': True,
        'query': query,
        'results': serialised,
    })


# --------------------------------------------------------------------------- #
# 3. USDA select + preview (AJAX, GET)
# --------------------------------------------------------------------------- #

@login_required
@require_GET
def usda_select_and_preview(request):
    """
    AJAX: fetch full nutrient detail for a USDA fdc_id.

    GET params:
        fdc_id = USDA food ID (required)

    Returns JSON:
        {
            "success": true,
            "fdc_id": 2003586,
            "description": "Flour, 00",
            "data_type": "Foundation",
            "calories_per_100g": "357.08",
            "protein_per_100g":  "11.40",
            "carbs_per_100g":    "74.45",
            "fat_per_100g":      "1.52",
            "fiber_per_100g":    "2.66",
            "sugar_per_100g":    null,
            "sodium_per_100g":   "0.00"
        }

    On 404 (known USDA quirk for some Foundation foods):
        {"success": false, "error": "USDA food X not available..."}
        — JS will tell user to pick a different match.
    """
    try:
        fdc_id = int(request.GET.get('fdc_id'))
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'fdc_id (integer) is required.',
        }, status=400)

    try:
        details = get_food_details(fdc_id)
    except USDAClientError as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=502)

    # Decimal -> string for JSON
    payload = {'success': True}
    for key, value in details.items():
        if isinstance(value, Decimal):
            payload[key] = str(value)
        else:
            payload[key] = value

    return JsonResponse(payload)


# --------------------------------------------------------------------------- #
# 4. Save mapping (AJAX, POST)
# --------------------------------------------------------------------------- #

@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
@require_POST
@csrf_protect
def save_ingredient_mapping(request):
    """
    AJAX: persist a USDA mapping for one ingredient.

    POST body (JSON):
        Standard SAVE:
        {
            "ingredient_id": 42,
            "fdc_id": 2003586,           # 0 = manual, positive int = USDA
            "fdc_description": "Flour, 00",
            "fdc_data_type": "Foundation",
            "calories_per_100g": "357.08",
            ... (other nutrients)
            "unit_conversion": {...}     # optional
        }

        REMOVE / CLEAR mapping:
        {
            "ingredient_id": 42,
            "clear": true,
            "fdc_id": null,
            ... (all nutrient values null)
        }

    Returns:
        {"success": true, "ingredient_id": 42, "is_mapped": true|false}
        {"success": false, "error": "..."}
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON body.',
        }, status=400)

    # --- Required field: ingredient_id ---
    try:
        ingredient_id = int(data.get('ingredient_id'))
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'ingredient_id (integer) is required.',
        }, status=400)

    ingredient = get_object_or_404(Ingredient, ingredient_id=ingredient_id)

    # --- Branch: CLEAR / REMOVE mapping ---
    is_clear = bool(data.get('clear'))
    if is_clear:
        ingredient.fdc_id = None
        ingredient.fdc_description = ''
        ingredient.fdc_data_type = ''
        for field_name in (
            'calories_per_100g', 'protein_per_100g', 'carbs_per_100g',
            'fat_per_100g', 'fiber_per_100g', 'sugar_per_100g', 'sodium_per_100g',
        ):
            setattr(ingredient, field_name, None)
        ingredient.nutrition_source = None
        ingredient.nutrition_synced_at = timezone.now()
        ingredient.save()
        return JsonResponse({
            'success': True,
            'ingredient_id': ingredient.ingredient_id,
            'is_mapped': False,
        })

    # --- Standard SAVE branch: fdc_id is required ---
    try:
        fdc_id = int(data.get('fdc_id'))
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'fdc_id (integer) is required. Use 0 for manual entry.',
        }, status=400)

    # Read nutrition_source from payload, with backward-compat fallback.
    # The frontend now sends 'usda' (from USDA-search saves) or 'manual'
    # (from the manual-entry panel). Older clients won't send it — for
    # those, infer from fdc_id (0 = manual, positive = USDA).
    nutrition_source = data.get('nutrition_source')
    if nutrition_source not in ('usda', 'manual'):
        nutrition_source = 'manual' if fdc_id == 0 else 'usda'

    # --- Update nutrition fields ---
    ingredient.fdc_id = fdc_id
    ingredient.fdc_description = (data.get('fdc_description') or '').strip()[:300]
    ingredient.fdc_data_type = (data.get('fdc_data_type') or '').strip()[:30]
    ingredient.nutrition_source = nutrition_source

    # Sanity caps — protect DecimalField precision (max_digits=8, decimal_places=2
    # means we can store up to 999999.99). USDA data is occasionally absurd
    # (e.g., a "Tomato Paste" entry with sodium = 484850 mg/100g, which is
    # physically impossible). Cap at sane upper bounds — anything higher means
    # the source data is corrupt.
    SANITY_CAPS = {
        'calories_per_100g': Decimal('9999'),     # nothing exceeds 9000 kcal/100g
        'protein_per_100g':  Decimal('100'),      # can't exceed 100g of protein per 100g
        'carbs_per_100g':    Decimal('100'),
        'fat_per_100g':      Decimal('100'),
        'fiber_per_100g':    Decimal('100'),
        'sugar_per_100g':    Decimal('100'),
        'sodium_per_100g':   Decimal('99999'),    # 99g of sodium per 100g is the absolute ceiling
    }

    nutrient_field_names = tuple(SANITY_CAPS.keys())
    for field_name in nutrient_field_names:
        raw = data.get(field_name)
        if raw is None or raw == '':
            setattr(ingredient, field_name, None)
        else:
            try:
                value = Decimal(str(raw))
            except (InvalidOperation, TypeError, ValueError):
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid decimal for {field_name}: {raw}',
                }, status=400)

            # Clamp negative values (USDA sometimes has tiny negatives from
            # estimation rounding) and absurdly high ones to NULL — better
            # to show "no data" than save corrupted data.
            cap = SANITY_CAPS[field_name]
            if value < 0 or value > cap:
                # Set to None instead of failing — degrades gracefully
                setattr(ingredient, field_name, None)
            else:
                setattr(ingredient, field_name, value)

    ingredient.nutrition_synced_at = timezone.now()

    try:
        ingredient.save()
    except Exception as e:  # noqa: BLE001
        return JsonResponse({
            'success': False,
            'error': f'Database error saving ingredient: {str(e)}',
        }, status=500)

    # --- Optional: save the unit conversion ---
    uc_payload = data.get('unit_conversion')
    if uc_payload:
        try:
            from_unit_id = int(uc_payload.get('from_unit_id'))
            to_unit_id   = int(uc_payload.get('to_unit_id'))
            multiplier   = Decimal(str(uc_payload.get('multiplier')))
        except (TypeError, ValueError, InvalidOperation):
            return JsonResponse({
                'success': False,
                'error': 'Invalid unit_conversion payload.',
            }, status=400)

        if multiplier <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Unit conversion multiplier must be positive.',
            }, status=400)

        from_unit = get_object_or_404(MeasurementUnit, measurement_unit_id=from_unit_id)
        to_unit   = get_object_or_404(MeasurementUnit, measurement_unit_id=to_unit_id)

        UnitConversion.objects.update_or_create(
            from_unit=from_unit,
            to_unit=to_unit,
            specific_ingredient=ingredient,
            defaults={
                'multiplier': multiplier,
                'notes': f'Auto-saved during nutrition mapping ({ingredient.name})',
            },
        )

    return JsonResponse({
        'success': True,
        'ingredient_id': ingredient.ingredient_id,
        'is_mapped': True,
    })


# --------------------------------------------------------------------------- #
# Helper: list of unit choices for the wizard's "to_unit" dropdown
# --------------------------------------------------------------------------- #
# (Not used as a separate view — the data is embedded in the wizard page render.
#  Kept here as a docstring example for clarity.)
#
#     def get_unit_choices_for_wizard():
#         """Returns [(unit_id, name, unit_type), ...] for the wizard's UI."""
#         return [
#             (u.measurement_unit_id, u.name, u.unit_type)
#             for u in MeasurementUnit.objects.all().order_by('unit_type', 'name')
#         ]


# --------------------------------------------------------------------------- #
# Recipe nutrition data (AJAX)
# --------------------------------------------------------------------------- #

@login_required
@require_GET
def recipe_nutrition_data(request, recipe_id):
    """
    AJAX: compute and return the nutrition breakdown for a recipe.
    Used by the Nutrition button on view_recipe.html.
    """
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)

    try:
        result = calculate_recipe_nutrition(recipe)
    except Exception as e:  # noqa: BLE001
        return JsonResponse({
            'success': False,
            'error': f'Calculator error: {str(e)}',
        }, status=500)

    return JsonResponse({
        'success': True,
        'recipe_id': recipe.recipe_id,
        'recipe_name': recipe.recipe_name,
        **result,
    })


def recipe_has_any_mapped_ingredient(recipe):
    """
    Helper: does this recipe have at least one ingredient that has been
    mapped to nutrition data? Used by view_recipe to decide whether to
    show the Nutrition button at all.
    """
    return RecipeIngredient.objects.filter(
        recipe=recipe,
        ingredient__calories_per_100g__isnull=False,
    ).exists()


# --------------------------------------------------------------------------- #
# Unconvertible ingredients for a recipe (AJAX)
# --------------------------------------------------------------------------- #

@login_required
@require_GET
def recipe_unconvertible_ingredients(request, recipe_id):
    """
    AJAX: return the list of ingredients in this recipe that have nutrition
    data mapped but are missing a unit conversion to grams.

    Used by the "Set unit conversions →" mini-modal on view_recipe.html.

    Returns:
    {
      "success": true,
      "items": [
        {
          "ingredient_id": 42,
          "ingredient_name": "Carrot/s",
          "from_unit_id": 7,
          "from_unit_name": "piece",
          "from_unit_type": "count",   # 'count' / 'volume' / 'weight' / 'other'
          "to_unit_id": 12,            # the gram unit id
          "to_unit_name": "g"
        },
        ...
      ]
    }
    """
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)

    # Re-run the calculator just to get the unconvertible list
    try:
        result = calculate_recipe_nutrition(recipe)
    except Exception as e:  # noqa: BLE001
        return JsonResponse({
            'success': False,
            'error': f'Calculator error: {str(e)}',
        }, status=500)

    # Find the gram unit
    gram_unit_id = None
    gram_unit_name = 'g'
    gram_candidates = MeasurementUnit.objects.filter(unit_type='weight').values(
        'measurement_unit_id', 'name', 'abbreviation'
    )
    for u in gram_candidates:
        name = (u.get('name') or '').strip().lower()
        abbr = (u.get('abbreviation') or '').strip().lower()
        if name in ('gram', 'grams', 'g') or abbr == 'g':
            gram_unit_id = u['measurement_unit_id']
            gram_unit_name = u.get('abbreviation') or u.get('name') or 'g'
            break

    if not gram_unit_id:
        return JsonResponse({
            'success': False,
            'error': 'Could not find the gram measurement unit in your database.',
        }, status=500)

    # Build a richer payload by joining each unconvertible ingredient with
    # the recipe's ingredient lines to get the from_unit info.
    unconvertible_ids = [item['ingredient_id'] for item in result['ingredient_breakdown']['unconvertible']]

    # Distinct (ingredient, unit) pairs that need conversion
    seen_pairs = set()
    items = []

    recipe_lines = (
        RecipeIngredient.objects
        .filter(recipe=recipe, ingredient_id__in=unconvertible_ids)
        .select_related('ingredient', 'unit')
    )

    for line in recipe_lines:
        if not line.unit:
            continue  # can't make a conversion without a from_unit

        pair_key = (line.ingredient.ingredient_id, line.unit.measurement_unit_id)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        items.append({
            'ingredient_id': line.ingredient.ingredient_id,
            'ingredient_name': line.ingredient.name,
            'from_unit_id': line.unit.measurement_unit_id,
            'from_unit_name': line.unit.name,
            'from_unit_type': line.unit.unit_type,
            'to_unit_id': gram_unit_id,
            'to_unit_name': gram_unit_name,
        })

    return JsonResponse({
        'success': True,
        'recipe_id': recipe.recipe_id,
        'recipe_name': recipe.recipe_name,
        'items': items,
    })