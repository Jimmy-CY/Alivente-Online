"""
Management command to populate initial asset categories, subcategories, and suppliers

Usage: python manage.py populate_asset_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import AssetCategory, AssetSubcategory, AssetSupplier


class Command(BaseCommand):
    help = 'Populate initial asset categories, subcategories, and suppliers'

    def handle(self, *args, **options):
        # Get the first superuser to use as created_by
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return
        
        self.stdout.write(self.style.SUCCESS('Starting asset data population...'))
        
        # ==================== CATEGORIES ====================
        categories_data = [
            {'name': 'Appliances', 'icon': 'fa-snowflake'},
            {'name': 'Furniture', 'icon': 'fa-couch'},
            {'name': 'Fixtures & Fittings', 'icon': 'fa-lightbulb'},
            {'name': 'Electronics', 'icon': 'fa-tv'},
            {'name': 'HVAC & Plumbing', 'icon': 'fa-fire'},
            {'name': 'Other', 'icon': 'fa-box'},
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
                self.stdout.write(f'  - Category already exists: {cat_data["name"]}')
        
        # ==================== SUBCATEGORIES ====================
        subcategories_data = {
            'Appliances': [
                'Air Conditioner',
                'Washing Machine',
                'Dryer',
                'Dishwasher',
                'Refrigerator',
                'Oven',
                'Stove',
                'Microwave',
                'Water Heater',
            ],
            'Furniture': [
                'Sofa/Couch',
                'Bed',
                'Dining Table',
                'Chairs',
                'Wardrobe/Closet',
                'Desk',
                'Shelving',
            ],
            'Fixtures & Fittings': [
                'Blinds/Curtains',
                'Light Fixtures',
                'Ceiling Fan',
                'Kitchen Cabinets',
                'Bathroom Fixtures',
            ],
            'Electronics': [
                'Television',
                'Internet Router',
                'Security System',
            ],
            'HVAC & Plumbing': [
                'Boiler',
                'Water Pump',
                'Radiator',
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
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Created subcategory: {cat_name} → {subcat_name}'))
                else:
                    self.stdout.write(f'    - Subcategory already exists: {cat_name} → {subcat_name}')
        
        # ==================== SUPPLIERS ====================
        suppliers_data = [
            'Superhome Center',
            'IKEA',
            'Leroy Merlin',
            'Electroline',
            'Scandia',
            'CMC Electric',
            'Stephanis',
        ]
        
        for supplier_name in suppliers_data:
            supplier, created = AssetSupplier.objects.get_or_create(
                name=supplier_name,
                defaults={'created_by': admin_user}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created supplier: {supplier_name}'))
            else:
                self.stdout.write(f'  - Supplier already exists: {supplier_name}')
        
        # ==================== SUMMARY ====================
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Asset data population complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Categories: {AssetCategory.objects.count()}')
        self.stdout.write(f'Subcategories: {AssetSubcategory.objects.count()}')
        self.stdout.write(f'Suppliers: {AssetSupplier.objects.count()}')