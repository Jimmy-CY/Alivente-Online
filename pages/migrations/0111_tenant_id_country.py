# -*- coding: utf-8 -*-
"""PC-1, 28 Oct 2026 - the Passport/ID country, on the record.

Adds tenant.tenant_id_country and tenant.tenant_2_id_country, blank by
default, so every existing row is correct the moment this lands. No data
is changed.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0110_notification_type_cash_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='tenant_id_country',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='tenant',
            name='tenant_2_id_country',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
