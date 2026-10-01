from django.db import migrations, models


class Migration(migrations.Migration):
    """Add 'password_reset_requested' to the notification-type choices.

    Section A round A1. Choices-only change: no column alteration, no data
    migration, no risk to existing rows. It exists so the notice that goes
    out when somebody asks for a password link can be configured from
    Administration -> Notification Settings instead of being hardcoded.

    THE MODEL IS HALF THE CHANGE. notification_settings() filters the
    choices through a hardcoded admin_types list in
    pages/views/notifications.py; a type missing from that list renders on
    no screen and reports no error. Round A1 adds it to both.
                                                  [test_auth_flow.py]
    """

    dependencies = [
        ('pages', '0095_none_columns'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationrecipient',
            name='notification_type',
            field=models.CharField(choices=[('celebration_reminder', 'Celebration Reminders'), ('document_expiry', 'Document Expiry Alerts'), ('daily_report', 'Daily Property Management Report'), ('new_lease_upload', 'New Lease Upload Reminders'), ('expense_needs_approval', 'Expense Needs Approval'), ('expense_approved', 'Expense Approved'), ('expense_paid', 'Expense Paid'), ('expense_mismatch', 'Expense Invoice Uploaded'), ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'), ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'), ('invoice_paid', 'Invoice Marked as Paid'), ('issue_comments_daily', 'Daily Issue Comments Report'), ('issue_comment_urgent', 'Urgent Issue Comment Alert'), ('physical_invoice_review', 'Physical Invoices Awaiting Approval'), ('physical_invoice_client', 'Physical Invoice to Client'), ('password_reset_requested', 'Password Reset Requested')], max_length=50),
        ),
    ]
