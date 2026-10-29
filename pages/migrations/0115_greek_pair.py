# -*- coding: utf-8 -*-
"""GL-3, 29 Oct 2026 - the Greek details per tenant; no second ΔΕΗ field.

His decisions of 29 October:

    - THE ΔΕΗ FIELD GOES. GL-1 added props.prop_deh_number and it duplicated
      Electricity Details, which already held each Athens floor's meter
      ("Meter: 3138572"). ΔΕΗ is Greek; Electricity Details is the field
      every property in every country has. Before the column goes, a ΔΕΗ
      number whose property has a BLANK Electricity Details is copied there
      as "Meter: <number>", so nothing typed is lost. Electricity Details
      that already holds anything is never touched.
    - THE SECOND TENANT GETS HIS OWN father's name, ΑΦΜ and ΔΟΥ ("we need
      these fields PER tenant"). Added blank.

Reversing it brings back an empty ΔΕΗ column and drops the three new ones.
"""
from django.db import migrations, models


def keep(apps, schema_editor):
    props = apps.get_model('pages', 'props')
    for p in props.objects.exclude(prop_deh_number=''):
        if not (p.prop_electricity or '').strip():
            props.objects.filter(pk=p.pk).update(
                prop_electricity='Meter: %s' % p.prop_deh_number.strip())


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0114_greek_address_generated_lease'),
    ]

    operations = [
        migrations.RunPython(keep, migrations.RunPython.noop),
        migrations.RemoveField(model_name='props', name='prop_deh_number'),
        migrations.AddField(
            model_name='tenant', name='tenant_2_father_name',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(
            model_name='tenant', name='tenant_2_afm',
            field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(
            model_name='tenant', name='tenant_2_doy',
            field=models.CharField(blank=True, max_length=100)),
    ]
