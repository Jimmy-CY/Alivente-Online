# -*- coding: utf-8 -*-
"""apply_housekeeping_three.py - round HK-3, 28 Oct 2026.

RELEASE 30 - ONE jQUERY, A FASTER GATE, AND THE HOUSE COLOURS.

    - base.html loads jQuery, Popper and Bootstrap once, in <head>. The 33
      pages that loaded their own jQuery (because their scripts ran before
      base's) no longer do, and the nine that also loaded their own
      Bootstrap 4.5/4.6 no longer do either - two Bootstraps answered
      every data-toggle twice.
    - test_print_queries and test_dr2_values load each fixture once and
      resize it, instead of a fresh page per measurement: 165s -> 40s and
      65s -> 11s alone, every result line identical.
    - His eye, 28 Oct: the six older Notifications icons carried
      Bootstrap's brights; the two newest carried the house tokens. All
      eight now use the tokens, and so do eight more Bootstrap brights a
      browser reads as CSS (edit-form highlights, shopping-list headings,
      the lease timeline's bars).

Stands on CR-2. Idempotent. Edits backed up to .bak_housekeep3; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_housekeep3'
MARK = 'HK-3, 28 Oct 2026'
CHECK = False
CREATES = (
    'test_housekeeping_three.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'templates', 'act_expense.html'), [
        (r'''
<!-- JavaScript -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

{# E1, 1 Oct 2026 - Analysis opened onto Loading and stayed there from #}
''',
         r'''
<!-- JavaScript -->

{# E1, 1 Oct 2026 - Analysis opened onto Loading and stayed there from #}
'''),
    ]),
    (os.path.join('pages', 'templates', 'asset_detail.html'), [
        (r'''</style>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</style>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'base.html'), [
        (r'''</style>

  </head>

''',
         r'''</style>

  {# HK-3, 28 Oct 2026 - the one jQuery, Popper and Bootstrap for every page. #}
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/popper.js@1.14.3/dist/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
  </head>

'''),
        (r'''
  <!-- ==================== SCRIPTS ==================== -->
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/popper.js@1.14.3/dist/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>

  <!-- Global help-modal tab-switch scroll reset -->
''',
         r'''
  <!-- ==================== SCRIPTS ==================== -->
  {# HK-3, 28 Oct 2026 - jQuery, Popper and Bootstrap now load once, in <head>, #}
  {# so a page's own scripts can use them and no page loads its own.          #}

  <!-- Global help-modal tab-switch scroll reset -->
'''),
    ]),
    (os.path.join('pages', 'templates', 'customer_list.html'), [
        (r'''    </div>
</div>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''    </div>
</div>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'edit_asset.html'), [
        (r'''</style>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</style>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'finance', 'cashflow_forecast.html'), [
        (r'''{% render_help_modal "cashflow_forecast" %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''{% render_help_modal "cashflow_forecast" %}

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'finance', 'financial_indicators.html'), [
        (r'''<!-- Chart.js Library -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/js/bootstrap.bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
''',
         r'''<!-- Chart.js Library -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance', 'vacancy_management.html'), [
        (r'''<!-- Chart.js Library -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/js/bootstrap.bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
''',
         r'''<!-- Chart.js Library -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_expense_add.html'), [
        (r'''{% endif %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
$(document).ready(function() {
''',
         r'''{% endif %}

<script>
$(document).ready(function() {
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_expense_edit.html'), [
        (r'''{% endif %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
$(document).ready(function() {
''',
         r'''{% endif %}

<script>
$(document).ready(function() {
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_expense_line_types_add.html'), [
        (r'''</form>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
$(document).ready(function() {
''',
         r'''</form>

<script>
$(document).ready(function() {
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_expense_line_types_edit.html'), [
        (r'''{% endif %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
''',
         r'''{% endif %}

<script>
document.addEventListener('DOMContentLoaded', function() {
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_pl_act.html'), [
        (r'''</style>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/js/bootstrap.bundle.min.js"></script>

<script>
''',
         r'''</style>


<script>
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_valuations.html'), [
        (r'''</style>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

{% endblock %}''',
         r'''</style>


{% endblock %}'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_valuations_edit.html'), [
        (r'''</style>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
''',
         r'''</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
'''),
    ]),
    (os.path.join('pages', 'templates', 'fsr.html'), [
        (r'''</div>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</div>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'invoices.html'), [
        (r'''  {% render_help_modal "invoices" %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''  {% render_help_modal "invoices" %}

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_timeline.html'), [
        (r'''        const isExpired = item.end_date && new Date(item.end_date) < today && item.is_active;

        let color;
        if (isExpired) {
            color = '#dc3545';
        } else if (item.is_active) {
            color = '#28a745';
        } else {
            color = '#6c757d';
        }

''',
         r'''        const isExpired = item.end_date && new Date(item.end_date) < today && item.is_active;

        // HK-3, 28 Oct 2026 - the house tokens, not Bootstrap's brights:
        // the colour lands in the bar's style attribute, where var() resolves.
        let color;
        if (isExpired) {
            color = 'var(--alv-bad)';
        } else if (item.is_active) {
            color = 'var(--alv-good)';
        } else {
            color = 'var(--alv-ink-soft)';
        }

'''),
    ]),
    (os.path.join('pages', 'templates', 'notifications.html'), [
        (r'''
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
        (r'''                
                <div class="indicator-cards">
                    <div class="indicator-card ${s.vacantProperties === 0 ? 'success' : 'urgent'}" data-category="vacant">
                        <div class="indicator-icon">
                            <i class="fas fa-home" style="color: ${s.vacantProperties === 0 ? '#28a745' : '#dc3545'};"></i>
                        </div>
                        <div class="indicator-label">Vacant Properties</div>
''',
         r'''                
                <div class="indicator-cards">
                    {# HK-3, 28 Oct 2026 - his eye: the two newest boxes were the   #}
                    {# standard and these six were not. All eight icons now take   #}
                    {# the house tokens their own card borders already use.        #}
                    <div class="indicator-card ${s.vacantProperties === 0 ? 'success' : 'urgent'}" data-category="vacant">
                        <div class="indicator-icon">
                            <i class="fas fa-home" style="color: ${s.vacantProperties === 0 ? 'var(--alv-good)' : 'var(--alv-bad)'};"></i>
                        </div>
                        <div class="indicator-label">Vacant Properties</div>
'''),
        (r'''                    <div class="indicator-card ${s.expiringLeases === 0 ? 'success' : 'warning'}" data-category="expiring">
                        <div class="indicator-icon">
                            <i class="fas fa-calendar-times" style="color: ${s.expiringLeases === 0 ? '#28a745' : '#ffc107'};"></i>
                        </div>
                        <div class="indicator-label">Expiring Leases</div>
''',
         r'''                    <div class="indicator-card ${s.expiringLeases === 0 ? 'success' : 'warning'}" data-category="expiring">
                        <div class="indicator-icon">
                            <i class="fas fa-calendar-times" style="color: ${s.expiringLeases === 0 ? 'var(--alv-good)' : 'var(--alv-warn)'};"></i>
                        </div>
                        <div class="indicator-label">Expiring Leases</div>
'''),
        (r'''                    <div class="indicator-card ${s.declinedRenewals === 0 ? 'success' : 'urgent'}" data-category="declined">
                        <div class="indicator-icon">
                            <i class="fas fa-times-circle" style="color: ${s.declinedRenewals === 0 ? '#28a745' : '#dc3545'};"></i>
                        </div>
                        <div class="indicator-label">Declined Renewals</div>
''',
         r'''                    <div class="indicator-card ${s.declinedRenewals === 0 ? 'success' : 'urgent'}" data-category="declined">
                        <div class="indicator-icon">
                            <i class="fas fa-times-circle" style="color: ${s.declinedRenewals === 0 ? 'var(--alv-good)' : 'var(--alv-bad)'};"></i>
                        </div>
                        <div class="indicator-label">Declined Renewals</div>
'''),
        (r'''                    <div class="indicator-card ${s.overdueInvoices === 0 ? 'success' : 'urgent'}" data-category="overdue">
                        <div class="indicator-icon">
                            <i class="fas fa-exclamation-triangle" style="color: ${s.overdueInvoices === 0 ? '#28a745' : '#dc3545'};"></i>
                        </div>
                        <div class="indicator-label">Overdue Invoices</div>
''',
         r'''                    <div class="indicator-card ${s.overdueInvoices === 0 ? 'success' : 'urgent'}" data-category="overdue">
                        <div class="indicator-icon">
                            <i class="fas fa-exclamation-triangle" style="color: ${s.overdueInvoices === 0 ? 'var(--alv-good)' : 'var(--alv-bad)'};"></i>
                        </div>
                        <div class="indicator-label">Overdue Invoices</div>
'''),
        (r'''                    <div class="indicator-card ${s.expensesWaitingApproval === 0 ? 'success' : 'warning'}" data-category="approval">
                        <div class="indicator-icon">
                            <i class="fas fa-clipboard-check" style="color: ${s.expensesWaitingApproval === 0 ? '#28a745' : '#ffc107'};"></i>
                        </div>
                        <div class="indicator-label">Expenses Waiting for Approval</div>
''',
         r'''                    <div class="indicator-card ${s.expensesWaitingApproval === 0 ? 'success' : 'warning'}" data-category="approval">
                        <div class="indicator-icon">
                            <i class="fas fa-clipboard-check" style="color: ${s.expensesWaitingApproval === 0 ? 'var(--alv-good)' : 'var(--alv-warn)'};"></i>
                        </div>
                        <div class="indicator-label">Expenses Waiting for Approval</div>
'''),
        (r'''                    <div class="indicator-card ${s.expensesWaitingPayment === 0 ? 'success' : 'warning'}" data-category="payment">
                        <div class="indicator-icon">
                            <i class="fas fa-credit-card" style="color: ${s.expensesWaitingPayment === 0 ? '#28a745' : '#0e7c8b'};"></i>
                        </div>
                        <div class="indicator-label">Expenses Waiting for Payment</div>
''',
         r'''                    <div class="indicator-card ${s.expensesWaitingPayment === 0 ? 'success' : 'warning'}" data-category="payment">
                        <div class="indicator-icon">
                            <i class="fas fa-credit-card" style="color: ${s.expensesWaitingPayment === 0 ? 'var(--alv-good)' : 'var(--alv-accent)'};"></i>
                        </div>
                        <div class="indicator-label">Expenses Waiting for Payment</div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'physical_invoice_list.html'), [
        (r'''</body>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</body>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_gantt.html'), [
        (r'''<link rel="stylesheet" href="https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.css">
<script src="https://export.dhtmlx.com/gantt/api.js"></script>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''<link rel="stylesheet" href="https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.css">
<script src="https://export.dhtmlx.com/gantt/api.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_subtasks_add.html'), [
        (r'''</form>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</form>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_task_list.html'), [
        (r'''</body>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
''',
         r'''</body>

<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_tasks_add.html'), [
        (r'''</form>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</form>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_tasks_delete.html'), [
        (r'''</div>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</div>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'project_tasks_edit.html'), [
        (r'''</form>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</form>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
        (r'''        const targetField = $('#' + targetFieldId);
        const originalBorder = targetField.css('border-color');
        targetField.css('border-color', '#ffc107');

        fetch('/translate/', {
''',
         r'''        const targetField = $('#' + targetFieldId);
        const originalBorder = targetField.css('border-color');
        targetField.css('border-color', 'var(--alv-warn)');

        fetch('/translate/', {
'''),
        (r'''            if (data.success) {
                targetField.val(data.translated_text);
                targetField.css('border-color', '#28a745');
                setTimeout(() => targetField.css('border-color', originalBorder), 2000);
                showAutoTranslationNotice(`${fieldName} automatically updated in Greek`);
''',
         r'''            if (data.success) {
                targetField.val(data.translated_text);
                targetField.css('border-color', 'var(--alv-good)');
                setTimeout(() => targetField.css('border-color', originalBorder), 2000);
                showAutoTranslationNotice(`${fieldName} automatically updated in Greek`);
'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'projects.html'), [
        (r'''{% render_help_modal "projects" %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''{% render_help_modal "projects" %}

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'projects_add.html'), [
        (r'''</form>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</form>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'projects_detail.html'), [
        (r'''</div>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</div>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'projects_edit.html'), [
        (r'''{% endwith %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''{% endwith %}

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
        (r'''        const targetField = $('#' + targetFieldId);
        const originalBorder = targetField.css('border-color');
        targetField.css('border-color', '#ffc107');

        fetch('/translate/', {
''',
         r'''        const targetField = $('#' + targetFieldId);
        const originalBorder = targetField.css('border-color');
        targetField.css('border-color', 'var(--alv-warn)');

        fetch('/translate/', {
'''),
        (r'''            if (data.success) {
                targetField.val(data.translated_text);
                targetField.css('border-color', '#28a745');
                setTimeout(() => { targetField.css('border-color', originalBorder); }, 2000);
                showAutoTranslationNotice(`${fieldName} automatically updated in Greek`);
''',
         r'''            if (data.success) {
                targetField.val(data.translated_text);
                targetField.css('border-color', 'var(--alv-good)');
                setTimeout(() => { targetField.css('border-color', originalBorder); }, 2000);
                showAutoTranslationNotice(`${fieldName} automatically updated in Greek`);
'''),
    ]),
    (os.path.join('pages', 'templates', 'properties.html'), [
        (r'''</body>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</body>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'property_assets.html'), [
        (r'''</style>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</style>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'property_detail.html'), [
        (r'''{% endif %}

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
''',
         r'''{% endif %}

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant.html'), [
        (r'''</body>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

''',
         r'''</body>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_add.html'), [
        (r'''
<!-- Required JavaScript -->
<script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
$(document).ready(function() {
''',
         r'''
<!-- Required JavaScript -->
<script>
$(document).ready(function() {
'''),
    ]),
    (os.path.join('pages', 'templates', 'view_recipe.html'), [
        (r'''        if (ing.group && ing.group !== currentGroup) {
            const groupHeader = document.createElement('div');
            groupHeader.style.cssText = 'font-weight: 600; color: #28a745; margin-top: 20px; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 2px solid #e0e0e0;';
            groupHeader.textContent = ing.group;
            container.appendChild(groupHeader);
''',
         r'''        if (ing.group && ing.group !== currentGroup) {
            const groupHeader = document.createElement('div');
            groupHeader.style.cssText = 'font-weight: 600; color: var(--alv-good); margin-top: 20px; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 2px solid #e0e0e0;';
            groupHeader.textContent = ing.group;
            container.appendChild(groupHeader);
'''),
        (r'''        const emptyMsg = document.createElement('p');
        emptyMsg.textContent = '✅ You have all ingredients!';
        emptyMsg.style.cssText = 'font-style: italic; color: #28a745; font-size: 16px; text-align: center; padding: 20px;';
        container.appendChild(emptyMsg);
        return;
''',
         r'''        const emptyMsg = document.createElement('p');
        emptyMsg.textContent = '✅ You have all ingredients!';
        emptyMsg.style.cssText = 'font-style: italic; color: var(--alv-good); font-size: 16px; text-align: center; padding: 20px;';
        container.appendChild(emptyMsg);
        return;
'''),
    ]),
    (os.path.join('test_amber.py'), [
        (r'''
EXPECT_PAGES = 23
EXPECT_REFUSED = 10
WARN, SOFT, INK, LINE = ('--alv-warn', '--alv-warn-soft',
                         '--alv-warn-ink', '--alv-warn-line')
''',
         r'''
EXPECT_PAGES = 23
EXPECT_REFUSED = 6   # HK-3, 28 Oct 2026 - four were Notifications icons and edit-form borders a later round read by eye and took to var(--alv-warn); the round this suite judges still refused them   # (was 10)
WARN, SOFT, INK, LINE = ('--alv-warn', '--alv-warn-soft',
                         '--alv-warn-ink', '--alv-warn-line')
'''),
    ]),
    (os.path.join('test_cssrules_outside.py'), [
        (r'''#   not move, because this round converted only var-safe ones.
MARKUP_STYLE = 80      # colour literals in inline style= attributes   # VR-1, 21 Oct 2026 - the cooking schedule readout on view_recipe held six: a slate heading, a hot pink icon and four copies of a hand-mixed 7 per cent black hairline. All six are tokens now, measured at dE 8.31, 45.73 and 1.75.   # (was 86)   # RT-1, 18 Oct 2026 - one was on a meal-plan screen MN-1 retired   # (was 87)   # PH-2, 14 Oct 2026 - pantry_staples' 92 staple chips carried #f0fff4 inline; they carry var(--alv-good-soft) now, and that page has no hex literal left at all.   # (was 88)
SCRIPT = 146            # colour literals inside <script> bodies   # RT-1, 18 Oct 2026 - two were in the scripts of meal-plan screens MN-1 retired   # (was 148)   # VC-1, 14 Oct 2026 - create_meal_plan's Favourites toggle no longer writes #e74c3c from JavaScript; it carries aria-pressed and base paints it.   # (was 149)
PRES = 0                # HTML presentation attributes carrying a colour
PAGES = 33              # real pages carrying any of them   # RT-1, 18 Oct 2026 - two of them were meal-plan screens MN-1 retired   # (was 35)   # PH-2 - and it was pantry_staples' ONLY one, so the page leaves this census   # (was 36)
STANDALONE = 26         # on the twelve exempt templates - correct, and staying
CTX = {'style-attr': 20, 'style-prop': 8, 'css-text': 0,   # RT-1, 18 Oct 2026 - two style-attr writes were in the scripts of meal-plan screens MN-1 retired   # (style-attr was 22)   # VC-1 - the hex above was a style-prop write, the var-safe kind   # (style-prop was 9)
       'canvas': 27, 'unknown': 91}

passed = failed = skipped = 0
''',
         r'''#   not move, because this round converted only var-safe ones.
MARKUP_STYLE = 80      # colour literals in inline style= attributes   # VR-1, 21 Oct 2026 - the cooking schedule readout on view_recipe held six: a slate heading, a hot pink icon and four copies of a hand-mixed 7 per cent black hairline. All six are tokens now, measured at dE 8.31, 45.73 and 1.75.   # (was 86)   # RT-1, 18 Oct 2026 - one was on a meal-plan screen MN-1 retired   # (was 87)   # PH-2, 14 Oct 2026 - pantry_staples' 92 staple chips carried #f0fff4 inline; they carry var(--alv-good-soft) now, and that page has no hex literal left at all.   # (was 88)
SCRIPT = 125            # colour literals inside <script> bodies   # HK-3, 28 Oct 2026 - 21 Bootstrap brights in style strings a browser reads as CSS took the house tokens: twelve on the Notifications icons (in ${} ternaries, which the classifier reads as unknown), four edit-form borders, two shopping-list headings, three lease-timeline bars   # (was 146)   # RT-1, 18 Oct 2026 - two were in the scripts of meal-plan screens MN-1 retired   # (was 148)   # VC-1, 14 Oct 2026 - create_meal_plan's Favourites toggle no longer writes #e74c3c from JavaScript; it carries aria-pressed and base paints it.   # (was 149)
PRES = 0                # HTML presentation attributes carrying a colour
PAGES = 32              # real pages carrying any of them   # HK-3, 28 Oct 2026 - Notifications carried none but those twelve   # (was 33)   # RT-1, 18 Oct 2026 - two of them were meal-plan screens MN-1 retired   # (was 35)   # PH-2 - and it was pantry_staples' ONLY one, so the page leaves this census   # (was 36)
STANDALONE = 26         # on the twelve exempt templates - correct, and staying
CTX = {'style-attr': 20, 'style-prop': 8, 'css-text': 0,   # RT-1, 18 Oct 2026 - two style-attr writes were in the scripts of meal-plan screens MN-1 retired   # (style-attr was 22)   # VC-1 - the hex above was a style-prop write, the var-safe kind   # (style-prop was 9)
       'canvas': 27, 'unknown': 70}   # HK-3, 28 Oct 2026 - the 21 in SCRIPT's note were all unknown to the classifier: a ${} ternary inside a style string, a jQuery .css() and a cssText with a ; before the colour. Read by eye, every one lands in the DOM as CSS   # (unknown was 91)

passed = failed = skipped = 0
'''),
        (r'''# safe half falls by two and the 118 that may NOT become var() does
# not move at all - which is the half this round is about.
ok(safe == 28,
   '28 of the 146 may become var() - and 118 may not, which is '
   'the whole reason this round exists. B-7 took 52 of the safe '
   'ones on 9 Oct 2026 and not one of the 118: a colour handed '
   'to a chart library as DATA is painted onto a canvas with '
   'no CSS step, so var() there is a meaningless string. That '
   'is why canvas and unknown did not move.', safe)


''',
         r'''# safe half falls by two and the 118 that may NOT become var() does
# not move at all - which is the half this round is about.
# HK-3, 28 Oct 2026 - 28 OF 125: the safe half did not move; 21 of
# the unknowns were read by eye, found to be CSS, and converted.
ok(safe == 28,
   '28 of the 125 may become var() - and 97 may not, which is '
   'the whole reason this round exists. B-7 took 52 of the safe '
   'ones on 9 Oct 2026 and not one of the 118: a colour handed '
   'to a chart library as DATA is painted onto a canvas with '
   'no CSS step, so var() there is a meaningless string. That '
   'is why canvas did not move, and unknown moved only by hand.', safe)


'''),
    ]),
    (os.path.join('test_customer_view.py'), [
        (r'''       '  writing the title with textContent, because a customer name is '
       'data somebody typed')
ok('code.jquery.com/jquery-3.6.0' in NOW,
   'jQuery really is on the page, so window.jQuery is not a hope')

''',
         r'''       '  writing the title with textContent, because a customer name is '
       'data somebody typed')
# HK-3, 28 Oct 2026 - the page no longer loads its own copy; base.html
# loads the one jQuery in <head>, ahead of every page's scripts.
_bsrc = read(alv_tree.path_of('base.html'))
ok(0 <= _bsrc.find('code.jquery.com/jquery-3.6.0') < _bsrc.find('</head>'),
   'jQuery really is on the page, so window.jQuery is not a hope')

'''),
    ]),
    (os.path.join('test_dr2_values.py'), [
        (r'''                                   if os.path.exists(exe) else {}))

        def computed(page_css, width, klass, props):
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style></head>'
                '<body style="margin:0"><div class="mobile-action-bar '
                'alv-table"><table class="alv-table"><tbody><tr>'
                '<td class="%s" id="probe">x</td></tr></tbody></table>'
                '</div></body></html>'
                % (read(BOOTF), bcss, page_css, klass))
            r = pg.evaluate(
                '(ps) => { const e = document.getElementById("probe");'
                ' const s = getComputedStyle(e); const o = {};'
                ' for (const p of ps) o[p] = s.getPropertyValue(p);'
                ' return o; }', props)
            pg.close()
            return r

        drifted, moved, painted = [], 0, 0
        for page in PAGES:
            p = alv_tree.last_path(page)
            a_css, b_css = css_of(was(p)), css_of(now(p))
            mine = [d for d in PLAIN if d[0] == page]
            klasses = {}
            for _p, sel, prop, _w in mine:
                klasses.setdefault(sel.split('&& ')[-1].lstrip('.'),
                                   []).append(prop)
            for klass, props in sorted(klasses.items()):
                for w in (320, 390, 768, 1280):
                    before = computed(a_css, w, klass, props)
                    after = computed(b_css, w, klass, props)
                    pure = computed('', w, klass, props)
                    painted += 1
                    for prop in props:
''',
         r'''                                   if os.path.exists(exe) else {}))

        # HK-3, 28 Oct 2026 - GATE SPEED. This was the gate's second
        # slowest suite (182s in a pool of three): three fresh pages, each
        # parsing Bootstrap and base.html, for every class at every width.
        # Now a document carries ALL of a page's classes, each in its own
        # bar-table-cell scaffold exactly as before (a separate table, so
        # no cell sizes another), and is loaded once and RESIZED through
        # the four widths. Base alone is one document for every class of
        # every page. The same properties are read from the same
        # scaffolds; the "really moved" CONTROL still has to see a change.
        #
        # THE INTEGERS ARE THE OLD ONES IN THE OLD ORDER, because
        # test_retired holds this suite to every integer it had - which
        # is why the code below is laid out the way it is.
        def computed_all(page_css, klasses):
            """{(klass, width): {prop: value}} for every klass."""
            H = 900
            ks = sorted(klasses)
            cells = ''.join(
                '<div class="mobile-action-bar alv-table"><table '
                'class="alv-table"><tbody><tr><td class="%s" '
                'id="probe%d">x</td></tr></tbody></table></div>' % (k, i)
                for i, k in enumerate(ks))
            pg = br.new_page(viewport={'width': min(WIDTHS), 'height': H})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style></head>'
                '<body style="margin:0">%s</body></html>'
                % (read(BOOTF), bcss, page_css, cells))
            out = {}
            for w in WIDTHS:
                pg.set_viewport_size({'width': w, 'height': H})
                got = pg.evaluate(
                    '(job) => job.map(([i, ps]) => {'
                    ' const s = getComputedStyle('
                    'document.getElementById("probe" + i)); const o = {};'
                    ' for (const p of ps) o[p] = s.getPropertyValue(p);'
                    ' return o; })',
                    [[i, sorted(set(klasses[k]))] for i, k in enumerate(ks)])
                for k, o in zip(ks, got):
                    out[(k, w)] = o
            pg.close()
            return out

        drifted, moved, painted = [], 0, 0

        def klasses_of(page):
            """{klass: [prop, ...]} - the page's PLAIN drops, by class."""
            klasses = {}
            for _p, sel, prop, _w in [d for d in PLAIN if d[0] == page]:
                klasses.setdefault(sel.split('&& ')[-1].lstrip('.'),
                                   []).append(prop)
            return klasses

        WIDTHS = (320, 390, 768, 1280)
        every = {}
        for page in PAGES:
            for k, ps in klasses_of(page).items():
                every.setdefault(k, []).extend(ps)
        PURE = computed_all('', every)

        for page in PAGES:
            p = alv_tree.last_path(page)
            a_css, b_css = css_of(was(p)), css_of(now(p))
            klasses = klasses_of(page)
            BEFORE = computed_all(a_css, klasses)
            AFTER = computed_all(b_css, klasses)
            for klass, props in sorted(klasses.items()):
                for w in WIDTHS:
                    before = BEFORE[(klass, w)]
                    after = AFTER[(klass, w)]
                    pure = PURE[(klass, w)]
                    painted += 1
                    for prop in props:
