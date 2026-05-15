"""
Invoices views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split.
Covers the invoice list/commit pages, the SMTP helper that notifies on
payment, and the two open-invoice reporting views.
"""
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from ..models import invoices, props, tenant


@permission_required('auth.can_access_invoices', raise_exception=True)
@login_required
def invoices_page(request):
    # Get filter values from POST request
    prop_output = request.POST.get('propname', '')
    tenant_output = request.POST.get('tenantname', '')

    # Always get all props for the dropdown
    all_props = props.objects.all().order_by('prop_country', 'prop_name')

    # Always get all tenants for the dropdown
    all_tenants = tenant.objects.all().order_by('tenant_name')

    # Get unpaid invoices
    iresults = invoices.objects.filter(invoice_paid="No").order_by('invoice_date')

    # Filter props based on selection
    if prop_output and prop_output != "All":
        filtered_props = props.objects.filter(prop_name=prop_output)
    else:
        filtered_props = all_props

    # Filter tenants based on selection
    if tenant_output and tenant_output != "All":
        filtered_tenants = tenant.objects.filter(tenant_name=tenant_output)
    else:
        filtered_tenants = all_tenants

    context = {
        "invoices": iresults,
        "tenant": filtered_tenants,  # Filtered tenants for display
        "props": filtered_props,     # Filtered props for display
        "all_props": all_props,      # All props for dropdown
        "all_tenants": all_tenants,  # All tenants for dropdown
        "selected_property": prop_output if prop_output != "All" else "",
        "selected_tenant": tenant_output if tenant_output != "All" else "",
    }

    return render(request, "invoices.html", context)


@permission_required('auth.can_edit_invoices', raise_exception=True)
@login_required
def invoices_commit(request, invoice_id):
    inv_tbp = invoices.objects.filter(pk=invoice_id).update(invoice_paid="Yes")
    iresults = invoices.objects.get(pk=invoice_id)
    tresults = tenant.objects.get(pk=iresults.tenant_id)

    # Get property information - FIXED: Changed 'prop' to 'props'
    presults = props.objects.get(pk=tresults.prop_id)

    # Attempt to send the notification email
    if send_invoices_paid_email(tresults, presults, iresults.invoice_date):
        messages.info(request, "Invoice marked as Paid notification email sent.")
    else:
        messages.warning(request, "Invoice marked as Paid, but email could not be sent.")
    return redirect('invoices')


def send_invoices_paid_email(tenant_obj, property_obj, invoice_date):
    """
    Send email notification of an invoice payment for a specific tenant
    """
    from django.db import connection
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header
    import logging
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import os

    logger = logging.getLogger(__name__)
    smtp_object = None

    try:
        # Get email recipients for invoice paid notifications (returns dict with to/cc/all)
        recipients = get_email_recipients('invoice_paid')

        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'
        email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')

        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients['cc']:
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = f"Invoice Paid - {property_obj.prop_name} - {tenant_obj.tenant_name}"

        # Build HTML email body
        html_body = f"""
        <html>
        <head>
        <style>
        p {{ margin: 0; padding: 0; }}
        .info-section {{ margin: 15px 0; }}
        .label {{ font-weight: bold; color: #2c3e50; }}
        .value {{ color: #495057; }}
        .success {{ color: #28a745; font-weight: bold; }}
        </style>
        </head>
        <body>
            <p>Dear User,</p>
            <br>
            <p class="success">✅ INVOICE MARKED AS PAID</p>
            <br>
            <div class="info-section">
                <p><span class="label">Property:</span> <span class="value">{property_obj.prop_name} ({property_obj.prop_country})</span></p>
                <p><span class="label">Tenant:</span> <span class="value">{tenant_obj.tenant_name}</span></p>
                <p><span class="label">Rental Amount:</span> <span class="value">€{tenant_obj.tenant_rent:,.2f}</span></p>
                <p><span class="label">Invoice Date:</span> <span class="value">{invoice_date.strftime('%Y-%m-%d')}</span></p>
            </div>
            <br>
            <p>This invoice has been successfully marked as paid in the Alivente Online System.</p>
            <br>
            <p>You can view all invoice records at <a href="https://alivente.online">alivente.online</a> in the Financial Management section.</p>
            <br>
            <p>Best regards,<br>
            Alivente Property Management System<br>
            Automated Invoice Tracking</p>
        </body>
        </html>
        """

        # Create plain text version
        text_body = f"""Dear User,

✅ INVOICE MARKED AS PAID

Property: {property_obj.prop_name} ({property_obj.prop_country})
Tenant: {tenant_obj.tenant_name}
Rental Amount: €{tenant_obj.tenant_rent:,.2f}
Invoice Date: {invoice_date.strftime('%Y-%m-%d')}

This invoice has been successfully marked as paid in the Alivente Online System.

You can view all invoice records at alivente.online in the Financial Management section.

Best regards,
Alivente Property Management System
Automated Invoice Tracking"""

        # Attach both HTML and plain text versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')

        msg.attach(part1)
        msg.attach(part2)

        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        smtp_object.login(email_user, email_password)

        # Send email to all recipients (TO + CC)
        text = msg.as_string()
        smtp_object.sendmail(email_user, recipients['all'], text)

        logger.info(f'Invoice paid notification sent for {property_obj.prop_name} - {tenant_obj.tenant_name}')
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending invoice paid email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()


