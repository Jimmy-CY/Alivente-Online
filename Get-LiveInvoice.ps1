<#
.SYNOPSIS
    Download invoice documents from LIVE to your laptop, by expense number.

.DESCRIPTION
    Read-only. Looks up each expense on Live, reads its attached document from
    the Railway volume, and saves a copy into .\live-invoices\ here.

    The file is streamed back as fixed-width base64 lines between markers, so
    it survives the SSH session wrapping long lines - which is what breaks the
    naive "one giant line" approach.

.PARAMETER ExpenseId
    One or more expense numbers, comma- or space-separated, as shown in the
    trial output. Works as -ExpenseId 55,62,66 and as -ExpenseId "55 62 66".

.PARAMETER Service
    Railway service name, if the project has more than one.

.PARAMETER Raw
    Also write the raw session transcript to live-invoices\_transcript.txt,
    for when something goes wrong and you want to see what came back.

.EXAMPLE
    .\Get-LiveInvoice.ps1 -ExpenseId 55,62,66
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string] $ExpenseId,
    [string] $Service = "",
    [switch] $Raw
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$outDir = Join-Path (Get-Location) 'live-invoices'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# powershell -File hands the whole list over as ONE string, so split it here.
$idList = @($ExpenseId -split '[,;\s]+' | Where-Object { $_ -match '^\d+$' })
if (-not $idList) {
    Write-Host "!!  No valid expense numbers in '$ExpenseId'" -ForegroundColor Red
    Write-Host "    Example:  -ExpenseId 55,62,66"
    exit 1
}
$ids = ($idList -join ',')

$python = @'
import base64, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()
from pages.models import act_expense

WIDTH = 200   # short enough that nothing wraps, long enough to stay quick

for pk in [__IDS__]:
    try:
        e = act_expense.objects.select_related('prop').get(act_expense_id=pk)
    except act_expense.DoesNotExist:
        print('XMISS|%s|no such expense' % pk); continue
    if not e.act_expense_document:
        print('XMISS|%s|no document attached' % pk); continue
    name = e.act_expense_document.name.split('/')[-1]
    try:
        e.act_expense_document.open('rb'); blob = e.act_expense_document.read()
        e.act_expense_document.close()
    except Exception as exc:
        print('XMISS|%s|unreadable: %s' % (pk, exc)); continue

    desc = (e.act_expense_description or '').replace('|', '/')
    print('XFILE|%s|%s|%s|%s|%s|%d' % (pk, name, e.prop.prop_name,
                                       e.act_expense_amount, desc, len(blob)))
    data = base64.standard_b64encode(blob).decode('ascii')
    print('XBEGIN')
    for i in range(0, len(data), WIDTH):
        print(data[i:i + WIDTH])
    print('XEND')
print('XDONE')
'@.Replace('__IDS__', $ids)

$b64script = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64script' | base64 -d > /tmp/getinv.py && python /tmp/getinv.py; rm -f /tmp/getinv.py"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Fetching $($idList.Count) document(s) from Live: $ids" -ForegroundColor Cyan
$lines = & railway @railwayArgs 2>&1 | ForEach-Object { "$_" }

if ($Raw) {
    $lines | Set-Content -Path (Join-Path $outDir '_transcript.txt') -Encoding UTF8
}

$saved = 0
$pending = $null
$buffer = $null

foreach ($line in $lines) {
    $t = $line.Trim()

    if ($t.StartsWith('XFILE|')) {
        $p = $t.Split('|')
        $pending = @{ Id = $p[1]; Name = $p[2]; Prop = $p[3]
                      Amount = $p[4]; Desc = $p[5]; Bytes = [int]$p[6] }
        continue
    }
    if ($t -eq 'XBEGIN') { $buffer = New-Object System.Text.StringBuilder; continue }
    if ($t -eq 'XEND') {
        if ($pending -and $buffer) {
            $safe = ($pending.Name -replace '[\\/:*?"<>|]', '_')
            $path = Join-Path $outDir ("{0}-{1}" -f $pending.Id, $safe)
            try {
                [IO.File]::WriteAllBytes($path, [Convert]::FromBase64String($buffer.ToString()))
                $got = (Get-Item $path).Length
                Write-Host ("    #{0}  {1}  EUR {2}  - {3}" -f `
                    $pending.Id, $pending.Prop, $pending.Amount, $pending.Desc) -ForegroundColor Gray
                if ($got -eq $pending.Bytes) {
                    Write-Host ("        saved: {0}  ({1:N0} bytes, size verified)" -f `
                        (Split-Path $path -Leaf), $got) -ForegroundColor Green
                    $saved++
                } else {
                    Write-Host ("        WARNING: got {0:N0} bytes, expected {1:N0} - file may be truncated" -f `
                        $got, $pending.Bytes) -ForegroundColor Yellow
                }
            } catch {
                Write-Host ("        FAILED to decode #{0}: {1}" -f $pending.Id, $_.Exception.Message) -ForegroundColor Red
            }
        }
        $pending = $null; $buffer = $null
        continue
    }
    if ($t.StartsWith('XMISS|')) {
        $p = $t.Split('|')
        Write-Host ("    #{0}  skipped - {1}" -f $p[1], $p[2]) -ForegroundColor Yellow
        continue
    }
    # Inside a file body: accumulate. Ignore anything that is not base64.
    if ($buffer -ne $null -and $t -match '^[A-Za-z0-9+/=]+$') {
        [void]$buffer.Append($t)
    }
}

Write-Host ""
if ($saved -gt 0) {
    Write-Host "==> $saved file(s) saved to: $outDir" -ForegroundColor Cyan
    Write-Host "    Drag them into the chat from there."
} else {
    Write-Host "!!  Nothing was saved." -ForegroundColor Red
    Write-Host "    Re-run with -Raw and send me live-invoices\_transcript.txt:"
    Write-Host "      powershell -ExecutionPolicy Bypass -File .\Get-LiveInvoice.ps1 -ExpenseId $ids -Raw"
}