'''),
    ]),
    (os.path.join('test_neutrals.py'), [
        (r'''# VR-1, 21 Oct 2026 - MARKUP_STYLE was 86 and the cooking schedule
# readout gave up six of them.
for want in ('MARKUP_STYLE = 80', 'SCRIPT = 146', 'PAGES = 33',
             "'style-attr': 20", "'style-prop': 8",
             'safe == 28'):
    ok(want in cr, '  CR-1 census now reads %s' % want)
ok("'canvas': 27" in cr and "'unknown': 91" in cr,
   '  and canvas 27 / unknown 91 did NOT move - 201 - 83 = 118 = 27 + 91, '
   'which is the arithmetic saying every refusal was honoured')

print('')
''',
         r'''# VR-1, 21 Oct 2026 - MARKUP_STYLE was 86 and the cooking schedule
# readout gave up six of them.
# HK-3, 28 Oct 2026 - SCRIPT 146 -> 125 and PAGES 33 -> 32, unknown
# 91 -> 70: 21 Bootstrap brights the classifier could not read, read by
# eye and taken to tokens. canvas did not move.
for want in ('MARKUP_STYLE = 80', 'SCRIPT = 125', 'PAGES = 32',
             "'style-attr': 20", "'style-prop': 8",
             'safe == 28'):
    ok(want in cr, '  CR-1 census now reads %s' % want)
