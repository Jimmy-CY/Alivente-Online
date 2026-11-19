# RA05, 19 Nov 2026 - the daily spending budget, spending, and sharing
# the costs or not (travel/budget.py).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("travel", "0011_idea_google"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="budget",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="trip",
            name="budget_by",
            field=models.CharField(default="day", max_length=5),
        ),
        migrations.AddField(
            model_name="trip",
            name="share_money",
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name="Spend",
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
                ("day", models.DateField()),
                ("what", models.CharField(blank=True, default="", max_length=120)),
                ("currency", models.CharField(default="EUR", max_length=3)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "amount_eur",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "fx_rate",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=14, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "added_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "trip",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="spends",
                        to="travel.trip",
                    ),
                ),
            ],
            options={
                "db_table": "travel_spends",
                "ordering": ["-day", "-id"],
            },
        ),
    ]
