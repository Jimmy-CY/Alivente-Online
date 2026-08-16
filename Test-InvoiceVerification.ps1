<#
.SYNOPSIS
    Read-only accuracy trial of invoice verification against LIVE data.

.DESCRIPTION
    Answers one question before you commit to the feature: if invoice checking
    had been switched on, what would it have concluded about your real invoices?

    Nothing is deployed and nothing is changed:
      * no git push, no migration, no new column
      * no database row is written, no email is sent
      * a temporary script is piped into the Railway container, run once,
        and deleted

    It reads your existing act_expense rows, opens each attached PDF from the
    Railway volume, sends it to the Anthropic API using the ANTHROPIC_API_KEY
    already set in the container, and prints what the verdict would have been.

.PARAMETER Limit
    How many expenses to check. Default 20.

.PARAMETER Property
    Only check one property (partial name match, case-insensitive).

.PARAMETER DryRun
    List what WOULD be checked and stop. Makes no API calls, costs nothing.

.PARAMETER Service
    Railway service name, if your project has more than one.

.PARAMETER Full
    Print the full extraction payload for each document.

.EXAMPLE
    .\Test-InvoiceVerification.ps1 -DryRun
    .\Test-InvoiceVerification.ps1 -Limit 20
    .\Test-InvoiceVerification.ps1 -Limit 5 -Property "Palikaridi" -Full

.NOTES
    Cost: roughly USD 0.004 per invoice, so about 8 cents for 20.
    Run from the project root (where manage.py lives).
#>

[CmdletBinding()]
param(
    [int]    $Limit = 20,
    [string] $Property = "",
    [switch] $DryRun,
    [string] $Service = "",
    [switch] $Full
)

$ErrorActionPreference = 'Stop'

function Write-Step { param($m) Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Warn { param($m) Write-Host "!!  $m" -ForegroundColor Yellow }
function Write-Err  { param($m) Write-Host "!!  $m" -ForegroundColor Red }

# --------------------------------------------------------------- checks ----
Write-Step "Checking prerequisites"

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Err "The Railway CLI is not on your PATH."
    Write-Host "    Install it with:  npm i -g @railway/cli"
    Write-Host "    Then:             railway login"
    exit 1
}

if (-not (Test-Path ".\manage.py")) {
    Write-Warn "manage.py not found here - run this from the project root."
    Write-Host "    Expected: C:\Users\demet\OneDrive\Desktop\PythonApps\Alivente-Online"
    exit 1
}

Write-Host "    Railway CLI found." -ForegroundColor DarkGray

# ------------------------------------------------- the throwaway script ----
# Single-quoted here-string: PowerShell does NOT touch $ or backticks inside.
$python = @'
# Temporary, read-only. Deleted by the wrapper when it finishes.
import base64, json, os, re, sys, urllib.request
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

LIMIT   = __LIMIT__
PROPERTY= __PROPERTY__
DRYRUN  = __DRYRUN__
FULL    = __FULL__

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()
from pages.models import act_expense

