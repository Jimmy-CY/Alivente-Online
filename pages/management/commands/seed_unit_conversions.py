from django.core.management.base import BaseCommand
from pages.models import MeasurementUnit, UnitConversion
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed unit conversion data for meal plan shopping list aggregation'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding unit conversions...')
        
        # Define conversions: (from_unit, to_unit, multiplier, notes)
        conversions = [
            # Volume - Metric to Imperial
            ('liter', 'ml', Decimal('1000'), 'Liters to milliliters'),
            ('ml', 'liter', Decimal('0.001'), 'Milliliters to liters'),
            ('liter', 'cup', Decimal('4.166666'), 'Liters to cups'),
            ('cup', 'liter', Decimal('0.240'), 'Cups to liters'),
            ('cup', 'ml', Decimal('240'), 'Cups to milliliters'),
            ('ml', 'cup', Decimal('0.00416666'), 'Milliliters to cups'),
            
            # Volume - Tablespoon/Teaspoon
            ('tablespoon', 'ml', Decimal('15'), 'Tablespoons to milliliters'),
            ('ml', 'tablespoon', Decimal('0.0666666'), 'Milliliters to tablespoons'),
            ('teaspoon', 'ml', Decimal('5'), 'Teaspoons to milliliters'),
            ('ml', 'teaspoon', Decimal('0.2'), 'Milliliters to teaspoons'),
            ('tablespoon', 'teaspoon', Decimal('3'), 'Tablespoons to teaspoons'),
            ('teaspoon', 'tablespoon', Decimal('0.333333'), 'Teaspoons to tablespoons'),
            ('cup', 'tablespoon', Decimal('16'), 'Cups to tablespoons'),
            ('tablespoon', 'cup', Decimal('0.0625'), 'Tablespoons to cups'),
            ('cup', 'teaspoon', Decimal('48'), 'Cups to teaspoons'),
            ('teaspoon', 'cup', Decimal('0.0208333'), 'Teaspoons to cups'),
            
            # Weight - Metric
            ('kilogram', 'gram', Decimal('1000'), 'Kilograms to grams'),
            ('gram', 'kilogram', Decimal('0.001'), 'Grams to kilograms'),
            ('kg', 'g', Decimal('1000'), 'Kg to g (abbreviation)'),
            ('g', 'kg', Decimal('0.001'), 'G to kg (abbreviation)'),
            
            # Weight - Imperial to Metric
            ('pound', 'gram', Decimal('453.592'), 'Pounds to grams'),
            ('gram', 'pound', Decimal('0.00220462'), 'Grams to pounds'),
            ('lb', 'g', Decimal('453.592'), 'Lb to g (abbreviation)'),
            ('g', 'lb', Decimal('0.00220462'), 'G to lb (abbreviation)'),
            ('ounce', 'gram', Decimal('28.3495'), 'Ounces to grams'),
            ('gram', 'ounce', Decimal('0.035274'), 'Grams to ounces'),
            ('oz', 'g', Decimal('28.3495'), 'Oz to g (abbreviation)'),
            ('g', 'oz', Decimal('0.035274'), 'G to oz (abbreviation)'),
            
            # Weight - Imperial
            ('pound', 'ounce', Decimal('16'), 'Pounds to ounces'),
            ('ounce', 'pound', Decimal('0.0625'), 'Ounces to pounds'),
            ('lb', 'oz', Decimal('16'), 'Lb to oz (abbreviation)'),
            ('oz', 'lb', Decimal('0.0625'), 'Oz to lb (abbreviation)'),
            
            # Common cooking conversions
            ('can', 'cup', Decimal('1.75'), 'Standard can to cups (14oz can)'),
            ('can', 'ml', Decimal('414.029'), 'Standard can to ml (14oz can)'),
        ]
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for from_unit_name, to_unit_name, multiplier, notes in conversions:
            try:
                # Get or create units (case-insensitive)
                from_unit = MeasurementUnit.objects.filter(
                    name__iexact=from_unit_name
                ).first()
                to_unit = MeasurementUnit.objects.filter(
                    name__iexact=to_unit_name
                ).first()
                
                if not from_unit:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  From unit "{from_unit_name}" not found, skipping'
                        )
                    )
                    skipped_count += 1
                    continue
                
                if not to_unit:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  To unit "{to_unit_name}" not found, skipping'
                        )
                    )
                    skipped_count += 1
                    continue
                
                # Create conversion if it doesn't exist
                conversion, created = UnitConversion.objects.get_or_create(
                    from_unit=from_unit,
                    to_unit=to_unit,
                    defaults={
                        'multiplier': multiplier,
                        'notes': notes
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created: {conversion}')
                else:
                    skipped_count += 1
                    self.stdout.write(f'  - Exists: {conversion}')
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error creating conversion {from_unit_name} → {to_unit_name}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Created: {created_count} conversions'))
        self.stdout.write(self.style.WARNING(f'- Skipped: {skipped_count} conversions'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errors: {error_count} conversions'))
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('\n✓ Unit conversion seeding complete!'))