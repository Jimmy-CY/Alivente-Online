from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.db import connection, transaction
from django.db.models import Q, Prefetch, Subquery, OuterRef, Sum, F
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseServerError, FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string, get_template
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST, require_http_methods
from django.views.static import serve
from docxtpl import DocxTemplate
from .translation_service import ensure_project_translations, get_translated_text
from . import forms
from .forms import PropForm, TenantForm, PettyForm, InvoicesForm, IssuesForm, DetailsForm, SupplierForm, ValuesForm, RevenueTypesForm, RevenueLineForm, RevenueForm, ExpenseTypesForm, ExpenseLineForm, ExpenseForm, ActExpenseForm 
from .models import (
    props,
    petty,
    issues,
    issues_details, 
    tenant, 
    invoices,
    supplier,
    prop_values,
    revenue_types,
    revenue_line_types,
    revenue,
    expense_types,
    expense_line_types,
    expense,
    act_expense,
    Project, 
    ProjectTask,
    ProjectDocument,
    Passport,
    )
import decimal
from decimal import Decimal
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlparse, parse_qs
from xhtml2pdf import pisa
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re
import uuid
import logging
import json
import tempfile

logger = logging.getLogger(__name__)

### PASSPORT MANAGEMENT ###
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
from .models import Passport  # Adjust import based on your app structure


@login_required
def passport_management(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # ADD NEW PASSPORT/ID
        if action == 'add':
            holder_name = request.POST.get('holder_name')
            document_type = request.POST.get('document_type')
            document_number = request.POST.get('document_number')
            country_of_issue = request.POST.get('country_of_issue')
            date_of_issue = request.POST.get('date_of_issue') or None
            expiry_date = request.POST.get('expiry_date') or None
            status = request.POST.get('status')
            document_file = request.FILES.get('document_file')
            
            try:
                Passport.objects.create(
                    holder_name=holder_name,
                    document_type=document_type,
                    document_number=document_number,
                    country_of_issue=country_of_issue,
                    date_of_issue=date_of_issue,
                    expiry_date=expiry_date,
                    status=status,
                    document_file=document_file
                )
                messages.success(request, f'Passport/ID for {holder_name} added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding passport/ID: {str(e)}')
        
        # EDIT PASSPORT/ID
        elif action == 'edit':
            passport_id = request.POST.get('passport_id')
            passport = get_object_or_404(Passport, id=passport_id)
            
            passport.holder_name = request.POST.get('holder_name')
            passport.document_type = request.POST.get('document_type')
            passport.document_number = request.POST.get('document_number')
            passport.country_of_issue = request.POST.get('country_of_issue')
            passport.date_of_issue = request.POST.get('date_of_issue') or None
            passport.expiry_date = request.POST.get('expiry_date') or None
            passport.status = request.POST.get('status')
            
            # Update file if a new one is uploaded
            if request.FILES.get('document_file'):
                passport.document_file = request.FILES.get('document_file')
            
            try:
                passport.save()
                messages.success(request, f'Passport/ID for {passport.holder_name} updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating passport/ID: {str(e)}')
        
        # UPLOAD DOCUMENT
        elif action == 'upload':
            passport_id = request.POST.get('passport_id')
            passport = get_object_or_404(Passport, id=passport_id)
            document_file = request.FILES.get('document_file')
            
            if document_file:
                passport.document_file = document_file
                try:
                    passport.save()
                    messages.success(request, f'Document uploaded successfully for {passport.holder_name}!')
                except Exception as e:
                    messages.error(request, f'Error uploading document: {str(e)}')
            else:
                messages.error(request, 'No file selected.')
        
        # DELETE PASSPORT/ID
        elif action == 'delete':
            passport_id = request.POST.get('passport_id')
            passport = get_object_or_404(Passport, id=passport_id)
            holder_name = passport.holder_name
            
            try:
                # Delete the file from storage
                if passport.document_file:
                    passport.document_file.delete()
                passport.delete()
                messages.success(request, f'Passport/ID for {holder_name} deleted successfully!')
            except Exception as e:
                messages.error(request, f'Error deleting passport/ID: {str(e)}')
        
        return redirect('passport_management')
    
    # GET request - display all passports
    passports = Passport.objects.all().order_by('-created_at')
    
    # Add expiry warning flag to each passport (for 6-month warning)
    today = date.today()
    six_months_from_now = today + timedelta(days=180)
    
    for passport in passports:
        if passport.expiry_date:
            # Flag if expiry date is within 6 months or already expired
            passport.expiring_soon = passport.expiry_date <= six_months_from_now
        else:
            passport.expiring_soon = False
    
    context = {
        'passports': passports,
    }
    
    return render(request, 'passport_management.html', context)

### LEASE TEMPLATE GENERATOR ###
import re

def is_superuser(user):
    """Check if user is superuser"""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
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

@csrf_exempt
@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def get_property_tenant_data(request):
    """
    AJAX endpoint to get property and tenant data for the modal
    """
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        tenant_id = data.get('tenant_id')
        
        response_data = {}
        
        # Get property data
        if property_id:
            try:
                property_obj = props.objects.get(prop_id=property_id)
                
                # Build full address
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
                
                response_data['property'] = {
                    'prop_id': property_obj.prop_id,
                    'prop_name': property_obj.prop_name or '',
                    'prop_address1': property_obj.prop_address1 or '',
                    'prop_address2': property_obj.prop_address2 or '',
                    'prop_suburb': property_obj.prop_suburb or '',
                    'prop_city': property_obj.prop_city or '',
                    'prop_province': property_obj.prop_province or '',
                    'prop_country': property_obj.prop_country or '',
                    'prop_pcode': property_obj.prop_pcode or '',
                    'prop_floor_area': property_obj.prop_floor_area or '',
                    'prop_year_built': property_obj.prop_year_built or '',
                    'full_address': full_address,
                    'prop_electricity': property_obj.prop_electricity or '',
                    'prop_water': property_obj.prop_water or '',
                    'prop_refuse': property_obj.prop_refuse or '',
                    'prop_sewerage': property_obj.prop_sewerage or '',
                    'prop_insurance': property_obj.prop_insurance or '',
                }
            except props.DoesNotExist:
                response_data['property_error'] = 'Property not found'
                logger.warning(f"Property with ID {property_id} not found")
        
        # Get tenant data
        if tenant_id:
            try:
                tenant_obj = tenant.objects.get(tenant_id=tenant_id)
                response_data['tenant'] = {
                    'tenant_id': tenant_obj.tenant_id,
                    'tenant_name': tenant_obj.tenant_name or '',
                    'tenant_type': tenant_obj.tenant_type or '',
                    'tenant_contact_person': tenant_obj.tenant_contact_person or '',
                    'tenant_contact_number': tenant_obj.tenant_contact_number or '',
                    'tenant_email': tenant_obj.tenant_email or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                    'tenant_rent': float(tenant_obj.tenant_rent) if tenant_obj.tenant_rent else 0,
                    'tenant_deposit': float(tenant_obj.tenant_deposit) if tenant_obj.tenant_deposit else 0,
                    'tenant_levies': float(tenant_obj.tenant_levies) if tenant_obj.tenant_levies else 0,
                    'tenant_payment_terms': tenant_obj.tenant_payment_terms or '',
                    'tenant_rental_type': tenant_obj.tenant_rental_type or '',
                    'tenant_renewal': tenant_obj.tenant_renewal or '',
                    'tenant_renewal_period': tenant_obj.tenant_renewal_period or '',
                }
            except tenant.DoesNotExist:
                response_data['tenant_error'] = 'Tenant not found'
                logger.warning(f"Tenant with ID {tenant_id} not found")
        elif tenant_id is None:
            # Handle case where no tenant_id is provided (new tenant case)
            response_data['tenant'] = None
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in get_property_tenant_data: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in get_property_tenant_data: {str(e)}")
        return JsonResponse({'error': 'Server error occurred'}, status=500)

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

### CASH FLOW ###
@login_required
def cashflow_forecast(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        horizon_months = int(request.GET.get("horizon", 12))
        today = date.today()
        
        # Calculate horizon cutoff date
        horizon_year = today.year + (today.month + horizon_months - 1) // 12
        horizon_month = (today.month + horizon_months - 1) % 12 + 1
        horizon_last_day = monthrange(horizon_year, horizon_month)[1]
        cutoff_date = date(horizon_year, horizon_month, horizon_last_day)
        
        expenses = []
        
        # Handle budget expenses - they repeat every year
        for exp in expense.objects.select_related("prop", "expense_line_types").all():
            month_fields = [
                ("expense_jan", 1), ("expense_feb", 2), ("expense_mar", 3),
                ("expense_apr", 4), ("expense_may", 5), ("expense_jun", 6),
                ("expense_jul", 7), ("expense_aug", 8), ("expense_sep", 9),
                ("expense_oct", 10), ("expense_nov", 11), ("expense_dec", 12),
            ]
            
            for field, month_idx in month_fields:
                amount = getattr(exp, field)
                if amount and amount > decimal.Decimal("0.00"):
                    # Generate expenses for each year within the horizon
                    current_year = today.year
                    while True:
                        last_day = monthrange(current_year, month_idx)[1]
                        due_date = date(current_year, month_idx, last_day)
                        
                        # Break if beyond our cutoff date
                        if due_date > cutoff_date:
                            break
                        
                        # Only include if the date is today or in the future
                        if due_date >= today:
                            days_ahead = (due_date - today).days
                            if days_ahead <= 30:
                                color = "red"
                            elif days_ahead <= 90:
                                color = "orange"
                            else:
                                color = "green"
                                
                            expenses.append({
                                "id": f"{exp.expense_id}-{current_year}-{month_idx}",
                                "property": exp.prop.prop_name,
                                "amount": float(amount),
                                "due_date": due_date.strftime("%Y-%m-%d"),
                                "description": exp.expense_line_types.expense_line_types_name,
                                "line_type": exp.expense_line_types.expense_line_types_name,
                                "color": color,
                            })
                        
                        current_year += 1
        
        expenses.sort(key=lambda x: x["due_date"])
        return JsonResponse({"expenses": expenses})
    
    return render(request, "finance/cashflow_forecast.html")

### NOTIFICATIONS ###
@login_required
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

def get_vacant_properties(cursor):
    """Get properties that are active and available but have no current tenant"""
    # Get properties with current tenants
    cursor.execute("""
        SELECT prop.prop_name
        FROM railway.tenant
        JOIN railway.prop ON prop.prop_id = tenant.prop_id
        WHERE tenant.tenant_current = 'Yes'
    """)
    prop_active_tenant = [row[0] for row in cursor.fetchall()]
    
    # Get all active properties available for rent
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country
        FROM railway.prop
        WHERE prop.prop_status = 'Active'
        AND prop.prop_available_for_rent = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC
    """)
    active_properties_data = cursor.fetchall()
    
    # Find vacant properties
    vacant_properties = []
    for prop_data in active_properties_data:
        prop_name = prop_data[0]
        prop_country = prop_data[1]
        
        if prop_name not in prop_active_tenant:
            vacant_properties.append({
                'prop_name': prop_name,
                'prop_country': prop_country
            })
    
    return vacant_properties

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
        renewal_period = int(row[4])
        renewal_status = row[5] if row[5] else 'pending'
        
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
        renewal_period = int(row[4])
        renewal_status = row[5] if row[5] else 'pending'
        
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
@login_required
def financial_indicators_view(request):
    """
    Display the Financial Indicators Dashboard - ONLY for Active Properties
    Using Portfolio-Wide Calculations
    """
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request for property data
        try:
            # Get ONLY active properties for all calculations and display
            properties = props.objects.filter(prop_status='Active')
            properties_data = []
            
            # Portfolio-wide totals for all active properties
            portfolio_totals = {
                'total_revenue': Decimal('0.00'),
                'total_budgeted_expenses': Decimal('0.00'),
                'total_purchase_price': Decimal('0.00'),
                'total_current_value': Decimal('0.00'),
                'total_floor_area': 0,
                'property_count': 0
            }
            
            for prop in properties:
                # Get revenue totals using your existing revenue model structure
                revenue_total = calculate_property_revenue(prop)
                
                # Get ONLY budgeted expense totals using your existing expense model
                budgeted_expense_total = calculate_property_budgeted_expenses(prop)
                
                # Get property values - ONLY for active properties
                property_values = prop_values.objects.filter(prop=prop).first()
                purchase_price = property_values.prop_values_purchase_price if property_values else 0
                current_value = property_values.prop_values_current_value if property_values else 0
                
                # Add to portfolio totals
                portfolio_totals['total_revenue'] += revenue_total
                portfolio_totals['total_budgeted_expenses'] += budgeted_expense_total
                portfolio_totals['total_purchase_price'] += purchase_price or 0
                portfolio_totals['total_current_value'] += current_value or 0
                portfolio_totals['total_floor_area'] += prop.prop_floor_area or 0
                portfolio_totals['property_count'] += 1
                
                # Calculate individual property indicators for display purposes
                gross_roi = (revenue_total / purchase_price * 100) if purchase_price > 0 else 0
                net_roi = ((revenue_total - budgeted_expense_total) / purchase_price * 100) if purchase_price > 0 else 0
                expense_ratio = (budgeted_expense_total / revenue_total * 100) if revenue_total > 0 else 0
                rent_per_sqm = (revenue_total / 12 / prop.prop_floor_area) if prop.prop_floor_area and prop.prop_floor_area > 0 else 0
                value_increase = ((current_value - purchase_price) / purchase_price * 100) if purchase_price > 0 and current_value > 0 else 0
                
                # Store individual property data
                properties_data.append({
                    'id': prop.prop_id,
                    'name': prop.prop_name or f"Property {prop.prop_id}",
                    'status': prop.prop_status,
                    'grossROI': round(float(gross_roi), 2),
                    'netROI': round(float(net_roi), 2),
                    'expensesToRevenue': round(float(expense_ratio), 2),
                    'rentPerSqm': round(float(rent_per_sqm), 2),
                    'valueIncrease': round(float(value_increase), 2),
                    'revenue': float(revenue_total),
                    'expenses': float(budgeted_expense_total),
                    'profit': float(revenue_total - budgeted_expense_total)
                })
            
            # Calculate TRUE PORTFOLIO-WIDE indicators
            portfolio_indicators = {
                'grossROI': round(float(
                    (portfolio_totals['total_revenue'] / portfolio_totals['total_purchase_price'] * 100) 
                    if portfolio_totals['total_purchase_price'] > 0 else 0
                ), 2),
                'netROI': round(float(
                    ((portfolio_totals['total_revenue'] - portfolio_totals['total_budgeted_expenses']) / 
                     portfolio_totals['total_purchase_price'] * 100) 
                    if portfolio_totals['total_purchase_price'] > 0 else 0
                ), 2),
                'expensesToRevenue': round(float(
                    (portfolio_totals['total_budgeted_expenses'] / portfolio_totals['total_revenue'] * 100) 
                    if portfolio_totals['total_revenue'] > 0 else 0
                ), 2),
                'rentPerSqm': round(float(
                    (portfolio_totals['total_revenue'] / 12 / portfolio_totals['total_floor_area']) 
                    if portfolio_totals['total_floor_area'] > 0 else 0
                ), 2),
                'valueIncrease': round(float(
                    ((portfolio_totals['total_current_value'] - portfolio_totals['total_purchase_price']) / 
                     portfolio_totals['total_purchase_price'] * 100) 
                    if portfolio_totals['total_purchase_price'] > 0 and portfolio_totals['total_current_value'] > 0 else 0
                ), 2)
            }
            
            return JsonResponse({
                'properties': properties_data,
                'portfolio_indicators': portfolio_indicators,
                'portfolio_totals': {
                    'total_revenue': float(portfolio_totals['total_revenue']),
                    'total_expenses': float(portfolio_totals['total_budgeted_expenses']),
                    'total_purchase_price': float(portfolio_totals['total_purchase_price']),
                    'total_current_value': float(portfolio_totals['total_current_value']),
                    'total_floor_area': portfolio_totals['total_floor_area'],
                    'property_count': portfolio_totals['property_count']
                },
                'total_active_properties': len(properties_data),
                'message': f'Showing {len(properties_data)} active properties with portfolio-wide calculations (budgeted expenses only)'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Regular page load
    context = {
        'page_title': 'Financial Indicators Dashboard - Portfolio-Wide Analysis (Active Properties)'
    }
    return render(request, 'finance/financial_indicators.html', context)

def calculate_property_revenue(property_obj):
    """
    Calculate total annual revenue for a property using your revenue model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')
        
    # Get all revenue records for this active property
    revenue_records = revenue.objects.filter(prop=property_obj)
    
    total_revenue = Decimal('0.00')
    
    for record in revenue_records:
        # Sum all monthly revenue amounts
        monthly_total = (
            (record.revenue_jan or Decimal('0.00')) +
            (record.revenue_feb or Decimal('0.00')) +
            (record.revenue_mar or Decimal('0.00')) +
            (record.revenue_apr or Decimal('0.00')) +
            (record.revenue_may or Decimal('0.00')) +
            (record.revenue_jun or Decimal('0.00')) +
            (record.revenue_jul or Decimal('0.00')) +
            (record.revenue_aug or Decimal('0.00')) +
            (record.revenue_sep or Decimal('0.00')) +
            (record.revenue_oct or Decimal('0.00')) +
            (record.revenue_nov or Decimal('0.00')) +
            (record.revenue_dec or Decimal('0.00'))
        )
        total_revenue += monthly_total
    
    return total_revenue

def calculate_property_budgeted_expenses(property_obj):
    """
    Calculate total annual budgeted expenses for a property using your expense model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')
        
    # Get all budgeted expense records for this active property
    expense_records = expense.objects.filter(prop=property_obj)
    
    total_expenses = Decimal('0.00')
    
    for record in expense_records:
        # Sum all monthly expense amounts
        monthly_total = (
            (record.expense_jan or Decimal('0.00')) +
            (record.expense_feb or Decimal('0.00')) +
            (record.expense_mar or Decimal('0.00')) +
            (record.expense_apr or Decimal('0.00')) +
            (record.expense_may or Decimal('0.00')) +
            (record.expense_jun or Decimal('0.00')) +
            (record.expense_jul or Decimal('0.00')) +
            (record.expense_aug or Decimal('0.00')) +
            (record.expense_sep or Decimal('0.00')) +
            (record.expense_oct or Decimal('0.00')) +
            (record.expense_nov or Decimal('0.00')) +
            (record.expense_dec or Decimal('0.00'))
        )
        total_expenses += monthly_total
    
    return total_expenses

def calculate_property_actual_expenses(property_obj):
    """
    Calculate total actual expenses for a property using your act_expense model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')
        
    # Get all actual expense records for this active property
    actual_expenses = act_expense.objects.filter(prop=property_obj)
    
    # Sum all actual expense amounts
    total_actual = actual_expenses.aggregate(
        total=Sum('act_expense_amount')
    )['total'] or Decimal('0.00')
    
    return total_actual

# Additional helper function for year-specific calculations if needed
def calculate_property_revenue_for_year(property_obj, year):
    """
    Calculate revenue for a specific year (if you need year filtering later)
    This would require adding year fields to your revenue model or 
    filtering by revenue_types that have year information
    """
    # This is a placeholder - you'd need to modify based on how you handle years
    # in your revenue_types model or add year fields to your models
    return calculate_property_revenue(property_obj)

def calculate_property_expenses_for_year(property_obj, year):
    """
    Calculate expenses for a specific year (if you need year filtering later)
    """
    # For budgeted expenses
    budgeted = calculate_property_budgeted_expenses(property_obj)
    
    # For actual expenses, you can filter by year using the date field
    from django.db.models import Q
    actual_expenses = act_expense.objects.filter(
        prop=property_obj,
        act_expense_date__year=year
    )
    actual_total = actual_expenses.aggregate(
        total=Sum('act_expense_amount')
    )['total'] or Decimal('0.00')
    
    return budgeted + actual_total

### PROJECTS ###
@login_required
def projects_list(request):
    """Display list of projects with filtering and handle modal-based deletion - FULLY OPTIMIZED"""
    
    # Handle POST request for modal-based deletion
    if request.method == 'POST' and 'delete_project_id' in request.POST:
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to delete projects.")
            return redirect('projects')
        
        project_id = request.POST.get('delete_project_id')
        # OPTIMIZED: Use select_related and prefetch_related for deletion
        project = get_object_or_404(
            Project.objects.select_related('prop').prefetch_related('projecttask_set', 'project_documents'), 
            project_id=project_id
        )
        
        try:
            with transaction.atomic():
                logger.info(f"User {request.user.username} deleting project via modal: {project.project_name}")
                
                # OPTIMIZED: Use prefetched data for counts (no additional queries)
                all_tasks = list(project.projecttask_set.all())
                main_task_count = sum(1 for task in all_tasks if task.parent_task is None)
                subtask_count = sum(1 for task in all_tasks if task.parent_task is not None)
                document_count = len(list(project.project_documents.all())) if hasattr(project, 'project_documents') else 0
                project_name = project.project_name
                
                # Delete the project
                project.delete()
                
                # Success message
                if subtask_count > 0:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {main_task_count} main tasks, {subtask_count} subtasks, and {document_count} documents."
                    )
                else:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {main_task_count} tasks and {document_count} documents."
                    )
                
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            messages.error(request, f"An error occurred while deleting the project '{project.project_name}'.")
        
        return redirect('projects')
    
    # Initialize filter variables from GET parameters FIRST
    search_query = request.GET.get('search', '').strip()
    selected_property = request.GET.get('property', '')
    selected_status = request.GET.get('status', '')
    
    # FULLY OPTIMIZED: Build the base queryset WITHOUT prefetching unnecessary data
    # Only prefetch what's absolutely needed for the list view
    projects_queryset = Project.objects.select_related('prop')
    
    # Apply filters BEFORE any prefetching to reduce the dataset
    if search_query:
        projects_queryset = projects_queryset.filter(
            Q(project_name__icontains=search_query) |
            Q(project_description__icontains=search_query)
        )
    
    if selected_property:
        try:
            property_id = int(selected_property)
            projects_queryset = projects_queryset.filter(prop_id=property_id)
        except (ValueError, TypeError):
            selected_property = ""
    
    if selected_status:
        valid_statuses = [choice[0] for choice in Project.PROJECT_STATUS_CHOICES]
        if selected_status in valid_statuses:
            projects_queryset = projects_queryset.filter(project_status=selected_status)
        else:
            selected_status = ""
    
    # Apply ordering AFTER filtering
    projects_queryset = projects_queryset.order_by(F('project_start_date').desc(nulls_last=True))
    
    # REQUIRED: Template calls calculated methods that need task data
    # The template uses: get_calculated_status, get_progress_percentage, 
    # get_calculated_start_date, get_calculated_expected_completion
    # Use comprehensive prefetching to load ALL related task data in minimal queries
    projects_queryset = projects_queryset.prefetch_related(
        Prefetch('projecttask_set', 
            queryset=ProjectTask.objects.select_related().prefetch_related('subtasks')
        )
    )
    
    # If template only shows basic project info (name, description, dates, status), 
    # then DON'T prefetch tasks at all
    
    # OPTIMIZED: Single query for all properties (only if dropdown is used)
    properties = props.objects.only('prop_id', 'prop_name').order_by('prop_name')
    
    # Pagination with filter preservation
    paginator = Paginator(projects_queryset, 25)
    page_number = request.GET.get('page')
    projects_page = paginator.get_page(page_number)
    
    context = {
        'projects': projects_page,
        'properties': properties,
        'search_query': search_query,
        'selected_property': selected_property,
        'selected_status': selected_status,
        'status_choices': Project.PROJECT_STATUS_CHOICES,
    }
    
    return render(request, 'projects/projects.html', context)

@login_required
def projects_add(request):
    """Add new project"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to add projects.")
        return redirect('projects')
    
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        prop_id = request.POST.get('prop_id')
        project_start_date = request.POST.get('project_start_date')
        project_expected_completion_date = request.POST.get('project_expected_completion_date')
        project_status = request.POST.get('project_status', 'Pending')
        project_actual_completion_date = request.POST.get('project_actual_completion_date')
        project_description = request.POST.get('project_description')
        
        try:
            # Get the property
            property_obj = get_object_or_404(props, prop_id=prop_id)
            
            # Create the project
            project = Project(  # Updated model name
                project_name=project_name,
                prop=property_obj,
                project_start_date=project_start_date if project_start_date else None,
                project_expected_completion_date=project_expected_completion_date if project_expected_completion_date else None,
                project_status=project_status,
                project_actual_completion_date=project_actual_completion_date if project_actual_completion_date else None,
                project_description=project_description
            )
            project.save()
            
            messages.success(request, f"Project '{project_name}' has been created successfully.")
            return redirect('projects')
            
        except Exception as e:
            messages.error(request, f"Error creating project: {str(e)}")
    
    # Get all properties for dropdown
    properties = props.objects.all().order_by('prop_name')
    
    context = {
        'properties': properties,
        'status_choices': Project.PROJECT_STATUS_CHOICES,  # Updated model name
    }
    
    return render(request, 'projects/projects_add.html', context)

@login_required
def projects_edit(request, project_id):
    """Edit existing project - enhanced to handle Gantt chart returns"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to edit projects.")
        return redirect('projects')
    
    project = get_object_or_404(Project, project_id=project_id)
    
    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', 'false') == 'true'
    
    if request.method == 'POST':
        project.project_name = request.POST.get('project_name')
        prop_id = request.POST.get('prop_id')
        project.project_start_date = request.POST.get('project_start_date') if request.POST.get('project_start_date') else None
        project.project_expected_completion_date = request.POST.get('project_expected_completion_date') if request.POST.get('project_expected_completion_date') else None
        project.project_status = request.POST.get('project_status', 'Pending')
        project.project_actual_completion_date = request.POST.get('project_actual_completion_date') if request.POST.get('project_actual_completion_date') else None
        project.project_description = request.POST.get('project_description')
        
        # Add Greek translation fields
        project.project_name_greek = request.POST.get('project_name_greek', '').strip()
        project.project_description_greek = request.POST.get('project_description_greek', '').strip()
        
        try:
            # Update the property
            property_obj = get_object_or_404(props, prop_id=prop_id)
            project.prop = property_obj
            
            project.save()
            
            messages.success(request, f"Project '{project.project_name}' has been updated successfully.")
            
            # Redirect based on where user came from
            if from_gantt:
                return redirect('project_gantt', project_id=project_id)
            else:
                return redirect('projects')
                
        except Exception as e:
            messages.error(request, f"Error updating project: {str(e)}")
    
    # Get all properties for dropdown
    properties = props.objects.all().order_by('prop_name')
    
    context = {
        'project': project,
        'properties': properties,
        'status_choices': Project.PROJECT_STATUS_CHOICES,
        'from_gantt': from_gantt,  # Pass this to template for form action
    }
    
    return render(request, 'projects/projects_edit.html', context)

