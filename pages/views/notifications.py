"""
Notification settings views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split.
Covers the two screens that manage email notification recipients —
the admin variant (for administration-area notifications like daily
reports, lease uploads, invoice/expense events, Friday status report,
issue comments) and the personal variant (for celebration reminders
and document expiry alerts).

Both share the NotificationRecipient model and follow the same shape:
GET renders the form populated with current recipients, POST upserts
the recipient row for the chosen notification_type.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from ..models import NotificationRecipient


@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
def notification_settings(request):
    """Manage email notification recipients for administration items"""

    # Handle form submission
    if request.method == 'POST':
        notification_type = request.POST.get('notification_type')
        to_addresses = request.POST.get('to_addresses', '')
        cc_addresses = request.POST.get('cc_addresses', '')

        recipient, created = NotificationRecipient.objects.get_or_create(
            notification_type=notification_type,
            defaults={'created_by': request.user}
        )
        recipient.to_addresses = to_addresses
        recipient.cc_addresses = cc_addresses
        recipient.save()

        messages.success(request, f'{recipient.get_notification_type_display()} email addresses updated successfully!')
        return redirect('notification_settings')

    # Get only administration notification types
    admin_types = [
        'daily_report',
        'new_lease_upload',
        'invoice_paid',
        'expense_needs_approval',
        'expense_approved',
        'expense_paid',
        'friday_status_report_supervisor',
        'friday_status_report_staff',
        'issue_comments_daily',
        'issue_comment_urgent',
    ]

    notification_settings = {}

    for type_code, type_name in NotificationRecipient.NOTIFICATION_TYPES:
        if type_code in admin_types:
            try:
                recipient = NotificationRecipient.objects.get(notification_type=type_code)
                notification_settings[type_code] = {
                    'name': type_name,
                    'to_emails': recipient.to_addresses,
                    'cc_emails': recipient.cc_addresses
                }
            except NotificationRecipient.DoesNotExist:
                notification_settings[type_code] = {
                    'name': type_name,
                    'to_emails': '',
                    'cc_emails': ''
                }

    return render(request, 'notification_settings.html', {
        'notification_settings': notification_settings,
    })


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def personal_notification_settings(request):
    """Manage email notification recipients for personal items"""

    # Handle form submission
    if request.method == 'POST':
        # Edit-level permission required to change notification settings
        if not request.user.has_perm('auth.can_edit_personal'):
            messages.error(request, 'You do not have permission to edit notification settings.')
            return redirect('personal_notification_settings')

        notification_type = request.POST.get('notification_type')
        to_addresses = request.POST.get('to_addresses', '')
        cc_addresses = request.POST.get('cc_addresses', '')

        recipient, created = NotificationRecipient.objects.get_or_create(
            notification_type=notification_type,
            defaults={'created_by': request.user}
        )
        recipient.to_addresses = to_addresses
        recipient.cc_addresses = cc_addresses
        recipient.save()

        messages.success(request, f'{recipient.get_notification_type_display()} email addresses updated successfully!')
        return redirect('personal_notification_settings')

    # Get only personal notification types
    personal_types = ['celebration_reminder', 'document_expiry']

    notification_settings = {}

    for type_code, type_name in NotificationRecipient.NOTIFICATION_TYPES:
        if type_code in personal_types:
            try:
                recipient = NotificationRecipient.objects.get(notification_type=type_code)
                notification_settings[type_code] = {
                    'name': type_name,
                    'to_emails': recipient.to_addresses,
                    'cc_emails': recipient.cc_addresses
                }
            except NotificationRecipient.DoesNotExist:
                notification_settings[type_code] = {
                    'name': type_name,
                    'to_emails': '',
                    'cc_emails': ''
                }

    return render(request, 'personal_notification_settings.html', {
        'notification_settings': notification_settings,
    })