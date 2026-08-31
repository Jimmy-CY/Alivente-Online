#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The two detail tables, a grading scale with names, and group D closed.

THE GRADING HEAT MAP HAD NO TOKENS BEHIND IT. Every cell of the Financial
Indicators table took an inline background from

    const hue = (1 - t) * 120;                 // 0 = red (worst) .. 120 = green
    return `background-color: hsl(${hue}, 62%, 90%);`;

Unlike the row tints deleted on 31 Aug, this colour carries REAL information -
where a property sits in the distribution for that metric. So it does not go.
But a continuous rainbow computed in JavaScript is outside the token system
entirely, cannot be printed, cannot be checked, and cannot be reasoned about;
and the one thing every step of it is guaranteed to do is put red next to green.

base gains `.alv-grade-1..5`: five steps, best to worst, on the same mechanism
as `.alv-age-*` - a step class sets two custom properties, an application class
consumes them. Deliberately NOT the same family. Ageing runs "not ageing" to
"severe" and starts at good; a grade runs across a distribution and has a
MIDDLE. Same machinery, different meaning, so different names.

The ends are anchored on tokens the system already has - step 1 is the
good tint, step 5 is the bad tint, step 3 is neutral - exactly as `.alv-age-2`
IS --alv-warn and `.alv-age-4` IS --alv-bad. A scale whose ends float free of
the semantics around it drifts, and this one had floated all the way to hsl().

Colour is REDUNDANT here, not load-bearing: every graded cell also prints its
own figure, so a reader who cannot separate the two ends still has the number.
That is what makes a green-to-red scale defensible at all, and it is worth
saying out loud rather than assuming.

GROUP D IS CLOSED. Both pages redefined `.table-container` as a horizontal
scroller while base uses the same name for a clipping panel. The sticky sweep
logged the collision and deliberately left it; base's own comment says these
two pages "belong on this, in a round of their own". This is that round, and
the answer is not a rename: the redefinition is DELETED, and the sideways
scroll the tables genuinely need gets a name of its own, `.ind-wide`.

Not base's `.alv-matrix-scroll`, which was the obvious home. It carries
`display: none` inside @media print, because the expense matrix deliberately
does not print. THESE tables do print, and did. Moving them onto that name
would have silently stopped it - which is the kind of thing a round notices
only if it looks.

THE TWO TABLES ARE NOT THE SAME TABLE, and this round does not pretend they
are. Vacancy's sits in a hand-rolled `.table-panel` / `.table-header` /
`.table-title` - which is `.alv-card` + `.alv-card-head` + `.alv-card-title`
spelled differently - and shows portrait phones a "Please rotate your device"
prompt instead of the table. Financial Indicators' sits in its own collapsible
`.fi-section` (untouched: a different component, a different question) and
carries Rank, Score and inactive rows that Vacancy has no equivalent for. What
they share is the table, and the table is what this round standardises.

The rotate prompt goes: base's card view is what the rest of the system does on
a phone, and it needs no instructions. `.table-panel`, `.table-header` and
`.table-title` are DEAD CSS in financial_indicators.html - the markup there
uses .fi-section - and are deleted from both.

WHAT THIS ROUND DOES NOT DO. The last hand-rolled segmented control - the
Budget / Actuals `.btn-group` on Financial Indicators, plus that page's other
`btn-outline-info` buttons - is a round of its own. So is the banding logic
that has drifted between the two files.

