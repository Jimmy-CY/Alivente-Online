"""
Phase 3 of the Personal-module multi-tenancy rollout.

Adds the workspace ForeignKey to the Passport model and backfills every
existing passport row to "Demetri's Household" (created in Phase 2,
migration 0067).

Three-step migration:
  1. AddField: workspace FK as nullable (so the AddField doesn't fail
     on a populated table).
  2. RunPython: backfill — assign every passport with workspace=NULL to
     the "Demetri's Household" workspace. If no household workspace
     exists but passports do, the migration fails with a clear error.
  3. AlterField: change the workspace FK to non-nullable now that
     every row has a value.

After this migration runs:
  - Every Passport row has a workspace_id pointing to "Demetri's
    Household".
  - New passports created via the view get workspace=<current user's
    workspace> automatically.
  - Queries through Passport.objects.for_user(user) are filtered to
    the user's workspace — no cross-workspace leakage possible.

Reverse path:
  - AlterField back to nullable.
  - Set workspace=NULL on every passport.
  - RemoveField.
"""
import django.db.models.deletion
from django.db import migrations, models


HOUSEHOLD_NAME = "Demetri's Household"


def backfill_workspace(apps, schema_editor):
    Passport = apps.get_model('pages', 'Passport')
    Workspace = apps.get_model('pages', 'Workspace')

    if not Passport.objects.exists():
        return  # Nothing to backfill.

    workspace = Workspace.objects.filter(name=HOUSEHOLD_NAME).first()
    if workspace is None:
        raise RuntimeError(
            f"Cannot backfill Passport.workspace: workspace "
            f"'{HOUSEHOLD_NAME}' does not exist but passports do. "
            f"Apply Phase 2 (migration 0067) first."
        )

    Passport.objects.filter(workspace__isnull=True).update(workspace=workspace)


def reverse_backfill(apps, schema_editor):
    Passport = apps.get_model('pages', 'Passport')
    Passport.objects.all().update(workspace=None)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0067_create_household_workspace'),
    ]

    operations = [
        # 1. Add as nullable so the alter doesn't fail on populated rows.
        migrations.AddField(
            model_name='passport',
            name='workspace',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='passports',
                to='pages.workspace',
                help_text='The workspace this passport belongs to.',
            ),
        ),
        # 2. Backfill every existing passport into Demetri's Household.
        migrations.RunPython(backfill_workspace, reverse_code=reverse_backfill),
        # 3. Now every row has a value, so we can tighten the constraint.
        migrations.AlterField(
            model_name='passport',
            name='workspace',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='passports',
                to='pages.workspace',
                help_text='The workspace this passport belongs to.',
            ),
        ),
    ]