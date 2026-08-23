<#
.SYNOPSIS
    Verify, tidy and push the pending Alivente-Online changes.

.DESCRIPTION
    Six changes are sitting in the working tree, all applied and tested locally:

        1. Effective-date baseline + the effective_date field on the four
           finance forms          (models.py, views/finance.py, 4 templates)
        2. Tenant Payment Behaviour report, incl. the 1-Aug-2026 cutoff
        3. Tenants Help - Payment Behaviour section
        4. Reports dropdown (desktop) on Tenants / Issues / Expenses
        5. Database error page - charset + connectivity wording

    This script runs every check first and only then touches git.

    SAFE BY DEFAULT.  With no switches it changes nothing: it verifies,
    reports, and stops before staging.  Nothing is committed without -Apply
    and nothing leaves the machine without -Push.

.PARAMETER Apply
    Stage and commit.  Without it the script stops after the report.

.PARAMETER Push
    Push to origin.  Implies -Apply.

.PARAMETER Force
    Continue past a failed sentinel check.  Use only when you know a sentinel
    string is simply out of date - never to push a half-applied tree.

.PARAMETER Message
    Override the commit subject line.

.EXAMPLE
    .\Push-PendingChanges.ps1
    Verify and report.  Changes nothing.

.EXAMPLE
    .\Push-PendingChanges.ps1 -Push
    Verify, tidy, commit and push.
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Push,
    [switch]$Force,
    [string]$Message = 'Pro-rata edits keep their history; opening and closing snapshots'
)

# Deliberately NOT 'Stop'.  Under 'Stop', anything a native command writes to
# stderr and we redirect with 2>&1 becomes a terminating NativeCommandError -
# git and manage.py both do this routinely.  Control flow here is driven by
# exit codes instead, which is what we actually want to branch on.
$ErrorActionPreference = 'Continue'
if ($Push) { $Apply = $true }

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Say    ($t) { Write-Host $t }
function Head   ($t) { Write-Host ''; Write-Host $t -ForegroundColor Cyan
                       Write-Host ('-' * $t.Length) -ForegroundColor Cyan }
function Good   ($t) { Write-Host ('  OK    ' + $t) -ForegroundColor Green }
function Bad    ($t) { Write-Host ('  FAIL  ' + $t) -ForegroundColor Red }
function Warn   ($t) { Write-Host ('  WARN  ' + $t) -ForegroundColor Yellow }

$problems = 0

# ---------------------------------------------------------------- 0. repo
Head 'Repository'
& git rev-parse --is-inside-work-tree > $null 2>&1
if ($LASTEXITCODE -ne 0) { Bad "$root is not a git working tree"; exit 1 }

$branch = (& git rev-parse --abbrev-ref HEAD).Trim()
$origin = (& git remote get-url origin 2>$null)
Say ("  root    : " + $root)
Say ("  branch  : " + $branch)
Say ("  origin  : " + $(if ($origin) { $origin } else { '(none)' }))

if (-not $origin -and $Push) { Bad 'no origin remote - cannot push'; exit 1 }

# ------------------------------------------------------- 1. is it applied?
# Each change leaves a distinctive string behind.  If one is missing the tree
# is only half-patched and must not be committed.
Head 'Are all the changes actually in the tree?'