Run from the repo root.  --check plans without writing.
"""
import os
import re
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FI = os.path.join(T, 'finance', 'financial_indicators.html')
VM = os.path.join(T, 'finance', 'vacancy_management.html')
SWEEP = os.path.join(ROOT, 'test_sticky_sweep.py')
INDMODAL = os.path.join(ROOT, 'test_ind_modal.py')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_gradetables'

SENTINEL = '--alv-grade-1:'

# ---------------------------------------------------------------------------
# 1. base: the grading scale
# ---------------------------------------------------------------------------
B_TOK_ANCHOR = '        --alv-age-4-soft: #f6d5d2;'

B_TOK_NEW = """        --alv-age-4-soft: #f6d5d2;

        /* THE GRADING SCALE - five steps, best to worst.
           A sibling of the ageing scale, NOT a member of it: ageing runs
           "not ageing" to "severe" and begins at good, while a grade runs
           across a distribution and has a MIDDLE. Ends anchored on the
           semantics already in this block - step 1 is the good tint, step 5
           is the bad tint, step 3 is neutral - so the scale cannot drift
           away from the meanings around it, which is exactly what the
           computed hsl() ramp it replaces had done. */
        --alv-grade-1:      #1e7d4f;
        --alv-grade-1-soft: #cfe9da;
        --alv-grade-2:      #4a7b46;
        --alv-grade-2-soft: #e2f0e0;
        --alv-grade-3:      #5b6b73;
        --alv-grade-3-soft: #f2f1ee;
        --alv-grade-4:      #a8481a;
        --alv-grade-4-soft: #fae3da;
        --alv-grade-5:      #b3261e;
        --alv-grade-5-soft: #f7d3ce;"""

B_CLS_ANCHOR = """/* A year that straddles a change: the months before it carry the previous"""

B_CLS_NEW = """/* THE GRADING SCALE.
   Same machinery as the ageing scale above - the step class carries the
   colour, the application class decides what to do with it - so a grade can
   drive a cell tint today and a pill or a bar tomorrow without a second
   family of classes.

   COLOUR IS REDUNDANT HERE, NOT LOAD-BEARING. Every graded cell prints its
   own figure, so a reader who cannot separate the two ends of a red-green
   scale still has the number. That is the condition under which a scale like
   this is defensible, and it is written down so the next screen that wants
   one has to meet it too. */
.alv-grade-1 { --grade: var(--alv-grade-1); --grade-soft: var(--alv-grade-1-soft); }
.alv-grade-2 { --grade: var(--alv-grade-2); --grade-soft: var(--alv-grade-2-soft); }
.alv-grade-3 { --grade: var(--alv-grade-3); --grade-soft: var(--alv-grade-3-soft); }
.alv-grade-4 { --grade: var(--alv-grade-4); --grade-soft: var(--alv-grade-4-soft); }
.alv-grade-5 { --grade: var(--alv-grade-5); --grade-soft: var(--alv-grade-5-soft); }

.alv-grade-cell { background: var(--grade-soft, transparent); }
.alv-grade-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex: none;
    background: var(--grade, var(--alv-neutral));
}
@media print {
    /* A tint that carried meaning has to survive a printer, the way the
       ageing columns do. */
    .alv-grade-cell {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}

/* A year that straddles a change: the months before it carry the previous"""

# ---------------------------------------------------------------------------
# 2. CSS shared by both pages
# ---------------------------------------------------------------------------
SHARED_CSS = """/* THE DETAIL TABLE.

   .table-panel / .table-header / .table-title were .alv-card,
   .alv-card-head and .alv-card-title spelled differently, and in
   financial_indicators.html they were dead CSS besides - that page's markup
   uses .fi-section. .data-table was .alv-table with different spelling; the PORTFOLIO row sat
   in the TBODY where a <tfoot> belongs, painted solid teal with !important.
   Both are base's now, and the totals band repeats on every printed page,
   which a tbody row cannot.

   GROUP D IS CLOSED HERE. This page redefined .table-container as a
   horizontal scroller while base uses that name for a CLIPPING panel - the
   collision the sticky sweep logged and deliberately left alone. The
   redefinition is gone. The sideways scroll this table genuinely needs has a
   name of its own, and base's .alv-matrix-scroll was NOT the home for it: it
   carries display:none in @media print because the expense matrix does not
   print. This table does. */
.ind-wide { overflow-x: auto; }
@media print { .ind-wide { overflow: visible !important; } }

/* The sorted column keeps its emphasis - but NOT with a background.

   The old rule was `background: #e3f2fd !important`, and !important in a
   stylesheet beats an inline style, so sorting a column ERASED the grading
   tint in exactly the column the reader had just asked to look at. The
   emphasis moves to the edges and the weight, where it cannot compete with
   the scale. Found by rendering the two together; no amount of reading the
   CSS would have shown it. */
.highlighted-column {
    font-weight: 600;
    box-shadow: inset 3px 0 0 var(--alv-accent), inset -3px 0 0 var(--alv-accent);
}"""

