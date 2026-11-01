# WL-13, 1 Nov 2026 - when a habit was paused, so paused days are Rest.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0011_weekly_challenges"),
    ]

    operations = [
        migrations.AddField(
            model_name="habit",
            name="pauses",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
