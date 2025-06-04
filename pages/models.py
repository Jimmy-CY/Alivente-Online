from django.db import models
from django.db import connections
from django.core.exceptions import ValidationError
import os
from django.utils.text import slugify

def expense_document_upload_path(instance, filename):
	"""
	Generate custom upload path for expense documents
	Format: expense_docs/PropertyName-YYYYMMDD-OriginalFileName.ext
	"""
	# Get the file extension
	ext = filename.split('.')[-1]

	# Get property name and clean it (remove spaces, special chars)
	property_name = slugify(instance.prop.prop_name)

	# Format the date as YYYYMMDD
	date_str = instance.act_expense_date.strftime('%Y%m%d')

	# Get the original filename without extension
	original_name = os.path.splitext(filename)[0]

	# Create the new filename
	new_filename = f"{property_name}-{date_str}-{original_name}.{ext}"

	# Return the full path
	return os.path.join('expense_docs', new_filename)

def title_deed_upload_path(instance, filename):
    """Generate upload path for title deeds"""
    # Sanitize the property name
    prop_name_slug = slugify(instance.prop_name or 'property')
    
    # Get file extension
    ext = os.path.splitext(filename)[1].lower()
    
    # Generate filename
    filename = f"prop_{instance.prop_id}_{prop_name_slug[:50]}_title_deed{ext}"
    
    # Return full path
    return os.path.join('properties', 'title_deeds', filename)

def lease_agreement_upload_path(instance, filename):
    """Generate upload path for lease agreements"""
    # Sanitize the tenant name
    tenant_name_slug = slugify(instance.tenant_name or 'tenant')
    
    # Get file extension
    ext = os.path.splitext(filename)[1].lower()
    
    # Generate filename
    filename = f"tenant_{instance.tenant_id}_{tenant_name_slug[:50]}_lease_agreement{ext}"
    
    # Return full path
    return os.path.join('tenants', 'lease_agreements', filename)

