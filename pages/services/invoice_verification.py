"""
Invoice verification for Actual Expenses  (two-way match).
==========================================================

The workflow this serves
------------------------
1. A user captures an `act_expense` with an ESTIMATED amount (the work has not
   been done and no invoice exists yet).
2. A superuser Approves it. From that moment the amount is read-only to the
   user (enforced in `act_expense_edit_commit`).
3. The supplier does the work and issues an invoice.
4. The user uploads that invoice on the Invoice Document tab.  <-- WE RUN HERE
5. The superuser reviews and pays; then marks it Paid.

Our only job at step 4 is to answer one question: **does the supplier's claim
match the amount that was authorised?**  We never populate, never correct and
never change a financial figure.  We record a verdict and (on a mismatch) send
an email, exactly like the existing approved/paid notifications.

Three verdicts, not two
-----------------------
The amount rule is EXACT match (a user decision).  That only works if documents
we cannot read confidently are kept OUT of ``mismatch``:

    verified      - payable total read confidently and equal to the approved amount
    mismatch      - payable total read confidently and different   -> email + amber
    unverified    - could not read a payable total we trust        -> review by eye
    not_invoice   - the file is not an invoice (a quote, a photo of a wall, ...)

Routing unreadable scans into ``mismatch`` would flood the flag and train
everyone to ignore it.  ``unverified`` costs nothing: it simply returns the
reviewer to the manual check they do today.

Only the AMOUNT can raise a mismatch.  Date, description and property are
advisory notes for the reviewer's eye — never a flag.  That is the main defence
against alert fatigue.

Dependencies: standard library only, same as `portfolio_insights._llm_brief`.
Configuration: ANTHROPIC_API_KEY (already set on Railway).  With no key the
feature is dormant and the system behaves exactly as it does today.
"""

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

log = logging.getLogger(__name__)

# ---------------------------------------------------------------- verdicts --
STATUS_VERIFIED = 'verified'
STATUS_MISMATCH = 'mismatch'
STATUS_UNVERIFIED = 'unverified'
STATUS_NOT_INVOICE = 'not_invoice'
STATUS_SPLIT = 'split'              # one invoice covering several expenses
STATUS_PENDING = 'pending'          # stored, never yet checked

STATUS_CHOICES = [
    (STATUS_VERIFIED, 'Verified'),
    (STATUS_MISMATCH, 'Mismatch'),
    (STATUS_UNVERIFIED, 'Could not verify'),
    (STATUS_NOT_INVOICE, 'Not an invoice'),
    (STATUS_SPLIT, 'Covers several expenses'),
    (STATUS_PENDING, 'Not checked'),
]

# Prompt/interface version. Stored with each verdict so an old row stays
# interpretable after the prompt is changed.
PROMPT_VERSION = 'iv-2'

# Extraction must be at least this sure of itself before we are willing to
# raise a mismatch against a human's approved figure.
MIN_CONFIDENCE = 0.75

# A MISMATCH accuses a supplier and emails the approver, so it must clear a
# higher bar than a VERIFIED (which only agrees with a figure a human already
# approved). Learned the hard way: on 16 Aug 2026 a handwritten ATOM invoice
# reading EUR 35.70 was reported at EUR 100.00 with self-reported confidence
# above 0.75. Self-assessment is not enough for a consequential verdict.
MIN_CONFIDENCE_TO_FLAG = 0.90

# ...and the extraction must prove itself arithmetically: net + VAT == total.
# A correctly-read invoice reconciles (30.00 + 5.70 = 35.70); a hallucinated
# total does not. Tolerance covers rounding on the document itself.
RECONCILE_TOLERANCE = Decimal('0.02')

# Invoice dates legitimately differ from the expense date; only comment when
# the gap is implausible.
DATE_GAP_DAYS = 90

DEFAULT_MODEL = 'claude-haiku-4-5'
DEFAULT_TIMEOUT = 30.0
API_URL = 'https://api.anthropic.com/v1/messages'

# A PDF larger than this is not worth sending; the reviewer looks by eye.
MAX_DOC_BYTES = 6 * 1024 * 1024


class ExtractionUnavailable(Exception):
    """Extraction could not run at all (no key, network, timeout, bad reply)."""


# ---------------------------------------------------------------------------
# 1. Extraction
# ---------------------------------------------------------------------------

