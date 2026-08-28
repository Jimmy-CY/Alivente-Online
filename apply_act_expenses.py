#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Actual Expenses joins the standard, and stops drawing facts as buttons.

Migration #8, and the largest page in the order: 2,507 lines, 157 CSS rules,
14 !important, 44 distinct hex colours. Scope agreed with the user - the main
expenses table plus the two Report-modal tables. The Analysis modal is OUT.

FOUR THINGS, and only the first is styling.

1. THE TABLE WAS IN .expense-table-wrapper, NOT .table-container. base's
   sticky-heading observer looks for .table-container, so it had never seen
   this page - and the wrapper set `overflow: hidden`, which makes it a scroll
   container and stops a sticky heading sticking even if it had. Exactly the
   Valuations fault, and the fourth page in a row to carry it.

2. A STATUS WAS DRAWN AS A CONTROL. Approved? and Paid? rendered a DISABLED
   BUTTON for a fact you cannot change, coloured #32CD32 (lime) and #DC143C
   (crimson) inside style attributes - two colours that exist nowhere else in
   this system and that no stylesheet could reach. A status you cannot change
   is a pill now; a button survives only where a button can be pressed. And
   base already owns .status-btn, so the pressable half needed no new
   component - only to stop wrapping its label in a coloured span. The page
   had been overriding base's button with `border: 1px solid black`.

3. "APPROVE FIRST" was a disabled CRIMSON button whose label explained why it
   was disabled. An expense that has not been approved yet is not an error and
   is not waiting on you - it is not yet due. It reads "Not yet" on the neutral
   pill, with the reason in the title, and EVERY user sees that reason now;
   before, a non-superuser was shown a red "Pending" with no explanation at all.

4. THE REPORT COUNTED LESS THAN IT CLAIMED. `act_expense_report_data`'s
   docstring said it "Aggregates ALL expense rows ... regardless of
   approved/paid status" while the line beneath it filtered on
   approved='Yes', paid='Yes'. A property carrying approved-but-unpaid
   expenses read as a smaller number than the grid behind the window, and
   nothing said why.

   DECIDED 28 Aug: the BEHAVIOUR is right and the words were wrong. No figure
   moves. The docstrings are corrected and the report states its population on
   its own face. Which also settles the drill table's Approved and Paid
   columns: the endpoint filters on exactly those two fields, so both were
   CONSTANT BY CONSTRUCTION and statusBadge()'s red branch was unreachable.
   Two columns of a narrow report carrying no information. They are gone, and
   the note above the overview says it once.

THE TWO REPORT TABLES ARE NOT IN THE MARKUP. Their rows are built in
JavaScript, so a check that reads the template sees nothing and a check that
greps the file finds the colours inside a <script>. The suite executes the row
builders and measures the DOM they produce.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'act_expense.html')
BASE   = os.path.join(TPL, 'base.html')
VIEW   = os.path.join(ROOT, 'pages', 'views', 'expenses.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_actexp'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:110]))


def blocks(text):
    """The ### NAME sections of payload_js.txt, as a dict."""
    out, name, buf = {}, None, []
    for line in text.split('\n'):
        if line.startswith('### '):
            if name:
                out[name] = '\n'.join(buf).strip('\n')
            name, buf = line[4:].strip(), []
        else:
            buf.append(line)
    if name:
        out[name] = '\n'.join(buf).strip('\n')
    return out


