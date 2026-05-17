"""
Recipe sub-resource, import, and favourite endpoints.

The lighter tail of the recipe subsystem: AJAX creators for recipe
lookups (course / category / ingredient / protein), a name-uniqueness
check, the AI import + preview/save flow, and the favourite toggle.

Functions
---------
- add_recipe_course      : AJAX create RecipeCourse (POST). Edit-tier.
- add_recipe_category    : AJAX create RecipeCategory (POST). Edit-tier.
- recipe_check_name      : AJAX recipe-name uniqueness check (GET).
                           Read-tier.
- add_recipe_ingredient  : AJAX create Ingredient (POST). Edit-tier.
- add_recipe_protein     : AJAX create CustomProtein (POST). Edit-tier.
- import_recipe          : Upload a file, extract text, run AI extraction,
                           stash result in the session, redirect to
                           preview. Edit-tier.
- preview_imported_recipe: Review/edit AI-extracted data; POST saves the
                           recipe (same save logic as create_recipe).
                           Read-tier (POST branch additionally checks
                           can_edit_personal).
- toggle_recipe_favourite: Toggle a recipe favourite for the user (POST).
                           Edit-tier.

Auth tiers
----------
Read-tier -> auth.can_access_personal
Edit-tier -> auth.can_edit_personal

Cross-module imports
--------------------
  pages.models : the recipe/lookup models (absolute, as elsewhere).
  ._helpers    : convert_to_decimal, get_or_create_ingredient,
                 get_or_create_preparation, get_or_create_unit
                 (homes verified during Phase 11a).
  .ai_extract  : extract_recipe_with_ai, extract_text_from_docx,
                 extract_text_from_image, extract_text_from_pdf
                 -- ASSUMED home (Phase 4 module). Verified by locator
                 grep + `manage.py check`; if it raises
                 `ImportError: cannot import name '...'`, the symbol
                 lives elsewhere (e.g. pages.utils, like the PDF helpers)
                 and this one import line gets repointed.

Preserved dead code
-------------------
`class TempRecipeData` (with its "Temporary storage..." comment) is kept
verbatim between add_recipe_protein and import_recipe. Nothing references
it (the import flow uses request.session), so it appears to be an unused
leftover -- but extraction is behavior-preserving, so it is preserved
as-is and noted as a post-split cleanup candidate, not removed here.

Encoding note (Phase 11b)
-------------------------
5 comment-only mojibake glyphs were replaced with ASCII: a mangled
em-dash (-> " - ") in preview_imported_recipe / toggle_recipe_favourite,
and mangled "look here" arrows before CHANGED / ADD THIS markers (the
arrow dropped, marker text kept). No code or behavioral string touched.
The inline `import uuid` in import_recipe was hoisted to module top per
the normalization standard. 100% ASCII.
"""

import json
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from pages.models import (
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
    RecipeInstruction,
)

