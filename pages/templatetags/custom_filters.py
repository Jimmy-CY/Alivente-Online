# templatetags/custom_filters.py

from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sort_by_expense_line_type(expenses):
    """
    Sort expenses by expense line type name alphabetically (case-insensitive)
    """
    if not expenses:
        return expenses
    
    try:
        return sorted(expenses, key=lambda exp: exp.expense_line_types.expense_line_types_name.lower() if exp.expense_line_types and exp.expense_line_types.expense_line_types_name else '')
    except (AttributeError, TypeError):
        return expenses

@register.filter
def sort_by_expense_type(expenses):
    """
    Sort expenses by expense type name alphabetically (case-insensitive)
    """
    if not expenses:
        return expenses
    
    try:
        return sorted(expenses, key=lambda exp: exp.expense_types.expense_types_name.lower() if exp.expense_types and exp.expense_types.expense_types_name else '')
    except (AttributeError, TypeError):
        return expenses

@register.filter
def sort_by_both(expenses):
    """
    Sort expenses first by expense line type, then by expense type (both alphabetically)
    """
    if not expenses:
        return expenses
    
    try:
        return sorted(expenses, key=lambda exp: (
            exp.expense_line_types.expense_line_types_name.lower() if exp.expense_line_types and exp.expense_line_types.expense_line_types_name else '',
            exp.expense_types.expense_types_name.lower() if exp.expense_types and exp.expense_types.expense_types_name else ''
        ))
    except (AttributeError, TypeError):
        return expenses

@register.filter
def sort_expense_line_types(expense_line_types):
    """
    Sort expense line types by their name alphabetically (case-insensitive)
    """
    if not expense_line_types:
        return expense_line_types
    
    try:
        return sorted(expense_line_types, key=lambda line_type: line_type.expense_line_types_name.lower() if line_type.expense_line_types_name else '')
    except (AttributeError, TypeError):
        return expense_line_types

@register.filter
def sort_revenue_line_types(revenue_line_types):
    """
    Sort revenue line types by their name alphabetically (case-insensitive)
    """
    if not revenue_line_types:
        return revenue_line_types
    
    try:
        return sorted(revenue_line_types, key=lambda line_type: line_type.revenue_line_types_name.lower() if line_type.revenue_line_types_name else '')
    except (AttributeError, TypeError):
        return revenue_line_types

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key, 0)  # Return 0 as default if key doesn't exist
    return 0  # Return 0 if input isn't a dictionary

@register.filter(name='subtract')
def subtract(value, arg):
    """Subtracts the arg from the value"""
    try:
        return float(value or 0) - float(arg or 0)
    except (ValueError, TypeError):
        return 0

@register.filter(name='add')
def add(value, arg):
    """Add arg to value"""
    try:
        return float(value or 0) + float(arg or 0)
    except (ValueError, TypeError):
        return 0

@register.filter(name='divide')
def divide(value, arg):
    """Divides the value by the arg"""
    try:
        arg_float = float(arg or 0)
        if arg_float == 0:
            return 0
        return float(value or 0) / arg_float
    except (ValueError, TypeError):
        return 0

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by the arg"""
    try:
        return float(value or 0) * float(arg or 0)
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_attr(iterable, attr):
    """Sums values of a specific attribute from a list of objects"""
    total = 0
    try:
        for item in iterable:
            if hasattr(item, attr):
                value = getattr(item, attr, 0)
                if value:
                    total += float(value)
    except (ValueError, TypeError):
        pass
    return total

@register.filter
def sum_purchase_prices(properties):
    """Sum purchase prices from properties"""
    total = 0
    try:
        for prop in properties:
            if hasattr(prop, 'prop_values_set') and prop.prop_values_set.exists():
                value = prop.prop_values_set.first().prop_values_purchase_price
                if value:  # Only add if not None
                    total += float(value)
    except (ValueError, TypeError):
        pass
    return total

@register.filter
def sum_prop_values(properties, attr_name):
    """Sum property values by attribute name"""
    total = 0
    try:
        for prop in properties:
            if hasattr(prop, 'prop_values_set') and prop.prop_values_set.exists():
                value = getattr(prop.prop_values_set.first(), attr_name, 0)
                if value:
                    total += float(value)
    except (ValueError, TypeError):
        pass
    return total

@register.filter
def add_thousand_separator(value):
    """Add thousand separators to a number"""
    try:
        # Convert to integer first to remove decimals, then format with commas
        return "{:,}".format(int(float(value)))
    except (ValueError, TypeError):
        return value

@register.filter
def sum_amounts(items):
    """Sum the 'amount' field from a list of dictionaries"""
    if not items:
        return 0
    total = Decimal('0')
    try:
        for item in items:
            if isinstance(item, dict) and 'amount' in item:
                amount = item['amount']
                if amount:
                    total += Decimal(str(amount))
    except (ValueError, TypeError):
        pass
    return total

@register.filter
def sum_field(queryset, field_name):
    """Sum a specific field from a queryset"""
    if not queryset:
        return 0
    total = Decimal('0')
    try:
        for item in queryset:
            field_value = getattr(item, field_name, None)
            if field_value:
                total += Decimal(str(field_value))
    except (ValueError, TypeError):
        pass
    return total

@register.filter
def normalize_decimal(value):
    """Remove trailing zeros from decimal numbers without using scientific notation"""
    if value is None:
        return ''
    
    try:
        # Convert to Decimal if not already
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Normalize removes trailing zeros but may use scientific notation
        normalized = value.normalize()
        
        # Check if it's in scientific notation (has 'E' in string)
        str_value = str(normalized)
        if 'E' in str_value.upper():
            # Convert back without scientific notation
            # Use a context with enough precision
            from decimal import Context, ROUND_HALF_UP
            ctx = Context(prec=50, rounding=ROUND_HALF_UP)
            normalized = ctx.create_decimal(value)
            
            # Format as fixed-point, then strip trailing zeros
            str_value = format(normalized, 'f')
            
            # Remove trailing zeros after decimal point
            if '.' in str_value:
                str_value = str_value.rstrip('0').rstrip('.')
            
            return str_value
        
        return str_value
    except:
        return str(value)

@register.filter
def format_unit(unit, amount):
    """Format unit with proper singular/plural based on amount"""
    if unit is None:
        return ''
    
    try:
        amount = float(amount) if amount else 1
    except (ValueError, TypeError):
        amount = 1
    
    # Use the model's get_display_name method if available
    if hasattr(unit, 'get_display_name'):
        return unit.get_display_name(amount)
    
    # Fallback: if it's a MeasurementUnit object without the method
    if hasattr(unit, 'abbreviation') and hasattr(unit, 'abbreviation_plural'):
        if amount == 1:
            return unit.abbreviation or unit.name
        else:
            return unit.abbreviation_plural or unit.abbreviation or unit.name_plural or unit.name
    
    # Final fallback for string
    return str(unit)


@register.filter
def format_amount(value):
    """Format amount - remove unnecessary decimals"""
    if value is None:
        return ''
    
    try:
        num = float(value)
        # If it's a whole number, show without decimals
        if num == int(num):
            return str(int(num))
        # Otherwise show up to 2 decimal places, removing trailing zeros
        return f"{num:.2f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value)