NEW_MAIN = r'''<!-- Expenses Table -->
<div class="table-container">
<table class="table alv-table expense-table">
<thead>
    <tr>
        <th style="width: {% if from_finance_pl_act %}15%{% else %}11%{% endif %}">Date</th>
        <th style="width: {% if from_finance_pl_act %}20%{% else %}20%{% endif %}">Property</th>
        <th style="text-align: left; width: {% if from_finance_pl_act %}45%{% else %}31%{% endif %}">Description</th>
        <th class="num" style="width: {% if from_finance_pl_act %}20%{% else %}12%{% endif %}">Amount</th>
        {% if not from_finance_pl_act %}
            <th style="width: 10%">Approved?</th>
            <th style="width: 10%">Paid?</th>
            <th class="desktop-action-cell cell-actions" style="width: 6%">Actions</th>
        {% endif %}
    </tr>
</thead>
<tbody>
    {% for expense in expenses %}
    <tr>
        <td data-label="Date">{{ expense.act_expense_date|date:"Y-m-d" }}</td>
        <td data-label="Property" class="cell-property" style="text-align: left">
            {{ expense.prop.prop_name }}
            {% if expense.act_expense_document %}
                {% with badge=expense.verify_badge %}
                <i class="fas {{ badge.1 }} verify-icon verify-{{ badge.0 }}"
                   onclick="viewInvoiceQuick('{{ expense.act_expense_document.url }}', '{{ expense.act_expense_document.name }}')"
                   title="{{ badge.2 }} - click to view invoice"></i>
                {% endwith %}
            {% endif %}
        </td>
        <td data-label="Description" style="text-align: left">{{ expense.act_expense_description }}</td>
        <td data-label="Amount" class="num cell-amount">&euro;{{ expense.act_expense_amount|floatformat:2|intcomma }}</td>
        {% if not from_finance_pl_act %}
            <!-- A STATUS IS NOT A CONTROL. Both columns used to draw a disabled
                 button for a fact you cannot change - and coloured it #32CD32 or
                 #DC143C in a style attribute, two colours that exist nowhere else
                 in the system and that no stylesheet could reach. A pill says
                 "this is how things are"; a button says "press me". Only the
                 branch that can actually be pressed is a button now. -->
            <td data-label="Approved?">
                {% if expense.act_expense_approved == 'Yes' %}
                    <span class="alv-pill alv-pill-good">Approved</span>
                {% elif user.is_superuser %}
                    <form method="post" action="{% url 'mark_approved' expense.act_expense_id %}" class="exp-inline-form">
                        {% csrf_token %}
                        <button type="submit" class="status-btn">
                            <i class="fas fa-check"></i> Approve
                        </button>
                    </form>
                {% else %}
                    <span class="alv-pill alv-pill-attn">Pending</span>
                {% endif %}
            </td>
            <td data-label="Paid?">
                {% if expense.act_expense_paid == 'Yes' %}
                    <span class="alv-pill alv-pill-good">Paid</span>
                {% elif expense.act_expense_approved != 'Yes' %}
                            <!-- NOT an error, and not waiting on you either - it is
                         not yet due. Keeping this off the red/amber scale is
                         what lets amber keep meaning "waiting on you"
                         everywhere else. The old label was a disabled CRIMSON
                         button reading "Approve First", and only a superuser
                         ever saw that reason at all. -->
                    <span class="alv-pill alv-pill-neutral"
                          title="This expense has to be approved before it can be paid">Not yet</span>
                {% elif user.is_superuser %}
                    <form method="post" action="{% url 'mark_paid' expense.act_expense_id %}" class="exp-inline-form">
                        {% csrf_token %}
                        <button type="submit" class="status-btn">
                            <i class="fas fa-euro-sign"></i> Pay
                        </button>
                    </form>
                {% else %}
                    <span class="alv-pill alv-pill-attn">Pending</span>
                {% endif %}
            </td>
            <td data-label="Actions" class="desktop-action-cell cell-actions">
                <div class="row-actions">
                {% if perms.auth.can_access_expenses %}
                    <button type="button" class="icon-action-btn icon-manage"
                            id="manage-btn-{{ expense.act_expense_id }}"
                            title="Manage this expense"
                            onclick="openManageModal({{ expense.act_expense_id }}, '{{ expense.act_expense_date|date:"Y-m-d" }}', '{{ expense.prop.prop_name }}', '{{ expense.act_expense_description }}', '{{ expense.act_expense_amount }}', '{{ expense.act_expense_approved }}', '{{ expense.act_expense_paid }}', {% if expense.act_expense_document %}'{{ expense.act_expense_document.url }}', '{{ expense.act_expense_document.name }}'{% else %}null, null{% endif %}, {{ user.is_superuser|yesno:"true,false" }}, {{ perms.auth.can_edit_expenses|yesno:"true,false" }})">
                        <i class="fas fa-folder-open"></i>
                    </button>
                {% else %}
                    <!-- The disabled twin holds the slot, so the column does
                         not change width between a user who may manage and one
                         who may not. Every migrated page does this. -->
                    <span class="icon-action-btn icon-disabled"
                          title="You do not have permission to manage expenses">
                        <i class="fas fa-folder-open"></i>
                    </span>
                {% endif %}
                </div>
            </td>

            <td class="mobile-action-bar cols-1">
                {% if perms.auth.can_access_expenses %}
                    <button type="button" class="mobile-action-btn"
                            onclick="openManageModal({{ expense.act_expense_id }}, '{{ expense.act_expense_date|date:"Y-m-d" }}', '{{ expense.prop.prop_name }}', '{{ expense.act_expense_description }}', '{{ expense.act_expense_amount }}', '{{ expense.act_expense_approved }}', '{{ expense.act_expense_paid }}', {% if expense.act_expense_document %}'{{ expense.act_expense_document.url }}', '{{ expense.act_expense_document.name }}'{% else %}null, null{% endif %}, {{ user.is_superuser|yesno:"true,false" }}, {{ perms.auth.can_edit_expenses|yesno:"true,false" }})">
                        <i class="fas fa-folder-open mobile-action-icon icon-color-manage"></i>
                        <span class="mobile-action-label">Manage</span>
                    </button>
                {% else %}
                    <span class="mobile-action-btn mobile-action-disabled">
                        <i class="fas fa-folder-open mobile-action-icon"></i>
                        <span class="mobile-action-label">Manage</span>
                    </span>
                {% endif %}
            </td>
        {% endif %}
    </tr>
    {% endfor %}
</tbody>
</table>

{% if not expenses %}
    <!-- An empty tbody looks exactly like a page that failed to load. -->
    <div class="alv-empty">
        <i class="fas fa-receipt"></i>
        <div class="alv-empty-title">No expenses to show</div>
        <div class="alv-empty-hint">
            Nothing matches the current filter. Clear it, or add an expense.
        </div>
    </div>
{% endif %}
</div>
'''

