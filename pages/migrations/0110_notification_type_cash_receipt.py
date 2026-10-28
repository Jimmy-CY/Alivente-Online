# -*- coding: utf-8 -*-
"""CR-2, 27 Oct 2026 - emailing a cash receipt.

Adds CashReceipt.sent_to (who the last email went to) and the
'cash_receipt_payer' notification type. No data is changed.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0109_ti1_identity_numbers'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashreceipt',
            name='sent_to',
            field=models.TextField(blank=True, default='', help_text='The addresses the receipt was last emailed to.'),
        ),
        migrations.AlterField(
            model_name='notificationrecipient',
            name='notification_type',
            field=models.CharField(choices=[('celebration_reminder', 'Celebration Reminders'), ('document_expiry', 'Document Expiry Alerts'), ('daily_report', 'Daily Property Management Report'), ('new_lease_upload', 'New Lease Upload Reminders'), ('expense_needs_approval', 'Expense Needs Approval'), ('expense_approved', 'Expense Approved'), ('expense_paid', 'Expense Paid'), ('expense_mismatch', 'Expense Invoice Uploaded'), ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'), ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)'), ('invoice_paid', 'Invoice Marked as Paid'), ('issue_comments_daily', 'Daily Issue Comments Report'), ('issue_comment_urgent', 'Urgent Issue Comment Alert'), ('physical_invoice_review', 'Physical Invoices Awaiting Approval'), ('physical_invoice_client', 'Physical Invoice to Client'), ('cash_receipt_payer', 'Cash Receipt to Payer'), ('password_reset_requested', 'Password Reset Requested')], max_length=50),
        ),
    ]
