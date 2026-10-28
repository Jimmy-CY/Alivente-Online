<#
.SYNOPSIS
    When did we own each property, and what would "Owned from" change in the
    budgets? Read-only, LIVE.  OF-1, 28 Oct 2026.

.DESCRIPTION
    Step 1 and Step 3 of the Owned-from plan agreed on 28 October. Nothing is
    changed: this only reads, and prints what the P&L shows today beside what
    it would show under the two agreed rules.

      1. OWNED FROM - each property's first lease start (his rule: the date
         of the first rental; the gap between buying and first letting is
         accepted). The earliest actual expense is shown beside it, for
         reference only.

      2. BUDGET AND REVENUE BY PROPERTY, per year - NOW (what the P&L draws
         today: every month, back to any year) against PROPOSED:
           - no budget or revenue in a month before the property's Owned-from
             month (any part of a month counts as the month);
           - the same for a PRO-RATA line: each owned property keeps its own
             share; the share of a property not yet owned drops (Option B,
             agreed 28 Oct), so early company totals get smaller.

      3. EVERY PRO-RATA LINE, per year - the company total NOW and PROPOSED,
         and each property's share both ways.

    Read-only: no INSERT, no UPDATE, no DELETE, nothing left behind on Live.

.PARAMETER Years
    Comma-separated years, in quotes. Default: every year in the P&L's year
    list - the earliest lease year through to next year.

.PARAMETER Service
    Railway service name, if `railway link` points somewhere else.

.EXAMPLE
    .\Show-OwnedFrom.ps1
    .\Show-OwnedFrom.ps1 -Years "2016,2017"
#>

