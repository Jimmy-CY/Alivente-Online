# -*- coding: utf-8 -*-
"""GL-2 and GE-1, 28 Oct 2026 - Release 35.

    - props.prop_address_greek: the address a Greek lease writes. Filled for
      the three Athens floors with his wording of 28 October,
      «οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, 154 52» - blanks only.
    - leasesigning.word_docx: the Word version of a lease that came from
      Generate, kept with its envelope (his decision: "Absolutely").
    - GeneratedLease: a lease Generate built for e-signing, waiting for the
      Send screen to make it an envelope.
"""

import django.db.models.deletion
import pages.models
from django.conf import settings
from django.db import migrations, models

GREEK_ADDRESS = 'οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, 154 52'
FLATS = ('Athens - First Floor', 'Athens - Second Floor',
         'Athens - Third Floor')


def fill(apps, schema_editor):
    props = apps.get_model('pages', 'props')
    props.objects.filter(prop_name__in=FLATS, prop_address_greek='') \
        .update(prop_address_greek=GREEK_ADDRESS)


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0113_greek_lease_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="leasesigning",
            name="word_docx",
            field=models.FileField(
                blank=True,
                max_length=255,
                null=True,
                upload_to=pages.models.lease_signing_upload_path,
            ),
        ),
        migrations.AddField(
            model_name="props",
            name="prop_address_greek",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Address (Greek)"
            ),
        ),
        migrations.CreateModel(
            name="GeneratedLease",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("country", models.CharField(max_length=20)),
                ("language", models.CharField(max_length=20)),
                (
                    "pdf",
                    models.FileField(
                        max_length=255,
                        upload_to=pages.models.generated_lease_upload_path,
                    ),
                ),
                (
                    "docx",
                    models.FileField(
                        max_length=255,
                        upload_to=pages.models.generated_lease_upload_path,
                    ),
                ),
                ("page_count", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "envelope",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="pages.leasesigning",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="generated_leases",
                        to="pages.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "generated_lease",
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
