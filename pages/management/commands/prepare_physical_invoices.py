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


def _period_end(period_first):
    """The last day of the period being billed.

    NOT _month_end(today) - that is the last day of the month the cron
    is RUNNING in. The period being billed is the next one, and the two
    were never the same thing; nothing used to need the distinction
    because nothing looked at the period's dates.
    """
    if period_first.month == 12:
        return date(period_first.year, 12, 31)
    return date(period_first.year, period_first.month + 1, 1) - timedelta(days=1)


def leases_for_period(period_first):
    """Every flagged lease whose term overlaps the period being billed.

    THIS IS THE WHOLE ROUND. The old query asked
    `tenant_current="Yes"`, which refresh_tenant_active sets from
    whether the lease covers TODAY - and this cron runs five days before
    the month it is billing. On 26 November that selected the lease
    ending 30 November and could not see the renewal starting 1
    December.

    NEVER ASSUME. A row whose lease dates are blank is excluded: a lease
    with no term cannot be said to cover anything, so a renewal that has
    not been filled in yet produces no invoice rather than a guessed
    one. The gap is reported instead - see period_gaps().

    NO GROUPING. models.py's _lease_month resolves an overlap with
    "latest-starting wins", which is right for a forecast - a property
    earns one rent - and wrong here: a tenant leaving on the 15th and
    another arriving on the 16th do not overlap, both cover the month,
    and both must be billed.
    """
    pe = _period_end(period_first)
    return (Tenant.objects
            .filter(tenant_physical_invoice_required=True,
                    tenant_lease_start_date__isnull=False,
                    tenant_lease_end_date__isnull=False,
                    tenant_lease_start_date__lte=pe,
                    tenant_lease_end_date__gte=period_first)
            .order_by("tenant_name"))


def covers_whole_period(lease, period_first):
    """Does this lease run for the whole of the period being billed?

    Derived, not stored - no model field and no migration. A lease that
    starts after the 1st or ends before the last day bills a FULL month
    and is flagged in the approval email, because pro-rata is a
    commercial decision and not one a cron should take quietly.
    """
    return (lease.tenant_lease_start_date <= period_first
            and lease.tenant_lease_end_date >= _period_end(period_first))


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


def reseed_draft(pi, month_label):
    """Correct a DRAFT whose governing lease has moved under it.

    Drafts are created once and the lines were seeded only on creation,
    so a renewal uploaded after the draft exists left the old rent in
    place for ever.

    ONLY A DRAFT, AND ONLY THE LINES THIS CRON WROTE. The match is on
    the generated description, so a line edited by hand stops being this
    cron's business and is left exactly as it is. Approved and sent
    invoices are never touched - the caller checks the status, and so
    does this.

    Returns a list of plain-English changes, empty when nothing moved.
    """
    if pi.status != PhysicalInvoice.STATUS_DRAFT:
        return []
    t = pi.tenant
    rent_desc = f"Rent for {month_label}"
    want_rent = Decimal(t.tenant_rent or 0)
    bill_comm = bool(getattr(t, "tenant_bill_levies", False)
                     and (t.tenant_levies or 0))
    want_comm = Decimal(t.tenant_levies or 0)
    changes = []

    rent = pi.lines.filter(service="RENTAL", description=rent_desc).first()
    if rent is not None and Decimal(rent.unit_price or 0) != want_rent:
        changes.append(f"rent {rent.unit_price:,.2f} -> {want_rent:,.2f}")
        rent.unit_price = want_rent
        rent.save()

    comm = pi.lines.filter(service="COMM", description="Communal Fees").first()
    if bill_comm and comm is None:
        PhysicalInvoiceLine.objects.create(
            physical_invoice=pi, service="COMM", unit_of_measure="MONTH",
            description="Communal Fees", qty=1, unit_price=want_comm,
            vatable=False, sort_order=1)
        changes.append(f"communal added at {want_comm:,.2f}")
    elif bill_comm and Decimal(comm.unit_price or 0) != want_comm:
        changes.append(f"communal {comm.unit_price:,.2f} -> {want_comm:,.2f}")
        comm.unit_price = want_comm
        comm.save()
    elif not bill_comm and comm is not None:
        changes.append(f"communal removed ({comm.unit_price:,.2f})")
        comm.delete()

    if changes:
        pi.recalc_totals()
    return changes


def ensure_month_drafts(period_first, vat_rate=DEFAULT_VAT_RATE):
    """Create a draft invoice for each lease COVERING THE PERIOD, seeding
    lines; correct any draft whose lease has moved. Idempotent.
    Returns (created, existing, reseeded)."""
    month_label = period_first.strftime("%B %Y")
    created, existing, reseeded = [], [], []
    for t in leases_for_period(period_first):
        pi, was_created = PhysicalInvoice.objects.get_or_create(
            tenant=t, period_year=period_first.year, period_month=period_first.month,
            defaults={"invoice_date": period_first, "vat_rate": vat_rate,
                      "status": PhysicalInvoice.STATUS_DRAFT})
        if was_created:
            _seed_lines(pi, month_label)
            pi.recalc_totals()
            created.append(pi)
        else:
            changes = reseed_draft(pi, month_label)
            if changes:
                reseeded.append((pi, changes))
            existing.append(pi)
    return created, existing, reseeded


def _previous_period(period_first):
    if period_first.month == 1:
        return date(period_first.year - 1, 12, 1)
    return date(period_first.year, period_first.month - 1, 1)