FI_EXTRA_CSS = """

/* Properties not held in the selected year: excluded from rank, score and
   totals, and said so in ink rather than in a grey of its own. They are not
   graded either, so their cells carry no tint to be confused with one. */
.data-grid tbody tr.fi-inactive td { color: var(--alv-ink-faint); font-style: italic; }
.data-grid tbody tr.fi-inactive .highlighted-column { box-shadow: none; }
.data-grid tbody tr.fi-inactive .alv-grade-cell { background: transparent; }"""

# ---------------------------------------------------------------------------
# 3. vacancy_management.html
# ---------------------------------------------------------------------------
VM_CUTS = [
    ('VM: the panel is a card, and the rotate prompt goes',
     '            <div class="table-panel rotate-on-portrait">',
     '<table class="data-table">',
     """            <div class="alv-card">
                <div class="alv-card-head">
                    <i class="fas fa-table"></i>
                    <span class="alv-card-title">Detailed Property Data</span>
                </div>
                ${this.getSelectedProperties().length > 0 ? `
                    <div class="ind-wide">
                        <table class="table alv-table data-grid">"""),
    ('VM: the portfolio row becomes a tfoot',
     '                                <tr class="average-row">',
     '</tbody>',
     """                            </tbody>
                            <tfoot>
                                <tr>
                                    <td data-label="Portfolio">PORTFOLIO AVERAGE</td>
                                    ${this.indicators.map(indicator =>
                                        `<td class="num ${this.sortConfig.column === indicator.key ? 'highlighted-column' : ''}" data-label="${indicator.label}">${indicator.format(this.portfolioIndicators[indicator.key] || 0)}</td>`
                                    ).join('')}
                                </tr>
                            </tfoot>"""),
    ('VM: the hand-rolled panel, table and teal totals row come out',
     '.table-panel {',
     '.average-row .highlighted-column {\n    background-color: #0a5e6a !important;\n'
     '    border-left: 3px solid #ffffff;\n    border-right: 3px solid #ffffff;\n}',
     SHARED_CSS),
    ('VM: and so does the rotate prompt',
     '/* Rotate prompt (portrait phones for the data table) */',
     '@keyframes rotate-hint {\n    0%, 30%   { transform: rotate(0deg); }\n'
     '    50%, 70%  { transform: rotate(-90deg); }\n'
     '    100%      { transform: rotate(0deg); }\n}',
     """/* The rotate-to-landscape prompt is gone. base turns .alv-table into
   cards on a phone, which is what every other list in this system does and
   needs no instructions - and the prompt was telling a reader to hold the
   device differently rather than showing them the data. */"""),
    ('VM: the phone rule that hid the table',
     '    /* Data table \u2192 rotate prompt on portrait */',
     '    .table-panel.rotate-on-portrait .rotate-prompt {\n        display: flex;\n    }',
     '    /* The table becomes cards through base now. */'),
]

VM_ONE = [
    ('VM: the sortable headings are numeric',
     "`<th class=\"sortable-header ${this.sortConfig.column === indicator.key",
     "`<th class=\"sortable-header num ${this.sortConfig.column === indicator.key"),
    ('VM: the name cell gets its card label',
     "<td>${property.name}</td>",
     '<td data-label="Property">${property.name}</td>'),
    ('VM: every metric cell is numeric and labelled',
     "`<td class=\"${this.sortConfig.column === indicator.key ? 'highlighted-column' : ''}\">${indicator.format(property[indicator.key])}</td>`",
     "`<td class=\"num ${this.sortConfig.column === indicator.key ? 'highlighted-column' : ''}\" data-label=\"${indicator.label}\">${indicator.format(property[indicator.key])}</td>`"),
]

