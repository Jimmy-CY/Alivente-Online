#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One modal, two files, and a verdict that stops being said five times.

Financial Indicators and Vacancy Management carry THE SAME MODAL. Same ids -
propertyDetailsModal, modalPropertyTable, modalPropertyTableBody,
excellentCount / goodCount / poorCount - the same five columns, the same
legend, the same three summary tiles. Two copies, kept in step by hand.

THE VERDICT WAS STATED FIVE TIMES PER ROW.

    1. a swatch in the legend above the table
    2. a row tint          .performance-excellent  rgba(40,167,69,.1)  !important
    3. the SAME tint again in the phone block, with a 4px left border
    4. the badge           .performance-badge.excellent  solid #28a745
    5. the summary tile    .summary-stat.excellent  washed green

Five statements of one fact, four of them colour. The badge stays, as
`.alv-pill-good / -attn / -bad`; the tiles stay, as the `.alv-stat` component
built for exactly this on 30 Aug; the tints and the legend go. Agreed 31 Aug,
and it is the same argument the stat tile settled: a row that says NEEDS
IMPROVEMENT in words does not also need to be red.

THE TWO COPIES HAD ALREADY DIVERGED ON MOBILE, in the most expensive way -
each solves the same problem differently and neither uses base:

  * financial_indicators.html converts the table to cards in CSS: ~90 lines
    under #modalPropertyTable hiding the head, blocking the cells, styling the
    name as a card title, positioning the badge, injecting data-label prefixes.
  * vacancy_management.html builds a SECOND DOM - #modalPropertyCards, filled
    in the same loop as the rows, with .mpc-header / .mpc-name / .mpc-rank /
    .mpc-row / .mpc-label / .mpc-value / .mpc-badge-row - and toggles the two
    with display:none.

base's `.alv-table` has done this for every list page since the table standard
shipped. Both go, and the two files stop disagreeing about phones.

THE RANK COLUMN STAYS, DESKTOP ONLY - as it already behaves, and as agreed.
That needs one deliberate rule: base promotes the FIRST cell of a card to the
title, and here the first cell is the rank, which is hidden. So the name cell
is told to be the title explicitly. Written down because it is the kind of
thing that looks like a stray override six months later.

THE VALUE LOSES ITS INLINE COLOUR. Every row carried
`<strong style="color: ${indicator.color}">`, so an entire column was painted
one colour that varies by which indicator you opened. A colour every row shares
distinguishes nothing, and it was the accent arriving as a literal through
JavaScript. The figure is ink now; the pill is the colour.

WHAT THIS ROUND DOES NOT DO. It does not touch the BANDING LOGIC, and that
matters: the two files have already drifted. financial_indicators.html
special-cases expensesToRevenue, avgDaysToFill and vacancyCost; vacancy_
management.html has a single generic branch instead. That is business logic,
not presentation, and it belongs to whoever owns the thresholds. Nor does it
touch Vacancy's Detailed Property Data table, its rotate-to-landscape prompt,
the `.table-container` name both pages redefine as a horizontal scroller - the
sticky sweep's group D, which base's own comment says belongs in a round of its
own - or the last hand-rolled segmented control. That is the next round.

Because of group D, the wrapper here is `.ind-drill` and the name
`.table-container` is deliberately NOT used on either page.

