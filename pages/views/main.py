from calendar import monthrange, monthcalendar, month_name
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fractions import Fraction
from io import BytesIO
from urllib.parse import urlparse, parse_qs
import base64
import calendar
import decimal
import io
import json
import json as json_module
import logging
import os
import re
import smtplib
import string
import tempfile
import time
import uuid

import anthropic
import mysql.connector
import PyPDF2
from docx import Document
from docxtpl import DocxTemplate
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from spellchecker import SpellChecker
from xhtml2pdf import pisa

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage, FileSystemStorage
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.db import connection, models, transaction
from django.db.models import Count, F, Max, Min, OuterRef, Prefetch, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.static import serve

from .recipes import *
from .. import forms
from .. import recipe_ai
from ..forms import (
    ActExpenseForm,
    DetailsForm,
    ExpenseForm,
    ExpenseLineForm,
    ExpenseTypesForm,
    InvoicesForm,
    IssuesForm,
    PettyForm,
    PropForm,
    RevenueForm,
    RevenueLineForm,
    RevenueTypesForm,
    SupplierForm,
    TenantForm,
    ValuesForm,
)
from ..models import (
    act_expense,
    AssetCategory,
    AssetMaintenance,
    AssetSubcategory,
    AssetSupplier,
    CelebrationEvent,
    Contact,
    CookingCalculation,
    CustomProtein,
    EventNotification,
    expense,
    expense_line_types,
    expense_types,
    Ingredient,
    IngredientCategory,
    invoices,
    issues,
    issues_details,
    MealPlan,
    MealPlanDay,
    MealPlanRecipe,
    MeasurementUnit,
    NotificationRecipient,
    Passport,
    petty,
    PreparationMethod,
    Project,
    ProjectDocument,
    ProjectTask,
    prop_values,
    PropertyAsset,
    props,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
    RecipeIngredient,
    RecipeIngredientText,
    RecipeInstruction,
    revenue,
    revenue_line_types,
    revenue_types,
    supplier,
    tenant,
    UnitConversion,
    UserProfile,
    VacancyPeriod,
)
from ..usda_client import get_food_details, search_foods, USDAClientError
from ..nutrition_calc import calculate_recipe_nutrition
from ..utils import convert_to_pdf, is_pdf, merge_pdfs, merge_pdfs_from_bytes, render_to_pdf
from pages.email_utils import get_email_recipients, format_email_recipients_for_header


logger = logging.getLogger(__name__)


