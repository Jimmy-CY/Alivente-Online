"""
Shared helpers for the recipes sub-package.

These utilities are used internally by multiple recipes submodules
(crud, meal_planning, conversions, nutrition, etc.) but are not
intended for use outside the recipes package. Hence the leading
underscore in the module name.

Contents:
    WEIGHT_UNIT_PRIORITY                - module constant: ordered
                                          weight units tried by
                                          get_preferred_weight_conversion.
    convert_to_decimal(quantity_str)    - parse "1/4" or "1 1/2" to
                                          Decimal.
    format_quantity(quantity_str)       - format Decimal/float for
                                          display, preserving fractions
                                          as-is.
    get_preferred_weight_conversion(from_unit, ingredient=None)
                                        - try weight units in priority
                                          order, ingredient-specific
                                          first then generic fallback.
    get_or_create_ingredient(name)      - title-case, case-insensitive
                                          lookup or create.
    get_or_create_unit(name)            - lowercase, case-insensitive
                                          lookup; auto-generates a
                                          5-char abbreviation on create.
    get_or_create_preparation(name)     - lowercase, case-insensitive
                                          lookup; returns None on empty
                                          input.

Extracted from pages/views/main.py as part of the modular views
migration (### RECIPE MANAGEMENT ### -> recipes/ sub-package, phase 1
of the Recipes extraction).
"""

from decimal import Decimal
from fractions import Fraction

from ...models import Ingredient, MeasurementUnit, PreparationMethod, UnitConversion


WEIGHT_UNIT_PRIORITY = ['g', 'kg', 'oz', 'lb']


def convert_to_decimal(quantity_str):
    """Convert fractions like '1/4' to Decimal(0.25)"""
    try:
        quantity_str = str(quantity_str).strip()

        if '/' in quantity_str:
            if ' ' in quantity_str:  # Mixed number like "1 1/2"
                parts = quantity_str.split(' ')
                whole = Decimal(parts[0])
                frac = Fraction(parts[1])
                return whole + Decimal(frac.numerator) / Decimal(frac.denominator)
            else:  # Simple fraction like "1/4"
                frac = Fraction(quantity_str)
                return Decimal(frac.numerator) / Decimal(frac.denominator)
        else:
            return Decimal(quantity_str)
    except Exception as e:
        print(f"Error converting '{quantity_str}': {e}")
        return Decimal("1")

def format_quantity(quantity_str):
    """Format for display - keep fractions as-is"""
    try:
        quantity_str = str(quantity_str).strip()

        # Keep fractions as fractions
        if '/' in quantity_str:
            return quantity_str

        # Remove trailing zeros from decimals
        num = float(quantity_str)
        return '{:g}'.format(num)

    except:
        return str(quantity_str)

def get_preferred_weight_conversion(from_unit, ingredient=None):
    """Try each weight unit in priority order, ingredient-specific first then generic."""
    for abbr in WEIGHT_UNIT_PRIORITY:
        # Ingredient-specific first
        if ingredient:
            conversion = UnitConversion.objects.filter(
                from_unit=from_unit,
                to_unit__abbreviation=abbr,
                to_unit__unit_type='weight',
                specific_ingredient=ingredient
            ).select_related('to_unit').first()
            if conversion:
                return conversion

        # Generic fallback
        conversion = UnitConversion.objects.filter(
            from_unit=from_unit,
            to_unit__abbreviation=abbr,
            to_unit__unit_type='weight',
            specific_ingredient__isnull=True
        ).select_related('to_unit').first()
        if conversion:
            return conversion

    return None

def get_or_create_ingredient(name):
    """Get or create an ingredient by name (case-insensitive)"""
    name = name.strip()
    # Capitalize each word
    name = ' '.join(word.capitalize() for word in name.split())

    ingredient, created = Ingredient.objects.get_or_create(
        name__iexact=name,
        defaults={'name': name}
    )
    return ingredient


def get_or_create_unit(name):
    """Get or create a measurement unit by name (case-insensitive)"""
    name = name.strip().lower()

    # Try to find existing
    unit = MeasurementUnit.objects.filter(name__iexact=name).first()
    if unit:
        return unit

    # Create new with abbreviation
    abbr = name[:5] if len(name) <= 5 else name[:4] + '.'
    unit = MeasurementUnit.objects.create(
        name=name,
        abbreviation=abbr,
        unit_type='other'
    )
    return unit


def get_or_create_preparation(name):
    """Get or create a preparation method by name (case-insensitive)"""
    if not name or not name.strip():
        return None

    name = name.strip().lower()

    prep, created = PreparationMethod.objects.get_or_create(
        name__iexact=name,
        defaults={'name': name}
    )
    return prep