# ---------------------------------------------------------------------------
# 4. financial_indicators.html
# ---------------------------------------------------------------------------
FI_CUTS = [
    ('FI: the table onto the standard, the wrapper renamed',
     '<div class="table-container">',
     '<table class="data-table">',
     '<div class="ind-wide">\n'
     '                        <table class="table alv-table data-grid">'),
    ('FI: the portfolio row becomes a tfoot',
     '                                <!-- Portfolio totals row -->',
     '</tbody>',
     """                            </tbody>
                            <tfoot>
                                <tr>
                                    <td data-label="Portfolio">PORTFOLIO TOTALS</td>
                                    <td class="num" data-label="Rank">&mdash;</td>
                                    <td class="num" data-label="Score">&mdash;</td>
                                    ${this.tableColumns.map(indicator =>
                                        `<td class="num ${this.sortConfig.column === indicator.key ? 'highlighted-column' : ''}" data-label="${indicator.label}">${indicator.format(this.portfolioIndicators[indicator.key] || 0)}</td>`
                                    ).join('')}
                                </tr>
                            </tfoot>"""),
    ('FI: the dead panel CSS and the teal totals row come out',
     '.table-panel {\n    background: white;',
     '.data-table tbody tr.fi-inactive .highlighted-column {\n'
     '    background: #eceded !important;\n'
     '    border-left-color: #cfd2d4;\n'
     '    border-right-color: #cfd2d4;\n}',
     SHARED_CSS + FI_EXTRA_CSS),
    ('FI: and a hundred lines of hand-rolled phone cards',
     '    .table-panel {\n        background: transparent;',
     '    .data-table tbody tr.average-row td.highlighted-column {\n'
     '        background: rgba(255,255,255,0.15) !important;\n'
     '        border-radius: 4px;\n        padding: 8px 10px;\n    }',
     '    /* The detail table becomes cards through base now - a hundred\n'
     '       lines of it used to live here, and a second hand-rolled copy\n'
     '       lived in the sibling file. */'),
]

FI_ONE = [
    ('FI: the leftover totals-row rule',
     """.average-row .highlighted-column {
    background-color: #0a5e6a !important;
    border-left: 3px solid #ffffff;
    border-right: 3px solid #ffffff;
}

""", ''),
    ('FI: the heat map becomes five named steps',
     """    cellColour(t) {
        if (t === undefined || t === null) return '';
        const hue = (1 - t) * 120;   // 0 = red (worst) .. 120 = green (best)
        return `background-color: hsl(${hue}, 62%, 90%);`;
    }""",
     """    // FIVE NAMED STEPS, not a computed ramp.
    //
    // This returned `background-color: hsl((1-t)*120, 62%, 90%)` - a
    // continuous red-through-yellow-to-green rainbow, built in JavaScript,
    // outside the token system, unprintable and uncheckable. The grade it
    // encodes is real information, so it stays; the way it was expressed
    // does not.
    //
    // WHICH END OF t IS GOOD. Read it off gradeColumn, not off the comment
    // above the old ramp - that comment describes the HUE value, not t, and
    // reads exactly backwards if you take it as describing t. gradeColumn
    // sorts BEST FIRST and stores position / (n - 1), so t = 0 is the best
    // property in the column and t = 1 is the worst. Hence t * 5, and step 1
    // is best. Getting this backwards inverts the whole table and every
    // figure still looks plausible.
    gradeClass(t) {
        if (t === undefined || t === null) return '';
        const step = Math.min(4, Math.max(0, Math.floor(t * 5)));
        return 'alv-grade-cell alv-grade-' + (step + 1);
    }"""),
    ('FI: the rank and score cells take a step',
     """                                        <td data-label="Rank" style="${inactive ? '' : this.cellColour(this._grade['_rank'][property.id])} font-weight:600;">${rankCell}</td>
                                        <td data-label="Score" style="${inactive ? '' : this.cellColour(this._grade['_score'][property.id])} font-weight:700;">${scoreCell}</td>""",
     """                                        <td class="num fi-rank ${inactive ? '' : this.gradeClass(this._grade['_rank'][property.id])}" data-label="Rank">${rankCell}</td>
                                        <td class="num fi-score ${inactive ? '' : this.gradeClass(this._grade['_score'][property.id])}" data-label="Score">${scoreCell}</td>"""),
    ('FI: and so does every metric cell',
     """                                            const style = (inactive || na) ? '' : this.cellColour(this._grade[indicator.key][property.id]);
                                            return `<td data-label="${indicator.label}" class="${this.sortConfig.column === indicator.key ? 'highlighted-column' : ''}" style="${style}">${show}</td>`;""",
     """                                            const grade = (inactive || na) ? '' : this.gradeClass(this._grade[indicator.key][property.id]);
                                            return `<td data-label="${indicator.label}" class="num ${grade} ${this.sortConfig.column === indicator.key ? 'highlighted-column' : ''}">${show}</td>`;"""),
    ('FI: the hover tint on the sorted column',
     """
@media (hover: hover) and (pointer: fine) {
    .data-table tbody tr:hover .highlighted-column {
        background-color: #bbdefb !important;
    }
}
""", ''),
    ('FI: and the last two selectors naming the old table',
     """    .data-table tbody tr,
    #modalPropertyTable tbody tr {
        padding: 10px 12px;
    }
""", ''),
    ('FI: the property name cell gets its card label',
     """                                        <td>${property.name}${inactive ? ' <span class="fi-inactive-tag">not held this year</span>' : ''}</td>""",
     """                                        <td data-label="Property">${property.name}${inactive ? ' <span class="fi-inactive-tag">not held this year</span>' : ''}</td>"""),
]

