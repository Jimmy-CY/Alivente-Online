# DC-1, 12 Nov 2026 - six more document types, and an optional earlier
# reminder (9 or 12 months before expiry) for slow renewals.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0116_meal_calendars"),
    ]

    operations = [
        migrations.AlterField(
            model_name="passport",
            name="document_type",
            field=models.CharField(choices=[
                ("passport", "Passport"), ("id", "ID"),
                ("drivers_license", "Driver's License"), ("visa", "Visa"),
                ("arc", "Alien Registration Card"),
                ("health", "Health Card"),
                ("residence", "Residence Certificate"),
                ("car_reg", "Car Registration"), ("mot", "MOT"),
                ("insurance", "Insurance"), ("tax_id", "Tax ID")],
                max_length=20),
        ),
        migrations.AddField(
            model_name="passport",
            name="remind_months",
            field=models.PositiveSmallIntegerField(
                blank=True, choices=[(9, "9 months before"),
                                     (12, "12 months before")],
                help_text="Remind earlier than six months before expiry",
                null=True),
        ),
    ]
