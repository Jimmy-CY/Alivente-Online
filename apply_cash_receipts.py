#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Cash Receipts - issue a numbered receipt, render it, store it, list it.

WHAT THIS ADDS. A receipt acknowledging that a payment was received: date,
amount, description, who paid, how. It gets a number from its own running
counter starting at CR-00372, a PDF on the Alivente letterhead, and a place
in a list with the newest on top.

WHAT IT DELIBERATELY REUSES. Nothing here is invented that the system already
has. The letterhead, the xhtml2pdf renderer and the static-file resolution all
come from `views/physical_invoices.py`; the numbering service is the same
shape as `services/physical_invoice_numbering.py`; the list screen is on the
table standard and the PDF is stored the way `PhysicalInvoice.pdf_file` is
stored. COMPANY defined twice would be two documents claiming different VAT
numbers, and nobody would notice until a tenant did.

DECIDED, 28 Aug:
  * Made out to a tenant or invoice customer, or to free text. The name and
    address are SNAPSHOTTED at issue - editing a tenant next year must not
    rewrite a receipt handed over last year.
  * No VAT. A receipt acknowledges money received; the VAT sits on the invoice.
  * Void, never delete. A voided receipt keeps its number and its row, so the
    sequence has no gap nobody can account for, and its stored PDF is
    re-rendered to say VOID on its face.
  * Its own item under Financial Management, beneath Invoices. In the CODE it
    sits beside Physical Invoices; menu placement and code placement are
    different questions.
  * Duplicate PRE-FILLS the form. It does not create a draft, and it does not
    carry a number - so nothing is written and no number is consumed until
    Issue is pressed.
  * Electronic or Printed is chosen once, at issue. Electronic omits the
    signature block and says the receipt is valid without one; Printed carries
    ruled lines instead and drops that sentence, because a page that says both
    contradicts itself.

A RECEIPT IS A DOCUMENT, NOT A POSTING. Issuing one changes no balances and
marks no invoice paid.

AFTER RUNNING THIS you must generate the migration - this patcher deliberately
does NOT hand-write one:

    python manage.py makemigrations pages
    python manage.py migrate

Django writes migrations that match its own expectations about field order,
dependencies and db_table. A hand-written one that looks right is a very
efficient way to break a deploy.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
URLS   = os.path.join(ROOT, 'pages', 'urls.py')
VINIT  = os.path.join(ROOT, 'pages', 'views', '__init__.py')
BASE   = os.path.join(TPL, 'base.html')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_receipts'

NEW_FILES = [
    (os.path.join(ROOT, 'pages', 'services', 'cash_receipt_numbering.py'), 'NUMBERING_PY'),
    (os.path.join(ROOT, 'pages', 'views', 'receipts.py'), 'VIEWS_PY'),
    (os.path.join(TPL, 'receipts', 'cash_receipt.html'), 'PDF_HTML'),
    (os.path.join(TPL, 'cash_receipts.html'), 'LIST_HTML'),
    (os.path.join(TPL, 'cash_receipt_add.html'), 'ADD_HTML'),
    (os.path.join(ROOT, 'pages', 'permissions.py'), 'PERMISSIONS_PY'),
]

USERS  = os.path.join(ROOT, 'pages', 'views', 'users.py')
VSETUP = os.path.join(ROOT, 'pages', 'views_setup.py')


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:110]))


MODELS_BLOCK = r'''

# ============================================================================
# CASH RECEIPTS
# ============================================================================
def cash_receipt_pdf_upload_path(instance, filename):
    """Storage path for a rendered cash-receipt PDF.

    Named by the receipt NUMBER first, because that is what somebody looking
    for a file will know. The payer's name follows it for readability only.
    """
    ext = (filename.rsplit('.', 1)[-1] or 'pdf').lower()
    number = slugify(instance.receipt_number or 'unnumbered')
    who = slugify(instance.payer_name or 'receipt')
    return os.path.join('cash_receipts', f"{number}-{who}.{ext}")


class CashReceiptNumbering(models.Model):
    """Singleton: the running counter for cash-receipt (CR) numbers.

    Deliberately a separate counter from PhysicalInvoiceNumbering. Receipts and
    invoices are different documents with different sequences; sharing one
    counter would interleave them and make either sequence unexplainable.

    Seeded at 372 so the first receipt the system issues is CR-00372, carrying
    on from the book that was in use before it.
    """
    prefix = models.CharField(max_length=10, default="CR-")
    pad_width = models.PositiveSmallIntegerField(default=5,
        help_text="Zero-padding width (5 -> CR-00372).")
    next_number = models.PositiveIntegerField(default=372,
        help_text="The next CR number the system will issue.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cash_receipt_numbering"
        verbose_name = "Cash Receipt Numbering"
        verbose_name_plural = "Cash Receipt Numbering"

    def __str__(self):
        return f"Receipt numbering — next {self.format(self.next_number)}"

    def format(self, n):
        return f"{self.prefix}{int(n):0{self.pad_width}d}"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()


class CashReceipt(models.Model):
    """A numbered receipt acknowledging that a payment was received.

    A DOCUMENT, NOT A POSTING. Issuing a receipt changes no balances and marks
    no invoice paid; it records that money arrived. `reference` may name the
    invoice it settles, as free text, without binding the two together.

    The payer's name and contact are SNAPSHOTTED at issue - `payer_name`,
    `payer_address`, `payer_tel` - exactly as PhysicalInvoice freezes its
    bill_* fields. Editing a tenant next year must not rewrite a receipt that
    was handed over last year. The FKs are kept alongside so the receipt can
    still be listed under that tenant, but they are never read back onto the
    document.

    Void, never delete. A voided receipt keeps its number and stays in the
    list, so the sequence has no gap that nobody can account for.
    """

    FORMAT_ELECTRONIC = 'electronic'
    FORMAT_PRINTED = 'printed'
    FORMAT_CHOICES = [
        (FORMAT_ELECTRONIC, 'Electronic'),
        (FORMAT_PRINTED, 'Printed'),
    ]

    METHOD_CASH = 'cash'
    METHOD_TRANSFER = 'transfer'
    METHOD_CHEQUE = 'cheque'
    METHOD_CARD = 'card'
    METHOD_OTHER = 'other'
    METHOD_CHOICES = [
        (METHOD_CASH, 'Cash'),
        (METHOD_TRANSFER, 'Bank Transfer'),
        (METHOD_CHEQUE, 'Cheque'),
        (METHOD_CARD, 'Card'),
        (METHOD_OTHER, 'Other'),
    ]

    cash_receipt_id = models.AutoField(primary_key=True)

    # unique=True is the last line of defence on the number. The counter and
    # the reconciliation in services/cash_receipt_numbering.py should make a
    # duplicate impossible; this makes the database refuse one anyway.
    receipt_number = models.CharField(max_length=32, unique=True,
        help_text='CR-##### — assigned when the receipt is issued.')
    receipt_date = models.DateField(help_text='The date the money was received.')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    description = models.TextField(help_text='What the payment was for.')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES,
                              default=METHOD_TRANSFER)
    reference = models.CharField(max_length=64, blank=True,
        help_text='Optional — e.g. the invoice this settles. May be left blank.')
    doc_format = models.CharField(max_length=20, choices=FORMAT_CHOICES,
        default=FORMAT_ELECTRONIC,
        help_text='Electronic omits the signature block and states the '
                  'receipt is valid without one. Printed carries the ruled '
                  'lines instead. Chosen once, at issue.')

    # Who paid, as links (for finding receipts later) ...
    tenant = models.ForeignKey(tenant, on_delete=models.PROTECT, null=True,
                               blank=True, related_name='cash_receipts')
    customer = models.ForeignKey('InvoiceCustomer', on_delete=models.PROTECT,
                                 null=True, blank=True,
                                 related_name='cash_receipts')
    prop = models.ForeignKey(props, on_delete=models.PROTECT, null=True,
                             blank=True, related_name='cash_receipts')

    # ... and as a frozen snapshot (what the document says).
    payer_name = models.CharField(max_length=255)
    payer_address = models.TextField(blank=True,
        help_text='One line per row. Optional — a receipt is valid without it.')
    payer_tel = models.CharField(max_length=64, blank=True)
    payer_email = models.TextField(blank=True,
        help_text='Comma-separated addresses used when the receipt is emailed.')

    pdf_file = models.FileField(upload_to=cash_receipt_pdf_upload_path,
                                blank=True, null=True)

    is_void = models.BooleanField(default=False)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  blank=True, related_name='voided_cash_receipts')
    void_reason = models.CharField(max_length=255, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name='issued_cash_receipts')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cash_receipts"
        verbose_name = "Cash Receipt"
        verbose_name_plural = "Cash Receipts"
        # Newest on top, which is how the list is asked to read. The id is the
        # tie-break so two receipts dated the same day keep a stable order
        # rather than swapping places between page loads.
        ordering = ['-receipt_date', '-cash_receipt_id']

    def __str__(self):
        return f"{self.receipt_number} — {self.payer_name}"

    @property
    def address_lines(self):
        return [l.strip() for l in (self.payer_address or '').splitlines()
                if l.strip()]
'''

