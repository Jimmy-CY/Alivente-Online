"""
Recipe CRUD and management views.

The core recipe lifecycle: book-detail JSON, list/manage (filters, A-Z,
pagination, nutrition sort, delete), document upload/merge, duplicate,
view, create, edit.

Functions
---------
- recipe_book_detail     : JSON recipe detail for the book view. Read-tier.
- recipe_management      : Recipe list w/ multi-select filters, A-Z,
                           pagination, nutrition sort; also handles the
                           POST delete action. Read-tier (the delete
                           branch additionally checks can_edit_recipes).
- recipe_manage_document : Upload / replace / merge / delete a recipe
                           document (POST). Edit-tier.
- duplicate_recipe       : Deep-copy a recipe + related rows (POST).
                           Edit-tier.
- view_recipe            : Recipe detail page. Read-tier.
- create_recipe          : Create a recipe (GET form / POST save).
                           Edit-tier.
- edit_recipe            : Edit a recipe (GET form / POST save). Edit-tier.

Auth tiers
----------
Read-tier -> auth.can_access_recipes
Edit-tier -> auth.can_edit_recipes

Cross-module imports (homes verified via grep + manage.py check)
----------------------------------------------------------------
  pages.utils : convert_to_pdf, is_pdf, merge_pdfs, merge_pdfs_from_bytes
                Project-level PDF utilities. Absolute import, matching the
                existing `from ..utils import ...` usage in expenses.py and
                the pre-split main.py (depth-independent, like pages.signals).
  ._helpers   : convert_to_decimal, format_quantity,
                get_or_create_ingredient, get_or_create_preparation,
                get_or_create_unit, get_preferred_weight_conversion
  .nutrition  : recipe_has_any_mapped_ingredient

Deliberate exception to import-hoisting
---------------------------------------
`from pages.signals import _recalculate_cache_for_recipe` is kept INLINE
inside create_recipe / edit_recipe (NOT hoisted to module top). The
original code imported it lazily to avoid a views <-> signals circular
import; hoisting it could break startup. Only the relative path was
corrected for the new package depth: in main.py `..signals` resolved to
`pages.signals`; from this deeper package that same relative form would
resolve to the non-existent `pages.views.signals`, so it is now the
absolute `pages.signals`.

Encoding note (Phase 11a)
-------------------------
7 comment-only mojibake glyphs (mangled em/en-dashes in `#` comments of
recipe_management / recipe_manage_document / create_recipe / edit_recipe)
were replaced with ASCII " - ". No code or behavioral string was touched.
Inline imports (json/transaction/traceback) hoisted per the normalization
standard, except the deliberate pages.signals case above. 100% ASCII.
"""

import json
import os
import string
import traceback
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from pages.models import (
    CookingCalculation,
    CustomProtein,
    Ingredient,
    IngredientCategory,
    MeasurementUnit,
    PreparationMethod,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
    RecipeIngredient,
    RecipeIngredientText,
    RecipeInstruction,
    UnitConversion,
)
from pages.utils import (
    convert_to_pdf,
    is_pdf,
    merge_pdfs,
    merge_pdfs_from_bytes,
)

