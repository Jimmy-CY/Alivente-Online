#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Receipts: editable, unvoidable, and viewed in the house PDF modal.

THREE CHANGES, asked for 29 Aug.

1. UNVOID. A receipt is not an invoice and does not need an invoice's
   strictness. Nothing about the numbering depended on a void being permanent:
   the number is kept either way, and `highest_issued_number` counts voided
   rows precisely so that lifting one changes nothing about the sequence.

2. EDIT everything except the NUMBER. Two consequences, both handled rather
   than left implicit:
     * the stored PDF is RE-RENDERED on every change - a record and a document
       that disagree is worse than either being wrong alone, because only one
       of them is what the payer holds;
     * an edit is STAMPED (`edited_at` / `edited_by`) and the list says
       "edited". The system cannot recall the copy already sent; it can at
       least stop pretending nothing happened.

   The number is not read from the form, not written by the update view, and
   not present on the form as a field - there is no path by which a posted
   value could reach it.

3. THE PDF OPENS IN THE HOUSE MODAL. `components/pdf_viewer.html` already
   does this everywhere else - PDF.js with page navigation, zoom, download,
   and on a phone the native share sheet, which is how a receipt reaches
   WhatsApp. This is an include and an onclick, not a new component.

A FILE-HANDLING FAULT FIXED ON THE WAY. The previous round saved the void PDF
under a different name and left the original orphaned, and Django does not
overwrite - saving `CR-00372.pdf` twice writes `CR-00372_a1b2c3.pdf`. With a
receipt now re-rendered on every edit, void and unvoid, that would accumulate
one stray file per change: each a plausible receipt with the right number and
the wrong contents, sitting in media with nothing pointing at it. `store_pdf`
deletes the old file first and always uses `<number>.pdf`.

AFTER RUNNING THIS, the model gained two fields, so:

    python manage.py makemigrations pages
    python manage.py migrate

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
URLS   = os.path.join(ROOT, 'pages', 'urls.py')
VIEWS  = os.path.join(ROOT, 'pages', 'views', 'receipts.py')
LIST   = os.path.join(TPL, 'cash_receipts.html')
ADD    = os.path.join(TPL, 'cash_receipt_add.html')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_receditv'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:110]))


