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


### LEASE TEMPLATE GENERATOR ###
import re

@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
@require_POST
def spell_check_instructions(request):
    """Spell check recipe instructions"""
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

def is_superuser(user):
    """Check if user is superuser"""
    return user.is_superuser

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def generate_lease_agreement_view(request):
    """
    View to display the lease agreement generation form and handle document generation
    """
    # Get properties and tenants from your actual models
    properties = props.objects.filter(prop_available_for_rent='Yes').order_by('prop_name')
    tenants = tenant.objects.select_related('prop').all().order_by('tenant_name')
    
    context = {
        'properties': properties,
        'tenants': tenants,
    }
    
    if request.method == 'POST':
        try:
            # Extract form data
            country = request.POST.get('country')
            language = request.POST.get('language')
            property_id = request.POST.get('property')
            tenant_id = request.POST.get('tenant')
            
            # Get additional data from modal (JSON format)
            additional_data_json = request.POST.get('additional_data', '{}')
            
            # Validate additional_data is valid JSON
            try:
                additional_data = json.loads(additional_data_json)
            except json.JSONDecodeError:
                additional_data = {}
                logger.warning(f"Invalid JSON in additional_data: {additional_data_json}")
            
            # Validate required fields
            if not all([country, language, property_id, tenant_id]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'generate_lease_agreement.html', context)
            
            # Validate additional data was provided
            if not additional_data:
                messages.error(request, 'Please complete the additional data by clicking "Review & Complete Data".')
                return render(request, 'generate_lease_agreement.html', context)
            
            # Get property object from database
            try:
                property_obj = get_object_or_404(props, prop_id=property_id)
            except:
                messages.error(request, 'Selected property not found.')
                return render(request, 'generate_lease_agreement.html', context)
            
            # Handle tenant (existing or new)
            if tenant_id == 'new_tenant':
                # Create a mock tenant object with new tenant data
                new_tenant_data = additional_data.get('new_tenant_data', {})
                if not new_tenant_data.get('tenant_name'):
                    messages.error(request, 'Tenant name is required for new tenant.')
                    return render(request, 'generate_lease_agreement.html', context)
                
                tenant_obj = type('MockTenant', (), {
                    'tenant_name': new_tenant_data.get('tenant_name', ''),
                    'tenant_type': new_tenant_data.get('tenant_type', 'Individual'),
                    'tenant_passport_id': new_tenant_data.get('tenant_passport_id', ''),
                    'tenant_passport_country': new_tenant_data.get('tenant_passport_country', ''),
                    'tenant_email': new_tenant_data.get('tenant_email', ''),
                    'tenant_contact_number': new_tenant_data.get('tenant_contact_number', ''),
                    'tenant_address': new_tenant_data.get('tenant_address', ''),
                    'tenant_rent': None,
                    'tenant_deposit': None,
                    'tenant_lease_start_date': None,
                    'tenant_lease_end_date': None,
                    'tenant_levies': None,
                    'tenant_payment_terms': None,
                    'tenant_rental_type': None,
                    'tenant_renewal': None,
                    'tenant_renewal_period': None,
                })()
            else:
                # Get existing tenant
                try:
                    tenant_obj = get_object_or_404(tenant, tenant_id=tenant_id)
                except:
                    messages.error(request, 'Selected tenant not found.')
                    return render(request, 'generate_lease_agreement.html', context)
            
            # Generate the lease agreement
            document_path = generate_lease_document(
                country=country,
                language=language,
                property_obj=property_obj,
                tenant_obj=tenant_obj,
                additional_data=additional_data
            )
            
            if document_path:
                # Create filename
                filename = f'lease_agreement_{property_obj.prop_name}_{tenant_obj.tenant_name}_{country}_{language}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
                filename = filename.replace(' ', '_').replace('/', '_')  # Clean filename
                
                # Return the generated document
                try:
                    response = FileResponse(
                        open(document_path, 'rb'),
                        as_attachment=True,
                        filename=filename
                    )
                    # messages.success(request, 'Lease agreement generated successfully!')
                    return response
                except Exception as e:
                    logger.error(f"Error returning file: {str(e)}")
                    messages.error(request, 'Error downloading the generated document.')
            else:
                messages.error(request, 'Error generating lease agreement. Please check the template file exists.')
                
        except Exception as e:
            logger.error(f"Error generating lease agreement: {str(e)}")
            messages.error(request, f'An error occurred while generating the lease agreement: {str(e)}')
    
    return render(request, 'generate_lease_agreement.html', context)

def get_ordinal_day(day):
    """Convert day number to ordinal (1st, 2nd, 3rd, etc.)"""
    day = int(day)
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"

