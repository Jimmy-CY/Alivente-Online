"""
Phase 2 of the Personal-module multi-tenancy rollout.

Creates the "Demetri's Household" workspace and assigns the household
members (Demetrios and angy) to it via UserProfile.workspace.

After this migration runs:
  - Workspace 'Demetri's Household' exists, owned by Demetrios.
  - Demetrios's UserProfile.workspace points at it.
  - angy's UserProfile.workspace points at it.
  - Other users (admin, StellaSimi) remain unassigned (workspace = NULL).

Erene and Alexandra are not yet auth_user records. They will be added
via the User Administration UI in a later phase, at which point they
can be assigned to this same workspace through that UI.

Idempotent: re-running produces the same end state without creating
duplicates. Safe to apply to fresh dev/test environments.

Reverse path:
  - Unassigns workspace from every UserProfile in 'Demetri's Household'
    (required because Workspace is PROTECTed by UserProfile.workspace).
  - Deletes the workspace.
  - The rest of the system is unaffected.
"""
from django.db import migrations


HOUSEHOLD_NAME = "Demetri's Household"
OWNER_USERNAME = "Demetrios"
MEMBER_USERNAMES = ["Demetrios", "angy"]


def create_household(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('pages', 'UserProfile')
    Workspace = apps.get_model('pages', 'Workspace')

    # If the owner doesn't exist (e.g. fresh dev DB without seed users),
    # skip silently rather than blocking the migration chain.
    try:
        owner = User.objects.get(username=OWNER_USERNAME)
    except User.DoesNotExist:
        return

    workspace, _ = Workspace.objects.get_or_create(
        name=HOUSEHOLD_NAME,
        defaults={'owner': owner},
    )

    for username in MEMBER_USERNAMES:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            continue
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.workspace_id is None:
            profile.workspace = workspace
            profile.save()


def remove_household(apps, schema_editor):
    UserProfile = apps.get_model('pages', 'UserProfile')
    Workspace = apps.get_model('pages', 'Workspace')

    # Clear member references first — Workspace is PROTECTed by
    # UserProfile.workspace, so a direct delete would fail otherwise.
    workspaces = Workspace.objects.filter(name=HOUSEHOLD_NAME)
    UserProfile.objects.filter(workspace__in=workspaces).update(workspace=None)
    workspaces.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0066_workspace_and_userprofile_link'),
    ]

    operations = [
        migrations.RunPython(create_household, reverse_code=remove_household),
    ]