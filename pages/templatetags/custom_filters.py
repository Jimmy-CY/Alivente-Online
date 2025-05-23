from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name='subtract')
def subtract(value, arg):
    """Subtracts the arg from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:
            return 0

@register.filter(name='divide')
def divide(value, arg):
    """Divides the value by the arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by the arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        try:
            return value * arg
        except Exception:
            return 0

@register.filter
def sum_attr(iterable, attr):
    """Sums values of a specific attribute from a list of objects"""
    return sum(getattr(item, attr, 0) for item in iterable if hasattr(item, attr))

@register.filter
def sum_purchase_prices(properties):
    total = 0
    for prop in properties:
        if prop.prop_values_set.exists():
            value = prop.prop_values_set.first().prop_values_purchase_price
            if value:  # Only add if not None
                total += float(value)
    return total

@register.filter
def sum_prop_values(properties, attr_name):
    total = 0
    for prop in properties:
        if hasattr(prop, 'prop_values_set') and prop.prop_values_set.exists():
            value = getattr(prop.prop_values_set.first(), attr_name, 0)
            total += value if value else 0
    return total
