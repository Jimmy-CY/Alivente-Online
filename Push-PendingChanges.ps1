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
    @{ File = 'pages\templates\base.html';                Text = 'pointer-events: none';            What = 'a disabled button is not a live link' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'btn action-primary';              What = 'Edit is the primary, not yellow' },
    @{ File = 'pages\templates\asset_detail.html';        Text = 'action-secondary action-danger';  What = 'and Delete is outlined, not solid red' },
    @{ File = 'pages\templates\base.html';                Text = 'display: none !important';        What = 'paper stops printing the furniture' },
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
    @{ File = 'pages\templates\invoices.html';            Text = '{% for prop in all_props %}'; What = 'the filter dropdown lists every property, not just the chosen one' },
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
    @{ File = 'pages\views\finance.py'; Text = 'carries_a_share(expense.objects.filter('; What = 'and the screens that decide membership go through it' }
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
    'test_share_of_zero.py'
)
# A suite listed here but not on disk currently prints an amber line and
# carries on. That is the right behaviour for a repo where a suite may not
# have been written yet - but the COUNT of skips is the thing worth seeing,
# because "23 passed" reads identically whether 23 ran or 23 were skipped.
$skipped = @()
foreach ($t in $suites) {
    if (-not (Test-Path (Join-Path $root $t))) {
        Warn ($t + ' not present - skipped')
        $skipped += $t
        continue
    }
    Say ''
    Say ('  == ' + $t)
    & python $t 2>&1 | ForEach-Object { Say ('     ' + $_) }
    if ($LASTEXITCODE -ne 0) {
        Bad ($t + ' FAILED')
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
