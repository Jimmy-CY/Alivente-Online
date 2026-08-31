#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The P&L drill-downs: the two identical fragments, and a wrapper that scrolls.

THE MODAL DOES NOT OWN ITS TABLE. Clicking a Revenue or Expense figure on the
P&L fires an AJAX request at ANOTHER PAGE and scrapes a table out of the reply:

    var $temp  = $('<div>').html(data);
    var $table = $temp.find('table.table').first();
    $('#revenueDetailsContent').html($('<div class="table-responsive">').append($table));

Everything except the <table> ELEMENT is discarded - the fragment's headings,
its wrapper divs, an empty-state alert sitting outside the table. That is worth
writing down, because it decides what this round may change: whatever the modal
must show has to be INSIDE the table, and the wrapper has to be built here, in
the page doing the scraping, not in the fragment being scraped.

TWO OF THE THREE FRAGMENTS ARE THE SAME FILE. revenue_details.html and
budget_expense_details.html differ in the loop variable and one sentence of
empty-state prose. Nothing else. Both carried:

  * `table table-sm table-bordered` with `thead-light`      - Bootstrap
  * a totals row in the TBODY, `class="font-weight-bold"`,
    `style="background-color: #f8f9fa"`                     - an inline literal
  * `class="text-right"` on the money column, twice per row - and again in the
    page's CSS, as a :nth-child(2) rule, so three rules aligned one column