Run from the repo root.  --check plans without writing.
"""
import os
import re
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
SWEEP = os.path.join(ROOT, 'test_sticky_sweep.py')
FI = os.path.join(T, 'finance', 'financial_indicators.html')
VM = os.path.join(T, 'finance', 'vacancy_management.html')
BASE = os.path.join(T, 'base.html')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_indmodal'

SENTINEL = '.ind-drill {'

# ---------------------------------------------------------------------------
# shared markup - the whole point is that both files end up with the same one
# ---------------------------------------------------------------------------
NEW_TABLE = """                <div class="ind-drill">
                    <table class="table alv-table" id="modalPropertyTable">
                        <thead>
                            <tr>
                                <th class="cell-rank">#</th>
                                <th class="cell-prop-name">Property Name</th>
                                <th class="cell-perf-value num">Performance</th>
                                <th class="cell-vs-avg num">vs Portfolio Avg</th>
                                <th class="cell-perf-level">Performance Level</th>
                            </tr>
                        </thead>
                        <tbody id="modalPropertyTableBody"></tbody>
                    </table>"""

NEW_STATS = """                <div class="alv-stats ind-stats">
                    <div class="alv-stat alv-stat-good">
                        <div class="alv-stat-value" id="excellentCount">0</div>
                        <div class="alv-stat-label">Excellent</div>
                    </div>
                    <div class="alv-stat alv-stat-attn">
                        <div class="alv-stat-value" id="goodCount">0</div>
                        <div class="alv-stat-label">Good</div>
                    </div>
                    <div class="alv-stat alv-stat-bad">
                        <div class="alv-stat-value" id="poorCount">0</div>
                        <div class="alv-stat-label">Needs Improvement</div>
                    </div>
                </div>"""

STATS_TAIL = NEW_STATS + """
            </div>
            <div class="modal-footer">"""

NEW_CSS = """/* THE INDICATOR DRILL-DOWN.

   Not .table-container: THIS PAGE redefines that name as a horizontal
   scroller, which is the collision the sticky sweep logged as group D and
   the next round settles. And it has to scroll anyway - a portfolio is
   longer than a modal - so it gets its own name, and base's sticky heading
   gets a container to stick to.

   What used to live here: .modal-legend with three swatches, the row tints
   .performance-excellent / -good / -poor with !important, three
   .performance-badge colours in Bootstrap green/amber/red, and .summary-stat
   washed to match. Five ways of saying one thing. .alv-pill and .alv-stat
   say it now, from base, on the house tokens. */
.ind-drill {
    max-height: 55vh;
    overflow: auto;
    background: var(--alv-paper);
    border-radius: var(--alv-radius);
}
.ind-stats {
    --alv-stats-cols: 3;
    margin-top: 20px;
}
#modalPropertyTable th.cell-rank,
#modalPropertyTable td.cell-rank { width: 6%; }
#modalPropertyTable th.cell-prop-name,
#modalPropertyTable td.cell-prop-name { width: 42%; }
#modalPropertyTable th.cell-perf-level,
#modalPropertyTable td.cell-perf-level { width: 18%; }"""

NEW_MOBILE_CSS = """    /* The modal table becomes cards through base, not through ninety lines
       here and a second DOM in the sibling file. Two rules survive, and
       both earn it.

       The rank is desktop-only, as it already was - "low value, takes a
       row" was this page's own verdict on it. But base promotes the FIRST
       cell of a card to its title, and the first cell here is the rank,
       which is now hidden - so the name has to be told to be the title. */
    #modalPropertyTable tbody td.cell-rank { display: none !important; }
    #modalPropertyTable tbody td.cell-prop-name {
        display: block !important;
        font-size: 16px;
        font-weight: 600;
        color: var(--alv-ink);
        padding-bottom: 8px !important;
        margin-bottom: 4px;
        border-bottom: 1px solid var(--alv-line-soft) !important;
    }
    #modalPropertyTable tbody td.cell-prop-name::before { content: none; }"""

# The band-to-pill map, named once per file. Same shape as BAND_PILL on the
# view side: a band cannot end up with a colour the rest of the system has
# never heard of, because the only colours available are base's.
PILL_MAP = """        // ONE map from band to pill, named rather than interpolated - so it
        // can be searched for, and so a band cannot acquire a colour base
        // does not define. Same shape as BAND_PILL in the tenants view.
        const PERF_PILL = {
            excellent: 'alv-pill-good',
            good: 'alv-pill-attn',
            poor: 'alv-pill-bad'
        };"""

# ---------------------------------------------------------------------------
# financial_indicators.html
# ---------------------------------------------------------------------------
FI_CUTS = [
    ('FI: legend out, the table onto the standard',
     '                <div class="modal-legend mb-3">', '</table>',
     NEW_TABLE),
    ('FI: the summary tiles become .alv-stat',
     '                <div class="modal-summary mt-4">',
     '<div class="modal-footer">', STATS_TAIL),
    ('FI: five ways of saying one thing come out of the CSS',
     '.modal-legend {',
     '.summary-stat .stat-label {\n    color: #6c757d;\n    font-size: 14px;\n'
     '    font-weight: 500;\n}',
     NEW_CSS),
    ('FI: and ninety lines of hand-rolled phone cards',
     '    /* Modal legend: stack vertically with line breaks */',
     '    .summary-stat .stat-label {\n        font-size: 12px;\n    }',
     NEW_MOBILE_CSS),
]

