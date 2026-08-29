#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Outstanding Invoices joins the table standard.

PART B. Part A (apply_ageing_scale.py) split the buckets and gave base the
`.alv-age-1..4` scale. This is the migration: the page stops drawing its own
table and uses the one the system already owns.

WHAT THE PAGE WAS DOING.

  .age-analysis-table th { background-color: #2c3e50; color: white;
                           border: 1px solid #34495e; }

A navy band with white text, in a system whose tables have had a defined
header treatment for a week. Not a drifted version of the standard - it
predates it, and nothing in base could reach it.

The table also sat in no container at all (group A of the sticky scan), its
TOTALS row was the last `<tr>` of the `<tbody>`, and its figures were set in
'Courier New' by a rule with `text-align: right !important`, which is `.num`
spelled by hand.

THE PRINT FIX NEEDS NO PRINT CSS. This page was on the list at 3.2 for
printing white on white, and its own 37-line `@media print` block is what
failed to fix it. base's print block already carries

    .alv-table th, .alv-table td { print-color-adjust: exact; }

so the moment the table IS an `.alv-table`, the fix applies. The page's print
block keeps only what is genuinely page-specific: swapping the desktop table
in for the mobile cards on paper. That is exactly what 2.6 predicted - "the
white-on-white goes away by joining the standard, not by anybody writing a
print rule".

A TOTALS ROW BELONGS IN A `<tfoot>`, and the standard had no rule for one.
That is why this page, and every other that wanted a summary line, put it in
the tbody and styled it by hand. base gains `.alv-table tfoot` here: it is a
gap in the component, not a quirk of this report.

THE MOBILE CARDS STAY AS THEY ARE. base's card view turns a table into blocks
with the column name beside each figure, which is right for a list of records.
This page has something better for the job - a proportional age bar and a
five-row legend - and it is hidden from base's card view because the whole
container is display:none below 768px. Adopting the standard does not mean
replacing something the standard cannot do.

Run from the repo root, after apply_ageing_scale.py.  --check plans only.
"""
import os, re, sys, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
BASE  = os.path.join(ROOT, 'pages', 'templates', 'base.html')
PAGE  = os.path.join(ROOT, 'pages', 'templates', 'open_invoices_report.html')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_oimigrate'

SENTINEL = 'A TOTALS ROW BELONGS IN A tfoot'

# ---------------------------------------------------------------------------
# 1. base: the standard gains a tfoot
# ---------------------------------------------------------------------------
B_ANCHOR = """.num, .alv-table td.num, .alv-table th.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }"""
B_TFOOT = """.num, .alv-table td.num, .alv-table th.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }

      /* A TOTALS ROW BELONGS IN A tfoot, and until now the standard had no
         rule for one - so every table that wanted a summary line put it in
         the tbody as an ordinary <tr> and styled it by hand. Outstanding
         Invoices did exactly that, with a background literal and a navy
         border.

         It is not only tidiness. A tfoot is announced as a summary rather
         than as another record, and a browser repeats it at the foot of each
         printed page, which a tbody row cannot do.

         Deliberately NOT sticky. .alv-matrix pins its footer because it
         scrolls sideways under a frozen column; an ordinary table does not,
         and a footer that follows the viewport in a page that scrolls
         normally is furniture, not information. */
      .alv-table tfoot td,
      .alv-table tfoot th {
        background: var(--alv-surface);
        border-top: 2px solid var(--alv-line);
        color: var(--alv-ink-strong);
        font-weight: 600;
        padding: 11px 12px;
      }"""

B_MOB_ANCHOR = """        .alv-table,
        .alv-table tbody,
        .alv-table tr,
        .alv-table td { display: block; width: 100%; }"""
B_MOB = """        .alv-table,
        .alv-table tbody,
        .alv-table tfoot,
        .alv-table tr,
        .alv-table td { display: block; width: 100%; }"""

# ---------------------------------------------------------------------------
# 2. the page: into the container, onto the standard
# ---------------------------------------------------------------------------
P_OLD_OPEN = """            <!-- Desktop: traditional table -->
            <table class="age-analysis-table desktop-only-table">"""
P_NEW_OPEN = """            <!-- Desktop: the house table. The container is what carries
                 desktop-only, so nothing is left drawing an empty shell on a
                 phone; the cards below replace the whole thing there. -->
            <div class="table-container desktop-only-table">
            <table class="alv-table">"""

P_OLD_TFOOT = """                    <!-- Totals Row -->
                    <tr class="totals-row">
                        <td class="tenant-name-cell"><strong>TOTALS</strong></td>"""
P_NEW_TFOOT = """                </tbody>
                <tfoot>
                    <tr>
                        <td class="tenant-name-cell"><strong>TOTALS</strong></td>"""

P_OLD_CLOSE = """                    </tr>
                </tbody>
            </table>

            <!-- Mobile: card list with sparkline-style age breakdown -->"""
P_NEW_CLOSE = """                    </tr>
                </tfoot>
            </table>
            </div>

            <!-- Mobile: card list with sparkline-style age breakdown -->"""

# .desktop-only-table now sits on a div, so it is a block, not a table.
P_OLD_D1 = """.desktop-only-table { display: table; }"""
P_NEW_D1 = """.desktop-only-table { display: block; }"""
P_OLD_D2 = """    .desktop-only-table { display: table !important; }"""
P_NEW_D2 = """    .desktop-only-table { display: block !important; }"""

# ---- rules base already owns, deleted -------------------------------------
P_OLD_TABLE_CSS = """/* Desktop table */
.age-analysis-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    font-size: 0.9rem;
}

