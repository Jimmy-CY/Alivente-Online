from django.db import migrations


def populate_unit_plurals(apps, schema_editor):
    MeasurementUnit = apps.get_model('pages', 'MeasurementUnit')
    
    # Define all unit data: name -> (singular, plural, abbr_singular, abbr_plural)
    unit_data = {
        # Volume - metric (abbreviations don't change)
        'milliliter': ('milliliter', 'milliliters', 'ml', 'ml'),
        'milliliter/s': ('milliliter', 'milliliters', 'ml', 'ml'),
        'liter': ('liter', 'liters', 'L', 'L'),
        'liter/s': ('liter', 'liters', 'L', 'L'),
        
        # Volume - imperial
        'teaspoon': ('teaspoon', 'teaspoons', 'tsp', 'tsp'),
        'teaspoon/s': ('teaspoon', 'teaspoons', 'tsp', 'tsp'),
        'tablespoon': ('tablespoon', 'tablespoons', 'tbsp', 'tbsp'),
        'tablespoon/s': ('tablespoon', 'tablespoons', 'tbsp', 'tbsp'),
        'fluid ounce': ('fluid ounce', 'fluid ounces', 'fl oz', 'fl oz'),
        'fluid ounce/s': ('fluid ounce', 'fluid ounces', 'fl oz', 'fl oz'),
        'cup': ('cup', 'cups', 'cup', 'cups'),
        'cup/s': ('cup', 'cups', 'cup', 'cups'),
        'pint': ('pint', 'pints', 'pt', 'pt'),
        'pint/s': ('pint', 'pints', 'pt', 'pt'),
        'quart': ('quart', 'quarts', 'qt', 'qt'),
        'quart/s': ('quart', 'quarts', 'qt', 'qt'),
        'gallon': ('gallon', 'gallons', 'gal', 'gal'),
        'gallon/s': ('gallon', 'gallons', 'gal', 'gal'),
        
        # Weight - metric (abbreviations don't change)
        'milligram': ('milligram', 'milligrams', 'mg', 'mg'),
        'milligram/s': ('milligram', 'milligrams', 'mg', 'mg'),
        'gram': ('gram', 'grams', 'g', 'g'),
        'gram/s': ('gram', 'grams', 'g', 'g'),
        'kilogram': ('kilogram', 'kilograms', 'kg', 'kg'),
        'kilogram/s': ('kilogram', 'kilograms', 'kg', 'kg'),
        
        # Weight - imperial
        'ounce': ('ounce', 'ounces', 'oz', 'oz'),
        'ounce/s': ('ounce', 'ounces', 'oz', 'oz'),
        'pound': ('pound', 'pounds', 'lb', 'lb'),
        'pound/s': ('pound', 'pounds', 'lb', 'lb'),
        
        # Count units (abbreviations do change for plural)
        'piece': ('piece', 'pieces', 'pc', 'pcs'),
        'piece/s': ('piece', 'pieces', 'pc', 'pcs'),
        'bottle': ('bottle', 'bottles', 'bottle', 'bottles'),
        'bottle/s': ('bottle', 'bottles', 'bottle', 'bottles'),
        'box': ('box', 'boxes', 'box', 'boxes'),
        'box/es': ('box', 'boxes', 'box', 'boxes'),
        'bunch': ('bunch', 'bunches', 'bunch', 'bunches'),
        'bunch/es': ('bunch', 'bunches', 'bunch', 'bunches'),
        'can': ('can', 'cans', 'can', 'cans'),
        'can/s': ('can', 'cans', 'can', 'cans'),
        'clove': ('clove', 'cloves', 'clove', 'cloves'),
        'clove/s': ('clove', 'cloves', 'clove', 'cloves'),
        'head': ('head', 'heads', 'head', 'heads'),
        'head/s': ('head', 'heads', 'head', 'heads'),
        'packet': ('packet', 'packets', 'pkt', 'pkts'),
        'packet/s': ('packet', 'packets', 'pkt', 'pkts'),
        'slice': ('slice', 'slices', 'slice', 'slices'),
        'slice/s': ('slice', 'slices', 'slice', 'slices'),
        'slab': ('slab', 'slabs', 'slab', 'slabs'),
        'slab/s': ('slab', 'slabs', 'slab', 'slabs'),
        'stalk': ('stalk', 'stalks', 'stalk', 'stalks'),
        'tin': ('tin', 'tins', 'tin', 'tins'),
        'tin/s': ('tin', 'tins', 'tin', 'tins'),
        'tub': ('tub', 'tubs', 'tub', 'tubs'),
        'tub/s': ('tub', 'tubs', 'tub', 'tubs'),
        
        # Other
        'centimeter': ('centimeter', 'centimeters', 'cm', 'cm'),
        'dash': ('dash', 'dashes', 'dash', 'dashes'),
        'pinch': ('pinch', 'pinches', 'pinch', 'pinches'),
        'to taste': ('to taste', 'to taste', 'to taste', 'to taste'),
    }
    
    for unit in MeasurementUnit.objects.all():
        name_lower = unit.name.lower().strip()
        
        if name_lower in unit_data:
            singular, plural, abbr_sing, abbr_plur = unit_data[name_lower]
            unit.name = singular
            unit.name_plural = plural
            unit.abbreviation = abbr_sing
            unit.abbreviation_plural = abbr_plur
            unit.save()
        else:
            # For unknown units, clean up and make a basic plural
            clean_name = unit.name.replace('/s', '').replace('/es', '').strip()
            unit.name = clean_name
            
            # Basic pluralization
            if clean_name.endswith(('s', 'x', 'ch', 'sh')):
                unit.name_plural = clean_name + 'es'
            else:
                unit.name_plural = clean_name + 's'
            
            # Keep existing abbreviation or use name
            if not unit.abbreviation:
                unit.abbreviation = clean_name
            unit.abbreviation_plural = unit.abbreviation
            unit.save()


def reverse_migration(apps, schema_editor):
    pass  # No reverse needed


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0038_measurementunit_abbreviation_plural_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_unit_plurals, reverse_migration),
    ]