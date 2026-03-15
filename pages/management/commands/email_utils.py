import os

def get_email_recipients(notification_type):
    """
    Get email recipients for a notification type with TO/CC distinction.
    Returns a dict with 'to', 'cc', and 'all' lists.
    Priority: Database > Environment Variables > Defaults
    """
    from pages.models import NotificationRecipient
    
    # Try database first
    try:
        recipient = NotificationRecipient.objects.get(notification_type=notification_type)
        return {
            'to': recipient.get_to_list(),
            'cc': recipient.get_cc_list(),
            'all': recipient.get_all_recipients()
        }
    except NotificationRecipient.DoesNotExist:
        pass
    
    # Map notification types to environment variable names
    env_var_map = {
        'celebration_reminder': 'EMAIL_TO_CELEBRATION',
        'passport_expiry': 'EMAIL_TO_PASSPORT_EXPIRY',
        'document_expiry': 'EMAIL_TO_PASSPORT_EXPIRY',
        'daily_report': 'EMAIL_TO_DAILY_REPORT',
        'new_lease_upload': 'EMAIL_TO_DAILY_REPORT',
    }
    
    # Try environment variables
    env_var = env_var_map.get(notification_type)
    if env_var:
        env_value = os.environ.get(env_var)
        if env_value:
            emails = [e.strip() for e in env_value.split(',') if e.strip()]
            return {'to': emails, 'cc': [], 'all': emails}
    
    # Default recipients with TO/CC distinction
    default_recipients = {
        'daily_report': {'to': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'], 'cc': []},
        'document_expiry': {'to': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com', 'erenemanias@gmail.com', 'leximanias@gmail.com'], 'cc': []},
        'passport_expiry': {'to': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com', 'erenemanias@gmail.com', 'leximanias@gmail.com'], 'cc': []},
        'celebration_reminder': {'to': ['demetrimanias@gmail.com', 'angmaniasbakers@gmail.com'], 'cc': []},
        'new_lease_upload': {'to': ['demetrimanias@gmail.com'], 'cc': []},
        'expense_needs_approval': {'to': ['demetrimanias@gmail.com'], 'cc': ['stella.simitopoulos@alivente.com']},
        'expense_approved': {'to': ['stella.simitopoulos@alivente.com'], 'cc': ['demetrimanias@gmail.com']},
        'expense_paid': {'to': ['stella.simitopoulos@alivente.com'], 'cc': ['demetrimanias@gmail.com']},
        'friday_status_report_supervisor': {'to': ['stella.simitopoulos@alivente.com'], 'cc': ['angmaniasbakers@gmail.com']},
        'friday_status_report_staff': {'to': ['demetrimanias@gmail.com'], 'cc': ['angmaniasbakers@gmail.com']},
    }
    
    defaults = default_recipients.get(notification_type, {'to': ['demetrimanias@gmail.com'], 'cc': []})
    defaults['all'] = defaults['to'] + defaults['cc']
    return defaults

def format_email_recipients_for_header(email_list):
    """
    Format email list for email 'To' header
    
    Args:
        email_list (list): List of email addresses
        
    Returns:
        str: Comma-separated email addresses for email header
    """
    return ', '.join(email_list)