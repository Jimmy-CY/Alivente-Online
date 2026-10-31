# WL-8, 31 Oct 2026 - challenges: a habit with a finish line.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellness", "0008_calm"),
    ]

    operations = [
        migrations.AddField(
            model_name="habit",
            name="challenge_days",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="habit",
            name="challenge_from",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="habit",
            name="challenge_seen",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="habit",
            name="challenge_done_on",
            field=models.DateField(blank=True, null=True),
        ),
    ]