VIEWS_PY = r'''"""Cash receipts.

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
          <th style="text-align: left; width: 21%">Being Payment For</th>
          <th class="num" style="width: 12%">Amount</th>
          <th style="width: 9%">Status</th>
          <!-- 13%, not 9%. .cell-actions is nowrap, so four 34px buttons and
               their gaps need 178px whatever the declaration says - and the
               browser takes the difference from whichever column is next to
               it. Declaring the real width means the layout is what the file
               says it is. -->
          <th class="desktop-action-cell cell-actions" style="width: 13%">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for row in rows %}
          <tr{% if row.is_void %} class="rec-void"{% endif %}>
            <td data-label="Receipt #" class="ref">{{ row.number }}{% if row.is_edited %}
              <span class="rec-edited" title="Edited on {{ row.edited_display }} — any copy already sent shows the previous details">edited</span>{% endif %}</td>
            <td data-label="Date">{{ row.date|date:"Y-m-d" }}</td>
            <td data-label="Received From" style="text-align: left">{{ row.payer }}</td>
            <td data-label="Being Payment For" style="text-align: left">{{ row.description }}</td>
            <td data-label="Amount" class="num">&euro; {{ row.amount|floatformat:2|intcomma }}</td>
            <td data-label="Status">
              <span class="alv-pill {{ row.status_pill }}">{{ row.status_display }}</span>
            </td>
            <td data-label="Actions" class="desktop-action-cell cell-actions">
              <div class="row-actions">
                <a href="{% url 'cash_receipt_pdf' row.pk %}"
                   onclick="openPdfViewer('{% url 'cash_receipt_pdf' row.pk %}', 'Receipt {{ row.number|escapejs }} &mdash; {{ row.payer|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                   class="icon-action-btn icon-view" title="View receipt">
                  <i class="fas fa-file-pdf"></i>
                </a>
                {% if perms.auth.can_edit_receipts %}
                  <a href="{% url 'cash_receipt_edit' row.pk %}"
                     class="icon-action-btn icon-edit" title="Edit this receipt">
                    <i class="fas fa-pencil-alt"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No permission to edit receipts">
                    <i class="fas fa-pencil-alt"></i>
                  </span>
                {% endif %}
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
                {% if row.is_void and perms.auth.can_edit_receipts %}
                  <form method="post" action="{% url 'cash_receipt_unvoid' row.pk %}"
                        class="rec-inline-form"
                        onsubmit="return confirm('Bring receipt {{ row.number }} back into use?\n\nThe VOID stamp comes off its PDF.');">
                    {% csrf_token %}
                    <button type="submit" class="icon-action-btn icon-approve" title="Unvoid — bring back into use">
                      <i class="fas fa-rotate-left"></i>
                    </button>
                  </form>
                {% elif perms.auth.can_edit_receipts %}
                  <form method="post" action="{% url 'cash_receipt_void' row.pk %}"
                        class="rec-inline-form"
                        onsubmit="return confirm('Void receipt {{ row.number }}?\n\nIt keeps its number and stays in the list, marked VOID. You can lift it again afterwards.');">
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
            <td class="mobile-action-bar cols-4">
              <a href="{% url 'cash_receipt_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'cash_receipt_pdf' row.pk %}', 'Receipt {{ row.number|escapejs }} &mdash; {{ row.payer|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View</span>
              </a>
              {% if perms.auth.can_edit_receipts %}
                <a href="{% url 'cash_receipt_edit' row.pk %}" class="mobile-action-btn">
                  <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                  <span class="mobile-action-label">Edit</span>
                </a>
              {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                  <i class="fas fa-pencil-alt mobile-action-icon"></i>
                  <span class="mobile-action-label">Edit</span>
                </span>
              {% endif %}
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
              {% if perms.auth.can_edit_receipts %}
                {% if row.is_void %}
                  <form method="post" action="{% url 'cash_receipt_unvoid' row.pk %}"
                        class="rec-inline-form-mobile"
                        onsubmit="return confirm('Bring receipt {{ row.number }} back into use?\n\nThe VOID stamp comes off its PDF.');">
                    {% csrf_token %}
                    <button type="submit" class="mobile-action-btn">
                      <i class="fas fa-rotate-left mobile-action-icon icon-color-approve"></i>
                      <span class="mobile-action-label">Unvoid</span>
                    </button>
                  </form>
                {% else %}
                  <form method="post" action="{% url 'cash_receipt_void' row.pk %}"
                        class="rec-inline-form-mobile"
                        onsubmit="return confirm('Void receipt {{ row.number }}?\n\nIt keeps its number and stays in the list, marked VOID. You can lift it again afterwards.');">
                    {% csrf_token %}
                    <button type="submit" class="mobile-action-btn">
                      <i class="fas fa-ban mobile-action-icon icon-color-delete"></i>
                      <span class="mobile-action-label">Void</span>
                    </button>
                  </form>
                {% endif %}
              {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                  <i class="fas fa-ban mobile-action-icon"></i>
                  <span class="mobile-action-label">Void</span>
                </span>
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

<!-- The house PDF viewer: a modal with page navigation, zoom, download, and -
     on a phone - the native share sheet, which is how a receipt reaches
     WhatsApp. Same component Physical Invoices, Passports and Title Deeds use.

     This note is an HTML comment on purpose. Django's own template comments
     are SINGLE-LINE ONLY - its lexer matches them without a DOTALL flag - so
     one spanning several lines is not a comment at all and renders as visible
     text on the page. This note was written that way first, and
     test_delete_choice.py caught it before it reached Live. -->
{% include 'components/pdf_viewer.html' %}

<style>
.rec-next {
    color: var(--alv-ink-soft);
    font-size: 13px;
    margin-bottom: 8px;
}

/* An inline <form> is how a POST icon button is written on every page that
   has one. It must not become a layout box of its own. */
.rec-inline-form { display: inline; margin: 0; }

/* A receipt that has been changed since it was issued. Quiet - it is not an
   error - but present, because the copy the payer holds may say something
   else and the system cannot recall it. */
.rec-edited {
    display: inline-block;
    margin-left: 6px;
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .04em;
    color: var(--alv-ink-faint);
}

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
{% if editing %}Edit Receipt{% else %}Issue Receipt{% endif %}
{% endblock %}

{% block content %}

<h2 class="page-title-h2"><center>ALIVENTE ONLINE - RECEIPTS</center></h2>
<h4 class="page-subtitle-h4"><center>{% if editing %}EDIT RECEIPT {{ next_number }}{% else %}ISSUE RECEIPT{% endif %}</center></h4>
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
    <i class="fas fa-check"></i> {% if editing %}Save Changes{% else %}Issue Receipt{% endif %}
  </button>
  <a href="{% url 'cash_receipt_list' %}" class="btn action-back" title="Back to receipts">
    <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
  </a>
</div>

{% if editing %}
  <div class="rec-note rec-note-warn">
    <i class="fas fa-pen"></i>
    Editing <strong>{{ next_number }}</strong>. Saving re-makes the stored PDF, and
    the receipt is marked as edited. <strong>Any copy already emailed or handed
    over still shows the previous details</strong> &mdash; the system cannot recall it.
  </div>
{% endif %}

{% if duplicated_from %}
  <div class="rec-note">
    <i class="fas fa-copy"></i>
    Copied from <strong>{{ duplicated_from }}</strong>, dated today. It becomes a
    new receipt with its own number when you issue it — nothing has been saved yet.
  </div>
{% endif %}

<form action="{% if editing %}{% url 'cash_receipt_update' receipt.pk %}{% else %}{% url 'cash_receipt_commit' %}{% endif %}" method="post" id="receiptForm">
  {% csrf_token %}

  <div class="alv-card">
    <div class="alv-card-head">
      <span class="alv-card-title">The payment</span>
      <span class="alv-card-aside rec-number">{% if editing %}Receipt {{ next_number }} &mdash; the number cannot change{% else %}Will be issued as {{ next_number }}{% endif %}</span>
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
.rec-note-warn {
    background: var(--alv-warn-soft);
    border-color: #ecd9a8;
    color: var(--alv-warn);
}
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


# ------------------------------------------------------------------ anchors
# NOT `sent_at` alone - PhysicalInvoice has one too and the anchor matched
# twice. The void_reason line above it belongs to CashReceipt only.
MODEL_ANCHOR = """    void_reason = models.CharField(max_length=255, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)"""

MODEL_ADD = """    void_reason = models.CharField(max_length=255, blank=True)

    # An edit changes what the record says AFTER a copy may already have been
    # handed over. The system cannot recall that copy; stamping the change is
    # the least it can do, and the list shows it.
    edited_at = models.DateTimeField(null=True, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  blank=True, related_name='edited_cash_receipts')

    sent_at = models.DateTimeField(null=True, blank=True)"""

URL_ANCHOR = ('    path("receipts/<int:cash_receipt_id>/void/", '
              'views.cash_receipt_void, name="cash_receipt_void"),')

URL_ADD = (URL_ANCHOR + '\n'
           '    path("receipts/<int:cash_receipt_id>/unvoid/", views.cash_receipt_unvoid, name="cash_receipt_unvoid"),\n'
           '    path("receipts/<int:cash_receipt_id>/edit/", views.cash_receipt_edit, name="cash_receipt_edit"),\n'
           '    path("receipts/<int:cash_receipt_id>/update/", views.cash_receipt_update, name="cash_receipt_update"),')


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and os.path.exists(p):
        shutil.copy2(p, b)


def main():
    for p in (MODELS, URLS, VIEWS, LIST, ADD):
        if not os.path.exists(p):
            sys.exit('! %s is missing - run apply_cash_receipts.py first'
                     % os.path.relpath(p, ROOT))

    msrc, usrc = read(MODELS), read(URLS)
    vsrc, lsrc, asrc = read(VIEWS), read(LIST), read(ADD)

    # "Already applied" must mean applied AT THIS VERSION, not applied at
    # some version. The first cut of this round shipped a multi-line Django
    # comment in cash_receipts.html - which is not a comment at all, because
    # Django's lexer has no DOTALL flag, so it renders as visible text. With
    # the coarse test below, a tree that had the broken version would report
    # "already applied" and re-running would repair nothing. VERSION_MARK is
    # a string only the fixed template carries.
    VERSION_MARK = 'SINGLE-LINE ONLY'
    if ('def cash_receipt_unvoid' in vsrc and 'edited_at' in msrc
            and 'cash_receipt_edit' in usrc and VERSION_MARK in lsrc):
        print('  receipts edit/unvoid/modal   already applied')
        print('\n  0 file(s) changed')
        return

    # ---- model
    if 'edited_at' in msrc:
        mout = msrc
    else:
        one(msrc, MODEL_ANCHOR, 'the CashReceipt sent_at field')
        mout = msrc.replace(MODEL_ANCHOR, MODEL_ADD, 1)

    # ---- urls
    if 'cash_receipt_unvoid' in usrc:
        uout = usrc
    else:
        one(usrc, URL_ANCHOR, 'the receipt void route')
        uout = usrc.replace(URL_ANCHOR, URL_ADD, 1)

    # ---- the three files this round rewrites wholesale. They were written by
    # apply_cash_receipts.py one round ago and are ours; the check below is
    # that they are still THAT version and have not been edited since.
    for label, src, marker, absent in (
            ('views/receipts.py', vsrc, 'def cash_receipt_commit', 'def cash_receipt_unvoid'),
            ('cash_receipts.html', lsrc, 'receipts-table', 'cash_receipt_unvoid'),
            ('cash_receipt_add.html', asrc, 'id="receiptForm"', 'form_action')):
        if marker not in src:
            sys.exit('! %s does not look like the version this round expects '
                     '(no %r)' % (label, marker))

    vout, lout, aout = VIEWS_PY, LIST_HTML, ADD_HTML

    # ---- self-check BEFORE anything is written
    bad = []
    if 'edited_at' not in mout or 'edited_by' not in mout:
        bad.append('the edit stamp did not land on the model')
    if mout.count('edited_at = models.DateTimeField') != 1:
        bad.append('edited_at is missing or duplicated')
    for name in ('cash_receipt_unvoid', 'cash_receipt_edit', 'cash_receipt_update'):
        if ('name="%s"' % name) not in uout:
            bad.append('%s is not routed' % name)
        if ('def %s(' % name) not in vout:
            bad.append('%s is routed but not defined' % name)
        if ('"%s"' % name) not in vout.split(']')[0]:
            bad.append('%s is not exported, so views.%s will not resolve'
                       % (name, name))
    # THE NUMBER. The update path must not be able to write it, by any route.
    #
    # The first version of this check searched cash_receipt_update for the
    # string "receipt_number" - and caught its own docstring, which says the
    # number is never touched. Prose is not mechanism. What actually decides
    # this is that `cash_receipt_update` writes ONLY the keys `_read_form`
    # returns, so the question is whether that dict can contain the number.
    try:
        import ast
        _tree = ast.parse(vout)
        _fns = {n.name: n for n in _tree.body if isinstance(n, ast.FunctionDef)}

        # (a) the dict _read_form builds must not carry the number
        _keys = set()
        for node in ast.walk(_fns.get('_read_form', ast.Module(body=[], type_ignores=[]))):
            if isinstance(node, ast.Dict):
                for k in node.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        _keys.add(k.value)
        if not _keys:
            bad.append('could not read the fields _read_form returns')
        if 'receipt_number' in _keys:
            bad.append('_read_form returns receipt_number, so the update loop '
                       'would write it')

        # (b) and nothing in the update assigns to it directly either
        for node in ast.walk(_fns.get('cash_receipt_update',
                                      ast.Module(body=[], type_ignores=[]))):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Attribute) and t.attr == 'receipt_number':
                        bad.append('cash_receipt_update assigns receipt_number')
            if isinstance(node, ast.Call):
                fn = node.func
                if (isinstance(fn, ast.Name) and fn.id == 'setattr'
                        and len(node.args) >= 2
                        and isinstance(node.args[1], ast.Constant)
                        and node.args[1].value == 'receipt_number'):
                    bad.append('cash_receipt_update setattrs receipt_number')
    except SyntaxError as e:
        bad.append('the view module does not parse: %s' % e)
    if "request.POST.get('receipt_number')" in vout:
        bad.append('the number is read from the form somewhere')
    if 'name="receipt_number"' in aout:
        bad.append('the form carries a receipt_number field')
    # THE FILE. One name, old one deleted first.
    if 'pdf_file.delete(save=False)' not in vout:
        bad.append('store_pdf does not delete the previous file, so every '
                   'edit would orphan one')
    if '-void.pdf' in vout:
        bad.append('the void path still writes a second filename')
    if vout.count('def store_pdf') != 1:
        bad.append('store_pdf is missing or duplicated')
    for path in ('commit', 'update', 'void', 'unvoid'):
        seg = vout.split('def cash_receipt_%s' % path)[1].split('\ndef ')[0]
        if 'store_pdf(receipt)' not in seg:
            bad.append('cash_receipt_%s does not re-store the PDF' % path)
    # unvoid must actually clear the state, not just the flag
    _un = vout.split('def cash_receipt_unvoid')[1].split('\ndef ')[0]
    for field in ('is_void = False', 'voided_at = None', 'voided_by = None',
                  "void_reason = ''"):
        if field not in _un:
            bad.append('unvoid does not clear %s' % field.split(' =')[0])
    # the viewer
    if VERSION_MARK not in lout:
        bad.append('the list template is not the fixed version')
    for name, html in (('cash_receipts.html', lout), ('cash_receipt_add.html', aout)):
        _open = [i for i, l in enumerate(html.split('\n'), 1)
                 if '{#' in l and '#}' not in l]
        if _open:
            bad.append('%s has a Django comment spanning lines (line %s) - '
                       'Django matches {#...#} without DOTALL, so it renders '
                       'as visible text' % (name, _open))
    if "{% include 'components/pdf_viewer.html' %}" not in lout:
        bad.append('the list does not include the PDF viewer component')
    if 'openPdfViewer(' not in lout:
        bad.append('the View action does not open the modal')
    if 'target="_blank"' in lout:
        bad.append('a View action still opens a new tab instead of the modal')
    if not os.path.exists(os.path.join(TPL, 'components', 'pdf_viewer.html')):
        bad.append('components/pdf_viewer.html is not in this tree')
    # four actions, so four columns on a phone
    if 'mobile-action-bar cols-4' not in lout:
        bad.append('the mobile bar does not declare four columns')
    if 'cols-2' in lout:
        bad.append('the mobile bar still varies its column count')
    if '.mobile-action-bar.cols-4' not in read(os.path.join(TPL, 'base.html')):
        bad.append('base does not define cols-4')
    # the form serves both purposes
    if "{% url 'cash_receipt_update' receipt.pk %}" not in aout:
        bad.append('the form cannot post an update')
    if 'the number cannot change' not in aout:
        bad.append('the form does not say the number is fixed')
    if 'still shows the previous details' not in aout:
        bad.append('the form does not warn that a sent copy will differ')
    try:
        compile(vout, 'views/receipts.py', 'exec')
        compile(mout, 'models.py', 'exec')
    except SyntaxError as e:
        bad.append('does not parse: %s' % e)
    for name, html in (('cash_receipts.html', lout), ('cash_receipt_add.html', aout)):
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
    if bad:
        sys.exit('! receipts edit/unvoid round self-check FAILED, nothing '
                 'written:\n   - %s' % '\n   - '.join(bad))

    print('  pages/models.py             edited_at / edited_by on CashReceipt')
    print('  pages/urls.py               3 routes: unvoid, edit, update')
    print('  pages/views/receipts.py     rewritten - one form parser, one store_pdf')
    print('  cash_receipts.html          PDF modal, Edit, Void/Unvoid')
    print('  cash_receipt_add.html       serves add AND edit')

    if not CHECK:
        for p in (MODELS, URLS, VIEWS, LIST, ADD):
            backup(p)
        for p, out in ((MODELS, mout), (URLS, uout), (VIEWS, vout),
                       (LIST, lout), (ADD, aout)):
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  5 file(s) %s' % ('would change' if CHECK else 'changed'))
    if not CHECK:
        print('\n  NEXT, because the model gained two fields:')
        print('     python manage.py makemigrations pages')
        print('     python manage.py migrate')


if __name__ == '__main__':
    main()