from ._helpers import (
    convert_to_decimal,
    get_or_create_ingredient,
    get_or_create_preparation,
    get_or_create_unit,
)
from .ai_extract import (
    extract_recipe_with_ai,
    extract_text_from_docx,
    extract_text_from_image,
    extract_text_from_pdf,
)


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_recipe_course(request):
    """AJAX view to add a new recipe course"""

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        display_order = data.get('display_order', 0)

        if not name:
            return JsonResponse({'success': False, 'error': 'Course name is required'})

        if RecipeCourse.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'A course with this name already exists'})

        course = RecipeCourse.objects.create(
            name=name,
            display_order=int(display_order)
        )

        return JsonResponse({
            'success': True,
            'course_id': course.recipe_course_id,
            'name': course.name,
            'display_order': course.display_order
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_recipe_category(request):
    """AJAX view to add a new recipe category"""

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({'success': False, 'error': 'Category name is required'})

        if RecipeCategory.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'A category with this name already exists'})

        category = RecipeCategory.objects.create(name=name)

        return JsonResponse({
            'success': True,
            'category_id': category.recipe_category_id,
            'name': category.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def recipe_check_name(request):
    """AJAX endpoint to check if a recipe name already exists"""
    name = request.GET.get('name', '').strip()
    exclude = request.GET.get('exclude', '').strip()

    if not name:
        return JsonResponse({'exists': False})

    qs = Recipe.objects.filter(recipe_name__iexact=name)
    if exclude:
        qs = qs.exclude(recipe_name__iexact=exclude)

    return JsonResponse({'exists': qs.exists()})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_recipe_ingredient(request):
    """AJAX view to add a new ingredient"""

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        category_id = data.get('category_id', None)

        if not name:
            return JsonResponse({'success': False, 'error': 'Ingredient name is required'})

        if Ingredient.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'An ingredient with this name already exists'})

        ingredient = Ingredient.objects.create(name=name)

        if category_id:
            ingredient.category_id = category_id
            ingredient.save()

        return JsonResponse({
            'success': True,
            'ingredient_id': ingredient.ingredient_id,
            'name': ingredient.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_recipe_protein(request):
    """AJAX view to add a new custom protein - UPDATED"""

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({'success': False, 'error': 'Protein name is required'})

        # CHANGED: Only check if it exists in CustomProtein table
        if CustomProtein.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'This protein already exists'})

        # REMOVED: Check against MAIN_PROTEIN_CHOICES (no longer exists)

        protein = CustomProtein.objects.create(name=name)

        return JsonResponse({
            'success': True,
            'protein_id': protein.custom_protein_id,  # CHANGED: Return ID
            'name': protein.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Temporary storage for extracted recipe data (use session or database)
class TempRecipeData:
    """Temporary storage for AI-extracted recipe data"""
    def __init__(self, recipe_id, data):
        self.recipe_id = recipe_id
        self.data = data


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def import_recipe(request):
    """Upload recipe file for AI extraction"""

    if request.method == 'POST':
        uploaded_file = request.FILES.get('recipe_file')

        if not uploaded_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('import_recipe')

        try:
            file_name = uploaded_file.name
            file_ext = file_name.split('.')[-1].lower()

            # Extract text based on file type
            if file_ext == 'pdf':
                text_content = extract_text_from_pdf(uploaded_file)
            elif file_ext in ['doc', 'docx']:
                text_content = extract_text_from_docx(uploaded_file)
            elif file_ext in ['jpg', 'jpeg', 'png']:
                text_content = extract_text_from_image(uploaded_file)
            else:
                messages.error(request, 'Unsupported file format.')
                return redirect('import_recipe')

            # Use Claude AI to extract
            extracted_data = extract_recipe_with_ai(text_content, file_ext)

            if not extracted_data:
                messages.error(request, 'Could not extract recipe data. Please try a different file.')
                return redirect('import_recipe')

            # Store in session
            temp_id = str(uuid.uuid4())
            request.session[f'temp_recipe_{temp_id}'] = extracted_data
            request.session[f'temp_recipe_{temp_id}_file'] = file_name
            request.session.modified = True
            request.session.save()  # Force session to write to DB before redirect

            messages.success(request, 'Recipe extracted successfully! Please review and edit as needed.')
            return redirect('preview_imported_recipe', temp_id=temp_id)

        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('import_recipe')

    return render(request, 'import_recipe.html')


# ============================================
# VIEW: Preview Imported Recipe
# ============================================

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def preview_imported_recipe(request, temp_id):
    """Preview and edit AI-extracted recipe data - SAME save logic as create_recipe"""

    extracted_data = request.session.get(f'temp_recipe_{temp_id}')

    if not extracted_data:
        messages.error(request, 'Recipe data not found. Please import again.')
        return redirect('import_recipe')

    if request.method == 'POST':
        # Edit-level - POST creates the recipe
        if not request.user.has_perm('auth.can_edit_personal'):
            messages.error(request, "You don't have permission to save recipes.")
            return redirect('recipe_management')

        # ========== SAVE LOGIC - IDENTICAL TO create_recipe ==========
        try:
            recipe = Recipe()
            recipe.recipe_name = request.POST.get('recipe_name')
            recipe.recipe_description = request.POST.get('recipe_description', '')
            recipe.author = request.POST.get('author', 'General')
            recipe.prep_time = request.POST.get('prep_time') or None
            recipe.cook_time = request.POST.get('cook_time') or None
            recipe.total_time = request.POST.get('total_time') or None
            recipe.servings = request.POST.get('servings')
            recipe.difficulty_level = request.POST.get('difficulty_level')
            recipe.is_vegetarian = request.POST.get('is_vegetarian') == '1'
            recipe.created_by = request.user.username if request.user.is_authenticated else 'Anonymous'
            recipe.is_ai_imported = True

            if 'recipe_image' in request.FILES:
                recipe.recipe_image = request.FILES['recipe_image']

            recipe.save()

            # Many-to-many
            course_ids = request.POST.getlist('course[]')
            if course_ids:
                recipe.courses.set(course_ids)

            category_ids = request.POST.getlist('category[]')
            if category_ids:
                recipe.categories.set(category_ids)

            protein_ids = request.POST.getlist('protein[]')
            if not recipe.is_vegetarian and protein_ids:
                recipe.proteins.set(protein_ids)

            # ========== SAVE INGREDIENTS (NORMALIZED) - SAME AS create_recipe ==========
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
                        amount=convert_to_decimal(quantity_str),  # CHANGED
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

            # Clear session
            del request.session[f'temp_recipe_{temp_id}']
            if f'temp_recipe_{temp_id}_file' in request.session:
                del request.session[f'temp_recipe_{temp_id}_file']

            messages.success(request, f'Recipe "{recipe.recipe_name}" has been imported successfully!')
            return redirect('recipe_management')

        except Exception as e:
            messages.error(request, f'Error saving recipe: {str(e)}')
            return redirect('recipe_management')

    # GET request - show preview
    existing_measurements = list(MeasurementUnit.objects.values_list('name', flat=True))
    existing_ingredients_list = list(Ingredient.objects.values_list('name', flat=True))
    existing_preparations = list(PreparationMethod.objects.values_list('name', flat=True))
    courses = RecipeCourse.objects.all().order_by('name')
    categories = RecipeCategory.objects.all().order_by('name')
    proteins = CustomProtein.objects.all().order_by('name')
    ingredient_categories = IngredientCategory.objects.all().order_by('name')  # ADD THIS LINE

    # Load all units for the modal
    all_units = MeasurementUnit.objects.all().order_by('name')

    context = {
        'mode': 'import',
        'temp_recipe_id': temp_id,
        'extracted_data': extracted_data,
        'existing_measurements': json.dumps(existing_measurements),
        'existing_ingredients': json.dumps(existing_ingredients_list),
        'existing_preparations': json.dumps(existing_preparations),
        'courses': courses,
        'categories': categories,
        'proteins': proteins,
        'ingredient_categories': ingredient_categories,
        'all_units': all_units,  # ADD THIS
    }

    return render(request, 'preview_imported_recipe.html', context)


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def toggle_recipe_favourite(request, recipe_id):
    """Toggle a recipe as favourite for the current user"""
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
        favourite, created = RecipeFavourite.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            # Already a favourite - remove it
            favourite.delete()
            is_favourite = False
        else:
            is_favourite = True

        return JsonResponse({
            'success': True,
            'is_favourite': is_favourite,
            'recipe_id': recipe_id
        })

    return JsonResponse({'success': False}, status=400)