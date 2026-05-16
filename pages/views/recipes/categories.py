"""
Ingredient categories — admin UI + AJAX CRUD.

Owns the `IngredientCategory` lookup table: the management list view plus
add / update / usage-check / delete AJAX endpoints driven by the categories
admin UI.

Functions
---------
- categories_management : Admin list view; every category with its ingredient
                          count and ingredient-name list (used for tooltips).
- add_category          : AJAX create.
- update_category       : AJAX rename.
- check_category_usage  : AJAX usage probe (pre-delete confirmation).
- delete_category       : AJAX delete; refuses if any ingredient references it.

Auth tiers
----------
Read views (`categories_management`, `check_category_usage`) require
`auth.can_access_personal`. Mutating views (`add_category`, `update_category`,
`delete_category`) require `auth.can_edit_personal`.
"""

import json

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render

from pages.models import Ingredient, IngredientCategory


# =====================================================================
# INGREDIENT CATEGORIES
# =====================================================================

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def categories_management(request):
    """Manage ingredient categories"""
    # Get all categories sorted alphabetically
    categories = IngredientCategory.objects.all().order_by('name')

    # Get ingredient count and names for each category
    categories_with_count = []
    for category in categories:
        ingredients = Ingredient.objects.filter(category=category).order_by('name')
        ingredient_names = list(ingredients.values_list('name', flat=True))

        categories_with_count.append({
            'category': category,
            'ingredient_count': ingredients.count(),
            'ingredients': ingredient_names,  # List of ingredient names for tooltip
        })

    context = {
        'categories_with_count': categories_with_count
    }

    return render(request, 'categories_management.html', context)


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def add_category(request):
    """Add a new ingredient category"""
    if request.method == 'POST':
        data = json.loads(request.body)
        category_name = data.get('name', '').strip()

        # Validate name is not empty
        if not category_name:
            return JsonResponse({'success': False, 'error': 'Category name cannot be empty'})

        # Check for duplicate names (case-insensitive)
        duplicate = IngredientCategory.objects.filter(name__iexact=category_name).first()
        if duplicate:
            return JsonResponse({
                'success': False,
                'error': f'A category named "{category_name}" already exists'
            })

        # Create new category
        category = IngredientCategory.objects.create(name=category_name)

        return JsonResponse({
            'success': True,
            'message': 'Category added successfully',
            'category': {
                'id': category.ingredient_category_id,
                'name': category.name
            }
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def update_category(request):
    """Update category name"""
    if request.method == 'POST':
        data = json.loads(request.body)
        category_id = data.get('category_id')
        new_name = data.get('name', '').strip()

        try:
            category = IngredientCategory.objects.get(ingredient_category_id=category_id)

            # Validate name is not empty
            if not new_name:
                return JsonResponse({'success': False, 'error': 'Category name cannot be empty'})

            # Check for duplicate names (case-insensitive, excluding current category)
            duplicate = IngredientCategory.objects.filter(name__iexact=new_name).exclude(ingredient_category_id=category_id).first()
            if duplicate:
                return JsonResponse({
                    'success': False,
                    'error': f'A category named "{new_name}" already exists'
                })

            # Update category
            category.name = new_name
            category.save()

            return JsonResponse({
                'success': True,
                'message': 'Category updated successfully',
                'category': {
                    'id': category.ingredient_category_id,
                    'name': category.name
                }
            })

        except IngredientCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def check_category_usage(request):
    """Check if category is used by any ingredients"""
    if request.method == 'POST':
        data = json.loads(request.body)
        category_id = data.get('category_id')

        try:
            category = IngredientCategory.objects.get(ingredient_category_id=category_id)

            # Count ingredients using this category
            ingredient_count = Ingredient.objects.filter(category=category).count()

            # Get ingredient names (limit to 5 for display)
            ingredients = Ingredient.objects.filter(category=category)[:5]
            ingredient_names = [ing.name for ing in ingredients]

            return JsonResponse({
                'success': True,
                'usage_count': ingredient_count,
                'ingredient_names': ingredient_names,
                'can_delete': ingredient_count == 0
            })

        except IngredientCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def delete_category(request):
    """Delete category if not used by any ingredients"""
    if request.method == 'POST':
        data = json.loads(request.body)
        category_id = data.get('category_id')

        try:
            category = IngredientCategory.objects.get(ingredient_category_id=category_id)

            # Check if category is used by any ingredients
            ingredient_count = Ingredient.objects.filter(category=category).count()

            if ingredient_count > 0:
                return JsonResponse({
                    'success': False,
                    'error': f'Cannot delete - category is used by {ingredient_count} ingredient(s)'
                })

            # Safe to delete
            category_name = category.name
            category.delete()

            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted category: {category_name}'
            })

        except IngredientCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})