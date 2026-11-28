# RA35, 28 Nov 2026 - Secret Santa: date, time and place "not decided yet",
# and the update owed to everyone once they are added after the draw.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0123_santa_many_per_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='santaexchange',
            name='details_later',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='santaexchange',
            name='details_due',
            field=models.BooleanField(default=False),
        ),
    ]