$sentinels = @(
    @{ File = 'pages\models.py';                          Text = 'FH_BASELINE_DATE = _fh_date(';  What = 'baseline constant' },
    @{ File = 'pages\models.py';                          Text = 'def ensure_expense_baseline';   What = 'expense baseline helper' },
    @{ File = 'pages\models.py';                          Text = 'def ensure_revenue_baseline';   What = 'revenue baseline helper' },
    @{ File = 'pages\views\finance.py';                   Text = '_fh_save_expense';              What = 'baseline-then-snapshot ordering' },
    @{ File = 'pages\templates\finance_expense_add.html';  Text = 'name="effective_date"';        What = 'effective-date field' },
    @{ File = 'pages\templates\finance_expense_edit.html'; Text = 'name="effective_date"';        What = 'effective-date field' },
    @{ File = 'pages\templates\finance_revenue_add.html';  Text = 'name="effective_date"';        What = 'effective-date field' },
    @{ File = 'pages\templates\finance_revenue_edit.html'; Text = 'name="effective_date"';        What = 'effective-date field' },
    @{ File = 'pages\views\tenants.py';                   Text = 'PAYMENT_DATA_STARTS';           What = '1-Aug-2026 cutoff' },
    @{ File = 'pages\views\tenants.py';                   Text = 'PAYMENT_GRACE_DAYS';            What = '7-day grace band' },
    @{ File = 'pages\urls.py';                            Text = 'tenant_payment_days';           What = 'report route' },
    @{ File = 'pages\templates\tenant_payment_days.html'; Text = 'pd-detail-table';               What = 'report template (mobile fix)' },
    @{ File = 'pages\templates\base.html';                Text = 'data-menu-toggle';              What = 'shared dropdown JS' },
    @{ File = 'pages\middleware.py';                      Text = '_CONNECTIVITY_ERRNOS';          What = 'errno classification' },
    @{ File = 'pages\middleware.py';                      Text = 'charset=utf-8';                 What = 'error page charset' },
    @{ File = 'pages\help_content\operational.html';      Text = 'Payment Behaviour';             What = 'Tenants help section' },
    @{ File = 'pages\models.py';                          Text = 'def ensure_expense_opening';    What = 'opening zero snapshot' },
    @{ File = 'pages\views\finance.py';                   Text = 'def _fh_close_expense';         What = 'closing snapshot on un-tick' },
    @{ File = 'pages\views\finance.py';                   Text = '_fh_old_group';                 What = 'pro-rata edit updates in place' },
    @{ File = 'pages\templates\finance_expense_add.html';  Text = "{% now 'Y' %}-01-01";          What = 'add form defaults to 1 January' },
    @{ File = 'pages\templates\finance_revenue_add.html';  Text = "{% now 'Y' %}-01-01";          What = 'add form defaults to 1 January' },
    @{ File = 'pages\templates\finance_expense_line_types_edit.html'; Text = 'fh-applies-from';  What = 'line-type change is datable' },
    @{ File = 'pages\models.py';                          Text = 'def purge_figure_history';     What = 'purge on a complete removal' },
    @{ File = 'pages\views\finance.py';                   Text = "request.POST.get('delete_mode')"; What = 'delete asks what it means' },
    @{ File = 'pages\templates\finance_expense.html';     Text = 'id="expenseDeleteModal"';      What = 'delete dialog replaces confirm()' },
    @{ File = 'pages\templates\finance_expense_line_types.html'; Text = 'id="ltd-choice"';       What = 'line-type delete offers both' },
    @{ File = 'pages\templates\finance_expense_line_types.html'; Text = 'delete-dialog fits the viewport'; What = 'dialog stays on screen' },
    @{ File = 'pages\views\finance.py';                   Text = 'That is a pro-rata expense';    What = 'pro-rata rows refuse deletion' },
    @{ File = 'pages\templates\finance_expense.html';     Text = 'title="Pro-rata expense';       What = 'pro-rata Delete greyed out' },
    @{ File = 'pages\templates\finance_expense_edit.html'; Text = 'take up its share';            What = 'un-ticking is explained' }
)

foreach ($s in $sentinels) {
    $p = Join-Path $root $s.File
    $label = '{0}  ({1})' -f $s.File, $s.What
    if (-not (Test-Path $p)) { Bad ($label + '  - FILE MISSING'); $problems++; continue }
    $hit = Select-String -LiteralPath $p -Pattern $s.Text -SimpleMatch -Quiet
    if ($hit) { Good $label } else { Bad ($label + '  - not found'); $problems++ }
}

if ($problems -and -not $Force) {
    Write-Host ''
    Bad ("$problems sentinel check(s) failed - refusing to go further.")
    Say  '        Re-run the relevant apply_*.py patcher, or pass -Force if you'
    Say  '        are certain the sentinel string is simply out of date.'
    exit 1
}

