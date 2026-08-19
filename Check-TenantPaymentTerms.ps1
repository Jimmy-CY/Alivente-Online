<#
.SYNOPSIS
    Which tenants have payment terms captured on their lease? Read-only, LIVE.

.DESCRIPTION
    tenant_payment_terms is a REQUIRED field on both the tenant add and edit
    forms, so in principle every tenant has one. This proves it either way.

    The distinction that matters, and the one the payment-days report was
    getting wrong: NULL is not the same as 0.

      NULL  the field was never captured - the record predates the field, or
            was written by something other than the form
      0     captured, and means "due on the invoice date" - a real answer

    A report that treats 0 as "not set" hides a perfectly good number, so this
    prints the raw value rather than a tidied one.

    Read-only: no write, no email, nothing left behind.

.PARAMETER Service
    Railway service name, if the project has more than one.

.EXAMPLE
    .\Check-TenantPaymentTerms.ps1
#>

[CmdletBinding()]
param(
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
from pages.models import tenant

BAR = '=' * 96
print(BAR)
print('TENANT PAYMENT TERMS - as captured on the lease record')
print('NULL = never captured.  0 = captured, means due on the invoice date.')
print(BAR)

ts = list(tenant.objects.select_related('prop').order_by('tenant_name'))
current = [t for t in ts if (t.tenant_current or '').strip().lower() == 'yes']
past    = [t for t in ts if t not in current]


def dump(title, group):
    if not group:
        return [], []
    print('')
    print(title + ' (%d)' % len(group))
    print('%-30s %-22s %-14s %s' % ('TENANT', 'PROPERTY', 'TERMS (days)', 'NOTE'))
    print('-' * 96)
    missing, zeros = [], []
    for t in group:
        v = t.tenant_payment_terms
        if v is None:
            shown, note = 'NULL', '<-- not captured'
            missing.append(t)
        elif v == 0:
            shown, note = '0', 'due on invoice date'
            zeros.append(t)
        else:
            shown, note = str(v), ''
        print('%-30s %-22s %-14s %s'
              % ((t.tenant_name or '')[:30], (getattr(t.prop, 'prop_name', '') or '')[:22],
                 shown, note))
    return missing, zeros


miss_cur, zero_cur = dump('CURRENT TENANTS', current)
miss_past, _       = dump('PAST TENANTS', past)

print('')
print(BAR)
print('SUMMARY')
print('  current tenants          : %d' % len(current))
print('  ...with terms captured   : %d' % (len(current) - len(miss_cur)))
print('  ...missing (NULL)        : %d' % len(miss_cur))
print('  ...captured as 0 days    : %d' % len(zero_cur))
print('  past tenants missing     : %d of %d' % (len(miss_past), len(past)))

if miss_cur:
    print('')
    print('  Fix these on the Tenants page (Edit -> Rental Payment Terms):')
    for t in miss_cur:
        print('    - %s  (%s)' % (t.tenant_name, getattr(t.prop, 'prop_name', '')))
else:
    print('')
    print('  Every current tenant has payment terms captured.')
    if zero_cur:
        print('  %d of them are 0 days, which is a real value, not a gap.' % len(zero_cur))

# Distribution - a quick sanity read on whether the numbers look deliberate.
vals = {}
for t in current:
    v = t.tenant_payment_terms
    if v is not None:
        vals[v] = vals.get(v, 0) + 1
if vals:
    print('')
    print('  Distribution across current tenants:')
    for v in sorted(vals):
        print('    %3d days : %s (%d)' % (v, '#' * vals[v], vals[v]))

print(BAR)
'@

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/tpt.py && python /tmp/tpt.py; rc=`$?; rm -f /tmp/tpt.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Reading tenant payment terms from Live (read-only)" -ForegroundColor Cyan
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
