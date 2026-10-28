from django import forms
from . import models

class PropForm(forms.ModelForm):
    class Meta:
        model = models.props
        fields = [
            "prop_name",
            "prop_address1", 
            "prop_address2",
            "prop_suburb",
            "prop_city",
            "prop_province",
            "prop_country",
            "prop_pcode",
            "prop_latitude",
            "prop_longitude",
            "prop_floor_area",
            "prop_year_built",
            "prop_status",
            "prop_available_for_rent",
            "prop_title_deed",
            "prop_title_deed_status",
            "prop_include_in_occupancy",  # ADD THIS LINE
            "prop_electricity",
            "prop_water",
            "prop_refuse",
            "prop_property_tax",
            "prop_sewerage",
            "prop_insurance"
        ]

class PettyForm(forms.ModelForm):
	class Meta:
		model = models.petty
		fields = ["petty_cash_date","petty_cash_description","petty_cash_amount","petty_cash_dr_cr"]

# In your forms.py
class TenantForm(forms.ModelForm):
    class Meta:
        model = models.tenant
        fields = [
            'tenant_type', 'tenant_name', 'tenant_contact_person', 
            'tenant_contact_number', 'tenant_email',
            # T2-1, 24 Oct 2026. fields is an explicit list, so a
            # column missing from it is a column the form silently
            # ignores - the user types a joint tenant and the save
            # drops them without a word.
            'tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email',
            # TI-1, 26 Oct 2026 - the three identity numbers, optional.
            # In this list or the form drops them without a word (T2-1).
            'tenant_company_reg_no', 'tenant_id_number', 'tenant_2_id_number',
            # PC-1, 28 Oct 2026 - the country that issued each Passport/ID.
            'tenant_id_country', 'tenant_2_id_country',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
            'tenant_rent', 'tenant_levies', 'tenant_payment_terms',
            'tenant_renewal', 'tenant_renewal_period', 'tenant_renewal_status',
            'tenant_current', 'prop'
        ]

    # ONE ADDRESS PER PERSON - T2-8, 25 Oct 2026. His rule, in his
    # words: "we will have problems in the e-signing function and
    # other email areas". A signing link is a credential for ONE
    # person; a box holding two addresses hands one link to two
    # people and the trail cannot tell them apart.
    #
    # ON THE FORM AND NOT IN tenant.clean(). save() calls full_clean(),
    # so a model rule would refuse every save of a record that still
    # holds two addresses - including the ones the five-minute cron
    # makes. His decision was BLOCK ON NEXT SAVE: stored values keep
    # working, and the refusal meets a person, with the screen in
    # front of them, when they open that tenant and press Save.
    #
    # REQUIRED, both of them - the second only when there IS a second
    # tenant, decided by the name exactly as has_second_tenant decides
    # it. Send for Signature should never meet a tenant it cannot
    # reach; refusing there moves the complaint to the moment he is
    # trying to get something done.
    ONE_ADDRESS_SPLIT = r'[\s,;]+'

    @classmethod
    def one_address(cls, raw, who):
        """The single address in `raw`, or a ValidationError saying why not.

        AN EMPTY VALUE IS RETURNED EMPTY - whether it is ALLOWED to be
        empty is the caller's question, because for the second tenant
        it depends on another field.
        """
        import re as _re
        from django.core.exceptions import ValidationError
        from django.core.validators import validate_email
        parts = [p for p in _re.split(cls.ONE_ADDRESS_SPLIT, raw or '') if p]
        if not parts:
            return ''
        found = [p for p in parts if '@' in p]
        if len(found) > 1:
            raise ValidationError(
                '%s holds %d addresses (%s). Keep exactly one - each '
                'person gets their own signing link and their own '
                'email, and one box cannot be two people.'
                % (who, len(found), ', '.join(found)))
        if len(parts) != 1:
            raise ValidationError('%s "%s" is not a valid email address.'
                                  % (who, ' '.join(parts)))
        try:
            validate_email(parts[0])
        except ValidationError:
            raise ValidationError('%s "%s" is not a valid email address.'
                                  % (who, parts[0]))
        return parts[0]

    def clean_tenant_email(self):
        from django.core.exceptions import ValidationError
        got = self.one_address(self.cleaned_data.get('tenant_email'),
                               'Tenant Email Address')
        if not got:
            raise ValidationError('Tenant Email Address is required.')
        return got

    def clean_tenant_2_email(self):
        return self.one_address(self.cleaned_data.get('tenant_2_email'),
                                'Second Tenant Email Address')

    def clean(self):
        data = super().clean()
        # THE NAME DECIDES, as has_second_tenant does on the model. An
        # address with no name is a half-typed form; a name with no
        # address is a liable person nobody can reach.
        if ((data.get('tenant_2_name') or '').strip()
                and not data.get('tenant_2_email')
                and 'tenant_2_email' not in self.errors):
            self.add_error('tenant_2_email',
                           'Second Tenant Email Address is required when '
                           'there is a second tenant.')
        return data

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

class ValuesForm(forms.ModelForm):
	class Meta:
		model = models.prop_values
		fields = ["prop", "prop_values_purchase_price","prop_values_current_value"]

class RevenueTypesForm(forms.ModelForm):
	class Meta:
		model = models.revenue_types
		fields = ["revenue_types_name", "revenue_types_jan", "revenue_types_feb", "revenue_types_mar", "revenue_types_apr", "revenue_types_may", "revenue_types_jun", "revenue_types_jul", "revenue_types_aug", "revenue_types_sep", "revenue_types_oct", "revenue_types_nov", "revenue_types_dec"]

class RevenueLineForm(forms.ModelForm):
	class Meta:
		model = models.revenue_line_types
		fields = ["revenue_line_types_name", "revenue_line_types_description"]

class RevenueForm(forms.ModelForm):
	class Meta:
		model = models.revenue
		fields = ["revenue_types", "prop","revenue_line_types","revenue_amount","revenue_jan","revenue_feb","revenue_mar","revenue_apr","revenue_may","revenue_jun","revenue_jul","revenue_aug","revenue_sep","revenue_oct","revenue_nov","revenue_dec"]

class ExpenseTypesForm(forms.ModelForm):
	class Meta:
		model = models.expense_types
		fields = ["expense_types_name", "expense_types_jan", "expense_types_feb", "expense_types_mar", "expense_types_apr", "expense_types_may", "expense_types_jun", "expense_types_jul", "expense_types_aug", "expense_types_sep", "expense_types_oct", "expense_types_nov", "expense_types_dec"]

class ExpenseLineForm(forms.ModelForm):
	class Meta:
		model = models.expense_line_types
		fields = ["expense_line_types_name", "expense_line_types_description", "expense_line_types_prorata", "expense_line_types_pr_amount"]

class ExpenseForm(forms.ModelForm):
	class Meta:
		model = models.expense
		fields = ["expense_types","expense_line_types","expense_amount","prop","expense_jan","expense_feb","expense_mar","expense_apr","expense_may","expense_jun","expense_jul","expense_aug","expense_sep","expense_oct","expense_nov","expense_dec"]

class ActExpenseForm(forms.ModelForm):
	class Meta:
		model = models.act_expense
		fields = ["act_expense_date","prop","act_expense_description","act_expense_amount","act_expense_approved","act_expense_paid","act_expense_document"]
