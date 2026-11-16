# TR-8, 16 Nov 2026 - a boarding pass put right by hand.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("travel", "0006_settle_up"),
    ]

    operations = [
        migrations.AddField(
            model_name="boardingpass",
            name="marked",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
        migrations.AddField(
            model_name="boardingpass",
            name="marked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
