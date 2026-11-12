# PT-1, 12 Nov 2026 - a workout logged afterwards keeps how long it took.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0014_progress_photos"),
    ]

    operations = [
        migrations.AddField(
            model_name="workoutsession",
            name="minutes",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
