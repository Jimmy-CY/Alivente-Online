"""
Notification recipient settings views.

Extracted from the legacy pages/views/main.py during the modular views
split. Two screens manage who receives system e-mails, both backed by
the NotificationRecipient model: GET renders the form populated with the
current recipients; POST upserts the recipient row for the chosen
notification_type.

Functions
---------
- notification_settings          : Administration-area notifications
                                   (daily report, lease uploads,
                                   invoice/expense events, Friday status
                                   report, issue comments).
- personal_notification_settings : Personal notifications (celebration
                                   reminders, document-expiry alerts).

Auth tiers
----------
notification_settings          -> auth.can_access_administration
personal_notification_settings -> any of auth.can_access_passports,
                                  auth.can_access_recipes,
                                  auth.can_access_celebrations,
                                  auth.can_access_crs (composite — personal
                                  notifications cut across all four Personal
                                  sub-modules, so any sub-module access
                                  grants visibility). POST additionally
                                  requires any of the matching can_edit_*
                                  permissions; the admin view has no
                                  separate edit gate - access to
                                  administration is sufficient there.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.shortcuts import redirect, render

from ..models import NotificationRecipient
from pages.workspace import ensure_workspace


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
@user_passes_test(lambda u: (
    u.has_perm('auth.can_access_passports')
    or u.has_perm('auth.can_access_celebrations')
))
def personal_notification_settings(request):
    """
    Manage email recipients for the current user's workspace.

    Visibility is gated per section: a user only sees the Celebration card
    if they have can_access_celebrations, only sees the Document Expiry card
    if they have can_access_passports. Editing is further gated by
    can_edit_celebrations / can_edit_passports respectively.

    Each personal notification type stores one row per workspace, so two
    households can independently configure their own recipients without
    leaking into each other.
    """
    workspace = ensure_workspace(request.user)

    # type_code -> (access_perm, edit_perm). Stays in sync with
    # NotificationRecipient.PERSONAL_NOTIFICATION_TYPES.
    PERSONAL_TYPES_PERMS = {
        'celebration_reminder': ('can_access_celebrations', 'can_edit_celebrations'),
        'document_expiry':      ('can_access_passports',    'can_edit_passports'),
    }

    if request.method == 'POST':
        notification_type = request.POST.get('notification_type')

        if notification_type not in PERSONAL_TYPES_PERMS:
            messages.error(request, 'Invalid notification type.')
            return redirect('personal_notification_settings')

        access_perm, edit_perm = PERSONAL_TYPES_PERMS[notification_type]

        # Per-section edit check. Block the case where a user with, say,
        # can_edit_celebrations only tries to POST a document_expiry update.
        if not request.user.has_perm(f'auth.{edit_perm}'):
            messages.error(
                request,
                'You do not have permission to edit these notification settings.'
            )
            return redirect('personal_notification_settings')

        to_addresses = request.POST.get('to_addresses', '').strip()
        cc_addresses = request.POST.get('cc_addresses', '').strip()

        recipient, _created = NotificationRecipient.objects.get_or_create(
            notification_type=notification_type,
            workspace=workspace,
            defaults={
                'created_by': request.user,
                'to_addresses': to_addresses,
                'cc_addresses': cc_addresses,
            },
        )
        recipient.to_addresses = to_addresses
        recipient.cc_addresses = cc_addresses
        recipient.save()

        messages.success(
            request,
            f'{recipient.get_notification_type_display()} email addresses updated successfully!'
        )
        return redirect('personal_notification_settings')

    # GET: build settings dict, only including types the user can access.
    notification_settings = {}
    type_display_map = dict(NotificationRecipient.NOTIFICATION_TYPES)

    for type_code, (access_perm, edit_perm) in PERSONAL_TYPES_PERMS.items():
        if not request.user.has_perm(f'auth.{access_perm}'):
            continue

        recipient = NotificationRecipient.objects.filter(
            notification_type=type_code,
            workspace=workspace,
        ).first()

        notification_settings[type_code] = {
            'name': type_display_map.get(type_code, type_code),
            'to_emails': recipient.to_addresses if recipient else '',
            'cc_emails': recipient.cc_addresses if recipient else '',
            'can_edit': request.user.has_perm(f'auth.{edit_perm}'),
        }

    return render(request, 'personal_notification_settings.html', {
        'notification_settings': notification_settings,
        'workspace': workspace,
    })