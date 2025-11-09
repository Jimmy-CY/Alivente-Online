"""
Django Management Command to populate initial Recipe Keeper data
Save this as: pages/management/commands/populate_recipe_data.py

Then run: python manage.py populate_recipe_data
"""

from django.core.management.base import BaseCommand
from pages.models import (
    MeasurementUnit, IngredientCategory, RecipeCourse, RecipeCategory
)

class Command(BaseCommand):
    help = 'Populate initial data for Recipe Keeper (measurement units, categories, etc.)'

    def handle(self, *args, **options):
        self.stdout.write('=== POPULATING RECIPE KEEPER INITIAL DATA ===')
        
        # Create Measurement Units
        self.stdout.write('\nCreating Measurement Units...')
        measurement_units = [
            # Volume
            ('teaspoon', 'tsp', 'volume'),
            ('tablespoon', 'tbsp', 'volume'),
            ('cup', 'cup', 'volume'),
            ('milliliter', 'ml', 'volume'),
            ('liter', 'L', 'volume'),
            ('fluid ounce', 'fl oz', 'volume'),
            ('pint', 'pt', 'volume'),
            ('quart', 'qt', 'volume'),
            ('gallon', 'gal', 'volume'),
            
            # Weight
            ('gram', 'g', 'weight'),
            ('kilogram', 'kg', 'weight'),
            ('ounce', 'oz', 'weight'),
            ('pound', 'lb', 'weight'),
            ('milligram', 'mg', 'weight'),
            
            # Count
            ('piece', 'pc', 'count'),
            ('pieces', 'pcs', 'count'),
            ('clove', 'clove', 'count'),
            ('cloves', 'cloves', 'count'),
            ('bunch', 'bunch', 'count'),
            ('packet', 'packet', 'count'),
            ('packets', 'packets', 'count'),
            ('can', 'can', 'count'),
            ('jar', 'jar', 'count'),
            ('slice', 'slice', 'count'),
            ('slices', 'slices', 'count'),
            
            # Other
            ('pinch', 'pinch', 'other'),
            ('dash', 'dash', 'other'),
            ('to taste', 'to taste', 'other'),
        ]
        
        created_units = 0
        for name, abbr, unit_type in measurement_units:
            obj, created = MeasurementUnit.objects.get_or_create(
                name=name,
                defaults={'abbreviation': abbr, 'unit_type': unit_type}
            )
            if created:
                created_units += 1
                self.stdout.write(f'  ✓ Created: {name}')
        
        self.stdout.write(f'\n✅ Created {created_units} measurement units')
        
        # Create Ingredient Categories
        self.stdout.write('\nCreating Ingredient Categories...')
        ingredient_categories = [
            ('Vegetables', 'Fresh and frozen vegetables'),
            ('Fruits', 'Fresh and dried fruits'),
            ('Poultry', 'Chicken, turkey, duck, etc.'),
            ('Meat', 'Beef, pork, lamb, etc.'),
            ('Fish & Seafood', 'Fish, shellfish, and other seafood'),
            ('Dairy', 'Milk, cheese, yogurt, cream, etc.'),
            ('Eggs', 'Eggs and egg products'),
            ('Grains & Pasta', 'Rice, pasta, quinoa, couscous, etc.'),
            ('Bread & Bakery', 'Bread, rolls, pastries, etc.'),
            ('Herbs & Spices', 'Fresh and dried herbs and spices'),
            ('Oils & Fats', 'Cooking oils, butter, lard, etc.'),
            ('Condiments & Sauces', 'Ketchup, mustard, soy sauce, etc.'),
            ('Canned & Jarred', 'Canned vegetables, beans, tomatoes, etc.'),
            ('Baking', 'Flour, sugar, baking powder, etc.'),
            ('Nuts & Seeds', 'Almonds, walnuts, sunflower seeds, etc.'),
            ('Legumes', 'Beans, lentils, chickpeas, etc.'),
            ('Beverages', 'Stock, wine, beer, etc.'),
            ('Frozen', 'Frozen vegetables, fruits, etc.'),
            ('Other', 'Miscellaneous ingredients'),
        ]
        
        created_categories = 0
        for name, description in ingredient_categories:
            obj, created = IngredientCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                created_categories += 1
                self.stdout.write(f'  ✓ Created: {name}')
        
        self.stdout.write(f'\n✅ Created {created_categories} ingredient categories')
        
        # Create Recipe Courses
        self.stdout.write('\nCreating Recipe Courses...')
        recipe_courses = [
            ('Appetizer', 1),
            ('Starter', 2),
            ('Soup', 3),
            ('Salad', 4),
            ('Main', 5),
            ('Side', 6),
            ('Dessert', 7),
            ('Snack', 8),
            ('Beverage', 9),
            ('Breakfast', 10),
            ('Brunch', 11),
            ('Lunch', 12),
            ('Dinner', 13),
        ]
        
        created_courses = 0
        for name, order in recipe_courses:
            obj, created = RecipeCourse.objects.get_or_create(
                name=name,
                defaults={'display_order': order}
            )
            if created:
                created_courses += 1
                self.stdout.write(f'  ✓ Created: {name}')
        
        self.stdout.write(f'\n✅ Created {created_courses} recipe courses')
        
        # Create Recipe Categories
        self.stdout.write('\nCreating Recipe Categories...')
        recipe_categories = [
            ('Pasta', 'Pasta dishes and noodles'),
            ('Rice', 'Rice-based dishes'),
            ('Salad', 'Fresh and composed salads'),
            ('Soup & Stew', 'Soups, stews, and chowders'),
            ('Casserole', 'Baked casseroles and one-pot dishes'),
            ('Grilled', 'Grilled and barbecued dishes'),
            ('Roasted', 'Roasted meats and vegetables'),
            ('Stir Fry', 'Quick stir-fried dishes'),
            ('Pizza', 'Pizzas and flatbreads'),
            ('Sandwich & Burger', 'Sandwiches, burgers, and wraps'),
            ('Curry', 'Curries and curry-based dishes'),
            ('Asian', 'Asian-inspired cuisine'),
            ('Italian', 'Italian cuisine'),
            ('Mexican', 'Mexican cuisine'),
            ('Indian', 'Indian cuisine'),
            ('Chinese', 'Chinese cuisine'),
            ('Thai', 'Thai cuisine'),
            ('Greek', 'Greek cuisine'),
            ('Mediterranean', 'Mediterranean cuisine'),
            ('American', 'American cuisine'),
            ('Cake', 'Cakes and layer cakes'),
            ('Cookie', 'Cookies and bars'),
            ('Pie & Tart', 'Pies, tarts, and pastries'),
            ('Bread', 'Homemade breads'),
            ('Breakfast', 'Breakfast dishes'),
            ('Vegetarian', 'Vegetarian dishes'),
            ('Vegan', 'Vegan dishes'),
            ('Slow Cooker', 'Slow cooker recipes'),
            ('Instant Pot', 'Instant Pot and pressure cooker recipes'),
            ('Air Fryer', 'Air fryer recipes'),
            ('One Pot', 'One-pot meals'),
            ('Quick & Easy', 'Quick recipes under 30 minutes'),
            ('Comfort Food', 'Classic comfort foods'),
            ('Holiday', 'Holiday and special occasion recipes'),
        ]
        
        created_recipe_cats = 0
        for name, description in recipe_categories:
            obj, created = RecipeCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                created_recipe_cats += 1
                self.stdout.write(f'  ✓ Created: {name}')
        
        self.stdout.write(f'\n✅ Created {created_recipe_cats} recipe categories')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'  • Measurement Units: {MeasurementUnit.objects.count()} total')
        self.stdout.write(f'  • Ingredient Categories: {IngredientCategory.objects.count()} total')
        self.stdout.write(f'  • Recipe Courses: {RecipeCourse.objects.count()} total')
        self.stdout.write(f'  • Recipe Categories: {RecipeCategory.objects.count()} total')
        self.stdout.write('='*50)
        self.stdout.write('\n✅ Initial data population complete!')
        self.stdout.write('\nYou can now:')
        self.stdout.write('  1. Access Django Admin to add ingredients and recipes')
        self.stdout.write('  2. Add more custom categories and units as needed')
        self.stdout.write('  3. Start creating your recipes!\n')