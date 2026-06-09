from django.db import migrations

HOUSEHOLD_NAME = "Demetri's Household"
SEED_MEMBERS = [
    ("Demetri",   "demetrimanias@gmail.com"),
    ("Angy",      "angmaniasbakers@gmail.com"),
    ("Erene",     "erenemanias@gmail.com"),
    ("Alexandra", "leximanias@gmail.com"),
]


def seed_members(apps, schema_editor):
    Workspace = apps.get_model('pages', 'Workspace')
    HouseholdMember = apps.get_model('pages', 'HouseholdMember')
    User = apps.get_model('auth', 'User')

    ws = Workspace.objects.filter(name=HOUSEHOLD_NAME).first()
    if ws is None:
        return  # Fresh DB / other env — nothing to seed.

    for name, email in SEED_MEMBERS:
        if HouseholdMember.objects.filter(workspace=ws, name=name).exists():
            continue
        user = User.objects.filter(email__iexact=email).first()
        HouseholdMember.objects.create(
            workspace=ws, name=name, email=email, user=user, is_active=True,
        )


def unseed_members(apps, schema_editor):
    Workspace = apps.get_model('pages', 'Workspace')
    HouseholdMember = apps.get_model('pages', 'HouseholdMember')
    ws = Workspace.objects.filter(name=HOUSEHOLD_NAME).first()
    if ws is not None:
        HouseholdMember.objects.filter(
            workspace=ws, name__in=[n for n, _ in SEED_MEMBERS],
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0071_householdmember'),
    ]
    operations = [
        migrations.RunPython(seed_members, reverse_code=unseed_members),
    ]