# ------------------------------------------------------------ 2. migrations
Head 'Do these changes need a migration?'
# --check exits 1 both when a migration is missing AND when the command itself
# blows up, so the exit code alone cannot be trusted - read the output too.
$mmOut = & python manage.py makemigrations --check --dry-run 2>&1
$mmCode = $LASTEXITCODE
$mmOut | ForEach-Object { Say ('  ' + $_) }
$mmText = ($mmOut | Out-String)

if ($mmCode -eq 0 -or $mmText -match 'No changes detected') {
    Good 'no model changes outstanding - nothing to migrate'
} elseif ($mmText -match 'Traceback|ImproperlyConfigured|OperationalError|Unknown command') {
    Warn 'makemigrations could not run (settings or database) - check this by hand'
} else {
    Bad 'Django wants a migration.  Generate and review it before pushing.'
    if (-not $Force) { exit 1 }
}

Head 'Django system check'
$chkOut = & python manage.py check 2>&1
$chkOut | ForEach-Object { Say ('  ' + $_) }
if ($LASTEXITCODE -ne 0) {
    Bad 'manage.py check failed'
    if (-not $Force) { exit 1 }
} else {
    Good 'no issues'
}

# ----------------------------------------------------------------- 3. tests
Head 'Test suites'
$suites = @(
    'test_effective_date_baseline.py',
    'test_prorata_history.py',
    'test_delete_choice.py',
    'test_tenant_payment_days.py',
    'test_db_error_page.py'
)
foreach ($t in $suites) {
    if (-not (Test-Path (Join-Path $root $t))) { Warn ($t + ' not present - skipped'); continue }
    Say ''
    Say ('  == ' + $t)
    & python $t 2>&1 | ForEach-Object { Say ('     ' + $_) }
    if ($LASTEXITCODE -ne 0) {
        Bad ($t + ' FAILED')
        if (-not $Force) { Say ''; Say '  Stopping.  Nothing has been staged.'; exit 1 }
    }
}

# ---------------------------------------------------------------- 4. tidy up
# test_db_error_page.py writes two sample pages into the repo root every run.
# They are output, not source, so they belong in .gitignore rather than in a
# commit.  Anchored with a leading slash so only the root copies are ignored.
Head 'Housekeeping'

$gi = Join-Path $root '.gitignore'
$giText = Get-Content -LiteralPath $gi -Raw
if ($null -eq $giText) { $giText = '' }
if ($giText -notmatch '(?m)^/error_\*\.html\s*$') {
    if ($Apply) {
        $nl = if ($giText.Contains("`r`n")) { "`r`n" } else { "`n" }
        if (-not $giText.EndsWith("`n")) { $giText += $nl }
        $giText += ($nl + '# Sample pages written by test_db_error_page.py' + $nl + '/error_*.html' + $nl)
        # WriteAllText with a no-BOM encoder: Set-Content -Encoding UTF8 would
        # prepend a BOM on Windows PowerShell 5.1.
        [System.IO.File]::WriteAllText(
            $gi, $giText, (New-Object System.Text.UTF8Encoding($false)))
        Good '.gitignore now ignores the root error_*.html samples'
    } else {
        Say '  would add "/error_*.html" to .gitignore  (test output, not source)'
    }
} else {
    Good '.gitignore already ignores the root error_*.html samples'
}

foreach ($f in @('error_schema.html', 'error_connectivity.html')) {
    $p = Join-Path $root $f
    if (Test-Path $p) {
        if ($Apply) { Remove-Item -LiteralPath $p -Force; Good ('removed ' + $f) }
        else        { Say ('  would remove ' + $f + '  (regenerated by the test)') }
    }
}

Say ''
Say '  .bak_* files are already covered by .gitignore - leaving them alone.'

# --------------------------------------------------------------- 5. the diff
Head 'What would be committed'
$status = & git status --porcelain
if (-not $status) { Say '  (working tree clean - nothing to do)'; exit 0 }

