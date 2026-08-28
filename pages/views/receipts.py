"""Cash receipts.

Issue a numbered receipt for a payment, render it to PDF on the Alivente
letterhead, store the PDF on the record, and list what has been issued.

WHAT IS DELIBERATELY REUSED. The letterhead, the PDF engine and the static
resolution all come from `physical_invoices` rather than being written again.
COMPANY in two places is the contradiction pattern - two documents claiming
different VAT numbers, and nobody noticing until a tenant does.

EDITABLE, AND UNVOIDABLE - decided 29 Aug. A receipt is not an invoice and
does not need an invoice's strictness. Everything except the NUMBER can be
changed, and a void can be lifted. Two consequences follow, and both are
handled here rather than left implicit:

  * THE STORED PDF IS RE-RENDERED ON EVERY CHANGE. A record and a document
    that disagree is worse than either being wrong on its own, because only
    one of them is what the payer holds.
  * AN EDIT IS STAMPED. `edited_at` / `edited_by` record that the receipt no
    longer matches the copy that was originally handed over. The system cannot
    recall that copy; it can at least stop pretending nothing happened.

Functions
---------
- cash_receipt_list    : the issued receipts, newest first.
- cash_receipt_add     : the issue form; ?duplicate=<id> pre-fills from an
                         existing receipt WITHOUT copying its number or PDF.
- cash_receipt_commit  : assign the number, save, render and store the PDF -
                         all inside one transaction.
- cash_receipt_edit    : the same form, loaded from an existing receipt.
- cash_receipt_update  : save changes; the number is never touched.
- cash_receipt_void    : mark void; the number is kept.
- cash_receipt_unvoid  : lift a void.
- cash_receipt_pdf     : serve the stored PDF.

Auth tiers
----------
read tier -> auth.can_access_receipts  (list, pdf)
edit tier -> auth.can_edit_receipts    (add, commit, edit, update, void, unvoid)

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
    "cash_receipt_edit",
    "cash_receipt_update",
    "cash_receipt_void",
    "cash_receipt_unvoid",
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


def store_pdf(receipt):
    """Render the receipt and replace the stored file.

    THE OLD FILE IS DELETED FIRST, and this is the reason: Django does not
    overwrite: saving `CR-00372.pdf` over an existing one writes
    `CR-00372_a1b2c3.pdf` and leaves the first orphaned in media. Since a
    receipt is now re-rendered on every edit, void and unvoid, that would
    accumulate a copy per change - each one a plausible-looking receipt with
    the right number and the wrong contents, sitting in the media folder with
    nothing pointing at it.
    """
    pdf_bytes = render_cash_receipt_pdf(build_receipt_context(receipt))
    if receipt.pdf_file:
        receipt.pdf_file.delete(save=False)
    receipt.pdf_file.save(f"{receipt.receipt_number}.pdf",
                          ContentFile(pdf_bytes), save=True)


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
            'is_edited': bool(r.edited_at),
            'edited_display': r.edited_at.strftime('%Y-%m-%d') if r.edited_at else '',
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


# ---------------------------------------------------------------- the form
def _payer_choices():
    return {
        "tenants": Tenant.objects.all().order_by('tenant_name'),
        "customers": InvoiceCustomer.objects.all().order_by('name'),
        "properties": props.objects.all().order_by('prop_country', 'prop_name'),
    }


def _prefill_from(source, today=True):
    """The CONTENT of a receipt, as form values.

    Shared by Duplicate and Edit, which want the same fields for opposite
    reasons: one is about to make a new receipt that looks like this, the
    other is about to change this one.
    """
    return {
        "receipt_date": (date.today() if today else source.receipt_date).isoformat(),
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
        prefill.update(_prefill_from(source))
        # reference is NOT copied: it names the invoice the ORIGINAL settled,
        # and carrying it over would attach this receipt to a payment it has
        # nothing to do with.

    ctx = {"prefill": prefill, "next_number": preview_next(),
           "duplicated_from": source.receipt_number if source else "",
           "editing": False, "form_action": "commit"}
    ctx.update(_payer_choices())
    return render(request, "cash_receipt_add.html", ctx)


@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
def cash_receipt_edit(request, cash_receipt_id):
    """The same form, loaded from an existing receipt.

    Its own date is kept - an edit is a correction to a receipt for a payment
    that happened on a particular day, and re-dating it to today would change
    the fact rather than fix the record of it.
    """
    receipt = get_object_or_404(CashReceipt, pk=cash_receipt_id)
    prefill = _prefill_from(receipt, today=False)
    prefill["reference"] = receipt.reference     # unlike Duplicate, this IS the
                                                 # same receipt, so it keeps it
    ctx = {"prefill": prefill, "next_number": receipt.receipt_number,
           "duplicated_from": "", "editing": True, "form_action": "update",
           "receipt": receipt}
    ctx.update(_payer_choices())
    return render(request, "cash_receipt_add.html", ctx)


def _decimal_or_none(raw):
    try:
        value = Decimal((raw or '').replace(',', '').strip())
    except (InvalidOperation, AttributeError):
        return None
    return value


def _read_form(request):
    """Parse and validate the posted fields. Returns (values, errors).

    ONE parser for issue and for update, so the two can never come to
    different conclusions about what a valid receipt is.
    """
    errors = []
    payer_name = (request.POST.get('payer_name') or '').strip()
    amount = _decimal_or_none(request.POST.get('amount'))
    description = (request.POST.get('description') or '').strip()
    raw_date = (request.POST.get('receipt_date') or '').strip()

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

    def _fk(model, raw):
        raw = (raw or '').strip()
        return model.objects.filter(pk=raw).first() if raw.isdigit() else None

    method = request.POST.get('method') or CashReceipt.METHOD_TRANSFER
    if method not in dict(CashReceipt.METHOD_CHOICES):
        method = CashReceipt.METHOD_OTHER
    doc_format = request.POST.get('doc_format') or CashReceipt.FORMAT_ELECTRONIC
    if doc_format not in dict(CashReceipt.FORMAT_CHOICES):
        doc_format = CashReceipt.FORMAT_ELECTRONIC

    values = {
        'receipt_date': receipt_date,
        'amount': amount,
        'currency': (request.POST.get('currency') or 'EUR').strip()[:3] or 'EUR',
        'description': description,
        'method': method,
        'reference': (request.POST.get('reference') or '').strip(),
        'doc_format': doc_format,
        'tenant': _fk(Tenant, request.POST.get('tenant_id')),
        'customer': _fk(InvoiceCustomer, request.POST.get('customer_id')),
        'prop': _fk(props, request.POST.get('prop_id')),
        'payer_name': payer_name,
        'payer_address': (request.POST.get('payer_address') or '').strip(),
        'payer_tel': (request.POST.get('payer_tel') or '').strip(),
        'payer_email': (request.POST.get('payer_email') or '').strip(),
    }
    return values, errors


@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
@require_POST
def cash_receipt_commit(request):
    """Issue the receipt: number, record and PDF, in ONE transaction.

    The number is taken here and nowhere else. Assigning it when the form
    opens would show CR-00372 to two people at once; assigning it after the
    save would leave a receipt with no number if the render failed.
    """
    values, errors = _read_form(request)
    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('cash_receipt_add')

    with transaction.atomic():
        receipt = CashReceipt(
            receipt_number=assign_next(),
            created_by=request.user if request.user.is_authenticated else None,
            **values)
        receipt.save()
        # The PDF is stored, not re-rendered on demand. A receipt is a document
        # somebody was handed; re-rendering it next year through a changed
        # template would produce a different one under the same number.
        store_pdf(receipt)

    messages.info(request, f"Receipt {receipt.receipt_number} issued.")
    return redirect('cash_receipt_list')


@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
@require_POST
def cash_receipt_update(request, cash_receipt_id):
    """Save changes to an existing receipt.

    THE NUMBER IS NEVER TOUCHED. It is not read from the form, not written
    here, and not present on the form as a field - so there is no path by
    which a posted value could reach it. Everything else may change.

    The stored PDF is re-rendered, because a record and a document that
    disagree is worse than either being wrong alone.
    """
    receipt = get_object_or_404(CashReceipt, pk=cash_receipt_id)
    values, errors = _read_form(request)
    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('cash_receipt_edit', cash_receipt_id=receipt.pk)

    with transaction.atomic():
        for field, value in values.items():
            setattr(receipt, field, value)
        receipt.edited_at = timezone.now()
        receipt.edited_by = request.user if request.user.is_authenticated else None
        receipt.save()
        store_pdf(receipt)

    messages.info(request, f"Receipt {receipt.receipt_number} updated. "
                           "The stored PDF has been re-made; any copy already "
                           "sent shows the previous details.")
    return redirect('cash_receipt_list')


# --------------------------------------------------------------- void/unvoid
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
        store_pdf(receipt)

    messages.info(request, f"Receipt {receipt.receipt_number} voided. "
                           "Its number is kept, so the sequence has no gap.")
    return redirect('cash_receipt_list')


@login_required
@permission_required('auth.can_edit_receipts', raise_exception=True)
@require_POST
def cash_receipt_unvoid(request, cash_receipt_id):
    """Lift a void.

    Decided 29 Aug: a receipt is not an invoice and does not need an invoice's
    strictness. Nothing about the numbering depends on a void being permanent -
    the number was kept either way, and `highest_issued_number` counts voided
    rows precisely so that it does not matter.

    The void STAMP comes off the stored PDF, and the reason is cleared: it
    described a state the receipt is no longer in, and a stale reason on a live
    receipt is worse than none.
    """
    receipt = get_object_or_404(CashReceipt, pk=cash_receipt_id)
    if not receipt.is_void:
        messages.warning(request, f"{receipt.receipt_number} is not void.")
        return redirect('cash_receipt_list')

    with transaction.atomic():
        receipt.is_void = False
        receipt.voided_at = None
        receipt.voided_by = None
        receipt.void_reason = ''
        receipt.save(update_fields=['is_void', 'voided_at', 'voided_by',
                                    'void_reason', 'updated_at'])
        store_pdf(receipt)

    messages.info(request, f"Receipt {receipt.receipt_number} is live again.")
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
