"""PL-1 - THE DRILL-DOWN GETS AN INVOICE COLUMN.

   Demetri, 5 Oct 2026, of Dashboard -> Profit & Loss: "when I click on
   an Actual Expense figure, I get the list of Invoices making up that
   figure, which is correct. However, to view a copy of a specific
   invoice I need to click the little black tick. This is not intuitive.
   I prefer the option of the Actual Expenses ... It is more intuitive."

   HE IS RIGHT, AND THE REASON IS WORTH NAMING. The little black tick is
   `verify_badge` - a STATUS glyph. It says "Invoice verified", or
   mismatched, or not checked, and it draws fa-check-circle,
   fa-exclamation-triangle, fa-question-circle, fa-file or
   fa-object-group depending which. It is also, and only, the way to open
   the document. A status indicator doing duty as a control is the same
   mistake RA-2 spent a round on in a different costume: nothing about a
   tick says DOCUMENT, so nobody would think to press it.

   The Actual Expenses screen he prefers has it right - a column headed
   INVOICE, a document icon in it, and a plain dash where there is none.
   The modal is a scrape of THIS page's table, so this is where the
   column has to be added.

   NOTHING IS TAKEN AWAY. The tick keeps working: it is still a status
   badge and still opens the document if pressed. The round adds the
   obvious control beside it rather than moving the hidden one, because
   the complaint was that the only way in was unfindable - not that the
   tick was wrong about anything.

   ONLY IN THE DRILL-DOWN. The full Actual Expenses page already carries
   an Actions column with .report-invoice-icon in it; it is the
   from_finance_pl_act branch - the one the modal scrapes, which hides
   Approved, Paid and Actions to fit - that had no document control of
   its own. So both edits sit inside that branch and the full page is
   untouched.

   WHAT THIS ROUND CANNOT SHOW YOU. The modal builds itself by fetching
   this page over AJAX and lifting `table.table` out of the response.
   Nothing in this sandbox can run that fetch, so the suite renders the
   TABLE - the thing that is scraped - and checks the column is in it,
   in the right place, with the right icon. Whether the modal then
   displays it is Demetri's to confirm on Live.

   FILES: act_expense.html.                    [test_pl_invoice_col.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_plinvcol'

HEAD_OLD = '''        <th class="num" style="width: {% if from_finance_pl_act %}20%{% else %}12%{% endif %}">Amount</th>
        {% if not from_finance_pl_act %}'''

HEAD_NEW = '''        <th class="num" style="width: {% if from_finance_pl_act %}15%{% else %}12%{% endif %}">Amount</th>
        {% if from_finance_pl_act %}
            {# PL-1, 5 Oct 2026 - a column that says INVOICE. #}
            {# #}
            {# The drill-down's only way to open a document was the #}
            {# verify badge beside the property name - a STATUS glyph #}
            {# that draws a tick, or a warning triangle, or a question #}
            {# mark. Nothing about a tick says document, so nobody #}
            {# would think to press it. Demetri: "This is not #}
            {# intuitive. I prefer the option of the Actual Expenses." #}
            {# Same shape as that screen: a named column, a document #}
            {# icon, a dash where there is none. #}
            {# #}
            {# ONE COMMENT PER LINE, and this is not style. Django's #}
            {# comment lexer has no DOTALL - one that does not close #}
            {# on its own line is not a comment, and the rest of it #}
            {# renders into the page. The first build of this round #}
            {# wrote a six-line block and three suites caught it. #}
            <th style="width: 10%">Invoice</th>
        {% endif %}
        {% if not from_finance_pl_act %}'''

CELL_OLD = '''        <td data-label="Amount" class="num cell-amount">&euro;{{ expense.act_expense_amount|floatformat:2|intcomma }}</td>
        {% if not from_finance_pl_act %}'''

CELL_NEW = '''        <td data-label="Amount" class="num cell-amount">&euro;{{ expense.act_expense_amount|floatformat:2|intcomma }}</td>
        {% if from_finance_pl_act %}
            {# PL-1 - the control property_detail's Actual Expenses #}
            {# table uses, which is the screen Demetri named: a #}
            {# fa-file-alt on the data attributes the drill-down's #}
            {# handler reads. A dash, not an empty cell, so "no #}
            {# invoice" is stated rather than implied. #}
            <td data-label="Invoice" class="cell-invoice">
                {% if expense.act_expense_document %}
                    <i class="fas fa-file-alt report-invoice-icon"
                       title="View invoice"
                       aria-label="View invoice"
                       data-invoice-url="{{ expense.act_expense_document.url }}"
                       data-filename="{{ expense.act_expense_document.name }}"></i>
                {% else %}
                    <span class="report-invoice-none">&mdash;</span>
                {% endif %}
            </td>
        {% endif %}
        {% if not from_finance_pl_act %}'''

# ------------------------------------------------- and the handler
#
# THE SUITE CAUGHT THIS, AND IT WOULD HAVE SHIPPED A DEAD BUTTON. The
# drill-down's own handler in finance_pl_act.html listens for
# `.verify-icon` and nothing else:
#
#     $(document).off('click', '.verify-icon')
#               .on('click', '.verify-icon', ...)
#
# so the new column's .report-invoice-icon - the class the full page and
# the Report modal both use, and the right name for the thing - would
# have been a document icon that did nothing when pressed. Worse than
# the unfindable tick, which at least worked.
#
# The handler listens for both. The class stays .report-invoice-icon,
# because the name should say what the control IS rather than which
# listener happens to be wired to it.
HANDLER_OLD = ("$(document).off('click', '.verify-icon')"
               ".on('click', '.verify-icon', function(e) {")
HANDLER_NEW = ("$(document).off('click', '.verify-icon, .report-invoice-icon')"
               ".on('click', '.verify-icon, .report-invoice-icon', "
               "function(e) {")

PARTS = [(HEAD_OLD, HEAD_NEW), (CELL_OLD, CELL_NEW)]


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    path = T.path_of('act_expense.html')
    text = read(path)
    done = 0

    for old, new in PARTS:
        if fit(text, new) in text:
            continue
        o = fit(text, old)
        n = text.count(o)
        if n != 1:
            raise SystemExit('PL-1: an anchor matched %d times, expected 1. '
                             'The page has moved since this was measured; '
                             'look at it rather than let the round guess.' % n)
        text = text.replace(o, fit(text, new), 1)
        done += 1

    if done and not check:
        backup(path)
        write(path, text)

    # the handler, in the page that owns the modal
    pl = T.path_of('finance_pl_act.html')
    ptext = read(pl)
    wired = 0
    if HANDLER_NEW not in ptext:
        n = ptext.count(HANDLER_OLD)
        if n != 1:
            raise SystemExit('PL-1: the drill-down handler matched %d times, '
                             'expected 1' % n)
        ptext = ptext.replace(HANDLER_OLD, HANDLER_NEW, 1)
        if not check:
            backup(pl)
            write(pl, ptext)
        wired = 1

    print('PL-1  drill-down edits : %d' % done)
    print('PL-1  handler widened  : %d' % wired)

    if check:
        if done or wired:
            print('PL-1  NOT APPLIED')
            return 1
        print('PL-1  applied')
        return 0
    # BOTH OR NEITHER. A header with no cell shifts every column in the
    # scraped table one place to the left, which is worse than the
    # unfindable tick this round exists to replace.
    if done not in (0, len(PARTS)):
        print('PL-1  REFUSED: partial application (%d of %d)'
              % (done, len(PARTS)))
        return 2
    print('PL-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
