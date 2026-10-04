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

# ------------------------------------------------------- 1. is it applied?
# Each change leaves a distinctive string behind.  If one is missing the tree
# is only half-patched and must not be committed.
Head 'Are all the changes actually in the tree?'

$sentinels = @(
    @{ File = 'pages\templates\base.html'; Text = 'PU-1b, 3 Oct 2026'; What = 'PU-1b: a scroll inside the popup no longer closes it' },
    @{ File = 'pages\templates\unit_conversions_management.html'; Text = 'UC-1b, 3 Oct 2026'; What = 'UC-1b: the scope toggle uses icons, which CSS can colour' },
    @{ File = 'pages\templates\create_meal_plan.html'; Text = 'icon-action-btn icon-delete'; What = 'MP-1: the trashcans are on the house row-action strip' },
    @{ File = 'pages\templates\create_meal_plan.html'; Text = 'btn-add-recipe'; Absent = $true; Code = $true; What = 'MP-1: and the green Add Recipe is gone, script included' },
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
    @{ File = 'pages\templates\meal_plans.html'; Text = 'icon-action-btn icon-view'; What = 'ML-1: the row is on the house action strip' },
    @{ File = 'pages\templates\base.html'; Text = '.icon-list       { color: var(--alv-view)'; What = 'ML-1: base carries the shopping-list NAME on the view colour' },
    @{ File = 'pages\templates\meal_plans.html'; Text = 'onclick="confirmDelete('; Absent = $true; Code = $true; What = 'ML-1: the plan name is not written into a handler' },
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
    @{ File = 'pages\templates\view_meal_plan.html'; Text = 'A-BAR, 2 Oct 2026. Back used to come FIRST here'; What = 'A-BAR: Back sits at the END of the bar on View Meal Plan' },
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
    @{ File = 'pages\templates\base.html';                Text = '.sidebar-toggle:hover { background: #0a5e6a;'; What = 'sidebar hover uses the new ink' },
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
    @{ File = 'pages\templates\customer_list.html';       Text = 'mobile-action-bar cols-2'; What = 'and its two mobile actions say so' },
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
    @{ File = 'pages\templates\meal_plan_calendar.html'; Text = 'class="alv-seg"'; What = 'the Calendar page can get back to the list' },
    @{ File = 'pages\templates\meal_plan_calendar.html'; Text = 'rgba(255, 255, 255, 0.7)'; What = 'and the white ink that hid the List half is gone'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\meal_plans.html'; Text = 'class="alv-seg"'; What = 'the list page wears the same two-segment control' },
    # Five filled buttons in five colours became the icon strip the list
    # rows already wore. #007bff is named because it was the loudest.
    @{ File = 'pages\templates\meal_plan_calendar.html'; Text = 'icon-action-btn icon-duplicate'; What = 'the Calendar week actions are the row-action strip' },
    @{ File = 'pages\templates\meal_plan_calendar.html'; Text = '#007bff'; What = 'and the five filled colours went with them'; Absent = $true; Code = $true },
    # A disabled button that rendered as a live one, because .btn.action-primary
    # outranked the page's own grey. There is no string this adds that proves
    # it, so the absence of the old class is the assertion.
    @{ File = 'pages\templates\meal_plans.html'; Text = 'btn-create-disabled'; What = 'the no-permission Create no longer renders as a live button'; Absent = $true; Code = $true },
    @{ File = 'pages\templates\meal_plans.html'; Text = 'action-primary disabled-btn'; What = 'it wears the class base paints grey' },

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
    @{ File = 'test_tree_roots.py'; Text = 'def python_code_only'; What = 'the Python-source one has a name of its own now' },
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
    @{ File = 'mysite\settings.py'; Text = 'django-insecure-'; What = 'and no generated-and-never-changed key is left in the file'; Absent = $true }
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
    $t = [regex]::Replace($t, '/\*.*?\*/', '', $sl)
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
)
# A suite listed here but not on disk currently prints an amber line and
# carries on. That is the right behaviour for a repo where a suite may not
# have been written yet - but the COUNT of skips is the thing worth seeing,
# because "23 passed" reads identically whether 23 ran or 23 were skipped.
$skipped = @()
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
# the 203, it shows 1/203 and then name for the first one... This way I can
# monitor progress and manage my time better."
#
# THE TOTAL IS $suites.Count, NOT A NUMBER TYPED HERE. The list grows by a
# line every round - 197 three weeks ago, 203 today - and a hardcoded total
# would be wrong the first time somebody appends to it and would go on
# being wrong silently. The width is computed from the count too, so the
# numbers stay in a straight column whether there are 99 or 1,099.
#
# The three names carry a suite prefix because this script is 1,200 lines
# and $label already belongs to the manifest loop five hundred lines up.
$suiteNo = 0
$suiteWide = ('' + $suites.Count).Length
foreach ($t in $suites) {
    $suiteNo++
    $suiteLabel = ('[' + ('' + $suiteNo).PadLeft($suiteWide) + '/' + $suites.Count + ']')
    if (-not (Test-Path (Join-Path $root $t))) {
        Warn ($suiteLabel + ' ' + $t + ' not present - skipped')
        $skipped += $t
        continue
    }
    Say ''
    Say ('  == ' + $suiteLabel + ' ' + $t)
    & python $t 2>&1 | ForEach-Object { Say ('     ' + $_) }
    if ($LASTEXITCODE -ne 0) {
        # THE NUMBER ON THE FAILURE LINE TOO. In a 203-suite run the failure
        # scrolls past the banner that said which suite was starting, and
        # "test_x FAILED" alone does not say how far in it was.
        Bad ($suiteLabel + ' ' + $t + ' FAILED')
        if (-not $Force) { Say ''; Say '  Stopping.  Nothing has been staged.'; exit 1 }
    }
}

Say ''
if ($skipped.Count -gt 0) {
    Warn ('' + $skipped.Count + ' of ' + $suites.Count + ' suite(s) were not on disk and did not run:')
    foreach ($t in $skipped) { Warn ('     ' + $t) }
} else {
    Good ('all ' + $suites.Count + ' suite(s) ran')
}

# A suite proves the pages it was written about.  Show-ButtonDrift --strict
# proves the ones nobody thought to write a check for: it walks every
# template and exits non-zero while ANY button still carries a Bootstrap
# colour class in a place base.html owns.  Cheap, and it is the thing that
# catches the next page somebody adds by copying an old one.
$guard = Join-Path $root 'Show-ButtonDrift.py'
if (Test-Path $guard) {
    Say ''
    Say '  == Show-ButtonDrift.py --strict'
    & python $guard --strict 2>&1 | ForEach-Object { Say ('     ' + $_) }
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
