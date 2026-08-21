<#
.SYNOPSIS
    Is the revenue side correct - lease rent AND seasonal? Read-only, LIVE.

.DESCRIPTION
    Revenue reaches the P&L by two completely different routes, and only one of
    them can suffer the Company Tax failure.

      LEASE RENT / LEVIES   built on the fly by lease_revenue_rows() as UNSAVED
                            revenue objects, straight from the tenant leases.
                            No revenue_id, so no history and none possible. The
                            lease dates ARE the effective dating.

      SEASONAL / DIRECT     real revenue rows, resolved through
                            FinancialFigureHistory exactly like budgeted
                            expenses - so exposed to the same failure, and
                            currently untriggered only because no revenue row
                            has ever been edited.

    Being immune to that bug is not the same as being right, so this checks the
    lease path on its own terms.

    Section A is the one that matters most. _lease_month() matches a lease to a
    month with:

        l.tenant_lease_start_date <= month_end AND
        l.tenant_lease_end_date   >= month_start

    Both dates must be present. A lease with a NULL end date matches NOTHING -
    the property reads as vacant and its rent silently disappears from the P&L.
    The same is true of a NULL start date.

    Read-only: no write, no email, nothing left behind.

.PARAMETER Year
    Year to trace. Default: current year.

.PARAMETER Detail
    Print the month-by-month lease resolution for every property.

.EXAMPLE
    .\Show-RevenueTrace.ps1
    .\Show-RevenueTrace.ps1 -Year 2027 -Detail
#>

[CmdletBinding()]
param(
    [int] $Year = 0,
    [switch] $Detail,
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}
if ($Year -eq 0) { $Year = (Get-Date).Year }

$python = @'
import os, sys
from datetime import date
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from pages.models import (props, tenant, revenue, revenue_line_types,
                          FinancialFigureHistory, resolve_year_months_bulk,
                          lease_revenue_rows, _lease_month)

YEAR   = __YEAR__
DETAIL = __DETAIL__
MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BAR = '=' * 104
today = date.today()


def f(v):
    return 0.0 if v is None else float(v)


print(BAR)
print('REVENUE TRACE  -  year %d' % YEAR)
print(BAR)

# ============================================================== SECTION A
print('')
print('A. LEASE DATA QUALITY  -  what would silently vanish from the P&L')
print('-' * 104)
print('_lease_month() needs BOTH a start and an end date to match a month.')
print('A lease missing either matches nothing, and the property reads vacant.')
print('')

all_leases = list(tenant.objects.select_related('prop').order_by('prop__prop_name',
                                                                'tenant_lease_start_date'))
no_end   = [t for t in all_leases if not t.tenant_lease_end_date]
no_start = [t for t in all_leases if not t.tenant_lease_start_date]
no_rent  = [t for t in all_leases if not t.tenant_rent]

def show(label, rows, extra=None):
    print('  %-34s %d' % (label, len(rows)))
    for t in rows:
        note = ''
        if extra:
            note = '   ' + extra(t)
        print('      %-26s %-24s start=%-12s end=%-12s rent=%s%s'
              % ((t.tenant_name or '')[:26], (t.prop.prop_name or '')[:24],
                 t.tenant_lease_start_date or '(none)',
                 t.tenant_lease_end_date or '(none)',
                 t.tenant_rent if t.tenant_rent is not None else '(none)', note))

show('leases with NO END date', no_end,
     lambda t: '<-- INVISIBLE to the P&L' if t.tenant_lease_start_date else '')
show('leases with NO START date', no_start, lambda t: '<-- INVISIBLE to the P&L')
show('leases with no/zero rent', no_rent)
if not (no_end or no_start or no_rent):
    print('  No lease-date or rent gaps found.')

# ============================================================== SECTION B
print('')
print(BAR)
print('B. MONTH-BY-MONTH LEASE RESOLUTION  -  %d' % YEAR)
print(BAR)
print('lease   = a lease covers that month')
print('assumed = no lease covers it, but a recent one is assumed to continue')
print('vacant  = nothing; contributes ZERO rent')
print('')

