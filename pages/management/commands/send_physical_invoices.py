# -*- coding: utf-8 -*-
"""
Send approved physical (VAT) invoices to clients.

Runs DAILY. For the open period (the current calendar month, or --month), it:

  1. Numbers every APPROVED-but-unnumbered invoice A->Z (tenant name), gap-free,
     advancing the PR counter. Invoices already numbered on a prior run (e.g. a
     failed-email retry) keep their number -- they are NOT re-numbered.
  2. For each APPROVED (not yet sent) invoice: renders the stored PDF, saves it
     to pdf_file, e-mails it to the tenant (TO = tenant_email,
     CC = the 'physical_invoice_client' recipient card), and -- only on a
     successful send -- marks it sent.
  3. Self-heals the collection link: for every APPROVED or SENT invoice in the
     period whose collection_invoice is still null, finds that month's
     collection invoice, sets its invoice_amount = pi.total, and links it. This
     back-fills links for invoices sent on a previous run without re-sending.

Client e-mail (step 2)
----------------------
* Subject is derived from the period:  "<Month Year> - Rental Invoice".
* Body = the per-tenant client_email_body saved on the PhysicalInvoiceProfile,
  with the one token {month} replaced by "<Month Year>" (e.g. "June 2026").
  A tenant with no saved body gets a generic default so they are still invoiced.
* The fixed signature/contact footer lives in this file (FOOTER_TEXT /
  _footer_html) -- one place to change it.
* Sent as HTML + plain-text (multipart/alternative). The Alivente logo is
  embedded inline via Content-ID if LOGO_PATH resolves to a file; if not, the
  e-mail still sends, just without the logo.
* MIME shape:  mixed -> [ related -> [ alternative -> [plain, html], logo ],
                          pdf attachment ].

Design notes
------------
* Number-on-send, in approval order (decision 5a): an invoice approved later
  gets the next number on the day it is processed, so the sequence is gap-free
  and ascending but follows approval order, not a strict whole-month A->Z.
* mark_sent ONLY on a successful e-mail (decision 4). A failed send leaves the
  invoice approved (and numbered) so the next daily run retries the send with no
  re-numbering.
* Collection-row CREATION stays owned by the daily collection cron
  (check_lease_renewal_and_invoices). This cron only ever UPDATES/links a row.
* E-mail uses raw smtplib via the EMAIL_* env vars, matching
  email_utils.send_issue_comments_email -- NOT Django's mail backend.

Schedule it daily, after the collection cron, on the same Railway cadence as
check_lease_renewal_and_invoices.
"""

import os
import re
import smtplib
import ssl
from datetime import date
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.html import escape
from django.utils.text import slugify

from pages.email_utils import get_email_recipients
from pages.models import PhysicalInvoiceNumbering, invoices as Invoices
from pages.services.physical_invoice_numbering import month_batch, suggested_next_number


def _tenant_batch(year, month, statuses=None):
    """month_batch filtered to TENANT invoices only. Customer (non-tenant)
    invoices are sent on demand, never by this monthly cron."""
    return [pi for pi in month_batch(year, month, statuses=statuses)
            if pi.tenant_id is not None]
from pages.services.invoice_email import (
    LOGO_PATH, assemble_bodies, load_logo, send_invoice_email,
)
from pages.views.physical_invoices import (
    build_context_from_invoice,
    render_physical_invoice_pdf,
)

CLIENT_NOTIFICATION_TYPE = "physical_invoice_client"


