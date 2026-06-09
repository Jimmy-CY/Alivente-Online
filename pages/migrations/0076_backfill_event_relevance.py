from django.db import migrations

# notify_* boolean -> the seeded HouseholdMember name it maps to.
MAPPING = {
    'notify_demetri':   'Demetri',
    'notify_angy':      'Angy',
    'notify_erene':     'Erene',
    'notify_alexandra': 'Alexandra',
}


def backfill(apps, schema_editor):
    CelebrationEvent = apps.get_model('pages', 'CelebrationEvent')
    HouseholdMember = apps.get_model('pages', 'HouseholdMember')

    for event in CelebrationEvent.objects.all().select_related('contact'):
        ws_id = event.contact.workspace_id
        if not ws_id:
            continue
        for field, member_name in MAPPING.items():
            if getattr(event, field, False):
                m = HouseholdMember.objects.filter(
                    workspace_id=ws_id, name__iexact=member_name
                ).first()
                if m:
                    event.relevant_to.add(m)


def unbackfill(apps, schema_editor):
    CelebrationEvent = apps.get_model('pages', 'CelebrationEvent')
    for event in CelebrationEvent.objects.all():
        event.relevant_to.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0075_celebrationevent_relevant_to'),
    ]

    operations = [
        migrations.RunPython(backfill, reverse_code=unbackfill),
    ]