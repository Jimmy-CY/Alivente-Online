<#
.SYNOPSIS
    Repair the Company Tax budget history so 2024-2027 report correctly.
    DRY RUN BY DEFAULT.

.DESCRIPTION
    Two problems, one cause. The 2027 provisional-tax change was saved on
    5 Aug 2026 and stamped with that date, because the budget edit form has no
    effective-date field. That single snapshot is the ONLY history the line has,
    so:

      2024 / 2025   no snapshot in range -> falls back to the LIVE row, showing
                    today's EUR 6,600 for years that were EUR 7,000
      2026          snapshot exists but is dated August, so Jan-Jul resolve to
                    nothing and Aug-Dec resolve to the snapshot's empty months.
                    Total zero -> the P&L drops the row entirely
      2027          correct

    This script makes two changes:

      STEP 1  Redate the ten 5-Aug-2026 snapshots to 2026-07-01 - the JULY 2026
              payment is the first one at the reduced rate, and it continues at
              that rate until changed again.
      STEP 2  Insert ten BASELINE snapshots dated 2000-01-01 holding the old
              EUR 7,000 figures, so EVERY period before the change resolves to
              the old rate.

              The date is deliberately far back. A baseline is not a statement
              about a particular year - it says "this is what the figure was
              until it changed". Date it at 2024 and 2023 falls outside the
              resolver's range, the source drops out of the result, and the
              caller falls back to the LIVE row - which holds today's figure.
              Every year earlier than the oldest snapshot silently shows the
              CURRENT rate. Dating it far enough back removes that window.

    The result:

      everything before Jul 2026    EUR 3,500 + EUR 3,500  = 7,000
      Jan 2026                      EUR 3,500  (old rate, from the baseline)
      Jul 2026 onwards              EUR 3,300  (new rate, and it stays there
                                                until something changes it)
      2026 total                    EUR 6,800  - a blend, not 7,000 or 6,600

    A calendar year is not the unit of change here; the effective date is. Any
    year the rate changes mid-way will read as a blend, and should.

    The EUR 7,000 was never recorded anywhere - not in history, not in
    act_expense - so the baseline is derived: each property's live figure
    scaled by 7000/6600, keeping the existing relative weights and the existing
    month pattern. The month shape is READ FROM THE DATA, not assumed, and the
    total is forced to exactly 7000.00 with any rounding residual applied to the
    largest cell.

    Idempotent. Re-running after a successful apply changes nothing: the redate
    skips rows already at 2027-01-01, and the baseline skips if one exists.

.PARAMETER Apply
    Actually write. Without this it is a dry run and nothing is changed.

.PARAMETER OldTotal
    The annual figure to restore. Default 7000.

.PARAMETER BaselineDate
    Effective date for the baseline snapshot. Default 2000-01-01, deliberately
    far back so no year can fall outside it and retro-show today's figure.

.PARAMETER NewDate
    Effective date the reduced rate should carry. Default 2026-07-01 - the
    July 2026 payment is the first at EUR 3,300, and it continues from there.

.EXAMPLE
    .\Repair-CompanyTaxHistory.ps1
    .\Repair-CompanyTaxHistory.ps1 -Apply
#>

[CmdletBinding()]
param(
    [switch] $Apply,
    [decimal] $OldTotal = 7000,
    [string] $BaselineDate = "2000-01-01",
    [string] $NewDate = "2026-07-01",
    [string] $Line = "Company Tax",
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}
foreach ($d in @($BaselineDate, $NewDate)) {
    if ($d -notmatch '^\d{4}-\d{2}-\d{2}$') {
        Write-Host "!!  Dates must be YYYY-MM-DD (got '$d')" -ForegroundColor Red
        exit 1
    }
}

$python = @'
import os, sys
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from django.db import transaction
from pages.models import (expense, expense_line_types, FinancialFigureHistory,
                          resolve_year_months_bulk)

LINE      = '__LINE__'
OLD_TOTAL = Decimal('__OLDTOTAL__')
BASELINE  = datetime.strptime('__BASELINE__', '%Y-%m-%d').date()
NEWDATE   = datetime.strptime('__NEWDATE__', '%Y-%m-%d').date()
APPLY     = __APPLY__

MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BAR = '=' * 100
CENT = Decimal('0.01')