NEW_REPORT = r'''          <div id="reportContent" style="display:none;">
            <div class="report-chart-wrap"><canvas id="reportChart"></canvas></div>
            <div class="report-grand-total" id="reportGrandTotal"></div>
            <!-- The population, said on the face of the report. The query has
                 always filtered to approved AND paid, while the docstring above
                 it claimed the opposite - so a property carrying approved-but-
                 unpaid expenses read as a smaller number here than in the grid,
                 and nothing on screen said why. The figures are unchanged; what
                 changed is that the report now admits what it counts. -->
            <p class="report-basis">
              <i class="fas fa-info-circle"></i>
              Counts expenses that are <strong>approved and paid</strong>. Anything
              still awaiting approval or payment is not included, so these totals
              can be lower than the list behind this window.
            </p>
            <div class="table-container">
              <table class="table alv-table report-table">
                <thead>
                  <tr>
                    <th style="text-align: left">Property</th>
                    <th class="num">Expenses</th>
                    <th class="num"># Items</th>
                  </tr>
                </thead>
                <tbody id="reportTableBody"></tbody>
              </table>
            </div>
            <p class="text-muted small mb-0"><i class="fas fa-hand-pointer"></i> Click a bar or a row to see that property's expenses.</p>
          </div>
        </div>

        <div id="reportDrill" style="display:none;">
          <button type="button" class="btn action-back btn-sm mb-3" id="reportDrillBack">
            <i class="fas fa-arrow-left"></i> Back to overview
          </button>
          <h6 id="reportDrillTitle" class="report-drill-title"></h6>
          <!-- Approved and Paid used to be columns here. They could only ever
               read "Yes": the endpoint behind this table filters on exactly
               those two fields, so both were constant by construction and the
               red branch of statusBadge() was unreachable. Two columns of a
               narrow report saying nothing. The note above the overview says it
               once instead. -->
          <div class="table-container">
            <table class="table alv-table report-drill-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th style="text-align: left">Description</th>
                  <th class="num">Amount</th>
                  <th>Invoice</th>
                </tr>
              </thead>
              <tbody id="reportDrillBody"></tbody>
            </table>
          </div>
          <div class="report-drill-total" id="reportDrillTotal"></div>
        </div>
'''

