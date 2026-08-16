from django.db import migrations, models


class Migration(migrations.Migration):
    """Invoice verification fields + widened actual-expense amount.

    Purely additive. The amount change widens max_digits 6 -> 10, which no
    existing value can fail, so it is safe on live data.
    """

    dependencies = [
        ('pages', '0088_invoices_invoice_paid_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='act_expense',
            name='act_expense_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_status',
            field=models.CharField(blank=True, max_length=20, null=True,
                help_text='verified | mismatch | unverified | not_invoice | pending'),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_checked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True,
                help_text='Payable total as read from the invoice.'),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_number',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_supplier',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_raw',
            field=models.TextField(blank=True, null=True,
                help_text='Full extraction payload - the audit record.'),
        ),
        migrations.AddField(
            model_name='act_expense',
            name='act_expense_verify_model',
            field=models.CharField(blank=True, max_length=60, null=True,
                help_text='Model + prompt version, so old verdicts stay interpretable.'),
        ),
    ]
