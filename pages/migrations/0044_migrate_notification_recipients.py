# Generated migration for notification recipients

from django.db import migrations, models


def migrate_email_addresses_to_to_addresses(apps, schema_editor):
    """Copy existing email_addresses to to_addresses before removing the old field"""
    NotificationRecipient = apps.get_model('pages', 'NotificationRecipient')
    
    # Copy all existing email_addresses to to_addresses
    for recipient in NotificationRecipient.objects.all():
        recipient.to_addresses = recipient.email_addresses
        recipient.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0043_notificationrecipient'),
    ]

    operations = [
        # 1. Update model options
        migrations.AlterModelOptions(
            name='notificationrecipient',
            options={'verbose_name': 'Notification Recipient', 'verbose_name_plural': 'Notification Recipients'},
        ),
        
        # 2. Add the new to_addresses field (nullable temporarily)
        migrations.AddField(
            model_name='notificationrecipient',
            name='to_addresses',
            field=models.TextField(help_text='Comma-separated TO email addresses (primary recipients)', null=True, blank=True),
        ),
        
        # 3. Add the new cc_addresses field
        migrations.AddField(
            model_name='notificationrecipient',
            name='cc_addresses',
            field=models.TextField(blank=True, default='', help_text='Comma-separated CC email addresses (optional)'),
        ),
        
        # 4. Copy data from email_addresses to to_addresses
        migrations.RunPython(migrate_email_addresses_to_to_addresses, migrations.RunPython.noop),
        
        # 5. Remove the old email_addresses field
        migrations.RemoveField(
            model_name='notificationrecipient',
            name='email_addresses',
        ),
        
        # 6. Make to_addresses non-nullable now that data is migrated
        migrations.AlterField(
            model_name='notificationrecipient',
            name='to_addresses',
            field=models.TextField(help_text='Comma-separated TO email addresses (primary recipients)'),
        ),
        
        # 7. Update notification_type choices to include new types
        migrations.AlterField(
            model_name='notificationrecipient',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('celebration_reminder', 'Celebration Reminders'),
                    ('document_expiry', 'Document Expiry Alerts'),
                    ('daily_report', 'Daily Property Management Report'),
                    ('new_lease_upload', 'New Lease Upload Reminders'),
                    ('expense_needs_approval', 'Expense Needs Approval'),
                    ('expense_approved', 'Expense Approved'),
                    ('expense_paid', 'Expense Paid'),
                    ('friday_status_report_supervisor', 'Friday Status Report (Submitted by Supervisor)'),
                    ('friday_status_report_staff', 'Friday Status Report (Submitted by Staff)')
                ],
                max_length=50,
                unique=True
            ),
        ),
    ]