def number_to_words_greek(num):
    """Convert number to Greek words with proper capitalization"""
    if num == 0:
        return "Μηδέν"
    
    ones = ["", "Ένα", "Δύο", "Τρία", "Τέσσερα", "Πέντε", "Έξι", "Επτά", "Οκτώ", "Εννέα",
            "Δέκα", "Έντεκα", "Δώδεκα", "Δεκατρία", "Δεκατέσσερα", "Δεκαπέντε", 
            "Δεκαέξι", "Δεκαεπτά", "Δεκαοκτώ", "Δεκαεννέα"]
    
    tens = ["", "", "Είκοσι", "Τριάντα", "Σαράντα", "Πενήντα", "Εξήντα", "Εβδομήντα", "Ογδόντα", "Ενενήντα"]
    
    hundreds = ["", "Εκατό", "Διακόσια", "Τριακόσια", "Τετρακόσια", "Πεντακόσια", 
                "Εξακόσια", "Επτακόσια", "Οκτακόσια", "Εννιακόσια"]
    
    num = int(num)  # Remove decimals
    
    if num < 20:
        return ones[num]
    elif num < 100:
        return tens[num // 10] + ("" if num % 10 == 0 else " " + ones[num % 10])
    elif num < 1000:
        return hundreds[num // 100] + ("" if num % 100 == 0 else " " + number_to_words_greek(num % 100))
    elif num < 1000000:
        thousands = num // 1000
        remainder = num % 1000
        
        if thousands == 1:
            thousands_text = "Χίλια"
        elif thousands < 20:
            thousands_text = ones[thousands] + " Χιλιάδες"
        else:
            thousands_text = number_to_words_greek(thousands) + " Χιλιάδες"
            
        return thousands_text + ("" if remainder == 0 else " " + number_to_words_greek(remainder))
    else:
        return str(int(num))  # Fallback for very large numbers

def format_date_greek(date_obj):
    """Convert date object to Greek format with ordinal day and Greek month name"""
    if not date_obj:
        return 'N/A'
    
    # Greek month names (genitive case for dates)
    greek_months = {
        1: "Ιανουαρίου", 2: "Φεβρουαρίου", 3: "Μαρτίου", 4: "Απριλίου",
        5: "Μαΐου", 6: "Ιουνίου", 7: "Ιουλίου", 8: "Αυγούστου",
        9: "Σεπτεμβρίου", 10: "Οκτωβρίου", 11: "Νοεμβρίου", 12: "Δεκεμβρίου"
    }
    
    day = date_obj.day
    month = greek_months[date_obj.month]
    year = date_obj.year
    
    # Add Greek ordinal suffix to day
    ordinal_day = f"{day}η"
    
    return f"{ordinal_day} {month} {year}"

def translate_to_greek(text):
    """Translate common property and name terms to Greek"""
    if not text or text.strip() == '':
        return text
    
    # Complete translations dictionary
    translations = {
        # Common street types
        'Street': 'Οδός',
        'St': 'Οδός',
        'Avenue': 'Λεωφόρος',
        'Ave': 'Λεωφόρος',
        'Road': 'Δρόμος',
        'Rd': 'Δρόμος',
        'Lane': 'Δρομάκι',
        'Square': 'Πλατεία',
        'Plaza': 'Πλατεία',
        
        # Specific street names and areas
        'Eleftheroupoleos': 'Ελευθερουπόλεως',
        'Agias': 'Αγίας',
        'Annas': 'Άννας',
        'Dikaiosynis': 'Δικαιοσύνης',
        'Ionion': 'Ιόνιον',
        'Aristoteli': 'Αριστοτέλη',
        'Valaoriti': 'Βαλαωρίτη',
        'Pindarou': 'Πινδάρου',
        'Evagora': 'Ευαγόρα',
        'Palikaridi': 'Παλικαρίδη',
        'Agios': 'Άγιος',
        'Dometios': 'Δομέτιος',
        'Aristoteli Valaoriti': 'Αριστοτέλη Βαλαωρίτη',
        
        # Common area names in Cyprus
        'Nicosia': 'Λευκωσία',
        'Limassol': 'Λεμεσός',
        'Larnaca': 'Λάρνακα',
        'Paphos': 'Πάφος',
        'Famagusta': 'Αμμόχωστος',
        'Kyrenia': 'Κερύνεια',
        'Engomi': 'Έγκωμη',
        'Strovolos': 'Στρόβολος',
        'Lakatamia': 'Λακαταμια',
        'Latsia': 'Λατσιά',
        'Aglandjia': 'Αγλαντζιά',
        'Agia Thekla': 'Αγία Θέκλα',
        'Sotira': 'Σωτήρα',
        'Cyprus': 'Κύπρος',
        'Agios Dometios': 'Άγιος Δομέτιος',
        
        # Common building types
        'Flat': 'Διαμέρισμα',
        'Apartment': 'Διαμέρισμα',
        'House': 'Σπίτι',
        'Villa': 'Βίλα',
        'Villas': 'Βίλες',
        'Office': 'Γραφείο',
        'Building': 'Κτίριο',
        'Complex': 'Συγκρότημα',
        'Tower': 'Πύργος',
        'Center': 'Κέντρο',
        'Centre': 'Κέντρο',
        
        # FURNITURE AND APPLIANCES
        'Television': 'Τηλεόραση',
        'Televisions': 'Τηλεοράσεις',
        'TV': 'Τηλεόραση',
        'TVs': 'Τηλεοράσεις',
        'Washing Machine': 'Πλυντήριο',
        'Washing Machines': 'Πλυντήρια',
        'Dishwasher': 'Πλυντήριο Πιάτων',
        'Dishwashers': 'Πλυντήρια Πιάτων',
        'Oven': 'Φούρνος',
        'Ovens': 'Φούρνοι',
        'Stove': 'Ηλεκτρικές εστίες',
        'Stoves': 'Ηλεκτρικές εστίες',
        'Extractor Fan': 'Απορροφητήρας',
        'Extractor Fans': 'Απορροφητήρες',
        'Fridge Freezer': 'Ψυγειοκαταψύκτης',
        'Fridge Freezers': 'Ψυγειοκαταψύκτες',
        'Airconditioner': 'Κλιματιστικό',
        'Airconditioners': 'Κλιματιστικά',
        'Air Conditioner': 'Κλιματιστικό',
        'Air Conditioners': 'Κλιματιστικά',
        'Microwave': 'Φούρνος Μικροκυμάτων',
        'Microwaves': 'Φούρνοι Μικροκυμάτων',
        'Three Seater Couch': 'Τριθέσιος Καναπές',
        'Three Seater Couches': 'Τριθέσιοι Καναπέδες',
        'Two Seater Couch': 'Διθέσιος Καναπές',
        'Two Seater Couches': 'Διθέσιοι Καναπέδες',
        'Lounge Chair': 'Πολυθρόνα',
        'Lounge Chairs': 'Πολυθρόνες',
        'Coffee Tables': 'Τραπεζάκια Σαλονιού',
        'Coffee Table': 'Τραπεζάκι Σαλονιού',
        'Corner Tables': 'Γωνιακά Τραπέζια',
        'Corner Table': 'Γωνιακό Τραπέζι',
        'Standing Lamps': 'Φωτιστικά Δαπέδου',
        'Standing Lamp': 'Φωτιστικό Δαπέδου',
        'Table Lamps': 'Φωτιστικά Τραπεζιού',
        'Table Lamp': 'Φωτιστικό Τραπεζιού',
        'Dining Tables': 'Τραπεζαρίες',
        'Dining Table': 'Τραπεζαρία',
        'Dining Chairs': 'Καρέκλες Τραπεζαρίας',
        'Dining Chair': 'Καρέκλα Τραπεζαρίας',
        'Single Beds': 'Μονά Κρεβάτια',
        'Single Bed': 'Μονό Κρεβάτι',
        'Queen Beds': 'Διπλά Κρεβάτια',
        'Queen Bed': 'Διπλό Κρεβάτι',
        'Double Bed': 'Διπλό Κρεβάτι',
        'Double Beds': 'Διπλά Κρεβάτια',
        'Outside Tables': 'Εξωτερικά Τραπέζια',
        'Outside Table': 'Εξωτερικό Τραπέζι',
        'Outside Chairs': 'Εξωτερικές Καρέκλες',
        'Outside Chair': 'Εξωτερική Καρέκλα',
        'TV Table': 'Τραπέζι Tηλεόρασης',
        'TV Tables': 'Τραπέζια Tηλεόρασης',
        'Bed': 'Κρεβάτι',
        'Beds': 'Κρεβάτια',
        'Sofa': 'Καναπές',
        'Sofas': 'Καναπέδες',
        'Table': 'Τραπέζι',
        'Tables': 'Τραπέζια',
        'Chair': 'Καρέκλα',
        'Chairs': 'Καρέκλες',
        'Lamp': 'Λάμπα',
        'Lamps': 'Λάμπες',
        'Desk': 'Γραφείο',
        'Desks': 'Γραφεία',
        'Wardrobe': 'Ντουλάπα',
        'Wardrobes': 'Ντουλάπες',
        'Refrigerator': 'Ψυγείο',
        'Refrigerators': 'Ψυγεία',
        'Fridge': 'Ψυγείο',
        'Fridges': 'Ψυγεία',
        'Heater': 'Θερμάστρα',
        'Heaters': 'Θερμάστρες',
        'Curtain': 'Κουρτίνα',
        'Curtains': 'Κουρτίνες',
        'Mirror': 'Καθρέφτης',
        'Mirrors': 'Καθρέφτες',
        'Bookshelf': 'Βιβλιοθήκη',
        'Bookshelves': 'Βιβλιοθήκες',
        'AC': 'Κλιματιστικό',
        'ACs': 'Κλιματιστικά',
        'Bedside Table': 'Κομοδίνο',
        'Bedside Tables': 'Κομοδίνα',
        'Roller Blind': 'Ρολό',
        'Roller Blinds': 'Ρολά',
        'Stool': 'Σκαμπό',
        'Stools': 'Σκαμπό',
        
        # Keys - Complete singular and plural forms
        'Key': 'Κλειδί',
        'Keys': 'Κλειδιά',
        'Front Door': 'Κεντρική Πόρτα',
        'Front Door Key': 'Κλειδί Κεντρικής Πόρτας',
        'Front Door Keys': 'Κλειδιά Κεντρικής Πόρτας',
        'Main Door': 'Κεντρική Πόρτα',
        'Main Door Key': 'Κλειδί Κεντρικής Πόρτας',
        'Main Door Keys': 'Κλειδιά Κεντρικής Πόρτας',
        'Building Key': 'Κλειδί Κτιρίου',
        'Building Keys': 'Κλειδιά Κτιρίου',
        'Entrance': 'Είσοδος',
        'Entrance Key': 'Κλειδί Εισόδου',
        'Entrance Keys': 'Κλειδιά Εισόδου',
        'Mailbox': 'Γραμματοκιβώτιο',
        'Mailbox Key': 'Κλειδί Γραμματοκιβωτίου',
        'Mailbox Keys': 'Κλειδιά Γραμματοκιβωτίου',
        'Post Box Key': 'Κλειδί Γραμματοκιβωτίου',
        'Post Box Keys': 'Κλειδιά Γραμματοκιβωτίου',
        'Storeroom Key': 'Κλειδί Αποθήκης',
        'Storeroom Keys': 'Κλειδιά Αποθήκης',
        'Storage Key': 'Κλειδί Αποθήκης',
        'Storage Keys': 'Κλειδιά Αποθήκης',
        'Garage Key': 'Κλειδί Γκαράζ',
        'Garage Keys': 'Κλειδιά Γκαράζ',
        'Garage': 'Γκαράζ',
        'Storage': 'Αποθήκη',
        'Balcony Key': 'Κλειδί Μπαλκονιού',
        'Balcony Keys': 'Κλειδιά Μπαλκονιού',
        'Balcony': 'Μπαλκόνι',
        'Terrace Key': 'Κλειδί Βεράντας',
        'Terrace Keys': 'Κλειδιά Βεράντας',
        'Terrace': 'Βεράντα',
        
        # Common names - CORRECTED
        'Demetri': 'Δημήτρης',
        'Manias': 'Μανιάς',
        'Foti': 'Φώτι',  # CORRECTED - was Φώτης
        'Pitta': 'Πίττα',
        'George': 'Γεώργιος',
        'Maria': 'Μαρία',
        'Andreas': 'Ανδρέας',
        'Christina': 'Χριστίνα',
        'Kostas': 'Κώστας',
        'Nikos': 'Νίκος',
        
        # Company terms
        'Limited': 'Περιορισμένη',
        'Ltd': 'Περιορισμένη',
        'Company': 'Εταιρεία',
        'Co': 'Εταιρεία',
    }
    
    # Simple direct matching - no regex complications
    if text in translations:
        return translations[text]
    
    # Case insensitive fallback
    for eng, greek in translations.items():
        if text.lower() == eng.lower():
            return greek
    
    # Handle compound names and addresses by translating individual parts
    if ' ' in text:
        words = text.split()
        translated_words = []
        for word in words:
            # Clean punctuation
            clean_word = word.strip('.,;:!?()[]{}')
            punctuation = word[len(clean_word):]
            
            if clean_word in translations:
                translated_words.append(translations[clean_word] + punctuation)
            else:
                # Case insensitive check
                found = False
                for eng, greek in translations.items():
                    if clean_word.lower() == eng.lower():
                        translated_words.append(greek + punctuation)
                        found = True
                        break
                if not found:
                    translated_words.append(word)
        
        result = ' '.join(translated_words)
        if result != text:
            return result
    
    return text

def generate_lease_document(country, language, property_obj, tenant_obj, additional_data):
    """
    Generate the actual lease agreement document using Word templates
    """
    try:
        # Define template paths based on country and language
        template_mapping = {
            'cyprus': {
                'english': 'lease_templates/cyprus_english_lease_template.docx',
                'greek': 'lease_templates/cyprus_greek_lease_template.docx'
            },
            'greece': {
                'greek': 'lease_templates/greece_greek_lease_template.docx'
            },
            'spain': {
                'spanish': 'lease_templates/spain_spanish_lease_template.docx'
            }
        }
        
        # Get template path
        template_filename = template_mapping.get(country, {}).get(language)
        if not template_filename:
            logger.error(f"No template mapping found for country: {country}, language: {language}")
            return None
            
        template_path = os.path.join(settings.BASE_DIR, 'pages', 'templates', template_filename)

        # Check if template exists
        if not os.path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            # Try fallback - create basic document
            return create_basic_lease_document(country, language, property_obj, tenant_obj, additional_data)
        
        # Load template
        doc = DocxTemplate(template_path)
        
        # Prepare data for template
        template_data = prepare_lease_template_data(
            country, language, property_obj, tenant_obj, additional_data
        )
        
        # Render document
        doc.render(template_data)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_file.name)
        
        logger.info(f"Lease document generated successfully: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Error in generate_lease_document: {str(e)}")
        return None

def prepare_lease_template_data(country, language, property_obj, tenant_obj, additional_data):
    """
    Prepare data dictionary for the lease agreement template using your models
    """
    # Get current date components
    current_date = datetime.now()
    
    # Helper function to convert numbers to words with proper capitalization
    def number_to_words(num):
        """Convert number to English words with proper capitalization"""
        if num == 0:
            return "Zero"
        
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", 
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", 
                "Seventeen", "Eighteen", "Nineteen"]
        
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        num = int(num)  # Remove decimals
        
        if num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + ("" if num % 10 == 0 else " " + ones[num % 10])
        elif num < 1000:
            return ones[num // 100] + " Hundred" + ("" if num % 100 == 0 else " " + number_to_words(num % 100))
        elif num < 1000000:
            return number_to_words(num // 1000) + " Thousand" + ("" if num % 1000 == 0 else " " + number_to_words(num % 1000))
        else:
            return str(int(num))  # Fallback for very large numbers
    
    # Helper function to pluralize items
    def pluralize_item(item_name, count):
        """Add 's' to item names when count > 1"""
        if count > 1:
            # Handle special cases - check the last word only for compound items
            words = item_name.split()
            last_word = words[-1]
            
            if last_word.endswith('y') and len(last_word) > 1 and last_word[-2] not in 'aeiou':
                # Only change y to ies for words ending in consonant + y (like "Key" but not "Boy")
                words[-1] = last_word[:-1] + 'ies'
                return ' '.join(words)
            elif last_word.endswith(('s', 'sh', 'ch', 'x', 'z')):
                words[-1] = last_word + 'es'
                return ' '.join(words)
            else:
                words[-1] = last_word + 's'
                return ' '.join(words)
        return item_name
    
    # Get dates from additional_data or tenant object
    start_date_str = additional_data.get('start_date') or (
        tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') 
        if hasattr(tenant_obj, 'tenant_lease_start_date') and tenant_obj.tenant_lease_start_date else ''
    )
    end_date_str = additional_data.get('end_date') or (
        tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') 
        if hasattr(tenant_obj, 'tenant_lease_end_date') and tenant_obj.tenant_lease_end_date else ''
    )
    
    # Convert date strings to datetime objects
    start_date_obj = None
    end_date_obj = None
    duration_days = 0
    duration_months = 0
    
    try:
        if start_date_str:
            start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if start_date_obj and end_date_obj:
            duration_days = (end_date_obj - start_date_obj).days
            duration_months = max(1, round(duration_days / 30.44))  # More accurate month calculation
    except ValueError as e:
        logger.warning(f"Date parsing error: {str(e)}")
    
    # Get financial information - prefer additional_data over database (remove decimals)
    monthly_rent = int(float(additional_data.get('monthly_rent') or (
        tenant_obj.tenant_rent if hasattr(tenant_obj, 'tenant_rent') and tenant_obj.tenant_rent else 0
    )))
    security_deposit = int(float(additional_data.get('security_deposit') or (
        tenant_obj.tenant_deposit if hasattr(tenant_obj, 'tenant_deposit') and tenant_obj.tenant_deposit else 0
    )))
    communal_expenses = int(float(additional_data.get('communal_expenses', 0)))
    
    # Get extension information
    extension_period = int(additional_data.get('extension_period', 0))
    extension_date_str = additional_data.get('extension_date', '')
    extension_date_obj = None
    if extension_date_str:
        try:
            extension_date_obj = datetime.strptime(extension_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Handle rental increase percentage (remove decimals if whole number)
    rental_increase = float(additional_data.get('rental_increase', 0))
    rental_increase_formatted = f"{int(rental_increase)}" if rental_increase == int(rental_increase) else f"{rental_increase}"
    
    # Get currency symbol based on country
    currency_symbols = {
        'cyprus': '€',
        'greece': '€',
        'spain': '€'
    }
    currency = currency_symbols.get(country, '€')
    
    # Build full property address
    address_parts = [
        property_obj.prop_address1,
        property_obj.prop_address2,
        property_obj.prop_suburb,
        property_obj.prop_city,
        property_obj.prop_province,
        property_obj.prop_country,
        property_obj.prop_pcode
    ]
    full_address = ', '.join([part for part in address_parts if part and part.strip()])
    
    # Get tenant information (handle both existing and new tenants)
    if additional_data.get('is_new_tenant') and additional_data.get('new_tenant_data'):
        new_tenant_data = additional_data['new_tenant_data']
        tenant_name = new_tenant_data.get('tenant_name', 'N/A')
        tenant_address = new_tenant_data.get('tenant_address', 'N/A')
        tenant_phone = new_tenant_data.get('tenant_contact_number', 'N/A')
        tenant_email = new_tenant_data.get('tenant_email', 'N/A')
        tenant_type = new_tenant_data.get('tenant_type', 'Individual')
        
        if tenant_type == 'Company':
            tenant_passport_id = 'N/A'
            tenant_passport_country = 'N/A'
            tenant_registration_number = new_tenant_data.get('tenant_registration_number', 'N/A')
            tenant_contact_person = new_tenant_data.get('tenant_contact_person', 'N/A')
        else:
            tenant_passport_id = new_tenant_data.get('tenant_passport_id', 'N/A')
            tenant_passport_country = new_tenant_data.get('tenant_passport_country', 'N/A')
            tenant_registration_number = 'N/A'
            tenant_contact_person = 'N/A'
    else:
        tenant_name = tenant_obj.tenant_name or 'N/A'
        # Use property address as tenant address for existing tenants
        tenant_address = full_address or 'N/A'
        tenant_phone = getattr(tenant_obj, 'tenant_contact_number', 'N/A') or 'N/A'
        tenant_email = getattr(tenant_obj, 'tenant_email', 'N/A') or 'N/A'
        tenant_type = getattr(tenant_obj, 'tenant_type', 'Individual') or 'Individual'
        tenant_contact_person = getattr(tenant_obj, 'tenant_contact_person', 'N/A') or 'N/A'

        # Get additional information for existing tenants from form data
        existing_tenant_data = additional_data.get('existing_tenant_data', {})
        if tenant_type == 'Company':
            tenant_passport_id = 'N/A'
            tenant_passport_country = 'N/A'
            tenant_registration_number = existing_tenant_data.get('tenant_registration_number', 'N/A')
        else:
            tenant_passport_id = existing_tenant_data.get('tenant_passport_id', 'N/A')
            tenant_passport_country = existing_tenant_data.get('tenant_passport_country', 'N/A')
            tenant_registration_number = 'N/A'
    
    # Second tenant information
    has_second_tenant = additional_data.get('has_second_tenant', False)
    second_tenant_data = additional_data.get('second_tenant_data', {})
    
    # Second tenant variables for template
    if has_second_tenant and second_tenant_data:
        second_tenant_name = second_tenant_data.get('tenant_name', 'N/A')
        second_tenant_passport_id = second_tenant_data.get('tenant_passport_id', 'N/A')
        second_tenant_passport_country = second_tenant_data.get('tenant_passport_country', 'N/A')
        second_tenant_address = second_tenant_data.get('tenant_address', 'N/A')
        second_tenant_contact_number = second_tenant_data.get('tenant_contact_number', 'N/A')
        second_tenant_email = second_tenant_data.get('tenant_email', 'N/A')
    else:
        second_tenant_name = ''
        second_tenant_passport_id = ''
        second_tenant_passport_country = ''
        second_tenant_address = ''
        second_tenant_contact_number = ''
        second_tenant_email = ''
    
    # Process furniture and appliances
    furniture_items = {}
    furniture_list = []
    furniture_list_greek = []
    for key, value in additional_data.items():
        if key.startswith('furniture_') and int(value or 0) > 0:
            count = int(value)
            item_name = key.replace('furniture_', '').replace('_', ' ').title()
            pluralized_name = pluralize_item(item_name, count)
            furniture_items[pluralized_name] = count
            furniture_list.append(f"{count} x {pluralized_name}")
            
            # Create Greek version - translate the pluralized name
            item_name_greek = translate_to_greek(pluralized_name)
            furniture_list_greek.append(f"{count} x {item_name_greek}")
            
    # Get fully furnished checkbox value
    fully_furnished = additional_data.get('fully_furnished') == 'true'
    
    # Get parking and storeroom checkbox values
    has_parking = additional_data.get('amenity_parking') == True  # Boolean, not string
    has_storeroom = additional_data.get('amenity_storeroom') == True  # Boolean, not string

    # Process keys
    keys_items = {}
    keys_list = []
    keys_list_greek = []
    for key, value in additional_data.items():
        if key.startswith('keys_') and int(value or 0) > 0:
            count = int(value)
            key_name = key.replace('keys_', '').replace('_', ' ').title() + ' Key'
            pluralized_key = pluralize_item(key_name, count)
            keys_items[pluralized_key] = count
            keys_list.append(f"{count} x {pluralized_key}")
            
            # Create Greek version - translate the pluralized key name
            key_name_greek = translate_to_greek(pluralized_key)
            keys_list_greek.append(f"{count} x {key_name_greek}")
            
    # Prepare template data
    template_data = {
        # Current date components with ordinal day
        'today_day': get_ordinal_day(current_date.day),
        'today_month': current_date.strftime('%B'),
        'today_year': current_date.strftime('%Y'),
        'today_date': current_date.strftime('%B %d, %Y'),
        
        # Greek date formats
        'today_date_greek': format_date_greek(current_date.date()),
        'lease_start_date_greek': format_date_greek(start_date_obj) if start_date_obj else 'N/A',
        'lease_end_date_greek': format_date_greek(end_date_obj) if end_date_obj else 'N/A',
        
        # Document information
        'document_date': current_date.strftime('%B %d, %Y'),
        'document_id': f'LA-{current_date.strftime("%Y%m%d-%H%M%S")}',
        'country': country.title(),
        'language': language.title(),
        
        # Landlord information
        'landlord_name': additional_data.get('landlord_name', 'Alivente Limited'),
        'landlord_contact_person': additional_data.get('landlord_contact_person', 'Demetri Manias'),
        'landlord_contact_person_greek': translate_to_greek(additional_data.get('landlord_contact_person', 'Demetri Manias')),
        'landlord_registration_number': additional_data.get('landlord_registration_number', 'HE123456'),
        'landlord_phone': additional_data.get('landlord_phone', '+357-96668557'),
        'landlord_phone_number': additional_data.get('landlord_phone', '+357-96668557'),
        'landlord_email': additional_data.get('landlord_email', 'demetri.manias@alivente.com'),
        'landlord_address': additional_data.get('landlord_address', 'Alivente House, Dikaiosynis 13A, Engomi, Nicosia, Cyprus, 2412'),
        
        # Tenant information
        'tenant_name': tenant_name,
        'tenant_full_name': tenant_name,
        'tenant_passport_id': tenant_passport_id,
        'tenant_passport_country': tenant_passport_country,
        'tenant_address': tenant_address,
        'tenant_phone': tenant_phone,
        'tenant_email': tenant_email,
        'tenant_type': tenant_type,
        'tenant_registration_number': tenant_registration_number,
        'tenant_contact_person': tenant_contact_person,
        
        # Second tenant information
        'has_second_tenant': has_second_tenant,
        'second_tenant_name': second_tenant_name,
        'second_tenant_passport_id': second_tenant_passport_id,
        'second_tenant_passport_country': second_tenant_passport_country,
        'second_tenant_address': second_tenant_address,
        'second_tenant_contact_number': second_tenant_contact_number,
        'second_tenant_email': second_tenant_email,
        
        # Property information
        'property_name': property_obj.prop_name or 'N/A',
        'property_address': full_address or 'N/A',
        'property_address1': property_obj.prop_address1 or '',
        'property_address2': property_obj.prop_address2 or '',
        'property_suburb': property_obj.prop_suburb or '',
        'property_city': property_obj.prop_city or '',
        'property_province': property_obj.prop_province or '',
        'property_country': property_obj.prop_country or '',
        'property_pcode': property_obj.prop_pcode or '',
        'property_floor_area': property_obj.prop_floor_area or 'N/A',
        'property_year_built': property_obj.prop_year_built or 'N/A',
        
        # Property information - Greek translations
        'property_address1_greek': translate_to_greek(property_obj.prop_address1 or ''),
        'property_address2_greek': translate_to_greek(property_obj.prop_address2 or ''),
        'property_suburb_greek': translate_to_greek(property_obj.prop_suburb or ''),
        'property_city_greek': translate_to_greek(property_obj.prop_city or ''),
        'property_province_greek': translate_to_greek(property_obj.prop_province or ''),
        
        # Lease terms
        'lease_start_date': start_date_obj.strftime('%B %d, %Y') if start_date_obj else 'N/A',
        'lease_end_date': end_date_obj.strftime('%B %d, %Y') if end_date_obj else 'N/A',
        'lease_start_date_short': start_date_obj.strftime('%d/%m/%Y') if start_date_obj else 'N/A',
        'lease_end_date_short': end_date_obj.strftime('%d/%m/%Y') if end_date_obj else 'N/A',
        'duration_months': duration_months,
        'duration_months_words': number_to_words(duration_months),
        'duration_days': duration_days,
        
        # Financial terms - numbers (without decimals)
        'rental_amount': monthly_rent,
        'communal_expenses': communal_expenses,
        'security_deposit': security_deposit,
        'deposit_amount': security_deposit,
        
        # Financial terms - words (with proper capitalization)
        'rental_amount_words': number_to_words(monthly_rent),
        'communal_expenses_words': number_to_words(communal_expenses),
        'deposit_amount_words': number_to_words(security_deposit),
        
        # Greek financial terms in words
        'rental_amount_words_greek': number_to_words_greek(monthly_rent),
        'deposit_amount_words_greek': number_to_words_greek(security_deposit),
        'communal_expenses_words_greek': number_to_words_greek(communal_expenses),
        
        # Financial terms - with thousand separators (the template uses the raw numbers)
        'rental_amount': f'{monthly_rent:,}',
        'communal_expenses': f'{communal_expenses:,}',
        'security_deposit': f'{security_deposit:,}',
        
        # Additional formatted versions for compatibility
        'rental_amount_formatted': f'{currency}{monthly_rent:,}',
        'communal_expenses_formatted': f'{currency}{communal_expenses:,}',
        'deposit_amount_formatted': f'{currency}{security_deposit:,}',
        'security_deposit_formatted': f'{currency}{security_deposit:,}',
        'total_rent_formatted': f'{currency}{(monthly_rent * duration_months):,}' if duration_months else f'{currency}0',
        'monthly_rent_formatted': f'{currency}{monthly_rent:,}',
        
        # Extension and increase terms
        'lease_extension_period': extension_period,
        'lease_extension_period_words': number_to_words(extension_period),
        'lease_extension_period_words_greek': number_to_words_greek(extension_period),
        'lease_extension_date': extension_date_obj.strftime('%B %d, %Y') if extension_date_obj else 'N/A',
        'lease_extension_date_greek': format_date_greek(extension_date_obj) if extension_date_obj else 'N/A',
        'percentage_rental_increase': rental_increase_formatted,
        
        # Currency
        'currency': currency,
        
        # Furniture and appliances (with proper pluralization and comma-separated lists)
        'furniture_items': furniture_items,
        'furniture_list': ', '.join(furniture_list) if furniture_list else 'None',
        'furniture_list_greek': ', '.join(furniture_list_greek) if furniture_list_greek else 'Κανένα',
        'fully_furnished': fully_furnished,
        
        # Parking and Storeroom
        'has_parking': has_parking,
        'has_storeroom': has_storeroom,
        
        # Keys (with proper pluralization and comma-separated lists)
        'keys_items': keys_items,
        'keys_list': ', '.join(keys_list) if keys_list else 'None',
        'keys_list_greek': ', '.join(keys_list_greek) if keys_list_greek else 'Κανένα',
        
        # Legacy fields for compatibility
        'start_date': start_date_obj.strftime('%B %d, %Y') if start_date_obj else 'N/A',
        'end_date': end_date_obj.strftime('%B %d, %Y') if end_date_obj else 'N/A',
        'monthly_rent': monthly_rent,
        
        # Generation metadata
        'generation_timestamp': current_date.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return template_data

def create_basic_lease_document(country, language, property_obj, tenant_obj, additional_data):
    """
    Create a basic lease document when no template is available
    This is a fallback method for demonstration purposes
    """
    try:
        from docx import Document
        from docx.shared import Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # Helper function to pluralize items (for fallback function)
        def pluralize_item(item_name, count):
            """Add 's' to item names when count > 1"""
            if count > 1:
                # Handle special cases
                if item_name.endswith('y'):
                    return item_name[:-1] + 'ies'  # e.g., "Key" -> "Keys"
                elif item_name.endswith(('s', 'sh', 'ch', 'x', 'z')):
                    return item_name + 'es'
                else:
                    return item_name + 's'
            return item_name
        
        # Create a new document
        document = Document()
        
        # Add title
        title = document.add_heading('LEASE AGREEMENT', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add subtitle
        subtitle = document.add_paragraph(f'{country.title()} - {language.title()}')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        document.add_paragraph('')  # Empty line
        
        # Document info
        document.add_paragraph(f'Document ID: LA-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        document.add_paragraph(f'Generated: {datetime.now().strftime("%B %d, %Y")}')
        document.add_paragraph('')
        
        # Property information
        document.add_heading('Property Information', level=1)
        document.add_paragraph(f'Property Name: {property_obj.prop_name or "N/A"}')
        
        address_parts = [
            property_obj.prop_address1,
            property_obj.prop_address2,
            property_obj.prop_suburb,
            property_obj.prop_city,
            property_obj.prop_province,
            property_obj.prop_country,
            property_obj.prop_pcode
        ]
        full_address = ', '.join([part for part in address_parts if part])
        document.add_paragraph(f'Address: {full_address or "N/A"}')
        
        if property_obj.prop_floor_area:
            document.add_paragraph(f'Floor Area: {property_obj.prop_floor_area} m²')
        if property_obj.prop_year_built:
            document.add_paragraph(f'Year Built: {property_obj.prop_year_built}')
        
        document.add_paragraph('')
        
        # Tenant information
        document.add_heading('Tenant Information', level=1)
        if additional_data.get('is_new_tenant') and additional_data.get('new_tenant_data'):
            new_tenant_data = additional_data['new_tenant_data']
            document.add_paragraph(f'Tenant Name: {new_tenant_data.get("tenant_name", "N/A")}')
            document.add_paragraph(f'Passport/ID: {new_tenant_data.get("tenant_passport_id", "N/A")}')
            document.add_paragraph(f'Email: {new_tenant_data.get("tenant_email", "N/A")}')
            document.add_paragraph(f'Phone: {new_tenant_data.get("tenant_contact_number", "N/A")}')
            document.add_paragraph(f'Address: {new_tenant_data.get("tenant_address", "N/A")}')
        else:
            document.add_paragraph(f'Tenant Name: {tenant_obj.tenant_name or "N/A"}')
            document.add_paragraph(f'Email: {getattr(tenant_obj, "tenant_email", "N/A") or "N/A"}')
            document.add_paragraph(f'Phone: {getattr(tenant_obj, "tenant_contact_number", "N/A") or "N/A"}')
        
        document.add_paragraph('')
        
        # Lease terms
        document.add_heading('Lease Terms', level=1)
        
        # Get dates
        start_date = additional_data.get('start_date') or (
            tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') 
            if hasattr(tenant_obj, 'tenant_lease_start_date') and tenant_obj.tenant_lease_start_date else 'N/A'
        )
        end_date = additional_data.get('end_date') or (
            tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') 
            if hasattr(tenant_obj, 'tenant_lease_end_date') and tenant_obj.tenant_lease_end_date else 'N/A'
        )
        
        document.add_paragraph(f'Start Date: {start_date}')
        document.add_paragraph(f'End Date: {end_date}')
        
        # Financial terms (without decimals, with thousand separators)
        monthly_rent = int(float(additional_data.get('monthly_rent') or (
            tenant_obj.tenant_rent if hasattr(tenant_obj, 'tenant_rent') and tenant_obj.tenant_rent else 0
        )))
        security_deposit = int(float(additional_data.get('security_deposit') or (
            tenant_obj.tenant_deposit if hasattr(tenant_obj, 'tenant_deposit') and tenant_obj.tenant_deposit else 0
        )))
        communal_expenses = int(float(additional_data.get('communal_expenses', 0)))
        
        document.add_paragraph(f'Monthly Rent: €{monthly_rent:,}')
        document.add_paragraph(f'Security Deposit: €{security_deposit:,}')
        if communal_expenses > 0:
            document.add_paragraph(f'Communal Expenses: €{communal_expenses:,}')
        
        if hasattr(tenant_obj, 'tenant_levies') and tenant_obj.tenant_levies:
            document.add_paragraph(f'Levies: €{int(float(tenant_obj.tenant_levies)):,}')
        
        # Furniture and appliances (with pluralization)
        furniture_list = []
        for key, value in additional_data.items():
            if key.startswith('furniture_') and int(value or 0) > 0:
                count = int(value)
                item_name = key.replace('furniture_', '').replace('_', ' ').title()
                pluralized_name = pluralize_item(item_name, count)
                furniture_list.append(f"{count} x {pluralized_name}")
        
        if furniture_list:
            document.add_paragraph('')
            document.add_heading('Furniture and Appliances', level=1)
            document.add_paragraph(', '.join(furniture_list))
        
        # Keys (with pluralization)
        keys_list = []
        for key, value in additional_data.items():
            if key.startswith('keys_') and int(value or 0) > 0:
                count = int(value)
                key_name = key.replace('keys_', '').replace('_', ' ').title() + ' Key'
                pluralized_key = pluralize_item(key_name, count)
                keys_list.append(f"{count} x {pluralized_key}")
        
        if keys_list:
            document.add_paragraph('')
            document.add_heading('Keys Provided', level=1)
            document.add_paragraph(', '.join(keys_list))
        
        # Signatures
        document.add_paragraph('')
        document.add_heading('Signatures', level=1)
        document.add_paragraph('Landlord: _________________________    Date: _________')
        document.add_paragraph('Tenant: _________________________     Date: _________')
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        document.save(temp_file.name)
        
        logger.info(f"Basic lease document created: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Error creating basic lease document: {str(e)}")
        return None

### NOTIFICATIONS ###
@login_required
@permission_required('auth.can_access_dashboard', raise_exception=True)
def notifications_dashboard(request):
    """
    Notifications Dashboard view - shows property management alerts and status
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON data
        try:
            notification_data = get_notification_data()
            return JsonResponse(notification_data)
        except Exception as e:
            return JsonResponse({
                'error': f'Error loading notification data: {str(e)}'
            })
    else:
        # Regular page load - return template
        return render(request, 'notifications.html')

def get_notification_data():
    """
    Get notification data by running similar queries to the management command
    """
    import logging
    from django.db import connection as django_connection
    
    logger = logging.getLogger(__name__)
    mydb = None
    my_cursor = None
    
    try:
        mydb = mysql.connector.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=settings.DATABASES['default']['NAME'],
        )
        
        my_cursor = mydb.cursor()
        today = date.today()
        
        # Get vacant properties
        from .properties import get_vacant_properties
        vacant_properties = get_vacant_properties(my_cursor)
        
        # Get expiring leases (pending renewals)
        expiring_leases = get_expiring_leases(my_cursor, today)
        
        # Get declined renewals
        declined_renewals = get_declined_renewals(my_cursor, today)
        
        # Get overdue invoices
        overdue_invoices = get_overdue_invoices(my_cursor, today)
        
        # Get expenses waiting for approval
        expenses_waiting_approval = get_expenses_waiting_approval(my_cursor)
        
        # Get expenses waiting for payment
        expenses_waiting_payment = get_expenses_waiting_payment(my_cursor)
        
        return {
            'summary': {
                'vacantProperties': len(vacant_properties),
                'expiringLeases': len(expiring_leases),
                'declinedRenewals': len(declined_renewals),
                'overdueInvoices': len(overdue_invoices),
                'expensesWaitingApproval': len(expenses_waiting_approval),
                'expensesWaitingPayment': len(expenses_waiting_payment)
            },
            'vacantProperties': vacant_properties,
            'expiringLeases': expiring_leases,
            'declinedRenewals': declined_renewals,
            'overdueInvoices': overdue_invoices,
            'expensesWaitingApproval': expenses_waiting_approval,
            'expensesWaitingPayment': expenses_waiting_payment,
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except mysql.connector.Error as e:
        logger.error(f"MySQL connection error in get_notification_data: {e}")
        # Return empty data structure on error
        return {
            'summary': {
                'vacantProperties': 0,
                'expiringLeases': 0,
                'declinedRenewals': 0,
                'overdueInvoices': 0,
                'expensesWaitingApproval': 0,
                'expensesWaitingPayment': 0
            },
            'vacantProperties': [],
            'expiringLeases': [],
            'declinedRenewals': [],
            'overdueInvoices': [],
            'expensesWaitingApproval': [],
            'expensesWaitingPayment': [],
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_notification_data: {e}")
        # Return empty data structure on error
        return {
            'summary': {
                'vacantProperties': 0,
                'expiringLeases': 0,
                'declinedRenewals': 0,
                'overdueInvoices': 0,
                'expensesWaitingApproval': 0,
                'expensesWaitingPayment': 0
            },
            'vacantProperties': [],
            'expiringLeases': [],
            'declinedRenewals': [],
            'overdueInvoices': [],
            'expensesWaitingApproval': [],
            'expensesWaitingPayment': [],
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    finally:
        # Always close cursor and connection
        if my_cursor:
            try:
                my_cursor.close()
            except:
                pass
        if mydb and mydb.is_connected():
            try:
                mydb.close()
            except:
                pass
        # Also close Django's connection
        django_connection.close()

def get_expenses_waiting_approval(cursor):
    """Get expenses that require approval (status = 'require_approval')"""
    cursor.execute("""
        SELECT ae.act_expense_id, ae.act_expense_date, ae.act_expense_description,
               ae.act_expense_amount, p.prop_name
        FROM railway.act_expense ae
        JOIN railway.prop p ON ae.prop_id = p.prop_id
        WHERE ae.act_expense_approved = 'No' 
        AND ae.act_expense_paid = 'No'
        ORDER BY ae.act_expense_date ASC
    """)
    
    expenses_data = cursor.fetchall()
    expenses_waiting_approval = []
    
    for row in expenses_data:
        expenses_waiting_approval.append({
            'expense_id': row[0],
            'expense_date': row[1].strftime('%Y-%m-%d') if row[1] else '',
            'description': row[2] or '',
            'amount': float(row[3]) if row[3] else 0.0,
            'property_name': row[4] or '',
            'expense_type': 'General Expense',  # You might want to add this field to your database
            'submitted_date': row[1].strftime('%Y-%m-%d') if row[1] else ''
        })
    
    return expenses_waiting_approval

def get_expenses_waiting_payment(cursor):
    """Get expenses that are approved but not yet paid"""
    cursor.execute("""
        SELECT ae.act_expense_id, ae.act_expense_date, ae.act_expense_description,
               ae.act_expense_amount, p.prop_name
        FROM railway.act_expense ae
        JOIN railway.prop p ON ae.prop_id = p.prop_id
        WHERE ae.act_expense_approved = 'Yes' 
        AND ae.act_expense_paid = 'No'
        ORDER BY ae.act_expense_date ASC
    """)
    
    expenses_data = cursor.fetchall()
    expenses_waiting_payment = []
    
    for row in expenses_data:
        expenses_waiting_payment.append({
            'expense_id': row[0],
            'expense_date': row[1].strftime('%Y-%m-%d') if row[1] else '',
            'description': row[2] or '',
            'amount': float(row[3]) if row[3] else 0.0,
            'property_name': row[4] or '',
            'expense_type': 'General Expense',  # You might want to add this field to your database
            'approved_date': row[1].strftime('%Y-%m-%d') if row[1] else ''  # Using expense date as approximation
        })
    
    return expenses_waiting_payment

def get_expiring_leases(cursor, today):
    """Get leases that are expiring and pending renewal"""
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name, 
               tenant.tenant_lease_end_date, tenant.tenant_renewal_period,
               tenant.tenant_renewal_status
        FROM railway.tenant
        JOIN railway.prop ON prop.prop_id = tenant.prop_id
        WHERE tenant.tenant_current = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC
    """)
    tenant_rows = cursor.fetchall()
    
    expiring_leases = []
    
    for row in tenant_rows:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        lease_end_date = row[3]
        renewal_period = int(row[4]) if row[4] is not None else 0
        renewal_status = row[5] if row[5] else 'pending'

        # Skip tenants with no lease end date — we can't compute a renewal date
        if lease_end_date is None:
            continue

        renewal_date = lease_end_date - timedelta(days=renewal_period)
#        warning_date = renewal_date - timedelta(days=30)
        warning_date = renewal_date

        if today >= warning_date and renewal_status == 'pending':
            expiring_leases.append({
                'prop_name': prop_name,
                'prop_country': prop_country,
                'tenant_name': tenant_name,
                'lease_end_date': lease_end_date.strftime('%Y-%m-%d'),
                'renewal_date': renewal_date.strftime('%Y-%m-%d')
            })
    
    return expiring_leases

def get_declined_renewals(cursor, today):
    """Get renewals that have been declined"""
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name, 
               tenant.tenant_lease_end_date, tenant.tenant_renewal_period,
               tenant.tenant_renewal_status
        FROM railway.tenant
        JOIN railway.prop ON prop.prop_id = tenant.prop_id
        WHERE tenant.tenant_current = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC
    """)
    tenant_rows = cursor.fetchall()
    
    declined_renewals = []
    
    for row in tenant_rows:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        lease_end_date = row[3]
        renewal_period = int(row[4]) if row[4] is not None else 0
        renewal_status = row[5] if row[5] else 'pending'

        # Skip tenants with no lease end date — we can't compute a renewal date
        if lease_end_date is None:
            continue

        renewal_date = lease_end_date - timedelta(days=renewal_period)
        warning_date = renewal_date - timedelta(days=30)

        if today >= warning_date and renewal_status == 'declined':
            declined_renewals.append({
                'prop_name': prop_name,
                'prop_country': prop_country,
                'tenant_name': tenant_name,
                'lease_end_date': lease_end_date.strftime('%Y-%m-%d'),
                'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT'
            })
    
    return declined_renewals

def get_overdue_invoices(cursor, today):
    """Get properties with overdue invoices"""
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name, 
               tenant.tenant_payment_terms, tenant.tenant_rent,
               invoice.invoice_date, invoice.invoice_id
        FROM railway.invoice
        JOIN railway.tenant ON invoice.tenant_id = tenant.tenant_id
        JOIN railway.prop ON tenant.prop_id = prop.prop_id
        WHERE invoice.invoice_paid = 'No'
        AND tenant.tenant_current = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC, invoice.invoice_date ASC
    """)
    
    invoice_data = cursor.fetchall()
    
    # Create a flat list of overdue invoices instead of grouping
    overdue_invoices_list = []
    
    for row in invoice_data:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        payment_terms = int(row[3]) if row[3] else 0
        tenant_rent = row[4]
        invoice_date = row[5]
        invoice_id = row[6]
        
        # Calculate due date based on invoice date and payment terms
        due_date = invoice_date + timedelta(days=payment_terms)
        
        # Only include if invoice is overdue
        if due_date < today:
            # Calculate days overdue
            days_overdue = (today - due_date).days
            
            overdue_invoices_list.append({
                'prop_name': prop_name,
                'prop_country': prop_country,
                'tenant_name': tenant_name,
                'tenant_rent': tenant_rent,
                'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'invoice_id': invoice_id
            })
    
    return overdue_invoices_list

### FINANCIAL DASHBOARD ###
def calculate_occupancy_metrics(property, start_date=None, end_date=None):
    """
    Calculate occupancy rate and average days to fill for a property
    FIXED: Only count days within actual lease period, ignore tenant_current status
    """
    if not end_date:
        end_date = timezone.now().date()
    
    if not start_date:
        first_tenant = tenant.objects.filter(prop=property).order_by('tenant_lease_start_date').first()
        if first_tenant and first_tenant.tenant_lease_start_date:
            start_date = first_tenant.tenant_lease_start_date
        else:
            from datetime import timedelta
            start_date = end_date - timedelta(days=365)
    
    total_days = (end_date - start_date).days
    if total_days <= 0:
        return {
            'occupancy_rate': 0,
            'avg_days_to_fill': 0,
            'current_vacancy_days': 0,
            'is_currently_vacant': False
        }
    
    # Calculate occupied days - DATE BASED ONLY
    occupied_days = 0
    property_tenants = tenant.objects.filter(
        prop=property,
        tenant_lease_start_date__lte=end_date
    )
    
    for t in property_tenants:
        if not t.tenant_lease_start_date:
            continue
            
        lease_start = max(t.tenant_lease_start_date, start_date)
        
        # FIXED: Only count up to lease end date
        if t.tenant_lease_end_date:
            lease_end = min(t.tenant_lease_end_date, end_date)
        else:
            lease_end = end_date
        
        if lease_end >= lease_start:
            occupied_days += (lease_end - lease_start).days + 1
    
    occupied_days = min(occupied_days, total_days)
    occupancy_rate = (occupied_days / total_days * 100) if total_days > 0 else 0
    
    # Calculate average days to fill
    vacancies = VacancyPeriod.objects.filter(
        prop=property,
        status='FILLED',
        reason='BETWEEN_TENANTS',
        start_date__gte=start_date,
        end_date__lte=end_date
    )
    
    if vacancies.exists():
        from django.db.models import Avg
        avg_days = vacancies.aggregate(Avg('days_vacant'))['days_vacant__avg']
        avg_days_to_fill = round(avg_days, 0) if avg_days else 0
    else:
        avg_days_to_fill = 0
    
    # Auto-detect if currently vacant
    is_currently_vacant = True
    for t in property_tenants:
        if t.tenant_lease_start_date and t.tenant_lease_start_date <= end_date:
            if t.tenant_lease_end_date:
                if t.tenant_lease_end_date >= end_date:
                    is_currently_vacant = False
                    break
            else:
                is_currently_vacant = False
                break
    
    # Calculate current vacancy days
    current_vacancy_days = 0
    if is_currently_vacant:
        last_tenant = property_tenants.filter(
            tenant_lease_end_date__isnull=False
        ).order_by('-tenant_lease_end_date').first()
        
        if last_tenant and last_tenant.tenant_lease_end_date:
            current_vacancy_days = (end_date - last_tenant.tenant_lease_end_date).days
    
    return {
        'occupancy_rate': round(occupancy_rate, 1),
        'avg_days_to_fill': int(avg_days_to_fill),
        'current_vacancy_days': current_vacancy_days,
        'is_currently_vacant': is_currently_vacant
    }

def calculate_occupancy_metrics_optimized(property, start_date=None, end_date=None):
    """
    Calculate occupancy metrics using PREFETCHED data
    FIXED: Only count days within actual lease period
    """
    if not end_date:
        end_date = timezone.now().date()
    
    property_tenants = list(property.tenant_set.all())
    
    if not start_date:
        if property_tenants:
            tenants_with_dates = [t for t in property_tenants if t.tenant_lease_start_date]
            if tenants_with_dates:
                first_tenant = min(tenants_with_dates, key=lambda t: t.tenant_lease_start_date)
                start_date = first_tenant.tenant_lease_start_date
            else:
                from datetime import timedelta
                start_date = end_date - timedelta(days=365)
        else:
            from datetime import timedelta
            start_date = end_date - timedelta(days=365)
    
    total_days = (end_date - start_date).days
    if total_days <= 0:
        return {
            'occupancy_rate': 0,
            'avg_days_to_fill': 0,
            'current_vacancy_days': 0,
            'is_currently_vacant': False
        }
    
    # Calculate occupied days - DATE BASED ONLY
    occupied_days = 0
    for t in property_tenants:
        if not t.tenant_lease_start_date or t.tenant_lease_start_date > end_date:
            continue
            
        lease_start = max(t.tenant_lease_start_date, start_date)
        
        # FIXED: Only count up to lease end date
        if t.tenant_lease_end_date:
            lease_end = min(t.tenant_lease_end_date, end_date)
        else:
            lease_end = end_date
        
        if lease_end >= lease_start:
            occupied_days += (lease_end - lease_start).days + 1
    
    occupied_days = min(occupied_days, total_days)
    occupancy_rate = (occupied_days / total_days * 100) if total_days > 0 else 0
    
    # Use prefetched vacancy data
    vacancies = [v for v in property.vacancy_periods.all() 
                 if v.status == 'FILLED' 
                 and v.reason == 'BETWEEN_TENANTS'
                 and v.start_date >= start_date
                 and v.end_date and v.end_date <= end_date]
    
    if vacancies:
        avg_days = sum(v.days_vacant for v in vacancies) / len(vacancies)
        avg_days_to_fill = round(avg_days, 0)
    else:
        avg_days_to_fill = 0
    
    # Auto-detect if currently vacant
    is_currently_vacant = True
    for t in property_tenants:
        if t.tenant_lease_start_date and t.tenant_lease_start_date <= end_date:
            if t.tenant_lease_end_date:
                if t.tenant_lease_end_date >= end_date:
                    is_currently_vacant = False
                    break
            else:
                is_currently_vacant = False
                break
    
    # Calculate current vacancy days
    current_vacancy_days = 0
    if is_currently_vacant:
        tenants_with_end_dates = [t for t in property_tenants if t.tenant_lease_end_date]
        if tenants_with_end_dates:
            last_tenant = max(tenants_with_end_dates, key=lambda t: t.tenant_lease_end_date)
            current_vacancy_days = (end_date - last_tenant.tenant_lease_end_date).days
    
    return {
        'occupancy_rate': round(occupancy_rate, 1),
        'avg_days_to_fill': int(avg_days_to_fill),
        'current_vacancy_days': current_vacancy_days,
        'is_currently_vacant': is_currently_vacant
    }

def calculate_portfolio_occupancy_metrics_optimized(properties, start_date=None, end_date=None):
    """
    Calculate portfolio metrics using SIMPLE AVERAGE method
    Each property judged on its own history
    """
    if not end_date:
        end_date = timezone.now().date()
    
    # Calculate occupancy for each property using its OWN start date
    property_occupancy_rates = []
    
    for prop in properties:
        metrics = calculate_occupancy_metrics_optimized(prop, start_date=None, end_date=end_date)
        property_occupancy_rates.append(metrics['occupancy_rate'])
    
    # Simple average
    if property_occupancy_rates:
        portfolio_occupancy = sum(property_occupancy_rates) / len(property_occupancy_rates)
    else:
        portfolio_occupancy = 0
    
    # For avg_days_to_fill
    if not start_date:
        all_tenants = []
        for prop in properties:
            all_tenants.extend([t for t in prop.tenant_set.all() if t.tenant_lease_start_date])
        
        if all_tenants:
            first_tenant = min(all_tenants, key=lambda t: t.tenant_lease_start_date)
            start_date = first_tenant.tenant_lease_start_date
        else:
            from datetime import timedelta
            start_date = end_date - timedelta(days=365)
    
    # Get all vacancies
    all_vacancies = []
    for prop in properties:
        vacancies = [v for v in prop.vacancy_periods.all()
                    if v.status == 'FILLED'
                    and v.reason == 'BETWEEN_TENANTS'
                    and v.start_date >= start_date
                    and v.end_date and v.end_date <= end_date]
        all_vacancies.extend(vacancies)
    
    # Weighted average
    if all_vacancies and len(list(properties)) > 0:
        total_vacancy_days = sum(v.days_vacant for v in all_vacancies)
        portfolio_avg_days = round(total_vacancy_days / len(list(properties)), 1)
    else:
        portfolio_avg_days = 0
    
    return {
        'occupancy_rate': round(portfolio_occupancy, 1),
        'avg_days_to_fill': portfolio_avg_days
    }


### HOME ###
def _build_today_items(notification_data):
    """
    Build the ordered list of non-zero Today items for the home page panel.

    Each item is a dict with:
      - label    — singular/plural human heading
      - count    — integer count
      - icon     — Font Awesome class
      - severity — 'urgent' | 'warning' | 'info' (drives the colour)
      - category — matches the data-category strings used by the modal JS
                   (so we can look up the right detail rows on tap)
      - permission — perms_map key gating visibility

    Returns items in priority order: urgent first, then warning, then info.
    Zero-count items are filtered out so the Today panel only shows
    things the user can act on.
    """
    summary = (notification_data or {}).get('summary', {}) or {}

    # `category` strings MUST match the categories used in the
    # SimpleNotificationDashboard JS class (see home.html / notifications.html):
    # 'vacant', 'expiring', 'declined', 'overdue', 'approval', 'payment'
    candidates = [
        # URGENT (red)
        {
            'key': 'overdueInvoices',
            'category': 'overdue',
            'label': 'Overdue Invoice',
            'label_plural': 'Overdue Invoices',
            'icon': 'fas fa-exclamation-triangle',
            'severity': 'urgent',
            'permission': 'invoices',
        },
        {
            'key': 'vacantProperties',
            'category': 'vacant',
            'label': 'Vacant Property',
            'label_plural': 'Vacant Properties',
            'icon': 'fas fa-home',
            'severity': 'urgent',
            'permission': 'properties',
        },
        {
            'key': 'declinedRenewals',
            'category': 'declined',
            'label': 'Declined Renewal',
            'label_plural': 'Declined Renewals',
            'icon': 'fas fa-times-circle',
            'severity': 'urgent',
            'permission': 'tenants',
        },
        # WARNING (yellow)
        {
            'key': 'expiringLeases',
            'category': 'expiring',
            'label': 'Expiring Lease',
            'label_plural': 'Expiring Leases',
            'icon': 'fas fa-calendar-times',
            'severity': 'warning',
            'permission': 'tenants',
        },
        {
            'key': 'expensesWaitingApproval',
            'category': 'approval',
            'label': 'Expense awaiting approval',
            'label_plural': 'Expenses awaiting approval',
            'icon': 'fas fa-clipboard-check',
            'severity': 'warning',
            'permission': 'expenses',
        },
        # INFO (teal)
        {
            'key': 'expensesWaitingPayment',
            'category': 'payment',
            'label': 'Expense awaiting payment',
            'label_plural': 'Expenses awaiting payment',
            'icon': 'fas fa-credit-card',
            'severity': 'info',
            'permission': 'expenses',
        },
    ]

    items = []
    for c in candidates:
        count = summary.get(c['key'], 0) or 0
        if count <= 0:
            continue
        items.append({
            'label': c['label_plural'] if count != 1 else c['label'],
            'count': count,
            'icon': c['icon'],
            'severity': c['severity'],
            'category': c['category'],
            'permission': c['permission'],
        })
    return items


def home(request):
    results = props.objects.all().order_by('prop_country', 'prop_name')
    tresults = tenant.objects.filter(tenant_current="Yes")
    sresults = supplier.objects.all().order_by('supplier_country', 'supplier_contact_person')

    # Build permission flags for the template
    perms = {}
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Superusers have access to everything
            perms = {
                'properties': True,
                'tenants': True,
                'suppliers': True,
                'issues': True,
                'dashboard': True,
                'invoices': True,
                'expenses': True,
                'petty_cash': True,
                'financials': True,
                'projects': True,
                'personal': True,
                'administration': True,
            }
        else:
            perms = {
                'properties': request.user.has_perm('auth.can_access_properties'),
                'tenants': request.user.has_perm('auth.can_access_tenants'),
                'suppliers': request.user.has_perm('auth.can_access_suppliers'),
                'issues': request.user.has_perm('auth.can_access_issues'),
                'dashboard': request.user.has_perm('auth.can_access_dashboard'),
                'invoices': request.user.has_perm('auth.can_access_invoices'),
                'expenses': request.user.has_perm('auth.can_access_expenses'),
                'petty_cash': request.user.has_perm('auth.can_access_petty_cash'),
                'financials': request.user.has_perm('auth.can_access_financials'),
                'projects': request.user.has_perm('auth.can_access_projects'),
                'personal': request.user.has_perm('auth.can_access_personal'),
                'administration': request.user.has_perm('auth.can_access_administration'),
            }

    # Today panel — build for authenticated users with dashboard access
    # (same permission gating as the Notifications Dashboard view itself).
    today_items = []
    notification_data_json = '{}'
    if request.user.is_authenticated and perms.get('dashboard'):
        cache_key = f'home_notification_data_user_{request.user.id}'
        notification_data = cache.get(cache_key)
        if notification_data is None:
            try:
                notification_data = get_notification_data()
                # 30-second TTL — fast page loads, ~minute-fresh counts.
                cache.set(cache_key, notification_data, 30)
            except Exception:
                notification_data = None

        if notification_data:
            all_today_items = _build_today_items(notification_data)
            # Filter out rows the user can't navigate to (permission gated).
            today_items = [
                item for item in all_today_items
                if perms.get(item['permission'], False)
            ]
            # Embed full data (counts + detail rows) so modals open instantly
            # without a second round-trip. ~few KB of JSON.
            try:
                notification_data_json = json.dumps(notification_data, default=str)
            except Exception:
                notification_data_json = '{}'

    return render(request, "home.html", {
        "props": results,
        "tenant": tresults,
        "supplier": sresults,
        "perms_map": perms,
        "today_items": today_items,
        "notification_data_json": notification_data_json,
    })

### TENANTS ###
@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_page(request):
    # Get filter values from the new form
    selected_property = request.POST.get('propname', '').strip()
    selected_tenant = request.POST.get('tenantname', '').strip()
    selected_status = request.POST.get('act', '').strip()
    
    # Start with all properties and tenants
    all_properties = props.objects.all().order_by('prop_country', 'prop_name')
    all_tenants = tenant.objects.all().order_by('tenant_name')
    
    # Filter tenants based on the selected criteria
    filtered_tenants = all_tenants
    
    # Apply tenant name filter
    if selected_tenant:
        filtered_tenants = filtered_tenants.filter(tenant_name=selected_tenant)
    
    # Apply status filter
    if selected_status:
        filtered_tenants = filtered_tenants.filter(tenant_current=selected_status)
    
    # Filter properties based on the selected property
    filtered_properties = all_properties
    if selected_property:
        filtered_properties = filtered_properties.filter(prop_name=selected_property)
    
    # Pass filter values back to template for form persistence
    context = {
        'tenant': filtered_tenants,
        'props': filtered_properties,
        'selected_property': selected_property,
        'selected_tenant': selected_tenant,
        'selected_status': selected_status,
    }
    
    return render(request, "tenant.html", context)

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	return render(request, "tenant_add.html", {"props":results, "tenant":tresults})

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_edit(request, tenant_id):
	tresults = tenant.objects.filter(pk=tenant_id)
	results = props.objects.all().order_by('prop_country','prop_name')
	return render (request, "tenant_edit.html", {"props":results, "tenant":tresults})

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_commit(request):
    props_list = props.objects.all().order_by('prop_country','prop_name')
    
    if request.method == "POST":
        form = TenantForm(request.POST)
        
        if form.is_valid():
            try:
                new_tenant = form.save()
                messages.success(request, f"Tenant {new_tenant.tenant_name} added successfully")
                return redirect('tenant')
            except ValidationError as e:
                # Clean up the error message
                clean_error = str(e).replace('__all__: ', '')
                messages.error(request, clean_error)
                return render(request, "tenant_add.html", {
                    'form': form,
                    'props': props_list,
                    'form_data': request.POST
                })
            except Exception as e:
                messages.error(request, f"Error saving tenant: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    clean_error = str(error).replace('__all__: ', '')
                    messages.error(request, clean_error)
    
    return render(request, "tenant_add.html", {
        'form': TenantForm(request.POST if request.method == "POST" else None),
        'props': props_list,
        'form_data': request.POST if request.method == "POST" else None
    })

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_edit_commit(request, tenant_id):
	ten = tenant.objects.get(pk=tenant_id)
	if request.method == "POST":
		form = TenantForm(request.POST or None, instance=ten)
		if form.is_valid():
			form.save()
			messages.success(request, "Tenant Edited Successfully")
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	return render (request, "tenant.html", {"tenant":tresults, "props":results})

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_lease_agreement(request):
    tenants = tenant.objects.all().order_by('prop__prop_country', 'prop__prop_name', 'tenant_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        tenant_id = request.POST.get('tenant_id')
        
        if not tenant_id:
            messages.error(request, 'No tenant selected')
            return redirect('tenant_lease_agreement')
        
        try:
            tenant_obj = get_object_or_404(tenant, pk=tenant_id)
            
            if action == 'delete':
                if tenant_obj.tenant_lease_agreement:
                    # Delete the file from storage
                    tenant_obj.tenant_lease_agreement.delete()
                    tenant_obj.tenant_lease_agreement_status = "No Lease Agreement"
                    tenant_obj.save()
                    messages.success(request, f'Lease agreement deleted for {tenant_obj.tenant_name}!')
                else:
                    messages.warning(request, 'No lease agreement found to delete.')
                    

            elif action == 'upload':
                if 'lease_agreement' in request.FILES:
                    uploaded_file = request.FILES['lease_agreement']
                    
                    # Validate file size (10MB limit)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 10MB limit')
                        return redirect('tenant_lease_agreement')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF or image files only.')
                        return redirect('tenant_lease_agreement')
                    
                    try:
                        # Ensure directory exists
                        upload_path = os.path.join(settings.MEDIA_ROOT, 'tenants', 'lease_agreements')
                        os.makedirs(upload_path, exist_ok=True)
                        
                        # Delete old file if exists
                        if tenant_obj.tenant_lease_agreement:
                            tenant_obj.tenant_lease_agreement.delete(save=False)
                        
                        # Save new file
                        tenant_obj.tenant_lease_agreement = uploaded_file
                        tenant_obj.tenant_lease_agreement_status = "Lease Agreement Uploaded"
                        tenant_obj.save()
                        
                        messages.success(request, f'Lease agreement uploaded successfully for {tenant_obj.tenant_name}!')
                    except Exception as e:
                        messages.error(request, f'Error saving file: {str(e)}')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    context = {
        'tenants': tenants,
    }
    return render(request, 'tenant_lease_agreement.html', context)

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_timeline_view(request):
    # Get all properties with their tenants
    properties = props.objects.filter(prop_status='Active').prefetch_related(
        'tenant_set'
    ).order_by('prop_country', 'prop_name')
    
    # Build timeline data
    timeline_data = []
    
    for prop in properties:
        tenants = prop.tenant_set.all().order_by('tenant_lease_start_date')
        
        for t in tenants:
            if t.tenant_lease_start_date:
                timeline_data.append({
                    'property_id': prop.prop_id,
                    'property_name': prop.prop_name,
                    'tenant_id': t.tenant_id,
                    'tenant_name': t.tenant_name,
                    'start_date': t.tenant_lease_start_date.isoformat(),
                    'end_date': t.tenant_lease_end_date.isoformat() if t.tenant_lease_end_date else None,
                    'is_active': t.tenant_current == 'Yes',
                    'rent': float(t.tenant_rent) if t.tenant_rent else 0,
                })
    
    context = {
        'properties': properties,
        'timeline_data': timeline_data,
    }
    
    return render(request, 'lease_timeline.html', context)

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def duplicate_tenant_view(request, tenant_id):
    """
    Duplicate an existing tenant to create a renewal or new lease.
    Copies all tenant details except ID and lease dates.
    """
    try:
        # Get the original tenant
        original_tenant = tenant.objects.get(pk=tenant_id)
        
        # Create a new tenant instance with copied data
        new_tenant = tenant()
        
        # Copy all fields EXCEPT primary key and dates
        new_tenant.prop = original_tenant.prop
        new_tenant.tenant_type = original_tenant.tenant_type
        new_tenant.tenant_name = original_tenant.tenant_name
        new_tenant.tenant_contact_person = original_tenant.tenant_contact_person
        new_tenant.tenant_contact_number = original_tenant.tenant_contact_number
        new_tenant.tenant_email = original_tenant.tenant_email
        new_tenant.tenant_deposit = original_tenant.tenant_deposit
        new_tenant.tenant_rental_type = original_tenant.tenant_rental_type
        new_tenant.tenant_renewal = original_tenant.tenant_renewal
        new_tenant.tenant_renewal_period = original_tenant.tenant_renewal_period
        new_tenant.tenant_rent = original_tenant.tenant_rent
        new_tenant.tenant_levies = original_tenant.tenant_levies
        new_tenant.tenant_payment_terms = original_tenant.tenant_payment_terms
        
        # Set lease dates to None - user will fill these in
        new_tenant.tenant_lease_start_date = None
        new_tenant.tenant_lease_end_date = None
        
        # Set as inactive initially - user will activate after setting dates
        new_tenant.tenant_current = 'No'
        
        # Reset renewal status
        new_tenant.tenant_renewal_status = 'pending'
        
        # Don't copy lease agreement - user may need to upload new one
        new_tenant.tenant_lease_agreement = None
        new_tenant.tenant_lease_agreement_status = None
        
        # Save the new tenant
        new_tenant.save()
        
        # Redirect to edit page for the new tenant
        messages.success(
            request, 
            f'Tenant duplicated successfully! Please update the lease dates and set to Active when ready.'
        )
        return redirect('tenant_edit', tenant_id=new_tenant.tenant_id)
        
    except tenant.DoesNotExist:
        messages.error(request, 'Tenant not found.')
        return redirect('tenant')  # ← FIXED
    except Exception as e:
        messages.error(request, f'Error duplicating tenant: {str(e)}')
        return redirect('tenant')  # ← FIXED

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def delete_tenant_view(request, tenant_id):
    """
    Delete a tenant and automatically recalculate vacancy periods.
    Requires can_edit_tenants permission.
    """

    try:
        tenant_to_delete = tenant.objects.get(pk=tenant_id)
        tenant_name = tenant_to_delete.tenant_name
        property_name = tenant_to_delete.prop.prop_name
        
        # Delete the tenant (signal will handle vacancy cleanup)
        tenant_to_delete.delete()
        
        messages.success(
            request,
            f'Tenant "{tenant_name}" from {property_name} has been deleted. Vacancy periods have been automatically recalculated.'
        )
        return redirect('tenant')
        
    except tenant.DoesNotExist:
        messages.error(request, 'Tenant not found.')
        return redirect('tenant')
    except Exception as e:
        messages.error(request, f'Error deleting tenant: {str(e)}')
        return redirect('tenant')

### USER ADMIN AND LOGIN AND LOGOUT ###
def login_user(request):
	if request.method =="POST":
	    username = request.POST["username"]
	    password = request.POST["password"]
	    user = authenticate(request, username=username, password=password)
	    if user is not None:
	        login(request, user)
	        messages.success(request, ('You Have Successfully Logged In.'))
	        return redirect('home')
	    else:
	        messages.success(request, ('Error Logging In - Please Try Again !!'))
	        return redirect('login')
	else:
		return render(request, 'login.html', {})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, ('You Have Succefully Logged Out.'))
    return redirect('home')

### RECIPE MANAGEMENT ###
# HELPER FUNCTION

def convert_to_decimal(quantity_str):
    """Convert fractions like '1/4' to Decimal(0.25)"""
    try:
        quantity_str = str(quantity_str).strip()
        
        if '/' in quantity_str:
            if ' ' in quantity_str:  # Mixed number like "1 1/2"
                parts = quantity_str.split(' ')
                whole = Decimal(parts[0])
                frac = Fraction(parts[1])
                return whole + Decimal(frac.numerator) / Decimal(frac.denominator)
            else:  # Simple fraction like "1/4"
                frac = Fraction(quantity_str)
                return Decimal(frac.numerator) / Decimal(frac.denominator)
        else:
            return Decimal(quantity_str)
    except Exception as e:
        print(f"Error converting '{quantity_str}': {e}")
        return Decimal("1")

def format_quantity(quantity_str):
    """Format for display - keep fractions as-is"""
    try:
        quantity_str = str(quantity_str).strip()
        
        # Keep fractions as fractions
        if '/' in quantity_str:
            return quantity_str
        
        # Remove trailing zeros from decimals
        num = float(quantity_str)
        return '{:g}'.format(num)
        
    except:
        return str(quantity_str)

WEIGHT_UNIT_PRIORITY = ['g', 'kg', 'oz', 'lb']

def get_preferred_weight_conversion(from_unit, ingredient=None):
    """Try each weight unit in priority order, ingredient-specific first then generic."""
    for abbr in WEIGHT_UNIT_PRIORITY:
        # Ingredient-specific first
        if ingredient:
            conversion = UnitConversion.objects.filter(
                from_unit=from_unit,
                to_unit__abbreviation=abbr,
                to_unit__unit_type='weight',
                specific_ingredient=ingredient
            ).select_related('to_unit').first()
            if conversion:
                return conversion

        # Generic fallback
        conversion = UnitConversion.objects.filter(
            from_unit=from_unit,
            to_unit__abbreviation=abbr,
            to_unit__unit_type='weight',
            specific_ingredient__isnull=True
        ).select_related('to_unit').first()
        if conversion:
            return conversion

    return None

def get_or_create_ingredient(name):
    """Get or create an ingredient by name (case-insensitive)"""
    name = name.strip()
    # Capitalize each word
    name = ' '.join(word.capitalize() for word in name.split())
    
    ingredient, created = Ingredient.objects.get_or_create(
        name__iexact=name,
        defaults={'name': name}
    )
    return ingredient


def get_or_create_unit(name):
    """Get or create a measurement unit by name (case-insensitive)"""
    name = name.strip().lower()
    
    # Try to find existing
    unit = MeasurementUnit.objects.filter(name__iexact=name).first()
    if unit:
        return unit
    
    # Create new with abbreviation
    abbr = name[:5] if len(name) <= 5 else name[:4] + '.'
    unit = MeasurementUnit.objects.create(
        name=name,
        abbreviation=abbr,
        unit_type='other'
    )
    return unit


def get_or_create_preparation(name):
    """Get or create a preparation method by name (case-insensitive)"""
    if not name or not name.strip():
        return None
    
    name = name.strip().lower()
    
    prep, created = PreparationMethod.objects.get_or_create(
        name__iexact=name,
        defaults={'name': name}
    )
    return prep

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


# ============================================================================
# RATE LIMIT — 10 requests per user per hour
# ============================================================================
def _check_rate_limit(user, max_per_hour: int = 10) -> tuple[bool, int]:
    """
    Simple cache-based rate limit.
    Returns (allowed, remaining). On allowed=False, remaining is 0.
    
    Uses Django's cache backend. Falls back to per-process memory if you
    haven't configured a real cache backend (works fine for low traffic).
    """
    cache_key = f"recipe_ai_throttle:{user.pk}"
    history = cache.get(cache_key) or []
    now = time.time()
    one_hour_ago = now - 3600
    
    # Trim entries older than 1 hour
    history = [t for t in history if t > one_hour_ago]
    
    if len(history) >= max_per_hour:
        return False, 0
    
    history.append(now)
    cache.set(cache_key, history, 3600)
    return True, max_per_hour - len(history)
 
 
# ============================================================================
# THE VIEW
# ============================================================================
@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
@require_POST
def suggest_recipe_modification(request, recipe_id):
    """
    POST /recipes/<recipe_id>/suggest_modification/
    
    Body (JSON): { "goal": "reduce_carbs" | "reduce_calories" | "increase_protein" | "reduce_fat" }
    
    Response (200): {
        "success": true,
        "suggestions": <full validated suggestion dict>,
        "from_cache": <bool>,
        "rate_limit_remaining": <int>
    }
    
    Response (4xx/5xx): { "success": false, "error": <str> }
    """
    # Parse body
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON body'}, status=400)
    
    goal = data.get('goal')
    if goal not in recipe_ai.VALID_GOALS:
        return JsonResponse({
            'success': False,
            'error': f'Invalid goal. Must be one of: {", ".join(recipe_ai.VALID_GOALS)}',
        }, status=400)
    
    # Recipe must exist
    try:
        recipe = Recipe.objects.get(recipe_id=recipe_id)
    except Recipe.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Recipe not found'}, status=404)
    
    # is_complete gate — only completed recipes can be analyzed
    nutrition_cache = getattr(recipe, 'nutrition_cache', None)
    if not nutrition_cache or not nutrition_cache.is_complete:
        return JsonResponse({
            'success': False,
            'error': 'This recipe is not fully nutrition-mapped yet. Suggestions are available once all ingredients are mapped and convertible.',
        }, status=400)
    
    # Rate limit (10/hour per user)
    allowed, remaining = _check_rate_limit(request.user)
    if not allowed:
        return JsonResponse({
            'success': False,
            'error': "You've reached the suggestion limit (10 per hour). Try again later.",
        }, status=429)
    
    # Generate (or return from cache)
    try:
        # Check cache first WITHOUT counting against the rate limit — cache hits are free
        version_hash = recipe_ai.compute_recipe_version_hash(recipe)
        from ..models import RecipeModificationSuggestion
        cached = (
            RecipeModificationSuggestion.objects
            .filter(recipe=recipe, goal_type=goal, recipe_version_hash=version_hash)
            .first()
        )
        if cached:
            # Refund the rate-limit slot we just consumed — cache hit doesn't cost the API
            _refund_rate_limit_slot(request.user)
            return JsonResponse({
                'success': True,
                'suggestions': cached.suggestions_json,
                'from_cache': True,
                'rate_limit_remaining': remaining + 1,
            })
        
        # Cache miss — full call
        suggestions = recipe_ai.suggest_modifications(recipe, goal)
    
    except recipe_ai.RecipeNotEligibleError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except recipe_ai.APICallError as e:
        return JsonResponse({
            'success': False,
            'error': "Couldn't reach the AI service. Try again in a moment.",
            'detail': str(e),
        }, status=503)
    except recipe_ai.ResponseValidationError as e:
        return JsonResponse({
            'success': False,
            'error': "The AI returned an unexpected response. Try again.",
            'detail': str(e),
        }, status=502)
    
    return JsonResponse({
        'success': True,
        'suggestions': suggestions,
        'from_cache': False,
        'rate_limit_remaining': remaining,
    })
 
 
def _refund_rate_limit_slot(user):
    """Cache hits shouldn't count against the rate limit — pop the most recent entry."""
    cache_key = f"recipe_ai_throttle:{user.pk}"
    history = cache.get(cache_key) or []
    if history:
        history.pop()
        cache.set(cache_key, history, 3600)

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
def help_page(request):
    """
    The main Help page. Renders an accordion of all 32 help modules
    grouped by top-level menu section, with client-side search filtering.
    All 32 help modals are rendered in-page so clicks open them instantly.

    Modules are filtered against the logged-in user's permissions:
    superusers see everything; other users see only modules whose
    data-module-permission they hold (modules with no permission declared
    are always visible).
    """
    from ..services.help_renderer import get_all_modules_grouped, get_all_modules

    def _user_can_see_module(user, module):
        if user.is_superuser:
            return True
        perm = module.get('permission', '')
        if not perm:
            return True  # no permission declared = always visible
        # Permissions live under the 'auth' app (e.g. auth.can_access_properties)
        return user.has_perm(f'auth.{perm}')

    grouped = get_all_modules_grouped()

    # Prune modules the user is not allowed to see. Empty sub-sections and
    # empty groups are removed so no empty cards are rendered.
    filtered_grouped = []
    for group in grouped:
        direct = [m for m in group['direct_modules']
                  if _user_can_see_module(request.user, m)]

        subsections = []
        for sub in group['subsections']:
            visible_mods = [m for m in sub['modules']
                            if _user_can_see_module(request.user, m)]
            if visible_mods:
                subsections.append({
                    'name': sub['name'],
                    'parent_module_slug': sub['parent_module_slug'],
                    'parent_module_name': sub['parent_module_name'],
                    'modules': visible_mods,
                })

        if direct or subsections:
            filtered_grouped.append({
                'name': group['name'],
                'direct_modules': direct,
                'subsections': subsections,
            })

    grouped = filtered_grouped

    # Build a flat set of visible slugs, used to render only the modals the
    # user can see (and to drive the JS search index implicitly via template).
    visible_slugs = set()
    for group in grouped:
        for m in group['direct_modules']:
            visible_slugs.add(m['slug'])
        for sub in group['subsections']:
            for m in sub['modules']:
                visible_slugs.add(m['slug'])

    # Enrich every visible module with a lowercased, HTML-stripped 'search_text'
    # blob used by the client-side filter. Safe: mutation is idempotent and
    # no other template reads this key.
    def _build_search_text(module):
        parts = [module.get('name', ''), module.get('subtitle', '')]
        for tab in module.get('tabs', []):
            parts.append(tab.get('name', ''))
            parts.append(strip_tags(tab.get('content_html', '')))
        text = ' '.join(p for p in parts if p).lower()
        return ' '.join(text.split())  # collapse whitespace runs

    for group in grouped:
        for m in group['direct_modules']:
            if 'search_text' not in m:
                m['search_text'] = _build_search_text(m)
        for sub in group['subsections']:
            for m in sub['modules']:
                if 'search_text' not in m:
                    m['search_text'] = _build_search_text(m)

    # Flat list, pruned to only modules the user can see, used to render modals
    all_modules_flat = [m for m in get_all_modules() if m['slug'] in visible_slugs]

    # Icon for each top-level group (used on the accordion header)
    group_icons = {
        'Property Operations':  'fa-building',
        'Financial Management': 'fa-chart-line',
        'Administration':       'fa-cogs',
        'Personal':             'fa-user-circle',
        'Notifications':        'fa-bell',
        'My Profile':           'fa-user',
    }

    # Total module count per group, for the header badge.
    # Also attach each sub-section to its parent module (so the template can
    # render nested children inline under the parent), and collect leftover
    # "orphan" sub-sections that have no parent module.
    for group in grouped:
        total = len(group['direct_modules'])

        # Index direct modules by slug for quick lookup
        direct_by_slug = {m['slug']: m for m in group['direct_modules']}

        # Initialise per-module nested_subs lists
        for m in group['direct_modules']:
            m['nested_subs'] = []

        # Partition sub-sections: nested (attached to a parent module) vs orphan
        orphan_subs = []
        for sub in group['subsections']:
            total += len(sub['modules'])
            parent_slug = sub.get('parent_module_slug')
            if parent_slug and parent_slug in direct_by_slug:
                direct_by_slug[parent_slug]['nested_subs'].append(sub)
            else:
                orphan_subs.append(sub)

        group['orphan_subsections'] = orphan_subs
        group['total_count'] = total
        group['icon'] = group_icons.get(group['name'], 'fa-folder')

    context = {
        'grouped': grouped,
        'all_modules_flat': all_modules_flat,
        'total_module_count': sum(g['total_count'] for g in grouped),
    }
    return render(request, 'help_page.html', context)

@login_required
@require_POST
def generate_user_manual(request):
    """
    Generates a personalised User Manual PDF.

    Architecture — the long story short, we had to fight xhtml2pdf on
    several fronts to get this reliable. The shape of the pipeline:

      STEP 1 — Build the hierarchical chapter tree from the user's
               checkbox-tree selection, permission-filtered.

      STEP 2 — FIRST xhtml2pdf PASS: render the body (cover + TOC +
               chapters) using plain @page margins (NO @frame). The
               TOC page is rendered with EMPTY page-number columns
               because we don't know them yet. We only need this pass
               so pypdf can read the PDF outlines (from h1/h2/h3
               -pdf-outline directives) and discover each heading's
               page number.

      STEP 3 — Inject the discovered page numbers back into the
               context tree. Each chapter/nested module now has a
               `page_num` attribute.

      STEP 4 — SECOND xhtml2pdf PASS: re-render the body with the
               TOC now showing real page numbers.

      STEP 5 — Build a footer overlay PDF with ReportLab canvas
               ("Page X of Y" on every page except the cover).

      STEP 6 — pypdf merges the overlay onto every body page.

    Returns the final PDF as `inline` so the JS preview modal can
    display it in an iframe. A custom `X-Manual-Filename` header
    carries the user-facing filename for the Download button.

    Why two render passes? xhtml2pdf's built-in <pdf:toc/> macro
    triggers ReportLab's multiBuild, which combined with other
    features amplifies pagination bugs in rich content. Running
    xhtml2pdf twice ourselves is slower but far more predictable.
    """
    import io
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from pypdf import PdfReader, PdfWriter
    from ..services.help_renderer import get_all_modules_grouped, get_all_modules

    # -------- Parse selections ------------------------------------
    selected_modules = set(request.POST.getlist('selected_modules'))
    selected_tabs = request.POST.getlist('selected_tabs')

    tabs_by_module = {}
    for combined in selected_tabs:
        if '::' not in combined:
            continue
        mod_slug, tab_slug = combined.split('::', 1)
        tabs_by_module.setdefault(mod_slug, set()).add(tab_slug)

    # -------- Permission re-check ---------------------------------
    def _user_can_see_module(user, module):
        if user.is_superuser:
            return True
        perm = module.get('permission', '')
        if not perm:
            return True
        return user.has_perm(f'auth.{perm}')

    all_modules_by_slug = {m['slug']: m for m in get_all_modules()}
    accessible_slugs = {
        slug for slug, m in all_modules_by_slug.items()
        if _user_can_see_module(request.user, m)
    }

    # -------- Filter each module to selected tabs only ------------
    def _filter_module_for_pdf(module):
        """Return a shallow-copied module with only selected tabs, or None."""
        if module['slug'] not in selected_modules:
            return None
        if module['slug'] not in accessible_slugs:
            return None
        wanted = tabs_by_module.get(module['slug'], set())
        kept_tabs = [t for t in module.get('tabs', []) if t['slug'] in wanted]
        if not kept_tabs:
            return None
        return {
            'slug':     module['slug'],
            'name':     module['name'],
            'icon':     module.get('icon', ''),
            'subtitle': module.get('subtitle', ''),
            'group':    module.get('group', ''),
            'category': module.get('category', ''),
            'tabs':     kept_tabs,
        }

    # -------- Build the hierarchical pdf_groups structure ---------
    grouped = get_all_modules_grouped()

    for group in grouped:
        direct_by_slug = {m['slug']: m for m in group['direct_modules']}
        for m in group['direct_modules']:
            m['nested_subs'] = []
        orphan_subs = []
        for sub in group['subsections']:
            parent_slug = sub.get('parent_module_slug')
            if parent_slug and parent_slug in direct_by_slug:
                direct_by_slug[parent_slug]['nested_subs'].append(sub)
            else:
                orphan_subs.append(sub)
        group['orphan_subsections'] = orphan_subs

    pdf_groups = []
    total_modules_included = 0

    for group in grouped:
        pdf_chapters = []

        for m in group['direct_modules']:
            filtered = _filter_module_for_pdf(m)
            nested_chapters = []
            for sub in m.get('nested_subs', []):
                sub_mods = []
                for nm in sub['modules']:
                    nf = _filter_module_for_pdf(nm)
                    if nf:
                        sub_mods.append(nf)
                if sub_mods:
                    nested_chapters.append({
                        'name': sub['name'],
                        'modules': sub_mods,
                    })
            if filtered or nested_chapters:
                pdf_chapters.append({
                    'module': filtered,
                    'nested': nested_chapters,
                })
                if filtered:
                    total_modules_included += 1
                total_modules_included += sum(len(n['modules']) for n in nested_chapters)

        orphan_sub_chapters = []
        for sub in group.get('orphan_subsections', []):
            sub_mods = []
            for om in sub['modules']:
                of = _filter_module_for_pdf(om)
                if of:
                    sub_mods.append(of)
            if sub_mods:
                orphan_sub_chapters.append({
                    'name': sub['name'],
                    'modules': sub_mods,
                })
                total_modules_included += len(sub_mods)

        if pdf_chapters or orphan_sub_chapters:
            pdf_groups.append({
                'name':                group['name'],
                'icon':                group.get('icon', ''),
                'chapters':            pdf_chapters,
                'orphan_sub_chapters': orphan_sub_chapters,
            })

    # -------- Guard: nothing to print -----------------------------
    if total_modules_included == 0:
        return HttpResponse(
            'No modules with selected tabs were found. Please select at least one tab.',
            status=400, content_type='text/plain'
        )

    # -------- Cover page module list ------------------------------
    cover_module_list = []
    for group in pdf_groups:
        for ch in group['chapters']:
            if ch['module']:
                cover_module_list.append(ch['module']['name'])
            for n in ch['nested']:
                for nm in n['modules']:
                    cover_module_list.append(f"\u2022 {nm['name']}")
        for osc in group['orphan_sub_chapters']:
            for om in osc['modules']:
                cover_module_list.append(om['name'])

    full_name = request.user.get_full_name() or request.user.username

    context = {
        'pdf_groups':        pdf_groups,
        'generated_on':      timezone.now(),
        'user_full_name':    full_name,
        'user_username':     request.user.username,
        'total_modules':     total_modules_included,
        'cover_module_list': cover_module_list,
    }

    # -------- Helper: render body to an in-memory PDF buffer -------
    def _render_body(ctx):
        html = render_to_string('manual_pdf.html', ctx)
        buf = io.BytesIO()
        status = pisa.CreatePDF(src=html, dest=buf, encoding='utf-8')
        if status.err:
            return None
        buf.seek(0)
        return buf

    # -------- Helper: collect {heading_title: page_num} from PDF outlines
    def _collect_outline_pages(pdf_buf):
        pdf_buf.seek(0)
        reader = PdfReader(pdf_buf)
        pages_by_title = {}

        def walk(outlines):
            for item in outlines:
                if isinstance(item, list):
                    walk(item)
                else:
                    try:
                        title = item.title
                        page_0 = reader.get_destination_page_number(item)
                        if title not in pages_by_title:  # first occurrence wins
                            pages_by_title[title] = page_0 + 1
                    except Exception:
                        pass

        if reader.outline:
            walk(reader.outline)
        return pages_by_title

    # -------- Helper: inject page numbers into context tree --------
    def _inject_page_numbers(ctx, outline_pages):
        for group in ctx['pdf_groups']:
            group['page_num'] = outline_pages.get(group['name'], '')
            for chapter in group['chapters']:
                if chapter.get('module'):
                    m = chapter['module']
                    m['page_num'] = outline_pages.get(m['name'], '')
                for nested in chapter.get('nested', []):
                    for nm in nested['modules']:
                        # Template renders nested h3 as "Name (SubSection)"
                        composite_key = f"{nm['name']} ({nested['name']})"
                        nm['page_num'] = outline_pages.get(
                            composite_key,
                            outline_pages.get(nm['name'], '')
                        )
            for osc in group.get('orphan_sub_chapters', []):
                for om in osc['modules']:
                    composite_key = f"{om['name']} ({osc['name']})"
                    om['page_num'] = outline_pages.get(
                        composite_key,
                        outline_pages.get(om['name'], '')
                    )

    # -------- STEP 2: first xhtml2pdf pass ------------------------
    body_pass1 = _render_body(context)
    if body_pass1 is None:
        return HttpResponse(
            'PDF generation failed (first pass).',
            status=500, content_type='text/plain'
        )

    # -------- STEP 3: read outlines, inject page numbers ----------
    outline_pages = _collect_outline_pages(body_pass1)
    _inject_page_numbers(context, outline_pages)

    # -------- STEP 4: second xhtml2pdf pass -----------------------
    body_pass2 = _render_body(context)
    if body_pass2 is None:
        return HttpResponse(
            'PDF generation failed (second pass).',
            status=500, content_type='text/plain'
        )

    # -------- STEP 5: build footer overlay ------------------------
    body_pass2.seek(0)
    body_reader = PdfReader(body_pass2)
    num_pages = len(body_reader.pages)

    footer_text = (
        f"Alivente Online \u2014 User Manual   |   "
        f"Generated for {full_name} on {timezone.now().strftime('%d %b %Y')}"
    )

    overlay_buf = io.BytesIO()
    c = rl_canvas.Canvas(overlay_buf, pagesize=A4)
    page_w, page_h = A4
    margin_pt = 56.7          # 2cm in PDF points
    footer_line_y = 56.7
    footer_text_y = 42

    for page_num in range(1, num_pages + 1):
        # Skip footer on the cover page (page 1)
        if page_num == 1:
            c.showPage()
            continue

        c.setStrokeColorRGB(0.87, 0.88, 0.89)  # #dee2e6
        c.setLineWidth(0.5)
        c.line(margin_pt, footer_line_y, page_w - margin_pt, footer_line_y)

        c.setFont('Helvetica', 8.5)
        c.setFillColorRGB(0.42, 0.46, 0.49)   # #6c757d
        page_info = f"   |   Page {page_num} of {num_pages}"
        c.drawCentredString(page_w / 2, footer_text_y, footer_text + page_info)

        c.showPage()

    c.save()
    overlay_buf.seek(0)

    # -------- STEP 6: merge overlay onto body pages ---------------
    body_pass2.seek(0)
    body_reader = PdfReader(body_pass2)
    overlay_reader = PdfReader(overlay_buf)
    writer = PdfWriter()

    for i, page in enumerate(body_reader.pages):
        if i < len(overlay_reader.pages):
            page.merge_page(overlay_reader.pages[i])
        writer.add_page(page)

    final_buf = io.BytesIO()
    writer.write(final_buf)
    final_buf.seek(0)

    # -------- Ship the PDF inline so preview iframe can render it
    today = timezone.now().strftime('%Y-%m-%d')
    filename = f"alivente_user_manual_{request.user.username}_{today}.pdf"

    response = HttpResponse(final_buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    response['X-Manual-Filename'] = filename
    response['Access-Control-Expose-Headers'] = 'X-Manual-Filename'
    return response



# --------------------------------------------------------------------------- #
# 1. Wizard page (GET)
# --------------------------------------------------------------------------- #

@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
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
@permission_required('auth.can_edit_personal', raise_exception=True)
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

# ============================================================
# RECIPE NUTRITION VIEWS — paste at the bottom of views.py
# (alongside the wizard views you added earlier)
# ============================================================


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

# ============================================================
# STEP D-PREP: Add this view function to pages/views.py
# (alongside the other nutrition views)
# ============================================================

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

# --------------------------------------------------------------------------- #
# Unit Conversions Wizard
# --------------------------------------------------------------------------- #

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

# ============================================================================
# Urgent issue-comment notification
# Posted from the "Notify Now" button on the fsr_details comment list.
# Server-side 5-minute cooldown (URGENT_NOTIFICATION_COOLDOWN_MINUTES) per
# comment. Recipients = configured 'issue_comment_urgent' list MINUS the
# user pressing the button.
# ============================================================================

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def notify_comment_urgent(request, comment_id):
    """
    Fire an immediate "URGENT" email for a single issue comment.
    Routes to recipients of 'issue_comment_urgent' notification type, excluding
    the user pressing the button. Server-side cooldown of
    URGENT_NOTIFICATION_COOLDOWN_MINUTES suppresses repeat presses.

    POST only. Returns JSON for the AJAX caller.
    """
    from datetime import timedelta
    from pages.email_utils import (
        get_email_recipients,
        send_issue_comments_email,
        ADMIN_USER_INITIALS,
        URGENT_NOTIFICATION_COOLDOWN_MINUTES,
    )

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'reason': 'method_not_allowed'}, status=405)

    comment = get_object_or_404(issues_details, pk=comment_id)
    now = timezone.now()

    # Cooldown check (defense in depth — the UI also blocks)
    if comment.issues_details_last_notified_at:
        elapsed = now - comment.issues_details_last_notified_at
        cooldown = timedelta(minutes=URGENT_NOTIFICATION_COOLDOWN_MINUTES)
        if elapsed < cooldown:
            seconds_remaining = int((cooldown - elapsed).total_seconds())
            return JsonResponse({
                'ok': False,
                'reason': 'cooldown',
                'seconds_remaining': seconds_remaining,
                'minutes_ago': int(elapsed.total_seconds() // 60),
            }, status=429)

    # Build the single-comment payload (same shape get_yesterdays_issue_comments returns)
    issue = comment.issues
    prop = issue.prop if issue else None
    user_initials = (comment.issues_details_user or '').strip()
    is_admin = user_initials.upper() in [u.upper() for u in ADMIN_USER_INITIALS]

    comment_payload = [{
        'comment': comment.issues_details_comment or '',
        'user': user_initials or 'Unknown',
        'is_admin': is_admin,
        'date': (comment.issues_details_date.strftime('%Y/%m/%d')
                 if comment.issues_details_date else now.strftime('%Y/%m/%d')),
        'issue_heading': (issue.issues_heading if issue else None) or 'Untitled Issue',
        'issue_description': (issue.issues_description if issue else '') or '',
        'issue_status': (issue.issues_status if issue else None) or 'Unknown',
        'prop_name': (prop.prop_name if prop else 'Unknown Property'),
        'prop_country': (getattr(prop, 'prop_country', '') if prop else '') or '',
    }]

    # Recipients minus the presser
    presser_email = (request.user.email or '').lower()
    all_recipients = get_email_recipients('issue_comment_urgent')
    recipients = {
        'to':  [r for r in all_recipients['to']  if r.lower() != presser_email],
        'cc':  [r for r in all_recipients['cc']  if r.lower() != presser_email],
        'all': [r for r in all_recipients['all'] if r.lower() != presser_email],
    }

    if not recipients['all']:
        return JsonResponse({
            'ok': False,
            'reason': 'no_recipients',
            'message': 'No other recipients configured for urgent alerts. '
                       'Add one in the notification settings.',
        }, status=400)

    now_label = now.strftime('%Y/%m/%d %H:%M')
    presser_name = request.user.get_full_name() or request.user.username

    ok = send_issue_comments_email(
        comments=comment_payload,
        subject="URGENT - Issue needs attention",
        header_label=f"URGENT ISSUE COMMENT - {now_label}",
        intro_text=(f"The following comment was flagged as urgent by {presser_name} "
                    f"and requires immediate attention:"),
        recipients=recipients,
    )

    if not ok:
        return JsonResponse({'ok': False, 'reason': 'send_failed'}, status=500)

    # Record timestamp so the cooldown blocks the next press for 5 minutes
    comment.issues_details_last_notified_at = now
    comment.save(update_fields=['issues_details_last_notified_at'])

    return JsonResponse({
        'ok': True,
        'last_notified_at': now.isoformat(),
    })