They become `table alv-table` (the house pairing act_expense.html already
uses, and the pairing the scraper's own `table.table` selector needs), `.num`
on the money column, and a real `<tfoot>` - the element base gained on 29 Aug,
which repeats on every printed page where a tbody row cannot.

THE WRAPPER IS THE INTERESTING PART. It is NOT .table-container: that is
`overflow: clip` by design, and this one has to scroll, because a month of
revenue is longer than a modal. It keeps the 60vh vertical scroll the page
already had, under a name of its own rather than Bootstrap's .table-responsive.

And because it scrolls, base's sticky `.alv-table thead th` finally has a
scroll container to stick TO - the Property / Amount heading now stays put
through a sixty-row list. The sticky sweep spent a round on containers that
scroll when they should not; this is the same mechanism, the right way round.

WHAT THIS ROUND DOES NOT DO. The Financial Indicators and Vacancy Management
modal (one modal, duplicated across two files, stating each verdict five times)
is the next round. Vacancy's Detailed Property Data table, the .table-container
name collision those two pages carry, and the last hand-rolled segmented
control are the round after that. Nor does it touch the P&L's own main grid at
line 225 - `.table-responsive.pl-table-wrap` is that table's wrapper and a
different question.

ALSO FOUND, DELIBERATELY NOT TOUCHED: total_expense_details.html renders
through total_expense_details_view at a live URL that NO template links to.
120 lines and a view, unreachable. Removing a URL is a different class of
change from restyling a table, so it goes on the list rather than into this
patcher.

Run from the repo root.  --check plans without writing.
"""
import os
import re
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(T, 'finance_pl_act.html')
REV = os.path.join(T, 'revenue_details.html')
BUD = os.path.join(T, 'budget_expense_details.html')
BASE = os.path.join(T, 'base.html')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_pldrill'

SENTINEL = '.pl-drill {'


# ---------------------------------------------------------------------------
# 1. the two fragments
# ---------------------------------------------------------------------------
def old_fragment(var, noun):
    return """<div class="container-fluid">
    <div class="table-responsive">
        <table class="table table-sm table-bordered">
            <thead class="thead-light">
                <tr>
                    <th>Property</th>
                    <th class="text-right">Amount (€)</th>
                </tr>
            </thead>
            <tbody>
                {%% for item in %(var)s %%}
                <tr>
                    <td>{{ item.property.prop_name }}</td>
                    <td class="text-right">{{ item.amount|floatformat:"2"|intcomma }}</td>
                </tr>
                {%% empty %%}
                <tr>
                    <td colspan="2" class="text-center">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            No %(noun)s data found for the selected criteria.
                        </div>
                    </td>
                </tr>
                {%% endfor %%}
                
                {%% if %(var)s %%}
                <tr class="font-weight-bold" style="background-color: #f8f9fa">
                    <td>Total:</td>
                    <td class="text-right">
                        {{ total_amount|floatformat:"2"|intcomma }}
                    </td>
                </tr>
                {%% endif %%}
            </tbody>
        </table>
    </div>
</div>""" % {'var': var, 'noun': noun}


def new_fragment(var, empty_line):
    return """<!-- FETCHED, NOT RENDERED. finance_pl_act.html requests this over
     AJAX and keeps the TABLE ELEMENT ONLY - every wrapper, heading and alert
     outside it is discarded by the scraper. So anything the modal must show
     goes INSIDE the table, and the scrolling wrapper is built by the page
     doing the scraping. The old container-fluid and table-responsive wrappers
     were thrown away every time and are gone.

     An HTML comment and NOT {# #}: a Django comment does not span lines, and
     this one would have rendered five lines of prose above the table. That is
     the fault this round's own self-check caught in its first draft.

     No <style> here on purpose - the classes are base's, and base is loaded
     by the page this table lands in. -->
<div class="table-container">
    <table class="table alv-table">
        <thead>
            <tr>
                <th>Property</th>
                <th class="num">Amount (€)</th>
            </tr>
        </thead>
        <tbody>
            {%% for item in %(var)s %%}
            <tr>
                <td data-label="Property">{{ item.property.prop_name }}</td>
                <td class="num" data-label="Amount (€)">{{ item.amount|floatformat:"2"|intcomma }}</td>
            </tr>
            {%% empty %%}
            <tr>
                <td colspan="2">
                    <div class="alv-empty">
                        <i class="fas fa-info-circle"></i>
                        <div class="alv-empty-title">Nothing to show</div>
                        <div class="alv-empty-hint">%(empty)s</div>
                    </div>
                </td>
            </tr>
            {%% endfor %%}
        </tbody>
        {%% if %(var)s %%}
        <tfoot>
            <tr>
                <td>Total</td>
                <td class="num">{{ total_amount|floatformat:"2"|intcomma }}</td>
            </tr>
        </tfoot>
        {%% endif %%}
    </table>
</div>""" % {'var': var, 'empty': empty_line}


REV_OLD = old_fragment('revenue_items', 'revenue')
REV_NEW = new_fragment(
    'revenue_items',
    'No revenue was recorded for the properties and period selected.')
BUD_OLD = old_fragment('expense_items', 'budget expense')
BUD_NEW = new_fragment(
    'expense_items',
    'No budget expense was recorded for the properties and period selected.')

# ---------------------------------------------------------------------------
# 2. the page: one wrapper name, and column widths that stop repeating .num
# ---------------------------------------------------------------------------
P_OLD_CSS = """#revenueDetailsModal .table-responsive,
#budgetExpenseDetailsModal .table-responsive {
    width: 100%;
    overflow-x: visible;
    max-height: 60vh;
    overflow-y: auto;
}

#revenueDetailsModal .table th:nth-child(1),
#revenueDetailsModal .table td:nth-child(1),
#budgetExpenseDetailsModal .table th:nth-child(1),
#budgetExpenseDetailsModal .table td:nth-child(1) {
    width: 70%;
    min-width: 200px;
}
#revenueDetailsModal .table th:nth-child(2),
#revenueDetailsModal .table td:nth-child(2),
#budgetExpenseDetailsModal .table th:nth-child(2),
#budgetExpenseDetailsModal .table td:nth-child(2) {
    width: 30%;
    min-width: 100px;
    text-align: right;
}"""

P_NEW_CSS = """/* THE DRILL-DOWN WRAPPER.

   Deliberately NOT .table-container - that is `overflow: clip` by design,
   and this one HAS to scroll: a month of revenue is longer than a modal.
   It keeps the 60vh the page already had, under a name of its own rather
   than leaning on Bootstrap's .table-responsive.

   And because it scrolls, base's sticky .alv-table heading finally has a
   scroll container to stick TO - Property / Amount now stays put through a
   sixty-row list. The sticky sweep spent a round on containers that scroll
   when they should not; this is the same mechanism the right way round.

   Built HERE and not in the fragment because the scraper appends the fetched
   table element and discards every wrapper around it. */
.pl-drill {
    max-height: 60vh;
    overflow: auto;
    background: var(--alv-paper);
    border-radius: var(--alv-radius);
}

/* Two columns, and the second is money. WIDTH ONLY. The right-alignment
   comes from .num on the cells - one rule in base instead of four here, and
   a heading that cannot end up aligned differently from the figures under
   it, which is how the old :nth-child(2) rule and the two `text-right`
   classes managed to say the same thing three times. */
