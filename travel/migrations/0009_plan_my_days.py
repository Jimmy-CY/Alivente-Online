# TR-11, 17 Nov 2026 - Plan my days: what the planner knows about a place,
# and the plan itself (its answers, its proposal and what Undo puts back).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("travel", "0008_day_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="place", name="lat",
            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(
            model_name="place", name="lng",
            field=models.FloatField(blank=True, null=True)),
        migrations.AddField(
            model_name="place", name="facts",
            field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(
            model_name="place", name="facts_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(
            name="TripPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("status", models.CharField(
                    choices=[("working", "Working it out"),
                             ("ready", "Ready to review"),
                             ("failed", "Could not plan"),
                             ("applied", "Applied"), ("undone", "Undone"),
                             ("discarded", "Discarded"),
                             ("replaced", "Replaced by a later plan")],
                    default="working", max_length=10)),
                ("answers", models.JSONField(blank=True, default=dict)),
                ("progress", models.JSONField(blank=True, default=dict)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("before", models.JSONField(blank=True, default=dict)),
                ("applied", models.JSONField(blank=True, default=dict)),
                ("error", models.CharField(blank=True, default="",
                                           max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("trip", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="plans", to="travel.trip")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