class Command(BaseCommand):
    help = "Send approved physical (VAT) invoices for the open period to clients (daily)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month", dest="month", default=None,
            help="Target period as YYYY-MM (defaults to the current month).",
        )
        parser.add_argument(
            "--no-email", action="store_true", dest="no_email",
            help="Do everything except actually send e-mail (still renders, "
                 "numbers, stores the PDF, and links the collection invoice).",
        )
        parser.add_argument(
            "--dry-run", action="store_true", dest="dry_run",
            help="Report what would happen; write nothing, send nothing.",
        )

    # ------------------------------------------------------------------ #
    # period helpers
    # ------------------------------------------------------------------ #
    def _target_period(self, month_arg):
        if month_arg:
            y, m = month_arg.split("-")
            return int(y), int(m)
        today = timezone.localdate()
        return today.year, today.month

    # ------------------------------------------------------------------ #
    # numbering: number approved+unnumbered only, A->Z, advance counter
    # ------------------------------------------------------------------ #
    def _number_unnumbered_approved(self, year, month, dry_run):
        cfg = PhysicalInvoiceNumbering.get_solo()
        approved = _tenant_batch(year, month, statuses=("approved",))  # A->Z, then tenant_id
        to_number = [pi for pi in approved if not pi.invoice_number]
        if not to_number:
            return []
        n = suggested_next_number(cfg)
        assigned = []
        for pi in to_number:
            number = cfg.format(n)
            assigned.append((pi, number))
            if not dry_run:
                pi.invoice_number = number
                pi.save(update_fields=["invoice_number", "updated_at"])
            n += 1
        if not dry_run:
            cfg.next_number = n
            cfg.save(update_fields=["next_number", "updated_at"])
        return assigned

    # ------------------------------------------------------------------ #
    # collection-invoice link (self-healing, never creates a row)
    # ------------------------------------------------------------------ #
    def _find_collection_invoice(self, tenant, year, month):
        return (Invoices.objects
                .filter(tenant=tenant,
                        invoice_date__year=year,
                        invoice_date__month=month)
                .order_by("invoice_id")
                .first())

    def _link_collection(self, pi, year, month, dry_run):
        """Set the month's collection invoice amount = pi.total and link it.
        Returns one of: 'linked', 'already', 'missing'."""
        if pi.collection_invoice_id:
            return "already"
        ci = self._find_collection_invoice(pi.tenant, year, month)
        if ci is None:
            return "missing"
        if not dry_run:
            ci.invoice_amount = pi.total
            ci.save(update_fields=["invoice_amount"])
            pi.collection_invoice = ci
            pi.save(update_fields=["collection_invoice", "updated_at"])
        return "linked"

    # ------------------------------------------------------------------ #
    # PDF render + store
    # ------------------------------------------------------------------ #
    def _render_and_store_pdf(self, pi, dry_run):
        context = build_context_from_invoice(pi)
        pdf_bytes = render_physical_invoice_pdf(context)
        if not dry_run:
            base = slugify(pi.invoice_number or f"draft-{pi.pk}")
            pi.pdf_file.save(f"{base}.pdf", ContentFile(pdf_bytes), save=True)
        return pdf_bytes

    # ------------------------------------------------------------------ #
    # client e-mail body assembly
    # ------------------------------------------------------------------ #
    def _saved_body_for(self, tenant):
        """The per-tenant client_email_body from the PhysicalInvoiceProfile,
        or '' if there is no profile / no saved text."""
        try:
            return (tenant.physical_invoice_profile.client_email_body or "").strip()
        except ObjectDoesNotExist:
            return ""

    def _assemble_bodies(self, saved_body, tenant_name, period_label, include_logo):
        """Resolve the per-tenant core (token + generic default), then delegate
        to the shared assembler for footer + HTML wrap."""
        saved_body = (saved_body or "").strip()
        if saved_body:
            core = saved_body.replace("{month}", period_label)
        else:
            core = (f"Dear {tenant_name},\n\n"
                    f"Please find attached the rental invoice for {period_label}.")
        return assemble_bodies(core, include_logo)

    # ------------------------------------------------------------------ #
    # handle
    # ------------------------------------------------------------------ #
    def handle(self, *args, **options):
        no_email = options["no_email"]
        dry_run = options["dry_run"]
        year, month = self._target_period(options["month"])
        period_label = date(year, month, 1).strftime("%B %Y")

        self.stdout.write(
            f"Send physical invoices for {period_label}"
            f"{'  [DRY-RUN]' if dry_run else ''}"
            f"{'  [NO-EMAIL]' if no_email else ''}"
        )

        # 1) Number approved+unnumbered (A->Z), gap-free, retry-safe.
        assigned = self._number_unnumbered_approved(year, month, dry_run)
        for pi, number in assigned:
            self.stdout.write(f"  numbered {number}  {pi.tenant}")

        # CC list for the client e-mail (TO is per-tenant, handled below).
        try:
            cc_list = get_email_recipients(CLIENT_NOTIFICATION_TYPE).get("cc", []) or []
        except Exception as exc:  # never let recipient lookup abort the run
            cc_list = []
            self.stderr.write(f"  warning: could not load CC recipients: {exc}")

        # Inline logo, loaded once for the whole run.
        logo_bytes = load_logo()
        if logo_bytes is None:
            self.stderr.write(
                f"  note: signature logo not found at {LOGO_PATH}; "
                f"e-mails will send without it."
            )

        # 2) Send approved-not-sent invoices (A->Z within the period).
        approved = _tenant_batch(year, month, statuses=("approved",))
        sent_count = failed_count = 0
        for pi in approved:
            tenant = pi.tenant
            # tenant_email is a free-text field that may hold several addresses
            # (separated by "and", commas, spaces, etc.). Pull out every email so
            # the invoice reaches all recipients recorded on the tenant.
            raw_email = getattr(tenant, "tenant_email", "") or ""
            to_list = re.findall(r"[^\s,;<>()]+@[^\s,;<>()]+\.[^\s,;<>()]+", raw_email)
            to_display = ", ".join(to_list)

            try:
                pdf_bytes = self._render_and_store_pdf(pi, dry_run)
            except Exception as exc:
                failed_count += 1
                self.stderr.write(f"  ERROR rendering {pi.invoice_number} ({tenant}): {exc}")
                continue

            if not to_list:
                failed_count += 1
                self.stderr.write(
                    f"  SKIP {pi.invoice_number} ({tenant}): no valid email in "
                    f"tenant_email; stays approved for retry."
                )
                continue

            subject = f"{period_label} - Rental Invoice"
            tenant_name = getattr(tenant, "tenant_name", "") or ""
            text_body, html_body = self._assemble_bodies(
                self._saved_body_for(tenant), tenant_name, period_label,
                include_logo=logo_bytes is not None,
            )
            filename = (f"{pi.invoice_number} - {tenant_name} - "
                        f"({year:04d}-{month:02d}-01).pdf")

            if dry_run or no_email:
                self.stdout.write(
                    f"  would send {pi.invoice_number} -> {to_display}"
                    f"{' (+cc ' + ', '.join(cc_list) + ')' if cc_list else ''}"
                )
                # In no-email mode we still link the collection invoice below,
                # but we do NOT mark the invoice sent.
            else:
                try:
                    send_invoice_email(to_list[0], to_list[1:] + cc_list, subject,
                                       text_body, html_body, pdf_bytes, filename,
                                       logo_bytes)
                except Exception as exc:
                    failed_count += 1
                    if hasattr(pi, "email_status"):
                        pi.email_status = "failed"
                        pi.save(update_fields=["email_status", "updated_at"])
                    self.stderr.write(
                        f"  ERROR emailing {pi.invoice_number} ({to_display}): {exc}; "
                        f"stays approved for retry."
                    )
                    continue
                if hasattr(pi, "email_status"):
                    pi.email_status = "sent"
                pi.mark_sent()
                sent_count += 1
                self.stdout.write(f"  sent {pi.invoice_number} -> {to_display}")

            # Link the collection invoice for this freshly-handled invoice.
            status = self._link_collection(pi, year, month, dry_run)
            if status == "missing":
                self.stderr.write(
                    f"  warning: {pi.invoice_number} ({tenant}) sent but no "
                    f"{period_label} collection invoice found to link "
                    f"(will back-fill on a later run)."
                )

        # 3) Back-fill links for already-SENT invoices still unlinked (no re-send).
        backfilled = 0
        for pi in _tenant_batch(year, month, statuses=("sent",)):
            if pi.collection_invoice_id:
                continue
            if self._link_collection(pi, year, month, dry_run) == "linked":
                backfilled += 1
                self.stdout.write(f"  back-filled link for {pi.invoice_number}  {pi.tenant}")

        self.stdout.write(
            f"Done: {sent_count} sent, {failed_count} failed/skipped, "
            f"{backfilled} link(s) back-filled."
        )