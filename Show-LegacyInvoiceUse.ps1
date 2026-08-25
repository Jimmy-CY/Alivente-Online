<#
.SYNOPSIS
    Is anything still using the legacy invoice helpers? Read-only, LIVE.

.DESCRIPTION
    Three legacy call sites share one project-root module, open_invoices.py:

      1. Administration > Generate Invoices   -> create_invoices()
      2. Administration > Email Unpaid Report -> open_invoices()
      3. Invoices page  > open_invoices view  -> open_invoices()

    (2) and (3) write their PDF to a hard-coded Windows path from a previous
    machine. (1) inserts collection invoices WITHOUT an invoice_amount, which
    the five-minute cron always sets. This script gathers the evidence for
    whether any of them has actually run, rather than reasoning about it:

      A. CAN THE REPORT WRITE AT ALL?
         Resolves the hard-coded path the way the container would and reports
         whether it exists. On Linux "C:/Users/..." has no leading slash, so it
         is a RELATIVE path - it would land under the working directory.

      B. WHAT THE LOGS SAY
         Greps the Django log files for those views, for fpdf, and for the
         Windows path. Read the caveat it prints: the container filesystem is
         ephemeral, so these files only cover the time since the last deploy.

      C. THE BUTTON'S FINGERPRINT  (the strongest evidence)
         A cron-created collection invoice has an invoice_amount. One created
         by Generate Invoices does NOT. Counting invoices with a null amount -
         and, crucially, only those DATED AFTER amounts started being written -
         says whether that button has ever been pressed in anger.

      D. SUMMARY

    Read-only: SELECTs and file reads only. Nothing is written on Live.

.PARAMETER Detail
    Print every matching log line and every suspect invoice, not just counts.

.PARAMETER Service
    Railway service name, if `railway link` points somewhere else.

.EXAMPLE
    .\Show-LegacyInvoiceUse.ps1
    .\Show-LegacyInvoiceUse.ps1 -Detail
#>

[CmdletBinding()]
param(
    [switch] $Detail,
    [string] $Service = ""
)

$ErrorActionPreference = 'Continue'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$python = @'
import os, re, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from datetime import datetime
from pages.models import invoices as Invoice

DETAIL = __DETAIL__
BAR = '=' * 100

# The literal string in open_invoices.open_invoices(). Note the absence of a
# leading slash: on Linux this is a RELATIVE path, so it resolves under the
# process working directory rather than at the root.
LEGACY_PATH = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"

# ------------------------------------------------------------------ SECTION A
print('')
print(BAR)
print('A. THE REPORT FUNCTION - CAN IT WRITE AT ALL?')
print(BAR)
print('open_invoices.open_invoices() ends with:')
print('    pdf.output("%s" + "Open Invoices Report (<date>).pdf")' % LEGACY_PATH)
print('')
print('  working directory : %s' % os.getcwd())
print('  path is absolute  : %s' % os.path.isabs(LEGACY_PATH))
print('  would resolve to  : %s' % os.path.abspath(LEGACY_PATH))
print('')

exists = os.path.isdir(LEGACY_PATH)
print('  that directory exists : %s' % ('YES' if exists else 'NO'))
if exists:
    try:
        files = sorted(os.listdir(LEGACY_PATH))
        print('  it holds %d file(s)%s'
              % (len(files), (': ' + ', '.join(files[:5])) if files else ''))
        print('')
        print('  >> The report COULD have written here. Any PDFs above are')
        print('     evidence it ran. Check their dates.')
    except OSError as exc:
        print('  (could not list it: %s)' % exc)
else:
    # Report how far up the chain does exist, so the failure is precise rather
    # than merely asserted.
    parts, walked = LEGACY_PATH.strip('/').split('/'), ''
    deepest = '(nothing - not even the first segment)'
    for p in parts:
        walked = os.path.join(walked, p) if walked else p
        if os.path.isdir(walked):
            deepest = walked
        else:
            break
    print('  deepest existing part : %s' % deepest)
    print('')
    print('  >> fpdf opens this path for writing WITHOUT creating parents, so')
    print('     the call raises FileNotFoundError. Both the Email Unpaid Report')
    print('     button and the Invoices open_invoices view therefore 500 on Live')
    print('     - they cannot have produced a report from this container.')