#revenueDetailsModal .alv-table th:first-child,
#revenueDetailsModal .alv-table td:first-child,
#budgetExpenseDetailsModal .alv-table th:first-child,
#budgetExpenseDetailsModal .alv-table td:first-child {
    width: 70%;
    min-width: 200px;
}
#revenueDetailsModal .alv-table th.num,
#revenueDetailsModal .alv-table td.num,
#budgetExpenseDetailsModal .alv-table th.num,
#budgetExpenseDetailsModal .alv-table td.num {
    width: 30%;
    min-width: 100px;
}"""

P_OLD_JS_EXP = (
    """$('#expenseDetailsContent').html($('<div class="table-responsive">')"""
    """.append($table));""")
P_NEW_JS_EXP = (
    """$('#expenseDetailsContent').html($('<div class="pl-drill">')"""
    """.append($table));""")

P_OLD_JS_REV = (
    """$('#revenueDetailsContent').html($('<div class="table-responsive">')"""
    """.append($table.clone()));""")
P_NEW_JS_REV = (
    """$('#revenueDetailsContent').html($('<div class="pl-drill">')"""
    """.append($table.clone()));""")

P_OLD_JS_BUD = (
    """$('#budgetExpenseDetailsContent').html($('<div class="table-responsive">')"""
    """.append($table));""")
P_NEW_JS_BUD = (
    """$('#budgetExpenseDetailsContent').html($('<div class="pl-drill">')"""
    """.append($table));""")

EDITS_REV = [('revenue_details.html joins the standard', REV_OLD, REV_NEW)]
EDITS_BUD = [('budget_expense_details.html, its twin', BUD_OLD, BUD_NEW)]
EDITS_PAGE = [
    ('the drill-down wrapper gets a name, and scrolls', P_OLD_CSS, P_NEW_CSS),
    ('  the actual-expense drill-down uses it', P_OLD_JS_EXP, P_NEW_JS_EXP),
    ('  the revenue drill-down uses it', P_OLD_JS_REV, P_NEW_JS_REV),
    ('  and the budget drill-down uses it', P_OLD_JS_BUD, P_NEW_JS_BUD),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:260]))
    return text.replace(old, new, 1)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NOT re.S. Django's {# #} does not span lines, and a stripper more
    # permissive than the lexer it models certifies the faults it catches.
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def skeleton(frag):
    """Tag-and-class shape, with the two things that legitimately differ -
    the loop variable and the empty-state sentence - removed. The fragments
    were copies of each other and must not silently stop being copies."""
    s = re.sub(r'<!--.*?-->', '', frag, flags=re.S)
    s = re.sub(r'\{[{%].*?[%}]\}', '{}', s, flags=re.S)
    s = re.sub(r'>[^<]*<', '><', s)
    return ' '.join(s.split())


def main():
    for p in (PAGE, REV, BUD, BASE):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    pg, rv, bd, bs = read(PAGE), read(REV), read(BUD), read(BASE)
    pg0 = pg

    if SENTINEL in pg:
        print('  P&L drill-downs                already applied')
        print('\n  0 file(s) changed')
        return

    for name, old, new in EDITS_REV:
        rv = one(rv, old, new, name)
    for name, old, new in EDITS_BUD:
        bd = one(bd, old, new, name)
    for name, old, new in EDITS_PAGE:
        pg = one(pg, old, new, name)

    # -----------------------------------------------------------------------
    # SELF-CHECK. Nothing is written unless every one of these holds.
    # -----------------------------------------------------------------------
    bad = []
    pc, bc = nocomment_html(pg), nocomment_html(bs)
    frags = (('revenue_details.html', nocomment_html(rv)),
             ('budget_expense_details.html', nocomment_html(bd)))

    for name, f in frags:
        if len(re.findall(r'<table\b', f)) != 1:
            bad.append('%s no longer holds exactly one table' % name)
        # THE SCRAPER'S OWN SELECTOR. `table.table` is what finance_pl_act.html
        # looks for first; dropping the Bootstrap class would send it down the
        # untested fallback branch.
        if 'class="table alv-table"' not in f:
            bad.append('%s must keep `table` beside `alv-table` - the page '
                       'scrapes it with table.table' % name)
        if '<tfoot>' not in f:
            bad.append('%s has no tfoot' % name)
        if f.count('class="num"') < 3:
            bad.append('%s: the money column is not .num in head, body and '
                       'foot (%d)' % (name, f.count('class="num"')))
        if f.count('data-label=') != 2:
            bad.append('%s: %d data-label(s), expected 2 - base builds the '
                       'phone card view from them' % (name, f.count('data-label=')))
        if 'alv-empty' not in f:
            bad.append('%s lost its empty state' % name)
        for _dead in ('thead-light', 'table-bordered', 'table-sm',
                      'text-right', 'font-weight-bold', 'alert alert-info',
                      'table-responsive', 'container-fluid'):
            if _dead in f:
                bad.append('%s: %s survives' % (name, _dead))
        if re.search(r'style="[^"]*background', f):
            bad.append('%s still paints a row inline' % name)
        if re.search(r'#[0-9a-fA-F]{3,8}\b', f):
            bad.append('%s carries a literal colour' % name)
        # The empty state must live INSIDE the table, because the scraper
        # keeps the <table> element and throws the rest away.
        _tbl = f[f.find('<table'):f.find('</table>')]
        if 'alv-empty' not in _tbl:
            bad.append('%s: the empty state is outside the table, so the '
                       'modal would show an empty box' % name)

    # THE TWO FRAGMENTS ARE COPIES. They must stay copies, or the next round
    # fixes one of them.
    if skeleton(rv) != skeleton(bd):
        bad.append('the two fragments have stopped being the same shape')

    # -- the page ----------------------------------------------------------
    if pc.count('.pl-drill') != 1:
        bad.append('.pl-drill is defined %d times' % pc.count('.pl-drill'))
    if pc.count('class="pl-drill"') != 3:
        bad.append('%d drill-downs use the wrapper, expected 3'
                   % pc.count('class="pl-drill"'))
    # NOT .table-container: that one clips, and this one has to scroll.
    if re.search(r'\.pl-drill\s*\{[^}]*overflow:\s*clip', pc):
        bad.append('the wrapper clips instead of scrolling')
    if not re.search(r'\.pl-drill\s*\{[^}]*overflow:\s*auto', pc):
        bad.append('the wrapper does not scroll')
    # The main P&L grid keeps ITS wrapper. This round is the modals only.
    if 'table-responsive pl-table-wrap' not in pc:
        bad.append("the page's own table lost its wrapper - out of scope")
    if 'table-responsive' in pc[pc.find('DRILL-DOWN MODALS'):]:
        bad.append('a drill-down still wraps in .table-responsive')
    if 'nth-child' in pc[pc.find('.pl-drill'):pc.find('.pl-drill') + 1400]:
        bad.append('the column widths still key off nth-child')
    if re.search(r'#(revenue|budgetExpense)DetailsModal[^{]*\{[^}]*text-align',
                 pc):
        bad.append('the page still aligns a column .num already aligns')
    # base has to actually own the classes the fragments now name.
    for _cls in ('.alv-table', '.table-container', '.alv-empty',
                 '.alv-table tfoot td'):
        if _cls not in bc:
            bad.append('base does not define %s' % _cls)
    for _tok in ('--alv-paper', '--alv-radius'):
        if '%s:' % _tok not in bc:
            bad.append('%s is referenced and never defined' % _tok)

    # -- structure ---------------------------------------------------------
    for name, f in (('page', pg), ('revenue', rv), ('budget', bd)):
        for o, c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                     (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
            if len(re.findall(o, f)) != len(re.findall(c, f)):
                bad.append('%s: a Django block no longer balances (%s)'
                           % (name, o))
        for _l in f.split('\n'):
            if _l.count('{#') != _l.count('#}'):
                bad.append('%s: a {# #} comment spans lines, which Django '
                           'renders' % name)
                break
    for name, f in frags:          # comment-stripped: the prose names tags
        for tag in ('div', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'td',
                    'th'):
            _o = len(re.findall(r'<%s\b' % tag, f))
            _c = len(re.findall(r'</%s\s*>' % tag, f))
            if _o != _c:
                bad.append('%s: %d <%s> open, %d close' % (name, _o, tag, _c))
    _css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pg, re.S))
    if _css.count('{') != _css.count('}'):
        bad.append('page CSS braces do not balance')
    # The edit must not change how much markup the page holds.
    _pc0 = nocomment_html(pg0)     # stripped: prose in a CSS comment names tags
    for tag in ('div', 'table', 'tr', 'td'):
        if (len(re.findall(r'<%s\b' % tag, pc))
                != len(re.findall(r'<%s\b' % tag, _pc0))):
            bad.append('the page gained or lost a <%s>' % tag)

    # -- CONTROL on the stripper -------------------------------------------
    # Each fragment's new prose names table-responsive and container-fluid,
    # two of the classes the checks above hunt for. If comments were not being
    # stripped, those checks would be reading the prose.
    if 'table-responsive' not in rv:
        bad.append('CONTROL: the fragment lost the prose it strips against')
    if 'table-responsive' in nocomment_html(rv):
        bad.append('CONTROL: comments are not being stripped from the fragment')

    if bad:
        sys.exit('! P&L drill-down self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS_REV + EDITS_BUD + EDITS_PAGE:
        print('  %s' % name)

    if not CHECK:
        for path, out in ((REV, rv), (BUD, bd), (PAGE, pg)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  3 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
