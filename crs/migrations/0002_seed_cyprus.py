"""
Seed the initial Cyprus CountryConfiguration row.
"""
from django.db import migrations


CYPRUS_DEFAULTS = {
    "country_name": "Cyprus",
    "is_active": True,
    "oecd_version": "2.0",
    "tin_regex": "",
    "message_ref_id_template": "[SENDING_FI_IN].[YEAR]_[UUID]",
    "fi_doc_ref_id_template": "[SENDING_FI_IN].[YEAR]_[YYYYMMDDHHMM]_[UUID]",
    "account_doc_ref_id_template": "[SENDING_FI_IN].[YEAR]_[YYYYMMDDHHMM]_[UUID]",
    "output_filename_template": "[SENDING_FI_IN]_[CURRENT_DATE].xml",
    "default_currency": "EUR",
}


def seed_cyprus(apps, schema_editor):
    CountryConfiguration = apps.get_model("crs", "CountryConfiguration")
    CountryConfiguration.objects.update_or_create(
        country_code="CY",
        defaults=CYPRUS_DEFAULTS,
    )


def unseed_cyprus(apps, schema_editor):
    CountryConfiguration = apps.get_model("crs", "CountryConfiguration")
    CountryConfiguration.objects.filter(country_code="CY").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("crs", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_cyprus, unseed_cyprus),
    ]