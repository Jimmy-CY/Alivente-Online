# -*- coding: utf-8 -*-
"""ROUND N1 - a text column stops having two kinds of empty.

Demetri found this on Suppliers: leave the email blank, and the edit form
comes back with the word None in the box, because Django renders a NULL
as the text "None". Press Save and "None" is real data - and then
type="email" refuses it.

The cause is that a text column may be NULL at all. Django's own
documentation says not to do that on a string field: you end up with two
possible empty values and have to remember which is which in every
template, every filter and every form.

So: 127 text columns across 32 models lose null=True. THE DATA RUNS FIRST,
while the column still allows NULL - every NULL and every value that is
exactly the string "None" becomes ''. Then the schema follows.

The forward pass prints one line per column it actually touched, so the
damage is counted rather than guessed at. It is safe to run twice: the
second time it finds nothing and says so.

REVERSING restores null=True on the columns. It does NOT put the NULLs
back, because which rows were NULL and which were already '' is exactly
the distinction this round exists to destroy, and inventing it again
would be worse than leaving them empty. See test_none_columns.py.
"""
from django.db import migrations, models


COLUMNS = [
    ('Project', 'project_name'),
    ('Project', 'project_status'),
    ('Project', 'project_description'),
    ('Project', 'project_name_greek'),
    ('Project', 'project_description_greek'),
    ('ProjectTask', 'task_name'),
    ('ProjectTask', 'task_description'),
    ('ProjectTask', 'task_name_greek'),
    ('ProjectTask', 'task_description_greek'),
    ('ProjectTask', 'task_status'),
    ('ProjectTask', 'task_priority'),
    ('ProjectTask', 'task_assigned_to'),
    ('ProjectDocument', 'document_name'),
    ('ProjectDocument', 'document_description'),
    ('ProjectDocument', 'document_uploaded_by'),
    ('props', 'prop_name'),
    ('props', 'prop_address1'),
    ('props', 'prop_address2'),
    ('props', 'prop_suburb'),
    ('props', 'prop_city'),
    ('props', 'prop_province'),
    ('props', 'prop_country'),
    ('props', 'prop_pcode'),
    ('props', 'prop_status'),
    ('props', 'prop_available_for_rent'),
    ('props', 'prop_title_deed_status'),
    ('props', 'prop_electricity'),
    ('props', 'prop_water'),
    ('props', 'prop_refuse'),
    ('props', 'prop_property_tax'),
    ('props', 'prop_sewerage'),
    ('props', 'prop_insurance'),
    ('petty', 'petty_cash_description'),
    ('petty', 'petty_cash_dr_cr'),
    ('tenant', 'tenant_type'),
    ('tenant', 'tenant_name'),
    ('tenant', 'tenant_contact_person'),
    ('tenant', 'tenant_contact_number'),
    ('tenant', 'tenant_email'),
    ('tenant', 'tenant_rental_type'),
    ('tenant', 'tenant_renewal'),
    ('tenant', 'tenant_current'),
    ('tenant', 'tenant_lease_agreement_status'),
    ('tenant', 'tenant_renewal_status'),
    ('supplier', 'supplier_contact_person'),
    ('supplier', 'supplier_contact_number'),
    ('supplier', 'supplier_email'),
    ('supplier', 'supplier_company_name'),
    ('supplier', 'supplier_role'),
    ('supplier', 'supplier_country'),
    ('invoices', 'invoice_paid'),
    ('PhysicalInvoice', 'invoice_number'),
    ('PhysicalInvoice', 'email_status'),
    ('issues', 'issues_heading'),
    ('issues', 'issues_description'),
    ('issues', 'issues_status'),
    ('issues', 'issues_resolving_user'),
    ('issues_details', 'issues_details_comment'),
    ('issues_details', 'issues_details_user'),
    ('IssueAuditLog', 'old_value'),
    ('IssueAuditLog', 'new_value'),
    ('revenue_types', 'revenue_types_name'),
    ('revenue_types', 'revenue_types_jan'),
    ('revenue_types', 'revenue_types_feb'),
    ('revenue_types', 'revenue_types_mar'),
    ('revenue_types', 'revenue_types_apr'),
    ('revenue_types', 'revenue_types_may'),
    ('revenue_types', 'revenue_types_jun'),
    ('revenue_types', 'revenue_types_jul'),
    ('revenue_types', 'revenue_types_aug'),
    ('revenue_types', 'revenue_types_sep'),
    ('revenue_types', 'revenue_types_oct'),
    ('revenue_types', 'revenue_types_nov'),
    ('revenue_types', 'revenue_types_dec'),
    ('revenue_line_types', 'revenue_line_types_name'),
    ('revenue_line_types', 'revenue_line_types_description'),
    ('expense_types', 'expense_types_name'),
    ('expense_types', 'expense_types_jan'),
    ('expense_types', 'expense_types_feb'),
    ('expense_types', 'expense_types_mar'),
    ('expense_types', 'expense_types_apr'),
    ('expense_types', 'expense_types_may'),
    ('expense_types', 'expense_types_jun'),
    ('expense_types', 'expense_types_jul'),
    ('expense_types', 'expense_types_aug'),
    ('expense_types', 'expense_types_sep'),
    ('expense_types', 'expense_types_oct'),
    ('expense_types', 'expense_types_nov'),
    ('expense_types', 'expense_types_dec'),
    ('expense_line_types', 'expense_line_types_name'),
    ('expense_line_types', 'expense_line_types_description'),
    ('expense_line_types', 'expense_line_types_prorata'),
    ('act_expense', 'act_expense_description'),
    ('act_expense', 'act_expense_approved'),
    ('act_expense', 'act_expense_paid'),
    ('act_expense', 'act_expense_verify_status'),
    ('act_expense', 'act_expense_verify_number'),
    ('act_expense', 'act_expense_verify_supplier'),
    ('act_expense', 'act_expense_verify_notes'),
    ('act_expense', 'act_expense_verify_raw'),
    ('act_expense', 'act_expense_verify_model'),
    ('MeasurementUnit', 'abbreviation'),
    ('MeasurementUnit', 'abbreviation_plural'),
    ('IngredientCategory', 'description'),
    ('Ingredient', 'notes'),
    ('Ingredient', 'fdc_description'),
    ('Ingredient', 'fdc_data_type'),
    ('Ingredient', 'nutrition_source'),
    ('RecipeCategory', 'description'),
    ('Recipe', 'recipe_description'),
    ('Recipe', 'difficulty_level'),
    ('Recipe', 'created_by'),
    ('RecipeIngredient', 'preparation_note'),
    ('RecipeIngredient', 'ingredient_group'),
    ('RecipeIngredientText', 'ingredient_group'),
    ('RecipeInstruction', 'instruction_group'),
    ('Contact', 'email'),
    ('Contact', 'phone'),
    ('Contact', 'notes'),
    ('HouseholdMember', 'email'),
    ('CelebrationEvent', 'notes'),
    ('AssetCategory', 'icon'),
    ('PropertyAsset', 'brand_manufacturer'),
    ('PropertyAsset', 'notes'),
    ('AssetMaintenance', 'service_provider'),
    ('FinancialFigureHistory', 'line_type'),
    ('FinancialFigureHistory', 'source'),
]


