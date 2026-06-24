"""
Management command: prepare_physical_invoices

Run daily. Within the lead window (~5 days before month-end, configurable),
it creates a DRAFT physical invoice for each flagged active tenant for the
UPCOMING month, seeds the rent (+communal) lines, and emails the daily
"these drafts need approving" reminder listing whatever is still in draft.
Idempotent: safe to run every day.
"""
import os
import smtplib
from datetime import date, timedelta
from decimal import Decimal
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from pages.models import (
    tenant as Tenant, PhysicalInvoice, PhysicalInvoiceLine, NotificationRecipient,
)
from pages.services.physical_invoice_numbering import preview_batch_numbers

DEFAULT_VAT_RATE = Decimal("0.19")
REMINDER_TYPE = "physical_invoice_review"


def _upcoming_period(today):
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def _month_end(today):
    return _upcoming_period(today) - timedelta(days=1)


def _seed_lines(pi, month_label):
    t = pi.tenant
    PhysicalInvoiceLine.objects.create(
        physical_invoice=pi, service="RENTAL", unit_of_measure="MONTH",
        description=f"Rent for {month_label}", qty=1,
        unit_price=Decimal(t.tenant_rent or 0), vatable=True, sort_order=0)
    if getattr(t, "tenant_bill_levies", False) and (t.tenant_levies or 0):
        PhysicalInvoiceLine.objects.create(
            physical_invoice=pi, service="COMM", unit_of_measure="MONTH",
            description="Communal Fees", qty=1,
            unit_price=Decimal(t.tenant_levies), vatable=False, sort_order=1)


def ensure_month_drafts(period_first, vat_rate=DEFAULT_VAT_RATE):
    """Create a draft invoice for each flagged active tenant for the month,
    seeding lines. Idempotent. Returns (created, existing)."""
    month_label = period_first.strftime("%B %Y")
    created, existing = [], []
    flagged = (Tenant.objects
               .filter(tenant_physical_invoice_required=True, tenant_current="Yes")
               .order_by("tenant_name"))
    for t in flagged:
        pi, was_created = PhysicalInvoice.objects.get_or_create(
            tenant=t, period_year=period_first.year, period_month=period_first.month,
            defaults={"invoice_date": period_first, "vat_rate": vat_rate,
                      "status": PhysicalInvoice.STATUS_DRAFT})
        if was_created:
            _seed_lines(pi, month_label)
            pi.recalc_totals()
            created.append(pi)
        else:
            existing.append(pi)
    return created, existing


def reminder_rows(period_first):
    """Rows for the reminder: only invoices still in draft, with provisional #."""
    provisional = preview_batch_numbers(
        period_first.year, period_first.month, statuses=("draft", "approved"))
    drafts = (PhysicalInvoice.objects
              .filter(period_year=period_first.year, period_month=period_first.month,
                      status=PhysicalInvoice.STATUS_DRAFT)
              .select_related("tenant", "tenant__prop")
              .order_by("tenant__tenant_name"))
    rows = []
    for pi in drafts:
        rows.append({
            "number": provisional.get(pi.pk, ""),
            "tenant": pi.tenant.tenant_name,
            "property": getattr(pi.tenant.prop, "prop_name", "") or "",
            "total": pi.total,
            "pk": pi.pk,
        })
    return rows