ok("'canvas': 27" in cr and "'unknown': 70" in cr,
   '  and canvas 27 did NOT move; unknown is 70 because HK-3 read 21 of '
   'the 91 by eye - every automatic refusal was honoured')

print('')
'''),
    ]),
    (os.path.join('test_pdf_viewer.py'), [
        (r'''N_INCLUDERS = 13
N_HANDROLLED = 0
N_DUP_JQUERY = 33   # MD-1, 18 Oct 2026 - E31 took meal_plan_calendar's second copy out; base already loads the same file from the same CDN   # (was 34)
CONVERTED_NOW, ALIAS_NOW = 79, 69

''',
         r'''N_INCLUDERS = 13
N_HANDROLLED = 0
N_DUP_JQUERY = 0   # HK-3, 28 Oct 2026 - base loads jQuery once, in <head>, and every page's own copy is gone   # (was 33)
CONVERTED_NOW, ALIAS_NOW = 79, 69

'''),
    ]),
    (os.path.join('test_print_queries.py'), [
        (r'''    n = [0]

    def load(br, html, w, h, media):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_pq_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': h})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        pg.emulate_media(media=media)
        _goto(pg, fx)
        return ctx, pg

    def probe(br, styles, probes, media):
        got = {}
        for w, h in sorted(set((p[1], p[2]) for p in probes)):
            names = [p[0] for p in probes if (p[1], p[2]) == (w, h)]
            ctx, pg = load(br, fixture(boot, base_css, styles), w, h, media)
            for nm, v in zip(names, pg.evaluate(PROBE_JS, names)):
                got[nm] = v == '1'
            ctx.close()
        return got

