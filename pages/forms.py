from django import forms
from . import models

class PropForm(forms.ModelForm):
	class Meta:
		model = models.props
		fields = ["prop_name","prop_address1","prop_address2","prop_suburb","prop_city","prop_province","prop_country","prop_pcode","prop_floor_area","prop_year_built","prop_status","prop_available_for_rent","prop_title_deed","prop_title_deed_status","prop_electricity","prop_water","prop_refuse","prop_property_tax","prop_sewerage","prop_insurance"]

class PettyForm(forms.ModelForm):
	class Meta:
		model = models.petty
		fields = ["petty_cash_date","petty_cash_description","petty_cash_amount","petty_cash_dr_cr"]

class TenantForm(forms.ModelForm):
	class Meta:
		model = models.tenant
		fields = ["prop","tenant_type","tenant_name","tenant_contact_person","tenant_contact_number","tenant_email","tenant_deposit","tenant_lease_start_date","tenant_lease_end_date","tenant_rental_type","tenant_renewal","tenant_renewal_period","tenant_rent","tenant_levies","tenant_payment_terms","tenant_current","tenant_lease_agreement"]

class SupplierForm(forms.ModelForm):
	class Meta:
		model = models.supplier
		fields = ["supplier_contact_person","supplier_contact_number","supplier_email","supplier_company_name","supplier_role","supplier_country"]

class InvoicesForm(forms.ModelForm):
	class Meta:
		model = models.invoices
		fields = ["tenant","invoice_date","invoice_paid"]

class IssuesForm(forms.ModelForm):
	class Meta:
		model = models.issues
		fields = ["prop","issues_heading","issues_description","issues_date_logged","issues_status","issues_resolution_date","issues_resolving_user"]

class DetailsForm(forms.ModelForm):
	class Meta:
		model = models.issues_details
		fields = ["issues","issues_details_comment","issues_details_user","issues_details_date"]