# Match the P&L exactly: finance_pl_act filters prop_status="Active". Tracing
# every property instead produced two zero rows that look like missing revenue
# and are simply not in the report.
properties = list(props.objects.filter(prop_status='Active').order_by('prop_name'))
excluded = list(props.objects.exclude(prop_status='Active').order_by('prop_name'))
if excluded:
    print('  NOT in the P&L (prop_status is not "Active") - %d propert(ies):'
          % len(excluded))
    for p in excluded:
        print('      %-24s status=%s' % ((p.prop_name or '')[:24],
                                         p.prop_status or '(none)'))
    print('')
tag_totals = {'lease': 0, 'assumed': 0, 'vacant': 0}
year_rent = 0.0
year_lev = 0.0
vacancies = []
seasonal_props = []      # no leases at all -> the revenue table is used as-is

for p in properties:
    leases = list(tenant.objects.filter(prop=p))
    if not leases:
        # NOT an error: lease_revenue_rows() returns the stored revenue rows
        # verbatim for a property with no leases. That is the seasonal path.
        # Reported explicitly, because silently skipping it is what made the
        # reconciliation below look like an unexplained gap.
        seasonal_props.append(p)
        continue
    tags, rents = [], []
    prent = plev = 0.0
    for m in range(1, 13):
        tag, l, r, v = _lease_month(leases, YEAR, m, today)
        tags.append(tag)
        rents.append(f(r))
        prent += f(r)
        plev += f(v)
        tag_totals[tag] = tag_totals.get(tag, 0) + 1
        if tag == 'vacant':
            vacancies.append((p.prop_name, m))
    year_rent += prent
    year_lev += plev
    if DETAIL or 'vacant' in tags or 'assumed' in tags:
        short = {'lease': 'L', 'assumed': 'A', 'vacant': '.'}
        print('  %-24s %s   rent=%.0f'
              % ((p.prop_name or '')[:24],
                 ' '.join('%s%-6s' % (short[t], '%.0f' % r if r else '')
                          for t, r in zip(tags, rents)),
                 prent))

print('')
print('  month-slots: %d from a lease, %d assumed, %d vacant'
      % (tag_totals.get('lease', 0), tag_totals.get('assumed', 0),
         tag_totals.get('vacant', 0)))
print('  lease rent total   EUR %.2f' % year_rent)
print('  lease levies total EUR %.2f' % year_lev)

seasonal_total = 0.0
if seasonal_props:
    print('')
    print('  SEASONAL PROPERTIES (no leases - the revenue table is used as-is):')
    for p in seasonal_props:
        t = 0.0
        for r in p.revenue_set.all():
            t += sum(f(getattr(r, 'revenue_' + m)) for m in MONTHS)
        seasonal_total += t
        print('      %-24s EUR %12.2f   (%d revenue row(s))'
              % ((p.prop_name or '')[:24], t, p.revenue_set.count()))
    print('  seasonal total     EUR %.2f' % seasonal_total)
if vacancies:
    print('  vacant months (zero rent):')
    for name, m in vacancies:
        print('      %-24s %s' % ((name or '')[:24], MONTHS[m-1].upper()))

# ============================================================== SECTION C
print('')
print(BAR)
print('C. WHAT THE P&L ACTUALLY BUILDS  -  via lease_revenue_rows()')
print(BAR)
print('Same function the report calls. Should reconcile with section B.')
print('')
by_line = {}
for p in properties:
    for r in lease_revenue_rows(p, YEAR):
        name = str(r.revenue_line_types) if r.revenue_line_types else '(no line type)'
        tot = sum(f(getattr(r, 'revenue_' + m)) for m in MONTHS)
        by_line[name] = by_line.get(name, 0.0) + tot
grand = 0.0
for name in sorted(by_line):
    print('  %-34s EUR %12.2f' % (name[:34], by_line[name]))
    grand += by_line[name]
print('  %-34s EUR %12.2f' % ('TOTAL REVENUE', grand))
print('')
recon = year_rent + year_lev + seasonal_total
print('  section B lease rent           : EUR %12.2f' % year_rent)
print('  section B lease levies         : EUR %12.2f' % year_lev)
print('  section B seasonal properties  : EUR %12.2f' % seasonal_total)
print('  %-30s EUR %12.2f' % ('total', recon))
diff = grand - recon
print('  difference vs section C        : EUR %12.2f   %s'
      % (diff, '(exact)' if abs(diff) < 0.005 else '!! UNEXPLAINED - investigate'))

