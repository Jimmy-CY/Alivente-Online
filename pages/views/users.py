"""
User administration views.

Extracted from the legacy pages/views/main.py during the modular views
split. Covers the superuser-only User Administration screens: list,
add, edit, per-user module permissions, and permanent delete (with
safety checks).

All five views share the same three-decorator stack:
    @login_required
    @user_passes_test(lambda u: u.is_superuser)
    @permission_required('auth.can_access_administration', raise_exception=True)

Note: self-service profile editing (my_profile) is intentionally NOT
here - it is a different concern (a regular user updating their own
details, with a different decorator set) and lives in its own module.
(The original docstring said it "stays in main.py"; main.py was removed
during the split, so that reference is obsolete.)

Functions
---------
- user_administration : List users; POST toggles a user's active flag
                        (cannot disable yourself).
- user_add            : Create a user with NO USABLE PASSWORD and email
                        them a link to choose one. Email is required.
- user_edit           : Update a user; cannot strip your own superuser
                        status. No password fields since round A1.
- user_reset_password : POST-only. Emails a set-password link. Does not
                        clear the current password - see the view.
- user_permissions    : Grant/revoke per-module access & edit
                        permissions (edit implies access).
- user_delete         : Permanently delete a user (must be disabled,
                        not yourself, and not the last superuser).
"""

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.contrib.auth.models import Permission, User
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType
from pages.permissions import MODULE_PERMISSIONS
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from pages import password_reset as pwr
# The public flow owns the sending; this module owns the admin trigger.
# No cycle: views/auth.py imports nothing from here.
from .auth import _notify_reset_requested, _send_link

