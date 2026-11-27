# RA32, 27 Nov 2026 - Secret Santa: more than one a year, and the occasion
# (Christmas, an office party, or another the user names).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0122_secret_santa'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='santaexchange',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='santaexchange',
            name='occasion',
            field=models.CharField(choices=[('christmas', 'Christmas'), ('office', 'Office / company party'), ('other', 'Other occasion')], default='christmas', max_length=16),
        ),
        migrations.AddField(
            model_name='santaexchange',
            name='occasion_name',
            field=models.CharField(blank=True, max_length=60),
        ),
    ]
