import logging
import os
import smtplib
from collections import OrderedDict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


# Admin user initials. Mirrors the hardcoded list previously duplicated in
# pages/views/main.py (comments_report view) and the management command's
# get_yesterdays_issue_comments fetcher. Both now import from here.
ADMIN_USER_INITIALS = ['DM']

# How long to suppress repeat "Notify Immediately" presses on the same comment.
URGENT_NOTIFICATION_COOLDOWN_MINUTES = 5

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
        'issue_comments_daily': {'to': ['demetrimanias@gmail.com'], 'cc': []},
        'issue_comment_urgent': {'to': ['demetrimanias@gmail.com', 'stella.simitopoulos@alivente.com'], 'cc': []},
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

# ============================================================================
# Issue-comments email rendering & sending
# Used by both the daily cron (check_lease_renewal_and_invoices) and the
# immediate "Notify Urgent" view (pages.views.main.notify_comment_urgent).
# ============================================================================

def render_issue_comments_email_html(grouped, header_label, intro_text):
    """
    Build the HTML body for an issue-comments email.

    Parameters:
        grouped       -- OrderedDict: prop_key -> issue_key -> [comment_dicts]
        header_label  -- bold/underlined banner inside the body
                         (e.g. "DAILY ISSUE COMMENTS REPORT - 2026/05/13"
                          or   "URGENT ISSUE COMMENT - 2026/05/13 14:32")
        intro_text    -- sentence under the banner

    Returns a complete HTML string ready for MIMEText.
    """
    html_body = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #2c3e50; line-height: 1.5; }}
        p {{ margin: 0; padding: 0; }}
        .header-line {{ color: #17a2b8; font-weight: bold; }}
        .property-bar {{
            background-color: #f0f9fb;
            border-left: 4px solid #17a2b8;
            padding: 10px 14px;
            margin: 24px 0 8px 0;
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
        }}
        .issue-block {{
            margin: 8px 0 16px 12px;
            padding: 10px 14px;
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 6px;
        }}
        .issue-heading {{ font-weight: 600; color: #2c3e50; font-size: 14px; }}
        .issue-description {{ font-style: italic; color: #6c757d; font-size: 13px; margin-top: 2px; }}
        .status-badge {{
            display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 11px;
            font-weight: 600; margin-left: 8px; vertical-align: middle;
        }}
        .status-resolved {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .status-unresolved {{ background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
        .status-other {{ background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
    </style>
    </head>
    <body>
        <p>Dear User,</p>
        <br>
        <p><b><u class="header-line">{header_label}:</u></b></p>
        <p>{intro_text}</p>
        <div style="margin: 12px 0; font-size: 13px;">
            <span style="margin-right: 16px;">
                <span style="background-color: #e3f2fd; border: 1px solid #90caf9; padding: 2px 10px; margin-right: 6px;">&nbsp;&nbsp;</span>Admin Comments
            </span>
            <span>
                <span style="background-color: #fff3e0; border: 1px solid #ffcc80; padding: 2px 10px; margin-right: 6px;">&nbsp;&nbsp;</span>User Comments
            </span>
        </div>
    """

    for prop_key, issues_dict in grouped.items():
        html_body += f'<div class="property-bar">{prop_key}</div>'
        for (issue_heading, issue_status, issue_description), issue_comments in issues_dict.items():
            if issue_status == 'Resolved':
                badge_class = 'status-resolved'
            elif issue_status in ('Unresolved', 'Open'):
                badge_class = 'status-unresolved'
            else:
                badge_class = 'status-other'

            html_body += f"""
            <div class="issue-block">
                <div>
                    <span class="issue-heading">{issue_heading}</span>
                    <span class="status-badge {badge_class}">{issue_status}</span>
                </div>
            """
            if issue_description:
                html_body += f'<div class="issue-description">{issue_description}</div>'

            for c in issue_comments:
                if c['is_admin']:
                    box_style = "background-color: #e3f2fd; border-left: 3px solid #1565c0;"
                    user_color = "#1565c0"
                else:
                    box_style = "background-color: #fff3e0; border-left: 3px solid #e65100;"
                    user_color = "#e65100"
                html_body += f"""
                <div style="margin-top: 10px; padding: 10px 12px; border-radius: 5px; {box_style}">
                    <div style="font-size: 14px; color: #2c3e50;">"{c['comment']}"</div>
                    <div style="font-size: 12px; color: #6c757d; margin-top: 4px;">
                        &mdash; <span style="color: {user_color}; font-weight: 600;">{c['user']}</span> on {c['date']}
                    </div>
                </div>
                """

            html_body += "</div>"

    html_body += """
        <br>
        <p>Please log into the Alivente Online System at <a href="https://alivente.online">alivente.online</a> for full details and to manage these issues.</p>
        <br>
        <p>Best regards,<br>
        Alivente Property Management System<br>
        Automated Issue Comments Report</p>
    </body>
    </html>
    """
    return html_body


def render_issue_comments_email_text(grouped, header_label, intro_text):
    """
    Build the plain-text body for an issue-comments email.
    Same grouped structure and parameters as the HTML renderer.
    """
    text_body = f"""Dear User,

{header_label}:

{intro_text}

(Legend: [ADMIN] = Admin comment, [USER] = User comment)
"""
    for prop_key, issues_dict in grouped.items():
        text_body += f"\n=== {prop_key} ===\n"
        for (issue_heading, issue_status, issue_description), issue_comments in issues_dict.items():
            text_body += f"\nIssue: {issue_heading} [{issue_status}]\n"
            if issue_description:
                text_body += f"  Description: {issue_description}\n"
            for c in issue_comments:
                role = '[ADMIN]' if c['is_admin'] else '[USER]'
                text_body += f'  {role} "{c["comment"]}" -- {c["user"]} on {c["date"]}\n'

    text_body += """

Please log into the Alivente Online System at alivente.online for full details and to manage these issues.

Best regards,
Alivente Property Management System
Automated Issue Comments Report"""
    return text_body


def send_issue_comments_email(comments, subject, header_label, intro_text, recipients):
    """
    Group, render, and SMTP-send an issue-comments email.

    Used by both the daily cron (in check_lease_renewal_and_invoices.py) and
    the immediate "Notify Urgent" view (notify_comment_urgent).

    Parameters:
        comments      -- list of comment dicts (same shape as the daily fetcher returns)
        subject       -- email subject line
        header_label  -- bold/underlined banner inside the body
        intro_text    -- sentence under the banner
        recipients    -- dict with 'to', 'cc', 'all' keys (from get_email_recipients)

    Returns True on success, False on failure.
    Returns True without sending if comments is empty, so callers can blindly call this.
    """
    smtp_object = None

    if not comments:
        return True

    if not recipients or not recipients.get('all'):
        logger.warning('send_issue_comments_email: no recipients, skipping')
        return False

    try:
        # Email settings — same env vars as every other sender in the project
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('send_issue_comments_email: EMAIL_PASSWORD not set')
            return False

        # Group: prop -> issue -> [comments]
        grouped = OrderedDict()
        for c in comments:
            prop_key = f"{c['prop_name']}{' (' + c['prop_country'] + ')' if c['prop_country'] else ''}"
            if prop_key not in grouped:
                grouped[prop_key] = OrderedDict()
            issue_key = (c['issue_heading'], c['issue_status'], c['issue_description'])
            if issue_key not in grouped[prop_key]:
                grouped[prop_key][issue_key] = []
            grouped[prop_key][issue_key].append(c)

        # Build MIME message
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients.get('cc'):
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = subject

        html_body = render_issue_comments_email_html(grouped, header_label, intro_text)
        text_body = render_issue_comments_email_text(grouped, header_label, intro_text)

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send via SMTP
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        smtp_object.login(email_user, email_password)
        smtp_object.sendmail(email_user, recipients['all'], msg.as_string())

        logger.info(f'Issue comments email sent: {subject}')
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f'SMTP Authentication Error: {e}')
        return False
    except smtplib.SMTPException as e:
        logger.error(f'SMTP Error: {e}')
        return False
    except Exception as e:
        logger.error(f'Error sending issue comments email: {e}', exc_info=True)
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except Exception:
                pass