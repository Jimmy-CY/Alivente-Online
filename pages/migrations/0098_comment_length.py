# -*- coding: utf-8 -*-
"""CM-1 - the issue comment column goes from 255 to 1000 characters.

Demetri asked for the Enter New Comment field to hold about three times
what it held. The browser said 250, the edit box said 255, the edit view
enforced 255 and the add view enforced nothing; the column was the real
ceiling at 255. All five now say 1000.

WIDENING IS NOT A DATA CHANGE. Every existing comment is already inside
255 and is left exactly as it is - no truncation, no re-encoding, no
backfill. MySQL rewrites the column definition and that is all.

THE REVERSE IS SAFE TODAY AND WILL NOT STAY SAFE. The moment one comment
longer than 255 exists, running this backwards truncates it. Django
would generate that reverse silently; it is written out here so that it
is a decision somebody makes rather than one that happens.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0097_passport_holder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issues_details',
            name='issues_details_comment',
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]