print('')
print('  Two more desktop-era dependencies in the same path:')
print('    pdf_display.py -> webbrowser.open(...)   opens a browser ON THE SERVER')
print('    the rep_output "Display" branch is meaningless headless.')

# ------------------------------------------------------------------ SECTION B
print('')
print(BAR)
print('B. WHAT THE LOGS SAY')
print(BAR)

LOGS = ['middleware_errors.log', 'lease_renewal_check.log',
        'database_connections.log']
PATTERNS = [
    ('open_invoices', 'the report helper or its view'),
    ('admin_unpaid', 'the Email Unpaid Report button'),
    ('admin_invoices', 'the Generate Invoices button'),
    ('create_invoices', 'either invoice-creation path'),
    ('DemetrisManias', 'the hard-coded Windows path'),
    ('fpdf', 'the PDF library the report uses'),
    ('FileNotFoundError', 'the error a bad output path raises'),
]
_TS = re.compile(r'(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})')

any_log = False
for name in LOGS:
    if not os.path.exists(name):
        print('')
        print('  %-28s NOT PRESENT' % name)
        continue
    any_log = True
    size = os.path.getsize(name)
    mtime = datetime.fromtimestamp(os.path.getmtime(name))
    try:
        with open(name, encoding='utf-8', errors='replace') as fh:
            lines = fh.readlines()
    except OSError as exc:
        print('  %-28s could not be read: %s' % (name, exc))
        continue

    stamps = [m.group(1) for m in (_TS.search(l) for l in lines) if m]
    print('')
    print('  %-28s %8d bytes, %6d lines, last written %s'
          % (name, size, len(lines), mtime.strftime('%Y-%m-%d %H:%M')))
    if stamps:
        print('  %-28s covers %s .. %s' % ('', stamps[0], stamps[-1]))

    for pat, what in PATTERNS:
        hits = [l.rstrip() for l in lines if pat.lower() in l.lower()]
        if not hits:
            continue
        print('      %-18s %4d line(s)   (%s)' % (pat, len(hits), what))
        show = hits if DETAIL else hits[-3:]
        for h in show:
            print('        | %s' % h[:150])
        if not DETAIL and len(hits) > 3:
            print('        | ... %d more (re-run with -Detail)' % (len(hits) - 3))

print('')
print('  !! READ THIS BEFORE TRUSTING A CLEAN RESULT !!')
print('  The log handlers use RELATIVE filenames, so they live in the container')
print('  working directory - and that filesystem is REBUILT ON EVERY DEPLOY.')
print('  These files only cover the window printed above. Silence here means')
print('  "not since the last deploy", NOT "never". Section C is the durable')
print('  evidence; this section can only confirm, never exonerate.')
if not any_log:
    print('')
    print('  (No log files at all - most likely a fresh deploy.)')

# ------------------------------------------------------------------ SECTION C
print('')
print(BAR)
print("C. THE GENERATE INVOICES FINGERPRINT  (survives redeploys)")
print(BAR)
print('The cron sets invoice_amount when it creates a collection invoice:')
print('    _collection_amount(rent, levies, bill_levies, physical_invoice_required)')
print('The legacy button does not - its INSERT names only')
print('    (tenant_id, invoice_date, invoice_paid)')
print('So a null amount is that button\'s signature - EXCEPT on invoices old')
print('enough to predate the column being populated at all.')

rows = list(Invoice.objects.select_related('tenant')
            .values('invoice_id', 'invoice_date', 'invoice_amount',
                    'tenant__tenant_name'))
total = len(rows)
priced = [r for r in rows if r['invoice_amount'] is not None
          and r['invoice_amount'] != 0]
nulls = [r for r in rows if r['invoice_amount'] is None]
zeros = [r for r in rows if r['invoice_amount'] is not None
         and r['invoice_amount'] == 0]