### RECIPE MANAGEMENT ###

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
@require_POST
def spell_check_instructions(request):
    """Spell check recipe instructions"""
    import re
    from spellchecker import SpellChecker
    try:
        data = json.loads(request.body)
        instructions = data.get('instructions', [])
        
        if not instructions:
            return JsonResponse({'success': False, 'error': 'No instructions provided'})
        
        # Initialize spell checker
        spell = SpellChecker()
        
        # Common cooking terms to ignore
        cooking_terms = {
            'tsp', 'tbsp', 'mins', 'hrs', 'preheat', 'saute', 'sauteed', 
            'broil', 'simmer', 'whisk', 'preheated',
            'mins', 'secs', 'ml', 'oz', 'fahrenheit', 'celsius'
        }
        spell.word_frequency.load_words(cooking_terms)
        
        errors = []
        
        for idx, instruction in enumerate(instructions):
            if not instruction.strip():
                continue
                
            # Remove common cooking abbreviations and numbers
            text = instruction.lower()
            
            # Split into words, removing punctuation
            words = re.findall(r'\b[a-z]+\b', text)
            
            # Find misspelled words
            misspelled = spell.unknown(words)
            
            if misspelled:
                for word in misspelled:
                    # Get suggestions - handle None case
                    candidates = spell.candidates(word)
                    
                    # Convert to list and handle None
                    if candidates is None:
                        suggestions = []
                    else:
                        suggestions = list(candidates)[:5]
                    
                    errors.append({
                        'step': idx + 1,
                        'word': word,
                        'suggestions': suggestions,  # Will be empty list if no suggestions
                        'context': instruction
                    })
        
        return JsonResponse({
            'success': True,
            'errors': errors,
            'total_errors': len(errors)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full error to console for debugging
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# RECIPE MANAGEMENT

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
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
            print(f"  Shopping unit: {shopping_unit.name if shopping_unit else 'NOT SET ❌'}")
            
            if not from_unit:
                continue
            
            # Determine final unit and amount
            if not shopping_unit:
                print(f"  ❌ No shopping unit - using recipe unit")
                final_unit = from_unit
                final_amount = quantity
            elif from_unit.measurement_unit_id == shopping_unit.measurement_unit_id:
                print(f"  ✅ Same unit - no conversion needed")
                final_unit = shopping_unit
                final_amount = quantity
            else:
                print(f"  🔄 Trying conversion: {from_unit.name} → {shopping_unit.name}")
                converted_qty, _ = convert_quantity(quantity, from_unit, shopping_unit)
                if converted_qty is not None:
                    print(f"  ✅ Conversion SUCCESS: {quantity} {from_unit.name} = {converted_qty} {shopping_unit.name}")
                    final_unit = shopping_unit
                    final_amount = converted_qty
                else:
                    print(f"  ❌ Conversion FAILED - using recipe unit")
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
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
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
@permission_required('auth.can_access_personal', raise_exception=True)
def recipe_management(request):
    """Recipe management page with multi-select filtering, A-Z filter, pagination, and nutrition sort."""
    # Handle delete action
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        if not request.user.has_perm('auth.can_edit_personal'):
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
    # Also count how many recipes were hidden (the "X hidden — finish mapping" nudge).
    hidden_by_nutrition_sort = 0
    if nutrition_sort:
        sort_field = NUTRITION_SORT_FIELDS[nutrition_sort]
        order_prefix = '' if nutrition_order == 'asc' else '-'
 
        # Count BEFORE narrowing — that's the total of recipes matching all
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
    import json as json_module
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
        'all_recipes_for_book': json_module.dumps(all_recipes_for_book),
        # Step 3 — nutrition sort
        'nutrition_sort': nutrition_sort,
        'nutrition_order': nutrition_order,
        'hidden_by_nutrition_sort': hidden_by_nutrition_sort,
    }
    
    return render(request, 'recipe_management.html', context)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
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
                        # Merge — existing must be PDF
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
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def duplicate_recipe(request, recipe_id):
    """Duplicate a recipe with all its ingredients and related data"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    try:
        from django.db import transaction
        
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
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ============================================
# VIEW: View Recipe
# ============================================

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
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
# VIEW: Create Recipe
# ============================================

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
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
            
            # Cache recompute — explicit final call so the cache reflects the
            # final ingredient set, regardless of signal timing.
            from ..signals import _recalculate_cache_for_recipe
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
@permission_required('auth.can_edit_personal', raise_exception=True)
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
                        # File handle is now closed — safe to delete on Windows

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

            # Cache recompute — explicit because bulk_create above doesn't fire signals,
            # and the in-flight signal cascade saw transient empty-ingredient state.
            from ..signals import _recalculate_cache_for_recipe
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
            import uuid
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
        # Edit-level — POST creates the recipe
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
                        amount=convert_to_decimal(quantity_str),  # ← CHANGED
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
    ingredient_categories = IngredientCategory.objects.all().order_by('name')  # ← ADD THIS LINE

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
        'all_units': all_units,  # ← ADD THIS
    }

    return render(request, 'preview_imported_recipe.html', context)

def aggregate_meal_plan_ingredients(meal_plan):
    """
    Aggregate ingredients and convert to shopping units.
    Always uses the ingredient's shopping unit. Prompts for missing conversions.
    Returns: (aggregated_dict, missing_conversions_list, missing_shopping_units_list)
    """
    from collections import defaultdict
    from decimal import Decimal
    import math
    
    def smart_categorize(ingredient_name):
        """Intelligently categorize ingredients based on name"""
        ingredient_lower = ingredient_name.lower()
        
        canned_terms = ['stock', 'broth', 'cube', 'bouillon', 'canned', 'tinned', 'tin', 'paste', 'sauce', 'puree', 'concentrate']
        for term in canned_terms:
            if term in ingredient_lower:
                return 'Canned & Packaged'
        
        beverages = ['wine', 'beer', 'sherry', 'brandy', 'rum', 'vodka', 'whiskey', 'liqueur']
        for term in beverages:
            if term in ingredient_lower:
                return 'Beverages'
        
        herbs_spices = ['oregano', 'origanum', 'basil', 'thyme', 'rosemary', 'sage', 'parsley', 'cilantro', 'pepper', 'salt', 'paprika', 'cumin', 'turmeric', 'cinnamon', 'nutmeg', 'cloves', 'curry', 'chili', 'cayenne']
        for term in herbs_spices:
            if term in ingredient_lower:
                return 'Herbs & Spices'
        
        meats = ['beef', 'pork', 'chicken', 'lamb', 'mince', 'meat', 'bacon', 'sausage', 'fish', 'salmon', 'tuna', 'shrimp', 'prawns']
        for term in meats:
            if term in ingredient_lower:
                return 'Meat & Seafood'
        
        dairy = ['milk', 'cream', 'yogurt', 'cheese', 'butter']
        is_beverage = any(bev in ingredient_lower for bev in beverages)
        if not is_beverage:
            for term in dairy:
                if term in ingredient_lower:
                    return 'Dairy'
        
        oils_fats = ['oil', 'olive oil', 'vegetable oil', 'butter', 'margarine', 'lard', 'ghee']
        for term in oils_fats:
            if term in ingredient_lower:
                return 'Oils & Fats'
        
        grains = ['flour', 'rice', 'pasta', 'spaghetti', 'noodles', 'bread', 'quinoa', 'couscous', 'oats', 'macaroni']
        for term in grains:
            if term in ingredient_lower:
                return 'Grains & Pasta'
        
        vegetables = ['onion', 'garlic', 'tomato', 'potato', 'carrot', 'celery', 'pepper', 'lettuce', 'spinach', 'broccoli', 'mushroom', 'peas', 'corn']
        for term in vegetables:
            if term in ingredient_lower:
                return 'Vegetables'
        
        return 'Other'
    
    def round_shopping_qty(qty, unit):
        """
        Round quantities intelligently based on unit type for shopping lists.
        NEVER rounds down - always rounds UP to ensure you have enough.
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
                return math.ceil(qty * 2) / 2
            elif qty < 100:
                return math.ceil(qty / 5) * 5
            else:
                return math.ceil(qty / 10) * 10
        
        elif unit_type == 'volume':
            # Round UP to sensible numbers based on magnitude
            if qty < 10:
                return math.ceil(qty * 4) / 4
            elif qty < 100:
                return math.ceil(qty / 5) * 5
            else:
                return math.ceil(qty / 10) * 10
        
        else:
            # OTHER (dash, pinch, to taste): round UP
            return max(1, math.ceil(qty))
    
    def get_unit_display(unit, qty):
        """Get the proper unit display with pluralization"""
        if qty == 1:
            return unit.abbreviation or unit.name
        else:
            return unit.abbreviation_plural or unit.abbreviation or unit.name_plural or unit.name
    
    # Pre-load all unit conversions for fast lookups (prevents N+1 queries)
    conversion_cache = get_conversion_cache()
    
    # Track issues
    missing_conversions = []
    missing_shopping_units = []
    seen_missing_conversions = set()
    seen_missing_units = set()
    
    # Dictionary: ingredient_id -> {amount, unit, ingredient_obj, unconverted_items}
    aggregated = defaultdict(lambda: {
        'unit': None,
        'amount': Decimal('0'),
        'ingredient_obj': None,
        'unconverted_items': []  # Items that couldn't be converted
    })
    
    # Process all recipes in meal plan
    for day in meal_plan.days.all().order_by('date'):
        for meal_recipe in day.recipes.all():
            recipe = meal_recipe.recipe
            servings_multiplier = Decimal(meal_recipe.servings) / Decimal(recipe.servings or 1)
            
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                ingredient_id = ingredient.ingredient_id
                quantity = Decimal(recipe_ingredient.amount or 0) * servings_multiplier
                from_unit = recipe_ingredient.unit
                
                if not from_unit:
                    continue
                
                # CRITICAL: Always use the ingredient's shopping unit
                shopping_unit = ingredient.default_unit
                
                # Track ingredients without shopping units
                if not shopping_unit:
                    if ingredient_id not in seen_missing_units:
                        seen_missing_units.add(ingredient_id)
                        missing_shopping_units.append({
                            'ingredient_id': ingredient_id,
                            'ingredient_name': ingredient.name,
                            'recipe': recipe.recipe_name
                        })
                    # Add to unconverted items
                    if ingredient_id not in aggregated:
                        aggregated[ingredient_id]['ingredient_obj'] = ingredient
                        aggregated[ingredient_id]['unit'] = from_unit  # Fallback
                    
                    aggregated[ingredient_id]['unconverted_items'].append({
                        'quantity': float(quantity),
                        'unit': from_unit.name,
                        'recipe': recipe.recipe_name,
                        'reason': 'No shopping unit defined'
                    })
                    continue
                
                # Initialize if first time seeing this ingredient
                if aggregated[ingredient_id]['unit'] is None:
                    aggregated[ingredient_id]['unit'] = shopping_unit
                    aggregated[ingredient_id]['ingredient_obj'] = ingredient
                
                shopping_unit = aggregated[ingredient_id]['unit']
                
                # Convert to shopping unit
                if from_unit.measurement_unit_id == shopping_unit.measurement_unit_id:
                    # Same unit - just add
                    aggregated[ingredient_id]['amount'] += quantity
                else:
                    # Need conversion - USE CACHE for fast lookup
                    converted_qty, multiplier = convert_quantity(quantity, from_unit, shopping_unit, ingredient, conversion_cache)
                    
                    if converted_qty is not None:
                        # Conversion successful
                        aggregated[ingredient_id]['amount'] += converted_qty
                    else:
                        # NO CONVERSION EXISTS - Track it
                        conversion_key = f"{from_unit.measurement_unit_id}-{shopping_unit.measurement_unit_id}"
                        if conversion_key not in seen_missing_conversions:
                            seen_missing_conversions.add(conversion_key)
                            missing_conversions.append({
                                'ingredient': ingredient.name,
                                'from_unit': from_unit.name,
                                'from_unit_id': from_unit.measurement_unit_id,
                                'to_unit': shopping_unit.name,
                                'to_unit_id': shopping_unit.measurement_unit_id,
                                'quantity': float(quantity),
                                'recipe': recipe.recipe_name
                            })
                        
                        # Add to unconverted items
                        aggregated[ingredient_id]['unconverted_items'].append({
                            'quantity': float(quantity),
                            'unit': from_unit.name,
                            'recipe': recipe.recipe_name,
                            'reason': f'Missing conversion from {from_unit.name} to {shopping_unit.name}'
                        })
    
    # Build categorized shopping list
    categorized_ingredients = defaultdict(list)
    
    for ingredient_id in sorted(aggregated.keys(), key=lambda x: aggregated[x]['ingredient_obj'].name):
        data = aggregated[ingredient_id]
        ingredient_obj = data['ingredient_obj']
        unit = data['unit']
        
        # Determine category
        if ingredient_obj and ingredient_obj.category:
            category = ingredient_obj.category.name
        else:
            category = smart_categorize(ingredient_obj.name)
        
        # Only add to shopping list if we successfully converted some amount
        if data['amount'] > 0:
            # Apply smart rounding for shopping
            raw_qty = float(data['amount'])
            qty = round_shopping_qty(raw_qty, unit)
            
            # Get proper unit display with pluralization
            unit_display = get_unit_display(unit, qty)
            
            entry = {
                'ingredient': ingredient_obj.name,
                'quantity': qty,
                'unit': unit_display
            }
            
            # Add note about unconverted items
            if data['unconverted_items']:
                entry['has_unconverted'] = True
                entry['unconverted_count'] = len(data['unconverted_items'])
                entry['unconverted_items'] = data['unconverted_items']
            
            categorized_ingredients[category].append(entry)
    
    return (dict(categorized_ingredients), missing_conversions, missing_shopping_units)

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def meal_plans(request):
    """List all meal plans"""
    
    # Get all meal plans with recipe counts, sorted by most recent first
    meal_plans_list = MealPlan.objects.annotate(
        recipe_count=Count('days__recipes')
    ).order_by('-start_date')  # ← This orders newest first
    
    context = {
        'meal_plans': meal_plans_list,
    }
    
    return render(request, 'meal_plans.html', context)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def create_meal_plan(request):
    """Create a new meal plan"""
    
    if request.method == 'POST':
        try:
            plan_name = request.POST.get('plan_name')
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            days_diff = (end_date - start_date).days + 1
            if days_diff < 1 or days_diff > 7:
                messages.error(request, 'Meal plan must be between 1 and 7 days.')
                return redirect('create_meal_plan')
            
            meal_plan = MealPlan.objects.create(
                plan_name=plan_name,
                start_date=start_date,
                end_date=end_date,
                created_by=request.user
            )
            
            current_date = start_date
            while current_date <= end_date:
                meal_day = MealPlanDay.objects.create(
                    meal_plan=meal_plan,
                    date=current_date
                )
                
                date_key = current_date.strftime('%Y-%m-%d')
                recipe_ids = request.POST.getlist(f'recipes_{date_key}[]')
                servings_list = request.POST.getlist(f'servings_{date_key}[]')
                
                for idx, recipe_id in enumerate(recipe_ids):
                    if recipe_id:
                        recipe = Recipe.objects.get(recipe_id=recipe_id)
                        servings = int(servings_list[idx]) if idx < len(servings_list) else recipe.servings
                        
                        MealPlanRecipe.objects.create(
                            meal_plan_day=meal_day,
                            recipe=recipe,
                            servings=servings,
                            sort_order=idx
                        )
                
                current_date += timedelta(days=1)
            
            messages.success(request, f'Meal plan "{plan_name}" created successfully!')
            return redirect('view_meal_plan', meal_plan_id=meal_plan.meal_plan_id)
            
        except Exception as e:
            print(f"\n!!! ERROR: {str(e)} !!!")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error creating meal plan: {str(e)}')
            return redirect('create_meal_plan')
    
    # GET request - show form
    recipes_qs = Recipe.objects.prefetch_related(
        'courses', 'categories', 'proteins'
    ).all().order_by('recipe_name')
    
    recipes = []
    for recipe in recipes_qs:
        recipes.append({
            'recipe_id': recipe.recipe_id,
            'recipe_name': recipe.recipe_name,
            'servings': recipe.servings,
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'difficulty_level': recipe.difficulty_level or '',
            'is_vegetarian': recipe.is_vegetarian,
            'author': recipe.author,
            'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,
            'courses': [course.name for course in recipe.courses.all()],
            'categories': [cat.name for cat in recipe.categories.all()],
            'proteins': [protein.name for protein in recipe.proteins.all()]
        })
    
    all_courses = list(RecipeCourse.objects.all().order_by('name').values('recipe_course_id', 'name'))
    all_categories = list(RecipeCategory.objects.all().order_by('name').values('recipe_category_id', 'name'))
    all_proteins = list(CustomProtein.objects.all().order_by('name').values('custom_protein_id', 'name'))
    
    all_authors = [
        {'value': 'General', 'name': 'General'},
        {'value': 'Demetri & Angy', 'name': 'Demetri & Angy'},
        {'value': 'Erene', 'name': 'Erene'},
        {'value': 'Alexandra', 'name': 'Alexandra'},
    ]

    today = datetime.now().date()
    default_end = today + timedelta(days=6)

    user_favourite_ids = list(
        RecipeFavourite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    )
    
    context = {
        'edit_mode': False,
        'recipes_json': json.dumps(recipes),
        'all_courses_json': json.dumps(all_courses),
        'all_categories_json': json.dumps(all_categories),
        'all_proteins_json': json.dumps(all_proteins),
        'all_authors_json': json.dumps(all_authors),
        'user_favourite_ids_json': json.dumps(user_favourite_ids),
        'today': today,
        'default_start_date': today.strftime('%Y-%m-%d'),
        'default_end_date': default_end.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'create_meal_plan.html', context)

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def view_meal_plan(request, meal_plan_id):
    """View a meal plan with all days and recipes"""
    
    # Get meal plan with optimized prefetch
    meal_plan = get_object_or_404(
        MealPlan.objects.prefetch_related(
            Prefetch(
                'days',
                queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                    Prefetch(
                        'recipes',
                        queryset=MealPlanRecipe.objects.select_related('recipe')
                    )
                )
            )
        ),
        meal_plan_id=meal_plan_id
    )
    
    # Days are already prefetched and ordered
    days = meal_plan.days.all()

    user_favourites = set(
        RecipeFavourite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    )
    
    context = {
        'meal_plan': meal_plan,
        'days': days,
        'user_favourites': user_favourites,
    }
    
    return render(request, 'view_meal_plan.html', context)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def delete_meal_plan(request, meal_plan_id):
    """Delete a meal plan"""
    
    # Only allow POST requests for deletion
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('meal_plans')
    
    try:
        meal_plan = MealPlan.objects.get(meal_plan_id=meal_plan_id)
        plan_name = meal_plan.plan_name
        
        # Delete the meal plan (cascade will delete days and recipes)
        meal_plan.delete()
        
        messages.success(request, f'Meal plan "{plan_name}" has been deleted successfully.')
        
    except MealPlan.DoesNotExist:
        messages.error(request, 'Meal plan not found.')
    
    # Check where to redirect
    redirect_to = request.POST.get('redirect_to', 'list')
    if redirect_to == 'calendar':
        return redirect('meal_plan_calendar')
    return redirect('meal_plans')

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def edit_meal_plan(request, meal_plan_id):
    """Edit an existing meal plan"""
    
    meal_plan = get_object_or_404(
        MealPlan.objects.prefetch_related(
            Prefetch(
                'days',
                queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                    Prefetch(
                        'recipes',
                        queryset=MealPlanRecipe.objects.select_related('recipe').order_by('sort_order')
                    )
                )
            )
        ),
        meal_plan_id=meal_plan_id
    )
    
    if request.method == 'POST':
        try:
            from django.db import transaction
            
            new_plan_name = request.POST.get('plan_name', '').strip()
            new_start_date_str = request.POST.get('start_date')
            new_end_date_str = request.POST.get('end_date')
            
            if not new_plan_name:
                messages.error(request, 'Plan name is required.')
                return redirect('edit_meal_plan', meal_plan_id=meal_plan_id)
            
            new_start_date = datetime.strptime(new_start_date_str, '%Y-%m-%d').date()
            new_end_date = datetime.strptime(new_end_date_str, '%Y-%m-%d').date()
            
            days_diff = (new_end_date - new_start_date).days + 1
            if days_diff < 1 or days_diff > 7:
                messages.error(request, 'Meal plan must be between 1 and 7 days.')
                return redirect('edit_meal_plan', meal_plan_id=meal_plan_id)
            
            with transaction.atomic():
                meal_plan.plan_name = new_plan_name
                meal_plan.start_date = new_start_date
                meal_plan.end_date = new_end_date
                meal_plan.save()
                
                existing_days = {day.date: day for day in meal_plan.days.all()}
                
                new_dates = []
                current_date = new_start_date
                while current_date <= new_end_date:
                    new_dates.append(current_date)
                    current_date += timedelta(days=1)
                
                dates_to_keep = set(new_dates)
                for date, day in existing_days.items():
                    if date not in dates_to_keep:
                        day.delete()
                
                for date in new_dates:
                    if date in existing_days:
                        meal_day = existing_days[date]
                    else:
                        meal_day = MealPlanDay.objects.create(
                            meal_plan=meal_plan,
                            date=date
                        )
                    
                    date_key = date.strftime('%Y-%m-%d')
                    recipe_ids = request.POST.getlist(f'recipes_{date_key}[]')
                    servings_list = request.POST.getlist(f'servings_{date_key}[]')
                    
                    existing_recipes = {mr.recipe.recipe_id: mr for mr in meal_day.recipes.all()}
                    recipes_to_keep = set()
                    
                    for idx, recipe_id in enumerate(recipe_ids):
                        if recipe_id:
                            recipe_id = int(recipe_id)
                            recipes_to_keep.add(recipe_id)
                            
                            recipe = Recipe.objects.get(recipe_id=recipe_id)
                            servings = int(servings_list[idx]) if idx < len(servings_list) else recipe.servings
                            
                            if recipe_id in existing_recipes:
                                meal_recipe = existing_recipes[recipe_id]
                                meal_recipe.servings = servings
                                meal_recipe.sort_order = idx
                                meal_recipe.save()
                            else:
                                MealPlanRecipe.objects.create(
                                    meal_plan_day=meal_day,
                                    recipe=recipe,
                                    servings=servings,
                                    sort_order=idx
                                )
                    
                    for recipe_id, meal_recipe in existing_recipes.items():
                        if recipe_id not in recipes_to_keep:
                            meal_recipe.delete()
            
            messages.success(request, f'Meal plan "{new_plan_name}" updated successfully!')
            return redirect('view_meal_plan', meal_plan_id=meal_plan_id)
            
        except Exception as e:
            print(f"\n!!! ERROR: {str(e)} !!!")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error updating meal plan: {str(e)}')
            return redirect('edit_meal_plan', meal_plan_id=meal_plan_id)
    
    # GET request - prepare data for editing
    meal_plan_data = {
        'meal_plan_id': meal_plan.meal_plan_id,
        'plan_name': meal_plan.plan_name,
        'start_date': meal_plan.start_date.strftime('%Y-%m-%d'),
        'end_date': meal_plan.end_date.strftime('%Y-%m-%d'),
        'days': []
    }
    
    for day in meal_plan.days.all():
        day_data = {
            'date': day.date.strftime('%Y-%m-%d'),
            'recipes': []
        }
        
        for meal_recipe in day.recipes.all():
            recipe = meal_recipe.recipe
            day_data['recipes'].append({
                'meal_plan_recipe_id': meal_recipe.meal_plan_recipe_id,
                'recipe_id': recipe.recipe_id,
                'recipe_name': recipe.recipe_name,
                'servings': meal_recipe.servings,
                'sort_order': meal_recipe.sort_order,
                'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,
                'prep_time': recipe.prep_time,
                'cook_time': recipe.cook_time,
                'difficulty_level': recipe.difficulty_level or '',
                'is_vegetarian': recipe.is_vegetarian,
                'courses': [course.name for course in recipe.courses.all()],
                'categories': [cat.name for cat in recipe.categories.all()],
                'proteins': [protein.name for protein in recipe.proteins.all()]
            })
        
        meal_plan_data['days'].append(day_data)
    
    recipes_qs = Recipe.objects.prefetch_related(
        'courses', 'categories', 'proteins'
    ).all().order_by('recipe_name')
    
    recipes = []
    for recipe in recipes_qs:
        recipes.append({
            'recipe_id': recipe.recipe_id,
            'recipe_name': recipe.recipe_name,
            'servings': recipe.servings,
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'difficulty_level': recipe.difficulty_level or '',
            'is_vegetarian': recipe.is_vegetarian,
            'author': recipe.author,
            'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,
            'courses': [course.name for course in recipe.courses.all()],
            'categories': [cat.name for cat in recipe.categories.all()],
            'proteins': [protein.name for protein in recipe.proteins.all()]
        })
    
    all_courses = list(RecipeCourse.objects.all().order_by('name').values('recipe_course_id', 'name'))
    all_categories = list(RecipeCategory.objects.all().order_by('name').values('recipe_category_id', 'name'))
    all_proteins = list(CustomProtein.objects.all().order_by('name').values('custom_protein_id', 'name'))
    
    all_authors = [
        {'value': 'General', 'name': 'General'},
        {'value': 'Demetri & Angy', 'name': 'Demetri & Angy'},
        {'value': 'Erene', 'name': 'Erene'},
        {'value': 'Alexandra', 'name': 'Alexandra'},
    ]

    user_favourite_ids = list(
        RecipeFavourite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    )
    
    context = {
        'edit_mode': True,
        'meal_plan': meal_plan,
        'meal_plan_json': json.dumps(meal_plan_data),
        'recipes_json': json.dumps(recipes),
        'all_courses_json': json.dumps(all_courses),
        'all_categories_json': json.dumps(all_categories),
        'all_proteins_json': json.dumps(all_proteins),
        'all_authors_json': json.dumps(all_authors),
        'user_favourite_ids_json': json.dumps(user_favourite_ids),
    }
    
    return render(request, 'create_meal_plan.html', context)

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
def duplicate_meal_plan(request, meal_plan_id):
    """Duplicate a meal plan to new dates"""
    
    try:
        # Get the original meal plan with all related data
        original_plan = MealPlan.objects.prefetch_related(
            'days__recipes__recipe'
        ).get(meal_plan_id=meal_plan_id)
        
        if request.method == 'POST':
            new_plan_name = request.POST.get('new_plan_name', '').strip()
            new_start_date = request.POST.get('new_start_date')
            
            if not new_plan_name:
                messages.error(request, 'Please enter a name for the duplicated meal plan.')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)
            
            if not new_start_date:
                messages.error(request, 'Please select a start date.')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)
            
            try:
                # Parse the new start date
                new_start = datetime.strptime(new_start_date, '%Y-%m-%d').date()
                
                # Calculate duration of original plan
                duration = (original_plan.end_date - original_plan.start_date).days
                new_end = new_start + timedelta(days=duration)
                
                # Create new meal plan with user-provided name
                new_plan = MealPlan.objects.create(
                    plan_name=new_plan_name,
                    start_date=new_start,
                    end_date=new_end,
                    created_by=request.user
                )
                
                # Duplicate all days and recipes
                for day in original_plan.days.all().order_by('date'):
                    # Calculate the offset from original start date
                    day_offset = (day.date - original_plan.start_date).days
                    new_day_date = new_start + timedelta(days=day_offset)
                    
                    # Create new day
                    new_day = MealPlanDay.objects.create(
                        meal_plan=new_plan,
                        date=new_day_date
                    )
                    
                    # Copy all recipes for this day
                    for meal_recipe in day.recipes.all():
                        MealPlanRecipe.objects.create(
                            meal_plan_day=new_day,
                            recipe=meal_recipe.recipe,
                            servings=meal_recipe.servings
                        )
                
                # Check if user wants to delete original (shift functionality)
                delete_original = request.POST.get('delete_original') == 'yes'

                if delete_original:
                    # Delete the original meal plan (this is a "shift" operation)
                    original_plan_name = original_plan.plan_name
                    original_plan.delete()
                    messages.success(request, f'Meal plan "{original_plan_name}" shifted to new dates: {new_start.strftime("%B %d, %Y")} - {new_end.strftime("%B %d, %Y")}')
                else:
                    # Regular duplicate (keep original)
                    messages.success(request, f'Meal plan "{new_plan_name}" created successfully starting on {new_start.strftime("%B %d, %Y")}.')

                return redirect('view_meal_plan', meal_plan_id=new_plan.meal_plan_id)
                
            except ValueError as e:
                messages.error(request, f'Invalid date format: {str(e)}')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)
            except Exception as e:
                messages.error(request, f'Error duplicating meal plan: {str(e)}')
                return redirect('view_meal_plan', meal_plan_id=meal_plan_id)
        
        # GET request - should not happen with modal, but redirect just in case
        return redirect('view_meal_plan', meal_plan_id=meal_plan_id)
        
    except MealPlan.DoesNotExist:
        messages.error(request, 'Meal plan not found.')
        return redirect('meal_plans')

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def meal_plan_calendar(request):
    """Calendar view for meal plans"""
    from datetime import timedelta
    from calendar import monthcalendar
    import json
    
    # Get requested month/year or default to current
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Get selected week start date (Monday)
    selected_week_start = request.GET.get('week')
    if selected_week_start:
        selected_week_start = datetime.strptime(selected_week_start, '%Y-%m-%d').date()
    else:
        # Default to current week (find Monday)
        selected_week_start = today - timedelta(days=today.weekday())
    
    selected_week_end = selected_week_start + timedelta(days=6)
    
    # Build calendar data for the month
    # Get first day of month and adjust to start from Monday
    first_of_month = date(year, month, 1)
    
    # Get all days we need to show (including overflow from prev/next months)
    cal = monthcalendar(year, month)  # Returns weeks starting from Monday
    
    # Get all meal plans (shared across users)
    all_meal_plans = MealPlan.objects.all().order_by('-start_date')

    # Get meal plans that overlap with this month (for dot indicators)
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    month_meal_plans = MealPlan.objects.filter(
        start_date__lte=month_end,
        end_date__gte=month_start
    )
    
    # Build a set of dates that have meals planned
    dates_with_meals = set()
    for plan in month_meal_plans:
        days_with_recipes = MealPlanDay.objects.filter(
            meal_plan=plan,
            recipes__isnull=False
        ).values_list('date', flat=True).distinct()
        dates_with_meals.update(days_with_recipes)
    
    # Build calendar weeks with metadata
    calendar_weeks = []
    for week in cal:
        week_data = []
        week_dates = []
        for day_num in week:
            if day_num == 0:
                week_data.append(None)
            else:
                day_date = date(year, month, day_num)
                week_dates.append(day_date)
                week_data.append({
                    'day': day_num,
                    'date': day_date,
                    'has_meal': day_date in dates_with_meals,
                    'is_today': day_date == today,
                })
        
        # Calculate week start (Monday) for this row
        if week_dates:
            # Find the Monday of this week
            first_valid_date = week_dates[0]
            week_start = first_valid_date - timedelta(days=first_valid_date.weekday())
        else:
            week_start = None
            
        calendar_weeks.append({
            'days': week_data,
            'week_start': week_start,
        })
    
    # Get the meal plan for the selected week (if any)
    selected_meal_plan = MealPlan.objects.filter(
        start_date__lte=selected_week_end,
        end_date__gte=selected_week_start
    ).first()
    
    # Build week detail data
    week_days = []
    for i in range(7):
        day_date = selected_week_start + timedelta(days=i)
        day_data = {
            'date': day_date,
            'day_name': day_date.strftime('%A'),
            'day_short': day_date.strftime('%a'),
            'day_num': day_date.day,
            'is_today': day_date == today,
            'recipes': [],
            'meal_plan_day_id': None,
        }
        
        # If there's a meal plan for this week, get recipes for this day
        if selected_meal_plan:
            meal_plan_day = MealPlanDay.objects.filter(
                meal_plan=selected_meal_plan,
                date=day_date
            ).first()
            
            if meal_plan_day:
                day_data['meal_plan_day_id'] = meal_plan_day.meal_plan_day_id
                recipes = MealPlanRecipe.objects.filter(
                    meal_plan_day=meal_plan_day
                ).select_related('recipe').order_by('sort_order')
                
                for mpr in recipes:
                    recipe = mpr.recipe
                    day_data['recipes'].append({
                        'meal_plan_recipe_id': mpr.meal_plan_recipe_id,
                        'recipe_id': recipe.recipe_id,
                        'name': recipe.recipe_name,
                        'image': recipe.recipe_image.url if recipe.recipe_image else None,
                        'prep_time': recipe.prep_time,
                        'cook_time': recipe.cook_time,
                        'total_time': (recipe.prep_time or 0) + (recipe.cook_time or 0),
                        'servings': mpr.servings,
                        'difficulty': recipe.difficulty_level,
                    })
        
        week_days.append(day_data)
    
    # Previous and next month for navigation
    if month == 1:
        prev_month = {'year': year - 1, 'month': 12}
    else:
        prev_month = {'year': year, 'month': month - 1}
    
    if month == 12:
        next_month = {'year': year + 1, 'month': 1}
    else:
        next_month = {'year': year, 'month': month + 1}
    
    # Month name for display
    month_name = date(year, month, 1).strftime('%B %Y')
    
    # Get all recipes for the "Add Recipe" modal
    all_recipes = Recipe.objects.all().order_by('recipe_name')
    
    context = {
        'calendar_weeks': calendar_weeks,
        'month_name': month_name,
        'year': year,
        'month': month,
        'prev_month': prev_month,
        'next_month': next_month,
        'today': today,
        'selected_week_start': selected_week_start,
        'selected_week_end': selected_week_end,
        'selected_meal_plan': selected_meal_plan,
        'week_days': week_days,
        'all_meal_plans': all_meal_plans,
        'all_recipes': all_recipes,
    }
    
    return render(request, 'meal_plan_calendar.html', context)

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def meal_plan_shopping_list(request, meal_plan_id):
    """Display shopping list with unit conversion and prompt for missing conversions"""
    
    try:
        # Get meal plan with optimized prefetching
        meal_plan = get_object_or_404(
            MealPlan.objects.prefetch_related(
                Prefetch(
                    'days',
                    queryset=MealPlanDay.objects.order_by('date').prefetch_related(
                        Prefetch(
                            'recipes',
                            queryset=MealPlanRecipe.objects.select_related('recipe').prefetch_related(
                                Prefetch(
                                    'recipe__recipe_ingredients',
                                    queryset=RecipeIngredient.objects.select_related(
                                        'ingredient',
                                        'ingredient__category',
                                        'ingredient__default_unit',
                                        'unit'
                                    )
                                )
                            )
                        )
                    )
                )
            ),
            meal_plan_id=meal_plan_id
        )
        
        # Aggregate ingredients with conversion
        ingredients, missing_conversions, missing_shopping_units = aggregate_meal_plan_ingredients(meal_plan)
        
        # Check for missing conversions or shopping units
        has_issues = len(missing_conversions) > 0 or len(missing_shopping_units) > 0
        
        context = {
            'meal_plan': meal_plan,
            'ingredients': ingredients,
            'total_ingredients': sum(len(items) for items in ingredients.values()),
            'missing_conversions': json.dumps(missing_conversions) if missing_conversions else '[]',
            'missing_shopping_units': json.dumps(missing_shopping_units) if missing_shopping_units else '[]',
            'has_missing_conversions': len(missing_conversions) > 0,
            'has_missing_shopping_units': len(missing_shopping_units) > 0,
            'has_issues': has_issues,
        }
        
        return render(request, 'meal_plan_shopping_list.html', context)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error generating shopping list: {str(e)}')
        return redirect('view_meal_plan', meal_plan_id=meal_plan_id)