FI_WEIGHT_CSS = """
/* The two graded columns keep their weight; the tint says where they sit. */
.data-grid td.fi-rank { font-weight: 600; }
.data-grid td.fi-score { font-weight: 700; }"""

# ---------------------------------------------------------------------------
# 5. section 4b - the sticky sweep records that group D is CLOSED
# ---------------------------------------------------------------------------
S_OLD = """    check('%-38s still has its own rule' % rel, bool(container_rules(src)))
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

# The indicator-modal round asserted that THIS round's work was still ahead of
# it - a deliberate scope guard, and exactly the kind of expectation that has
# to move the moment the next round lands. It is superseded, not wrong.
I_OLD = """# ... and the NEXT round's work is untouched
for _keep in ('rotate-prompt', 'rotate-on-portrait', 'data-table',
              'Detailed Property Data'):
    check('vacancy: %s survives - that is the next round' % _keep, _keep in V)
check('vacancy: group D is untouched',
      '.table-container { overflow-x: auto; }' in V)"""

I_NEW = """# SUPERSEDED 1 Sep: the next round landed. These four asserted that the detail
# table, its rotate-to-landscape prompt and the group D name collision were
# still ahead - a scope guard, and one that has to invert the moment the work
# it was guarding is done. The screen it names is still there; what carried it
# is not.
check('vacancy: the detail table is still on the page',
      'Detailed Property Data' in V)
for _gone in ('rotate-prompt', 'rotate-on-portrait', 'data-table'):
    check('vacancy: %s went with the detail-table round' % _gone,
          _gone not in VC)
