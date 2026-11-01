# WL-11, 1 Nov 2026 - calories burnt on a workout, typed in from the watch.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0009_challenges"),
    ]

    operations = [
        migrations.AddField(
            model_name="workoutsession",
            name="calories",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
