# -*- coding: utf-8 -*-
"""OF-3, 28 Oct 2026 - Owned From, on the property.

Adds props.prop_owned_from and fills it, as he decided on 28 October:

    - every property with a lease: the start of its FIRST lease ("the date
      of the first rental for that property as the date that we owned it
      from"; the gap between buying and first letting is accepted);
    - Ionion - Villa 24: 1 January 2010, and Ionion - Villa H4: 1 January
      2014 - seasonal, no lease, dates given by him;
    - anything else with no lease stays blank, which counts as owned all
      along - exactly how the P&L treated it before this.

Only a BLANK date is ever filled, so running it on a database where somebody
has already typed a date changes nothing. Reversing it removes the column.
"""
import datetime

from django.db import migrations, models
from django.db.models import Min

GIVEN = {
    'Ionion - Villa 24': datetime.date(2010, 1, 1),
    'Ionion - Villa H4': datetime.date(2014, 1, 1),
}


def fill(apps, schema_editor):
    props = apps.get_model('pages', 'props')
    tenant = apps.get_model('pages', 'tenant')
    first = dict(tenant.objects.exclude(tenant_lease_start_date__isnull=True)
                 .values('prop_id')
                 .annotate(_m=Min('tenant_lease_start_date'))
                 .values_list('prop_id', '_m'))
    for p in props.objects.filter(prop_owned_from__isnull=True):
        d = first.get(p.prop_id) or GIVEN.get((p.prop_name or '').strip())
        if d:
            props.objects.filter(pk=p.pk).update(prop_owned_from=d)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0111_tenant_id_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='props',
            name='prop_owned_from',
            field=models.DateField(
                blank=True, null=True, verbose_name='Owned From',
                help_text='Budgets and revenue count from this month. Blank = the first lease start.'),
        ),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
