"""
Invoices views.

Extracted from the legacy pages/views/main.py during the modular views
split. Covers the unpaid-invoice list/commit pages, the SMTP helper
that emails a notification when an invoice is marked paid, and the two
open-invoice reporting views (including the Debtors Age Analysis).

Note: this module intentionally contains non-ASCII characters in the
notification-email bodies (the Euro sign and a check-mark glyph). Those
are user-facing content and must be preserved byte-for-byte - do NOT
"ASCII-ize" them.

Functions
---------
- invoices_page            : Unpaid-invoice list with property /
                             tenant filters.
- invoices_commit          : Mark an invoice paid; send notification.
- send_invoices_paid_email : SMTP helper (lazy-imported deps; returns
                             bool success).
- open_invoices_report     : Render the on-screen Debtors Age Analysis.

Auth tiers
----------
read tier -> auth.can_access_invoices  (invoices_page,
                                        open_invoices_report)
edit tier -> auth.can_edit_invoices    (invoices_commit)
"""

from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from ..models import invoices, props, tenant


def _open_invoice_rows(open_invoices, shown_props, shown_tenants):
    """One row per open invoice, in the order the template's loops produced.

    The template used to do this itself:

        for p in props: for t in tenant: for i in invoices:
            if i.tenant_id == t.tenant_id and t.prop_id == p.prop_id

    which is O(props x tenants x invoices) comparisons to print a few dozen
    rows, and - because the decision is taken inside the loop - leaves the
    template unable to say whether it printed any.

    ORDER IS REPRODUCED BY POSITION, NOT BY SORT KEY. `shown_props` may be
    `props.objects.filter(prop_name=...)`, which carries no `order_by`, so
    its order is whatever the database returned and cannot be rebuilt from
    prop_country and prop_name. The loops walked these lists in order, so the
    index in each list is the sort key, with the invoice's own position last.

    A row is skipped on exactly the two conditions the `{% if %}` skipped on:
    the invoice's tenant is not in `shown_tenants`, or that tenant's property
    is not in `shown_props`.
    """
    tenant_at, tenant_by_id = {}, {}
    for i, t in enumerate(shown_tenants):
        if t.tenant_id not in tenant_by_id:      # first wins, as the loop did
            tenant_at[t.tenant_id] = i
            tenant_by_id[t.tenant_id] = t
    prop_at, prop_by_id = {}, {}
    for i, p in enumerate(shown_props):
        if p.prop_id not in prop_by_id:
            prop_at[p.prop_id] = i
            prop_by_id[p.prop_id] = p

    today = date.today()
    ordered = []
    for pos, inv in enumerate(open_invoices):
        t = tenant_by_id.get(inv.tenant_id)
        if t is None:
            continue
        p = prop_by_id.get(t.prop_id)
        if p is None:
            continue
        # Same arithmetic as calculate_due_date / calculate_days_overdue, and
        # the same as open_invoices_report. It is written here once now.
        #
        # The None guard is not defensive habit - it is fidelity. The old tag
        # returned the invoice date unchanged when it had nothing to add to,
        # and 0 days overdue from there, so an invoice with no date rendered
        # a blank-dated row rather than raising. Dropping the guard would turn
        # that row into a 500.
        terms = t.tenant_payment_terms or 0
        if inv.invoice_date:
            due = inv.invoice_date + timedelta(days=int(terms))
            overdue = (today - due).days if today > due else 0
        else:
            due, overdue = None, 0
        ordered.append(((prop_at[p.prop_id], tenant_at[t.tenant_id], pos), {
            'invoice_id':   inv.invoice_id,
            'prop_name':    p.prop_name,
            'prop_country': p.prop_country,
            'tenant_name':  t.tenant_name,
            'amount':       inv.effective_amount,
            'invoice_date': inv.invoice_date,
            'due_date':     due,
            'days_overdue': overdue,
            'is_overdue':   overdue > 0,
        }))
    ordered.sort(key=lambda pair: pair[0])
    return [row for _, row in ordered]


@login_required
@permission_required('auth.can_access_invoices', raise_exception=True)
def invoices_page(request):
    # Get filter values from POST request
    prop_output = request.POST.get('propname', '')
    tenant_output = request.POST.get('tenantname', '')

    # Always get all props for the dropdown
    all_props = props.objects.all().order_by('prop_country', 'prop_name')

    # Always get all tenants for the dropdown
    all_tenants = tenant.objects.all().order_by('tenant_name')

    # Get unpaid invoices
    iresults = invoices.objects.filter(invoice_paid="No").select_related('tenant').order_by('invoice_date')

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
        # The rows the table draws, decided here rather than by three nested
        # loops in the template. `filtered_*` still say WHICH rows; they are
        # no longer what the dropdowns are built from.
        "rows": _open_invoice_rows(iresults, filtered_props, filtered_tenants),
        # The dropdowns list EVERY property and tenant. They used to be built
        # from the filtered lists, so choosing property X left the property
        # dropdown holding only X - you could not move to Y without clearing
        # first. Both of these were already in this context and unused.
        "all_props": all_props,
        "all_tenants": all_tenants,
        "selected_property": prop_output if prop_output != "All" else "",
        "selected_tenant": tenant_output if tenant_output != "All" else "",
    }

    return render(request, "invoices.html", context)


@login_required
@permission_required('auth.can_edit_invoices', raise_exception=True)
def invoices_commit(request, invoice_id):
    # Mark paid AND stamp the paid date. .update() is a direct SQL UPDATE that
    # bypasses the model's save() (which also stamps the date), so the date must
    # be set explicitly here — this button is the primary "mark paid" path.
    inv_tbp = invoices.objects.filter(pk=invoice_id).update(
        invoice_paid="Yes", invoice_paid_date=date.today())
    iresults = invoices.objects.get(pk=invoice_id)
    tresults = tenant.objects.get(pk=iresults.tenant_id)

    # Get property information
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
    # Deferred imports: only needed when actually sending the notification
    # email. pages.email_utils is imported here (not at module top) to
    # avoid a circular import at views package load time.
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

            invoice_amount = invoice_obj.effective_amount

            tenant_invoices.append({
                'invoice_id': invoice_obj.invoice_id,
                'invoice_date': invoice_obj.invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'amount': float(invoice_amount),
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
            amount = float(invoice_obj.effective_amount)

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