NUMBERING_PY = r'''"""Cash-receipt (CR) number assignment.

One running counter (CashReceiptNumbering). The suggested next number is the
counter, reconciled against the highest number already issued so the sequence
can never go backwards.

WHY BOTH. The counter alone can be wrong - restored from a backup, edited by
hand, or advanced by a transaction that later rolled back. The highest issued
alone cannot survive the whole book being voided, and reading every row to
issue one receipt is the wrong shape. `max(counter, highest + 1)` is right
whichever of the two has drifted.

A VOIDED RECEIPT STILL COUNTS. `highest_issued_number` deliberately does not
filter out voided rows: a voided number has been used and must never be
handed out again. That is the whole reason voiding is not deleting.

Deliberately a separate counter from the invoice one. Receipts and invoices
are different sequences; sharing a counter would interleave them.
"""
import re

from django.db import transaction

from pages.models import CashReceipt, CashReceiptNumbering

_TRAILING_NUM = re.compile(r"(\d+)\s*$")


def _numeric_part(receipt_number, prefix):
    if not receipt_number:
        return None
    s = receipt_number.strip()
    if prefix and s.startswith(prefix):
        s = s[len(prefix):]
    m = _TRAILING_NUM.search(s)
    return int(m.group(1)) if m else None


def highest_issued_number(settings=None):
    settings = settings or CashReceiptNumbering.get_solo()
    highest = 0
    for num in (CashReceipt.objects
                .exclude(receipt_number__isnull=True)
                .exclude(receipt_number="")
                .values_list("receipt_number", flat=True)):
        n = _numeric_part(num, settings.prefix)
        if n and n > highest:
            highest = n
    return highest


def suggested_next_number(settings=None):
    settings = settings or CashReceiptNumbering.get_solo()
    return max(settings.next_number, highest_issued_number(settings) + 1)


def preview_next(settings=None):
    """The formatted number the next receipt WOULD get. For display only.

    Never write this to a record. Two people with the issue form open would
    both be shown CR-00372; only `assign_next` decides which of them gets it.
    """
    settings = settings or CashReceiptNumbering.get_solo()
    return settings.format(suggested_next_number(settings))


def assign_next():
    """Take the next number and advance the counter, atomically.

    `select_for_update` on the singleton is what makes two simultaneous issues
    safe: the second waits for the first to commit, then reads the advanced
    counter. Without it both read 372 and the unique index on receipt_number
    rejects the loser - correct, but as a 500 rather than as a queue.

    Must be called inside a transaction, alongside the row it numbers, so a
    failure to save the receipt cannot leave the counter advanced past a
    number nothing ever used.
    """
    settings = (CashReceiptNumbering.objects.select_for_update().first()
                or CashReceiptNumbering.objects.create())
    n = suggested_next_number(settings)
    number = settings.format(n)
    settings.next_number = n + 1
    settings.save(update_fields=["next_number", "updated_at"])
    return number
'''