FI_OLD_ROW = """            return `
                <tr class="performance-${performanceClass}">
                    <td class="cell-rank"><strong>${index + 1}</strong></td>
                    <td class="cell-prop-name">${property.name}</td>
                    <td class="cell-perf-value" data-label="Performance"><strong style="color: ${indicator.color};">${formattedValue}</strong></td>
                    <td class="cell-vs-avg" data-label="vs Avg">${difference}</td>
                    <td class="cell-perf-level">
                        <span class="performance-badge ${performanceClass}">${performanceLevel}</span>
                    </td>
                </tr>
            `;"""

NEW_ROW = """            return `
                <tr>
                    <td class="cell-rank">${index + 1}</td>
                    <td class="cell-prop-name" data-label="Property">${property.name}</td>
                    <td class="cell-perf-value num" data-label="Performance"><strong>${formattedValue}</strong></td>
                    <td class="cell-vs-avg num" data-label="vs Portfolio Avg">${difference}</td>
                    <td class="cell-perf-level" data-label="Level"><span class="alv-pill ${PERF_PILL[performanceClass]}">${performanceLevel}</span></td>
                </tr>
            `;"""

FI_BODY_START = ("        const tableBody = "
                 "document.getElementById('modalPropertyTableBody');")
FI_BODY_END = "        let excellentCount = 0, goodCount = 0, poorCount = 0;"
FI_NEW_BODY = FI_BODY_START + "\n" + FI_BODY_END + "\n" + PILL_MAP

# ---------------------------------------------------------------------------
# vacancy_management.html
# ---------------------------------------------------------------------------
VM_CUTS = [
    ('VM: legend out, the table onto the standard',
     '                <div class="modal-legend mb-3">', '</table>',
     NEW_TABLE),
    ('VM: the second DOM and the summary tiles go together',
     '                <!-- Mobile: cards -->',
     '<div class="modal-footer">', STATS_TAIL),
    ('VM: five ways of saying one thing come out of the CSS',
     '.modal-legend { display: flex; justify-content: center; }',
     '.modal-mobile-cards { display: none; }',
     NEW_CSS),
    ('VM: and sixty lines of a hand-built card that base already draws',
     '    #propertyDetailsModal .modal-desktop-table { display: none; }',
     '    .modal-summary .col-md-4 { width: 100%; padding: 0; }',
     NEW_MOBILE_CSS),
]

VM_ROW_START = "            // Desktop table row"
VM_ROW_END = "                </div>\n            `);"

VM_NEW_ROW = """            // ONE row template. The mobile card that used to be built beside
            // it is base's job now - same markup, one source of truth, and it
            // stops disagreeing with the sibling file that did it in CSS.
            tableRows.push(`
                <tr>
                    <td class="cell-rank">${index + 1}</td>
                    <td class="cell-prop-name" data-label="Property">${property.name}</td>
                    <td class="cell-perf-value num" data-label="Performance"><strong>${formattedValue}</strong></td>
                    <td class="cell-vs-avg num" data-label="vs Portfolio Avg">${difference}</td>
                    <td class="cell-perf-level" data-label="Level"><span class="alv-pill ${PERF_PILL[performanceClass]}">${performanceLevel}</span></td>
                </tr>
            `);"""

VM_BODY_START = ("        const tableBody = "
                 "document.getElementById('modalPropertyTableBody');")
VM_BODY_END = "        const cards = [];"
VM_NEW_BODY = (FI_BODY_START + "\n"
               + "        let excellentCount = 0, goodCount = 0, poorCount = 0;\n"
               + "\n        const tableRows = [];\n" + PILL_MAP)

VM_OLD_JOIN = """        tableBody.innerHTML = tableRows.join('');
        cardsContainer.innerHTML = cards.join('');"""

# ---------------------------------------------------------------------------
# section 4b - an earlier suite's expectation is SUPERSEDED, so it moves
# ---------------------------------------------------------------------------
# test_sticky_sweep.py left these two pages alone and said why: the
# .table-container name collision was harmless BECAUSE nothing on either page
# used .alv-table, so base's rule and the page's rule never competed over the
# same table. This round makes the modal table .alv-table, and that premise
# stops being true. The expectation is not wrong, it is superseded - so it
# moves to the thing that actually keeps the collision harmless.
S_OLD = """    check('%-38s still has its own rule' % rel, bool(container_rules(src)))
    check('  because it is not on .alv-table at all - the name is coincidental',
          'alv-table' not in src)"""