print('')
print('  %6d invoice(s) in total' % total)
print('  %6d with an amount' % len(priced))
print('  %6d with NO amount (null)' % len(nulls))
print('  %6d with an amount of exactly 0' % len(zeros))

dated_priced = [r['invoice_date'] for r in priced if r['invoice_date']]
cutover = min(dated_priced) if dated_priced else None

if cutover is None:
    print('')
    print('  >> No invoice anywhere carries an amount, so this test cannot')
    print('     separate the button from the column\'s own history. Inconclusive.')
else:
    print('')
    print('  Amounts first appear on an invoice dated %s.' % cutover)
    print('  Anything null BEFORE that is explained by the column\'s history.')
    print('  Anything null ON OR AFTER it is not.')

    suspect = [r for r in (nulls + zeros)
               if r['invoice_date'] and r['invoice_date'] >= cutover]
    print('')
    if not suspect:
        print('  >> ZERO unexplained invoices. Every invoice created since')
        print('     amounts began carries one, which is what the cron does and')
        print('     what the button does NOT. On this evidence the Generate')
        print('     Invoices button has never created a row that survives.')
    else:
        print('  >> %d invoice(s) dated on or after %s carry no amount.'
              % (len(suspect), cutover))
        print('     Each is either a Generate Invoices row or a manual edit.')
        by_month = {}
        for r in suspect:
            k = r['invoice_date'].strftime('%Y-%m')
            by_month[k] = by_month.get(k, 0) + 1
        print('')
        print('     %-10s %s' % ('MONTH', 'COUNT'))
        for k in sorted(by_month):
            print('     %-10s %d' % (k, by_month[k]))
        if DETAIL:
            print('')
            print('     %-9s %-12s %-28s %s'
                  % ('ID', 'DATE', 'TENANT', 'AMOUNT'))
            for r in sorted(suspect, key=lambda r: r['invoice_date']):
                print('     %-9s %-12s %-28s %s'
                      % (r['invoice_id'], r['invoice_date'],
                         (r['tenant__tenant_name'] or '')[:28],
                         r['invoice_amount']))
        else:
            print('')
            print('     (-Detail lists them individually)')

# This month specifically: the cron should already have covered it.
from datetime import date as _d
_t = _d.today()
this_month = [r for r in rows if r['invoice_date']
              and r['invoice_date'].year == _t.year
              and r['invoice_date'].month == _t.month]
tm_priced = [r for r in this_month if r['invoice_amount']]
print('')
print('  This month (%s): %d invoice(s), %d with an amount.'
      % (_t.strftime('%B %Y'), len(this_month), len(tm_priced)))
if this_month and len(tm_priced) == len(this_month):
    print('  >> All priced, so the cron got here first - which is exactly why')
    print('     pressing the button would report "they already exist".')

# ------------------------------------------------------------------ SECTION D
print('')
print(BAR)
print('D. SUMMARY')
print(BAR)
print('  report path reachable on Live        : %s' % ('YES' if exists else 'NO'))
print('  invoices with no amount, total       : %d' % len(nulls))
print('  ... of those, unexplained by history : %s'
      % (len([r for r in (nulls + zeros)
              if cutover and r['invoice_date'] and r['invoice_date'] >= cutover])
         if cutover else 'n/a'))
print('')
print('  Section A is a fact about this container and does not expire.')
print('  Section B expires on every deploy.')
print('  Section C is in the database, so it is the one to decide on.')
print(BAR)
print('')
'@

$python = $python.Replace('__DETAIL__', $(if ($Detail) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/leginv.py && python /tmp/leginv.py; rc=`$?; rm -f /tmp/leginv.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Checking the legacy invoice helpers on Live (read-only)" -ForegroundColor Cyan
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0) {
    Write-Host "==> Done. Nothing on Live was changed." -ForegroundColor Cyan
} else {
    Write-Host "!!  railway ssh exited with code $code" -ForegroundColor Red
    Write-Host "    Try:  railway link    (or add -Service <name>)"
}
exit $code