BAR = '=' * 74
PROMPT = """You are reading a supplier invoice for a property-management company.

Return ONLY a JSON object, no prose and no markdown fence, with exactly these keys:
{"is_invoice": true|false, "payable_total": number|null, "net_amount": number|null,
 "vat_amount": number|null, "invoice_count": integer, "total_is_unambiguous": true|false,
 "currency": "EUR"|null, "invoice_date": "YYYY-MM-DD"|null, "invoice_number": string|null,
 "supplier_name": string|null, "property_hint": string|null,
 "description_summary": string|null, "confidence": 0.0-1.0}

- "payable_total" is the single amount the customer must actually PAY: the final
  gross total after any discount, INCLUDING VAT when VAT is charged. It is NOT
  the net/subtotal and NOT the VAT line on its own.
- "total_is_unambiguous" must be false whenever you are not certain which figure
  is the payable total - net/VAT/gross all shown with an unclear layout, an
  illegible or cut-off scan, competing totals, or a running balance rather than
  an amount due. When in doubt say false; that is a good answer.
- "is_invoice" is false for quotations, estimates, proformas, delivery notes,
  statements, payment receipts, or anything that is not a bill.
- "net_amount" and "vat_amount" are the figures that ADD UP to payable_total.
  Report them whenever printed; use null if they are not on the document. Never
  invent them - they exist so your arithmetic can be checked.
- "invoice_count": how many SEPARATE invoices this file contains. Files are
  often several documents merged together (labour from one supplier, parts from
  another). If it is more than 1, also set total_is_unambiguous false.
- "property_hint": any address or property named on the invoice; null if none.
- "description_summary": max 10 words, in English even for a Greek invoice.

HOW THESE PARTICULAR INVOICES ARE PRINTED - read this carefully:

- The page MAY BE ROTATED 90, 180 or 270 degrees, because invoices are often
  scanned or photographed sideways. Mentally rotate the page and read it in
  whatever orientation makes sense. A rotated page is normal, not a reason to
  give up.
- Amounts are often HANDWRITTEN on a pre-printed pad.
- Amounts are often printed in TWO SEPARATE ADJACENT COLUMNS, one headed
  euro / EUR / EUR and the next headed cent / cents. When you see this, JOIN
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


def to_decimal(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        try: return Decimal(str(v))
        except InvalidOperation: return None
    t = re.sub(r'[^\d,.\-]', '', str(v).strip())
    if not t: return None
    if ',' in t and '.' in t:
        t = (t.replace('.', '').replace(',', '.') if t.rfind(',') > t.rfind('.')
             else t.replace(',', ''))
    elif ',' in t:
        t = t.replace(',', '.') if re.search(r',\d{1,2}$', t) else t.replace(',', '')
    try: return Decimal(t)
    except InvalidOperation: return None


def to_date(v):
    if not v: return None
    t = str(v).strip()[:10]
    for f in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'):
        try: return datetime.strptime(t, f).date()
        except ValueError: pass
    return None


def sniff_media_type(blob, name=''):
    """Stored documents are not all PDFs - older ones were saved as .jpg/.png
    before the auto-convert-to-PDF path existed. Detect from magic bytes."""
    if blob[:5] == b'%PDF-':
        return 'application/pdf'
    if blob[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if blob[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if blob[:4] == b'RIFF' and blob[8:12] == b'WEBP':
        return 'image/webp'
    if blob[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    lower = (name or '').lower()
    for ext, mt in (('.pdf', 'application/pdf'), ('.jpg', 'image/jpeg'),
                    ('.jpeg', 'image/jpeg'), ('.png', 'image/png')):
        if lower.endswith(ext):
            return mt
    return None


def extract(blob, media_type='application/pdf'):
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise RuntimeError('ANTHROPIC_API_KEY is not set in this container')
    if len(blob) > 6 * 1024 * 1024:
        raise RuntimeError('document too large (%.1f MB)' % (len(blob) / 1048576.0))
    body = json.dumps({
        'model': os.environ.get('INVOICE_VERIFY_MODEL', 'claude-haiku-4-5'),
        'max_tokens': 700,
        'messages': [{'role': 'user', 'content': [
            ({'type': 'document', 'source': {'type': 'base64',
              'media_type': 'application/pdf',
              'data': base64.standard_b64encode(blob).decode('ascii')}}
             if media_type == 'application/pdf' else
             {'type': 'image', 'source': {'type': 'base64',
              'media_type': media_type,
              'data': base64.standard_b64encode(blob).decode('ascii')}}),
            {'type': 'text', 'text': PROMPT}]}],
    }).encode('utf-8')
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body,
        headers={'x-api-key': key, 'anthropic-version': '2023-06-01',
                 'content-type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode('utf-8'))
    txt = ''.join(b.get('text', '') for b in (data.get('content') or [])
                  if b.get('type') == 'text').strip()
    if txt.startswith('```'):
        txt = re.sub(r'^```[a-zA-Z]*\s*', '', txt); txt = re.sub(r'\s*```$', '', txt)
    return json.loads(txt)


def reconciles(total, net, vat):
    """net + VAT == total. An objective proof the figures were read correctly -
    unlike the model's own confidence score, which can be confidently wrong."""
    if total is None or net is None or vat is None:
        return False
    return abs((net + vat) - total) <= Decimal('0.02')