S_NEW = """    check('%-38s still has its own rule' % rel, bool(container_rules(src)))
    # SUPERSEDED 31 Aug by the indicator-modal round, and MOVED rather than
    # deleted. The old check read `'alv-table' not in src`: the collision was
    # harmless because neither page used the standard at all. The drill-down
    # modal table is .alv-table now, so what keeps the collision harmless is
    # narrower and worth stating exactly - that .alv-table never sits inside
    # the .table-container these pages redefine.
    check('  it carries .alv-table now, in the modal', 'alv-table' in src)
    check('  but NOT inside the .table-container this page redefines',
          not re.search(r'class="table-container"\\s*>\\s*<table[^>]*alv-table',
                        src))
    check('  the modal table has a wrapper of its own',
          bool(re.search(r'class="ind-drill">\\s*<table class="table alv-table"',
                         src)))"""
VM_NEW_JOIN = """        tableBody.innerHTML = tableRows.join('');"""


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:260]))
    return text.replace(old, new, 1)


def between(text, start, end, new, what):
    """Replace start..end INCLUSIVE. `start` must be unique; `end` is the
    first occurrence at or after it, because a closing tag like </thead>
    legitimately appears more than once in a file with two tables."""
    if text.count(start) != 1:
        sys.exit('! %s: the start marker appears %d times, expected 1:\n%s'
                 % (what, text.count(start), start[:200]))
    i = text.index(start)
    j = text.find(end, i)
    if j < 0:
        sys.exit('! %s: the end marker never appears after the start:\n%s'
                 % (what, end[:200]))
    return text[:i] + new + text[j + len(end):]


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NOT re.S: Django's {# #} does not span lines.
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def css_of(text):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))