from ._helpers import (
    convert_to_decimal,
    format_quantity,
    get_or_create_ingredient,
    get_or_create_preparation,
    get_or_create_unit,
    get_preferred_weight_conversion,
)
from .nutrition import recipe_has_any_mapped_ingredient


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def recipe_book_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
    ingredients = recipe.recipe_ingredients.select_related(
        'ingredient', 'unit', 'preparation'
    ).order_by('ingredient_group', 'ingredient_order')
    instructions = recipe.instructions.all().order_by('step_number')

    def get_weight_equivalent(ing):
        """Return weight equivalent string or None"""
        if not ing.unit:
            return None
        if ing.unit.unit_type == 'weight':
            return None
        try:
            amount = float(ing.amount) if ing.amount else 0
            if amount <= 0:
                return None
            conversion = get_preferred_weight_conversion(ing.unit, ing.ingredient)
            if not conversion:
                return None
            weight_amount = round(amount * float(conversion.multiplier), 1)
            if weight_amount == int(weight_amount):
                weight_amount = int(weight_amount)
            if weight_amount <= 0:
                return None
            weight_unit = conversion.to_unit.abbreviation or conversion.to_unit.name
            # If result is kg but less than 1, convert to grams
            if weight_unit == 'kg' and weight_amount < 1:
                weight_amount = round(weight_amount * 1000)
                weight_unit = 'g'
            return f"{weight_amount}{weight_unit}"
        except Exception:
            return None

    data = {
        'recipe_name': recipe.recipe_name,
        'prep_time': recipe.prep_time,
        'cook_time': recipe.cook_time,
        'servings': recipe.servings,
        'difficulty_level': recipe.difficulty_level,
        'author': recipe.author,
        'is_vegetarian': recipe.is_vegetarian,
        'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,
        'courses': [c.name for c in recipe.courses.all()],
        'categories': [c.name for c in recipe.categories.all()],
        'proteins': [p.name for p in recipe.proteins.all()],
        'ingredients': [
            {
                'amount': str(ing.get_amount_display()),
                'amount_raw': float(ing.amount) if ing.amount else 0,
                'unit': ing.unit.abbreviation if ing.unit and ing.unit.abbreviation else (ing.unit.name if ing.unit else ''),
                'ingredient': ing.ingredient.name,
                'preparation': ing.preparation.name if ing.preparation else '',
                'group': ing.ingredient_group or '',
                'weight_equivalent': get_weight_equivalent(ing)
            }
            for ing in ingredients
        ],
        'instructions': [
            {
                'step_number': inst.step_number,
                'instruction_text': inst.instruction_text,
                'group': inst.instruction_group or ''
            }
            for inst in instructions
        ]
    }
    return JsonResponse(data)


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def recipe_management(request):
    """Recipe management page with multi-select filtering, A-Z filter, pagination, and nutrition sort."""
    # Handle delete action
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        if not request.user.has_perm('auth.can_edit_recipes'):
            messages.error(request, "You don't have permission to delete recipes.")
            return redirect('recipe_management')

        recipe_id = request.POST.get('recipe_id')
        try:
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            recipe_name = recipe.recipe_name
            recipe.delete()
            messages.success(request, f'Recipe "{recipe_name}" has been deleted successfully.')
        except Recipe.DoesNotExist:
            messages.error(request, 'Recipe not found.')
        return redirect('recipe_management')

    # Get all recipes with prefetch
    recipes = Recipe.objects.all().prefetch_related('courses', 'categories', 'proteins')

    # Get filter parameters
    search_query = request.GET.get('search', '')
    search_type = request.GET.get('search_type', 'name')
    show_favourites = request.GET.get('favourites') == '1'

    # Get current user's favourites as a set of recipe IDs for fast lookup
    user_favourites = set(
        RecipeFavourite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    )

    selected_courses = request.GET.getlist('course')
    selected_categories = request.GET.getlist('category')
    selected_proteins = request.GET.getlist('protein')
    selected_authors = request.GET.getlist('author')
    selected_letter = request.GET.get('letter', '')

    # === Nutrition sort params (Step 3) ===
    NUTRITION_SORT_FIELDS = {
        'calories': 'nutrition_cache__calories_per_100g',
        'protein':  'nutrition_cache__protein_per_100g',
        'carbs':    'nutrition_cache__carbs_per_100g',
        'fat':      'nutrition_cache__fat_per_100g',
    }
    nutrition_sort = request.GET.get('nutrition_sort', '')
    nutrition_order = request.GET.get('nutrition_order', 'desc')
    if nutrition_order not in ('asc', 'desc'):
        nutrition_order = 'desc'
    if nutrition_sort not in NUTRITION_SORT_FIELDS:
        nutrition_sort = ''  # ignore unknown values silently

    # Apply filters
    if search_query:
        if search_type == 'ingredient':
            recipes = recipes.filter(
                recipe_ingredients__ingredient__name__icontains=search_query
            )
        else:
            recipes = recipes.filter(recipe_name__icontains=search_query)

    if selected_courses:
        recipes = recipes.filter(courses__recipe_course_id__in=selected_courses)

    if selected_categories:
        recipes = recipes.filter(categories__recipe_category_id__in=selected_categories)

    if selected_proteins:
        if 'vegetarian' in selected_proteins:
            protein_ids = [p for p in selected_proteins if p != 'vegetarian']
            if protein_ids:
                recipes = recipes.filter(
                    Q(is_vegetarian=True) |
                    Q(proteins__custom_protein_id__in=protein_ids)
                )
            else:
                recipes = recipes.filter(is_vegetarian=True)
        else:
            recipes = recipes.filter(proteins__custom_protein_id__in=selected_proteins)

    if selected_authors:
        recipes = recipes.filter(author__in=selected_authors)

    if show_favourites:
        recipes = recipes.filter(favourited_by__user=request.user)

    recipes = recipes.distinct()

    # === Nutrition sort branch (Step 3) ===
    # If a nutrient was picked, switch the queryset over to:
    #   - join the nutrition_cache table via select_related
    #   - filter to recipes whose cache is_complete=True (so the ranking is trustworthy)
    #   - order by the chosen per-100g column
    # Also count how many recipes were hidden (the "X hidden - finish mapping" nudge).
    hidden_by_nutrition_sort = 0
    if nutrition_sort:
        sort_field = NUTRITION_SORT_FIELDS[nutrition_sort]
        order_prefix = '' if nutrition_order == 'asc' else '-'

        # Count BEFORE narrowing - that's the total of recipes matching all
        # other filters. The hidden count is total minus complete count.
        total_for_filter = recipes.count()

        recipes = (
            recipes
            .select_related('nutrition_cache')
            .filter(nutrition_cache__is_complete=True)
            .order_by(f'{order_prefix}{sort_field}', 'recipe_name')
        )

        complete_for_filter = recipes.count()
        hidden_by_nutrition_sort = max(0, total_for_filter - complete_for_filter)
    else:
        # Default ordering when no nutrition sort is active
        recipes = recipes.order_by('recipe_name')

    # Calculate available letters BEFORE applying letter filter
    all_letters = list(string.ascii_uppercase)
    available_letters = set()

    for recipe in recipes:
        if recipe.recipe_name:
            first_letter = recipe.recipe_name[0].upper()
            if first_letter.isalpha():
                available_letters.add(first_letter)

    # Create letter data for template
    letter_data = []
    for letter in all_letters:
        letter_data.append({
            'letter': letter,
            'available': letter in available_letters
        })

    # NOW apply letter filter
    if selected_letter:
        recipes = recipes.filter(recipe_name__istartswith=selected_letter)

    # Handle AJAX request for Load More
    page = request.GET.get('page', 1)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Pagination: 48 recipes per page
    paginator = Paginator(recipes, 48)
    page_obj = paginator.get_page(page)

    if is_ajax:
        recipes_data = []
        for recipe in page_obj:
            # Nutrition values for the inline badge (only when sort is active)
            nutrition_values = None
            if nutrition_sort:
                cache = getattr(recipe, 'nutrition_cache', None)
                if cache:
                    nutrition_values = {
                        'calories': float(cache.calories_per_100g) if cache.calories_per_100g is not None else None,
                        'protein':  float(cache.protein_per_100g)  if cache.protein_per_100g  is not None else None,
                        'carbs':    float(cache.carbs_per_100g)    if cache.carbs_per_100g    is not None else None,
                        'fat':      float(cache.fat_per_100g)      if cache.fat_per_100g      is not None else None,
                    }

            recipes_data.append({
                'recipe_id': recipe.recipe_id,
                'recipe_name': recipe.recipe_name,
                'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,
                'prep_time': recipe.prep_time,
                'cook_time': recipe.cook_time,
                'servings': recipe.servings,
                'difficulty_level': recipe.difficulty_level,
                'is_vegetarian': recipe.is_vegetarian,
                'author': recipe.author,
                'courses': [{'name': c.name} for c in recipe.courses.all()],
                'categories': [{'name': c.name} for c in recipe.categories.all()],
                'proteins': [{'name': p.name} for p in recipe.proteins.all()],
                'is_favourite': recipe.recipe_id in user_favourites,
                'nutrition_values': nutrition_values,
            })

        return JsonResponse({
            'recipes': recipes_data,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'total_count': paginator.count,
        })

    # Get all for filter dropdowns
    courses = RecipeCourse.objects.all().order_by('name')
    categories = RecipeCategory.objects.all().order_by('name')
    proteins = CustomProtein.objects.all().order_by('name')

    authors = [
        {'value': 'General', 'name': 'General'},
        {'value': 'Demetri & Angy', 'name': 'Demetri & Angy'},
        {'value': 'Erene', 'name': 'Erene'},
        {'value': 'Alexandra', 'name': 'Alexandra'},
    ]

    # Serialize filtered recipes for book view (use already-filtered queryset)
    all_recipes_for_book = []
    for r in recipes:
        nutrition_values = None
        if nutrition_sort:
            cache = getattr(r, 'nutrition_cache', None)
            if cache:
                nutrition_values = {
                    'calories': float(cache.calories_per_100g) if cache.calories_per_100g is not None else None,
                    'protein':  float(cache.protein_per_100g)  if cache.protein_per_100g  is not None else None,
                    'carbs':    float(cache.carbs_per_100g)    if cache.carbs_per_100g    is not None else None,
                    'fat':      float(cache.fat_per_100g)      if cache.fat_per_100g      is not None else None,
                }
        all_recipes_for_book.append({
            'recipe_id': r.recipe_id,
            'recipe_name': r.recipe_name,
            'recipe_image': r.recipe_image.url if r.recipe_image else None,
            'prep_time': r.prep_time,
            'cook_time': r.cook_time,
            'servings': r.servings,
            'difficulty_level': r.difficulty_level,
            'is_vegetarian': r.is_vegetarian,
            'author': r.author,
            'courses': [c.name for c in r.courses.all()],
            'categories': [c.name for c in r.categories.all()],
            'proteins': [p.name for p in r.proteins.all()],
            'nutrition_values': nutrition_values,
        })

    context = {
        'recipes': page_obj,
        'total_recipe_count': paginator.count,
        'show_favourites': show_favourites,
        'user_favourites': user_favourites,
        'courses': courses,
        'categories': categories,
        'proteins': proteins,
        'authors': authors,
        'search_query': search_query,
        'search_type': search_type,
        'selected_courses': selected_courses,
        'selected_categories': selected_categories,
        'selected_proteins': selected_proteins,
        'selected_authors': selected_authors,
        'selected_letter': selected_letter,
        'letter_data': letter_data,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'ingredient_categories': IngredientCategory.objects.prefetch_related('ingredient_set').all().order_by('name'),
        'all_recipes_for_book': json.dumps(all_recipes_for_book),
        # Step 3 - nutrition sort
        'nutrition_sort': nutrition_sort,
        'nutrition_order': nutrition_order,
        'hidden_by_nutrition_sort': hidden_by_nutrition_sort,
    }

    return render(request, 'recipe_management.html', context)