from ..models import UserProfile, Workspace


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def user_administration(request):
    """User administration screen - list all users"""

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_active':
            user_id = request.POST.get('user_id')
            new_status = request.POST.get('new_status') == '1'
            try:
                target_user = User.objects.get(id=user_id)
                # Prevent disabling yourself
                if target_user == request.user:
                    messages.error(request, 'You cannot disable your own account.')
                else:
                    target_user.is_active = new_status
                    target_user.save()
                    status_text = 'enabled' if new_status else 'disabled'
                    messages.success(request, f'User "{target_user.username}" has been {status_text}.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

        return redirect('user_administration')

    # GET request
    users = User.objects.select_related('profile').order_by('username')

    # Ensure every user has a profile
    for user in users:
        if not hasattr(user, 'profile'):
            UserProfile.objects.get_or_create(user=user)

    # Re-query after ensuring profiles exist so select_related('profile')
    # reflects any UserProfile rows just created above (the first queryset
    # was evaluated before those rows existed). This double query is
    # intentional - do not collapse it.
    users = User.objects.select_related('profile').order_by('username')

    context = {
        'users': users,
    }

    return render(request, 'user_administration.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def user_add(request):
    """Add a new user"""

    workspaces = Workspace.objects.all().order_by('name')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'user')
        is_active = request.POST.get('is_active') == '1'
        workspace_id = request.POST.get('workspace_id', '').strip()

        # Validation
        errors = []
        if not username:
            errors.append('Username is required.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        # EMAIL IS REQUIRED NOW - Demetri: "Email must be required on Add
        # User." It has to be. The account is created with NO USABLE
        # PASSWORD and an emailed link is the only way one ever gets set,
        # so an account with no address has no route in at all.
        # Show-UserEmails.py was written before this round to check that no
        # existing account was already in that state. None was.
        if not email:
            errors.append('Email address is required - the new user is sent '
                          'a link to choose their own password, so there has '
                          'to be somewhere to send it.')
        # iexact, not exact. Forgot Password matches the address
        # case-insensitively, so two accounts differing only in case would
        # both answer one request and "which account did I just reset"
        # would have no answer.
        if email and User.objects.filter(email__iexact=email).exists():
            errors.append('A user with this email already exists.')

        # Validate workspace_id (empty string = unassigned, which is allowed)
        workspace = None
        if workspace_id:
            try:
                workspace = Workspace.objects.get(id=workspace_id)
            except Workspace.DoesNotExist:
                errors.append('Selected workspace does not exist.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'user_add.html', {
                'form_data': request.POST,
                'workspaces': workspaces,
            })

        # Create the user WITH NO USABLE PASSWORD. password=None makes
        # create_user call set_unusable_password(), so there is no password
        # for anybody to know - not the new user, not the administrator
        # creating them. The invitation below is the only way in, which is
        # the entire point of the change.
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=None,
            first_name=first_name,
            last_name=last_name,
        )
        new_user.is_active = is_active
        if role == 'superuser':
            new_user.is_superuser = True
            new_user.is_staff = True
        new_user.save()

        # Ensure profile exists, and assign workspace if one was selected.
        # Empty selection means the user gets their own workspace auto-created
        # the first time they touch a Personal module.
        profile, _ = UserProfile.objects.get_or_create(user=new_user)
        if workspace is not None:
            profile.workspace = workspace
            profile.save(update_fields=['workspace', 'updated_at'])

        # THE INVITATION - AND A LOUD FAILURE IF IT DOES NOT GO OUT.
        #
        # The account is NOT rolled back on a mail failure. Rolling it back
        # would throw away the role, the status and the workspace the
        # administrator just set, and Reset Password on the user list
        # retries the send in one click. What must never happen is a
        # SILENT failure: this account has an unusable password, so with no
        # email nobody can get into it and nothing on screen would say so.
        if _send_link(request, new_user, pwr.MODE_WELCOME):
            messages.success(
                request,
                f'User "{username}" created. A link to choose a password has '
                f'been emailed to {email}.')
        else:
            messages.error(
                request,
                f'User "{username}" was created, BUT THE INVITATION EMAIL DID '
                f'NOT GO OUT to {email}. They cannot log in until it does - '
                f'use Reset Password on the user list to send it again.')
        return redirect('user_administration')

    return render(request, 'user_add.html', {
        'form_data': {},
        'workspaces': workspaces,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def user_edit(request, user_id):
    """Edit an existing user"""

    target_user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    workspaces = Workspace.objects.all().order_by('name')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'user')
        is_active = request.POST.get('is_active') == '1'
        workspace_id = request.POST.get('workspace_id', '').strip()

        # NO PASSWORD FIELDS HERE ANY MORE - A1. The administrator does not
        # type passwords; Reset Password emails a link. See
        # user_reset_password below.
        errors = []
        # REQUIRED ON EDIT TOO, which is one step past what Demetri asked
        # for ("Email must be required on Add User") and follows from it:
        # if an edit could CLEAR the address, the account it cleared would
        # lose its only route in, and Add User's rule would guard nothing.
        if not email:
            errors.append('Email address is required - it is the only way '
                          'this account can be sent a password link.')
        if email and User.objects.filter(email__iexact=email).exclude(id=user_id).exists():
            errors.append('A user with this email already exists.')

        # Validate workspace_id (empty string = unassigned)
        workspace = None
        if workspace_id:
            try:
                workspace = Workspace.objects.get(id=workspace_id)
            except Workspace.DoesNotExist:
                errors.append('Selected workspace does not exist.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'user_edit.html', {
                'target_user': target_user,
                'profile': profile,
                'workspaces': workspaces,
            })

        # Update user
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email

        # Prevent disabling yourself. The "Active" checkbox is disabled in the
        # UI when target == request.user, which means the browser doesn't
        # submit it at all; without this guard the view sees is_active=False
        # and silently locks the user out of their own account.
        if target_user != request.user:
            target_user.is_active = is_active

        # Prevent removing your own superuser status
        if target_user != request.user:
            if role == 'superuser':
                target_user.is_superuser = True
                target_user.is_staff = True
            else:
                target_user.is_superuser = False
                target_user.is_staff = False

        target_user.save()

        # Update workspace assignment. Setting workspace=None unassigns the
        # user (they get their own workspace auto-created on next access).
        new_workspace_id = workspace.id if workspace else None
        if profile.workspace_id != new_workspace_id:
            profile.workspace = workspace
            profile.save(update_fields=['workspace', 'updated_at'])

        messages.success(request, f'User "{target_user.username}" updated successfully!')
        return redirect('user_administration')

    return render(request, 'user_edit.html', {
        'target_user': target_user,
        'profile': profile,
        'workspaces': workspaces,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def user_permissions(request, user_id):
    """Manage module permissions for a user"""

    target_user = get_object_or_404(User, id=user_id)

    # Define all available module permissions.
    # edit_codename: set this to enable add/edit/delete control for the module.
    # Leave as None for modules that don't yet have edit-level control.
    # ONE definition, in pages/permissions.py. This list and the seeder's copy
    # in views_setup.py had drifted five modules and an entire tier apart.
    all_permissions = MODULE_PERMISSIONS

    # Ensure all permissions exist in the database
    content_type = ContentType.objects.get_for_model(User)
    for perm in all_permissions:
        Permission.objects.get_or_create(
            codename=perm['codename'],
            content_type=content_type,
            defaults={'name': f"Can access {perm['label']}"}
        )
        if perm['edit_codename']:
            Permission.objects.get_or_create(
                codename=perm['edit_codename'],
                content_type=content_type,
                defaults={'name': f"Can edit {perm['label']}"}
            )

    if request.method == 'POST':
        submitted = request.POST.getlist('permissions')

        for perm in all_permissions:
            # Handle access permission
            access_permission = Permission.objects.get(
                codename=perm['codename'],
                content_type=content_type
            )
            has_access = perm['codename'] in submitted
            if has_access:
                target_user.user_permissions.add(access_permission)
            else:
                target_user.user_permissions.remove(access_permission)

            # Handle edit permission (if applicable)
            if perm['edit_codename']:
                edit_permission = Permission.objects.get(
                    codename=perm['edit_codename'],
                    content_type=content_type
                )
                # Safety: edit requires access. If access isn't granted, revoke edit
                # even if it was somehow submitted (e.g. via tampered form).
                if has_access and perm['edit_codename'] in submitted:
                    target_user.user_permissions.add(edit_permission)
                else:
                    target_user.user_permissions.remove(edit_permission)

        messages.success(request, f'Permissions updated for "{target_user.username}".')
        return redirect('user_administration')

    # GET - build list with current status
    user_perm_codenames = set(
        target_user.user_permissions.filter(
            content_type=content_type
        ).values_list('codename', flat=True)
    )

    for perm in all_permissions:
        perm['granted'] = perm['codename'] in user_perm_codenames
        if perm['edit_codename']:
            perm['edit_granted'] = perm['edit_codename'] in user_perm_codenames
        else:
            perm['edit_granted'] = False

    context = {
        'target_user': target_user,
        'all_permissions': all_permissions,
    }

    return render(request, 'user_permissions.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def user_delete(request, user_id):
    """Permanently delete a disabled user"""

    target_user = get_object_or_404(User, id=user_id)

    # Safety checks
    if target_user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_administration')

    if target_user.is_active:
        messages.error(request, 'You must disable a user before deleting them.')
        return redirect('user_administration')

    # Check we're not deleting the last superuser
    if target_user.is_superuser:
        superuser_count = User.objects.filter(is_superuser=True, is_active=True).count()
        if superuser_count <= 1:
            messages.error(request, 'Cannot delete the last superuser account.')
            return redirect('user_administration')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f'User "{username}" has been permanently deleted.')
        return redirect('user_administration')

    return redirect('user_administration')


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
@require_POST
def user_reset_password(request, user_id):
    """Email this user a link to set a new password.

    Demetri: "If I reset a user's Password, I should get a popup coming up
    that tells me that an email will be sent to the user... When I press
    OK, it needs to draft a standard Password Reset email."

    The popup is the confirm modal on the user list and on the edit screen;
    it names the address before anything is sent. This view is what OK
    does.

    WHAT IT DOES NOT DO: clear the current password. That is deliberate and
    it is the fail-safe order. If the send fails - wrong address, SMTP
    down, Gmail throttling - the person can still log in exactly as they
    could a minute ago. Clear it first and a failed send locks somebody out
    of a system they could reach before an administrator tried to help
    them. The old password dies when the emailed link is USED, because the
    token is derived from the password hash.

    THE ADMINISTRATOR IS TREATED IDENTICALLY. Demetri asked: "Does this
    mean that the admin user is treated in exactly the same way?" Yes.
    There is no branch on is_superuser anywhere in this flow. The only
    difference is that the courtesy notice is suppressed when the person
    resetting is the person being reset.

    @require_POST is innermost, below the auth decorators - the order
    test_require_post.py section 3 proves: outermost, a logged-out caller
    would get 405 instead of the login page, which both answers wrongly and
    confirms the URL exists.
    """
    target_user = get_object_or_404(User, id=user_id)
    address = (target_user.email or '').strip()

    if not address:
        messages.error(
            request,
            f'"{target_user.username}" has no email address, so there is '
            f'nowhere to send a link. Add one on their Edit screen first.')
        return redirect('user_administration')

    if _send_link(request, target_user, pwr.MODE_RESET):
        _notify_reset_requested(request, target_user)
        messages.success(
            request,
            f'A link to set a new password has been emailed to {address}. '
            f'It works once and expires after three days. "'
            f'{target_user.username}" can still log in with their current '
            f'password until they use it.')
    else:
        # LOUD, because the alternative is somebody waiting for an email
        # that was never sent.
        messages.error(
            request,
            f'THE EMAIL DID NOT GO OUT to {address}. "'
            f'{target_user.username}" has NOT been sent a link - their '
            f'current password still works. Check the mail settings and '
            f'try again.')
    return redirect('user_administration')


# ===========================================================================
# Workspace Management
# ===========================================================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def workspace_management(request):
    """List all workspaces with owner, member count, and actions."""
    workspaces = (
        Workspace.objects
        .select_related('owner')
        .annotate(member_count=Count('members'))
        .order_by('name')
    )

    # Pre-fetch members for the count tooltip and edit-page reuse.
    for ws in workspaces:
        ws.member_list = list(ws.members.select_related('user').order_by('user__username'))

    return render(request, 'workspace_management.html', {
        'workspaces': workspaces,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def workspace_add(request):
    """Create a new workspace."""
    users = User.objects.all().order_by('username')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        owner_id = request.POST.get('owner_id', '').strip()

        errors = []
        if not name:
            errors.append('Workspace name is required.')

        owner = None
        if not owner_id:
            errors.append('Owner is required.')
        else:
            try:
                owner = User.objects.get(id=owner_id)
            except User.DoesNotExist:
                errors.append('Selected owner does not exist.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'workspace_add.html', {
                'form_data': request.POST,
                'users': users,
            })

        Workspace.objects.create(name=name, owner=owner)
        messages.success(request, f'Workspace "{name}" created successfully!')
        return redirect('workspace_management')

    return render(request, 'workspace_add.html', {
        'form_data': {},
        'users': users,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def workspace_edit(request, workspace_id):
    """Edit a workspace's name and owner; display read-only member list."""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    users = User.objects.all().order_by('username')
    members = workspace.members.select_related('user').order_by('user__username')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        owner_id = request.POST.get('owner_id', '').strip()

        errors = []
        if not name:
            errors.append('Workspace name is required.')

        owner = None
        if not owner_id:
            errors.append('Owner is required.')
        else:
            try:
                owner = User.objects.get(id=owner_id)
            except User.DoesNotExist:
                errors.append('Selected owner does not exist.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'workspace_edit.html', {
                'workspace': workspace,
                'users': users,
                'members': members,
            })

        workspace.name = name
        workspace.owner = owner
        workspace.save()
        messages.success(request, f'Workspace "{name}" updated successfully!')
        return redirect('workspace_management')

    return render(request, 'workspace_edit.html', {
        'workspace': workspace,
        'users': users,
        'members': members,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def workspace_delete(request, workspace_id):
    """Permanently delete a workspace (only if it has zero members)."""
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if workspace.members.exists():
        messages.error(
            request,
            f'Cannot delete workspace "{workspace.name}" because it has members. '
            f'Reassign or remove the members first via User Administration.'
        )
        return redirect('workspace_management')

    if request.method == 'POST':
        name = workspace.name
        workspace.delete()
        messages.success(request, f'Workspace "{name}" has been permanently deleted.')
        return redirect('workspace_management')

    return redirect('workspace_management')