.age-analysis-table th {
    background-color: #2c3e50;
    color: white;
    padding: 12px 8px;
    text-align: center;
    font-weight: 600;
    border: 1px solid #34495e;
    font-size: 0.85rem;
    line-height: 1.2;
    min-width: 120px;
}

.age-analysis-table td {
    padding: 10px 8px;
    border: 1px solid #dee2e6;
    text-align: center;
}
"""
P_NEW_TABLE_CSS = """/* The table's own appearance is base's now - the shell, the header
   treatment, the borders, the hover, the print behaviour. What was here was a
   navy band with white text at #2c3e50, which nothing in base could reach and
   which no other table in the system wears. */
"""

P_OLD_AMOUNT = """.amount-cell {
    text-align: right !important;
    font-family: 'Courier New', monospace;
}
"""
P_NEW_AMOUNT = """/* .amount-cell was `text-align: right !important` plus 'Courier New' - which
   is base's .num spelled by hand, and less well: .num also sets
   tabular-nums, so the digits line up in a column. fsr.html and
   property_report.html were already using it. */
"""

P_OLD_TOTROW = """.totals-row {
    background-color: #f1f3f4;
    border-top: 2px solid #2c3e50;
}

.totals-row .amount-cell {
    font-weight: bold;
}
"""
P_NEW_TOTROW = """/* The totals row is a <tfoot> now, and base styles it. */
"""

P_OLD_PRINT_FS = """    .age-analysis-table {
        font-size: 0.8rem;
    }

