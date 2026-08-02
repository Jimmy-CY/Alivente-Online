from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0087_revenue_line_types_lease_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoices',
            name='invoice_paid_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
