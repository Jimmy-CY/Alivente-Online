<#
.SYNOPSIS
    How many budget / revenue lines are blanked out by the history resolver?
    Read-only, LIVE.

.DESCRIPTION
    The Company Tax trace showed a specific failure: a line with SOME history
    but none effective early enough resolves to blank for every month before
    its first snapshot. This answers "how widespread is that", by comparing —
    for every source row, for each year — what resolve_year_months_bulk()
    returns against the live cells.

    Three verdicts per source per year:

      OK        resolver and live agree, or the difference looks like a real
                deliberate change
      BLANKED   resolver returns None for months where the live row has a
                figure, AND the source has no snapshot effective that early.
                This is money silently missing from the report.
      RETRO     no history in range at all, so today's figure is being applied
                to a past year it may never have had

    Section B separately lists ACTUAL company-tax payments from act_expense,
    which is the reliable source for what was really paid — better than
    reverse-engineering it from a budget total.

    Read-only: no write, no email, nothing left behind.

.PARAMETER Years
    Comma-separated years to test. Default 2024,2025,2026,2027.

.PARAMETER Detail
    Show every affected source row, not just the per-year summary.

.EXAMPLE
    .\Show-BudgetHistoryGaps.ps1
    .\Show-BudgetHistoryGaps.ps1 -Detail
#>

[CmdletBinding()]
param(
    [string] $Years = "2024,2025,2026,2027",
    [switch] $Detail,
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$yearList = ($Years -split '[,;\s]+' | Where-Object { $_ } | ForEach-Object { [int]$_ }) -join ', '
if (-not $yearList) { Write-Host "!!  No years given." -ForegroundColor Red; exit 1 }

$python = @'
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from pages.models import (expense, revenue, act_expense, FinancialFigureHistory,
                          resolve_year_months_bulk)

YEARS  = [__YEARS__]
DETAIL = __DETAIL__
MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BAR = '=' * 104


def f(v):
    return 0.0 if v is None else float(v)


def scan(model, prefix, kind, label):
    rows = list(model.objects.select_related('prop').all())
    if not rows:
        print('  (no %s rows)' % label)
        return

    live = {}
    for r in rows:
        pk = getattr(r, prefix + '_id')
        live[pk] = {
            'row': r,
            'months': [getattr(r, prefix + '_' + m) for m in MONTHS],
            'line': str(getattr(r, prefix + '_line_types', '')),
            'prop': (r.prop.prop_name or '')[:22],
        }

    # Earliest snapshot per source - the date before which it goes blank.
    earliest = {}
    for h in (FinancialFigureHistory.objects
              .filter(kind=kind, source_pk__in=list(live))
              .order_by('source_pk', 'effective_date')):
        earliest.setdefault(h.source_pk, h.effective_date)

    prop_ids = sorted({r.prop_id for r in rows})

    for year in YEARS:
        resolved = resolve_year_months_bulk(prop_ids, kind, year)
        blanked, retro = [], []
        blank_amount = 0.0
        retro_amount = 0.0

        for pk, info in live.items():
            live_total = sum(f(v) for v in info['months'])
            if live_total == 0:
                continue                      # nothing budgeted; nothing to lose

            if pk not in resolved:
                # No snapshot on or before 31 Dec of this year -> live cells are
                # used for a year that may predate the figure entirely.
                first = earliest.get(pk)
                if first is not None and first.year > year:
                    retro.append((pk, info, live_total, first))
                    retro_amount += live_total
                continue

            vals = resolved[pk]
            got = sum(f(v) for v in vals)
            missing = 0.0
            for i, m in enumerate(MONTHS):
                if vals[i] is None and f(info['months'][i]) != 0:
                    missing += f(info['months'][i])
            if missing > 0:
                blanked.append((pk, info, live_total, got, missing,
                                earliest.get(pk)))
                blank_amount += missing

        print('')
        print('  --- %d ---' % year)
        print('    BLANKED : %-3d source(s), about EUR %.0f of budgeted figures '
              'resolving to blank' % (len(blanked), blank_amount))
        print('    RETRO   : %-3d source(s), about EUR %.0f of today\'s figures '
              'applied to a year before they existed' % (len(retro), retro_amount))

        if DETAIL and blanked:
            print('    Blanked detail:')
            for pk, info, live_total, got, missing, first in blanked:
                print('      #%-5s %-22s %-22s live=%-8.0f resolved=%-8.0f '
                      'missing=%-8.0f first snapshot %s'
                      % (pk, info['prop'], info['line'][:22], live_total, got,
                         missing, first))
        if DETAIL and retro:
            print('    Retro detail:')
            for pk, info, live_total, first in retro:
                print('      #%-5s %-22s %-22s live=%-8.0f first snapshot %s'
                      % (pk, info['prop'], info['line'][:22], live_total, first))


print(BAR)
print('A. HISTORY-RESOLVER GAPS')
print(BAR)
print('BLANKED = budgeted money the P&L is silently dropping for that year.')
print('RETRO   = today\'s figure being shown for a year that predates it.')

print('')
print('BUDGETED EXPENSES')
scan(expense, 'expense', FinancialFigureHistory.KIND_BUDGET, 'expense')

print('')
print('DIRECT / SEASONAL REVENUE')
scan(revenue, 'revenue', FinancialFigureHistory.KIND_REVENUE, 'revenue')

# ------------------------------------------------------------------ SECTION B
print('')
print(BAR)
print('B. ACTUAL COMPANY-TAX PAYMENTS  (act_expense, description search)')
print(BAR)
print('The reliable answer to "what was really paid", rather than deriving it')
print('from a budget total.')

hits = (act_expense.objects.select_related('prop')
        .filter(act_expense_description__icontains='tax')
        .order_by('act_expense_date'))
rows = [a for a in hits if a.act_expense_date]
if not rows:
    print('')
    print('No act_expense rows with "tax" in the description.')
else:
    by_year = {}
    print('')
    print('%-12s %-24s %-30s %10s %5s %5s'
          % ('DATE', 'PROPERTY', 'DESCRIPTION', 'AMOUNT', 'APPR', 'PAID'))
    print('-' * 104)
    for a in rows:
        y = a.act_expense_date.year
        by_year[y] = by_year.get(y, 0.0) + f(a.act_expense_amount)
        print('%-12s %-24s %-30s %10.2f %5s %5s'
              % (a.act_expense_date, (a.prop.prop_name or '')[:24],
                 (a.act_expense_description or '')[:30],
                 f(a.act_expense_amount),
                 a.act_expense_approved or '-', a.act_expense_paid or '-'))
    print('-' * 104)
    for y in sorted(by_year):
        print('  %d total: EUR %.2f' % (y, by_year[y]))

print('')
print(BAR)
'@

$python = $python.Replace('__YEARS__',  $yearList)
$python = $python.Replace('__DETAIL__', $(if ($Detail) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/bhgaps.py && python /tmp/bhgaps.py; rc=`$?; rm -f /tmp/bhgaps.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Scanning budget/revenue history gaps on Live (read-only)" -ForegroundColor Cyan
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
