# WL-19, 12 Nov 2026 - progress photos. The pictures themselves are
# encrypted files outside the public media folder; this table holds only
# their date, pose, note and file name.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0013_workouts_sports"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProgressPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("pose", models.CharField(choices=[("front", "Front"), ("side", "Side"),
                                                   ("back", "Back"), ("other", "Other")],
                                          default="front", max_length=8)),
                ("note", models.CharField(blank=True, max_length=120)),
                ("stem", models.CharField(max_length=64, unique=True)),
                ("width", models.PositiveIntegerField(default=0)),
                ("height", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="wellness_photos",
                                           to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "wellness_progress_photo",
                     "ordering": ["-date", "-created_at"]},
        ),
    ]