@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
@require_POST
def recipe_manage_document(request):
    """Handle document upload, replacement, merging and deletion for recipes"""
    if request.method == 'POST':
        action = request.POST.get('action')
        document_action = request.POST.get('document_action')
        recipe_id = request.POST.get('recipe_id')

        if not recipe_id:
            messages.error(request, 'No recipe selected')
            return redirect('recipe_management')

        try:
            recipe = get_object_or_404(Recipe, pk=recipe_id)

            if action == 'delete_document':
                if recipe.recipe_document:
                    if recipe.recipe_document.storage.exists(recipe.recipe_document.name):
                        recipe.recipe_document.storage.delete(recipe.recipe_document.name)
                    Recipe.objects.filter(pk=recipe_id).update(recipe_document='')
                    messages.success(request, f'Document deleted successfully for "{recipe.recipe_name}"!')
                else:
                    messages.warning(request, 'No document found to delete.')

            elif action == 'upload':
                if 'recipe_document' in request.FILES:
                    uploaded_file = request.FILES['recipe_document']

                    # Validate file size (5MB limit)
                    if uploaded_file.size > 5 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 5MB limit.')
                        return redirect('recipe_management')

                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF, JPG, PNG, Excel, or Word files only.')
                        return redirect('recipe_management')

                    if document_action == 'add_to_existing' and recipe.recipe_document:
                        # Merge - existing must be PDF
                        if not is_pdf(recipe.recipe_document):
                            messages.error(request, 'Cannot merge: Existing document is not a PDF. Please use Replace instead.')
                            return redirect('recipe_management')

                        try:
                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                            merged_pdf = merge_pdfs(recipe.recipe_document, pdf_content)

                            original_name = os.path.splitext(os.path.basename(recipe.recipe_document.name))[0]
                            new_filename = f"{original_name}_merged_{uuid.uuid4().hex[:8]}.pdf"

                            if recipe.recipe_document.storage.exists(recipe.recipe_document.name):
                                recipe.recipe_document.storage.delete(recipe.recipe_document.name)
                            Recipe.objects.filter(pk=recipe_id).update(recipe_document='')
                            recipe = Recipe.objects.get(pk=recipe_id)

                            recipe.recipe_document.save(new_filename, merged_pdf, save=True)
                            messages.success(request, f'Documents merged successfully for "{recipe.recipe_name}"!')
                        except ValueError as e:
                            messages.error(request, f'Error: {str(e)}')
                        except Exception as e:
                            messages.error(request, f'Error merging documents: {str(e)}')

                    else:
                        # Replace or new upload
                        if recipe.recipe_document:
                            if recipe.recipe_document.storage.exists(recipe.recipe_document.name):
                                recipe.recipe_document.storage.delete(recipe.recipe_document.name)
                            Recipe.objects.filter(pk=recipe_id).update(recipe_document='')
                            recipe = Recipe.objects.get(pk=recipe_id)

                        try:
                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                            name_part = os.path.splitext(pdf_filename)[0]
                            unique_filename = f"{name_part}_{uuid.uuid4().hex[:8]}.pdf"
                            recipe.recipe_document.save(unique_filename, pdf_content, save=True)

                            if file_extension != '.pdf':
                                messages.success(request, f'Document uploaded and converted to PDF for "{recipe.recipe_name}"!')
                            else:
                                messages.success(request, f'Document uploaded successfully for "{recipe.recipe_name}"!')
                        except Exception as e:
                            messages.error(request, f'Error processing document: {str(e)}')
                else:
                    messages.error(request, 'Please select a file to upload.')

        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')

    return redirect('recipe_management')


