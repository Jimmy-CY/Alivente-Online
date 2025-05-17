from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import connection
from django.db.models import Q, Prefetch
from django.http import HttpResponse, HttpResponseServerError, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.cache import never_cache
from django.views.static import serve
from . import forms
from .forms import PropForm, TenantForm, PettyForm, InvoicesForm, IssuesForm, DetailsForm, SupplierForm, ValuesForm, RevenueTypesForm, RevenueLineForm, RevenueForm, ExpenseTypesForm, ExpenseLineForm, ExpenseForm 
from .models import props, petty, issues, issues_details, tenant, invoices, supplier, prop_values, revenue_types, revenue_line_types, revenue, expense_types, expense_line_types, expense
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlparse, parse_qs
import mysql.connector
import os
import re
import uuid
import logging

logger = logging.getLogger(__name__)

### HOME ###
def home(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.filter(tenant_current="Yes")
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "home.html", {"props":results, "tenant":tresults, "supplier":sresults})

### ADMIN ###
def admin_apms(request):
    results = props.objects.all().order_by('prop_country', 'prop_name')
    tresults = tenant.objects.select_related('prop').all().order_by('tenant_name')
    return render(request, "admin_apms.html", {
        "props": results, 
        "tenant": tresults
    })

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

def admin_clear(request):
	import os
	import glob
	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/*.pdf"
	files = glob.glob(file_path)
	for f in files:
		os.remove(f)
	return redirect("admin_apms")

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

def admin_invoices(request):
	import open_invoices
	today = date.today()
	months = ('Month','January','February','March','April','May','June','July','August','September','October','November','December')
	open_invoices.create_invoices(months[today.month],today.year)
	return redirect("admin_apms")

### FINANCE ###
def finance(request):
#	return redirect("finance")
	return render (request, "finance.html", {})

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

def finance_revenue_add(request):
    props_data = props.objects.all().order_by('prop_country', 'prop_name')
    revenue_types_list = revenue_types.objects.all()  # Fetch all revenue types
    revenue_line_types_list = revenue_line_types.objects.all()  # Fetch all revenue line types

    return render(request, "finance_revenue_add.html", {
        "props_data": props_data,
        "revenue_types": revenue_types_list,  # Pass to template
        "revenue_line_types": revenue_line_types_list,  # Pass to template
    })

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

def finance_revenue_types(request):
    rev_types = revenue_types.objects.all()
    return render(request, "finance_revenue_types.html", {
        "rtresults": rev_types,
    })

def finance_revenue_types_add(request):
    rev_types = revenue_types.objects.all().order_by('revenue_types_name')
    return render(request, "finance_revenue_types_add.html", {"rtresults":rev_types})

def finance_revenue_types_commit(request):
    if request.method == "POST":
        form = RevenueTypesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Types Added Successfully")
    rev_types = revenue_types.objects.all()
    return render(request, "finance_revenue_types.html", {"rtresults":rev_types})

def finance_revenue_types_edit(request, revenue_types_id):
    rev_types = revenue_types.objects.filter(pk=revenue_types_id)
    return render(request, "finance_revenue_types_edit.html", {"rtresults":rev_types})

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

def finance_revenue_line_types(request):
    rev_line_types = revenue_line_types.objects.all()
    return render(request, "finance_revenue_line_types.html", {
        "rltresults": rev_line_types,
    })

def finance_revenue_line_types_add(request):
    rev_line_types = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    return render(request, "finance_revenue_line_types_add.html", {"rltresults":rev_line_types})

def finance_revenue_line_types_commit(request):
    if request.method == "POST":
        form = RevenueLineForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Revenue Line Types Added Successfully")
    rev_line_types = revenue_line_types.objects.all()
    return render(request, "finance_revenue_line_types.html", {"rltresults":rev_line_types})

def finance_revenue_line_types_edit(request, revenue_line_types_id):
    rev_line_types = revenue_line_types.objects.filter(pk=revenue_line_types_id)
    return render(request, "finance_revenue_line_types_edit.html", {"rltresults":rev_line_types})

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

def finance_expense_types(request):
    exp_types = expense_types.objects.all()
    return render(request, "finance_expense_types.html", {
        "etresults": exp_types,
    })

def finance_expense_types_add(request):
    exp_types = expense_types.objects.all().order_by('expense_types_name')
    return render(request, "finance_expense_types_add.html", {"etresults":exp_types})

def finance_expense_types_commit(request):
    if request.method == "POST":
        form = ExpenseTypesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Types Added Successfully")
    exp_types = expense_types.objects.all()
    return render(request, "finance_expense_types.html", {"etresults":exp_types})

def finance_expense_types_edit(request, expense_types_id):
    exp_types = expense_types.objects.filter(pk=expense_types_id)
    return render(request, "finance_expense_types_edit.html", {"etresults":exp_types})

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

def finance_expense_line_types(request):
    exp_line_types = expense_line_types.objects.all().order_by('expense_line_types_name')
    return render(request, "finance_expense_line_types.html", {
        "eltresults": exp_line_types,
    })

def finance_expense_line_types_add(request):
    exp_line_types = expense_line_types.objects.all()
    return render(request, "finance_expense_line_types_add.html", {"eltresults":exp_line_types})

def finance_expense_line_types_commit(request):
    if request.method == "POST":
        form = ExpenseLineForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense Line Type Added Successfully")
    exp_line_types = expense_line_types.objects.all()
    return render(request, "finance_expense_line_types.html", {"eltresults":exp_line_types})

def finance_expense_line_types_edit(request, expense_line_types_id):
    exp_line_types = expense_line_types.objects.filter(pk=expense_line_types_id)
    return render(request, "finance_expense_line_types_edit.html", {"eltresults":exp_line_types})

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

def finance_valuations_add(request):
	results = props.objects.all().order_by('prop_country', 'prop_name')
	vresults = prop_values.objects.all()
	context = {
		'props': results,
		'prop_values': vresults,
	}
	return render(request, "finance_valuations_add.html", context)

def finance_valuations_commit(request):
    if request.method == "POST":
        form = ValuesForm(request.POST)  # Remove 'or None'
        if form.is_valid():
            form.save()
            messages.success(request, "Valuation Added Successfully")
            return redirect('finance_valuations')  # Redirect after success
        else:
            print(form.errors.as_data())
            messages.error(request, "Please correct the errors below")
    
    # For GET requests or failed POSTs
    results = props.objects.all().order_by('prop_country','prop_name')
    vresults = prop_values.objects.all().order_by('prop_values_purchase_price')    
    
    pur_balance = sum(x.prop_values_purchase_price for x in vresults if x.prop_values_purchase_price is not None)
    cur_balance = sum(x.prop_values_current_value for x in vresults if x.prop_values_current_value is not None)

    context = {
        'pur_balance': pur_balance,
        'cur_balance': cur_balance,        
        'props': results,
        'prop_values': vresults,
        'form_data': request.POST if request.method == "POST" else None  # Preserve form data
    }
    return render(request, "finance_valuations.html", context)

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
def tenant_page(request):
	prop_output = request.POST.get('propname')
	tenant_output = request.POST.get('tenantname')
	active_output = request.POST.get('act')
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	if tenant_output is None:
		tresults = tenant.objects.all().order_by('tenant_name')
		if active_output is None:
			tresults = tenant.objects.all().order_by('tenant_name')
		elif active_output == "All":
			tresults = tenant.objects.all().order_by('tenant_name')
		else:
			tresults = tenant.objects.filter(tenant_current=active_output)
	elif tenant_output == "All":
		tresults = tenant.objects.all().order_by('tenant_name')
		if active_output is None:
			tresults = tenant.objects.all().order_by('tenant_name')
		elif active_output == "All":
			tresults = tenant.objects.all().order_by('tenant_name')
		else:
			tresults = tenant.objects.filter(tenant_current=active_output)
	else:
		tresults = tenant.objects.filter(tenant_name=tenant_output)
	if prop_output is None:
		results = props.objects.all().order_by('prop_country','prop_name')
	elif prop_output == "All":
		results = props.objects.all().order_by('prop_country','prop_name')
	else:
		results = props.objects.filter(prop_name=prop_output)
	return render (request, "tenant.html", {"tenant":tresults, "props":results})

def tenant_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	return render(request, "tenant_add.html", {"props":results, "tenant":tresults})

def tenant_edit(request, tenant_id):
	tresults = tenant.objects.filter(pk=tenant_id)
	results = props.objects.all().order_by('prop_country','prop_name')
	return render (request, "tenant_edit.html", {"props":results, "tenant":tresults})

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

### SUPPLIERS ###
def suppliers(request):
	sup_output = request.POST.get('supname')
	sup_count = request.POST.get('supcount')
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	if sup_output is None and sup_count is None:
		sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	elif sup_output == "All" or sup_count == "All":
		sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	else:
		if sup_output is not None:
			sresults = supplier.objects.filter(supplier_contact_person=sup_output)
		elif sup_count is not None:
			sresults = supplier.objects.filter(supplier_country=sup_count)
	return render (request, "suppliers.html", {"supplier":sresults})

def suppliers_add(request):
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render(request, "suppliers_add.html", {"supplier":sresults})

def suppliers_edit(request, supplier_id):
	sresults = supplier.objects.filter(pk=supplier_id)
	return render (request, "suppliers_edit.html", {"supplier":sresults})

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

def suppliers_edit_commit(request, supplier_id):
	sup = supplier.objects.get(pk=supplier_id)
	if request.method == "POST":
		form = SupplierForm(request.POST or None, instance=sup)
		if form.is_valid():
			form.save()
			messages.success(request, "Supplier Edited Successfully")
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "suppliers.html", {"supplier":sresults})


### INVOICES ###
def invoices_page(request):
	prop_output = request.POST.get('propname')
	tenant_output = request.POST.get('tenantname')
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	iresults = invoices.objects.filter(invoice_paid="No").order_by('invoice_date')
	if tenant_output is None:
		tresults = tenant.objects.all().order_by('tenant_name')
	elif tenant_output == "All":
		tresults = tenant.objects.all().order_by('tenant_name')
	else:
		tresults = tenant.objects.filter(tenant_name=tenant_output)
	if prop_output is None:
		results = props.objects.all().order_by('prop_country','prop_name')
	elif prop_output == "All":
		results = props.objects.all().order_by('prop_country','prop_name')
	else:
		results = props.objects.filter(prop_name=prop_output)
	return render (request, "invoices.html", {"invoices":iresults, "tenant":tresults, "props":results})

def invoices_commit(request, invoice_id):
	inv_tbp = invoices.objects.filter(pk=invoice_id).update(invoice_paid="Yes")
	return redirect('invoices')


### PROPERTIES ###
def properties_page(request):
	prop_output = request.POST.get('propname')
	country_output = request.POST.get('country')
	active_output = request.POST.get('act')
	results = props.objects.all().order_by('prop_country','prop_name')
	if prop_output is None and active_output is None and country_output is None:
		results = props.objects.all().order_by('prop_country','prop_name')
	elif prop_output == "All" or active_output == "All" or country_output == "All":
		results = props.objects.all().order_by('prop_country','prop_name')
	else:
		if prop_output is not None:
			results = props.objects.filter(prop_name=prop_output)
		elif country_output is not None:
			results = props.objects.filter(prop_country=country_output)
		elif active_output is not None:
			results = props.objects.filter(prop_status=active_output)
	return render (request, "properties.html", {"props":results})

def properties_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	existing_names = list(props.objects.values_list('prop_name', flat=True))
	return render(request, "properties_add.html", {"props":results, "existing_names": existing_names})

def properties_commit(request):
	if request.method == "POST":
		form = PropForm(request.POST or None)
		if form.is_valid():
			form.save()
	results = props.objects.all().order_by('prop_country','prop_name')
	messages.success(request, "Property Added Successfully")
	return render (request, "properties.html", {"props":results})

def properties_edit(request, prop_id):
    # Get the current property being edited
    current_property = get_object_or_404(props, pk=prop_id)
    
    # Get all other property names (excluding the current one)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)
    
    return render(request, "properties_edit.html", {
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names)  # Add this for client-side validation
    })

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

### PETTY CASH ###
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

def petty_cash_add(request):
	presults = petty.objects.all().order_by('petty_cash_date')
	return render(request, "petty_cash_add.html", {"petty":presults})


### ISSUES - FRIDAY STATUS REPORT ###
def fsr(request):
	prop_output = request.POST.get('propname')
	country_output = request.POST.get('propcountry')
	active_output = request.POST.get('issuestatus')
	results = props.objects.all().order_by('prop_country','prop_name')
	if prop_output is None and active_output is None and country_output is None:
		results = props.objects.all().order_by('prop_country','prop_name')
		isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
		idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
	elif prop_output == "All" or active_output == "All" or country_output == "All":
		results = props.objects.all().order_by('prop_country','prop_name')
		isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
		idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
	else:
		if country_output is not None:
			results = props.objects.filter(prop_country=country_output).order_by('prop_country','prop_name')
			isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
			idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
		elif prop_output is not None:
			results = props.objects.filter(prop_name=prop_output).order_by('prop_country','prop_name')
			isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
			idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
		elif active_output is not None:
			isresults = issues.objects.filter(issues_status=active_output).order_by('issues_date_logged','issues_status')
			results = props.objects.all().order_by('prop_country','prop_name')
			idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
	return render(request, "fsr.html", {"props":results, "issues":isresults, "issues_details":idresults})

def fsr_add(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
	idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
	log_date = date.today()
	return render(request, "fsr_add.html", {"props":results, "issues":isresults, "issues_details":idresults, "log_date":log_date})

def fsr_commit(request):
    if request.method == "POST":
        form = IssuesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Issue Added Successfully")
    temp_results = issues.objects.all().order_by('-issues_id')
    is_id = temp_results[0].issues_id
    return redirect(reverse("fsr_details", args=[is_id]) + "?from=fsr_add&origin=fsr")

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

def fsr_commit_status_change(request):
    if request.method == "POST":
        # Get form data
        issues_id = request.POST.get('issues_id')
        new_status = request.POST.get('issues_status')
        next_url = request.POST.get('next', '')
        
        # Update the issue
        issue = issues.objects.get(pk=issues_id)
        issue.issues_status = new_status
        if new_status == "Resolved":
            issue.issues_resolution_date = date.today()
        issue.save()
        
        # Parse the next URL to get parameters
        parsed_url = urlparse(next_url)
        params = parse_qs(parsed_url.query)
        from_param = params.get('from', ['fsr'])[0]
        
        # Determine redirect URL with refresh
        if from_param == 'fsr':
            return redirect(reverse('fsr') + "?refresh=true")
        elif from_param == 'status_report':
            return redirect(reverse('friday_status_report') + "?refresh=true")
        else:
            return redirect(reverse('fsr') + "?refresh=true")

#def fsr_comment_add(request, issues_id):
#	iss_det = request.POST.get('issues_details_comment')
#	if request.user.is_authenticated:
#		lname = request.user.last_name
#		fname = request.user.first_name
#		user_initials = fname[:1]+lname[:1]
#	comm_date = date.today()
#	print("YES", issues_id, comm_date, user_initials, iss_det)
#	issue_update=issues_details.objects.create (issues_details_comment=iss_det, issues_details_user=user_initials, issues_details_date=comm_date, issues_id=issues_id)
#	return redirect("fsr_details", issues_id)

def fsr_comment_add(request, issues_id):
    if request.method == 'POST':
        # Get comment text from form
        comment_text = request.POST.get('issues_details_comment', '').strip()
        
        # Validate comment exists
        if not comment_text:
            messages.error(request, "Comment cannot be empty")
            return redirect(reverse('fsr_details', args=[issues_id]) + f"?from={request.GET.get('from', '')}&referrer={request.GET.get('referrer', '')}")
        
        # Get user info if authenticated
        user_initials = ''
        if request.user.is_authenticated:
            user_initials = f"{request.user.first_name[:1]}{request.user.last_name[:1]}"
        
        # Create the comment
        issues_details.objects.create(
            issues_details_comment=comment_text,
            issues_details_user=user_initials,
            issues_details_date=date.today(),
            issues_id=issues_id
        )
        
        # Determine where to redirect back to
        redirect_url = request.POST.get('next', '')
        if not redirect_url:
            # Reconstruct the original URL with parameters
            from_param = request.GET.get('from', '')
            referrer = request.GET.get('referrer', '')
            if from_param and referrer:
                redirect_url = reverse('fsr_details', args=[issues_id]) + f"?from={from_param}&referrer={referrer}"
            else:
                redirect_url = reverse('fsr_details', args=[issues_id])
        
        messages.success(request, "Comment added successfully")
        return redirect(redirect_url)
    
    # If not POST, redirect to details page
    return redirect(reverse('fsr_details', args=[issues_id]))

### REPORTS - DASHBOARD (FROM HOME PAGE) ###
from django.shortcuts import render
from .models import props, revenue_line_types, revenue

def finance_pl(request):
    # Get all properties with prefetched prop_values to optimize queries
    properties = props.objects.all().prefetch_related('prop_values_set')
    
    # Revenue Section
    revenue_line_types_list = revenue_line_types.objects.all()
    revenues = revenue.objects.all()
    
    # Calculate revenue totals
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
    
    # Calculate revenue totals by line type for all properties
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
    
    # Calculate property-specific revenue totals
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
    expenses = expense.objects.all()
    
    # Calculate expense totals
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
    
    # Calculate expense totals by line type for all properties
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
    
    # Calculate property-specific expense totals
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

    # Calculate Profit (Revenue - Expenses)
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

    return render(request, 'finance_pl.html', {
        'properties': properties,
        'revenue_line_types': revenue_line_types_list,
        'revenue_totals': revenue_totals,
        'revenue_totals_by_line': revenue_totals_by_line,
        'revenue_prop_totals': revenue_prop_totals,
        'expense_line_types': expense_line_types_list,
        'expense_totals': expense_totals,
        'expense_totals_by_line': expense_totals_by_line,
        'expense_prop_totals': expense_prop_totals,
        'profit_totals': profit_totals,
        'prop_values_map': prop_values_map  # Add property values mapping to context
    })

def petty_cash_rep(request):
	import petty_cash
	rep_output = request.POST.get('d_e')
	if request.user.is_authenticated:
		email = request.user.email
		fname = request.user.first_name
	petty_cash.petty_cash(rep_output, email, fname)
	messages.success(request, "Report Created Successfully")
	return redirect('home')

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

def title_deed_report(request, prop_id):
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
	return render(request, 'title_deed_report.html', context)

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

def friday_status_report(request):
    mydb = mysql.connector.connect(
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
        auth_plugin=settings.DATABASES['default']['AUTH_PLUGIN'],
    )
    today = date.today()
    rep_date = today
    with mydb.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT prop.prop_name FROM prop ORDER BY prop.prop_country ASC, prop.prop_name ASC")
        properties = cursor.fetchall()
        cursor.execute("""
            SELECT 
                prop.prop_name,
                issues.issues_id, issues.issues_heading, issues.issues_description, 
                issues.issues_status, issues.issues_date_logged, issues.issues_resolution_date,
                issues_details.issues_details_id, issues_details.issues_details_comment, 
                issues_details.issues_details_user, issues_details.issues_details_date
            FROM issues
            JOIN prop ON prop.prop_id = issues.prop_id
            JOIN issues_details ON issues_details.issues_id = issues.issues_id
            ORDER BY issues.issues_id ASC, issues_details.issues_details_id DESC
        """)
        issues_data = cursor.fetchall()
    
    issues = []
    current_issue = None
    for row in issues_data:
        if current_issue is None or current_issue['issues_id'] != row['issues_id']:
            if current_issue is not None:
                issues.append(current_issue)
            current_issue = {
                'prop_name': row['prop_name'],
                'issues_id': row['issues_id'],
                'issues_heading': row['issues_heading'],
                'issues_description': row['issues_description'],
                'issues_status': row['issues_status'],
                'issues_date_logged': row['issues_date_logged'],
                'issues_resolution_date': row['issues_resolution_date'],
                'days_to_resolve': None,  # For resolved issues
                'days_open': None,       # For unresolved issues
                'details': []
            }
            # Calculate days metrics based on status
            if current_issue['issues_date_logged']:
                if current_issue['issues_status'] == 'Resolved':
                    if (current_issue['issues_resolution_date'] and 
                        current_issue['issues_resolution_date'] != date(1900, 1, 1)):
                        current_issue['days_to_resolve'] = (current_issue['issues_resolution_date'] - current_issue['issues_date_logged']).days
                else:  # For Unresolved and Issue status
                    current_issue['days_open'] = (today - current_issue['issues_date_logged']).days
                    
        current_issue['details'].append({
            'issues_details_id': row['issues_details_id'],
            'issues_details_comment': row['issues_details_comment'],
            'issues_details_user': row['issues_details_user'],
            'issues_details_date': row['issues_details_date']
        })
    if current_issue is not None:
        issues.append(current_issue)

    processed_data = {}
    cut_off_date = date.today() - timedelta(days=7)
    for status in ['Resolved', 'Unresolved', 'Issue']:
        processed_data[status] = {}
        for prop in properties:
            prop_name = prop['prop_name']
            processed_data[status][prop_name] = []

            # Track unique issues by heading+description
            unique_issues = set()

            for issue in issues:
                if (issue['prop_name'] == prop_name and 
                    issue['issues_status'] == status and 
                    (issue['issues_heading'], issue['issues_description']) not in unique_issues):

                    # For Resolved, check cutoff date
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
        'status_groups': [
            {
                'status': status,
                'property_issues': [
                    {
                        'prop_name': prop['prop_name'],
                        'issues': processed_data[status][prop['prop_name']]
                    }
                    for prop in properties
                    if processed_data[status][prop['prop_name']]  # Only include if issues exist
                ]
            }
            for status in ['Resolved', 'Unresolved', 'Issue']
        ]
    }

    if mydb.is_connected():
        mydb.close()
    
    return render(request, 'friday_status_report.html', context)

from datetime import datetime, date
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from collections import defaultdict
from django.utils.dateparse import parse_date

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

def open_invoices_report(request):
	mydb = mysql.connector.connect(
		host=settings.DATABASES['default']['HOST'],
		port=settings.DATABASES['default']['PORT'],
		user=settings.DATABASES['default']['USER'],
		password=settings.DATABASES['default']['PASSWORD'],
		database=settings.DATABASES['default']['NAME'],
		auth_plugin=settings.DATABASES['default']['AUTH_PLUGIN'],
	)
	my_cursor = mydb.cursor(dictionary=True)
	today = date.today()
	properties_with_invoices = []
	my_cursor.execute("""
		SELECT prop.prop_name, prop.prop_country, tenant.tenant_id, tenant.tenant_name,
			tenant.tenant_contact_person, tenant.tenant_contact_number, tenant.tenant_email,
			tenant.tenant_rent, tenant.tenant_payment_terms
		FROM railway.tenant 
		JOIN railway.prop ON prop.prop_id = tenant.prop_id 
		WHERE tenant.tenant_current = 'Yes'
		ORDER BY prop.prop_country ASC, prop.prop_name ASC
	""")
	tenants_rows = my_cursor.fetchall()
	my_cursor.execute("""
		SELECT invoice.invoice_id, invoice.tenant_id, invoice.invoice_date, invoice.invoice_paid 
		FROM railway.invoice
		WHERE invoice.invoice_paid = 'No' 
		ORDER BY invoice.invoice_date ASC
	""")
	unpaid_invoices = my_cursor.fetchall()
	for ten in tenants_rows:
		tenant_invoices = []
		for invoice in unpaid_invoices:
			if ten['tenant_id'] == invoice['tenant_id']:
				due_date = invoice['invoice_date'] + timedelta(days=ten['tenant_payment_terms'])
				days_overdue = (today - due_date).days if today > due_date else 0
				tenant_invoices.append({
					'invoice_id': invoice['invoice_id'],
					'invoice_date': invoice['invoice_date'].strftime('%Y-%m-%d'),
					'due_date': due_date.strftime('%Y-%m-%d'),
					'days_overdue': days_overdue,
					'overdue': days_overdue > 0
				})
		if tenant_invoices:
			properties_with_invoices.append({
				'prop_name': ten['prop_name'],
				'prop_country': ten['prop_country'],
				'tenant_id': ten['tenant_id'],
				'tenant_name': ten['tenant_name'],
				'tenant_contact_person': ten['tenant_contact_person'],
				'tenant_contact_number': ten['tenant_contact_number'],
				'tenant_email': ten['tenant_email'],
				'tenant_rent': ten['tenant_rent'],
				'tenant_payment_terms': ten['tenant_payment_terms'],
				'invoices': tenant_invoices
			})
	context = {
		'today': today.strftime('%Y-%m-%d'),
		'properties_with_invoices': properties_with_invoices
	}
	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
	return render(request, 'open_invoices_report.html', context)


def lease_renewal_report(request):
	mydb = mysql.connector.connect(
		host=settings.DATABASES['default']['HOST'],
		port=settings.DATABASES['default']['PORT'],
		user=settings.DATABASES['default']['USER'],
		password=settings.DATABASES['default']['PASSWORD'],
		database=settings.DATABASES['default']['NAME'],
		auth_plugin=settings.DATABASES['default']['AUTH_PLUGIN'],
	)
	my_cursor = mydb.cursor()
	today = date.today()
	tenants = []
	vacant_properties = []
	my_cursor.execute("""
		SELECT prop.prop_name, prop.prop_country, tenant.tenant_type, tenant.tenant_name,
		tenant.tenant_contact_person, tenant.tenant_contact_number, tenant.tenant_email,
		tenant.tenant_deposit, tenant.tenant_lease_start_date, tenant.tenant_lease_end_date,
		tenant.tenant_rental_type, tenant.tenant_renewal, tenant.tenant_renewal_period,
		tenant.tenant_rent, tenant.tenant_levies, tenant.tenant_payment_terms,
		tenant.tenant_current
		FROM railway.tenant
		JOIN railway.prop ON prop.prop_id = tenant.prop_id
		WHERE tenant.tenant_current = 'Yes'
		ORDER BY prop.prop_country ASC, prop.prop_name ASC
	""")
	tenant_rows = my_cursor.fetchall()
	my_cursor.execute("""
		SELECT prop.prop_name
		FROM railway.tenant
		JOIN railway.prop ON prop.prop_id = tenant.prop_id
		WHERE tenant.tenant_current = 'Yes'
		ORDER BY prop.prop_country ASC, prop.prop_name ASC
	""")
	prop_active_tenant = [row[0] for row in my_cursor.fetchall()]
	my_cursor.execute("""
		SELECT prop.prop_name
		FROM railway.prop
		WHERE prop.prop_status = 'Active'
		AND prop.prop_available_for_rent = 'Yes'
		ORDER BY prop.prop_country ASC, prop.prop_name ASC
	""")
	active_properties = [row[0] for row in my_cursor.fetchall()]
	for row in tenant_rows:
		lease_end_date = row[9]  # tenant_lease_end_date
		renewal_period = int(row[12])  # tenant_renewal_period
		renewal_date = lease_end_date - timedelta(days=renewal_period)
		warning_date = renewal_date - timedelta(days=30)
		if today >= warning_date:
			tenants.append({
				'prop_name': row[0],
				'prop_country': row[1],
				'tenant_type': row[2],
				'tenant_name': row[3],
				'tenant_contact_person': row[4],
				'tenant_contact_number': row[5],
				'tenant_email': row[6],
				'tenant_deposit': row[7],
				'tenant_lease_start_date': row[8].strftime('%Y-%m-%d') if row[8] else '',
				'tenant_lease_end_date': row[9].strftime('%Y-%m-%d') if row[9] else '',
				'tenant_rental_type': row[10],
				'tenant_renewal': row[11],
				'tenant_renewal_period': row[12],
				'tenant_rent': row[13],
				'tenant_levies': row[14],
				'tenant_payment_terms': row[15],
				'renewal_date': renewal_date.strftime('%Y-%m-%d'),
				'needs_renewal': True
			})
		vacant_properties = [{'prop_name': prop} for prop in active_properties if prop not in prop_active_tenant]
	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
	context = {
		'tenants': tenants,
		'vacant_properties': vacant_properties,
		'today': today.strftime('%Y-%m-%d')
	}
	return render(request, 'lease_renewal_report.html', context)

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