# ============================================================== SECTION D
print('')
print(BAR)
print('D. SEASONAL / DIRECT REVENUE  -  the part that CAN break')
print(BAR)
rev_rows = list(revenue.objects.select_related('prop', 'revenue_line_types').all())

# Exposure is NOT "the line type has no lease_role". It is "this stored row
# actually reaches the P&L", and that depends on whether the PROPERTY has
# leases:
#   property WITH leases    -> synthetic lease rows replace any rent/levies
#                              row, so only non-lease-role rows reach the P&L
#   property WITHOUT leases -> lease_revenue_rows() returns EVERY stored row
#                              verbatim, lease_role or not
# Classifying by lease_role alone hid a seasonal property whose revenue sits on
# the Rental line type - which is precisely the case worth checking.
leased_prop_ids = set(tenant.objects.values_list('prop_id', flat=True))
seasonal = []
for r in rev_rows:
    role = getattr(r.revenue_line_types, 'lease_role', None) if r.revenue_line_types else None
    if r.prop_id in leased_prop_ids and role:
        continue          # superseded by the synthetic lease row; never drawn
    seasonal.append(r)

if not seasonal:
    print('  No stored revenue row reaches the P&L.')
else:
    src_ids = [r.revenue_id for r in seasonal]
    hist = list(FinancialFigureHistory.objects
                .filter(kind=FinancialFigureHistory.KIND_REVENUE,
                        source_pk__in=src_ids).order_by('source_pk', 'effective_date'))
    print('  %d stored revenue row(s) reach the P&L, %d history snapshot(s)'
          % (len(seasonal), len(hist)))
    print('  (a row on a lease-role line type still counts when its property')
    print('   has no leases - that is how a seasonal rental is stored)')
    resolved = resolve_year_months_bulk([r.prop_id for r in seasonal],
                                        FinancialFigureHistory.KIND_REVENUE, YEAR)
    print('')
    print('  %-6s %-22s %-22s %10s %10s %s'
          % ('rev_id', 'PROPERTY', 'LINE TYPE', 'LIVE', 'RESOLVED', 'NOTE'))
    for r in seasonal:
        live = sum(f(getattr(r, 'revenue_' + m)) for m in MONTHS)
        if r.revenue_id in resolved:
            got = sum(f(v) for v in resolved[r.revenue_id])
            note = '' if abs(got - live) < 0.005 else 'differs - check the dates'
        else:
            got = live
            note = 'no history -> live cells used for EVERY year'
        print('  %-6s %-22s %-22s %10.2f %10.2f %s'
              % (r.revenue_id, (r.prop.prop_name or '')[:22],
                 str(r.revenue_line_types)[:22], live, got, note))
    if not hist:
        print('')
        print('  NO revenue row has ever been edited, which is the only reason')
        print('  this side looks clean. The FIRST edit of any of these rows will')
        print('  do exactly what the Company Tax edit did - unless the baseline')
        print('  fix is deployed first.')

print('')
print(BAR)
print('SUMMARY')
print(BAR)
print('  Lease rent/levies : computed from lease dates, no history involved.')
print('                      Immune to the snapshot failure - but only as good')
print('                      as the lease start/end dates in section A.')
print('  Seasonal / direct : goes through history, same exposure as budgeted')
print('                      expenses. See section D.')
print(BAR)
'@

$python = $python.Replace('__YEAR__',   "$Year")
$python = $python.Replace('__DETAIL__', $(if ($Detail) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/revtrace.py && python /tmp/revtrace.py; rc=`$?; rm -f /tmp/revtrace.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Tracing revenue for $Year on Live (read-only)" -ForegroundColor Cyan
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0) {
    Write-Host "==> Done. Nothing on Live was changed." -ForegroundColor Cyan
} else {
    Write-Host "!!  railway ssh exited with code $code" -ForegroundColor Red
}
exit $code