VIEWS_PY = r'''"""Cash receipts.

Issue a numbered receipt for a payment, render it to PDF on the Alivente
letterhead, store the PDF on the record, and list what has been issued.

WHAT IS DELIBERATELY REUSED. The letterhead, the PDF engine and the static
resolution all come from `physical_invoices` rather than being written again.
COMPANY in two places is the contradiction pattern - two documents claiming
different VAT numbers, and nobody noticing until a tenant does.

Functions
---------
- cash_receipt_list    : the issued receipts, newest first.
- cash_receipt_add     : the issue form; ?duplicate=<id> pre-fills from an
                         existing receipt WITHOUT copying its number or PDF.
- cash_receipt_commit  : assign the number, save, render and store the PDF -
                         all inside one transaction.
- cash_receipt_void    : mark void; the number is kept.
- cash_receipt_pdf     : serve the stored PDF.

Auth tiers
----------
read tier -> auth.can_access_receipts  (list, pdf)
edit tier -> auth.can_edit_receipts    (add, commit, void)

Its OWN tier, not the invoices one: issuing a receipt for cash received is a
different duty from raising and chasing an invoice, and the two are grantable
apart. The codenames are defined in pages/permissions.py and come into
existence the first time a superuser opens any user's permissions screen.
"""
import io
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from xhtml2pdf import pisa

from pages.models import CashReceipt, InvoiceCustomer, props
from pages.models import tenant as Tenant
from pages.services.cash_receipt_numbering import assign_next, preview_next

# The letterhead and the PDF plumbing, borrowed rather than duplicated. These
# are private names in that module; importing them is deliberate and is why
# this comment exists. If they are ever made public, drop the underscores here
# and nothing else changes.
from .physical_invoices import COMPANY, LOGO_STATIC_PATH, _link_callback, _resolve_logo

__all__ = [
    "cash_receipt_list",
    "cash_receipt_add",
    "cash_receipt_commit",
    "cash_receipt_void",
    "cash_receipt_pdf",
    "render_cash_receipt_pdf",
    "amount_in_words",
]

TEMPLATE_NAME = "receipts/cash_receipt.html"


# --------------------------------------------------------------------- words
_ONES = ('', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
         'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen',
         'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen')
_TENS = ('', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy',
         'Eighty', 'Ninety')


def _under_thousand(n):
    if n < 20:
        return _ONES[n]
    if n < 100:
        return (_TENS[n // 10] + ('-' + _ONES[n % 10] if n % 10 else '')).strip()
    return (_ONES[n // 100] + ' Hundred'
            + (' and ' + _under_thousand(n % 100) if n % 100 else ''))


def amount_in_words(amount, currency='Euro', minor='Cent'):
    """`One Thousand Two Hundred and Fifty Euro and 00 Cents`.

    The words are the guard against a mistyped or altered figure - the same
    reason a cheque carries them - and they matter more on a receipt than on
    an invoice, because the receipt is the payer's proof.
    """
    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        return ''
    negative = amount < 0
    amount = abs(amount)
    whole = int(amount)
    cents = int((amount - whole) * 100)
    parts, rest = [], whole
    for value, name in ((1000000000, 'Billion'), (1000000, 'Million'),
                        (1000, 'Thousand'), (1, '')):
        if rest >= value:
            count, rest = divmod(rest, value)
            parts.append((_under_thousand(count) + ' ' + name).strip())
    words = ' '.join(parts) if parts else 'Zero'
    out = '%s %s and %02d %ss' % (words, currency, cents, minor)
    return ('Minus ' + out) if negative else out


def _money(value):
    return f"{float(value):,.2f}"


def _company_context():
    return {**COMPANY, "logo_path": _resolve_logo(LOGO_STATIC_PATH)}


# ----------------------------------------------------------------------- pdf
def build_receipt_context(receipt):
    return {
        "company": _company_context(),
        "currency_symbol": "€" if (receipt.currency or "EUR") == "EUR" else "",
        "payer": {
            "name": receipt.payer_name,
            "address_lines": receipt.address_lines,
            "tel": receipt.payer_tel,
            # One flag rather than two tests in the template: an address block
            # that is present but empty still takes vertical space.
            "has_contact": bool(receipt.address_lines or receipt.payer_tel),
        },
        "receipt": {
            "number": receipt.receipt_number,
            "date_display": receipt.receipt_date.strftime("%d.%m.%Y"),
            "amount_display": _money(receipt.amount),
            "amount_words": amount_in_words(receipt.amount),
            "description": receipt.description,
            "method_display": receipt.get_method_display(),
            "property_name": getattr(receipt.prop, "prop_name", "") if receipt.prop_id else "",
            "reference": receipt.reference,
            "is_void": receipt.is_void,
            "is_printed": receipt.doc_format == CashReceipt.FORMAT_PRINTED,
            "is_electronic": receipt.doc_format == CashReceipt.FORMAT_ELECTRONIC,
        },
    }


def render_cash_receipt_pdf(context):
    """Render the receipt template + context to PDF bytes via xhtml2pdf."""
    html = render_to_string(TEMPLATE_NAME, context)
    buffer = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8",
                            link_callback=_link_callback)
    if result.err:
        raise RuntimeError("xhtml2pdf failed to render the cash receipt")
    return buffer.getvalue()


# ---------------------------------------------------------------------- list
@login_required
@permission_required('auth.can_access_receipts', raise_exception=True)
def cash_receipt_list(request):
    """Issued receipts, newest first.

    The rows are built here rather than in the template - the same reasoning
    as Open Invoices. A template that decides its own rows cannot tell you
    whether it drew any, so it cannot have an empty state.
    """
    qs = (CashReceipt.objects
          .select_related('tenant', 'customer', 'prop')
          .order_by('-receipt_date', '-cash_receipt_id'))

    rows = []
    for r in qs:
        rows.append({
            'pk': r.pk,
            'number': r.receipt_number,
            'date': r.receipt_date,
            'payer': r.payer_name,
            'description': r.description,
            'amount': r.amount,
            'currency': r.currency,
            'method_display': r.get_method_display(),
            'format_display': r.get_doc_format_display(),
            'is_void': r.is_void,
            'status_pill': 'alv-pill-neutral' if r.is_void else 'alv-pill-good',
            'status_display': 'Void' if r.is_void else 'Issued',
            'has_pdf': bool(r.pdf_file),
        })

    total = sum((r['amount'] for r in rows if not r['is_void']), Decimal('0.00'))

    return render(request, "cash_receipts.html", {
        "rows": rows,
        "receipt_total": total,
        "next_number": preview_next(),
    })


# ----------------------------------------------------------------------- add
def _payer_choices():
    return {
        "tenants": Tenant.objects.all().order_by('tenant_name'),
        "customers": InvoiceCustomer.objects.all().order_by('name'),
        "properties": props.objects.all().order_by('prop_country', 'prop_name'),
    }


@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
def cash_receipt_add(request):
    """The issue form.

    `?duplicate=<id>` pre-fills from an existing receipt. It copies the
    CONTENT - payer, description, amount, method, format - and deliberately
    not the number, the PDF or the void state, and it dates the new one
    today. Nothing is written and no number is consumed until Issue is
    pressed, which is why duplicating does not need a draft record.
    """
    prefill = {
        "receipt_date": date.today().isoformat(),
        "method": CashReceipt.METHOD_TRANSFER,
        "doc_format": CashReceipt.FORMAT_ELECTRONIC,
        "currency": "EUR",
    }
    source = None
    dup = (request.GET.get('duplicate') or '').strip()
    if dup.isdigit():
        source = CashReceipt.objects.filter(pk=int(dup)).first()
    if source:
        prefill.update({
            "payer_name": source.payer_name,
            "payer_address": source.payer_address,
            "payer_tel": source.payer_tel,
            "payer_email": source.payer_email,
            "tenant_id": source.tenant_id,
            "customer_id": source.customer_id,
            "prop_id": source.prop_id,
            "amount": source.amount,
            "description": source.description,
            "method": source.method,
            "doc_format": source.doc_format,
            "currency": source.currency,
            # reference is NOT copied: it names the invoice the ORIGINAL
            # settled, and carrying it over would attach this receipt to a
            # payment it has nothing to do with.
        })

    ctx = {"prefill": prefill, "next_number": preview_next(),
           "duplicated_from": source.receipt_number if source else ""}
    ctx.update(_payer_choices())
    return render(request, "cash_receipt_add.html", ctx)


def _decimal_or_none(raw):
    try:
        value = Decimal((raw or '').replace(',', '').strip())
    except (InvalidOperation, AttributeError):
        return None
    return value


@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
@require_POST
def cash_receipt_commit(request):
    """Issue the receipt: number, record and PDF, in ONE transaction.

    The number is taken here and nowhere else. Assigning it when the form
    opens would show CR-00372 to two people at once; assigning it after the
    save would leave a receipt with no number if the render failed.
    """
    payer_name = (request.POST.get('payer_name') or '').strip()
    amount = _decimal_or_none(request.POST.get('amount'))
    description = (request.POST.get('description') or '').strip()
    raw_date = (request.POST.get('receipt_date') or '').strip()

    errors = []
    if not payer_name:
        errors.append("Received from — who paid? This is what the receipt is made out to.")
    if amount is None or amount <= 0:
        errors.append("Amount — enter the sum received.")
    if not description:
        errors.append("Being payment for — say what the payment was for.")
    try:
        receipt_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        errors.append("Date — enter the date the money was received.")
        receipt_date = None
    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('cash_receipt_add')

    def _fk(model, raw):
        raw = (raw or '').strip()
        return model.objects.filter(pk=raw).first() if raw.isdigit() else None

    method = request.POST.get('method') or CashReceipt.METHOD_TRANSFER
    if method not in dict(CashReceipt.METHOD_CHOICES):
        method = CashReceipt.METHOD_OTHER
    doc_format = request.POST.get('doc_format') or CashReceipt.FORMAT_ELECTRONIC
    if doc_format not in dict(CashReceipt.FORMAT_CHOICES):
        doc_format = CashReceipt.FORMAT_ELECTRONIC

    with transaction.atomic():
        receipt = CashReceipt(
            receipt_number=assign_next(),
            receipt_date=receipt_date,
            amount=amount,
            currency=(request.POST.get('currency') or 'EUR').strip()[:3] or 'EUR',
            description=description,
            method=method,
            reference=(request.POST.get('reference') or '').strip(),
            doc_format=doc_format,
            tenant=_fk(Tenant, request.POST.get('tenant_id')),
            customer=_fk(InvoiceCustomer, request.POST.get('customer_id')),
            prop=_fk(props, request.POST.get('prop_id')),
            payer_name=payer_name,
            payer_address=(request.POST.get('payer_address') or '').strip(),
            payer_tel=(request.POST.get('payer_tel') or '').strip(),
            payer_email=(request.POST.get('payer_email') or '').strip(),
            created_by=request.user if request.user.is_authenticated else None,
        )
        receipt.save()
        # The PDF is stored, not re-rendered on demand. A receipt is a document
        # somebody was handed; re-rendering it next year through a changed
        # template would produce a different one under the same number.
        pdf_bytes = render_cash_receipt_pdf(build_receipt_context(receipt))
        receipt.pdf_file.save(f"{receipt.receipt_number}.pdf",
                              ContentFile(pdf_bytes), save=True)

    messages.info(request, f"Receipt {receipt.receipt_number} issued.")
    return redirect('cash_receipt_list')


# ---------------------------------------------------------------------- void
@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
@require_POST
def cash_receipt_void(request, cash_receipt_id):
    """Void a receipt. The number is kept and the row stays in the list.

    The PDF is re-rendered so that the stored copy says VOID on its face. The
    copy already in somebody's inbox cannot be recalled, but the one in the
    system should never go on looking valid.
    """
    receipt = get_object_or_404(CashReceipt, pk=cash_receipt_id)
    if receipt.is_void:
        messages.warning(request, f"{receipt.receipt_number} was already void.")
        return redirect('cash_receipt_list')

    with transaction.atomic():
        receipt.is_void = True
        receipt.voided_at = timezone.now()
        receipt.voided_by = request.user if request.user.is_authenticated else None
        receipt.void_reason = (request.POST.get('void_reason') or '').strip()[:255]
        receipt.save(update_fields=['is_void', 'voided_at', 'voided_by',
                                    'void_reason', 'updated_at'])
        pdf_bytes = render_cash_receipt_pdf(build_receipt_context(receipt))
        receipt.pdf_file.save(f"{receipt.receipt_number}-void.pdf",
                              ContentFile(pdf_bytes), save=True)

    messages.info(request, f"Receipt {receipt.receipt_number} voided. "
                           "Its number is kept, so the sequence has no gap.")
    return redirect('cash_receipt_list')


# ----------------------------------------------------------------------- pdf
@login_required
@permission_required('auth.can_access_receipts', raise_exception=True)
def cash_receipt_pdf(request, cash_receipt_id):
    """Serve the STORED PDF. Falls back to rendering only if none was saved."""
    receipt = get_object_or_404(CashReceipt, pk=cash_receipt_id)
    if receipt.pdf_file:
        receipt.pdf_file.open('rb')
        try:
            data = receipt.pdf_file.read()
        finally:
            receipt.pdf_file.close()
    else:
        data = render_cash_receipt_pdf(build_receipt_context(receipt))
    response = HttpResponse(data, content_type="application/pdf")
    disposition = 'attachment' if request.GET.get('download') else 'inline'
    response["Content-Disposition"] = (
        f'{disposition}; filename="{receipt.receipt_number}.pdf"')
    return response
'''