$status | ForEach-Object { Say ('  ' + $_) }

Say ''
$stat = & git diff --stat
if ($stat) { $stat | ForEach-Object { Say ('  ' + $_) } }

# ------------------------------------------------------------ 6. commit/push
if (-not $Apply) {
    Head 'Nothing has been changed'
    Say '  This was a dry run.'
    Say ''
    Say '  To commit:            .\Push-PendingChanges.ps1 -Apply'
    Say '  To commit and push:   .\Push-PendingChanges.ps1 -Push'
    exit 0
}

Head 'Commit'
& git add -A
if ($LASTEXITCODE -ne 0) { Bad 'git add failed'; exit 1 }

& git commit -m $Message `
    -m 'The pro-rata expense edit deleted every row in a (line type, expense type) group and recreated it, so every expense_id changed and every snapshot keyed on it was orphaned. That is what destroyed the Company Tax trail: the audit found ten dead expense_ids holding thirty unreachable snapshots. The branch now matches rows on the natural key the add screen already uses and updates them in place.' `
    -m 'Un-ticking a property zeroes its row and snapshots that, instead of deleting it. Deleting took the row past with it, because the P&L only re-colours rows that still exist, so prior years silently lost that property share.' `
    -m 'Creating a row writes a zero opening snapshot at FH_BASELINE_DATE. Without one a new row had no history covering earlier years, so the caller fell back to its live cells - a budget line added in August 2026 showed a full year of spend in 2024 while January to July of 2026 vanished.' `
    -m 'The two add forms now default Applies from to 1 January of the current year; the edit forms still default to today. A budget entered mid-year counts for the whole year, and the date field genuinely controls which years a figure reaches.' `
    -m 'Edit Expense Line Type gained an Applies from field, shown only when the pro-rata amount actually changes. It was the last screen that could change a figure without dating it, and for a pro-rata line it is the ONLY place the figure can change - the amount is read-only on the expense itself.' `
    -m 'Deleting an expense now asks what delete means: stop it from a date, keeping every earlier year intact, or remove it and its history completely. Same choice when deleting a line type, where stopping keeps the line type because its expenses carry the history. Removing completely now also deletes the snapshots, which is what stops them becoming orphans.' `
    -m 'A pro-rata expense row can no longer be deleted on its own - it is a share of the amount on the line type, and removing one row leaves the others holding shares of a larger split, so the line stops adding up to the charge owed. Delete is greyed out on those rows and refused server-side; un-ticking the property on the edit screen re-divides the amount and closes the row with the same zero snapshot.' `
    -m 'Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>'
if ($LASTEXITCODE -ne 0) { Bad 'git commit failed'; exit 1 }
Good 'committed'
Say ''
& git --no-pager log -1 --stat | ForEach-Object { Say ('  ' + $_) }

if (-not $Push) {
    Head 'Committed but not pushed'
    Say ('  Push when ready:   git push origin ' + $branch)
    exit 0
}

Head 'Push'
Say ('  pushing ' + $branch + ' to ' + $origin)
& git push origin $branch 2>&1 | ForEach-Object { Say ('  ' + $_) }
if ($LASTEXITCODE -ne 0) { Bad 'git push failed'; exit 1 }
Good 'pushed'

Write-Host ''
Write-Host 'Railway will build and deploy from this push.' -ForegroundColor Cyan
Write-Host 'Migrations run automatically on deploy; this batch adds none.' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Worth checking on Live once the deploy is green:' -ForegroundColor Cyan
Write-Host '  1. Finance > add an expense - Applies from is prefilled 1 January'
Write-Host '  2. Finance > edit an expense - Applies from is prefilled today'
Write-Host '  3. Edit a pro-rata line, change nothing, save - then re-run'
Write-Host '     .\Show-HistoryOrphans.ps1 and confirm the orphan count has NOT moved'
Write-Host '  4. Company Tax still reads 3,500 + 3,500 before Jul-2026 and 3,300 + 3,300 after'
