"""
Standalone tests for the invoice-verification comparison logic.

No Django, no database, no network: `evaluate()` is a pure function, which is
exactly why it was written that way. Run from the project root:

    python test_invoice_verification.py
"""

import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, '.')
from pages.services import invoice_verification as iv   # noqa: E402

PASS, FAIL = [], []


def check(name, got, want):
    (PASS if got == want else FAIL).append((name, got, want))


def ev(extracted, amount='100.00', edate=date(2026, 7, 23),
       desc='ATOM disinfection', prop='Palikaridi'):
    return iv.evaluate(Decimal(amount) if amount is not None else None,
                       edate, desc, prop, extracted)


# net + VAT must equal payable_total: a MISMATCH is only allowed when the
# figures prove themselves arithmetically (see MIN_CONFIDENCE_TO_FLAG).
BASE = {
    'is_invoice': True, 'payable_total': 100.00,
    'net_amount': 84.03, 'vat_amount': 15.97, 'invoice_count': 1,
    'total_is_unambiguous': True,
    'currency': 'EUR', 'invoice_date': '2026-07-23', 'invoice_number': 'A-1',
    'supplier_name': 'ATOM Ltd', 'property_hint': None,
    'description_summary': None, 'confidence': 0.95,
}


def recon(total):
    """net/VAT at Cyprus 19% that add up to `total`, so a case can flag."""
    net = round(total / 1.19, 2)
    return {'payable_total': total, 'net_amount': net, 'vat_amount': round(total - net, 2)}


def d(**over):
    out = dict(BASE)
    out.update(over)
    return out


# --- the exact-match rule ---------------------------------------------------
check('exact match -> verified', ev(d())['status'], iv.STATUS_VERIFIED)
check('one cent over -> mismatch', ev(d(**recon(100.01)))['status'], iv.STATUS_MISMATCH)
check('one cent under -> mismatch', ev(d(**recon(99.99)))['status'], iv.STATUS_MISMATCH)
check('95.2 == 95.20', ev(d(payable_total=95.2), amount='95.20')['status'], iv.STATUS_VERIFIED)

# --- number formats real invoices use --------------------------------------
check('euro decimal comma "1.234,56"',
      ev(d(payable_total='1.234,56'), amount='1234.56')['status'], iv.STATUS_VERIFIED)
check('uk/us "1,234.56"',
      ev(d(payable_total='1,234.56'), amount='1234.56')['status'], iv.STATUS_VERIFIED)
check('bare comma decimal "95,20"',
      ev(d(payable_total='95,20'), amount='95.20')['status'], iv.STATUS_VERIFIED)
check('thousands comma only "1,234"',
      ev(d(payable_total='1,234'), amount='1234.00')['status'], iv.STATUS_VERIFIED)
check('currency symbol stripped',
      ev(d(payable_total='EUR 100,00'))['status'], iv.STATUS_VERIFIED)

# --- the gates: uncertainty must NEVER become a mismatch -------------------
check('ambiguous total -> unverified',
      ev(d(total_is_unambiguous=False, payable_total=120))['status'], iv.STATUS_UNVERIFIED)
check('low confidence -> unverified',
      ev(d(confidence=0.4, payable_total=120))['status'], iv.STATUS_UNVERIFIED)
check('no total -> unverified',
      ev(d(payable_total=None))['status'], iv.STATUS_UNVERIFIED)
check('unreadable garbage total -> unverified',
      ev(d(payable_total='n/a'))['status'], iv.STATUS_UNVERIFIED)
check('non-EUR -> unverified',
      ev(d(currency='GBP', payable_total=120))['status'], iv.STATUS_UNVERIFIED)
check('not an invoice -> not_invoice',
      ev(d(is_invoice=False, payable_total=120))['status'], iv.STATUS_NOT_INVOICE)
check('expense has no amount -> unverified',
      ev(d(), amount=None)['status'], iv.STATUS_UNVERIFIED)

