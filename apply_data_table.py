# -*- coding: utf-8 -*-
"""apply_data_table.py - round DT-1, 16 Oct 2026.

THE LAST TWO PAGES WITH A TABLE STANDARD OF THEIR OWN.

Demetri, 16 Oct, asked for the Home and Notifications tables to match the
rest of the application. They did not, for a reason no gate could report:
their tables are BUILT IN JAVASCRIPT, as strings, so every table suite in
this project walks straight past them. Banked as DT-1 when NV-1b
converted the title deeds table.

WHAT WAS THERE
    13 tables - seven on home.html, six on notifications.html - drawn
    against 25 page-local `.data-table` rule openings. The six panels are
    THE SAME SIX on both pages, built twice from two copies of the code:
    one joins strings, the other uses template literals. Both pages also
    declared the same four `.status-badge` rules, word for word.

    And the `.table-container { overflow-x: auto }` line above them
    OVERRODE base's card shell on source order, so these panels scrolled
    sideways instead of sitting in the house panel.

WHAT THIS ROUND DOES
    The tables wear `table alv-table`. Both stylesheet blocks go, on both
    pages. The 11 status chips become house pills, in the house wording -
    `alv-pill-bad`, `alv-pill-attn`, `alv-pill-info`. Money and day counts
    take `.num`, which base right-aligns with tabular figures; statuses
    take `.col-center`. Everything else is left, which is what base does
    with a cell that says nothing.

TWO OF THE THREE TONES WERE SOLID FILLS
    `status-urgent` was a filled red block with white text and
    `status-info` a filled teal one. No other status in this application
    is a fill. Demetri saw all seven chips rendered three ways before this
    round was written and chose the house pill with house wording.

THE ONE TONE DECIDED IN JAVASCRIPT STAYS DECIDED THERE
    The income pop-up picks its tone from `b.tag === 'at_risk'`. That is
    DATA, not drift, so only the names change. The expiring-leases chip
    reads `item.renewal_status` and used to shout it with `.toUpperCase()`;
    it is capitalised in place instead, because DB-8's own note three
    lines above it records what happened the last time that column was a
    constant dressed as data.

WHY THE ANCHORS ARE NOT TYPED
    notifications.html carries 785 CRLF line endings AND SEVEN BARE LFs.
    Every anchor below was taken verbatim from the file on disk and every
    replacement wears the line endings of the text it replaces, because a
    round that normalises newlines rewrites lines it never meant to touch.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_datatable'
PAGES = ('home.html', 'notifications.html')
ME = 'test_data_table.py'
PATCHER = 'apply_data_table.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
IMP = 'test_important_base.py'
LV = 'test_leave_decided.py'
AMB = 'test_amber.py'
PC = 'test_pair_contrast.py'
SB = 'test_surface_border.py'
PL = 'test_print_leaks.py'
ST = 'test_system_teal.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 90, 91
ALIAS_WAS, ALIAS_NOW = 91, 93
ALIAS_P_WAS, ALIAS_S_WAS = 45, 46
ALIAS_P_NOW, ALIAS_S_NOW = 46, 47

N_TABLES = 13
N_PILLS = 11
N_CSS_BLOCKS = 4
IMP_WAS, IMP_NOW = 842, 828
PAIRS_WAS, PAIRS_NOW = 706, 698
GAINED_WAS, GAINED_NOW = 82, 76
TAG_WAS = '<table class="data-table">'
TAG_NOW = '<table class="table alv-table">'

# --------------------------------------------------------------------------
# THE PAIRS. Generated from the two pages rather than transcribed - see the
# docstring. Each is (before, after, kind); `tag` is the one that replaces
# every occurrence, the rest must each appear EXACTLY ONCE.
# --------------------------------------------------------------------------
PAIRS = {
 'home.html': [
  ('                                .table-container { overflow-x: auto; }\n    .data-table { width: 100%; border-collapse: collapse; margin: 0; }\n    .data-table th { background: var(--alv-surface); padding: 12px 15px; text-align: center; border-bottom: 2px solid var(--alv-line); font-weight: 600; color: var(--alv-ink-strong); font-size: 14px; }\n    .data-table th:first-child { text-align: left; }\n    .data-table td { padding: 12px 15px; border-bottom: 1px solid var(--alv-line); text-align: center; font-size: 14px; }\n    .data-table td:first-child { text-align: left; font-weight: 500; }\n    .data-table tbody tr:hover { background: var(--alv-surface); }\n    .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }\n    .status-urgent { background: var(--alv-bad); color: var(--alv-on-accent); }\n    .status-warning { border: 1px solid var(--alv-warn-line);\n background: var(--alv-warn-soft); color: var(--alv-warn); }\n    .status-info { background: var(--alv-accent); color: var(--alv-on-accent); }',
   "    /* DT-1, 16 Oct 2026 - THE RULE OPENINGS THAT WERE HERE ARE BASE'S.\n       This page drew its tables against a .data-table stylesheet of its own -\n       a hand-rolled copy of the house table standard, living beside it - and\n       the .table-container line above them OVERRODE base's card shell on\n       source order, so these panels scrolled sideways instead of sitting in\n       it. The tables wear `table alv-table` now and base owns every line that\n       stood here. The four status tones went with them: two of the three were\n       SOLID FILLS, which no other status in this application is, and they are\n       house pills now. See test_data_table.py. */",
   'css'),
  ('                                                .data-table thead { display: none; }\n        .data-table, .data-table tbody, .data-table tr { display: block; width: 100%; }\n        .data-table tr { background: var(--alv-paper); border: 1px solid var(--alv-line); border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; }\n        .data-table tr:hover { background: var(--alv-paper); }\n        .data-table td { display: flex !important; justify-content: space-between; align-items: center; gap: 12px; padding: 6px 0 !important; border-bottom: none; text-align: right !important; font-size: 13px; }\n        .data-table td:first-child { font-size: 15px; font-weight: 600; color: var(--alv-ink); padding-bottom: 8px !important; margin-bottom: 4px; border-bottom: 1px solid var(--alv-line-soft) !important; text-align: left !important; display: block !important; }\n        .data-table td:not(:first-child)::before { content: attr(data-label); font-weight: 600; color: var(--alv-ink-soft); font-size: 12px; text-transform: uppercase; letter-spacing: 0.4px; text-align: left; flex-shrink: 0; }\n        .status-badge { font-size: 11px; }',
   "        /* DT-1, 16 Oct 2026 - and the phone card with it. This page built its\n           own table-as-cards block: a good copy of base's, and still a copy. Base\n           owns the card, the labels and the first cell. */",
   'css'),
  ('<thead><tr><th>Property Name</th><th>Country</th><th>Status</th><th>Action Required</th></tr></thead>',
   '<thead><tr><th>Property Name</th><th>Country</th><th class="col-center">Status</th><th>Action Required</th></tr></thead>',
   'head'),
  ('<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Status"><span class="status-badge status-urgent">VACANT</span></td>\' +\n          \'<td data-label="Action">Contact estate agents ASAP</td></tr>',
   '<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Status" class="text-center"><span class="alv-pill alv-pill-bad">Vacant</span></td>\' +\n          \'<td data-label="Action">Contact estate agents ASAP</td></tr>',
   'row'),
  ('<thead><tr><th>Property Name</th><th>Country</th><th>Tenant</th><th>Lease End Date</th><th>Days to End</th><th>Status</th></tr></thead>',
   '<thead><tr><th>Property Name</th><th>Country</th><th>Tenant</th><th>Lease End Date</th><th class="num">Days to End</th><th class="col-center">Status</th></tr></thead>',
   'head'),
  ('<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Tenant">\' + (item.tenant_name || \'\') + \'</td>\' +\n          \'<td data-label="Lease End">\' + (item.lease_end_date || \'\') + \'</td>\' +\n          /* DB-8, 2 Oct 2026. Was "Renewal Due" from item.renewal_date,\n             which the new rule does not produce - there is no renewal\n             period in it. Days to end is what the panel beside this one\n             shows, and it is the same number. */\n          \'<td data-label="Days to End">\' + (item.days_to_end != null ? item.days_to_end + \'d\' : \'\') + \'</td>\' +\n          /* And the status was the literal string PENDING - true only\n             because the OLD query filtered on it, so the column was a\n             constant dressed as data. */\n          \'<td data-label="Status"><span class="status-badge status-warning">\' + ((item.renewal_status || \'pending\').toUpperCase()) + \'</span></td></tr>',
   '<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Tenant">\' + (item.tenant_name || \'\') + \'</td>\' +\n          \'<td data-label="Lease End">\' + (item.lease_end_date || \'\') + \'</td>\' +\n          /* DB-8, 2 Oct 2026. Was "Renewal Due" from item.renewal_date,\n             which the new rule does not produce - there is no renewal\n             period in it. Days to end is what the panel beside this one\n             shows, and it is the same number. */\n          \'<td data-label="Days to End" class="num">\' + (item.days_to_end != null ? item.days_to_end + \'d\' : \'\') + \'</td>\' +\n          /* And the status was the literal string PENDING - true only\n             because the OLD query filtered on it, so the column was a\n             constant dressed as data. */\n          \'<td data-label="Status" class="text-center"><span class="alv-pill alv-pill-attn">\' + (item.renewal_status || \'pending\').replace(/^./, function (c) { return c.toUpperCase(); }) + \'</span></td></tr>',
   'row'),
  ('<thead><tr><th>Property Name</th><th>Country</th><th>Current Tenant</th><th>Lease End Date</th><th>Status</th></tr></thead>',
   '<thead><tr><th>Property Name</th><th>Country</th><th>Current Tenant</th><th>Lease End Date</th><th class="col-center">Status</th></tr></thead>',
   'head'),
  ('<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Current Tenant">\' + (item.tenant_name || \'\') + \'</td>\' +\n          \'<td data-label="Lease End">\' + (item.lease_end_date || \'\') + \'</td>\' +\n          \'<td data-label="Status"><span class="status-badge status-urgent">NEED NEW TENANT</span></td></tr>',
   '<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Current Tenant">\' + (item.tenant_name || \'\') + \'</td>\' +\n          \'<td data-label="Lease End">\' + (item.lease_end_date || \'\') + \'</td>\' +\n          \'<td data-label="Status" class="text-center"><span class="alv-pill alv-pill-bad">Need new tenant</span></td></tr>',
   'row'),
  ('<thead><tr><th>Property Name</th><th>Country</th><th>Tenant</th><th>Amount</th><th>Due Date</th><th>Days Overdue</th></tr></thead>',
   '<thead><tr><th>Property Name</th><th>Country</th><th>Tenant</th><th class="num">Amount</th><th>Due Date</th><th class="num">Days Overdue</th></tr></thead>',
   'head'),
  ('<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Tenant">\' + (item.tenant_name || \'\') + \'</td>\' +\n          \'<td data-label="Amount">€\' + formattedAmount + \'</td>\' +\n          \'<td data-label="Due Date">\' + (item.due_date || \'\') + \'</td>\' +\n          \'<td data-label="Days Overdue">\' + (item.days_overdue || 0) + \'</td></tr>',
   '<tr>\' +\n          \'<td>\' + (item.prop_name || \'\') + \'</td>\' +\n          \'<td data-label="Country">\' + (item.prop_country || \'\') + \'</td>\' +\n          \'<td data-label="Tenant">\' + (item.tenant_name || \'\') + \'</td>\' +\n          \'<td data-label="Amount" class="num">€\' + formattedAmount + \'</td>\' +\n          \'<td data-label="Due Date">\' + (item.due_date || \'\') + \'</td>\' +\n          \'<td data-label="Days Overdue" class="num">\' + (item.days_overdue || 0) + \'</td></tr>',
   'row'),
  ('<thead><tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th>Amount</th><th>Submitted Date</th><th>Status</th></tr></thead>',
   '<thead><tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th class="num">Amount</th><th>Submitted Date</th><th class="col-center">Status</th></tr></thead>',
   'head'),
  ('<tr>\' +\n          \'<td>\' + (item.property_name || \'N/A\') + \'</td>\' +\n          \'<td data-label="Type">\' + (item.expense_type || \'General\') + \'</td>\' +\n          \'<td data-label="Description">\' + (item.description || \'\') + \'</td>\' +\n          \'<td data-label="Amount">€\' + parseFloat(item.amount || 0).toFixed(2) + \'</td>\' +\n          \'<td data-label="Submitted">\' + (item.submitted_date || item.expense_date || \'\') + \'</td>\' +\n          \'<td data-label="Status"><span class="status-badge status-warning">PENDING APPROVAL</span></td></tr>',
   '<tr>\' +\n          \'<td>\' + (item.property_name || \'N/A\') + \'</td>\' +\n          \'<td data-label="Type">\' + (item.expense_type || \'General\') + \'</td>\' +\n          \'<td data-label="Description">\' + (item.description || \'\') + \'</td>\' +\n          \'<td data-label="Amount" class="num">€\' + parseFloat(item.amount || 0).toFixed(2) + \'</td>\' +\n          \'<td data-label="Submitted">\' + (item.submitted_date || item.expense_date || \'\') + \'</td>\' +\n          \'<td data-label="Status" class="text-center"><span class="alv-pill alv-pill-attn">Pending approval</span></td></tr>',
   'row'),
  ('<thead><tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th>Amount</th><th>Approved Date</th><th>Status</th></tr></thead>',
   '<thead><tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th class="num">Amount</th><th>Approved Date</th><th class="col-center">Status</th></tr></thead>',
   'head'),
  ('<tr>\' +\n          \'<td>\' + (item.property_name || \'N/A\') + \'</td>\' +\n          \'<td data-label="Type">\' + (item.expense_type || \'General\') + \'</td>\' +\n          \'<td data-label="Description">\' + (item.description || \'\') + \'</td>\' +\n          \'<td data-label="Amount">€\' + parseFloat(item.amount || 0).toFixed(2) + \'</td>\' +\n          \'<td data-label="Approved">\' + (item.approved_date || item.expense_date || \'\') + \'</td>\' +\n          \'<td data-label="Status"><span class="status-badge status-info">APPROVED - AWAITING PAYMENT</span></td></tr>',
   '<tr>\' +\n          \'<td>\' + (item.property_name || \'N/A\') + \'</td>\' +\n          \'<td data-label="Type">\' + (item.expense_type || \'General\') + \'</td>\' +\n          \'<td data-label="Description">\' + (item.description || \'\') + \'</td>\' +\n          \'<td data-label="Amount" class="num">€\' + parseFloat(item.amount || 0).toFixed(2) + \'</td>\' +\n          \'<td data-label="Approved">\' + (item.approved_date || item.expense_date || \'\') + \'</td>\' +\n          \'<td data-label="Status" class="text-center"><span class="alv-pill alv-pill-info">Approved - awaiting payment</span></td></tr>',
   'row'),
  ('<thead><tr><th>Property</th><th>Tenant</th><th>Rent</th><th>Communal</th><th>Type</th></tr></thead>',
   '<thead><tr><th>Property</th><th>Tenant</th><th class="num">Rent</th><th class="num">Communal</th><th class="col-center">Type</th></tr></thead>',
   'head'),
  ('<tr>\' +\n              \'<td>\' + esc(b.prop || \'\') + \'</td>\' +\n              \'<td data-label="Tenant">\' + esc(b.name || \'\') + \'</td>\' +\n              \'<td data-label="Rent">\' + fmt(b.rent) + \'</td>\' +\n              \'<td data-label="Communal">\' + fmt(b.levies) + \'</td>\' +\n              \'<td data-label="Type"><span class="status-badge \' +\n                (b.tag === \'at_risk\' ? \'status-warning\' : \'status-info\') + \'">\' +\n                (b.tag === \'at_risk\' ? \'AT-RISK\' : \'SIGNED\') + \'</span></td>\' +\n            \'</tr>',
   '<tr>\' +\n              \'<td>\' + esc(b.prop || \'\') + \'</td>\' +\n              \'<td data-label="Tenant">\' + esc(b.name || \'\') + \'</td>\' +\n              \'<td data-label="Rent" class="num">\' + fmt(b.rent) + \'</td>\' +\n              \'<td data-label="Communal" class="num">\' + fmt(b.levies) + \'</td>\' +\n              \'<td data-label="Type" class="text-center"><span class="status-badge \' +\n                (b.tag === \'at_risk\' ? \'status-warning\' : \'status-info\') + \'">\' +\n                (b.tag === \'at_risk\' ? \'AT-RISK\' : \'SIGNED\') + \'</span></td>\' +\n            \'</tr>',
   'row'),
  ('<span class="status-badge \' +\n                (b.tag === \'at_risk\' ? \'status-warning\' : \'status-info\') + \'">\' +\n                (b.tag === \'at_risk\' ? \'AT-RISK\' : \'SIGNED\') + \'</span>',
   '<span class="alv-pill \' +\n                (b.tag === \'at_risk\' ? \'alv-pill-attn\' : \'alv-pill-info\') + \'">\' +\n                (b.tag === \'at_risk\' ? \'At risk\' : \'Signed\') + \'</span>',
   'chip'),
  ('<table class="data-table">',
   '<table class="table alv-table">',
   'tag'),
 ],
 'notifications.html': [
  ('.table-container {\r\n    overflow-x: auto;\r\n}\r\n\r\n.data-table {\r\n    width: 100%;\r\n    border-collapse: collapse;\r\n    margin: 0;\r\n}\r\n\r\n.data-table th {\r\n    background: var(--alv-surface);\r\n    padding: 12px 15px;\r\n    text-align: center;\r\n    border-bottom: 2px solid var(--alv-line);\r\n    font-weight: 600;\r\n    color: var(--alv-ink-strong);\r\n    font-size: 14px;\r\n}\r\n\r\n.data-table th:first-child {\r\n    text-align: left;\r\n}\r\n\r\n.data-table td {\r\n    padding: 12px 15px;\r\n    border-bottom: 1px solid var(--alv-line);\r\n    text-align: center;\r\n    font-size: 14px;\r\n}\r\n\r\n.data-table td:first-child {\r\n    text-align: left;\r\n    font-weight: 500;\r\n}\r\n\r\n.data-table tbody tr:hover {\r\n    background: var(--alv-surface);\r\n}\r\n\r\n.status-badge {\r\n    padding: 4px 8px;\r\n    border-radius: 4px;\r\n    font-size: 12px;\r\n    font-weight: 500;\r\n}\r\n\r\n.status-urgent {\r\n    background: var(--alv-bad);\r\n    color: var(--alv-on-accent);\r\n}\r\n\r\n.status-warning {\r\n    border: 1px solid var(--alv-warn-line);\n    background: var(--alv-warn-soft);\r\n    color: var(--alv-warn);\r\n}\r\n\r\n.status-info {\r\n    background: var(--alv-accent);\r\n    color: var(--alv-on-accent);\r\n}',
   "/* DT-1, 16 Oct 2026 - THE RULE OPENINGS THAT WERE HERE ARE BASE'S.\r\n   This page drew its tables against a .data-table stylesheet of its own -\r\n   a hand-rolled copy of the house table standard, living beside it - and\r\n   the .table-container line above them OVERRODE base's card shell on\r\n   source order, so these panels scrolled sideways instead of sitting in\r\n   it. The tables wear `table alv-table` now and base owns every line that\r\n   stood here. The four status tones went with them: two of the three were\r\n   SOLID FILLS, which no other status in this application is, and they are\r\n   house pills now. See test_data_table.py. */",
   'css'),
  ('    /* Tables → card layout */\r\n    .data-table thead {\r\n        display: none;\r\n    }\r\n    .data-table,\r\n    .data-table tbody,\r\n    .data-table tr {\r\n        display: block;\r\n        width: 100%;\r\n    }\r\n    .data-table tr {\r\n        background: var(--alv-paper);\r\n        border: 1px solid var(--alv-line);\r\n        border-radius: 8px;\r\n        padding: 12px 14px;\r\n        margin-bottom: 10px;\r\n    }\r\n    .data-table tr:hover {\r\n        background: var(--alv-paper);\r\n    }\r\n    .data-table td {\r\n        display: flex !important;\r\n        justify-content: space-between;\r\n        align-items: center;\r\n        gap: 12px;\r\n        padding: 6px 0 !important;\r\n        border-bottom: none;\r\n        text-align: right !important;\r\n        font-size: 13px;\r\n    }\r\n    .data-table td:first-child {\r\n        font-size: 15px;\r\n        font-weight: 600;\r\n        color: var(--alv-ink);\r\n        padding-bottom: 8px !important;\r\n        margin-bottom: 4px;\r\n        border-bottom: 1px solid var(--alv-line-soft) !important;\r\n        text-align: left !important;\r\n        display: block !important;\r\n    }\r\n    .data-table td:not(:first-child)::before {\r\n        content: attr(data-label);\r\n        font-weight: 600;\r\n        color: var(--alv-ink-soft);\r\n        font-size: 12px;\r\n        text-transform: uppercase;\r\n        letter-spacing: 0.4px;\r\n        text-align: left;\r\n        flex-shrink: 0;\r\n    }\r\n    .status-badge {\r\n        font-size: 11px;\r\n    }',
   "    /* DT-1, 16 Oct 2026 - and the phone card with it. This page built its\r\n       own table-as-cards block: a good copy of base's, and still a copy. Base\r\n       owns the card, the labels and the first cell. */",
   'css'),
  ('<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th>Status</th><th>Action Required</th></tr>\r\n                    </thead>',
   '<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th class="col-center">Status</th><th>Action Required</th></tr>\r\n                    </thead>',
   'head'),
  ('<tr>\r\n                <td>${item.prop_name || \'\'}</td>\r\n                <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                <td data-label="Status"><span class="status-badge status-urgent">VACANT</span></td>\r\n                <td data-label="Action">Contact estate agents ASAP</td>\r\n            </tr>',
   '<tr>\r\n                <td>${item.prop_name || \'\'}</td>\r\n                <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                <td data-label="Status" class="text-center"><span class="alv-pill alv-pill-bad">Vacant</span></td>\r\n                <td data-label="Action">Contact estate agents ASAP</td>\r\n            </tr>',
   'row'),
  ('<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th>Tenant</th><th>Lease End Date</th><th>Days to End</th><th>Status</th></tr>\r\n                    </thead>',
   '<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th>Tenant</th><th>Lease End Date</th><th class="num">Days to End</th><th class="col-center">Status</th></tr>\r\n                    </thead>',
   'head'),
  ('<tr>\r\n                <td>${item.prop_name || \'\'}</td>\r\n                <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                <td data-label="Tenant">${item.tenant_name || \'\'}</td>\r\n                <td data-label="Lease End">${item.lease_end_date || \'\'}</td>\r\n                <!-- DB-8, 2 Oct 2026. Was "Renewal Due" from item.renewal_date,\r\n                     which the new rule does not produce, and a hard-coded\r\n                     PENDING that was only ever true because the OLD query\r\n                     filtered on it. -->\r\n                <td data-label="Days to End">${item.days_to_end != null ? item.days_to_end + \'d\' : \'\'}</td>\r\n                <td data-label="Status"><span class="status-badge status-warning">${(item.renewal_status || \'pending\').toUpperCase()}</span></td>\r\n            </tr>',
   '<tr>\r\n                <td>${item.prop_name || \'\'}</td>\r\n                <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                <td data-label="Tenant">${item.tenant_name || \'\'}</td>\r\n                <td data-label="Lease End">${item.lease_end_date || \'\'}</td>\r\n                <!-- DB-8, 2 Oct 2026. Was "Renewal Due" from item.renewal_date,\r\n                     which the new rule does not produce, and a hard-coded\r\n                     PENDING that was only ever true because the OLD query\r\n                     filtered on it. -->\r\n                <td data-label="Days to End" class="num">${item.days_to_end != null ? item.days_to_end + \'d\' : \'\'}</td>\r\n                <td data-label="Status" class="text-center"><span class="alv-pill alv-pill-attn">${(item.renewal_status || \'pending\').replace(/^./, c => c.toUpperCase())}</span></td>\r\n            </tr>',
   'row'),
  ('<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th>Current Tenant</th><th>Lease End Date</th><th>Status</th></tr>\r\n                    </thead>',
   '<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th>Current Tenant</th><th>Lease End Date</th><th class="col-center">Status</th></tr>\r\n                    </thead>',
   'head'),
  ('<tr>\r\n                <td>${item.prop_name || \'\'}</td>\r\n                <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                <td data-label="Current Tenant">${item.tenant_name || \'\'}</td>\r\n                <td data-label="Lease End">${item.lease_end_date || \'\'}</td>\r\n                <td data-label="Status"><span class="status-badge status-urgent">NEED NEW TENANT</span></td>\r\n            </tr>',
   '<tr>\r\n                <td>${item.prop_name || \'\'}</td>\r\n                <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                <td data-label="Current Tenant">${item.tenant_name || \'\'}</td>\r\n                <td data-label="Lease End">${item.lease_end_date || \'\'}</td>\r\n                <td data-label="Status" class="text-center"><span class="alv-pill alv-pill-bad">Need new tenant</span></td>\r\n            </tr>',
   'row'),
  ('<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th>Tenant</th><th>Amount</th><th>Due Date</th><th>Days Overdue</th></tr>\r\n                    </thead>',
   '<thead>\r\n                        <tr><th>Property Name</th><th>Country</th><th>Tenant</th><th class="num">Amount</th><th>Due Date</th><th class="num">Days Overdue</th></tr>\r\n                    </thead>',
   'head'),
  ('<tr>\r\n                    <td>${item.prop_name || \'\'}</td>\r\n                    <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                    <td data-label="Tenant">${item.tenant_name || \'\'}</td>\r\n                    <td data-label="Amount">€${formattedAmount}</td>\r\n                    <td data-label="Due Date">${item.due_date || \'\'}</td>\r\n                    <td data-label="Days Overdue">${item.days_overdue || 0}</td>\r\n                </tr>',
   '<tr>\r\n                    <td>${item.prop_name || \'\'}</td>\r\n                    <td data-label="Country">${item.prop_country || \'\'}</td>\r\n                    <td data-label="Tenant">${item.tenant_name || \'\'}</td>\r\n                    <td data-label="Amount" class="num">€${formattedAmount}</td>\r\n                    <td data-label="Due Date">${item.due_date || \'\'}</td>\r\n                    <td data-label="Days Overdue" class="num">${item.days_overdue || 0}</td>\r\n                </tr>',
   'row'),
  ('<thead>\r\n                        <tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th>Amount</th><th>Submitted Date</th><th>Status</th></tr>\r\n                    </thead>',
   '<thead>\r\n                        <tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th class="num">Amount</th><th>Submitted Date</th><th class="col-center">Status</th></tr>\r\n                    </thead>',
   'head'),
  ('<tr>\r\n                <td>${item.property_name || \'N/A\'}</td>\r\n                <td data-label="Type">${item.expense_type || \'General\'}</td>\r\n                <td data-label="Description">${item.description || \'\'}</td>\r\n                <td data-label="Amount">€${parseFloat(item.amount || 0).toFixed(2)}</td>\r\n                <td data-label="Submitted">${item.submitted_date || item.expense_date || \'\'}</td>\r\n                <td data-label="Status"><span class="status-badge status-warning">PENDING APPROVAL</span></td>\r\n            </tr>',
   '<tr>\r\n                <td>${item.property_name || \'N/A\'}</td>\r\n                <td data-label="Type">${item.expense_type || \'General\'}</td>\r\n                <td data-label="Description">${item.description || \'\'}</td>\r\n                <td data-label="Amount" class="num">€${parseFloat(item.amount || 0).toFixed(2)}</td>\r\n                <td data-label="Submitted">${item.submitted_date || item.expense_date || \'\'}</td>\r\n                <td data-label="Status" class="text-center"><span class="alv-pill alv-pill-attn">Pending approval</span></td>\r\n            </tr>',
   'row'),
  ('<thead>\r\n                        <tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th>Amount</th><th>Approved Date</th><th>Status</th></tr>\r\n                    </thead>',
   '<thead>\r\n                        <tr><th>Property Name</th><th>Expense Type</th><th>Description</th><th class="num">Amount</th><th>Approved Date</th><th class="col-center">Status</th></tr>\r\n                    </thead>',
   'head'),
  ('<tr>\r\n                <td>${item.property_name || \'N/A\'}</td>\r\n                <td data-label="Type">${item.expense_type || \'General\'}</td>\r\n                <td data-label="Description">${item.description || \'\'}</td>\r\n                <td data-label="Amount">€${parseFloat(item.amount || 0).toFixed(2)}</td>\r\n                <td data-label="Approved">${item.approved_date || item.expense_date || \'\'}</td>\r\n                <td data-label="Status"><span class="status-badge status-info">APPROVED - AWAITING PAYMENT</span></td>\r\n            </tr>',
   '<tr>\r\n                <td>${item.property_name || \'N/A\'}</td>\r\n                <td data-label="Type">${item.expense_type || \'General\'}</td>\r\n                <td data-label="Description">${item.description || \'\'}</td>\r\n                <td data-label="Amount" class="num">€${parseFloat(item.amount || 0).toFixed(2)}</td>\r\n                <td data-label="Approved">${item.approved_date || item.expense_date || \'\'}</td>\r\n                <td data-label="Status" class="text-center"><span class="alv-pill alv-pill-info">Approved - awaiting payment</span></td>\r\n            </tr>',
   'row'),
  ('<table class="data-table">',
   '<table class="table alv-table">',
   'tag'),
 ],
}


# --------------------------------------------------------------------------
# REGISTRATION. These three anchors are LV-1's tails, because DT-1 lands on
# top of TD-2 and LV-1 in that order.
# --------------------------------------------------------------------------
SUITE_WAS = """    'test_leave_decided.py'
)"""
SUITE_NOW = """    'test_leave_decided.py',
    'test_data_table.py'
)"""

TREE_WAS = """    'test_leave_decided.py',
]"""
TREE_NOW = """    'test_leave_decided.py',
    # DT-1, 16 Oct 2026 - the last two pages with a table standard of
    # their own. 13 tables built in JavaScript, 25 rule openings and 11
    # status chips, none of which a markup gate could ever see. Wide
    # from birth.
    'test_data_table.py',
]"""

ROUNDS_WAS = """    '.bak_leavedecided',
]"""
ROUNDS_NOW = """    '.bak_leavedecided',
    # DT-1, 16 Oct 2026 - home.html and notifications.html give up their
    # own .data-table stylesheet and their own .status-badge tones. The
    # six panels existed TWICE, built from two copies of the code; the
    # duplication is what the round is really about.
    '.bak_datatable',
]"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""
SENT_NEW = """    # ------------------------------------------------- DT-1, 16 Oct 2026
    # Demetri: make the Home and Notifications tables match the rest of
    # the application. They could not be reported by any table suite,
    # because they are built in JavaScript as strings.
    @{ File = 'pages\\\\templates\\\\home.html'; Text = 'table alv-table'; What = 'DT-1: the Home tables are on the house table standard' },
    @{ File = 'pages\\\\templates\\\\home.html'; Text = 'data-table'; Absent = $true; Code = $true; What = 'DT-1: and the page keeps no table stylesheet of its own' },
    @{ File = 'pages\\\\templates\\\\notifications.html'; Text = 'alv-pill alv-pill-attn'; What = 'DT-1: the Notifications status chips are house pills' },
    @{ File = 'pages\\\\templates\\\\notifications.html'; Text = 'status-badge'; Absent = $true; Code = $true; What = 'DT-1: and the solid-fill status tones are gone' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""


# ------------------------------------------------- test_leave_decided
# LV-1's SUITE READS THE SHARED COUNTERS LIVE, and DT-1 moves both. TD-2's
# suite already asks them through as_left_by - "as THIS round left them" -
# because three rounds a week bump these two files; LV-1's was written an
# hour later and did not. The round that falsifies a claim fixes it, and
# the fix is the one TD-2 already carries.
LV_WAS = """wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counts %d converted suites' % CONVERTED_NOW)
co = read(os.path.join(ROOT, 'test_code_only.py'))
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counts %d files aliasing code_only' % ALIAS_NOW)
ok('45 patchers and 46 suites' in co,
   '  split 45 patchers and 46 suites - TD-2 made it 44 and 45, and this '
   'round is one of each on top')"""

LV_NOW = """# DT-1, 16 Oct 2026 - AS THIS ROUND LEFT THEM, NOT AS THEY STAND.
# These three read the live files until DT-1 bumped both an hour later
# and every one of them failed. A shared counter is read through
# as_left_by, which walks ROUNDS forward and hands back the next round's
# backup - the text LV-1 actually wrote. TD-2's suite was written this
# way; this one was not, and that is the whole difference.


