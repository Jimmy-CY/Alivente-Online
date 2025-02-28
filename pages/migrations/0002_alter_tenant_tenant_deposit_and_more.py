# Generated by Django 5.1.4 on 2025-01-27 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tenant",
            name="tenant_deposit",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=6, null=True
            ),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="tenant_levies",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=6, null=True
            ),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="tenant_payment_terms",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=6, null=True
            ),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="tenant_renewal_period",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=6, null=True
            ),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="tenant_rent",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=6, null=True
            ),
        ),
    ]
