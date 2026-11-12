# MS-1, 12 Nov 2026 - one meal plan per person, shared with whom they
# choose. Existing meals keep calendar empty until the backfill command
# places them (dry run first): pages/management/commands/meal_calendar_backfill.py

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0115_greek_pair"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MealCalendar",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                               related_name="meal_calendar",
                                               to=settings.AUTH_USER_MODEL)),
                ("shared_with", models.ManyToManyField(blank=True,
                                                       related_name="shared_meal_calendars",
                                                       to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "meal_calendars"},
        ),
        migrations.AddField(
            model_name="mealentry",
            name="calendar",
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    related_name="entries", to="pages.mealcalendar"),
        ),
    ]
