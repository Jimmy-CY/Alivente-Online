<#
.SYNOPSIS
    The missing cent in Company Tax, July 2026. LIVE.  OF-2, 28 Oct 2026.
    Dry run unless you add -Write.

.DESCRIPTION
    July 2026 Company Tax reads 3,299.99 instead of 3,300.00. The reason:
    the ten snapshots dated 2026-07-01 add up to 3,299.99 (Ionion carries
    484 where it should be 485). The ten corrected snapshots, saved on
    24 August, were dated 2026-08-24, so they only take effect from the next
    Company Tax month, January 2027.

    This moves the effective date of those ten corrected snapshots back to
    2026-07-01. Nothing else changes: no figure is edited, nothing is deleted,
    the older 2026-07-01 snapshots stay as history. Where two snapshots share
    a date the one saved later wins, which is the corrected one.

    Safety:
      - refuses unless it finds exactly 10 snapshots dated 2026-08-24 on
        the Company Tax line;
      - shows July 2026, January 2026 and January 2027 before and after;
      - refuses to save unless, afterwards, July 2026 equals the live
        Company Tax figures for July exactly;
      - a dry run makes the change inside a transaction and then rolls it
        back, so the "after" figures are the real resolver's answer and
        nothing is kept.

.PARAMETER Write
    Actually save the change. Without it, nothing is kept.

.PARAMETER Service
    Railway service name, if `railway link` points somewhere else.

.EXAMPLE
    .\Fix-CompanyTaxCent.ps1           # dry run - shows before and after
    .\Fix-CompanyTaxCent.ps1 -Write    # saves it
#>

[CmdletBinding()]
param(
    [switch] $Write,
    [string] $Service = ""
)

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

from decimal import Decimal
from datetime import date
from django.db import transaction
from pages.models import (expense, expense_line_types, FinancialFigureHistory,
                          resolve_year_months_bulk)

WRITE = __WRITE__
FROM = date(2026, 8, 24)
TO = date(2026, 7, 1)
EXPECT = 10
BAR = '=' * 78
K = FinancialFigureHistory.KIND_BUDGET


class Refuse(Exception):
    pass


class DryRun(Exception):
    pass


lts = list(expense_line_types.objects.filter(
    expense_line_types_name__icontains='company tax'))
if len(lts) != 1:
    print('!! expected one Company Tax line type, found %d - nothing changed' % len(lts))
    sys.exit(2)
lt = lts[0]
EXP = list(expense.objects.filter(expense_line_types=lt))
SRC = [e.expense_id for e in EXP]
PIDS = sorted(set(e.prop_id for e in EXP))


def totals():
    out = {}
    for y, i in ((2026, 0), (2026, 6), (2027, 0)):
        vm = resolve_year_months_bulk(PIDS, K, y)
        tot = Decimal('0')
        for e in EXP:
            v = vm.get(e.expense_id)
            x = v[i] if v is not None else getattr(e, ('expense_jan', 0, 0, 0, 0, 0, 'expense_jul')[i])
            tot += Decimal(str(x or 0))
        out[(y, i)] = tot
    return out


def show(label, t):
    print('  %-8s  Jan 2026 %10s   Jul 2026 %10s   Jan 2027 %10s' % (
        label, '{:,.2f}'.format(t[(2026, 0)]), '{:,.2f}'.format(t[(2026, 6)]),
        '{:,.2f}'.format(t[(2027, 0)])))


live_jul = sum((Decimal(str(e.expense_jul or 0)) for e in EXP), Decimal('0'))

print(BAR)
print('COMPANY TAX - re-date the corrected snapshots  (%s)' % ('WRITE' if WRITE else 'DRY RUN'))
print(BAR)
print('Line type: id=%s  %s     live July figures add up to %s'
      % (lt.pk, lt.expense_line_types_name, '{:,.2f}'.format(live_jul)))

qs = FinancialFigureHistory.objects.filter(kind=K, source_pk__in=SRC, effective_date=FROM)
rows = list(qs.order_by('source_pk'))
print('Snapshots dated %s on this line: %d (expected %d)' % (FROM, len(rows), EXPECT))
if len(rows) != EXPECT:
    print('!! not exactly %d - nothing changed' % EXPECT)
    sys.exit(2)
for r in rows:
    print('   #%-6s src %-5s Jan %8s  Jul %8s' % (r.pk, r.source_pk, r.jan, r.jul))

before = totals()
print('')
show('BEFORE', before)

kept = False
try:
    with transaction.atomic():
        n = FinancialFigureHistory.objects.filter(
            pk__in=[r.pk for r in rows]).update(effective_date=TO)
        if n != EXPECT:
            raise Refuse('updated %d rows, expected %d' % (n, EXPECT))
        after = totals()
        show('AFTER', after)
        if after[(2026, 6)] != live_jul:
            raise Refuse('July 2026 would be %s, not %s'
                         % (after[(2026, 6)], live_jul))
        if not WRITE:
            raise DryRun()
        kept = True
except DryRun:
    pass
except Refuse as exc:
    print('')
    print('!! %s - rolled back, nothing changed' % exc)
    sys.exit(3)

print('')
if kept:
    print('SAVED: %d snapshots now dated %s.' % (EXPECT, TO))
else:
    print('DRY RUN: rolled back, nothing kept. Run again with -Write to save.')
print(BAR)
'@

$python = $python.Replace('__WRITE__', $(if ($Write) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/ctcent.py && python /tmp/ctcent.py; rc=`$?; rm -f /tmp/ctcent.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

if ($Write) {
    Write-Host "==> Company Tax cent fix on Live - WRITE" -ForegroundColor Yellow
} else {
    Write-Host "==> Company Tax cent fix on Live - dry run, nothing will be kept" -ForegroundColor Cyan
}
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -ne 0) {
    Write-Host "!!  Exited with code $code - see the message above." -ForegroundColor Red
}
exit $code