_PROMPT = """You are reading a supplier invoice for a property-management company.

Return ONLY a JSON object, no prose and no markdown fence, with exactly these keys:

{
  "is_invoice": true|false,
  "payable_total": number|null,
  "net_amount": number|null,
  "vat_amount": number|null,
  "invoice_count": integer,
  "total_is_unambiguous": true|false,
  "currency": "EUR"|"GBP"|... |null,
  "invoice_date": "YYYY-MM-DD"|null,
  "invoice_number": string|null,
  "supplier_name": string|null,
  "property_hint": string|null,
  "description_summary": string|null,
  "confidence": 0.0-1.0
}

Definitions, follow them exactly:

- "payable_total" is the single amount the customer must actually PAY: the
  final gross total, after any discount, INCLUDING VAT if VAT is charged.
  It is NOT the net/subtotal and NOT the VAT line on its own.
- "total_is_unambiguous" must be false whenever you are not certain which
  figure is the payable total - for example when net, VAT and gross are all
  shown and the layout is unclear, when the scan is cut off or illegible,
  when several totals compete, or when the document shows a running balance
  rather than an amount due. When in doubt, say false. A false here is a
  perfectly good answer and is much better than a confident wrong number.
- "is_invoice" is false for quotations, estimates, proformas, delivery notes,
  statements, receipts for something else, or any image that is not a bill.
- "property_hint" is any address, apartment, floor or property name printed on
  the invoice that identifies WHERE the work was done. null if none is shown -
  most small invoices show none, and that is normal.
- "description_summary" is a short phrase (max 10 words) for the work or goods
  billed, in English even when the invoice is in Greek.
- "net_amount" and "vat_amount" are the figures that ADD UP to payable_total.
  Report them whenever they are printed. If VAT is not charged, vat_amount is
  0 and net_amount equals payable_total. These let us check your arithmetic,
  so do not invent them - use null if they are not on the document.
- "invoice_count" is how many SEPARATE invoices this file contains. A file is
  often several documents merged together - e.g. a labour invoice from one
  supplier and a parts invoice from another. Count them honestly. If it is
  more than 1, also make total_is_unambiguous false, because there is no
  single payable total for the file.
- "confidence" is your overall confidence in the extracted figures.

HOW THESE PARTICULAR INVOICES ARE PRINTED - read this carefully:

- The page MAY BE ROTATED 90, 180 or 270 degrees, because invoices are often
  scanned or photographed sideways. Mentally rotate the page and read it in
  whatever orientation makes sense. A rotated page is normal, not a reason to
  give up.
- Amounts are often HANDWRITTEN on a pre-printed pad.
- Amounts are often printed in TWO SEPARATE ADJACENT COLUMNS, one headed
  euro / EUR / € and the next headed cent / cents. When you see this, JOIN
  them: euro column 84 and cent column 03 means 84.03 - NOT 8403 and NOT 84.
  Getting the cents column wrong is the single most common mistake here.
- Where several rows are stacked, the payable total is the LAST one, labelled
  with any of: Total, Ολικό, ΟΛΙΚΟ, Σύνολο, ΣΥΝΟΛΟ, Πληρωτέο, Amount Due,
  Grand Total. The rows above it - Amount, Ποσό, Subtotal, Αξία, and the VAT
  row (V.A.T., Φ.Π.Α.) - are NOT the payable total. Typical shape:
      Amount / Ποσό      84 | 03
      V.A.T. / Φ.Π.Α 19%  15 | 97
      Total / Ολικό     100 | 00     <- payable_total is 100.00
  A quick sanity check you should apply: net + VAT should equal the total. If
  it does, you have identified the rows correctly and total_is_unambiguous can
  be true even on a handwritten pad.

The invoice may be in Greek or English. Read either. Never guess a number that
is not printed on the document; use null instead."""


