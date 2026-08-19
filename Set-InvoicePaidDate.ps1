<#
.SYNOPSIS
    Backfill invoice_paid_date on LIVE for invoices that were marked paid
    before the field existed.

.DESCRIPTION
    DRY RUN BY DEFAULT - shows exactly which rows would change and what the
    resulting days-to-pay would be. Nothing is written until you add -Apply.

    Deliberately narrow. It will ONLY touch invoices that are:
      * for a tenant whose name matches one you named
      * dated within the month you gave
      * already marked Paid
      * currently missing a paid date

    An invoice that already HAS a paid date is never overwritten, so re-running
    is safe and cannot corrupt organically captured data.

    Writes with queryset.update(), which bypasses the model's save(). That
    matters: save() stamps TODAY when a paid invoice has no date, which would
    silently defeat the whole point of backdating.

.PARAMETER Tenant
    One or more tenant name fragments, comma separated. Case-insensitive.

.PARAMETER PaidDate
    The paid date to set, YYYY-MM-DD.

.PARAMETER Month
    Restrict to invoices dated in this month, YYYY-MM. Defaults to the month
    of -PaidDate.

.PARAMETER Apply
    Actually write. Without this it is a dry run.

.EXAMPLE
    .\Set-InvoicePaidDate.ps1 -Tenant Capacitor,Elisavet -PaidDate 2026-08-01
    .\Set-InvoicePaidDate.ps1 -Tenant Capacitor,Elisavet -PaidDate 2026-08-01 -Apply
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string] $Tenant,
    [Parameter(Mandatory = $true)][string] $PaidDate,
    [string] $Month = "",
    [switch] $Apply,
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}
if ($PaidDate -notmatch '^\d{4}-\d{2}-\d{2}$') {
    Write-Host "!!  -PaidDate must be YYYY-MM-DD (got '$PaidDate')" -ForegroundColor Red
    exit 1
}
if (-not $Month) { $Month = $PaidDate.Substring(0, 7) }
if ($Month -notmatch '^\d{4}-\d{2}$') {
    Write-Host "!!  -Month must be YYYY-MM (got '$Month')" -ForegroundColor Red
    exit 1
}

$names = @($Tenant -split '[,;]+' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if (-not $names) {
    Write-Host "!!  No tenant names given." -ForegroundColor Red
    exit 1
}
$nameList = ($names | ForEach-Object { "'" + ($_ -replace "'", "") + "'" }) -join ', '

$python = @'
import os, sys
from datetime import date, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()
from pages.models import invoices

NAMES     = [__NAMES__]
PAID_DATE = datetime.strptime('__PAID__', '%Y-%m-%d').date()
MONTH     = '__MONTH__'
APPLY     = __APPLY__

year, month = int(MONTH[:4]), int(MONTH[5:7])
start = date(year, month, 1)
end = date(year + (month == 12), (month % 12) + 1, 1)

BAR = '=' * 92
print(BAR)
print('BACKFILL invoice_paid_date  ->  %s' % PAID_DATE)
print('Tenants matching: %s' % ', '.join(NAMES))
print('Invoices dated  : %s to %s (exclusive)' % (start, end))
print('Mode            : %s' % ('APPLY - WILL WRITE' if APPLY else 'DRY RUN - nothing written'))
print(BAR)

targets = []
for frag in NAMES:
    qs = (invoices.objects
          .select_related('tenant', 'tenant__prop')
          .filter(tenant__tenant_name__icontains=frag,
                  invoice_date__gte=start, invoice_date__lt=end))
    for inv in qs.order_by('invoice_date'):
        paid_flag = (inv.invoice_paid or '').strip().lower()
        if inv.invoice_paid_date is not None:
            print('  SKIP  %-28s invoiced %s  already has paid_date=%s'
                  % (inv.tenant.tenant_name[:28], inv.invoice_date, inv.invoice_paid_date))
        elif paid_flag != 'yes':
            print('  SKIP  %-28s invoiced %s  not marked paid (paid=%r)'
                  % (inv.tenant.tenant_name[:28], inv.invoice_date, inv.invoice_paid))
        else:
            targets.append(inv)

if not targets:
    print('')
    print('Nothing to change.')
else:
    print('')
    print('WOULD CHANGE:' if not APPLY else 'CHANGING:')
    for inv in targets:
        days = (PAID_DATE - inv.invoice_date).days
        print('  #%-6s %-28s %-20s invoiced %s -> paid %s  = %d days   EUR %s'
              % (inv.invoice_id, inv.tenant.tenant_name[:28],
                 (inv.tenant.prop.prop_name or '')[:20],
                 inv.invoice_date, PAID_DATE, days, inv.effective_amount))
        if days < 0:
            print('        WARNING: paid date is BEFORE the invoice date.')

    if APPLY:
        ids = [i.invoice_id for i in targets]
        # .update() on purpose: the model's save() stamps TODAY when a paid
        # invoice has no date, which would defeat backdating entirely.
        n = invoices.objects.filter(invoice_id__in=ids).update(invoice_paid_date=PAID_DATE)
        print('')
        print('  %d row(s) updated.' % n)
        print('')
        print('  Verifying from the database:')
        for inv in invoices.objects.filter(invoice_id__in=ids).select_related('tenant'):
            ok = 'OK' if inv.invoice_paid_date == PAID_DATE else 'MISMATCH'
            print('    #%-6s %-28s paid_date=%s  [%s]'
                  % (inv.invoice_id, inv.tenant.tenant_name[:28],
                     inv.invoice_paid_date, ok))
    else:
        print('')
        print('  Dry run - nothing was written. Re-run with -Apply to commit.')

print(BAR)
'@

$python = $python.Replace('__NAMES__', $nameList)
$python = $python.Replace('__PAID__',  $PaidDate)
$python = $python.Replace('__MONTH__', $Month)
$python = $python.Replace('__APPLY__', $(if ($Apply) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/setpaid.py && python /tmp/setpaid.py; rc=`$?; rm -f /tmp/setpaid.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

if ($Apply) {
    Write-Host "==> APPLYING to LIVE - this writes to the database" -ForegroundColor Yellow
} else {
    Write-Host "==> Dry run against LIVE - nothing will be written" -ForegroundColor Cyan
}
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -ne 0) {
    Write-Host "!!  railway ssh exited with code $code" -ForegroundColor Red
    Write-Host "    Try:  railway link    (or add -Service <name>)"
}
exit $code