NEW_CSS = r'''
/* ============================================================
   ACTUAL EXPENSES - what is left after base took the rest
   ============================================================ */

/* The verify icon sat on `style="cursor: pointer; margin-left: 8px"`. Its
   COLOUR was already a class; its shape was not, so half of it was out of
   reach of this stylesheet. */
.verify-icon { cursor: pointer; margin-left: 8px; }

/* The status columns are pills now, so the only thing left inside them is the
   one branch that is still a control. base owns .status-btn - the page used to
   override it with `border: 1px solid black`, a colour that appears nowhere
   else in the system. This wrapper is all the page still needs. */
.exp-inline-form { display: inline; }

/* A spanning cell inside the report tables that is a message rather than a
   row - loading, empty, failed. base has no name for one, because every other
   list page puts its empty state OUTSIDE the table where it needs no colspan;
   these two tables are filled by JavaScript, which cannot reach outside the
   tbody it owns. */
.report-note-cell {
    text-align: center;
    color: var(--alv-ink-soft);
    padding: 18px 8px;
}
.report-note-cell.is-bad { color: var(--alv-bad); }

/* The population of the report, stated on its face. Quiet: it is a caveat, not
   a warning - the figures are right, they simply describe a narrower set than
   the list behind the window. */
.report-basis {
    color: var(--alv-ink-soft);
    font-size: 12.5px;
    line-height: 1.45;
    margin: -4px 0 12px;
}
.report-basis i { color: var(--alv-ink-faint); margin-right: 4px; }

/* Viewing a document is the VIEW verb, and base has a colour for it. This was
   #28a745 - Bootstrap's success green - which said "good" about an icon that
   only opens a file. */
.report-invoice-icon { cursor: pointer; color: var(--alv-view); }
.report-invoice-none { color: var(--alv-ink-faint); }

/* The overview rows are click targets; base tints a row on hover, but nothing
   in base says a row can be CLICKED. */
.report-table tbody tr { cursor: pointer; }

/* The report modal's own title icon carried `style="color:#0e7c8b"` - the
   accent as a literal, in the one place a token cannot reach. */
.expense-report-dialog .modal-title i { color: var(--alv-accent); }
'''

BASE_CSS = r'''

/* Manage: the third NAME on an existing colour, and for the same reason as
   Duplicate and Upload. Opening an expense's record - its details, its invoice
   document, its delete tab - is a VIEW, so it points at --alv-view, the same
   colour the eye already wears.

   It gets its own name rather than reusing .icon-view because a class carries
   ONE picture. `test_icon_buttons.py` §1b exists because .icon-edit had drifted
   to two glyphs across the system; hanging fa-folder-open on .icon-view beside
   the fa-eye it already carries would be that same fault, one class along.
   Alias the colour, never the name. */
.icon-manage       { color: var(--alv-view); border-color: var(--alv-accent-line); }
.icon-manage:hover { background-color: var(--alv-view); border-color: var(--alv-view); color: var(--alv-on-accent); }
.icon-color-manage { color: var(--alv-view); }
'''

JS_BLOCKS = r'''### OVERVIEW_ROW
            tr.innerHTML = '<td data-label="Property" style="text-align: left">' + escapeHtml(r.prop_name) + '</td><td data-label="Expenses" class="num">' + euro(r.total) + '</td><td data-label="# Items" class="num">' + r.count + '</td>';
### DRILL_LOADING
        document.getElementById('reportDrillBody').innerHTML = '<tr><td colspan="4" class="report-note-cell"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';
### DRILL_EMPTY
                    body.innerHTML = '<tr><td colspan="4" class="report-note-cell">No expenses for this property in the selected year(s).</td></tr>';
### DRILL_ROW
                        tr.innerHTML =
                            '<td data-label="Date">' + e.date + '</td>' +
                            '<td data-label="Description" style="text-align: left">' + escapeHtml(e.description) + '</td>' +
                            '<td data-label="Amount" class="num">' + euro(e.amount) + '</td>' +
                            '<td data-label="Invoice">' + inv + '</td>';
### DRILL_FAILED
                document.getElementById('reportDrillBody').innerHTML = '<tr><td colspan="4" class="report-note-cell is-bad">Failed to load.</td></tr>';
### STATUS_BADGE
    // statusBadge() is gone. It returned an inline-styled span in #28a745 or
    // #dc3545 - two Bootstrap colours reachable by no stylesheet - for the
    // Approved and Paid columns of the drill table. Those columns are gone
    // too: the endpoint behind that table filters on approved='Yes' AND
    // paid='Yes', so both were constant by construction and the red branch
    // never ran. The report says its population once, above the overview.
'''


JS = blocks(JS_BLOCKS)

