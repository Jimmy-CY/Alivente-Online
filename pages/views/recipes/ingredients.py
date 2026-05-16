"""
Ingredients — management AJAX endpoints + inline-from-recipe create.

Owns the `Ingredient` mutation/lookup AJAX surface driven by the ingredients
admin UI, plus a single endpoint for adding an ingredient inline from recipe
forms. There is no GET/render list view here — the ingredients page itself is
served by the recipe-management templates elsewhere; this module is purely the
mutation + usage-probe API.

Functions
---------
- check_ingredient_usage : AJAX usage probe (recipe count; pre-delete confirmation).
- delete_ingredient      : AJAX delete; refuses if the ingredient is used in any recipe.
- update_ingredient_full : AJAX update of name / category / shopping unit.
- add_ingredient_ajax    : AJAX create from inline recipe forms (the "+ Add
                           ingredient" path next to an ingredient dropdown).

Auth tiers
----------
`check_ingredient_usage` is read-tier (`auth.can_access_personal`). The
mutating endpoints (`delete_ingredient`, `update_ingredient_full`,
`add_ingredient_ajax`) require `auth.can_edit_personal`.
"""

import json

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from pages.models import (
    Ingredient,
    IngredientCategory,
    MeasurementUnit,
    RecipeIngredient,
)


# =====================================================================
# INGREDIENT MANAGEMENT (AJAX)
# =====================================================================

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def check_ingredient_usage(request):
    """Check if ingredient is used in any recipes"""
    if request.method == 'POST':
        data = json.loads(request.body)
        ingredient_id = data.get('ingredient_id')

        try:
            ingredient = Ingredient.objects.get(ingredient_id=ingredient_id)

            # Count recipes using this ingredient
            usage_count = RecipeIngredient.objects.filter(ingredient=ingredient).count()

            # Get recipe names (limit to 5 for display)
            recipes = RecipeIngredient.objects.filter(ingredient=ingredient).select_related('recipe')[:5]
            recipe_names = [ri.recipe.recipe_name for ri in recipes]

            return JsonResponse({
                'success': True,
                'usage_count': usage_count,
                'recipe_names': recipe_names,
                'can_delete': usage_count == 0
            })

        except Ingredient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ingredient not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def delete_ingredient(request):
    """Delete ingredient if not used in any recipes"""
    if request.method == 'POST':
        data = json.loads(request.body)
        ingredient_id = data.get('ingredient_id')

        try:
            ingredient = Ingredient.objects.get(ingredient_id=ingredient_id)

            # Check if ingredient is used in any recipes
            usage_count = RecipeIngredient.objects.filter(ingredient=ingredient).count()

            if usage_count > 0:
                return JsonResponse({
                    'success': False,
                    'error': f'Cannot delete - ingredient is used in {usage_count} recipe(s)'
                })

            # Safe to delete
            ingredient_name = ingredient.name
            ingredient.delete()

            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted ingredient: {ingredient_name}'
            })

        except Ingredient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ingredient not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def update_ingredient_full(request):
    """Update ingredient name, category, and shopping unit"""
    if request.method == 'POST':
        data = json.loads(request.body)
        ingredient_id = data.get('ingredient_id')
        new_name = data.get('name', '').strip()
        category_id = data.get('category_id')
        unit_id = data.get('unit_id')

        try:
            ingredient = Ingredient.objects.get(ingredient_id=ingredient_id)

            # Validate name is not empty
            if not new_name:
                return JsonResponse({'success': False, 'error': 'Ingredient name cannot be empty'})

            # Check for duplicate names (case-insensitive, excluding current ingredient)
            duplicate = Ingredient.objects.filter(name__iexact=new_name).exclude(ingredient_id=ingredient_id).first()
            if duplicate:
                return JsonResponse({
                    'success': False,
                    'error': f'An ingredient named "{new_name}" already exists'
                })

            # Validate category
            if not category_id:
                return JsonResponse({'success': False, 'error': 'Category must be selected'})

            try:
                category = IngredientCategory.objects.get(ingredient_category_id=category_id)
            except IngredientCategory.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid category'})

            # Validate unit (optional - can be None)
            unit = None
            if unit_id:
                try:
                    unit = MeasurementUnit.objects.get(measurement_unit_id=unit_id)
                except MeasurementUnit.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Invalid unit'})

            # Update ingredient
            ingredient.name = new_name
            ingredient.category = category
            ingredient.default_unit = unit
            ingredient.save()

            return JsonResponse({
                'success': True,
                'message': 'Ingredient updated successfully',
                'ingredient': {
                    'name': ingredient.name,
                    'category_id': ingredient.category.ingredient_category_id,
                    'category_name': ingredient.category.name,
                    'unit_id': ingredient.default_unit.measurement_unit_id if ingredient.default_unit else None,
                    'unit_name': ingredient.default_unit.name if ingredient.default_unit else None
                }
            })

        except Ingredient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ingredient not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# =====================================================================
# INLINE AJAX ENDPOINT (called from recipe forms)
# =====================================================================

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_ingredient_ajax(request):
    """Add new ingredient via AJAX (inline from recipe forms)."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        category_id = data.get('category_id')
        shopping_unit_id = data.get('shopping_unit_id')  # NEW

        if not name:
            return JsonResponse({'success': False, 'message': 'Ingredient name is required'})

        if not shopping_unit_id:
            return JsonResponse({'success': False, 'message': 'Shopping unit is required'})

        # Check if already exists
        if Ingredient.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'message': 'Ingredient already exists'})

        # Create ingredient with category AND shopping unit
        ingredient = Ingredient.objects.create(
            name=name,
            category_id=category_id if category_id else None,
            default_unit_id=shopping_unit_id  # NEW: Set shopping unit
        )

        return JsonResponse({
            'success': True,
            'ingredient_id': ingredient.ingredient_id,
            'name': ingredient.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})