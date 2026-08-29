<#
.SYNOPSIS
    One expense line type, resolved month by month, with its snapshot
    timeline. Read-only, LIVE.

.DESCRIPTION
    Answers three questions about a line type in one pass:

      A  WHEN did the charge change? Every distinct snapshot date across the
         line, with the line-wide total carried at that date. This is the
         timeline of the charge as the system recorded it.

      B  WHAT does each year resolve to, month by month, through the resolver
         that is actually deployed? Per-month totals across the whole line, so
         a blended year is visible as a blend rather than as a single number.

      C  WHICH property carries what, in the year asked about.

    Written to test a specific claim: that Company Tax 2026 resolves to
    3,499.99 in January (the old rate) plus 3,300.00 in July (the new rate) =
    6,799.99, and that this is CORRECT rather than stale. If section B shows
    two different rates in the two charge months, the month-by-month resolver
    is honouring an effective date somebody set deliberately.

    Read-only: no write, no save, no delete, nothing left behind.

.PARAMETER LineType
    Exact line-type name. Default "Company Tax".

.PARAMETER Years
    Comma-separated. Default 2024,2025,2026,2027.

.EXAMPLE
    .\Show-LineYear.ps1
    .\Show-LineYear.ps1 -LineType "Communal Fees 1"
#>
[CmdletBinding()]
param(
    [string] $LineType = "Company Tax",
    [string] $Years = "2024,2025,2026,2027",
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

from decimal import Decimal
from django.db import connection
from pages.models import (expense, expense_line_types,
                          FinancialFigureHistory as H, FH_BASELINE_DATE,
                          resolve_year_months_bulk)

MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
NAME = '__LINETYPE__'
YEARS = [__YEARS__]
BAR = '=' * 96

_db = connection.settings_dict
print('-' * 96)
print('DATABASE  engine=%s  name=%s  host=%s'
      % (_db.get('ENGINE'), _db.get('NAME'), _db.get('HOST') or '(local)'))
print('-' * 96)

lt = expense_line_types.objects.filter(expense_line_types_name=NAME).first()
if lt is None:
    print('No line type named %r. Available:' % NAME)
    for x in expense_line_types.objects.all().order_by('expense_line_types_name'):
        print('   %s' % x.expense_line_types_name)
    sys.exit(0)

rows = list(expense.objects.select_related('prop')
            .filter(expense_line_types_id=lt.expense_line_types_id))
ids = [e.expense_id for e in rows]
prop_ids = [e.prop_id for e in rows]
name_of = {e.expense_id: (e.prop.prop_name if e.prop else '?') for e in rows}

print(BAR)
print('%s  -  %d contributing row(s)' % (NAME, len(rows)))
print(BAR)

# ---- A. the timeline of the charge --------------------------------------
print('')
print('A. SNAPSHOT TIMELINE  (line-wide total carried at each effective date)')
print('   a date appearing more than once means several writes that day')
by_date = {}
for h in H.objects.filter(kind=H.KIND_BUDGET, source_pk__in=ids):
    tot = sum((getattr(h, m) or Decimal('0')) for m in MONTHS)
    d = by_date.setdefault(h.effective_date, {'n': 0, 'tot': Decimal('0'),
                                              'months': set()})
    d['n'] += 1
    d['tot'] += tot
    d['months'].update(m for m in MONTHS if (getattr(h, m) or 0))
for d in sorted(by_date):
    v = by_date[d]
    print('   %s %-9s %3d snapshot(s)   line total %10s   months: %s'
          % (d, 'BASELINE' if d == FH_BASELINE_DATE else '', v['n'], v['tot'],
             ', '.join(m for m in MONTHS if m in v['months']) or '-'))

# ---- B. what each year resolves to, month by month ----------------------
print('')
print('B. RESOLVED BY THE DEPLOYED RESOLVER  (line-wide total per month)')
print('   %-6s %s' % ('year', ' '.join('%9s' % m for m in MONTHS)))
for y in YEARS:
    vm = resolve_year_months_bulk(prop_ids, H.KIND_BUDGET, y)
    per = []
    for i in range(12):
        t = Decimal('0')
        for e in rows:
            vals = vm.get(e.expense_id)
            if vals is not None:
                t += (vals[i] or 0)
            else:
                t += (getattr(e, 'expense_' + MONTHS[i], 0) or 0)
        per.append(t)
    print('   %-6s %s   = %s'
          % (y, ' '.join(('%9s' % t) if t else ('%9s' % '.') for t in per),
             sum(per)))
    charge_months = [(MONTHS[i], per[i]) for i in range(12) if per[i]]
    if len(set(v for _m, v in charge_months)) > 1:
        print('          ^ BLENDED: %s'
              % ', '.join('%s=%s' % (m, v) for m, v in charge_months))

# ---- C. per property, for the last year asked about ---------------------
Y = YEARS[-1] if YEARS else 2026
print('')
print('C. PER PROPERTY, %d' % Y)
vm = resolve_year_months_bulk(prop_ids, H.KIND_BUDGET, Y)
for e in sorted(rows, key=lambda e: (name_of[e.expense_id] or '').lower()):
    vals = vm.get(e.expense_id)
    src = 'history' if vals is not None else 'live cells'
    if vals is None:
        vals = [getattr(e, 'expense_' + m, None) for m in MONTHS]
    on = [(MONTHS[i], vals[i]) for i in range(12) if vals[i]]
    print('   %-24s %-11s %10s   %s'
          % (name_of[e.expense_id][:24], src,
             sum((v or Decimal('0')) for v in vals),
             ', '.join('%s=%s' % (m, v) for m, v in on) or '-'))

print('')
print(BAR)
'@

$python = $python.Replace('__LINETYPE__', $LineType)
$python = $python.Replace('__YEARS__',    $yearList)

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/lineyear.py && python /tmp/lineyear.py; rc=`$?; rm -f /tmp/lineyear.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> $LineType on Live, resolved month by month (read-only)" -ForegroundColor Cyan
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0) { Write-Host "==> Done. Nothing on Live was changed." -ForegroundColor Cyan }
else { Write-Host "!!  railway ssh exited with code $code" -ForegroundColor Red }
exit $code