check('vacancy: group D is closed - the page no longer redefines the name',
      '.table-container { overflow-x: auto; }' not in V)"""

S_NEW = """    # GROUP D IS CLOSED - 1 Sep. Twice this block has been moved rather than
    # deleted: first because these pages did not use .alv-table at all, then
    # because the .alv-table they gained sat outside the redefined name. Now
    # the redefinition itself is gone, so the expectation inverts one last
    # time and becomes the strongest form of itself: this page must NOT
    # redefine .table-container, and base's meaning of the name is the only
    # one left.
    check('%-38s no longer redefines .table-container' % rel,
          not container_rules(src),
          '%d rule(s)' % len(container_rules(src)))
    check('  it is on the standard', 'alv-table' in src)
    check('  and the sideways scroll it needs has its own name',
          '.ind-wide' in src)
    check('  so nothing on the page claims the name any more',
          'class=\"table-container\"' not in src)"""


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
    """start..end INCLUSIVE. `start` must be unique; `end` is the first one
    at or after it, since a closing tag appears many times in a file."""
    if text.count(start) != 1:
        sys.exit('! %s: the start marker appears %d times, expected 1:\n%s'
                 % (what, text.count(start), start[:220]))
    i = text.index(start)
    j = text.find(end, i)
    if j < 0:
        sys.exit('! %s: the end marker never appears after the start:\n%s'
                 % (what, end[:220]))
    return text[:i] + new + text[j + len(end):]


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)   # NOT re.S - Django has no DOTALL

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
    for p in (BASE, FI, VM, SWEEP, INDMODAL):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    bs, fi, vm, sw = read(BASE), read(FI), read(VM), read(SWEEP)
    im = read(INDMODAL)
    bs0, fi0, vm0, sw0, im0 = bs, fi, vm, sw, im

    if SENTINEL in bs:
        print('  grading scale + detail tables    already applied')
        print('\n  0 file(s) changed')
        return

    names = []
    bs = one(bs, B_TOK_ANCHOR, B_TOK_NEW, 'base: the grading tokens')
    bs = one(bs, B_CLS_ANCHOR, B_CLS_NEW, 'base: .alv-grade-1..5')
    names += ['base: the grading tokens', 'base: .alv-grade-1..5']

    for what, old, new in VM_ONE:
        vm = one(vm, old, new, what)
        names.append(what)
    for what, start, end, new in VM_CUTS:
        vm = between(vm, start, end, new, what)
        names.append(what)

    for what, start, end, new in FI_CUTS:
        fi = between(fi, start, end, new, what)
        names.append(what)
    for what, old, new in FI_ONE:
        fi = one(fi, old, new, what)
        names.append(what)
    fi = one(fi, SHARED_CSS + FI_EXTRA_CSS,
             SHARED_CSS + FI_EXTRA_CSS + FI_WEIGHT_CSS,
             'FI: the two graded columns keep their weight')
    names.append('FI: the two graded columns keep their weight')

    sw = one(sw, S_OLD, S_NEW, '4b: the sweep records group D as CLOSED')
    im = one(im, I_OLD, I_NEW, "4b: the modal round's scope guard inverts")
    names += ['4b: the sweep records group D as CLOSED',
              "4b: the modal round's scope guard inverts"]

    # -----------------------------------------------------------------------
    # SELF-CHECK. Nothing is written unless every one of these holds.
    # -----------------------------------------------------------------------
    bad = []
    bc = nocomment_html(bs)
    pages = (('financial_indicators.html', nocomment_html(fi), fi, fi0),
             ('vacancy_management.html', nocomment_html(vm), vm, vm0))

    # -- base: the scale exists, is defined, and is five distinct steps -----
    for n in range(1, 6):
        for suffix in ('', '-soft'):
            if '--alv-grade-%d%s:' % (n, suffix) not in bc:
                bad.append('base has no --alv-grade-%d%s token' % (n, suffix))
        if '.alv-grade-%d {' % n not in bc:
            bad.append('base has no .alv-grade-%d class' % n)
    _softs = re.findall(r'--alv-grade-\d-soft:\s*(#[0-9a-fA-F]{6})', bc)
    if len(set(_softs)) != 5:
        bad.append('the five steps are not five distinct colours: %s' % _softs)
    # A SCALE THAT LOOKS LIKE A SCALE. Outstanding Invoices once shipped two
    # near-identical pale blues with a grey between them.
    def _rgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    for a, b in zip(_softs, _softs[1:]):
        _d = sum(abs(x - y) for x, y in zip(_rgb(a), _rgb(b)))
        if _d < 18:
            bad.append('steps %s and %s are too close to read as an order '
                       '(distance %d)' % (a, b, _d))
    # The ends are anchored, not invented.
    if '--alv-grade-1: ' not in bc.replace('  ', ' '):
        pass
    for _end, _tok in (('1', '--alv-good'), ('5', '--alv-bad')):
        _v = re.search(r'--alv-grade-%s:\s*(#[0-9a-fA-F]{6})' % _end, bc)
        _t = re.search(r'%s:\s*(#[0-9a-fA-F]{6})' % _tok, bc)
        if not (_v and _t and _v.group(1).lower() == _t.group(1).lower()):
            bad.append('step %s is not anchored on %s' % (_end, _tok))
    if '.alv-grade-cell' not in bc:
        bad.append('base defines no application class for the scale')
    for _tok in sorted(set(re.findall(r'var\((--alv-[a-z0-9-]+)\s*\)',
                                      B_CLS_NEW + B_TOK_NEW))):
        if '%s:' % _tok not in bc:
            bad.append('%s is referenced and never defined' % _tok)

    # -- the pages ---------------------------------------------------------
    for name, c, raw, before in pages:
        for _dead in ('data-table', 'table-panel', 'table-header',
                      'table-title', 'average-row', 'cellColour'):
            if re.search(r'(?<![\w-])%s(?![\w-])' % _dead, c):
                bad.append('%s: %s survives' % (name, _dead))
        # GROUP D: the redefinition must be GONE, not renamed.
        _css = re.sub(r'/\*.*?\*/', '', css_of(raw), flags=re.S)
        if re.search(r'(^|\})\s*\.table-container[^{]*\{', _css):
            bad.append('%s: still redefines .table-container - group D is '
                       'the whole point of this round' % name)
        if '.ind-wide {' not in c:
            bad.append('%s: the sideways scroll lost its name' % name)
        if 'class="ind-wide"' not in c:
            bad.append('%s: nothing uses .ind-wide' % name)
        # NOT .alv-matrix-scroll: it is display:none in print.
        if 'alv-matrix-scroll' in c:
            bad.append('%s: moved onto .alv-matrix-scroll, which does not '
                       'print' % name)
        if 'class="table alv-table data-grid"' not in c:
            bad.append('%s: the detail table is not .alv-table' % name)
        if '<tfoot>' not in c:
            bad.append('%s: the portfolio row is still in the tbody' % name)
        if c.count('<tfoot>') != c.count('</tfoot>'):
            bad.append('%s: the tfoot does not close' % name)
        if 'data-label="Property"' not in c:
            bad.append('%s: the name cell has no card label' % name)
        if 'data-label="Portfolio"' not in c:
            bad.append('%s: the totals row has no card label' % name)
        if not re.search(r'\.highlighted-column\s*\{[^}]*var\(--alv-accent\)', c):
            bad.append('%s: the sorted column is not on a token' % name)
        if re.search(r'(?m)^\.highlighted-column\s*\{[^}]*background', c):
            bad.append('%s: the sorted column still paints a background, '
                       'which would erase the grade tint under it' % name)
        # NOT "these literals are gone from the file": #0e7c8b is this
        # page's accent and appears in buttons this round never touches. A
        # check wider than its round reports failures that are not defects,
        # and then gets relaxed. What must hold is that the rules this round
        # replaced no longer carry them, and that the file got LESS literal.
        _before_lits = set(re.findall(r'#[0-9a-fA-F]{3,8}\b',
                                      re.sub(r'/\*.*?\*/', '',
                                             css_of(before), flags=re.S)))
        _after_lits = set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _css))
        if len(_after_lits) >= len(_before_lits):
            bad.append('%s: distinct literal colours did not fall (%d -> %d)'
                       % (name, len(_before_lits), len(_after_lits)))
        if re.search(r'\.highlighted-column[^{]*\{[^}]*#[0-9a-fA-F]{3,8}', _css):
            bad.append('%s: the sorted column still carries a literal' % name)
        # The round must SHRINK these files.
        if len(raw) >= len(before):
            bad.append('%s did not get smaller (%d -> %d)'
                       % (name, len(before), len(raw)))
        # Structure.
        if _css.count('{') != _css.count('}'):
            bad.append('%s: CSS braces do not balance' % name)
        for o, cl in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                      (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
            if len(re.findall(o, raw)) != len(re.findall(cl, raw)):
                bad.append('%s: a Django block no longer balances' % name)
        for _l in raw.split('\n'):
            if _l.count('{#') != _l.count('#}'):
                bad.append('%s: a {# #} comment spans lines' % name)
                break
        for tag in ('table', 'thead', 'tbody', 'tfoot'):
            if (len(re.findall(r'<%s\b' % tag, c))
                    != len(re.findall(r'</%s\s*>' % tag, c))):
                bad.append('%s: <%s> does not balance' % (name, tag))

    # -- vacancy: the rotate prompt, root and branch -----------------------
    _v = nocomment_html(vm)
    for _dead in ('rotate-prompt', 'rotate-on-portrait', 'rotate-icon',
                  'rotate-hint', 'Please rotate your device'):
        if _dead in _v:
            bad.append('vacancy_management.html: %s survives' % _dead)
    if 'class="alv-card"' not in _v or 'alv-card-head' not in _v:
        bad.append('vacancy_management.html: the panel is not a card')

    # -- financial indicators: the scale is USED, and only through classes --
    _f = nocomment_html(fi)
    if 'gradeClass(' not in _f:
        bad.append('financial_indicators.html: nothing assigns a grade')
    if 'hsl(' in _f:
        bad.append('financial_indicators.html: the computed ramp survives')
    if re.search(r'style="\$\{[^"]*grade', _f):
        bad.append('financial_indicators.html: a grade still arrives as an '
                   'inline style')
    if _f.count('gradeClass(') != 4:
        bad.append('financial_indicators.html: gradeClass is declared once '
                   'and used three times, found %d references'
                   % _f.count('gradeClass('))
    # THE STEP FUNCTION'S ENDS - and its DIRECTION, which is the part that
    # nearly shipped inverted. t comes from gradeColumn, which sorts best
    # first and stores position / (n - 1): t = 0 is best. Both halves are
    # asserted, because a step function with the right ends and the wrong
    # direction produces a table that looks entirely reasonable.
    if not re.search(r'const order = \[\.\.\.valid\]\.sort\(\(a, b\) => '
                     r'higher \? \(b\[key\] - a\[key\]\)', _f):
        bad.append('gradeColumn no longer sorts best-first, so t may not mean '
                   'what gradeClass assumes')
    if 'Math.floor(t * 5)' not in _f:
        bad.append('the step function does not read t the way gradeColumn '
                   'writes it')
    for _t, _want in ((0.0, 1), (1.0, 5), (0.5, 3)):
        _step = min(4, max(0, int(_t * 5))) + 1
        if _step != _want:
            bad.append('the step function maps t=%s to %d, expected %d'
                       % (_t, _step, _want))

    # -- 4b ----------------------------------------------------------------
    try:
        compile(sw, 'test_sticky_sweep.py', 'exec')
    except SyntaxError as exc:
        bad.append('the patched sticky suite does not parse: %s' % exc)
    if sw.count('check(') < sw0.count('check('):
        bad.append('the sticky suite lost checks - an expectation was DELETED')
    _sw_code = '\n'.join(l for l in sw.split('\n')
                         if not l.lstrip().startswith('#'))
    if 'container_rules(src))' in _sw_code and \
            'not container_rules(src)' not in _sw_code:
        bad.append('the sweep still expects these pages to redefine the name')
    try:
        compile(im, 'test_ind_modal.py', 'exec')
    except SyntaxError as exc:
        bad.append('the patched modal suite does not parse: %s' % exc)
    if im.count('check(') < im0.count('check('):
        bad.append('the modal suite lost checks - an expectation was DELETED')
    _im_code = '\n'.join(l for l in im.split('\n')
                         if not l.lstrip().startswith('#'))
    if 'that is the next round' in _im_code:
        bad.append('the modal suite still guards work this round has done')

    # -- CONTROL on the stripper -------------------------------------------
    if '.table-panel' not in vm:
        bad.append('CONTROL: the round lost the prose it strips against')
    if '.table-panel' in _v:
        bad.append('CONTROL: comments are not being stripped')

    if bad:
        sys.exit('! grading/detail-table self-check FAILED, nothing written:'
                 '\n   - %s' % '\n   - '.join(bad))

    for n in names:
        print('  %s' % n)
    print('  financial_indicators.html  %d -> %d bytes' % (len(fi0), len(fi)))
    print('  vacancy_management.html    %d -> %d bytes' % (len(vm0), len(vm)))

    if not CHECK:
        for path, out in ((BASE, bs), (FI, fi), (VM, vm), (SWEEP, sw),
                          (INDMODAL, im)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  5 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
