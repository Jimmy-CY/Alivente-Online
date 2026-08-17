"""
Notification recipient settings views.

Extracted from the legacy pages/views/main.py during the modular views
split.

Functions
---------
- notification_settings          : Administration-area notifications
                                   (daily report, lease uploads,
                                   invoice/expense events, Friday status
                                   report, issue comments). Backed by the
                                   NotificationRecipient model: GET renders
                                   the form with current recipients; POST
                                   upserts the recipient row for the chosen
                                   notification_type.
- personal_notification_settings : RETIRED. Personal notification opt-ins
                                   now live on the Household Members roster
                                   as per-member, per-type toggles. Kept as
                                   a permanent redirect so old links,
                                   bookmarks and nav entries still resolve.

Auth tiers
----------
notification_settings          -> auth.can_access_administration
personal_notification_settings -> login only (the redirect target enforces
                                  its own composite Personal permission).
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
        'physical_invoice_review',
        'physical_invoice_client',
        'expense_needs_approval',
        'expense_approved',
        'expense_paid',
        'expense_mismatch',
        'friday_status_report_supervisor',
        'friday_status_report_staff',
        'issue_comments_daily',
        'issue_comment_urgent',
    ]

    # NOTE: local dict (not the enclosing function); named distinctly to
    # avoid shadowing `notification_settings`. The template context key
    # stays 'notification_settings' (template contract).
    settings_by_type = {}

    for type_code, type_name in NotificationRecipient.NOTIFICATION_TYPES:
        if type_code in admin_types:
            try:
                recipient = NotificationRecipient.objects.get(notification_type=type_code)
                settings_by_type[type_code] = {
                    'name': type_name,
                    'to_emails': recipient.to_addresses,
                    'cc_emails': recipient.cc_addresses
                }
            except NotificationRecipient.DoesNotExist:
                settings_by_type[type_code] = {
                    'name': type_name,
                    'to_emails': '',
                    'cc_emails': ''
                }

    return render(request, 'notification_settings.html', {
        'notification_settings': settings_by_type,
    })


@login_required
def personal_notification_settings(request):
    """
    Retired screen. Personal notification opt-ins (celebration reminders,
    document-expiry alerts) are now managed per-member on the Household
    Members roster, which composes them with per-event relevance.

    Kept as a permanent redirect so existing links, bookmarks and any nav
    entries that still point here land on the roster instead of 404-ing.
    The roster screen enforces its own composite Personal permission.
    """
    return redirect('household_member_management')