@login_required
@require_POST
@permission_required('auth.can_edit_personal', raise_exception=True)
def add_recipe_to_meal_plan_day(request, meal_plan_id):
    """Add a recipe to a meal plan day"""
    meal_plan_day_id = request.POST.get('meal_plan_day_id')
    recipe_id = request.POST.get('recipe_id')
    servings = request.POST.get('servings', 4)
    
    try:
        meal_plan_day = MealPlanDay.objects.get(meal_plan_day_id=meal_plan_day_id)
        recipe = Recipe.objects.get(recipe_id=recipe_id)
        
        # Verify user owns this meal plan
        if meal_plan_day.meal_plan.created_by != request.user:
            messages.error(request, 'You do not have permission to modify this meal plan.')
            return redirect('meal_plan_calendar')
        
        # Get max sort order for this day
        max_order = MealPlanRecipe.objects.filter(
            meal_plan_day=meal_plan_day
        ).aggregate(Max('sort_order'))['sort_order__max'] or 0
        
        # Create the meal plan recipe
        MealPlanRecipe.objects.create(
            meal_plan_day=meal_plan_day,
            recipe=recipe,
            servings=int(servings),
            sort_order=max_order + 1
        )
        
        messages.success(request, f'Added "{recipe.recipe_name}" to {meal_plan_day.date.strftime("%A, %B %d")}')
        
    except (MealPlanDay.DoesNotExist, Recipe.DoesNotExist) as e:
        messages.error(request, 'Error adding recipe. Please try again.')
    
    # Redirect back to calendar with current view
    return redirect(f"{reverse('meal_plan_calendar')}?week={meal_plan_day.date.strftime('%Y-%m-%d')}")


