# TR-12, 17 Nov 2026 - Suggest things to do: a run of suggestions, and each
# suggestion kept on the trip (shown, Not interested, or added).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("travel", "0009_plan_my_days"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdeaRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True,
                                           primary_key=True,
                                           serialize=False,
                                           verbose_name="ID")),
                ("status", models.CharField(
                    choices=[("working", "Finding ideas"),
                             ("ready", "Ready"),
                             ("failed", "Could not suggest")],
                    default="working", max_length=10)),
                ("answers", models.JSONField(blank=True, default=dict)),
                ("progress", models.JSONField(blank=True, default=dict)),
                ("more", models.BooleanField(default=False)),
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
                    related_name="idea_runs", to="travel.trip")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Idea",
            fields=[
                ("id", models.BigAutoField(auto_created=True,
                                           primary_key=True,
                                           serialize=False,
                                           verbose_name="ID")),
                ("city", models.CharField(max_length=80)),
                ("interest", models.CharField(blank=True, default="",
                                              max_length=20)),
                ("name", models.CharField(max_length=160)),
                ("area", models.CharField(blank=True, default="",
                                          max_length=120)),
                ("blurb", models.CharField(blank=True, default="",
                                           max_length=400)),
                ("kind", models.CharField(default="sight", max_length=10)),
                ("visit", models.CharField(blank=True, default="",
                                           max_length=40)),
                ("price", models.CharField(blank=True, default="",
                                           max_length=60)),
                ("book", models.BooleanField(default=False)),
                ("note", models.CharField(blank=True, default="",
                                          max_length=160)),
                ("state", models.CharField(
                    blank=True,
                    choices=[("", "Suggested"), ("hidden", "Not interested"),
                             ("added", "Added to Things to do")],
                    default="", max_length=8)),
                ("position", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("place", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="travel.place")),
                ("run", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="ideas", to="travel.idearun")),
                ("trip", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ideas", to="travel.trip")),
            ],
            options={"ordering": ["position", "id"]},
        ),
    ]