"""
P_NEW_PRINT_FS = """"""

# ---- literals onto tokens -------------------------------------------------
P_OLD_TITLE = """.analysis-title {
    font-size: 1.5rem;
    color: #2c3e50;
    margin-bottom: 20px;
    font-weight: bold;
}"""
P_NEW_TITLE = """.analysis-title {
    font-size: 1.5rem;
    color: var(--alv-ink-strong);
    margin-bottom: 20px;
    font-weight: bold;
}"""

P_OLD_TNAME = """.tenant-name-cell {
    text-align: left !important;
    font-weight: 500;
    background-color: #f8f9fa;
}"""
P_NEW_TNAME = """.tenant-name-cell {
    text-align: left !important;
    font-weight: 500;
    background-color: var(--alv-surface);
}"""

P_OLD_TOTAMT = """.total-amount {
    background-color: #e3f2fd;
    font-weight: 600;
}"""
P_NEW_TOTAMT = """.total-amount {
    background-color: var(--alv-accent-soft);
    font-weight: 600;
}"""

P_OLD_CLICK = """.clickable-amount {
    cursor: pointer;
    transition: background-color 0.2s ease;
    text-decoration: underline;
    color: #007bff;
}"""
P_NEW_CLICK = """.clickable-amount {
    cursor: pointer;
    transition: background-color 0.2s ease;
    text-decoration: underline;
    color: var(--alv-edit);
}"""

P_OLD_CLICKH = """.clickable-amount:hover {
    background-color: #d1ecf1 !important;
    color: #0056b3;
}"""
P_NEW_CLICKH = """.clickable-amount:hover {
    background-color: var(--alv-accent-soft) !important;
    color: var(--alv-accent);
}"""

EDITS_BASE = [
    ('the standard gains a tfoot', B_ANCHOR, B_TFOOT),
    ('  which behaves on a phone like the rest of the table', B_MOB_ANCHOR, B_MOB),
]
EDITS_PAGE = [
    ('the table goes into a container and onto .alv-table',
     P_OLD_OPEN, P_NEW_OPEN),
    ('  TOTALS moves out of the tbody into a real tfoot', P_OLD_TFOOT, P_NEW_TFOOT),
    ('  and the markup closes both', P_OLD_CLOSE, P_NEW_CLOSE),
    ('desktop-only now hides a block, not a table', P_OLD_D1, P_NEW_D1),
    ('  on paper too', P_OLD_D2, P_NEW_D2),
    ('the navy header band goes, with the rest base owns',
     P_OLD_TABLE_CSS, P_NEW_TABLE_CSS),
    ('  and Courier New gives way to .num', P_OLD_AMOUNT, P_NEW_AMOUNT),
    ('  and the hand-styled totals row', P_OLD_TOTROW, P_NEW_TOTROW),
    ('  and its print override, which base sets properly',
     P_OLD_PRINT_FS, P_NEW_PRINT_FS),
    ('the section title takes the ink token', P_OLD_TITLE, P_NEW_TITLE),
    ('the tenant column takes the surface token', P_OLD_TNAME, P_NEW_TNAME),
    ('the total column takes the accent tint', P_OLD_TOTAMT, P_NEW_TOTAMT),
    ('a clickable figure is an edit-coloured link', P_OLD_CLICK, P_NEW_CLICK),
    ('  and its hover is house too', P_OLD_CLICKH, P_NEW_CLICKH),
]

# ---------------------------------------------------------------------------
# 3. the modal table - built in JS, and already shaped for the standard
# ---------------------------------------------------------------------------
# Its cells carry data-label already, which is what base's mobile card view
# reads, so it needs nothing invented for it. It had a grey #e9ecef header
# band and its own border rules; the container it sat in set overflow-x: auto,
# which is the property .table-container must NOT have - that is what makes an
# element the scroll container for a sticky descendant, and the sticky sweep's
# whole finding.
P_OLD_MODAL = """        html += '<div class="invoice-table-wrap desktop-only-invoices">';
        html += '<table class="invoice-table">';
        html += '<thead><tr><th>Invoice Date</th><th>Due Date</th><th>Days Overdue</th><th>Amount</th></tr></thead>';"""
P_NEW_MODAL = """        html += '<div class="table-container desktop-only-invoices">';
        html += '<table class="alv-table">';
        html += '<thead><tr><th>Invoice Date</th><th>Due Date</th><th class="num">Days Overdue</th><th class="num">Amount</th></tr></thead>';"""

P_OLD_MODAL_TD = """            html += '<td data-label="Days Overdue">' + (invoice.days_overdue !== undefined ? invoice.days_overdue : '-') + '</td>';
            html += '<td data-label="Amount">\u20ac' + formatAmount(invoice.amount != null ? invoice.amount : (tenant.tenant_rent || 0)) + '</td>';"""
P_NEW_MODAL_TD = """            html += '<td class="num" data-label="Days Overdue">' + (invoice.days_overdue !== undefined ? invoice.days_overdue : '-') + '</td>';
            html += '<td class="num" data-label="Amount">\u20ac' + formatAmount(invoice.amount != null ? invoice.amount : (tenant.tenant_rent || 0)) + '</td>';"""

P_OLD_MODAL_CSS = """.invoice-table-wrap {
    overflow-x: auto;
}