def period_gaps(period_first):
    """Tenants invoiced LAST period and not this one, with the reason.

    Picking by period means a tenant whose lease does not reach into the
    period gets nothing. That is correct and it is SILENT, and silence is
    the better failure but still the wrong thing to discover in
    February. So it is named here.

    The definition is self-limiting on purpose: it fires the month a
    lease lapses or a renewal is left blank, and goes quiet once the
    tenant is genuinely gone, because there is no invoice last period
    either.
    """
    prev = _previous_period(period_first)
    had = (PhysicalInvoice.objects
           .filter(period_year=prev.year, period_month=prev.month,
                   tenant__isnull=False)
           .select_related("tenant", "tenant__prop"))
    now_ids = set(PhysicalInvoice.objects
                  .filter(period_year=period_first.year,
                          period_month=period_first.month,
                          tenant__isnull=False)
                  .values_list("tenant_id", flat=True))
    covering = {t.pk for t in leases_for_period(period_first)}
    rows = []
    for pi in had:
        t = pi.tenant
        if t.pk in now_ids or t.pk in covering:
            continue
        if not t.tenant_physical_invoice_required:
            why = "no longer flagged for physical invoicing"
        elif not (t.tenant_lease_start_date and t.tenant_lease_end_date):
            why = "lease dates are blank"
        elif t.tenant_lease_end_date < period_first:
            why = f"lease ended {t.tenant_lease_end_date:%d %b %Y}"
        else:
            why = "no lease covering the period"
        rows.append({
            "tenant": t.tenant_name,
            "property": getattr(t.prop, "prop_name", "") or "",
            "why": why,
        })
    return sorted(rows, key=lambda r: r["tenant"])


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
        part = not covers_whole_period(pi.tenant, period_first) if (
            pi.tenant.tenant_lease_start_date
            and pi.tenant.tenant_lease_end_date) else False
        rows.append({
            "number": provisional.get(pi.pk, ""),
            "tenant": pi.tenant.tenant_name,
            "property": getattr(pi.tenant.prop, "prop_name", "") or "",
            "total": pi.total,
            "pk": pi.pk,
            # Derived from the lease term, not stored - no migration.
            "part_month": part,
            "term": ("%s to %s" % (
                pi.tenant.tenant_lease_start_date.strftime("%d %b %Y"),
                pi.tenant.tenant_lease_end_date.strftime("%d %b %Y")))
            if part else "",
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
        created, existing, reseeded = ensure_month_drafts(
            period_first, vat_rate)
        self.stdout.write(self.style.SUCCESS(
            f"{period_first:%B %Y}: {len(created)} draft(s) created, {len(existing)} already present."))
        for _pi, _ch in reseeded:
            self.stdout.write(self.style.WARNING(
                f"  re-seeded {_pi.tenant.tenant_name}: {', '.join(_ch)}"))

        if not opts["no_email"]:
            self._send_review_reminder(period_first)

    def _send_review_reminder(self, period_first):
        rows = reminder_rows(period_first)
        gaps = period_gaps(period_first)
        # A GAP IS NEWS EVEN WHEN THERE IS NOTHING TO APPROVE. This used
        # to return the moment there were no drafts, which is exactly
        # the state a lapsed lease produces - so the one month the
        # reminder mattered most was the one month it stayed silent.
        if not rows and not gaps:
            self.stdout.write("No drafts awaiting approval; no reminder sent.")
            return
        month_label = period_first.strftime("%B %Y")
        count = len(rows)
        invoice_word = "invoice" if count == 1 else "invoices"
        is_are = "is" if count == 1 else "are"
        needs = "needs" if count == 1 else "need"
        them = "it" if count == 1 else "them"
        gap_note = f" + {len(gaps)} with no lease" if gaps else ""
        subject = (f"Physical invoices to approve \u2014 {month_label} "
                   f"({count} pending{gap_note})")

        def _part(r):
            # Derived from the lease term - a full month is unremarkable
            # and says nothing, a part month says so and shows the term.
            return (f" <b>[part month: {r['term']}]</b>"
                    if r.get("part_month") else "")

        html_items = "".join(
            f"<li><b>{r['number']}</b> — {r['tenant']} ({r['property']}) "
            f"— €{r['total']:,.2f}{_part(r)}</li>"
            for r in rows)
        text_items = "".join(
            f"\n \u2022 {r['number']}  {r['tenant']} ({r['property']})  "
            f"€{r['total']:,.2f}"
            + (f"  [part month: {r['term']}]" if r.get("part_month") else "")
            for r in rows)
        html_gaps = "".join(
            f"<li><b>{g['tenant']}</b> ({g['property']}) — {g['why']}</li>"
            for g in gaps)
        text_gaps = "".join(
            f"\n \u2022 {g['tenant']} ({g['property']})  {g['why']}"
            for g in gaps)
        gap_html = (
            "<br><p><b><u class=\"header\">NO INVOICE THIS MONTH "
            f"({len(gaps)}):</u></b></p>"
            "<p>These were invoiced last month and have no lease covering "
            f"{month_label}. Nothing has been raised for them:</p>"
            f"<ul>{html_gaps}</ul>") if gaps else ""
        gap_text = (
            f"\n\nNO INVOICE THIS MONTH ({len(gaps)}):\n"
            "These were invoiced last month and have no lease covering "
            f"{month_label}. Nothing has been raised for them:{text_gaps}"
        ) if gaps else ""

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
            {gap_html}
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
            f"{text_items}"
            f"{gap_text}\n\n"
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