@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
@require_POST
def duplicate_recipe(request, recipe_id):
    """Duplicate a recipe with all its ingredients and related data"""

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        # Get the original recipe
        original_recipe = Recipe.objects.get(recipe_id=recipe_id)

        with transaction.atomic():
            # Store the original recipe ID
            original_id = original_recipe.recipe_id

            # Store many-to-many relationships before modifying
            original_courses = list(original_recipe.courses.all())
            original_categories = list(original_recipe.categories.all())
            original_proteins = list(original_recipe.proteins.all())

            # Get related data
            original_recipe_ingredients = list(RecipeIngredient.objects.filter(recipe_id=original_id))
            original_text_ingredients = list(RecipeIngredientText.objects.filter(recipe_id=original_id))
            original_instructions = list(RecipeInstruction.objects.filter(recipe_id=original_id))

            # Create new recipe by setting pk to None
            original_recipe.pk = None
            original_recipe.recipe_id = None  # Let it auto-generate
            original_recipe.recipe_name = f"{original_recipe.recipe_name} (Copy)"
            original_recipe.save()

            new_recipe_id = original_recipe.recipe_id
            new_recipe_name = original_recipe.recipe_name

            # Copy many-to-many relationships
            original_recipe.courses.set(original_courses)
            original_recipe.categories.set(original_categories)
            original_recipe.proteins.set(original_proteins)

            # Bulk create structured recipe ingredients
            new_recipe_ingredients = [
                RecipeIngredient(
                    recipe=original_recipe,
                    ingredient=ri.ingredient,
                    amount=ri.amount,
                    unit=ri.unit,
                    preparation=ri.preparation,
                    preparation_note=ri.preparation_note,
                    ingredient_order=ri.ingredient_order,
                    ingredient_group=ri.ingredient_group,
                )
                for ri in original_recipe_ingredients
            ]
            if new_recipe_ingredients:
                RecipeIngredient.objects.bulk_create(new_recipe_ingredients)

            # Bulk create text-based ingredients
            new_text_ingredients = [
                RecipeIngredientText(
                    recipe=original_recipe,
                    ingredient_text=ti.ingredient_text,
                    ingredient_group=ti.ingredient_group,
                    order=ti.order,
                )
                for ti in original_text_ingredients
            ]
            if new_text_ingredients:
                RecipeIngredientText.objects.bulk_create(new_text_ingredients)

            # Bulk create instructions
            new_instructions = [
                RecipeInstruction(
                    recipe=original_recipe,
                    step_number=inst.step_number,
                    instruction_text=inst.instruction_text,
                    instruction_group=inst.instruction_group,
                    time_estimate=inst.time_estimate,
                    step_image=inst.step_image,
                )
                for inst in original_instructions
            ]
            if new_instructions:
                RecipeInstruction.objects.bulk_create(new_instructions)

        return JsonResponse({
            'success': True,
            'new_recipe_id': new_recipe_id,
            'new_recipe_name': new_recipe_name
        })

    except Recipe.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Recipe not found'
        }, status=404)

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================
# VIEW: View Recipe
# ============================================

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def view_recipe(request, recipe_id):
    """View recipe detail page"""

    # Prefetch all related objects in one go to avoid N+1 queries
    recipe = get_object_or_404(
        Recipe.objects.prefetch_related(
            'courses',
            'categories',
            'proteins',
        ).select_related(),
        recipe_id=recipe_id
    )

    # Get ingredients with all related data in a single query
    ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related(
        'ingredient',
        'ingredient__category',
        'unit',
        'preparation',
    ).order_by('ingredient_group', 'ingredient_order')

    # Pre-fetch all unit conversions needed for weight equivalents in bulk
    # to avoid one DB hit per ingredient inside the loop
    units_needed = set()
    for ing in ingredients:
        if ing.unit and ing.unit.unit_type != 'weight' and ing.amount:
            units_needed.add(ing.unit_id)

    # Bulk fetch all relevant conversions once
    conversions_qs = UnitConversion.objects.filter(
        from_unit_id__in=units_needed
    ).select_related('from_unit', 'to_unit', 'specific_ingredient').order_by('specific_ingredient', 'from_unit')

    # Build a lookup dict: (from_unit_id, specific_ingredient_id) -> conversion
    #                   and (from_unit_id, None) -> conversion as fallback
    conversion_map = {}
    for conv in conversions_qs:
        key_specific = (conv.from_unit_id, conv.specific_ingredient_id)
        key_generic  = (conv.from_unit_id, None)
        if key_specific not in conversion_map:
            conversion_map[key_specific] = conv
        if conv.specific_ingredient_id is None and key_generic not in conversion_map:
            conversion_map[key_generic] = conv

    # Format amounts and compute weight equivalents from the in-memory map
    for ing in ingredients:
        ing.formatted_amount = format_quantity(ing.amount)
        ing.weight_equivalent = None
        if ing.unit and ing.unit.unit_type != 'weight':
            try:
                amount = float(ing.amount) if ing.amount else 0
                if amount > 0:
                    # Look up specific ingredient first, then generic fallback
                    conversion = (
                        conversion_map.get((ing.unit_id, ing.ingredient_id)) or
                        conversion_map.get((ing.unit_id, None))
                    )
                    if conversion:
                        weight_amount = round(amount * float(conversion.multiplier), 1)
                        if weight_amount == int(weight_amount):
                            weight_amount = int(weight_amount)
                        if weight_amount > 0:
                            weight_unit = conversion.to_unit.abbreviation or conversion.to_unit.name
                            if weight_unit == 'kg' and weight_amount < 1:
                                weight_amount = round(weight_amount * 1000)
                                weight_unit = 'g'
                            ing.weight_equivalent = f"{weight_amount}{weight_unit}"
            except Exception:
                pass

    # Get instructions
    instructions = RecipeInstruction.objects.filter(recipe=recipe).order_by('step_number')

    # Get cooking calculation if exists
    try:
        cooking_calc = recipe.cooking_calculation
    except Exception:
        cooking_calc = None

    show_nutrition_button = recipe_has_any_mapped_ingredient(recipe)
    show_ai_suggestions = (
        show_nutrition_button
        and getattr(recipe, 'nutrition_cache', None) is not None
        and recipe.nutrition_cache.is_complete
    )

    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'instructions': instructions,
        'cooking_calculation': cooking_calc,
        'show_nutrition_button': show_nutrition_button,
        'show_ai_suggestions': show_ai_suggestions,
    }

    return render(request, 'view_recipe.html', context)