@login_required
def projects_delete(request, project_id):
    """Delete project with enhanced cascade deletion and warnings - OPTIMIZED"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to delete projects.")
        return redirect('projects')
    
    # OPTIMIZED: Single query with prefetching for counts
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            'projecttask_set', 'project_documents'
        ), 
        project_id=project_id
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                logger.info(f"User {request.user.username} attempting to delete project: {project.project_name} (ID: {project_id})")
                
                # OPTIMIZED: Use prefetched data for counts (no additional queries)
                all_tasks = list(project.projecttask_set.all())
                main_task_count = sum(1 for task in all_tasks if task.parent_task is None)
                subtask_count = sum(1 for task in all_tasks if task.parent_task is not None)
                total_task_count = len(all_tasks)
                document_count = len(list(project.project_documents.all())) if hasattr(project, 'project_documents') else 0
                
                project_name = project.project_name
                
                # Delete the project (this will cascade to delete all related tasks and subtasks)
                project.delete()
                
                logger.info(f"Successfully deleted project: {project_name} (ID: {project_id}) with {main_task_count} main tasks, {subtask_count} subtasks, and {document_count} documents")
                
                # Success message with detailed information
                if subtask_count > 0:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {main_task_count} main tasks, {subtask_count} subtasks, and {document_count} documents."
                    )
                else:
                    messages.success(
                        request, 
                        f"Project '{project_name}' has been permanently deleted along with {total_task_count} tasks and {document_count} documents."
                    )
                
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            messages.error(
                request, 
                f"An error occurred while deleting the project '{project.project_name}'. Please try again or contact support."
            )
            return render(request, 'projects/projects_delete.html', {'project': project})
        
        return redirect('projects')
    
    # OPTIMIZED: Use prefetched data for confirmation page (no additional queries)
    all_tasks = list(project.projecttask_set.all())
    main_tasks = [task for task in all_tasks if task.parent_task is None]
    subtasks = [task for task in all_tasks if task.parent_task is not None]
    documents = list(project.project_documents.all()) if hasattr(project, 'project_documents') else []
    
    context = {
        'project': project,
        'main_task_count': len(main_tasks),
        'subtask_count': len(subtasks),
        'document_count': len(documents),
        'main_tasks': main_tasks[:5],  # Show first 5 main tasks as examples
        'subtasks': subtasks[:10],     # Show first 10 subtasks as examples
        'documents': documents[:5],    # Show first 5 documents as examples
    }
    
    return render(request, 'projects/projects_delete.html', context)

@login_required
def projects_detail(request, project_id):
    """Display project details with tasks and subtasks - OPTIMIZED"""
    # OPTIMIZED: Single query with comprehensive prefetching
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            Prefetch('projecttask_set', 
                queryset=ProjectTask.objects.filter(parent_task__isnull=True).prefetch_related(
                    Prefetch('subtasks', queryset=ProjectTask.objects.all())
                ).order_by('task_start_date', 'task_id')
            )
        ), 
        project_id=project_id
    )
    
    # OPTIMIZED: Use prefetched data (no additional queries)
    main_tasks = list(project.projecttask_set.all())  # These are already filtered and ordered
    
    context = {
        'project': project,
        'main_tasks': main_tasks,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,
    }
    
    return render(request, 'projects/projects_detail.html', context)

@login_required
def project_tasks_add(request, project_id):
    """Add new task to project"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to add tasks.")
        return redirect('projects_detail', project_id=project_id)
    
    project = get_object_or_404(Project, project_id=project_id)  # Updated model name
    
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task_description = request.POST.get('task_description')
        task_start_date = request.POST.get('task_start_date')
        task_expected_completion_date = request.POST.get('task_expected_completion_date')
        task_status = request.POST.get('task_status', 'Pending')
        task_priority = request.POST.get('task_priority', 'Medium')
        task_budgeted_cost = request.POST.get('task_budgeted_cost')
        task_actual_cost = request.POST.get('task_actual_cost')
        task_assigned_to = request.POST.get('task_assigned_to')
        task_actual_completion_date = request.POST.get('task_actual_completion_date')
        
        try:
            task = ProjectTask(  # Updated model name
                project=project,
                task_name=task_name,
                task_description=task_description,
                task_start_date=task_start_date if task_start_date else None,
                task_expected_completion_date=task_expected_completion_date if task_expected_completion_date else None,
                task_status=task_status,
                task_priority=task_priority,
                task_budgeted_cost=task_budgeted_cost if task_budgeted_cost else 0.00,
                task_actual_cost=task_actual_cost if task_actual_cost else 0.00,
                task_assigned_to=task_assigned_to,
                task_actual_completion_date=task_actual_completion_date if task_actual_completion_date else None
            )
            task.save()
            
            messages.success(request, f"Task '{task_name}' has been added successfully.")
            return redirect('projects_detail', project_id=project_id)
            
        except Exception as e:
            messages.error(request, f"Error adding task: {str(e)}")
    
    context = {
        'project': project,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,  # Updated model name
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,  # Updated model name
    }
    
    return render(request, 'projects/project_tasks_add.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from .models import Project, ProjectTask

def project_tasks_edit(request, project_id, task_id):
    """
    Edit a project task or subtask with support for Greek language fields
    """
    project = get_object_or_404(Project, project_id=project_id)
    task = get_object_or_404(ProjectTask, task_id=task_id, project=project)
    
    # Check if coming from Gantt chart
    from_gantt = request.GET.get('from_gantt', False)
    
    if request.method == 'POST':
        try:
            # Update basic task fields (always editable)
            task.task_name = request.POST.get('task_name', '').strip()
            task.task_description = request.POST.get('task_description', '').strip()
            
            # Update Greek fields
            task.task_name_greek = request.POST.get('task_name_greek', '').strip()
            task.task_description_greek = request.POST.get('task_description_greek', '').strip()
            
            # Update priority (always editable)
            task.task_priority = request.POST.get('task_priority')
            
            # Handle different logic for main tasks vs subtasks
            if task.parent_task:  # This is a subtask - most fields are editable
                # Status is editable for subtasks
                task.task_status = request.POST.get('task_status')
                
                # Dates are editable for subtasks
                start_date = request.POST.get('task_start_date')
                if start_date:
                    task.task_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                else:
                    task.task_start_date = None
                
                expected_date = request.POST.get('task_expected_completion_date')
                if expected_date:
                    task.task_expected_completion_date = datetime.strptime(expected_date, '%Y-%m-%d').date()
                else:
                    task.task_expected_completion_date = None
                
                # Handle actual completion date (only for subtasks when status is Completed)
                actual_date = request.POST.get('task_actual_completion_date')
                if actual_date:
                    task.task_actual_completion_date = datetime.strptime(actual_date, '%Y-%m-%d').date()
                else:
                    task.task_actual_completion_date = None
                
                # Costs are editable for subtasks
                budgeted_cost = request.POST.get('task_budgeted_cost')
                if budgeted_cost:
                    task.task_budgeted_cost = Decimal(budgeted_cost)
                else:
                    task.task_budgeted_cost = Decimal('0.00')
                
                actual_cost = request.POST.get('task_actual_cost')
                if actual_cost:
                    task.task_actual_cost = Decimal(actual_cost)
                else:
                    task.task_actual_cost = Decimal('0.00')
                
                # Progress percentage is editable for subtasks
                progress = request.POST.get('task_progress_percentage')
                if progress:
                    task.task_progress_percentage = int(progress)
                else:
                    task.task_progress_percentage = 0
                
                # Assigned to is editable for subtasks
                task.task_assigned_to = request.POST.get('task_assigned_to', '').strip()
                
            else:  # This is a main task - most fields are auto-calculated
                # For main tasks, only basic info and priority are directly editable
                # Status, dates, and costs are calculated from subtasks
                # The model's calculation methods will handle the auto-calculation
                pass
            
            # Validate the task before saving
            task.full_clean()
            
            # Save the task
            task.save()
            
            # Success message
            if task.parent_task:
                messages.success(request, f'Subtask "{task.task_name}" updated successfully!')
            else:
                messages.success(request, f'Main task "{task.task_name}" updated successfully!')
            
            # Redirect based on where we came from
            if from_gantt:
                return redirect('project_gantt', project_id=project.project_id)
            else:
                return redirect('projects_detail', project_id=project.project_id)
                
        except ValidationError as e:
            # Handle Django model validation errors
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    field_name = field.replace('_', ' ').title()
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
            else:
                error_messages = e.messages if hasattr(e, 'messages') else [str(e)]
            
            for error_msg in error_messages:
                messages.error(request, error_msg)
                
        except ValueError as e:
            # Handle value conversion errors (dates, decimals, etc.)
            if 'time data' in str(e):
                messages.error(request, 'Invalid date format. Please use the date picker.')
            elif 'invalid literal' in str(e):
                messages.error(request, 'Invalid number format. Please enter valid numbers for costs and percentages.')
            else:
                messages.error(request, f'Invalid data: {str(e)}')
                
        except Exception as e:
            # Handle any other unexpected errors
            messages.error(request, f'Error updating task: {str(e)}')
    
    # Prepare context for the template
    context = {
        'project': project,
        'task': task,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,
        'from_gantt': from_gantt,
    }
    
    return render(request, 'projects/project_tasks_edit.html', context)

@login_required
@require_http_methods(["POST"])
def translate_text(request):
    """
    Translate text using Google Translate API
    """
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        target_language = data.get('target_language', 'greek')
        source_language = data.get('source_language', 'english')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'No text provided'})
        
        # Use Google Translate service
        if target_language == 'greek':
            translated_text = translate_to_greek_service(text)
        else:
            translated_text = text
        
        return JsonResponse({
            'success': True,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })
        
    except Exception as e:
        print(f"Translation view error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def translate_to_greek_service(text):
    """
    Use Google Translate API to translate English text to Greek
    """
    try:
        from googletrans import Translator
        
        # Initialize Google Translator
        translator = Translator()
        
        # Translate from English to Greek
        result = translator.translate(text, dest='el', src='en')
        
        return result.text
        
    except Exception as e:
        print(f"Google Translation service error: {e}")
        return text  # Return original text if translation fails

@login_required
def project_tasks_delete(request, project_id, task_id):
    """Delete task"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to delete tasks.")
        return redirect('projects_detail', project_id=project_id)
    
    project = get_object_or_404(Project, project_id=project_id)  # Updated model name
    task = get_object_or_404(ProjectTask, task_id=task_id, project=project)  # Updated model name
    task_name = task.task_name
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, f"Task '{task_name}' has been deleted successfully.")
        return redirect('projects_detail', project_id=project_id)
    
    context = {
        'project': project,
        'task': task,
    }
    
    return render(request, 'projects/project_tasks_delete.html', context)

@login_required
def project_subtasks_add(request, project_id, parent_task_id):
    """Add subtask to a main task"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to add subtasks.")
        return redirect('projects_detail', project_id=project_id)
    
    project = get_object_or_404(Project, project_id=project_id)  # Updated model name
    parent_task = get_object_or_404(ProjectTask, task_id=parent_task_id, project=project)  # Updated model name
    
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task_description = request.POST.get('task_description')
        task_start_date = request.POST.get('task_start_date')
        task_expected_completion_date = request.POST.get('task_expected_completion_date')
        task_status = request.POST.get('task_status', 'Pending')
        task_priority = request.POST.get('task_priority', 'Medium')
        task_budgeted_cost = request.POST.get('task_budgeted_cost')
        task_actual_cost = request.POST.get('task_actual_cost')
        task_assigned_to = request.POST.get('task_assigned_to')
        task_actual_completion_date = request.POST.get('task_actual_completion_date')
        
        try:
            subtask = ProjectTask(  # Updated model name
                project=project,
                parent_task=parent_task,
                task_name=task_name,
                task_description=task_description,
                task_start_date=task_start_date if task_start_date else None,
                task_expected_completion_date=task_expected_completion_date if task_expected_completion_date else None,
                task_status=task_status,
                task_priority=task_priority,
                task_budgeted_cost=task_budgeted_cost if task_budgeted_cost else 0.00,
                task_actual_cost=task_actual_cost if task_actual_cost else 0.00,
                task_assigned_to=task_assigned_to,
                task_actual_completion_date=task_actual_completion_date if task_actual_completion_date else None
            )
            subtask.save()
            
            messages.success(request, f"Subtask '{task_name}' has been added successfully.")
            return redirect('projects_detail', project_id=project_id)
            
        except Exception as e:
            messages.error(request, f"Error adding subtask: {str(e)}")
    
    context = {
        'project': project,
        'parent_task': parent_task,
        'task_status_choices': ProjectTask.TASK_STATUS_CHOICES,  # Updated model name
        'task_priority_choices': ProjectTask.TASK_PRIORITY_CHOICES,  # Updated model name
    }
    
    return render(request, 'projects/project_subtasks_add.html', context)

@login_required
def project_gantt(request, project_id):
    """Display Gantt chart for project with tasks and subtasks - OPTIMIZED"""
    # OPTIMIZED: Single query with comprehensive prefetching
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            Prefetch('projecttask_set', 
                queryset=ProjectTask.objects.filter(parent_task__isnull=True).prefetch_related(
                    Prefetch('subtasks', 
                        queryset=ProjectTask.objects.filter(
                            task_start_date__isnull=False,
                            task_expected_completion_date__isnull=False
                        ).order_by('task_start_date', 'task_id')
                    )
                ).order_by('task_start_date', 'task_id')
            )
        ), 
        project_id=project_id
    )
    
    # Check if returning from edit page
    from_edit = request.GET.get('from_edit', False)
    if from_edit:
        messages.success(request, "Changes saved successfully. Gantt chart has been refreshed.")
    
    # OPTIMIZED: Use prefetched data (no additional queries)
    main_tasks = list(project.projecttask_set.all())
    
    # Build Gantt data structure using prefetched data
    gantt_data = []
    
    # Add project as the main item
    project_start = project.get_calculated_start_date()
    project_end = project.get_calculated_expected_completion()
    
    if project_start and project_end:
        project_item = {
            'id': f'project_{project.project_id}',
            'text': project.project_name,
            'start_date': project_start.strftime('%Y-%m-%d'),
            'end_date': project_end.strftime('%Y-%m-%d'),
            'duration': (project_end - project_start).days + 1,
            'progress': project.get_progress_percentage() / 100,
            'type': 'project',
            'status': project.get_calculated_status(),
            'budgeted_cost': float(project.get_calculated_budgeted_cost() or 0),
            'actual_cost': float(project.get_calculated_actual_cost() or 0),
            'open': True
        }
        gantt_data.append(project_item)
    
    # Add main tasks and their subtasks using prefetched data
    for task in main_tasks:
        task_start = task.get_calculated_start_date()
        task_end = task.get_calculated_expected_completion()
        
        if task_start and task_end:
            # Add main task
            task_item = {
                'id': f'task_{task.task_id}',
                'text': task.task_name,
                'start_date': task_start.strftime('%Y-%m-%d'),
                'end_date': task_end.strftime('%Y-%m-%d'),
                'duration': (task_end - task_start).days + 1,
                'progress': task.get_subtask_progress() / 100 if task.subtasks.all() else (1.0 if task.get_calculated_status() == 'Completed' else 0.0),
                'type': 'task',
                'status': task.get_calculated_status(),
                'budgeted_cost': float(task.get_calculated_budgeted_cost() or 0),
                'actual_cost': float(task.get_calculated_actual_cost() or 0),
                'assigned_to': task.task_assigned_to or '',
                'parent': f'project_{project.project_id}' if project_start and project_end else None,
                'open': True,
                'calculated_progress_percentage': round(task.get_subtask_progress(), 1)
            }
            gantt_data.append(task_item)
            
            # Add subtasks for this main task using prefetched data
            subtasks = list(task.subtasks.all())  # Already filtered in prefetch
            
            for subtask in subtasks:
                subtask_start = subtask.task_start_date
                subtask_end = subtask.task_expected_completion_date
                
                if subtask_start and subtask_end:
                    # Calculate progress for subtask
                    subtask_progress = 0
                    if subtask.task_status == 'Completed':
                        subtask_progress = 1.0
                    elif subtask.task_status == 'In Progress':
                        subtask_progress = (subtask.task_progress_percentage or 0) / 100
                    
                    subtask_item = {
                        'id': f'subtask_{subtask.task_id}',
                        'text': subtask.task_name,
                        'start_date': subtask_start.strftime('%Y-%m-%d'),
                        'end_date': subtask_end.strftime('%Y-%m-%d'),
                        'duration': (subtask_end - subtask_start).days + 1,
                        'progress': subtask_progress,
                        'type': 'subtask',
                        'status': subtask.task_status,
                        'budgeted_cost': float(subtask.task_budgeted_cost or 0),
                        'actual_cost': float(subtask.task_actual_cost or 0),
                        'assigned_to': subtask.task_assigned_to or '',
                        'parent': f'task_{task.task_id}',
                        'priority': subtask.task_priority,
                        'progress_percentage': subtask.task_progress_percentage or 0
                    }
                    gantt_data.append(subtask_item)
    
    # If no tasks have dates, create a placeholder message
    if not gantt_data:
        from datetime import datetime
        today = datetime.now().date()
        placeholder_item = {
            'id': 'placeholder_1',
            'text': f'{project.project_name} (No dates set)',
            'start_date': today.strftime('%Y-%m-%d'),
            'duration': 30,
            'progress': 0,
            'type': 'project',
            'status': 'Pending'
        }
        gantt_data.append(placeholder_item)
    
    context = {
        'project': project,
        'main_tasks': main_tasks,
        'gantt_data': json.dumps(gantt_data),
    }
    
    return render(request, 'projects/project_gantt.html', context)

@login_required
def ajax_update_project_status(request):
    """AJAX view to update project status"""
    if request.method == 'POST' and request.user.is_superuser:
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            new_status = data.get('status')
            actual_completion_date = data.get('actual_completion_date')
            
            project = get_object_or_404(Project, project_id=project_id)
            project.project_status = new_status
            
            if new_status == 'Completed' and actual_completion_date:
                project.project_actual_completion_date = actual_completion_date
            elif new_status != 'Completed':
                project.project_actual_completion_date = None
            
            project.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Project status updated to {new_status}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error updating project status: {str(e)}"
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def ajax_update_task_status(request):
    """AJAX view to update task status"""
    if request.method == 'POST' and request.user.is_superuser:
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            new_status = data.get('status')
            actual_completion_date = data.get('actual_completion_date')
            
            task = get_object_or_404(ProjectTask, task_id=task_id)
            task.task_status = new_status
            
            if new_status == 'Completed' and actual_completion_date:
                task.task_actual_completion_date = actual_completion_date
            elif new_status != 'Completed':
                task.task_actual_completion_date = None
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Task status updated to {new_status}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error updating task status: {str(e)}"
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def ajax_duplicate_project(request):
    """
    OPTIMIZED: AJAX view to duplicate a project with all its tasks and subtasks,
    adjusting all dates based on the new project start date and handling budget copy options
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'})
    
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to duplicate projects'
        })
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        project_id = data.get('project_id')
        new_project_name = data.get('new_project_name', '').strip()
        new_project_description = data.get('new_project_description', '').strip()
        new_project_start_date_str = data.get('new_project_start_date', '').strip()
        budget_copy_option = data.get('budget_copy_option', 'budgeted')
        clear_greek_translations = data.get('clear_greek_translations', False)
        
        # Validate required fields
        if not project_id or not new_project_name or not new_project_description or not new_project_start_date_str:
            return JsonResponse({
                'success': False,
                'message': 'Project ID, new project name, description, and start date are required'
            })
        
        # Validate budget copy option
        if budget_copy_option not in ['budgeted', 'actual']:
            budget_copy_option = 'budgeted'
        
        # Parse the new start date
        try:
            from datetime import datetime, timedelta
            new_project_start_date = datetime.strptime(new_project_start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid date format. Please use YYYY-MM-DD format.'
            })
        
        # Ensure project_id is an integer
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': f'Invalid project ID: {project_id}'
            })
        
        # OPTIMIZED: Get the original project with comprehensive prefetching
        try:
            original_project = Project.objects.select_related('prop').prefetch_related(
                Prefetch('projecttask_set', 
                    queryset=ProjectTask.objects.select_related().prefetch_related('subtasks')
                ),
                'project_documents'
            ).get(project_id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Project with ID {project_id} was not found'
            })
        
        # Check if project name already exists
        if Project.objects.filter(project_name=new_project_name).exists():
            return JsonResponse({
                'success': False,
                'message': f'A project with the name "{new_project_name}" already exists'
            })
        
        # Calculate date offset if original project has a start date
        date_offset = None
        original_start_date = original_project.get_calculated_start_date()
        
        if original_start_date:
            date_offset = (new_project_start_date - original_start_date).days
        
        def adjust_date(original_date, offset_days):
            """Helper function to adjust a date by the offset"""
            if original_date and offset_days is not None:
                return original_date + timedelta(days=offset_days)
            return original_date
        
        def get_cost_for_budget(original_task, budget_option):
            """Helper function to determine which cost to use as the new budget"""
            if budget_option == 'actual':
                return original_task.task_actual_cost
            else:
                return original_task.task_budgeted_cost
        
        # Use transaction to ensure all-or-nothing duplication
        with transaction.atomic():
            # Calculate new project dates
            new_project_expected_completion = None
            if original_project.get_calculated_expected_completion() and date_offset is not None:
                new_project_expected_completion = adjust_date(
                    original_project.get_calculated_expected_completion(), 
                    date_offset
                )
            
            # Calculate new project budget based on option
            new_project_total_budgeted_cost = original_project.project_total_budgeted_cost
            if budget_copy_option == 'actual':
                new_project_total_budgeted_cost = original_project.get_calculated_actual_cost()
            
            # Create new project
            new_project = Project.objects.create(
                project_name=new_project_name,
                project_description=new_project_description,
                prop=original_project.prop,
                project_start_date=new_project_start_date,
                project_expected_completion_date=new_project_expected_completion,
                project_status='Pending',
                project_actual_completion_date=None,
                project_total_budgeted_cost=new_project_total_budgeted_cost,
                project_total_actual_cost=Decimal('0.00'),
                project_name_greek=None if clear_greek_translations else getattr(original_project, 'project_name_greek', None),
                project_description_greek=None if clear_greek_translations else getattr(original_project, 'project_description_greek', None),
            )
            
            # OPTIMIZED: Get all tasks using prefetched data
            all_original_tasks = list(original_project.projecttask_set.all())
            main_tasks = [task for task in all_original_tasks if task.parent_task_id is None]
            
            # OPTIMIZED: Prepare bulk data for main tasks
            main_tasks_to_create = []
            task_id_mapping = {}  # Map old task ID to new task index
            
            # First pass: Prepare main tasks for bulk creation
            for original_task in main_tasks:
                new_task_start_date = adjust_date(original_task.task_start_date, date_offset)
                new_task_expected_completion = adjust_date(original_task.task_expected_completion_date, date_offset)
                new_task_budgeted_cost = get_cost_for_budget(original_task, budget_copy_option)
                
                new_task = ProjectTask(
                    project=new_project,
                    task_name=original_task.task_name,
                    task_description=original_task.task_description,
                    task_start_date=new_task_start_date,
                    task_expected_completion_date=new_task_expected_completion,
                    task_budgeted_cost=new_task_budgeted_cost,
                    task_actual_cost=Decimal('0.00'),
                    task_priority=original_task.task_priority,
                    task_status='Pending',
                    task_actual_completion_date=None,
                    task_assigned_to=original_task.task_assigned_to,
                    parent_task=None,
                    task_progress_percentage=0,
                    task_name_greek=getattr(original_task, 'task_name_greek', None),
                    task_description_greek=getattr(original_task, 'task_description_greek', None),
                )
                main_tasks_to_create.append(new_task)
                # Store mapping for later subtask creation
                task_id_mapping[original_task.task_id] = len(main_tasks_to_create) - 1
            
            # OPTIMIZED: Bulk create main tasks
            created_main_tasks = ProjectTask.objects.bulk_create(main_tasks_to_create)
            
            # IMPORTANT: After bulk_create, we need to fetch the tasks with their IDs
            # because bulk_create doesn't populate the ID field on the returned objects
            created_main_tasks_with_ids = list(
                ProjectTask.objects.filter(
                    project=new_project, 
                    parent_task__isnull=True
                ).order_by('task_id')
            )
            
            # Create mapping from original task ID to new task object (with ID)
            task_object_mapping = {}
            for i, original_task in enumerate(main_tasks):
                if i < len(created_main_tasks_with_ids):
                    task_object_mapping[original_task.task_id] = created_main_tasks_with_ids[i]
            
            # OPTIMIZED: Prepare bulk data for subtasks
            subtasks_to_create = []
            
            # Get all subtasks using prefetched data and group by parent
            for original_main_task in main_tasks:
                # Use prefetched subtasks
                subtasks = list(original_main_task.subtasks.all())
                
                if original_main_task.task_id in task_object_mapping:
                    new_main_task = task_object_mapping[original_main_task.task_id]
                    
                    for original_subtask in subtasks:
                        new_subtask_start_date = adjust_date(original_subtask.task_start_date, date_offset)
                        new_subtask_expected_completion = adjust_date(original_subtask.task_expected_completion_date, date_offset)
                        new_subtask_budgeted_cost = get_cost_for_budget(original_subtask, budget_copy_option)
                        
                        new_subtask = ProjectTask(
                            project=new_project,
                            task_name=original_subtask.task_name,
                            task_description=original_subtask.task_description,
                            task_start_date=new_subtask_start_date,
                            task_expected_completion_date=new_subtask_expected_completion,
                            task_budgeted_cost=new_subtask_budgeted_cost,
                            task_actual_cost=Decimal('0.00'),
                            task_priority=original_subtask.task_priority,
                            task_status='Pending',
                            task_actual_completion_date=None,
                            task_assigned_to=original_subtask.task_assigned_to,
                            parent_task=new_main_task,
                            task_progress_percentage=0,
                            task_name_greek=getattr(original_subtask, 'task_name_greek', None),
                            task_description_greek=getattr(original_subtask, 'task_description_greek', None),
                        )
                        subtasks_to_create.append(new_subtask)
            
            # OPTIMIZED: Bulk create subtasks
            if subtasks_to_create:
                ProjectTask.objects.bulk_create(subtasks_to_create)
            
            # OPTIMIZED: Copy project documents using prefetched data
            documents_to_create = []
            try:
                original_documents = list(original_project.project_documents.all())
                for original_doc in original_documents:
                    new_document = ProjectDocument(
                        project=new_project,
                        task=None,
                        document_name=f"Copy of {original_doc.document_name}" if original_doc.document_name else None,
                        document_description=original_doc.document_description,
                        document_file=original_doc.document_file,
                        document_uploaded_by=request.user.username,
                    )
                    documents_to_create.append(new_document)
                
                # Bulk create documents
                if documents_to_create:
                    ProjectDocument.objects.bulk_create(documents_to_create)
                    
            except Exception as doc_error:
                # Silent fail for document copying
                pass
        
        # Build success message
        budget_message = ""
        if budget_copy_option == 'actual':
            budget_message = " with actual costs copied as budgeted costs"
        else:
            budget_message = " with budgeted costs copied"
        
        translation_message = ""
        if clear_greek_translations:
            translation_message = " and Greek translations cleared for project name and description"
            
        success_message = f'Project "{new_project_name}" created successfully{budget_message}{translation_message}'
        if date_offset is not None:
            success_message += f' and all dates adjusted by {date_offset} days'
        
        return JsonResponse({
            'success': True,
            'message': success_message,
            'new_project_id': new_project.project_id,
            'date_offset': date_offset,
            'budget_copy_option': budget_copy_option,
            'greek_translations_cleared': clear_greek_translations
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred while duplicating the project: {str(e)}'
        })

@login_required
def project_task_list(request, project_id):
    """Display task list for a specific project and assignee - OPTIMIZED"""
    # OPTIMIZED: Single query with comprehensive prefetching
    project = get_object_or_404(
        Project.objects.select_related('prop').prefetch_related(
            Prefetch('projecttask_set', 
                queryset=ProjectTask.objects.filter(parent_task__isnull=True).prefetch_related(
                    'subtasks'
                ).order_by('task_start_date', 'task_id')
            )
        ), 
        project_id=project_id
    )
    
    # Get parameters
    assigned_to = request.GET.get('assigned_to', '')
    language = request.GET.get('language', 'english')
    
    # Ensure Greek translations if language is Greek
    if language == 'greek':
        ensure_project_translations(project)
    
    # OPTIMIZED: Use prefetched data
    main_tasks = list(project.projecttask_set.all())
    
    # OPTIMIZED: Filter in Python using prefetched data instead of additional queries
    if assigned_to:
        filtered_main_tasks = []
        for task in main_tasks:
            task_matches = task.task_assigned_to == assigned_to
            subtask_matches = any(subtask.task_assigned_to == assigned_to for subtask in task.subtasks.all())
            if task_matches or subtask_matches:
                filtered_main_tasks.append(task)
        main_tasks = filtered_main_tasks
    
    # Build task list with hierarchy using prefetched data
    task_list = []
    total_tasks = 0
    completed_tasks = 0
    pending_tasks = 0
    
    # Add project as root item
    project_start_date = project.get_calculated_start_date()
    project_end_date = project.get_calculated_expected_completion()
    project_is_overdue = (
        project_end_date and 
        project_end_date < timezone.now().date() and 
        project.get_calculated_status() != 'Completed'
    )
    
    project_item = {
        'name': project.project_name,
        'name_greek': get_translated_text(
            project.project_name, 
            getattr(project, 'project_name_greek', None), 
            language
        ) if language == 'greek' else project.project_name,
        'description': project.project_description,
        'description_greek': get_translated_text(
            project.project_description, 
            getattr(project, 'project_description_greek', None), 
            language
        ) if language == 'greek' else project.project_description,
        'type': 'project',
        'status': project.get_calculated_status(),
        'start_date': project_start_date,
        'end_date': project_end_date,
        'priority': None,
        'indent_level': 0,
        'is_overdue': project_is_overdue,
        'project_obj': project
    }
    task_list.append(project_item)
    
    # Process main tasks and subtasks using prefetched data
    for main_task in main_tasks:
        # For main tasks, use calculated dates
        task_start_date = main_task.get_calculated_start_date()
        task_end_date = main_task.get_calculated_expected_completion()
        task_is_overdue = (
            task_end_date and 
            task_end_date < timezone.now().date() and 
            main_task.get_calculated_status() != 'Completed'
        )
        
        main_task_item = {
            'name': main_task.task_name,
            'name_greek': get_translated_text(
                main_task.task_name, 
                getattr(main_task, 'task_name_greek', None), 
                language
            ) if language == 'greek' else main_task.task_name,
            'description': main_task.task_description,
            'description_greek': get_translated_text(
                main_task.task_description, 
                getattr(main_task, 'task_description_greek', None), 
                language
            ) if language == 'greek' else main_task.task_description,
            'type': 'task',
            'status': main_task.get_calculated_status(),
            'start_date': task_start_date,
            'end_date': task_end_date,
            'priority': main_task.task_priority,
            'indent_level': 1,
            'is_overdue': task_is_overdue,
            'task_obj': main_task
        }
        task_list.append(main_task_item)
        
        # Add subtasks using prefetched data
        subtasks = list(main_task.subtasks.all())
        if assigned_to:
            subtasks = [subtask for subtask in subtasks if subtask.task_assigned_to == assigned_to]
        
        # Sort subtasks by start date and task_id
        subtasks.sort(key=lambda x: (x.task_start_date or timezone.now().date(), x.task_id))
        
        for subtask in subtasks:
            is_overdue = (
                subtask.task_expected_completion_date and 
                subtask.task_expected_completion_date < timezone.now().date() and 
                subtask.task_status != 'Completed'
            )
            
            subtask_item = {
                'name': subtask.task_name,
                'name_greek': get_translated_text(
                    subtask.task_name, 
                    getattr(subtask, 'task_name_greek', None), 
                    language
                ) if language == 'greek' else subtask.task_name,
                'description': subtask.task_description,
                'description_greek': get_translated_text(
                    subtask.task_description, 
                    getattr(subtask, 'task_description_greek', None), 
                    language
                ) if language == 'greek' else subtask.task_description,
                'type': 'subtask',
                'status': subtask.task_status,
                'start_date': subtask.task_start_date,
                'end_date': subtask.task_expected_completion_date,
                'priority': subtask.task_priority,
                'indent_level': 2,
                'is_overdue': is_overdue,
                'task_obj': subtask
            }
            task_list.append(subtask_item)
            
            # ONLY count subtasks in totals
            total_tasks += 1
            
            if subtask.task_status == 'Completed':
                completed_tasks += 1
            else:
                pending_tasks += 1
    
    # Calculate completion percentage
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    context = {
        'project': project,
        'task_list': task_list,
        'assigned_to': assigned_to,
        'language': language,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_percentage': completion_percentage,
        'current_date': timezone.now(),
    }
    
    return render(request, 'projects/project_task_list.html', context)

@login_required
def ajax_delete_task(request):
    """
    AJAX view to delete a task or subtask
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'})
    
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to delete tasks'
        })
    
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        task_type = data.get('task_type')  # 'task' or 'subtask'
        
        if not task_id:
            return JsonResponse({
                'success': False,
                'message': 'Task ID is required'
            })
        
        try:
            task_id = int(task_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': f'Invalid task ID: {task_id}'
            })
        
        # Get the task to delete
        try:
            task_to_delete = ProjectTask.objects.get(task_id=task_id)
        except ProjectTask.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Task with ID {task_id} was not found'
            })
        
        # Use transaction to ensure all-or-nothing deletion
        with transaction.atomic():
            if task_type == 'task':
                # Delete main task and all its subtasks
                subtasks = ProjectTask.objects.filter(parent_task=task_to_delete)
                subtask_count = subtasks.count()
                
                # Delete subtasks first
                subtasks.delete()
                
                # Delete the main task
                task_name = task_to_delete.task_name
                task_to_delete.delete()
                
                message = f'Task "{task_name}" and {subtask_count} subtask(s) deleted successfully'
                
            elif task_type == 'subtask':
                # Delete only the subtask
                task_name = task_to_delete.task_name
                task_to_delete.delete()
                
                message = f'Subtask "{task_name}" deleted successfully'
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid task type. Must be "task" or "subtask"'
                })
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred while deleting: {str(e)}'
        })

