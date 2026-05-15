"""
Unit conversion management — the largest module in the recipes sub-package.

13 functions covering:

Helpers (used by other recipe modules and views):
    get_base_unit_for_ingredient(ingredient)
        Best base unit for an ingredient: 1) ingredient.default_unit,
        2) category-based defaults (Vegetables/Fruits/Meat/... -> gram,
        Dairy/Oils/Beverages -> milliliter), 3) gram fallback.
    get_conversion_cache()
        Pre-loads all UnitConversion rows into a dict structure for
        O(1) lookups: cache['specific'][ing_id][(from_id, to_id)]
        and cache['generic'][(from_id, to_id)].
    convert_quantity(amount, from_unit, to_unit, ingredient=None,
                     conversion_cache=None)
        Convert quantity between units. Priority: 1) ingredient-specific
        conversion, 2) generic conversion. Tries forward then reverse.
        Returns (converted_amount, multiplier) or (None, None).
        Uses cache if provided (fast path); otherwise falls back to
        per-call DB queries.

AJAX endpoint (called from various inline forms):
    save_unit_conversion(request) [POST]
        Upsert by (from_unit, to_unit, specific_ingredient).

Conversion management UI:
    scan_for_missing_conversions()
        Walk all recipe ingredients, return list of (ingredient,
        from_unit, to_unit) tuples that lack a conversion.
    add_conversion(request) [POST, form-encoded]
    unit_conversions_management(request)
        Main list view; renders unit_conversions_management.html.
    add_unit_conversion_manual(request) [POST, JSON body]
    edit_unit_conversion(request) [POST, JSON body]
    delete_unit_conversion(request) [POST, JSON body]

Ingredient base-unit management UI:
    ingredient_base_units_management(request)
        Per-ingredient shopping-unit + nutrition + conversion-status
        dashboard. Renders ingredient_base_units_management.html.
    update_ingredient_base_unit(request) [POST, JSON body]

Bulk-conversion wizard (originally at the bottom of main.py):
    unit_conversions_wizard(request)
        Walks user through every mapped ingredient whose conversion
        status is partial or missing. Supports ?recipe_id=N for
        recipe-scoped, ?ingredient_id=N for single-row drill-in, and
        ?return_to=recipe to send the Back button back to view_recipe.

Three save/upsert endpoints (save_unit_conversion, add_conversion,
add_unit_conversion_manual) exist for historical reasons — called
from different UIs. Candidate for consolidation in a future cleanup.

Extracted from pages/views/main.py as part of the modular views
migration (### RECIPE MANAGEMENT ### -> recipes/ sub-package, phase 5).
Two non-contiguous source blocks in main.py merged into this single
module for cohesion (originally separated by meal-planning,
measurement-units, and toggle-favourite functions which stay in main
until their own phases).

Cleanups during the move:
  - Removed dead 'from collections import defaultdict' inside
    scan_for_missing_conversions (imported but never used).
"""

import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from ...models import (
    Ingredient,
    IngredientCategory,
    MeasurementUnit,
    Recipe,
    RecipeIngredient,
    UnitConversion,
)


def get_base_unit_for_ingredient(ingredient):
    """
    Determine the best base unit for an ingredient.
    Priority: 1) ingredient.default_unit, 2) category defaults, 3) gram
    Returns a MeasurementUnit object.
    """
    # PRIORITY 1: Use ingredient's default_unit if set
    if ingredient.default_unit:
        return ingredient.default_unit

    # PRIORITY 2: Use category-based defaults
    base_unit_map = {
        'Vegetables': 'gram',
        'Fruits': 'gram',
        'Meat & Seafood': 'gram',
        'Poultry': 'gram',
        'Dairy': 'milliliter',
        'Grains & Pasta': 'gram',
        'Oils & Fats': 'milliliter',
        'Baking': 'gram',
        'Herbs & Spices': 'gram',
        'Canned & Packaged': 'gram',
        'Beverages': 'milliliter',
    }

    if ingredient.category:
        preferred_unit_name = base_unit_map.get(ingredient.category.name, 'gram')
    else:
        preferred_unit_name = 'gram'

    # PRIORITY 3: Try to get the preferred unit
    try:
        return MeasurementUnit.objects.get(name__iexact=preferred_unit_name)
    except MeasurementUnit.DoesNotExist:
        # PRIORITY 4: Fallback to gram
        try:
            return MeasurementUnit.objects.get(name__iexact='gram')
        except:
            # PRIORITY 5: Last resort - any unit
            return MeasurementUnit.objects.first()

