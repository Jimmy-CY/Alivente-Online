"""
Shopping-list generation for recipes.

Owns the recipe shopping-list endpoints plus the shared smart-rounding helper.
Quantities are converted to each ingredient's shopping unit (via the
conversion layer in `recipes/conversions.py`) and rounded UP so the user
never under-buys.

Functions
---------
- round_shopping_quantity       : Shared helper. Rounds a quantity UP based on
                                  unit type (count/weight/volume/other). Pure
                                  function, no request.
- send_shopping_list            : Legacy/"DEBUG VERSION" single-recipe list.
                                  Edit-tier. See note below.
- generate_recipe_shopping_list : Production single-recipe list with conversion
                                  caching, smart rounding, and missing-conversion
                                  / missing-shopping-unit reporting. Read-tier.

Auth tiers
----------
`send_shopping_list` requires `auth.can_edit_recipes`;
`generate_recipe_shopping_list` requires `auth.can_access_recipes`.
`round_shopping_quantity` is an undecorated internal helper (correct - not a view).

Cleanup note
------------
`send_shopping_list` is self-labelled a DEBUG VERSION: it logs heavily via
`print()` (with corrupted mojibake glyphs) and appears functionally superseded
by `generate_recipe_shopping_list`. Flagged for the post-split review - verify
whether any URL still routes to it before deleting; if not, it is dead code.
"""

import json
import math
import traceback
from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from pages.models import Recipe

from .conversions import convert_quantity, get_conversion_cache


# =====================================================================
# SHARED HELPER
# =====================================================================

def round_shopping_quantity(qty, unit):
    """
    Round quantities intelligently based on unit type for shopping lists.
    NEVER rounds down - always rounds UP to ensure you have enough.
    - COUNT units: Round UP to whole numbers (min 1)
    - WEIGHT/VOLUME: Round UP to nearest sensible number
    - OTHER: Round UP to whole numbers
    """
    if qty <= 0:
        return qty

    unit_type = getattr(unit, 'unit_type', 'other')

    if unit_type == 'count':
        # Always round UP to whole number, minimum 1
        return max(1, math.ceil(qty))

    elif unit_type == 'weight':
        # Round UP to sensible numbers based on magnitude
        if qty < 10:
            # Small amounts: round UP to nearest 0.5
            return math.ceil(qty * 2) / 2
        elif qty < 100:
            # Medium amounts: round UP to nearest 5
            return math.ceil(qty / 5) * 5
        else:
            # Large amounts: round UP to nearest 10
            return math.ceil(qty / 10) * 10

    elif unit_type == 'volume':
        # Round UP to sensible numbers based on magnitude
        if qty < 10:
            # Small amounts (tsp, tbsp): round UP to nearest 0.25
            return math.ceil(qty * 4) / 4
        elif qty < 100:
            # Medium amounts: round UP to nearest 5
            return math.ceil(qty / 5) * 5
        else:
            # Large amounts: round UP to nearest 10
            return math.ceil(qty / 10) * 10

    else:
        # OTHER (dash, pinch, to taste): round UP
        return max(1, math.ceil(qty))


# =====================================================================
# SHOPPING LIST GENERATION
# =====================================================================