# ---------------------------------------------------------------- the page
MAIN_START = '<!-- Expenses Table -->'
MAIN_END = '<!-- Main Management Modal with 3 Tabs -->'
REPORT_START = '          <div id="reportContent" style="display:none;">'
TITLE_ICON_OLD = ('<i class="fas fa-chart-bar" style="color:#0e7c8b;"></i> '
                  'Expenses by Property')
TITLE_ICON_NEW = '<i class="fas fa-chart-bar"></i> Expenses by Property'

# EVERYTHING BELOW THE ANALYSIS MODAL IS OUT OF SCOPE this round, and it holds
# its own Bootstrap colours - a check that reads the whole file reports them and
# looks like a fault in work that was never touched.
ANALYSIS_MARK = '<!-- ==================== EXPENSES vs RENT'


def in_scope(text):
    i = text.find(ANALYSIS_MARK)
    return text if i < 0 else text[:i]
REPORT_END = '\n\n      </div>\n    </div>\n  </div>\n</div>\n\n\n<!-- Standard PDF Viewer'

DROP = (
    # base owns the shell, and its overflow:clip is deliberate. The page's own
    # wrapper used overflow:hidden, which is what stopped the heading sticking.
    '.expense-table-wrapper',
    '.expense-table',
    '.expense-table thead',
    '.expense-table, .expense-table tbody, .expense-table tr',
    '.expense-table tr',
    '.expense-table tr:hover',
    '.expense-table td',
    '.expense-table td:first-child',
    '.expense-table td:not(:first-child)::before',
    '.expense-table td.cell-property',
    '.expense-table td.cell-action',
    '.expense-table td.cell-action:first-of-type',
    '.expense-table td.cell-action::before',
    '.expense-table td.cell-action .status-btn, .expense-table td.cell-action form, '
    '.expense-table td.cell-action button',
    '.expense-table td.cell-action .status-btn',
    # the page was overriding base's own button with a BLACK border.
    '.expense-table .status-btn',
    '.expense-table .status-btn.is-disabled',
    # the button sweep moved these into base and left the page's copies.
    '.page-action-buttons .action-more-wrapper',
    '.action-more-menu',
    '.action-more-item:hover, .action-more-item:active, .action-more-item:focus',
    '.action-back-label',
    # base's mobile card conversion does all of this for both report tables.
    '.report-table tbody tr',
    '.report-table tbody tr:hover',
    '.report-table th, .report-table td',
    '.report-table td:first-child',
    '.report-drill-table thead',
    '.report-drill-table, .report-drill-table tbody, .report-drill-table tr, '
    '.report-drill-table td',
    '.report-drill-table tr',
    '.report-drill-table td',
    '.report-drill-table td::before',
    '.report-drill-table td[data-label="Description"]',
    '.report-drill-table td[data-label="Description"]::before',
    '.report-drill-table td[colspan]',
    '.report-drill-table td[colspan]::before',
    # replaced by .report-invoice-icon on the view token.
    '.report-invoice-icon',
    '.report-invoice-none',
)

# `.expense-table td.cell-amount` is NOT dropped: it is the mobile card's
# emphasis on the money, which base has no opinion about.


def drop_rules(text, drop):
    dropped, missing = 0, list(drop)
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
        css = text[a:z]
        out, cur = [], 0
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
            if sel in drop:
                out.append(css[cur:m.start()]); cur = m.end(); dropped += 1
                while sel in missing:
                    missing.remove(sel)
        if out:
            out.append(css[cur:])
            text = text[:a] + ''.join(out) + text[z:]
    return text, dropped, missing


