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
        # Edit-level ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â POST creates the recipe
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
                        amount=convert_to_decimal(quantity_str),  # ÃƒÂ¢Ã¢â‚¬Â Ã‚Â CHANGED
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
    ingredient_categories = IngredientCategory.objects.all().order_by('name')  # ÃƒÂ¢Ã¢â‚¬Â Ã‚Â ADD THIS LINE

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
        'all_units': all_units,  # ÃƒÂ¢Ã¢â‚¬Â Ã‚Â ADD THIS
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
            # Already a favourite ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â remove it
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


