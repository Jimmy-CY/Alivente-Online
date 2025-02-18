from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.http import HttpResponse
from .models import props, petty, issues, issues_details, tenant, invoices, supplier
from datetime import date, datetime
from . import forms
from .forms import PropForm, TenantForm, PettyForm, InvoicesForm, IssuesForm, DetailsForm, SupplierForm

###  HOME ###
def home(request):
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.filter(tenant_current="Yes")
	sresults = supplier.objects.all().order_by('supplier_country','supplier_contact_person')
	return render (request, "home.html", {"props":results, "tenant":tresults, "supplier":sresults})

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
	if request.method == "POST":
		form = TenantForm(request.POST or None)
		if form.is_valid():
			form.save()
			messages.success(request, "Tenant Added Successfully")
		else:
			print(form.errors.as_data())
	results = props.objects.all().order_by('prop_country','prop_name')
	tresults = tenant.objects.all().order_by('tenant_name')
	return render (request, "tenant.html", {"props":results, "tenant":tresults})

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
	iresults = invoices.objects.filter(invoice_paid="No")
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
	return render(request, "properties_add.html", {"props":results})

def properties_commit(request):
	if request.method == "POST":
		form = PropForm(request.POST or None)
		if form.is_valid():
			form.save()
	results = props.objects.all().order_by('prop_country','prop_name')
	messages.success(request, "Property Added Successfully")
	return render (request, "properties.html", {"props":results})

def properties_edit(request, prop_id):
	results = props.objects.filter(pk=prop_id)
	return render (request, "properties_edit.html", {"props":results})

def properties_edit_commit(request, prop_id):
	prop = props.objects.get(pk=prop_id)
	if request.method == "POST":
		form = PropForm(request.POST or None, instance=prop)
		if form.is_valid():
			form.save()
	results = props.objects.all().order_by('prop_country','prop_name')
	messages.success(request, "Property Edited Successfully")
	return render (request, "properties.html", {"props":results})


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
#	results = props.objects.all().order_by('prop_country','prop_name')
#	isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
#	idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
#	return render(request, "fsr.html", {"props":results, "issues":isresults, "issues_details":idresults})
	return redirect("fsr_details", is_id)

def fsr_details(request, issues_id):
	isresults = issues.objects.filter(pk=issues_id)
	results = props.objects.all().order_by('prop_country','prop_name')
	idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id').reverse()
	return render(request, "fsr_details.html", {"props":results, "issues":isresults, "issues_details":idresults})

def fsr_commit_status_change(request):
	pname = request.POST.get('prop_name')
	is_head = request.POST.get('issues_heading')
	is_id = request.POST.get('issues_id')
	is_status = request.POST.get('issues_status')
	issue_update = issues.objects.filter(pk=is_id).update(issues_status=is_status)
	isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
	isvalues = issues.objects.values()
	today_date = date.today()
	for x in isvalues:
		if int(x['issues_id']) == int(is_id):
			if x['issues_status'] == "Resolved":
				if request.user.is_authenticated:
					lname = request.user.last_name
					fname = request.user.first_name
					user_initials = fname[:1]+lname[:1]
				issue_update = issues.objects.filter(pk=is_id).update(issues_resolution_date=today_date)
				issue_update = issues.objects.filter(pk=is_id).update(issues_resolving_user=user_initials)
			else:
				issue_update = issues.objects.filter(pk=is_id).update(issues_resolution_date='1900-01-01')
				issue_update = issues.objects.filter(pk=is_id).update(issues_resolving_user='')
	messages.success(request, "Status Updated Successfully")
	return redirect("fsr")
#	return redirect("fsr_details", issues_id=is_id)

def fsr_comment_add(request, issues_id):
	iss_det = request.POST.get('issues_details_comment')
	if request.user.is_authenticated:
		lname = request.user.last_name
		fname = request.user.first_name
		user_initials = fname[:1]+lname[:1]
	comm_date = date.today()
	print("YES", issues_id, comm_date, user_initials, iss_det)
	issue_update=issues_details.objects.create (issues_details_comment=iss_det, issues_details_user=user_initials, issues_details_date=comm_date, issues_id=issues_id)
	return redirect("fsr_details", issues_id)

	#return redirect("fsr_details", issues_id)

### REPORTS - DASHBOARD (FROM HOME PAGE) ###
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
