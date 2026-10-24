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
    [string[]]$Checks = @(),
    # GT-2, 17 Oct 2026 - E17. A failure at suite 300 should restart at
    # 300, not at 1. alv_run.py decides what may be skipped: a suite is
    # only skipped when NOTHING IT COULD READ has changed since the run
    # that passed it, which alv_impact answers. Everything else re-runs.
    [switch]$Resume,
    # WK-1, 23 Oct 2026 - HOW MANY SUITES RUN AT ONCE.
    #
    # alv_run.py has had --workers since GT-2 and defaults to 6. This
    # script could not pass it, so the only way to sweep at 3 was to
    # run alv_run.py by hand and then push - which Demetri had to do
    # twice on 23 October after rc=3221227274 (0xC0000374, Windows
    # heap corruption under pool contention) killed a sweep at suite
    # 371 and again at 370. Both suites passed when re-run alone.
    #
    # ZERO MEANS SAY NOTHING. The argument is only added when it is
    # asked for, so a push that does not mention workers behaves
    # exactly as every push before this round did.
    [int]$Workers = 0,
    # DP-1, 22 Oct 2026 - WAIT FOR THE DEPLOY, DO NOT ANNOUNCE IT.
    # Push 4 and push 5 both ended by saying Railway would build and
    # deploy, and in both cases it did not. -Site is where to ask,
    # -WaitMinutes is how long to care, -NoWait skips it entirely.
    [string]$Site = 'https://alivente.online',
    [int]$WaitMinutes = 8,
    [switch]$NoWait
)

# Deliberately NOT 'Stop'.  Under 'Stop', anything a native command writes to
# stderr and we redirect with 2>&1 becomes a terminating NativeCommandError -
# git and manage.py both do this routinely.  Control flow here is driven by
# exit codes instead, which is what we actually want to branch on.
$ErrorActionPreference = 'Continue'
if ($Push) { $Apply = $true }

