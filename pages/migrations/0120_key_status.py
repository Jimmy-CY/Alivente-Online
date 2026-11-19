# RA04, 19 Nov 2026 - how each outside service's key is doing, for the
# email that says when one stops working.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0119_celebration_gifts"),
    ]

    operations = [
        migrations.CreateModel(
            name="KeyStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name="ID")),
                ("service", models.CharField(max_length=30, unique=True)),
                ("ok", models.BooleanField(default=True)),
                ("problem", models.CharField(blank=True, default="",
                                             max_length=20)),
                ("detail", models.CharField(blank=True, default="",
                                            max_length=255)),
                ("failing_since", models.DateTimeField(blank=True,
                                                       null=True)),
                ("last_ok", models.DateTimeField(blank=True, null=True)),
                ("last_checked", models.DateTimeField(blank=True,
                                                      null=True)),
                ("emailed_on", models.DateField(blank=True, null=True)),
            ],
            options={"db_table": "key_status", "ordering": ["service"]},
        ),
    ]
