# pages/management/commands/create_module_permissions.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create module permissions and optionally assign them to groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Also create sample user groups with different permission levels',
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating module permissions...')
        
        # Get content type (using User model as base)
        content_type = ContentType.objects.get_for_model(User)
        
        # Define permissions
        permissions_data = [
            ('can_access_properties', 'Can access Properties module'),
            ('can_access_tenants', 'Can access Tenants module'),
            ('can_access_suppliers', 'Can access Suppliers module'),
            ('can_access_expenses', 'Can access Expenses module'),
            ('can_access_petty_cash', 'Can access Petty Cash module'),
            ('can_access_financials', 'Can access Financials module'),
            ('can_access_invoices', 'Can access Invoices module'),
            ('can_access_projects', 'Can access Projects module'),
            ('can_access_issues', 'Can access Issues module'),
            ('can_access_dashboard', 'Can access Dashboard module'),
        ]
        
        created_permissions = []
        existing_permissions = []
        
        for codename, name in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            
            if created:
                created_permissions.append(permission)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created permission: {name}')
                )
            else:
                existing_permissions.append(permission)
                self.stdout.write(
                    self.style.WARNING(f'- Permission already exists: {name}')
                )
        
        # Summary
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Created: {len(created_permissions)} permissions')
        self.stdout.write(f'  Existing: {len(existing_permissions)} permissions')
        
        # Optionally create groups
        if options['create_groups']:
            self.create_sample_groups(permissions_data, content_type)

    def create_sample_groups(self, permissions_data, content_type):
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Creating sample user groups...')
        
        # Define group configurations
        group_configs = {
            'Property Managers': [
                'can_access_dashboard',
                'can_access_properties',
                'can_access_tenants',
                'can_access_issues',
                'can_access_projects',
            ],
            'Financial Staff': [
                'can_access_dashboard',
                'can_access_expenses',
                'can_access_petty_cash',
                'can_access_financials',
                'can_access_invoices',
                'can_access_suppliers',
            ],
            'Full Access': [perm[0] for perm in permissions_data],  # All permissions
            'View Only': [
                'can_access_dashboard',
            ],
        }
        
        for group_name, permission_codenames in group_configs.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {group_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Group already exists: {group_name}')
                )
            
            # Add permissions to group
            permissions = Permission.objects.filter(
                codename__in=permission_codenames,
                content_type=content_type
            )
            
            group.permissions.set(permissions)
            self.stdout.write(
                f'  → Added {permissions.count()} permissions to {group_name}'
            )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Sample groups created! You can now assign users to these groups.')
        self.stdout.write('To assign a user to a group in Django admin or shell:')
        self.stdout.write('  user.groups.add(Group.objects.get(name="Property Managers"))')
        
        # Show current superusers
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            self.stdout.write(f'\nNote: These superusers bypass all permissions:')
            for user in superusers:
                self.stdout.write(f'  - {user.username}')
        else:
            self.stdout.write(f'\nNote: No superusers found. Consider creating one with:')
            self.stdout.write(f'  python manage.py createsuperuser')