@login_required
@require_POST
@permission_required('auth.can_edit_personal', raise_exception=True)
def remove_recipe_from_meal_plan(request, meal_plan_id):
    """Remove a recipe from a meal plan day"""
    meal_plan_recipe_id = request.POST.get('meal_plan_recipe_id')
    
    try:
        meal_plan_recipe = MealPlanRecipe.objects.get(meal_plan_recipe_id=meal_plan_recipe_id)
        meal_plan_day = meal_plan_recipe.meal_plan_day
        
        # Verify user owns this meal plan
        if meal_plan_day.meal_plan.created_by != request.user:
            messages.error(request, 'You do not have permission to modify this meal plan.')
            return redirect('meal_plan_calendar')
        
        recipe_name = meal_plan_recipe.recipe.recipe_name
        week_date = meal_plan_day.date.strftime('%Y-%m-%d')
        
        meal_plan_recipe.delete()
        
        messages.success(request, f'Removed "{recipe_name}" from the meal plan')
        
        return redirect(f"{reverse('meal_plan_calendar')}?week={week_date}")
        
    except MealPlanRecipe.DoesNotExist:
        messages.error(request, 'Recipe not found.')
        return redirect('meal_plan_calendar')

def round_shopping_quantity(qty, unit):
    """
    Round quantities intelligently based on unit type for shopping lists.
    NEVER rounds down - always rounds UP to ensure you have enough.
    - COUNT units: Round UP to whole numbers (min 1)
    - WEIGHT/VOLUME: Round UP to nearest sensible number
    - OTHER: Round UP to whole numbers
    """
    import math
    
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

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
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
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
    from collections import defaultdict
    
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

