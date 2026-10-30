# WL-4b, 30 Oct 2026 - phone reminders: a time per habit, and the phones
# that may receive them.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0006_profile_prefs"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="habit",
            name="remind_at",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="PushDevice",
            fields=[
                ("id", models.BigAutoField(auto_created=True,
                                           primary_key=True, serialize=False,
                                           verbose_name="ID")),
                ("endpoint", models.TextField()),
                ("endpoint_hash", models.CharField(max_length=64,
                                                   unique=True)),
                ("p256dh", models.CharField(max_length=255)),
                ("auth", models.CharField(max_length=64)),
                ("label", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_ok_at", models.DateTimeField(blank=True, null=True)),
                ("failures", models.PositiveSmallIntegerField(default=0)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="wellness_push_devices",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "wellness_push_device",
                     "ordering": ["-created_at"]},
        ),
    ]
