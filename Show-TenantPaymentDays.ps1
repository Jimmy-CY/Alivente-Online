<#
.SYNOPSIS
    How quickly does each tenant pay? Read-only, against LIVE data.

.DESCRIPTION
    Runs the tenant payment-days report inside the Railway container without
    deploying anything: a temporary script is piped in, run once, and deleted.

    Read-only - no database write, no email, nothing left behind.

    Measures invoice_paid_date - invoice_date per invoice and summarises per
    tenant, against the payment terms on their lease.

    NOTE: paid dates only began being recorded on 3 Aug 2026 (migration 0088).
    Anything paid before then is invisible here and cannot be recovered.

.PARAMETER All
    Include past tenants, not only current ones.

.PARAMETER Detail
    List every measured invoice per tenant.

.PARAMETER Service
    Railway service name, if the project has more than one.

.EXAMPLE
    .\Show-TenantPaymentDays.ps1
    .\Show-TenantPaymentDays.ps1 -Detail
#>

[CmdletBinding()]
param(
    [switch] $All,
    [switch] $Detail,
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$python = @'
import os, sys
from datetime import date
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()
from pages.models import invoices, tenant

SHOW_ALL = __ALL__
DETAIL   = __DETAIL__
BAR = '=' * 100
today = date.today()

# Days past the agreed terms before a tenant is called slow. Not zero: terms
# across this portfolio are 0 (rent due on the invoice date), so a knife-edge
# at zero would flag everyone who pays on the 2nd rather than the 1st.
GRACE_DAYS = 7


def median(vals):
    if not vals:
        return None
    v = sorted(vals); m = len(v) // 2
    return float(v[m]) if len(v) % 2 else (v[m-1] + v[m]) / 2.0


ts = tenant.objects.select_related('prop').order_by('tenant_name')
if not SHOW_ALL:
    ts = ts.filter(tenant_current__iexact='Yes')

print(BAR)
print('TENANT PAYMENT BEHAVIOUR - days from invoice date to payment')
print('Data starts 2026-08-03 (when the paid date began being recorded).')
print(BAR)

rows, nodata, outstanding = [], [], []
for t in ts:
    qs = invoices.objects.filter(tenant=t).order_by('invoice_date')
    measured = [(i.invoice_date, i.invoice_paid_date,
                 (i.invoice_paid_date - i.invoice_date).days, i.effective_amount)
                for i in qs if i.invoice_paid_date and i.invoice_date]
    for i in qs:
        if (i.invoice_paid or '').strip().lower() != 'yes' and i.invoice_date:
            outstanding.append((t, i, (today - i.invoice_date).days))
    if not measured:
        nodata.append(t); continue
    d = [m[2] for m in measured]
    terms = t.tenant_payment_terms
    avg = sum(d) / float(len(d))
    rows.append({'t': t, 'n': len(d), 'avg': avg, 'med': median(d),
                 'best': min(d), 'worst': max(d), 'last': d[-1], 'terms': terms,
                 'vs': (avg - terms) if terms is not None else None,
                 'measured': measured})

if not rows:
    print('')
    print('No measurable payments yet. Each one needs BOTH an invoice date and a')
    print('paid date, and paid dates only began on 2026-08-03.')
else:
    rows.sort(key=lambda r: r['avg'], reverse=True)
    print('')
    print('%-28s %-20s %3s %7s %7s %5s %6s %6s %9s'
          % ('TENANT', 'PROPERTY', 'n', 'AVG', 'MEDIAN', 'BEST', 'WORST', 'LAST', 'VS TERMS'))
    print('-' * 100)
    for r in rows:
        vs = ('%+.1f' % r['vs']) if r['vs'] is not None else '  n/a'
        if r['vs'] is None:
            flag = ''
        elif r['vs'] > GRACE_DAYS * 2:
            flag = ' <-- WELL past terms'
        elif r['vs'] > GRACE_DAYS:
            flag = ' <-- slower than agreed'
        else:
            flag = ''
        print('%-28s %-20s %3d %7.1f %7.1f %5d %6d %6d %9s%s'
              % ((r['t'].tenant_name or '')[:28], (r['t'].prop.prop_name or '')[:20],
                 r['n'], r['avg'], r['med'], r['best'], r['worst'], r['last'], vs, flag))
    print('-' * 100)
    print('n = payments measured.  VS TERMS = average minus the agreed lease terms;')
    print('positive means slower than agreed. Flagged only beyond a %d-day grace,' % GRACE_DAYS)
    print('doubled to %d for the louder flag.  Rows with n below ~6 are indicative only.'
          % (GRACE_DAYS * 2))

    if DETAIL:
        print('')
        print(BAR)
        print('EVERY MEASURED PAYMENT')
        for r in rows:
            print('')
            print('%s  (%s)  terms: %s'
                  % (r['t'].tenant_name, r['t'].prop.prop_name,
                     'not set' if r['terms'] is None else r['terms']))
            for idate, pdate, days, amt in r['measured']:
                print('    invoiced %s  paid %s  = %3d days   EUR %s' % (idate, pdate, days, amt))

if nodata:
    print('')
    print(BAR)
    print('NO MEASURABLE PAYMENTS YET (%d) - and why' % len(nodata))
    print('A payment is measurable only when the invoice has BOTH a date and a')
    print('paid date. Paid dates began on 2026-08-03; anything marked paid before')
    print('that has no date and cannot be recovered.')
    for t in nodata:
        print('')
        print('  %s  (%s)' % (t.tenant_name, t.prop.prop_name))
        inv_rows = list(invoices.objects.filter(tenant=t).order_by('-invoice_date')[:6])
        if not inv_rows:
            print('      no invoices on record at all')
            continue
        for i in inv_rows:
            paid = (i.invoice_paid or '(blank)')
            if i.invoice_paid_date:
                why = 'measurable'
            elif (i.invoice_paid or '').strip().lower() == 'yes':
                why = '<-- marked paid, but NO paid date (paid before 2026-08-03)'
            else:
                why = 'not paid yet'
            print('      invoiced %-12s paid=%-8s paid_date=%-12s %s'
                  % (i.invoice_date, paid, i.invoice_paid_date or '(none)', why))

if outstanding:
    outstanding.sort(key=lambda x: x[2], reverse=True)
    print('')
    print(BAR)
    print('CURRENTLY UNPAID - oldest first')
    for t, i, age in outstanding:
        print('    %-28s %-20s invoiced %s  %4d days ago  EUR %s'
              % ((t.tenant_name or '')[:28], (t.prop.prop_name or '')[:20],
                 i.invoice_date, age, i.effective_amount))

print('')
print(BAR)
print('Rent is monthly, so each tenant gives about one measurement a month.')
print('Around six is enough to trust an average. Until then read the RANKING,')
print('not the absolute numbers.')
print(BAR)
'@

$python = $python.Replace('__ALL__',    $(if ($All)    { 'True' } else { 'False' }))
$python = $python.Replace('__DETAIL__', $(if ($Detail) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/tpd.py && python /tmp/tpd.py; rc=`$?; rm -f /tmp/tpd.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Reading tenant payment history from Live (read-only)" -ForegroundColor Cyan
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