def _api_config():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    model = os.environ.get('INVOICE_VERIFY_MODEL', DEFAULT_MODEL)
    try:
        timeout = float(os.environ.get('INVOICE_VERIFY_TIMEOUT', DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT
    return api_key, model, timeout


def _strip_fence(text):
    """Models occasionally wrap JSON in a markdown fence despite instructions."""
    text = (text or '').strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    return text.strip()


def extract_invoice(file_bytes, media_type='application/pdf'):
    """Read an invoice and return the structured dict described in _PROMPT.

    Raises ExtractionUnavailable on any failure. The caller turns that into
    an 'unverified' verdict - it must never break the upload.
    """
    api_key, model, timeout = _api_config()
    if not api_key:
        raise ExtractionUnavailable('ANTHROPIC_API_KEY is not set')
    if not file_bytes:
        raise ExtractionUnavailable('empty file')
    if len(file_bytes) > MAX_DOC_BYTES:
        raise ExtractionUnavailable('document too large to verify (%d bytes)' % len(file_bytes))

    encoded = base64.standard_b64encode(file_bytes).decode('ascii')
    if media_type == 'application/pdf':
        doc_block = {
            'type': 'document',
            'source': {'type': 'base64', 'media_type': 'application/pdf', 'data': encoded},
        }
    else:
        doc_block = {
            'type': 'image',
            'source': {'type': 'base64', 'media_type': media_type, 'data': encoded},
        }

    body = json.dumps({
        'model': model,
        'max_tokens': 700,
        'messages': [{'role': 'user', 'content': [doc_block, {'type': 'text', 'text': _PROMPT}]}],
    }).encode('utf-8')

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        raise ExtractionUnavailable('HTTP %s from extraction API' % exc.code)
    except Exception as exc:                                    # noqa: BLE001
        raise ExtractionUnavailable('extraction call failed: %s' % exc)

    blocks = data.get('content') or []
    text = ''.join(b.get('text', '') for b in blocks if b.get('type') == 'text')
    try:
        parsed = json.loads(_strip_fence(text))
    except Exception:                                           # noqa: BLE001
        raise ExtractionUnavailable('extraction returned unparseable JSON')
    if not isinstance(parsed, dict):
        raise ExtractionUnavailable('extraction returned a non-object')
    return parsed


# ---------------------------------------------------------------------------
# 2. Coercion helpers - tolerant of the formats real invoices use
# ---------------------------------------------------------------------------

def _to_decimal(value):
    """'1.234,56' / '1,234.56' / '95,20' / 95.2 -> Decimal. None when hopeless."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r'[^\d,.\-]', '', text)       # drop EUR, spaces, symbols
    if not text:
        return None

    if ',' in text and '.' in text:
        # Whichever separator is last is the decimal point.
        text = (text.replace('.', '').replace(',', '.') if text.rfind(',') > text.rfind('.')
                else text.replace(',', ''))
    elif ',' in text:
        # A single comma is a decimal comma when it has 1-2 trailing digits.
        text = text.replace(',', '.') if re.search(r',\d{1,2}$', text) else text.replace(',', '')

    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _to_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _money(amount):
    return '€%s' % amount


# ---------------------------------------------------------------------------
# 3. The verdict
# ---------------------------------------------------------------------------

def evaluate(expense_amount, expense_date, expense_description, property_name, extracted):
    """Pure comparison - no ORM, no I/O, so it is directly unit-testable.

    Returns {status, invoice_total, invoice_date, invoice_number, supplier,
             notes, advisories}.
    """
    advisories = []
    total = _to_decimal(extracted.get('payable_total'))
    net = _to_decimal(extracted.get('net_amount'))
    vat = _to_decimal(extracted.get('vat_amount'))
    try:
        invoice_count = int(extracted.get('invoice_count') or 1)
    except (TypeError, ValueError):
        invoice_count = 1
    inv_date = _to_date(extracted.get('invoice_date'))
    inv_number = (extracted.get('invoice_number') or None)
    supplier = (extracted.get('supplier_name') or None)
    currency = (extracted.get('currency') or '').upper() or None
    confidence = _to_float(extracted.get('confidence'), 0.0)
    unambiguous = bool(extracted.get('total_is_unambiguous'))

    result = {
        'invoice_total': total,
        'invoice_date': inv_date,
        'invoice_number': inv_number,
        'supplier': supplier,
        'advisories': advisories,
    }

    # -- gates: anything uncertain becomes 'unverified', never 'mismatch' ----
    if extracted.get('is_invoice') is False:
        result['status'] = STATUS_NOT_INVOICE
        result['notes'] = 'This file does not look like an invoice, so no check was made.'
        return result

    if total is None:
        result['status'] = STATUS_UNVERIFIED
        result['notes'] = 'No payable total could be read. Please check the document by eye.'
        return result

    if invoice_count > 1:
        result['status'] = STATUS_UNVERIFIED
        result['notes'] = ('This file contains %d separate invoices, so it has no single '
                           'payable total. Please check it by eye.' % invoice_count)
        return result

    if not unambiguous:
        result['status'] = STATUS_UNVERIFIED
        result['notes'] = ('The payable total on this document is ambiguous (it may show net, '
                           'VAT and gross separately). Read %s as the amount due, but please '
                           'confirm by eye.' % _money(total))
        return result

    if confidence < MIN_CONFIDENCE:
        result['status'] = STATUS_UNVERIFIED
        result['notes'] = ('The document could not be read with enough confidence to check it. '
                           'Please check by eye.')
        return result

    if currency and currency != 'EUR':
        result['status'] = STATUS_UNVERIFIED
        result['notes'] = ('This invoice appears to be in %s, not euro, so the amount was not '
                           'compared. Please check by eye.' % currency)
        return result

    # -- advisories: never affect the verdict -------------------------------
    # Suppressed below this confidence: on a rotated or handwritten scan the
    # supplier/property text comes back as OCR noise ("KATERINI ADOMOMEEZ"),
    # which reads as a discrepancy when it is only a bad read. The amount is
    # far more robust than the words around it, so a low-confidence read is
    # allowed to decide the verdict but not to editorialise about it.
    advisories_trusted = confidence >= MIN_CONFIDENCE_TO_FLAG

    if advisories_trusted and inv_date and expense_date:
        delta = (inv_date - expense_date).days
        if delta < -DATE_GAP_DAYS or delta > DATE_GAP_DAYS:
            advisories.append('Invoice dated %s, %d days from the expense date %s.'
                              % (inv_date.isoformat(), abs(delta), expense_date.isoformat()))

    hint = (extracted.get('property_hint') or '').strip()
    if advisories_trusted and hint and property_name:
        # Silent when the invoice names no property - most small ones do not,
        # and absence of evidence must never read as a mismatch.
        if not _loosely_matches(hint, property_name):
            advisories.append('Invoice refers to "%s"; this expense is on %s.' % (hint, property_name))

    summary = (extracted.get('description_summary') or '').strip()
    if advisories_trusted and summary and expense_description:
        advisories.append('Invoice is for "%s"; expense says "%s".' % (summary, expense_description))

    # -- the only rule that can flag: exact amount match --------------------
    if expense_amount is None:
        result['status'] = STATUS_UNVERIFIED
        result['notes'] = 'The expense has no amount to compare against.'
        return result

    approved = _to_decimal(expense_amount)
    if approved is not None and total == approved:
        result['status'] = STATUS_VERIFIED
        result['notes'] = 'Invoice total %s matches the approved amount.' % _money(total)
    else:
        # Before accusing anyone, demand proof: high confidence AND arithmetic
        # that reconciles. Anything less is uncertainty, and uncertainty must
        # never become a mismatch.
        if confidence < MIN_CONFIDENCE_TO_FLAG or not _reconciles(total, net, vat):
            result['status'] = STATUS_UNVERIFIED
            reason = ('the figures on it do not add up (net + VAT should equal the total)'
                      if not _reconciles(total, net, vat)
                      else 'it could not be read confidently enough to be sure')
            result['notes'] = ('This invoice reads as %s against an approved %s, but %s. '
                               'Not reported as a mismatch - please check it by eye.'
                               % (_money(total), _money(approved), reason))
            return result

        factor = _split_factor(total, approved)
        if factor:
            result['status'] = STATUS_SPLIT
            result['notes'] = ('Invoice total %s is exactly %d x the approved amount %s - it '
                               'looks like one invoice covering %d expenses. Not treated as a '
                               'mismatch.' % (_money(total), factor, _money(approved), factor))
            return result
        difference = (total - approved) if approved is not None else None
        result['status'] = STATUS_MISMATCH
        result['notes'] = ('Invoice total %s does not match the approved amount %s (difference %s).'
                           % (_money(total), _money(approved),
                              _money(difference) if difference is not None else 'unknown'))
    return result


def _split_factor(total, approved):
    """How many equal expenses one invoice appears to cover.

    One supplier invoice is often raised for work across several properties and
    then attached to each of those expenses (e.g. a single EUR 744 certificate
    invoice booked against three EUR 248 expenses). That is correct accounting,
    not an overbill, so it must not be reported as a mismatch. Returns the
    integer factor (2..12) when the totals divide cleanly, else None.
    """
    if not total or not approved or approved <= 0 or total <= approved:
        return None
    ratio = total / approved
    nearest = int(ratio.to_integral_value())
    if 2 <= nearest <= 12 and abs(ratio - nearest) <= Decimal('0.005'):
        return nearest
    return None


def _reconciles(total, net, vat):
    """True when net + VAT equals the total, so the figures prove each other.

    This is an OBJECTIVE test, unlike the model's own confidence score, and it
    is what stands between a misread number and an accusation aimed at a
    supplier. Returns False when the parts are missing - unproven, so unusable
    for flagging.
    """
    if total is None or net is None or vat is None:
        return False
    return abs((net + vat) - total) <= RECONCILE_TOLERANCE


def _loosely_matches(hint, property_name):
    """True when the invoice's property hint plausibly refers to this property.

    Deliberately generous: this only ever produces an advisory note, and a
    false alarm is more annoying than a miss.
    """
    def tokens(text):
        return {t for t in re.split(r'[^0-9A-Za-zͰ-Ͽἀ-῿]+', (text or '').lower())
                if len(t) > 2}
    a, b = tokens(hint), tokens(property_name)
    return bool(a & b)


# ---------------------------------------------------------------------------
# 4. Orchestration - called from the upload view
# ---------------------------------------------------------------------------

def verify_expense_document(expense, file_bytes, media_type='application/pdf'):
    """Run extraction + comparison and write the verdict onto `expense`.

    Returns the verdict dict. NEVER raises: any problem becomes 'unverified',
    because a verification problem must not cost the user their upload.
    The caller is responsible for saving `expense`.
    """
    verdict = {
        'status': STATUS_UNVERIFIED,
        'notes': 'Verification did not run.',
        'invoice_total': None, 'invoice_date': None,
        'invoice_number': None, 'supplier': None, 'advisories': [],
    }
    raw = {}

    try:
        raw = extract_invoice(file_bytes, media_type)
        verdict = evaluate(
            expense_amount=expense.act_expense_amount,
            expense_date=expense.act_expense_date,
            expense_description=expense.act_expense_description,
            property_name=getattr(expense.prop, 'prop_name', None),
            extracted=raw,
        )
    except ExtractionUnavailable as exc:
        log.info('invoice verification unavailable for expense %s: %s',
                 getattr(expense, 'act_expense_id', '?'), exc)
        verdict['notes'] = 'Automatic checking was unavailable, so this document was not checked.'
    except Exception:                                           # noqa: BLE001
        log.exception('invoice verification failed for expense %s (upload was not affected)',
                      getattr(expense, 'act_expense_id', '?'))

    _apply(expense, verdict, raw)
    return verdict


def _apply(expense, verdict, raw):
    from django.utils import timezone
    _, model, _ = _api_config()

    expense.act_expense_verify_status = verdict.get('status', STATUS_UNVERIFIED)
    expense.act_expense_verify_checked_at = timezone.now()
    expense.act_expense_verify_total = verdict.get('invoice_total')
    expense.act_expense_verify_date = verdict.get('invoice_date')
    expense.act_expense_verify_number = (verdict.get('invoice_number') or '')[:60] or None
    expense.act_expense_verify_supplier = (verdict.get('supplier') or '')[:120] or None
    expense.act_expense_verify_model = ('%s/%s' % (model, PROMPT_VERSION))[:60]

    notes = [verdict.get('notes') or '']
    notes.extend(verdict.get('advisories') or [])
    expense.act_expense_verify_notes = '\n'.join(n for n in notes if n)[:2000]

    try:
        expense.act_expense_verify_raw = json.dumps(raw, ensure_ascii=False, default=str)[:20000]
    except Exception:                                           # noqa: BLE001
        expense.act_expense_verify_raw = None


def clear_verification(expense):
    """Reset the verdict - used when the document is deleted."""
    expense.act_expense_verify_status = STATUS_PENDING
    expense.act_expense_verify_checked_at = None
    expense.act_expense_verify_total = None
    expense.act_expense_verify_date = None
    expense.act_expense_verify_number = None
    expense.act_expense_verify_supplier = None
    expense.act_expense_verify_notes = None
    expense.act_expense_verify_raw = None
    expense.act_expense_verify_model = None


def is_enabled():
    """False when no API key is configured - the feature is then dormant and
    the system behaves exactly as it did before."""
    return bool(os.environ.get('ANTHROPIC_API_KEY'))
