<#
.SYNOPSIS
    What are inactive properties still carrying? Read-only.

.DESCRIPTION
    Two different problems, and they need different answers.

    A. STILL BEING CHARGED
       The P&L no longer filters on prop_status - it reports a YEAR, so a
       property keeps the years it was actually active for. The corollary is
       that an inactive property whose expenses were never CLOSED goes on
       contributing to the current and future years, because nothing stops it
       any more. Before, the status filter hid that. Now it shows.

       Every one of these wants the same fix: edit the expense, set "Applies
       from" to the date the property left, and stop it. Earlier years keep
       their figures; later years go to zero.

    B. HOLDING A PRO-RATA SHARE
       Worse, because it breaks the arithmetic rather than just adding to it.
       A pro-rata row is a SHARE of the amount on its line type. While an
       inactive property holds one, the other properties are carrying shares
       of a split that still counts it - so the line does not add up to the
       charge actually owed, and the sold property keeps being charged.

       These block deactivation now, but any that predate that guard are
       already in the data.

    Read-only: no INSERT, no UPDATE, no DELETE.

.PARAMETER Local
    Run against the LOCAL database instead of Live.

.PARAMETER Service
    Railway service name, if `railway link` points somewhere else.

.EXAMPLE
    .\Show-InactiveExposure.ps1
    .\Show-InactiveExposure.ps1 -Local
#>

[CmdletBinding()]
param(
    [switch] $Local,
    [string] $Service = ""
)

$ErrorActionPreference = 'Continue'

$python = @'
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from datetime import date
from pages.models import props, expense, revenue

MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BAR = '=' * 100
THIS_YEAR = date.today().year


def f(v):
    return 0.0 if v is None else float(v)


inactive = list(props.objects.exclude(prop_status='Active')
                .order_by('prop_country', 'prop_name'))

print('')
print(BAR)
print('INACTIVE PROPERTIES')
print(BAR)
if not inactive:
    print('  None. Nothing to report.')
    sys.exit(0)
for p in inactive:
    print('  %-28s status: %s' % (p.prop_name, p.prop_status or '(blank)'))

ids = [p.prop_id for p in inactive]
by_id = {p.prop_id: p for p in inactive}

# ------------------------------------------------------------------ SECTION A
rows = list(expense.objects.select_related('expense_line_types', 'expense_types')
            .filter(prop_id__in=ids).order_by('prop_id', 'expense_id'))

carrying = []
for e in rows:
    total = sum(f(getattr(e, 'expense_' + m)) for m in MONTHS)
    if total:
        lt = e.expense_line_types
        pr = (getattr(lt, 'expense_line_types_prorata', '') or '').strip().lower() == 'yes'
        carrying.append((e, total, pr))

print('')
print(BAR)
print('A. EXPENSES STILL CARRYING FIGURES')
print(BAR)
print('These now reach the P&L for %d and every year after, because the report' % THIS_YEAR)
print('no longer filters inactive properties out. Close each one from the date')
print('the property left.')
print('')
if not carrying:
    print('  None. Every expense on an inactive property is already at zero.')
else:
    print('  %-6s %-24s %-24s %-14s %11s %s'
          % ('ID', 'PROPERTY', 'LINE TYPE', 'TYPE', 'PER YEAR', 'PRO-RATA'))
    print('  ' + '-' * 96)
    total_all = 0.0
    for e, total, pr in carrying:
        total_all += total
        print('  %-6s %-24s %-24s %-14s %11s %s'
              % (e.expense_id, (by_id[e.prop_id].prop_name or '')[:24],
                 str(e.expense_line_types)[:24], str(e.expense_types)[:14],
                 '{:,.2f}'.format(total), 'YES' if pr else ''))
    print('  ' + '-' * 96)
    print('  %-72s %11s' % ('TOTAL still being charged, per year',
                            '{:,.2f}'.format(total_all)))

# ------------------------------------------------------------------ SECTION B
print('')
print(BAR)
print('B. PRO-RATA DISTRIBUTIONS THAT INCLUDE AN INACTIVE PROPERTY')
print(BAR)
print('The remaining properties hold shares of a split that still counts this')
print('one, so the line does not add up to the charge owed. Edit the line, set')
print('"Applies from", and un-tick the inactive property so the others take up')
print('its share.')
print('')

