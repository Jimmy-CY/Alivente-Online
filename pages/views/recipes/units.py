"""
Measurement units and preparation methods — admin UI + inline-from-recipe AJAX.

This module owns everything related to the `MeasurementUnit` lookup table
(grams, ml, cups, tsp, etc.) plus a single AJAX endpoint for adding a
`PreparationMethod` (diced, minced, etc.) inline from recipe forms.

Functions
---------
- measurement_units_management : Admin list view with per-unit usage counts
                                 (recipes, ingredients, conversions).
- add_measurement_unit         : AJAX create from the units admin UI.
- update_measurement_unit      : AJAX update from the units admin UI.
- check_unit_usage             : AJAX usage-count probe (pre-delete confirmation).
- delete_measurement_unit      : AJAX delete; refuses if unit is referenced anywhere.
- add_measurement_ajax         : AJAX create from inline recipe forms (the "+ Add
                                 measurement" path next to a unit dropdown).
- add_preparation_ajax         : AJAX create a PreparationMethod from inline
                                 recipe forms.

Notes
-----
- `add_preparation_ajax` rides with units as a compromise: no dedicated
  preparations management UI exists yet, and it shares the same lookup-table
  shape as `add_measurement_ajax`. Relocate to a `preparations.py` if a full
  preparations admin UI is ever built.
- `measurement_units_management` is the only GET/render view here; it is
  gated at the read tier (`auth.can_access_personal`), matching
  `check_unit_usage`. The mutating endpoints require `auth.can_edit_personal`.
"""

import json
from collections import defaultdict

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from pages.models import (
    Ingredient,
    MeasurementUnit,
    PreparationMethod,
    RecipeIngredient,
    UnitConversion,
)


