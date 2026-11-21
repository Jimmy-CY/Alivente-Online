# RA09, 21 Nov 2026 - Google's allowance, counted by Alivente (travel/gquota.py).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("travel", "0012_budget"),
    ]

    operations = [
        migrations.CreateModel(
            name="GoogleAllowance",
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
                ("per_month", models.PositiveIntegerField(default=1000)),
                ("per_day", models.PositiveIntegerField(default=100)),
                (
                    "warned_month",
                    models.CharField(blank=True, default="", max_length=7),
                ),
                ("rechecked_on", models.DateField(blank=True, null=True)),
            ],
            options={
                "db_table": "travel_google_allowance",
            },
        ),
        migrations.CreateModel(
            name="GoogleUse",
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
                ("day", models.DateField(unique=True)),
                ("searches", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "travel_google_use",
                "ordering": ["-day"],
            },
        ),
    ]
