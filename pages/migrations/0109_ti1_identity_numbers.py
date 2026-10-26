# TI-1, 26 Oct 2026 - identity numbers on the tenant, optional.
#
# Three AddField and nothing else: no data is touched, every existing row
# is valid the moment this lands (all three are blank=True).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0108_es7_house_marks"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="tenant_company_reg_no",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="tenant",
            name="tenant_id_number",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="tenant",
            name="tenant_2_id_number",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