def uncomment(text):
    """Every kind of comment this file can hold, removed.

    A CHECK THAT READS TEXT CATCHES PROSE. This round hit it three times in one
    patcher before a line was written: the note explaining that "Approve First"
    was removed contains the words Approve First; the note explaining that
    #32CD32 was removed contains #32CD32; the JavaScript comment explaining
    that statusBadge() is gone contains the word statusBadge. Each one reported
    a fault that had in fact been fixed.

    So the strippers come first and everything else reads their output:
    HTML comments, Django comments, CSS block comments, and both JavaScript
    comment forms - the last carefully, because a // inside a string literal
    (an http:// URL, say) is not a comment.
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)

    def strip_js(m):
        body = m.group(2)
        body = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
        out = []
        for line in body.split('\n'):
            # Only a // that starts a line (after whitespace) is treated as a
            # comment. Anything else risks eating half a URL.
            out.append('' if line.lstrip().startswith('//') else line)
        return m.group(1) + '\n'.join(out) + m.group(3)

    text = re.sub(r'(<script[^>]*>)(.*?)(</script>)', strip_js, text, flags=re.S)
    text = re.sub(r'(<style[^>]*>)(.*?)(</style>)',
                  lambda m: m.group(1) + re.sub(r'/\*.*?\*/', '', m.group(2),
                                                flags=re.S) + m.group(3),
                  text, flags=re.S)
    return text


def markup_of(text):
    """The elements alone: no stylesheet, no scripts, no commentary.

    On THIS page the scripts must go too - the report row builders are markup
    inside string literals, so a check about the template's own elements would
    otherwise read them.
    """
    text = uncomment(text)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.S)
    return text


def scripts_of(text):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',
                                uncomment(text), re.S))


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        shutil.copy2(p, b)


# ------------------------------------------------------------- the JS edits
JS_EDITS = [
    ("tr.innerHTML = '<td>' + escapeHtml(r.prop_name) + '</td><td class=\"text-right\">'"
     " + euro(r.total) + '</td><td class=\"text-center\">' + r.count + '</td>';",
     'OVERVIEW_ROW', 'the overview row builder'),
    ('document.getElementById(\'reportDrillBody\').innerHTML = \'<tr><td colspan="6" '
     'class="text-center text-muted"><i class="fas fa-spinner fa-spin"></i> '
     'Loading...</td></tr>\';',
     'DRILL_LOADING', 'the drill loading row'),
    ('body.innerHTML = \'<tr><td colspan="6" class="text-center text-muted">No '
     'expenses for this property in the selected year(s).</td></tr>\';',
     'DRILL_EMPTY', 'the drill empty row'),
    ('document.getElementById(\'reportDrillBody\').innerHTML = \'<tr><td colspan="6" '
     'class="text-center text-danger">Failed to load.</td></tr>\';',
     'DRILL_FAILED', 'the drill failure row'),
]

DRILL_ROW_OLD = """                        tr.innerHTML =
                            '<td data-label="Date">' + e.date + '</td>' +
                            '<td data-label="Description">' + escapeHtml(e.description) + '</td>' +
                            '<td data-label="Amount" class="text-right">' + euro(e.amount) + '</td>' +
                            '<td data-label="Approved" class="text-center">' + statusBadge(e.approved) + '</td>' +
                            '<td data-label="Paid" class="text-center">' + statusBadge(e.paid) + '</td>' +
                            '<td data-label="Invoice" class="text-center">' + inv + '</td>';"""

STATUS_BADGE_OLD = """    function statusBadge(v) {
        var yes = (v === 'Yes');
        return '<span style="color:' + (yes ? '#28a745' : '#dc3545') + ';font-weight:600;">' + (yes ? 'Yes' : 'No') + '</span>';
    }"""

# ----------------------------------------------------------------- the view
DOC_OLD_A = """    Aggregates ALL expense rows (same population as act_expense_all),
    regardless of approved/paid status."""
DOC_NEW_A = """    Counts only expenses that are BOTH approved and paid. This docstring
    used to claim the opposite - "ALL expense rows ... regardless of
    approved/paid status" - while the line below it filtered on both
    fields, so the report quietly under-reported any property carrying
    approved-but-unpaid expenses and nothing on screen said why.

    Decided 28 Aug 2026: the behaviour is right and the words were wrong.
    No figure moved. The report states this population on its own face."""

DOC_OLD_B = """    JSON for the report drill-down: individual expenses for one property
    across the selected year(s), most recent first, with the attached
    document URL/name so the front-end can open it in the shared viewer."""
DOC_NEW_B = """    JSON for the report drill-down: individual expenses for one property
    across the selected year(s), most recent first, with the attached
    document URL/name so the front-end can open it in the shared viewer.

    Approved AND paid only, matching act_expense_report_data. Which is why
    the drill table no longer draws Approved and Paid columns: filtered on
    exactly those two fields, both could only ever read "Yes"."""


def main():
    psrc, bsrc, vsrc = read(PAGE), read(BASE), read(VIEW)

    if 'icon-action-btn icon-manage' in psrc and '.icon-manage' in bsrc:
        print('  actual expenses            already migrated')
        print('\n  0 file(s) changed')
        return

    # ---- base.html: one new NAME on an existing colour
    if '.icon-manage' in bsrc:
        bout, bn = bsrc, 0
    else:
        anchor = '.icon-color-duplicate { color: var(--alv-edit); }'
        one(bsrc, anchor, 'the duplicate alias')
        bout = bsrc.replace(anchor, anchor + BASE_CSS.rstrip('\n'), 1)
        bn = 1

    # ---- the main table
    i = psrc.find(MAIN_START)
    j = psrc.find(MAIN_END)
    if i < 0 or j < 0 or j <= i:
        sys.exit('! the expenses table could not be located')
    one(psrc, MAIN_START, 'the expenses table')
    one(psrc, MAIN_END, 'the manage modal')
    pout = psrc[:i] + NEW_MAIN.rstrip('\n') + '\n\n' + psrc[j:]

    # ---- the report modal's own title icon carried the accent as a LITERAL.
    # base has owned --alv-accent since the teal round; a hex in a style
    # attribute is the one place a token cannot reach.
    one(pout, TITLE_ICON_OLD, 'the report modal title icon')
    pout = pout.replace(TITLE_ICON_OLD, TITLE_ICON_NEW, 1)

    # ---- the two report tables
    a = pout.find(REPORT_START)
    z = pout.find(REPORT_END)
    if a < 0 or z < 0 or z <= a:
        sys.exit('! the report modal tables could not be located')
    pout = pout[:a] + NEW_REPORT.rstrip('\n') + pout[z:]

    # ---- the JavaScript that builds those rows
    jn = 0
    for old, key, what in JS_EDITS:
        one(pout, old, what)
        pout = pout.replace(old, JS[key], 1)
        jn += 1
    one(pout, DRILL_ROW_OLD, 'the drill row builder')
    pout = pout.replace(DRILL_ROW_OLD, JS['DRILL_ROW'], 1)
    one(pout, STATUS_BADGE_OLD, 'statusBadge')
    pout = pout.replace(STATUS_BADGE_OLD, JS['STATUS_BADGE'], 1)
    jn += 2

    pout, dropped, missing = drop_rules(pout, DROP)
    if missing:
        sys.exit('! expected on act_expense.html and not found:\n   - %s'
                 % '\n   - '.join(sorted(set(missing))))

    # The page has THREE style blocks; the page-specific additions belong to
    # the first, which is the page's own, not the report modal's and certainly
    # not the analysis modal's (which is out of scope this round).
    k = pout.find('</style>')
    if k < 0:
        sys.exit('! no </style> to append to')
    pout = pout[:k] + NEW_CSS + pout[k:]

    # ---- the view: two docstrings that said the opposite of their code
    one(vsrc, DOC_OLD_A, 'the report_data docstring')
    one(vsrc, DOC_OLD_B, 'the report_property docstring')
    vout = vsrc.replace(DOC_OLD_A, DOC_NEW_A, 1).replace(DOC_OLD_B, DOC_NEW_B, 1)

    # ---- self-check BEFORE anything is written
    bad = []
    _scoped = in_scope(pout)
    _mk = markup_of(_scoped)
    _js = scripts_of(_scoped)

    for gone in ('expense-table-wrapper', 'table-bordered', 'table-striped',
                 'text-center expense-table', 'Approve First',
                 'status-btn is-disabled'):
        if gone in _mk:
            bad.append('%s survived in the markup' % gone)
    # cell-action is a PREFIX of cell-actions, which the new markup uses. A
    # plain `in` reported the old per-verb cell surviving on a page that had
    # replaced it with the house one.
    if re.search(r'cell-action(?![-\w])', _mk):
        bad.append('the old per-verb cell-action class survived in the markup')
    _inline = [s for s in re.findall(r'style="[^"]*"', _mk)
               if re.search(r'colou?r\s*:', s)]
    if _inline:
        bad.append('an inline style still sets a colour: %s' % _inline[:2])
    _code = uncomment(_scoped)
    for hexed in ('#32CD32', '#DC143C'):
        if hexed in _code:
            bad.append('%s survives somewhere in the file' % hexed)
    if 'statusBadge' in _js:
        bad.append('statusBadge is still called or defined in a script')
    for hexed in ('#28a745', '#dc3545'):
        if hexed in _js:
            bad.append('%s survives inside a <script>' % hexed)
    if 'colspan="6"' in _js:
        bad.append('a drill row still spans 6 columns')
    # The scoping must not be doing the work. If the analysis modal were not
    # there at all, in_scope() would be the identity and these checks would
    # silently widen - so assert the boundary was actually found.
    if ANALYSIS_MARK not in pout:
        bad.append('the analysis-modal boundary was not found, so the '
                   'out-of-scope half is not being excluded - it is being '
                   'checked, or it has moved')
    if len(_scoped) >= len(pout):
        bad.append('in_scope() returned the whole file')

    for want in ('class="table alv-table expense-table"',
                 'class="table alv-table report-table"',
                 'class="table alv-table report-drill-table"',
                 'icon-action-btn icon-manage', 'fa-folder-open',
                 'alv-pill alv-pill-good', 'alv-pill alv-pill-attn',
                 'alv-pill alv-pill-neutral', 'alv-empty-title',
                 'mobile-action-bar cols-1', 'report-basis',
                 '.expense-report-dialog .modal-title i'):
        if want not in pout:
            bad.append('expected in the template and missing: %s' % want)
    for owed in ('.icon-manage', '.alv-pill-neutral', '.alv-empty',
                 '.table-container', '.mobile-action-bar.cols-1',
                 '.status-btn'):
        if owed not in bout:
            bad.append('base.html does not define %s' % owed)
    if bout.count('.icon-manage ') + bout.count('.icon-manage:') != 2:
        bad.append('base defines .icon-manage the wrong number of times')
    if re.search(r'\.icon-manage[^{]*\{[^}]*#[0-9A-Fa-f]{6}', bout):
        bad.append('.icon-manage introduced a NEW hex - it must alias a token')

    # A status must not be a disabled button anywhere in the two columns.
    _seg = _mk[_mk.find('data-label="Approved?"'):_mk.find('data-label="Actions"')]
    if 'button' in _seg and 'disabled' in _seg:
        bad.append('a disabled button survives in the status columns')

    # The view really did lose the claim, and kept the code.
    if 'regardless of approved/paid status' in vout:
        bad.append('the report docstring still claims it counts everything')
    if "filter(act_expense_approved='Yes', act_expense_paid='Yes')" not in vout:
        bad.append('the report query was CHANGED - this round moves no figure')

    ifs = len(re.findall(r'\{%\s*if\b', pout))
    endifs = len(re.findall(r'\{%\s*endif\s*%\}', pout))
    fors = len(re.findall(r'\{%\s*for\b', pout))
    endfors = len(re.findall(r'\{%\s*endfor\s*%\}', pout))
    withs = len(re.findall(r'\{%\s*with\b', pout))
    endwiths = len(re.findall(r'\{%\s*endwith\s*%\}', pout))
    if ifs != endifs:
        bad.append('if/endif do not balance (%d/%d)' % (ifs, endifs))
    if fors != endfors:
        bad.append('for/endfor do not balance (%d/%d)' % (fors, endfors))
    if withs != endwiths:
        bad.append('with/endwith do not balance (%d/%d)' % (withs, endwiths))
    if len(re.findall(r'<div\b', pout)) != len(re.findall(r'</div\s*>', pout)):
        bad.append('div tags do not balance')
    if len(re.findall(r'<table\b', pout)) != len(re.findall(r'</table\s*>', pout)):
        bad.append('table tags do not balance')
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pout, re.S))
    if css.count('{') != css.count('}'):
        bad.append('CSS braces do not balance')
    _open = [i for i, l in enumerate(pout.split('\n'), 1)
             if '{#' in l and '#}' not in l]
    if _open:
        bad.append('a Django comment spans lines (%s) - it would render as '
                   'visible text' % _open)
    try:
        compile(vout, 'expenses.py', 'exec')
    except SyntaxError as e:
        bad.append('the patched view does not parse: %s' % e)

    if bad:
        sys.exit('! actual expenses self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    n = 2 + (1 if bn else 0)
    if bn:
        print('  base.html                   .icon-manage - a NAME on --alv-view')
    print('  act_expense.html            rules dropped:%d, script edits:%d' % (dropped, jn))
    print('     a status is a pill; only what can be pressed is a button')
    print('  pages/views/expenses.py     two docstrings now match their code')
    print('     no figure moves - the report says its population instead')

    if not CHECK:
        for p in (BASE, PAGE, VIEW):
            backup(p)
        for p, out in ((BASE, bout), (PAGE, pout), (VIEW, vout)):
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  %d file(s) %s' % (n, 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
