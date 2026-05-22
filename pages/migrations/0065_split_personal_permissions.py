"""
Data migration: split the single Personal access/edit permission pair
into four module-specific pairs (Passports, Recipes, Celebrations, CRS).

For every user holding `can_access_personal`, grant all four new
`can_access_*` permissions. Same for `can_edit_personal` -> four
`can_edit_*` permissions. After migrating user grants, delete the two
old permission rows. The M2M relationship cascades.

Safe to run multiple times — `get_or_create` handles re-runs, and
the deletion at the end is a no-op if old perms are already gone.
"""
from django.db import migrations


NEW_PERMS = [
    ('can_access_passports',    'Can access Passports / Documents'),
    ('can_edit_passports',      'Can edit Passports / Documents'),
    ('can_access_recipes',      'Can access Recipes'),
    ('can_edit_recipes',        'Can edit Recipes'),
    ('can_access_celebrations', 'Can access Celebrations'),
    ('can_edit_celebrations',   'Can edit Celebrations'),
    ('can_access_crs',          'Can access CRS Reporting'),
    ('can_edit_crs',            'Can edit CRS Reporting'),
]

OLD_ACCESS = 'can_access_personal'
OLD_EDIT   = 'can_edit_personal'

NEW_ACCESS_CODES = [c for c, _ in NEW_PERMS if c.startswith('can_access_')]
NEW_EDIT_CODES   = [c for c, _ in NEW_PERMS if c.startswith('can_edit_')]


def forwards(apps, schema_editor):
    Permission  = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User        = apps.get_model('auth', 'User')

    user_ct = ContentType.objects.get_for_model(User)

    # 1. Create the 8 new permissions if missing
    new_perm_objs = {}
    for codename, name in NEW_PERMS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=user_ct,
            defaults={'name': name},
        )
        new_perm_objs[codename] = perm

    # 2. Find old permission rows (may not exist on a fresh DB — that's fine)
    old_access = Permission.objects.filter(
        codename=OLD_ACCESS, content_type=user_ct
    ).first()
    old_edit = Permission.objects.filter(
        codename=OLD_EDIT, content_type=user_ct
    ).first()

    # 3. Grant the 4 new access perms to every user who held the old one
    if old_access:
        new_access_perms = [new_perm_objs[c] for c in NEW_ACCESS_CODES]
        for user in User.objects.filter(user_permissions=old_access):
            user.user_permissions.add(*new_access_perms)

    # 4. Same for edit
    if old_edit:
        new_edit_perms = [new_perm_objs[c] for c in NEW_EDIT_CODES]
        for user in User.objects.filter(user_permissions=old_edit):
            user.user_permissions.add(*new_edit_perms)

    # 5. Delete old permission rows. M2M links to user_permissions
    #    cascade automatically via the through table.
    if old_access:
        old_access.delete()
    if old_edit:
        old_edit.delete()


def backwards(apps, schema_editor):
    """Reverse: recreate old perms, grant them to anyone who has ANY of
    the new perms, then delete the 8 new ones. Lossy (collapses 4 into 1)
    but reversible enough for a rollback in dev."""
    Permission  = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User        = apps.get_model('auth', 'User')

    user_ct = ContentType.objects.get_for_model(User)

    old_access, _ = Permission.objects.get_or_create(
        codename=OLD_ACCESS, content_type=user_ct,
        defaults={'name': 'Can access Personal'},
    )
    old_edit, _ = Permission.objects.get_or_create(
        codename=OLD_EDIT, content_type=user_ct,
        defaults={'name': 'Can edit Personal'},
    )

    new_access_perms = Permission.objects.filter(
        codename__in=NEW_ACCESS_CODES, content_type=user_ct
    )
    new_edit_perms = Permission.objects.filter(
        codename__in=NEW_EDIT_CODES, content_type=user_ct
    )

    for user in User.objects.filter(user_permissions__in=new_access_perms).distinct():
        user.user_permissions.add(old_access)
    for user in User.objects.filter(user_permissions__in=new_edit_perms).distinct():
        user.user_permissions.add(old_edit)

    new_access_perms.delete()
    new_edit_perms.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0064_alter_recipeingredient_amount_assetphoto'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