def verdict(exp, x):
    """EXACT match on the amount. Anything uncertain -> unverified, never mismatch."""
    notes = []
    total = to_decimal(x.get('payable_total'))
    net = to_decimal(x.get('net_amount'))
    vat = to_decimal(x.get('vat_amount'))
    try:
        count = int(x.get('invoice_count') or 1)
    except (TypeError, ValueError):
        count = 1
    if x.get('is_invoice') is False:
        return 'not_invoice', total, 'Not an invoice - no check made.', notes
    if total is None:
        return 'unverified', None, 'No payable total could be read.', notes
    if count > 1:
        return 'unverified', total, ('File contains %d separate invoices - no single payable '
                                     'total. Check by eye.' % count), notes
    if not x.get('total_is_unambiguous'):
        return 'unverified', total, 'Payable total is ambiguous (read %s) - check by eye.' % total, notes
    try: conf = float(x.get('confidence') or 0)
    except (TypeError, ValueError): conf = 0.0
    if conf < 0.75:
        return 'unverified', total, 'Confidence %.2f is too low to judge.' % conf, notes
    cur = (x.get('currency') or '').upper()
    if cur and cur != 'EUR':
        return 'unverified', total, 'Invoice is in %s, not euro.' % cur, notes

    idate = to_date(x.get('invoice_date'))
    if idate and exp.act_expense_date:
        gap = (idate - exp.act_expense_date).days
        if abs(gap) > 90:
            notes.append('Invoice dated %s, %d days from the expense date.' % (idate, abs(gap)))
    hint = (x.get('property_hint') or '').strip()
    if hint:
        tok = lambda s: {t for t in re.split(r'[^0-9A-Za-z\u0370-\u03ff\u1f00-\u1fff]+',
                                             (s or '').lower()) if len(t) > 2}
        if not (tok(hint) & tok(exp.prop.prop_name)):
            notes.append('Invoice refers to "%s"; expense is on %s.' % (hint, exp.prop.prop_name))
    summ = (x.get('description_summary') or '').strip()
    if summ:
        notes.append('Invoice is for "%s"; expense says "%s".' % (summ, exp.act_expense_description))

    approved = to_decimal(exp.act_expense_amount)
    if approved is not None and total == approved:
        return 'verified', total, 'Invoice total %s matches the approved amount.' % total, notes
    if conf < 0.90 or not reconciles(total, net, vat):
        why = ('figures do not add up (net %s + VAT %s != total %s)' % (net, vat, total)
               if not reconciles(total, net, vat) else 'confidence %.2f below the 0.90 bar to flag' % conf)
        return 'unverified', total, ('Reads %s vs approved %s, but %s - NOT flagged.'
                                     % (total, approved, why)), notes
    if approved and approved > 0 and total > approved:
        ratio = total / approved
        n = int(ratio.to_integral_value())
        if 2 <= n <= 12 and abs(ratio - n) <= Decimal('0.005'):
            return 'split', total, ('Invoice total %s is exactly %d x approved %s - one invoice '
                                    'covering %d expenses, not a mismatch.' % (total, n, approved, n)), notes
    diff = (total - approved) if approved is not None else None
    return 'mismatch', total, ('Invoice total %s does NOT match approved %s (difference %s).'
                               % (total, approved, diff)), notes


qs = (act_expense.objects.exclude(act_expense_document='')
      .exclude(act_expense_document=None).select_related('prop')
      .order_by('-act_expense_date', '-act_expense_id'))
if PROPERTY:
    qs = qs.filter(prop__prop_name__icontains=PROPERTY)
rows = list(qs[:LIMIT])

print(BAR)
print('INVOICE VERIFICATION - READ-ONLY TRIAL ON LIVE DATA')
print('%d expense(s) with an attached document. Nothing will be written.' % len(rows))
if not os.environ.get('ANTHROPIC_API_KEY'):
    print('WARNING: ANTHROPIC_API_KEY is not set in this container.')
print(BAR)