# GT-1, 12 Oct 2026 - THE SAME REFUSAL, ASKED EARLY.
#
# The real check is beside `Head 'Commit'` at the bottom of this
# file and is unchanged; it is what actually guards the commit.
# This is a pre-flight with the same words, because the bottom of
# this file is 330 suites, two drift guards, makemigrations and a
# Django check away from the top. E-10 paid all of that and was
# then refused for want of a one-line subject.
#
# A dry run is not blocked: it has no subject to want.
if ($Apply -and -not $Message) {
    Write-Host ''
    Write-Host '  ! No commit subject, and this run would commit.'
    Write-Host ''
    Write-Host '    There is no default on purpose - a default describes the'
    Write-Host '    previous change, not this one. Pass one:'
    Write-Host ''
    Write-Host '       .\Push-PendingChanges.ps1 -Push -Message <what changed>'
    Write-Host ''
    Write-Host '    Asked here rather than after the suites, which is where'
    Write-Host '    it used to be asked. See GT-1.'
    Write-Host ''
    exit 1
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Every python this script spawns prints through a pipe, and on Windows a
# pipe is cp1252 unless told otherwise. A suite that prints a Greek heading
# then dies of UnicodeEncodeError blocks the push exactly as hard as a
# failing check, while saying nothing about what is wrong. The empty
# encoding before the colon means KEEP whatever the console has and change
# only the error handler - forcing utf-8 here would hand PowerShell bytes
# it decodes as cp1252, which is mojibake, which reads like a data fault.
# Each tool carries the same guard in its own preamble; this is the belt to
# that pair of braces, and covers the next tool somebody writes without one.
$env:PYTHONIOENCODING = ':replace'

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

# ------------------------------------------ 0b. does the tree know it?
#
# PG-1, 18 Oct 2026 - E24. Twice in two days a push went through with a
# subject naming rounds the tree did not contain: an unextracted zip on
# 16 Oct, and six rounds delivered without their .bak_ files on 17 Oct.
# Both looked green all the way down, because everything downstream
# reads the tree in front of it and that tree was self-consistent.
#
# alv_preflight.py reads the SUBJECT and asks two things of each round
# it names: does alv_rounds.py have an entry for it, and is there a
# backup on disk. Both answers are already in the tree; neither is
# hand-kept here.
#
# HERE, not at the bottom. A wrong subject should cost seconds. GT-1
# moved the missing-subject refusal up for the same reason.
#
# IN PYTHON, not in this file. There is no PowerShell in the sandbox,
# so anything written here ships untested - GT-2's lesson, and the
# reason this is five lines and a call.
if ($Apply -and $Message) {
    & python (Join-Path $root 'alv_preflight.py') $Message 2>&1 |
        ForEach-Object { Say $_ }
    if ($LASTEXITCODE -ne 0) {
        Bad 'the subject names a round this tree does not have'
        if (-not $Force) {
            Say ''
            Say '  Stopping.  Nothing has been staged.'
            exit 1
        }
    }
}

# ------------------------------------------------------- 1. is it applied?
# Each change leaves a distinctive string behind.  If one is missing the tree
# is only half-patched and must not be committed.
Head 'Are all the changes actually in the tree?'

$sentinels = @(
    @{ File = 'pages\templates\base.html'; Text = 'PU-1b, 3 Oct 2026'; What = 'PU-1b: a scroll inside the popup no longer closes it' },
    @{ File = 'pages\templates\unit_conversions_management.html'; Text = 'UC-1b, 3 Oct 2026'; What = 'UC-1b: the scope toggle uses icons, which CSS can colour' },
    @{ File = 'pages\templates\preview_imported_recipe.html'; Text = 'form="saveRecipeForm"'; What = 'RE-1: the bar Update owns the form it is outside of' },
    @{ File = 'pages\templates\preview_imported_recipe.html'; Text = 'btn btn-secondary btn-lg'; Absent = $true; Code = $true; What = 'RE-1: and the bottom Cancel is gone' },
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = 'function hasPrintableList()'; What = 'SL-1: Print refuses when there is nothing to print' },
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = 'id="printBtn" hidden'; What = 'SL-1: and the button is not there until there is' },
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = 'function setBar(step)'; What = 'SL-2: one bar, and it says which step you are on' },
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = 'step-navigation'; Absent = $true; Code = $true; What = 'SL-2: and both bottom bars are gone' },
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = 'share-whatsapp'; What = 'SL-3: the one kept literal is named, not stray' },
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = '#28a745'; Absent = $true; Code = $true; What = 'SL-3: and the green is gone - a step is not a verdict' },
    @{ File = 'pages\services\portfolio_insights.py'; Text = 'def renewal_due('; What = 'DB-9: one function decides the renewal window' },
    @{ File = 'pages\views\notifications_dashboard.py'; Text = 'renewal_due(today=today, status=''pending'')'; What = 'DB-9: the Expiring Leases tile calls it' },
    @{ File = 'pages\views\notifications_dashboard.py'; Text = 'expiring_no_successor'; Absent = $true; What = 'DB-9: and the dashboard does NOT reach for the cash cliff' },
    @{ File = 'pages\templates\home.html'; Text = 'Inside their renewal period'; What = 'DB-9: the panel says what it shows' },
    @{ File = 'pages\templates\unit_conversions_management.html'; Text = 'alv-pill alv-pill-info conversion-number'; What = 'UC-1: the quantity chips are house pills' },
    @{ File = 'pages\templates\unit_conversions_management.html'; Text = '#ffc107'; Absent = $true; Code = $true; What = 'UC-1: and the amber is gone - a scope is not a verdict' },
    @{ File = 'pages\templates\base.html'; Text = 'ALV POP v1'; What = 'PU-1: one popup component, in a fixed layer' },
    @{ File = 'pages\templates\categories_management.html'; Text = 'ingredient-popup'; Absent = $true; Code = $true; What = 'PU-1: and the page keeps no copy of its own' },
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = 'data-live-search-cell="Ingredient Name"'; What = 'IB-1: the ingredient search narrows as you type' },
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = 'class="btn action-filter" id="filterBtn"'; What = 'IB-1: the filter folds behind a button' },
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = 'filter-bar'; Absent = $true; Code = $true; What = 'IB-1: and the always-open card is gone' },
    # NO APOSTROPHE IN A SENTINEL TEXT. PowerShell escapes one inside a
    # single-quoted string by DOUBLING it, not with a backslash, and the
    # first cut of this row wrote THE HEADER\'S - which reached the gate as
    # a backslash and resolved against nothing. The text below says the
    # same thing and has no quote in it at all.
    @{ File = 'pages\templates\base.html'; Text = 'TWO LABELS - IB-1, 2 Oct 2026'; What = 'IB-1: base swaps the panel header labels instead of a fifth local copy' },
    @{ File = 'pages\templates\recipe_management.html'; Text = 'B-1c, 2 Oct 2026: AND THEN THE NOTE ABOVE DID IT AGAIN'; What = 'B-1c: the Favourites note names the comment syntax rather than writing it' },
    @{ File = 'pages\views\tenants.py'; Text = 'TN-1, 2 Oct 2026'; What = 'TN-1: the tenants list defaults to current' },
    @{ File = 'pages\templates\tenant.html'; Text = 'Include past tenants'; What = 'TN-1: the toggle is on the Tenants bar' },
    @{ File = 'pages\templates\recipe_management.html'; Text = 'B-1b, 2 Oct 2026: THIS NOTE USED TO SIT INSIDE THE TAG'; What = 'B-1b: the Favourites note sits above its tag, not inside it' },
    @{ File = 'pages\templates\base.html'; Text = '.icon-list       { color: var(--alv-view)'; What = 'ML-1: base carries the shopping-list NAME on the view colour' },
    @{ File = 'pages\templates\recipe_management.html'; Text = 'aria-pressed="{% if show_favourites %}true'; What = 'B-1: Favourites says its state with aria-pressed' },
    @{ File = 'pages\templates\base.html'; Text = '.btn.action-secondary[aria-pressed="true"]'; What = 'B-1: base gives a pressed secondary a visible state' },
    @{ File = 'pages\templates\view_recipe.html'; Text = 'btn btn-danger action-secondary'; Absent = $true; Code = $true; What = 'B-1: no control wears a Bootstrap colour on top of a house role' },
    @{ File = 'pages\templates\recipe_management.html'; Text = 'data-recipe-name='; What = 'J-2: the recipe buttons carry the name as an attribute' },
    @{ File = 'pages\templates\recipe_management.html'; Text = 'onclick="deleteRecipe('; Absent = $true; Code = $true; What = 'J-2: no Delete button builds a handler around the recipe name' },
    @{ File = 'pages\templates\act_expense.html'; Text = 'reportViewInvoice'; Absent = $true; Code = $true; What = 'J-2: the Report drill icon no longer calls a hand-built handler' },
    @{ File = 'pages\templates\celebration_management.html'; Text = 'span class="contact-name"'; What = 'C-1: the contact name has a span of its own' },
    @{ File = 'pages\templates\celebration_management.html'; Text = 'THE COLLAPSED COMPACT CARD IS A LIST ROW'; What = 'C-1: the compact card rules are on the page' },
    @{ File = 'pages\templates\celebration_management.html'; Text = '}In compact'; Absent = $true; What = 'C-1: the stray close-comment that killed two rules has not come back' },
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = 'Desktop: [New Customer Invoice] [Help]'; What = 'A-BAR: Help sits BEHIND the primary on Physical Invoices' },
    @{ File = 'pages\templates\properties_edit.html'; Text = 'A-BAR, 2 Oct 2026. Assets came before Save'; What = 'A-BAR: Save sits ahead of Assets on the property edit form' },
    @{ File = 'pages\templates\celebration_calendar.html'; Text = 'class="btn btn-info"'; Absent = $true; Code = $true; What = 'A-BAR: the Calendar/Timeline toggle is no longer Bootstrap btn-info' },
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
    # SUPERSEDED 29 Aug 2026, seventh instance of the section-4b pattern. This
    # pinned `title="Pro-rata expense` - the attribute and its first words. The
    # spent-row round made that title conditional, so the row now reads
    # `title="{% if exp.is_closed %}...{% else %}Pro-rata expense ...`, and the
    # string with the quote attached stopped existing while the CLAIM was
    # untouched. Pin the ADVICE, which is the thing worth keeping, rather than
    # the punctuation around it.
    @{ File = 'pages\templates\finance_expense.html';     Text = 'Pro-rata expense &mdash; remove this property by editing'; What = 'pro-rata Delete greyed out' },
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
    # B-1, 5 Oct 2026: this read '... background: #0a5e6a;' until the
    # literal became the token it was already equal to. The sentinel
    # pins the SAME FACT in the new words - the sidebar hover is the
    # accent ink - and it is a stronger pin than before, because a
    # change to --alv-accent-ink now moves this hover with it.
    @{ File = 'pages\templates\base.html';                Text = '.sidebar-toggle:hover { background: var(--alv-accent-ink);'; What = 'sidebar hover uses the accent ink, by token' },
    # WAS: suppliers.html must contain 'border-color: var(--alv-accent-ink)'.
    # The accent-ink round asserted that Suppliers' own .btn-info:hover had
    # been moved onto the token, which was true and worth saying at the
    # time. DR-1, 4 Oct 2026, deleted that declaration outright - base
    # declares the identical thing and --alv-accent-ink resolves the same
    # either way, so the page was repeating base rather than overriding it.
    # The claim the accent-ink round was making still holds; it is just
    # made in base now, so that is where the row points. Rendered: all 22
    # pages paint identically before and after - test_btn_info.py.
    @{ File = 'pages\templates\base.html';                Text = '.btn-info:hover'; What = 'the btn-info hover ink lives in base, and no page repeats it' },
    @{ File = 'pages\templates\suppliers.html';           Text = 'border-color: var(--alv-accent-ink)'; What = 'and Suppliers no longer carries its own copy'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\suppliers.html';           Text = 'class="table alv-table suppliers-table"'; What = 'Suppliers is on the standard' },
    @{ File = 'pages\templates\suppliers.html';           Text = 'No suppliers to show';            What = 'and finally has an empty state' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-table .desktop-action-cell';  What = 'action columns stay centred' },
    @{ File = 'pages\templates\base.html';                Text = '.row-actions {';               What = 'and one actions cell holds them' },
    @{ File = 'pages\templates\suppliers.html';           Text = '<span class="row-actions">';     What = 'Suppliers has ONE actions column' },
    @{ File = 'pages\templates\base.html';                Text = 'position: sticky;';            What = 'headings stick when you scroll' },
    @{ File = 'pages\templates\base.html';                Text = 'and at top:0 with clip'; What = 'the TABLE container clips rather than hides, so a sticky heading has something to stick to' },
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
    @{ File = 'pages\templates\base.html';                Text = 'so a sticky heading inside a card has nothing'; What = 'the CARD clips rather than hides, same fault and same fix as the table container' },
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
    # WAS: '.page-action-buttons .action-danger', pinning the SCOPED form.
    # The module-wide sweep deliberately unscoped the tones - a tone is not
    # bar behaviour, and the same four names have to work in a modal footer
    # and on a report. So the expectation MOVED with the decision; deleting
    # the check would have been the wrong fix, and -Force would have been
    # worse. What it pins now is the .btn PAIRING, which is what makes a
    # tone beat a page's own .btn-danger on document order.
    #
    # A substring cannot express "unscoped" - that half is covered by
    # test_button_sweep.py section 1, which asserts the LAYOUT is still
    # scoped to .page-action-buttons while the tones are not.
    @{ File = 'pages\templates\base.html';                Text = '.icon-color-send'; What = 'base owns all seven icon colours, not four' },
    @{ File = 'pages\templates\base.html';                Text = '.icon-duplicate'; What = 'and Duplicate is a NAME on --alv-edit' },
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = 'table alv-table pi-table'; What = 'Physical Invoices is on the table standard' },
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = '{{ row.status_pill }}'; What = 'and its status class is decided in the view' },
    @{ File = 'pages\templates\customer_list.html';       Text = 'table alv-table customers-table'; What = 'Customers too, with ONE actions column' },
    @{ File = 'pages\views\physical_invoices.py';         Text = '_filter_chips'; What = 'the last filter holdout has chips, so it can have a Filter button' },
    @{ File = 'pages\templates\base.html';                Text = 'WIDENED from `.alv-filter`'; What = 'a form control is as tall as the value it shows' },
    @{ File = 'pages\templates\base.html';                Text = 'select.form-control:not([size]):not([multiple])'; What = 'and it matches Bootstrap own shape, or it loses on specificity' },
    @{ File = 'pages\templates\base.html';                Text = '.alv-filter.is-open'; What = 'ONE class says whether the filter panel is open' },
    @{ File = 'pages\templates\base.html';                Text = 'alv-filter script v1'; What = 'and one script reads it' },
    @{ File = 'pages\templates\suppliers.html';           Text = 'class="btn action-filter"'; What = 'the Filter button lives in the action bar' },
    @{ File = 'pages\templates\fsr.html';                 Text = 'class="alv-filter-active"'; What = 'the chips sit OUTSIDE the panel, so hiding it stays safe' },
    @{ File = 'pages\templates\base.html';                Text = '.btn.action-danger'; What = 'destructive is a tone, and it outranks a page btn-danger' },
    @{ File = 'pages\templates\base.html';                Text = '.page-action-buttons .action-more-btn'; What = 'and the More button keeps its edge' },
    @{ File = 'pages\templates\base.html';                Text = 'still a working link'; What = 'a disabled button is not a live link - base says pointer-events twice, so the row names THIS one' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'btn action-primary';              What = 'Edit is the primary, not yellow' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'action-secondary action-danger';  What = 'and Delete is outlined, not solid red' },
    @{ File = 'pages\templates\base.html';                Text = '.no-print { display: none !important; }'; What = 'paper stops printing the furniture - base says that declaration ten times, so the row names the rule' },
    @{ File = 'pages\templates\base.html';                Text = '.back-button {';                  What = 'and a report Back is quiet too' },
    @{ File = 'pages\templates\property_report.html';     Text = 'class="btn back-button"';          What = 'the Report Back joined' },
    @{ File = 'pages\templates\suppliers_edit.html';      Text = 'class="btn action-primary"';       What = 'Save is the primary on a form' },
    @{ File = 'pages\templates\property_assets.html';     Text = 'action-primary btn-sm';            What = 'and a small confirm stays small' },
    @{ File = 'pages\templates\base.html';                Text = '.btn.action-secondary';            What = 'a tone outranks a page btn-info' },
    @{ File = 'pages\templates\edit_asset.html';          Text = 'alv-card alv-card-lead form-card'; What = 'Edit Asset lost its yellow bar' },
    @{ File = 'pages\templates\edit_asset.html';          Text = 'class="btn action-back"';          What = 'and its Back joined the standard' },
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = 'desktop-action-cell cell-actions'; What = 'the Actions heading sits over the buttons it labels' },
    @{ File = 'pages\templates\customer_list.html';       Text = 'desktop-action-cell cell-actions'; What = 'and Customers matches it' },
    # Lease Renewals. The sentinel to care about is the SECOND one: it is the
    # contradiction this round existed to end. tenant_report paints a declined
    # renewal amber; this page painted it red, and WE made them disagree.
    @{ File = 'pages\templates\lease_renewal_report.html'; Text = 'alv-card renewal-card'; What = 'the renewal cards are base cards' },
    @{ File = 'pages\templates\lease_renewal_report.html'; Text = 'alv-pill alv-pill-attn"><i class="fas fa-times-circle"></i> Renewal declined'; What = 'and a declined renewal is amber HERE too, as it is on Tenants' },
    @{ File = 'pages\templates\lease_renewal_report.html'; Text = '.alv-pill i.fas { color: inherit; }'; What = 'the pill icon keeps the pill colour, not the head grey' },
    # Open Invoices. The FIRST of these is the one that matters - the table's
    # rows are decided in Python now rather than by three nested loops in the
    # template, which is what lets the page have an empty state at all.
    @{ File = 'pages\views\invoices.py';                  Text = 'def _open_invoice_rows'; What = 'the rows are built in the view, not by three nested loops' },
    @{ File = 'pages\views\invoices.py';                  Text = '"rows": _open_invoice_rows(iresults, filtered_props, filtered_tenants)'; What = 'and still from the FILTERED lists, so filtering still filters' },
    @{ File = 'pages\templates\invoices.html';            Text = 'class="table alv-table invoices-table"'; What = 'Open Invoices is on the table standard' },
    @{ File = 'pages\templates\invoices.html';            Text = '{% if not rows %}'; What = 'an empty result says so instead of looking like a failed load' },
    @{ File = 'pages\templates\invoices.html';            Text = '{% for name in all_prop_names %}'; What = 'the property dropdown lists every property, each once, not just the chosen one' },
    @{ File = 'pages\templates\invoices.html';            Text = '{% for name in all_tenant_names %}'; What = 'and the tenant dropdown lists each NAME once - a tenant row is per lease' },
    @{ File = 'pages\templates\base.html';                Text = '.mobile-action-bar.cols-1'; What = 'a single mobile action gets the whole card width' },
    # Icon buttons. The SECOND of these is a fault this session shipped: the
    # no-permission Paid tick wore `is-disabled`, which base defines only for
    # .status-btn, so it rendered exactly like the live one.
    @{ File = 'pages\templates\customer_list.html';       Text = 'alv-empty-title'; What = 'Invoice Customers uses base empty state, not its own' },
    @{ File = 'pages\templates\customer_list.html';       Text = '{% if not perms.auth.can_edit_invoices %} cols-2'; What = 'and the mobile bar asks for as many columns as it draws controls - three being base own default, so unnamed' },
    @{ File = 'pages\templates\invoices.html';            Text = 'icon-approve icon-disabled'; What = 'a disabled Paid tick wears a class base actually defines' },
    # Cash Receipts - a new module. The MIGRATION is not sentinelled here
    # because its filename is whatever makemigrations chose; test_cash_receipts.py
    # section 0b checks a migration creating CashReceipt exists, which is the
    # one thing that would otherwise deploy cleanly and then 500 on first use.
    @{ File = 'pages\models.py';                          Text = 'class CashReceipt(';        What = 'the receipt record' },
    @{ File = 'pages\models.py';                          Text = 'class CashReceiptNumbering('; What = 'and its own running counter, starting at CR-00372' },
    @{ File = 'pages\permissions.py';                     Text = 'can_access_receipts';       What = 'Receipts is its own grantable module' },
    @{ File = 'pages\views\users.py';                     Text = 'all_permissions = MODULE_PERMISSIONS'; What = 'and User Administration reads the shared list' },
    @{ File = 'pages\views_setup.py';                     Text = 'permissions_data = all_codenames()'; What = 'so does the seeder - one list, both tiers' },
    @{ File = 'pages\views\receipts.py';                  Text = 'def cash_receipt_commit';   What = 'issuing takes the number, saves and stores the PDF in one transaction' },
    @{ File = 'pages\urls.py';                            Text = 'name="cash_receipt_list"';  What = 'the receipts list is routed' },
    @{ File = 'pages\templates\base.html';                Text = "url 'cash_receipt_list'";   What = 'and reachable from the menu' },
    # Receipts, round 2: editable, unvoidable, shown in the house PDF modal.
    @{ File = 'pages\views\receipts.py';                  Text = 'def cash_receipt_unvoid';   What = 'a void can be lifted - a receipt is not an invoice' },
    @{ File = 'pages\views\receipts.py';                  Text = 'def store_pdf';             What = 'and one place re-renders the stored PDF, deleting the old file' },
    @{ File = 'pages\urls.py';                            Text = 'name="cash_receipt_update"'; What = 'a receipt can be edited - everything but the number' },
    @{ File = 'pages\models.py';                          Text = 'edited_at = models.DateTimeField'; What = 'and the edit is stamped, because the sent copy cannot be recalled' },
    @{ File = 'pages\templates\cash_receipts.html';       Text = "include 'components/pdf_viewer.html'"; What = 'the PDF opens in the house modal, with share and download' },
    # Valuations. The FIRST is the one that mattered: the page named its own
    # shell, so base's sticky observer - which looks for .table-container -
    # had never seen it.
    @{ File = 'pages\templates\finance_valuations.html';  Text = 'class="table-container"'; What = 'Valuations uses the shell base actually looks for' },
    @{ File = 'pages\templates\finance_valuations.html';  Text = 'table alv-table valuations-table'; What = 'and is on the table standard' },
    @{ File = 'pages\templates\finance_valuations.html';  Text = '<tfoot>';                 What = 'its TOTAL row is a footer, not a record' },
    @{ File = 'pages\views\finance.py';                   Text = 'def _valuation_rows';     What = 'the rows and the three filter chains moved into the view' },
    @{ File = 'pages\views\finance.py';                   Text = "sum(r['purchase'] for r in rows"; What = 'and the total is the sum of the rows on screen' },
    # The way back from a receipt changed directly in the database: the row
    # moves, the stored PDF does not, and nothing on screen says so.
    @{ File = 'pages\management\commands\regenerate_receipt_pdf.py'; Text = 'None marked as edited'; What = 'a receipt edited in MySQL can be re-rendered WITHOUT being stamped' },
    # One verb, one glyph. base owns an icon button's colour but not its
    # picture, so the picture drifted: four pages drew Edit as a pencil and
    # two as a pencil-on-paper. test_icon_buttons.py section 1b scans every
    # template, so the next page to disagree fails here.
    @{ File = 'pages\templates\finance_valuations.html'; Text = 'fa-pencil-alt'; What = 'the Valuations Edit icon matches every other list page' },
    @{ File = 'pages\templates\asset_detail.html';       Text = 'fa-pencil-alt'; What = 'and so does Asset Details' },
    # Petty Cash. The page said Income-or-Expense THREE times - the amount in
    # keyword green/red inside a style attribute, a Bootstrap alert badge, and
    # a coloured card border on mobile - and the view ran two queries for one
    # page, duplicated in petty_cash_commit.
    @{ File = 'pages\views\petty_cash.py';               Text = 'def _petty_ledger'; What = 'one helper returns the rows AND the balance they add up to' },
    @{ File = 'pages\views\petty_cash.py';               Text = '_EPOCH = date.min'; What = 'and an undated row no longer empties the whole ledger' },
    @{ File = 'pages\templates\petty_cash.html';         Text = 'table alv-table petty-cash-table'; What = 'Petty Cash is on the table standard' },
    @{ File = 'pages\templates\petty_cash.html';         Text = 'alv-tag {{ row.tag }}'; What = 'Income/Expense is a category tone, not a verdict' },
    @{ File = 'pages\templates\petty_cash.html';         Text = 'pc-balance-figure'; What = 'and the closing balance is ink until it goes below zero' },
    # Actual Expenses. The first three are styling; the fourth is not - the
    # Expenses-by-Property report has always counted approved-and-paid only
    # while its docstring claimed the opposite, so it quietly under-reported.
    # No figure moved: the words were corrected and the report now says its
    # population on its own face.
    @{ File = 'pages\templates\base.html';               Text = '.icon-manage'; What = 'Manage is a NAME on --alv-view, not a seventh colour' },
    @{ File = 'pages\templates\act_expense.html';        Text = 'table alv-table expense-table'; What = 'Actual Expenses is on the table standard' },
    @{ File = 'pages\templates\act_expense.html';        Text = 'alv-pill-neutral'; What = 'and a status you cannot change is a pill, not a disabled button' },
    @{ File = 'pages\templates\act_expense.html';        Text = 'report-basis'; What = 'the report states the population it counts' },
    @{ File = 'pages\views\expenses.py';                 Text = 'Counts only expenses that are BOTH approved and paid'; What = 'and the docstring finally agrees with the query beneath it' },
    # The sticky sweep. Six pages carried a page-local .table-container rule
    # with overflow:hidden - same specificity as base's, later in the document,
    # so the page won and the element became a scroll container. Only
    # physical_invoice_list is on .alv-table today, so it is the only one where
    # a heading actually starts sticking; the other five are pre-emptive.
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = '.table-container'; What = 'Physical Invoices stopped redefining base shell - its heading sticks at last'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\fsr.html';                   Text = '.table-container'; What = 'and neither does Issues'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\comments_report.html';       Text = '.table-container'; What = 'nor the Comments report'; Absent = $true; Code = $true },
    # Fifteen commit endpoints refuse a GET. @login_required says WHO may call
    # a view; nothing said HOW, so every one of them did its work on a GET -
    # including deleting a tenant, which was a plain link a prefetcher could
    # follow. Two of the fifteen were half-fixed by our own Actual Expenses
    # round: POST in the template, GET still accepted by the view.
    @{ File = 'pages\views\tenants.py';    Text = 'from django.views.decorators.http import require_POST'; What = 'deleting or duplicating a tenant needs a POST' },
    @{ File = 'pages\views\expenses.py';   Text = 'from django.views.decorators.http import require_POST'; What = 'and so do approve, pay and delete' },
    @{ File = 'pages\views\finance.py';    Text = 'from django.views.decorators.http import require_POST'; What = 'and the eight finance commit/delete views' },
    @{ File = 'pages\views\invoices.py';   Text = 'from django.views.decorators.http import require_POST'; What = 'and marking an invoice paid' },
    @{ File = 'pages\templates\tenant.html';      Text = 'tenant-inline-form'; What = 'Delete is a POST form, not a link a prefetcher can follow' },
    @{ File = 'pages\templates\tenant_edit.html'; Text = 'form="duplicateTenantForm"'; What = 'and Duplicate posts from a form outside the edit form' },
    # The Manage Expense modal - twelve controls built inside <script>, which
    # every markup scan in this project was blind to. The bucket
    # Show-ButtonDrift has listed for weeks as "decided by hand".
    @{ File = 'pages\templates\act_expense.html'; Text = 'exp-note-success'; What = 'the verify banner is on house tokens, not Bootstrap alerts' },
    @{ File = 'pages\templates\act_expense.html'; Text = 'action-danger btn-sm'; What = 'and Delete Document reads destructive by TONE, not a red fill' },
    # The P&L drill-down could not open an invoice: the handler bound a glyph
    # verify_badge never emits, then decided whether an icon WAS an invoice by
    # comparing its colour to Bootstrap green.
    @{ File = 'pages\templates\finance_pl_act.html'; Text = 'window.viewInvoiceQuick'; What = 'the P&L drill-down opens an invoice by reading the document, not the colour' },
    # Code = $true: the comment above the new handler quotes the dead line it
    # replaced, "isGreen" and all. That is the record of the fault, not the
    # fault. See NoComments below.
    @{ File = 'pages\templates\finance_pl_act.html'; Text = 'isGreen'; What = 'and the colour test is gone'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\act_expense.html'; Text = 'data-invoice-url'; What = 'the invoice icon carries its document, so the P&A modal that injects this table can open it' },
    @{ File = 'pages\templates\finance_pl_act.html'; Text = 'showInvoiceModalLikeExisting('; What = 'and the drill-down handler calls the viewer THIS file has' },
    # The pro-rata anchor deadlock (item 8.2). The screen said "un-tick it"
    # and the anchor's blanket `disabled` would not let you. Two rules
    # collided - the anchor is always in, an inactive property must come out -
    # and the anchor rule gives way, because an inactive property leaving is
    # exactly the case it should allow.
    @{ File = 'pages\templates\finance_expense_edit.html'; Text = 'function anchorIsReleasable'; What = 'one predicate decides whether the anchor may be released' },
    @{ File = 'pages\templates\finance_expense_edit.html'; Text = 'prorata-anchor-note'; What = 'and the banner says what releasing it does to THIS record' },
    # Code = $true because the patcher leaves a {# #} comment above the tag
    # explaining what the old unconditional form was.
    @{ File = 'pages\templates\finance_expense_edit.html'; Text = 'existing_expense.prop_id %}disabled'; What = 'the anchor is no longer disabled unconditionally'; Absent = $true; Code = $true },
    # Item 8.1, the half that needs no money decision: the valuation preview
    # says when it is about to fund a property the P&L does not report. No
    # figure moves - the participant set is untouched by that round.
    @{ File = 'pages\views\finance.py'; Text = 'inactive_property_names'; What = 'the preview reports what it would fund on an inactive property' },
    @{ File = 'pages\templates\finance_valuations_edit.html'; Text = 'val-preview-inactive-warning'; What = 'and the modal says so, naming them and the money' },
    # Code = $true: the CSS comment above the new pill explains that the old
    # inline #ffc107 was removed, and quotes it.
    @{ File = 'pages\templates\finance_valuations_edit.html'; Text = 'background:#ffc107'; What = 'the edited pill lost its literal'; Absent = $true; Code = $true },
    # A share of zero is not a share. Membership stopped meaning "a row
    # exists" - a released pro-rata row is CLOSED, not deleted, and three
    # screens were still counting it. This one DOES move figures on the
    # valuation preview, deliberately.
    @{ File = 'pages\views\finance.py'; Text = 'def carries_a_share'; What = 'one helper decides whether a row carries a share' },
    @{ File = 'pages\views\finance.py'; Text = 'carries_a_share(expense.objects.filter('; What = 'and the screens that decide membership go through it' },
    # The year-on-year matrix, and the two components base was missing for it.
    # .alv-matrix could NOT be .table-container: that one sets overflow: clip
    # so a sticky heading can pin, and a matrix needs overflow-x: auto.
    @{ File = 'pages\templates\base.html'; Text = '.alv-seg {'; What = 'base owns the segmented control at last - third asker' },
    @{ File = 'pages\templates\base.html'; Text = '.alv-matrix-scroll {'; What = 'and a matrix that scrolls sideways with frozen edges' },
    @{ File = 'pages\views\finance.py'; Text = 'def expense_matrix'; What = 'one expense, resolved year by year on the P&L resolver' },
    @{ File = 'pages\templates\finance_expense.html'; Text = 'alv-matrix-row-head'; What = 'and the Expenses screen has a second view' },
    # A closed row with no past. The delete guard refused every pro-rata row -
    # right about a LIVE one, whose removal would leave the others holding
    # shares of a larger split, and wrong about a CLOSED one, which holds no
    # share at all. It tested what the row IS, not what it HOLDS.
    @{ File = 'pages\views\finance.py'; Text = 'def _expense_has_past'; What = 'one definition of whether a row has a past worth keeping' },
    @{ File = 'pages\views\finance.py'; Text = '_exp_row.is_spent'; What = 'and the list knows which rows hold nothing and never did' },
    @{ File = 'pages\templates\finance_expense.html'; Text = 'exp-closed-pill'; What = 'a closed row reads CLOSED, not a bare zero' },

    # ------------------------------------------------- SECTION MC, 3 Oct 2026
    # The Meal Plans / Calendar programme. The first two rows are the BUG
    # Demetri reported - he said the toggle was missing from the Calendar
    # view; it was there, painted white on a white page by a rule written
    # for a coloured header bar the page no longer has. Both halves of that
    # are asserted: the control is present, and the ink that hid it is gone.
    # Five filled buttons in five colours became the icon strip the list
    # rows already wore. #007bff is named because it was the loudest.
    # A disabled button that rendered as a live one, because .btn.action-primary
    # outranked the page's own grey. There is no string this adds that proves
    # it, so the absence of the old class is the assertion.

    # ------------------------------------------------- SECTION SL, 3 Oct 2026
    # Four people's email addresses were typed into a template, in a product
    # whose HouseholdMember docstring says the table exists to replace that.
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = 'demetrimanias@gmail.com'; What = 'no address is typed into the shopping list any more'; Absent = $true; Code = $true },
    @{ File = 'pages\views\recipes\meal_planning.py'; Text = 'household_emails'; What = 'the roster is where they come from' },
    @{ File = 'pages\templates\meal_plan_shopping_list.html'; Text = 'id="emailPanel"'; What = 'and the address box opens only when Email is pressed' },

    # ------------------------------------- THE FILTER PROGRAMME, 3 Oct 2026
    # base's .filter-grid declared a grid and no columns, so the one page
    # that did not set its own stacked its fields at the full panel width.
    @{ File = 'pages\templates\base.html'; Text = 'repeat(auto-fit, minmax(200px, 240px))'; What = 'a filter field is capped, and fits on one line' },
    @{ File = 'pages\templates\categories_management.html'; Text = 'id="filterPanel"'; What = 'Categories has the house filter' },
    @{ File = 'pages\templates\measurement_units_management.html'; Text = 'data-unit-type'; What = 'and Measurement Units filters on type without reading a cell that holds a select of every type' },
    # NO data-live-search SENTINEL HERE. The obvious row - Absent = $true
    # on 'data-live-search' - is one test_sentinels refuses, and rightly:
    # it tried thirteen historical versions of this file and the string
    # has never been in any of them, so the row could never have failed
    # and proves nothing. The claim that these two filters compose
    # instead of racing lives in test_ref_filters section 6, where a
    # browser sets a Type, types a letter, and checks the Type survived -
    # which CAN fail.
    # The seventh and eighth hand-rolled segmented controls.
    @{ File = 'pages\templates\unit_conversions_management.html'; Text = 'scope-btn'; What = 'the Conversions scope toggle is base''s segment now'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\finance_pl_act.html'; Text = 'btn-outline-info'; What = 'Budget/Actuals is no longer half house, half Bootstrap'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\property_assets.html'; Text = 'view-toggle-group'; What = 'and Group by, which every census of btn-info missed for a month'; Absent = $true; Code = $true },

    # --------------------------------------- THE REPAIR ROUNDS, 3 Oct 2026
    # Outstanding item 4, logged 1 Oct: four suites each typed the number of
    # filtered pages. Now none of them does.
    @{ File = 'alv_tree.py'; Text = 'def house_filter_pages'; What = 'one census of the filtered pages, derived from the tree' },
    # A dropdown toggle does not do anything - it asks which thing you want
    # to look at - so it is never what the lone-button rule promotes.
    @{ File = 'Show-ButtonDrift.py'; Text = 'def is_chooser'; What = 'a chooser is not a verb, and a report page may have no primary' },
    @{ File = 'pages\templates\base.html'; Text = '.page-action-buttons .alv-seg > *'; What = 'a segment in an action bar is the bar''s height, not nearly it' },
    # ------------------------------------------------ RS-1b, 14 Oct 2026
    # The recipe side finishes, and the drift gate above runs --recipes.
    # Its own comment claimed it walked every template while it asked 117
    # of 142.
    @{ File = 'Show-ButtonDrift.py'; Text = 'def not_the_verb'; What = 'a named exception is not the page''s verb - a map, because the rule I proposed would have demoted Submit FSR' },
    @{ File = 'Show-ButtonDrift.py'; Text = "'d-flex':"; What = 'and d-flex is off the role register - a layout utility that only ever got one button wrong'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\view_recipe.html'; Text = 'btn action-secondary" onclick="printShoppingList()'; What = 'Print and Copy join the three house siblings in the same share row' },
    @{ File = 'pages\templates\import_recipe.html'; Text = 'btn action-primary btn-lg'; What = 'and Extract Recipe with AI is the page it sits on' },
    # ------------------------------------------------- VC-1, 14 Oct 2026
    # The gate asked every PAGE after RS-1b and still not every BUTTON.
    # Three controls were a <label>, two Bootstrap colours were off the
    # list, one HOUSE name was off every list, and a decided wrapper
    # could not reach a button with no colour at all.
    @{ File = 'Show-ButtonDrift.py'; Text = '<(a|button|span|label)'; What = 'the button scanner can see a <label>, which three file pickers are' },
    @{ File = 'Show-ButtonDrift.py'; Text = 'btn-outline-light'; What = 'and six of Bootstrap''s eight outline colours is not the list' },
    @{ File = 'Show-ButtonDrift.py'; Text = 'def print_painted'; What = 'and a button painted by page CSS or JavaScript is counted, not dropped' },
    @{ File = 'pages\templates\my_profile.html'; Text = 'btn action-secondary btn-sm'; What = 'Upload Photo stops being Bootstrap blue at 3.98 to 1' },
    @{ File = 'pages\templates\ingredient_families.html'; Text = 'icon-action-btn icon-delete'; What = 'and the family icons stop being a near-white glyph on green at 2.97 to 1' },
    # ------------------------------------------------- PH-2, 14 Oct 2026
    # Demetri asked why three recipe screens were green. Because a STATUS
    # token was being used as decoration - base already mapped bg-success
    # onto --alv-good, so they were house-coloured and semantically wrong.
    @{ File = 'pages\templates\base.html'; Text = '.bg-light { background-color: var(--alv-surface)'; What = 'the last Bootstrap background utility is house-owned - a rename, not a recolour' },
    @{ File = 'pages\templates\ingredient_families.html'; Text = 'alv-card-head'; What = 'and 28 family cards stop wearing the success colour as chrome' },
    @{ File = 'pages\templates\wcim_results.html'; Text = 'bg-info'; What = 'the least-ready tier stops being the loudest thing on the page'; Absent = $true; Code = $true },
    # AND NOT A SENTINEL FOR "Almost There KEEPS the amber". It was
    # written as one and test_sentinels refused it, correctly: bg-warning
    # is in all eight backed-up versions of that file, so the row could
    # never fail and therefore asserted nothing. A sentinel catches a
    # REGRESSION in something this round changed. "I deliberately did not
    # touch this" belongs in the round's own suite, and section 2 of
    # test_panel_heads.py says it there, with the reason attached.
    @{ File = 'pages\templates\pantry_staples.html'; Text = 'var(--alv-good-soft)'; What = 'and 92 pantry chips leave a hex literal no colour census could see' },
    # ------------------------------------------------- VB-1, 15 Oct 2026
    # Three questions from the live site and one answer: a colour that
    # names a verb in one module and a different verb in another names
    # nothing. No sentinel below claims a thing was LEFT alone - that
    # belongs in the round's suite, which is where test_sentinels sent
    # the last one I wrote.
    @{ File = 'pages\templates\wcim_landing.html'; Text = 'rgba(14, 124, 139, 0.3)'; What = 'the chooser chip stops wearing a Bootstrap green no census could see' },
    @{ File = 'pages\templates\wcim_extras.html'; Text = 'var(--alv-accent-soft)'; What = 'and a selection stops being reported as a positive status' },
    @{ File = 'pages\templates\map_ingredients_nutrition.html'; Text = 'var(--alv-warn-line)'; What = 'the Undo on the confirmation bar is readable again - 1.60:1 to 8.87:1' },
    @{ File = 'pages\templates\unit_conversions_wizard.html'; Text = 'var(--alv-good-line)'; What = 'and the tick beside it clears the glyph floor it was under' },
    @{ File = 'pages\templates\recipe_management.html'; Text = 'var(--alv-edit)'; What = 'the recipe Edit button is the same blue as every other module' },
    # NO `Absent` ROW FOR THE DUPLICATE HOVER. The obvious one was
    # var(--alv-accent-ink) marked Absent, and test_bar_order refused it:
    # that token has FIVE other legitimate uses on the page - the letter
    # filter's scrollbar thumb and four tag inks - so the claim was simply
    # false. Second sentinel in two rounds to assert something about what
    # a round REMOVED. The removal is checked in test_verb_colours section
    # 5, where it can name the selector instead of a substring, and that
    # is where it belongs.
    @{ File = 'alv_rowactions.py'; Text = 'VERNACULAR'; What = 'four controls no drift census could see are registered by verb' },
    # ------------------------------------------------- PV-1, 15 Oct 2026
    # Demetri asked why the P&L's invoice viewer has no Share button. It
    # was a second implementation of a component eleven pages share.
    @{ File = 'pages\templates\finance_pl_act.html'; Text = "include 'components/pdf_viewer.html'"; What = 'the P&L drops its own invoice viewer for the one eleven pages share' },
    @{ File = 'pages\templates\asset_detail.html'; Text = "include 'components/pdf_viewer.html'"; What = 'and so does asset_detail, whose markup apologised for its iframe' },
    @{ File = 'pages\templates\finance_pl_act.html'; Text = ':not(.pdf-viewer-footer)'; What = 'the page phone footer rule stops reaching a component it never knew about' },
    @{ File = 'pages\templates\asset_detail.html'; Text = ':not(.pdf-viewer-modal-dialog)'; What = 'and 963px of buttons stop being laid out on a 390px screen' },
    # ------------------------------------------------- CC-1, 15 Oct 2026
    # Five findings from a full check of the Celebrations module. The
    # blank November was never a one-year limit - every event was drawn
    # exactly once, so a birthday existed in one November for all time.
    @{ File = 'pages\models.py'; Text = 'def occurrences_in'; What = 'an event can be asked which days it falls on in a given month' },
    @{ File = 'pages\models.py'; Text = 'def age_at'; What = 'and the age is taken at the occurrence being drawn, not the next one' },
    @{ File = 'pages\templates\celebration_calendar.html'; Text = 'table-layout: fixed'; What = 'the calendar stops clipping its own Saturday column below 1300px' },
    @{ File = 'pages\templates\celebration_calendar.html'; Text = 'class="day-more"'; What = 'a busy day says how many it is not showing, and opens a sheet' },
    @{ File = 'pages\templates\celebration_calendar.html'; Text = 'cal-legend'; What = 'and the key sits above the grid it explains' },
    # A Django comment is not a flex item. RE-1b made this repair to one
    # fixture three days ago; this is the other one.
    @{ File = 'test_button_sweep.py'; Text = 'the seventeen comments in'; What = 'the bar fixture strips Django comments before measuring rows' },
    # -------------------------------------------------- SECTION CO, 3 Oct 2026
    # code_only was written out at module level in 47 files. It has a home.
    @{ File = 'alv_tree.py'; Text = 'def code_only_js'; What = 'the // variant three suites need and the rest must not have' },
    # And `/*` is not a comment opener in markup. The guard is the SHAPE of
    # the helper, not a note about it: the block syntax is only stripped
    # inside a style or script element, so accept="image/*" survives.
    @{ File = 'alv_tree.py'; Text = '(<(?:style|script)'; What = 'the block comment syntax is only a comment inside style or script' },
    # Named rather than merged: a tokenize function that reads PYTHON
    # source is a different job, and sharing a name hid that for a month.
    @{ File = 'test_tree_roots.py'; Text = 'python_code_only = functools.partial'; What = 'the Python-source one is alv_tree now, asking payloads=False' },
    # -------------------------------------------------- SECTION TL, 4 Oct 2026
    # A LIVE 500. The stub declared two parameters; project_task_list
    # passed three, six times, every one of them behind `if language ==
    # 'greek'`. English skipped all six and worked; Greek raised TypeError
    # before the template was reached. The third argument was never spare -
    # it is the translation stored on the model, and the signature says so.
    @{ File = 'pages\translation_service.py'; Text = 'def get_translated_text(text, stored='; What = 'the stub takes the stored translation it was always being handed' },
    # NO SENTINEL ON 'from ..translation_service import'. The obvious row,
    # and test_sentinels refuses it - rightly. That import line existed
    # before this round as a COMMENTED-OUT line, so the substring is in
    # every historical version of the file and the row could never have
    # failed. The claim that the view uses the shared stubs rather than
    # a second copy is held by the Absent row below, which CAN fail, and
    # by test_greek_arity section 3, which asks the parse tree.
    # DEFINED TWICE is how a definition drifts, and the copy that ran was
    # the one nobody was reading.
    @{ File = 'pages\views\projects.py'; Text = 'def get_translated_text'; What = 'rather than declaring a second copy of it'; Absent = $true; Code = $true },
    # TL-2. The origin is a KEY chosen from a map, never a path: ?next=
    # read back at face value is an open redirect, and it is the obvious
    # way to build this.
    @{ File = 'pages\views\projects.py'; Text = 'def task_origin_back'; What = 'Back resolves the page the edit was opened from' },
    @{ File = 'pages\templates\projects\project_task_list.html'; Text = '?{{ origin_query }}'; What = 'and the list says so on its links, with its own assignee and language' },
    @{ File = 'pages\templates\projects\project_tasks_delete.html'; Text = '{{ back_url }}'; What = 'Delete follows Edit, which it did not do at all before' },
    # CR-1. The house had never claimed .custom-control at all, so a CDN
    # decided what a selected radio looked like. Both type-scoped
    # selectors are named: Bootstrap writes the checked colour three
    # times at two specificities and a single generic rule loses to two
    # of them.
    @{ File = 'pages\templates\base.html'; Text = '.custom-checkbox .custom-control-input:checked'; What = 'a ticked box is the house accent, not Bootstrap blue' },
    @{ File = 'pages\templates\base.html'; Text = '.custom-radio .custom-control-input:checked'; What = 'and so is a selected radio' },
    # NOT an Absent sentinel on '#0e7c8b'. The first version of this row
    # was exactly that, and projects_detail carries NINE of them - a
    # heading icon, a tab underline, a modal header, a button. CR-1 owns
    # two. A sentinel has to say what its own round claims, or it fails
    # on work that round never touched and four suites report it.
    # The nine are real drift and are logged for a round of their own.
    @{ File = 'pages\templates\projects\projects_detail.html'; Text = '.custom-control-input:checked ~ .custom-control-label { color: var(--alv-accent); }'; What = 'and the one page that styled this control writes the token, not the hex' },
    # FA-1. end aligned the BOTTOMS of the filter groups, so any group
    # that was taller - a select beside an input, a search hint under a
    # control - pushed its own label and box up.
    @{ File = 'pages\templates\base.html'; Text = 'align-items: start;'; What = 'a filter panel lines up on the top of its labels' },
    @{ File = 'pages\templates\base.html'; Text = 'align-items: end;'; What = 'and no longer on the bottom of whatever each group happens to end with'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\projects\projects.html'; Text = '2fr 1fr 1fr'; What = 'Projects takes base''s capped columns - all three the same'; Absent = $true; Code = $true },
    # RA-1. The order lives in alv_rowactions.py and nowhere else -
    # the patcher, the drift report and the suite all ask it.
    @{ File = 'alv_rowactions.py'; Text = 'LOOK, CHANGE, COPY, ADVANCE, DESTROY'; What = 'one order for every action column, written down once' },
    @{ File = 'pages\templates\base.html'; Text = '.icon-document,'; What = 'and a document is not a plain view, so it can be placed' },
    @{ File = 'pages\templates\tenant.html'; Text = 'icon-action-btn icon-document'; What = 'the Tenants lease agreement is classed by what it is' },
    # AG-1. One warm neutral deepening, and a figure in the house colour.
    @{ File = 'pages\templates\base.html'; Text = '--alv-age-4:      #3b3733;'; What = 'the ageing scale is one tone, not green to red' },
    @{ File = 'pages\templates\base.html'; Text = '--age: var(--alv-good)'; What = 'and not ageing is no longer a health verdict'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\open_invoices_report.html'; Text = '#007bff'; What = 'the total outstanding figure is one colour on both screens'; Absent = $true; Code = $true },
    # PD-1. Seven dark table headers, in two different colours by two
    # different selectors, and a green pill beside a red one on two counts.
    @{ File = 'pages\templates\property_detail.html'; Text = '#343a40 !important'; What = 'property_detail draws its table headers like every other list'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\property_detail.html'; Text = 'background-color: #2c3e50'; What = 'including the two that coloured the ROW rather than the cell'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\property_detail.html'; Text = 'alv-pill alv-pill-neutral">{{ expired_warranties }}'; What = 'and a count reads as a count, not as a failure' },
    # PD-2. table AND alv-table: base sets the look, Bootstrap's .table
    # sets width 100%, and dropping it shrank every table to its content.
    @{ File = 'pages\templates\property_detail.html'; Text = 'class="table alv-table issues-table"'; What = 'property_detail''s tables are base''s, and keep their width' },
    @{ File = 'pages\templates\property_detail.html'; Text = 'table-striped'; What = 'with no zebra, like every other list in the app'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\base.html'; Text = '.icon-comment'; What = 'and reading an issue comment is a LOOK with a name of its own' },
    # CS-1. The move itself cannot be sentinelled on a string - it is the
    # same bytes in a different place - so the sentinel is on what the
    # move was FOR: Actual Expenses keeps its five-column rule, and the
    # stale page rules that would have woken up are gone.
    @{ File = 'pages\templates\act_expense.html'; Text = 'minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 1.2fr) 170px 170px'; What = 'the Actual Expenses filter keeps the five columns it was measured for' },
    @{ File = 'pages\templates\customer_form.html'; Text = 'color: #2c3e50'; What = 'and no page re-imposes a hex literal over a base token'; Absent = $true; Code = $true },
    # SL-1. On the component, not on the 3-up variant where it used to be.
    @{ File = 'pages\templates\base.html'; Text = 'overflow-wrap: break-word;'; What = 'a long stat label breaks inside the word rather than leaving its tile' },
    # TD-1. One page, one class, one line.
    @{ File = 'pages\templates\projects\project_task_list.html'; Text = 'white-space: nowrap;'; What = 'an overdue date keeps its warning on the same line' },
    # TR-1. The string that WAS the defect, and the import that replaces it.
    @{ File = 'pages\views\projects.py'; Text = 'return text  # Return original text if translation fails'; What = 'a failed translation no longer comes back as the English'; Absent = $true; Code = $true },
    @{ File = 'pages\views\projects.py'; Text = "return JsonResponse({'success': False, 'error': reason})"; What = 'and arrives as a failure the browser can show' },
    # 'from googletrans import', NOT 'googletrans'. A sentinel matches a
    # SUBSTRING, case-insensitively, and the class that replaces it is
    # deep_translator's GoogleTranslator - which contains 'googletrans'.
    # The bare word could never have passed, and test_sentinels said so.
    # Same family as 'badge' matching 'renewal-status-badge': a name is a
    # token, not a run of characters.
    @{ File = 'pages\views\projects.py'; Text = 'from googletrans import'; What = 'googletrans is gone - it has not been in requirements for weeks'; Absent = $true; Code = $true },
    # RB-1. The button Demetri pointed at, and the selector that hunts it.
    @{ File = 'pages\templates\preview_imported_recipe.html'; Text = 'class="btn action-secondary" onclick="spellCheckInstructions()"'; What = 'Check Spelling is a house secondary, not Bootstrap blue' },
    @{ File = 'pages\templates\preview_imported_recipe.html'; Text = 'remove-item-btn'; What = 'and the red block delete is the house row action everywhere else uses'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\preview_imported_recipe.html'; Text = '.action-danger[onclick*="confirmDeleteRecipeDocument"]'; What = 'with the selector that finds it again moved along with it' },
    # DR-1. Absent rows on two of the twenty-two, because the claim is a
    # removal. NOT an Absent row on the bare literal '#0e7c8b' - these
    # pages carry 79 of them in other components, and a sentinel has to
    # say what its own round claims. CR-1 learned that one the hard way.
    @{ File = 'pages\templates\tenant.html'; Text = 'background-color: #0e7c8b'; What = 'a page no longer spells out the colour the accent token already gives'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\properties.html'; Text = 'background-color: #0e7c8b'; What = 'and neither does Properties'; Absent = $true; Code = $true },
    # TR-2. The scraper out, the house API in, and the pool that existed
    # only to contain a library with no timeout.
    @{ File = 'pages\translation_service.py'; Text = 'api.anthropic.com/v1/messages'; What = 'translation runs on the API this app already talks to' },
    @{ File = 'pages\translation_service.py'; Text = 'urlopen(req, timeout=timeout)'; What = 'and the call can be told to give up' },
    @{ File = 'pages\views\projects.py'; Text = 'ThreadPoolExecutor'; What = 'so the thread pool that contained the scraper is gone'; Absent = $true; Code = $true },
    # NO SENTINEL ON requirements.txt. One was written here and
    # test_sentinels refused it, rightly: that file is UTF-16 LE, the
    # sentinel reader opens everything as utf-8-sig with errors='replace',
    # and the decoded mojibake contains no readable token - so an Absent
    # row on it is true in every version of the file and can never
    # discriminate. test_translate_api.py section 5 decodes it properly
    # and checks deep-translator is gone there instead.
    # SE-1. Absent rows on the NAMES, never on the values - the whole
    # lesson of this round is that a secret must not be written down in
    # order to be checked. The getenv call is the claim.
    @{ File = 'mysite\settings.py'; Text = "SECRET_KEY = os.getenv('SECRET_KEY', '')"; What = 'the signing key comes from the environment' },
    @{ File = 'mysite\settings.py'; Text = "USDA_API_KEY = os.getenv('USDA_API_KEY', '')"; What = 'and so does the USDA key' },
    @{ File = 'mysite\settings.py'; Text = 'django-insecure-'; What = 'and no generated-and-never-changed key is left in the file'; Absent = $true },
    # DR-1b. The shorthand, gone from the two pages DR-1 sentinelled.
    @{ File = 'pages\templates\tenant.html'; Text = 'border: 1px solid #0e7c8b'; What = 'and no page sets the accent border by shorthand either'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\properties.html'; Text = 'border: 1px solid #0e7c8b'; What = 'nor does Properties'; Absent = $true; Code = $true },
    # PF-1. The templates that hold the options once, the call that clones
    # them into a row, and - the rows worth the most - the two {% if %}
    # comparisons that existed ONLY inside the per-row option loops. They
    # are how a reader knows the 18,700 options really are gone.
    #
    # NOT an Absent row on '{% for cat in categories %}'. That loop is
    # still in the file: it is what fills the <template>, and it is also
    # what fills the page's own Category FILTER at the top. A sentinel has
    # to say what its round claims, and the claim is not that the loop
    # went - it is that it now runs once instead of 374 times.
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = 'id="categoryOptionsTpl"'; What = 'the category options are rendered once for the whole page' },
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = 'id="unitOptionsTpl"'; What = 'and so are the unit options' },
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = "fillPicker(row.querySelector('.category-edit'), 'categoryOptionsTpl');"; What = 'a row gets them the first time it is edited' },
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = 'item.ingredient.category.ingredient_category_id == cat.ingredient_category_id'; What = 'and no row renders nineteen categories of its own'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\ingredient_base_units_management.html'; Text = 'item.ingredient.default_unit.measurement_unit_id == unit.measurement_unit_id'; What = 'nor thirty-one units'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\ingredient_families.html'; Text = 'id="familyIngredientOptionsTpl"'; What = 'and one family picker holds all 374 ingredients for every card' },
    @{ File = 'pages\templates\ingredient_families.html'; Text = 'sel.dataset.filled'; What = 'filled on first focus, once per select' },
    # RA-2. The three names that were wrong, and the tooling that can now
    # see the third of the tree it was missing.
    #
    # NOT Absent rows on 'fa-file-invoice', 'fa-scroll' or
    # 'fa-rotate-left'. Every one of those glyphs is still in its page in
    # another component - an invoice heading, a deed heading, an undo on a
    # different control - so an Absent row would fail on a correct tree.
    # The icon-view row on Physical Invoices is the one removal that IS
    # the whole file's only occurrence, so it is the only Absent row here.
    @{ File = 'pages\templates\asset_detail.html'; Text = 'icon-document'; What = 'opening an asset document is the house document action' },
    @{ File = 'pages\templates\asset_detail.html'; Text = 'fa-file-contract'; What = 'and draws the document glyph, not an invoice' },
    @{ File = 'pages\templates\title_deeds_management.html'; Text = 'icon-document'; What = 'so is opening a title deed' },
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = 'icon-pdf'; What = 'and a PDF is named a PDF' },
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = 'icon-view'; What = 'not view, which three other pages use for something else'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\cash_receipts.html'; Text = 'icon-unapprove'; What = 'taking an approval back is its own action, not approve with an undo arrow' },
    @{ File = 'pages\templates\passport_management.html'; Text = 'icon-edit icon-disabled'; What = 'a disabled button still says what it would have done' },
    @{ File = 'alv_rowactions.py'; Text = 'def unwrapped('; What = 'and the drift report can see the buttons outside a wrapper' },
    @{ File = 'Show-RowActionDrift.py'; Text = 'NOT IN A .row-actions WRAPPER'; What = 'and names them without calling them drift' },
    # LU-1. Two rows that say the setting is SET, and two that say the
    # decorator and its import are gone.
    #
    # NO Code = $true ON EITHER ABSENT ROW. Both name a string that only
    # ever existed as live code, and the comment-stripper would make the
    # commented-out LOGIN_URL row absent in every version of the file -
    # vacuous, and test_sentinels would refuse it.
    #
    # NOT an Absent row on '@login_required' in auth.py. The block that
    # replaces the decorator EXPLAINS why there is no decorator, so it
    # contains the word. The patcher's own import gate hit that exact
    # shape and refused the round until it was taught to strip comments
    # first; a sentinel would have had no such warning.
    @{ File = 'mysite\settings.py'; Text = "LOGIN_URL = '/login/'"; What = 'a view with no session reaches the login page that exists' },
    @{ File = 'mysite\settings.py'; Text = '#LOGIN_URL = "/login/"'; What = 'and the setting is no longer commented out'; Absent = $true },
    @{ File = 'pages\views\auth.py'; Text = 'NO @login_required HERE - LU-1'; What = 'logging out when already logged out is a no-op, not a redirect' },
    @{ File = 'pages\views\auth.py'; Text = 'from django.contrib.auth.decorators import login_required'; What = 'and the import that view was the only user of has gone'; Absent = $true },
    # PD-3. The compensating rule, the tap floor, and three removals.
    #
    # Code = $true ON THE THREE ABSENT ROWS, and it is load-bearing here
    # rather than habit: #6c757d and #28a745 are each still in the file
    # ONCE, inside DB-7's and PD-2's comments describing what THEY
    # removed. Without the comment-stripping those rows would fail on
    # another round's record of its own finding.
    @{ File = 'pages\templates\property_detail.html'; Text = '.property-detail-page.container-fluid > .row {'; What = 'the page rows match its tighter wrapper, so it no longer scrolls sideways on a phone' },
    @{ File = 'pages\templates\property_detail.html'; Text = 'min-height: 44px'; What = 'and its one short select is 44px to tap' },
    @{ File = 'pages\templates\property_detail.html'; Text = '.issues-table th.text-left'; What = 'and the page no longer restates a Bootstrap utility word for word'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\property_detail.html'; Text = '#6c757d'; What = 'no muted grey is spelt out where base has a name for it'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\property_detail.html'; Text = '#28a745'; What = 'and no Bootstrap green either'; Absent = $true; Code = $true },
    # SV-1. The attribute itself, on both buttons. There is no Absent
    # row to write here: the defect was a MISSING attribute, and a
    # sentinel cannot assert the absence of nothing. The Present rows
    # are the whole claim, and test_submit_form.py section 4 is what
    # guards against a third one appearing.
    @{ File = 'pages\templates\edit_asset.html'; Text = '<button type="submit" form="editAssetForm"'; What = 'Save Changes belongs to the form it saves' },
    @{ File = 'pages\templates\generate_lease_agreement.html'; Text = 'form="lease-generation-form"'; What = 'and Generate Lease Agreement to the form it generates from' },
    # WS-1. One page per spelling, so a future round cannot narrow
    # the pattern back to the shorthand without a row failing.
    @{ File = 'pages\templates\occupancy_trends.html'; Text = 'border-left: 4px solid var(--alv-warn)'; What = 'a warning stripe is the house warning colour' },
    @{ File = 'pages\templates\home.html'; Text = 'border-left-color: var(--alv-warn)'; What = 'and so is one written the long way' },
    @{ File = 'pages\templates\occupancy_trends.html'; Text = 'border-left: 4px solid #ffc107'; What = 'no page spells the stripe out any more'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\home.html'; Text = 'border-left-color: #ffc107'; What = 'in either spelling'; Absent = $true; Code = $true },
    # RA-3 and CW-1.
    @{ File = 'pages\templates\title_deeds_management.html'; Text = '<span class="row-actions">'; What = 'an action column is a group, so the ordering standard can be read on it' },
    @{ File = 'crs\templates\crs\fi_form.html'; Text = 'grid-template-columns: 1.2fr 2fr 110px 44px;'; What = 'and the column that was squashing a 34px button is 44px, the tap floor' },
    @{ File = 'pages\templates\base.html'; Text = 'flex-wrap: wrap;'; What = 'a card cell wraps rather than pushing the page sideways' },
    # FN-1 and PL-1.
    @{ File = 'pages\templates\base.html'; Text = '.btn-row-edit'; What = 'the app has ONE row-action vocabulary, not two'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\finance_expense_line_types.html'; Text = 'icon-action-btn icon-delete'; What = 'and the finance screens speak it' },
    @{ File = 'pages\templates\finance_expense.html'; Text = '#fdecee'; What = 'the Expenses table no longer announces itself in red'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\finance_revenue.html'; Text = '#f0fbf4'; What = 'nor Revenue in green'; Absent = $true; Code = $true },
    # NOT 'data-label="Invoice"'. test_sentinels refused it, rightly:
    # that string is in all 34 backed-up versions of the page, because
    # the Report modal's JavaScript builder has carried one all along. A
    # row that is true in every version can never discriminate. The CLASS
    # on the new cell is the thing PL-1 actually added.
    @{ File = 'pages\templates\act_expense.html'; Text = 'class="cell-invoice"'; What = 'the P&L drill-down has a column that says Invoice' },
    @{ File = 'pages\templates\finance_pl_act.html'; Text = "'.verify-icon, .report-invoice-icon'"; What = 'and its handler listens for the document icon, not only the tick' },
    # AI-1, LA-1, RA-3b and RA-4.
    @{ File = 'pages\templates\edit_asset.html'; Text = 'form="deleteInvoiceForm"'; What = 'an attached invoice can be taken off again' },
    @{ File = 'pages\views\properties.py'; Text = 'def delete_asset_invoice'; What = 'and the file leaves storage, not just the record' },
    @{ File = 'pages\templates\generate_lease_agreement.html'; Text = 'click the button above'; What = 'step 3 points at the button where it actually is' },
    @{ File = 'pages\templates\generate_lease_agreement.html'; Text = 'click the button below'; What = 'and not where it used to be'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\invoices.html'; Text = '<span class="row-actions">'; What = 'an action column of forms is still one group' }
    # CO-2, IC-1, AE-4, OI-1 and RA-5, 5 Oct 2026.
    @{ File = 'Push-PendingChanges.ps1'; Text = '(?is)<(style|script)'; What = 'CO-2: this script reads block comments only inside style or script' },
    @{ File = 'pages\templates\user_administration.html'; Text = 'fa-user-slash'; What = 'IC-1: Disable has a picture of its own' },
    @{ File = 'pages\templates\household_member_management.html'; Text = '}user-slash{'; What = 'and so does Deactivate, where the name is built across a tag' },
    # NO SENTINEL ON cash_receipts / 'fa-ban'. One was written and
    # test_sentinels refused it: Void has drawn fa-ban in all eleven
    # backed-up versions of that page, so a Present row on it is true in
    # every one and can never discriminate. The claim worth making - that
    # IC-1 renamed one meaning and left the other alone - is a BEFORE AND
    # AFTER, and test_user_slash section 3 makes it against the tree.
    @{ File = 'pages\templates\act_expense.html'; Text = '{% else %}6%{% endif %}">Invoice</th>'; What = 'AE-4: the full page has an Invoice column, at a width that keeps the table at 100%' },
    @{ File = 'pages\templates\open_invoices_report.html'; Text = 'var(--alv-ink-strong)'; What = 'OI-1: the ageing labels are on a token' },
    @{ File = 'pages\templates\open_invoices_report.html'; Text = '#155724'; What = 'and the green empty-state panel has left the page'; Absent = $true; Code = $true },
    # 'def named(page, hits)', NOT 'NAMED = {'. The first spelling of this
    # row carried an opening brace with no close, which moved this
    # script's own brace balance by one and failed CO-2's suite - a
    # sentinel about a register breaking the gate it was registered in.
    @{ File = 'alv_rowactions.py'; Text = 'def named(page, hits)'; What = 'RA-5: the order knows which controls are not action columns' },
    @{ File = 'Show-RowActionDrift.py'; Text = 'REGISTERED COUNT HAS MOVED'; What = 'and the register refuses to absorb a new one' }
    # IC-2 and DR-2a, 5 Oct 2026.
    @{ File = 'pages\templates\user_administration.html'; Text = 'fa-user-check'; What = 'IC-2: Enable has a picture of its own, the twin of Disable' },
    @{ File = 'pages\templates\household_member_management.html'; Text = '}user-check{'; What = 'and so does Activate, on the other half of the split name' },
    @{ File = 'pages\templates\title_deeds_management.html'; Text = 'DR-2a, 5 Oct 2026'; What = 'DR-2a: the page says what it took and why' },
    @{ File = 'pages\templates\passport_management.html'; Text = 'grid-template-columns: 1fr 1fr 1fr'; What = 'and no longer spells out what base says as repeat(3, 1fr)'; Absent = $true; Code = $true },
    # CS-2, 5 Oct 2026.
    @{ File = 'alv_tree.py'; Text = 'def standalone(base=None)'; What = 'CS-2: the tree knows which templates base cannot reach' },
    @{ File = 'test_css_order.py'; Text = 'alv_tree.standalone()'; What = 'and the drift census asks it rather than counting a PDF body as drift' },
    # DR-2b, 5 Oct 2026.
    @{ File = 'pages\templates\title_deeds_management.html'; Text = 'DR-2b, 5 Oct 2026'; What = 'DR-2b: the page records what it gave back to base' },
    @{ File = 'pages\templates\title_deeds_management.html'; Text = '.icon-color-delete'; What = 'and the rule it emptied is gone, not left as empty braces'; Absent = $true; Code = $true },
    @{ File = 'apply_dr2_values.py'; Text = 'KEPT = {'; What = 'while four declarations a page can justify are named, not dropped' },
    # PH-1, 5 Oct 2026.
    @{ File = 'pages\models.py'; Text = 'holder = models.ForeignKey'; What = 'PH-1: a passport holder is a household member, not a string' },
    # NO SENTINEL ON models.py / 'holder_name = models.CharField'. One was
    # written and test_sentinels refused it: the field is in all eighteen
    # backed-up versions of that file, because PH-1 adds a key BESIDE it
    # and does not touch it. A Present row on a line this round
    # deliberately leaves alone is true in every version and can never
    # discriminate. test_passport_holder section 1 makes the claim
    # properly, by comparing the count before and after.
    @{ File = 'pages\migrations\0097_passport_holder.py'; Text = 'on_delete=django.db.models.deletion.PROTECT'; What = 'the column is nullable and the member cannot be deleted under it' },
    @{ File = 'pages\management\commands\backfill_passport_holder.py'; Text = 'DRY RUN - nothing was written'; What = 'and the backfill writes only when told to' },
    # PH-1b, 5 Oct 2026.
    @{ File = 'pages\management\commands\backfill_passport_holder.py'; Text = 'get_table_description'; What = 'PH-1b: the backfill asks the table what columns it has before querying' },
    @{ File = 'pages\management\commands\backfill_passport_holder.py'; Text = '0097_passport_holder has not been applied'; What = 'and says which migration is missing rather than raising pymysql at the reader' },
    # PH-1c, 5 Oct 2026.
    @{ File = 'pages\management\commands\backfill_passport_holder.py'; Text = "'angela manias': 'Angy'"; What = 'PH-1c: the one mapping no rule could reach is written down as a decision' },
    @{ File = 'pages\management\commands\backfill_passport_holder.py'; Text = 'THE MAP POINTS AT A MEMBER WHO IS NOT '; What = 'and a stale map entry is reported rather than silently skipped' },
    # E-2b, 6 Oct 2026. Exactly the shape a sentinel is for: a file that
    # must exist and a string that must NOT. The f-string survived for
    # the life of the project because nothing asked either question.
    @{ File = 'pages\templates\access_denied.html'; Text = 'E-2b, 6 Oct 2026'; What = 'E-2b: the 403 page is a template on base, not eighty lines of f-string' },
    @{ File = 'pages\middleware.py'; Text = 'html_content'; What = 'and the purple gradient 172 URL prefixes used to answer with is gone'; Absent = $true }
    # NO SENTINEL FOR OI-1 ON A COLOUR IT KEPT. #0e7c8b was already the
    # accent's own value written out, so a Present row on var(--alv-accent)
    # is true of pages that never went through this round and an Absent row
    # on the literal is true of most of the tree. The two above are a token
    # this page did not use before and a literal only this page carried.
    # NO SENTINEL FOR RA-4. Its claim is an ORDER - pdf, then duplicate,
    # then approve or unapprove, then send, then delete - and a sentinel
    # matches a SUBSTRING. There is no string that is present when five
    # blocks are in the right sequence and absent when they are not; the
    # one tried here was 'icon-pdf', which RA-2 already sentinels on this
    # same page and which is equally true in either order.
    # test_invoice_order.py reads the blocks and compares the sequence,
    # which is the only way to say it.
    # ------------------------------------------- E-10, 11 Oct 2026
    # The colour of a switched-off button belongs where the other
    # two tones keep it. Before this, `btn action-danger` with the
    # disabled attribute rendered faint RED - the only switched-off
    # button in the application that was not grey.
    @{ File = 'pages\templates\base.html'; Text = '.btn.action-danger[disabled]'; What = 'a switched-off danger greys, like a primary and a secondary' },
    # And the three CRS delete modals, which the button sweep never
    # saw because the tool could not resolve a name under the
    # second template root. Solid Bootstrap grey beside solid
    # Bootstrap red, measured, on three screens.
    @{ File = 'crs\templates\crs\country_list.html'; Text = 'btn btn-danger'; What = 'the CRS delete modals wear house tones, not Bootstrap'; Absent = $true; Code = $true },
    @{ File = 'crs\templates\crs\submission_list.html'; Text = 'btn btn-secondary'; What = 'and their Cancel is paper, not solid grey'; Absent = $true; Code = $true }
    # -------------------------------------------- F2b, 13 Oct 2026
    # A border is named by the border token. The three that keep
    # the surface token are base's switched-off recipe, where the
    # edge is MEANT to be the fill - and they are a var() fallback,
    # not a plain border, which is how the patcher tells them apart.
    @{ File = 'pages\templates\home.html'; Text = 'solid var(--alv-surface-deep)'; What = 'no page draws a plain border on the panel-wash token'; Absent = $true; Code = $true }
    # -------------------------------------------- E15, 13 Oct 2026
    # alv_tree owns the Python stripper now. A file defining its
    # own again is how nine copies and three algorithms happened
    # the first time.
    @{ File = 'test_tree_roots.py'; Text = 'alv_tree.python_code_only'; What = 'the census calls the house stripper, not a copy'; Code = $true }
    # -------------------------------------------- MH-2, 13 Oct 2026
    # The CRS delete confirmations are the house danger header
    # now, like the sixteen in the first root. Bootstrap's
    # bg-danger coming back here is the regression.
    @{ File = 'crs\templates\crs\submission_list.html'; Text = 'modal-header bg-danger'; What = 'the CRS delete header is base .alv-modal-head--danger'; Absent = $true; Code = $true }
    # -------------------------------------------- DB-5, 12 Oct 2026
    # The landing dim. 0.45 put the tile label at 2.54:1 and the
    # accent icon at 1.91:1 on the page you arrive at, and no
    # contrast gate in this system reads opacity, so it passed
    # every sweep. 0.75 is the lowest dim at which the icon still
    # clears 3.0:1. Its return is the regression.
    #
    # IT DOES NOT SAY 'pointer-events: none'. The first version of
    # this row did, and the TWIN keeps that declaration on purpose
    # - so the sentinel asserted the absence of a string that must
    # be present, and took ten suites down with it. A control that
    # cannot pass is as bad as one that cannot fail. The grid's own
    # pointer-events is guarded in test_dash_std section 4, where
    # the CSS can be split and the two rules told apart.
    @{ File = 'pages\templates\property_management_dashboard.html'; Text = 'opacity: 0.45'; What = 'the landing dim stays at the measured 0.75'; Absent = $true; Code = $true }
    # ------------------------------------------------- PJ-1, 15 Oct 2026
    # Demetri: Back from the Project Edit screen went to the Project
    # Details page whichever page the edit was opened from. Two of the
    # three links that reach it had no way to say where they were.
    @{ File = 'pages\views\projects.py'; Text = 'PROJECT_ORIGINS'; What = 'a project edit knows which of three pages it was opened from' },
    # NO APOSTROPHE IN THE TEXT. PowerShell escapes one inside a
    # single-quoted string by DOUBLING it, and the gate's own table says
    # not to rely on that. The query is enough on its own and appears in
    # no backup of this page.
    @{ File = 'pages\templates\projects\projects.html'; Text = '?from=list'; What = 'and the Projects list says so, on the desktop link and the phone one' },
    @{ File = 'pages\templates\projects\projects_edit.html'; Text = 'from_gantt'; Absent = $true; Code = $true; What = 'the edit screen has one Back control instead of a branch with two' },
    # ------------------------------------------------- PJ-2, 15 Oct 2026
    # Demetri: "I do not like it when COMPLETED cuts off in the box. The
    # same happens with Greek." Three tiles in a col-md-4 gave the label
    # a 28px box for an 82px word, and SL-1's break-word made the wrap
    # land mid-word. One column, measured: one line at every width in
    # both languages.
    @{ File = 'pages\templates\projects\project_task_list.html'; Text = '--alv-stats-cols: 1'; What = 'the three task tiles stack, so COMPLETED stops breaking in half' },
    # ------------------------------------------------ TB-1a, 15 Oct 2026
    # Demetri named the destination as he reads it - "the System Tab".
    # There was no system tab: the label said SYSTEM and six places
    # underneath said future, and the tab beside it said FUNCTIONAL over
    # six that said alivente.
    @{ File = 'pages\templates\admin_apms.html'; Text = 'id="tab-system"'; What = 'the tab labelled SYSTEM is called system in the code as well' },
    @{ File = 'pages\templates\admin_apms.html'; Text = 'btn-future'; Absent = $true; Code = $true; What = 'and six class names that styled nothing are gone, not respelled' },
    # ------------------------------------------------ TB-1b, 15 Oct 2026
    # Nine Back buttons reported, twenty-three found, and my_profile a
    # twenty-fourth that landed on Home. The tab is derived from the
    # panel that links to the page, and the view paints it.
    @{ File = 'pages\\services\\landing_tabs.py'; Text = 'def landing_tab'; What = 'a landing page opens on the tab it was asked for, by key' },
    @{ File = 'pages\\templates\\finance_revenue_types.html'; Text = '?tab=setup'; What = 'and the six Finance Setup pages ask for Setup by name' },
    @{ File = 'pages\\templates\\my_profile.html'; Text = 'url ''home'' %}" class="btn action-back"'; Absent = $true; Code = $true; What = 'My Profile stops sending you to the Home page' },
    # ------------------------------------------------ NV-1a, 16 Oct 2026
    # Demetri: why are the Modules on the User Permission Page Green,
    # they should be teal. Green is a verdict here and a ticked box is a
    # selection. The active/inactive dot is the one real verdict on the
    # page and it keeps the good token.
    # THE STRING HAS TO BE ONE THIS ROUND INTRODUCED. The first cut of
    # this row named '.permission-item.granted', which is the SELECTOR -
    # present long before this round, so the claim could never have
    # failed. test_sentinels section 4 names a row like that within one
    # run, and it is right to: a row that cannot fail is not a test.
    @{ File = 'pages\templates\user_permissions.html'; Text = 'font-size:12px; color:var(--alv-accent-ink)'; What = 'a granted module is a selection, so the page reads in the accent' },
    @{ File = 'pages\templates\user_permissions.html'; Text = 'icon.style.background'; Absent = $true; Code = $true; What = 'and the colour is declared once, in the stylesheet, not three times' },
    # ------------------------------------------------ NV-1b, 16 Oct 2026
    # Demetri: why does the Upload Title Deeds table not resemble our
    # standards. It wore no house class and re-declared base's whole
    # phone card block - fifteen rule openings, twelve of them base's.
    @{ File = 'pages\templates\title_deeds_management.html'; Text = 'class="table alv-table"'; What = 'the title deeds table wears the house table class' },
    @{ File = 'pages\templates\title_deeds_management.html'; Text = 'mobile-action-bar cols-2'; What = 'and asks base for the two columns it draws' },
    @{ File = 'pages\templates\title_deeds_management.html'; Text = '.mobile-action-bar'; Absent = $true; Code = $true; What = 'while declaring the bar NOWHERE itself - a page copy of that rule hid the bar on every phone' },
    # ------------------------------------------------ NV-1c, 16 Oct 2026
    # Demetri asked for Edit and Notify Now in the Issues comments to be
    # icon-only, and for a standard for Notify - a bell with a Notify
    # Now hover. ADVANCE splits by consequence, so the bell is warn.
    @{ File = 'pages\templates\base.html'; Text = '.icon-notify'; What = 'Notify is in the shared icon vocabulary, not on one page' },
    @{ File = 'alv_rowactions.py'; Text = "'notify': ADVANCE"; What = 'and the vocabulary sorts it after Edit without the markup saying so' },
    @{ File = 'pages\templates\fsr_details.html'; Text = 'status-btn'; Absent = $true; Code = $true; What = 'the two comment controls are icon-only at every width' },
    @{ File = 'pages\templates\physical_invoice_list.html'; Text = 'Duplicate is for customer invoices only'; What = 'and a tenant invoice says on screen why it has no copy' },
    # ------------------------------------------------ NV-1d, 16 Oct 2026
    # Demetri asked for a View button beside Edit and Delete on
    # Customers. There is no customer detail route, so View opens a
    # read-only sheet - the shape he described for receipts in the same
    # batch - carrying the four fields the table has no room for.
    @{ File = 'pages\templates\customer_list.html'; Text = 'js-cust-view'; What = 'Customers has a View, and it needs no edit permission' },
    @{ File = 'pages\templates\customer_list.html'; Text = 'cust-sheet-row'; What = 'and what it shows is MARKUP a gate can read, not a built string' },
    # NAMED AS THE ROW BUILDS IT. `billing_address` alone is in this
    # file three times already - a profile read, an edit POST and a
    # create - so the bare word could never have failed.
    @{ File = 'pages\views\physical_invoices.py'; Text = '"billing_address": c.billing_address'; What = 'the four hidden fields reach the template without a new query' },
    # ------------------------------------------------- TD-2, 16 Oct 2026
    # Demetri, with the two screens side by side: should the Title Deed
    # table not match the Lease Agreement table - there should only be
    # one Action column. NV-1b put that table on .alv-table and left its
    # two action columns alone.
    @{ File = 'pages\templates\title_deeds_management.html'; Text = 'data-label="Actions" class="desktop-action-cell cell-actions"'; What = 'the title deeds table has ONE action column, like the lease agreements table' },
    @{ File = 'pages\templates\title_deeds_management.html'; Text = '<span class="text-muted">-</span>'; Absent = $true; Code = $true; What = 'and a disabled twin where it used to draw a dash - a dash reads as missing DATA, not as a missing action' },
    # ------------------------------------------------- LV-1, 16 Oct 2026
    # A LEAVE entry short-circuited every button in its wrapper. Eleven
    # entries hid 33 buttons; 25 of them wore a raw Bootstrap colour and
    # three of the rest were action-primary Saves nobody was checking.
    @{ File = 'Show-ButtonDrift.py'; Text = "'zoom-controls':           [('*', S)]"; What = 'widget chrome is a DECIDED tone now, not a silence' },
    @{ File = 'Show-ButtonDrift.py'; Text = "'input-group-append':      [('save', P), ('*', S)]"; What = 'and Save is named FIRST, so the three property_assets Saves keep their tone' },
    @{ File = 'pages\templates\property_assets.html'; Text = 'btn-secondary btn-sm'; Absent = $true; Code = $true; What = 'the Cancels beside them are house secondary' },
    @{ File = 'pages\templates\projects\project_gantt.html'; Text = 'btn-outline-primary'; Absent = $true; Code = $true; What = 'and Fit to Screen stops being the only Bootstrap blue in a zoom control' },
    # ------------------------------------------------- DT-1, 16 Oct 2026
    # Demetri: make the Home and Notifications tables match the rest of
    # the application. They could not be reported by any table suite,
    # because they are built in JavaScript as strings.
    @{ File = 'pages\\templates\\home.html'; Text = 'table alv-table'; What = 'DT-1: the Home tables are on the house table standard' },
    @{ File = 'pages\\templates\\home.html'; Text = 'data-table'; Absent = $true; Code = $true; What = 'DT-1: and the page keeps no table stylesheet of its own' },
    @{ File = 'pages\\templates\\notifications.html'; Text = 'alv-pill alv-pill-attn'; What = 'DT-1: the Notifications status chips are house pills' },
    @{ File = 'pages\\templates\\notifications.html'; Text = 'status-badge'; Absent = $true; Code = $true; What = 'DT-1: and the solid-fill status tones are gone' },
    # ------------------------------------------------- AB-1, 16 Oct 2026
    # Demetri, testing Administration: every notification card collapsed
    # when the page opens, the list alphabetical, and Save Permissions at
    # the top of the page rather than the foot.
    @{ File = 'pages\templates\notification_settings.html'; Text = 'sessionStorage'; Absent = $true; Code = $true; What = 'AB-1: the notification cards remember nothing - every arrival is collapsed' },
    @{ File = 'pages\templates\notification_settings.html'; Text = 'localeCompare'; What = 'AB-1: and the list is alphabetical by what each card says it is' },
    @{ File = 'pages\views\notifications.py'; Text = 'f"?open={quote(notification_type)}"'; What = 'AB-1: a save says which card it saved, so that one reopens' },
    @{ File = 'pages\templates\user_permissions.html'; Text = 'MOVED UP FROM THE FOOT OF THE PAGE'; What = 'AB-1: Save Permissions and Back are at the top, like every other screen' },
    # ------------------------------------------------- HM-4, 16 Oct 2026
    # Demetri, testing Home: can we put the OPEN in the box.
    @{ File = 'pages\templates\home.html'; Text = '<span class="iss-head">Open</span>'; What = 'HM-4: the Open label is a term inside its strip' },
    @{ File = 'pages\templates\home.html'; Text = '<p class="iss-head">'; Absent = $true; Code = $true; What = 'HM-4: and is no longer a block on a line of its own' },
    # ------------------------------------------------- WM-1, 16 Oct 2026
    # Demetri, testing Administration: the member count should be
    # clickable and show the names.
    @{ File = 'pages\templates\workspace_management.html'; Text = 'alv-pop-trigger'; What = 'WM-1: the member count opens the names' },
    @{ File = 'pages\templates\workspace_management.html'; Text = 'ws-members" title='; Absent = $true; Code = $true; What = 'WM-1: and the hover-only tooltip is gone with it' },
    # ------------------------------------------------- AE-4, 16 Oct 2026
    # The suite clones the control instead of imitating it.
    @{ File = 'test_ae_line.py'; Text = 'const twin = model.cloneNode(true)'; What = 'AE-4: the probe is a clone of the real control' },
    # ABSENT ON THE CONSTRUCT, NOT ON THE PROSE. The replacement NAMES
    # the old padding in its own comment, explaining what went wrong, so
    # a sentinel on that spelling would refuse the round's own output -
    # which it did, in seven suites at once. createElement is the thing
    # that must not come back, and it is gone.
    @{ File = 'test_ae_line.py'; Text = 'createElement'; Absent = $true; What = 'AE-4: and the suite builds no control of its own' },
    # NOT Code = $true. The note lives in a CSS comment, and code_only
    # BLANKS those - so a Code sentinel would be absent in every version
    # ever written, including the ones where the sentence was there. It
    # would pass for ever and discriminate never, which test_sentinels
    # catches by trying each row against 45 older copies of the file.
    # A sentinel that cannot fail is not a sentinel - the same lesson
    # as the scrollWidth check this round threw away.
    @{ File = 'pages\templates\act_expense.html'; Text = 'A date input needs 165'; Absent = $true; What = 'AE-4: the page no longer quotes an imitation as a measurement' },
    # ------------------------------------------------- LF-1, 17 Oct 2026
    @{ File = 'test_label_fit.py'; Text = 'PJ-2'; What = 'LF-1: the narrowest width asks the wrap law' },
    @{ File = 'test_label_fit.py'; Text = 'white-space:nowrap'; What = 'LF-1: and measures what each label needs by cloning it' },
    # ------------------------------------------------- GT-2, 17 Oct 2026
    @{ File = 'Push-PendingChanges.ps1'; Text = 'alv_run.py'; What = 'GT-2: the gate runs its suites through alv_run' },
    # NO ABSENT SENTINEL ON THIS FILE, AND IT IS NOT AN OVERSIGHT.
    #
    # A sentinel row lives IN Push-PendingChanges.ps1. An ABSENT row
    # naming a string therefore PUTS that string into the very file it
    # declares the string missing from, and the check fails the moment
    # it is written. Three spellings were tried before the shape of the
    # problem was clear - the loop header, then a variable, then the
    # padding expression - and every one of them failed the same way,
    # because the fault is structural and not a choice of words.
    #
    # The claim is kept where it can be made: test_gate_speed.py asserts
    # by the SHAPE of the statement that no suite loop survives, which a
    # file checking itself cannot do.
    @{ File = 'alv_run.py'; Text = 'PLANTERS'; What = 'GT-2: the fourteen that must stay serial are named, not guessed' },
    # ------------------------------------------------- CC-2, 17 Oct 2026
    @{ File = 'pages\templates\celebration_management.html'; Text = 'contactDetailModal'; What = 'CC-2: the contact opens in a modal' },
    @{ File = 'pages\templates\celebration_management.html'; Text = 'toggleCardExpand'; Absent = $true; Code = $true; What = 'CC-2: and no longer grows the card in place' },
    # ------------------------------------------------- SB-1, 17 Oct 2026
    @{ File = 'pages\templates\property_detail.html'; Text = 'report-invoice-icon'; What = 'SB-1: one invoice icon on both routes' },
    @{ File = 'pages\templates\property_detail.html'; Text = 'font-size: 1.2em'; Absent = $true; Code = $true; What = 'SB-1: and it is not sized inline any more' },
    # ------------------------------------------------- DG-1, 17 Oct 2026
    @{ File = 'pages\templates\act_expense.html'; Text = 'action-secondary action-danger btn-sm'; What = 'DG-1: the Delete button wears the house pair' },
    # ------------------------------------------------- RI-1, 17 Oct 2026
    @{ File = 'pages\views\recipes\ai_extract.py'; Text = 'IMAGE_WIRE_MEDIA_TYPE'; What = 'RI-1: the encoder says what it produced' },
    @{ File = 'pages\views\recipes\ai_extract.py'; Text = 'MEDIA_TYPES[file_type]'; Absent = $true; What = 'RI-1: and the extension no longer picks the media type' },
    # ------------------------------------------------- AR-1, 17 Oct 2026
    @{ File = 'alv_run.py'; Text = 'died.append'; What = 'AR-1: a suite that printed no tally is re-run once, alone' },
    # ------------------------------------------------- CC-3, 17 Oct 2026
    @{ File = 'pages\templates\celebration_management.html'; Text = 'copyInto'; What = 'CC-3: the copy is shown and its controls are wired' },
    # ------------------------------------------------- NW-1, 17 Oct 2026
    @{ File = 'alv_offline.py'; Text = 'LOOPBACK'; What = 'NW-1: the network guard spares a suite own loopback server' },
    # ------------------------------------------------- PG-1, 18 Oct 2026
    @{ File = 'alv_preflight.py'; Text = 'as_left_by'; What = 'PG-1: the pre-flight says what missing backups cost' },
    # ------------------------------------------------- MP-1, 18 Oct 2026
    #
    # 'missing_units.append' AND NOT 'missing_units'. test_sentinels.py
    # asks of every row whether there is ANY historical version of the
    # file in which its text is absent - a row that cannot fail is a row
    # that watches nothing - and it refused the shorter text, because
    # `seen_missing_units` has carried `missing_units` as a SUBSTRING
    # since the aggregator was written.
    #
    # MN-1, 18 Oct 2026 - THREE OF THE FOUR ROWS THAT WERE HERE WATCHED
    # FILES RELEASE 3 DELETES: create_meal_plan.html's esc() helper,
    # view_meal_plan.html's repaired selector, and the calendar week's
    # query map. A sentinel on a file that does not exist is not a
    # failed sentinel, it is a row nobody can read. The one that
    # survives watches the aggregator, which survives.
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'missing_units.append'; What = 'MP-1: the shopping list names the ingredients it dropped' },
    # ------------------------------------------------- MN-1, 18 Oct 2026
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def aggregate_meal_entries'; What = 'MN-1: the aggregator walks dated entries, not a plan' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'stepServings('; What = 'MN-1: servings save on press, with no Save button' },
    # ------------------------------------------------- MH-1, 18 Oct 2026
    @{ File = 'pages/help_content/administration.html'; Text = 'data-module-slug="meal_plans"'; What = 'MH-1: the Meal Plans guide exists at all' },
    # ------------------------------------------------- MH-2, 18 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'meal_plansHelpModal'; What = 'MH-2: the planner has a Help button, wired to the guide' },
    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-name="Adding a Meal"'; What = 'MH-2: and the guide describes adding a meal to a day, not building a plan' },
    # ------------------------------------------------- MW-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="copyRangeModal"'; What = 'MW-1, as CP-2 left it: any span of days can be copied onto a landing date - a day, a week, a month or a range you type' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="menusModal"'; What = 'MW-1, as CP-2 left it: a week saved under a name by weekday, applied to any week, and deleted - all three in one dialog' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'added alongside'; What = 'MW-1: and the dialog counts what is there BEFORE the button - add alongside, and say so first' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def copy_week_rows('; What = 'MW-1: one function copies a week, parents before leftovers' },
    @{ File = 'pages/urls.py'; Text = "name='meal_week_preview'"; What = 'MW-1: the route the dialog asks the count of' },
    # ------------------------------------------------- MO-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="noteModal"'; What = 'MO-1: a day can take a planned night that is not a recipe' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="leftoverModal"'; What = 'MO-1: and a meal can be eaten again on another day' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'leftover-item'; What = 'MO-1: the leftover row is its own row - no stepper, because it buys nothing' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def add_leftover('; What = 'MO-1: and a leftover of a leftover points at the original' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "select_related('recipe', 'leftover_of')"; What = 'MO-1: in the ONE query the week already costs' },
    # ------------------------------------------------- NF-1, 19 Oct 2026
    @{ File = 'check_gates.py'; Text = 'def _toolchain('; What = 'NF-1: the round-name check asks the whole toolchain, not just the register' },
    @{ File = 'check_gates.py'; Text = 'name, taken, declared, referenced = nm'; What = 'NF-1: and the caller reads all four answers' },
    # ------------------------------------------------- MH-3, 19 Oct 2026
    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-name="Moving a Week"'; What = 'MH-3: the guide has a tab for copying a week and saving a Menu' },
    @{ File = 'pages/help_content/administration.html'; Text = 'Leftovers, and they are free'; What = 'MH-3: and tells the reader the second night costs nothing' },
    # ---------------------------- MC-4, 19 Oct 2026 - RETIRED by MV-2
    # Both rows pinned strings in the mini calendar's markup, and MV-2
    # deleted the component. The claim they defended - a grid must
    # contain the loop that fills it - is now test_month_view's, which
    # counts COLUMNS in a browser rather than reading a class name.
    # ------------------------------------------------- PK-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: repeat(auto-fill, minmax(240px, 1fr))'; What = 'PK-1: the recipe picker is a grid, not one column in a wide dialog' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'function pfChanged('; What = 'PK-1, widened by PF-2 19 Oct 2026: it filters, composing with the search rather than replacing it - by course and by four more things since Demetri asked for them' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerCount"'; What = 'PK-1: and says how many of how many are showing' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "prefetch_related('courses')"; What = 'PK-1: the course ids come from one query, not one per card' },
    # ------------------------------------------------- GS-1, 19 Oct 2026
    @{ File = 'alv_run.py'; Text = 'CONTENDED = ['; What = 'GS-1: a suite whose verdict moves with the load runs alone, because a pool failure cancels the rest of the sweep' },
    @{ File = 'alv_run.py'; Text = 'Only this list prevents it'; What = 'GS-1: and the phase 3 rescue is left alone - it explains a stop, it cannot undo one' },
    # ------------------------------------------------- MX-1, 19 Oct 2026
    @{ File = 'pages/migrations/0101_drop_meal_plan.py'; Text = "DeleteModel(name='MealPlanRecipe')"; What = 'MX-1: the old planner three tables go, children first - the step 0100 said would come last' },
    @{ File = 'pages/migrations/0101_drop_meal_plan.py'; Text = 'dropping %s - %d row(s)'; What = 'MX-1: and the count is taken BEFORE the drop and printed, because a DeleteModel reverses into an empty table' },
    # ------------------------------------------------- PF-2, 19 Oct 2026
    @{ File = 'pages/views/recipes/_recipe_filter.py'; Text = 'def filter_recipes('; What = 'PF-2: ONE place decides what a recipe filter selects, asked by the library and by the picker' },
    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'recipes = filter_recipes(recipes, _sel, request.user)'; What = 'PF-2: and the library stopped keeping its own copy of it' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def picker_recipes('; What = 'PF-2: the picker asks the server for its rows, after Demetri said it only allows you to choose Course' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerAuthor"'; What = 'PF-2: and all five filters are there - course, category, protein with vegetarian, author and favourites' },
    # ------------------------------------------------- MV-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'aria-label="Calendar view"'; What = 'MV-1: Month, Week and Day on base .alv-seg - server-rendered links, not JavaScript, so the view is in the URL' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'ONE ANCHOR DATE FOR THREE VIEWS'; What = 'MV-1: and the three zoom levels travel on one ?date=, so switching keeps the day you were looking at' },
    # ------------------------------------------------- MV-2, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="month-grid"'; What = 'MV-2: the month is the view, full page - a cell is 162px without the mini calendar and 113px with it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE MINI CALENDAR WAS HERE'; What = 'MV-2: and the 320px strip Demetri asked about is gone, with the record of why it went' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'THREE SHOWN, THE REST COUNTED'; What = 'MV-2: a cell shows three names then +n more - his own answer to what a full day looks like' },
    # ------------------------------------------------- MV-3, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-grid"'; What = 'MV-3: the week is seven columns - 4,900px of day cards becomes about 420px, after Demetri said the daily list was not required' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="day-strip"'; What = 'MV-3: and on a phone the week is a day strip with one day open, because seven columns is 51px there' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'WHICH DAY THE PHONE OPENS ON'; What = 'MV-3: the anchor when it is in this week, the Monday otherwise - one rule, where the anchor already lives' },
    # ------------------------------------------------- MV-4, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'ONE DAY, NOT SEVEN'; What = 'MV-4: the vertical list of seven day cards is gone - about 4,900px of it - which is what Demetri meant by the daily list not being required' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE DAY HAS ITS OWN NAV'; What = 'MV-4: and the Day view moves by days, because week arrows above one Tuesday move you seven' },
    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'def ingredient_rows('; What = 'RD-1: ONE read of a whole recipe, asked by the page, the PDF and the dialog - they held two copies of it and the two disagreed' },
    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'GRAMS_PER'; What = 'RW-1: the weight is worked out in grams - round(x, 1) is 100g of precision in kilograms, and a cup of flour at 0.120kg was reading 100g' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def planner_back('; What = 'PB-2: a write on the planner leaves you where you were - eleven redirects carried the date and dropped the view, so every add and remove bounced you to Month' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def move_meal_entry('; What = 'RD-2: move a meal to another day, and its leftovers travel with it keeping the gap - MM-1 logic, finally with buttons to reach it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-chip='; What = 'RD-2: a meal in Month or Week is a button with a menu - View, Move to and Remove - because a 152px column has room for a name and nothing else' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'week-nav-btn is-today'; What = 'MB-2: Today is an action, not a third direction - it sat between the two arrows wearing the same 44px box' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-col-body"'; What = 'WC-1: clicking a day opens the picker in WEEK view too - it only did so in Month, because the two views were built in different rounds' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WRAPPER THAT NEVER CLOSED'; What = 'DB-1: 88 rules and 2,471 lines were nested inside a max-width 1200px block that was never closed, so the date bar rendered as default browser buttons on any screen wider than that' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },
    @{ File = 'pages/templates/meal_plan_shopping_list.html'; Text = 'ALV_CAN_GENERATE'; What = 'SB-2: step 2 had TWO primaries - Done and Print, written on different days by rounds that could not see each other state. Demetri chose Done. And Generate List is hidden when no ingredient has a shopping unit, because step 1 is not rendered at all then - the same fault he reported about Print on 3 October' },
    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'unshare_file(original_recipe'; What = 'SI-1: duplicate_recipe set pk to None and saved, which copies the PATH of the photo and not the photo - two rows, one file. Changing the picture on either then deleted it for the other, which is how 71 Cottage Pie and 336 Beans, Edamame lost theirs on Live' },
    @{ File = 'pages/models.py'; Text = 'def delete_unheld'; What = 'SI-1: and a delete counts the rows naming that path before it removes the bytes - the copies made BEFORE this round are the ones that line protects' },
    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'delete_unheld(Recipe, released'; What = 'SI-1: and it runs AFTER recipe.save(), not before. The old order deleted the photo and then saved, so a save that raised - a missing difficulty_level does it - left the file gone and the row still naming it, which is the same broken image from the other direction' },
    @{ File = 'pages/management/commands/check_recipe_files.py'; Text = 'def held_names'; What = 'SI-1: the instrument. Missing, shared and orphaned, asked of the storage rather than reasoned about - the rebuild found the first two by luck, which is not a detector' },
    @{ File = 'pages/models.py'; Text = 'NAME_SLUG_CAP'; What = 'NL-1: four recipes on Live generated a display filename longer than the 100-character column, and Django truncated the stem mid-timestamp and added a random suffix rather than refusing - which left them permanently stale, because display_copy_is_stale compares names. The columns are 255 and the slug is bounded, so both halves have to fail before it can happen again' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = '{{ back_url }}'; What = 'PT-1: Back was the bare planner URL, so Back from a printed week landed on the month view on today date - Demetri reported it for all three views. The origin is carried because no arithmetic on from and to can recover it: a day sheet and a one-day range are the same two dates' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'start = min(max(start, range_min), range_max)'; What = 'PT-1: and the week bounds are CLAMPED on the server, not only offered as min and max to a browser - the attributes stop somebody picking a date outside the week, the clamp stops it working' },
    @{ File = 'pages/views/receipts.py'; Text = 'def cash_receipt_detail'; What = 'RV-1: the PDF shows the receipt as issued; nothing showed the record behind it. void_reason was captured, stored, and never once displayed anywhere in the application' },
    @{ File = 'pages/templates/cash_receipt_detail.html'; Text = 'rv-trail'; What = 'RV-1: and the history is built in the VIEW, oldest first, each event present only if it happened - a template that decides which events occurred cannot be asked how many it drew' },
    @{ File = 'pages/templates/base.html'; Text = 'alv-ref-link'; What = 'IR-1: the receipt number was grey monospace and the invoice number a teal link - two registers for one kind of identifier, Demetri 16 Oct. One rule in base now, which BOTH pages take; a second copy would make one register true by coincidence' },
    @{ File = 'pages/templates/base.html'; Text = '.alv-table .ref'; Absent = $true; Code = $true; What = 'IR-1: and the rule it replaced is gone rather than left. It had one consumer and no suite; a base rule nothing uses is one the next page picks up by accident' },
    @{ File = 'pages/models.py'; Text = 'def issue_token'; What = 'ES-1: the emailed link IS the credential, so the token is stored as a sha256 and the raw value exists only as this method return. A resend mints a new one and the old link dies - a link that expires and then works again never really expired' },
    @{ File = 'pages/models.py'; Text = 'class LeaseSigningEvent'; What = 'ES-1: and the audit trail is append only, because with no certificate it and pdf_sha256 ARE the evidence - nothing in the file proves anything' },
    @{ File = 'pages/services/lease_sealing.py'; Text = 'THE ORIGINAL IS NEVER TOUCHED'; What = 'ES-2: signatures go on an APPENDED page, so the lease everybody signed stays byte for byte the lease that was sent - which is also why this works on a PDF nobody here produced' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf'; What = 'ES-2: and the pin lives HERE because railway.json installs from this file, not requirements.txt - the same line in the other file would deploy nothing and fail at the first import on Live' },
    @{ File = 'pages/views/tenants.py'; Text = 'let_go_of_file'; What = 'UO-1: the old lease is RELEASED before the save and its bytes deleted after it, because delete-then-save destroys the file whenever the save raises - which is how two recipe photos were lost on 22 October, and a signed lease cannot be taken again' },
    @{ File = 'Show-RequirementsAudit.py'; Text = 'font faces resolved by name at runtime'; What = 'CF-2: pymupdf-fonts is named by pymupdf at runtime and imported by nothing, so the audit called it tooling-only - a verdict that, acted on, prints a row of dots where the tenant signed, on Live and nowhere else' },
    @{ File = 'Push-PendingChanges.ps1'; Text = 'ZERO MEANS SAY NOTHING'; What = 'WK-1: the sweep can be told how many workers to use, and a push that does not mention them behaves exactly as before - 6 is right on a machine that can take it and wrong on one that cannot, and rc=0xC0000374 killed two sweeps on 23 October saying so' },
    @{ File = 'pages/views/lease_signing.py'; Text = 'ONE ROW PER ENVELOPE'; What = 'ES-3a: the register is one row per ATTEMPT, not per tenant - which is why it is not a tab on Manage Lease Agreements, where one tenant with four attempts could only ever show one of them' },
    @{ File = 'pages/templates/lease_signing_list.html'; Text = 'data-label'; What = 'ES-3a: and the phone layout is base turning rows into cards, not a ninth hand-written copy of something base already does' },
    @{ File = 'pages/models.py'; Text = 'def tenant_display_name'; What = 'T2-2: one spelling of how a tenancy is NAMED on a screen - the register prints it today and the four reports T2-4 builds print the same thing, because five screens each joining two names for themselves is five chances to disagree about the separator' },
    @{ File = 'pages/templates/tenant_add.html'; Text = 'id="t2-add-btn"'; What = 'T2-2: one tenant stays the default and has to LOOK like it - the three second-tenant fields sit behind Add Second Tenant rather than on the form, and the button itself only appears once Tenant Type says Individual' },
    @{ File = 'pages/models.py'; Text = 'def has_second_tenant'; What = 'T2-1: one predicate for whether a tenancy has a joint tenant, named once - twenty templates and twenty-seven python modules read the first tenant details, and each deciding this for itself is how two screens come to disagree about whether somebody exists' },
    @{ File = 'pages/forms.py'; Text = 'tenant_2_name'; What = 'T2-1: and the three columns are in TenantForm.fields, which is an explicit list - a column missing from it is one the form silently drops, so the user types a joint tenant and the save forgets them without a word' },
    @{ File = 'alv_plant.py'; Text = 'def recover'; What = 'LK-1: fifteen suites write into real files and restore in a finally, which a SIGKILL does not run - the defect stays and nothing noticed. The lock is armed around the PLANTERS list, names every file a planter did not put back, and deliberately restores nothing' },
    @{ File = 'pages/views/users.py'; Text = "to_attr='member_list'"; What = 'WN-1: the workspace list ran one SELECT per workspace, which WM-1 left deliberately on 16 October and named as its own round. A Prefetch with to_attr does it in two, whatever N is - and to_attr because the template reads member_list, and an undefined name in a template is silence' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pillow-heif'; What = 'CF-1: railway.json installs THIS file, and it did not carry pillow-heif - so HEIC uploads from an iPhone failed quietly on Live, because pages/utils.py guards that import on purpose. Also UTF-8 now, and five open-ended packages bounded' },
    @{ File = 'pages/models.py'; Text = 'def store_display_jpeg'; What = 'SD-1: the ONE place that stores a display copy. Django storage does not overwrite, so --rebuild --write used to write a suffixed copy beside the one it meant to replace, leave the old on the volume and leave the row permanently stale. This deletes the target path first and checks the name it got' },
    @{ File = 'mysite/urls.py'; Text = 'def deploy_version'; What = 'DP-1: /version/ answers seven characters of hex - the commit the running process was built from - and this script asks it after a push until it answers the SHA just pushed. No Railway token anywhere' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'saveColumnOrder'; What = 'WD-1: the week view seven columns drag into order through reorder_meal_day, the endpoint RO-1 built - a column is a date. Within a column only: across days writes a date and that is Move' },
    @{ File = 'pages/help_content/administration.html'; Text = 'how far into the menu'; What = 'HG-1: the Moving a Week tab describes the feature MN-2 actually shipped - a menu is a span of days kept by offset, saved with a From and a To and landed on a date you choose. It said by weekday, and test_meal_guide3 was requiring it to' },
    @{ File = 'pages/templates/view_recipe.html'; Text = 'NOT A DATA TABLE'; What = 'VR-1: the cooking schedule readout and its printed copy are key-and-value lists, not data tables, and the three colour literals in the first of them became tokens' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def reorder_meal_day'; What = 'RO-1: the only endpoint that moves a row within its day - sort_order has decided the order since MN-1 and nothing could write it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'day-rows'; What = 'RO-1: the day card rows drag by the same grip the ingredients list uses, and the grip is hidden unless SortableJS actually loaded' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'MENU_MAX_DAYS'; What = 'MN-2: a saved menu is a span of days up to a quarter long, not a week, and Apply puts it on a date you choose - the table always allowed both and the two views did not' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'mn-preset'; What = 'MN-2: the Saved Menus dialog has a From, a To and a Landing on, with the same three presets CP-2 gave Copy' },
    @{ File = 'pages/templates/base.html'; Text = 'THE ONE MESSAGE LOOP - BM-1'; What = 'BM-1: base renders the message bar for every page that extends it - 81 identical copies removed, and the 55 pages that had none can show a message at last' },
    @{ File = 'pages/models.py'; Text = 'DISPLAY_FLOOR'; What = 'PX-2: a photo under 1200px on the long edge is resampled up once, on the server, with Lanczos and a light sharpen - the phone hero asks for about 1170 and the browser was doing that stretch itself on every page load' },
    @{ File = 'pages/management/commands/convert_recipe_photos.py'; Text = '--rebuild'; What = 'PX-2: the batch command can rebuild every display copy, because staleness is decided from filenames and this round changed what a display copy contains without changing its name' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'RG-3, 21 Oct 2026'; What = 'RG-3: the printed week and day are as tall as their content - 186mm to 55mm and 258mm to 44mm on his own week. The ruled fill and the Notes block are gone; the month still fills one sheet' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'corrected by WF-1'; What = 'WF-1: the selected week in Month view fills with tag-moss-soft and keeps its accent rule - a tint that clears every other fill on that grid by 6.9 dE, from the decorative palette WT-1 never looked at' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'THE RANGE - RG-2'; What = 'RG-2: From and To on the printable plan, on one 44px line like the shopping list - and a line saying what the second Print press does, which is the answer he chose to "why do we press Print twice"' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'is-{{ sheet }}'; What = 'RG-1: the printed sheet follows the range - a day prints a day, a week prints seven columns you can write in, and a month fits on one sheet of A4. Day view used to print a week with six columns greyed out' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'BACK ON THE BAR - CP-2'; What = 'CP-2: Copy... and Saved Menus... are bar buttons, so they can be reached on a desktop - MW-1 put all three week controls inside the More menu, which base hides above 768px, and for two days they existed only on a phone' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def copy_meal_range('; What = 'CP-2: a copy takes any span of days onto a landing date - day, week and month are presets that fill in two dates, because copy_week_rows has always worked by date offset' },
    @{ File = 'test_bar_order.py'; Text = 'A BAR IS NOT ALWAYS A <div>'; What = 'BA-1: the bar-order instrument reads the LIVE tree for its tree-wide claim, sees a bar written as a form, and asserts one bar per page - three holes that let four separate faults ship between 19 and 21 October' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'AND HELP - HP-1'; What = 'HP-1: Help is in the planner More menu, so it can be reached on a phone - base hides every secondary below 768px in a bar that has a menu, and MW-1 added the menu without putting Help in it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE MESSAGE BAR - MG-1'; What = 'MG-1: the planner, the shopping list and the printable plan render Django messages - between them they carried none, so twelve messages.success() calls queued in the session and surfaced on whatever screen came next' },
    @{ File = 'pages/templates/meal_plan_shopping_list.html'; Text = 'UNDER THE BAR - SH-2'; What = 'SH-2: the from/to range sits under the action bar and is a compact row rather than a second .page-action-buttons above it - the page had two bars, which 3.4 forbids, and two visible primaries' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEK OWNS BOTH NOW'; What = 'WT-1 as WF-1 corrected it: the selected week in Month view wears an accent rule above and below AND a moss fill. WT-1 found the fault - it used to fill with the exact token the meal pills fill with, so a pill on that row was its 1px border and nothing else - and concluded there was no room for a fourth fill after measuring two candidates. There was: moss clears every fill on that grid by 6.9 dE' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE PRIMARY FIRST - BO-1'; What = 'BO-1: the planner bar reads PRIMARY, SECONDARIES, BACK - Shopping List is the page verb and Print follows it, where PP-1 had put Print above it' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-when="today">Today<'; What = 'SC-1: the add-to-planner shortcut says Today rather than Tonight - the value was always today, and this module has no meal types, so it cannot know morning from evening' },
    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-slug="mp-print"'; What = 'MH-5: the meal plans guide has eight tabs and no longer describes the two-panel screen, the trashcan or the eye - none of which has existed since release 4 push 1' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def meal_plan_print('; What = 'PP-1: a meal plan can be printed - there was no print support on the planner at all, and the only mention of print on that screen was a comment about the print-leak rule' },
    @{ File = 'test_console_encoding.py'; Text = 'alv_conenc_'; What = 'CE-1: the console-encoding probe writes its throwaway script into a directory of its own - it used to write a .py into the repository, which test_code_only lists and reads, and one unlucky interleaving stopped a push at 290 of 395' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "'sl_from': sl_from"; What = 'SL-7: the Shopping List button covers the view you are on - it was hard-wired to the week, so Month bought for a week of the month and Day bought for a week round the day' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerNote"'; What = 'NT-1: a note can be added from Month and Week - openNote was reachable only from the Day card, and a note belongs to a DAY so it joins the dialog that adds things to one' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-act="leftovers"'; What = 'LO-1: leftovers can be added from Month and Week - openLeftover was reachable only from the Day card, so Demetri asked how to do it from the calendar and the answer was that he could not' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'A TOKEN FOR EVERYONE WHO CAN PRESS SOMETHING'; What = 'FV-1: the favourites heart is drawn for every user and posts with a CSRF cookie that was only set for users who may EDIT recipes - so for anybody else the heart filled in, the post came back 403, and it emptied again' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-id='; What = 'AP-1: a recipe goes on a day without leaving the library - beside the heart on all FOUR card renderings, because this page draws every card twice and the JavaScript copies redraw after a search' },
    @{ File = 'pages/templates/base.html'; Text = 'window.alvToast'; What = 'AP-1: and base owns the toast, the way it owns the modal overlay - a confirmation that does not take the page away, with an Undo, because django messages need a render and the whole point is staying put' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "payload['added_id']"; What = 'AP-1: the add endpoint hands back the row it just made - it created one and dropped it, so an Undo had nothing to point at' },
    @{ File = 'pages/templates/meal_planner.html'; Text = "document.addEventListener('DOMContentLoaded', bind)"; What = 'RL-1: the picker reload is bound after the document is parsed - base loads jQuery near the end, so PS-1 guard found none and silently bound nothing, and the month grid stayed stale until a hand refresh' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def planner_back(request, when=None, stay=True)'; What = 'PB-3: a write returns you to the DAY you were on, not to a date computed from the write - adding leftovers in Day view moved you to the Monday of the leftovers week, which read as the meal vanishing' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'name="from_date"'; What = 'PB-3: and the reader tells the server where they were, on the same nine forms PB-2 gave the view - one place instead of sixteen call sites each guessing' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'border-radius: 999px'; What = 'CL-1: a meal in the calendar is a pill again - RD-2 made the chips buttons and reset background, border and font in a LATER stylesheet, which beat the chip own rule and left 16px plain text' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'font: inherit'; Absent = $true; Code = $true; What = 'CL-1: and the shorthand that took the type size with it is gone - font-family is what a button needed, not the whole font' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="dc-tags"'; What = 'DC-1: the Day card is one line and the width carries the recipe facts - it was four lines using 37% of the row' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def day_payload('; What = 'PS-1: ONE description of what is on a day, asked by the dialog on open, on every add and on every remove, so the strip cannot drift from the calendar' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'function pickAdd('; What = 'PS-1: clicking a recipe ADDS it - twenty actions to put four things on a Saturday became seven, because the filters stop being forgotten between adds' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerDayList"'; What = 'PS-1: and the dialog shows the day it is adding to, each row removable - without it a mis-click would be a row you could not see' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-quicklook='; What = 'RD-3: the photograph opens the recipe without leaving the library - browsing 324 recipes stopped meaning 324 page loads' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'id="recipeViewIframe"'; Absent = $true; Code = $true; What = 'RD-3: and the second recipe dialog is gone - a whole page in a 75vh frame, with no caller and a Bootstrap 5 constructor on a 4.1.3 page' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'openRecipeInModal'; Absent = $true; Code = $true; What = 'RD-3: and so is its opener, which nothing in the file ever called' },
    @{ File = 'pages/templates/view_recipe.html'; Text = 'request.GET.modal'; Absent = $true; Code = $true; What = 'RD-3: and the 56-line mode that existed to hide the navbar inside that frame - fifteen more !important for a frame nobody could open' },
    @{ File = 'pages/templates/meal_planner.html'; Text = "}, true);"; What = 'RD-2: the chip listens in the CAPTURE phase - the month cell opens the picker on click, and a bubble-phase handler is told only after that has already happened' },
    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'def recipe_quicklook('; What = 'RD-1: the recipe as a partial, so clicking a meal in the calendar does not cost you the calendar' },
    @{ File = 'pages/templates/recipe_quicklook_shell.html'; Text = 'data-quicklook'; What = 'RD-1: a trigger is a link that still works - the href stays pointing at view_recipe for JavaScript-off and middle-click' },
    @{ File = 'pages/help_content/administration.html'; Text = 'coming:</strong> repeating a whole week'; Absent = $true; Code = $true; What = 'MH-3: and no longer promises four things MW-1 and MO-1 have built' },
    @{ File = 'check_gates.py'; Text = 'already owns %s in'; Absent = $true; Code = $true; What = 'NF-1: and the old message is gone - it could only print when the register had an entry, which is the case this round exists for' },
    # -------------------------------------------- HL-1, 12 Oct 2026
    # A Help button is not a Back button. Base hides the back
    # label below 768px, and 77 pages once carried their own
    # unscoped copy of that rule; the day one comes back here,
    # the word Help becomes a bare question mark.
    @{ File = 'crs\templates\crs\submission_detail.html'; Text = '<span class="action-back-label"> Help</span>'; What = 'the CRS Help button writes bare text, like the other 39'; Absent = $true; Code = $true }
    # NO SENTINEL ON 'border-radius: 6px'. One was written and
    # test_sentinels refused it: the radius is present in all 27 backed-up
    # versions of that file, so a Present row on it is true in every one
    # and can never discriminate. The claim worth making - that the radius
    # survived the shorthand being removed - is a BEFORE AND AFTER
    # comparison, and test_btn_border.py section 4 makes it properly.
)

# A sentinel normally asserts a string is PRESENT.  With Absent = $true it
# asserts the opposite: that something which used to be there has gone and has
# not crept back.  The sticky sweep needs this - what it changed is the ABSENCE
# of a page-local .table-container rule, and there is no string it adds that
# could stand in for that.
#
# WITH Code = $true THE COMMENTS COME OUT FIRST.  A CHECK THAT READS TEXT
# CATCHES PROSE - this is the EIGHTH time in three weeks, and the first where
# it was this script doing the reading.  The P&L round removed a handler that
# decided whether an icon was an invoice by comparing its colour to Bootstrap
# green, and left a comment saying so, quoting the dead line:
#
#     //       var isGreen = color === 'rgb(40, 167, 69)' || ... '#28a745' ...
#
# The patcher's own self-check strips comments before it searches, so it was
# satisfied.  This script did a raw string search of the whole file, found
# "isGreen" in that comment, and reported the colour test was back.  It was
# not: it was being explained.
#
# The comment stays - it is the record of what was wrong, and deleting it to
# please a checker is how a codebase forgets.  The CHECKER learns to read code
# as code.  Opt-in rather than default, and HTML/CSS/JS only: stripping "#"
# comments from Python cannot be done with a regex without eating the "#" in
# a string literal, which is where half these colour hexes live.
function NoComments {
    param([string]$Text)
    $sl = [Text.RegularExpressions.RegexOptions]::Singleline
    $t = [regex]::Replace($Text, '<!--.*?-->', '', $sl)
    # Django's {# #} is single-line by design - its lexer regex has no DOTALL.
    $t = [regex]::Replace($t, '\{#[^\r\n]*?#\}', '')
    # CO-2, 5 Oct 2026 - `/*` IS NOT A COMMENT OPENER IN MARKUP, and
    # the line that used to stand here said it was.  accept="image/*"
    # puts one inside an attribute value, and blanking from there to
    # the next close anywhere in the file destroyed 3,268 characters
    # of passport_management.html, 1,088 of edit_asset.html and 776
    # of property_assets.html - the last of which carries a Code
    # sentinel.  This is CO-1's rule, which alv_tree.code_only has
    # had since 3 Oct, arriving in the other language: the block
    # syntax is only a comment INSIDE <style> or <script>.
    #
    # Written with [regex]::Matches, .Substring and concatenation
    # because this script already uses all three.  A MatchEvaluator
    # scriptblock would be shorter and would be the first in the
    # file, and a gate that will not start is worse than one that
    # reads a little too much.
    $out = ''
    $last = 0
    foreach ($m in [regex]::Matches($t, '(?is)<(style|script)\b[^>]*>.*?</\1>')) {
        $out = $out + $t.Substring($last, $m.Index - $last)
        $out = $out + [regex]::Replace($m.Value, '/\*.*?\*/', '', $sl)
        $last = $m.Index + $m.Length
    }
    $t = $out + $t.Substring($last)
    # Only a line that BEGINS with // - anything else eats the // in https://.
    $keep = foreach ($l in ($t -split "`n")) {
        if ($l.TrimStart().StartsWith('//')) { '' } else { $l }
    }
    return ($keep -join "`n")
}

# $BodyWas: see the collision check below the loop. Taken BEFORE the loop so
# it measures what the caller passed, not what the loop left behind.
$BodyWas = @($Body).Count

foreach ($s in $sentinels) {
    $p = Join-Path $root $s.File
    $want = -not $s.Absent
    $label = '{0}  ({1})' -f $s.File, $s.What
    if (-not (Test-Path $p)) { Bad ($label + '  - FILE MISSING'); $problems++; continue }
    if ($s.Code) {
        # NOT $body.  PowerShell variable names are case-INSENSITIVE, so $body
        # is this script's own -Body parameter - the commit message. The first
        # version of this block assigned the stripped file into it. Because
        # -Body is typed [string[]], the string was silently coerced to a
        # one-element ARRAY, so .IndexOf became Array.IndexOf and threw
        # "cannot find an overload ... argument count 2" on every Code
        # sentinel. That exception was the lucky part: had String.IndexOf's
        # 2-argument overload been reachable on an array, this would have
        # committed the contents of a template as the commit message.
        $fileText = [string](NoComments ([string](Get-Content -LiteralPath $p -Raw)))
        # IndexOf with OrdinalIgnoreCase, not .Contains: Select-String
        # -SimpleMatch is case-INSENSITIVE, and a checker that quietly became
        # case-sensitive would turn passing sentinels into failures that look
        # like real faults.
        $hit = $fileText.IndexOf($s.Text, [StringComparison]::OrdinalIgnoreCase) -ge 0
    } else {
        $hit = [bool](Select-String -LiteralPath $p -Pattern $s.Text -SimpleMatch -Quiet)
    }
    if ($hit -eq $want) { Good $label }
    else {
        if ($want) { $why = '  - not found' }
        else        { $why = '  - "' + $s.Text + '" is back' }
        if ($s.Code) { $why = $why + ' (comments stripped)' }
        Bad ($label + $why); $problems++
    }
}

# CONTROL.  Stripping comments can only ever make an Absent sentinel MORE
# likely to pass, so the flag needs its own proof that it has not simply
# switched the check off.  Two constructed cases through the same function:
# the string in a comment must vanish, the string in live code must survive.
$probeText = "// var isGreen = 1;`nvar isGreen = 2;`n<!-- isGreen -->"
$probeLeft  = NoComments $probeText
if ($probeLeft -match 'isGreen') {
    Good 'sentinel comment-stripping keeps live code (control)'
} else {
    Bad  'sentinel comment-stripping ate live code - the Code flag is unsafe'
    $problems++
}
if (([regex]::Matches($probeLeft, 'isGreen')).Count -ne 1) {
    Bad  'sentinel comment-stripping left a commented occurrence behind'
    $problems++
}

# AND THE COLLISION CONTROL. The loop above reads files into a variable; if
# that variable ever shares a name with a PARAMETER of this script - which is
# exactly what happened with $body on the 28 Aug run - the caller's commit
# message is destroyed before it is ever used. -Message is checked where it is
# used; -Body is not read until the commit is written, which is far too late
# for anything here to notice. So notice here.
if (@($Body).Count -ne $BodyWas) {
    Bad ('the sentinel loop changed -Body ({0} paragraph(s) in, {1} out)' -f $BodyWas, @($Body).Count)
    Say '        a variable in that loop is colliding with a script parameter.'
    $problems++
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
    'test_action_standard.py',
    'test_button_reach.py',
    'test_button_sweep.py',
    # The Tenants module. A gate that does not run the newest suites is
    # theatre - these are the three most recently written and therefore the
    # three most likely to be the ones that catch something.
    'test_table_tenants.py',
    'test_table_lease_agreement.py',
    'test_table_tenant_report.py',
    # The filter round. It touches base.html and eight list pages, so it is
    # the newest thing here and therefore the most likely to be what breaks.
    'test_filter_toggle.py',
    # Form controls tall enough to show their own value. Newest, so most
    # likely to be what breaks.
    'test_control_height.py',
    # Physical Invoices and Customers. Newest, so most likely to be what breaks.
    'test_table_invoices.py',
    # Lease Renewals. This one reads BOTH lease_renewal_report.html and
    # tenant_report.html and asserts they name the same pill for a declined
    # renewal - so changing one and not the other fails here rather than in
    # front of somebody triaging renewals. Newest, so most likely to break.
    'test_lease_renewal.py',
    # Open Invoices. This one is not only a styling suite: section 1 runs the
    # OLD triple loop and the NEW view function side by side over generated
    # portfolios and compares the row sequences, so a change to either that
    # alters which invoices appear fails here. Newest, so most likely to break.
    'test_open_invoices.py',
    # Icon buttons on Invoice Customers, and the disabled Paid tick. Its
    # section 4 renders `is-disabled` next to the live tick and asserts they
    # are IDENTICAL - a control for the exact fault, kept so the next person
    # can see why the class name mattered.
    'test_icon_buttons.py',
    # Cash Receipts. Section 0b refuses the push if `makemigrations` has not
    # been run - the one failure in this round that would deploy cleanly and
    # then 500 on the first query. Newest, so most likely to be what breaks.
    'test_cash_receipts.py',
    # Valuations. Section 1 runs the OLD template loop - including get_item,
    # divide_by, subtract and multiply exactly as custom_filters defines them,
    # quirks and all - beside the new view function, so a change to either
    # that alters a figure fails here. Newest, so most likely to break.
    'test_valuations.py',
    # Petty Cash. Section 2 LIFTS the old balance loop out of the backup and
    # runs it beside the new helper on the same rows, and section 5 scrapes
    # the rendered HTML and adds the amounts up to check they equal the
    # figure drawn above them. A change to either that moves a number fails
    # here. Newest, so most likely to break.
    'test_petty_cash.py',
    # Actual Expenses. Section 4 LIFTS the report modal's row builders out of
    # the page and RUNS them - those two tables have no markup, so nothing
    # else can see them. Section 5 reads the parse tree and fails if the
    # report's FILTER moved, because this round changed the words and must not
    # have changed a figure. Newest, so most likely to break.
    'test_act_expenses.py',
    # The sticky sweep. Its only real check is a MEASUREMENT: each page's own
    # table markup is rendered against base plus the page's stylesheet,
    # scrolled, and the heading's position read back. overflow:hidden and
    # overflow:clip look identical and behave oppositely - nothing static can
    # tell them apart. Newest, so most likely to break.
    'test_sticky_sweep.py',
    # require_POST. Section 3 composes the decorators exactly as the source
    # does and DRIVES all three cases through a RequestFactory - the ordering
    # is the part we chose and could have got wrong. Section 4 scans every
    # template for a surviving link to any of the fifteen. Newest, so most
    # likely to break.
    'test_require_post.py',
    # The Manage Expense modal. Its controls are markup inside JavaScript
    # string literals, so the statics read the SCRIPT text and section 2
    # lifts the document panel out of its template literal and draws it.
    # Newest, so most likely to break.
    'test_manage_modal.py',
    # The P&L invoice icons. The fault was "the click does nothing", so the
    # check is a CLICK: the page's own functions, the real icon markup, and
    # the viewer read back afterwards. Newest, so most likely to break.
    'test_pl_invoice.py',
    # The pro-rata anchor deadlock. Section 2 renders the real template
    # through Django with an inactive anchor and reads the `disabled`
    # attribute the browser actually receives; section 3 loads the page's own
    # script with REAL jQuery and CLICKS, because the fault was a refused
    # click. Section 4 checks the half that did NOT change - the commit still
    # closes an un-ticked anchor like any other row. Newest, so most likely
    # to be what breaks.
    'test_prorata_anchor.py',
    # The valuation preview's inactive warning. Section 1 runs the OLD view
    # and the NEW one over the SAME database and compares every figure the
    # old payload carried - that round adds keys and must not move a number.
    'test_valuation_inactive.py',
    # A share of zero. This one DOES move figures, so the suite separates the
    # two halves: the pre-ticks provably cannot move a number, and the
    # valuation preview's are diffed old-against-new and asserted line by
    # line - who leaves the denominator, that every remaining share rises,
    # and that the pot is unchanged. Newest, so most likely to break.
    'test_share_of_zero.py',
    # The year-on-year matrix. Section 4 SCROLLS the table in Chromium and
    # reads the frozen column's position back - position:sticky inside
    # overflow-x:auto is the most confident-looking thing in CSS that
    # silently does nothing, and it is the same family of fault as the
    # sticky headings. Newest, so most likely to be what breaks.
    'test_expense_matrix.py',
    # Spent rows. This one relaxes a guard on a DESTRUCTIVE path, so its
    # section 3 deletes a spent row from a real database and re-resolves
    # every year to prove nothing moved - then does the same to a row that
    # DOES have a past and shows the figure collapse, which is why the guard
    # still refuses that one. Newest, so most likely to be what breaks.
    'test_spent_row.py',

    # ------------------------------------------------------------------
    # WIRED ON 9 Sep 2026. Every suite below already existed and NONE of
    # them was on this list - they passed only because somebody ran them
    # by hand, which is not the same as being enforced. Two had been
    # failing for a day and a half without anything saying so.
    #
    # Four read a .bak_* snapshot, and those are gitignored: on a fresh
    # clone they fail or, worse, quietly shrink. See apply_gate_wire.py.
    # ------------------------------------------------------------------
    # The comment tint on the Issues screens.
    'test_comment_tint.py',
    # Tenant payment behaviour: the cutoff, and the ageing scale.
    'test_payment_days.py',
    # Issues Analysis colours - AND that no CSS comment in base spells a
    # script or style tag, which is how two pieces of prose broke it.
    'test_ia_palette.py',
    # The Issues Analysis tiles, and the drill-down they open.
    'test_ia_tiles.py',
    # What reaches paper. Needs .bak_leak; see the note in apply_gate_wire.
    'test_print_leaks.py',
    # The notification buttons. SILENTLY DROPS three checks when
    # .bak_notify is missing - 32 becomes 29 and it still says zero
    # failed. On the list to fix.
    'test_notify_btns.py',
    # A secondary button hides only where a More menu carries it.
    'test_secondary_visible.py',
    # One spelling for the required marker, in a colour base owns.
    'test_required_marker.py',
    # The standards block: it describes a base that exists, ships nothing,
    # and contains no prose shaped like a tag or a comment.
    'test_standards_block.py',
    # Every page heads itself the way base says.
    'test_heading_standard.py',
    # The brand is in the browser tab, not on the heading.
    'test_heading_prefix.py',
    # Shape B: the module on the h2, MODE LABEL and record name on the h4.
    'test_projects_heading.py',
    # Every required field says so. Newest, so most likely to be what
    # breaks.
    'test_required_sweep.py',
    # Nothing here dies because the console cannot draw a character it read
    # out of a template. Its section 1 RUNS the preamble under a forced
    # cp1252 stdout, and runs the same print without it to show the check
    # can fail. Newest, so most likely to be what breaks.
    'test_console_encoding.py',
    # The map asks a provider whose terms cover a business doing it, from one
    # definition, and says so when it has no key. Its section 2 RENDERS each
    # page's map block through Django in BOTH key states, because escapejs
    # rewrites four of the characters in the tile URL and nothing that reads
    # the template source can see what reached the browser. Newest, so most
    # likely to be what breaks.
    'test_map_provider.py',

    # ------------------------------------------------------------------
    # WIRED ON 16 Sep 2026, by a patcher that RAN each of them first.
    # A suite that cannot pass today cannot honestly be wired on today:
    # listing a red one does not enforce a standard, it stops every push
    # until somebody deletes the line.
    # ------------------------------------------------------------------
    # The ageing bands, on the cells and on the legend that explains them.
    'test_ageing_scale.py',
    # base's stat tile, and the rule that a verdict colours the FIGURE and
    # not the box behind it.
    'test_alv_stat.py',
    # The Friday status report colours. Its control renders the OLD file and
    # requires the old answer, so a green result cannot be vacuous.
    'test_fsr_palette.py',
    # The grade scale, and the detail tables that read it.
    'test_grade_tables.py',
    # The Issues Analysis drill-down: a modal inside a modal, measured.
    'test_ia_drill.py',
    # The indicator modal.
    'test_ind_modal.py',
    # Invoice verification. Pure value tests - what 95.2 against 95.20 does.
    'test_invoice_verification.py',
    # The Issues table, narrow and wide, against the markup it replaced.
    'test_issues_table.py',
    # The year-on-year matrix range. Every year in it is INJECTED as
    # today_year, so the suite owns the clock and cannot age.
    'test_matrix_range.py',
    # The outstanding-invoices migration.
    'test_oi_migration.py',
    # The P&L drill-down.
    'test_pl_drill.py',
    # What the print stylesheet does, as opposed to what it says.
    'test_print_media.py',
    # The resolved-issues report.
    'test_resolved_report.py',

    # base owns the three classes the standard is written in.
    # Its section 3 RENDERS both heading shapes and measures the
    # gap, because :has() is the kind of rule that silently does
    # nothing. Newest, so most likely to be what breaks.
    'test_heading_components.py',
    # The field label is bold, and the bold is in the markup. Its
    # section 4 RENDERS a field against base's real CSS and reads the
    # computed weight back, because a single strong{font-weight:normal}
    # anywhere would un-bold the system and leave the markup perfect.
    # Newest, so most likely to be what breaks.
    'test_label_bold.py',
    # The entry-screen components. Its section 4 RENDERS each page
    # that lost a rule with the rule and without it and compares the
    # computed style of a real control, because the whole claim of
    # the deletions is that they change nothing. Newest, so most
    # likely to be what breaks.
    'test_form_components.py',
    # Every Add and Edit screen has the house panel. Its section 3
    # checks each panel OPENS AND CLOSES AT THE SAME DJANGO BLOCK
    # DEPTH, because a panel opened inside an {% if %} and closed
    # outside it comes apart for one kind of user and not another,
    # and nothing reading the markup flat can see that. Newest, so
    # most likely to be what breaks.
    'test_entry_panel.py',
    # One action bar. Its section 2 RENDERS a bar at three widths
    # with one, two and five buttons and compares it against the
    # retired variant's rules re-applied, because the whole case for
    # removing that class is that it changed nothing. Newest, so most
    # likely to be what breaks.
    'test_one_action_bar.py',
    # The compound rules that outranked base. Its section 3 RENDERS
    # each migrated page's own stylesheet under base and reads the
    # control back, because unlike the earlier component rounds these
    # deletions DO change how a page looks. Newest, so most likely to
    # be what breaks.
    'test_compound_rules.py',
    # Save above the fields, one way out of a form. Its section 3
    # RENDERS the single-button bar variant with and without a
    # primary in it, because it has the SAME declaration as the
    # variant retired the day before and the opposite effect.
    # Newest, so most likely to be what breaks.
    'test_save_and_cancel.py',
    # The last entry screens take the house heading, with the module
    # name DERIVED from the screen Back returns to rather than typed.
    # Its section 2 follows every Back link and re-derives it, so a
    # module renamed later shows up as a heading that no longer
    # matches. Newest, so most likely to be what breaks.
    'test_entry_headings.py',
    # Administration and Personal, stage A. Its section 1 requires
    # every one of those templates to have ZERO tag mismatches, which
    # three of them did not before this round - a </div> closing
    # before the </form> it sits inside. Newest, so most likely to be
    # what breaks.
    'test_admin_repair.py',
    # Administration and Personal, stage B: the module heading. Its
    # section 2 re-derives every module name from the screen Back
    # returns to, so renaming a module reports its sub-screens the
    # same day. Newest, so most likely to be what breaks.
    'test_admin_headings.py',
    # The purple banner comes off Administration. Its section 2 is a
    # POSITION check - the module heading must not be inside any
    # container - because stage B checked the class and passed a
    # correct class sitting in a flex row that piled the mode line
    # on top of it. Newest, so most likely to be what breaks.
    'test_admin_banner.py',
    # .disabled-btn marks what is off PERMANENTLY. A <button> whose
    # disabled attribute JavaScript clears must NOT carry it, or the
    # class outlives the attribute and the button goes live while
    # staying grey. This guards a rule in Show-ButtonDrift.py, which
    # apply_button_sweep.py imports - a SHARED tool, so it needs a
    # guard of its own rather than riding on the sweep's suite.
    'test_disabled_state.py',
    # A fixture belongs to ONE process. Four suites used to build
    # _sup_probe.html in this directory; on this list two of them run back
    # to back, and the second was answered with net::ERR_FAILED. Every
    # fixture now lives in a mkdtemp directory, and this is what says so.
    'test_probe_location.py',
    # One panel title: h3.form-section-title, sized BY BASE. The
    # tag used to decide how big it was, and the system had five
    # answers - two of them at or below the size of the field
    # labels underneath. Its section 4 measures that, because a
    # size is not something a string search can check.
    'test_panel_title.py',
    # One section component, in place of the seven ways this system used
    # to say "this is a section". Its section 5 exists because one of those
    # headings is a CONTROL - it opens a notification card - and its
    # section 7 renders at 375, 390 and 768 with Bootstrap and base inlined,
    # against a 1280 control, because a rendering test without the page's
    # stylesheet measures nothing. Newest, so most likely to be what breaks.
    'test_entry_sections.py',
    # A parent task is kept in line with its own subtasks, the way a
    # project already is with its tasks. Its section 2 RUNS against the
    # real database inside a transaction it rolls back, and section 3
    # disconnects the receiver and requires the same sequence to fail -
    # a guard whose control cannot fail is not a guard. Newest, so most
    # likely to be what breaks.
    'test_project_rollup.py',
    # Four labels that did not fit their own column, and the rule
    # that let them. Its rendered section measures a col-md-3 at 168px -
    # the narrowest this application ever draws one, a 992-wide window
    # with the sidebar open - and its CONTROL renders the OLD label at
    # the same width and requires it to WRAP. A guard whose control
    # cannot fail is not a guard. Newest, so most likely to be what
    # breaks.
    'test_label_fit.py',
    # The last two hand-rolled tables joined the standard. Its
    # section 2 asserts the DATA the rebuilt blocks read is the data the
    # old ones read - the markup around it was replaced wholesale, so a
    # diff says nothing and the expressions are the only invariant there
    # is. Newest, so most likely to be what breaks.
    'test_table_admin.py',
    # The page-local iOS zoom guards base made redundant. Its rendered
    # section is the definition of redundant: every page touched, at 375
    # and 1280, before and after, and NO control's computed font-size or
    # padding may change. fsr.html is its control - a guard that is NOT
    # redundant, which the same render must show changing. Newest, so
    # most likely to be what breaks.
    'test_zoom_guards.py',
    # Every text control 16px on a phone. Its rendered section is the
    # invariant itself - every page that extends base, at 375, and NO
    # text control under 16px - plus the other half: at 1280, every
    # control's size identical to before the round. Its control takes the
    # new rule back out of base and must find the small ones again.
    # Newest, so most likely to be what breaks.
    'test_small_controls.py',
    # Every phone query says screen, so no phone layout reaches paper -
    # the P&L printed without its table, three pages printed a
    # rotate-your-phone prompt instead of their content. Its
    # probes put a marker in every block this round guarded and require
    # it to fire on screen and NOT on paper, then read the same block from
    # the backup, where it must fire on BOTH. Newest, so most likely to be
    # what breaks.
    'test_print_queries.py',
    # Buttons stay on the screen. Printed at A4 width, every page that
    # extends base must show no button but a .print-keep one - and ONLY
    # buttons may have left the page. Its control strips print-keep from
    # home's dashboard rows and must see the cards print empty. Newest,
    # so most likely to be what breaks.
    'test_print_buttons.py',
    # Every <div> pairs, on every branch of every if. Its rendered
    # section runs three templates through Django's own engine on the
    # branch that was broken and asks the browser where the page's last
    # element landed - inside the content wrapper now, outside it (or
    # swallowed by a card) from the backups. Newest, so most likely to be
    # what breaks.
    'test_div_balance.py',
    # A financial row's history goes with it, on every route. Its
    # database section builds the real schema in an in-memory SQLite,
    # deletes rows by a view-style delete, a queryset delete and a
    # property cascade, and requires their snapshots gone and a
    # neighbour's untouched. Its control disconnects the receiver and
    # must see the orphans come back. Newest, so most likely to be what
    # breaks.
    'test_history_purge.py',
    # One pop-up header, owned by base. Every business modal is opened
    # in the browser and must read the teal banner - or red, exactly when
    # its title says Delete - white title, white close, one size. Its
    # control puts the class on a header painted by bg-info, a page rule
    # and an inline style at once, and base must win over all three.
    # Newest, so most likely to be what breaks.
    'test_modal_heads.py',
    # The Issue page's two edit pop-ups are Bootstrap modals with base's
    # header and base's fields. Its render runs the real jQuery and
    # Bootstrap from two fixture files, opens both, fills the comment, and
    # closes them on Escape, the backdrop and Cancel.
    # Newest, so most likely to be what breaks.
    'test_ei_modal.py',
    # One report title, owned by base. Nine report screens render the
    # same title and subtitle at 1280, 375 and on paper, the brand shows
    # on paper only, and the dead title-deed pair stays gone - no view,
    # URL or access rule points at it.
    # Newest, so most likely to be what breaks.
    'test_report_head.py',
    # The Applies-from panel on five Financials entry screens and the two
    # delete pop-ups' choice cards are base's. Only style attributes moved;
    # rendered, all five panels and both card pairs read the same, from
    # base's tokens. Valuations names the date Applies from too.
    # Newest, so most likely to be what breaks.
    'test_applies_from.py',
    # The coloured page banners went (7 Sep); judged on the pages as that round left them.
    'test_banner_pages.py',
    # The Comments Report onto the table standard (2 Sep), as that round left it.
    'test_comments_report.py',
    # Financials headings off their bands (8 Sep), as that round left them.
    'test_finance_headings.py',
    # FI's segmented control on base's .alv-seg (5 Sep), as that round left base and the page.
    'test_fi_seg.py',
    # Map tiles off CARTO onto OSM (7 Sep), as that round left the map pages.
    'test_map_tiles.py',
    # The five above judge their own rounds again, and the Comments Report wears base's report title. Newest, so most likely to be what breaks.
    'test_old_rounds.py',
    # base.html's standards block records the decisions of 16-22 Sep,
    # and still costs the visitor nothing. Newest, so most likely to be
    # what breaks.
    'test_standards_doc.py',
    # Section C round C1: Customer Name required, Resolved authors as
    # chips, Quick Actions dropped, the occupancy label, settings tidied,
    'test_c_small.py',
    # Section C round C2: 44px to tap on a phone - the bar, the floor in
    # base, the pages' own copies gone,
    'test_tap_target.py',
    # Section C round C3: one filter chip in base, its x 44px to tap on a
    # phone, one Active filters label,
    'test_filter_chip.py',
    # Section C round C4: the Expenses vs Rent analysis takes base's
    # meaning tokens - the quadrants, the labels, the table and the key,
    'test_quadrant_tokens.py',
    # Section C round C5: the lease generator's thirteen coloured card
    # headers are house sections - three panels and ten titles,
    'test_lease_sections.py',
    # Section D round D1: four dead templates gone, and the orphan scan
    # reads a script - a class a script builds is worn,
    'test_dead_files.py',
    # Section D round D2: the Help label, the country filter read from
    # the data, and Select All as a secondary,
    'test_small_three.py',
    # Section D round D3: base owns the labelled row action, the last
    # four script-built buttons are decided, and three stale LEAVE
    # reasons are gone,
    'test_row_actions.py',
    # Section D round D4: base owns the filter field - one height, one
    # chevron and one focus ring on the ten pages that each had their own,
    'test_filter_field.py',
    # Section D round D5: base owns the series scale, a property keeps its
    # colour when the chart is filtered, and 59 status literals take tokens,
    'test_series_scale.py',
    # Section D round D6: the last six pop-up headers on the property
    # side, and base owns the overlay the drill-down two are built in,
    'test_modal_overlay.py',
    # Section D round D7: base hides the Back word wherever the button
    # sits, and 77 pages stop each writing the rule unscoped,
    'test_back_label.py',
    # Section D round D8: a time horizon is not a status - the three
    # cashflow summary cards take one accent header, two of which had been
    # failing contrast - and the zoom-guard note is measured, not guessed,
    'test_horizon_cards.py',
    # Section D round D9: base owns the avatar - five copies of one disc,
    # four of them failing contrast with their own initials,
    'test_avatar.py',
    # Section D round D10: fifteen rules put white text on a colour too
    # light to carry it - five of them failed even for large text,
    'test_contrast.py',
    # Section E round E1: the Personal side's 33 pop-up headers join
    # .alv-modal-head - fifteen of them were failing their own white text,
    'test_personal_heads.py'
    'test_purple.py'
    'test_action_bar.py'
    'test_named_bars.py'
    'test_palette.py'
    'test_line_soft.py'
    'test_accent_ink.py'
    'test_surface_deep.py'
    'test_page_title.py'
    'test_bar_top.py'
    'test_req_marker.py'
    'test_personal_teal.py'
    'test_celebrations.py'
    'test_body_backs.py'
    'test_bar_mobile.py'
    'test_table_personal.py'
    'test_row_personal.py'
    'test_table_preview.py'
    'test_table_breakdown.py'
    'test_house_header.py'
    'test_hub_bar.py'
    'test_good_warn.py'
    'test_more_menu.py'
    'test_subtree_tones.py'
    'test_more_css.py'
    'test_last_menus.py'
    'test_walk_passport.py'
    'test_walk_help.py'
    'test_filter_gap.py'
    'test_tree_roots.py'
    'test_crs_country_list.py'
    'test_crs_country_form.py'
    'test_crs_fi_list.py'
    'test_crs_fi_form.py'
    'test_crs_hub.py'
    'test_crs_submission_list.py'
    'test_crs_submission_start.py'
    'test_crs_detail_colour.py'
    'test_crs_detail_structure.py'
    'test_crs_detail_rest.py'
    'test_waiting_down.py'
    'test_crs_comment_fix.py'
    'test_celebration_filters.py'
    'test_future_tab_off.py'
    'test_celebration_az.py'
    'test_filter_box.py'
    'test_zoom_markup.py'
    'test_tab_right_edge.py'
    'test_event_tones.py'
    'test_message_bar.py'
    'test_control_accent.py'
    'test_countdown_tone.py'
    'test_recipe_filter.py'
    'test_recipe_chips.py'
    'test_crs_pill.py'
    'test_filter_on_close.py'
    'test_house_title.py'
    'test_subtitle_h5.py'
    'test_filter_frame.py'
    'test_retone.py'
    'test_report_back.py'
    'test_row_form.py'
    'test_stats_fold.py'
    'test_lease_filter.py'
    'test_none_columns.py'
    'test_report_arrow.py'
    'test_field_add.py'
    'test_projects_table.py'
    'test_dash_back.py'
    'test_live_search.py'
    'test_bar_stretch.py'
    'test_secondary_scope.py'
    'test_task_table.py'
    'test_search_hint.py'
    'test_analysis_order.py'
    'test_detail_pills.py'
    'test_projects_pills.py'
    'test_stats_3up.py'
    # Login and set-password-by-email. Its section 4 runs REAL
    # tokens and a REAL SetPasswordForm against a sqlite database it
    # builds itself, because the project's settings point at MySQL
    # and no suite can reach it - so this is the one flow that is
    # proved by running rather than by reading. Newest, so most
    # likely to be what breaks.
    'test_auth_flow.py'
    # A filter travels by GET. Its section 3 drives all five pages
    # through the real views against a database it builds itself,
    # and its control sends the OLD POST and requires the filter to
    # be IGNORED - which is the only way to show the move happened
    # rather than that both are being read. Newest, so most likely
    # to be what breaks.
    'test_filter_get.py'
    # Every configurable notification type has a control on the
    # settings screen. It RENDERS the page rather than reading the
    # four lists that have to agree, because A1 added a type to
    # three of them, wrote a suite that checked those same three,
    # and shipped a type nobody could configure. Newest, so most
    # likely to be what breaks.
    'test_notify_types.py'
    # The login box takes an email as well as a username. Its
    # section 3 drives real sign-ins against a database it builds
    # itself, and its control shows Django's own backend refusing
    # the address - so the resolution step is provably what makes
    # it work. Newest, so most likely to be what breaks.
    'test_login_email.py'
    # The two screens that could not be narrowed, now narrowed.
    # Its section 4 drives both through the real views against a
    # database it builds itself, and section 5 opens Receipts in a
    # browser and types into the live box to watch TOTAL ISSUED
    # follow it. Newest, so most likely to be what breaks.
    'test_filters_in_rc.py'
    # EVERY ANTHROPIC CALL SITE IN THE TREE, AGAINST ONE LIST.
    # Four files each hard-coded their own model id and one of
    # them sat on a model retired on 15 June 2026, so the AI
    # Import tool answered 'try a different file' for three and
    # a half months. No suite could see it: a model id is text.
    # This one reads the source and says so.
    'test_ai_models.py'
    # Five filters on one line, and the drill-down. Its section
    # 3 opens Chromium at six widths and reads back where every
    # control landed, because the defect AE-1 fixes - a date
    # input 15px narrower than a date - is invisible to a grep
    # and was invisible on screen for as long as it existed.
    'test_ae_line.py'
    # One option per choice. Its section 3 renders all five
    # dropdowns through the real views against a database it
    # builds itself, seeded with the duplicates from Demetri's
    # screenshot, and counts the options. A dropdown that lists
    # one thing twice cannot be seen by reading a template.
    'test_filter_distinct.py'
    # The tab standard. base had NO tab rule at all, and the one
    # that renders 205 of the app's 213 tabs wrote its colour
    # inline on {% if forloop.first %} - so every help modal
    # highlighted whichever tab rendered first, not the one you
    # opened. Its section 4 clicks a tab and reads the colour back.
    'test_tabs.py'
    # The invoice icon on the P&L Actual Expense drill-down. It
    # was on screen and could not fire: the icon called a
    # function from a script the modal never injects, and the
    # handler written for it returned early on every row. Its
    # section 4 clicks the icon in BOTH places and reads back
    # which document opened.
    'test_pl_invoice_icon.py'
    # A name with an apostrophe in it. 145 values across 19
    # templates were pasted into JavaScript string literals in
    # inline handlers, so a tenant called O'Brien made the View
    # Lease Agreement button a syntax error - it did nothing, in
    # silence. Its section 2 renders through Django and clicks in
    # Chromium; its section 1 is the gate that catches the next one.
    'test_js_escape.py'
    # The issue figures, moved above the table they summarise and
    # put on base's stat tile. Its section 3 renders the real
    # markup in Chromium and reads back that the figures sit ABOVE
    # the table - an ordering claim that a grep cannot make.
    'test_issue_stats.py'
    # The ORDER of the action bar - primary, secondaries, filter,
    # Back - asserted for the first time, across all 123 bars and all
    # 142 variants their {% if %} branches can render. Its section 4
    # draws the three moved bars in Chromium and reads the controls
    # back BY THEIR x POSITION, because base lays the bar out with
    # flex and flex has four ways to disagree with the markup.
    'test_bar_order.py'
    # The compact contact card - one line a name, no icon and no
    # pill until the card is opened. Its section 2 draws the cards at
    # three column counts and reads the name's TRUE text width with a
    # Range, because a clipped flex item lies about its own width. Its
    # section 3 is the one no suite had: CSS comments must balance,
    # tree-wide - two rules on that page had been discarded by the
    # parser since 25 Sep while the braces balanced perfectly.
    'test_compact_card.py'
    # The handlers JAVASCRIPT writes - the ones J-1's Django filter
    # could never reach. Its section 2 puts four recipe names through
    # the real markup in Chromium and records whether the handler RAN,
    # because whether an onclick is a syntax error is a fact about a
    # JavaScript parser and nothing else can answer it.
    'test_js_handlers.py'
    # Bootstrap colour worn on top of a house role. Its section 2
    # RENDERS each pair, because "(0,2,0) beats (0,1,0)" is a claim
    # about what a browser does - twelve of the thirteen classes were
    # changing nothing, and the thirteenth was the Favourites toggle,
    # whose ON and OFF states were pixel-identical.
    'test_btn_tone.py'
    # THE SENTINEL TABLE ITSELF. 210 rows run before any suite
    # starts, and until S-1 nothing tested them. It checks that the
    # reader sees every row (an earlier one saw 183 of 195 and
    # reported a clean census), that every row resolves, and - the
    # claim no round had made - that every row could ever have FAILED.
    'test_sentinels.py'
    # The Meal Plans row, onto base's row-action strip. Its section
    # 2 draws the five controls against a PLAIN base page and against
    # the page's own CSS, and demands they come out identical - a page
    # that merely looks similar is a page that copied the component
    # again. 54 local rules fell to 43 and 24 literals to 13.
    'test_meal_row.py'
    # ONE DEFINITION OF AN EXPIRING LEASE. The panel asked "ending
    # within 90 days with no successor" and the button asked "past
    # the tenant's own renewal lead time and still pending" - two
    # rules, one name, 3 and 2 on one screen. The button calls the
    # panel's function now; this suite asserts it CALLS rather than
    # COPIES, and that nothing calls the old rule it kept.
    'test_lease_rule.py'
    # Current tenants by default, past ones on ask. Its section 2 is
    # the one that matters: a status chosen in the filter panel must
    # be tested BEFORE the default, or picking Inactive returns an
    # empty page while showing Inactive as selected.
    'test_tenant_past.py'
    # The ingredient filter folds away. Its section 2 is the one that
    # matters: a live search may only promise what the server delivers,
    # so the suite re-asks the VIEW - name__icontains and nothing else,
    # no Paginator - rather than trusting the markup that names them.
    'test_ingredient_filter.py'
    # A scope is not a verdict. The Applies To column was amber for
    # one answer and green for the other, and neither is a judgement.
    # Its section 3 proves a CSS rule never fired, from the siblings
    # and then again in a browser.
    'test_conversion_pills.py'
    # The list popup was absolute inside an overflow: clip container,
    # so it was cut at the container's edge. Its section 3 clicks the
    # trigger in a real browser and measures what was painted.
    'test_fixed_popup.py'
    # The Shopping List: SL-1 the print guard, SL-2 the bar, SL-3 the
    # colours. ONE suite for three rounds because they are one programme
    # on one page - three suites would each read the whole of it. Its
    # section 1 is the functional bug, and it checks the three guards
    # SEPARATELY, because a keyboard Ctrl+P reaches none of the other two.
    'test_shopping_list.py'
    # The green Add Recipe and the red trashcans. Its section 2 is why it
    # was a round: four of the ten uses were inside JavaScript template
    # strings, so the day cards the page builds AFTER load would have kept
    # the old paint.
    'test_meal_plan_buttons.py'
    # Update at the top of Create/Edit Recipe. Its section 2 drives a real
    # browser, because a submit button outside its form fails SILENTLY -
    # the page looks right and pressing it does nothing.
    'test_recipe_bar_top.py'
    # The List/Calendar switch. Its section 5 measures the CONTRAST of
    # each half in a browser, and section 6 is the control: the old
    # Calendar toggle painted its inactive half white on a white page,
    # which is why Demetri could not get back to the list. Every class
    # name on that control was correct; only a renderer could see it.
    'test_view_seg.py'
    # Five filled buttons in five colours on the Calendar week header,
    # and a blue View plus a red x on every recipe card, onto the same
    # icon strip the list rows already wore. Its section 5 is the one
    # that matters: eleven controls were rewritten by hand, and every
    # handler and url has to still be the one it was.
    'test_calendar_actions.py'
    # The rest of the Meal Plan colours. Its section 3 RENDERS the
    # no-permission Create button, because that finding cannot be
    # checked by eye - the bug was that it looked right.
    'test_calendar_tone.py'
    # The Shopping List email box, which now opens when you ask for it
    # and reads its addresses from Household Members instead of four
    # people typed into the template.
    'test_email_reveal.py'
    # base's .filter-grid declared display:grid and no columns, so a
    # page that set none got ONE column. Its section 3 renders all 13
    # pages that use it under the old base CSS and the new, and fails
    # if any page setting its own columns moves by a pixel.
    'test_filter_grid.py'
    # Categories and Measurement Units join the house filter. Its
    # section 6 drives a browser because the claim is a RACE: base's
    # live search owns row.style.display outright, so a second filter
    # setting it would evaporate on the next keystroke.
    'test_ref_filters.py'
    # The Conversions filter into the house panel, and the seventh
    # hand-rolled segmented control converted. Its section 2 holds the
    # narrowing itself unchanged - the premise of the round is that
    # the logic was already right.
    'test_conversion_filter.py'
    # The last two hand-rolled segments. Its section 5 is the one that
    # matters beyond this round: accept="image/*" puts a /* inside an
    # attribute, and a code_only that reads it as a comment opener is
    # blind to 1,385 characters of real markup.
    'test_pl_seg.py'
    # code_only gets one home. Its section 2 does not compare the new
    # helper against a copy of the old one typed out in the suite - it
    # lifts the old definitions OUT OF THIS ROUND'S OWN BACKUPS, execs
    # them, and runs both over every template, so "4,892 characters were
    # hidden" is measured against the code that hid them.
    'test_code_only.py'
    # The Calendar hung because its Add Recipe modal rendered every recipe
    # photograph in the database. Its section 3 drives a browser against a
    # server that COUNTS requests: hidden and lazy is zero, hidden and
    # eager is four. display:none does not stop a fetch.
    'test_lazy_images.py'
    # Seventy lines of script written after the endblock, which Django
    # discards without a word. Its section 1 asks every child template in
    # the tree the same question, every run.
    'test_stranded.py'
    # A job that is done is a tick, not a sentence - on a phone.
    'test_done_badge.py'
    # The meal plan form's bar to the top, and Cancel becomes Back.
    'test_meal_bar_top.py'
    # Back goes where you came from, and the week travels with it.
    'test_from_calendar.py'
    # overflow:clip clips an absolutely-positioned descendant exactly as
    # hidden does. Its section 2 measures the dropdown in a browser: 13 of
    # 159 pixels inside the container before, 159 of 159 after.
    'test_escaping_drop.py'
    # Passports: four typed-in lists become four derived ones, and the
    # bespoke filter panel becomes the house one. Its section 4 drives a
    # browser - four filters narrowing TOGETHER, the chips following, an
    # empty state when nothing matches, and Clear All putting it back.
    'test_passport_filter.py'
    # The Passports row: badges to pills, labels from the model. Its
    # section 2 renders the backup's badges and the new pills side by
    # side and finds that three of the ten old ones drew no background at
    # all. Its section 3 refuses a pill tone assembled across a template
    # tag, and proves the check can fail by building one.
    'test_passport_pills.py'
    # The Holder filter matched nothing. Its section 2 is the gate that
    # would have caught it: for every filter on the page it reads the
    # field the narrowed cell renders and the field the options are
    # derived from, and fails unless they are the same field. Section 3
    # shows that gate failing on the code that shipped the bug.
    'test_passport_holders.py'
    # The Task List tree on a phone. Its section 2 renders the cards at
    # 390px before and after: 12/12/12 and three identical greys before,
    # 12/26/40 with three category inks after. Its section 3 renders the
    # DESKTOP and fails if anything but the bar colour moved.
    'test_task_depth.py'
    # The Greek Task List answered Server Error (500). Its section 1 does
    # not look for the function that broke: it binds EVERY call made by
    # bare name under pages/ against the signature it reaches, so the next
    # signature to drift away from its callers fails the sweep instead of
    # the deploy. Section 2 lifts the shipped definition out of the backup
    # and calls it with the argument count read from the backup's own call
    # sites, and requires the TypeError - the 500 reproduced, not described.
    'test_greek_arity.py'
    # Edit a task from the Task List and Back landed you on the Project.
    # Its section 1 LIFTS the three origin helpers out of the view by
    # parse and RUNS them against seven requests, two of them forged, so
    # it judges the answer and not the spelling. Section 2 runs the same
    # seven against the backup and requires the Task List case to come
    # back pointing at the Project.
    'test_task_origin.py'
    # The radio and the checkbox Bootstrap had been drawing in #007bff
    # since the stylesheet was linked. Its section 2 renders the real
    # markup under the real bootstrap 4.1.3, before and after, and reads
    # the computed colour of the ::before that draws the dot - which is
    # how it found that Bootstrap writes the checked colour three times
    # at two specificities, and that the first build of the round had
    # recoloured the radios and left every checkbox blue.
    'test_custom_control.py'
    # The filter fields that were not in line. Its section 1 renders
    # EVERY filter panel in the tree at 1280, under base as the backup
    # left it and under base as it is now, and reports the top of every
    # label and every control: ten panels crooked before, none after,
    # every control at y=27. Section 2 holds the fact that makes
    # aligning labels sufficient - that every label is one line.
    'test_filter_align.py'
    # The action column's order. Its section 1 judges EVERY .row-actions
    # wrapper in the tree, not the five the round changed. Its section 2
    # asks of every icon class whether it carries one picture - which is
    # what caught the first build of the round repairing .icon-view's
    # four glyphs by creating two classes with two each. Section 3
    # renders the Tenants row before and after and reads the order off
    # the screen.
    'test_row_action_order.py'
    # The ageing scale, toned into the theme. Its sections 1-3 RENDER the
    # five steps and compute contrast off the painted pixels: the tints
    # must darken monotonically with no reversal, every step must be a
    # neutral, and the pill must clear AA - which is the gate that caught
    # the round's own near-miss, where carrying var(--age) over as the
    # pill's text colour would have shipped 2.87 on step 0.
    'test_age_tone.py'
    # property_detail's palette. Its section 1 PAINTS every table on the
    # page and reads the computed background off each header, rather than
    # asking which rules the file contains - which is the only reason the
    # two headers that colour the ROW instead of the cell were found. Its
    # section 2 holds the distinction the round rests on: red appears on
    # the things that are verdicts and nowhere else.
    'test_pd_palette.py'
    # property_detail's seven tables. Its section 1 MEASURES every table
    # before and after and requires the widths unchanged - which is the
    # only reason the first build of the round was caught dropping
    # Bootstrap's .table along with the striping and shrinking every
    # table to fit its content. Section 3 holds the one named exception,
    # and fails if either half of it goes missing.
    'test_pd_tables.py'
    # base's stylesheet moving into the head. Its section 5 is the gate
    # that keeps it fixed: no page may redeclare a property of the block
    # that moved with a different value, or a pasted hex literal silently
    # un-tokenises a component again. Section 5b counts the older drift
    # against base's three head stylesheets and reports it WITHOUT
    # failing, because CS-1 neither caused it nor fixed it.
    'test_css_order.py'
    # the Greek stat label. Renders at seven widths, because the defect
    # lived only where base's 3-up phone rule does not apply and a
    # phone-only check would have passed in both directions.
    'test_stat_label.py'
    # the overdue date and its warning. Measures HEIGHT, not the number
    # of client rects - a Range returns one rect per text fragment, so
    # the obvious count reads 2 whether or not the span wrapped.
    'test_overdue_date.py'
    # the translation endpoint. Section 3 RUNS the service with the
    # import broken and requires (False, None, reason) - the old code
    # returned the English here, which is how a failure reached the user
    # as a green tick. Section 5 states what it could NOT test: a
    # successful translation, which has no route out of the sandbox.
    'test_translate_honest.py'
    # the recipe capture page's buttons. Section 3 is the one that earns
    # its keep: it requires that no selector in the file still hunts for
    # a class the round removed. The first build changed a button's class
    # and left the querySelector that finds it, which would have thrown
    # on the success path after the document was already deleted.
    'test_recipe_buttons.py'
    # the dead .btn-info declarations. Its section 3 PAINTS all 22 pages
    # before and after and requires getComputedStyle to return the same
    # string - a census that resolves two spellings to one colour is an
    # argument about CSS, not evidence about what a browser draws. Its
    # section 5 plants #b00020 and requires that to be caught, because a
    # harness that cannot tell colours apart proves nothing.
    'test_btn_info.py'
    # translation on the house API. Its section 3 RUNS every failure path
    # and requires (False, None, reason) from all of them - the contract
    # TR-1 established, which is exactly the thing an engine swap breaks
    # quietly. It makes one real call with a deliberately invalid key; the
    # assertion is about the contract, not the network, so no route is as
    # much a pass as a 401, and the printed line says which happened.
    'test_translate_api.py'
    # the two secrets leaving settings.py. It asks SHAPE questions and
    # prints VERDICTS - never a value - and its section 5 is a guard on
    # the suite and the patcher themselves, failing if either grows a
    # construct that could print a matched right-hand side. That rule
    # exists because I leaked two real keys into a conversation by
    # trusting a regex to mask them.
    'test_settings_env.py'
    # the border shorthand. Its section 3 paints all fifteen pages and
    # includes border WIDTH and STYLE in what it compares, because those
    # are exactly what the removed shorthand was supplying. Its section 4
    # guards the hyphen: border and border-radius are one careless regex
    # apart, every one of these rules carries both, and losing the radius
    # would not have failed section 3 - the border would be right and the
    # corners square.
    'test_btn_border.py'
    # the pickers that are built on demand. Its section 4 is the one that
    # matters: it pulls the REAL fillPicker out of the template, runs it
    # in a browser against a row with data-original-value set, and
    # requires the row to come back on its OWN values. A lazy picker that
    # fills correctly but forgets which option was selected would save
    # the 18,700 options and silently change what the form submits.
    'test_picker_lazy.py'
    # the icon names. Its section 2 censuses EVERY icon button in the
    # tree, wrapped or not, because the whole defect was that a third of
    # them were never looked at. Its section 5 plants the stray glyph on
    # an UNWRAPPED button deliberately - a stray on a wrapped one was
    # always catchable and would prove nothing about the widening.
    'test_icon_names.py'
    # the LOGIN_URL that was never set. Its section 2 does not read the
    # setting back - it wraps a view in Django's REAL login_required,
    # hands it an anonymous request, and reads the Location header, then
    # runs the SAME call with the setting put back as it was and requires
    # /accounts/login/. The 404 Demetri saw is reproduced, not described.
    # Its section 3 then resolves the target, because a LOGIN_URL that
    # routes nowhere is exactly what the defect was.
    'test_login_url.py'
    # property_detail's palette and its seven pixels. Section 1 is the
    # reason this suite exists: it PAINTS the page before and after at
    # four widths and compares scrollWidth to clientWidth, because the
    # overflow came from one rule here and one rule in Bootstrap and the
    # subtraction only happens in a browser - every text check in this
    # file would have passed on the broken page. Section 5 asserts the 25
    # surviving !important flags are STILL THERE, so a later round cannot
    # take them on this one's authority.
    'test_pd3.py'
    # the two submit buttons that belonged to no form. Its section 3
    # is a BROWSER check, not an argument about the HTML spec: it
    # clicks a submit button outside a form and requires NOTHING to
    # happen, then adds form= to that same button and requires the
    # form to submit. Section 5 then shows Enter still submitting the
    # BROKEN markup, which is why this survived for months.
    'test_submit_form.py'
    # the warning stripes. It renders TWICE, and the second kind is
    # the interesting one: three of the ten pages never draw the
    # element in the flattened fixture, so their page diff is empty -
    # and an empty diff is not evidence. Section 4 paints the RULE
    # instead, stylesheet plus one bare element, and answers for all
    # eleven. Section 6 requires that a border on all FOUR sides is
    # not caught, because sixteen of those exist and were never this
    # round's to change.
    'test_warn_stripe.py'
    # the 24 buttons that got a wrapper. Its section 3 is about a
    # button that was ALREADY broken: crs/fi_form drew its delete at
    # 15.5px, and the suite requires that measurement before it will
    # accept the 44px column as a fix. Section 5 counts the held-back
    # pages INCLUDING script - the first build reused the patcher's
    # own helper, which excludes it, and passed a page it was guarding.
    'test_row_wrap.py'
    # the card cell that could not wrap. Its section 2 paints eight
    # card tables and requires that SIX of them do not move - a fix in
    # base that quietly reflows every table in the app would be worth
    # knowing about before it ships, not after.
    'test_card_wrap.py'
    # the six finance screens. Its section 3 is about WORDS: ten of
    # the 22 controls had no title while 'Edit' was printed beside
    # them, and it requires every converted one to carry title AND
    # aria-label, and the twelve explanatory titles to have survived.
    # Section 6 counts braces, because the round's first attempt to
    # retire the component left broken CSS behind and the gate passed
    # it - the gate counted controls, not whether the sheet parsed.
    'test_finance_rows.py'
    # the P&L drill-down's Invoice column. Its section 4 is the check
    # that earned its keep: the drill-down handler listened for
    # .verify-icon alone, so the new document icon would have been a
    # button that did nothing when pressed - worse than the
    # unfindable tick, which at least worked.
    'test_pl_invoice_col.py'
    # the Remove on Edit Asset. Its section 3 checks FORM OWNERSHIP - the
    # button names a form and that form exists - because SV-1 proved a
    # submit button with no owner fails silently. Its section 4 reads the
    # view for .delete(save=False), which is the difference between a
    # file removed and a file merely unreachable.
    'test_asset_invoice.py'
    # one word on the lease page. Its section 2 is the part worth having:
    # a census of every sentence in the tree that points at a control by
    # DIRECTION, printed rather than bounded, because two of the three it
    # finds are comments nobody reads and the point is to put the list in
    # front of a person.
    'test_lease_above.py'
    # the ten form-shaped actions. Its section 2 requires that every form
    # inside the new wrapper still closes - a wrapper that swallowed a
    # </form> would read fine to a text census and be invalid markup.
    'test_form_wrap.py'
    # the invoice action order. Its section 4 reads the wrapper back and
    # counts what is inside it, because the first build of that round
    # moved a tag with a block and every other gate passed - a length
    # check cannot see a tag that merely moved.
    'test_invoice_order.py'
    # CO-2's suite cannot run PowerShell - there is none in the sandbox -
    # so it models NoComments in Python and requires the model to agree
    # with alv_tree.code_only on all 150 templates, then checks the SHAPE
    # of the lines on disk.
    'test_ps1_comment.py'
    # IC-1. Its section 4 censuses for a glyph name split across a
    # template tag, which is the shape that hid the third fa-ban from the
    # drift report and nearly let this round break its own rule.
    'test_user_slash.py'
    # AE-4. Section 4 is the column widths: revealing the Invoice column
    # without moving one makes the full page sum to 110 and a browser
    # normalises rather than refuses.
    'test_act_invoice_col.py'
    # OI-1. Its probe paints .age-label at 390 because the rule lives
    # inside a 768px media query - at 1280 it reads straight through to
    # Bootstrap's body colour and reports a pass for the wrong reason.
    'test_oi_report.py'
    # RA-5. Section 3 proves each registered control is the only icon
    # button in its element, and section 4 plants a fifth one and
    # requires --strict to refuse it.
    'test_row_exempt.py'
    # IC-2. Its section 3 makes the claim for the whole tree rather than
    # for one pair: after it, no picture is worn by two names at all.
    'test_user_check.py'
    # DR-2a. Section 3 paints all five pages at four widths and requires
    # every computed value to come back byte-identical, because a round
    # whose whole claim is that it cannot move a pixel is worth nothing
    # unless something looks.
    'test_dr2_spelling.py'
    # CS-2. Section 3 is the one that matters: the test is the extends
    # TAG, and a tag can be written inside a comment, so the reader has
    # to be code_only rather than the raw text.
    'test_css_standalone.py'
    # DR-2b. Section 3 paints each page's stylesheet against base AND
    # base with no page at all, and requires the two to agree on every
    # property the round touched - the claim is not that a declaration
    # is gone but that the page now computes what base alone computes.
    'test_dr2_values.py'
    # PH-1. Section 3 asks Django's own autodetector whether the
    # hand-written migration matches the model, rather than reading the
    # migration and deciding it looks right - this is the first schema
    # change in a fortnight and deploys run migrations automatically.
    'test_passport_holder.py'
    # PH-1b. Sections 3 to 5 run the real command against sqlite
    # databases built from the models' own metadata, through manage.py,
    # with a settings module that reads nothing from the environment for
    # its connection and so cannot reach a real database by accident.
    'test_passport_guard.py'
    # PH-1c. Section 3 runs the command against the shape production
    # really has - first-name members, full-name passports - and section
    # 5 plants a map that gives one member two names, which is how a
    # backfill quietly hands one person somebody else's documents.
    'test_passport_alias.py'
    # B-1, tier A of the Section B colour map. Section 1 reads base's
    # :root and resolves all thirteen substitutions against the literal
    # each one replaced; section 5 does the same for all 957 cuts off
    # the backups. The render in section 6 is smoke and is labelled as
    # smoke, because the whole claim is that the two pictures are the
    # same picture. Section 3 follows every non-browser render path in
    # the tree to its template and requires it to be standalone, which
    # is what keeps a var() out of a PDF that cannot read one.
    'test_colour_tokens.py'
    # B-2, tier B, the four neutrals. Section 2 is the round: every one
    # of the nine substitutions must move by EXACTLY the distance the
    # map records, to a tenth of an RGB unit, so a changed token refuses
    # the round rather than sliding 758 declarations. Section 6 measures
    # what it bought in contrast ratios and says out loud that the 201
    # borders went the other way. Section 7 is a real before-and-after,
    # bounded rather than identical.
    'test_colour_neutrals.py'
    # B-2b, the tail of tier B. Section 1 prints the shape - 21
    # spellings of one pale teal, 53 greys. Section 2 is B-2's gate
    # unchanged. Section 6 is the four entries where the classifier was
    # overruled, including the one that was dropped rather than fixed:
    # a border painted the page's own colour is invisible on purpose.
    'test_colour_tail.py'
    # E-2. THE GATE HAS NEVER COMPILED A TEMPLATE NOR REVERSED A NAME -
    # manage.py check does neither, so a typo in a {% url %}, an unknown
    # tag or a {% load %} nobody wrote has always shipped and 500'd on
    # the page that carried it. A census, not a round: no patcher, like
    # the twelve others on this list that have none. Section 6's control
    # is built IN MEMORY with Engine.from_string, deliberately - the one
    # named writer in the E4 flake is a suite that plants into a real
    # template on disk, and a gate proving the tree is sound must not be
    # the reason another one is flaky.
    'test_url_names.py'
    # E-2b. What E-2 found on its first run: pages/middleware.py named
    # access_denied.html and that template had never been written. A
    # bare except: swallowed it, so 172 guarded URL prefixes answered
    # with eighty lines of f-string instead - a purple gradient, two
    # emoji, no base. Section 4 renders the page through base at 1280
    # and 390; section 5 is the control, and it is the old fallback,
    # which must still fail every house check it ever failed.
    'test_access_denied.py'
    # E-2c. Seven suites resolved against pages.urls rather than the
    # project root, because the SANDBOX MIRROR could not import
    # mysite.urls - a gap in a copy of the tree recorded as a fact
    # about the tree. Section 3 measures what it cost: under
    # pages.urls /crs/ answers 404 and crs:index does not reverse.
    # Nothing in it mutates ROOT_URLCONF - both roots are asked in
    # one process with urlconf=, so this gate is not a writer.
    'test_root_urlconf.py'
    # B-3, tier C. The first colour round that cannot say nothing
    # moved: up to 88 RGB units. Its defence is contrast, and section
    # 3 measures it - seven pairs cross the AA line, two lose a
    # little and are named, none ends below it. Section 4 is the one
    # a (colour, role) map cannot do: 21 rest/hover pairs, each still
    # darker on hover after the move. Section 5 asserts the scope the
    # round left out, because a scope that is only in a comment is a
    # scope nobody checks.
    'test_colour_good_bad.py'
    # CM-1. One column had five limits and one of them was nothing:
    # the add path wrote request.POST straight to the row, with only
    # a browser maxlength between it and a DataError. Section 4 is the
    # one that matters and it is a behaviour, not a string - both
    # views driven with real POSTs against a real database, asked
    # whether 1000 is stored whole and 1001 is a message rather than a
    # crash. Section 5 asserts the two OTHER 255 columns on the same
    # page were not touched.
    'test_comment_length.py',
    # CR-1, 7 Oct 2026 - the five functions that let a colour round
    # see outside a <style> block, and the census they produce. The
    # section that matters is 5: it proves js_colour_context refuses
    # what it cannot classify rather than guessing, because a canvas
    # cannot resolve var() and 27 Chart.js colours in this tree would
    # vanish if it did.
    'test_cssrules_outside.py',
    # IM-1, 7 Oct 2026 - the gate that keeps decision 8 closed. Zero
    # page !important may beat base on the same selector and property.
    # It also holds CEILINGS, not equalities, on two numbers later
    # rounds remove - the 15 drift collisions decisions 12 and 15 carry
    # and the 227 dead declarations DW-1 deletes - so the gate fires if
    # either grows and stays quiet as they come down.
    'test_important_base.py',
    # DW-1, 7 Oct 2026 - the 177 copies of base deleted. Section 6
    # resolves the cascade for every one and shows the winning value
    # is the same before and after, which is the whole claim: this
    # round is invisible or it is wrong.
    'test_dead_weight.py',
    # PM-1, 7 Oct 2026 - the two mobile filter labels on Passports.
    # Section 3 drives Chromium at 390 and requires both to compute
    # `inline`, and at 1280 requires both to stay `none`, because the
    # round is a phone fix and must not touch the desktop.
    'test_passport_mobile.py',
    # B-4, 7 Oct 2026 - the amber. Section 4 proves the ink: eight
    # uses were below AA and now clear it, and not one that passed
    # drops. Section 5 re-applies B-3's rule that a hover must stay
    # darker than its rest state. Section 6 asserts the leave list -
    # the oranges, the chart series, the highlighter and the anTok
    # fallbacks - is untouched.
    'test_amber.py',
    # B-4b, 8 Oct 2026 - the fill/ink PAIR census. Section 2 is
    # the one declaration this round fixed; section 3 pins the 32
    # live pairs still below AA by name, each against the round
    # that owns it; section 4 names the 21 inactive ones and says
    # why WCAG exempts them.
    'test_pair_contrast.py',
    'test_recipe_spice.py',
    # B-5a, 8 Oct 2026 - the greys. Section 3 proves role picked
    # the token and not distance, section 4 is the fill/ink PAIR gate
    # B-4 did not have - fed B-4's own 9.77 -> 3.90 regression it
    # objects - and section 5 asserts what the round refused.
    'test_neutrals.py',
    # AD-1, 8 Oct 2026 - the System tab in teal. Section 2 renders
    # both tabs in Chromium and asserts they compute the SAME
    # colours, which is the instruction word for word; section 3 is
    # the tile contrast, including the one number that went down on
    # purpose; section 4 is the reserved cells, which are not
    # disabled buttons; section 5 is the decision this round
    # overturned, and who overturned it.
    'test_system_teal.py',
    # PR-1, 8 Oct 2026 - the Compliance tab. Section 2 renders both
    # tabs and asserts they compute the SAME colours, the way AD-1
    # does for Administration; section 3 measures the shared edge as
    # one 3px line; section 4 proves CRS Reporting MOVED rather than
    # being copied, gate and all; section 5 drives switchTab and
    # checks each panel actually shows.
    'test_compliance_tab.py',
    # TB-1, 8 Oct 2026 - the house tab treatment. Section 2 renders
    # BOTH landing pages and asserts every tab, panel and tile
    # computes the same, because one treatment is the claim; section
    # 3 is the derived edge; section 4 names each of the ten drifted
    # rules and which copy won it and why; section 6 is what moved
    # out of the pages and what stayed.
    'test_house_tabs.py',
    # FN-2, 8 Oct 2026 - Finance in two tabs. Section 2 renders it
    # beside Administration and asserts the same computed colours,
    # which is what "mimic Functional and System" means; section 3
    # proves all twelve destinations moved and none was invented or
    # lost; section 4 is that the page declares no tab CSS of its
    # own, which is the whole return on TB-1.
    'test_finance_tabs.py',
    # TB-2, 8 Oct 2026 - the tabs are CLICKED, on all three pages, and
    # exactly one carries .active after each click. The control is the
    # two pages as this round found them, where two did.
    'test_tab_switch.py',
    # B-5b, 8 Oct 2026 - the grey tail. Section 2 measures the pair
    # contrast of every rule it touched, before and after; section 4
    # asserts the empty-state watermark is now ONE value on twelve
    # pages; section 5 names everything the round left and proves it is
    # still there.
    'test_grey_tail.py',
    # HM-1, 8 Oct 2026 - the Home split. Section 2 renders both
    # audiences and asserts no income figure reaches the standard
    # user's page - the SOURCE, not the screen, because the defect
    # this round exists for was a card that was not drawn and a
    # payload that was still shipped.
    'test_home_split.py',
    # HM-2, 9 Oct 2026 - the Issues panel. Section 2 runs
    # issues_insight over a fixture whose answers are known by hand;
    # section 3 is the sentinel, with the control that asking IS NOT
    # NULL gets the wrong answer; section 4 is that the panel is
    # outside the income gate, because it is for both audiences.
    'test_issue_panel.py',
    'test_issue_dates.py',
    'test_brights.py',
    'test_issue_card.py',
    'test_issue_centre.py',
    'test_required_promise.py',
    'test_radius_token.py',
    'test_bar_height.py',
    'test_form_grid.py',
    'test_crs_print.py',
    'test_cashflow_cards.py',
    'test_label_weight.py',
    'test_lines_table.py',
    'test_form_card_radius.py',
    'test_held_four.py',
    'test_held_contrast.py',
    'test_drift_root.py',
    'test_help_label.py',
    'test_pi_leases.py',
    'test_dash_std.py',
    'test_modal_heads2.py',
    'test_py_code.py',
    'test_surface_border.py',
    'test_js_buttons.py',
    'test_recipe_tones.py',
    'test_recipe_photos.py',
    'test_recipe_side_b.py',
    'test_vocabulary.py',
    'test_panel_heads.py',
    'test_verb_colours.py',
    'test_pdf_viewer.py',
    'test_calendar_grid.py',
    'test_project_origin.py',
    'test_stat_cols.py',
    'test_tab_names.py',
    'test_landing_tab.py',
    'test_perm_select.py',
    'test_deed_table.py',
    'test_notify_icon.py',
    'test_customer_view.py',
    'test_deed_one_column.py',
    'test_leave_decided.py',
    'test_data_table.py',
    'test_admin_behaviour.py',
    'test_home_open.py',
    'test_ws_members.py',
    'test_ae_probe.py',
    'test_label_law.py',
    'test_gate_speed.py',
    'test_contact_modal.py',
    'test_invoice_icon.py',
    'test_danger_pair.py',
    'test_image_wire.py',
    # NW-1, 17 Oct 2026 - E20, the network guard and its 87 suites.
    'test_offline.py',
    # PG-1, 18 Oct 2026 - E24, the subject read against the tree.
    'test_preflight.py',
    # MN-1, 18 Oct 2026 - test_meal_fixes.py and test_meal_display.py
    # are RETIRED here. They asserted the shape of the two calendar
    # views, the Create/Edit screen and the plan list, and release 3
    # deletes all four. Their fixes are not dropped: the ones that
    # outlive the shape are asserted by test_planner.py below, and the
    # ones that were guards against a plan with dates dissolved when
    # the plan did.
    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Two screens now.
    'test_meal_help.py',
    # MN-1, 18 Oct 2026 - release 3. The calendar IS the plan.
    'test_planner.py',
    # RT-1, 18 Oct 2026 - what the tree does with a page it
    # used to have. Sixteen rows of the table above guarded
    # the four pages MN-1 retired; they are gone, and this
    # suite is why they cannot come back.
    'test_retired.py',
    # MW-1, 19 Oct 2026 - release 3, push 2. The week moves: copy
    # a week onto a week you pick, save one as a Menu, stamp a
    # Menu onto any week. No migration - Menu and MenuItem came
    # with 0100 in push 1, holding DAY INDEXES and not dates
    # exactly so that this round could exist.
    'test_meal_week.py',
    # MO-1, 19 Oct 2026 - release 3, push 2. The day speaks: a
    # planned night that is not a recipe, and leftovers that
    # cost nothing. Both columns shipped with 0100 and nothing
    # in the application could fill either.
    'test_meal_day.py',
    # NF-1, 19 Oct 2026 - the round-name check reads the tree. The
    # register is one place a name lives; MP-2 has no entry in it
    # and four live references, one of them a pin.
    'test_name_free.py',
    # MH-3, 19 Oct 2026 - release 3, push 2. The guide catches up
    # with the week. MH-2 promised four features at the foot of a
    # tab and MW-1 and MO-1 built all four the next morning.
    'test_meal_guide3.py',
    # MC-4's test_mini_grid.py was HERE, and is retired by MV-2,
    # 19 Oct 2026 - it rendered the mini calendar and MV-2 deletes
    # it. Its lesson moved to test_month_view.py, which counts
    # columns in a browser for the same reason MC-4 had to.
    # PK-1, 19 Oct 2026 - the picker is a grid, and it filters.
    # Demetri on the live dialog: "there is so much wasted space
    # on the right of each recipe. Should it not be a grid?"
    'test_picker_grid.py',
    # GS-1, 19 Oct 2026 - the contended list. This suite RUNS the
    # runner against a planted slow suite and counts which phase
    # it landed in, because a list nobody reads is a list that
    # stops being true.
    'test_gate_serial.py',
    # MX-1, 19 Oct 2026 - the old planner's three tables. The
    # suite re-asks the whole tree whether anything still reads
    # them, because a migration that drops a table something
    # still names is a 500 and not a failed check.
    'test_meal_drop.py',
    # PF-2, 19 Oct 2026 - the five filters on one shared function.
    # Section 2 REPLAYS the library's old filter block and the new
    # shared one against the same selections and compares the ORM
    # calls, because "it behaves the same" is a claim and a
    # recording is a reading.
    'test_pick_filter.py',
    # MV-1, 19 Oct 2026 - the view switcher. Section 3 DRIVES all
    # three links and asks the view which day it landed on,
    # because a switcher that loses the date is worse than none.
    'test_view_switch.py',
    # MV-2, 19 Oct 2026 - the month grid. It RENDERS the thing,
    # because MC-4 is the round where every class name was right
    # and the calendar drew one column.
    'test_month_view.py',
    # MV-3, 19 Oct 2026 - the week as seven columns. It RENDERS
    # the week and measures its height, because "the daily list
    # is not required" was a complaint about 4,900px and a
    # number is the only answer to it.
    'test_week_cols.py',
    # MV-4, 19 Oct 2026 - one day in full. It counts the cards a
    # page draws in each of the three views, because "not
    # required" was a claim about how many there were.
    'test_day_view.py',
    # RD-1, 19 Oct 2026 - the recipe modal, and the one read behind
    # it. Section 3 asks a real database whether the extracted read
    # gives the same answer as get_preferred_weight_conversion, which
    # is the authority the rest of the package already asks, on every
    # ingredient of every recipe it builds.
    'test_recipe_modal.py',
    # RW-1, 19 Oct 2026 - the weight in grams. Section 3 asks a real
    # database for the five quantities that were wrong, and section 1
    # asks the function directly for the one that was invisible.
    'test_recipe_weight.py',
    # PB-2, 19 Oct 2026 - the view survives a write. Section 3 drives
    # every one of the eleven endpoints from each of the three views
    # and asks where it landed, which is the question nobody asked in
    # push 1.
    'test_planner_back.py',
    # RD-2, 19 Oct 2026 - the chip menu. Section 3 clicks a chip and
    # asks whether the picker ALSO opened, which is the question the
    # capture phase exists to answer.
    'test_chip_menu.py',
    # MB-2, 19 Oct 2026 - the date bar. Section 3 RENDERS the three
    # views and measures the bar against the switcher above it,
    # because "I do not like how it displays" came down to 44px
    # against 32px.
    'test_month_bar.py',
    # WC-1, 19 Oct 2026 - a day is a day in every view. Section 3
    # clicks a day in BOTH views and asks whether the picker opened,
    # which is the comparison no suite was making.
    'test_week_click.py',
    # DC-1, 19 Oct 2026 - the Day card on one line. Section 3 RENDERS
    # it and measures the ink with a Range, because a block's
    # rectangle is the row's width whatever is in it and two earlier
    # instruments said 99% because of that.
    'test_day_card.py',
    # PS-1, 19 Oct 2026 - the picker adds on click and stays open.
    # Section 3 drives it in a browser: four adds, one open, and the
    # filters still set at the end.
    'test_picker_stays.py',
    # DB-1, 20 Oct 2026 - the responsive wrapper closes. Section 2
    # asks the BROWSER what media every rule in this file ends up in,
    # which is the question no suite in this system was asking.
    'test_date_bar.py',
    # CL-1, 20 Oct 2026 - the chip is a pill. Section 2 RENDERS it and
    # reads the COMPUTED fill and type size, because the fault was a
    # rule that was present in the file and beaten in the browser.
    'test_chip_pill.py',
    # RL-1, 20 Oct 2026 - the picker reload binds. Section 3 DRIVES a
    # real server in a real browser and counts navigations after Done,
    # because nothing readable in the source says whether a handler
    # was registered.
    'test_pick_reload.py',
    # PB-3, 20 Oct 2026 - a write leaves you on the day you were on.
    # Section 3 POSTS from a day and reads the Location header, which
    # is the only place this fault is visible.
    'test_back_date.py',
    # RD-3, 20 Oct 2026 - the photograph opens the recipe. Section 3
    # RENDERS the library and presses a heart, so the claim that the
    # overlays are siblings of the trigger is measured rather than
    # reasoned.
    'test_quick_look.py',
    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library.
    # Section 3 DRIVES it: press the icon, press a day, read the
    # toast, press Undo, and ask the database what is left.
    'test_add_planner.py',
    # FV-1, 20 Oct 2026 - a token for everyone who can press
    # something. Section 2 asks which {% if %} every csrf_token on
    # the page sits inside, which is the question that found it.
    'test_fav_token.py',
    # LO-1, 20 Oct 2026 - leftovers from Month and Week. Section 3
    # opens the menu on a RECIPE chip and on a NOTE chip and asks
    # which items each one offers.
    'test_chip_left.py',
    # NT-1, 20 Oct 2026 - a note from Month and Week. Section 3
    # drives the hand-off, because two dialogs and a reload is
    # exactly where this goes wrong.
    'test_pick_note.py',
    # SL-7, 20 Oct 2026 - the shopping list covers what you are
    # looking at. Section 3 asks the three views for their link and
    # reads the dates out of it.
    'test_list_range.py',
    # CE-1, 20 Oct 2026 - the console-encoding probe stops writing a
    # .py into the repository that test_code_only is reading.
    'test_ce_scratch.py',
    # PP-1, 20 Oct 2026 - the plan, laid out for paper. Section 3
    # asks the page for a ragged range and counts the columns.
    'test_print_plan.py',
    # MH-5, 20 Oct 2026 - the guide catches up with the calendar, and
    # stops describing two panels, a trashcan and an eye.
    'test_meal_guide5.py',
    # SC-1, 21 Oct 2026 - the library shortcut says Today, and the
    # third one that nobody wanted is gone.
    'test_say_today.py',
    # BO-1, 21 Oct 2026 - the planner bar reads primary first, which
    # is what the standard has said since 7 September.
    'test_bar_first.py',
    # WT-1, 21 Oct 2026 - the selected week and the meals on it were
    # the same token, dE 0.0. The week is an edge now.
    'test_week_band.py',
    # SH-2, 21 Oct 2026 - the shopping list had two action bars and
    # the wrong one came first.
    'test_sl_range_row.py',
    # MG-1, 21 Oct 2026 - three meal-plan pages wrote messages and
    # none of them could show one.
    'test_msg_bar.py',
    # HP-1, 21 Oct 2026 - Help on the planner could not be reached on
    # a phone at all. One control in 32 bars; the others are clean.
    'test_help_phone.py',
    # BA-1, 21 Oct 2026 - the bar instrument could not see a form
    # bar, read a tree-wide claim through a historical reader, and
    # nobody asked whether a menu item exists outside its menu.
    'test_bar_audit.py',
    # CP-2, 21 Oct 2026 - three features that could only be reached
    # on a phone are on the bar, and Copy takes any span of days.
    'test_copy_menus.py',
    # RG-1, 21 Oct 2026 - the printed plan has four shapes now, and a
    # month fits on one sheet of A4.
    'test_print_shape.py',
    # RG-2, 21 Oct 2026 - the printed plan takes a range of its own,
    # and says what the second Print press is for.
    'test_print_range.py',
    # WF-1, 21 Oct 2026 - the week band gets the fill he asked for,
    # from the one palette WT-1 never measured.
    'test_week_fill.py',
    # RG-3, 21 Oct 2026 - a sheet is as tall as what is on it. The
    # week and the day stop after the last recipe; the month still
    # fills its page, which is the point of the month.
    'test_print_compact.py',
    # PX-2, 21 Oct 2026 - a floor under the display copy, so the
    # browser stops upscaling 97 photos badly on every page load.
    'test_photo_floor.py',
    # BM-1, 21 Oct 2026 - one message loop in base, 81 copies gone,
    # and the 55 pages that could not show a message can now.
    'test_msg_base.py',
    # MN-2, 21 Oct 2026 - a menu takes a range and lands where you say.
    'test_menu_range.py',
    # RO-1, 21 Oct 2026 - a day is dragged into order by its grip.
    'test_day_order.py',
    # VR-1, 21 Oct 2026 - the cooking schedule readout wears tokens,
    # and the two tables that are NOT data tables say so.
    'test_recipe_tidy.py',
    # HG-1, 22 Oct 2026 - the guide names what the page shows, and the
    # page's bar is named in the guide. Both directions.
    'test_help_agrees.py',
    # WD-1, 22 Oct 2026 - the week columns drag, through RO-1 endpoint.
    'test_week_drag.py',
    # DP-1, 22 Oct 2026 - the site says what commit it is running.
    'test_deploy_probe.py',
    # SD-1, 22 Oct 2026 - a rebuild replaces the file it rebuilds.
    'test_photo_rebuild.py',
    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    'test_config_truth.py',
    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    'test_ws_prefetch.py',
    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    'test_planter_lock.py',
    # SB-2, 22 Oct 2026 - one primary on the shopping bar, and none
    # offering to do something there is nothing to do.
    'test_shop_bar2.py',
    # SI-1, 22 Oct 2026 - a copied recipe takes its own photo, and a
    # delete asks who else is holding the file.
    'test_shared_image.py',
    # NL-1, 22 Oct 2026 - a generated name fits the column it is
    # stored in, and the names got shorter as well as the column wider.
    'test_name_width.py',
    # PT-1, 22 Oct 2026 - the print sheet knows which view sent it, so
    # Back lands where it started and a week bounds its own pickers.
    'test_print_origin.py',
    # RV-1, 23 Oct 2026 - the receipt has a screen that shows the
    # record, not only the document. G2, outstanding since 16 Oct.
    'test_receipt_view.py',
    # IR-1, 23 Oct 2026 - one register for one kind of identifier, and
    # the receipt number finally goes somewhere. G1.
    'test_ref_link.py',
    # ES-1, 23 Oct 2026 - the e-signing envelope, its parties and its
    # append-only audit trail.
    'test_esign_model.py',
    # ES-2, 23 Oct 2026 - the lease rendered to page images, and the
    # signature page appended at sealing.
    'test_esign_pdf.py',
    # UO-1, 23 Oct 2026 - the lease and the deed survive a failed save.
    'test_upload_order.py',
    # CF-2, 23 Oct 2026 - one requirements file, and it is the one
    # railway.json installs.
    'test_one_list.py',
    # WK-1, 23 Oct 2026 - the push script can be told how many
    # suites to run at once.
    'test_push_workers.py',
    # ES-3a, 23 Oct 2026 - the envelope register and the fourth tile.
    'test_lease_signing.py',
    # T2-1, 24 Oct 2026 - a tenancy can hold two people.
    'test_second_tenant.py',
    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    'test_tenant_screens.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
# the 203, it shows 1/203 and then name for the first one... This way I can
# monitor progress and manage my time better."
#
# Still true, and alv_run.py still does it - the numbering, the total taken
# from the list rather than typed, and the count of suites that were not on
# disk. What moved is where the loop lives.
#
# GT-2, 17 Oct 2026 - THE LOOP LIVES IN alv_run.py NOW.
#
# It ran one suite at a time, which is where most of the hour went. The
# replacement runs them in a pool, with the fourteen suites that plant
# into real files pinned to a serial phase first, and the browser suites
# before the rest so a bad environment shows early. It reads $suites out
# of THIS FILE, so the list above stays the only place it is kept.
#
# WHY IT IS PYTHON. There is no PowerShell in the sandbox these rounds
# are built in, so nothing written here can be run before it is
# delivered. alv_run.py was run against all 360 suites before this round
# existed: 359 pass through it, and the one that does not fails alone
# too. Everything that can be got wrong is in the file that was tested;
# what is left here is a call.
#
# The numbering, the skip report and the stop-on-failure all moved with
# the loop - see alv_run.py, which prints them in the same shape.
$runArgs = @((Join-Path $root 'alv_run.py'))
if ($Force)  { $runArgs += '--force' }
if ($Resume) { $runArgs += '--resume' }
# WK-1, 23 Oct 2026. Only when asked - see the parameter.
if ($Workers -gt 0) { $runArgs += @('--workers', "$Workers") }
& python @runArgs 2>&1 | ForEach-Object { Say $_ }
if ($LASTEXITCODE -ne 0) {
    Bad 'one or more suites FAILED - see the lines above'
    if (-not $Force) { Say ''; Say '  Stopping.  Nothing has been staged.'; exit 1 }
} else {
    Good ('all ' + $suites.Count + ' suite(s) accounted for')
}

# A suite proves the pages it was written about.  Show-ButtonDrift
# --strict --recipes proves the ones nobody thought to write a check for:
# it exits non-zero while ANY button still carries a Bootstrap colour
# class in a place base.html owns.  Cheap, and it is the thing that
# catches the next page somebody adds by copying an old one.
#
# --recipes SINCE RS-1b, 14 Oct 2026, AND THE FLAG IS THE POINT.  Without
# it this gate asked 117 of the application's 142 pages: the recipe and
# meal-plan side was deferred by name in August, and the sentence above
# said "walks every template" for the whole two months in between.  RS-1a
# took that side's 35 decided buttons and RS-1b the 31 that were left, so
# the flag can go on and the claim can be true.
#
# WHAT IT STILL DOES NOT SEE, written here rather than discovered later:
# seventeen buttons across eight pages carry neither a Bootstrap colour
# this tool LISTS nor a house class, so every census in this project
# passes over them.  Two are `btn-outline-light` on ingredient_families -
# a Bootstrap colour that BOOTSTRAP does not list, which is the blind
# spot the note beside the outline variants warns about, one shade
# further on.  The rest are inline style, btn-link, or a page's own
# class.  Widening the page SCOPE does not widen the VOCABULARY, and
# that is the next thing in this line of work.
$guard = Join-Path $root 'Show-ButtonDrift.py'
if (Test-Path $guard) {
    Say ''
    Say '  == Show-ButtonDrift.py --strict --recipes'
    & python $guard --strict --recipes 2>&1 | ForEach-Object { Say ('     ' + $_) }
    if ($LASTEXITCODE -ne 0) {
        Bad ('button drift, an undecided button, or a page rendering its ' +
             'actions twice - see the output above')
        if (-not $Force) { Say ''; Say '  Stopping.  Nothing has been staged.'; exit 1 }
    } else {
        Good 'no button drift'
    }
} else {
    Warn 'Show-ButtonDrift.py not present - drift guard skipped'
}

# RA-1, 4 Oct 2026 - THE SECOND DRIFT GUARD, and for the same reason as the
# first: a standard that is only in a suite is a standard the next page
# copied from an old one will quietly leave. Demetri asked for one order
# for the action column "in all tables ... across the app", and this is
# what notices the day a table stops keeping it - including a page nobody
# has written a check for yet.
$raGuard = Join-Path $root 'Show-RowActionDrift.py'
if (Test-Path $raGuard) {
    Say ''
    Say '  == Show-RowActionDrift.py --strict'
    & python $raGuard --strict --quiet 2>&1 | ForEach-Object { Say ('     ' + $_) }
    if ($LASTEXITCODE -ne 0) {
        Bad ('an action column has left the house order, or an icon class ' +
             'has picked up a second picture - see the output above')
        if (-not $Force) { Say ''; Say '  Stopping.  Nothing has been staged.'; exit 1 }
    } else {
        Good 'no row action drift'
    }
} else {
    Warn 'Show-RowActionDrift.py not present - row action guard skipped'
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

# THE MESSAGE GOES THROUGH A FILE, NOT THROUGH -m.
#
# This used to be `git commit -m $Message -m $p ...`, and it broke the first
# time a -Body paragraph QUOTED something:
#
#     'Show-ButtonDrift has reported these as "NOT rewritten ... decided by
#      hand"; this is that hand.'
#
# PowerShell 5.1 does not escape an embedded " when it hands an argument to a
# NATIVE executable - it passes the string through verbatim, so the quote
# closed git's argument and git read the remainder as pathspecs:
#
#     error: pathspec 'rewritten' did not match any file(s) known to git
#
# Note where that lands: AFTER `git add -A`, so the tree was staged and the
# commit was not. Nothing was lost, but the next run had to be re-driven.
#
# There is no amount of doubling or backticking that makes this reliable
# across quoting styles - the fix is to stop passing prose on a command line
# at all. -F takes the whole message as a file, byte for byte, and quotes,
# backticks, semicolons and newlines in it stop meaning anything.
$msgFile = Join-Path ([IO.Path]::GetTempPath()) ('alv-commit-' + [guid]::NewGuid().ToString('N') + '.txt')
try {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add($Message)
    foreach ($p in $Body) { $lines.Add(''); $lines.Add($p) }
    $lines.Add('')
    $lines.Add('Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>')
    # UTF8 without a BOM: git would otherwise carry the BOM into the subject
    # line, where it shows up as a stray character in every log.
    [IO.File]::WriteAllText($msgFile, ($lines -join "`n"),
                            (New-Object Text.UTF8Encoding $false))
    & git commit -F $msgFile
    $commitCode = $LASTEXITCODE
} finally {
    if (Test-Path $msgFile) { Remove-Item $msgFile -Force }
}
if ($commitCode -ne 0) { Bad 'git commit failed'; exit 1 }
Good 'committed'

# CONTROL: the message that landed is the message that was asked for.
#
# The -m version failed loudly THIS time because git happened to read the
# fragments as pathspecs. A quoting fault that merely TRUNCATED a paragraph
# would have committed quietly with half the reasoning missing, and nobody
# would find out until they read the log months later. So read it back.
# .Contains, NOT -like: -like reads [ ] * ? as wildcards, and a commit body
# is prose that may contain any of them. An ordinal substring test is what is
# meant here.
$committed = [string]((& git --no-pager log -1 --pretty=%B) -join "`n")
$lost = New-Object System.Collections.Generic.List[string]
if (-not $committed.Contains($Message)) { $lost.Add('the subject') }
foreach ($p in @($Body)) {
    if (-not $committed.Contains($p)) {
        $lost.Add('"' + $p.Substring(0, [Math]::Min(48, $p.Length)) + '..."')
    }
}
if ($lost.Count) {
    Bad ('the commit message lost ' + $lost.Count + ' piece(s) between here and git:')
    foreach ($l in $lost) { Say ('        ' + $l) }
    Say  '        Amend it before pushing:  git commit --amend'
    exit 1
}
Good ('the commit message is intact (' + (1 + @($Body).Count) + ' part(s) read back)')
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

# DP-1, 22 Oct 2026 - AND THEN FIND OUT WHETHER IT DID.
#
# The line above has been printed at the end of every push since this
# script was written, and twice in two days it was not true: Railway
# had builds paused, the push landed, the post-deploy checks printed,
# and the live site went on running 3245f19.
#
# THE SITE ANSWERS THE QUESTION ITSELF. /version/ returns seven
# characters of hex - the commit the running process was built from -
# and this asks it until it answers the SHA just pushed. No token, no
# API, nothing on this laptop to leak.
#
# A TIMEOUT IS NOT A FAILURE. The push is already in; running out of
# patience costs nothing, so this exits 0 either way and says what the
# live site is still running.
$deployed = $false
if (-not $NoWait) {
    Head 'Deploy'
    $sha  = [string](& git rev-parse HEAD)
    $want = $sha.Trim().Substring(0, 7)
    $probe = ($Site.TrimEnd('/') + '/version/')
    Say ('  asking ' + $probe + ' for ' + $want)
    Say ('  up to ' + $WaitMinutes + ' minute(s). Ctrl-C costs nothing - the push is already in.')
    $deadline = (Get-Date).AddMinutes($WaitMinutes)
    $seen = ''
    while ((Get-Date) -lt $deadline) {
        $got = ''
        try {
            $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 15 -Uri $probe
            $got = ([string]$resp.Content).Trim()
        } catch {
            $got = '(no answer)'
        }
        if ($got -eq $want) { $deployed = $true; break }
        if ($got -ne $seen) {
            $seen = $got
            Say ('  ' + (Get-Date -Format 'HH:mm:ss') + '   live says: ' + $seen)
        }
        Start-Sleep -Seconds 15
    }
    if ($deployed) {
        Good ('DEPLOYED - ' + $Site + ' is running ' + $want)
    } elseif ($seen -eq 'unknown') {
        Warn 'the probe answers, but the build supplied no commit SHA'
        Say  '        Railway normally sets RAILWAY_GIT_COMMIT_SHA on its own.'
        Say  '        Until it does, this cannot tell one deploy from another.'
    } elseif ($seen -eq '(no answer)' -or $seen -eq '') {
        Warn ('no answer from ' + $probe + ' in ' + $WaitMinutes + ' minute(s)')
        Say  '        Either the deploy has not landed yet, or this is the'
        Say  '        first push carrying the probe and the OLD build has no'
        Say  '        /version/ to answer with. Both look the same from here.'
    } else {
        Warn ('not deployed after ' + $WaitMinutes + ' minute(s) - live is still running ' + $seen)
        Say  '        The push is in. Watch Railway, or ask again:'
        Say  ('           (Invoke-WebRequest -UseBasicParsing ' + $probe + ').Content')
    }
}

Write-Host ''
if ($Checks.Count -gt 0) {
    if ($deployed) {
        Write-Host 'The deploy is green. Worth checking on Live:' -ForegroundColor Cyan
    } else {
        Write-Host 'Worth checking on Live ONCE THE DEPLOY IS GREEN - it is not yet:' -ForegroundColor Yellow
    }
    for ($i = 0; $i -lt $Checks.Count; $i++) {
        Write-Host ('  {0}. {1}' -f ($i + 1), $Checks[$i])
    }
} else {
    Write-Host 'No post-deploy checks were given for this batch.' -ForegroundColor DarkYellow
    Write-Host 'Pass -Checks "..." , "..." next time if there is something to look at.'
}