def q(v):
    return (v or Decimal('0')).quantize(CENT, rounding=ROUND_HALF_UP)


print(BAR)
print('REPAIR COMPANY TAX HISTORY')
print('  restore annual total : EUR %s' % OLD_TOTAL)
print('  baseline effective   : %s' % BASELINE)
print('  redate change to     : %s' % NEWDATE)
print('  mode                 : %s' % ('APPLY - WILL WRITE' if APPLY else 'DRY RUN - nothing written'))
print(BAR)

lts = list(expense_line_types.objects.filter(expense_line_types_name__icontains=LINE))
if not lts:
    print('! No expense_line_types matched %r - aborting.' % LINE)
    raise SystemExit(1)

rows = list(expense.objects.select_related('prop', 'expense_line_types')
            .filter(expense_line_types__in=lts).order_by('prop__prop_name'))
if not rows:
    print('! No expense rows use that line type - aborting.')
    raise SystemExit(1)

src_ids = [r.expense_id for r in rows]

# ---------------------------------------------------------------- STEP 1
print('')
print('STEP 1 - redate the existing snapshots to %s' % NEWDATE)
print('-' * 100)
existing = list(FinancialFigureHistory.objects
                .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                        source_pk__in=src_ids)
                .exclude(source='baseline')
                .order_by('source_pk'))
if not existing:
    print('  No non-baseline snapshots found. Nothing to redate.')
to_redate = [h for h in existing if h.effective_date != NEWDATE]
for h in existing:
    mark = 'REDATE' if h.effective_date != NEWDATE else 'already correct'
    print('  #%-5s %-24s %s -> %s   [%s]'
          % (h.source_pk, (h.prop.prop_name or '')[:24], h.effective_date,
             NEWDATE, mark))
print('  %d row(s) to redate.' % len(to_redate))

# ---------------------------------------------------------------- STEP 2
print('')
print('STEP 2 - baseline snapshot at %s holding the old EUR %s' % (BASELINE, OLD_TOTAL))
print('-' * 100)

base_rows = list(FinancialFigureHistory.objects
                 .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                         source_pk__in=src_ids, source='baseline'))
already = set(b.source_pk for b in base_rows)
# A baseline at the WRONG date is corrected, not skipped. Skipping would leave
# an earlier run's too-recent date in place, and every year before it would go
# on retro-showing the current figure.
misdated = [b for b in base_rows if b.effective_date != BASELINE]
if already:
    print('  %d source(s) already have a baseline (%d at the wrong date, '
          'which will be corrected).' % (len(already), len(misdated)))
    for b in misdated:
        print('    #%-5s %-24s %s -> %s'
              % (b.source_pk, (b.prop.prop_name or '')[:24],
                 b.effective_date, BASELINE))

# Live total, and the month shape, read from the data rather than assumed.
live_total = Decimal('0')
for r in rows:
    for m in MONTHS:
        live_total += (getattr(r, 'expense_' + m) or Decimal('0'))

if live_total == 0:
    print('! Live total is zero - cannot scale. Aborting.')
    raise SystemExit(1)

scale = OLD_TOTAL / live_total
print('  live total EUR %s  ->  scale factor %s' % (q(live_total), round(scale, 6)))
print('')

plan = []          # (row, {month: Decimal})
running = Decimal('0')
biggest = None     # (row, month, value) - largest cell, absorbs the residual
for r in rows:
    cells = {}
    for m in MONTHS:
        v = getattr(r, 'expense_' + m)
        if v in (None, 0, Decimal('0')):
            continue
        nv = q(Decimal(v) * scale)
        cells[m] = nv
        running += nv
        if biggest is None or nv > biggest[2]:
            biggest = (r.expense_id, m, nv)
    if cells:
        plan.append((r, cells))

residual = q(OLD_TOTAL - running)
if residual != 0 and biggest is not None:
    for r, cells in plan:
        if r.expense_id == biggest[0] and biggest[1] in cells:
            cells[biggest[1]] = q(cells[biggest[1]] + residual)
            print('  rounding residual EUR %s applied to #%s %s'
                  % (residual, biggest[0], biggest[1].upper()))
            break

