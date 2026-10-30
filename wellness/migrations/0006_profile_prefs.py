# WL-4a, 30 Oct 2026 - personal settings and kept badges on the profile.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0005_cycle"),
    ]

    operations = [
        migrations.AddField(
            model_name="wellnessprofile",
            name="prefs",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