@login_required
@permission_required('auth.can_access_invoices', raise_exception=True)
def open_invoices(request):
    # NB: imports the project-root ``open_invoices.py`` reporting helper,
    # not anything in this views file. Absolute imports resolve via sys.path.
    import open_invoices
    rep_output = request.POST.get('d_e')
    check = 'No'
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    open_invoices.open_invoices(rep_output, check, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')


@login_required
@permission_required('auth.can_access_invoices', raise_exception=True)
def open_invoices_report(request):

    today = date.today()
    properties_with_invoices = []

    # Get all current tenants with their property details
    current_tenants = tenant.objects.filter(
        tenant_current='Yes'
    ).select_related('prop').order_by('prop__prop_country', 'prop__prop_name')

    # Get all unpaid invoices with tenant details in one query
    unpaid_invoices = invoices.objects.filter(
        invoice_paid='No'
    ).select_related('tenant', 'tenant__prop').order_by('invoice_date')

    # Process detailed invoice breakdown
    for tenant_obj in current_tenants:
        tenant_invoices = []

        # Get unpaid invoices for this tenant
        tenant_unpaid_invoices = [inv for inv in unpaid_invoices if inv.tenant.tenant_id == tenant_obj.tenant_id]

        for invoice_obj in tenant_unpaid_invoices:
            payment_terms = tenant_obj.tenant_payment_terms or 0
            due_date = invoice_obj.invoice_date + timedelta(days=payment_terms)
            days_overdue = (today - due_date).days if today > due_date else 0

            tenant_invoices.append({
                'invoice_id': invoice_obj.invoice_id,
                'invoice_date': invoice_obj.invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'overdue': days_overdue > 0
            })

        # Only include tenants with unpaid invoices
        if tenant_invoices:
            properties_with_invoices.append({
                'prop_name': tenant_obj.prop.prop_name,
                'prop_country': tenant_obj.prop.prop_country,
                'tenant_id': tenant_obj.tenant_id,
                'tenant_name': tenant_obj.tenant_name,
                'tenant_contact_person': tenant_obj.tenant_contact_person,
                'tenant_contact_number': tenant_obj.tenant_contact_number,
                'tenant_email': tenant_obj.tenant_email,
                'tenant_rent': tenant_obj.tenant_rent,
                'tenant_payment_terms': tenant_obj.tenant_payment_terms,
                'invoices': tenant_invoices
            })

    # Calculate Debtors Age Analysis
    debtors_age_analysis = []
    totals = {
        'total_outstanding': 0,
        'current_0_30': 0,
        'past_due_31_60': 0,
        'past_due_61_90': 0,
        'past_due_91_plus': 0
    }

    for tenant_obj in current_tenants:
        tenant_analysis = {
            'tenant_name': tenant_obj.tenant_name,
            'tenant_id': tenant_obj.tenant_id,  # Add tenant_id here too
            'total_outstanding': 0,
            'current_0_30': 0,
            'past_due_31_60': 0,
            'past_due_61_90': 0,
            'past_due_91_plus': 0
        }

        # Get unpaid invoices for this tenant
        tenant_unpaid_invoices = [inv for inv in unpaid_invoices if inv.tenant.tenant_id == tenant_obj.tenant_id]

        # Calculate aging for this tenant's invoices
        for invoice_obj in tenant_unpaid_invoices:
            payment_terms = tenant_obj.tenant_payment_terms or 0
            due_date = invoice_obj.invoice_date + timedelta(days=payment_terms)
            days_overdue = (today - due_date).days if today > due_date else 0
            amount = float(tenant_obj.tenant_rent or 0)

            tenant_analysis['total_outstanding'] += amount

            if days_overdue <= 30:
                # Current (0-30 days - includes not yet due and up to 30 days overdue)
                tenant_analysis['current_0_30'] += amount
            elif 31 <= days_overdue <= 60:
                # Past due 31-60 days
                tenant_analysis['past_due_31_60'] += amount
            elif 61 <= days_overdue <= 90:
                # Past due 61-90 days
                tenant_analysis['past_due_61_90'] += amount
            else:
                # Past due 91+ days
                tenant_analysis['past_due_91_plus'] += amount

        # Only include tenants with outstanding invoices
        if tenant_analysis['total_outstanding'] > 0:
            debtors_age_analysis.append(tenant_analysis)

            # Add to totals
            totals['total_outstanding'] += tenant_analysis['total_outstanding']
            totals['current_0_30'] += tenant_analysis['current_0_30']
            totals['past_due_31_60'] += tenant_analysis['past_due_31_60']
            totals['past_due_61_90'] += tenant_analysis['past_due_61_90']
            totals['past_due_91_plus'] += tenant_analysis['past_due_91_plus']

    # Sort debtors by total outstanding (highest first)
    debtors_age_analysis.sort(key=lambda x: x['total_outstanding'], reverse=True)

    context = {
        'today': today.strftime('%Y-%m-%d'),
        'properties_with_invoices': properties_with_invoices,
        'debtors_age_analysis': debtors_age_analysis,
        'totals': totals
    }

    return render(request, 'open_invoices_report.html', context)