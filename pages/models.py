from django.db import models
from django.db import connections

# Create your models here.

class props(models.Model):
	prop_id = models.AutoField(primary_key=True)
	prop_name = models.CharField(max_length=255, blank=True, null=True)
	prop_address1 = models.CharField(max_length=255, blank=True, null=True)
	prop_address2 = models.CharField(max_length=255, blank=True, null=True)
	prop_suburb = models.CharField(max_length=255, blank=True, null=True)
	prop_city = models.CharField(max_length=255, blank=True, null=True)
	prop_province = models.CharField(max_length=255, blank=True, null=True)
	prop_country = models.CharField(max_length=255, blank=True, null=True)
	prop_pcode = models.CharField(max_length=255, blank=True, null=True)
	prop_floor_area = models.IntegerField(blank=True, null=True)
	prop_year_built = models.IntegerField(blank=True, null=True)
	prop_status = models.CharField(max_length=255, blank=True, null=True)
	prop_available_for_rent = models.CharField(max_length=255, blank=True, null=True)
	prop_title_deed = models.CharField(max_length=255, blank=True, null=True)
	prop_title_deed_status = models.CharField(max_length=255, blank=True, null=True)
	prop_electricity = models.CharField(max_length=255, blank=True, null=True)
	prop_water = models.CharField(max_length=255, blank=True, null=True)
	prop_refuse = models.CharField(max_length=255, blank=True, null=True)
	prop_property_tax = models.CharField(max_length=255, blank=True, null=True)
	prop_sewerage = models.CharField(max_length=255, blank=True, null=True)
	prop_insurance = models.CharField(max_length=255, blank=True, null=True)

	def __str__(self):
		return self.prop_name

	class Meta:
		db_table="prop"

class petty(models.Model):
	petty_cash_id = models.AutoField(primary_key=True)
	petty_cash_date = models.DateField(blank=True, null=True)
	petty_cash_description = models.CharField(max_length=55, blank=True, null=True)
	petty_cash_amount = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
	petty_cash_dr_cr = models.CharField(max_length=2, blank=True, null=True)

	def __str__(self):
		return self.petty_cash_description

	class Meta:
		db_table="petty_cash"

class tenant(models.Model):
	tenant_id = models.AutoField(primary_key=True)
	prop = models.ForeignKey(props, on_delete=models.CASCADE)
	tenant_type = models.CharField(max_length=255, blank=True, null=True)
	tenant_name = models.CharField(max_length=255, blank=True, null=True)
	tenant_contact_person = models.CharField(max_length=255, blank=True, null=True)
	tenant_contact_number = models.CharField(max_length=255, blank=True, null=True)
	tenant_email = models.CharField(max_length=255, blank=True, null=True)
	tenant_deposit = models.IntegerField(blank=True, null=True)
	tenant_lease_start_date = models.DateField(blank=True, null=True)
	tenant_lease_end_date = models.DateField(blank=True, null=True)
	tenant_rental_type = models.CharField(max_length=255, blank=True, null=True)
	tenant_renewal = models.CharField(max_length=255, blank=True, null=True)
	tenant_renewal_period = models.IntegerField(blank=True, null=True)
	tenant_rent = models.IntegerField(blank=True, null=True)
	tenant_levies = models.IntegerField(blank=True, null=True)
	tenant_payment_terms = models.IntegerField(blank=True, null=True)
	tenant_current = models.CharField(max_length=255, blank=True, null=True)
	tenant_lease_agreement = models.CharField(max_length=255, blank=True, null=True)

	def __str__(self):
		return self.tenant_name

	class Meta:
		db_table="tenant"

class supplier(models.Model):
	supplier_id = models.AutoField(primary_key=True)
	supplier_contact_person = models.CharField(max_length=255, blank=True, null=True)
	supplier_contact_number = models.CharField(max_length=255, blank=True, null=True)
	supplier_email = models.CharField(max_length=255, blank=True, null=True)
	supplier_company_name = models.CharField(max_length=255, blank=True, null=True)
	supplier_role = models.CharField(max_length=255, blank=True, null=True)
	supplier_country = models.CharField(max_length=255, blank=True, null=True)
	
	def __str__(self):
		return self.supplier_contact_person

	class Meta:
		db_table="supplier"

class invoices(models.Model):
	invoice_id = models.AutoField(primary_key=True)
	tenant = models.ForeignKey(tenant, on_delete=models.CASCADE)
	invoice_date = models.DateField(blank=True, null=True)
	invoice_paid = models.CharField(max_length=255, blank=True, null=True)
	
	class Meta:
		db_table="invoice"

class issues(models.Model):
	issues_id = models.AutoField(primary_key=True)
	prop = models.ForeignKey(props, on_delete=models.CASCADE)
	issues_heading = models.CharField(max_length=255, blank=True, null=True)
	issues_description = models.CharField(max_length=255, blank=True, null=True)
	issues_date_logged = models.DateField(blank=True, null=True)
	issues_status = models.CharField(max_length=255, blank=True, null=True)
	issues_resolution_date = models.DateField(blank=True, null=True, default=None)
	issues_resolving_user = models.CharField(max_length=255, blank=True, null=True)

	def __str__(self):
		return self.issues_heading

	class Meta:
		db_table="issues"

class issues_details(models.Model):
	issues_details_id = models.AutoField(primary_key=True)
	issues = models.ForeignKey(issues, on_delete=models.CASCADE)
	issues_details_comment = models.CharField(max_length=255, blank=True, null=True)
	issues_details_user = models.CharField(max_length=255, blank=True, null=True)
	issues_details_date = models.DateField(blank=True, null=True)

	def __str__(self):
		return self.issues_details_comment

	class Meta:
		db_table="issues_details"

