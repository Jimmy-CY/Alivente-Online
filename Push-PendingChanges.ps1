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
    The commit subject. REQUIRED to commit - there is deliberately no default,
    because a default is a message that describes the last change rather than
    this one, and that is exactly what went wrong on the 24 Aug push.

.PARAMETER Body
    Optional paragraphs for the commit body, one string each.

.PARAMETER Checks
    What to verify on Live once this deploy is green, one string each.

    There is deliberately no default. The footer used to be four hardcoded
    lines about the effective-date round, and it kept printing them for three
    weeks after that work shipped - describing the LAST change rather than
    this one. That is exactly the failure -Message exists to prevent for the
    commit subject, and it had the same cause.

    Omit it and the footer says plainly that nothing was specified, rather
    than inventing something to check.

.EXAMPLE
    .\Push-PendingChanges.ps1
    Verify and report.  Changes nothing.

.EXAMPLE
    .\Push-PendingChanges.ps1 -Push
    Verify, tidy, commit and push.

.EXAMPLE
    .\Push-PendingChanges.ps1 -Push -Message "..." -Checks `
        "Suppliers: the Country filter returns one row for Greece", `
        "Properties: an Inactive property reads grey, not red"
    The -Checks lines are printed after the push, numbered, and nowhere else.
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Push,
    [switch]$Force,
    [string]$Message,
    [string[]]$Body = @(),
    [string[]]$Checks = @()
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
    @{ File = 'pages\templates\finance_expense_edit.html'; Text = 'take up its share';            What = 'un-ticking is explained' },
    @{ File = 'pages\views\properties.py';                Text = 'def _prorata_blockers';         What = 'deactivation blocked while shares remain' },
    @{ File = 'pages\templates\finance_expense_add.html';  Text = 'is-inactive';                  What = 'inactive cannot be ticked' },
    @{ File = 'pages\templates\finance_expense_edit.html'; Text = 'is-inactive-linked';           What = 'inactive-but-linked stays removable' },
    @{ File = 'pages\models.py';                          Text = '_projectable';                 What = 'no assumed rent for inactive' },
    @{ File = 'pages\views\finance.py';                  Text = 'No prop_status filter';        What = 'P&L reports a year, not today' },
    @{ File = 'pages\templates\finance_pl_act.html';     Text = 'pl-inactive-pill';             What = 'picker flags inactive' },
    @{ File = 'pages\views\properties.py';                Text = 'show_blocker_modal';           What = 'refusal shown on the edit page' },
    @{ File = 'pages\templates\properties_edit.html';     Text = 'statusBlockModal';             What = 'deactivation dialog' },
    @{ File = 'pages\templates\properties_edit.html';     Text = 'checkStatusBlockers';          What = 'Save refuses before submitting' },
    @{ File = 'pages\models.py';                          Text = 'def prorata_reconcile';        What = 'the split adds up to the charge' },
    @{ File = 'pages\views\finance.py';                  Text = '_pr_fixed';                    What = 'reconciled before saving' },
    @{ File = 'pages\admin.py';                           Text = 'FinancialFigureHistoryAdmin';  What = 'read-only history in the admin' },
    @{ File = 'pages\templates\finance_expense_add.html'; Text = 'residual on the largest share'; What = 'preview matches the save' },
    @{ File = 'pages\views\finance.py';                   Text = 'ind_props, ind_skipped';        What = 'indicators gate on the year' },
    @{ File = 'pages\views\finance.py';                   Text = 'ind_value_purchase';            What = 'value increase matched to purchase' },
    @{ File = 'pages\templates\finance_pl_act.html';      Text = 'divide:ind_purchase_total';     What = 'ROI divides by contributors' },
    @{ File = 'pages\templates\finance_pl_act.html';      Text = 'roi-basis';                     What = 'the exclusion is visible' },
    @{ File = 'pages\templates\finance_pl_act.html';      Text = 'selectAllIncBtn';               What = 'Select All is split' },
    @{ File = 'pages\templates\finance_pl_act.html';      Text = 'function markPanelState';       What = 'picker survives a selection' },
    @{ File = 'pages\views\finance.py';                   Text = 'ind_value_count';               What = 'value increase reports its coverage' },
    @{ File = 'pages\templates\finance_pl_act.html';      Text = 'roi-basis-val';                  What = 'the second denominator is visible' },
    @{ File = 'pages\help_content\reports.html';          Text = 'Which properties count';         What = 'P&L help explains the gate' },
    @{ File = 'pages\help_content\reports.html';          Text = 'Always a year, then Budget';     What = 'P&L help matches the toggle' },
    @{ File = 'pages\help_content\operational.html';      Text = 'A worked month';                 What = 'invoice help gives the dates' },
    @{ File = 'pages\help_content\operational.html';      Text = 'tenant-name order';              What = 'invoice help explains numbering' },
    @{ File = 'pages\views\issues.py';                    Text = 'Reports (7):';                   What = 'legacy lease_renewal view gone' },
    @{ File = 'pages\views\issues.py';                    Text = 'could never be written on Live'; What = 'and the reason is recorded' },
    @{ File = 'pages\views\administration.py';            Text = 'can_access_administration -> admin_apms'; What = 'legacy admin views gone' },
    @{ File = 'pages\help_content\administration.html';   Text = 'nothing to press';               What = 'admin help matches the page' },
    @{ File = 'pages\templates\base.html';                Text = '--alv-accent:';                  What = 'one accent, defined once' },
    @{ File = 'pages\templates\base.html';                Text = '.btn-info,';                     What = 'Bootstrap info overridden' },
    @{ File = 'pages\templates\base.html';                Text = '--alv-table-std';                 What = 'table standard hoisted into base' },
    @{ File = 'pages\templates\base.html';                Text = '.icon-action-btn {';              What = 'the house icon button has one home' },
    @{ File = 'pages\templates\base.html';                Text = '.mobile-action-bar {';            What = 'and so does the mobile action bar' },
    @{ File = 'pages\templates\base.html';                Text = '.sidebar-toggle:hover { background: #0a5e6a;'; What = 'sidebar hover uses the new ink' },
    @{ File = 'pages\templates\suppliers.html';           Text = 'border-color: #0a5e6a';         What = 'and so does a page-local btn-info hover' },
    @{ File = 'pages\templates\suppliers.html';           Text = 'class="table alv-table suppliers-table"'; What = 'Suppliers is on the standard' },
    @{ File = 'pages\templates\suppliers.html';           Text = 'No suppliers to show';            What = 'and finally has an empty state' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-table .desktop-action-cell';  What = 'action columns stay centred' },
    @{ File = 'pages\templates\base.html';                Text = '.row-actions {';               What = 'and one actions cell holds them' },
    @{ File = 'pages\templates\suppliers.html';           Text = '<span class="row-actions">';     What = 'Suppliers has ONE actions column' },
    @{ File = 'pages\templates\base.html';                Text = 'position: sticky;';            What = 'headings stick when you scroll' },
    @{ File = 'pages\templates\base.html';                Text = 'overflow: clip;';             What = 'and the container lets them' },
    @{ File = 'pages\templates\base.html';                Text = '--alv-ink-strong:';           What = 'headings have their own ink' },
    @{ File = 'pages\views\suppliers.py';                 Text = '"distinct_countries": distinct_countries,'; What = 'the Country filter finally has options' },
    @{ File = 'pages\templates\properties.html';          Text = 'class="table alv-table properties-table"'; What = 'Properties is on the standard' },
    @{ File = 'pages\templates\properties.html';          Text = 'alv-pill-neutral{% endif %}';          What = 'and Inactive is grey, not red' },
    @{ File = 'pages\templates\properties.html';          Text = 'mobile-action-bar cols-4';            What = 'its mobile bar declares four columns' },
    @{ File = 'pages\templates\base.html';                Text = '.table-container.is-stuck';            What = 'a stuck heading says so' },
    @{ File = 'pages\templates\base.html';                Text = 'alv-sticky-cue';                What = 'and the observer that sets it' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-table .cell-actions,';       What = 'ONE rule aligns the Actions column' },
    @{ File = 'pages\templates\base.html';                Text = '--alv-card-std';                 What = 'cards have a home' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-card-lead';                 What = 'and the first one may be louder' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-tag-slate';                 What = 'categories are off the semantic scale' },
    @{ File = 'pages\templates\base.html';                Text = '--alv-print-std';                What = 'and reports survive a printer' },
    @{ File = 'pages\templates\base.html';                Text = 'overflow: clip;';                What = 'a card cannot trap a sticky heading' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-tag-plum';                   What = 'a fifth tone for the fifth type' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-tag-sky::before';            What = 'and the dot belongs to the tone' },
    @{ File = 'pages\templates\property_report.html';     Text = 'alv-table assets-table';          What = 'the report tables are on the standard' },
    @{ File = 'pages\templates\property_report.html';     Text = 'alv-pill alv-pill-attn';          What = 'and an expired warranty is amber' },
    @{ File = 'pages\templates\property_assets.html';     Text = 'alv-table asset-table';           What = 'Property Assets is on the standard' },
    @{ File = 'pages\templates\property_assets.html';     Text = 'alv-card-aside alv-tag';          What = 'and each group is a card' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'alv-card alv-card-lead';          What = 'Asset Details leads with the asset' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'alv-table maintenance-table';     What = 'its maintenance table is on the standard' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'desktop-action-cell cell-actions'; What = 'with ONE actions column' },
    @{ File = 'pages\templates\base.html';                Text = '--alv-actions-std';               What = 'the page-header bar has a home' },
    @{ File = 'pages\templates\base.html';                Text = '.page-action-buttons .action-danger'; What = 'destructive is a tone, not a verb' },
    @{ File = 'pages\templates\base.html';                Text = '.page-action-buttons .action-more-btn'; What = 'and the More button keeps its edge' },
    @{ File = 'pages\templates\base.html';                Text = 'pointer-events: none';            What = 'a disabled button is not a live link' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'btn action-primary';              What = 'Edit is the primary, not yellow' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'action-secondary action-danger';  What = 'and Delete is outlined, not solid red' }
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
    'test_pl_historical.py',
    'test_prorata_rounding.py',
    'test_tenant_payment_days.py',
    'test_db_error_page.py',
    'test_pl_indicators.py',
    'test_help_pl.py',
    'test_help_physical_invoices.py',
    'test_remove_legacy_reports.py',
    'test_deeper_teal.py',
    'test_table_standard.py',
    'test_accent_shades.py',
    'test_table_suppliers.py',
    'test_table_polish.py',
    'test_supplier_countries.py',
    'test_table_properties.py',
    'test_sticky_cue.py',
    'test_card_standard.py',
    'test_detail_property.py',
    'test_action_standard.py'
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

if (-not $Message) {
    Bad 'No commit subject.'
    Say '  There is no default on purpose - a default describes the previous'
    Say '  change, not this one. Pass one:'
    Say ''
    Say '     .\Push-PendingChanges.ps1 -Push -Message "what changed" `'
    Say '        -Body "why", "and any detail worth keeping"'
    exit 1
}

& git add -A
if ($LASTEXITCODE -ne 0) { Bad 'git add failed'; exit 1 }

$commitArgs = @('commit', '-m', $Message)
foreach ($p in $Body) { $commitArgs += @('-m', $p) }
$commitArgs += @('-m', 'Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>')
& git @commitArgs
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
if ($Checks.Count -gt 0) {
    Write-Host 'Worth checking on Live once the deploy is green:' -ForegroundColor Cyan
    for ($i = 0; $i -lt $Checks.Count; $i++) {
        Write-Host ('  {0}. {1}' -f ($i + 1), $Checks[$i])
    }
} else {
    Write-Host 'No post-deploy checks were given for this batch.' -ForegroundColor DarkYellow
    Write-Host 'Pass -Checks "..." , "..." next time if there is something to look at.'
}
