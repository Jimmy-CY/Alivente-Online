"""
Management command to populate and clean up asset categories, subcategories, and suppliers.

Changes applied:
- Removed categories: 'Other', 'Test'
- Renamed 'HVAC & Plumbing' to 'Plumbing'
- Removed subcategories: 'Test 3', 'Test 2'
- Renamed 'Sofa/Couch' to 'Couch'
- Renamed 'Wardrobe/Closet' to 'Cupboards'
- Added subcategories under Furniture: 'Bedside Tables', 'Coffee Tables', 'Drawers', 'Lamps'
- Removed suppliers: 'ABC Limited', 'Kaka Head'

Usage: python manage.py populate_asset_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import AssetCategory, AssetSubcategory, AssetSupplier


class Command(BaseCommand):
    help = 'Populate and clean up asset categories, subcategories, and suppliers'

    def handle(self, *args, **options):
        # Get the first superuser to use as created_by
        admin_user = User.objects.filter(is_superuser=True).first()

        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return

        self.stdout.write(self.style.SUCCESS('Starting asset data cleanup and population...'))

        # ==================== STEP 1: RENAMES ====================
        self.stdout.write('\n--- Renaming Categories ---')

        # Rename 'HVAC & Plumbing' to 'Plumbing'
        try:
            cat = AssetCategory.objects.get(name='HVAC & Plumbing')
            cat.name = 'Plumbing'
            cat.save()
            self.stdout.write(self.style.SUCCESS("  ✓ Renamed 'HVAC & Plumbing' to 'Plumbing'"))
        except AssetCategory.DoesNotExist:
            self.stdout.write("  - 'HVAC & Plumbing' not found (may already be renamed)")

        self.stdout.write('\n--- Renaming Subcategories ---')

        # Rename 'Sofa/Couch' to 'Couch'
        try:
            sub = AssetSubcategory.objects.get(name='Sofa/Couch')
            sub.name = 'Couch'
            sub.save()
            self.stdout.write(self.style.SUCCESS("  ✓ Renamed 'Sofa/Couch' to 'Couch'"))
        except AssetSubcategory.DoesNotExist:
            self.stdout.write("  - 'Sofa/Couch' not found (may already be renamed)")

        # Rename 'Wardrobe/Closet' to 'Cupboards'
        try:
            sub = AssetSubcategory.objects.get(name='Wardrobe/Closet')
            sub.name = 'Cupboards'
            sub.save()
            self.stdout.write(self.style.SUCCESS("  ✓ Renamed 'Wardrobe/Closet' to 'Cupboards'"))
        except AssetSubcategory.DoesNotExist:
            self.stdout.write("  - 'Wardrobe/Closet' not found (may already be renamed)")

        # ==================== STEP 2: DELETIONS ====================
        self.stdout.write('\n--- Removing Test Subcategories ---')

        for name in ['Test 3', 'Test 2']:
            deleted, _ = AssetSubcategory.objects.filter(name=name).delete()
            if deleted:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Deleted subcategory: '{name}'"))
            else:
                self.stdout.write(f"  - Subcategory '{name}' not found")

        self.stdout.write('\n--- Removing Categories ---')

        for name in ['Other', 'Test']:
            deleted, _ = AssetCategory.objects.filter(name=name).delete()
            if deleted:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Deleted category: '{name}'"))
            else:
                self.stdout.write(f"  - Category '{name}' not found")

        self.stdout.write('\n--- Removing Suppliers ---')

        for name in ['ABC Limited', 'Kaka Head']:
            deleted, _ = AssetSupplier.objects.filter(name=name).delete()
            if deleted:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Deleted supplier: '{name}'"))
            else:
                self.stdout.write(f"  - Supplier '{name}' not found")

        # ==================== STEP 3: CREATE / ENSURE CATEGORIES ====================
        self.stdout.write('\n--- Ensuring Categories ---')

        categories_data = [
            {'name': 'Appliances',        'icon': 'fa-snowflake'},
            {'name': 'Electronics',       'icon': 'fa-tv'},
            {'name': 'Fixtures & Fittings','icon': 'fa-lightbulb'},
            {'name': 'Furniture',         'icon': 'fa-couch'},
            {'name': 'Plumbing',          'icon': 'fa-fire'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = AssetCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'created_by': admin_user
                }
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created category: {cat_data["name"]}'))
            else:
                self.stdout.write(f'  - Already exists: {cat_data["name"]}')

        # ==================== STEP 4: CREATE / ENSURE SUBCATEGORIES ====================
        self.stdout.write('\n--- Ensuring Subcategories ---')

        subcategories_data = {
            'Appliances': [
                'Air Conditioner',
                'Dishwasher',
                'Dryer',
                'Microwave',
                'Oven',
                'Refrigerator',
                'Stove',
                'Washing Machine',
                'Water Heater',
            ],
            'Electronics': [
                'Internet Router',
                'Security System',
                'Television',
            ],
            'Fixtures & Fittings': [
                'Bathroom Fixtures',
                'Blinds/Curtains',
                'Ceiling Fan',
                'Kitchen Cabinets',
                'Light Fixtures',
            ],
            'Furniture': [
                'Bed',
                'Bedside Tables',
                'Chairs',
                'Coffee Tables',
                'Couch',
                'Cupboards',
                'Desk',
                'Dining Table',
                'Drawers',
                'Lamps',
                'Shelving',
            ],
            'Plumbing': [
                'Boiler',
                'Radiator',
                'Water Pump',
            ],
        }

        for cat_name, subcat_list in subcategories_data.items():
            category = categories[cat_name]
            for subcat_name in subcat_list:
                subcategory, created = AssetSubcategory.objects.get_or_create(
                    category=category,
                    name=subcat_name,
                    defaults={'created_by': admin_user}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Created: {cat_name} → {subcat_name}'))
                else:
                    self.stdout.write(f'    - Already exists: {cat_name} → {subcat_name}')

        # ==================== STEP 5: CREATE / ENSURE SUPPLIERS ====================
        self.stdout.write('\n--- Ensuring Suppliers ---')

        suppliers_data = [
            'CMC Electric',
            'Electroline',
            'IKEA',
            'Leroy Merlin',
            'Scandia',
            'Stephanis',
            'Superhome Center',
        ]

        for supplier_name in suppliers_data:
            supplier, created = AssetSupplier.objects.get_or_create(
                name=supplier_name,
                defaults={'created_by': admin_user}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created supplier: {supplier_name}'))
            else:
                self.stdout.write(f'  - Already exists: {supplier_name}')

        # ==================== SUMMARY ====================
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('Asset data cleanup and population complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Categories:    {AssetCategory.objects.count()}')
        self.stdout.write(f'Subcategories: {AssetSubcategory.objects.count()}')
        self.stdout.write(f'Suppliers:     {AssetSupplier.objects.count()}')