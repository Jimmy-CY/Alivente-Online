<#
.SYNOPSIS
    Why does Company Tax appear in the 2027 P&L but not 2026? Read-only, LIVE.

.DESCRIPTION
    Dumps everything behind the Company Tax budget line:

      1. The LIVE `expense` rows (what the config screen holds today)
      2. Every FinancialFigureHistory snapshot for those rows, oldest first
      3. What the P&L resolver ACTUALLY returns for each month of each year -
         by calling resolve_year_months_bulk, the same function the P&L uses

    Point 3 is the one that matters. The first two say what is stored; only the
    third says what the report will draw, and the gap between them is the whole
    question.

    Read-only: no write, no email, nothing left behind.

.PARAMETER Line
    Line-type name to look for. Default "Company Tax". Case-insensitive
    substring, so "tax" widens it.

.PARAMETER Years
    Comma-separated years to resolve. Default 2025,2026,2027.

.EXAMPLE
    .\Show-CompanyTaxHistory.ps1
    .\Show-CompanyTaxHistory.ps1 -Line "tax" -Years 2024,2025,2026,2027
#>

[CmdletBinding()]
param(
    [string] $Line = "Company Tax",
    [string] $Years = "2025,2026,2027",
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

from pages.models import (expense, expense_line_types, FinancialFigureHistory,
                          resolve_year_months_bulk)

LINE  = '__LINE__'
YEARS = [__YEARS__]
MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BAR = '=' * 108


def money(v):
    return '-' if v is None else ('%.0f' % float(v))


print(BAR)
print('COMPANY TAX / BUDGET LINE TRACE  -  line type matching %r' % LINE)
print(BAR)

lts = list(expense_line_types.objects.filter(expense_line_types_name__icontains=LINE))
if not lts:
    print('')
    print('No expense_line_types matched %r.' % LINE)
    print('Available line types:')
    for lt in expense_line_types.objects.all().order_by('expense_line_types_name'):
        print('    %s' % lt.expense_line_types_name)
    raise SystemExit(0)

print('')
print('Matched line type(s):')
for lt in lts:
    print('    id=%-4s %s' % (lt.expense_line_types_id, lt.expense_line_types_name))

rows = list(expense.objects.select_related('prop', 'expense_line_types', 'expense_types')
            .filter(expense_line_types__in=lts).order_by('prop__prop_name'))

if not rows:
    print('')
    print('No `expense` rows use that line type at all.')
    raise SystemExit(0)

# ---------------------------------------------------------------- 1. LIVE
print('')
print(BAR)
print('1. LIVE `expense` ROWS  -  what the budget config holds right now')
print(BAR)
print('%-6s %-24s %-18s %s' % ('exp_id', 'PROPERTY', 'TYPE', '  '.join('%5s' % m.upper() for m in MONTHS)))
print('-' * 108)
live_total = 0.0
for r in rows:
    vals = [getattr(r, 'expense_' + m) for m in MONTHS]
    tot = sum(float(v or 0) for v in vals)
    live_total += tot
    print('%-6s %-24s %-18s %s   = %s'
          % (r.expense_id, (r.prop.prop_name or '')[:24],
             str(r.expense_types)[:18],
             '  '.join('%5s' % money(v) for v in vals), money(tot)))
print('-' * 108)
print('LIVE TOTAL ACROSS ALL PROPERTIES: %s' % money(live_total))

# ------------------------------------------------------------- 2. HISTORY
print('')
print(BAR)
print('2. FinancialFigureHistory SNAPSHOTS  -  oldest first')
print(BAR)
src_ids = [r.expense_id for r in rows]
hist = list(FinancialFigureHistory.objects
            .select_related('prop', 'changed_by')
            .filter(kind=FinancialFigureHistory.KIND_BUDGET, source_pk__in=src_ids)
            .order_by('source_pk', 'effective_date', 'changed_at'))

if not hist:
    print('')
    print('NO history rows exist for these expense rows.')
    print('That is the "no history" case: the resolver returns nothing for the')
    print('source and the P&L falls back to the LIVE cells above, for EVERY year.')
else:
    print('%-6s %-20s %-12s %-16s %-10s %s'
          % ('src', 'PROPERTY', 'EFFECTIVE', 'CHANGED_AT', 'BY', 'MONTHS'))
    print('-' * 108)
    for h in hist:
        vals = [getattr(h, m) for m in MONTHS]
        who = getattr(h.changed_by, 'username', None) or '-'
        print('%-6s %-20s %-12s %-16s %-10s %s   = %s'
              % (h.source_pk, (h.prop.prop_name or '')[:20],
                 h.effective_date, h.changed_at.strftime('%Y-%m-%d %H:%M'),
                 who[:10],
                 '  '.join('%5s' % money(v) for v in vals),
                 money(sum(float(v or 0) for v in vals))))

# --------------------------------------------------- 3. WHAT THE P&L DRAWS
print('')
print(BAR)
print('3. WHAT THE P&L ACTUALLY RESOLVES  -  via resolve_year_months_bulk()')
print(BAR)
print('This calls the same function the P&L uses. "-" means the resolver')
print('returned None for that month.')

prop_ids = sorted({r.prop_id for r in rows})
for year in YEARS:
    resolved = resolve_year_months_bulk(prop_ids, FinancialFigureHistory.KIND_BUDGET, year)
    print('')
    print('--- %d ---' % year)
    print('%-6s %-24s %s' % ('exp_id', 'PROPERTY', '  '.join('%5s' % m.upper() for m in MONTHS)))
    year_total = 0.0
    for r in rows:
        if r.expense_id in resolved:
            vals = resolved[r.expense_id]
            note = ''
        else:
            vals = [getattr(r, 'expense_' + m) for m in MONTHS]
            note = '  <- no history in range; LIVE cells used'
        tot = sum(float(v or 0) for v in vals)
        year_total += tot
        print('%-6s %-24s %s   = %-7s%s'
              % (r.expense_id, (r.prop.prop_name or '')[:24],
                 '  '.join('%5s' % money(v) for v in vals), money(tot), note))
    print('%-31s %s' % ('YEAR TOTAL:', money(year_total)))
    if year_total == 0:
        print('   NOTE: total is zero, so the P&L omits the row entirely -')
        print('         which is exactly "Company Tax is missing from that year".')

print('')
print(BAR)
print('HOW TO READ THIS')
print(BAR)
print('The resolver picks, for each month, the latest snapshot effective in')
print('that month or earlier. Two cases behave very differently:')
print('')
print('  NO history at all      -> source absent from the result, P&L falls')
print('                            back to the LIVE cells. Roughly right.')
print('  SOME history, but none -> source IS present, and every month before')
print('  early enough              the first snapshot resolves to None (blank).')
print('')
print('So a line that has been edited ONCE, with an effective date part-way')
print('through, goes blank for everything before that date - even though the')
print('figure was real and budgeted at the time. Compare section 2 dates')
print('against the blank months in section 3.')
print(BAR)
'@

$python = $python.Replace('__LINE__',  ($Line -replace "'", ""))
$python = $python.Replace('__YEARS__', $yearList)

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/cthist.py && python /tmp/cthist.py; rc=`$?; rm -f /tmp/cthist.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Tracing the '$Line' budget line on Live (read-only)" -ForegroundColor Cyan
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