.invoice-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

.invoice-table th, .invoice-table td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
}

.invoice-table th {
    background-color: #e9ecef;
    font-weight: 600;
}
"""
P_NEW_MODAL_CSS = """/* The modal table is base's too. Its wrapper set overflow-x: auto, which is
   precisely the declaration .table-container must not carry - an element that
   scrolls becomes the scroll container for any sticky descendant, and the
   header then pins to the wrapper rather than to the viewport. */
"""

EDITS_MODAL = [
    ('the modal table joins the standard as well', P_OLD_MODAL, P_NEW_MODAL),
    ('  with its figures on .num', P_OLD_MODAL_TD, P_NEW_MODAL_TD),
    ('  and its grey band and hand-drawn borders go',
     P_OLD_MODAL_CSS, P_NEW_MODAL_CSS),
]

# The sparkline's TRACK. Not part of either table, but it is the bar the
# ageing segments are drawn into - the scale's own container - so leaving it
# on a Bootstrap grey while the segments come from house tokens would be an
# odd place to stop.
P_OLD_TRACK = """        background-color: #e9ecef;
        display: flex;"""
P_NEW_TRACK = """        background-color: var(--alv-line-soft);
        display: flex;"""

EDITS_MODAL = EDITS_MODAL + [
    ('the ageing bar\'s track takes a house token', P_OLD_TRACK, P_NEW_TRACK),
]

# ---------------------------------------------------------------------------
# 4. the modal's rows stop being uniformly red
# ---------------------------------------------------------------------------
# Every overdue row was bold red - dates, days and amounts alike - so eight
# invoices aged 89 to 485 days all read identically. The scale built in part A
# can say which is which, so the severity moves onto the Days Overdue figure
# and the rows go back to ordinary text.
#
# The threshold chain existed once already, inline in the mobile path. It is a
# function now, used by both, mirroring `age_bucket` in the view - the same
# five bands, named once on each side of the wire.
P_OLD_FMT = """function formatAmount(value) {"""
P_NEW_FMT = """function ageStep(days) {
    // THE SAME FIVE BANDS THE VIEW BUCKETS ON, and the index matches
    // AGE_BUCKETS in pages/views/invoices.py: 0 is not yet due, 4 is 91+.
    // If these two ever part company an invoice gets two verdicts again,
    // which is the fault part A closed.
    if (days > 90) { return 'alv-age-4'; }
    if (days > 60) { return 'alv-age-3'; }
    if (days > 30) { return 'alv-age-2'; }
    if (days > 0)  { return 'alv-age-1'; }
    return 'alv-age-0';
}

function formatAmount(value) {"""

P_OLD_ROW = """            html += '<tr class="' + (invoice.overdue ? 'overdue' : '') + '">';
            html += '<td data-label="Invoice Date">' + (invoice.invoice_date || '-') + '</td>';
            html += '<td data-label="Due Date">' + (invoice.due_date || '-') + '</td>';
            html += '<td class="num" data-label="Days Overdue">' + (invoice.days_overdue !== undefined ? invoice.days_overdue : '-') + '</td>';"""
P_NEW_ROW = """            var d = invoice.days_overdue !== undefined ? invoice.days_overdue : 0;
            html += '<tr>';
            html += '<td data-label="Invoice Date">' + (invoice.invoice_date || '-') + '</td>';
            html += '<td data-label="Due Date">' + (invoice.due_date || '-') + '</td>';
            html += '<td class="num" data-label="Days Overdue">'
                 + '<span class="alv-age-pill ' + ageStep(d) + '">'
                 + (d > 0 ? d : 'Not yet due') + '</span></td>';"""

P_OLD_CHAIN = """            var daysClass = daysOverdue > 90 ? 'alv-age-4' :
                            daysOverdue > 60 ? 'alv-age-3' :
                            daysOverdue > 30 ? 'alv-age-2' :
                            daysOverdue > 0 ? 'alv-age-1' : 'alv-age-0';"""
P_NEW_CHAIN = """            var daysClass = ageStep(daysOverdue);"""

P_OLD_OVERDUE_CSS = """.overdue {
    color: var(--alv-bad);
    font-weight: bold;
}
"""
P_NEW_OVERDUE_CSS = """/* .overdue coloured a whole row - date, due date, days and amount - so an
   invoice 89 days late and one 485 days late looked the same. The severity
   is on the Days Overdue pill now, which can tell them apart. */
"""

EDITS_MODAL = EDITS_MODAL + [
    ('the five bands become a function on the page too', P_OLD_FMT, P_NEW_FMT),
    ('  used by the modal table', P_OLD_ROW, P_NEW_ROW),
    ('  and by the mobile rows, which had the chain inline',
     P_OLD_CHAIN, P_NEW_CHAIN),
    ('  so a row is no longer uniformly red', P_OLD_OVERDUE_CSS,
     P_NEW_OVERDUE_CSS),
]

# ---------------------------------------------------------------------------
# 5. numeric headings over narrow columns
# ---------------------------------------------------------------------------
B_CENTER_ANCHOR = """      .alv-table .desktop-action-cell,
      .alv-table th.desktop-action-cell { text-align: center; }"""
B_CENTER = """      .alv-table .desktop-action-cell,
      .alv-table th.desktop-action-cell { text-align: center; }

      /* A NUMERIC HEADING IS RIGHT-ALIGNED BY DEFAULT - see .num above - and
         that is right when the label is short enough to sit on one line,
         because it then hangs over the last digit of its own column.

         A stack of three-line labels over narrow columns reads differently:
         right-aligned they all crowd one edge and the column looks lopsided,
         with the label's shortest line stranded. .col-center is the opt-out,
         and it applies to the HEADING only - the figures underneath stay on
         .num, because numbers line up on the decimal or they line up on
         nothing. */
      .alv-table thead th.col-center { text-align: center; }"""

P_OLD_HEADS = """                        <th>Total Outstanding</th>
                        <th>Not Yet Due</th>
                        <th>Past Due<br>(1 to 30 Days)</th>
                        <th>Past Due<br>(31 to 60 Days)</th>
                        <th>Past Due<br>(61 to 90 Days)</th>
                        <th>Past Due<br>(91+ Days)</th>"""
P_NEW_HEADS = """                        <th class="col-center">Total Outstanding</th>
                        <th class="col-center">Not Yet Due</th>
                        <th class="col-center">Past Due<br>(1 to 30 Days)</th>
                        <th class="col-center">Past Due<br>(31 to 60 Days)</th>
                        <th class="col-center">Past Due<br>(61 to 90 Days)</th>
                        <th class="col-center">Past Due<br>(91+ Days)</th>"""

EDITS_BASE = EDITS_BASE + [
    ('a numeric heading can be centred over its column',
     B_CENTER_ANCHOR, B_CENTER),
]
EDITS_MODAL = EDITS_MODAL + [
    ('the six figure columns centre their headings', P_OLD_HEADS, P_NEW_HEADS),
]

# Twelve cells stop naming a page class and take base's .num.
P_CELL_SWAPS = [
    ('the tinted figures take .num', 'class="amount-cell alv-age-cell',
     'class="num alv-age-cell', 10),
    ('and so does the Total column', 'amount-cell total-amount',
     'num total-amount', 3),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:220]))
    return text.replace(old, new, 1)


def many(text, old, new, want, what):
    n = text.count(old)
    if n != want:
        sys.exit('! %s matched %d times, expected %d:\n%s'
                 % (what, n, want, old[:200]))
    return text.replace(old, new)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NOT re.S - Django's {# #} does not span lines, and a stripper more
    # permissive than the lexer it models certifies the faults it exists to
    # catch.
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def rules(src):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'@media[^{]*\{', '', css)
    out = {}
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        for sel in m.group(1).split(','):
            sel = ' '.join(sel.split())
            if sel:
                out.setdefault(sel, []).append(' '.join(m.group(2).split()))
    return out


def main():
    for p in (BASE, PAGE):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    bs, pg = read(BASE), read(PAGE)
    pg0 = pg

    if 'alv-age-cell' not in pg:
        sys.exit('! run apply_ageing_scale.py first - part B builds on part A')
    if SENTINEL in bs:
        print('  Outstanding Invoices migration  already applied')
        print('\n  0 file(s) changed')
        return

    for name, old, new in EDITS_BASE:
        bs = one(bs, old, new, name)
    for name, old, new in EDITS_PAGE:
        pg = one(pg, old, new, name)
    for name, old, new in EDITS_MODAL:
        pg = one(pg, old, new, name)
    for name, old, new, want in P_CELL_SWAPS:
        pg = many(pg, old, new, want, name)

    # ---- self-check BEFORE anything is written ----------------------------
    bad = []
    _bc, _pc = nocomment_html(bs), nocomment_html(pg)

    if not re.search(r'\.alv-table tfoot td', _bc):
        bad.append('base has no tfoot rule, so the totals row is unstyled')
    if 'position: sticky' in _bc.split('.alv-table tfoot')[-1][:400]:
        bad.append('the tfoot was made sticky - an ordinary table does not '
                   'scroll under a frozen column and does not want it')

    # THE PAGE MUST NO LONGER DRAW ITS OWN TABLE.
    _P = rules(pg)
    for _dead in ('.age-analysis-table', '.age-analysis-table th',
                  '.age-analysis-table td', '.totals-row', '.amount-cell',
                  '.invoice-table', '.invoice-table th', '.invoice-table-wrap'):
        if _dead in _P:
            bad.append('%s is still defined on the page' % _dead)
    if 'class="alv-table"' not in _pc:
        bad.append('the table did not join the standard')
    if 'table-container' not in _pc:
        bad.append('the table is still in no container - group A of the '
                   'sticky scan, and a sticky header cannot work')
    if '<tfoot>' not in _pc or '</tfoot>' not in _pc:
        bad.append('the totals row is still inside the tbody')
    if _pc.count('<tbody>') != _pc.count('</tbody>'):
        bad.append('tbody no longer balances')

    # LITERALS ARE CHECKED WHERE THE ROUND REACHES, and counted everywhere.
    #
    # The first version of this check demanded the whole page be free of
    # #2c3e50 and 'Courier New'. It is not, and should not be: those live in
    # the debtor cards and the mobile invoice rows, which this round does not
    # touch and which keep their own layout deliberately. A check whose scope
    # is wider than the round's reports failures that are not defects, and
    # gets relaxed - and a relaxed check catches nothing.
    #
    # So: the selectors this round REWRITES must carry no literal, and the
    # page's total literal count must fall by at least as much as the deleted
    # rules held. Both, because either alone can be satisfied by accident.
    _P_after = rules(pg)
    for _sel in ('.analysis-title', '.tenant-name-cell', '.total-amount',
                 '.clickable-amount', '.clickable-amount:hover'):
        _body = ' '.join(_P_after.get(_sel, []))
        if re.search(r'#[0-9a-fA-F]{3,8}\b', _body):
            bad.append('%s still carries a literal colour: %s' % (_sel, _body))
    _before = len(re.findall(r'#[0-9a-fA-F]{3,8}\b',
                             nocomment_html(pg0)))
    _after = len(re.findall(r'#[0-9a-fA-F]{3,8}\b', _pc))
    if _after >= _before - 11:
        bad.append('the round retired %d literal colours, expected at least 12'
                   % (_before - _after))
    if not re.search(r'\.alv-table thead th\.col-center\s*\{[^}]*center', _bc):
        bad.append('base does not define the centred heading')
    if _pc.count('class="col-center"') != 6:
        bad.append('the six figure headings are not centred (%d)'
                   % _pc.count('class="col-center"'))
    if 'col-center' in _pc and 'td class="col-center"' in _pc:
        bad.append('col-center reached a body cell - it is for headings only, '
                   'because figures line up on the decimal or on nothing')
    if '.overdue' in _P_after:
        bad.append('a whole row can still be painted red')
    if _pc.count('ageStep(') < 3:
        bad.append('the five bands are not a single function on the page')
    if 'alv-age-pill' not in _pc:
        bad.append('the modal has no ageing pill')
    if 'Courier New' in ' '.join(
            v for k, vs in _P_after.items() for v in vs
            if k in ('.amount-cell', '.invoice-table')):
        bad.append('Courier New survives in a table this round rewrote')

    # CONTAINER AND TABLE ARE ONE ELEMENT APART. If desktop-only ended up on
    # both, or on neither, a phone gets an empty white shell or a stray table.
    if _pc.count('table-container') != 2:
        bad.append('both tables should be in a container (%d found)'
                   % _pc.count('table-container'))
    if 'overflow-x: auto' in _pc.split('.table-container')[0][-400:]:
        bad.append('a scrolling wrapper survives around a container')
    if _pc.count('table-container desktop-only-table') != 1:
        bad.append('desktop-only is not on the container exactly once')
    if 'alv-table desktop-only-table' in _pc:
        bad.append('desktop-only is on the table as well as the container')
    if '.desktop-only-table { display: table' in _pc:
        bad.append('desktop-only still shows as a table, but it is a div now')

    # Balance is a DELTA. This page opens more <div> than it closes before
    # anything is patched - {% if %} branches need not balance as raw text.
    _want = {'div': 1, 'table': 0, 'tbody': 0, 'tr': 0, 'td': 0}
    for tag, w in _want.items():
        _o = (len(re.findall(r'<%s\b' % tag, pg))
              - len(re.findall(r'<%s\b' % tag, pg0)))
        _c = (len(re.findall(r'</%s\s*>' % tag, pg))
              - len(re.findall(r'</%s\s*>' % tag, pg0)))
        if _o != _c:
            bad.append('the edit opens %d <%s> and closes %d' % (_o, tag, _c))
        elif _o != w:
            bad.append('the edit adds %d <%s>, expected %d' % (_o, tag, w))

    _css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pg, re.S))
    if _css.count('{') != _css.count('}'):
        bad.append('page CSS braces do not balance')
    _bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', bs, re.S))
    if _bcss.count('{') != _bcss.count('}'):
        bad.append('base CSS braces do not balance')
    for o, c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                 (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
        if len(re.findall(o, pg)) != len(re.findall(c, pg)):
            bad.append('a Django block no longer balances (%s)' % o)
    for _l in pg.split('\n'):
        if _l.count('{#') != _l.count('#}'):
            bad.append('a {# #} comment spans lines, which Django renders')
            break
    # CONTROL on the stripper.
    if 'navy band with white text' in _pc:
        bad.append('CONTROL: CSS comments are not being stripped, so the '
                   'literal checks above may be reading prose')

    if bad:
        sys.exit('! migration self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS_BASE + EDITS_PAGE + EDITS_MODAL:
        print('  %s' % name)
    for name, _o, _n, _w in P_CELL_SWAPS:
        print('  %s' % name)

    if not CHECK:
        for path, out in ((BASE, bs), (PAGE, pg)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  2 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
