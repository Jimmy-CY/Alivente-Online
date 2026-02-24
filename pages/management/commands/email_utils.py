import os

def get_email_recipients(email_type='general'):
    """
    Get email recipients based on email type
    Priority: 1) Database, 2) Environment Variables, 3) Hardcoded defaults
    
    Args:
        email_type (str): Type of email - options:
            - 'daily_report': Daily property management reports
            - 'invoice_paid': Invoice payment notifications  
            - 'expense_added': New expense notifications
            - 'expense_approved': Expense approval notifications
            - 'expense_paid': Expense payment notifications
            - 'fsr': Financial Status Reports
            - 'passport_expiry': Passport/ID expiry notifications
            - 'document_expiry': Document expiry alerts (same as passport_expiry)
            - 'celebration_reminder': Celebration reminder notifications
            - 'new_lease_upload': New lease upload reminders
            - 'general': Default fallback
    
    Returns:
        list: List of email addresses
    """
    
    # Map email types to database notification types
    db_type_map = {
        'daily_report': 'daily_report',
        'passport_expiry': 'document_expiry',
        'document_expiry': 'document_expiry',
        'celebration_reminder': 'celebration_reminder',
        'new_lease_upload': 'new_lease_upload',
    }
    
    # Try to get from database first
    db_notification_type = db_type_map.get(email_type)
    if db_notification_type:
        try:
            from pages.models import NotificationRecipient
            recipient_obj = NotificationRecipient.objects.get(notification_type=db_notification_type)
            email_list = recipient_obj.get_email_list()
            if email_list:  # Only use if not empty
                return email_list
        except:
            pass  # Fall through to environment variables
    
    # Fall back to environment variables
    email_var_map = {
        'daily_report': 'EMAIL_TO_DAILY_REPORT',
        'invoice_paid': 'EMAIL_TO_INVOICE_PAID',
        'expense_added': 'EMAIL_TO_EXPENSE_ADDED',
        'expense_approved': 'EMAIL_TO_EXPENSE_APPROVED', 
        'expense_paid': 'EMAIL_TO_EXPENSE_PAID',
        'fsr': 'EMAIL_TO_FSR',
        'passport_expiry': 'EMAIL_TO_PASSPORT_EXPIRY',
        'document_expiry': 'EMAIL_TO_PASSPORT_EXPIRY',  # Same as passport
        'celebration_reminder': 'EMAIL_TO_CELEBRATION',
        'new_lease_upload': 'EMAIL_TO_DAILY_REPORT',  # Use same as daily report
        'general': 'EMAIL_TO'
    }
    
    # Get the environment variable name for this email type
    env_var = email_var_map.get(email_type, 'EMAIL_TO')
    
    # Get the email addresses from environment variable
    email_to_raw = os.environ.get(env_var)
    
    if email_to_raw:
        # Split by comma and strip whitespace
        email_list = [email.strip() for email in email_to_raw.split(',') if email.strip()]
        if email_list:
            return email_list
    
    # Final fallback to hardcoded defaults
    default_recipients = {
        'daily_report': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
        'passport_expiry': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
        'document_expiry': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
        'new_lease_upload': ['demetrimanias@gmail.com'],
        'celebration_reminder': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
        'invoice_paid': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
        'expense_added': ['demetrimanias@gmail.com'],
        'expense_approved': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
        'expense_paid': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
        'fsr': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'],
    }
    
    return default_recipients.get(email_type, ['demetrimanias@gmail.com'])

def format_email_recipients_for_header(email_list):
    """
    Format email list for email 'To' header
    
    Args:
        email_list (list): List of email addresses
        
    Returns:
        str: Comma-separated email addresses for email header
    """
    return ', '.join(email_list)