# =====================================================================
# MEASUREMENT UNITS ADMIN
# =====================================================================

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def measurement_units_management(request):
    """Admin list view: every MeasurementUnit with usage stats (recipes, ingredients, conversions)."""
    # Simple query - no annotations
    units = MeasurementUnit.objects.all().order_by('name')

    # Pre-fetch all recipe names by unit (single query)
    recipe_names_by_unit = defaultdict(list)
    recipe_data = (
        RecipeIngredient.objects
        .select_related('recipe', 'unit')
        .values('unit_id', 'recipe__recipe_name')
        .distinct()
        .order_by('recipe__recipe_name')
    )
    for item in recipe_data:
        recipe_names_by_unit[item['unit_id']].append(item['recipe__recipe_name'])

    # Pre-fetch all ingredient names by unit (single query)
    ingredient_names_by_unit = defaultdict(list)
    ingredient_data = (
        Ingredient.objects
        .filter(default_unit__isnull=False)
        .values('default_unit_id', 'name')
        .order_by('name')
    )
    for item in ingredient_data:
        ingredient_names_by_unit[item['default_unit_id']].append(item['name'])

    # Pre-fetch all conversions (single query)
    conversions_by_unit = defaultdict(list)
    from_conversions = (
        UnitConversion.objects
        .select_related('from_unit', 'to_unit')
        .all()
    )
    for conv in from_conversions:
        from_abbr = conv.from_unit.abbreviation or conv.from_unit.name
        to_abbr = conv.to_unit.abbreviation or conv.to_unit.name
        label = f"{from_abbr} → {to_abbr} (×{conv.multiplier})"
        conversions_by_unit[conv.from_unit_id].append(label)
        conversions_by_unit[conv.to_unit_id].append(label)

    # Build the final list - derive all counts from already-fetched data
    units_with_count = []
    for unit in units:
        recipes     = recipe_names_by_unit.get(unit.measurement_unit_id, [])
        ingredients = ingredient_names_by_unit.get(unit.measurement_unit_id, [])
        conversions = conversions_by_unit.get(unit.measurement_unit_id, [])

        units_with_count.append({
            'unit':             unit,
            'recipe_count':     len(recipes),
            'ingredient_count': len(ingredients),
            'conversion_count': len(conversions),
            'total_usage':      len(recipes) + len(ingredients) + len(conversions),
            'recipes':          recipes,
            'ingredients':      ingredients,
            'conversions':      conversions,
        })

    context = {
        'units_with_count': units_with_count,
        'unit_types':        MeasurementUnit.UNIT_TYPE_CHOICES,
    }

    return render(request, 'measurement_units_management.html', context)


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def add_measurement_unit(request):
    """Add a new measurement unit."""
    if request.method == 'POST':
        data = json.loads(request.body)
        unit_name = data.get('name', '').strip()
        name_plural = data.get('name_plural', '').strip()
        abbreviation = data.get('abbreviation', '').strip()
        abbreviation_plural = data.get('abbreviation_plural', '').strip()
        unit_type = data.get('unit_type', 'other')

        # Validate name is not empty
        if not unit_name:
            return JsonResponse({'success': False, 'error': 'Unit name cannot be empty'})

        # Check for duplicate names (case-insensitive)
        duplicate = MeasurementUnit.objects.filter(name__iexact=unit_name).first()
        if duplicate:
            return JsonResponse({
                'success': False,
                'error': f'A unit named "{unit_name}" already exists'
            })

        # Check for duplicate abbreviations if provided (case-insensitive)
        if abbreviation:
            duplicate_abbr = MeasurementUnit.objects.filter(abbreviation__iexact=abbreviation).first()
            if duplicate_abbr:
                return JsonResponse({
                    'success': False,
                    'error': f'A unit with abbreviation "{abbreviation}" already exists'
                })

        # Create new unit with plural fields
        unit = MeasurementUnit.objects.create(
            name=unit_name,
            name_plural=name_plural if name_plural else None,
            abbreviation=abbreviation if abbreviation else None,
            abbreviation_plural=abbreviation_plural if abbreviation_plural else None,
            unit_type=unit_type
        )

        return JsonResponse({
            'success': True,
            'message': 'Measurement unit added successfully',
            'unit': {
                'id': unit.measurement_unit_id,
                'name': unit.name,
                'name_plural': unit.name_plural,
                'abbreviation': unit.abbreviation,
                'abbreviation_plural': unit.abbreviation_plural,
                'unit_type': unit.unit_type,
                'unit_type_display': unit.get_unit_type_display()
            }
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def update_measurement_unit(request):
    """Update measurement unit name, abbreviation, and type."""
    if request.method == 'POST':
        data = json.loads(request.body)
        unit_id = data.get('unit_id')
        new_name = data.get('name', '').strip()
        new_name_plural = data.get('name_plural', '').strip()
        new_abbreviation = data.get('abbreviation', '').strip()
        new_abbreviation_plural = data.get('abbreviation_plural', '').strip()
        new_unit_type = data.get('unit_type', 'other')

        try:
            unit = MeasurementUnit.objects.get(measurement_unit_id=unit_id)

            # Validate name is not empty
            if not new_name:
                return JsonResponse({'success': False, 'error': 'Unit name cannot be empty'})

            # Check for duplicate names (case-insensitive, excluding current unit)
            duplicate = MeasurementUnit.objects.filter(name__iexact=new_name).exclude(measurement_unit_id=unit_id).first()
            if duplicate:
                return JsonResponse({
                    'success': False,
                    'error': f'A unit named "{new_name}" already exists'
                })

            # Check for duplicate abbreviations if provided (case-insensitive, excluding current unit)
            if new_abbreviation:
                duplicate_abbr = MeasurementUnit.objects.filter(abbreviation__iexact=new_abbreviation).exclude(measurement_unit_id=unit_id).first()
                if duplicate_abbr:
                    return JsonResponse({
                        'success': False,
                        'error': f'A unit with abbreviation "{new_abbreviation}" already exists'
                    })

            # Update unit with plural fields
            unit.name = new_name
            unit.name_plural = new_name_plural if new_name_plural else None
            unit.abbreviation = new_abbreviation if new_abbreviation else None
            unit.abbreviation_plural = new_abbreviation_plural if new_abbreviation_plural else None
            unit.unit_type = new_unit_type
            unit.save()

            return JsonResponse({
                'success': True,
                'message': 'Measurement unit updated successfully',
                'unit': {
                    'id': unit.measurement_unit_id,
                    'name': unit.name,
                    'name_plural': unit.name_plural,
                    'abbreviation': unit.abbreviation,
                    'abbreviation_plural': unit.abbreviation_plural,
                    'unit_type': unit.unit_type,
                    'unit_type_display': unit.get_unit_type_display()
                }
            })

        except MeasurementUnit.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Measurement unit not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def check_unit_usage(request):
    """Check if measurement unit is used in recipes, ingredients, or conversions."""
    if request.method == 'POST':
        data = json.loads(request.body)
        unit_id = data.get('unit_id')

        try:
            unit = MeasurementUnit.objects.get(measurement_unit_id=unit_id)

            # Count usage in recipes
            recipe_count = RecipeIngredient.objects.filter(unit=unit).count()

            # Count usage in ingredients (as default unit)
            ingredient_count = Ingredient.objects.filter(default_unit=unit).count()

            # Count usage in unit conversions
            conversion_count = UnitConversion.objects.filter(
                Q(from_unit=unit) | Q(to_unit=unit)
            ).count()

            total_usage = recipe_count + ingredient_count + conversion_count

            # Get some example names (limit to 5 total)
            usage_examples = []

            if recipe_count > 0:
                recipes = RecipeIngredient.objects.filter(unit=unit).select_related('recipe')[:3]
                for ri in recipes:
                    usage_examples.append(f"Recipe: {ri.recipe.recipe_name}")

            if ingredient_count > 0 and len(usage_examples) < 5:
                ingredients = Ingredient.objects.filter(default_unit=unit)[:2]
                for ing in ingredients:
                    usage_examples.append(f"Ingredient: {ing.name}")

            return JsonResponse({
                'success': True,
                'total_usage': total_usage,
                'recipe_count': recipe_count,
                'ingredient_count': ingredient_count,
                'conversion_count': conversion_count,
                'usage_examples': usage_examples,
                'can_delete': total_usage == 0
            })

        except MeasurementUnit.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Measurement unit not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def delete_measurement_unit(request):
    """Delete measurement unit if not used anywhere."""
    if request.method == 'POST':
        data = json.loads(request.body)
        unit_id = data.get('unit_id')

        try:
            unit = MeasurementUnit.objects.get(measurement_unit_id=unit_id)

            # Check if unit is used anywhere
            recipe_count = RecipeIngredient.objects.filter(unit=unit).count()
            ingredient_count = Ingredient.objects.filter(default_unit=unit).count()
            conversion_count = UnitConversion.objects.filter(
                Q(from_unit=unit) | Q(to_unit=unit)
            ).count()

            total_usage = recipe_count + ingredient_count + conversion_count

            if total_usage > 0:
                usage_details = []
                if recipe_count > 0:
                    usage_details.append(f'{recipe_count} recipe(s)')
                if ingredient_count > 0:
                    usage_details.append(f'{ingredient_count} ingredient(s)')
                if conversion_count > 0:
                    usage_details.append(f'{conversion_count} conversion(s)')

                return JsonResponse({
                    'success': False,
                    'error': f'Cannot delete - unit is used in {", ".join(usage_details)}'
                })

            # Safe to delete
            unit_name = unit.name
            unit.delete()

            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted measurement unit: {unit_name}'
            })

        except MeasurementUnit.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Measurement unit not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# =====================================================================