# ============================================
# VIEW: Recipe PDF (shareable)
# ============================================

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def recipe_pdf(request, recipe_id):
    """Generate a shareable PDF of a recipe.

    Backs the Share button on view_recipe.html: the browser fetches this
    endpoint and hands the PDF to the native share sheet (Web Share API),
    mirroring the title-deed share flow. Rendered with xhtml2pdf (pisa) from
    the recipe_pdf.html template. Read-tier auth, matching view_recipe.
    """
    from xhtml2pdf import pisa  # local import — pisa is only needed here

    recipe = get_object_or_404(
        Recipe.objects.prefetch_related('courses', 'categories', 'proteins'),
        recipe_id=recipe_id,
    )

    # Ingredients with formatted amounts + weight equivalents (mirrors view_recipe)
    ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related(
        'ingredient', 'ingredient__category', 'unit', 'preparation',
    ).order_by('ingredient_group', 'ingredient_order')

    units_needed = set()
    for ing in ingredients:
        if ing.unit and ing.unit.unit_type != 'weight' and ing.amount:
            units_needed.add(ing.unit_id)

    conversion_map = {}
    if units_needed:
        conversions_qs = UnitConversion.objects.filter(
            from_unit_id__in=units_needed
        ).select_related('from_unit', 'to_unit', 'specific_ingredient')
        for conv in conversions_qs:
            conversion_map.setdefault((conv.from_unit_id, conv.specific_ingredient_id), conv)
            if conv.specific_ingredient_id is None:
                conversion_map.setdefault((conv.from_unit_id, None), conv)

    for ing in ingredients:
        ing.formatted_amount = format_quantity(ing.amount)
        ing.weight_equivalent = None
        if ing.unit and ing.unit.unit_type != 'weight':
            try:
                amount = float(ing.amount) if ing.amount else 0
                if amount > 0:
                    conversion = (
                        conversion_map.get((ing.unit_id, ing.ingredient_id)) or
                        conversion_map.get((ing.unit_id, None))
                    )
                    if conversion:
                        weight_amount = round(amount * float(conversion.multiplier), 1)
                        if weight_amount == int(weight_amount):
                            weight_amount = int(weight_amount)
                        if weight_amount > 0:
                            weight_unit = conversion.to_unit.abbreviation or conversion.to_unit.name
                            if weight_unit == 'kg' and weight_amount < 1:
                                weight_amount = round(weight_amount * 1000)
                                weight_unit = 'g'
                            ing.weight_equivalent = f"{weight_amount}{weight_unit}"
            except Exception:
                pass

    instructions = RecipeInstruction.objects.filter(recipe=recipe).order_by('step_number')

    html = get_template('recipe_pdf.html').render({
        'recipe': recipe,
        'ingredients': ingredients,
        'instructions': instructions,
    })

    def link_callback(uri, rel):
        """Resolve media/static URLs to absolute filesystem paths so pisa can
        embed the recipe photo. Falls back to the original URI otherwise."""
        from django.conf import settings
        media_url = getattr(settings, 'MEDIA_URL', '') or ''
        media_root = getattr(settings, 'MEDIA_ROOT', '') or ''
        static_url = getattr(settings, 'STATIC_URL', '') or ''
        static_root = getattr(settings, 'STATIC_ROOT', '') or ''
        path = None
        if media_url and uri.startswith(media_url):
            path = os.path.join(media_root, uri[len(media_url):])
        elif static_url and uri.startswith(static_url) and static_root:
            path = os.path.join(static_root, uri[len(static_url):])
        if path and os.path.isfile(path):
            return path
        return uri

    filename = 'recipe_%s.pdf' % (slugify(recipe.recipe_name) or recipe.recipe_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="%s"' % filename

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Recipe PDF generation failed.', status=500)
    return response


# ============================================
# VIEW: Create Recipe
# ============================================

@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
def create_recipe(request):
    """Create new recipe - same for manual and AI import"""

    if request.method == 'POST':
        try:
            # Basic info
            recipe = Recipe()
            recipe.recipe_name = request.POST.get('recipe_name')

            # Check for duplicate name
            if Recipe.objects.filter(recipe_name__iexact=recipe.recipe_name).exists():
                messages.error(request, f'A recipe named "{recipe.recipe_name}" already exists. Please choose a different name.')
                return redirect('create_recipe')

            recipe.recipe_description = request.POST.get('recipe_description', '')
            recipe.author = request.POST.get('author', 'General')
            recipe.prep_time = request.POST.get('prep_time') or None
            recipe.cook_time = request.POST.get('cook_time') or None
            recipe.total_time = request.POST.get('total_time') or None
            recipe.servings = int(request.POST.get('servings', 4))
            recipe.difficulty_level = request.POST.get('difficulty_level', '')
            recipe.is_vegetarian = request.POST.get('is_vegetarian') == '1'

            if 'recipe_image' in request.FILES:
                recipe.recipe_image = request.FILES['recipe_image']

            recipe.created_by = request.user.username
            recipe.save()

            # Handle document upload
            if request.FILES.get('recipe_document'):
                uploaded_file = request.FILES['recipe_document']
                try:
                    pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                    recipe.recipe_document.save(pdf_filename, pdf_content, save=True)
                except Exception as e:
                    messages.warning(request, f'Recipe saved but document upload failed: {str(e)}')

            # Many-to-many
            course_ids = request.POST.getlist('course[]')
            if course_ids:
                recipe.courses.set(course_ids)

            category_ids = request.POST.getlist('category[]')
            if category_ids:
                recipe.categories.set(category_ids)

            if not recipe.is_vegetarian:
                protein_ids = request.POST.getlist('protein[]')
                if protein_ids:
                    recipe.proteins.set(protein_ids)

            # ========== SAVE INGREDIENTS (NORMALIZED) ==========
            ingredient_quantities = request.POST.getlist('ingredient_quantity[]')
            ingredient_measurements = request.POST.getlist('ingredient_measurement[]')
            ingredient_names = request.POST.getlist('ingredient_name[]')
            ingredient_preparations = request.POST.getlist('ingredient_preparation[]')
            ingredient_groups = request.POST.getlist('ingredient_group[]')

            for i in range(len(ingredient_names)):
                if ingredient_names[i].strip():
                    ingredient = get_or_create_ingredient(ingredient_names[i])
                    unit = get_or_create_unit(ingredient_measurements[i])

                    prep = None
                    if i < len(ingredient_preparations) and ingredient_preparations[i].strip():
                        prep = get_or_create_preparation(ingredient_preparations[i])

                    quantity_str = ingredient_quantities[i]

                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        unit=unit,
                        amount=convert_to_decimal(quantity_str),
                        preparation=prep,
                        ingredient_group=ingredient_groups[i] if i < len(ingredient_groups) else '',
                        ingredient_order=i
                    )

            # ========== SAVE INSTRUCTIONS ==========
            instructions = request.POST.getlist('instruction[]')
            instruction_groups = request.POST.getlist('instruction_group[]')

            for idx, instruction_text in enumerate(instructions):
                if instruction_text.strip():
                    group = instruction_groups[idx] if idx < len(instruction_groups) else ''
                    RecipeInstruction.objects.create(
                        recipe=recipe,
                        step_number=idx + 1,
                        instruction_text=instruction_text,
                        instruction_group=group
                    )

            # Cache recompute - explicit final call so the cache reflects the
            # final ingredient set, regardless of signal timing.
            # NOTE: kept inline (not hoisted) to preserve the original lazy
            # import that dodges a views <-> signals circular import; path
            # changed from relative ..signals to absolute pages.signals for
            # the new (deeper) package location.
            from pages.signals import _recalculate_cache_for_recipe
            _recalculate_cache_for_recipe(recipe)

            messages.success(request, f'Recipe "{recipe.recipe_name}" has been created successfully!')
            return redirect('recipe_management')

        except Exception as e:
            messages.error(request, f'Error creating recipe: {str(e)}')
            return redirect('create_recipe')

    # GET request - show empty form
    extracted_data = {
        'recipe_name': '',
        'description': '',
        'author': 'General',
        'prep_time': 0,
        'cook_time': 0,
        'total_time': 0,
        'servings': 4,
        'difficulty_level': '',
        'is_vegetarian': False,
        'ingredients': [],
        'instructions': [],
    }

    existing_measurements = list(MeasurementUnit.objects.values_list('name', flat=True))
    existing_ingredients_list = list(Ingredient.objects.values_list('name', flat=True))
    existing_preparations = list(PreparationMethod.objects.values_list('name', flat=True))
    courses = RecipeCourse.objects.all().order_by('name')
    categories = RecipeCategory.objects.all().order_by('name')
    proteins = CustomProtein.objects.all().order_by('name')
    ingredient_categories = IngredientCategory.objects.all().order_by('name')
    all_units = MeasurementUnit.objects.all().order_by('name')

    context = {
        'mode': 'create',
        'temp_recipe_id': None,
        'extracted_data': extracted_data,
        'existing_measurements': json.dumps(existing_measurements),
        'existing_ingredients': json.dumps(existing_ingredients_list),
        'existing_preparations': json.dumps(existing_preparations),
        'courses': courses,
        'categories': categories,
        'proteins': proteins,
        'ingredient_categories': ingredient_categories,
        'all_units': all_units,
    }

    return render(request, 'preview_imported_recipe.html', context)