''',
         r'''    n = [0]

    # HK-3, 28 Oct 2026 - GATE SPEED. This suite was the slowest on the
    # gate (215s in a pool of three): every measurement opened a new
    # browser context, a new page and a fresh parse of Bootstrap and
    # base.html. Now there is ONE page per media for the whole run - each
    # fixture is still a fresh navigation, so no document outlives its
    # measurement - and a fixture probed at several sizes is loaded once
    # and RESIZED, which is what a media query answers to. The verdicts
    # are the same ones; the CONTROLS below still have to see a leak and
    # a move, so a reuse that blinded the probe would fail them.
    pages_ = {}

    class _Kept(object):
        def close(self):
            pass

    def load(br, html, w, h, media):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_pq_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        pg = pages_.get(media)
        if pg is None:
            ctx = br.new_context(viewport={'width': w, 'height': h})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            pg.emulate_media(media=media)
            pages_[media] = pg
        else:
            pg.set_viewport_size({'width': w, 'height': h})
        _goto(pg, fx)
        return _Kept(), pg

    def probe(br, styles, probes, media):
        got = {}
        sizes = sorted(set((p[1], p[2]) for p in probes))
        if not sizes:
            return got
        ctx, pg = load(br, fixture(boot, base_css, styles),
                       sizes[0][0], sizes[0][1], media)
        for w, h in sizes:
            names = [p[0] for p in probes if (p[1], p[2]) == (w, h)]
            pg.set_viewport_size({'width': w, 'height': h})
            for nm, v in zip(names, pg.evaluate(PROBE_JS, names)):
                got[nm] = v == '1'
        return got

