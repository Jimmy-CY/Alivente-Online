# -*- coding: utf-8 -*-
"""GL-1, 28 Oct 2026 - what the Greek lease needs, on the record.

His decisions of 28 October:

    - the tenant's father's name, tax number (ΑΦΜ) and tax office (ΔΟΥ)
      live on the tenant - they were one past tenant's, typed into the
      Greece template;
    - the floor, parking space and ΔΕΗ supply number live on the property
      - the three Athens floors are otherwise identical: floor 1 parks in
      P1, floor 2 in P2, floor 3 in P3; ΔΕΗ supply numbers 3138572,
      3138573 and 3138574 (his figures; 3138574 is the one the template
      carried);
    - Alivente's own details are stored once (CompanyDetails): the real
      registration number HE283373, not the HE123456 placeholder, and his
      passport, issued 26-02-2022, expiring 25-02-2027.

Only blanks are ever filled, so nothing typed before this runs is touched.
Reversing it removes the columns and the table.
"""
import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

FLATS = {
    'Athens - First Floor': {'prop_floor': '1', 'prop_parking_space': 'P1',
                             'prop_deh_number': '3138572'},
    'Athens - Second Floor': {'prop_floor': '2', 'prop_parking_space': 'P2',
                              'prop_deh_number': '3138573'},
    'Athens - Third Floor': {'prop_floor': '3', 'prop_parking_space': 'P3',
                             'prop_deh_number': '3138574'},
}

COMPANY = {
    'company_name': 'Alivente Limited',
    'registration_number': 'HE283373',
    'contact_person': 'Demetri Manias',
    'phone': '+357-96668557',
    'email': 'demetri.manias@alivente.com',
    'address': 'Alivente House, Dikaiosynis 13A, Engomi, Nicosia, Cyprus, 2412',
    'passport_number': 'ΑΤ4635239',
    'passport_issued': datetime.date(2022, 2, 26),
    'passport_expires': datetime.date(2027, 2, 25),
}


def fill(apps, schema_editor):
    props = apps.get_model('pages', 'props')
    for name, values in FLATS.items():
        for p in props.objects.filter(prop_name=name):
            change = dict((k, v) for k, v in values.items()
                          if not getattr(p, k))
            if change:
                props.objects.filter(pk=p.pk).update(**change)
    CD = apps.get_model('pages', 'CompanyDetails')
    if not CD.objects.exists():
        CD.objects.create(**COMPANY)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0112_prop_owned_from'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant', name='tenant_father_name',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(
            model_name='tenant', name='tenant_afm',
            field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(
            model_name='tenant', name='tenant_doy',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(
            model_name='props', name='prop_floor',
            field=models.CharField(blank=True, max_length=20,
                                   verbose_name='Floor')),
        migrations.AddField(
            model_name='props', name='prop_parking_space',
            field=models.CharField(blank=True, max_length=20,
                                   verbose_name='Parking Space')),
        migrations.AddField(
            model_name='props', name='prop_deh_number',
            field=models.CharField(blank=True, max_length=30,
                                   verbose_name='ΔΕΗ Supply Number')),
        migrations.CreateModel(
            name='CompanyDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(blank=True, max_length=200)),
                ('registration_number', models.CharField(blank=True,
                                                         max_length=50)),
                ('contact_person', models.CharField(blank=True,
                                                    max_length=200)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('email', models.CharField(blank=True, max_length=200)),
                ('address', models.TextField(blank=True)),
                ('passport_number', models.CharField(blank=True,
                                                     max_length=50)),
                ('passport_issued', models.DateField(blank=True, null=True)),
                ('passport_expires', models.DateField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Company Details',
                     'verbose_name_plural': 'Company Details',
                     'db_table': 'company_details'},
        ),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
