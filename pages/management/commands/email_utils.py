import os

def get_email_recipients(email_type='general'):
    """
    Get email recipients based on email type
    
    Args:
        email_type (str): Type of email - options:
            - 'daily_report': Daily property management reports
            - 'invoice_paid': Invoice payment notifications  
            - 'expense_added': New expense notifications
            - 'expense_approved': Expense approval notifications
            - 'expense_paid': Expense payment notifications
            - 'fsr': Financial Status Reports
            - 'general': Default fallback
    
    Returns:
        list: List of email addresses
    """
    
    email_var_map = {
        'daily_report': 'EMAIL_TO_DAILY_REPORT',
        'invoice_paid': 'EMAIL_TO_INVOICE_PAID',
        'expense_added': 'EMAIL_TO_EXPENSE_ADDED',
        'expense_approved': 'EMAIL_TO_EXPENSE_APPROVED', 
        'expense_paid': 'EMAIL_TO_EXPENSE_PAID',
        'fsr': 'EMAIL_TO_FSR',
        'general': 'EMAIL_TO'
    }
    
    # Get the environment variable name for this email type
    env_var = email_var_map.get(email_type, 'EMAIL_TO')
    
    # Get the email addresses from environment variable
    email_to_raw = os.environ.get(env_var, 'demetrimanias@gmail.com')
    
    # Split by comma and strip whitespace
    email_list = [email.strip() for email in email_to_raw.split(',') if email.strip()]
    
    # Return the list (or fallback to default if empty)
    return email_list if email_list else ['demetrimanias@gmail.com']

def format_email_recipients_for_header(email_list):
    """
    Format email list for email 'To' header
    
    Args:
        email_list (list): List of email addresses
        
    Returns:
        str: Comma-separated email addresses for email header
    """
    return ', '.join(email_list)