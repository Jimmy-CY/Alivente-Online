<#
.SYNOPSIS
    What year range SHOULD the year-on-year matrix open on? Read-only, LIVE.

.DESCRIPTION
    The matrix currently derives its first year from the earliest NON-baseline
    snapshot. That is wrong in both directions:

      * include the baseline and it opens on 2000, drawing decades of the same
        repeated figure (the sentinel read as data);
      * exclude it and a line whose only dated change is recent opens on that
        change, hiding earlier years that resolve perfectly well FROM the
        baseline. Company Tax on Live shows 2026-2027 and hides 2024-2025.

    Both come from asking WHEN SNAPSHOTS EXIST instead of WHEN THE VALUE
    CHANGES.

    Proposed rule: start at the current year and walk backwards while the
    resolved line total keeps changing; stop once two consecutive years agree.
    A line that never changed shows one column. A line with a transition shows
    the years around it.

    This script applies both rules to every line type and prints them side by
    side, with the resolved totals it walked through, so the proposal can be
    judged before anything is built.

    Read-only: no write, no save, no delete, nothing left behind.

.PARAMETER Back
    How many years to walk back at most. Default 12.

.EXAMPLE
    .\Show-MatrixRange.ps1
#>
[CmdletBinding()]
param([int] $Back = 12, [string] $Service = "")

$ErrorActionPreference = 'Stop'
if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$python = @'
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from datetime import date
from decimal import Decimal
from django.db import connection
from django.db.models import Min
from pages.models import (expense, expense_line_types,
                          FinancialFigureHistory as H, FH_BASELINE_DATE,
                          resolve_year_months_bulk)

MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BACK = __BACK__
NOW = date.today().year
BAR = '=' * 100

_db = connection.settings_dict
print('-' * 100)
print('DATABASE  engine=%s  name=%s  host=%s'
      % (_db.get('ENGINE'), _db.get('NAME'), _db.get('HOST') or '(local)'))
print('-' * 100)
print(BAR)
print('current year %d;  walking back at most %d years' % (NOW, BACK))
print(BAR)

def line_total(rows, prop_ids, year):
    vm = resolve_year_months_bulk(prop_ids, H.KIND_BUDGET, year)
    t = Decimal('0')
    for e in rows:
        vals = vm.get(e.expense_id)
        if vals is not None:
            t += sum((v or Decimal('0')) for v in vals)
        else:
            t += sum((getattr(e, 'expense_' + m, None) or Decimal('0'))
                     for m in MONTHS)
    return t

for lt in expense_line_types.objects.all().order_by('expense_line_types_name'):
    rows = list(expense.objects.filter(
        expense_line_types_id=lt.expense_line_types_id))
    if not rows:
        continue
    prop_ids = [e.prop_id for e in rows]
    ids = [e.expense_id for e in rows]

    # what the matrix does TODAY
    first = (H.objects.filter(kind=H.KIND_BUDGET, source_pk__in=ids)
             .exclude(effective_date=FH_BASELINE_DATE)
             .aggregate(m=Min('effective_date'))['m'])
    shipped = first.year if first else NOW
    if shipped > NOW:
        shipped = NOW

    # DOES IT HAVE A BASELINE? This is the whole question. The baseline is
    # the sentinel meaning "it held this before anybody recorded a change", so
    # a line that has one can be resolved for ANY earlier year. A line without
    # one cannot: before its first snapshot the resolver returns nothing and
    # the caller falls back to the row's LIVE cells, so the matrix would draw
    # today's figure under a past year's heading. Same output, opposite status.
    has_base = H.objects.filter(kind=H.KIND_BUDGET, source_pk__in=ids,
                                effective_date=FH_BASELINE_DATE).exists()
    earliest_any = (H.objects.filter(kind=H.KIND_BUDGET, source_pk__in=ids)
                    .aggregate(m=Min('effective_date'))['m'])
    earliest_any_year = earliest_any.year if earliest_any else NOW

    # floor = max(earliest answerable year, one year before the first change)
    if first is None:
        proposed = NOW
    else:
        proposed = max(earliest_any_year, first.year - 1)
    if proposed > NOW:
        proposed = NOW

    totals = {}
    for y in range(min(proposed, shipped), NOW + 2):
        totals[y] = line_total(rows, prop_ids, y)

    ys = sorted(totals)
    trail = '  '.join(
        '%d=%s%s' % (t, totals[t], '' if (has_base or t >= earliest_any_year)
                     else '(FABRICATED)')
        for t in ys)
    flag = '' if proposed == shipped else '   <-- DIFFERS'
    print('')
    print('%-26s shipped opens %d   proposed opens %d%s'
          % ((lt.expense_line_types_name or '?')[:26], shipped, proposed, flag))
    print('   baseline: %-3s  earliest snapshot: %s  first dated change: %s'
          % ('YES' if has_base else 'no', earliest_any,
             first if first else '(none)'))
    print('   %s' % trail)
    hidden = [t for t in ys if t < shipped]
    if hidden:
        print('   RESTORED BY THE PROPOSAL: %s'
              % ', '.join(str(t) for t in hidden))

print('')
print(BAR)
'@

$python = $python.Replace('__BACK__', [string]$Back)
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/matrixrange.py && python /tmp/matrixrange.py; rc=`$?; rm -f /tmp/matrixrange.py; exit `$rc"
$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Matrix year range: shipped vs proposed (read-only)" -ForegroundColor Cyan
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0) { Write-Host "==> Done. Nothing on Live was changed." -ForegroundColor Cyan }
else { Write-Host "!!  railway ssh exited with code $code" -ForegroundColor Red }
exit $code
