"""
Household member roster (the workspace audience) + notification opt-ins.

A workspace-level screen, lifted out of Celebrations because the roster
(HouseholdMember) is shared across Personal modules: it is the audience for
celebration reminders and document-expiry alerts (and, later, recipes).
The model lives in pages/models.py keyed on Workspace; only this view, its
URL, nav and permission sit at the Personal level.

This screen is also the people-and-notifications hub: each member carries a
per-type subscription (MemberNotificationSubscription) that decides whether
they receive that notification type. Those toggles replace the old
comma-separated NotificationRecipient CSV editor.

Functions
---------
- household_member_management : list + add / edit / toggle-active / delete
                                members, and toggle each member's per-type
                                notification subscriptions.

Auth tiers
----------
View          : any of can_access_passports / can_access_celebrations
                (composite -- the roster cuts across the Personal sub-modules
                that consume it).
Identity write: any of the matching can_edit_* permissions (add / edit /
                activate / delete a member).
Subscription  : gated PER TYPE, mirroring the old personal-settings page --
                a Celebrations column needs can_access_celebrations to see
                and can_edit_celebrations to change; Document expiry needs
                can_access_passports / can_edit_passports.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from ..models import HouseholdMember, MemberNotificationSubscription
from pages.workspace import ensure_workspace


# Personal notification types surfaced as toggle columns, with the per-type
# access / edit permissions. Stays in sync with
# NotificationRecipient.PERSONAL_NOTIFICATION_TYPES.
#   (type_code, column_label, access_perm, edit_perm)
PERSONAL_TYPE_PERMS = [
    ('celebration_reminder', 'Celebrations', 'can_access_celebrations', 'can_edit_celebrations'),
    ('document_expiry',      'Doc expiry',   'can_access_passports',    'can_edit_passports'),
]
_TYPE_LABEL = {code: label for code, label, _a, _e in PERSONAL_TYPE_PERMS}
_TYPE_EDIT_PERM = {code: edit for code, _l, _a, edit in PERSONAL_TYPE_PERMS}


def _save_member(request, workspace, member=None):
    """Create or update a HouseholdMember from POST data. Validates name
    uniqueness within the workspace, that any linked user belongs to it, and
    that the member has an email (derived from the linked login if blank)."""
    name = (request.POST.get('name') or '').strip()
    email = (request.POST.get('email') or '').strip() or None
    is_active = request.POST.get('is_active') == 'on'
    user_id = request.POST.get('user_id') or None

    if not name:
        messages.error(request, 'Name is required.')
        return

    clash = HouseholdMember.objects.for_user(request.user).filter(name__iexact=name)
    if member is not None:
        clash = clash.exclude(id=member.id)
    if clash.exists():
        messages.error(request, f'A member named "{name}" already exists.')
        return

    user = None
    if user_id:
        prof = workspace.members.filter(user_id=user_id).first()
        if prof is None:
            messages.error(request, 'Selected user is not part of this workspace.')
            return
        user = prof.user
        other = HouseholdMember.objects.for_user(request.user).filter(user=user)
        if member is not None:
            other = other.exclude(id=member.id)
        if other.exists():
            label = user.get_full_name() or user.username
            messages.error(request, f'{label} is already linked to another member.')
            return

    # Email is required. If none was typed but a login is linked, take the
    # login's email; otherwise reject -- a member needs an email to be notified.
    if not email and user is not None and (user.email or '').strip():
        email = user.email.strip()
    if not email:
        messages.error(request, 'Email is required (a member needs an email to receive notifications).')
        return

    if member is None:
        member = HouseholdMember(workspace=workspace)
    member.name = name
    member.email = email
    member.user = user
    member.is_active = is_active
    member.save()
    messages.success(request, f'Member "{name}" saved.')


@login_required
@user_passes_test(lambda u: (
    u.has_perm('auth.can_access_passports')
    or u.has_perm('auth.can_access_celebrations')
))
def household_member_management(request):
    """Manage the workspace's household members and their notification opt-ins."""
    workspace = ensure_workspace(request.user)
    can_edit = (
        request.user.has_perm('auth.can_edit_passports')
        or request.user.has_perm('auth.can_edit_celebrations')
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        # Subscription toggles are gated per type (not by the composite
        # identity-edit gate), so handle them before the can_edit block.
        if action == 'toggle_subscription':
            member = HouseholdMember.objects.for_user(request.user).filter(
                id=request.POST.get('member_id')).first()
            ntype = request.POST.get('notification_type')
            if member is None:
                messages.error(request, 'Member not found.')
            elif ntype not in _TYPE_EDIT_PERM:
                messages.error(request, 'Invalid notification type.')
            elif not request.user.has_perm(f'auth.{_TYPE_EDIT_PERM[ntype]}'):
                messages.error(request, 'You do not have permission to change that subscription.')
            else:
                desired = request.POST.get('subscribe') == 'on'
                MemberNotificationSubscription.objects.update_or_create(
                    member=member,
                    notification_type=ntype,
                    defaults={'is_active': desired},
                )
                messages.success(
                    request,
                    f"{member.name}: {_TYPE_LABEL[ntype]} notifications "
                    f"{'on' if desired else 'off'}."
                )
            return redirect('household_member_management')

        # All remaining actions are identity CRUD -- composite edit gate.
        if not can_edit:
            messages.error(request, 'You do not have permission to manage household members.')
            return redirect('household_member_management')

        if action == 'add_member':
            _save_member(request, workspace, member=None)

        elif action == 'edit_member':
            member = HouseholdMember.objects.for_user(request.user).filter(
                id=request.POST.get('member_id')).first()
            if member is None:
                messages.error(request, 'Member not found.')
            else:
                _save_member(request, workspace, member=member)

        elif action == 'toggle_active':
            member = HouseholdMember.objects.for_user(request.user).filter(
                id=request.POST.get('member_id')).first()
            if member is None:
                messages.error(request, 'Member not found.')
            else:
                member.is_active = not member.is_active
                member.save()
                messages.success(request, f"{member.name} {'activated' if member.is_active else 'deactivated'}.")

        elif action == 'delete_member':
            member = HouseholdMember.objects.for_user(request.user).filter(
                id=request.POST.get('member_id')).first()
            if member is None:
                messages.error(request, 'Member not found.')
            else:
                name = member.name
                member.delete()
                messages.success(request, f'Member "{name}" deleted.')

        return redirect('household_member_management')

    # GET -----------------------------------------------------------------
    members = list(
        HouseholdMember.objects.for_user(request.user)
        .select_related('user')
        .order_by('name')
    )

    # Which subscription columns this user may see, and may edit.
    sub_columns = [
        {'code': code, 'label': label, 'can_edit': request.user.has_perm(f'auth.{edit_perm}')}
        for code, label, access_perm, edit_perm in PERSONAL_TYPE_PERMS
        if request.user.has_perm(f'auth.{access_perm}')
    ]
    visible_codes = [c['code'] for c in sub_columns]

    # One query for every active subscription in the workspace -> a set of
    # (member_id, type_code) we can test in memory.
    active_subs = set(
        MemberNotificationSubscription.objects.filter(
            member__workspace=workspace,
            notification_type__in=visible_codes,
            is_active=True,
        ).values_list('member_id', 'notification_type')
    )

    # Per-member cells aligned to sub_columns (avoids dynamic dict lookup
    # in the template).
    for m in members:
        m.sub_cells = [
            {
                'code': col['code'],
                'label': col['label'],
                'can_edit': col['can_edit'],
                'on': (m.id, col['code']) in active_subs,
            }
            for col in sub_columns
        ]

    # Login-account options for the link dropdown. Deduped by user (a user
    # can only appear once), labelled "Name (email)" so two people who share
    # a display name are distinguishable, and carrying the email so the form
    # can auto-fill it when a login is chosen.
    workspace_users = []
    seen_user_ids = set()
    for p in workspace.members.select_related('user').all():
        u = p.user
        if u is None or u.id in seen_user_ids:
            continue
        seen_user_ids.add(u.id)
        display = u.get_full_name() or u.username
        detail = (u.email or '').strip() or u.username
        workspace_users.append({
            'id': u.id,
            'label': f'{display} ({detail})' if detail else display,
            'email': (u.email or '').strip(),
        })
    workspace_users.sort(key=lambda d: d['label'].lower())

    return render(request, 'household_member_management.html', {
        'members': members,
        'workspace': workspace,
        'workspace_users': workspace_users,
        'can_edit': can_edit,
        'sub_columns': sub_columns,
    })