@login_required
def get_project_assignees(request, project_id):
    """AJAX endpoint to get all assignees for a project - OPTIMIZED"""
    # OPTIMIZED: Single query with prefetching
    project = get_object_or_404(
        Project.objects.prefetch_related('projecttask_set'), 
        project_id=project_id
    )
    
    # OPTIMIZED: Use prefetched data to get assignees
    assignees = set()
    
    for task in project.projecttask_set.all():
        if task.task_assigned_to and task.task_assigned_to.strip():
            assignees.add(task.task_assigned_to.strip())
    
    # Convert to sorted list
    assignees_list = sorted(list(assignees))
    
    return JsonResponse({
        'success': True,
        'assignees': assignees_list,
        'project_name': project.project_name
    })


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)
    return response

### HOME ###
def home(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.filter(tenant_current="Yes")
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "home.html", {"props":results, "tenant":tresults, "supplier":sresults})

### ADMIN ###
@login_required
def admin_apms(request):
    results = props.objects.all().order_by('prop_country', 'prop_name')
    tresults = tenant.objects.select_related('prop').all().order_by('tenant_name')
    return render(request, "admin_apms.html", {
        "props": results, 
        "tenant": tresults
    })

@login_required
def lease_agreement_report(request, tenant_id):
    try:
        # Get tenant and property info
        tenant_obj = get_object_or_404(tenant, pk=tenant_id)
        if not hasattr(tenant_obj, 'prop') or not tenant_obj.prop:
            raise Http404("Tenant has no property assigned")
        
        property_name = tenant_obj.prop.prop_name
        filename = f"{property_name} - Lease Agreement.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, 'lease_agreements', filename)
        
        context = {
            'tenant': tenant_obj,
            'property': tenant_obj.prop,
            'filename': filename,
            'file_exists': os.path.exists(file_path),
            'file_url': os.path.join(settings.MEDIA_URL, 'lease_agreements', filename)
        }
        return render(request, 'lease_agreement_report.html', context)
        
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})

@login_required
def serve_lease(request, filename):
    try:
        # Security validation
        if not filename.endswith(' - Lease Agreement.pdf'):
            raise Http404("Invalid filename format")
            
        file_path = os.path.join(settings.MEDIA_ROOT, 'lease_agreements', filename)
        
        if not os.path.exists(file_path):
            raise Http404("File not found")
            
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
        
    except Exception as e:
        return Http404(str(e))

@login_required
def upload_lease_agreement(request):
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        uploaded_file = request.FILES.get('lease_agreement')
        
        if not uploaded_file:
            messages.error(request, "No file was uploaded.")
            return redirect('admin_apms')
        
        try:
            # Validate file
            if not uploaded_file.name.lower().endswith('.pdf'):
                raise ValueError("Only PDF files are allowed")
                
            tenant_obj = tenant.objects.get(pk=tenant_id)
            if not hasattr(tenant_obj, 'prop') or not tenant_obj.prop:
                raise ValueError("No property assigned to tenant")
                
            property_name = tenant_obj.prop.prop_name
            lease_dir = os.path.join(settings.STATIC_ROOT, 'lease_agreements')
            os.makedirs(lease_dir, exist_ok=True)
            
            filename = f"{property_name} - Lease Agreement.pdf"
            file_path = os.path.join(lease_dir, filename)
            
            # Save file
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            messages.success(request, f"Lease agreement uploaded successfully!")
            return redirect('admin_apms')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('admin_apms')
    return redirect('admin_apms')

@login_required
def serve_lease(request, filename):
    """Secure file serving for exact filename format"""
    try:
        # Verify filename format
        if not filename.endswith(' - Lease Agreement.pdf'):
            raise Http404("Invalid filename format")
            
        file_path = os.path.join(settings.STATIC_ROOT, 'lease_agreements', filename)
        
        if not os.path.exists(file_path):
            raise Http404("Lease agreement not found")
            
        # Serve with cache-control headers
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Cache-Control'] = 'no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        return response
        
    except Exception as e:
        messages.error(request, f"Error serving file: {str(e)}")
        return redirect('admin_apms')

@login_required
def upload_title_deed(request):
    if request.method == 'POST':
        # Get the selected property name
        property_name = request.POST.get('property')
        
        # Get the uploaded file
        uploaded_file = request.FILES.get('title_deed')
        
        if not uploaded_file:
            messages.error(request, "No file was uploaded.")
            return redirect('admin_apms')
        
        # Validate file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            messages.error(request, "Only PDF files are allowed.")
            return redirect('admin_apms')
        
        # Create the title_deeds directory if it doesn't exist
        title_deeds_dir = os.path.join(settings.STATIC_ROOT, 'title_deeds')
        os.makedirs(title_deeds_dir, exist_ok=True)
        
        # Create the filename
        filename = f'{property_name} - Title Deed.pdf'
        file_path = os.path.join(title_deeds_dir, filename)
        
        # Save the file
        try:
            # Delete existing file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
                
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            messages.success(request, f"Title deed for {property_name} uploaded successfully!")
        except Exception as e:
            messages.error(request, f"Error saving file: {str(e)}")
        
        return redirect('admin_apms')
    
    return redirect('admin_apms')

