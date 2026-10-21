# -*- coding: utf-8 -*-
"""apply_week_band.py - round WT-1, 21 Oct 2026.

THE SELECTED WEEK AND THE MEALS ON IT WERE THE SAME COLOUR.

Demetri, testing push 3:

    "Can the week highlight of the month view differ in colour to the
     colour of the pills for the recipes?"

MEASURED, AND IT IS WORSE THAN DIFFERING TOO LITTLE:

    .month-cell.in-week   background: var(--alv-accent-soft)
    .month-chip           background: var(--alv-accent-soft)

The same token. In CIE Lab the distance between a pill and the row it
sits on is dE 0.0 - not "hard to tell apart", IDENTICAL. The only
thing separating them is the 1px accent-line border CL-1 added on 20
October, which is why CL-1's note says a pill on the tinted week row
needed "borders on tinted surfaces". That round treated the symptom.

A FOURTH FILL IS NOT AVAILABLE. The month cell already paints three
states in a very narrow band of near-whites - paper for a normal day,
surface for hover and for a day outside the month, accent-soft for
the selected week - and every candidate for a fourth was measured:

    surface-deep   dE 4.5 from the pill, but dE 4.8 from is-out, so
                   "the week you are on" and "not this month" become
                   two greys
    a pale accent  as it gets far enough from the pill (dE 4+) it
                   closes on surface (dE 2.2). There is no gap.

SO CHANGE THE CHANNEL, NOT THE COLOUR. The week is marked by a 2px
accent rule above and below it and the cells stay white. The row and
the pill stop competing for the same property: one owns the EDGE, the
other owns the FILL. Rendered side by side with all four candidates
before this was written.

THE 1px GRID GAPS DO NOT BREAK IT. .month-grid is `gap: 1px` over a
line-soft ground, so an inset rule is interrupted six times across a
week. I expected that to read as a dashed line and it does not - at
1px the breaks are invisible and the band reads continuous. Rendered,
not reasoned.

Idempotent. Every file backed up to .bak_weekband.
"""
import os
import re
import sys

SUFFIX = '.bak_weekband'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_week_band.py'
PATCHER = 'apply_week_band.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'WT-1, 21 Oct 2026'
CHECK = False
CREATES = ()

BAND_WAS = """.month-cell.in-week {
    background: var(--alv-accent-soft);
}"""

BAND_NOW = """/* THE WEEK OWNS THE EDGE, THE MEAL OWNS THE FILL - WT-1, 21 Oct 2026.
   This was `background: var(--alv-accent-soft)`, which is the SAME
   TOKEN .month-chip fills itself with: dE 0.0 in Lab, so a pill on
   the selected week was the pill's 1px border and nothing else. CL-1
   added that border on 20 October and it was treating the symptom.
   A fourth near-white was measured and there is no room for one -
   surface-deep lands 4.8 from is-out, and a pale accent closes on
   surface before it clears the pill. Two properties, not two tints. */
.month-cell.in-week {
    background: var(--alv-paper);
    box-shadow: inset 0 2px 0 var(--alv-accent),
                inset 0 -2px 0 var(--alv-accent);
}"""


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
    raise SystemExit('WT-1 REFUSED: %s' % msg)


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


def rule(text, sel):
    """The body of one CSS rule, by exact selector."""
    m = re.search(re.escape(sel) + r'\s*\{([^}]*)\}', text)
    return m.group(1) if m else None


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'THE WEEK OWNS THE EDGE' in t:
        print('WT-1  already applied - the week is a band.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)

    # ---- THE FINDING, ASKED OF THE TWO RULES RATHER THAN ASSUMED.
    row = rule(code, '.month-cell.in-week')
    chip = rule(code, '.month-chip')
    if row is None or chip is None:
        refuse('%s: cannot find both .month-cell.in-week and .month-chip'
               % TPL)
    def bg(body):
        m = re.search(r'background:\s*([^;]+);', body or '')
        return m.group(1).strip() if m else None
    if bg(row) != bg(chip):
        refuse('%s: the row fills with %r and the pill with %r - they '
               'already differ, so this round has nothing to separate'
               % (TPL, bg(row), bg(chip)))

    t = swap(t, BAND_WAS, BAND_NOW, '%s (the selected week)' % TPL)
    out[pt] = t

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_bar_first.py'
)""", """    'test_bar_first.py',
    # WT-1, 21 Oct 2026 - the selected week and the meals on it were
    # the same token, dE 0.0. The week is an edge now.
    'test_week_band.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE PRIMARY FIRST - BO-1';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEK OWNS THE EDGE'; What = 'WT-1: the selected week in Month view is marked by an accent rule above and below rather than by a fill - it used to fill with the exact token the meal pills fill with, so a pill on that row was its 1px border and nothing else' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE PRIMARY FIRST - BO-1';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # BO-1, 21 Oct 2026 - the planner bar in house order.
    'test_bar_first.py',
]""", """    # BO-1, 21 Oct 2026 - the planner bar in house order.
    'test_bar_first.py',
    # WT-1, 21 Oct 2026 - a row and the pills on it, told apart.
    'test_week_band.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # BO-1, 21 Oct 2026 - the primary comes first.
    '.bak_barfirst',
]""", """    # BO-1, 21 Oct 2026 - the primary comes first.
    '.bak_barfirst',
    # WT-1, 21 Oct 2026 - the week owns the edge, the meal the fill.
    '.bak_weekband',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # WT-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    nrow = rule(nc, '.month-cell.in-week')
    nchip = rule(nc, '.month-chip')
    if bg(nrow) == bg(nchip):
        refuse('%s: the row and the pill still fill with %r'
               % (TPL, bg(nrow)))
    if 'box-shadow' not in (nrow or ''):
        refuse('%s: the week has no edge to be marked by' % TPL)
    if 'var(--alv-accent)' not in (nrow or ''):
        refuse('%s: the edge is not the accent, so it will not read as '
               'a selection' % TPL)
    # AND THE PILL IS UNTOUCHED. The fix belongs to the row: the pill
    # colour is the meal vocabulary and Week and Day views use it too.
    if bg(nchip) != 'var(--alv-accent-soft)':
        refuse('%s: this round moved the PILL (%r). Three views share '
               'that token and only Month has the collision.'
               % (TPL, bg(nchip)))
    # THE OTHER THREE CELL STATES ARE UNTOUCHED.
    for sel, want in (('.month-cell', 'var(--alv-paper)'),
                      ('.month-cell.is-out', 'var(--alv-surface)')):
        if bg(rule(nc, sel)) != want:
            refuse('%s: %s no longer fills with %s' % (TPL, sel, want))

    if CHECK:
        print('WT-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        row %s -> %s   (pill stays %s)'
              % (bg(row), bg(nrow), bg(nchip)))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('WT-1  applied - the week is an edge, the meal is a fill.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