class Command(BaseCommand):
    help = "Create upcoming-month draft physical invoices and send the daily approval reminder."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="Ignore the lead-time window and run anyway.")
        parser.add_argument("--month", help="Target month YYYY-MM (default: upcoming month).")
        parser.add_argument("--no-email", action="store_true", help="Skip the reminder email.")

    def handle(self, *args, **opts):
        today = timezone.localdate()
        lead_days = getattr(settings, "PHYSICAL_INVOICE_PREPARE_LEAD_DAYS", 5)

        if opts.get("month"):
            y, m = opts["month"].split("-")
            period_first, in_window = date(int(y), int(m), 1), True
        else:
            period_first = _upcoming_period(today)
            in_window = (_month_end(today) - today).days <= lead_days

        if not in_window and not opts["force"]:
            self.stdout.write(self.style.NOTICE(
                f"Outside the {lead_days}-day lead window "
                f"({(_month_end(today) - today).days} days to month-end); nothing to do."))
            return

        vat_rate = Decimal(str(getattr(settings, "PHYSICAL_INVOICE_VAT_RATE", "0.19")))
        created, existing = ensure_month_drafts(period_first, vat_rate)
        self.stdout.write(self.style.SUCCESS(
            f"{period_first:%B %Y}: {len(created)} draft(s) created, {len(existing)} already present."))

        if not opts["no_email"]:
            self._send_review_reminder(period_first)

    def _send_review_reminder(self, period_first):
        rows = reminder_rows(period_first)
        if not rows:
            self.stdout.write("No drafts awaiting approval; no reminder sent.")
            return
        month_label = period_first.strftime("%B %Y")
        count = len(rows)
        invoice_word = "invoice" if count == 1 else "invoices"
        is_are = "is" if count == 1 else "are"
        needs = "needs" if count == 1 else "need"
        them = "it" if count == 1 else "them"
        subject = f"Physical invoices to approve — {month_label} ({count} pending)"

        html_items = "".join(
            f"<li><b>{r['number']}</b> — {r['tenant']} ({r['property']}) "
            f"— €{r['total']:,.2f}</li>"
            for r in rows)
        text_items = "".join(
            f"\n \u2022 {r['number']}  {r['tenant']} ({r['property']})  €{r['total']:,.2f}"
            for r in rows)

        html_body = f"""
        <html>
        <head>
        <style>
        p {{ margin: 0; padding: 0; }}
        ul {{ margin: 0; padding: 0; padding-left: 20px; }}
        li {{ margin: 0; padding: 0; margin-bottom: 8px; }}
        .header {{ color: #cc0000; font-weight: bold; }}
        </style>
        </head>
        <body>
            <p>Dear User,</p>
            <br>
            <p><b><u class="header">PHYSICAL INVOICES TO APPROVE \u2014 {month_label.upper()} ({count}):</u></b></p>
            <p>The following physical {invoice_word} for {month_label} {is_are} still in DRAFT and {needs} approving:</p>
            <br>
            <ul>{html_items}</ul>
            <br>
            <p>Please log into the Alivente Online System to approve {them} before the 1st.</p>
            <br>
            <p>Best regards,<br>
            Alivente Property Management System<br>
            Automated Report</p>
        </body>
        </html>
        """

        text_body = (
            "Dear User,\n\n"
            f"PHYSICAL INVOICES TO APPROVE \u2014 {month_label.upper()} ({count}):\n"
            f"The following physical {invoice_word} for {month_label} {is_are} "
            f"still in DRAFT and {needs} approving:\n"
            f"{text_items}\n\n"
            f"Please log into the Alivente Online System to approve {them} "
            "before the 1st.\n\n"
            "Best regards,\n"
            "Alivente Property Management System\n"
            "Automated Report"
        )

        try:
            rec = NotificationRecipient.objects.get(notification_type=REMINDER_TYPE)
            to_list, cc_list = rec.get_to_list(), rec.get_cc_list()
        except NotificationRecipient.DoesNotExist:
            to_list, cc_list = [], []

        if not to_list:
            self.stdout.write(self.style.WARNING(
                f"No recipients configured for '{REMINDER_TYPE}'; reminder not sent."))
            return

        # Raw smtplib via the EMAIL_* env vars, matching the project's other
        # cron mailers (check_lease_renewal_and_invoices) so this uses the same
        # proven path as everything else rather than Django's mail backend.
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            self.stderr.write(self.style.ERROR(
                "EMAIL_PASSWORD not set; reminder not sent."))
            return

        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = ", ".join(to_list)
        if cc_list:
            msg['Cc'] = ", ".join(cc_list)
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        smtp_object = None
        try:
            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()
            smtp_object.login(email_user, email_password)
            smtp_object.sendmail(email_user, to_list + cc_list, msg.as_string())
            self.stdout.write(self.style.SUCCESS(
                f"Reminder sent to {len(to_list)} recipient(s) ({len(rows)} draft(s))."))
        except Exception as exc:  # don't let a mail failure abort the cron
            self.stderr.write(self.style.ERROR(f"Reminder send failed: {exc}"))
        finally:
            if smtp_object is not None:
                try:
                    smtp_object.quit()
                except Exception:
                    pass