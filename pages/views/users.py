"""
User administration views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split.
Covers the superuser-only User Administration screen: list, add, edit,
per-user module permissions, and permanent delete (with safety checks).

All five views are protected by the same three-decorator stack:
    @login_required
    @user_passes_test(lambda u: u.is_superuser)
    @permission_required('auth.can_access_administration', raise_exception=True)

Self-service profile editing (my_profile) stays in main.py — it's a
different concern (a regular user updating their own details) and uses a
different decorator set.
"""
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from ..models import UserProfile


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

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'user')
        is_active = request.POST.get('is_active') == '1'

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

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'user_add.html', {
                'form_data': request.POST
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

        # Ensure profile exists
        UserProfile.objects.get_or_create(user=new_user)

        messages.success(request, f'User "{username}" created successfully!')
        return redirect('user_administration')

    return render(request, 'user_add.html', {'form_data': {}})


@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required('auth.can_access_administration', raise_exception=True)
def user_edit(request, user_id):
    """Edit an existing user"""

    target_user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'user')
        is_active = request.POST.get('is_active') == '1'
        new_password = request.POST.get('password1', '').strip()
        confirm_password = request.POST.get('password2', '').strip()

        errors = []
        if email and User.objects.filter(email=email).exclude(id=user_id).exists():
            errors.append('A user with this email already exists.')
        if new_password and new_password != confirm_password:
            errors.append('Passwords do not match.')
        if new_password and len(new_password) < 8:
            errors.append('Password must be at least 8 characters.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'user_edit.html', {
                'target_user': target_user,
                'profile': profile,
            })

        # Update user
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email
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
        messages.success(request, f'User "{target_user.username}" updated successfully!')
        return redirect('user_administration')

    return render(request, 'user_edit.html', {
        'target_user': target_user,
        'profile': profile,
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
    all_permissions = [
        {'codename': 'can_access_properties',     'edit_codename': 'can_edit_properties', 'label': 'Properties',       'icon': 'fa-building'},
        {'codename': 'can_access_tenants',        'edit_codename': 'can_edit_tenants',    'label': 'Tenants',          'icon': 'fa-users'},
        {'codename': 'can_access_suppliers',      'edit_codename': 'can_edit_suppliers',  'label': 'Suppliers',        'icon': 'fa-truck'},
        {'codename': 'can_access_expenses',       'edit_codename': 'can_edit_expenses',   'label': 'Expenses',         'icon': 'fa-receipt'},
        {'codename': 'can_access_petty_cash',     'edit_codename': 'can_edit_petty_cash', 'label': 'Petty Cash',       'icon': 'fa-coins'},
        {'codename': 'can_access_financials',     'edit_codename': 'can_edit_financials', 'label': 'Financials',       'icon': 'fa-chart-line'},
        {'codename': 'can_access_invoices',       'edit_codename': 'can_edit_invoices',   'label': 'Invoices',         'icon': 'fa-file-invoice'},
        {'codename': 'can_access_projects',       'edit_codename': 'can_edit_projects',   'label': 'Projects',         'icon': 'fa-project-diagram'},
        {'codename': 'can_access_issues',         'edit_codename': 'can_edit_issues',     'label': 'Issues',           'icon': 'fa-exclamation-circle'},
        {'codename': 'can_access_dashboard',      'edit_codename': None,                  'label': 'Dashboard',        'icon': 'fa-tachometer-alt'},
        {'codename': 'can_access_administration', 'edit_codename': None,                  'label': 'Administration',   'icon': 'fa-cogs'},
        {'codename': 'can_access_personal',       'edit_codename': 'can_edit_personal',   'label': 'Personal',         'icon': 'fa-user-circle'},
    ]

    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

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

    # GET — build list with current status
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