broken = {}
for e, total, pr in carrying:
    if pr:
        broken.setdefault(str(e.expense_line_types), []).append((e, total))

if not broken:
    print('  None. No inactive property is holding a pro-rata share.')
else:
    for lt_name in sorted(broken):
        members = list(expense.objects.select_related('prop')
                       .filter(expense_line_types__expense_line_types_name=lt_name))
        group_total = sum(sum(f(getattr(m, 'expense_' + mm)) for mm in MONTHS)
                          for m in members)
        stranded = sum(t for _, t in broken[lt_name])
        print('  %s' % lt_name)
        print('    %d row(s) in the distribution, %s a year in total'
              % (len(members), '{:,.2f}'.format(group_total)))
        for e, t in broken[lt_name]:
            print('    -> %-24s holds %s   <-- inactive'
                  % ((by_id[e.prop_id].prop_name or '')[:24], '{:,.2f}'.format(t)))
        print('    %s of that is allocated to a property that is no longer active.'
              % '{:,.2f}'.format(stranded))
        print('')

# ------------------------------------------------------------------ SECTION C
rev_rows = [r for r in revenue.objects.select_related('prop', 'revenue_line_types')
            .filter(prop_id__in=ids)
            if sum(f(getattr(r, 'revenue_' + m)) for m in MONTHS)]

print(BAR)
print('C. REVENUE ROWS ON INACTIVE PROPERTIES')
print(BAR)
if not rev_rows:
    print('  None.')
else:
    for r in rev_rows:
        t = sum(f(getattr(r, 'revenue_' + m)) for m in MONTHS)
        print('  %-24s %-24s %11s'
              % ((r.prop.prop_name or '')[:24], str(r.revenue_line_types)[:24],
                 '{:,.2f}'.format(t)))
    print('')
    print('  Lease rent is not listed here - it is projected from the leases and')
    print('  is already suppressed for an inactive property. These are stored')
    print('  revenue rows, which are not.')

print('')
print(BAR)
print('SUMMARY')
print(BAR)
print('  inactive properties                       : %d' % len(inactive))
print('  expenses still carrying figures           : %d' % len(carrying))
print('  distributions with an inactive member     : %d' % len(broken))
print('  revenue rows still carrying figures       : %d' % len(rev_rows))
print(BAR)
print('')
'@

if ($Local) {
    Write-Host "==> Inactive-property exposure on LOCAL (read-only)" -ForegroundColor Cyan
    Write-Host ""
    $tmp = Join-Path $env:TEMP 'alivente_inactive_exposure.py'
    # WriteAllText with a no-BOM encoder; Set-Content -Encoding UTF8 would add
    # a BOM, which is legal in Python source but pointless noise.
    [System.IO.File]::WriteAllText(
        $tmp, $python, (New-Object System.Text.UTF8Encoding($false)))
    & python $tmp
    $code = $LASTEXITCODE
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
} else {
    if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
        Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
        Write-Host "    Or run against the local database:  .\Show-InactiveExposure.ps1 -Local"
        exit 1
    }
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
    $remote = "echo '$b64' | base64 -d > /tmp/inact.py && python /tmp/inact.py; rc=`$?; rm -f /tmp/inact.py; exit `$rc"
    $railwayArgs = @('ssh')
    if ($Service) { $railwayArgs += @('--service', $Service) }
    $railwayArgs += $remote

    Write-Host "==> Inactive-property exposure on LIVE (read-only)" -ForegroundColor Cyan
    Write-Host ""
    & railway @railwayArgs
    $code = $LASTEXITCODE
}

Write-Host ""
if ($code -eq 0) {
    Write-Host "==> Done. Nothing was changed." -ForegroundColor Cyan
} else {
    Write-Host "!!  exited with code $code" -ForegroundColor Red
    if (-not $Local) { Write-Host "    Try:  railway link    (or add -Service <name>)" }
}
exit $code
