# Generated for round C1 on 2026-09-22 - a label change only.
# AlterField with the same type, default and help text: Django records it
# and the database is not altered.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0093_cashreceipt_edited_at_cashreceipt_edited_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='props',
            name='prop_include_in_occupancy',
            field=models.BooleanField(default=True, help_text='Uncheck to exclude this property from occupancy rate and days-to-fill calculations (e.g., for seasonal rentals)', verbose_name='Include in Occupancy'),
        ),
    ]