# ============================================
# VIEW: Edit Recipe
# ============================================

@login_required
@permission_required('auth.can_edit_recipes', raise_exception=True)
def edit_recipe(request, recipe_id):
    """Edit an existing recipe"""

    recipe = get_object_or_404(
        Recipe.objects.prefetch_related(
            'courses',
            'categories',
            'proteins',
            'recipe_ingredients__ingredient',
            'recipe_ingredients__unit',
            'recipe_ingredients__preparation',
            'instructions'
        ),
        recipe_id=recipe_id
    )

    if request.method == 'POST':
        try:
            # Basic information
            recipe.recipe_name = request.POST.get('recipe_name')

            # Check for duplicate name (exclude current recipe)
            if Recipe.objects.filter(recipe_name__iexact=recipe.recipe_name).exclude(recipe_id=recipe_id).exists():
                messages.error(request, f'A recipe named "{recipe.recipe_name}" already exists. Please choose a different name.')
                return redirect('edit_recipe', recipe_id=recipe_id)

            recipe.recipe_description = request.POST.get('recipe_description', '')
            recipe.author = request.POST.get('author', 'General')
            recipe.prep_time = request.POST.get('prep_time') or None
            recipe.cook_time = request.POST.get('cook_time') or None
            recipe.total_time = request.POST.get('total_time') or None
            recipe.servings = request.POST.get('servings')

            # Image handling
            if request.POST.get('remove_image') == '1':
                if recipe.recipe_image:
                    recipe.recipe_image.delete(save=False)
                    recipe.recipe_image = None

            if 'recipe_image' in request.FILES:
                if recipe.recipe_image:
                    recipe.recipe_image.delete(save=False)
                recipe.recipe_image = request.FILES['recipe_image']

            # Classification
            course_ids = request.POST.getlist('course[]')
            category_ids = request.POST.getlist('category[]')
            recipe.difficulty_level = request.POST.get('difficulty_level')

            # Dietary
            recipe.is_vegetarian = request.POST.get('is_vegetarian') == '1'
            protein_ids = request.POST.getlist('protein[]')

            # Save recipe
            recipe.save()

            # Handle document upload/merge/replace
            if request.FILES.get('recipe_document'):
                uploaded_file = request.FILES['recipe_document']
                doc_action = request.POST.get('doc_action', 'replace')

                # Re-fetch recipe from DB to avoid stale FileField state
                recipe_fresh = Recipe.objects.get(pk=recipe.pk)

                try:
                    if doc_action == 'add_to_existing' and recipe_fresh.recipe_document:
                        # Read existing file fully into memory and close handle BEFORE any delete
                        existing_file_name = recipe_fresh.recipe_document.name
                        with recipe_fresh.recipe_document.open('rb') as f:
                            existing_bytes = f.read()
                        # File handle is now closed - safe to delete on Windows

                        if existing_bytes[:4] != b'%PDF':
                            messages.warning(request, 'Cannot merge: existing document is not a PDF. Replaced instead.')
                            if recipe_fresh.recipe_document.storage.exists(existing_file_name):
                                recipe_fresh.recipe_document.storage.delete(existing_file_name)
                            Recipe.objects.filter(pk=recipe.pk).update(recipe_document='')
                            recipe_fresh = Recipe.objects.get(pk=recipe.pk)
                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                            name_part = os.path.splitext(pdf_filename)[0]
                            unique_filename = f"{name_part}_{uuid.uuid4().hex[:8]}.pdf"
                            recipe_fresh.recipe_document.save(unique_filename, pdf_content, save=True)
                        else:
                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                            merged_pdf = merge_pdfs_from_bytes(existing_bytes, pdf_content)
                            original_name = os.path.splitext(os.path.basename(existing_file_name))[0]
                            if recipe_fresh.recipe_document.storage.exists(existing_file_name):
                                recipe_fresh.recipe_document.storage.delete(existing_file_name)
                            Recipe.objects.filter(pk=recipe.pk).update(recipe_document='')
                            recipe_fresh = Recipe.objects.get(pk=recipe.pk)
                            recipe_fresh.recipe_document.save(f"{original_name}_merged_{uuid.uuid4().hex[:8]}.pdf", merged_pdf, save=True)
                    else:
                        # Replace or new upload
                        if recipe_fresh.recipe_document:
                            existing_file_name = recipe_fresh.recipe_document.name
                            # Open and close immediately to release any lingering handle
                            try:
                                with recipe_fresh.recipe_document.open('rb') as f:
                                    pass
                            except Exception:
                                pass
                            if recipe_fresh.recipe_document.storage.exists(existing_file_name):
                                recipe_fresh.recipe_document.storage.delete(existing_file_name)
                            Recipe.objects.filter(pk=recipe.pk).update(recipe_document='')
                            recipe_fresh = Recipe.objects.get(pk=recipe.pk)
                        pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                        name_part = os.path.splitext(pdf_filename)[0]
                        unique_filename = f"{name_part}_{uuid.uuid4().hex[:8]}.pdf"
                        recipe_fresh.recipe_document.save(unique_filename, pdf_content, save=True)

                except Exception as e:
                    messages.warning(request, f'Recipe saved but document upload failed: {str(e)}')

            # Update many-to-many
            if course_ids:
                recipe.courses.set(course_ids)
            if category_ids:
                recipe.categories.set(category_ids)
            if recipe.is_vegetarian:
                recipe.proteins.clear()
            elif protein_ids:
                recipe.proteins.set(protein_ids)

            # ========== OPTIMIZED INGREDIENTS SECTION ==========
            recipe.recipe_ingredients.all().delete()

            ingredient_quantities = request.POST.getlist('ingredient_quantity[]')
            ingredient_measurements = request.POST.getlist('ingredient_measurement[]')
            ingredient_names = request.POST.getlist('ingredient_name[]')
            ingredient_preparations = request.POST.getlist('ingredient_preparation[]')
            ingredient_groups = request.POST.getlist('ingredient_group[]')

            ingredient_name_set = {name.strip() for name in ingredient_names if name.strip()}
            measurement_name_set = {meas.strip() for meas in ingredient_measurements if meas.strip()}
            preparation_name_set = {prep.strip() for prep in ingredient_preparations if prep.strip()}

            existing_ingredients = {
                ing.name: ing
                for ing in Ingredient.objects.filter(name__in=ingredient_name_set)
            }
            existing_units = {
                unit.name: unit
                for unit in MeasurementUnit.objects.filter(name__in=measurement_name_set)
            }
            existing_preparations = {
                prep.name: prep
                for prep in PreparationMethod.objects.filter(name__in=preparation_name_set)
            }

            new_ingredients = []
            for name in ingredient_name_set:
                if name not in existing_ingredients:
                    new_ingredients.append(Ingredient(name=name))
            if new_ingredients:
                Ingredient.objects.bulk_create(new_ingredients)
                existing_ingredients = {
                    ing.name: ing
                    for ing in Ingredient.objects.filter(name__in=ingredient_name_set)
                }

            new_units = []
            for name in measurement_name_set:
                if name not in existing_units:
                    new_units.append(MeasurementUnit(name=name))
            if new_units:
                MeasurementUnit.objects.bulk_create(new_units)
                existing_units = {
                    unit.name: unit
                    for unit in MeasurementUnit.objects.filter(name__in=measurement_name_set)
                }

            new_preparations = []
            for name in preparation_name_set:
                if name not in existing_preparations:
                    new_preparations.append(PreparationMethod(name=name))
            if new_preparations:
                PreparationMethod.objects.bulk_create(new_preparations)
                existing_preparations = {
                    prep.name: prep
                    for prep in PreparationMethod.objects.filter(name__in=preparation_name_set)
                }

            recipe_ingredients = []
            for i in range(len(ingredient_names)):
                if ingredient_names[i].strip():
                    ingredient = existing_ingredients.get(ingredient_names[i].strip())
                    unit = existing_units.get(ingredient_measurements[i].strip())

                    prep = None
                    if i < len(ingredient_preparations) and ingredient_preparations[i].strip():
                        prep = existing_preparations.get(ingredient_preparations[i].strip())

                    quantity_str = ingredient_quantities[i]

                    recipe_ingredients.append(RecipeIngredient(
                        recipe=recipe,
                        ingredient=ingredient,
                        unit=unit,
                        amount=convert_to_decimal(quantity_str),
                        preparation=prep,
                        ingredient_group=ingredient_groups[i] if i < len(ingredient_groups) else '',
                        ingredient_order=i
                    ))

            if recipe_ingredients:
                RecipeIngredient.objects.bulk_create(recipe_ingredients)

            # ========== OPTIMIZED INSTRUCTIONS SECTION ==========
            recipe.instructions.all().delete()

            instructions = request.POST.getlist('instruction[]')
            instruction_groups = request.POST.getlist('instruction_group[]')

            instruction_objects = []
            for idx, instruction_text in enumerate(instructions):
                if instruction_text.strip():
                    group = instruction_groups[idx] if idx < len(instruction_groups) else ''
                    instruction_objects.append(RecipeInstruction(
                        recipe=recipe,
                        step_number=idx + 1,
                        instruction_text=instruction_text,
                        instruction_group=group
                    ))

            if instruction_objects:
                RecipeInstruction.objects.bulk_create(instruction_objects)

            # ========== COOKING CALCULATION ==========
            calc_enabled = request.POST.get('calc_enabled') == '1'
            if calc_enabled:
                serving_time = request.POST.get('calc_serving_time')
                fire_lighting = request.POST.get('calc_fire_lighting')
                resting = request.POST.get('calc_resting')
                cutting_sauce = request.POST.get('calc_cutting_sauce')
                meat_weight = request.POST.get('calc_meat_weight')
                rate1 = request.POST.get('calc_rate1')
                rate1_threshold = request.POST.get('calc_rate1_threshold') or None
                rate2 = request.POST.get('calc_rate2') or None
                cooking_method = request.POST.get('calc_cooking_method', 'braai')
                additional_mins = request.POST.get('calc_additional_minutes') or None

                if all([serving_time, fire_lighting, resting, cutting_sauce, meat_weight, rate1]):
                    CookingCalculation.objects.update_or_create(
                        recipe=recipe,
                        defaults={
                            'serving_time': serving_time,
                            'cooking_method': cooking_method,
                            'fire_lighting_duration': int(fire_lighting),
                            'resting_duration': int(resting),
                            'cutting_sauce_duration': int(cutting_sauce),
                            'meat_weight': int(meat_weight),
                            'rate1_minutes_per_500g': rate1,
                            'rate1_threshold_grams': int(rate1_threshold) if rate1_threshold else None,
                            'rate2_minutes_per_500g': rate2 if rate2 else None,
                            'additional_cooking_minutes': int(additional_mins) if additional_mins else None,
                        }
                    )
            else:
                CookingCalculation.objects.filter(recipe=recipe).delete()

            # Cache recompute - explicit because bulk_create above doesn't fire signals,
            # and the in-flight signal cascade saw transient empty-ingredient state.
            # NOTE: kept inline (not hoisted) to preserve the original lazy
            # import that dodges a views <-> signals circular import; path
            # changed from relative ..signals to absolute pages.signals for
            # the new (deeper) package location.
            from pages.signals import _recalculate_cache_for_recipe
            _recalculate_cache_for_recipe(recipe)

            messages.success(request, f'Recipe "{recipe.recipe_name}" has been updated successfully!')
            return redirect('recipe_management')

        except Exception as e:
            messages.error(request, f'Error updating recipe: {str(e)}')
            return redirect('recipe_management')

    # ========== GET request - prepare data for editing ==========
    existing_ingredients = []

    for ing in recipe.recipe_ingredients.select_related(
        'ingredient', 'unit', 'preparation'
    ).order_by('ingredient_order'):
        existing_ingredients.append({
            'quantity': format_quantity(ing.amount),
            'measurement': ing.unit.name if ing.unit else '',
            'ingredient': ing.ingredient.name,
            'preparation': ing.preparation.name if ing.preparation else '',
            'group': ing.ingredient_group or ''
        })

    existing_instructions = [
        {
            'instruction': inst.instruction_text,
            'group': inst.instruction_group or ''
        }
        for inst in recipe.instructions.all().order_by('step_number')
    ]

    extracted_data = {
        'recipe_name': recipe.recipe_name,
        'description': recipe.recipe_description or '',
        'author': recipe.author,
        'prep_time': recipe.prep_time or 0,
        'cook_time': recipe.cook_time or 0,
        'total_time': recipe.total_time or 0,
        'servings': recipe.servings or 1,
        'difficulty_level': recipe.difficulty_level or '',
        'is_vegetarian': recipe.is_vegetarian,
        'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,
        'ingredients': existing_ingredients,
        'instructions': existing_instructions,
    }

    existing_measurements = list(MeasurementUnit.objects.values_list('name', flat=True))
    existing_ingredients_list = list(Ingredient.objects.values_list('name', flat=True))
    existing_preparations = list(PreparationMethod.objects.values_list('name', flat=True))
    courses = RecipeCourse.objects.all().order_by('name')
    categories = RecipeCategory.objects.all().order_by('name')
    proteins = CustomProtein.objects.all().order_by('name')
    ingredient_categories = IngredientCategory.objects.all().order_by('name')

    selected_course_ids = list(recipe.courses.values_list('recipe_course_id', flat=True))
    selected_category_ids = list(recipe.categories.values_list('recipe_category_id', flat=True))
    selected_protein_ids = list(recipe.proteins.values_list('custom_protein_id', flat=True))

    all_units = MeasurementUnit.objects.all().order_by('name')

    cooking_calc = getattr(recipe, 'cooking_calculation', None)

    context = {
        'mode': 'edit',
        'temp_recipe_id': recipe_id,
        'recipe': recipe,
        'extracted_data': extracted_data,
        'existing_measurements': json.dumps(existing_measurements),
        'existing_ingredients': json.dumps(existing_ingredients_list),
        'existing_preparations': json.dumps(existing_preparations),
        'courses': courses,
        'categories': categories,
        'proteins': proteins,
        'ingredient_categories': ingredient_categories,
        'all_units': all_units,
        'selected_courses': json.dumps(selected_course_ids),
        'selected_categories': json.dumps(selected_category_ids),
        'selected_proteins': json.dumps(selected_protein_ids),
        'cooking_calculation': cooking_calc,
    }

    return render(request, 'preview_imported_recipe.html', context)