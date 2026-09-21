<#
.SYNOPSIS
    Archive, then remove, the 30 orphaned history snapshots on Live.

.DESCRIPTION
    FinancialFigureHistory keys on source_pk, a plain integer. When the old
    pro-rata edit deleted and recreated the Company Tax rows (before 24 Aug
    2026), thirty snapshots were left pointing at expense ids 28-37, which no
    row owns. Show-HistoryOrphans.ps1 has reported the same thirty ever since.
    Agreed 21 Sep: archive them, then delete exactly those.

    TWO STEPS, ON PURPOSE.

      .\Remove-HistoryOrphans.ps1            DRY RUN. Lists the orphans and
                                             writes every field of every one
                                             to history_orphans_archive.json
                                             in this folder. Changes nothing.

      .\Remove-HistoryOrphans.ps1 -Apply     Deletes exactly the rows named in
                                             that archive - and only if Live
                                             still has exactly those, all
                                             thirty, all on ids 28-37.

    GUARDS. It refuses, and changes nothing, if:
      - the orphans on Live are not exactly 30 Company Tax snapshots on
        expense ids 28-37 (anything else means the picture has moved and a
        person should look before anything is removed);
      - -Apply is given and the archive file is not in this folder;
      - the rows on Live are not exactly the rows in the archive.
    The delete runs in ONE transaction and is rolled back if it removes any
    number of rows other than the number it was given.

    It prints which database it is talking to before anything else, and
    it reads no password.

.PARAMETER Apply
    Delete. Without it nothing on Live changes.

.PARAMETER Service
    Railway service name, if `railway link` points somewhere else.
#>

[CmdletBinding()]
param(
    [switch] $Apply,
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'
$archive = Join-Path $PSScriptRoot 'history_orphans_archive.json'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$python = @'
import json, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()
from django.db import transaction
from pages.models import (expense, revenue, prop_values, act_expense,
                          FinancialFigureHistory as H)

try:
    from pages.db_banner import print_banner
    print_banner()
except Exception as e:
    print('(database banner unavailable: %s)' % e)

APPLY = __APPLY__
WANT = __IDS__
EXPECTED_COUNT = 30
EXPECTED_SOURCES = set(range(28, 38))
KINDS = (('budget_expense', expense), ('revenue', revenue),
         ('valuation', prop_values), ('expense_actual', act_expense))


def orphans():
    out = []
    for kind, model in KINDS:
        live = set(model.objects.values_list('pk', flat=True))
        out += [h for h in H.objects.filter(kind=kind).order_by('pk')
                if h.source_pk not in live]
    return out


def as_record(h):
    rec = {'pk': h.pk}      # the table's key is not called id
    for f in H._meta.concrete_fields:
        v = getattr(h, f.attname)
        rec[f.attname] = v if isinstance(v, (int, type(None))) else str(v)
    return rec


found = orphans()
print('')
print('%d orphaned snapshot(s) on this database.' % len(found))
for h in found:
    print('  history id %-6s  expense id %-4s  %-14s  %-12s  %s'
          % (h.pk, h.source_pk, h.kind, h.effective_date, h.line_type))

problems = []
if len(found) != EXPECTED_COUNT:
    problems.append('expected %d orphans, found %d' % (EXPECTED_COUNT,
                                                      len(found)))
if set(h.source_pk for h in found) != EXPECTED_SOURCES:
    problems.append('expected expense ids 28-37, found %s'
                    % sorted(set(h.source_pk for h in found)))
if any(h.kind != 'budget_expense' or (h.line_type or '') != 'Company Tax'
       for h in found):
    problems.append('not every orphan is a Company Tax budgeted expense')
if problems:
    print('')
    print('REFUSING - the picture on this database is not the one agreed:')
    for p in problems:
        print('  - ' + p)
    print('Nothing was changed.')
    sys.exit(3)

if not APPLY:
    print('')
    print('===ARCHIVE-BEGIN===')
    print(json.dumps([as_record(h) for h in found], indent=1))
    print('===ARCHIVE-END===')
    print('DRY RUN. Nothing was changed.')
    sys.exit(0)

want = sorted(WANT or [])
have = sorted(h.pk for h in found)
if want != have:
    print('')
    print('REFUSING - Live does not hold exactly the rows in the archive.')
    print('  archive: %s' % want)
    print('  Live   : %s' % have)
    print('Nothing was changed.')
    sys.exit(4)

with transaction.atomic():
    deleted, per_model = H.objects.filter(pk__in=want).delete()
    if deleted != len(want):
        raise RuntimeError('deleted %d, expected %d - rolled back'
                           % (deleted, len(want)))
print('')
print('Deleted %d snapshot(s) in one transaction.' % deleted)
print('Orphans left: %d' % len(orphans()))
'@

if ($Apply) {
    if (-not (Test-Path $archive)) {
        Write-Host "!!  $archive is not here. Run without -Apply first - it writes the archive." -ForegroundColor Red
        exit 1
    }
    $records = Get-Content -Raw $archive | ConvertFrom-Json
    $ids = ($records | ForEach-Object { $_.pk }) -join ', '
    $python = $python.Replace('__APPLY__', 'True').Replace('__IDS__', "[$ids]")
    Write-Host "==> REMOVING $(@($records).Count) archived orphan(s) on Live" -ForegroundColor Yellow
} else {
    $python = $python.Replace('__APPLY__', 'False').Replace('__IDS__', 'None')
    Write-Host "==> Orphaned history on Live - DRY RUN, nothing will change" -ForegroundColor Cyan
}

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/hrm.py && python /tmp/hrm.py; rc=`$?; rm -f /tmp/hrm.py; exit `$rc"
$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

$out = (& railway @railwayArgs 2>&1 | Out-String)
$code = $LASTEXITCODE

$begin = $out.IndexOf('===ARCHIVE-BEGIN===')
$end = $out.IndexOf('===ARCHIVE-END===')
if ($begin -ge 0 -and $end -gt $begin) {
    Write-Host $out.Substring(0, $begin)
    $json = $out.Substring($begin + 19, $end - $begin - 19).Trim()
    $parsed = $json | ConvertFrom-Json
    if (Test-Path $archive) {
        $old = (Get-Content -Raw $archive).Trim()
        if ($old -ne $json) {
            Write-Host "!!  $archive already exists and differs from Live. Left as it was." -ForegroundColor Red
            exit 5
        }
        Write-Host "==> $archive already holds these $(@($parsed).Count) record(s)." -ForegroundColor Cyan
    } else {
        [IO.File]::WriteAllText($archive, $json + "`n")
        Write-Host "==> Archived $(@($parsed).Count) record(s) to $archive" -ForegroundColor Cyan
    }
    Write-Host $out.Substring($end + 17)
} else {
    Write-Host $out
}

if ($code -eq 0) {
    if ($Apply) { Write-Host "==> Done. Run .\Show-HistoryOrphans.ps1 - it should report 0 orphans." -ForegroundColor Cyan }
    else { Write-Host "==> Dry run complete. Commit the archive, then run with -Apply." -ForegroundColor Cyan }
} else {
    Write-Host "!!  exited with code $code - see above. Nothing changes on a refusal." -ForegroundColor Red
}
exit $code