[CmdletBinding()]
param(
    [string] $Years = "",
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
from datetime import date
from django.db.models import Min
from pages.models import (props, tenant, expense, act_expense,
                          FinancialFigureHistory, resolve_year_months_bulk,
                          lease_revenue_rows)

YEARS = [__YEARS__]          # empty = every year, worked out below
MON = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BAR = '=' * 104
Z = Decimal('0')


def m(v):
    return '-' if not v else '{:,.2f}'.format(v)


def owned_in(of, y, i):
    """Is a property with Owned-from `of` owned in month i (0-11) of year y?
    Any part of a month counts as the month. No date = owned all along."""
    if of is None:
        return True
    return (y, i + 1) >= (of.year, of.month)


P = list(props.objects.all().order_by('prop_name'))
NAME = dict((p.prop_id, p.prop_name or ('Property %s' % p.prop_id)) for p in P)

# ------------------------------------------------------------------ 1
print(BAR)
print('1. OWNED FROM  -  the first lease start, and the evidence beside it')
print(BAR)
print('%-26s %-14s %-16s %s' % ('PROPERTY', 'FIRST LEASE', 'FIRST EXPENSE', 'NOTE'))
print('-' * 104)
OF = {}
for p in P:
    fl = tenant.objects.filter(prop=p).exclude(
        tenant_lease_start_date__isnull=True).aggregate(
        x=Min('tenant_lease_start_date'))['x']
    fe = act_expense.objects.filter(prop=p).exclude(
        act_expense_date__isnull=True).aggregate(
        x=Min('act_expense_date'))['x']
    OF[p.prop_id] = fl
    note = ''
    if fl is None:
        note = 'no lease on record - treated as owned all along'
    elif fe and fe < fl:
        note = 'first expense earlier (for reference)'
    print('%-26s %-14s %-16s %s' % (NAME[p.prop_id][:26],
                                     fl.isoformat() if fl else '-',
                                     fe.isoformat() if fe else '-', note))

if not YEARS:
    first = [d.year for d in OF.values() if d]
    lo = min(first) if first else date.today().year      # same range as the P&L year list
    YEARS = list(range(lo, date.today().year + 2))
print('')
print('Years: %s' % ', '.join(str(y) for y in YEARS))

# ------------------------------------------------------------------ data
EXP = list(expense.objects.select_related('expense_line_types',
                                          'expense_types'))


def is_prorata(e):
    lt = e.expense_line_types
    return bool(lt) and (lt.expense_line_types_prorata or '').strip().lower() in ('yes', 'y', 'true', '1')


def months_now(e, vmap):
    v = vmap.get(e.expense_id)
    if v is not None:
        return [Decimal(str(x or 0)) for x in v]
    return [Decimal(str(getattr(e, 'expense_' + mm, 0) or 0)) for mm in MON]


GROUPS = {}
for e in EXP:
    if is_prorata(e):
        GROUPS.setdefault((e.expense_line_types_id, e.expense_types_id), []).append(e)

summary = {}
for y in YEARS:
    vmap = resolve_year_months_bulk([p.prop_id for p in P],
                                    FinancialFigureHistory.KIND_BUDGET, y)
    now = dict((e.expense_id, months_now(e, vmap)) for e in EXP)
    # Option B (agreed 28 Oct): one rule for every line, pro-rata or not -
    # a property carries nothing before its Owned-from month. A pro-rata
    # line keeps each owned property's own share; the share of a property
    # not yet owned simply drops, so the company total for those early
    # months gets smaller.
    new = dict((e.expense_id, [v if owned_in(OF.get(e.prop_id), y, i) else Z
                               for i, v in enumerate(now[e.expense_id])])
               for e in EXP)
    gsum = dict((key, (rows, None)) for key, rows in GROUPS.items())
    rev_now, rev_new = {}, {}
    for p in P:
        rn, rw = Z, Z
        for r in lease_revenue_rows(p, y):
            for i, mm in enumerate(MON):
                v = Decimal(str(getattr(r, 'revenue_' + mm, 0) or 0))
                rn += v
                if owned_in(OF.get(p.prop_id), y, i):
                    rw += v
        rev_now[p.prop_id], rev_new[p.prop_id] = rn, rw
    summary[y] = (now, new, gsum, rev_now, rev_new)

# ------------------------------------------------------------------ 2
print('')
print(BAR)
print('2. BUDGETED EXPENSES AND REVENUE BY PROPERTY  -  NOW against PROPOSED')
print(BAR)
for y in YEARS:
    now, new, gsum, rev_now, rev_new = summary[y]
    print('')
    print('--- %d ---' % y)
    print('%-26s %14s %14s %12s   %14s %14s' % (
        'PROPERTY', 'BUDGET NOW', 'PROPOSED', 'CHANGE', 'REVENUE NOW', 'PROPOSED'))
    tb_n = tb_w = tr_n = tr_w = Z
    for p in P:
        bn = sum((sum(now[e.expense_id]) for e in EXP if e.prop_id == p.prop_id), Z)
        bw = sum((sum(new[e.expense_id]) for e in EXP if e.prop_id == p.prop_id), Z)
        rn, rw = rev_now[p.prop_id], rev_new[p.prop_id]
        tb_n += bn; tb_w += bw; tr_n += rn; tr_w += rw
        flag = '' if bn == bw and rn == rw else '  <-'
        print('%-26s %14s %14s %12s   %14s %14s%s' % (
            NAME[p.prop_id][:26], m(bn), m(bw),
            ('{:+,.2f}'.format(bw - bn) if bw != bn else '-'),
            m(rn), m(rw), flag))
    print('-' * 104)
    print('%-26s %14s %14s %12s   %14s %14s' % (
        'ALL PROPERTIES', m(tb_n), m(tb_w),
        ('{:+,.2f}'.format(tb_w - tb_n) if tb_w != tb_n else '-'),
        m(tr_n), m(tr_w)))

# ------------------------------------------------------------------ 3
print('')
print(BAR)
print('3. PRO-RATA LINES  -  shares of properties not yet owned drop out')
print(BAR)
for y in YEARS:
    now, new, gsum, rev_now, rev_new = summary[y]
    print('')
    print('--- %d ---' % y)
    for key, (rows, unalloc) in sorted(gsum.items(), key=lambda kv: (
            str(kv[1][0][0].expense_line_types), str(kv[1][0][0].expense_types))):
        tn = sum((sum(now[e.expense_id]) for e in rows), Z)
        tw = sum((sum(new[e.expense_id]) for e in rows), Z)
        if not tn:
            continue
        print('  %s / %s   company total now %s, proposed %s%s' % (
            rows[0].expense_line_types, rows[0].expense_types, m(tn), m(tw),
            '' if tw == tn else '   (drops {:,.2f})'.format(tn - tw)))
        for e in sorted(rows, key=lambda r: NAME.get(r.prop_id, '')):
            a, b = sum(now[e.expense_id]), sum(new[e.expense_id])
            if a or b:
                print('       %-26s %12s -> %12s%s' % (NAME.get(e.prop_id, '?')[:26],
                      m(a), m(b), '' if a == b else '   <-'))

print('')
print(BAR)
print('HOW TO READ THIS')
print(BAR)
print('Section 1 is the date the rule hangs on: the first lease start.')
print('Before a property\'s Owned-from month it carries nothing - its own')
print('lines and its share of every pro-rata line drop out (Option B).')
print('Sections 2 and 3 change NOTHING; they are what the P&L would show.')
print(BAR)
'@

$python = $python.Replace('__YEARS__', $yearList)

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/ownedfrom.py && python /tmp/ownedfrom.py; rc=`$?; rm -f /tmp/ownedfrom.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Owned-from report on Live (read-only)" -ForegroundColor Cyan
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