tally = {}
for i, exp in enumerate(rows, 1):
    name = (exp.act_expense_document.name or '').split('/')[-1]
    print('')
    print('[%d/%d] expense #%s   %s   %s' % (i, len(rows), exp.act_expense_id,
                                             exp.act_expense_date, exp.prop.prop_name))
    print('   description : %s' % exp.act_expense_description)
    print('   approved    : EUR %s   (approved=%s, paid=%s)' % (
        exp.act_expense_amount, exp.act_expense_approved, exp.act_expense_paid))
    print('   document    : %s' % name)
    if DRYRUN:
        tally['dry-run'] = tally.get('dry-run', 0) + 1
        continue
    try:
        exp.act_expense_document.open('rb'); blob = exp.act_expense_document.read()
        exp.act_expense_document.close()
    except Exception as e:
        print('   FILE UNREADABLE: %s' % e)
        tally['file error'] = tally.get('file error', 0) + 1
        continue
    mt = sniff_media_type(blob, name)
    if mt is None:
        print('   SKIPPED     : not a PDF or image (%s) - cannot be read' % name.split('.')[-1])
        tally['unsupported'] = tally.get('unsupported', 0) + 1
        continue
    if mt != 'application/pdf':
        print('   file type   : %s' % mt)
    try:
        x = extract(blob, mt)
    except Exception as e:
        print('   EXTRACTION FAILED: %s' % e)
        tally['unverified'] = tally.get('unverified', 0) + 1
        continue
    st, total, msg, notes = verdict(exp, x)
    tally[st] = tally.get(st, 0) + 1
    mark = {'verified': 'OK  ', 'mismatch': 'FLAG', 'unverified': '??  ',
            'not_invoice': '--  ', 'split': 'SPLT'}.get(st, '    ')
    print('   VERDICT     : %s %s' % (mark, st.upper()))
    print('   invoice tot : %s' % (total if total is not None else '(not read)'))
    print('   supplier    : %s' % (x.get('supplier_name') or '(not read)'))
    print('   %s' % msg)
    for n in notes:
        print('   note: %s' % n)
    if FULL:
        print('   raw: %r' % (x,))

print('')
print(BAR)
print('SUMMARY')
for k in ('verified', 'split', 'mismatch', 'unverified', 'not_invoice',
          'unsupported', 'file error', 'dry-run'):
    if tally.get(k):
        print('   %-12s %d' % (k, tally[k]))
print('')
print('Judge it on two questions:')
print('  1. Is every FLAG a real difference?   (false alarms destroy trust)')
print('  2. Is the ?? rate low enough to save you work?  (that is the whole point)')
print(BAR)
'@

# --------------------------------------------------------- parameterise ----
$python = $python.Replace('__LIMIT__',    "$Limit")
$python = $python.Replace('__PROPERTY__', "'" + ($Property -replace "'", "''") + "'")
$python = $python.Replace('__DRYRUN__',   $(if ($DryRun) { 'True' } else { 'False' }))
$python = $python.Replace('__FULL__',     $(if ($Full)   { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
Write-Host "    Script prepared ($([Math]::Round($b64.Length/1KB,1)) KB encoded)." -ForegroundColor DarkGray

if ($DryRun) {
    Write-Step "DRY RUN - listing only, no API calls, no cost"
} else {
    $cost = [Math]::Round($Limit * 0.004, 2)
    Write-Step "Checking up to $Limit invoice(s) on LIVE - estimated cost about USD $cost"
    Write-Host "    Nothing is written. No migration. No deploy." -ForegroundColor DarkGray
}

# ------------------------------------------------------------------ run ----
$remote = "echo '$b64' | base64 -d > /tmp/iv_trial.py && python /tmp/iv_trial.py; rc=`$?; rm -f /tmp/iv_trial.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Step "Connecting to Railway"
Write-Host ""

& railway @railwayArgs
$code = $LASTEXITCODE

Write-Host ""
if ($code -eq 0) {
    Write-Step "Done. Nothing on Live was changed."
} else {
    Write-Err "railway ssh exited with code $code."
    Write-Host "    Common causes:"
    Write-Host "      * not linked to the project   ->  railway link"
    Write-Host "      * more than one service       ->  re-run with -Service <name>"
    Write-Host "      * not logged in               ->  railway login"
}
exit $code
