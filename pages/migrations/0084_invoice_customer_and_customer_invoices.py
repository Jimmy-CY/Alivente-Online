# Phase 1: customer (non-tenant) invoices.
#   - new InvoiceCustomer model
#   - PhysicalInvoice.tenant -> nullable
#   - PhysicalInvoice.customer FK (PROTECT) + 7 bill_* snapshot fields
from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0083_physicalinvoiceprofile_client_email_body'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoiceCustomer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('customer_id_label', models.CharField(
                    blank=True, max_length=255,
                    help_text="Shown in the 'Customer ID' box on the invoice.")),
                ('billing_address', models.TextField(blank=True, help_text='One line per row.')),
                ('billing_tel', models.CharField(blank=True, max_length=64)),
                ('email_to', models.TextField(blank=True, help_text='Comma-separated To addresses.')),
                ('email_cc', models.TextField(blank=True, help_text='Comma-separated CC addresses.')),
                ('email_body', models.TextField(
                    blank=True,
                    help_text="Optional saved greeting/body for this customer's invoice e-mail. "
                              "Blank uses a generic default.")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Invoice Customer',
                'verbose_name_plural': 'Invoice Customers',
                'db_table': 'invoice_customers',
                'ordering': ['name'],
            },
        ),
        migrations.AlterField(
            model_name='physicalinvoice',
            name='tenant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='physical_invoices', to='pages.tenant'),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='customer',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='invoices', to='pages.invoicecustomer'),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='bill_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='bill_customer_label',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='bill_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='bill_tel',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='bill_email_to',
            field=models.TextField(
                blank=True,
                help_text='Comma-separated To addresses for a customer invoice.'),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='bill_email_cc',
            field=models.TextField(
                blank=True,
                help_text='Comma-separated CC addresses for a customer invoice.'),
        ),
        migrations.AddField(
            model_name='physicalinvoice',
            name='bill_email_body',
            field=models.TextField(blank=True),
        ),
    ]