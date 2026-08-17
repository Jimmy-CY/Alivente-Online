from django.db import migrations, models


class Migration(migrations.Migration):
    """Relabel 'expense_mismatch' - it now covers EVERY invoice upload, not
    only mismatches. The key is deliberately unchanged so any recipients
    already configured for it keep working.

    Label-only change: no column altered, no data touched.
    """

    dependencies = [
        ('pages', '0090_notification_type_expense_mismatch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationrecipient',
            name='notification_type',
            field=models.CharField(choices=[('celebration_reminder', 'Celebration Reminders'), ('document_expiry', 'Document Expiry Alerts'), ('daily_report', 'Daily Property Management Report'), ('new_lease_upload', 'New Lease Upload Reminders'), ('expense_needs_approval', 'Expense Needs Approval'), ('expense_approved', 'Expense Approved'), ('expense_paid', 'Expense Paid'), ('expense_mismatch', 'Expense Invoice Uploaded'), ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'), ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'), ('invoice_paid', 'Invoice Marked as Paid'), ('issue_comments_daily', 'Daily Issue Comments Report'), ('issue_comment_urgent', 'Urgent Issue Comment Alert'), ('physical_invoice_review', 'Physical Invoices Awaiting Approval'), ('physical_invoice_client', 'Physical Invoice to Client')], max_length=50),
        ),
    ]
