<#
.SYNOPSIS
    Which budgeted figures would move if the YEAR became the unit of effective
    dating? Read-only, LIVE.

.DESCRIPTION
    Replays every budgeted expense row through both resolution rules and
    reports only the cells that differ.

      OLD (shipped)   for month m of year y, choose the latest snapshot with
                      (eff.year, eff.month) <= (y, m), then read THAT
                      snapshot's column m. A change made in August cannot
                      supply June of the same year - so a mid-year budget edit
                      is invisible until the following January.

      NEW (proposed)  for year y, choose the latest snapshot effective on or
                      before 31 Dec y and read all twelve of its columns. The
                      twelve columns are the SHAPE of the year's budget; the
                      latest word on that year wins.

    Both rules are implemented in this script, independently of the resolver
    being changed, so this measures the proposal rather than trusting it.

    A row with no history is skipped: it falls back to live cells under both
    rules and cannot move.

    Read the output as the blast radius. A year printed UNCHANGED is a year the
    P&L reports identically before and after. Movement in a CLOSED year is the
    finding that should stop the change.

    Runs inside the Railway container via `railway ssh`, because the database
    host is on Railway's private network and does not resolve from a laptop.

    Read-only: no write, no save, no delete, no email, nothing left behind.

.PARAMETER Years
    Comma-separated years to test. Default: derived from the data.

.PARAMETER Cap
    Rows listed per year, largest movement first. Default 25. The net is always
    exact; only the listing is capped.

.PARAMETER Service
    Railway service name, if `railway link` did not pin one.

.EXAMPLE
    .\Show-BlastRadius.ps1
    .\Show-BlastRadius.ps1 -Years 2024,2025,2026,2027 -Cap 100
#>

[CmdletBinding()]
param(
    [string] $Years = "",
    [int]    $Cap = 25,
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$yearList = ($Years -split '[,;\s]+' | Where-Object { $_ } | ForEach-Object { [int]$_ }) -join ', '

$python = @'
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db import connection
from pages.models import expense, FinancialFigureHistory as H, FH_BASELINE_DATE

MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
YEARS = [__YEARS__]
CAP = __CAP__
BAR = '=' * 92

# WHICH DATABASE IS THIS? Printed first so the output carries its own
# provenance - a local run and a Live run must never be confusable.
_db = connection.settings_dict
print('-' * 92)
print('DATABASE  engine=%s  name=%s' % (_db.get('ENGINE'), _db.get('NAME')))
print('          host=%s  port=%s'
      % (_db.get('HOST') or '(local socket / file)', _db.get('PORT') or ''))
print('-' * 92)


def old_rule(versions, year):
    vals = []
    for m in range(1, 13):
        chosen = None
        for v in versions:
            if (v.effective_date.year, v.effective_date.month) <= (year, m):
                chosen = v
            else:
                break
        vals.append(getattr(chosen, MONTHS[m - 1]) if chosen is not None else None)
    return vals


def new_rule(versions, year):
    eligible = [v for v in versions if v.effective_date.year <= year]
    if not eligible:
        return [None] * 12
    chosen = eligible[-1]
    return [getattr(chosen, m) for m in MONTHS]


def total(vals):
    return sum((v or Decimal('0')) for v in vals)


rows = list(H.objects.filter(kind=H.KIND_BUDGET)
            .order_by('source_pk', 'effective_date', 'changed_at'))
by_src = defaultdict(list)
for r in rows:
    by_src[r.source_pk].append(r)

labels = {}
for e in (expense.objects.select_related('prop', 'expense_line_types')
          .filter(expense_id__in=list(by_src.keys()))):
    labels[e.expense_id] = (
        (e.prop.prop_name if e.prop else '?'),
        (e.expense_line_types.expense_line_types_name
         if e.expense_line_types else '?'))

real_dates = [r.effective_date for r in rows if r.effective_date != FH_BASELINE_DATE]
if not real_dates:
    print('No non-baseline budget history at all; nothing can move.')
    sys.exit(0)

years = YEARS or list(range(min(real_dates).year,
                            max(max(real_dates).year, date.today().year) + 2))

print(BAR)
print('%d source row(s) with history; testing %s'
      % (len(by_src), ', '.join(str(y) for y in years)))
print('orphan = a snapshot whose expense row no longer exists')
print(BAR)

grand = Decimal('0')
moved = set()
for year in years:
    diffs = []
    for src, versions in by_src.items():
        o, n = old_rule(versions, year), new_rule(versions, year)
        if total(o) != total(n):
            diffs.append((src, total(o), total(n)))
    if not diffs:
        print('')
        print('%d  UNCHANGED' % year)
        continue
    delta = sum((n - o) for _, o, n in diffs)
    grand += delta
    print('')
    print('%d  %d row(s) move, net %+.2f' % (year, len(diffs), delta))
    ordered = sorted(diffs, key=lambda d: abs(d[2] - d[1]), reverse=True)
    for src, o, n in ordered[:CAP]:
        name, lt = labels.get(src, ('(orphan snapshot)', '?'))
        print('     %-22s %-20s id=%-6s %10s -> %-10s %+.2f'
              % (name[:22], lt[:20], src, o, n, n - o))
    if len(ordered) > CAP:
        rest = sum((n - o) for _, o, n in ordered[CAP:])
        print('     ... and %d more row(s), together %+.2f'
              % (len(ordered) - CAP, rest))
    for src, _o, _n in diffs:
        moved.add(src)

print('')
print(BAR)
print('%d of %d source row(s) move in at least one year; net %+.2f overall'
      % (len(moved), len(by_src), grand))
print('A year listed UNCHANGED reports identically before and after.')
print(BAR)
'@

$python = $python.Replace('__YEARS__', $yearList)
$python = $python.Replace('__CAP__',   [string]$Cap)

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/blastradius.py && python /tmp/blastradius.py; rc=`$?; rm -f /tmp/blastradius.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Measuring year-granular effective dating on Live (read-only)" -ForegroundColor Cyan
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