@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
@require_POST
def send_shopping_list(request):
    """Generate shopping list with unit conversion - DEBUG VERSION"""

    try:
        data = json.loads(request.body)

        recipe_id = data.get('recipe_id')
        servings = data.get('servings')
        original_servings = data.get('original_servings')

        # Get recipe
        recipe = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient__category',
            'recipe_ingredients__ingredient__default_unit',
            'recipe_ingredients__unit'
        ).get(recipe_id=recipe_id)

        servings_multiplier = Decimal(servings) / Decimal(original_servings)

        # Build shopping list
        shopping_list_categorized = {}

        print("\n" + "="*80)
        print(f"DEBUGGING SHOPPING LIST FOR: {recipe.recipe_name}")
        print("="*80)

        for recipe_ingredient in recipe.recipe_ingredients.all():
            ingredient = recipe_ingredient.ingredient
            quantity = Decimal(recipe_ingredient.amount or 0) * servings_multiplier
            from_unit = recipe_ingredient.unit
            shopping_unit = ingredient.default_unit

            print(f"\nIngredient: {ingredient.name}")
            print(f"  Recipe amount: {quantity} {from_unit.name if from_unit else 'None'}")
            print(f"  Shopping unit: {shopping_unit.name if shopping_unit else 'NOT SET [X]'}")

            if not from_unit:
                continue

            # Determine final unit and amount
            if not shopping_unit:
                print(f"  [X] No shopping unit - using recipe unit")
                final_unit = from_unit
                final_amount = quantity
            elif from_unit.measurement_unit_id == shopping_unit.measurement_unit_id:
                print(f"  [OK] Same unit - no conversion needed")
                final_unit = shopping_unit
                final_amount = quantity
            else:
                print(f"  [CONV] Trying conversion: {from_unit.name} -> {shopping_unit.name}")
                converted_qty, _ = convert_quantity(quantity, from_unit, shopping_unit)
                if converted_qty is not None:
                    print(f"  [OK] Conversion SUCCESS: {quantity} {from_unit.name} = {converted_qty} {shopping_unit.name}")
                    final_unit = shopping_unit
                    final_amount = converted_qty
                else:
                    print(f"  [X] Conversion FAILED - using recipe unit")
                    final_unit = from_unit
                    final_amount = quantity

            print(f"  Final: {final_amount} {final_unit.name}")

            # Format amount
            qty = float(final_amount)
            if qty % 1 == 0:
                qty_str = f"{int(qty)}"
            else:
                qty_str = f"{qty:.2f}".rstrip('0').rstrip('.')

            # Get category
            category = ingredient.category.name if ingredient.category else 'Other'

            if category not in shopping_list_categorized:
                shopping_list_categorized[category] = []

            shopping_list_categorized[category].append(
                f"{qty_str} {final_unit.name} {ingredient.name}"
            )

        print("\n" + "="*80 + "\n")

        return JsonResponse({
            'success': True,
            'shopping_list_categorized': shopping_list_categorized,
            'recipe_name': recipe.recipe_name,
            'servings': servings,
            'original_servings': original_servings
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
@require_POST
def generate_recipe_shopping_list(request):
    """Generate shopping list for a single recipe with unit conversion to shopping units"""
    try:
        data = json.loads(request.body)
        recipe_id = data.get('recipe_id')
        servings = data.get('servings')

        recipe = Recipe.objects.select_related().prefetch_related(
            'recipe_ingredients__ingredient__category',
            'recipe_ingredients__ingredient__default_unit',
            'recipe_ingredients__unit'
        ).get(recipe_id=recipe_id)

        original_servings = recipe.servings or 4
        servings_multiplier = Decimal(servings) / Decimal(original_servings)

        # Track issues
        missing_conversions = []
        missing_shopping_units = []
        seen_missing_conversions = set()
        seen_missing_units = set()

        # Pre-load all unit conversions for fast lookups
        conversion_cache = get_conversion_cache()

        # Aggregate by ingredient ID
        aggregated = defaultdict(lambda: {
            'amount': Decimal('0'),
            'unit': None,
            'ingredient_obj': None,
            'unconverted_items': []
        })

        for recipe_ingredient in recipe.recipe_ingredients.all():
            ingredient = recipe_ingredient.ingredient
            ingredient_id = ingredient.ingredient_id
            quantity = Decimal(recipe_ingredient.amount or 0) * servings_multiplier
            from_unit = recipe_ingredient.unit

            if not from_unit:
                continue

            # CRITICAL: Always use shopping unit
            shopping_unit = ingredient.default_unit

            # Track ingredients without shopping units
            if not shopping_unit:
                if ingredient_id not in seen_missing_units:
                    seen_missing_units.add(ingredient_id)
                    missing_shopping_units.append({
                        'ingredient_id': ingredient_id,
                        'ingredient_name': ingredient.name
                    })

                # Use fallback unit
                if aggregated[ingredient_id]['unit'] is None:
                    aggregated[ingredient_id]['unit'] = from_unit
                    aggregated[ingredient_id]['ingredient_obj'] = ingredient

                aggregated[ingredient_id]['unconverted_items'].append({
                    'quantity': float(quantity),
                    'unit': from_unit.name,
                    'reason': 'No shopping unit defined'
                })
                continue

            # Initialize
            if aggregated[ingredient_id]['unit'] is None:
                aggregated[ingredient_id]['unit'] = shopping_unit
                aggregated[ingredient_id]['ingredient_obj'] = ingredient

            shopping_unit = aggregated[ingredient_id]['unit']

            # Convert to shopping unit
            if from_unit.measurement_unit_id == shopping_unit.measurement_unit_id:
                # Same unit - just add
                aggregated[ingredient_id]['amount'] += quantity
            else:
                # Need conversion
                converted_qty, multiplier = convert_quantity(quantity, from_unit, shopping_unit, ingredient, conversion_cache)

                if converted_qty is not None:
                    # Conversion successful
                    aggregated[ingredient_id]['amount'] += converted_qty
                else:
                    # Missing conversion
                    conversion_key = f"{from_unit.measurement_unit_id}-{shopping_unit.measurement_unit_id}"
                    if conversion_key not in seen_missing_conversions:
                        seen_missing_conversions.add(conversion_key)
                        missing_conversions.append({
                            'ingredient': ingredient.name,
                            'from_unit': from_unit.name,
                            'from_unit_id': from_unit.measurement_unit_id,
                            'to_unit': shopping_unit.name,
                            'to_unit_id': shopping_unit.measurement_unit_id,
                            'quantity': float(quantity)
                        })

                    # Track unconverted
                    aggregated[ingredient_id]['unconverted_items'].append({
                        'quantity': float(quantity),
                        'unit': from_unit.name,
                        'reason': f'Missing conversion from {from_unit.name} to {shopping_unit.name}'
                    })

        # Build categorized shopping list
        shopping_list_categorized = defaultdict(list)

        for ingredient_id, agg_data in aggregated.items():
            ingredient_obj = agg_data['ingredient_obj']
            category = ingredient_obj.category.name if ingredient_obj.category else 'Other'

            # Only add if we have a converted amount
            if agg_data['amount'] > 0:
                unit = agg_data['unit']
                raw_qty = float(agg_data['amount'])

                # Apply smart rounding for shopping
                qty = round_shopping_quantity(raw_qty, unit)

                # Format quantity string
                if qty % 1 == 0:
                    qty_str = f"{int(qty)}"
                else:
                    qty_str = f"{qty:.2f}".rstrip('0').rstrip('.')

                # Get proper unit display with pluralization
                if qty == 1:
                    unit_display = unit.abbreviation or unit.name
                else:
                    unit_display = unit.abbreviation_plural or unit.abbreviation or unit.name_plural or unit.name

                item_str = f"{qty_str} {unit_display} {ingredient_obj.name}"

                # Add note if there are unconverted items
                if agg_data['unconverted_items']:
                    item_str += f" (+ unconverted items)"

                shopping_list_categorized[category].append(item_str)

        # Check if we have issues to prompt for
        has_issues = len(missing_conversions) > 0 or len(missing_shopping_units) > 0

        if has_issues:
            return JsonResponse({
                'success': False,
                'needs_conversions': True,
                'missing_conversions': missing_conversions,
                'missing_shopping_units': missing_shopping_units
            })

        return JsonResponse({
            'success': True,
            'shopping_list_categorized': dict(shopping_list_categorized),
            'recipe_name': recipe.recipe_name,
            'servings': servings,
            'original_servings': original_servings
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)