'''),
    ]),
    (os.path.join('test_prorata_anchor.py'), [
        (r'''        # A base that carries the blocks and nothing else. The page under
        # test supplies its own <style> and <script>.
        f.write('<!doctype html><html><head><title>'
                '{% block title %}{% endblock %}</title></head><body>'
                '{% block content %}{% endblock %}</body></html>')

''',
         r'''        # A base that carries the blocks and nothing else. The page under
        # test supplies its own <style> and <script>.
        # HK-3, 28 Oct 2026 - AND jQUERY, IN <head>, as the real base now
        # loads it: the page stopped loading its own copy, so a stub
        # without one would leave the harness nothing to swap for the
        # local file and the page's script nothing to run on.
        f.write('<!doctype html><html><head><title>'
                '{% block title %}{% endblock %}</title>'
                '<script src="https://code.jquery.com/jquery-3.6.0.min.js">'
                '</script></head><body>'
                '{% block content %}{% endblock %}</body></html>')

'''),
    ]),
    (os.path.join('test_recipe_tidy.py'), [
        (r'''# NOTHING ELSE ON THE PAGE MOVED. This round touched one table.
oldlits = sorted(re.findall(r'#[0-9a-fA-F]{3,6}\b', T.code_only(BEFORE)))
newlits = sorted(re.findall(r'#[0-9a-fA-F]{3,6}\b', CODE))
ok(len(oldlits) - len(newlits) == 2,
   'exactly TWO hex literals left the page - %d before, %d after. This '
''',
         r'''# NOTHING ELSE ON THE PAGE MOVED. This round touched one table.
oldlits = sorted(re.findall(r'#[0-9a-fA-F]{3,6}\b', T.code_only(BEFORE)))
# HK-3, 28 Oct 2026 - AS THIS ROUND LEFT THE PAGE. A later round took
# two shopping-list greens to tokens, and "nothing else moved" is a claim
# about this round's edit, not about every edit since.
from alv_rounds import as_left_by as _alb                 # noqa: E402
newlits = sorted(re.findall(r'#[0-9a-fA-F]{3,6}\b',
                            T.code_only(_alb(TPL, SUFFIX, read))))
ok(len(oldlits) - len(newlits) == 2,
   'exactly TWO hex literals left the page - %d before, %d after. This '
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('HK-3 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_housekeeping_three.py'" in read(pq):
        print('HK-3 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_receipt_email.py'" not in read(pq):
        refuse('CR-2 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_receipt_email.py'
)""", """    'test_receipt_email.py',
    # HK-3, 28 Oct 2026 - one jQuery, a faster gate, the house colours.
    'test_housekeeping_three.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/views/receipts.py'; Text = 'def cash_receipt_send(';""",
        """    @{ File = 'pages/templates/tenant_add.html'; Text = 'code.jquery.com/jquery-3.5.1'; Absent = $true; What = 'HK-3: base loads the one jQuery in head - a page that brings its own back puts two on the page, and this was the one on an older version' },
    @{ File = 'pages/views/receipts.py'; Text = 'def cash_receipt_send(';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_receipt_email.py',
]""", """    'test_receipt_email.py',
    # HK-3, 28 Oct 2026 - one jQuery, a faster gate, the house colours.
    'test_housekeeping_three.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_receiptemail',
]""", """    '.bak_receiptemail',
    # HK-3, 28 Oct 2026 - one jQuery, a faster gate, the house colours.
    '.bak_housekeep3',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # HK-3, 28 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    b = out[os.path.join(root, 'pages', 'templates', 'base.html')]
    hd = b[:b.find('</head>')]
    if b.count('code.jquery.com/jquery-') != 1 or 'code.jquery.com' not in hd:
        refuse('base.html must load jQuery exactly once, in <head>.')
    for k, val in out.items():
        if (k.endswith('.html') and not k.endswith('base.html')
                and 'code.jquery.com/jquery-' in val):
            refuse('%s still loads its own jQuery.' % os.path.relpath(k, root))

    if CHECK:
        print('HK-3 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('HK-3 applied - one jQuery and one Bootstrap, in base <head>; '
          'two slow suites resize instead of reloading; the Notifications '
          'icons and eight more Bootstrap brights take the house tokens.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
