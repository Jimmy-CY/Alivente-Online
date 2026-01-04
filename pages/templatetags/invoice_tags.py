# pages/templatetags/invoice_tags.py
# Create this file in your Django app's templatetags folder

from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.simple_tag
def calculate_due_date(invoice_date, payment_terms):
    """
    Calculate due date from invoice date and payment terms
    
    Args:
        invoice_date: Date object or string
        payment_terms: Integer (number of days)
    
    Returns:
        Date object representing the due date
    """
    if not invoice_date or payment_terms is None:
        return invoice_date
    
    # Convert string to date if necessary
    if isinstance(invoice_date, str):
        try:
            invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d').date()
        except ValueError:
            return invoice_date
    
    # Calculate due date
    due_date = invoice_date + timedelta(days=int(payment_terms))
    return due_date


@register.simple_tag
def calculate_days_overdue(due_date):
    """
    Calculate days overdue from due date to today
    
    Args:
        due_date: Date object
    
    Returns:
        Integer representing days overdue (0 if not overdue)
    """
    if not due_date:
        return 0
    
    # Convert string to date if necessary
    if isinstance(due_date, str):
        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except ValueError:
            return 0
    
    today = datetime.now().date()
    
    if today > due_date:
        return (today - due_date).days
    else:
        return 0