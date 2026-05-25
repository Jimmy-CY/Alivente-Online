"""
Phase 5.1 of the Personal-module multi-tenancy rollout.

Makes Contact workspace-aware. Same 3-step pattern as
0068_passport_workspace:

  1. Add the workspace ForeignKey as nullable so AddField doesn't fail
     on the existing populated table.
  2. Backfill every existing Contact row to "Demetri's Household" via
     RunPython.
  3. AlterField to drop null=True, matching the final model state where
     workspace is required.

After this migration:
  - All existing Contacts belong to Demetri's Household.
  - Future Contacts must be assigned a workspace at create time (the
    view layer enforces this via ensure_workspace).
  - CelebrationEvent inherits its workspace through contact.workspace —
    no separate FK on Event.
"""
import django.db.models.deletion
from django.db import migrations, models


HOUSEHOLD_NAME = "Demetri's Household"


def backfill_contact_workspace(apps, schema_editor):
    Contact = apps.get_model('pages', 'Contact')
    Workspace = apps.get_model('pages', 'Workspace')

    workspace = Workspace.objects.filter(name=HOUSEHOLD_NAME).first()
    if workspace is None:
        # No household exists. If Contact has rows, this leaves them
        # workspace=NULL — the next AlterField step will then reject the
        # migration, which is deliberate: better to fail loudly here
        # than ship orphaned Contact rows to a live database.
        return

    Contact.objects.filter(workspace__isnull=True).update(workspace=workspace)


def reverse_backfill(apps, schema_editor):
    Contact = apps.get_model('pages', 'Contact')
    Contact.objects.update(workspace=None)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0069_notificationrecipient_workspace'),
    ]

    operations = [
        # 1. Add workspace FK as nullable so the column can be added to
        #    the existing populated contacts table.
        migrations.AddField(
            model_name='contact',
            name='workspace',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='contacts',
                to='pages.workspace',
            ),
        ),
        # 2. Backfill every existing Contact to Demetri's Household.
        migrations.RunPython(backfill_contact_workspace, reverse_code=reverse_backfill),
        # 3. Drop null=True to match the final model state (FK required).
        migrations.AlterField(
            model_name='contact',
            name='workspace',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='contacts',
                to='pages.workspace',
            ),
        ),
    ]