def get_conversion_cache():
    """
    Pre-load all unit conversions into memory for fast lookups.
    Returns a dictionary structure for O(1) lookup time.
    """
    cache = {
        'specific': {},  # ingredient_id -> {(from_id, to_id): multiplier}
        'generic': {}    # (from_id, to_id): multiplier
    }

    # Load all conversions in one query
    conversions = UnitConversion.objects.select_related('specific_ingredient').all()

    for conv in conversions:
        from_id = conv.from_unit_id
        to_id = conv.to_unit_id
        multiplier = conv.multiplier

        if conv.specific_ingredient_id:
            # Ingredient-specific conversion
            ing_id = conv.specific_ingredient_id
            if ing_id not in cache['specific']:
                cache['specific'][ing_id] = {}
            cache['specific'][ing_id][(from_id, to_id)] = multiplier
        else:
            # Generic conversion
            cache['generic'][(from_id, to_id)] = multiplier

    return cache

def convert_quantity(amount, from_unit, to_unit, ingredient=None, conversion_cache=None):
    """
    Convert a quantity from one unit to another using the UnitConversion table.
    Priority: 1) Ingredient-specific conversion, 2) Generic conversion
    Returns (converted_amount, multiplier) or (None, None) if no conversion exists.

    If conversion_cache is provided, uses in-memory lookups (much faster).
    Otherwise falls back to database queries.
    """
    if from_unit.measurement_unit_id == to_unit.measurement_unit_id:
        return (amount, Decimal('1'))

    from_id = from_unit.measurement_unit_id
    to_id = to_unit.measurement_unit_id

    # Use cache if provided (fast path)
    if conversion_cache:
        # PRIORITY 1: Check ingredient-specific conversion
        if ingredient and ingredient.ingredient_id in conversion_cache['specific']:
            specific_cache = conversion_cache['specific'][ingredient.ingredient_id]

            # Direct conversion
            if (from_id, to_id) in specific_cache:
                multiplier = specific_cache[(from_id, to_id)]
                converted = Decimal(amount) * multiplier
                return (converted, multiplier)

            # Reverse conversion
            if (to_id, from_id) in specific_cache:
                multiplier = specific_cache[(to_id, from_id)]
                converted = Decimal(amount) / multiplier
                return (converted, Decimal('1') / multiplier)

        # PRIORITY 2: Check generic conversion
        generic_cache = conversion_cache['generic']

        # Direct conversion
        if (from_id, to_id) in generic_cache:
            multiplier = generic_cache[(from_id, to_id)]
            converted = Decimal(amount) * multiplier
            return (converted, multiplier)

        # Reverse conversion
        if (to_id, from_id) in generic_cache:
            multiplier = generic_cache[(to_id, from_id)]
            converted = Decimal(amount) / multiplier
            return (converted, Decimal('1') / multiplier)

        # No conversion found
        return (None, None)

    # Fallback to database queries (slow path - for backwards compatibility)
    # PRIORITY 1: Check for INGREDIENT-SPECIFIC conversion (if ingredient provided)
    if ingredient:
        # Try direct conversion
        try:
            conversion = UnitConversion.objects.get(
                from_unit=from_unit,
                to_unit=to_unit,
                specific_ingredient=ingredient
            )
            converted = Decimal(amount) * conversion.multiplier
            return (converted, conversion.multiplier)
        except UnitConversion.DoesNotExist:
            pass

        # Try reverse conversion
        try:
            conversion = UnitConversion.objects.get(
                from_unit=to_unit,
                to_unit=from_unit,
                specific_ingredient=ingredient
            )
            converted = Decimal(amount) / conversion.multiplier
            return (converted, Decimal('1') / conversion.multiplier)
        except UnitConversion.DoesNotExist:
            pass

    # PRIORITY 2: Check for GENERIC conversion (specific_ingredient IS NULL)
    # Try direct conversion
    try:
        conversion = UnitConversion.objects.get(
            from_unit=from_unit,
            to_unit=to_unit,
            specific_ingredient=None
        )
        converted = Decimal(amount) * conversion.multiplier
        return (converted, conversion.multiplier)
    except UnitConversion.DoesNotExist:
        pass

    # Try reverse conversion
    try:
        conversion = UnitConversion.objects.get(
            from_unit=to_unit,
            to_unit=from_unit,
            specific_ingredient=None
        )
        converted = Decimal(amount) / conversion.multiplier
        return (converted, Decimal('1') / conversion.multiplier)
    except UnitConversion.DoesNotExist:
        pass

    # No conversion found (neither ingredient-specific nor generic)
    return (None, None)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def save_unit_conversion(request):
    """Save a new unit conversion"""

    try:
        data = json.loads(request.body)

        from_unit_id = data.get('from_unit_id')
        to_unit_id = data.get('to_unit_id')
        multiplier = data.get('multiplier')
        ingredient_name = data.get('ingredient_name')  # ← NEW: Get ingredient name if provided

        if not all([from_unit_id, to_unit_id, multiplier]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        from_unit = MeasurementUnit.objects.get(measurement_unit_id=from_unit_id)
        to_unit = MeasurementUnit.objects.get(measurement_unit_id=to_unit_id)

        # Get specific ingredient if provided
        specific_ingredient = None
        if ingredient_name:
            try:
                specific_ingredient = Ingredient.objects.get(name__iexact=ingredient_name)
            except Ingredient.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Ingredient "{ingredient_name}" not found'}, status=404)

        try:
            mult = Decimal(multiplier)
            if mult <= 0:
                return JsonResponse({'success': False, 'error': 'Multiplier must be positive'}, status=400)
        except:
            return JsonResponse({'success': False, 'error': 'Invalid multiplier'}, status=400)

        # Check for existing conversion (with the same specific_ingredient setting)
        existing = UnitConversion.objects.filter(
            from_unit=from_unit,
            to_unit=to_unit,
            specific_ingredient=specific_ingredient
        ).first()

        if existing:
            existing.multiplier = mult
            existing.save()
        else:
            # Create conversion (generic or ingredient-specific based on user choice)
            UnitConversion.objects.create(
                from_unit=from_unit,
                to_unit=to_unit,
                specific_ingredient=specific_ingredient,
                multiplier=mult
            )

        return JsonResponse({
            'success': True,
            'message': f'Conversion saved: 1 {from_unit.name} = {mult} {to_unit.name}'
        })

    except MeasurementUnit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Unit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# UNIT CONVERSION MANAGEMENT
# ============================================

def scan_for_missing_conversions():
    """
    Scan all recipe ingredients and find missing unit conversions.
    Returns list of missing conversions needed.
    """
    missing = []
    seen = set()  # To avoid duplicates

    # Get conversion cache for fast lookups
    conversion_cache = get_conversion_cache()

    # Get all recipe ingredients with their units
    recipe_ingredients = RecipeIngredient.objects.select_related(
        'ingredient',
        'ingredient__default_unit',
        'unit',
        'recipe'
    ).exclude(
        ingredient__default_unit__isnull=True  # Skip ingredients without shopping units
    ).exclude(
        unit__isnull=True  # Skip ingredients without recipe units
    )

    for ri in recipe_ingredients:
        ingredient = ri.ingredient
        from_unit = ri.unit
        to_unit = ingredient.default_unit

        # Skip if same unit
        if from_unit.measurement_unit_id == to_unit.measurement_unit_id:
            continue

        # Create unique key to avoid duplicates
        cache_key = f"{from_unit.measurement_unit_id}-{to_unit.measurement_unit_id}-{ingredient.ingredient_id}"

        if cache_key in seen:
            continue

        # Check if conversion exists
        converted_qty, multiplier = convert_quantity(
            Decimal('1'),
            from_unit,
            to_unit,
            ingredient,
            conversion_cache
        )

        if converted_qty is None:
            # Missing conversion found
            seen.add(cache_key)
            missing.append({
                'ingredient': ingredient.name,
                'ingredient_id': ingredient.ingredient_id,
                'from_unit': from_unit.name,
                'from_unit_id': from_unit.measurement_unit_id,
                'to_unit': to_unit.name,
                'to_unit_id': to_unit.measurement_unit_id,
                'recipe_example': ri.recipe.recipe_name
            })

    return missing

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def add_conversion(request):
    """Add a new unit conversion via AJAX"""

    if request.method == 'POST':
        try:
            from_unit_id = request.POST.get('from_unit')
            to_unit_id = request.POST.get('to_unit')
            specific_ingredient_id = request.POST.get('specific_ingredient')
            multiplier = request.POST.get('multiplier')

            if not all([from_unit_id, to_unit_id, multiplier]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})

            from_unit = MeasurementUnit.objects.get(measurement_unit_id=from_unit_id)
            to_unit = MeasurementUnit.objects.get(measurement_unit_id=to_unit_id)

            # Handle specific ingredient (can be null for generic conversions)
            specific_ingredient = None
            if specific_ingredient_id and specific_ingredient_id != 'null':
                specific_ingredient = Ingredient.objects.get(ingredient_id=specific_ingredient_id)

            # Check if conversion already exists
            existing = UnitConversion.objects.filter(
                from_unit=from_unit,
                to_unit=to_unit,
                specific_ingredient=specific_ingredient
            ).first()

            if existing:
                # Update existing
                existing.multiplier = multiplier
                existing.save()
            else:
                # Create new
                UnitConversion.objects.create(
                    from_unit=from_unit,
                    to_unit=to_unit,
                    specific_ingredient=specific_ingredient,
                    multiplier=multiplier
                )

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def unit_conversions_management(request):
    """Manage unit conversions"""

    conversions = UnitConversion.objects.all().select_related(
        'from_unit',
        'to_unit',
        'specific_ingredient'
    ).order_by('from_unit__name', 'specific_ingredient__name', 'to_unit__name')

    all_units = MeasurementUnit.objects.all().order_by('name')
    all_ingredients = Ingredient.objects.all().order_by('name')

    # Scan for missing conversions across all recipes
    missing_conversions = scan_for_missing_conversions()

    context = {
        'conversions': conversions,
        'all_units': all_units,
        'all_ingredients': all_ingredients,
        'missing_conversions': json.dumps(missing_conversions) if missing_conversions else '[]',
        'missing_count': len(missing_conversions),
    }

    return render(request, 'unit_conversions_management.html', context)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_unit_conversion_manual(request):
    """Add a new unit conversion"""

    try:
        data = json.loads(request.body)

        from_unit_id = data.get('from_unit_id')
        to_unit_id = data.get('to_unit_id')
        specific_ingredient_id = data.get('specific_ingredient_id')  # ← NEW
        multiplier = data.get('multiplier')

        if not all([from_unit_id, to_unit_id, multiplier]):
            return JsonResponse({'success': False, 'error': 'All required fields must be filled'}, status=400)

        # Check if same unit
        if from_unit_id == to_unit_id:
            return JsonResponse({'success': False, 'error': 'Cannot convert a unit to itself'}, status=400)

        from_unit = MeasurementUnit.objects.get(measurement_unit_id=from_unit_id)
        to_unit = MeasurementUnit.objects.get(measurement_unit_id=to_unit_id)

        # Get specific ingredient if provided
        specific_ingredient = None
        if specific_ingredient_id:
            try:
                specific_ingredient = Ingredient.objects.get(ingredient_id=specific_ingredient_id)
            except Ingredient.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Ingredient not found'}, status=404)

        mult = Decimal(multiplier)
        if mult <= 0:
            return JsonResponse({'success': False, 'error': 'Multiplier must be positive'}, status=400)

        # Check if already exists (now includes specific_ingredient in the check)
        if UnitConversion.objects.filter(
            from_unit=from_unit,
            to_unit=to_unit,
            specific_ingredient=specific_ingredient
        ).exists():
            if specific_ingredient:
                return JsonResponse({'success': False, 'error': f'This conversion already exists for {specific_ingredient.name}'}, status=400)
            else:
                return JsonResponse({'success': False, 'error': 'This generic conversion already exists'}, status=400)

        # Create conversion
        conversion = UnitConversion.objects.create(
            from_unit=from_unit,
            to_unit=to_unit,
            specific_ingredient=specific_ingredient,  # ← NEW
            multiplier=mult
        )

        return JsonResponse({
            'success': True,
            'conversion': {
                'id': conversion.unit_conversion_id,
                'from_unit': from_unit.name,
                'to_unit': to_unit.name,
                'specific_ingredient': specific_ingredient.name if specific_ingredient else 'Generic',
                'multiplier': str(mult)
            }
        })

    except MeasurementUnit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Unit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def edit_unit_conversion(request):
    """Edit an existing unit conversion"""

    try:
        data = json.loads(request.body)

        conversion_id = data.get('conversion_id')
        multiplier = data.get('multiplier')
        specific_ingredient_id = data.get('specific_ingredient_id')  # ← NEW

        if not all([conversion_id, multiplier]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        conversion = UnitConversion.objects.get(unit_conversion_id=conversion_id)

        mult = Decimal(multiplier)
        if mult <= 0:
            return JsonResponse({'success': False, 'error': 'Multiplier must be positive'}, status=400)

        # Get specific ingredient if provided
        specific_ingredient = None
        if specific_ingredient_id:
            try:
                specific_ingredient = Ingredient.objects.get(ingredient_id=specific_ingredient_id)
            except Ingredient.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Ingredient not found'}, status=404)

        # Check if changing specific_ingredient would create a duplicate
        duplicate = UnitConversion.objects.filter(
            from_unit=conversion.from_unit,
            to_unit=conversion.to_unit,
            specific_ingredient=specific_ingredient
        ).exclude(unit_conversion_id=conversion_id).exists()

        if duplicate:
            if specific_ingredient:
                return JsonResponse({'success': False, 'error': f'A conversion for {specific_ingredient.name} already exists'}, status=400)
            else:
                return JsonResponse({'success': False, 'error': 'A generic conversion already exists'}, status=400)

        # Update the conversion
        conversion.multiplier = mult
        conversion.specific_ingredient = specific_ingredient
        conversion.save()

        applies_to = specific_ingredient.name if specific_ingredient else 'all ingredients'

        return JsonResponse({
            'success': True,
            'message': f'Updated: 1 {conversion.from_unit.name} = {mult} {conversion.to_unit.name} (applies to {applies_to})'
        })

    except UnitConversion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversion not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def delete_unit_conversion(request):
    """Delete a unit conversion"""

    try:
        data = json.loads(request.body)
        conversion_id = data.get('conversion_id')

        if not conversion_id:
            return JsonResponse({'success': False, 'error': 'Conversion ID required'}, status=400)

        conversion = UnitConversion.objects.get(unit_conversion_id=conversion_id)
        conversion_text = f"1 {conversion.from_unit.name} = {conversion.multiplier} {conversion.to_unit.name}"
        conversion.delete()

        return JsonResponse({
            'success': True,
            'message': f'Deleted conversion: {conversion_text}'
        })

    except UnitConversion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversion not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# INGREDIENT BASE UNIT MANAGEMENT
# ============================================
@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def ingredient_base_units_management(request):
    """Manage ingredient shopping units, with nutrition + conversion status."""

    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    ingredients = Ingredient.objects.select_related('category', 'default_unit').all()

    if search_query:
        ingredients = ingredients.filter(name__icontains=search_query)

    if category_filter:
        ingredients = ingredients.filter(category__ingredient_category_id=category_filter)

    ingredients = ingredients.order_by('name')

    all_units = MeasurementUnit.objects.all().order_by('name')
    categories = IngredientCategory.objects.all().order_by('name')

    # ----- Find the gram unit ID -----
    gram_unit_id = None
    for u in MeasurementUnit.objects.filter(unit_type='weight').values(
        'measurement_unit_id', 'name', 'abbreviation'
    ):
        name = (u.get('name') or '').strip().lower()
        abbr = (u.get('abbreviation') or '').strip().lower()
        if name in ('gram', 'grams', 'g') or abbr == 'g':
            gram_unit_id = u['measurement_unit_id']
            break

    # ----- Pre-fetch ALL specific conversions to grams -----
    ingredient_ids = [ing.ingredient_id for ing in ingredients]

    conversions_by_ingredient = {}  # for the modal (full list)
    units_with_path_to_grams = {}   # for the conversion-status calc

    if ingredient_ids and gram_unit_id:
        conv_qs = (
            UnitConversion.objects
            .filter(specific_ingredient_id__in=ingredient_ids)
            .filter(Q(from_unit_id=gram_unit_id) | Q(to_unit_id=gram_unit_id))
            .select_related('from_unit', 'to_unit')
        )
        for c in conv_qs:
            ing_id = c.specific_ingredient_id
            conversions_by_ingredient.setdefault(ing_id, []).append({
                'from_unit_name': c.from_unit.name,
                'from_unit_id': c.from_unit_id,
                'to_unit_name': c.to_unit.name,
                'to_unit_id': c.to_unit_id,
                'multiplier': float(c.multiplier),
            })
            if c.to_unit_id == gram_unit_id:
                units_with_path_to_grams.setdefault(ing_id, set()).add(c.from_unit_id)

    unit_types = dict(
        MeasurementUnit.objects.values_list('measurement_unit_id', 'unit_type')
    )
    unit_names = dict(
        MeasurementUnit.objects.values_list('measurement_unit_id', 'name')
    )

    # ----- Recipe usage per ingredient -----
    units_used_per_ingredient = {}
    if ingredient_ids:
        ri_pairs = (
            RecipeIngredient.objects
            .filter(ingredient_id__in=ingredient_ids)
            .exclude(unit_id__isnull=True)
            .values_list('ingredient_id', 'unit_id')
            .distinct()
        )
        for ing_id, unit_id in ri_pairs:
            units_used_per_ingredient.setdefault(ing_id, set()).add(unit_id)

    # ----- Conversion status helpers -----
    def _unit_has_path_to_grams(unit_id, ingredient_id):
        if unit_id is None:
            return False
        if gram_unit_id and unit_id == gram_unit_id:
            return True
        if unit_id in units_with_path_to_grams.get(ingredient_id, set()):
            return True
        if unit_types.get(unit_id) == 'weight':
            return True
        return False

    def _compute_conversion_status(ing):
        if ing.fdc_id is None:
            return 'na', []
        units_to_check = set()
        units_to_check.update(units_used_per_ingredient.get(ing.ingredient_id, set()))
        if ing.default_unit_id:
            units_to_check.add(ing.default_unit_id)
        if not units_to_check:
            return 'missing', ['(no unit set, not used in any recipe)']
        ok_units = []
        bad_units = []
        for u_id in units_to_check:
            if _unit_has_path_to_grams(u_id, ing.ingredient_id):
                ok_units.append(u_id)
            else:
                bad_units.append(u_id)
        if not bad_units:
            return 'ready', []
        if not ok_units:
            return 'missing', sorted(unit_names.get(u, f'unit#{u}') for u in bad_units)
        return 'partial', sorted(unit_names.get(u, f'unit#{u}') for u in bad_units)

    # ----- Helper: build a human-readable conversions summary for tooltip -----
    def _summarize_conversions(ing_id):
        """
        Return a list of strings like "1 cup → 240 g" describing every
        ingredient-specific conversion to grams. Used in the Conversion
        badge tooltip.
        """
        rows = conversions_by_ingredient.get(ing_id, [])
        out = []
        for r in rows:
            if r['to_unit_id'] == gram_unit_id:
                # Format multiplier neatly — drop trailing zeros
                m = r['multiplier']
                m_str = f"{m:.4f}".rstrip('0').rstrip('.') if isinstance(m, float) else str(m)
                out.append(f"1 {r['from_unit_name']} → {m_str} g")
        return sorted(out)

    # ----- Build the final list with tooltip data attached -----
    ingredients_with_base = []
    for ing in ingredients:
        status, missing_units = _compute_conversion_status(ing)

        # Nutrition values for the Nutrition badge tooltip.
        # Decimal values come back as Decimal — convert to float so the JSON
        # serializer in data-* attributes doesn't choke. None passes through.
        def _f(v):
            return float(v) if v is not None else None

        nutrition_values = {
            'calories': _f(ing.calories_per_100g),
            'protein':  _f(ing.protein_per_100g),
            'carbs':    _f(ing.carbs_per_100g),
            'fat':      _f(ing.fat_per_100g),
        }

        # Conversion strings for the Conversion badge tooltip
        conversions_summary = _summarize_conversions(ing.ingredient_id)

        # Nutrition source — supports the badge's manual/USDA distinction.
        # Falls back gracefully if the field doesn't exist yet (pre-migration).
        nutrition_source = getattr(ing, 'nutrition_source', None)

        ingredients_with_base.append({
            'ingredient': ing,
            'conversions': conversions_by_ingredient.get(ing.ingredient_id, []),
            'conversion_status': status,
            'missing_units': missing_units,
            'nutrition_values': nutrition_values,
            'conversions_summary': conversions_summary,
            'nutrition_source': nutrition_source,
        })

    # ----- Global outstanding counts for the action-bar buttons -----
    page_ingredient_ids = set(ing.ingredient_id for ing in ingredients)
    unmapped_count = Ingredient.objects.filter(fdc_id__isnull=True).count()

    unconvertible_count = sum(
        1 for item in ingredients_with_base
        if item['conversion_status'] in ('partial', 'missing')
    )

    other_mapped = (
        Ingredient.objects
        .filter(fdc_id__isnull=False)
        .exclude(ingredient_id__in=page_ingredient_ids)
        .select_related('default_unit')
    )
    if other_mapped.exists():
        other_ids = [i.ingredient_id for i in other_mapped]

        other_units_to_grams = {}
        if gram_unit_id:
            for c in (
                UnitConversion.objects
                .filter(specific_ingredient_id__in=other_ids, to_unit_id=gram_unit_id)
                .values_list('specific_ingredient_id', 'from_unit_id')
            ):
                other_units_to_grams.setdefault(c[0], set()).add(c[1])

        other_units_used = {}
        for ing_id, unit_id in (
            RecipeIngredient.objects
            .filter(ingredient_id__in=other_ids)
            .exclude(unit_id__isnull=True)
            .values_list('ingredient_id', 'unit_id')
            .distinct()
        ):
            other_units_used.setdefault(ing_id, set()).add(unit_id)

        for ing in other_mapped:
            units_to_check = set()
            units_to_check.update(other_units_used.get(ing.ingredient_id, set()))
            if ing.default_unit_id:
                units_to_check.add(ing.default_unit_id)

            if not units_to_check:
                unconvertible_count += 1
                continue

            ok = False
            bad = False
            for u_id in units_to_check:
                if (gram_unit_id and u_id == gram_unit_id) \
                   or u_id in other_units_to_grams.get(ing.ingredient_id, set()) \
                   or unit_types.get(u_id) == 'weight':
                    ok = True
                else:
                    bad = True

            if bad:
                unconvertible_count += 1

    context = {
        'ingredients_with_base': ingredients_with_base,
        'categories': categories,
        'all_units': all_units,
        'search_query': search_query,
        'category_filter': category_filter,
        'unmapped_count': unmapped_count,
        'unconvertible_count': unconvertible_count,
    }

    return render(request, 'ingredient_base_units_management.html', context)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def update_ingredient_base_unit(request):
    """Update an ingredient's default unit"""

    try:
        data = json.loads(request.body)

        ingredient_id = data.get('ingredient_id')
        base_unit_id = data.get('base_unit_id')

        if not ingredient_id:
            return JsonResponse({'success': False, 'error': 'Ingredient ID required'}, status=400)

        ingredient = Ingredient.objects.get(ingredient_id=ingredient_id)

        # If base_unit_id is None or empty, clear the override
        if not base_unit_id:
            ingredient.default_unit = None
            ingredient.save()
            return JsonResponse({
                'success': True,
                'message': f'Cleared override for {ingredient.name} - now using automatic unit'
            })

        base_unit = MeasurementUnit.objects.get(measurement_unit_id=base_unit_id)
        ingredient.default_unit = base_unit
        ingredient.save()

        return JsonResponse({
            'success': True,
            'message': f'Updated {ingredient.name} default unit to {base_unit.name}'
        })

    except Ingredient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ingredient not found'}, status=404)
    except MeasurementUnit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Unit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# UNIT CONVERSIONS WIZARD (BULK)
# ============================================

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def unit_conversions_wizard(request):
    """
    Render the bulk conversions wizard.

    Walks the user through every mapped ingredient whose conversion status
    is partial or missing — i.e., the calculator can't fully convert its
    recipe-line units to grams.

    For each ingredient, returns the set of units that lack a path to
    grams (so the wizard knows which conversion fields to display).

    Query params:
        recipe_id = optional; filters the queue to ingredients used in
                    this specific recipe (matches the mapping-wizard pattern)
        return_to = optional; 'recipe' means the Back button returns to
                    the view_recipe page and auto-reopens the Nutrition modal
    """
    recipe_id = request.GET.get('recipe_id')
    return_to = request.GET.get('return_to', 'ingredients')
    single_ingredient_id = request.GET.get('ingredient_id')  # drill-in from row badge

    # Recipe-scoped filtering
    scoped_recipe = None
    scoped_ingredient_ids = None
    if recipe_id:
        try:
            scoped_recipe = Recipe.objects.get(recipe_id=int(recipe_id))
            scoped_ingredient_ids = list(
                RecipeIngredient.objects
                .filter(recipe=scoped_recipe)
                .values_list('ingredient_id', flat=True)
                .distinct()
            )
        except (Recipe.DoesNotExist, ValueError, TypeError):
            scoped_recipe = None
            scoped_ingredient_ids = None

    # Single-ingredient drill-in: overrides recipe scoping if both are passed
    if single_ingredient_id:
        try:
            single_id = int(single_ingredient_id)
            scoped_ingredient_ids = [single_id]
        except (ValueError, TypeError):
            pass

    # ----- Find the gram unit ID -----
    gram_unit_id = None
    for u in MeasurementUnit.objects.filter(unit_type='weight').values(
        'measurement_unit_id', 'name', 'abbreviation'
    ):
        name = (u.get('name') or '').strip().lower()
        abbr = (u.get('abbreviation') or '').strip().lower()
        if name in ('gram', 'grams', 'g') or abbr == 'g':
            gram_unit_id = u['measurement_unit_id']
            break

    # ----- Pre-fetch unit metadata -----
    units_by_id = {
        u.measurement_unit_id: u for u in MeasurementUnit.objects.all()
    }

    # ----- Find candidate ingredients: mapped (fdc_id IS NOT NULL) -----
    # We'll filter further to partial/missing in the loop.
    candidate_qs = (
        Ingredient.objects
        .filter(fdc_id__isnull=False)
        .select_related('default_unit', 'category')
        .order_by('name')
    )
    if scoped_ingredient_ids is not None:
        candidate_qs = candidate_qs.filter(ingredient_id__in=scoped_ingredient_ids)

    candidate_ingredients = list(candidate_qs)
    candidate_ids = [ing.ingredient_id for ing in candidate_ingredients]

    # ----- Pre-fetch existing conversions to grams (specific-ingredient) -----
    units_with_path_to_grams = {}  # {ingredient_id: set([from_unit_id, ...])}
    if candidate_ids and gram_unit_id:
        for c in (
            UnitConversion.objects
            .filter(specific_ingredient_id__in=candidate_ids, to_unit_id=gram_unit_id)
            .values_list('specific_ingredient_id', 'from_unit_id')
        ):
            units_with_path_to_grams.setdefault(c[0], set()).add(c[1])

    # ----- Pre-fetch units used in recipes for these ingredients -----
    units_used_per_ingredient = {}  # {ingredient_id: set([unit_id, ...])}
    if candidate_ids:
        ri_qs = RecipeIngredient.objects.filter(
            ingredient_id__in=candidate_ids
        ).exclude(unit_id__isnull=True)
        if scoped_recipe is not None:
            ri_qs = ri_qs.filter(recipe=scoped_recipe)
        for ing_id, unit_id in ri_qs.values_list('ingredient_id', 'unit_id').distinct():
            units_used_per_ingredient.setdefault(ing_id, set()).add(unit_id)

    # ----- Helper: does this unit have a path to grams for this ingredient? -----
    def _has_path_to_grams(unit_id, ingredient_id):
        if unit_id is None:
            return False
        if gram_unit_id and unit_id == gram_unit_id:
            return True
        if unit_id in units_with_path_to_grams.get(ingredient_id, set()):
            return True
        unit_obj = units_by_id.get(unit_id)
        if unit_obj and unit_obj.unit_type == 'weight':
            return True
        return False

    # ----- Build the queue: one entry per ingredient with missing conversions -----
    queue = []
    for ing in candidate_ingredients:
        # Build the candidate set of units to evaluate
        units_to_check = set()
        units_to_check.update(units_used_per_ingredient.get(ing.ingredient_id, set()))
        if ing.default_unit_id:
            units_to_check.add(ing.default_unit_id)

        # Find units lacking a path to grams
        missing_unit_ids = [
            u_id for u_id in units_to_check
            if not _has_path_to_grams(u_id, ing.ingredient_id)
        ]

        if not missing_unit_ids and units_to_check:
            # All units have a path — this ingredient is 'ready', skip it
            continue

        if not units_to_check:
            # Ingredient is mapped but has no default unit and no recipe usage.
            # Status would be 'missing' — but there's no specific unit for the
            # user to enter a conversion against. Surface it anyway so the
            # user knows; the card will show a "no units to set up" note.
            queue.append({
                'ingredient_id': ing.ingredient_id,
                'name': ing.name,
                'category': ing.category.name if ing.category else None,
                'fdc_description': ing.fdc_description,
                'default_unit_name': None,
                'missing_units': [],  # nothing actionable
                'has_no_units': True,
            })
            continue

        # Build the per-unit details for the card
        missing_unit_details = []
        for u_id in sorted(missing_unit_ids, key=lambda x: (units_by_id.get(x).name if units_by_id.get(x) else '')):
            u = units_by_id.get(u_id)
            if not u:
                continue
            missing_unit_details.append({
                'from_unit_id': u_id,
                'from_unit_name': u.name,
                'from_unit_abbr': u.abbreviation or '',
                'from_unit_type': u.unit_type,  # 'volume' / 'weight' / 'count' / 'other'
            })

        queue.append({
            'ingredient_id': ing.ingredient_id,
            'name': ing.name,
            'category': ing.category.name if ing.category else None,
            'fdc_description': ing.fdc_description,
            'default_unit_name': ing.default_unit.name if ing.default_unit else None,
            'missing_units': missing_unit_details,
            'has_no_units': False,
        })

    # ----- Compute progress totals -----
    # "Total in set" = total mapped ingredients in the scope.
    # "Already converted" = total in set - len(queue).
    if scoped_recipe is not None:
        total_mapped_in_scope = (
            Ingredient.objects
            .filter(fdc_id__isnull=False, ingredient_id__in=(scoped_ingredient_ids or []))
            .count()
        )
    else:
        total_mapped_in_scope = Ingredient.objects.filter(fdc_id__isnull=False).count()

    total_to_convert = len(queue)
    total_already_converted = max(0, total_mapped_in_scope - total_to_convert)

    context = {
        'queue_json': json.dumps(queue),
        'total_count': total_to_convert,                # how many in the queue right now
        'total_in_set': total_mapped_in_scope,          # denominator for progress display
        'total_converted': total_already_converted,     # numerator at page load
        'gram_unit_id': gram_unit_id,
        'scoped_recipe': scoped_recipe,
        'return_to': return_to,
    }
    return render(request, 'unit_conversions_wizard.html', context)