"""
Phase 4.5 of the Personal-module multi-tenancy rollout.

Makes NotificationRecipient workspace-aware for personal notification
types (celebration_reminder, document_expiry). Admin notification types
(daily_report, etc.) keep workspace = NULL and remain effectively global.

Steps:
  1. Add the workspace ForeignKey as nullable.
  2. Drop the unique=True constraint on notification_type so different
     workspaces can each have their own row per personal type.
  3. Backfill: any existing celebration_reminder / document_expiry rows
     (currently workspace=NULL) get assigned to "Demetri's Household".
  4. Add unique_together = (notification_type, workspace) so personal
     types can't be duplicated within a workspace.

Reverse path mirrors the forward steps in reverse.
"""
import django.db.models.deletion
from django.db import migrations, models


HOUSEHOLD_NAME = "Demetri's Household"
PERSONAL_TYPES = ('celebration_reminder', 'document_expiry')

NOTIFICATION_TYPE_CHOICES = [
    ('celebration_reminder', 'Celebration Reminders'),
    ('document_expiry', 'Document Expiry Alerts'),
    ('daily_report', 'Daily Property Management Report'),
    ('new_lease_upload', 'New Lease Upload Reminders'),
    ('expense_needs_approval', 'Expense Needs Approval'),
    ('expense_approved', 'Expense Approved'),
    ('expense_paid', 'Expense Paid'),
    ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'),
    ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'),
    ('invoice_paid', 'Invoice Marked as Paid'),
    ('issue_comments_daily', 'Daily Issue Comments Report'),
    ('issue_comment_urgent', 'Urgent Issue Comment Alert'),
]


def backfill_personal_workspace(apps, schema_editor):
    NotificationRecipient = apps.get_model('pages', 'NotificationRecipient')
    Workspace = apps.get_model('pages', 'Workspace')

    workspace = Workspace.objects.filter(name=HOUSEHOLD_NAME).first()
    if workspace is None:
        # No household workspace exists. If there are no personal-type
        # rows to backfill either, this is fine. If there are, we leave
        # them as workspace=NULL — the next deploy's cron run will log
        # them as orphaned-workspace and skip them, which surfaces the
        # state without crashing.
        return

    NotificationRecipient.objects.filter(
        notification_type__in=PERSONAL_TYPES,
        workspace__isnull=True,
    ).update(workspace=workspace)


def reverse_backfill(apps, schema_editor):
    NotificationRecipient = apps.get_model('pages', 'NotificationRecipient')
    NotificationRecipient.objects.filter(
        notification_type__in=PERSONAL_TYPES,
    ).update(workspace=None)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0068_passport_workspace'),
    ]

    operations = [
        # 1. Add workspace FK as nullable so the alter doesn't fail.
        migrations.AddField(
            model_name='notificationrecipient',
            name='workspace',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notification_recipients',
                to='pages.workspace',
                help_text='Required for personal notification types '
                          '(celebration_reminder, document_expiry); NULL '
                          'for admin types (daily_report, etc.).',
            ),
        ),
        # 2. Drop unique=True so multiple workspaces can each have their
        #    own row for the same personal notification_type.
        migrations.AlterField(
            model_name='notificationrecipient',
            name='notification_type',
            field=models.CharField(
                max_length=50,
                choices=NOTIFICATION_TYPE_CHOICES,
            ),
        ),
        # 3. Backfill existing personal-type rows into Demetri's Household.
        migrations.RunPython(backfill_personal_workspace, reverse_code=reverse_backfill),
        # 4. Add the composite uniqueness constraint.
        migrations.AlterUniqueTogether(
            name='notificationrecipient',
            unique_together={('notification_type', 'workspace')},
        ),
    ]