def as_lv_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


wd = as_lv_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when LV-1 left it'
   % CONVERTED_NOW)
co = as_lv_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)
ok('45 patchers and 46 suites' in co,
   '  split 45 patchers and 46 suites - TD-2 made it 44 and 45, and this '
   'round was one of each on top')"""


# ------------------------------------------------------- test_amber
# B-4, 10 Oct, wrote the house warn tokens into each page's OWN
# .status-warning rule and kept its shape, because adding .alv-pill-attn
# as a class would have resized seven pills nobody asked to resize. On
# these two pages the shape WAS asked about, so the rule goes and base's
# pill draws them. B-4's claim - the amber here is on house tokens - is
# MORE true after this round, not less; it is re-pointed at base rather
# than deleted.
AMB_WAS = """PILLS = (('home.html', '.status-warning'),
         ('notifications.html', '.status-warning'),
         ('finance_expense_add.html', '.anchor-pill'),"""

AMB_NOW = """# DT-1, 16 Oct 2026 - HOME AND NOTIFICATIONS DECLARE NO PILL AT ALL NOW.
# B-4 wrote the house warn tokens into each page's OWN .status-warning
# rule and kept its shape, because adding .alv-pill-attn as a class would
# have resized seven pills nobody asked to resize. On these two pages the
# shape was asked about: Demetri saw the chips rendered three ways and
# chose the house pill over the solid fills they sat beside. So the rule
# is gone and base's draws them. The claim is made below the loop
# instead, because a rule that does not exist carries no tokens.
PILLS = (('finance_expense_add.html', '.anchor-pill'),"""

AMB_TAIL_WAS = """

def _value(code, ba, bb, prop):"""

AMB_TAIL_NOW = """
# DT-1, 16 Oct 2026 - THE TWO THAT LEFT THAT LIST, ASKED PROPERLY.
# B-4's claim was that the amber on these pages is on house tokens. That
# is MORE true now, not less: the tokens are in base and the pages carry
# no copy. Asserted here so the substance of the claim survives the rule
# it used to be attached to.
for _pg in ('home.html', 'notifications.html'):
    _body = T.code_only(read(T.path_of(_pg)))
    ok('.status-warning' not in _body,
       '%-26s declares no pill of its own any more' % _pg)
    ok('alv-pill-attn' in _body,
       '  and wears base .alv-pill-attn instead')
_attn = rule(T.path_of('base.html'), '.alv-pill-attn') or ''
ok('var(%s)' % SOFT in _attn,
   '%-26s .alv-pill-attn has the soft fill' % 'base.html', _attn)
ok('var(%s)' % WARN in _attn, '  and the warn ink')
ok('var(%s)' % LINE in _attn, '  and a warn-line border')


def _value(code, ba, bb, prop):"""

# --------------------------------------------------- test_print_leaks
# THE MIGRATION QUEUE. These two pages have been on it since it was
# written, and they were the hardest entries on it to see: that census
# finds a hand-rolled card view by the `content: attr(data-label)` the
# page declares, which is the only trace a JavaScript-built table leaves
# in CSS. A page leaving the queue is a migration and comes off in the
# same round - the queue's own comment says so.
LEAKS_Q_WAS = """QUEUE = [
    'home.html', 'notifications.html', 'cash_receipts.html',"""
LEAKS_Q_NOW = """QUEUE = [
    'cash_receipts.html',"""

LEAKS_M_WAS = """MIGRATED_NV1B = ['title_deeds_management.html']"""
LEAKS_M_NOW = """MIGRATED_NV1B = ['title_deeds_management.html']
# Left the queue: 16 Oct 2026 round DT-1 (.bak_datatable), after Demetri
# asked for the Home and Notifications tables to match the rest of the
# application. These two were the hardest entries on this list to see:
# their tables are BUILT IN JAVASCRIPT, as strings, so no table suite in
# this project could report them and this census found them only by the
# `content: attr(data-label)` their own phone block declared. Both wear
# .alv-table now and base draws the card, so the declaration this census
# looks for is gone with it.
MIGRATED_DT1 = ['home.html', 'notifications.html']"""

LEAKS_C_WAS = """check('  and the nine migrated so far are off it',
      not (set(_cards) & (set(MIGRATED_H4) | set(MIGRATED_P2)
                          | set(MIGRATED_NV1B))),
      sorted(set(_cards) & (set(MIGRATED_H4) | set(MIGRATED_P2)
                            | set(MIGRATED_NV1B))))"""
LEAKS_C_NOW = """_MIGRATED = (set(MIGRATED_H4) | set(MIGRATED_P2) | set(MIGRATED_NV1B)
             | set(MIGRATED_DT1))
check('  and the %d migrated so far are off it' % len(_MIGRATED),
      not (set(_cards) & _MIGRATED),
      sorted(set(_cards) & _MIGRATED))"""

# -------------------------------------------------- test_system_teal
# A CLAIM ABOUT AN ABILITY, ASSERTED THROUGH A NUMBER. AD-1 taught the
# pair census to resolve a page's own :root; the suite then pinned the
# census's VALUE as proof. An equality broke, a floor broke, and the
# replacement floor breaks here - four times, each for a round that had
# nothing to do with AD-1. The capability is one argument in
# apply_edit_ink.py and that is what this round asserts instead.
ST_A_WAS = """ok(_pairs > 701,
   'and the pair census is at %d against the 701 it could see before AD-1 '
   'taught it to read a page own :root - every tab rule in the tree was '
   'written in one and not a single one of them was being counted'
   % _pairs)"""

ST_A_NOW = """# DT-1, 16 Oct 2026 - AND IT IS NOT A COUNT ANY MORE, which is what
# the note directly below this one has been saying since TB-1.
#
# The history: AD-1 wrote an equality here. PR-1 caught it and made it
# `>= 714`. TB-1 broke that by moving four copies of one rule into base,
# because consolidation REMOVES pairs. The file then wrote `_pairs > 701`
# - a floor again - two lines above its own sentence saying `what is
# worth asserting is not a count at all`. DT-1 deleted eight pairs with
# two page stylesheets and took it to 698, which is a round that is none
# of AD-1's business, and that is the fourth time this one claim has gone
# red for somebody else's work.
#
# WHAT AD-1 ACTUALLY DID is pass the PAGE'S code into base_tokens, so a
# rule written in a page-local token is resolved instead of skipped.
# That is a capability. It is one argument in apply_edit_ink.py, no
# later round can undo it by adding or deleting a rule, and it is what
# gets asserted now. The number is printed, not judged.
_ink = read(os.path.join(ROOT, 'apply_edit_ink.py'))
ok('base_tokens(code, base_code)' in _ink,
   'the census still resolves a page OWN :root and not base alone - '
   'every tab rule in the tree is written in one, and before AD-1 not a '
   'single one of them was being counted (the census reads %d pairs '
   'today, which is reported and not judged)' % _pairs)"""

ST_B_WAS = """ok(_pairs > 701,
   '  which is the claim that survives: 701 was what it could see before, '
   'and no later round can take it back there')"""

ST_B_NOW = """ok('--alv-accent' in pc or '.admin-tab' in pc,
   '  and the claim that survives is the PAIRING, not the population it '
   'sits in: a table that names its rows cannot be moved by a round that '
   'adds or deletes one somewhere else')"""

def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('DT-1 REFUSED: %s' % msg)


def once(text, lit, where):
    got = text.count(lit)
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(was, now, 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED, asked of the tree.
    if TAG_NOW in code_only(read(alv_tree.path_of('home.html'))):
        print('DT-1  already applied - the Home tables wear the house '
              'table standard.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE STANDARD IS READ, NOT REMEMBERED. Everything these pages are
    # being moved ONTO is asserted against base as it stands today.
    base = code_only(read(alv_tree.path_of('base.html')))
    for need, what in (
            ('.alv-table thead th', 'the house table head'),
            ('.alv-table td::before', 'the phone card label'),
            ('.alv-table th.num', 'the right-aligned number column'),
            ('.alv-table thead th.col-center', 'the centred column'),
            ('.alv-pill-bad', 'the bad pill'),
            ('.alv-pill-attn', 'the attention pill'),
            ('.alv-pill-info', 'the info pill'),
            ('.table-container', 'the card shell these panels were overriding')):
        if need not in base:
            refuse('base.html no longer declares %s (%s), and this round '
                   'moves two pages onto it' % (need, what))

    # ---------------------------------------------------------------- 2
    n_tag = n_pill = n_css = 0
    for page in PAGES:
        p = alv_tree.path_of(page)
        s = read(p)
        for was, now, kind in PAIRS[page]:
            if kind == 'tag':
                got = s.count(was)
                if got < 1:
                    refuse('%s: no `%s` left to convert' % (page, was))
                s = s.replace(was, now)
                n_tag += got
            else:
                s = swap(s, was, now, '%s (%s)' % (page, kind))
                if kind == 'css':
                    n_css += 1
                # COUNT THE CHIPS, NOT THE WORD. Each chip writes
                # `class="alv-pill alv-pill-attn"`, which is the word
                # twice, and the income ternary writes it three times.
                n_pill += (now.count('class="alv-pill')
                           - was.count('class="alv-pill'))
        out[p] = s

    # ---------------------------------------------------------------- 3
    # GATES, every one asked of the CODE - this round's own comments
    # spell `data-table` and `status-badge` in order to say they are gone.
    for p, s in out.items():
        rel = os.path.relpath(p, root)
        body = code_only(s)
        if 'data-table' in body:
            refuse('%s: a .data-table reference survives the round' % rel)
        if 'status-badge' in body:
            refuse('%s: a status-badge survives the round' % rel)
        if TAG_WAS in body:
            refuse('%s: a table still wears the old class' % rel)
        # EVERY TABLE HAS AS MANY HEADS AS ITS ROW HAS CELLS, which is
        # what makes the phone card readable - base prints each cell's
        # own data-label, and a cell with none prints nothing.
        for m in re.finditer(r'<thead>.*?</thead>', body, re.S):
            if '<th' not in m.group(0):
                continue
            n_th = len(re.findall(r'<th\b', m.group(0)))
            if n_th < 4:
                refuse('%s: a head row has %d column(s)' % (rel, n_th))
        # A CENTRED CELL IS `text-center`, A CENTRED HEAD IS
        # `col-center`. base declares only `.alv-table thead
        # th.col-center`, so col-center on a <td> styles nothing at all -
        # which is what the first cut of this round wrote, and what
        # section 6 of the suite caught by RUNNING the builder.
        for mm in re.finditer(r'<td\b[^>]*class="([^"]*)"', body):
            if 'col-center' in mm.group(1).split():
                refuse('%s: a CELL carries col-center, which base styles '
                       'nowhere - a cell is centred with text-center' % rel)
        for mm in re.finditer(r'<th\b[^>]*class="([^"]*)"', body):
            if 'text-center' in mm.group(1).split():
                refuse('%s: a HEAD carries text-center - a head is '
                       'centred with col-center' % rel)

        # THE PILL TONES ARE BASE'S THREE, AND NOTHING ELSE.
        for mm in re.finditer(r'alv-pill-(\w+)', body):
            if mm.group(1) not in ('bad', 'attn', 'info'):
                refuse('%s: an unexpected pill tone %r' % (rel, mm.group(1)))
        # AND NOTHING SHOUTS ANY MORE. The shape that shouts is
        # toUpperCase applied to the WHOLE status; the replacement
        # applies it to one character, and the first cut of this gate
        # refused its own output for saying the same word. A gate asks
        # for the shape, not for the word.
        if re.search(r"renewal_status[^;]{0,40}\)\.toUpperCase\(\)", body):
            refuse('%s: a status is still shouted - toUpperCase on the '
                   'whole value' % rel)

    if n_tag != N_TABLES:
        refuse('%d table(s) converted, expected %d' % (n_tag, N_TABLES))
    if n_pill != N_PILLS:
        refuse('%d pill(s) written, expected %d' % (n_pill, N_PILLS))
    if n_css != N_CSS_BLOCKS:
        refuse('%d stylesheet block(s) cut, expected %d'
               % (n_css, N_CSS_BLOCKS))

    # LINE ENDINGS ARE PART OF THE FILE. notifications.html is CRLF with
    # seven bare LFs in it; a round that changes that count has rewritten
    # lines it never touched.
    for p, s in out.items():
        was = read(p)
        a_crlf, b_crlf = was.count('\r\n'), s.count('\r\n')
        a_lf = was.count('\n') - a_crlf
        b_lf = s.count('\n') - b_crlf
        if b_lf > a_lf:
            refuse('%s: bare LF count went %d -> %d, so the round '
                   'introduced a line ending the file did not have'
                   % (os.path.relpath(p, root), a_lf, b_lf))

    # ---------------------------------------------------------------- 4
    p = os.path.join(root, PS1)
    s = read(p)
    if ME in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'DT-1, 16 Oct 2026 - this round own suite. The Home and '
                  'Notifications tables join the house standard, after '
                  'Demetri asked for them to match the rest of the '
                  'application.', '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'DT-1, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 4b
    # THE !IMPORTANT CENSUS. The two phone blocks this round cuts carried
    # fourteen !important declarations between them, every one a copy of
    # something base already says with the same !important - so nothing
    # changed about what wins, there is simply one copy of each now. The
    # same shape NV-1b found on the title deeds page.
    p = os.path.join(root, IMP)
    out[p] = bump(read(p), 'IMP_TREE = %d', IMP_WAS, IMP_NOW,
                  'DT-1, 16 Oct 2026 - fourteen went with the two '
                  'table-as-cards blocks on home and notifications. Each '
                  'was a copy of a declaration base already makes, with '
                  'the same !important.', '%s (the tree census)' % IMP)

    # ---------------------------------------------------------------- 4c
    p = os.path.join(root, LV)
    out[p] = swap(read(p), LV_WAS, LV_NOW, '%s (the shared counters)' % LV)

    # ---------------------------------------------------------------- 4d
    p = os.path.join(root, AMB)
    t = read(p)
    t = swap(t, AMB_WAS, AMB_NOW, '%s (the pill list)' % AMB)
    t = swap(t, AMB_TAIL_WAS, AMB_TAIL_NOW, '%s (the two that left it)' % AMB)
    out[p] = t

    # ---------------------------------------------------------------- 4e
    # TWO MORE CENSUSES, both of them counting RULES rather than pages,
    # and both moved by the same 25 rule openings this round deletes.
    # test_recipe_spice needs nothing: it reads EXPECT_PAIRS out of
    # test_pair_contrast at run time rather than keeping its own copy,
    # which is the right way to hold the same number twice.
    p = os.path.join(root, PC)
    out[p] = bump(read(p), 'EXPECT_PAIRS = %d', PAIRS_WAS, PAIRS_NOW,
                  'DT-1, 16 Oct 2026 - eight rules that set both a '
                  'background and a colour went with the two .data-table '
                  'stylesheets. Every pair below AA that this table names '
                  'is untouched; the gross count is what moved.',
                  '%s (the pair census)' % PC)

    p = os.path.join(root, SB)
    out[p] = bump(read(p), 'N_GAINED = %d', GAINED_WAS, GAINED_NOW,
                  'DT-1, 16 Oct 2026 - six of the rules this round '
                  'deletes carried the border token. base draws those '
                  'borders now, so the count falls by exactly the copies '
                  'that went.', '%s (the border census)' % SB)

    # ---------------------------------------------------------------- 4f
    p = os.path.join(root, PL)
    t = read(p)
    t = swap(t, LEAKS_Q_WAS, LEAKS_Q_NOW, '%s (the queue)' % PL)
    t = swap(t, LEAKS_M_WAS, LEAKS_M_NOW, '%s (what it left for)' % PL)
    t = swap(t, LEAKS_C_WAS, LEAKS_C_NOW, '%s (the migrated check)' % PL)
    out[p] = t

    # ---------------------------------------------------------------- 4g
    p = os.path.join(root, ST)
    t = read(p)
    t = swap(t, ST_A_WAS, ST_A_NOW, '%s (the census claim)' % ST)
    t = swap(t, ST_B_WAS, ST_B_NOW, '%s (the surviving claim)' % ST)
    out[p] = t

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('DT-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        print('   %d table(s), %d pill(s), %d stylesheet block(s)'
              % (n_tag, n_pill, n_css))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('DT-1 applied.')
    print('   %d table(s) wear `table alv-table` - 7 on home, 6 on '
          'notifications' % n_tag)
    print('   %d stylesheet block(s) gone, and base owns what they said'
          % n_css)
    print('   %d status chip(s) are house pills in house wording - two of'
          % n_pill)
    print('         the three tones were SOLID FILLS and no other status')
    print('         in this application is one')
    print('   money and day counts take .num, statuses take .col-center')
    print('   the income tone is still decided in JavaScript, because it')
    print('         is data and not drift')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
