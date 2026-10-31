# WL-7, 31 Oct 2026 - Calm: breathing, sitting and guided practices. The
# minutes kept, and a habit that Calm minutes can tick.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0007_reminders"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="habit",
            name="auto_from",
            field=models.CharField(
                blank=True, default="", max_length=10,
                choices=[("", "Ticked by hand"),
                         ("workout", "A finished workout"),
                         ("calm", "Calm minutes")]),
        ),
        migrations.CreateModel(
            name="CalmSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name="ID")),
                ("date", models.DateField()),
                ("kind", models.CharField(
                    max_length=10,
                    choices=[("breathe", "Breathe"), ("sit", "Sit"),
                             ("guided", "Guided")])),
                ("practice", models.CharField(blank=True, max_length=24)),
                ("seconds", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="wellness_calm_sessions",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "wellness_calm_session",
                     "ordering": ["-created_at"]},
        ),
    ]