# INLINE AJAX ENDPOINTS (called from recipe forms)
# =====================================================================

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_measurement_ajax(request):
    """Add new measurement unit via AJAX (inline from recipe forms)."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        name_plural = data.get('name_plural', '').strip()
        abbreviation = data.get('abbreviation', '').strip()
        abbreviation_plural = data.get('abbreviation_plural', '').strip()
        unit_type = data.get('unit_type', 'other')

        if not name:
            return JsonResponse({'success': False, 'message': 'Name is required'})

        # Check if already exists
        if MeasurementUnit.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'message': 'Measurement already exists'})

        # Check for duplicate abbreviations if provided
        if abbreviation:
            if MeasurementUnit.objects.filter(abbreviation__iexact=abbreviation).exists():
                return JsonResponse({'success': False, 'message': f'A unit with abbreviation "{abbreviation}" already exists'})

        # Create new measurement with all fields
        measurement = MeasurementUnit.objects.create(
            name=name,
            name_plural=name_plural if name_plural else None,
            abbreviation=abbreviation if abbreviation else None,
            abbreviation_plural=abbreviation_plural if abbreviation_plural else None,
            unit_type=unit_type
        )

        return JsonResponse({
            'success': True,
            'message': 'Measurement added successfully',
            'measurement_id': measurement.measurement_unit_id,
            'name': measurement.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_preparation_ajax(request):
    """Add new preparation method via AJAX (inline from recipe forms)."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip().lower()

        if not name:
            return JsonResponse({'success': False, 'message': 'Name is required'})

        # Check if already exists
        if PreparationMethod.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'message': 'Preparation method already exists'})

        # Create new preparation method
        preparation = PreparationMethod.objects.create(name=name)

        return JsonResponse({
            'success': True,
            'message': 'Preparation method added successfully',
            'preparation_id': preparation.preparation_method_id,
            'name': preparation.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})