# A wrong number that the model is sure about IS a mismatch - the gates must
# not be so wide that a real overbill slips through as "unverified".
check('confident wrong number still flags',
      ev(d(confidence=0.99, **recon(952.00)))['status'], iv.STATUS_MISMATCH)

# --- the two real failures found on Live, 16 Aug 2026 ----------------------
# #62: a handwritten ATOM invoice for EUR 35.70 was read as EUR 100.00 with
# high self-reported confidence. Nothing reconciled it, so it must not flag.
check('REGRESSION #62: unreconciled total never flags',
      ev(d(payable_total=100.00, net_amount=None, vat_amount=None),
         amount='35.70')['status'], iv.STATUS_UNVERIFIED)
check('REGRESSION #62: read correctly -> verified',
      ev(d(payable_total=35.70, net_amount=30.00, vat_amount=5.70),
         amount='35.70')['status'], iv.STATUS_VERIFIED)
# #55: labour invoice (95.20) and parts invoice (196.25) merged into one file.
check('REGRESSION #55: multi-invoice file -> unverified',
      ev(d(payable_total=95.20, net_amount=80.00, vat_amount=15.20, invoice_count=2),
         amount='196.25')['status'], iv.STATUS_UNVERIFIED)
# A genuine overbill that reconciles must still get through the new gates.
check('genuine overbill still flags',
      ev(d(**recon(150.00)), amount='100.00')['status'], iv.STATUS_MISMATCH)
check('reconciles but confidence 0.80 -> no flag',
      ev(d(confidence=0.80, **recon(150.00)), amount='100.00')['status'], iv.STATUS_UNVERIFIED)
# Split invoice survives the new gates.
check('split 744 = 3 x 248',
      ev(d(**recon(744.00)), amount='248.00')['status'], iv.STATUS_SPLIT)

# --- advisories: context only, never change the verdict --------------------
r = ev(d(invoice_date='2026-12-31'))
check('far-off date still verified', r['status'], iv.STATUS_VERIFIED)
check('far-off date raises an advisory', len(r['advisories']) >= 1, True)

r = ev(d(invoice_date='2026-07-25'))
check('nearby date raises no date advisory',
      any('days from the expense' in a for a in r['advisories']), False)

r = ev(d(property_hint='Pindarou 12, Nicosia'))
check('wrong property still verified', r['status'], iv.STATUS_VERIFIED)
check('wrong property raises an advisory',
      any('Pindarou' in a for a in r['advisories']), True)

r = ev(d(property_hint='Palikaridi Apartment 3'))
check('matching property raises no advisory',
      any('refers to' in a for a in r['advisories']), False)

r = ev(d(property_hint=None))
check('absent property is silent',
      any('refers to' in a for a in r['advisories']), False)

# --- extracted values are carried through ----------------------------------
r = ev(d(payable_total=100.00))
check('total carried', r['invoice_total'], Decimal('100.00'))
check('date parsed', r['invoice_date'], date(2026, 7, 23))
check('supplier carried', r['supplier'], 'ATOM Ltd')
check('number carried', r['invoice_number'], 'A-1')

# --- date parsing tolerance -------------------------------------------------
check('dd/mm/yyyy parsed', iv._to_date('23/07/2026'), date(2026, 7, 23))
check('dd.mm.yyyy parsed', iv._to_date('23.07.2026'), date(2026, 7, 23))
check('junk date -> None', iv._to_date('not a date'), None)

# --- extraction is fail-soft when no key is configured ---------------------
import os                                                        # noqa: E402
os.environ.pop('ANTHROPIC_API_KEY', None)
check('feature dormant without a key', iv.is_enabled(), False)
try:
    iv.extract_invoice(b'%PDF-1.4')
    check('extract raises without a key', False, True)
except iv.ExtractionUnavailable:
    check('extract raises without a key', True, True)


# --- report -----------------------------------------------------------------
for name, got, want in FAIL:
    print('FAIL  %-42s got %r, expected %r' % (name, got, want))
print('\n%d passed, %d failed' % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