@login_required
@require_POST
@permission_required('auth.can_edit_personal', raise_exception=True)
def send_meal_plan_shopping_list(request, meal_plan_id):
    """Send meal plan shopping list via email"""
    
    try:
        data = json.loads(request.body)
        
        meal_plan_name = data.get('meal_plan_name')
        date_range = data.get('date_range')
        total_recipes = data.get('total_recipes')
        email = data.get('email')
        ingredients_by_category = data.get('ingredients', {})
        
        # Validate
        if not email:
            return JsonResponse({'success': False, 'error': 'Email address is required'}, status=400)
        
        if not ingredients_by_category:
            return JsonResponse({'success': False, 'error': 'No ingredients to send'}, status=400)
        
        # Build email content
        subject = f'🛒 Shopping List for {meal_plan_name}'
        
        # Plain text version
        text_content = f"""Shopping List for {meal_plan_name}

{date_range}
{total_recipes} recipes

Items to Buy:
"""
        
        for category in sorted(ingredients_by_category.keys()):
            text_content += f"\n{category}:\n"
            for item in ingredients_by_category[category]:
                qty = item['quantity']
                # Format quantity nicely
                if qty % 1 == 0:
                    qty_str = f"{int(qty)}"
                else:
                    qty_str = f"{qty:.2f}".rstrip('0').rstrip('.')
                text_content += f"☐ {qty_str} {item['unit']} {item['ingredient']}\n"
        
        text_content += "\n---\nGenerated by ALIVENTE ONLINE - Recipe Management"
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            color: #2c3e50;
        }}
        .header {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 5px 0;
            opacity: 0.95;
        }}
        .category {{
            margin-bottom: 25px;
        }}
        .category-header {{
            color: #28a745;
            font-size: 20px;
            font-weight: 600;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 15px;
        }}
        ul {{
            list-style: none;
            padding-left: 0;
        }}
        li {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        li:hover {{
            background: #f8f9fa;
        }}
        li:last-child {{
            border-bottom: none;
        }}
        .checkbox {{
            width: 18px;
            height: 18px;
            border: 2px solid #28a745;
            border-radius: 3px;
            flex-shrink: 0;
        }}
        .quantity {{
            font-weight: 600;
            color: #28a745;
            margin-right: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 Shopping List</h1>
        <p><strong>{meal_plan_name}</strong></p>
        <p>{date_range}</p>
        <p>{total_recipes} recipes</p>
    </div>
"""
        
        # Add categories
        for category in sorted(ingredients_by_category.keys()):
            html_content += f"""
    <div class="category">
        <div class="category-header">📌 {category}</div>
        <ul>
"""
            for item in ingredients_by_category[category]:
                qty = item['quantity']
                if qty % 1 == 0:
                    qty_str = f"{int(qty)}"
                else:
                    qty_str = f"{qty:.2f}".rstrip('0').rstrip('.')
                
                html_content += f"""
            <li>
                <div class="checkbox"></div>
                <span><span class="quantity">{qty_str} {item['unit']}</span> {item['ingredient']}</span>
            </li>
"""
            html_content += """
        </ul>
    </div>
"""
        
        html_content += f"""
    <div class="footer">
        <p>Generated by <strong>ALIVENTE ONLINE</strong> - Recipe Management</p>
        <p>{datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>
</body>
</html>
"""
        
        # Send email using same method as recipe shopping list
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        return JsonResponse({
            'success': True,
            'message': f'Shopping list sent to {email}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def measurement_units_management(request):
    from collections import defaultdict

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
    """Add a new measurement unit"""
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
    """Update measurement unit name, abbreviation, and type"""
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
            # Already a favourite — remove it
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

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def check_unit_usage(request):
    """Check if measurement unit is used in recipes, ingredients, or conversions"""
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
    """Delete measurement unit if not used anywhere"""
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

# ============================================
# FILE EXTRACTION FUNCTIONS
# ============================================

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_text_from_docx(file):
    """Extract text from Word document"""
    try:
        doc = Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error reading Word document: {str(e)}")


def extract_text_from_image(file):
    """For images, we'll pass directly to Claude's vision API"""
    # Convert to base64 for Claude API
    try:
        image = Image.open(file)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")


# ============================================
# AI EXTRACTION FUNCTION
# ============================================

# Replace the extract_recipe_with_ai function in your views.py

def extract_recipe_with_ai(content, file_type):
    """Use Claude AI to extract recipe data with structured ingredients"""
    
    # Get API key from settings
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not found in settings")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Updated prompt for structured ingredient extraction
    system_prompt = """You are a recipe extraction expert. Extract recipe information from the provided content and return it in JSON format.

Extract the following fields:
- recipe_name: The name of the recipe
- description: A brief description (if available)
- prep_time: Preparation time in minutes (number only)
- cook_time: Cooking time in minutes (number only)
- total_time: Total time in minutes (number only)
- servings: Number of servings (number only)
- ingredients: Array of ingredient objects with these fields:
  * quantity: The amount (e.g., "2", "1/4", "1.5") - extract the number only
  * measurement: The unit (e.g., "cups", "tablespoons", "teaspoons", "packets", "cloves") - use singular lowercase
  * ingredient: The ingredient name (e.g., "flour", "olive oil", "frozen artichokes")
  * preparation: Any preparation notes (e.g., "chopped", "diced", "minced", "grated") - empty string if none
- instructions: Array of instruction strings (step by step)

For ingredients, parse each one carefully:
Example: "2 packets Frozen Artichokes" should be:
  {"quantity": "2", "measurement": "packets", "ingredient": "Frozen Artichokes", "preparation": ""}

Example: "1/4 teaspoon salt" should be:
  {"quantity": "1/4", "measurement": "teaspoon", "ingredient": "salt", "preparation": ""}

Example: "2 tablespoons olive oil, extra virgin" should be:
  {"quantity": "2", "measurement": "tablespoons", "ingredient": "olive oil", "preparation": "extra virgin"}

Example: "1 teaspoon minced fresh garlic" should be:
  {"quantity": "1", "measurement": "teaspoon", "ingredient": "fresh garlic", "preparation": "minced"}

Return ONLY valid JSON with these fields. If a field is not found, use null for numbers or empty string/array for text."""

    import time

    for attempt in range(3):
        try:
            if file_type in ['jpg', 'jpeg', 'png']:
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": f"image/{file_type}",
                                        "data": content,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "Extract the recipe information from this image and return it in the JSON format specified."
                                }
                            ],
                        }
                    ],
                    system=system_prompt
                )
            else:
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Extract the recipe information from this text and return it in the JSON format specified:\n\n{content}"
                        }
                    ],
                    system=system_prompt
                )

            # Parse the response
            response_text = message.content[0].text

            # Extract JSON from response (Claude might wrap it in markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            recipe_data = json.loads(response_text)

            # Validate and set defaults
            recipe_data.setdefault('recipe_name', 'Imported Recipe')
            recipe_data.setdefault('description', '')
            recipe_data.setdefault('prep_time', None)
            recipe_data.setdefault('cook_time', None)
            recipe_data.setdefault('total_time', None)
            recipe_data.setdefault('servings', 4)
            recipe_data.setdefault('ingredients', [])
            recipe_data.setdefault('instructions', [])

            # Ensure ingredients have all required fields
            for ing in recipe_data['ingredients']:
                ing.setdefault('quantity', '')
                ing.setdefault('measurement', '')
                ing.setdefault('ingredient', '')
                ing.setdefault('preparation', '')

            return recipe_data

        except json.JSONDecodeError as e:
            print(f"AI JSON Parse Error: {str(e)}")
            print(f"Raw response was: {response_text}")
            return None
        except Exception as e:
            import traceback
            print(f"AI Extraction Error (attempt {attempt + 1}): {str(e)}")
            if attempt < 2:
                wait_time = (attempt + 1) * 3  # 3s, then 6s
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(traceback.format_exc())
                return None

# AJAX endpoint to add new measurement
@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_measurement_ajax(request):
    """Add new measurement unit via AJAX"""
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

# AJAX endpoint to add new ingredient
@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_ingredient_ajax(request):
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

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def add_preparation_ajax(request):
    """Add new preparation method via AJAX"""
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
