from django.db import migrations, models


def seed_roles(apps, schema_editor):
    RLT = apps.get_model('pages', 'revenue_line_types')
    for lt in RLT.objects.all():
        nm = (lt.revenue_line_types_name or '').lower()
        if 'levies' in nm or 'levy' in nm:
            role = 'levies'
        elif 'rental' in nm or 'rent' in nm:
            role = 'rent'
        else:
            role = ''
        if role and lt.lease_role != role:
            lt.lease_role = role
            lt.save(update_fields=['lease_role'])


def unseed(apps, schema_editor):
    RLT = apps.get_model('pages', 'revenue_line_types')
    RLT.objects.update(lease_role='')


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0086_financialfigurehistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='revenue_line_types',
            name='lease_role',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.RunPython(seed_roles, unseed),
    ]
