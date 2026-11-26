# RA28, 26 Nov 2026 - when you first opened a listing's page.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acquisitions", "0003_buy_or_rent"),
    ]

    operations = [
        migrations.AddField(
            model_name="scenariomatch",
            name="opened_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
