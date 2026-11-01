# WL-12, 1 Nov 2026 - weekly challenges: a challenge counts days or weeks.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0010_workout_calories"),
    ]

    operations = [
        migrations.AddField(
            model_name="habit",
            name="challenge_unit",
            field=models.CharField(blank=True, default="day", max_length=4),
        ),
    ]