def empty_the_nones(apps, schema_editor):
    """Every NULL, and every literal "None", becomes ''."""
    total_null = total_word = 0
    for model_name, field in COLUMNS:
        model = apps.get_model('pages', model_name)
        n_null = model.objects.filter(**{field + '__isnull': True}).update(
            **{field: ''})
        n_word = model.objects.filter(**{field: 'None'}).update(**{field: ''})
        if n_null or n_word:
            print('    %-30s %5d NULL  %5d "None"'
                  % (model_name + '.' + field, n_null, n_word))
        total_null += n_null
        total_word += n_word
    print('    %d NULL and %d literal "None" value(s) emptied across %d '
          'column(s)' % (total_null, total_word, len(COLUMNS)))


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0094_alter_props_prop_include_in_occupancy'),
    ]

    operations = [
        # THE DATA FIRST. Emptying a NULL after the column has been made
        # NOT NULL is not possible - the ALTER is what would fail.
        migrations.RunPython(empty_the_nones, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='project',
            name='project_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='project_status',
            field=models.CharField(max_length=20, choices=[ ('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed'), ], default='Pending', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='project_description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='project_name_greek',
            field=models.CharField(max_length=255, blank=True, help_text='Greek translation of project name'),
        ),
        migrations.AlterField(
            model_name='project',
            name='project_description_greek',
            field=models.TextField(blank=True, help_text='Greek translation of project description'),
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='task_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='task_description',
            field=models.TextField(blank=True) # longtext,
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='task_name_greek',
            field=models.CharField(max_length=255, blank=True, help_text='Greek translation of task name'),
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='task_description_greek',
            field=models.TextField(blank=True, help_text='Greek translation of task description'),
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='task_status',
            field=models.CharField(max_length=20, choices=[ ('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed'), ], default='Pending', blank=True),
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='task_priority',
            field=models.CharField(max_length=10, choices=[ ('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical'), ], blank=True),
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='task_assigned_to',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='projectdocument',
            name='document_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='projectdocument',
            name='document_description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='projectdocument',
            name='document_uploaded_by',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_address1',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_address2',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_suburb',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_city',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_province',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_country',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_pcode',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_status',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_available_for_rent',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_title_deed_status',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_electricity',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_water',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_refuse',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_property_tax',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_sewerage',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='props',
            name='prop_insurance',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='petty',
            name='petty_cash_description',
            field=models.CharField(max_length=55, blank=True),
        ),
        migrations.AlterField(
            model_name='petty',
            name='petty_cash_dr_cr',
            field=models.CharField(max_length=2, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_type',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_contact_person',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_contact_number',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_email',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_rental_type',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_renewal',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_current',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_lease_agreement_status',
            field=models.CharField(max_length=255, blank=True, verbose_name="Lease Agreement Status"),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='tenant_renewal_status',
            field=models.CharField(max_length=20, choices=[ ('pending', 'Pending'), ('declined', 'Declined'), ('new_lease_signed', 'New Lease Signed'), ], default='pending', blank=True, verbose_name="Renewal Status"),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='supplier_contact_person',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='supplier_contact_number',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='supplier_email',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='supplier_company_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='supplier_role',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='supplier_country',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='invoices',
            name='invoice_paid',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='physicalinvoice',
            name='invoice_number',
            field=models.CharField(max_length=32, blank=True, help_text='PR-#### — assigned when the invoice is sent.'),
        ),
        migrations.AlterField(
            model_name='physicalinvoice',
            name='email_status',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='issues',
            name='issues_heading',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='issues',
            name='issues_description',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='issues',
            name='issues_status',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='issues',
            name='issues_resolving_user',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='issues_details',
            name='issues_details_comment',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='issues_details',
            name='issues_details_user',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='issueauditlog',
            name='old_value',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='issueauditlog',
            name='new_value',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_jan',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_feb',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_mar',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_apr',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_may',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_jun',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_jul',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_aug',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_sep',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_oct',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_nov',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_types',
            name='revenue_types_dec',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_line_types',
            name='revenue_line_types_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='revenue_line_types',
            name='revenue_line_types_description',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_jan',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_feb',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_mar',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_apr',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_may',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_jun',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_jul',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_aug',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_sep',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_oct',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_nov',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_types',
            name='expense_types_dec',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_line_types',
            name='expense_line_types_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_line_types',
            name='expense_line_types_description',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='expense_line_types',
            name='expense_line_types_prorata',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_description',
            field=models.CharField(max_length=55, blank=True),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_approved',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_paid',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_verify_status',
            field=models.CharField(max_length=20, blank=True, help_text='verified | mismatch | unverified | not_invoice | pending'),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_verify_number',
            field=models.CharField(max_length=60, blank=True),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_verify_supplier',
            field=models.CharField(max_length=120, blank=True),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_verify_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_verify_raw',
            field=models.TextField(blank=True, help_text='Full extraction payload - the audit record.'),
        ),
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_verify_model',
            field=models.CharField(max_length=60, blank=True, help_text='Model + prompt version, so old verdicts stay interpretable.'),
        ),
        migrations.AlterField(
            model_name='measurementunit',
            name='abbreviation',
            field=models.CharField(max_length=10, blank=True, help_text='Singular short form (e.g., tsp, cup, g)'),
        ),
        migrations.AlterField(
            model_name='measurementunit',
            name='abbreviation_plural',
            field=models.CharField(max_length=10, blank=True, help_text='Plural short form (e.g., tsp, cups, g)'),
        ),
        migrations.AlterField(
            model_name='ingredientcategory',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='notes',
            field=models.TextField(blank=True, help_text='Storage tips, substitutions, etc.'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='fdc_description',
            field=models.CharField(max_length=300, blank=True, help_text='USDA description of the matched food (for reference)'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='fdc_data_type',
            field=models.CharField(max_length=30, blank=True, help_text='USDA data type: Foundation, SR Legacy, Survey (FNDDS), or Branded'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='nutrition_source',
            field=models.CharField(max_length=10, choices=[ ('usda', 'USDA'), ('manual', 'Manual'), ], blank=True, help_text='Where the per-100g nutrition values came from. NULL = not set yet.'),
        ),
        migrations.AlterField(
            model_name='recipecategory',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='recipe_description',
            field=models.TextField(blank=True, help_text='Brief description or introduction'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='difficulty_level',
            field=models.CharField(max_length=20, choices=[ ('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ], blank=True),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='created_by',
            field=models.CharField(max_length=255, blank=True, help_text='User who created this recipe'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='preparation_note',
            field=models.CharField(max_length=255, blank=True, help_text='Additional preparation notes'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='ingredient_group',
            field=models.CharField(max_length=100, blank=True, help_text='e.g., "For the sauce", "For garnish"'),
        ),
        migrations.AlterField(
            model_name='recipeingredienttext',
            name='ingredient_group',
            field=models.CharField(max_length=100, blank=True, help_text='Ingredient grouping') # ADD THIS,
        ),
        migrations.AlterField(
            model_name='recipeinstruction',
            name='instruction_group',
            field=models.CharField(max_length=100, blank=True, help_text='e.g., "Preparation", "Cooking", "Assembly"'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='phone',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='householdmember',
            name='email',
            field=models.EmailField(blank=True),
        ),
        migrations.AlterField(
            model_name='celebrationevent',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='assetcategory',
            name='icon',
            field=models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class (e.g., 'fa-snowflake')"),
        ),
        migrations.AlterField(
            model_name='propertyasset',
            name='brand_manufacturer',
            field=models.CharField(max_length=100, blank=True, verbose_name="Brand/Manufacturer"),
        ),
        migrations.AlterField(
            model_name='propertyasset',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='assetmaintenance',
            name='service_provider',
            field=models.CharField(max_length=200, blank=True, help_text="Technician/company name (optional)"),
        ),
        migrations.AlterField(
            model_name='financialfigurehistory',
            name='line_type',
            field=models.CharField(max_length=255, blank=True, help_text='Denormalised line-type label, e.g. Rental / Insurance.'),
        ),
        migrations.AlterField(
            model_name='financialfigurehistory',
            name='source',
            field=models.CharField(max_length=30, blank=True, help_text='budget | direct | prorata | prorata_line | prorata_valuation | seed'),
        ),
    ]
