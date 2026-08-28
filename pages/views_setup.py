from django.http import HttpResponse
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from pages.permissions import all_codenames

@user_passes_test(lambda u: u.is_superuser)
def setup_permissions(request):
    """Setup permissions and groups - only accessible by superusers"""
    
    output = ["<h2>Setting up permissions and groups...</h2>"]
    
    try:
        # Get content type
        content_type = ContentType.objects.get_for_model(User)
        
        # Create permissions
        # ONE definition, in pages/permissions.py. This list used to be
        # maintained separately from the User Administration screen's and had
        # fallen five modules behind it - and it carried no can_edit_* at all,
        # so a rebuilt environment came up missing half the permissions the
        # system checks.
        permissions_data = all_codenames()
        
        for codename, name in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            if created:
                output.append(f"✓ Created: {name}")
            else:
                output.append(f"- Already exists: {name}")
        
        # Create groups
        pm_group, created = Group.objects.get_or_create(name='Property Managers')
        pm_permissions = Permission.objects.filter(
            codename__in=[
                'can_access_properties', 'can_access_tenants', 'can_access_suppliers',
                'can_access_expenses', 'can_access_petty_cash', 'can_access_issues', 'can_access_fsr'
            ],
            content_type=content_type
        )
        pm_group.permissions.set(pm_permissions)
        output.append(f"✓ {'Created' if created else 'Updated'} Property Managers group with {pm_permissions.count()} permissions")
        
        # Create Full Access group
        full_group, created = Group.objects.get_or_create(name='Full Access')
        all_permissions = Permission.objects.filter(
            codename__startswith='can_access_',
            content_type=content_type
        )
        full_group.permissions.set(all_permissions)
        output.append(f"✓ {'Created' if created else 'Updated'} Full Access group with {all_permissions.count()} permissions")
        
        output.append("<br><h3>Setup completed successfully!</h3>")
        output.append("<p>Now go to <a href='/admin/'>Django Admin</a> and assign users to groups.</p>")
        
    except Exception as e:
        output.append(f"❌ Error: {str(e)}")
    
    return HttpResponse("<br>".join(output))