print('%-6s %-24s %s' % ('exp_id', 'PROPERTY', 'BASELINE CELLS'))
check = Decimal('0')
for r, cells in plan:
    check += sum(cells.values())
    shown = '  '.join('%s=%s' % (m.upper(), cells[m]) for m in MONTHS if m in cells)
    skip = '   [baseline exists - values kept]' if r.expense_id in already else ''
    print('%-6s %-24s %s%s'
          % (r.expense_id, (r.prop.prop_name or '')[:24], shown, skip))
print('-' * 100)
print('  BASELINE TOTAL: EUR %s   (target EUR %s)  %s'
      % (q(check), OLD_TOTAL, 'OK' if q(check) == OLD_TOTAL else '!! MISMATCH'))
if q(check) != OLD_TOTAL:
    print('! Baseline does not reconcile to the target - aborting, nothing written.')
    raise SystemExit(1)

# ---------------------------------------------------------------- WRITE
if not APPLY:
    print('')
    print('DRY RUN - nothing was written. Re-run with -Apply to commit.')
else:
    print('')
    print('APPLYING...')
    with transaction.atomic():
        n = (FinancialFigureHistory.objects
             .filter(pk__in=[h.pk for h in to_redate])
             .update(effective_date=NEWDATE))
        print('  redated %d snapshot(s)' % n)

        if misdated:
            n = (FinancialFigureHistory.objects
                 .filter(pk__in=[b.pk for b in misdated])
                 .update(effective_date=BASELINE))
            print('  corrected the date on %d existing baseline(s)' % n)

        made = 0
        for r, cells in plan:
            if r.expense_id in already:
                continue
            months = {m: cells.get(m) for m in MONTHS}
            FinancialFigureHistory.objects.create(
                prop=r.prop, kind=FinancialFigureHistory.KIND_BUDGET,
                source_pk=r.expense_id, line_type=str(r.expense_line_types),
                effective_date=BASELINE, amount=sum(cells.values()),
                source='baseline', changed_by=None, **months)
            made += 1
        print('  created %d baseline snapshot(s)' % made)

# ------------------------------------------------------------- VERIFY
print('')
print(BAR)
print('VERIFY - what the P&L resolves %s' % ('AFTER the change' if APPLY else 'RIGHT NOW (unchanged)'))
print(BAR)
prop_ids = sorted({r.prop_id for r in rows})
for year in (2022, 2023, 2024, 2025, 2026, 2027, 2028):
    resolved = resolve_year_months_bulk(prop_ids, FinancialFigureHistory.KIND_BUDGET, year)
    # Per-month, because a year total hides the interesting case: 2026 should
    # be a BLEND of the old January and the new July, not one rate or the other.
    per_month = dict((m, Decimal('0')) for m in MONTHS)
    fallback = 0
    for r in rows:
        if r.expense_id in resolved:
            vals = resolved[r.expense_id]
        else:
            vals = [getattr(r, 'expense_' + m) for m in MONTHS]
            fallback += 1
        for i, m in enumerate(MONTHS):
            if vals[i] is not None:
                per_month[m] += Decimal(vals[i])
    total = sum(per_month.values())
    live = '  '.join('%s %s' % (m.upper(), q(per_month[m]))
                     for m in MONTHS if per_month[m] != 0)
    note = '   (%d fell back to live cells)' % fallback if fallback else ''
    print('  %d : EUR %-10s %s%s' % (year, q(total), live or '(nothing)', note))

print('')
print('Read the month columns, not just the totals. A year in which the rate')
print('changes should show one figure before the change and another after it.')
print(BAR)
'@

$python = $python.Replace('__LINE__',     ($Line -replace "'", ""))
$python = $python.Replace('__OLDTOTAL__', $OldTotal.ToString([System.Globalization.CultureInfo]::InvariantCulture))
$python = $python.Replace('__BASELINE__', $BaselineDate)
$python = $python.Replace('__NEWDATE__',  $NewDate)
$python = $python.Replace('__APPLY__',    $(if ($Apply) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/ctrepair.py && python /tmp/ctrepair.py; rc=`$?; rm -f /tmp/ctrepair.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

if ($Apply) {
    Write-Host "==> APPLYING to LIVE - this writes history rows" -ForegroundColor Yellow
} else {
    Write-Host "==> Dry run against LIVE - nothing will be written" -ForegroundColor Cyan
}
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -ne 0) {
    Write-Host "!!  exited with code $code" -ForegroundColor Red
    Write-Host "    Try:  railway link    (or add -Service <name>)"
}
exit $code