##### Create your models here ###############
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
    prop_title_deed = models.FileField(upload_to=title_deed_upload_path, blank=True, null=True)
    prop_title_deed_status = models.CharField(max_length=255, blank=True, null=True)
    prop_electricity = models.CharField(max_length=255, blank=True, null=True)
    prop_water = models.CharField(max_length=255, blank=True, null=True)
    prop_refuse = models.CharField(max_length=255, blank=True, null=True)
    prop_property_tax = models.CharField(max_length=255, blank=True, null=True)
    prop_sewerage = models.CharField(max_length=255, blank=True, null=True)
    prop_insurance = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.prop_name or f"Property {self.prop_id}"

    class Meta:
        db_table = "prop"
        verbose_name = "Property"
        verbose_name_plural = "Properties"

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
    tenant_lease_agreement = models.FileField(
        upload_to=lease_agreement_upload_path, 
        blank=True, 
        null=True,
        verbose_name="Lease Agreement Document"
    )
    tenant_lease_agreement_status = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Lease Agreement Status"
    )

    def clean(self):
        """Validate lease dates and check for ACTIVE tenant overlaps only"""
        if self.tenant_lease_start_date and self.tenant_lease_end_date:
            # Validate date order
            if self.tenant_lease_end_date <= self.tenant_lease_start_date:
                raise ValidationError("Lease end date must be after start date")
            
            # Only check for overlaps with ACTIVE tenants
            if hasattr(self, 'prop'):
                overlapping = tenant.objects.filter(
                    prop=self.prop,
                    tenant_current='Yes',  # KEY CHANGE - only active tenants
                    tenant_lease_start_date__lte=self.tenant_lease_end_date,
                    tenant_lease_end_date__gte=self.tenant_lease_start_date
                ).exclude(pk=self.pk)
                
                if overlapping.exists():
                    tenant_list = ", ".join([f"{t.tenant_name} ({'Active' if t.tenant_current == 'Yes' else 'Inactive'})" 
                                           for t in overlapping])
                    raise ValidationError(
                        f"Property already has active tenant(s) during this period: {tenant_list}"
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tenant_name if self.tenant_name else ""

    class Meta:
        db_table = "tenant"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

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

class prop_values(models.Model):
	prop_values_id = models.AutoField(primary_key=True)
	prop = models.ForeignKey(props, on_delete=models.CASCADE)
	prop_values_purchase_price = models.IntegerField(blank=True, null=True)
	prop_values_current_value = models.IntegerField(blank=True, null=True)

	def __str__(self):
		return str(self.prop_values_purchase_price)

	class Meta:
		db_table="prop_values"

class revenue_types(models.Model):
	revenue_types_id = models.AutoField(primary_key=True)
	revenue_types_name = models.CharField(max_length=255, blank=True, null=True)
	revenue_types_jan = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_feb = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_mar = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_apr = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_may = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_jun = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_jul = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_aug = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_sep = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_oct = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_nov = models.CharField(max_length=3, blank=True, null=True)
	revenue_types_dec = models.CharField(max_length=3, blank=True, null=True)

	def __str__(self):
		return str(self.revenue_types_name)

	class Meta:
		db_table="revenue_types"

class revenue_line_types(models.Model):
	revenue_line_types_id = models.AutoField(primary_key=True)
	revenue_line_types_name = models.CharField(max_length=255, blank=True, null=True)
	revenue_line_types_description = models.CharField(max_length=255, blank=True, null=True)
	
	def __str__(self):
		return str(self.revenue_line_types_name)

	class Meta:
		db_table="revenue_line_types"

class revenue(models.Model):
	revenue_id = models.AutoField(primary_key=True)
	revenue_types = models.ForeignKey(revenue_types, on_delete=models.CASCADE)
	prop = models.ForeignKey(props, on_delete=models.CASCADE)
	revenue_line_types = models.ForeignKey(revenue_line_types, on_delete=models.CASCADE)
	revenue_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_jan = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_feb = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_mar = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_apr = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_may = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_jun = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_jul = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_aug = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_sep = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_oct = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_nov = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	revenue_dec = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

	def __str__(self):
		return str(self.revenue_id)

	class Meta:
		db_table="revenue"

class expense_types(models.Model):
	expense_types_id = models.AutoField(primary_key=True)
	expense_types_name = models.CharField(max_length=255, blank=True, null=True)
	expense_types_jan = models.CharField(max_length=3, blank=True, null=True)
	expense_types_feb = models.CharField(max_length=3, blank=True, null=True)
	expense_types_mar = models.CharField(max_length=3, blank=True, null=True)
	expense_types_apr = models.CharField(max_length=3, blank=True, null=True)
	expense_types_may = models.CharField(max_length=3, blank=True, null=True)
	expense_types_jun = models.CharField(max_length=3, blank=True, null=True)
	expense_types_jul = models.CharField(max_length=3, blank=True, null=True)
	expense_types_aug = models.CharField(max_length=3, blank=True, null=True)
	expense_types_sep = models.CharField(max_length=3, blank=True, null=True)
	expense_types_oct = models.CharField(max_length=3, blank=True, null=True)
	expense_types_nov = models.CharField(max_length=3, blank=True, null=True)
	expense_types_dec = models.CharField(max_length=3, blank=True, null=True)

	def __str__(self):
		return str(self.expense_types_name)

	class Meta:
		db_table="expense_types"

class expense_line_types(models.Model):
	expense_line_types_id = models.AutoField(primary_key=True)
	expense_line_types_name = models.CharField(max_length=255, blank=True, null=True)
	expense_line_types_description = models.CharField(max_length=255, blank=True, null=True)
	expense_line_types_prorata = models.CharField(max_length=3, blank=True, null=True)
	expense_line_types_pr_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

	def __str__(self):
		return str(self.expense_line_types_name)

	class Meta:
		db_table="expense_line_types"

class expense(models.Model):
	expense_id = models.AutoField(primary_key=True)
	expense_types = models.ForeignKey(expense_types, on_delete=models.CASCADE)
	expense_line_types = models.ForeignKey(expense_line_types, on_delete=models.CASCADE)
	expense_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	prop = models.ForeignKey(props, on_delete=models.CASCADE)
	expense_jan = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_feb = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_mar = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_apr = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_may = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_jun = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_jul = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_aug = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_sep = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_oct = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_nov = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	expense_dec = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

	def __str__(self):
		return str(self.expense_id)

	class Meta:
		db_table="expense"

class act_expense(models.Model):
	act_expense_id = models.AutoField(primary_key=True)
	act_expense_date = models.DateField(blank=True, null=True)
	prop = models.ForeignKey(props, on_delete=models.CASCADE)
	act_expense_description = models.CharField(max_length=55, blank=True, null=True)
	act_expense_amount = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
	act_expense_approved = models.CharField(max_length=3, blank=True, null=True)
	act_expense_paid = models.CharField(max_length=3, blank=True, null=True)
	act_expense_document = models.FileField(upload_to=expense_document_upload_path, blank=True, null=True)

	def __str__(self):
		return self.act_expense_description
	def approved_display(self):
	    return "Yes" if self.act_expense_approved == 'Yes' else "No"
	def paid_display(self):
		return "Yes" if self.act_expense_paid == 'Yes' else "No"

	class Meta:
		db_table="act_expense"
