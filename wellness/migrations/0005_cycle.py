# CY-1, 30 Oct 2026 - the cycle tracker's locked record.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0004_exercise_library"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CycleRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name="ID")),
                ("prefs", models.TextField(blank=True)),
                ("days", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="wellness_cycle",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "wellness_cycle_record"},
        ),
    ]