def main():
    for p in (FI, VM, BASE, SWEEP):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    fi, vm, bs, sw = read(FI), read(VM), read(BASE), read(SWEEP)
    fi0, vm0, sw0 = fi, vm, sw

    if SENTINEL in fi:
        print('  the indicator modal              already applied')
        print('\n  0 file(s) changed')
        return

    names = []
    for what, start, end, new in FI_CUTS:
        fi = between(fi, start, end, new, what)
        names.append(what)
    fi = between(fi, FI_BODY_START, FI_BODY_END, FI_NEW_BODY,
                 'FI: the band-to-pill map')
    fi = one(fi, FI_OLD_ROW, NEW_ROW, 'FI: the row template')
    names += ['FI: the band-to-pill map', 'FI: the row template']

    for what, start, end, new in VM_CUTS:
        vm = between(vm, start, end, new, what)
        names.append(what)
    vm = between(vm, VM_BODY_START, VM_BODY_END, VM_NEW_BODY,
                 'VM: the band-to-pill map')
    vm = between(vm, VM_ROW_START, VM_ROW_END, VM_NEW_ROW,
                 'VM: the row template, and the card built beside it')
    vm = one(vm, VM_OLD_JOIN, VM_NEW_JOIN, 'VM: nothing to fill any more')
    names += ['VM: the band-to-pill map', 'VM: the row template',
              'VM: nothing left to fill']
    sw = one(sw, S_OLD, S_NEW, '4b: the sticky sweep\'s premise moves')
    names.append('4b: the sticky sweep\'s premise moves')

    # -----------------------------------------------------------------------
    # SELF-CHECK. Nothing is written unless every one of these holds.
    # -----------------------------------------------------------------------
    bad = []
    bc = nocomment_html(bs)
    both = (('financial_indicators.html', nocomment_html(fi), fi),
            ('vacancy_management.html', nocomment_html(vm), vm))

    for name, c, raw in both:
        # -- the five statements are down to two --------------------------
        # WORD BOUNDARIES, not substrings: the replacements are called
        # alv-stat-value and alv-stat-label, and a bare `in` test reports the
        # class it just introduced as the class it was hunting.
        for _dead in ('performance-excellent', 'performance-good',
                      'performance-poor', 'performance-badge', 'legend-color',
                      'legend-item', 'modal-legend', 'summary-stat',
                      'modal-summary', 'stat-value', 'stat-label'):
            if re.search(r'(?<![\w-])%s(?![\w-])' % _dead, c):
                bad.append('%s: %s survives' % (name, _dead))
        for _pill in ('alv-pill-good', 'alv-pill-attn', 'alv-pill-bad'):
            if _pill not in c:
                bad.append('%s: the row can never be %s' % (name, _pill))
        if 'PERF_PILL' not in c:
            bad.append('%s: the band-to-pill map is gone' % name)
        if c.count('PERF_PILL') != 2:
            bad.append('%s: PERF_PILL is named %d times, expected 2 - '
                       'declared once and used once'
                       % (name, c.count('PERF_PILL')))

        # -- the table is on the standard ---------------------------------
        if 'class="table alv-table" id="modalPropertyTable"' not in c:
            bad.append('%s: the modal table is not .alv-table' % name)
        if 'class="ind-drill"' not in c:
            bad.append('%s: the table has no scrolling wrapper' % name)
        if c.count('.ind-drill {') != 1:
            bad.append('%s: .ind-drill defined %d times'
                       % (name, c.count('.ind-drill {')))
        # GROUP D. This page redefines .table-container as a horizontal
        # scroller. The page's ONE existing user of that name is the Detailed
        # Property Data table, which the NEXT round settles - so the count must
        # be unchanged, not zero. A check that demanded zero would be wider
        # than its round, and would get relaxed.
        _before = fi0 if name.startswith('financial') else vm0
        if c.count('class="table-container"') != \
                nocomment_html(_before).count('class="table-container"'):
            bad.append('%s: the number of .table-container users changed - '
                       'that name is group D and belongs to the next round'
                       % name)
        if '<div class="ind-drill">' not in c or \
                c.find('id="modalPropertyTable"') < c.find('ind-drill'):
            bad.append('%s: the modal table is not inside .ind-drill' % name)
        for _lbl in ('data-label="Property"', 'data-label="Performance"',
                     'data-label="vs Portfolio Avg"', 'data-label="Level"'):
            if _lbl not in c:
                bad.append('%s: the card view has no %s' % (name, _lbl))
        if 'class="cell-rank"' not in c:
            bad.append('%s: the rank column is gone' % name)
        if 'td.cell-rank { display: none !important; }' not in c:
            bad.append('%s: the rank is not hidden on a phone' % name)
        # base promotes the FIRST cell; here it is the hidden rank.
        if not re.search(r'td\.cell-prop-name\s*\{[^}]*display:\s*block',
                         c):
            bad.append('%s: the name cell is not promoted to the card title, '
                       'so the card has no heading' % name)
        if c.count('class="num"') + c.count(' num"') < 4:
            bad.append('%s: the two numeric columns are not .num in head and '
                       'body' % name)

        # -- the tiles are the component ----------------------------------
        if 'class="alv-stats ind-stats"' not in c:
            bad.append('%s: the tiles are not .alv-stats' % name)
        for _v, _id in (('good', 'excellentCount'), ('attn', 'goodCount'),
                        ('bad', 'poorCount')):
            if 'alv-stat alv-stat-%s' % _v not in c:
                bad.append('%s: no alv-stat-%s tile' % (name, _v))
            if 'id="%s"' % _id not in c:
                bad.append('%s: the JS fills #%s and nothing carries that id'
                           % (name, _id))
        if '--alv-stats-cols: 3' not in c:
            bad.append('%s: the tile strip is not three-up' % name)

        # -- colour ---------------------------------------------------------
        # SCOPED TO THE ROW. indicator.color also paints the indicator cards
        # on the page and the single Portfolio Average figure in the modal
        # header - one figure carrying its own indicator's accent is not the
        # fault. The fault was a whole COLUMN painted one colour, which
        # distinguishes nothing. A wider check here would report the two
        # legitimate uses and then get relaxed.
        if 'cell-perf-value num" data-label="Performance"><strong style=' in c:
            bad.append('%s: the value column still takes an inline colour'
                       % name)
        # And the round must actually have REMOVED colours, measured.
        _lit_before = set(re.findall(r'#[0-9a-fA-F]{3,8}\b',
                                     nocomment_html(_before)))
        _lit_after = set(re.findall(r'#[0-9a-fA-F]{3,8}\b', c))
        if len(_lit_after) >= len(_lit_before):
            bad.append('%s: distinct literal colours did not fall (%d -> %d)'
                       % (name, len(_lit_before), len(_lit_after)))

        # -- the round must SHRINK these files ------------------------------
        # A patcher that appended instead of replacing passes everything above.
        _was = len(_before)
        if len(raw) >= _was:
            bad.append('%s did not get smaller (%d -> %d) - something was '
                       'added rather than replaced' % (name, _was, len(raw)))

        # -- structure ------------------------------------------------------
        _c = css_of(raw)
        if _c.count('{') != _c.count('}'):
            bad.append('%s: CSS braces do not balance' % name)
        for o, cl in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                      (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
            if len(re.findall(o, raw)) != len(re.findall(cl, raw)):
                bad.append('%s: a Django block no longer balances' % name)
        for _l in raw.split('\n'):
            if _l.count('{#') != _l.count('#}'):
                bad.append('%s: a {# #} comment spans lines' % name)
                break

    # VM only: the second DOM is gone, root and branch.
    _v = nocomment_html(vm)
    for _dead in ('modalPropertyCards', 'modal-mobile-cards',
                  'modal-desktop-table', 'modal-property-card', 'mpc-header',
                  'mpc-name', 'mpc-rank', 'mpc-row', 'mpc-label', 'mpc-value',
                  'mpc-badge-row', 'cardsContainer', 'const cards'):
        if _dead in _v:
            bad.append('vacancy_management.html: %s survives - the second DOM '
                       'is only half gone' % _dead)
    # ... and the ROUND 3 work is still there, untouched.
    for _keep in ('rotate-prompt', 'rotate-on-portrait', 'data-table',
                  'Detailed Property Data'):
        if _keep not in vm:
            bad.append('vacancy_management.html: %s was removed - that is the '
                       'NEXT round, not this one' % _keep)
    if '.table-container { overflow-x: auto; }' not in vm:
        bad.append('vacancy_management.html: group D was touched - next round')

    # THE POINT OF THE ROUND: the two modals must now be the same markup.
    def modal_shape(raw):
        c = nocomment_html(raw)
        i = c.find('<div class="ind-drill">')
        j = c.find('</div>', c.find('id="poorCount"'))
        return ' '.join(c[i:j].split())
    if modal_shape(fi) != modal_shape(vm):
        bad.append('the two modals are STILL not the same markup')
    # A control for that comparison - it has to be able to see a difference.
    if modal_shape(fi) == modal_shape(fi.replace('cell-rank', 'cell-rankX')):
        bad.append('CONTROL: the modal comparison cannot tell two apart')

    # -- base owns what both files now name --------------------------------
    for _cls in ('.alv-table', '.alv-stats', '.alv-stat', '.alv-pill-good',
                 '.alv-pill-attn', '.alv-pill-bad'):
        if _cls not in bc:
            bad.append('base does not define %s' % _cls)
    for _tok in ('--alv-paper', '--alv-radius', '--alv-ink', '--alv-line-soft'):
        if '%s:' % _tok not in bc:
            bad.append('%s is referenced and never defined' % _tok)

    # -- 4b: the suite still parses, and says at least as much -------------
    try:
        compile(sw, 'test_sticky_sweep.py', 'exec')
    except SyntaxError as exc:
        bad.append('the patched sticky suite does not parse: %s' % exc)
    if sw.count('check(') < sw0.count('check('):
        bad.append('the sticky suite lost checks - an expectation was DELETED '
                   'rather than moved')
    # A CHECK THAT READS TEXT CATCHES PROSE - eighteenth instance, and this
    # time in a comment this very round wrote. The moved check's own comment
    # QUOTES the expectation it superseded, so a bare `in` test on the file
    # finds it in the explanation of why it is gone.
    _sw_code = '\n'.join(l for l in sw.split('\n')
                         if not l.lstrip().startswith('#'))
    if "'alv-table' not in src" in _sw_code:
        bad.append('the superseded expectation is still live and will fail')
    if "'alv-table' not in src" not in sw:
        bad.append('CONTROL: the moved check no longer says what it replaced')

    # -- CONTROL on the stripper -------------------------------------------
    # This round's own prose names performance-badge and modal-legend, two of
    # the classes hunted above. If comments were not stripped, those checks
    # would be reading the prose and reporting classes that are gone.
    if 'performance-badge' not in fi:
        bad.append('CONTROL: the round lost the prose it strips against')
    if 'performance-badge' in nocomment_html(fi):
        bad.append('CONTROL: comments are not being stripped')

    if bad:
        sys.exit('! indicator-modal self-check FAILED, nothing written:'
                 '\n   - %s' % '\n   - '.join(bad))

    for n in names:
        print('  %s' % n)
    print('  %s shrinks %d -> %d bytes'
          % ('financial_indicators.html', len(fi0), len(fi)))
    print('  %s shrinks %d -> %d bytes'
          % ('vacancy_management.html', len(vm0), len(vm)))

    if not CHECK:
        for path, out in ((FI, fi), (VM, vm), (SWEEP, sw)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  3 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
