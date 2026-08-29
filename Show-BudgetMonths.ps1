<#
.SYNOPSIS
    Which months does each budgeted expense actually carry money in? Read-only, LIVE.

.DESCRIPTION
    The year-granular decision only has teeth for a row that carries money in
    MORE THAN ONE month, because that is the only case where an earlier month's
    figure can be restated by a later edit. A row with a single charge month
    cannot blend, so the decision costs it nothing.

    This counts them. For every budgeted expense row it prints the months that
    carry money on the LIVE row, then groups:

      SINGLE   one charge month - the decision is free
      MULTI    two or more - the decision has consequences, listed in full
      EMPTY    carries nothing at all

    Read-only: no write, no save, no delete, nothing left behind.

.EXAMPLE
    .\Show-BudgetMonths.ps1
#>
[CmdletBinding()]
param([string] $Service = "")

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

from django.db import connection
from pages.models import expense

MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BAR = '=' * 88

_db = connection.settings_dict
print('-' * 88)
print('DATABASE  engine=%s  name=%s  host=%s'
      % (_db.get('ENGINE'), _db.get('NAME'), _db.get('HOST') or '(local)'))
print('-' * 88)

single, multi, empty = [], [], []
for e in expense.objects.select_related('prop', 'expense_line_types').all():
    live = [(m, getattr(e, 'expense_' + m, None)) for m in MONTHS]
    on = [(m, v) for m, v in live if v not in (None, 0)]
    name = e.prop.prop_name if e.prop else '?'
    lt = e.expense_line_types.expense_line_types_name if e.expense_line_types else '?'
    rec = (name, lt, e.expense_id, on, e.expense_amount)
    (empty if not on else (single if len(on) == 1 else multi)).append(rec)

print(BAR)
print('%d budgeted row(s):  %d single-month, %d MULTI-month, %d empty'
      % (len(single) + len(multi) + len(empty), len(single), len(multi), len(empty)))
print(BAR)

if multi:
    print('')
    print('MULTI-MONTH - these are the rows the decision actually affects:')
    for name, lt, eid, on, amt in sorted(multi, key=lambda r: (r[1].lower(), r[0].lower())):
        print('   %-22s %-22s id=%-6s amount=%-10s  %s'
              % (name[:22], lt[:22], eid, amt,
                 ', '.join('%s=%s' % (m, v) for m, v in on)))
else:
    print('')
    print('No multi-month rows at all: every charge falls in one month, so the')
    print('year-granular decision cannot restate an earlier month for any row.')

# Which LINE TYPES are multi-month, since that is how you think about them.
lts = {}
for name, lt, eid, on, amt in multi:
    lts.setdefault(lt, set()).update(m for m, _v in on)
if lts:
    print('')
    print('by line type:')
    for lt in sorted(lts):
        print('   %-30s %s' % (lt[:30], ', '.join(
            m for m in MONTHS if m in lts[lt])))

print('')
print(BAR)
'@

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/budgetmonths.py && python /tmp/budgetmonths.py; rc=`$?; rm -f /tmp/budgetmonths.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Which months do budgeted expenses carry? (read-only)" -ForegroundColor Cyan
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0) { Write-Host "==> Done. Nothing on Live was changed." -ForegroundColor Cyan }
else { Write-Host "!!  railway ssh exited with code $code" -ForegroundColor Red }
exit $code