@login_required
def admin_clear(request):
	import os
	import glob
	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/*.pdf"
	files = glob.glob(file_path)
	for f in files:
		os.remove(f)
	return redirect("admin_apms")

@login_required
def admin_unpaid(request):
	import open_invoices
	rep_output = "Email"
	check = "Yes"
	email = "demetrimanias@gmail.com"
	fname = "Demetri"
	open_invoices.open_invoices(rep_output, check, email, fname)
#	email = "stella.simitopoulos@alivente.com"
#	fname = "Stella"
#	open_invoices.open_invoices(rep_output, check, email, fname)
	return redirect("admin_apms")

@login_required
def admin_renewals(request):
	import lease_renewal
	rep_output = "Email"
	check = "Yes"
	email = "demetrimanias@gmail.com"
	fname = "Demetri"
	lease_renewal.lease_renewal(rep_output,check, email, fname)
#	email = "stella.simitopoulos@alivente.com"
#	fname = "Stella"
#	lease_renewal.lease_renewal(rep_output,check, email, fname)
	return redirect("admin_apms")

@login_required
def admin_invoices(request):
	import open_invoices
	today = date.today()
	months = ('Month','January','February','March','April','May','June','July','August','September','October','November','December')
	open_invoices.create_invoices(months[today.month],today.year,request)
	return redirect("admin_apms")

### DASHBOARD ###
@login_required
def property_management_dashboard(request):
    """
    Main property dashboard view with spoke-and-wheel interface
    """
    try:
        # Get all properties for the dropdown
        properties = props.objects.filter(prop_status='Active').order_by('prop_name')
        
        # Check if a specific property was selected
        selected_property_id = request.GET.get('property')
        selected_property = None
        
        if selected_property_id:
            try:
                selected_property = props.objects.get(prop_id=selected_property_id)
            except props.DoesNotExist:
                messages.error(request, f"Property with ID {selected_property_id} not found.")
        
        context = {
            'properties': properties,
            'selected_property': selected_property,
        }
        
        return render(request, 'property_management_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('properties')

@login_required
def property_detail(request, property_id, box_type):
    property_obj = get_object_or_404(props, prop_id=property_id)
    
    # Get the active tenant for this property (there should only be one)
    active_tenant = tenant.objects.filter(
        prop=property_obj, 
        tenant_current='Yes'
    ).first()
    
    # Get open invoices data for this property
    open_invoices_data = None
    total_invoices_amount = 0
    
    # Lease renewal data
    lease_renewal_data = None
    
    # Issues data for this specific property
    property_issues = None
    resolved_count = 0
    unresolved_count = 0
    total_issues_count = 0
    
    # Valuation data for this specific property
    property_valuation = None
    
    # Revenue data for this specific property
    property_revenues = None
    total_revenue_amount = 0
    
    # Budgeted expenses data for this specific property
    property_budgeted_expenses = None
    total_budgeted_expense_amount = 0
    
    # Actual expenses data for this specific property
    property_actual_expenses = None
    actual_expense_years = []
    selected_actual_year = None
    
    if active_tenant:
        # Get all unpaid invoices for this tenant
        unpaid_invoices = invoices.objects.filter(
            tenant=active_tenant
        ).exclude(
            invoice_paid='Yes'  # Exclude paid invoices
        ).order_by('invoice_date')
        
        # Calculate days overdue and prepare data
        open_invoices_data = []
        today = timezone.now().date()
        
        for invoice in unpaid_invoices:
            # Calculate due date (invoice_date + payment_terms)
            payment_terms = active_tenant.tenant_payment_terms or 0
            due_date = invoice.invoice_date + timedelta(days=payment_terms)
            
            # Calculate days overdue
            days_overdue = (today - due_date).days if today > due_date else 0
            
            # Use the actual invoice amount if available, otherwise fall back to tenant rent
            invoice_amount = getattr(invoice, 'invoice_amount', None) or active_tenant.tenant_rent
            
            open_invoices_data.append({
                'invoice_date': invoice.invoice_date,
                'due_date': due_date,
                'days_overdue': days_overdue,
                'overdue': days_overdue > 0,
                'amount': invoice_amount
            })
            
            # Add to total amount
            total_invoices_amount += invoice_amount
        
        # Lease renewal logic for this specific property
        if box_type == 'lease-renewals':
            lease_renewal_data = {
                'tenant': active_tenant,
                'property': property_obj,
                'needs_renewal': False,
                'renewal_date': None,
                'status': 'current',
                'message': None
            }
            
            if active_tenant.tenant_lease_end_date:
                # Calculate renewal contact date
                renewal_period = active_tenant.tenant_renewal_period or 30
                renewal_contact_date = active_tenant.tenant_lease_end_date - timedelta(days=renewal_period)
                
                # Check if renewal is needed
                if today >= renewal_contact_date:
                    lease_renewal_data['needs_renewal'] = True
                    lease_renewal_data['renewal_date'] = renewal_contact_date
                    
                    # Check renewal status
                    if active_tenant.tenant_renewal_status == 'declined':
                        lease_renewal_data['status'] = 'declined'
                        lease_renewal_data['message'] = f"TENANT DECLINED RENEWAL - LEASE EXPIRES {active_tenant.tenant_lease_end_date}"
                    elif active_tenant.tenant_renewal_status == 'new_lease_signed':
                        lease_renewal_data['status'] = 'renewed'
                        lease_renewal_data['message'] = "NEW LEASE SIGNED"
                    else:
                        lease_renewal_data['status'] = 'pending'
                        lease_renewal_data['message'] = f"RENEWAL CONTACT REQUIRED BY {renewal_contact_date}"
    
    elif box_type == 'lease-renewals':
        # No active tenant - property is vacant
        lease_renewal_data = {
            'tenant': None,
            'property': property_obj,
            'status': 'vacant',
            'message': "NO CURRENT TENANT - NEED NEW TENANT"
        }
    
    # Issues logic - process for any box_type but only use data when box_type is 'issues'
    if box_type == 'issues':
        # Get all issues for this property, ordered by date (most recent first)
        property_issues = issues.objects.filter(
            prop=property_obj
        ).order_by('-issues_date_logged')
        
        # Calculate issue counts
        total_issues_count = property_issues.count()
        resolved_count = property_issues.filter(issues_status='Resolved').count()
        
        # Updated logic: Include both "Unresolved" AND "Issue" status as unresolved
        unresolved_count = property_issues.filter(
            issues_status__in=['Unresolved', 'Issue']
        ).count()
    
    # Valuation logic - process when box_type is 'valuation'
    if box_type == 'valuation':
        # Get valuation data for this property
        try:
            property_valuation = prop_values.objects.get(prop=property_obj)
            
            # Calculate value change in the view
            if property_valuation.prop_values_current_value and property_valuation.prop_values_purchase_price:
                difference = property_valuation.prop_values_current_value - property_valuation.prop_values_purchase_price
                if property_valuation.prop_values_purchase_price > 0:
                    percentage = (difference / property_valuation.prop_values_purchase_price) * 100
                else:
                    percentage = 0
                
                # Add calculated values to the valuation object
                property_valuation.value_difference = difference
                property_valuation.value_percentage = percentage
            else:
                property_valuation.value_difference = 0
                property_valuation.value_percentage = 0
                
        except prop_values.DoesNotExist:
            property_valuation = None
    
    # Revenue logic - process when box_type is 'revenues'
    if box_type == 'revenues':
        # Get all revenue data for this property
        property_revenues = property_obj.revenue_set.all().order_by('revenue_line_types__revenue_line_types_name', 'revenue_types__revenue_types_name')
        
        # Calculate total revenue amount
        total_revenue_amount = sum(rev.revenue_amount for rev in property_revenues)
    
    # Budgeted Expenses logic - process when box_type is 'budgeted-expenses'
    if box_type == 'budgeted-expenses':
        # Get all budgeted expense data for this property, sorted by expense line type
        property_budgeted_expenses = property_obj.expense_set.all().order_by('expense_line_types__expense_line_types_name', 'expense_types__expense_types_name')
        
        # Calculate total budgeted expense amount
        total_budgeted_expense_amount = sum(exp.expense_amount for exp in property_budgeted_expenses)
    
    # Actual Expenses logic - process when box_type is 'actual-expenses'
    if box_type == 'actual-expenses':
        from django.db.models import Q
        
        # Get selected year from request or default to current year
        selected_actual_year = request.GET.get('year')
        current_year = timezone.now().year
        
        # Get all years that have actual expenses for this property (approved and paid only)
        actual_expense_years = list(
            property_obj.act_expense_set.filter(
                act_expense_approved='Yes',
                act_expense_paid='Yes'
            ).dates('act_expense_date', 'year', order='DESC').distinct()
        )
        actual_expense_years = [date.year for date in actual_expense_years]
        
        # Default to the latest year if no year selected
        if not selected_actual_year and actual_expense_years:
            selected_actual_year = actual_expense_years[0]
        elif not selected_actual_year:
            selected_actual_year = current_year
        else:
            selected_actual_year = int(selected_actual_year)
        
        # Get actual expenses for the selected year (only approved and paid)
        property_actual_expenses = property_obj.act_expense_set.filter(
            act_expense_date__year=selected_actual_year,
            act_expense_approved='Yes',
            act_expense_paid='Yes'
        ).order_by('-act_expense_date')
        
        # Calculate total actual expenses amount
        total_actual_expense_amount = sum(exp.act_expense_amount for exp in property_actual_expenses)
    
    # Map box types to display names
    box_type_display_map = {
        'title-deed': 'Title Deed',
        'property-report': 'Property Report',
        'tenant': 'Tenant Information',
        'actual-expenses': 'Actual Expenses',
        'issues': 'Property Issues',
        'valuation': 'Property Valuation',
        'profit-loss': 'Profit & Loss',
        'revenues': 'Revenues',
        'expenses': 'Budgeted Expenses',
        'open-invoices': 'Open Invoices',
        'lease-renewals': 'Lease Renewals',
        'lease': 'Lease Details',
    }
    
    context = {
        'property': property_obj,
        'active_tenant': active_tenant,
        'open_invoices_data': open_invoices_data,
        'total_invoices_amount': total_invoices_amount,
        'lease_renewal_data': lease_renewal_data,
        'property_issues': property_issues,
        'resolved_count': resolved_count,
        'unresolved_count': unresolved_count,
        'total_issues_count': total_issues_count,
        'property_valuation': property_valuation,
        'property_revenues': property_revenues,
        'total_revenue_amount': total_revenue_amount,
        'property_budgeted_expenses': property_budgeted_expenses,
        'total_budgeted_expense_amount': total_budgeted_expense_amount,
        'property_actual_expenses': property_actual_expenses,
        'actual_expense_years': actual_expense_years,
        'selected_actual_year': selected_actual_year,
        'total_actual_expense_amount': locals().get('total_actual_expense_amount', 0),
        'box_type': box_type,
        'box_type_display': box_type_display_map.get(box_type, box_type.title()),
        'today': timezone.now().date(),
    }
    
    return render(request, 'property_detail.html', context)

@login_required
def dashboard_pl(request, property_id):
    """
    Dedicated view for Profit & Loss dashboard
    """
    property_obj = get_object_or_404(props, prop_id=property_id)

    from django.db.models import Sum, Q
    from collections import defaultdict
    
    # Get selected year from request
    selected_year = request.GET.get('year', 'budget')
    
    # Get available years for this property (from actual expenses only since revenues/expenses are budget data)
    actual_expense_years_obj = set(property_obj.act_expense_set.filter(
        act_expense_approved='Yes',
        act_expense_paid='Yes'
    ).dates('act_expense_date', 'year', order='DESC').distinct())
    
    # Convert to integers and sort
    available_years = sorted([date.year for date in actual_expense_years_obj], reverse=True)

    # Set display name for selected year
    if selected_year == 'budget':
        selected_year_display = 'Budget'
    else:
        try:
            selected_year = int(selected_year)
            selected_year_display = str(selected_year)
        except (ValueError, TypeError):
            selected_year = 'budget'
            selected_year_display = 'Budget'
    
    # Get revenue and expense line types - using correct model names
    revenue_line_types_queryset = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    expense_line_types_queryset = expense_line_types.objects.all().order_by('expense_line_types_name')
    
    # Initialize totals dictionaries
    property_revenue_totals = {}
    property_expense_totals = {}
    
    # Initialize monthly totals
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    property_revenue_total = {month: 0 for month in months}
    property_revenue_total['year'] = 0
    property_expense_total = {month: 0 for month in months}
    property_expense_total['year'] = 0
    property_actual_expense_total = {month: 0 for month in months}
    property_actual_expense_total['year'] = 0
    
    # Process revenues for this property (using monthly fields)
    for line_type in revenue_line_types_queryset:
        line_totals = {month: 0 for month in months}
        line_totals['total'] = 0
        
        # Get revenues for this line type and property
        revenues = property_obj.revenue_set.filter(
            revenue_line_types=line_type
        )
        
        # Sum revenues by month using the monthly fields
        for rev in revenues:
            line_totals['jan'] += rev.revenue_jan or 0
            line_totals['feb'] += rev.revenue_feb or 0
            line_totals['mar'] += rev.revenue_mar or 0
            line_totals['apr'] += rev.revenue_apr or 0
            line_totals['may'] += rev.revenue_may or 0
            line_totals['jun'] += rev.revenue_jun or 0
            line_totals['jul'] += rev.revenue_jul or 0
            line_totals['aug'] += rev.revenue_aug or 0
            line_totals['sep'] += rev.revenue_sep or 0
            line_totals['oct'] += rev.revenue_oct or 0
            line_totals['nov'] += rev.revenue_nov or 0
            line_totals['dec'] += rev.revenue_dec or 0
        
        # Calculate total for this line type
        line_totals['total'] = sum(line_totals[month] for month in months)
        
        property_revenue_totals[line_type.revenue_line_types_id] = line_totals
        
        # Add to property totals
        for month in months:
            property_revenue_total[month] += line_totals[month]
        property_revenue_total['year'] += line_totals['total']
    
    # Process budgeted expenses for this property (using monthly fields)
    for line_type in expense_line_types_queryset:
        line_totals = {month: 0 for month in months}
        line_totals['total'] = 0
        
        # Get expenses for this line type and property
        expenses = property_obj.expense_set.filter(
            expense_line_types=line_type
        )
        
        # Sum expenses by month using the monthly fields
        for exp in expenses:
            # Your expense model has monthly fields
            line_totals['jan'] += exp.expense_jan or 0
            line_totals['feb'] += exp.expense_feb or 0
            line_totals['mar'] += exp.expense_mar or 0
            line_totals['apr'] += exp.expense_apr or 0
            line_totals['may'] += exp.expense_may or 0
            line_totals['jun'] += exp.expense_jun or 0
            line_totals['jul'] += exp.expense_jul or 0
            line_totals['aug'] += exp.expense_aug or 0
            line_totals['sep'] += exp.expense_sep or 0
            line_totals['oct'] += exp.expense_oct or 0
            line_totals['nov'] += exp.expense_nov or 0
            line_totals['dec'] += exp.expense_dec or 0
        
        # Calculate total for this line type
        line_totals['total'] = sum(line_totals[month] for month in months)
        
        property_expense_totals[line_type.expense_line_types_id] = line_totals
        
        # Add to property totals
        for month in months:
            property_expense_total[month] += line_totals[month]
        property_expense_total['year'] += line_totals['total']
    
    # Process actual expenses for this property (only if not budget view)
    if selected_year != 'budget':
        actual_expenses = property_obj.act_expense_set.filter(
            act_expense_date__year=selected_year,
            act_expense_approved='Yes',
            act_expense_paid='Yes'
        ).values('act_expense_date', 'act_expense_amount')
        
        # Sum actual expenses by month
        for exp in actual_expenses:
            month_name = months[exp['act_expense_date'].month - 1]
            property_actual_expense_total[month_name] += exp['act_expense_amount']
            property_actual_expense_total['year'] += exp['act_expense_amount']
    
    context = {
        'property': property_obj,
        'available_years': available_years,
        'selected_year': selected_year,
        'selected_year_display': selected_year_display,
        'revenue_line_types': revenue_line_types_queryset,  # Updated variable name
        'expense_line_types': expense_line_types_queryset,  # Updated variable name
        'property_revenue_totals': property_revenue_totals,
        'property_expense_totals': property_expense_totals,
        'property_revenue_total': property_revenue_total,
        'property_expense_total': property_expense_total,
        'property_actual_expense_total': property_actual_expense_total,
        'today': timezone.now().date(),
    }
    
    return render(request, 'dashboard_pl.html', context)

### FINANCE ###
@login_required
def finance(request):
#	return redirect("finance")
	return render (request, "finance.html", {})

@login_required
def finance_revenue(request):
	prop_output = request.POST.get('propname')
	if prop_output is None or prop_output == "All":
			props_data = props.objects.prefetch_related(
				Prefetch(
					'revenue_set',
					queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types')
				)
			).all().order_by('prop_country', 'prop_name')
	else:
		if prop_output is not None:
				props_data = props.objects.prefetch_related(
					Prefetch(
						'revenue_set',
						queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types')
					)
				).all().order_by('prop_country', 'prop_name').filter(prop_name=prop_output)
	return render(request, "finance_revenue.html", {
		"props_data": props_data,
	})

@login_required
def finance_revenue_add(request):
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    revenue_types_list = revenue_types.objects.all()  # Fetch all revenue types
    revenue_line_types_list = revenue_line_types.objects.all()  # Fetch all revenue line types

    return render(request, "finance_revenue_add.html", {
        "props_data": props_data,
        "revenue_types": revenue_types_list,  # Pass to template
        "revenue_line_types": revenue_line_types_list,  # Pass to template
    })

@login_required
def finance_revenue_commit(request):
    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        rlt_id = request.POST.get('revenue_line_types')  # revenue_line_types_id
        rt_id = request.POST.get('revenue_types')    # revenue_types_id
        revenue_amount = request.POST.get('revenue_amount')

        # Fetch the revenue_type to check monthly flags
        try:
            revenue_type = revenue_types.objects.get(revenue_types_id=rt_id)
        except revenue_types.DoesNotExist:
            messages.error(request, "Invalid Revenue Type")
            return redirect('finance_revenue_add')
        # Initialize monthly revenue data
        monthly_data = {
            'prop_id': prop_id,
            'revenue_line_types_id': rlt_id,
            'revenue_types_id': rt_id,
            'revenue_amount': revenue_amount,
        }
        # Check each month and set revenue_jan, revenue_feb, etc. if "YES"
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for month in months:
            if getattr(revenue_type, f'revenue_types_{month}') == "Yes":
                monthly_data[f'revenue_{month}'] = revenue_amount
                print(monthly_data[f'revenue_{month}'])
        # Create or update the revenue record
        revenue.objects.update_or_create(
            prop_id=prop_id,
            revenue_line_types_id=rlt_id,
            revenue_types_id=rt_id,
            defaults=monthly_data
        )
        messages.success(request, "Revenue Updated Successfully")
        return redirect('finance_revenue')
    # If not a POST request, redirect back
    return redirect('finance_revenue_add')

@login_required
def finance_revenue_edit(request, revenue_id):
    rev = get_object_or_404(revenue, pk=revenue_id)
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    revenue_types_list = revenue_types.objects.all()
    revenue_line_types_list = revenue_line_types.objects.all()
    form = RevenueForm(instance=rev)  # Use your actual form class
    
    return render(request, "finance_revenue_edit.html", {
        "rev": rev,  # Changed from rresults to rev for clarity
        "props_data": props_data,
        "revenue_types": revenue_types_list,
        "revenue_line_types": revenue_line_types_list,
        "form": form,  # Pass the form to template
    })

@login_required
def finance_revenue_edit_commit(request, revenue_id):
    rev = get_object_or_404(revenue, pk=revenue_id)
    
    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        rlt_id = request.POST.get('revenue_line_types')
        rt_id = request.POST.get('revenue_types')
        revenue_amount = request.POST.get('revenue_amount')

        # Fetch the revenue_type to check monthly flags
        try:
            revenue_type = revenue_types.objects.get(revenue_types_id=rt_id)
        except revenue_types.DoesNotExist:
            messages.error(request, "Invalid Revenue Type")
            return redirect('finance_revenue_edit', revenue_id=revenue_id)

        # Initialize monthly revenue data
        monthly_data = {
            'prop_id': prop_id,
            'revenue_line_types_id': rlt_id,
            'revenue_types_id': rt_id,
            'revenue_amount': revenue_amount,
        }

        # Check each month and set revenue_jan, revenue_feb, etc. if "YES"
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for month in months:
            if getattr(revenue_type, f'revenue_types_{month}') == "Yes":
                monthly_data[f'revenue_{month}'] = revenue_amount
            else:
                monthly_data[f'revenue_{month}'] = None  # Clear if not applicable

        # Update the revenue record
        for key, value in monthly_data.items():
            setattr(rev, key, value)
        rev.save()

        messages.success(request, "Revenue Updated Successfully")
        return redirect('finance_revenue')

    # If GET request, show the form
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    revenue_types_list = revenue_types.objects.all()
    revenue_line_types_list = revenue_line_types.objects.all()
    form = RevenueForm(instance=rev)
    
    return render(request, "finance_revenue_edit.html", {
        "rev": rev,
        "props_data": props_data,
        "revenue_types": revenue_types_list,
        "revenue_line_types": revenue_line_types_list,
        "form": form,
    })

@login_required
def finance_revenue_types(request):
    rev_types = revenue_types.objects.all()
    return render(request, "finance_revenue_types.html", {
        "rtresults": rev_types,
    })

@login_required
def finance_revenue_types_add(request):
    rev_types = revenue_types.objects.all().order_by('revenue_types_name')
    return render(request, "finance_revenue_types_add.html", {"rtresults":rev_types})

@login_required
def finance_revenue_types_commit(request):
    if request.method == "POST":
        form = RevenueTypesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Types Added Successfully")
    rev_types = revenue_types.objects.all()
    return render(request, "finance_revenue_types.html", {"rtresults":rev_types})

@login_required
def finance_revenue_types_edit(request, revenue_types_id):
    rev_types = revenue_types.objects.filter(pk=revenue_types_id)
    return render(request, "finance_revenue_types_edit.html", {"rtresults":rev_types})

@login_required
def finance_revenue_types_edit_commit(request, revenue_types_id):
    rev = get_object_or_404(revenue_types, pk=revenue_types_id)
    all_types = revenue_types.objects.all().order_by('revenue_types_name')
    if request.method == "POST":
        name = request.POST.get('revenue_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if revenue_types.objects.filter(
            revenue_types_name__iexact=name
        ).exclude(
            pk=revenue_types_id
        ).exists():
            messages.error(request, "No duplicate Revenue Types Allowed")
            return render(request, "finance_revenue_types.html", {
                "rtresults": all_types,
                "rev": rev,
                "name_error": True
            })
        form = RevenueTypesForm(request.POST, instance=rev)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Type Edited Successfully")
            return redirect('finance_revenue_types')
    # If GET request or form invalid
    return render(request, "finance_revenue_types.html", {
        "rtresults": all_types,
        "rev": rev
    })

@login_required
def finance_revenue_line_types(request):
    rev_line_types = revenue_line_types.objects.all()
    return render(request, "finance_revenue_line_types.html", {
        "rltresults": rev_line_types,
    })

@login_required
def finance_revenue_line_types_add(request):
    rev_line_types = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    return render(request, "finance_revenue_line_types_add.html", {"rltresults":rev_line_types})

@login_required
def finance_revenue_line_types_commit(request):
    if request.method == "POST":
        form = RevenueLineForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Line Types Added Successfully")
    rev_line_types = revenue_line_types.objects.all()
    return render(request, "finance_revenue_line_types.html", {"rltresults":rev_line_types})

@login_required
def finance_revenue_line_types_edit(request, revenue_line_types_id):
    rev_line_types = revenue_line_types.objects.filter(pk=revenue_line_types_id)
    return render(request, "finance_revenue_line_types_edit.html", {"rltresults":rev_line_types})

@login_required
def finance_revenue_line_types_edit_commit(request, revenue_line_types_id):
    rev = get_object_or_404(revenue_line_types, pk=revenue_line_types_id)
    all_types = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    if request.method == "POST":
        name = request.POST.get('revenue_line_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if revenue_line_types.objects.filter(
            revenue_line_types_name__iexact=name
        ).exclude(
            pk=revenue_line_types_id
        ).exists():
            messages.error(request, "No duplicate Revenue Line Types Allowed")
            return render(request, "finance_revenue_line_types.html", {
                "rltresults": all_types,
                "rev": rev,
                "name_error": True
            })
        form = RevenueLineForm(request.POST, instance=rev)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Line Type Edited Successfully")
            return redirect('finance_revenue_line_types')
    
    # If GET request or form invalid
    return render(request, "finance_revenue_line_types.html", {
        "rltresults": all_types,
        "rev": rev
    })

@login_required
def finance_expense(request):
    prop_output = request.POST.get('propname')
    if prop_output is None or prop_output == "All":
            props_data = props.objects.prefetch_related(
                Prefetch(
                    'expense_set',
                    queryset=expense.objects.select_related('expense_line_types', 'expense_types')
                )
            ).all().order_by('prop_country', 'prop_name')
    else:
        if prop_output is not None:
                props_data = props.objects.prefetch_related(
                    Prefetch(
                        'expense_set',
                        queryset=expense.objects.select_related('expense_line_types', 'expense_types')
                    )
                ).all().order_by('prop_country', 'prop_name').filter(prop_name=prop_output)
    return render(request, "finance_expense.html", {
        "props_data": props_data,
    })

@login_required
def finance_expense_add(request):
    # Get properties with their values (using select_related if it's a ForeignKey)
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    # Annotate each property with its current value (0 if none exists)
    props_data = props_data.annotate(
        current_value=Coalesce(
            Subquery(
                prop_values.objects.filter(prop_id=OuterRef('prop_id'))
                .values('prop_values_current_value')[:1]
            ),
            0
        )
    )
    expense_types_list = expense_types.objects.all()
    expense_line_types_list = expense_line_types.objects.all().order_by('expense_line_types_name')
    return render(request, "finance_expense_add.html", {
        "props_data": props_data,
        "expense_types": expense_types_list,
        "expense_line_types": expense_line_types_list,
    })

@login_required
def finance_expense_commit(request):
    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        elt_id = request.POST.get('expense_line_types')
        et_id = request.POST.get('expense_types')  # Fix: Changed from 'expense_types' to match your form
        expense_amount = request.POST.get('expense_amount')
        prorata_data = request.POST.get('prorata_calculation_data')

        # Define months list outside the prorata block
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        try:
            expense_type = expense_types.objects.get(expense_types_id=et_id)
        except expense_types.DoesNotExist:
            messages.error(request, "Invalid Expense Type")
            return redirect('finance_expense_add')

        # Check if this is a pro-rata expense with multiple properties
        if prorata_data:
            try:
                prorata_data = json.loads(prorata_data)
                selected_properties = prorata_data.get('selected_properties', [])
                
                # Create an expense for each selected property
                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    
                    for month in months:
                        if getattr(expense_type, f'expense_types_{month}') == "Yes":
                            monthly_data[f'expense_{month}'] = property_data['calculated_amount']
                    
                    expense.objects.update_or_create(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                        defaults=monthly_data
                    )
                
                messages.success(request, f"{len(selected_properties)} pro-rata expenses created successfully")
                return redirect('finance_expense')
                
            except json.JSONDecodeError:
                messages.error(request, "Invalid pro-rata data")
                return redirect('finance_expense_add')

        # Handle non-pro-rata or single property expense
        monthly_data = {
            'prop_id': prop_id,
            'expense_line_types_id': elt_id,
            'expense_types_id': et_id,
            'expense_amount': expense_amount,
        }
        
        for month in months:
            if getattr(expense_type, f'expense_types_{month}') == "Yes":
                monthly_data[f'expense_{month}'] = expense_amount
        
        expense.objects.update_or_create(
            prop_id=prop_id,
            expense_line_types_id=elt_id,
            expense_types_id=et_id,
            defaults=monthly_data
        )
        
        messages.success(request, "Expense Updated Successfully")
        return redirect('finance_expense')
    
    return redirect('finance_expense_add')

@login_required
def finance_expense_edit(request, expense_id):
    # Get the existing expense
    try:
        existing_expense = expense.objects.get(expense_id=expense_id)
    except expense.DoesNotExist:
        messages.error(request, "Expense not found")
        return redirect('finance_expense')

    # Get properties with their values (using select_related if it's a ForeignKey)
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    # Annotate each property with its current value (0 if none exists)
    props_data = props_data.annotate(
        current_value=Coalesce(
            Subquery(
                prop_values.objects.filter(prop_id=OuterRef('prop_id'))
                .values('prop_values_current_value')[:1]
            ),
            0
        )
    )
    
    expense_types_list = expense_types.objects.all()
    expense_line_types_list = expense_line_types.objects.all().order_by('expense_line_types_name')
    
    return render(request, "finance_expense_edit.html", {
        "props_data": props_data,
        "expense_types": expense_types_list,
        "expense_line_types": expense_line_types_list,
        "existing_expense": existing_expense,
    })

@login_required
def finance_expense_edit_commit(request, expense_id):
    # Get the existing expense first
    try:
        existing_expense = expense.objects.get(expense_id=expense_id)
    except expense.DoesNotExist:
        messages.error(request, "Expense not found")
        return redirect('finance_expense')

    if request.method == "POST":
        # Extract form data
        prop_id = request.POST.get('prop')
        elt_id = request.POST.get('expense_line_types')
        et_id = request.POST.get('expense_types')
        expense_amount = request.POST.get('expense_amount')
        prorata_data = request.POST.get('prorata_calculation_data')

        # Define months list outside the prorata block
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        try:
            expense_type = expense_types.objects.get(expense_types_id=et_id)
        except expense_types.DoesNotExist:
            messages.error(request, "Invalid Expense Type")
            return redirect('finance_expense_edit', expense_id=expense_id)

        # Check if this is a pro-rata expense with multiple properties
        if prorata_data and prorata_data != 'undefined':
            try:
                prorata_data = json.loads(prorata_data)
                selected_properties = prorata_data.get('selected_properties', [])
                
                if not selected_properties:
                    messages.error(request, "No properties selected for pro-rata distribution")
                    return redirect('finance_expense_edit', expense_id=expense_id)
                
                # For pro-rata expenses, we need to handle the original expense differently
                # First, get all existing expenses with the ORIGINAL line type and expense type
                original_expenses = expense.objects.filter(
                    expense_line_types_id=existing_expense.expense_line_types_id,
                    expense_types_id=existing_expense.expense_types_id
                )
                
                # Delete all original pro-rata expenses (they will be recreated)
                original_expenses.delete()
                
                # Create new expenses for each selected property
                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    
                    for month in months:
                        if getattr(expense_type, f'expense_types_{month}') == "Yes":
                            monthly_data[f'expense_{month}'] = property_data['calculated_amount']
                    
                    # Create new expense
                    expense.objects.create(**monthly_data)
                
                messages.success(request, f"{len(selected_properties)} pro-rata expenses updated successfully")
                return redirect('finance_expense')
                
            except json.JSONDecodeError:
                messages.error(request, "Invalid pro-rata data")
                return redirect('finance_expense_edit', expense_id=expense_id)
            except Exception as e:
                messages.error(request, f"Error processing pro-rata expense: {str(e)}")
                return redirect('finance_expense_edit', expense_id=expense_id)

        # Handle non-pro-rata or single property expense
        # IMPORTANT: Clear all monthly amounts first, then set only the active ones
        monthly_data = {
            'prop_id': prop_id,
            'expense_line_types_id': elt_id,
            'expense_types_id': et_id,
            'expense_amount': expense_amount,
            # Clear all monthly amounts first
            'expense_jan': None,
            'expense_feb': None,
            'expense_mar': None,
            'expense_apr': None,
            'expense_may': None,
            'expense_jun': None,
            'expense_jul': None,
            'expense_aug': None,
            'expense_sep': None,
            'expense_oct': None,
            'expense_nov': None,
            'expense_dec': None,
        }
        
        # Set only the active months based on the NEW expense type
        for month in months:
            if getattr(expense_type, f'expense_types_{month}') == "Yes":
                monthly_data[f'expense_{month}'] = expense_amount
        
        # Update the existing expense directly (don't use update_or_create)
        for field, value in monthly_data.items():
            setattr(existing_expense, field, value)
        existing_expense.save()
        
        messages.success(request, "Expense Updated Successfully")
        return redirect('finance_expense')
    
    return redirect('finance_expense_edit', expense_id=expense_id)

@login_required
def finance_expense_types(request):
    exp_types = expense_types.objects.all()
    return render(request, "finance_expense_types.html", {
        "etresults": exp_types,
    })

@login_required
def finance_expense_types_add(request):
    exp_types = expense_types.objects.all().order_by('expense_types_name')
    return render(request, "finance_expense_types_add.html", {"etresults":exp_types})

@login_required
def finance_expense_types_commit(request):
    if request.method == "POST":
        form = ExpenseTypesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Types Added Successfully")
    exp_types = expense_types.objects.all()
    return render(request, "finance_expense_types.html", {"etresults":exp_types})

@login_required
def finance_expense_types_edit(request, expense_types_id):
    exp_types = expense_types.objects.filter(pk=expense_types_id)
    return render(request, "finance_expense_types_edit.html", {"etresults":exp_types})

@login_required
def finance_expense_types_edit_commit(request, expense_types_id):
    exp = get_object_or_404(expense_types, pk=expense_types_id)
    all_types = expense_types.objects.all().order_by('expense_types_name')
    if request.method == "POST":
        name = request.POST.get('expense_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if expense_types.objects.filter(
            expense_types_name__iexact=name
        ).exclude(
            pk=expense_types_id
        ).exists():
            messages.error(request, "No duplicate Expense Types Allowed")
            return render(request, "finance_expense_types.html", {
                "etresults": all_types,
                "exp": exp,
                "name_error": True
            })
        form = ExpenseTypesForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Type Edited Successfully")
            return redirect('finance_expense_types')
    
    # If GET request or form invalid
    return render(request, "finance_expense_types.html", {
        "etresults": all_types,
        "exp": exp
    })

@login_required
def finance_expense_line_types(request):
    exp_line_types = expense_line_types.objects.all().order_by('expense_line_types_name')
    return render(request, "finance_expense_line_types.html", {
        "eltresults": exp_line_types,
    })

@login_required
def finance_expense_line_types_add(request):
    exp_line_types = expense_line_types.objects.all()
    return render(request, "finance_expense_line_types_add.html", {"eltresults":exp_line_types})

@login_required
def finance_expense_line_types_commit(request):
    if request.method == "POST":
        form = ExpenseLineForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Line Type Added Successfully")
    exp_line_types = expense_line_types.objects.all()
    return render(request, "finance_expense_line_types.html", {"eltresults":exp_line_types})

@login_required
def finance_expense_line_types_edit(request, expense_line_types_id):
    exp_line_types = expense_line_types.objects.filter(pk=expense_line_types_id)
    return render(request, "finance_expense_line_types_edit.html", {"eltresults":exp_line_types})

@login_required
def finance_expense_line_types_edit_commit(request, expense_line_types_id):
    exp = get_object_or_404(expense_line_types, pk=expense_line_types_id)
    all_types = expense_line_types.objects.all().order_by('expense_line_types_name')
    if request.method == "POST":
        name = request.POST.get('expense_line_types_name')
        # Check for duplicates (case-insensitive, excluding current record)
        if expense_line_types.objects.filter(
            expense_line_types_name__iexact=name
        ).exclude(
            pk=expense_line_types_id
        ).exists():
            messages.error(request, "No duplicate Expense Line Types Allowed")
            return render(request, "finance_expense_line_types.html", {
                "eltresults": all_types,
                "exp": exp,
                "name_error": True
            })
        form = ExpenseLineForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Line Type Edited Successfully")
            return redirect('finance_expense_line_types')
    
    # If GET request or form invalid
    return render(request, "finance_expense_line_types.html", {
        "eltresults": all_types,
        "exp": exp
    })

@login_required
def check_expenses_for_line_type(request, expense_line_type_id):
    """
    Check if there are expenses linked to this expense line type
    Returns JSON with expense details if any exist
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get the expense line type
        expense_line_type = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
        
        # Check for linked expenses using the correct foreign key field name
        linked_expenses = expense.objects.filter(expense_line_types=expense_line_type)
        
        if linked_expenses.exists():
            # Prepare expense data for the frontend
            expenses_data = []
            for exp in linked_expenses:
                # Calculate total amount from all months
                total_amount = 0
                monthly_amounts = []
                
                months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                         'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                
                for month in months:
                    month_value = getattr(exp, f'expense_{month}', None)
                    if month_value:
                        total_amount += month_value
                        monthly_amounts.append(f'{month.capitalize()}: {month_value}')
                
                # Use base expense_amount if available, otherwise use calculated total
                display_amount = exp.expense_amount if exp.expense_amount else total_amount
                
                expenses_data.append({
                    'id': exp.expense_id,
                    'expense_type': str(exp.expense_types) if exp.expense_types else 'N/A',
                    'property': str(exp.prop) if exp.prop else 'N/A',
                    'base_amount': str(exp.expense_amount) if exp.expense_amount else '0.00',
                    'total_monthly': str(total_amount),
                    'display_amount': str(display_amount),
                    'monthly_breakdown': monthly_amounts
                })
            
            return JsonResponse({
                'has_expenses': True,
                'expense_count': linked_expenses.count(),
                'expenses': expenses_data
            })
        else:
            return JsonResponse({
                'has_expenses': False,
                'expense_count': 0,
                'expenses': []
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_expense_line_type(request, expense_line_type_id):
    """
    Delete an expense line type and all its linked expenses
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        with transaction.atomic():
            # Get the expense line type
            expense_line_type = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
            
            # Get linked expenses before deletion
            linked_expenses = expense.objects.filter(expense_line_types=expense_line_type)
            expense_count = linked_expenses.count()
            
            # Delete all linked expenses first
            linked_expenses.delete()
            
            # Delete the expense line type
            expense_line_type_name = expense_line_type.expense_line_types_name
            expense_line_type.delete()
            
            # Create success message
            if expense_count > 0:
                message = f'Expense line type "{expense_line_type_name}" and {expense_count} linked expense(s) have been deleted successfully.'
            else:
                message = f'Expense line type "{expense_line_type_name}" has been deleted successfully.'
            
            messages.success(request, message)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'deleted_expenses': expense_count
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def finance_valuations(request):
    props_list = props.objects.all().order_by('prop_country', 'prop_name')
    valuations = prop_values.objects.all()
    
    # Create a dictionary for easy lookup
    valuations_dict = {v.prop_id: v for v in valuations}
    
    # Calculate totals
    pur_balance = sum(
        v.prop_values_purchase_price 
        for v in valuations 
        if v.prop_values_purchase_price is not None
    )
    cur_balance = sum(
        v.prop_values_current_value 
        for v in valuations 
        if v.prop_values_current_value is not None
    )
    
    return render(request, "finance_valuations.html", {
        "props": props_list,
        "prop_values": valuations_dict,
        "pur_balance": pur_balance,
        "cur_balance": cur_balance
    })

@login_required
def finance_valuations_add(request):
	results = props.objects.all().order_by('prop_country', 'prop_name')
	vresults = prop_values.objects.all()
	context = {
		'props': results,
		'prop_values': vresults,
	}
	return render(request, "finance_valuations_add.html", context)

@login_required
def finance_valuations_commit(request):
    if request.method == "POST":
        prop_id = request.POST.get('prop_id')  # Get property ID from form
        
        # Check if valuation already exists for this property
        if prop_values.objects.filter(prop_id=prop_id).exists():
            messages.error(request, "A valuation already exists for this property. Please edit the existing valuation.")
            return redirect('finance_valuations')
            
        form = ValuesForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Valuation Added Successfully")
            return redirect('finance_valuations')
        else:
            messages.error(request, "Please correct the errors below")
    
    # Rest of your view remains the same...
    results = props.objects.all().order_by('prop_country','prop_name')
    vresults = prop_values.objects.all().order_by('prop_values_purchase_price')    
    
    pur_balance = sum(x.prop_values_purchase_price for x in vresults if x.prop_values_purchase_price is not None)
    cur_balance = sum(x.prop_values_current_value for x in vresults if x.prop_values_current_value is not None)

    context = {
        'pur_balance': pur_balance,
        'cur_balance': cur_balance,        
        'props': results,
        'prop_values': vresults,
    }
    return render(request, "finance_valuations.html", context)

@login_required
def finance_valuations_edit(request, prop_values_id):
	try:
		vresults = prop_values.objects.get(pk=prop_values_id)
	except prop_values.DoesNotExist:
		print(f"ERROR: No prop_values record found for ID {prop_values_id}")
		raise Http404("Valuation not found")
	results = props.objects.all().order_by('prop_country','prop_name')
	return render(request, "finance_valuations_edit.html", {
		"props": results,
		"vresults": vresults
	})

@login_required
def finance_valuations_edit_commit(request, prop_values_id):
    print("Form data received:", request.POST)
    vresult = prop_values.objects.get(pk=prop_values_id)
    
    if request.method == "POST":
        form = ValuesForm(request.POST, instance=vresult)
        if form.is_valid():
            print("Form is valid, saving...")
            form.save()
            print("Saved values:", vresult.prop_values_purchase_price, vresult.prop_values_current_value)
            messages.success(request, "Valuations Edited Successfully")
            return redirect('finance_valuations')  # Redirect instead of render
        else:
        	print("Form errors:", form.errors)
    
    # If GET or invalid form, show the valuations page
    return redirect('finance_valuations')

### TENANTS ###
@login_required
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
def tenant_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	return render(request, "tenant_add.html", {"props":results, "tenant":tresults})

@login_required
def tenant_edit(request, tenant_id):
	tresults = tenant.objects.filter(pk=tenant_id)
	results = props.objects.all().order_by('prop_country','prop_name')
	return render (request, "tenant_edit.html", {"props":results, "tenant":tresults})

@login_required
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

### SUPPLIERS ###
@login_required
def suppliers(request):
    sup_output = request.POST.get('supname')
    sup_count = request.POST.get('supcount')
    
    # Start with all suppliers
    sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
    
    # Apply search filter if provided and not "All"
    if sup_output and sup_output != "All":
        sresults = sresults.filter(supplier_contact_person__icontains=sup_output)
    
    # Apply country filter if provided and not "All"  
    if sup_count and sup_count != "All":
        sresults = sresults.filter(supplier_country=sup_count)
    
    # Pass the search values back to template for form preservation
    context = {
        "supplier": sresults,
        "selected_supplier": sup_output if sup_output and sup_output != "All" else "",
        "selected_country": sup_count if sup_count and sup_count != "All" else "All"
    }
    
    return render(request, "suppliers.html", context)

@login_required
def suppliers_add(request):
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render(request, "suppliers_add.html", {"supplier":sresults})

@login_required
def suppliers_edit(request, supplier_id):
	sresults = supplier.objects.filter(pk=supplier_id)
	return render (request, "suppliers_edit.html", {"supplier":sresults})

@login_required
def suppliers_commit(request):
	if request.method == "POST":
		form = SupplierForm(request.POST or None)
		if form.is_valid():
			form.save()
			messages.success(request, "Supplier Added Successfully")
		else:
			print(form.errors.as_data())
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "suppliers.html", {"supplier":sresults})

@login_required
def suppliers_edit_commit(request, supplier_id):
	sup = supplier.objects.get(pk=supplier_id)
	if request.method == "POST":
		form = SupplierForm(request.POST or None, instance=sup)
		if form.is_valid():
			form.save()
			messages.success(request, "Supplier Edited Successfully")
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "suppliers.html", {"supplier":sresults})

@login_required
def suppliers_delete(request, supplier_id):
    if request.method == 'POST' and request.user.is_superuser:
        try:
            supplier_instance = supplier.objects.get(supplier_id=supplier_id)
            contact_person = supplier_instance.supplier_contact_person
            supplier_instance.delete()
            messages.success(request, f'Supplier "{contact_person}" has been deleted successfully.')
        except supplier.DoesNotExist:
            messages.error(request, 'Supplier not found.')
        except Exception as e:
            messages.error(request, f'Error deleting supplier: {str(e)}')
    else:
        messages.error(request, 'Unauthorized action.')
    
    return redirect('suppliers')

### INVOICES ###
@login_required
def invoices_page(request):
    # Get filter values from POST request
    prop_output = request.POST.get('propname', '')
    tenant_output = request.POST.get('tenantname', '')
    
    # Always get all props for the dropdown
    all_props = props.objects.all().order_by('prop_country', 'prop_name')
    
    # Always get all tenants for the dropdown  
    all_tenants = tenant.objects.all().order_by('tenant_name')
    
    # Get unpaid invoices
    iresults = invoices.objects.filter(invoice_paid="No").order_by('invoice_date')
    
    # Filter props based on selection
    if prop_output and prop_output != "All":
        filtered_props = props.objects.filter(prop_name=prop_output)
    else:
        filtered_props = all_props
    
    # Filter tenants based on selection
    if tenant_output and tenant_output != "All":
        filtered_tenants = tenant.objects.filter(tenant_name=tenant_output)
    else:
        filtered_tenants = all_tenants
    
    context = {
        "invoices": iresults,
        "tenant": filtered_tenants,  # Filtered tenants for display
        "props": filtered_props,     # Filtered props for display
        "all_props": all_props,      # All props for dropdown
        "all_tenants": all_tenants,  # All tenants for dropdown
        "selected_property": prop_output if prop_output != "All" else "",
        "selected_tenant": tenant_output if tenant_output != "All" else "",
    }
    
    return render(request, "invoices.html", context)

@login_required
def invoices_commit(request, invoice_id):
    inv_tbp = invoices.objects.filter(pk=invoice_id).update(invoice_paid="Yes")
    iresults = invoices.objects.get(pk=invoice_id)
    tresults = tenant.objects.get(pk=iresults.tenant_id)
    # Attempt to send the notification email
    if send_invoices_paid_email(tresults, iresults.invoice_date):
        messages.info(request, "Invoice marked as Paid notification email sent.")
    else:
        messages.warning(request, "Invoice marked as Paid, but email could not be sent.")
    return redirect('invoices')

def send_invoices_paid_email(tenant, invoice_date):
    """
    Send email notification of an invoice payment for a specific tenant
    """
    from django.db import connection
    import logging
    
    logger = logging.getLogger(__name__)
    smtp_object = None
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "demetrimanias@gmail.com"
        msg['Subject'] = "Rent Payment"
        
        # Email body with proper formatting
        body = f"""Dear User,

The rent has been received from the following tenant:
 - Tenant: {tenant}
 - Invoice Date: {invoice_date}

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
        
        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)
        
        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, "demetrimanias@gmail.com", text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()

### PROPERTIES ###
@login_required
def properties_page(request):
    # Get filter values from the new form
    search_query = request.POST.get('search', '').strip()
    selected_country = request.POST.get('country', '')
    selected_status = request.POST.get('status', '')
    
    # Start with all properties
    results = props.objects.all()
    
    # Apply cumulative filters (all work together)
    if search_query:
        results = results.filter(prop_name__icontains=search_query)
    
    if selected_country:
        results = results.filter(prop_country=selected_country)
    
    if selected_status:
        results = results.filter(prop_status=selected_status)
    
    # Always order the results
    results = results.order_by('prop_country', 'prop_name')
    
    # Pass filter values back to template for form persistence
    context = {
        'props': results,
        'search_query': search_query,
        'selected_country': selected_country,
        'selected_status': selected_status,
    }

    return render(request, "properties.html", context)

@login_required
def properties_map_view(request):
    """Display all properties on an interactive map"""
    
    # Get all properties from the database
    properties = props.objects.all()
    
    # Convert properties to JSON format for JavaScript
    properties_data = []
    for prop in properties:
        # Handle Decimal fields properly
        latitude = None
        longitude = None
        
        if prop.prop_latitude is not None:
            latitude = float(prop.prop_latitude)
        if prop.prop_longitude is not None:
            longitude = float(prop.prop_longitude)
        
        property_dict = {
            'id': prop.prop_id,
            'name': prop.prop_name,
            'address1': prop.prop_address1,
            'address2': prop.prop_address2,
            'suburb': prop.prop_suburb,
            'city': prop.prop_city,
            'province': prop.prop_province,
            'country': prop.prop_country,
            'pcode': prop.prop_pcode,
            'latitude': latitude,
            'longitude': longitude,
            'floor_area': prop.prop_floor_area,
            'year_built': prop.prop_year_built,
            'status': prop.prop_status,
            'available_for_rent': prop.prop_available_for_rent,
        }
        properties_data.append(property_dict)
    
    context = {
        'properties_json': json.dumps(properties_data),
        'properties_count': len(properties_data)
    }
    
    return render(request, 'map_view.html', context)

@login_required
def properties_title_deed(request):
    properties = props.objects.all().order_by('prop_country','prop_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        prop_id = request.POST.get('property_id')  # Changed from 'prop_id' to match form
        
        if not prop_id:
            messages.error(request, 'No property selected')
            return redirect('properties_title_deed')
        
        try:
            property_obj = get_object_or_404(props, pk=prop_id)
            
            if action == 'delete':
                if property_obj.prop_title_deed:
                    # Delete the file from storage
                    property_obj.prop_title_deed.delete()
                    property_obj.prop_title_deed_status = "No Title Deed"
                    property_obj.save()
                    messages.success(request, f'Title deed deleted for {property_obj.prop_name}!')
                else:
                    messages.warning(request, 'No title deed found to delete.')
                    

            elif action == 'upload':
                if 'title_deed' in request.FILES:
                    uploaded_file = request.FILES['title_deed']
                    
                    # Validate file size (10MB limit)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 10MB limit')
                        return redirect('properties_title_deed')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF or image files only.')
                        return redirect('properties_title_deed')
                    
                    try:
                        # Ensure directory exists
                        upload_path = os.path.join(settings.MEDIA_ROOT, 'properties', 'title_deeds')
                        os.makedirs(upload_path, exist_ok=True)
                        
                        # Delete old file if exists
                        if property_obj.prop_title_deed:
                            property_obj.prop_title_deed.delete(save=False)
                        
                        # Save new file
                        property_obj.prop_title_deed = uploaded_file
                        property_obj.prop_title_deed_status = "Title Deed Uploaded"
                        property_obj.save()
                        
                        messages.success(request, f'Title deed uploaded successfully for {property_obj.prop_name}!')
                    except Exception as e:
                        messages.error(request, f'Error saving file: {str(e)}')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    context = {
        'properties': properties,
    }
    return render(request, 'properties_title_deed.html', context)

@login_required
def properties_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	existing_names = list(props.objects.values_list('prop_name', flat=True))
	return render(request, "properties_add.html", {"props":results, "existing_names": existing_names})

@login_required
def properties_commit(request):
	if request.method == "POST":
		form = PropForm(request.POST or None)
		if form.is_valid():
			form.save()
	results = props.objects.all().order_by('prop_country','prop_name')
	messages.success(request, "Property Added Successfully")
	return render (request, "properties.html", {"props":results})

@login_required
def properties_edit(request, prop_id):
    # Get the current property being edited
    current_property = get_object_or_404(props, pk=prop_id)
    
    # Get all other property names (excluding the current one)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)
    
    return render(request, "properties_edit.html", {
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names)  # Add this for client-side validation
    })

@login_required
def properties_edit_commit(request, prop_id):
    prop = get_object_or_404(props, pk=prop_id)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)
    
    if request.method == "POST":
        form = PropForm(request.POST, instance=prop)
        
        if form.is_valid():
            new_name = form.cleaned_data.get('prop_name')
            current_name = prop.prop_name
            
            if new_name.lower() != current_name.lower():
                if props.objects.exclude(prop_id=prop_id).filter(prop_name__iexact=new_name).exists():
                    messages.error(request, "A property with this name already exists.")
                    return render(request, "properties_edit.html", {
                        'props': [prop],
                        'existing_names': list(existing_names)
                    })
            
            form.save()
            messages.success(request, "Property Edited Successfully")
            results = props.objects.all().order_by('prop_country','prop_name')
            return redirect('properties')  # Better to redirect after POST
        
        # Form is invalid
        messages.error(request, "Please correct the errors below.")
        return render(request, "properties_edit.html", {
            'props': [prop],
            'existing_names': list(existing_names)
        })
    
    # If not POST, redirect to properties page
    return redirect('properties')


### ACTUAL EXPENSES ###
@login_required
def act_expense_manage_document(request):
    """
    Handle document upload, replacement, and deletion within the main expense page
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        expense_id = request.POST.get('expense_id')
        
        if not expense_id:
            messages.error(request, 'No expense selected')
            return redirect('act_expense_all')
        
        try:
            expense = get_object_or_404(act_expense, pk=expense_id)
            
            if action == 'delete_document':
                # Handle document deletion only (not the entire expense)
                if expense.act_expense_document:
                    # Delete the physical file
                    if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                        expense.act_expense_document.delete(save=False)
                    
                    # Clear the database field
                    expense.act_expense_document = None
                    expense.save()
                    
                    messages.success(request, f'Invoice document deleted successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.warning(request, 'No document found to delete.')
                    
            elif action == 'upload':
                # Handle file upload/replacement
                if 'act_expense_document' in request.FILES:
                    uploaded_file = request.FILES['act_expense_document']
                    
                    # Validate file size (5MB limit)
                    if uploaded_file.size > 5 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 5MB limit')
                        return redirect('act_expense_all')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF, JPG, PNG, Excel, or Word files only.')
                        return redirect('act_expense_all')
                    
                    # Delete existing file if present
                    if expense.act_expense_document:
                        if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                            expense.act_expense_document.delete(save=False)
                    
                    expense.act_expense_document = uploaded_file
                    expense.save()
                    messages.success(request, f'Invoice document uploaded successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    return redirect('act_expense_all')

from datetime import datetime

@login_required
def act_expense_all(request):
    # Get filter parameters from request
    search_query = request.GET.get('search', '').strip()
    property_filter = request.GET.get('property', '').strip()
    status_filter = request.GET.get('status', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    # Base queryset - all expenses, ordered by date (most recent first)
    expenses = act_expense.objects.select_related('prop').order_by('-act_expense_date')
    
    # Apply filters one by one
    
    # 1. Search filter - search in description
    if search_query:
        expenses = expenses.filter(
            act_expense_description__icontains=search_query
        )
    
    # 2. Property filter
    if property_filter:
        try:
            property_id = int(property_filter)
            expenses = expenses.filter(prop_id=property_id)
        except (ValueError, TypeError):
            pass
    
    # 3. Status filter
    if status_filter:
        if status_filter == 'require_approval':
            expenses = expenses.filter(act_expense_approved='No', act_expense_paid='No')
        elif status_filter == 'approved_not_paid':
            expenses = expenses.filter(act_expense_approved='Yes', act_expense_paid='No')
        elif status_filter == 'approved_and_paid':
            expenses = expenses.filter(act_expense_approved='Yes', act_expense_paid='Yes')
    
    # 4. Date range filtering
    if from_date:
        try:
            # Ensure proper date format
            parsed_from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            expenses = expenses.filter(act_expense_date__gte=parsed_from_date)
        except ValueError:
            pass
    
    if to_date:
        try:
            # Ensure proper date format
            parsed_to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            expenses = expenses.filter(act_expense_date__lte=parsed_to_date)
        except ValueError:
            pass
    
    # Get properties for filter dropdown
    properties = props.objects.filter(prop_status="Active").order_by('prop_country', 'prop_name')
    
    # Determine navigation context
    came_from = request.GET.get('from', None)
    from_finance_pl_act = request.GET.get('from_finance_pl_act', False)
    
    # Convert string 'True'/'False' to boolean if needed
    if isinstance(from_finance_pl_act, str):
        from_finance_pl_act = from_finance_pl_act.lower() == 'true'

    return render(request, 'act_expense.html', {
        'expenses': expenses,
        'props': properties,
        'current_year': datetime.now().year,
        'from_finance_pl_act': from_finance_pl_act,
        'came_from': came_from,
        # Pass filter values back to template to maintain state
        'search_query': search_query,
        'selected_property': property_filter,
        'selected_status': status_filter,
        'selected_from_date': from_date,
        'selected_to_date': to_date,
    })

@login_required
def act_expense_upload_inv(request):
    # Get all expenses to display in the table
    expenses = act_expense.objects.all().order_by('-act_expense_date')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        expense_id = request.POST.get('expense_id')
        
        if not expense_id:
            messages.error(request, 'No expense selected')
            return redirect('act_expense_upload_inv')
        
        try:
            expense = get_object_or_404(act_expense, pk=expense_id)
            
            if action == 'delete':
                # Handle file deletion
                if expense.act_expense_document:
                    # Delete the physical file
                    if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                        expense.act_expense_document.delete(save=False)
                    
                    # Clear the database field
                    expense.act_expense_document = None
                    expense.save()
                    
                    messages.success(request, f'Document deleted successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.warning(request, 'No document found to delete.')
                    
            elif action == 'upload':
                # Handle file upload (your existing code)
                if 'act_expense_document' in request.FILES:
                    uploaded_file = request.FILES['act_expense_document']
                    
                    # Validate file size (5MB limit)
                    if uploaded_file.size > 5 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 5MB limit')
                        return redirect('act_expense_upload_inv')
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF, JPG, PNG, Excel, or Word files only.')
                        return redirect('act_expense_upload_inv')
                    
                    # Delete existing file if present
                    if expense.act_expense_document:
                        if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                            expense.act_expense_document.delete(save=False)
                    
                    expense.act_expense_document = uploaded_file
                    expense.save()
                    messages.success(request, f'Document uploaded successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.error(request, 'Please select a file to upload')
                    
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    context = {
        'expenses': expenses,
    }
    return render(request, 'act_expense_upload_inv.html', context)

@login_required
def act_expense_view(request):
    # Get year/month from request or use current year as default
    selected_year = request.GET.get('year', datetime.now().year)
    selected_month = request.GET.get('month')
    from_finance_pl_act = request.GET.get('from_finance_pl_act', False)
    property_id = request.GET.get('property_id')
    properties = request.GET.get('properties', '')  # NEW: Handle comma-separated properties
    
    # Base queryset - only approved and paid expenses, ordered by date
    expenses = act_expense.objects.select_related('prop').filter(
        act_expense_approved="Yes",
        act_expense_paid="Yes"
    ).order_by('-act_expense_date')
    
    # Filter by property - UPDATED LOGIC
    if properties:  # NEW: Handle comma-separated properties
        try:
            property_ids = [int(prop_id.strip()) for prop_id in properties.split(',') if prop_id.strip()]
            expenses = expenses.filter(prop_id__in=property_ids)
        except ValueError:
            pass  # Invalid property IDs, skip filtering
    elif property_id:  # Keep existing single property logic for backward compatibility
        try:
            expenses = expenses.filter(prop_id=int(property_id))
        except (ValueError, TypeError):
            pass  # Skip if property_id is invalid
    
    # Handle YEAR/MONTH filtering (convert to int safely)
    try:
        year = int(request.GET.get('year', 0)) if request.GET.get('year') else None
        month = int(request.GET.get('month', 0)) if request.GET.get('month') else None
    except (ValueError, TypeError):
        year, month = None, None  # Fallback if invalid input
    
    if year:
        expenses = expenses.filter(act_expense_date__year=year)
        if month:
            expenses = expenses.filter(act_expense_date__month=month)
    
    # Handle DATE RANGE filtering
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date and to_date:
        expenses = expenses.filter(
            act_expense_date__gte=from_date,
            act_expense_date__lte=to_date
        )
    
    # Get available years for filter dropdown
    available_years = act_expense.objects.filter(
        act_expense_approved="Yes",
        act_expense_paid="Yes"
    ).dates('act_expense_date', 'year').order_by('-act_expense_date')
    
    return render(request, 'act_expense.html', {
        'expenses': expenses,
        'selected_year': year if year else int(selected_year),
        'selected_month': month,
        'current_year': datetime.now().year,
        'available_years': [y.year for y in available_years],
        'from_finance_pl_act': from_finance_pl_act,
        'selected_property_id': property_id
    })

@login_required
def act_expense_edit(request, expense_id):
    # Get the current expense being edited
    current_expense = get_object_or_404(act_expense, pk=expense_id)
    
    # Get property details from props table
    results = props.objects.filter(prop_status="Active").order_by('prop_country','prop_name')

    return render(request, "act_expense_edit.html", {
        "props": results,
        "current_expense": current_expense,
    })

@login_required
def act_expense_edit_commit(request, expense_id):
    if request.method == 'POST':
        try:
            expense = act_expense.objects.get(act_expense_id=expense_id)
            
            # Update expense fields
            expense.act_expense_date = request.POST.get('act_expense_date')
            expense.prop_id = request.POST.get('prop')
            expense.act_expense_description = request.POST.get('act_expense_description')
            expense.act_expense_amount = request.POST.get('act_expense_amount')
            
            if request.user.is_superuser:
                expense.act_expense_approved = request.POST.get('act_expense_approved')
                
                # Handle the paid field - check for hidden field if main field is missing
                paid_value = request.POST.get('act_expense_paid')
                if not paid_value:  # If main field is empty (disabled)
                    paid_value = request.POST.get('act_expense_paid_hidden')
                
                expense.act_expense_paid = paid_value
            
            expense.save()
            
            messages.success(request, 'Expense updated successfully!')
            
        except act_expense.DoesNotExist:
            messages.error(request, 'Expense not found.')
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
    
    return redirect('act_expense_all')

@login_required
def get_expense_invoice(request, expense_id):
    try:
        # Adjust this query based on your Expense model
        # expense_id might be the date or actual expense ID
        expense = YourExpenseModel.objects.filter(
            # Add your filter logic here - could be by date, ID, etc.
            date=expense_id  # or id=expense_id
        ).first()
        
        if expense and expense.invoice_file:  # Adjust field name
            response = HttpResponse(
                expense.invoice_file.read(), 
                content_type='application/pdf'  # or detect content type
            )
            response['Content-Disposition'] = f'inline; filename="invoice_{expense_id}.pdf"'
            return response
        else:
            raise Http404("Invoice not found")
            
    except Exception as e:
        raise Http404("Invoice not found")

@login_required
def mark_approved(request, expense_id):
    expense = get_object_or_404(act_expense, pk=expense_id)
    if expense.act_expense_approved != 'Yes':  # Only update if not already approved
        expense.act_expense_approved = 'Yes'
        expense.save()
        # Attempt to send the notification email with enhanced details
        from datetime import date
        if send_expense_approved_email(
            expense.act_expense_date, 
            expense.prop.prop_name,  # Access through the foreign key relationship
            expense.act_expense_description, 
            expense.act_expense_amount,
            date.today()
        ):
            messages.info(request, "Expense approved and notification email sent.")
        else:
            messages.warning(request, "Expense approved, but email could not be sent.")
    return redirect('act_expense_all')

@login_required
def mark_paid(request, expense_id):
    expense = get_object_or_404(act_expense, pk=expense_id)
    if expense.act_expense_paid != 'Yes':  # Only update if not already paid
        expense.act_expense_paid = 'Yes'
        expense.save()
        # Attempt to send the notification email with enhanced details
        from datetime import date
        if send_expense_paid_email(
            expense.act_expense_date,
            expense.prop.prop_name,  # Access through the foreign key relationship
            expense.act_expense_description,
            expense.act_expense_amount,
            date.today()
        ):
            messages.info(request, "Expense marked as paid and notification email sent.")
        else:
            messages.warning(request, "Expense marked as paid, but email could not be sent.")
    return redirect('act_expense_all')

@login_required
def mark_deleted(request, expense_id):
    try:
        expense = get_object_or_404(act_expense, pk=expense_id)
        expense.delete()  # Permanently deletes the record
        messages.success(request, "Expense deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting expense: {str(e)}")
    return redirect('act_expense_all')

@login_required
def act_expense_add(request):
    results = props.objects.filter(prop_status="Active").order_by('prop_country','prop_name')
    return render(request, "act_expense_add.html", {'props': results})

def send_expense_approved_email(expense_date, property_name, description, amount, approved_date):
    """
    Send email notification of an expense approval for a specific expense
    """
    from django.db import connection
    import logging
    
    logger = logging.getLogger(__name__)
    smtp_object = None
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "stella.simitopoulos@alivente.com"
        msg['Cc'] = "demetrimanias@gmail.com"
        msg['Subject'] = f"Expense Approved - €{amount} for {property_name}"
        
        # Email body with proper formatting
        body = f"""Dear User,

An expense has been APPROVED. The details are as follows:

- Expense Date: {expense_date.strftime('%d/%m/%Y')}
- Property: {property_name}
- Description: {description}
- Amount: €{amount}
- Approved Date: {approved_date.strftime('%d/%m/%Y')}
- Status: Approved (Pending Payment)

You can view this expense in the Alivente Property Management System.

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
        
        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)
        
        # Send email to both To and CC recipients
        recipients = ["stella.simitopoulos@alivente.com", "demetrimanias@gmail.com"]
        text = msg.as_string()
        smtp_object.sendmail(email, recipients, text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()

def send_expense_paid_email(expense_date, property_name, description, amount, paid_date):
    """
    Send email notification of an expense payment for a specific expense
    """
    from django.db import connection
    import logging
    
    logger = logging.getLogger(__name__)
    smtp_object = None
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "stella.simitopoulos@alivente.com"
        msg['Cc'] = "demetrimanias@gmail.com"
        msg['Subject'] = f"Expense Paid - €{amount} for {property_name}"
        
        # Email body with proper formatting
        body = f"""Dear User,

An expense has been PAID. The details are as follows:

- Expense Date: {expense_date.strftime('%d/%m/%Y')}
- Property: {property_name}
- Description: {description}
- Amount: €{amount}
- Paid Date: {paid_date.strftime('%d/%m/%Y')}
- Status: Fully Processed

This expense has been completed and processed.

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
        
        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)
        
        # Send email to both To and CC recipients
        recipients = ["stella.simitopoulos@alivente.com", "demetrimanias@gmail.com"]
        text = msg.as_string()
        smtp_object.sendmail(email, recipients, text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()

def send_expense_approval_email_with_link(expense_date, property_name, description, amount, created_date):
    """
    Send email notification for expense approval with enhanced details
    """
    from django.db import connection
    import logging
    
    logger = logging.getLogger(__name__)
    smtp_object = None
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = "demetrimanias@gmail.com"
        msg['Cc'] = "stella.simitopoulos@alivente.com"
        msg['Subject'] = f"New Expense Requires Approval - €{amount} for {property_name}"
        
        # Email body with proper formatting
        body = f"""Dear User,

A new Actual Expense has been created that requires your approval. The details are as follows:

- Expense Date: {expense_date.strftime('%d/%m/%Y')}
- Property: {property_name}
- Description: {description}
- Amount: €{amount}
- Created Date: {created_date.strftime('%d/%m/%Y')}
- Status: Pending Approval

You can view this expense in the Alivente Property Management System.

Thanks,

Alivente Property Management System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
        
        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False
        
        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()
        
        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)
        
        # Send email to both To and CC recipients
        recipients = ["demetrimanias@gmail.com", "stella.simitopoulos@alivente.com"]
        text = msg.as_string()
        smtp_object.sendmail(email, recipients, text)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()

@login_required
def act_expense_commit(request):
    if request.method == 'POST':
        try:
            # Get data from the form
            expense_date = request.POST.get('act_expense_date')
            expense_prop = request.POST.get('prop')
            expense_description = request.POST.get('act_expense_description')
            expense_amount = request.POST.get('act_expense_amount')
            expense_approved = request.POST.get('act_expense_approved', 'No')
            expense_paid = request.POST.get('act_expense_paid', 'No')
            
            # Validate required fields
            if not expense_date or not expense_description or not expense_amount or not expense_prop:
                messages.error(request, 'All fields are required.')
                return redirect('act_expense_add')
            
            # Create and save the expense record
            expense = act_expense(
                act_expense_date=expense_date,
                act_expense_description=expense_description,
                act_expense_amount=float(expense_amount),
                act_expense_approved=expense_approved,
                act_expense_paid=expense_paid,
                prop_id=expense_prop
            )
            expense.save()
            
            # Check if user is not a superuser and send email
            if not request.user.is_superuser:
                from datetime import date
                from django.utils.dateparse import parse_date
                
                # Parse the expense date for email
                parsed_expense_date = parse_date(expense_date)
                
                email_sent = send_expense_approval_email_with_link(
                    parsed_expense_date,
                    expense.prop.prop_name,  # Get property name through foreign key
                    expense_description,
                    expense_amount,
                    date.today()  # Created date
                )
                if email_sent:
                    messages.success(request, 'Expense added successfully and approval email sent!')
                else:
                    messages.warning(request, 'Expense added successfully but failed to send approval email.')
            else:
                messages.success(request, 'Expense added successfully!')
            
            return redirect('act_expense_all')
            
        except ValueError as e:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('act_expense_add')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('act_expense_add')
    
    return redirect('act_expense_add')

### PETTY CASH ###
@login_required
def petty_cash(request):
	presults = petty.objects.all().order_by('petty_cash_date')
	pvalues = petty.objects.values()
	balance = 0
	for x in pvalues:
		if x['petty_cash_dr_cr'] == "DR":
			balance = balance + x['petty_cash_amount']
		elif x['petty_cash_dr_cr'] == "CR":
			balance = balance - x['petty_cash_amount']
	return render (request, "petty_cash.html", {"petty":presults, "balance":balance})

@login_required
def petty_cash_commit(request):
	if request.method == "POST":
		form = PettyForm(request.POST or None)
		print(form)
		if form.is_valid():
			form.save()
			messages.success(request, "Transaction Added Successfully")
	presults = petty.objects.all().order_by('petty_cash_date')
	pvalues = petty.objects.values()
	balance = 0
	for x in pvalues:
		if x['petty_cash_dr_cr'] == "DR":
			balance = balance + x['petty_cash_amount']
		elif x['petty_cash_dr_cr'] == "CR":
			balance = balance - x['petty_cash_amount']
	return render (request, "petty_cash.html", {"petty":presults, "balance":balance})

@login_required
def petty_cash_add(request):
	presults = petty.objects.all().order_by('petty_cash_date')
	return render(request, "petty_cash_add.html", {"petty":presults})


### ISSUES - FRIDAY STATUS REPORT ###
@login_required
def fsr(request):
    # Get filter parameters
    prop_output = request.POST.get('propname', '').strip()
    country_output = request.POST.get('propcountry', '').strip()
    status_output = request.POST.get('issuestatus', '').strip()
    search_query = request.POST.get('search', '').strip()
    
    # Start with all objects
    results = props.objects.all().order_by('prop_country', 'prop_name')
    isresults = issues.objects.all().order_by('issues_date_logged', 'issues_status')
    idresults = issues_details.objects.all().order_by('issues_details_date', 'issues_details_id')
    
    # Apply filters to properties based on country
    if country_output and country_output != 'All':
        results = results.filter(prop_country=country_output)
    
    # Apply filters to properties based on property name
    if prop_output and prop_output != 'All':
        results = results.filter(prop_name=prop_output)
    
    # Apply filters to issues based on status
    if status_output and status_output != 'All':
        isresults = isresults.filter(issues_status=status_output)
    
    # Apply search filter to issues (search in heading and description)
    if search_query:
        isresults = isresults.filter(
            Q(issues_heading__icontains=search_query) | 
            Q(issues_description__icontains=search_query)
        )
    
    # Get the property IDs from filtered results to ensure issues match filtered properties
    if country_output and country_output != 'All':
        property_ids = results.values_list('prop_id', flat=True)
        isresults = isresults.filter(prop_id__in=property_ids)
    
    if prop_output and prop_output != 'All':
        property_ids = results.values_list('prop_id', flat=True)
        isresults = isresults.filter(prop_id__in=property_ids)
    
    # Pass search query to template for displaying in search input
    context = {
        "props": results, 
        "issues": isresults, 
        "issues_details": idresults,
        "search_query": search_query,
        "selected_country": country_output,
        "selected_property": prop_output,
        "selected_status": status_output,
    }
    
    return render(request, "fsr.html", context)

@login_required
@require_POST
def delete_issue(request, issue_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        with transaction.atomic():
            # Get the issue (using your actual model name)
            issue_obj = get_object_or_404(issues, issues_id=issue_id)
            
            # Delete all related details first
            issues_details.objects.filter(issues=issue_obj).delete()
            
            # Delete the issue
            issue_obj.delete()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def fsr_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
	idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
	log_date = date.today()
	return render(request, "fsr_add.html", {"props":results, "issues":isresults, "issues_details":idresults, "log_date":log_date})

@login_required
def fsr_commit(request):
    if request.method == "POST":
        form = IssuesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Issue Added Successfully")
    temp_results = issues.objects.all().order_by('-issues_id')
    is_id = temp_results[0].issues_id
    return redirect(reverse("fsr_details", args=[is_id]) + "?from=fsr_add&origin=fsr")

@login_required
def fsr_details(request, issues_id):
    isresults = issues.objects.filter(pk=issues_id)
    results = props.objects.all().order_by('prop_country','prop_name')
    idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id').reverse()
    
    # Get the HTTP_REFERER if it exists
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Determine the clean redirect URL
    if 'fsr_details' in referrer:
        # If coming from another details page, go back to main FSR
        redirect_url = reverse('fsr')
    elif 'status_report' in referrer:
        # If coming from status report, go back there
        redirect_url = reverse('friday_status_report')
    else:
        # Default to the main FSR page
        redirect_url = reverse('fsr')
    
    context = {
        "props": results,
        "issues": isresults,
        "issues_details": idresults,
        "redirect_url": redirect_url,
    }
    
    return render(request, "fsr_details.html", context)

@login_required
def fsr_commit_status_change(request):
    if request.method == "POST":
        # Get form data
        issues_id = request.POST.get('issues_id')
        new_status = request.POST.get('issues_status')
        next_url = request.POST.get('next', '')
        
        # Get return parameters from hidden fields
        from_param = request.POST.get('from', 'fsr')
        property_id = request.POST.get('property_id')
        box_type = request.POST.get('box_type')
        
        # Update the issue
        issue = issues.objects.get(pk=issues_id)
        issue.issues_status = new_status
        if new_status == "Resolved":
            issue.issues_resolution_date = date.today()
        issue.save()
        
        # Handle property_detail navigation
        if from_param == 'property_detail' and property_id and box_type:
            # Redirect back to the same fsr_details page with property_detail parameters
            redirect_url = reverse('fsr_details', args=[issues_id])
            redirect_url += f"?from=property_detail&property_id={property_id}&box_type={box_type}"
            return redirect(redirect_url)
        
        # Handle other cases
        elif from_param == 'fsr':
            return redirect(reverse('fsr') + "?refresh=true")
        elif from_param == 'status_report':
            return redirect(reverse('friday_status_report') + "?refresh=true")
        else:
            # Fallback - try to use the next_url if available
            if next_url:
                return redirect(next_url)
            else:
                return redirect(reverse('fsr') + "?refresh=true")

@login_required
def fsr_comment_add(request, issues_id):
    if request.method == 'POST':
        # Get comment text from form
        comment_text = request.POST.get('issues_details_comment', '').strip()
        
        # Get navigation context efficiently
        next_url = request.POST.get('next', '')
        from_param = request.GET.get('from', '')
        
        # Build redirect URL early to avoid complex logic later
        if next_url:
            redirect_url = next_url
        elif from_param:
            redirect_url = reverse('fsr_details', args=[issues_id]) + f"?from={from_param}"
        else:
            redirect_url = reverse('fsr_details', args=[issues_id])
        
        # Validate comment exists
        if not comment_text:
            messages.error(request, "Comment cannot be empty")
            return redirect(redirect_url)
        
        # Get user info if authenticated
        user_initials = ''
        if request.user.is_authenticated:
            user_initials = f"{request.user.first_name[:1]}{request.user.last_name[:1]}"
        
        try:
            # Create the comment - single database operation
            issues_details.objects.create(
                issues_details_comment=comment_text,
                issues_details_user=user_initials,
                issues_details_date=date.today(),
                issues_id=issues_id
            )
            
            messages.success(request, "Comment added successfully")
            
        except Exception as e:
            messages.error(request, "Failed to add comment. Please try again.")
            
        # Use the pre-built redirect URL
        return redirect(redirect_url)
    
    # If not POST, redirect to details page
    return redirect('fsr_details', issues_id=issues_id)

def fsr_pdf(request):
    """
    Generate PDF version of FSR report
    """
    from django.db import connection
    
    try:
        context = get_fsr_context_data(request)
        return render_to_pdf('fsr_email.html', context)
    finally:
        # Close database connection
        connection.close()

def get_fsr_context_data(request):
    """
    Generate context data for Friday Status Report (used by both web view and email)
    Rewritten to use Django ORM instead of raw SQL
    """
    from django.db import connection
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        today = date.today()
        
        # Get max_comments parameter for summarized reports
        max_comments = request.GET.get('max_comments', None) if hasattr(request, 'GET') else None
        is_summarized_report = max_comments is not None
        
        if is_summarized_report:
            try:
                max_comments = int(max_comments)
            except (ValueError, TypeError):
                max_comments = None
                is_summarized_report = False
        
        # Get all properties ordered by country and name
        properties = props.objects.all().order_by('prop_country', 'prop_name').values('prop_name')
        
        # Get all issues with their details, using select_related and prefetch_related for optimization
        issues_queryset = issues.objects.select_related('prop').prefetch_related(
            Prefetch(
                'issues_details_set',
                queryset=issues_details.objects.all().order_by('-issues_details_id'),
                to_attr='details_list'
            )
        ).order_by('issues_id')
        
        # Process issues data
        issues_data = []
        for issue_obj in issues_queryset:
            # Build the issue dictionary
            issue_dict = {
                'prop_name': issue_obj.prop.prop_name,
                'issues_id': issue_obj.issues_id,
                'issues_heading': issue_obj.issues_heading,
                'issues_description': issue_obj.issues_description,
                'issues_status': issue_obj.issues_status,
                'issues_date_logged': issue_obj.issues_date_logged,
                'issues_resolution_date': issue_obj.issues_resolution_date,
                'days_to_resolve': None,
                'days_open': None,
                'details': []
            }
            
            # Calculate days metrics based on status
            if issue_dict['issues_date_logged']:
                if issue_dict['issues_status'] == 'Resolved':
                    if (issue_dict['issues_resolution_date'] and 
                        issue_dict['issues_resolution_date'] != date(1900, 1, 1)):
                        issue_dict['days_to_resolve'] = (issue_dict['issues_resolution_date'] - issue_dict['issues_date_logged']).days
                else:
                    issue_dict['days_open'] = (today - issue_dict['issues_date_logged']).days
            
            # Process details
            details_data = []
            for detail in issue_obj.details_list:
                details_data.append({
                    'issues_details_id': detail.issues_details_id,
                    'issues_details_comment': detail.issues_details_comment,
                    'issues_details_user': detail.issues_details_user,
                    'issues_details_date': detail.issues_details_date
                })
            
            # Apply comment limiting for summarized reports
            if is_summarized_report and max_comments and len(details_data) > max_comments:
                total_comments_before_limit = len(details_data)
                issue_dict['details'] = details_data[:max_comments]
                issue_dict['has_more_comments'] = True
                issue_dict['total_comments'] = total_comments_before_limit
            else:
                issue_dict['details'] = details_data
                issue_dict['has_more_comments'] = False
                issue_dict['total_comments'] = len(details_data)
            
            issues_data.append(issue_dict)
        
        # Process data by status and property
        processed_data = {}
        for status in ['Resolved', 'Unresolved', 'Issue']:
            processed_data[status] = {}
            for prop in properties:
                prop_name = prop['prop_name']
                processed_data[status][prop_name] = []

                unique_issues = set()

                for issue in issues_data:
                    if (issue['prop_name'] == prop_name and 
                        issue['issues_status'] == status and 
                        (issue['issues_heading'], issue['issues_description']) not in unique_issues):

                        if status == 'Resolved':
                            if (issue['issues_resolution_date'] != date(1900, 1, 1) and 
                                issue['issues_resolution_date'] >= (date.today() - timedelta(days=7))):
                                processed_data[status][prop_name].append(issue)
                                unique_issues.add((issue['issues_heading'], issue['issues_description']))
                        else:
                            processed_data[status][prop_name].append(issue)
                            unique_issues.add((issue['issues_heading'], issue['issues_description']))
        
        context = {
            'today': today,
            'statuses': ['Resolved', 'Unresolved', 'Issue'],
            'properties': properties,
            'is_summarized_report': is_summarized_report,
            'max_comments': max_comments,
            'status_groups': [
                {
                    'status': status,
                    'property_issues': [
                        {
                            'prop_name': prop['prop_name'],
                            'issues': processed_data[status][prop['prop_name']]
                        }
                        for prop in properties
                        if processed_data[status][prop['prop_name']]
                    ]
                }
                for status in ['Resolved', 'Unresolved', 'Issue']
            ]
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Error in get_fsr_context_data: {e}")
        # Return minimal context on error
        return {
            'today': date.today(),
            'statuses': ['Resolved', 'Unresolved', 'Issue'],
            'properties': [],
            'is_summarized_report': False,
            'max_comments': None,
            'status_groups': []
        }
        
    finally:
        # Close database connection
        connection.close()

@login_required
def fsr_notification(request):
    from django.db import connection
    from django.db.utils import OperationalError, InterfaceError
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    smtp_object = None
    
    # Close any stale connections before starting
    connection.close()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Check if there's a max_comments parameter in the session or request
            # This indicates the user wants a summarized report
            max_comments = None
            is_summarized_report = False
            
            # Check for max_comments in various places:
            # 1. Direct GET parameter (if coming from Friday report page)
            # 2. Session storage (if user navigated from a summarized report)
            # 3. HTTP_REFERER analysis (check if previous page had max_comments)
            
            if 'max_comments' in request.GET:
                max_comments = request.GET.get('max_comments')
                is_summarized_report = True
            elif 'last_report_type' in request.session:
                # If we stored the last report type in session
                if request.session['last_report_type'] == 'summarized':
                    max_comments = request.session.get('max_comments', '2')
                    is_summarized_report = True
            else:
                # Check the HTTP referer to see if it came from a summarized report
                referer = request.META.get('HTTP_REFERER', '')
                if 'max_comments=' in referer:
                    # Extract max_comments from referer URL
                    import re
                    match = re.search(r'max_comments=(\d+)', referer)
                    if match:
                        max_comments = match.group(1)
                        is_summarized_report = True
            
            # Validate max_comments
            if is_summarized_report and max_comments:
                try:
                    max_comments = int(max_comments)
                    if max_comments < 1:
                        max_comments = 2
                        is_summarized_report = False
                except (ValueError, TypeError):
                    max_comments = 2
                    is_summarized_report = False
            
            # Create a mock request object with the appropriate parameters for context generation
            mock_request = type('MockRequest', (), {})()
            mock_request.user = request.user
            mock_request.session = request.session
            mock_request.META = request.META
            
            if is_summarized_report:
                # Create GET parameters for summarized report
                mock_request.GET = {'max_comments': str(max_comments)}
                report_type_text = f"Summarized Report (Max {max_comments} comments per issue)"
            else:
                # No parameters for detailed report
                mock_request.GET = {}
                report_type_text = "Detailed Report (All comments)"
            
            # Fetch context data for the report with appropriate parameters
            # This is the critical database operation that needs protection
            context = get_fsr_context_data(mock_request)
            
            # Add report type information to context for email template
            context['is_summarized_report'] = is_summarized_report
            context['max_comments'] = max_comments if is_summarized_report else None
            context['report_type_text'] = report_type_text
            
            # Render HTML content
            html_content = render_to_string("fsr_email.html", context, request=request)
            text_content = strip_tags(html_content)
            
            # Determine recipients based on user permissions
            if request.user.is_superuser:
                # Supervisor: Send to Stella
                to_email = "stella.simitopoulos@alivente.com"
            else:
                # Non-supervisor: Send to Demetri
                to_email = "demetrimanias@gmail.com"
            
            # Always CC angmaniasbakers
            cc_email = "angmaniasbakers@gmail.com"
            
            # Prepare email with report type in subject
            msg = MIMEMultipart("alternative")
            msg['From'] = "demetrimanias@gmail.com"
            msg['To'] = to_email
            msg['Cc'] = cc_email
            
            # Include report type in subject
            if is_summarized_report:
                msg['Subject'] = f"Friday Status Report - Summarized ({max_comments} comments/issue)"
            else:
                msg['Subject'] = "Friday Status Report - Detailed"
            
            # Attach both plain text and HTML
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Get email credentials and settings from environment variables
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
            
            if not email_password:
                logger.error('❌ EMAIL_PASSWORD environment variable not set')
                messages.error(request, "Failed to send email - No password configured.")
                return redirect('fsr')
            
            # SMTP setup with environment variable configuration
            if email_use_ssl:
                # Use SSL connection (typically port 465)
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
            else:
                # Use regular SMTP connection (typically port 587)
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()
            
            email = "demetrimanias@gmail.com"
            smtp_object.login(email, email_password)
            
            # Send email to both To and CC recipients
            recipients = [to_email, cc_email]
            smtp_object.sendmail(email, recipients, msg.as_string())
            
            success_message = f"Friday Status Report ({report_type_text}) sent successfully!"
            messages.success(request, success_message)
            
            # If we get here, everything worked - break out of retry loop
            break
            
        except (OperationalError, InterfaceError) as e:
            if attempt < max_retries - 1:
                # Close connection and wait before retry
                connection.close()
                time.sleep(2)  # Wait 2 seconds before retry
                logger.warning(f"Database connection error on attempt {attempt + 1}, retrying: {e}")
                continue
            else:
                # Final attempt failed
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                messages.error(request, "Database connection error. Please try again in a moment.")
                return redirect('fsr')
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            messages.error(request, "Failed to send email - Authentication error.")
            break
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            messages.error(request, "Failed to send email - SMTP error.")
            break
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            messages.error(request, f"Failed to send email notification: {str(e)}")
            break
            
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except:
                    pass
            # Close database connection
            connection.close()
    
    return redirect('fsr')

### REPORTS - DASHBOARD (FROM HOME PAGE) ###
# Add these views to your views.py file
@login_required
def revenue_details_view(request):
    """
    View to show revenue details breakdown for budgeted/fixed revenues
    """
    year = request.GET.get('year', datetime.now().year)  # Just for display
    month = request.GET.get('month')
    line_type = request.GET.get('line_type')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    properties = request.GET.get('properties', '')  # NEW: Handle comma-separated properties
    
    # Get all revenue records (no year filtering needed for budgeted revenues)
    revenues = revenue.objects.all().select_related('prop', 'revenue_line_types', 'revenue_types')
    
    # Filter by line type if specified
    if line_type:
        revenues = revenues.filter(revenue_line_types_id=line_type)
    
    # Filter by property - UPDATED LOGIC
    if properties:  # NEW: Handle comma-separated properties
        try:
            property_ids = [int(prop_id.strip()) for prop_id in properties.split(',') if prop_id.strip()]
            revenues = revenues.filter(prop_id__in=property_ids)
        except ValueError:
            pass  # Invalid property IDs, show no results
    elif property_id and property_id != 'all':
        revenues = revenues.filter(prop_id=property_id)
    elif prop and prop != 'all':
        revenues = revenues.filter(prop_id=prop)
    
    # Get line type name for header
    line_type_name = "Revenue"
    if line_type:
        try:
            line_type_obj = revenue_line_types.objects.get(revenue_line_types_id=line_type)
            line_type_name = line_type_obj.revenue_line_types_name
        except revenue_line_types.DoesNotExist:
            line_type_name = "Unknown"
    
    # Get month name for subtitle
    month_names = {
        '1': 'January', '2': 'February', '3': 'March', '4': 'April',
        '5': 'May', '6': 'June', '7': 'July', '8': 'August',
        '9': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    month_name = month_names.get(str(month), "All Months") if month else "All Months"
    
    # Create a list of revenue items with monthly breakdown
    revenue_items = []
    total_amount = 0
    
    for rev in revenues:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for i, month_name_field in enumerate(months, 1):
            month_value = getattr(rev, f'revenue_{month_name_field}', 0)
            
            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue
                
                revenue_items.append({
                    'revenue_id': rev.revenue_id,
                    'property': rev.prop,
                    'amount': float(month_value),
                })
                total_amount += float(month_value)
    
    context = {
        'revenue_items': revenue_items,
        'total_amount': total_amount,
        'selected_year': year,
        'selected_month': month,
        'selected_line_type': line_type,
        'line_type_name': line_type_name,
        'month_name': month_name,
    }
    
    return render(request, 'revenue_details.html', context)

@login_required
def budget_expense_details_view(request):
    """
    View to show budgeted expense details breakdown
    """
    year = request.GET.get('year', datetime.now().year)  # Just for display
    month = request.GET.get('month')
    line_type = request.GET.get('line_type')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    properties = request.GET.get('properties', '')  # NEW: Handle comma-separated properties
    
    # Get all budgeted expense records (no year filtering needed for budgeted expenses)
    expenses = expense.objects.all().select_related('prop', 'expense_line_types', 'expense_types')
    
    # Filter by line type if specified
    if line_type:
        expenses = expenses.filter(expense_line_types_id=line_type)
    
    # Filter by property - UPDATED LOGIC
    if properties:  # NEW: Handle comma-separated properties
        try:
            property_ids = [int(prop_id.strip()) for prop_id in properties.split(',') if prop_id.strip()]
            expenses = expenses.filter(prop_id__in=property_ids)
        except ValueError:
            pass  # Invalid property IDs, show no results
    elif property_id and property_id != 'all':
        expenses = expenses.filter(prop_id=property_id)
    elif prop and prop != 'all':
        expenses = expenses.filter(prop_id=prop)
    
    # Get line type name for header
    line_type_name = "Budget Expenses"
    if line_type:
        try:
            line_type_obj = expense_line_types.objects.get(expense_line_types_id=line_type)
            line_type_name = line_type_obj.expense_line_types_name
        except expense_line_types.DoesNotExist:
            line_type_name = "Unknown"
    
    # Get month name for subtitle
    month_names = {
        '1': 'January', '2': 'February', '3': 'March', '4': 'April',
        '5': 'May', '6': 'June', '7': 'July', '8': 'August',
        '9': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    month_name = month_names.get(str(month), "All Months") if month else "All Months"
    
    # Create a list of expense items with monthly breakdown
    expense_items = []
    total_amount = 0
    
    for exp in expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for i, month_field in enumerate(months, 1):
            month_value = getattr(exp, f'expense_{month_field}', 0)
            
            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue
                
                expense_items.append({
                    'expense_id': exp.expense_id,
                    'property': exp.prop,
                    'amount': float(month_value),
                })
                total_amount += float(month_value)
    
    context = {
        'expense_items': expense_items,
        'total_amount': total_amount,
        'selected_year': year,
        'selected_month': month,
        'selected_line_type': line_type,
        'line_type_name': line_type_name,
        'month_name': month_name,
    }
    
    return render(request, 'budget_expense_details.html', context)

@login_required
def total_expense_details_view(request):
    """
    View to show combined actual + budgeted expense details
    """
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    
    # Get actual expenses
    actual_expenses = act_expense.objects.filter(
        act_expense_date__year=year
    ).select_related('prop')
    
    # Get budget expenses
    budget_expenses = expense.objects.filter(
        expense_types__expense_types_name__icontains=str(year)
    ).select_related('prop', 'expense_line_types', 'expense_types')
    
    # Filter by month if specified
    if month:
        actual_expenses = actual_expenses.filter(act_expense_date__month=month)
    
    # Filter by property
    if property_id:
        actual_expenses = actual_expenses.filter(prop_id=property_id)
        budget_expenses = budget_expenses.filter(prop_id=property_id)
    elif prop != 'all':
        actual_expenses = actual_expenses.filter(prop_id=prop)
        budget_expenses = budget_expenses.filter(prop_id=prop)
    
    # Order by date
    actual_expenses = actual_expenses.order_by('-act_expense_date')
    
    # Create budget expense items with monthly breakdown (similar to budget_expense_details_view)
    budget_expense_items = []
    for exp in budget_expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        for i, month_name in enumerate(months, 1):
            month_value = getattr(exp, f'expense_{month_name}', 0)
            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue
                    
                budget_expense_items.append({
                    'expense_id': exp.expense_id,
                    'property': exp.prop,
                    'expense_line_type': exp.expense_line_types,
                    'expense_type': exp.expense_types,
                    'month': i,
                    'month_name': month_name.capitalize(),
                    'amount': month_value,
                    'description': f"{exp.expense_line_types.expense_line_types_name} - {month_name.capitalize()} {year}",
                    'type': 'budget'
                })
    
    # Get line types and properties for context
    expense_line_types_list = expense_line_types.objects.all()
    properties = props.objects.all()
    
    context = {
        'actual_expenses': actual_expenses,
        'budget_expense_items': budget_expense_items,
        'expense_line_types': expense_line_types_list,
        'properties': properties,
        'selected_year': year,
        'selected_month': month,
        'selected_property': property_id,
        'prop': prop,
    }
    
    return render(request, 'total_expense_details.html', context)

@login_required
def finance_pl(request):
    # Get selected properties from request
    selected_properties = request.GET.getlist('properties')
    
    # Get all active properties with prefetched prop_values to optimize queries
    all_properties = props.objects.filter(prop_status="Active").prefetch_related('prop_values_set')
    
    # If no properties selected, return empty data
    if not selected_properties:
        # Return minimal context with empty data
        context = {
            'properties': [],
            'all_properties': all_properties,
            'revenue_line_types': revenue_line_types.objects.all(),
            'expense_line_types': expense_line_types.objects.all(),
            'revenue_totals': {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                             'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0, 'year': 0},
            'expense_totals': {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                             'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0, 'year': 0},
            'profit_totals': {'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
                            'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0, 'year': 0},
            'revenue_totals_by_line': {'all': {}},
            'expense_totals_by_line': {'all': {}},
            'revenue_prop_totals': {},
            'expense_prop_totals': {},
            'total_current_value': 0,
            'selected_properties': selected_properties,
        }
        return render(request, 'finance_pl.html', context)
    
    # Convert to integers and filter
    selected_prop_ids = [int(pid) for pid in selected_properties if pid.isdigit()]
    properties = all_properties.filter(prop_id__in=selected_prop_ids)
    
    # Revenue Section
    revenue_line_types_list = revenue_line_types.objects.all()
    
    # Filter revenues by selected properties only
    revenues = revenue.objects.filter(prop_id__in=selected_prop_ids)
    
    # Calculate revenue totals for selected properties
    revenue_totals = {
        'jan': sum(r.revenue_jan or 0 for r in revenues),
        'feb': sum(r.revenue_feb or 0 for r in revenues),
        'mar': sum(r.revenue_mar or 0 for r in revenues),
        'apr': sum(r.revenue_apr or 0 for r in revenues),
        'may': sum(r.revenue_may or 0 for r in revenues),
        'jun': sum(r.revenue_jun or 0 for r in revenues),
        'jul': sum(r.revenue_jul or 0 for r in revenues),
        'aug': sum(r.revenue_aug or 0 for r in revenues),
        'sep': sum(r.revenue_sep or 0 for r in revenues),
        'oct': sum(r.revenue_oct or 0 for r in revenues),
        'nov': sum(r.revenue_nov or 0 for r in revenues),
        'dec': sum(r.revenue_dec or 0 for r in revenues),
    }
    revenue_totals['year'] = sum(revenue_totals.values())
    
    # Calculate revenue totals by line type for selected properties
    revenue_totals_by_line = {'all': {}}
    for lt in revenue_line_types_list:
        line_revenues = revenues.filter(revenue_line_types=lt)
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in line_revenues),
            'feb': sum(r.revenue_feb or 0 for r in line_revenues),
            'mar': sum(r.revenue_mar or 0 for r in line_revenues),
            'apr': sum(r.revenue_apr or 0 for r in line_revenues),
            'may': sum(r.revenue_may or 0 for r in line_revenues),
            'jun': sum(r.revenue_jun or 0 for r in line_revenues),
            'jul': sum(r.revenue_jul or 0 for r in line_revenues),
            'aug': sum(r.revenue_aug or 0 for r in line_revenues),
            'sep': sum(r.revenue_sep or 0 for r in line_revenues),
            'oct': sum(r.revenue_oct or 0 for r in line_revenues),
            'nov': sum(r.revenue_nov or 0 for r in line_revenues),
            'dec': sum(r.revenue_dec or 0 for r in line_revenues),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        revenue_totals_by_line['all'][lt.revenue_line_types_id] = monthly_totals
    
    # Calculate property-specific revenue totals for selected properties
    revenue_prop_totals = {}
    for prop in properties:
        prop_revenues = revenues.filter(prop=prop)
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in prop_revenues),
            'feb': sum(r.revenue_feb or 0 for r in prop_revenues),
            'mar': sum(r.revenue_mar or 0 for r in prop_revenues),
            'apr': sum(r.revenue_apr or 0 for r in prop_revenues),
            'may': sum(r.revenue_may or 0 for r in prop_revenues),
            'jun': sum(r.revenue_jun or 0 for r in prop_revenues),
            'jul': sum(r.revenue_jul or 0 for r in prop_revenues),
            'aug': sum(r.revenue_aug or 0 for r in prop_revenues),
            'sep': sum(r.revenue_sep or 0 for r in prop_revenues),
            'oct': sum(r.revenue_oct or 0 for r in prop_revenues),
            'nov': sum(r.revenue_nov or 0 for r in prop_revenues),
            'dec': sum(r.revenue_dec or 0 for r in prop_revenues),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        revenue_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific revenue line type totals
        revenue_totals_by_line[prop.prop_id] = {}
        for lt in revenue_line_types_list:
            prop_line_revenues = prop_revenues.filter(revenue_line_types=lt)
            line_monthly_totals = {
                'jan': sum(r.revenue_jan or 0 for r in prop_line_revenues),
                'feb': sum(r.revenue_feb or 0 for r in prop_line_revenues),
                'mar': sum(r.revenue_mar or 0 for r in prop_line_revenues),
                'apr': sum(r.revenue_apr or 0 for r in prop_line_revenues),
                'may': sum(r.revenue_may or 0 for r in prop_line_revenues),
                'jun': sum(r.revenue_jun or 0 for r in prop_line_revenues),
                'jul': sum(r.revenue_jul or 0 for r in prop_line_revenues),
                'aug': sum(r.revenue_aug or 0 for r in prop_line_revenues),
                'sep': sum(r.revenue_sep or 0 for r in prop_line_revenues),
                'oct': sum(r.revenue_oct or 0 for r in prop_line_revenues),
                'nov': sum(r.revenue_nov or 0 for r in prop_line_revenues),
                'dec': sum(r.revenue_dec or 0 for r in prop_line_revenues),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            revenue_totals_by_line[prop.prop_id][lt.revenue_line_types_id] = line_monthly_totals

    # Expense Section
    expense_line_types_list = expense_line_types.objects.all()
    
    # Filter expenses by selected properties only
    expenses = expense.objects.filter(prop_id__in=selected_prop_ids)
    
    # Calculate expense totals for selected properties
    expense_totals = {
        'jan': sum(e.expense_jan or 0 for e in expenses),
        'feb': sum(e.expense_feb or 0 for e in expenses),
        'mar': sum(e.expense_mar or 0 for e in expenses),
        'apr': sum(e.expense_apr or 0 for e in expenses),
        'may': sum(e.expense_may or 0 for e in expenses),
        'jun': sum(e.expense_jun or 0 for e in expenses),
        'jul': sum(e.expense_jul or 0 for e in expenses),
        'aug': sum(e.expense_aug or 0 for e in expenses),
        'sep': sum(e.expense_sep or 0 for e in expenses),
        'oct': sum(e.expense_oct or 0 for e in expenses),
        'nov': sum(e.expense_nov or 0 for e in expenses),
        'dec': sum(e.expense_dec or 0 for e in expenses),
    }
    expense_totals['year'] = sum(expense_totals.values())
    
    # Calculate expense totals by line type for selected properties
    expense_totals_by_line = {'all': {}}
    for elt in expense_line_types_list:
        line_expenses = expenses.filter(expense_line_types=elt)
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in line_expenses),
            'feb': sum(e.expense_feb or 0 for e in line_expenses),
            'mar': sum(e.expense_mar or 0 for e in line_expenses),
            'apr': sum(e.expense_apr or 0 for e in line_expenses),
            'may': sum(e.expense_may or 0 for e in line_expenses),
            'jun': sum(e.expense_jun or 0 for e in line_expenses),
            'jul': sum(e.expense_jul or 0 for e in line_expenses),
            'aug': sum(e.expense_aug or 0 for e in line_expenses),
            'sep': sum(e.expense_sep or 0 for e in line_expenses),
            'oct': sum(e.expense_oct or 0 for e in line_expenses),
            'nov': sum(e.expense_nov or 0 for e in line_expenses),
            'dec': sum(e.expense_dec or 0 for e in line_expenses),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        expense_totals_by_line['all'][elt.expense_line_types_id] = monthly_totals
    
    # Calculate property-specific expense totals for selected properties
    expense_prop_totals = {}
    for prop in properties:
        prop_expenses = expenses.filter(prop=prop)
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in prop_expenses),
            'feb': sum(e.expense_feb or 0 for e in prop_expenses),
            'mar': sum(e.expense_mar or 0 for e in prop_expenses),
            'apr': sum(e.expense_apr or 0 for e in prop_expenses),
            'may': sum(e.expense_may or 0 for e in prop_expenses),
            'jun': sum(e.expense_jun or 0 for e in prop_expenses),
            'jul': sum(e.expense_jul or 0 for e in prop_expenses),
            'aug': sum(e.expense_aug or 0 for e in prop_expenses),
            'sep': sum(e.expense_sep or 0 for e in prop_expenses),
            'oct': sum(e.expense_oct or 0 for e in prop_expenses),
            'nov': sum(e.expense_nov or 0 for e in prop_expenses),
            'dec': sum(e.expense_dec or 0 for e in prop_expenses),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        expense_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific expense line type totals
        expense_totals_by_line[prop.prop_id] = {}
        for elt in expense_line_types_list:
            prop_line_expenses = prop_expenses.filter(expense_line_types=elt)
            line_monthly_totals = {
                'jan': sum(e.expense_jan or 0 for e in prop_line_expenses),
                'feb': sum(e.expense_feb or 0 for e in prop_line_expenses),
                'mar': sum(e.expense_mar or 0 for e in prop_line_expenses),
                'apr': sum(e.expense_apr or 0 for e in prop_line_expenses),
                'may': sum(e.expense_may or 0 for e in prop_line_expenses),
                'jun': sum(e.expense_jun or 0 for e in prop_line_expenses),
                'jul': sum(e.expense_jul or 0 for e in prop_line_expenses),
                'aug': sum(e.expense_aug or 0 for e in prop_line_expenses),
                'sep': sum(e.expense_sep or 0 for e in prop_line_expenses),
                'oct': sum(e.expense_oct or 0 for e in prop_line_expenses),
                'nov': sum(e.expense_nov or 0 for e in prop_line_expenses),
                'dec': sum(e.expense_dec or 0 for e in prop_line_expenses),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            expense_totals_by_line[prop.prop_id][elt.expense_line_types_id] = line_monthly_totals

    # Calculate Profit (Revenue - Expenses) for selected properties
    profit_totals = {
        'jan': revenue_totals['jan'] - expense_totals['jan'],
        'feb': revenue_totals['feb'] - expense_totals['feb'],
        'mar': revenue_totals['mar'] - expense_totals['mar'],
        'apr': revenue_totals['apr'] - expense_totals['apr'],
        'may': revenue_totals['may'] - expense_totals['may'],
        'jun': revenue_totals['jun'] - expense_totals['jun'],
        'jul': revenue_totals['jul'] - expense_totals['jul'],
        'aug': revenue_totals['aug'] - expense_totals['aug'],
        'sep': revenue_totals['sep'] - expense_totals['sep'],
        'oct': revenue_totals['oct'] - expense_totals['oct'],
        'nov': revenue_totals['nov'] - expense_totals['nov'],
        'dec': revenue_totals['dec'] - expense_totals['dec'],
        'year': revenue_totals['year'] - expense_totals['year']
    }

    # Prepare property values mapping for easy access in template
    prop_values_map = {prop.prop_id: prop.prop_values_set.first() for prop in properties}
    total_current_value = 0
    for prop in properties:
        prop_values = prop.prop_values_set.first()
        if prop_values and prop_values.prop_values_current_value is not None:
            total_current_value += prop_values.prop_values_current_value

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'properties': [{'id': p.prop_id, 'name': p.prop_name} for p in properties],
            'revenue_totals': revenue_totals,
            'expense_totals': expense_totals,
            'profit_totals': profit_totals,
            'selected_properties': selected_properties,
        })

    context = {
        'properties': properties,
        'all_properties': all_properties,  # For the property selector
        'revenue_line_types': revenue_line_types_list,
        'revenue_totals': revenue_totals,
        'revenue_totals_by_line': revenue_totals_by_line,
        'revenue_prop_totals': revenue_prop_totals,
        'expense_line_types': expense_line_types_list,
        'expense_totals': expense_totals,
        'expense_totals_by_line': expense_totals_by_line,
        'expense_prop_totals': expense_prop_totals,
        'profit_totals': profit_totals,
        'prop_values_map': prop_values_map,
        'total_current_value': total_current_value,
        'selected_properties': selected_properties,
    }
    
    return render(request, 'finance_pl.html', context)

@login_required
def finance_pl_act(request):
    # Get selected year from request (default to 'budget')
    selected_year = request.GET.get('year', 'budget')
    
    # Get selected properties from request
    selected_properties = request.GET.getlist('properties')

    # Handle year parameter - can be 'budget' or a year number
    if selected_year != 'budget':
        try:
            selected_year = int(selected_year)
            # Ensure only 2024 or 2025 is selectable
            if selected_year not in [2024, 2025]:
                selected_year = 'budget'
        except (ValueError, TypeError):
            selected_year = 'budget'
    
    # FULLY OPTIMIZED: Single query with comprehensive prefetching
    all_properties = props.objects.filter(prop_status="Active").select_related().prefetch_related(
        'prop_values_set',  # Simplified - no explicit queryset
        Prefetch('revenue_set', queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types')),
        Prefetch('expense_set', queryset=expense.objects.select_related('expense_line_types', 'expense_types'))
    )
    
    # If no properties selected, default to ALL properties
    if not selected_properties:
        selected_properties = [str(prop.prop_id) for prop in all_properties]
    
    # Convert to integers and filter
    selected_prop_ids = [int(pid) for pid in selected_properties if pid.isdigit()]
    properties = all_properties.filter(prop_id__in=selected_prop_ids)
    
    # OPTIMIZED: Single queries for line types
    revenue_line_types_list = list(revenue_line_types.objects.all())
    expense_line_types_list = list(expense_line_types.objects.all())
    
    # OPTIMIZED: Use prefetched data instead of separate queries
    revenues = []
    expenses = []
    
    for prop in properties:
        revenues.extend(prop.revenue_set.all())
        expenses.extend(prop.expense_set.all())
    
    # ========= REVENUE SECTION ========= (optimized calculations)
    revenue_totals = {
        'jan': sum(r.revenue_jan or 0 for r in revenues),
        'feb': sum(r.revenue_feb or 0 for r in revenues),
        'mar': sum(r.revenue_mar or 0 for r in revenues),
        'apr': sum(r.revenue_apr or 0 for r in revenues),
        'may': sum(r.revenue_may or 0 for r in revenues),
        'jun': sum(r.revenue_jun or 0 for r in revenues),
        'jul': sum(r.revenue_jul or 0 for r in revenues),
        'aug': sum(r.revenue_aug or 0 for r in revenues),
        'sep': sum(r.revenue_sep or 0 for r in revenues),
        'oct': sum(r.revenue_oct or 0 for r in revenues),
        'nov': sum(r.revenue_nov or 0 for r in revenues),
        'dec': sum(r.revenue_dec or 0 for r in revenues),
    }
    revenue_totals['year'] = sum(revenue_totals.values())
    
    # OPTIMIZED: Pre-group revenues by line type
    revenues_by_line_type = {}
    for rev in revenues:
        line_type_id = rev.revenue_line_types.revenue_line_types_id
        if line_type_id not in revenues_by_line_type:
            revenues_by_line_type[line_type_id] = []
        revenues_by_line_type[line_type_id].append(rev)
    
    # Calculate revenue totals by line type
    revenue_totals_by_line = {'all': {}}
    for lt in revenue_line_types_list:
        line_revenues = revenues_by_line_type.get(lt.revenue_line_types_id, [])
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in line_revenues),
            'feb': sum(r.revenue_feb or 0 for r in line_revenues),
            'mar': sum(r.revenue_mar or 0 for r in line_revenues),
            'apr': sum(r.revenue_apr or 0 for r in line_revenues),
            'may': sum(r.revenue_may or 0 for r in line_revenues),
            'jun': sum(r.revenue_jun or 0 for r in line_revenues),
            'jul': sum(r.revenue_jul or 0 for r in line_revenues),
            'aug': sum(r.revenue_aug or 0 for r in line_revenues),
            'sep': sum(r.revenue_sep or 0 for r in line_revenues),
            'oct': sum(r.revenue_oct or 0 for r in line_revenues),
            'nov': sum(r.revenue_nov or 0 for r in line_revenues),
            'dec': sum(r.revenue_dec or 0 for r in line_revenues),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        revenue_totals_by_line['all'][lt.revenue_line_types_id] = monthly_totals
    
    # OPTIMIZED: Pre-group revenues by property
    revenues_by_property = {}
    for rev in revenues:
        prop_id = rev.prop.prop_id
        if prop_id not in revenues_by_property:
            revenues_by_property[prop_id] = []
        revenues_by_property[prop_id].append(rev)
    
    # Calculate property-specific revenue totals
    revenue_prop_totals = {}
    for prop in properties:
        prop_revenues = revenues_by_property.get(prop.prop_id, [])
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in prop_revenues),
            'feb': sum(r.revenue_feb or 0 for r in prop_revenues),
            'mar': sum(r.revenue_mar or 0 for r in prop_revenues),
            'apr': sum(r.revenue_apr or 0 for r in prop_revenues),
            'may': sum(r.revenue_may or 0 for r in prop_revenues),
            'jun': sum(r.revenue_jun or 0 for r in prop_revenues),
            'jul': sum(r.revenue_jul or 0 for r in prop_revenues),
            'aug': sum(r.revenue_aug or 0 for r in prop_revenues),
            'sep': sum(r.revenue_sep or 0 for r in prop_revenues),
            'oct': sum(r.revenue_oct or 0 for r in prop_revenues),
            'nov': sum(r.revenue_nov or 0 for r in prop_revenues),
            'dec': sum(r.revenue_dec or 0 for r in prop_revenues),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        revenue_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific revenue line type totals
        revenue_totals_by_line[prop.prop_id] = {}
        for lt in revenue_line_types_list:
            prop_line_revenues = [r for r in prop_revenues if r.revenue_line_types.revenue_line_types_id == lt.revenue_line_types_id]
            line_monthly_totals = {
                'jan': sum(r.revenue_jan or 0 for r in prop_line_revenues),
                'feb': sum(r.revenue_feb or 0 for r in prop_line_revenues),
                'mar': sum(r.revenue_mar or 0 for r in prop_line_revenues),
                'apr': sum(r.revenue_apr or 0 for r in prop_line_revenues),
                'may': sum(r.revenue_may or 0 for r in prop_line_revenues),
                'jun': sum(r.revenue_jun or 0 for r in prop_line_revenues),
                'jul': sum(r.revenue_jul or 0 for r in prop_line_revenues),
                'aug': sum(r.revenue_aug or 0 for r in prop_line_revenues),
                'sep': sum(r.revenue_sep or 0 for r in prop_line_revenues),
                'oct': sum(r.revenue_oct or 0 for r in prop_line_revenues),
                'nov': sum(r.revenue_nov or 0 for r in prop_line_revenues),
                'dec': sum(r.revenue_dec or 0 for r in prop_line_revenues),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            revenue_totals_by_line[prop.prop_id][lt.revenue_line_types_id] = line_monthly_totals

    # ========= EXPENSE SECTION ========= (optimized)
    # Initialize actual expense totals
    actual_expense_totals = {
        'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0, 'year': 0
    }
    
    # FULLY OPTIMIZED: Actual expenses with single aggregate query
    actual_expense_prop_totals = {}
    if selected_year != 'budget':
        from django.db.models import Sum
        
        # Single query to get all actual expenses with month grouping
        actual_expenses_aggregated = act_expense.objects.filter(
            act_expense_date__year=selected_year,
            act_expense_approved="Yes",
            act_expense_paid="Yes",
            prop_id__in=selected_prop_ids
        ).values('prop_id', 'act_expense_date__month').annotate(
            total_amount=Sum('act_expense_amount')
        ).order_by('prop_id', 'act_expense_date__month')
        
        # Calculate monthly totals for all properties in one pass
        month_mapping = {
            1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', 6: 'jun',
            7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dec'
        }
        
        # Initialize all property totals
        for prop in properties:
            actual_expense_prop_totals[prop.prop_id] = {month: 0 for month in month_mapping.values()}
            actual_expense_prop_totals[prop.prop_id]['year'] = 0
        
        # Process aggregated results
        for result in actual_expenses_aggregated:
            prop_id = result['prop_id']
            month_num = result['act_expense_date__month']
            amount = result['total_amount'] or 0
            
            if prop_id in actual_expense_prop_totals:
                month_name = month_mapping[month_num]
                actual_expense_prop_totals[prop_id][month_name] = amount
                actual_expense_prop_totals[prop_id]['year'] += amount
        
        # Calculate overall monthly totals
        for month_name in month_mapping.values():
            actual_expense_totals[month_name] = sum(
                actual_expense_prop_totals[prop.prop_id][month_name] 
                for prop in properties
            )
        
        actual_expense_totals['year'] = sum(actual_expense_totals.values())
    
    # Calculate budgeted expense totals
    expense_totals = {
        'jan': sum(e.expense_jan or 0 for e in expenses),
        'feb': sum(e.expense_feb or 0 for e in expenses),
        'mar': sum(e.expense_mar or 0 for e in expenses),
        'apr': sum(e.expense_apr or 0 for e in expenses),
        'may': sum(e.expense_may or 0 for e in expenses),
        'jun': sum(e.expense_jun or 0 for e in expenses),
        'jul': sum(e.expense_jul or 0 for e in expenses),
        'aug': sum(e.expense_aug or 0 for e in expenses),
        'sep': sum(e.expense_sep or 0 for e in expenses),
        'oct': sum(e.expense_oct or 0 for e in expenses),
        'nov': sum(e.expense_nov or 0 for e in expenses),
        'dec': sum(e.expense_dec or 0 for e in expenses),
    }
    expense_totals['year'] = sum(expense_totals.values())
    
    # OPTIMIZED: Pre-group expenses by line type
    expenses_by_line_type = {}
    for exp in expenses:
        line_type_id = exp.expense_line_types.expense_line_types_id
        if line_type_id not in expenses_by_line_type:
            expenses_by_line_type[line_type_id] = []
        expenses_by_line_type[line_type_id].append(exp)
    
    # Calculate expense totals by line type
    expense_totals_by_line = {'all': {}}
    for elt in expense_line_types_list:
        line_expenses = expenses_by_line_type.get(elt.expense_line_types_id, [])
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in line_expenses),
            'feb': sum(e.expense_feb or 0 for e in line_expenses),
            'mar': sum(e.expense_mar or 0 for e in line_expenses),
            'apr': sum(e.expense_apr or 0 for e in line_expenses),
            'may': sum(e.expense_may or 0 for e in line_expenses),
            'jun': sum(e.expense_jun or 0 for e in line_expenses),
            'jul': sum(e.expense_jul or 0 for e in line_expenses),
            'aug': sum(e.expense_aug or 0 for e in line_expenses),
            'sep': sum(e.expense_sep or 0 for e in line_expenses),
            'oct': sum(e.expense_oct or 0 for e in line_expenses),
            'nov': sum(e.expense_nov or 0 for e in line_expenses),
            'dec': sum(e.expense_dec or 0 for e in line_expenses),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        expense_totals_by_line['all'][elt.expense_line_types_id] = monthly_totals
    
    # OPTIMIZED: Pre-group expenses by property
    expenses_by_property = {}
    for exp in expenses:
        prop_id = exp.prop.prop_id
        if prop_id not in expenses_by_property:
            expenses_by_property[prop_id] = []
        expenses_by_property[prop_id].append(exp)
    
    # Calculate property-specific expense totals
    expense_prop_totals = {}
    for prop in properties:
        prop_expenses = expenses_by_property.get(prop.prop_id, [])
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in prop_expenses),
            'feb': sum(e.expense_feb or 0 for e in prop_expenses),
            'mar': sum(e.expense_mar or 0 for e in prop_expenses),
            'apr': sum(e.expense_apr or 0 for e in prop_expenses),
            'may': sum(e.expense_may or 0 for e in prop_expenses),
            'jun': sum(e.expense_jun or 0 for e in prop_expenses),
            'jul': sum(e.expense_jul or 0 for e in prop_expenses),
            'aug': sum(e.expense_aug or 0 for e in prop_expenses),
            'sep': sum(e.expense_sep or 0 for e in prop_expenses),
            'oct': sum(e.expense_oct or 0 for e in prop_expenses),
            'nov': sum(e.expense_nov or 0 for e in prop_expenses),
            'dec': sum(e.expense_dec or 0 for e in prop_expenses),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        expense_prop_totals[prop.prop_id] = monthly_totals
        
        # Add property-specific expense line type totals
        expense_totals_by_line[prop.prop_id] = {}
        for elt in expense_line_types_list:
            prop_line_expenses = [e for e in prop_expenses if e.expense_line_types.expense_line_types_id == elt.expense_line_types_id]
            line_monthly_totals = {
                'jan': sum(e.expense_jan or 0 for e in prop_line_expenses),
                'feb': sum(e.expense_feb or 0 for e in prop_line_expenses),
                'mar': sum(e.expense_mar or 0 for e in prop_line_expenses),
                'apr': sum(e.expense_apr or 0 for e in prop_line_expenses),
                'may': sum(e.expense_may or 0 for e in prop_line_expenses),
                'jun': sum(e.expense_jun or 0 for e in prop_line_expenses),
                'jul': sum(e.expense_jul or 0 for e in prop_line_expenses),
                'aug': sum(e.expense_aug or 0 for e in prop_line_expenses),
                'sep': sum(e.expense_sep or 0 for e in prop_line_expenses),
                'oct': sum(e.expense_oct or 0 for e in prop_line_expenses),
                'nov': sum(e.expense_nov or 0 for e in prop_line_expenses),
                'dec': sum(e.expense_dec or 0 for e in prop_line_expenses),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            expense_totals_by_line[prop.prop_id][elt.expense_line_types_id] = line_monthly_totals

    # ========= PROFIT CALCULATION =========
    if selected_year == 'budget':
        profit_totals = {
            'jan': revenue_totals['jan'] - expense_totals['jan'],
            'feb': revenue_totals['feb'] - expense_totals['feb'],
            'mar': revenue_totals['mar'] - expense_totals['mar'],
            'apr': revenue_totals['apr'] - expense_totals['apr'],
            'may': revenue_totals['may'] - expense_totals['may'],
            'jun': revenue_totals['jun'] - expense_totals['jun'],
            'jul': revenue_totals['jul'] - expense_totals['jul'],
            'aug': revenue_totals['aug'] - expense_totals['aug'],
            'sep': revenue_totals['sep'] - expense_totals['sep'],
            'oct': revenue_totals['oct'] - expense_totals['oct'],
            'nov': revenue_totals['nov'] - expense_totals['nov'],
            'dec': revenue_totals['dec'] - expense_totals['dec'],
            'year': revenue_totals['year'] - expense_totals['year']
        }
    else:
        profit_totals = {
            'jan': revenue_totals['jan'] - expense_totals['jan'] - actual_expense_totals['jan'],
            'feb': revenue_totals['feb'] - expense_totals['feb'] - actual_expense_totals['feb'],
            'mar': revenue_totals['mar'] - expense_totals['mar'] - actual_expense_totals['mar'],
            'apr': revenue_totals['apr'] - expense_totals['apr'] - actual_expense_totals['apr'],
            'may': revenue_totals['may'] - expense_totals['may'] - actual_expense_totals['may'],
            'jun': revenue_totals['jun'] - expense_totals['jun'] - actual_expense_totals['jun'],
            'jul': revenue_totals['jul'] - expense_totals['jul'] - actual_expense_totals['jul'],
            'aug': revenue_totals['aug'] - expense_totals['aug'] - actual_expense_totals['aug'],
            'sep': revenue_totals['sep'] - expense_totals['sep'] - actual_expense_totals['sep'],
            'oct': revenue_totals['oct'] - expense_totals['oct'] - actual_expense_totals['oct'],
            'nov': revenue_totals['nov'] - expense_totals['nov'] - actual_expense_totals['nov'],
            'dec': revenue_totals['dec'] - expense_totals['dec'] - actual_expense_totals['dec'],
            'year': revenue_totals['year'] - expense_totals['year'] - actual_expense_totals['year']
        }

    # FULLY OPTIMIZED: Property values using prefetched data - NO additional queries
    prop_values_map = {}
    total_current_value = 0
    
    for prop in properties:
        # Use the prefetched prop_values_set data
        prop_values_list = list(prop.prop_values_set.all())
        if prop_values_list:
            prop_values = prop_values_list[0]
            prop_values_map[prop.prop_id] = prop_values
            if prop_values.prop_values_current_value is not None:
                total_current_value += prop_values.prop_values_current_value
        else:
            prop_values_map[prop.prop_id] = None

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'properties': [{'id': p.prop_id, 'name': p.prop_name} for p in properties],
            'revenue_totals': revenue_totals,
            'expense_totals': expense_totals,
            'actual_expense_totals': actual_expense_totals,
            'profit_totals': profit_totals,
            'selected_properties': selected_properties,
        })

    return render(request, 'finance_pl_act.html', {
        'properties': properties,
        'all_properties': all_properties,
        'revenue_line_types': revenue_line_types_list,
        'revenue_totals': revenue_totals,
        'revenue_totals_by_line': revenue_totals_by_line,
        'revenue_prop_totals': revenue_prop_totals,
        'expense_line_types': expense_line_types_list,
        'expense_totals': expense_totals,
        'expense_totals_by_line': expense_totals_by_line,
        'expense_prop_totals': expense_prop_totals,
        'profit_totals': profit_totals,
        'prop_values_map': prop_values_map,
        'total_current_value': total_current_value,
        'actual_expense_totals': actual_expense_totals,
        'actual_expense_prop_totals': actual_expense_prop_totals,
        'selected_year': selected_year,
        'selected_properties': selected_properties,
        'available_years': [2025, 2024],
    })

@login_required
def petty_cash_rep(request):
	import petty_cash
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	petty_cash.petty_cash(rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def lease_agreements(request):
	import print_lease
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_lease.lease_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def title_deeds(request):
	import print_title
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_title.title_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def prop_rep(request):
	import print_prop
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_prop.prop_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def property_report(request, prop_id):
	today = date.today()
	property = get_object_or_404(props.objects.only(
    	'prop_id', 'prop_name', 'prop_address1', 'prop_address2', 'prop_suburb', 
		'prop_city', 'prop_province', 'prop_country', 'prop_pcode',
		'prop_floor_area', 'prop_year_built', 'prop_status',
		'prop_available_for_rent', 'prop_title_deed',
		'prop_title_deed_status', 'prop_electricity', 'prop_water',
		'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance'
	), pk=prop_id)
	context = {
		'today': today,
		'property': property,
	}
	return render(request, 'property_report.html', context)

@login_required
def title_deed_report(request, prop_id):
    property = get_object_or_404(props, pk=prop_id)
    
    if not property.prop_title_deed:
        return JsonResponse({'error': 'No title deed available for this property'}, status=404)
    
    # Return JSON with the file URL and type
    return JsonResponse({
        'file_url': property.prop_title_deed.url,
        'file_name': property.prop_title_deed.name.split('/')[-1],
        'file_type': property.prop_title_deed.name.split('.')[-1].lower()
    })

@login_required
def lease_agreement_report(request, tenant_id):
	today = date.today()
	tenant_obj = get_object_or_404(tenant.objects.only(
		'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number', 
		'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',
		'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
		'tenant_rent', 'tenant_levies',
		'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement'
	), pk=tenant_id)
	property = get_object_or_404(props.objects.only(
		'prop_id', 'prop_name', 'prop_address1', 'prop_address2', 'prop_suburb', 
		'prop_city', 'prop_province', 'prop_country', 'prop_pcode',
		'prop_floor_area', 'prop_year_built', 'prop_status',
		'prop_available_for_rent', 'prop_title_deed',
		'prop_title_deed_status', 'prop_electricity', 'prop_water',
		'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance'
	), pk=tenant_obj.prop_id)
	context = {
		'today': today,
		'tenant': tenant_obj,
		'property': property,
	}
	return render(request, 'lease_agreement_report.html', context)

@login_required
def tenant_report(request, tenant_id):
	today = date.today()
	tenant_obj = get_object_or_404(tenant.objects.only(
		'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number', 
		'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',
		'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
		'tenant_rent', 'tenant_levies',
		'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement'
	), pk=tenant_id)
	context = {
		'today': today,
		'tenant': tenant_obj,
	}
	return render(request, 'tenant_report.html', context)

@login_required
def supplier_report(request, supplier_id):
	today = date.today()
	supplier_obj = get_object_or_404(supplier.objects.only(
		'supplier_id', 'supplier_contact_person', 'supplier_contact_number', 
		'supplier_email', 'supplier_company_name', 'supplier_role',
		'supplier_country'
	), pk=supplier_id)
	context = {
		'today': today,
		'supplier': supplier_obj,
	}
	return render(request, 'supplier_report.html', context)

@login_required
def tenant_rep(request):
	import print_tenant
	prop = request.POST.get('propname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_tenant.tenant_report(prop, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def suppliers_rep(request):
	import print_supplier
	sup = request.POST.get('supname')
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	print_supplier.supplier_report(sup, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def fsr_rep(request):
	import fsr
	rep_type = request.POST.get('d_s')
	rep_output = request.POST.get('d_e')
	rep_date = date.today()
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	fsr.fsr_report(rep_type, rep_date, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def friday_status_report(request):
    from django.db import connection
    from django.db.utils import OperationalError, InterfaceError
    import time
    
    # Close any stale connections before starting
    connection.close()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            today = date.today()
            
            # Get max_comments parameter for summarized reports
            max_comments = request.GET.get('max_comments', None)
            is_summarized_report = max_comments is not None
            
            # Store report type in session for use by fsr_notification
            if is_summarized_report:
                try:
                    max_comments = int(max_comments)
                    request.session['last_report_type'] = 'summarized'
                    request.session['max_comments'] = max_comments
                except (ValueError, TypeError):
                    max_comments = None
                    is_summarized_report = False
                    request.session['last_report_type'] = 'detailed'
                    request.session.pop('max_comments', None)
            else:
                request.session['last_report_type'] = 'detailed'
                request.session.pop('max_comments', None)
            
            # OPTIMIZED APPROACH: Process data in smaller chunks
            
            # 1. Get properties first (lightweight query)
            properties = list(props.objects.all().order_by('prop_country', 'prop_name').values('prop_id', 'prop_name'))
            
            # 2. Get issues in smaller batches
            all_issues = []
            batch_size = 50  # Process 50 issues at a time
            
            # Get total count first
            total_issues = issues.objects.count()
            
            for offset in range(0, total_issues, batch_size):
                # Get a batch of issues with minimal related data
                issues_batch = issues.objects.select_related('prop').filter(
                ).order_by('issues_id')[offset:offset + batch_size]
                
                for issue_obj in issues_batch:
                    # Build basic issue data
                    issue_dict = {
                        'prop_name': issue_obj.prop.prop_name,
                        'issues_id': issue_obj.issues_id,
                        'issues_heading': issue_obj.issues_heading,
                        'issues_description': issue_obj.issues_description,
                        'issues_status': issue_obj.issues_status,
                        'issues_date_logged': issue_obj.issues_date_logged,
                        'issues_resolution_date': issue_obj.issues_resolution_date,
                        'days_to_resolve': None,
                        'days_open': None,
                        'details': [],
                        'has_more_comments': False,
                        'total_comments': 0
                    }
                    
                    # Calculate days metrics
                    if issue_dict['issues_date_logged']:
                        if issue_dict['issues_status'] == 'Resolved':
                            if (issue_dict['issues_resolution_date'] and 
                                issue_dict['issues_resolution_date'] != date(1900, 1, 1)):
                                issue_dict['days_to_resolve'] = (issue_dict['issues_resolution_date'] - issue_dict['issues_date_logged']).days
                        else:
                            issue_dict['days_open'] = (today - issue_dict['issues_date_logged']).days
                    
                    # Get details separately for this issue
                    if is_summarized_report and max_comments:
                        # For summarized reports, get limited details
                        details_queryset = issues_details.objects.filter(
                            issues_id=issue_obj.issues_id
                        ).order_by('-issues_details_id')[:max_comments + 1]  # Get one extra to check if there are more
                        
                        details_list = list(details_queryset)
                        
                        if len(details_list) > max_comments:
                            # There are more comments than the limit
                            issue_dict['details'] = [{
                                'issues_details_id': detail.issues_details_id,
                                'issues_details_comment': detail.issues_details_comment,
                                'issues_details_user': detail.issues_details_user,
                                'issues_details_date': detail.issues_details_date
                            } for detail in details_list[:max_comments]]
                            issue_dict['has_more_comments'] = True
                            issue_dict['total_comments'] = issues_details.objects.filter(issues_id=issue_obj.issues_id).count()
                        else:
                            issue_dict['details'] = [{
                                'issues_details_id': detail.issues_details_id,
                                'issues_details_comment': detail.issues_details_comment,
                                'issues_details_user': detail.issues_details_user,
                                'issues_details_date': detail.issues_details_date
                            } for detail in details_list]
                            issue_dict['has_more_comments'] = False
                            issue_dict['total_comments'] = len(details_list)
                    else:
                        # For detailed reports, get all details
                        details_queryset = issues_details.objects.filter(
                            issues_id=issue_obj.issues_id
                        ).order_by('-issues_details_id')
                        
                        issue_dict['details'] = [{
                            'issues_details_id': detail.issues_details_id,
                            'issues_details_comment': detail.issues_details_comment,
                            'issues_details_user': detail.issues_details_user,
                            'issues_details_date': detail.issues_details_date
                        } for detail in details_queryset]
                        issue_dict['has_more_comments'] = False
                        issue_dict['total_comments'] = len(issue_dict['details'])
                    
                    all_issues.append(issue_dict)
                
                # Small pause between batches to prevent overwhelming the DB
                time.sleep(0.1)
            
            # 3. Process data by status and property
            processed_data = {}
            cutoff_date = today - timedelta(days=7)
            
            for status in ['Resolved', 'Unresolved', 'Issue']:
                processed_data[status] = {}
                for prop in properties:
                    prop_name = prop['prop_name']
                    processed_data[status][prop_name] = []
                    
                    unique_issues = set()
                    
                    for issue in all_issues:
                        if (issue['prop_name'] == prop_name and 
                            issue['issues_status'] == status and 
                            (issue['issues_heading'], issue['issues_description']) not in unique_issues):
                            
                            # For Resolved issues, check if:
                            # 1. Resolved within last 7 days, OR
                            # 2. Has a comment added within last 7 days
                            if status == 'Resolved':
                                show_issue = False
                                
                                # Check if resolved within last 7 days
                                if (issue['issues_resolution_date'] and
                                    issue['issues_resolution_date'] != date(1900, 1, 1) and 
                                    issue['issues_resolution_date'] >= cutoff_date):
                                    show_issue = True
                                
                                # Check if any comment was added within last 7 days
                                if not show_issue and issue['details']:
                                    for detail in issue['details']:
                                        if (detail['issues_details_date'] and 
                                            detail['issues_details_date'] >= cutoff_date):
                                            show_issue = True
                                            break
                                
                                if show_issue:
                                    processed_data[status][prop_name].append(issue)
                                    unique_issues.add((issue['issues_heading'], issue['issues_description']))
                            else:
                                processed_data[status][prop_name].append(issue)
                                unique_issues.add((issue['issues_heading'], issue['issues_description']))
            
            # 4. Build context
            context = {
                'today': today,
                'statuses': ['Resolved', 'Unresolved', 'Issue'],
                'properties': [{'prop_name': prop['prop_name']} for prop in properties],
                'is_summarized_report': is_summarized_report,
                'max_comments': max_comments,
                'status_groups': [
                    {
                        'status': status,
                        'property_issues': [
                            {
                                'prop_name': prop['prop_name'],
                                'issues': processed_data[status][prop['prop_name']]
                            }
                            for prop in properties
                            if processed_data[status][prop['prop_name']]
                        ]
                    }
                    for status in ['Resolved', 'Unresolved', 'Issue']
                ]
            }
            
            return render(request, 'friday_status_report.html', context)
            
        except (OperationalError, InterfaceError) as e:
            if attempt < max_retries - 1:
                connection.close()
                time.sleep(3)  # Increased wait time
                continue
            else:
                messages.error(request, "Database connection error. Please try again in a moment.")
                return redirect('fsr')
        except Exception as e:
            messages.error(request, f"An error occurred while generating the report: {str(e)}")
            return redirect('fsr')

@login_required
def resolved_issues_report(request):
    # Get dates from GET parameters
    f_date_str = request.GET.get('f_date')
    t_date_str = request.GET.get('t_date')

    # Validate dates
    if not f_date_str or not t_date_str:
        messages.error(request, "Both date ranges are required")
        return redirect('fsr')

    try:
        f_date = parse_date(f_date_str)
        t_date = parse_date(t_date_str)
        
        if not f_date or not t_date:
            raise ValueError("Invalid date format")
            
        if t_date < f_date:
            messages.error(request, "End date cannot be before start date")
            return redirect('fsr')

    except (ValueError, TypeError) as e:
        messages.error(request, f"Invalid date format: {str(e)}")
        return redirect('fsr')

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    prop.prop_name, 
                    issues.issues_heading, 
                    issues.issues_description, 
                    issues.issues_status,
                    issues_details.issues_details_comment,
                    issues_details.issues_details_user,
                    issues_details.issues_details_date,
                    issues.issues_resolution_date,
                    issues.issues_date_logged
                FROM 
                    prop
                    JOIN issues ON prop.prop_id = issues.prop_id
                    JOIN issues_details ON issues.issues_id = issues_details.issues_id
                WHERE 
                    issues.issues_status = 'Resolved'
                    AND issues.issues_resolution_date BETWEEN %s AND %s
                ORDER BY 
                    prop.prop_name ASC,
                    issues.issues_heading ASC,
                    issues_details.issues_details_date DESC
            """, [f_date_str, t_date_str])

            rows = cursor.fetchall()

        # Helper function to parse dates
        def parse_db_date(date_value):
            if isinstance(date_value, date):
                return date_value
            elif isinstance(date_value, str):
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            elif isinstance(date_value, datetime):
                return date_value.date()
            else:
                raise ValueError(f"Unsupported date format: {type(date_value)}")

        # Structure the data
        properties = defaultdict(lambda: {
            'prop_name': '',
            'issues': defaultdict(list)
        })

        for row in rows:
            prop_name = row[0]
            issue_heading = row[1]
            
            try:
                resolution_date = parse_db_date(row[7])
                date_logged = parse_db_date(row[8])
                days_to_resolve = (resolution_date - date_logged).days
            except Exception as e:
                days_to_resolve = 0  # Default value if date parsing fails

            properties[prop_name]['prop_name'] = prop_name
            properties[prop_name]['issues'][issue_heading].append({
                'issues_description': row[2],
                'comment': row[4],
                'user': row[5],
                'comment_date': row[6],
                'resolution_date': row[7],
                'date_logged': row[8],
                'days_to_resolve': days_to_resolve
            })

        # Convert to list format for template
        properties_list = []
        for prop_name, prop_data in properties.items():
            issues_list = []
            for issue_heading, comments in prop_data['issues'].items():
                issues_list.append({
                    'heading': issue_heading,
                    'description': comments[0]['issues_description'],
                    'issues_date_logged': comments[0]['date_logged'],
                    'issues_resolution_date': comments[0]['resolution_date'],
                    'days_to_resolve': comments[0]['days_to_resolve'],
                    'comments': sorted(comments, key=lambda x: x['comment_date'], reverse=True)[:20]
                })

            properties_list.append({
                'prop_name': prop_name,
                'issues': sorted(issues_list, key=lambda x: x['heading'])
            })

        context = {
            'f_date': f_date_str,
            't_date': t_date_str,
            'properties': sorted(properties_list, key=lambda x: x['prop_name'])
        }

        return render(request, 'resolved_issues_report.html', context)

    except Exception as e:
        messages.error(request, f"Error generating report: {str(e)}")
        return redirect('fsr')

@login_required
def issues_rep(request):
	import issues
	f_d = request.POST.get('from_date')
	f_date = datetime.strptime(f_d, "%Y-%m-%d")
	from_date = f_date.date()
	t_d = request.POST.get('to_date')
	t_date = datetime.strptime(t_d, "%Y-%m-%d")
	to_date = t_date.date()
	rep_output = request.POST.get('d_e')
	rep_date = date.today()
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	issues.issues_report(from_date, to_date, rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def open_invoices(request):
	import open_invoices
	rep_output = request.POST.get('d_e')
	check = 'No'
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	open_invoices.open_invoices(rep_output, check, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

@login_required
def open_invoices_report(request):
    
    today = date.today()
    properties_with_invoices = []
    
    # Get all current tenants with their property details
    current_tenants = tenant.objects.filter(
        tenant_current='Yes'
    ).select_related('prop').order_by('prop__prop_country', 'prop__prop_name')
    
    # Get all unpaid invoices with tenant details in one query
    unpaid_invoices = invoices.objects.filter(
        invoice_paid='No'
    ).select_related('tenant', 'tenant__prop').order_by('invoice_date')
    
    # Process detailed invoice breakdown
    for tenant_obj in current_tenants:
        tenant_invoices = []
        
        # Get unpaid invoices for this tenant
        tenant_unpaid_invoices = [inv for inv in unpaid_invoices if inv.tenant.tenant_id == tenant_obj.tenant_id]
        
        for invoice_obj in tenant_unpaid_invoices:
            payment_terms = tenant_obj.tenant_payment_terms or 0
            due_date = invoice_obj.invoice_date + timedelta(days=payment_terms)
            days_overdue = (today - due_date).days if today > due_date else 0
            
            tenant_invoices.append({
                'invoice_id': invoice_obj.invoice_id,
                'invoice_date': invoice_obj.invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'overdue': days_overdue > 0
            })
        
        # Only include tenants with unpaid invoices
        if tenant_invoices:
            properties_with_invoices.append({
                'prop_name': tenant_obj.prop.prop_name,
                'prop_country': tenant_obj.prop.prop_country,
                'tenant_id': tenant_obj.tenant_id,
                'tenant_name': tenant_obj.tenant_name,
                'tenant_contact_person': tenant_obj.tenant_contact_person,
                'tenant_contact_number': tenant_obj.tenant_contact_number,
                'tenant_email': tenant_obj.tenant_email,
                'tenant_rent': tenant_obj.tenant_rent,
                'tenant_payment_terms': tenant_obj.tenant_payment_terms,
                'invoices': tenant_invoices
            })
    
    # Calculate Debtors Age Analysis
    debtors_age_analysis = []
    totals = {
        'total_outstanding': 0,
        'current_0_30': 0,
        'past_due_31_60': 0,
        'past_due_61_90': 0,
        'past_due_91_plus': 0
    }
    
    for tenant_obj in current_tenants:
        tenant_analysis = {
            'tenant_name': tenant_obj.tenant_name,
            'tenant_id': tenant_obj.tenant_id,  # Add tenant_id here too
            'total_outstanding': 0,
            'current_0_30': 0,
            'past_due_31_60': 0,
            'past_due_61_90': 0,
            'past_due_91_plus': 0
        }
        
        # Get unpaid invoices for this tenant
        tenant_unpaid_invoices = [inv for inv in unpaid_invoices if inv.tenant.tenant_id == tenant_obj.tenant_id]
        
        # Calculate aging for this tenant's invoices
        for invoice_obj in tenant_unpaid_invoices:
            payment_terms = tenant_obj.tenant_payment_terms or 0
            due_date = invoice_obj.invoice_date + timedelta(days=payment_terms)
            days_overdue = (today - due_date).days if today > due_date else 0
            amount = float(tenant_obj.tenant_rent or 0)
            
            tenant_analysis['total_outstanding'] += amount
            
            if days_overdue <= 30:
                # Current (0-30 days - includes not yet due and up to 30 days overdue)
                tenant_analysis['current_0_30'] += amount
            elif 31 <= days_overdue <= 60:
                # Past due 31-60 days
                tenant_analysis['past_due_31_60'] += amount
            elif 61 <= days_overdue <= 90:
                # Past due 61-90 days
                tenant_analysis['past_due_61_90'] += amount
            else:
                # Past due 91+ days
                tenant_analysis['past_due_91_plus'] += amount
        
        # Only include tenants with outstanding invoices
        if tenant_analysis['total_outstanding'] > 0:
            debtors_age_analysis.append(tenant_analysis)
            
            # Add to totals
            totals['total_outstanding'] += tenant_analysis['total_outstanding']
            totals['current_0_30'] += tenant_analysis['current_0_30']
            totals['past_due_31_60'] += tenant_analysis['past_due_31_60']
            totals['past_due_61_90'] += tenant_analysis['past_due_61_90']
            totals['past_due_91_plus'] += tenant_analysis['past_due_91_plus']
    
    # Sort debtors by total outstanding (highest first)
    debtors_age_analysis.sort(key=lambda x: x['total_outstanding'], reverse=True)

    context = {
        'today': today.strftime('%Y-%m-%d'),
        'properties_with_invoices': properties_with_invoices,
        'debtors_age_analysis': debtors_age_analysis,
        'totals': totals
    }
    
    return render(request, 'open_invoices_report.html', context)

@login_required
def lease_renewal_report(request):
    
    today = date.today()
    tenants_for_renewal = []
    vacant_properties = []
    declined_renewals = []
    
    # Get all active tenants with their property details using select_related for efficiency
    active_tenants = tenant.objects.filter(
        tenant_current='Yes'
    ).select_related('prop').order_by('prop__prop_country', 'prop__prop_name')
    
    # Get list of property names that have active tenants
    prop_active_tenant = list(active_tenants.values_list('prop__prop_name', flat=True))
    
    # Get all active properties available for rent
    active_properties = props.objects.filter(
        prop_status='Active',
        prop_available_for_rent='Yes'
    ).order_by('prop_country', 'prop_name')
    
    # Process each active tenant for renewal logic
    for tenant_obj in active_tenants:
        lease_end_date = tenant_obj.tenant_lease_end_date
        renewal_period = tenant_obj.tenant_renewal_period or 30  # Default to 30 days if None
        
        if lease_end_date:  # Make sure lease_end_date exists
            renewal_date = lease_end_date - timedelta(days=renewal_period)
            warning_date = renewal_date
#           This was for the old notification which was 30 days before the renewal date
#           warning_date = renewal_date - timedelta(days=30)
            renewal_status = tenant_obj.tenant_renewal_status or 'pending'  # Default to pending
            
            if today >= warning_date:
                if renewal_status == 'pending':
                    # Normal renewal case - add to tenants list
                    tenants_for_renewal.append({
                        'prop_name': tenant_obj.prop.prop_name,
                        'prop_country': tenant_obj.prop.prop_country,
                        'tenant_type': tenant_obj.tenant_type,
                        'tenant_name': tenant_obj.tenant_name,
                        'tenant_contact_person': tenant_obj.tenant_contact_person,
                        'tenant_contact_number': tenant_obj.tenant_contact_number,
                        'tenant_email': tenant_obj.tenant_email,
                        'tenant_deposit': tenant_obj.tenant_deposit,
                        'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                        'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                        'tenant_rental_type': tenant_obj.tenant_rental_type,
                        'tenant_renewal': tenant_obj.tenant_renewal,
                        'tenant_renewal_period': tenant_obj.tenant_renewal_period,
                        'tenant_rent': tenant_obj.tenant_rent,
                        'tenant_levies': tenant_obj.tenant_levies,
                        'tenant_payment_terms': tenant_obj.tenant_payment_terms,
                        'renewal_date': renewal_date.strftime('%Y-%m-%d'),
                        'needs_renewal': True
                    })
                elif renewal_status == 'declined':
                    # Tenant declined renewal - add to declined_renewals list
                    declined_renewals.append({
                        'prop_name': tenant_obj.prop.prop_name,
                        'tenant_name': tenant_obj.tenant_name,
                        'lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                        'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT'
                    })
                # If renewal_status == 'new_lease_signed', do nothing (exclude from report)
    
    # Find vacant properties (properties without active tenants)
    vacant_properties = []
    for prop in active_properties:
        if prop.prop_name not in prop_active_tenant:
            vacant_properties.append({
                'prop_name': prop.prop_name,
                'prop_country': prop.prop_country
            })
    
    context = {
        'tenants': tenants_for_renewal,
        'vacant_properties': vacant_properties,
        'declined_renewals': declined_renewals,
        'today': today.strftime('%Y-%m-%d')
    }
    return render(request, 'lease_renewal_report.html', context)

@login_required
def lease_renewal(request):
	import lease_renewal
	rep_output = request.POST.get('d_e')
	check = 'No'
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	lease_renewal.lease_renewal(rep_output, check, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')


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

def logout_user(request):
    logout(request)
    messages.success(request, ('You Have Succefully Logged Out.'))
    return redirect('home')