PDF_HTML = r'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    /* Deliberately the same visual language as invoices/physical_invoice.html:
       A4, Helvetica 9pt, the #2f5496 band, the raised centred logo, the
       bordered meta box top-right. A receipt and an invoice are a matched
       pair and should look like they came from the same desk. What differs is
       what a receipt IS: one amount, already paid, no line items, no VAT. */
    @page {
        size: a4 portrait;
        margin: 1.3cm 1.3cm 1.1cm 1.3cm;
    }
    body {
        font-family: Helvetica;
        font-size: 9pt;
        color: #1a1a1a;
        line-height: 1.3;
    }
    .company-name { font-size: 16pt; color: #2f5496; font-weight: bold; }
    .doc-title { font-size: 18pt; color: #2f5496; font-weight: bold; text-align: right; }
    .muted { color: #555555; }
    .link  { color: #2f5496; }

    table.layout { width: 100%; }
    table.layout td { vertical-align: top; }

    .band {
        background-color: #2f5496;
        color: #ffffff;
        font-weight: bold;
        padding: 4pt 7pt;
        font-size: 10pt;
    }

    table.meta { border-collapse: collapse; }
    table.meta td { border: 0.75pt solid #2f5496; padding: 2pt 5pt; font-size: 8.5pt; }
    table.meta td.k { font-weight: bold; }

    table.detail { width: 100%; border-collapse: collapse; margin-top: 3pt; }
    table.detail td {
        font-size: 9pt;
        padding: 6pt 7pt;
        border: 0.5pt solid #c9c9c9;
    }
    table.detail td.k { font-weight: bold; width: 26%; background-color: #f4f6fb; }

    /* The amount is the whole point of the document, so it is the only thing
       on the page allowed to be large. */
    .amount-box {
        background-color: #eaeef7;
        border: 0.75pt solid #2f5496;
        padding: 9pt 12pt;
    }
    .amount-label { font-size: 9pt; font-weight: bold; color: #2f5496; }
    .amount-value { font-size: 20pt; font-weight: bold; color: #2f5496; text-align: right; }
    .amount-words { font-size: 8.5pt; color: #555555; }

    table.sign { width: 100%; margin-top: 30pt; }
    table.sign td { font-size: 8.5pt; vertical-align: bottom; }
    .sign-rule { border-bottom: 0.5pt solid #1a1a1a; height: 30pt; }

    .footer-bar { background-color: #2f5496; height: 9pt; }

    /* A voided receipt keeps its number and stays in the list, so its PDF has
       to say so on its face - otherwise the copy in somebody's inbox goes on
       looking valid forever. */
    .void-stamp {
        color: #b3261e;
        border: 2pt solid #b3261e;
        font-size: 30pt;
        font-weight: bold;
        text-align: center;
        padding: 6pt;
        letter-spacing: 6pt;
    }
</style>
</head>
<body>

    <!-- ===================== LOGO (raised, centred) ===================== -->
    {% if company.logo_path %}
    <div style="position: absolute; top: -22pt; left: 0; width: 100%; text-align: center;">
        <img src="{{ company.logo_path }}" style="width: 118pt;">
    </div>
    {% endif %}

    <!-- ===================== HEADER ===================== -->
    <table class="layout">
        <tr>
            <td width="34%">
                <div class="company-name">{{ company.name }}</div>
                <div class="muted">VAT Number: {{ company.vat_number }}</div>
                <div style="height: 7pt;"></div>
                <div>{% for line in company.address_lines %}{{ line }}<br>{% endfor %}Phone: {{ company.phone }}<br><span class="link">{{ company.website }}</span></div>
            </td>
            <td width="32%">&nbsp;</td>
            <td width="34%">
                <div class="doc-title">RECEIPT</div>
                <table class="meta" width="100%" style="margin-top: 8pt;">
                    <tr><td class="k" width="46%">Date</td><td>{{ receipt.date_display }}</td></tr>
                    <tr><td class="k">Receipt #</td><td>{{ receipt.number }}</td></tr>
                    {% if receipt.reference %}<tr><td class="k">Reference</td><td>{{ receipt.reference }}</td></tr>{% endif %}
                </table>
            </td>
        </tr>
    </table>

    {% if receipt.is_void %}
    <div style="height: 10pt;"></div>
    <div class="void-stamp">VOID</div>
    {% endif %}

    <!-- ===================== RECEIVED FROM ===================== -->
    <div style="height: 9pt;"></div>
    <div class="band">RECEIVED FROM</div>
    <div style="padding: 6pt 2pt 2pt 2pt;">
        <div style="font-weight: bold;">{{ payer.name }}</div>
        {% if payer.has_contact %}<div style="padding-top: 3pt;">{% for line in payer.address_lines %}{{ line }}<br>{% endfor %}{% if payer.tel %}Tel: {{ payer.tel }}{% endif %}</div>{% endif %}
    </div>

    <!-- ===================== THE AMOUNT ===================== -->
    <div style="height: 9pt;"></div>
    <table class="layout amount-box">
        <tr>
            <td width="52%">
                <div class="amount-label">AMOUNT RECEIVED</div>
                <div class="amount-words">{{ receipt.amount_words }}</div>
            </td>
            <td width="48%">
                <div class="amount-value">{{ currency_symbol }} {{ receipt.amount_display }}</div>
            </td>
        </tr>
    </table>

    <!-- ===================== DETAIL ===================== -->
    <div style="height: 9pt;"></div>
    <div class="band">DETAILS</div>
    <table class="detail">
        <tr>
            <td class="k">Being payment for</td>
            <td>{{ receipt.description }}</td>
        </tr>
        <tr>
            <td class="k">Method of payment</td>
            <td>{{ receipt.method_display }}</td>
        </tr>
        {% if receipt.property_name %}
        <tr>
            <td class="k">Property</td>
            <td>{{ receipt.property_name }}</td>
        </tr>
        {% endif %}
    </table>

    <!-- ===================== ACKNOWLEDGEMENT ===================== -->
    <div style="font-size: 9.5pt; padding-top: 16pt;">
        Received with thanks from <strong>{{ payer.name }}</strong> the sum of
        <strong>{{ currency_symbol }} {{ receipt.amount_display }}</strong>
        on {{ receipt.date_display }}.
    </div>

    {% if receipt.is_printed %}
    <table class="sign">
        <tr>
            <td width="46%">
                <div class="sign-rule">&nbsp;</div>
                <div class="muted">For and on behalf of {{ company.name }}</div>
            </td>
            <td width="8%">&nbsp;</td>
            <td width="46%">
                <div class="sign-rule">&nbsp;</div>
                <div class="muted">Date</div>
            </td>
        </tr>
    </table>
    <div class="muted" style="font-size: 8pt; padding-top: 22pt;">
        Receipt number {{ receipt.number }}.
    </div>
    {% endif %}
    {% if receipt.is_electronic %}
    <div class="muted" style="font-size: 8pt; padding-top: 26pt;">
        This receipt is issued electronically by {{ company.name }} and is valid without signature.
        Receipt number {{ receipt.number }}.
    </div>
    {% endif %}

    <div class="footer-bar" style="margin-top: 10pt;">&nbsp;</div>

</body>
</html>
'''

LIST_HTML = r'''{% extends 'base.html' %}
{% load static %}
{% load humanize %}
{% load help_modal_tags %}

{% block title %}
Receipts
{% endblock %}

{% block content %}

<h2 class="page-title-h2"><center>ALIVENTE ONLINE - RECEIPTS</center></h2>
<br/>

{% for msg in messages %}
  <div class="alert alert-secondary alert-dismissible fade show auto-dismiss" role="alert">
    <strong></strong> <center>{{ msg }}</center>
    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
      <span aria-hidden="true">&times;</span>
    </button>
  </div>
  <script>
    setTimeout(function() {
      document.querySelectorAll('.auto-dismiss').forEach(alert => {
        alert.classList.remove('show');
        alert.classList.add('fade');
        setTimeout(() => alert.remove(), 500);
      });
    }, 2500);
  </script>
{% endfor %}

  <div class="page-action-buttons">
    {% if perms.auth.can_edit_receipts %}
      <a href="{% url 'cash_receipt_add' %}" class="btn action-primary action-add-new">
        <i class="fas fa-plus"></i> Issue Receipt
      </a>
    {% else %}
      <span class="btn action-primary disabled-btn action-add-new"
            title="You do not have permission to issue receipts">
        <i class="fas fa-plus"></i> Issue Receipt
      </span>
    {% endif %}
    <a href="{% url 'home' %}" class="btn action-back" aria-label="Back to home">
      <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
  </div>

  <div class="rec-next">Next receipt number: <strong>{{ next_number }}</strong></div>

  <div class="table-container">
    <table class="table alv-table receipts-table">
      <thead>
        <tr>
          <th style="width: 12%">Receipt #</th>
          <th style="width: 11%">Date</th>
          <th style="text-align: left; width: 22%">Received From</th>
          <th style="text-align: left; width: 25%">Being Payment For</th>
          <th class="num" style="width: 12%">Amount</th>
          <th style="width: 9%">Status</th>
          <th class="desktop-action-cell cell-actions" style="width: 9%">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for row in rows %}
          <tr{% if row.is_void %} class="rec-void"{% endif %}>
            <td data-label="Receipt #" class="ref">{{ row.number }}</td>
            <td data-label="Date">{{ row.date|date:"Y-m-d" }}</td>
            <td data-label="Received From" style="text-align: left">{{ row.payer }}</td>
            <td data-label="Being Payment For" style="text-align: left">{{ row.description }}</td>
            <td data-label="Amount" class="num">&euro; {{ row.amount|floatformat:2|intcomma }}</td>
            <td data-label="Status">
              <span class="alv-pill {{ row.status_pill }}">{{ row.status_display }}</span>
            </td>
            <td data-label="Actions" class="desktop-action-cell cell-actions">
              <div class="row-actions">
                <a href="{% url 'cash_receipt_pdf' row.pk %}" target="_blank"
                   class="icon-action-btn icon-view" title="View receipt">
                  <i class="fas fa-file-pdf"></i>
                </a>
                {% if perms.auth.can_edit_receipts %}
                  <a href="{% url 'cash_receipt_add' %}?duplicate={{ row.pk }}"
                     class="icon-action-btn icon-duplicate"
                     title="Issue a new receipt with these details">
                    <i class="fas fa-copy"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No permission to issue receipts">
                    <i class="fas fa-copy"></i>
                  </span>
                {% endif %}
                {% if row.is_void %}
                  <span class="icon-action-btn icon-disabled" title="Already void">
                    <i class="fas fa-ban"></i>
                  </span>
                {% elif perms.auth.can_edit_receipts %}
                  <form method="post" action="{% url 'cash_receipt_void' row.pk %}"
                        class="rec-inline-form"
                        onsubmit="return confirm('Void receipt {{ row.number }}?\n\nIt keeps its number and stays in the list, marked VOID. This cannot be undone.');">
                    {% csrf_token %}
                    <button type="submit" class="icon-action-btn icon-delete" title="Void this receipt">
                      <i class="fas fa-ban"></i>
                    </button>
                  </form>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No permission to void">
                    <i class="fas fa-ban"></i>
                  </span>
                {% endif %}
              </div>
            </td>

            <!-- Mobile-only action bar -->
            <td class="mobile-action-bar{% if row.is_void %} cols-2{% endif %}">
              <a href="{% url 'cash_receipt_pdf' row.pk %}" target="_blank" class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View</span>
              </a>
              {% if perms.auth.can_edit_receipts %}
                <a href="{% url 'cash_receipt_add' %}?duplicate={{ row.pk }}" class="mobile-action-btn">
                  <i class="fas fa-copy mobile-action-icon icon-color-edit"></i>
                  <span class="mobile-action-label">Duplicate</span>
                </a>
              {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                  <i class="fas fa-copy mobile-action-icon"></i>
                  <span class="mobile-action-label">Duplicate</span>
                </span>
              {% endif %}
              {% if not row.is_void and perms.auth.can_edit_receipts %}
                <form method="post" action="{% url 'cash_receipt_void' row.pk %}"
                      class="rec-inline-form-mobile"
                      onsubmit="return confirm('Void receipt {{ row.number }}?\n\nIt keeps its number and stays in the list, marked VOID. This cannot be undone.');">
                  {% csrf_token %}
                  <button type="submit" class="mobile-action-btn">
                    <i class="fas fa-ban mobile-action-icon icon-color-delete"></i>
                    <span class="mobile-action-label">Void</span>
                  </button>
                </form>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
      </tbody>
      {% if rows %}
      <tfoot>
        <tr>
          <td class="cell-totals-label" colspan="4">TOTAL ISSUED</td>
          <td class="num" data-label="Total issued">&euro; {{ receipt_total|floatformat:2|intcomma }}</td>
          <td></td>
          <td></td>
        </tr>
      </tfoot>
      {% endif %}
    </table>

    {% if not rows %}
      {# An empty tbody looks exactly like a failed load. #}
      <div class="alv-empty">
        <i class="fas fa-receipt"></i>
        <div class="alv-empty-title">No receipts issued yet</div>
        <div class="alv-empty-hint">
          The first one will be {{ next_number }}.
        </div>
      </div>
    {% endif %}
  </div>

{% render_help_modal "cash_receipts" %}

<style>
.rec-next {
    color: var(--alv-ink-soft);
    font-size: 13px;
    margin-bottom: 8px;
}

/* An inline <form> is how a POST icon button is written on every page that
   has one. It must not become a layout box of its own. */
.rec-inline-form { display: inline; margin: 0; }

/* A voided receipt stays in the list on purpose - the number must not vanish.
   It reads as past tense rather than as an error: the row is quiet, not red.
   Only the strike on the number says what happened, because a whole grey row
   is easy to mistake for a disabled control. */
.receipts-table tbody tr.rec-void td { color: var(--alv-ink-faint); }
.receipts-table tbody tr.rec-void td.ref { text-decoration: line-through; }

/* The total is not a record, so it is not in the tbody. base styles rows;
   this styles the summary of them. */
.receipts-table tfoot td {
    background: var(--alv-surface);
    border-top: 2px solid var(--alv-line);
    font-weight: 700;
    padding: 11px 12px;
    vertical-align: middle;
}
.receipts-table tfoot .cell-totals-label {
    text-align: right;
    color: var(--alv-ink-soft);
    text-transform: uppercase;
    letter-spacing: .04em;
    font-size: 12.5px;
}

@media (max-width: 768px) {
    .rec-inline-form-mobile { display: flex; margin: 0; }
    .rec-inline-form-mobile .mobile-action-btn { width: 100%; }

    /* base turns tbody rows into cards; a tfoot is not a tbody, so the totals
       card is built here. */
    .receipts-table tfoot,
    .receipts-table tfoot tr,
    .receipts-table tfoot td { display: block; width: 100%; }
    .receipts-table tfoot tr {
        background: var(--alv-surface);
        border: 1px solid var(--alv-accent-line);
        border-radius: var(--alv-radius);
        padding: 12px;
        margin-bottom: 12px;
    }
    .receipts-table tfoot td {
        border: 0;
        padding: 6px 0;
        display: flex;
        justify-content: space-between;
        gap: 8px;
    }
    .receipts-table tfoot td:empty { display: none; }
    .receipts-table tfoot td::before {
        content: attr(data-label);
        font-weight: 600;
        color: var(--alv-ink-soft);
        font-size: 12.5px;
    }
    .receipts-table tfoot .cell-totals-label {
        display: block;
        text-align: left;
        color: var(--alv-accent-ink);
    }
    .receipts-table tfoot .cell-totals-label::before { content: none; }
}
</style>

{% endblock %}
'''

ADD_HTML = r'''{% extends 'base.html' %}
{% load static %}

{% block title %}
Issue Receipt
{% endblock %}

{% block content %}

<h2 class="page-title-h2"><center>ALIVENTE ONLINE - RECEIPTS</center></h2>
<h4 class="page-subtitle-h4"><center>ISSUE RECEIPT</center></h4>
<br/>

{% for msg in messages %}
  <div class="alert alert-secondary alert-dismissible fade show auto-dismiss" role="alert">
    <strong></strong> <center>{{ msg }}</center>
    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
      <span aria-hidden="true">&times;</span>
    </button>
  </div>
{% endfor %}

<div class="page-action-buttons">
  <button type="submit" form="receiptForm" class="btn action-primary">
    <i class="fas fa-check"></i> Issue Receipt
  </button>
  <a href="{% url 'cash_receipt_list' %}" class="btn action-back" title="Back to receipts">
    <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
  </a>
</div>

{% if duplicated_from %}
  <div class="rec-note">
    <i class="fas fa-copy"></i>
    Copied from <strong>{{ duplicated_from }}</strong>, dated today. It becomes a
    new receipt with its own number when you issue it — nothing has been saved yet.
  </div>
{% endif %}

<form action="{% url 'cash_receipt_commit' %}" method="post" id="receiptForm">
  {% csrf_token %}

  <div class="alv-card">
    <div class="alv-card-head">
      <span class="alv-card-title">The payment</span>
      <span class="alv-card-aside rec-number">Will be issued as {{ next_number }}</span>
    </div>
    <div class="alv-card-body">
      <div class="form-row">
        <div class="form-group col-md-3 col-sm-6">
          <label for="receipt_date"><strong>Date received</strong></label>
          <input type="date" class="form-control" id="receipt_date" name="receipt_date"
                 value="{{ prefill.receipt_date }}" required>
        </div>
        <div class="form-group col-md-3 col-sm-6">
          <label for="amount"><strong>Amount</strong></label>
          <div class="input-group">
            <div class="input-group-prepend"><span class="input-group-text">&euro;</span></div>
            <input type="number" class="form-control text-right" id="amount" name="amount"
                   step="0.01" min="0.01" placeholder="0.00"
                   value="{{ prefill.amount|default_if_none:'' }}" required>
          </div>
        </div>
        <div class="form-group col-md-3 col-sm-6">
          <label for="method"><strong>Method of payment</strong></label>
          <select class="form-control" id="method" name="method">
            <option value="transfer" {% if prefill.method == 'transfer' %}selected{% endif %}>Bank Transfer</option>
            <option value="cash"     {% if prefill.method == 'cash' %}selected{% endif %}>Cash</option>
            <option value="cheque"   {% if prefill.method == 'cheque' %}selected{% endif %}>Cheque</option>
            <option value="card"     {% if prefill.method == 'card' %}selected{% endif %}>Card</option>
            <option value="other"    {% if prefill.method == 'other' %}selected{% endif %}>Other</option>
          </select>
        </div>
        <div class="form-group col-md-3 col-sm-6">
          <label for="reference"><strong>Reference</strong> <span class="rec-optional">optional</span></label>
          <input type="text" class="form-control" id="reference" name="reference"
                 placeholder="e.g. PR-0169" value="{{ prefill.reference|default_if_none:'' }}">
        </div>
      </div>

      <div class="form-row">
        <div class="form-group col-12">
          <label for="description"><strong>Being payment for</strong></label>
          <input type="text" class="form-control" id="description" name="description"
                 placeholder="e.g. Rent for August 2026 — Eleftheroupoleos 6, Flat 16"
                 value="{{ prefill.description|default_if_none:'' }}" required>
        </div>
      </div>
    </div>
  </div>

  <div class="alv-card">
    <div class="alv-card-head">
      <span class="alv-card-title">Received from</span>
    </div>
    <div class="alv-card-body">
      <div class="form-row">
        <div class="form-group col-md-6 col-sm-12">
          <label for="payerPicker"><strong>Pick a tenant or customer</strong>
            <span class="rec-optional">or just type a name below</span></label>
          <select class="form-control" id="payerPicker">
            <option value="">— someone else —</option>
            <optgroup label="Tenants">
              {% for t in tenants %}
                <option value="tenant:{{ t.tenant_id }}"
                        data-name="{{ t.tenant_name }}"
                        data-tel="{{ t.tenant_contact_number|default_if_none:'' }}"
                        data-email="{{ t.tenant_email|default_if_none:'' }}"
                        {% if prefill.tenant_id == t.tenant_id %}selected{% endif %}>{{ t.tenant_name }}</option>
              {% endfor %}
            </optgroup>
            <optgroup label="Invoice customers">
              {% for c in customers %}
                <option value="customer:{{ c.pk }}"
                        data-name="{{ c.name }}"
                        data-address="{{ c.billing_address }}"
                        data-tel="{{ c.billing_tel }}"
                        data-email="{{ c.email_to }}"
                        {% if prefill.customer_id == c.pk %}selected{% endif %}>{{ c.name }}</option>
              {% endfor %}
            </optgroup>
          </select>
          <input type="hidden" name="tenant_id" id="tenantId" value="{{ prefill.tenant_id|default_if_none:'' }}">
          <input type="hidden" name="customer_id" id="customerId" value="{{ prefill.customer_id|default_if_none:'' }}">
        </div>
        <div class="form-group col-md-6 col-sm-12">
          <label for="payer_name"><strong>Name on the receipt</strong></label>
          <input type="text" class="form-control" id="payer_name" name="payer_name"
                 value="{{ prefill.payer_name|default_if_none:'' }}" required>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group col-md-6 col-sm-12">
          <label for="payer_address"><strong>Address</strong> <span class="rec-optional">optional, one line per row</span></label>
          <textarea class="form-control" id="payer_address" name="payer_address"
                    rows="3">{{ prefill.payer_address|default_if_none:'' }}</textarea>
        </div>
        <div class="form-group col-md-3 col-sm-6">
          <label for="payer_tel"><strong>Telephone</strong> <span class="rec-optional">optional</span></label>
          <input type="text" class="form-control" id="payer_tel" name="payer_tel"
                 value="{{ prefill.payer_tel|default_if_none:'' }}">
        </div>
        <div class="form-group col-md-3 col-sm-6">
          <label for="payer_email"><strong>Email</strong> <span class="rec-optional">optional</span></label>
          <input type="text" class="form-control" id="payer_email" name="payer_email"
                 value="{{ prefill.payer_email|default_if_none:'' }}">
        </div>
      </div>

      <div class="form-row">
        <div class="form-group col-md-6 col-sm-12">
          <label for="prop_id"><strong>Property</strong> <span class="rec-optional">optional</span></label>
          <select class="form-control" id="prop_id" name="prop_id">
            <option value="">— none —</option>
            {% for p in properties %}
              <option value="{{ p.prop_id }}" {% if prefill.prop_id == p.prop_id %}selected{% endif %}>{{ p.prop_name }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="form-group col-md-6 col-sm-12">
          <label><strong>Receipt format</strong></label>
          <div class="rec-format">
            <label class="rec-radio">
              <input type="radio" name="doc_format" value="electronic"
                     {% if prefill.doc_format != 'printed' %}checked{% endif %}>
              <span><strong>Electronic</strong> — no signature block; states it is
                    valid without one. For emailing or sharing.</span>
            </label>
            <label class="rec-radio">
              <input type="radio" name="doc_format" value="printed"
                     {% if prefill.doc_format == 'printed' %}checked{% endif %}>
              <span><strong>Printed</strong> — carries ruled signature and date
                    lines instead. For handing over on paper.</span>
            </label>
          </div>
          <div class="rec-hint">
            Chosen once. The PDF is stored on the receipt as it is issued, so this
            decides what the stored document looks like.
          </div>
        </div>
      </div>
    </div>
  </div>
</form>

<style>
.page-subtitle-h4 { margin-bottom: 0; }

.rec-note {
    background: var(--alv-accent-soft);
    border: 1px solid var(--alv-accent-line);
    border-radius: var(--alv-radius);
    color: var(--alv-accent-ink);
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 13.5px;
}
.rec-number { color: var(--alv-ink-soft); font-weight: 600; font-size: 12.5px; }
.rec-optional {
    color: var(--alv-ink-faint);
    font-weight: 400;
    font-size: 12px;
    text-transform: none;
    letter-spacing: 0;
}
.rec-hint { color: var(--alv-ink-soft); font-size: 12.5px; margin-top: 6px; }

.rec-format { display: flex; flex-direction: column; gap: 8px; padding-top: 4px; }
.rec-radio {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-weight: 400;
    font-size: 13px;
    margin: 0;
    cursor: pointer;
}
.rec-radio input { margin-top: 3px; flex: 0 0 auto; }
</style>

<script>
document.addEventListener('DOMContentLoaded', function () {
    // Picking a tenant or customer FILLS the fields; it does not lock them.
    // The name on the receipt is whatever is in the box when Issue is
    // pressed, which is what lets a receipt be made out to somebody the
    // system has never heard of.
    var picker = document.getElementById('payerPicker');
    if (!picker) return;
    var name = document.getElementById('payer_name');
    var addr = document.getElementById('payer_address');
    var tel = document.getElementById('payer_tel');
    var email = document.getElementById('payer_email');
    var tenantId = document.getElementById('tenantId');
    var customerId = document.getElementById('customerId');

    picker.addEventListener('change', function () {
        var opt = picker.options[picker.selectedIndex];
        var value = picker.value || '';
        tenantId.value = '';
        customerId.value = '';
        if (value.indexOf('tenant:') === 0) {
            tenantId.value = value.split(':')[1];
        } else if (value.indexOf('customer:') === 0) {
            customerId.value = value.split(':')[1];
        }
        if (!value) { return; }
        name.value = opt.getAttribute('data-name') || '';
        addr.value = opt.getAttribute('data-address') || '';
        tel.value = opt.getAttribute('data-tel') || '';
        email.value = opt.getAttribute('data-email') || '';
    });
});
</script>

{% endblock %}
'''

PERMISSIONS_PY = r'''"""The module permission list - ONE definition, two consumers.

WHY THIS FILE EXISTS. The same list was written twice: `all_permissions` in
`views/users.py`, which drives the User Administration screen and creates the
Permission rows, and `permissions_data` in `views_setup.py`, which seeds a
fresh environment. They had drifted. views_setup was missing
`can_access_administration`, `can_access_passports`, `can_access_recipes`,
`can_access_celebrations` and `can_access_crs`, and it carried **no
`can_edit_*` codenames at all** - so a rebuilt environment came up with about
half the permissions the system actually checks, and the missing half only
showed up as a 403 on a screen somebody could reach yesterday.

Both now read this. A new module is added HERE, once, and both the admin
screen and the seeder gain it together.

`edit_codename` is None for a module that has no edit tier - Dashboard and
Administration are look-at-it screens.
"""

MODULE_PERMISSIONS = [
    {'codename': 'can_access_properties',     'edit_codename': 'can_edit_properties',     'label': 'Properties',            'icon': 'fa-building'},
    {'codename': 'can_access_tenants',        'edit_codename': 'can_edit_tenants',        'label': 'Tenants',               'icon': 'fa-users'},
    {'codename': 'can_access_suppliers',      'edit_codename': 'can_edit_suppliers',      'label': 'Suppliers',             'icon': 'fa-truck'},
    {'codename': 'can_access_expenses',       'edit_codename': 'can_edit_expenses',       'label': 'Expenses',              'icon': 'fa-receipt'},
    {'codename': 'can_access_petty_cash',     'edit_codename': 'can_edit_petty_cash',     'label': 'Petty Cash',            'icon': 'fa-coins'},
    {'codename': 'can_access_financials',     'edit_codename': 'can_edit_financials',     'label': 'Financials',            'icon': 'fa-chart-line'},
    {'codename': 'can_access_invoices',       'edit_codename': 'can_edit_invoices',       'label': 'Invoices',              'icon': 'fa-file-invoice'},
    # Receipts is its OWN module, not a corner of Invoices: issuing a receipt
    # for cash received is a different duty from raising and chasing an
    # invoice, and the two should be grantable apart.
    {'codename': 'can_access_receipts',       'edit_codename': 'can_edit_receipts',       'label': 'Receipts',              'icon': 'fa-receipt'},
    {'codename': 'can_access_projects',       'edit_codename': 'can_edit_projects',       'label': 'Projects',              'icon': 'fa-project-diagram'},
    {'codename': 'can_access_issues',         'edit_codename': 'can_edit_issues',         'label': 'Issues',                'icon': 'fa-exclamation-circle'},
    {'codename': 'can_access_dashboard',      'edit_codename': None,                      'label': 'Dashboard',             'icon': 'fa-tachometer-alt'},
    {'codename': 'can_access_administration', 'edit_codename': None,                      'label': 'Administration',        'icon': 'fa-cogs'},
    {'codename': 'can_access_passports',      'edit_codename': 'can_edit_passports',      'label': 'Passports / Documents', 'icon': 'fa-passport'},
    {'codename': 'can_access_recipes',        'edit_codename': 'can_edit_recipes',        'label': 'Recipes',               'icon': 'fa-utensils'},
    {'codename': 'can_access_celebrations',   'edit_codename': 'can_edit_celebrations',   'label': 'Celebrations',          'icon': 'fa-birthday-cake'},
    {'codename': 'can_access_crs',            'edit_codename': 'can_edit_crs',            'label': 'CRS Reporting',         'icon': 'fa-landmark'},
]

# `can_access_fsr` is checked in the Issues module and granted to the Property
# Managers group, but it is not a row on the User Administration screen. It is
# listed here so the seeder still creates it, and named separately so nobody
# adds it to the screen by accident.
EXTRA_PERMISSIONS = [
    ('can_access_fsr', 'Can access FSR module'),
]


def all_codenames():
    """Every codename the system expects to exist, access and edit tiers both."""
    out = []
    for m in MODULE_PERMISSIONS:
        out.append((m['codename'], "Can access %s" % m['label']))
        if m['edit_codename']:
            out.append((m['edit_codename'], "Can edit %s" % m['label']))
    out.extend(EXTRA_PERMISSIONS)
    return out
'''


# ------------------------------------------------------------------ anchors
URL_ANCHOR = ('    path("physical-invoices/<int:physical_invoice_id>/delete/", '
              'views.physical_invoice_delete, name="physical_invoice_delete"),')

URL_BLOCK = """
    # ============================================================================
    # CASH RECEIPTS
    # ============================================================================
    path("receipts/", views.cash_receipt_list, name="cash_receipt_list"),
    path("receipts/new/", views.cash_receipt_add, name="cash_receipt_add"),
    path("receipts/issue/", views.cash_receipt_commit, name="cash_receipt_commit"),
    path("receipts/<int:cash_receipt_id>/void/", views.cash_receipt_void, name="cash_receipt_void"),
    path("receipts/<int:cash_receipt_id>/pdf/", views.cash_receipt_pdf, name="cash_receipt_pdf"),"""

VINIT_ANCHOR = 'from .invoices import *  # noqa: F401, F403'
VINIT_ADD = ('from .invoices import *  # noqa: F401, F403\n'
             'from .receipts import *  # noqa: F401, F403')

# The navbar dropdown. Receipts sits directly beneath Invoices, which is where
# somebody looking for it will look.
NAV_ANCHOR = ('                {% if user.is_superuser or perms.auth.can_access_invoices %}'
              '<a class="dropdown-item" href="{% url \'invoices\' %}">Invoices</a>{% endif %}')
NAV_ADD = (NAV_ANCHOR + '\n'
           '                {% if user.is_superuser or perms.auth.can_access_receipts %}'
           '<a class="dropdown-item" href="{% url \'cash_receipt_list\' %}">Receipts</a>{% endif %}')

# ... and the sidebar, which is a separate menu that must not be forgotten:
# a page reachable from one and not the other is a page half the users cannot
# find, depending on a preference they set months ago.
SIDE_ANCHOR = """          {% if user.is_superuser or perms.auth.can_access_invoices %}
          <a href="{% url 'invoices' %}" class="sidebar-link {% if request.resolver_match.url_name == 'invoices' %}active{% endif %}" data-tooltip="Invoices">
              <i class="fas fa-file-invoice"></i><span class="link-text">Invoices</span>
          </a>
          {% endif %}"""
SIDE_ADD = SIDE_ANCHOR + """
          {% if user.is_superuser or perms.auth.can_access_receipts %}
          <a href="{% url 'cash_receipt_list' %}" class="sidebar-link {% if request.resolver_match.url_name == 'cash_receipt_list' %}active{% endif %}" data-tooltip="Receipts">
              <i class="fas fa-receipt"></i><span class="link-text">Receipts</span>
          </a>
          {% endif %}"""

USERS_ANCHOR = r"""    all_permissions = [
        {'codename': 'can_access_properties',     'edit_codename': 'can_edit_properties', 'label': 'Properties',       'icon': 'fa-building'},
        {'codename': 'can_access_tenants',        'edit_codename': 'can_edit_tenants',    'label': 'Tenants',          'icon': 'fa-users'},
        {'codename': 'can_access_suppliers',      'edit_codename': 'can_edit_suppliers',  'label': 'Suppliers',        'icon': 'fa-truck'},
        {'codename': 'can_access_expenses',       'edit_codename': 'can_edit_expenses',   'label': 'Expenses',         'icon': 'fa-receipt'},
        {'codename': 'can_access_petty_cash',     'edit_codename': 'can_edit_petty_cash', 'label': 'Petty Cash',       'icon': 'fa-coins'},
        {'codename': 'can_access_financials',     'edit_codename': 'can_edit_financials', 'label': 'Financials',       'icon': 'fa-chart-line'},
        {'codename': 'can_access_invoices',       'edit_codename': 'can_edit_invoices',   'label': 'Invoices',         'icon': 'fa-file-invoice'},
        {'codename': 'can_access_projects',       'edit_codename': 'can_edit_projects',   'label': 'Projects',         'icon': 'fa-project-diagram'},
        {'codename': 'can_access_issues',         'edit_codename': 'can_edit_issues',     'label': 'Issues',           'icon': 'fa-exclamation-circle'},
        {'codename': 'can_access_dashboard',      'edit_codename': None,                  'label': 'Dashboard',        'icon': 'fa-tachometer-alt'},
        {'codename': 'can_access_administration', 'edit_codename': None,                  'label': 'Administration',   'icon': 'fa-cogs'},
        {'codename': 'can_access_passports',      'edit_codename': 'can_edit_passports',      'label': 'Passports / Documents', 'icon': 'fa-passport'},
        {'codename': 'can_access_recipes',        'edit_codename': 'can_edit_recipes',        'label': 'Recipes',               'icon': 'fa-utensils'},
        {'codename': 'can_access_celebrations',   'edit_codename': 'can_edit_celebrations',   'label': 'Celebrations',          'icon': 'fa-birthday-cake'},
        {'codename': 'can_access_crs',            'edit_codename': 'can_edit_crs',            'label': 'CRS Reporting',         'icon': 'fa-landmark'},

        ]
"""

USERS_REPLACEMENT = """    # ONE definition, in pages/permissions.py. This list and the seeder's copy
    # in views_setup.py had drifted five modules and an entire tier apart.
    all_permissions = MODULE_PERMISSIONS"""

USERS_IMPORT_ANCHOR = 'from django.contrib.contenttypes.models import ContentType'
USERS_IMPORT_ADD = ('from django.contrib.contenttypes.models import ContentType\n'
                    'from pages.permissions import MODULE_PERMISSIONS')

SETUP_ANCHOR = r"""        permissions_data = [
            ('can_access_properties', 'Can access Properties module'),
            ('can_access_tenants', 'Can access Tenants module'),
            ('can_access_suppliers', 'Can access Suppliers module'),
            ('can_access_expenses', 'Can access Expenses module'),
            ('can_access_petty_cash', 'Can access Petty Cash module'),
            ('can_access_financials', 'Can access Financials module'),
            ('can_access_invoices', 'Can access Invoices module'),
            ('can_access_projects', 'Can access Projects module'),
            ('can_access_issues', 'Can access Issues module'),
            ('can_access_dashboard', 'Can access Dashboard module'),
            ('can_access_fsr', 'Can access FSR module'),
        ]"""

SETUP_REPLACEMENT = """        # ONE definition, in pages/permissions.py. This list used to be
        # maintained separately from the User Administration screen's and had
        # fallen five modules behind it - and it carried no can_edit_* at all,
        # so a rebuilt environment came up missing half the permissions the
        # system checks.
        permissions_data = all_codenames()"""

SETUP_IMPORT_ANCHOR = 'from django.contrib.auth.decorators import user_passes_test'
SETUP_IMPORT_ADD = ('from django.contrib.auth.decorators import user_passes_test\n'
                    'from pages.permissions import all_codenames')


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and os.path.exists(p):
        shutil.copy2(p, b)


def main():
    msrc, usrc, vsrc, bsrc = read(MODELS), read(URLS), read(VINIT), read(BASE)
    pusrc, pssrc = read(USERS), read(VSETUP)

    already = ('class CashReceipt(' in msrc
               and 'cash_receipt_list' in usrc
               and 'from .receipts import *' in vsrc
               and 'MODULE_PERMISSIONS' in pusrc)
    if already:
        print('  cash receipts               already installed')
        print('\n  0 file(s) changed')
        return

    # ---- models: appended, never inserted. models.py ends with signal
    # handlers and appending keeps this block whole and findable.
    if 'class CashReceipt(' in msrc:
        mout = msrc
    else:
        mout = msrc.rstrip('\n') + '\n' + MODELS_BLOCK

    # ---- urls
    if 'cash_receipt_list' in usrc:
        uout = usrc
    else:
        one(usrc, URL_ANCHOR, 'the invoices url block')
        uout = usrc.replace(URL_ANCHOR, URL_ANCHOR + '\n' + URL_BLOCK, 1)

    # ---- views package aggregator
    if 'from .receipts import *' in vsrc:
        vout = vsrc
    else:
        one(vsrc, VINIT_ANCHOR, 'the views aggregator')
        vout = vsrc.replace(VINIT_ANCHOR, VINIT_ADD, 1)

    # ---- both menus
    bout = bsrc
    menus = 0
    if 'cash_receipt_list' not in bout:
        one(bout, NAV_ANCHOR, 'the navbar Invoices item')
        bout = bout.replace(NAV_ANCHOR, NAV_ADD, 1); menus += 1
        one(bout, SIDE_ANCHOR, 'the sidebar Invoices link')
        bout = bout.replace(SIDE_ANCHOR, SIDE_ADD, 1); menus += 1

    # ---- the permission list: ONE definition, two consumers
    if 'MODULE_PERMISSIONS' in pusrc:
        puout = pusrc
    else:
        one(pusrc, USERS_ANCHOR, "the User Administration module list")
        puout = pusrc.replace(USERS_ANCHOR, USERS_REPLACEMENT + '\n', 1)
        one(puout, USERS_IMPORT_ANCHOR, 'the users.py ContentType import')
        puout = puout.replace(USERS_IMPORT_ANCHOR, USERS_IMPORT_ADD, 1)
    if 'all_codenames' in pssrc:
        psout = pssrc
    else:
        one(pssrc, SETUP_ANCHOR, "the seeder's permission list")
        psout = pssrc.replace(SETUP_ANCHOR, SETUP_REPLACEMENT, 1)
        one(psout, SETUP_IMPORT_ANCHOR, 'the views_setup.py decorator import')
        psout = psout.replace(SETUP_IMPORT_ANCHOR, SETUP_IMPORT_ADD, 1)

    # ---- self-check BEFORE anything is written
    bad = []
    if 'class CashReceipt(' not in mout:
        bad.append('the CashReceipt model did not land')
    if 'class CashReceiptNumbering(' not in mout:
        bad.append('the numbering singleton did not land')
    if 'db_table = "cash_receipts"' not in mout:
        bad.append('the model has no explicit db_table')
    if mout.count('def cash_receipt_pdf_upload_path') != 1:
        bad.append('the upload path helper is missing or duplicated')
    for name in ('cash_receipt_list', 'cash_receipt_add', 'cash_receipt_commit',
                 'cash_receipt_void', 'cash_receipt_pdf'):
        if ('name="%s"' % name) not in uout:
            bad.append('url %s is not routed' % name)
    if 'from .receipts import *' not in vout:
        bad.append('views/receipts.py is not re-exported, so the URLconf '
                   'cannot resolve views.cash_receipt_list')
    if bout.count("url 'cash_receipt_list'") != 2:
        bad.append('expected Receipts in BOTH menus, found %d'
                   % bout.count("url 'cash_receipt_list'"))
    # every view the URLconf names must exist in the module being written
    for name in ('cash_receipt_list', 'cash_receipt_add', 'cash_receipt_commit',
                 'cash_receipt_void', 'cash_receipt_pdf'):
        if ('def %s(' % name) not in VIEWS_PY:
            bad.append('urls.py routes %s but the view module has no such '
                       'function' % name)
        if ('"%s"' % name) not in VIEWS_PY.split('__all__')[1][:400]:
            bad.append('%s is missing from the view module __all__, so the '
                       'wildcard re-export will not pick it up' % name)
    # THE PERMISSION THE SCREENS REQUIRE MUST BE A PERMISSION THE ADMIN SCREEN
    # OFFERS. A view guarded by a codename nobody can grant is a 403 with no
    # way out - and nothing else in this patcher would have noticed.
    for codename in ('can_access_receipts', 'can_edit_receipts'):
        if codename not in VIEWS_PY:
            bad.append('the views do not require %s' % codename)
        if codename not in PERMISSIONS_PY:
            bad.append('%s is not on the module permission list, so User '
                       'Administration cannot grant it' % codename)
    if 'MODULE_PERMISSIONS' not in puout:
        bad.append('users.py does not read the shared permission list')
    if 'all_codenames' not in psout:
        bad.append('views_setup.py does not read the shared permission list')
    if 'can_edit_' not in PERMISSIONS_PY:
        bad.append('the shared list has no edit tier')
    # the menus are gated on the RECEIPTS permission, not the invoices one
    if 'perms.auth.can_access_receipts' not in bout:
        bad.append('the menu entries are not gated on can_access_receipts')

    for src, label in ((NUMBERING_PY, 'cash_receipt_numbering.py'),
                       (VIEWS_PY, 'views/receipts.py'), (mout, 'models.py'),
                       (PERMISSIONS_PY, 'permissions.py'), (puout, 'views/users.py'),
                       (psout, 'views_setup.py')):
        try:
            compile(src, label, 'exec')
        except SyntaxError as e:
            bad.append('%s does not parse: %s' % (label, e))
    for name, html in (('cash_receipt.html', PDF_HTML),
                       ('cash_receipts.html', LIST_HTML),
                       ('cash_receipt_add.html', ADD_HTML)):
        ifs = len(re.findall(r'\{%\s*if\b', html))
        endifs = len(re.findall(r'\{%\s*endif\s*%\}', html))
        fors = len(re.findall(r'\{%\s*for\b', html))
        endfors = len(re.findall(r'\{%\s*endfor\s*%\}', html))
        if ifs != endifs:
            bad.append('%s: if/endif do not balance (%d/%d)' % (name, ifs, endifs))
        if fors != endfors:
            bad.append('%s: for/endfor do not balance (%d/%d)' % (name, fors, endfors))
        if len(re.findall(r'<div\b', html)) != len(re.findall(r'</div\s*>', html)):
            bad.append('%s: div tags do not balance' % name)
        css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.S))
        if css.count('{') != css.count('}'):
            bad.append('%s: CSS braces do not balance' % name)
    # the two screens must be on the standard, or this is a new page that
    # starts out needing a migration round of its own
    if 'table alv-table receipts-table' not in LIST_HTML:
        bad.append('the list screen is not on the table standard')
    if 'alv-empty-title' not in LIST_HTML:
        bad.append('the list screen has no empty state')
    if 'mobile-action-bar' not in LIST_HTML:
        bad.append('the list screen has no mobile action bar')
    # base must already own what these screens lean on
    for owed in ('.icon-duplicate', '.alv-empty', '.mobile-action-bar.cols-2',
                 '.alv-pill-good'):
        if owed not in bsrc:
            bad.append('base.html does not define %s - is an earlier push '
                       'missing?' % owed)
    if bad:
        sys.exit('! cash receipts self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  pages/models.py             CashReceipt + CashReceiptNumbering')
    print('  pages/urls.py               5 routes')
    print('  pages/views/__init__.py     receipts re-exported')
    print('  pages/templates/base.html   Receipts in %d menu(s)' % menus)
    print('  pages/views/users.py        reads the shared permission list')
    print('  pages/views_setup.py        seeds BOTH tiers from the same list')
    for path, key in NEW_FILES:
        print('  %-27s new' % os.path.relpath(path, ROOT).replace(os.sep, '/'))

    if not CHECK:
        for p in (MODELS, URLS, VINIT, BASE, USERS, VSETUP):
            backup(p)
        for p, out in ((MODELS, mout), (URLS, uout), (VINIT, vout), (BASE, bout),
                       (USERS, puout), (VSETUP, psout)):
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)
        for path, key in NEW_FILES:
            d = os.path.dirname(path)
            if not os.path.isdir(d):
                os.makedirs(d)
            if os.path.exists(path):
                backup(path)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(globals()[key])

    print('\n  %d file(s) %s'
          % (6 + len(NEW_FILES), 'would change' if CHECK else 'changed'))
    if not CHECK:
        print('\n  NEXT, and this round is not finished without it:')
        print('     python manage.py makemigrations pages')
        print('     python manage.py migrate')


if __name__ == '__main__':
    main()
