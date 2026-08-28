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
- user_add            : Create a user (validates username / email /
                        password; optional superuser role).
- user_edit           : Update a user; optional password reset; cannot
                        strip your own superuser status.
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
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'user')
        is_active = request.POST.get('is_active') == '1'
        workspace_id = request.POST.get('workspace_id', '').strip()

        # Validation
        errors = []
        if not username:
            errors.append('Username is required.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if not password1:
            errors.append('Password is required.')
        if password1 != password2:
            errors.append('Passwords do not match.')
        if len(password1) < 8:
            errors.append('Password must be at least 8 characters.')
        if email and User.objects.filter(email=email).exists():
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

        # Create the user
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
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

        messages.success(request, f'User "{username}" created successfully!')
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
        new_password = request.POST.get('password1', '').strip()
        confirm_password = request.POST.get('password2', '').strip()
        workspace_id = request.POST.get('workspace_id', '').strip()

        errors = []
        if email and User.objects.filter(email=email).exclude(id=user_id).exists():
            errors.append('A user with this email already exists.')
        if new_password and new_password != confirm_password:
            errors.append('Passwords do not match.')
        if new_password and len(new_password) < 8:
            errors.append('Password must be at least 8 characters.')

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

        if new_password:
            target_user.set_password(new_password)

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