# -*- coding: utf-8 -*-
"""apply_week_fill.py - round WF-1, 21 Oct 2026.

THE WEEK BAND NEEDS A FILL, AND THERE WAS ROOM FOR ONE AFTER ALL.

Demetri, having used what WT-1 shipped this morning:

    "I don't like the way that the current week is highlighted in the
     Month View. It needs a colour fill."

WT-1 WAS RIGHT ABOUT THE FAULT AND WRONG ABOUT THE REMEDY. The band
used to fill with `--alv-accent-soft`, which is the token .month-chip
fills ITSELF with - dE 0.0 in CIE Lab, so a meal on the selected week
was the pill's 1px border and nothing else. That finding stands.

WHAT WT-1 GOT WRONG WAS THE SEARCH, NOT THE SUM. It measured two
candidates for a fourth fill - `--alv-surface-deep` and a pale accent
- found both too close to something, and concluded there was no room:

    "A fourth near-white was measured and there is no room for one."

TWO IS NOT A SEARCH. base carries ten more pale tints in the TAG
palette - sky, moss, clay, slate, plum - which exist to be decorative
and carry no status meaning at all, unlike good (healthy), warn
(attention) or bad (overdue). None of them was looked at.

ASKED OF ALL THIRTEEN, AGAINST ALL FOUR THINGS ALREADY ON THE GRID -
the cell, the out-of-month cell, and the three pill fills a meal, a
note and a leftover wear. Worst-case dE, so a candidate is only as
good as its closest collision:

    tag-moss-soft   #eef4e9     6.9     <- this round
    tag-clay-soft   #f7efe7     6.4
    tag-plum-soft   #f3edf5     4.3
    spice-soft      #fdf0e4     5.2     (5.2 of it from the NOTE pill)
    good-soft       #e6f4ec     5.1     (5.1 of it from the MEAL pill)
    tag-sky-soft    #e8f1f5     2.3
    surface-deep    #e9ecef     0.0     (IS the leftover pill)
    warn-soft       #fdf3dd     0.0     (IS the note pill)
    accent-soft     #e4f3f5     0.0     (IS the meal pill - the fault)

MOSS CLEARS EVERYTHING BY 6.9, which is three times the threshold a
trained eye can just detect. Demetri was shown moss and clay side by
side on a week holding all three pill types: "I'm happy with the
moss."

AND THE EDGE STAYS. Two signals, not one - the fill says WHICH week
and the accent rule says the band is a selection rather than a tint
somebody chose. WT-1's own lesson, kept.

Idempotent. Every file backed up to .bak_weekfill.
"""
import os
import re
import sys

SUFFIX = '.bak_weekfill'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
BAND = 'test_week_band.py'
ME = 'test_week_fill.py'
PATCHER = 'apply_week_fill.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'WF-1, 21 Oct 2026'
CHECK = False
CREATES = ()

CSS_WAS = """/* THE WEEK OWNS THE EDGE, THE MEAL OWNS THE FILL - WT-1, 21 Oct 2026.
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

CSS_NOW = """/* THE WEEK OWNS BOTH NOW - WT-1, 21 Oct 2026, corrected by WF-1 the
   same day.

   THE FAULT WT-1 FOUND STANDS. This filled with `--alv-accent-soft`,
   which is the SAME TOKEN .month-chip fills itself with: dE 0.0 in
   Lab, so a pill on the selected week was the pill's 1px border and
   nothing else. CL-1 added that border on 20 October and it was
   treating the symptom.

   WHAT WT-1 GOT WRONG WAS THE SEARCH. It measured TWO candidates for
   a fourth fill - surface-deep and a pale accent - and concluded
   there was no room. base carries ten more pale tints in the TAG
   palette, which exist to be decorative and carry no status meaning
   at all. None of them had been looked at.

   ASKED OF ALL THIRTEEN against the four fills already on this grid -
   the cell, the out-of-month cell, and the meal, note and leftover
   pills. Worst-case dE, because a candidate is only as good as its
   nearest collision:

       tag-moss-soft  6.9      spice-soft   5.2 (from the NOTE pill)
       tag-clay-soft  6.4      good-soft    5.1 (from the MEAL pill)
       tag-plum-soft  4.3      tag-sky-soft 2.3

   Moss clears everything by 6.9 - three times the threshold a trained
   eye can just detect - and carries no meaning to collide with.

   AND THE EDGE STAYS. Two signals: the fill says WHICH week, the rule
   says it is a selection rather than a tint somebody chose. */
.month-cell.in-week {
    background: var(--alv-tag-moss-soft);
    box-shadow: inset 0 2px 0 var(--alv-accent),
                inset 0 -2px 0 var(--alv-accent);
}"""


# =====================================================================
# WT-1's OWN SUITE, CORRECTED IN THE SAME PATCHER
# =====================================================================
# Two of its claims are about the remedy rather than the fault, and
# this round changes the remedy. The fault claim - row and pill no
# longer share a fill - is untouched and still the point.
BAND_PAPER_WAS = """    c['  the cells themselves are paper again'] = (
        bg(row) == 'var(--alv-paper)')"""

BAND_PAPER_NOW = """    # WF-1, 21 Oct 2026 - MOSS, not paper. Demetri, having used what
    # WT-1 shipped: "It needs a colour fill." The band fills with a
    # tag-palette tint that clears every other fill on this grid by
    # 6.9 dE, and keeps the accent rule as a second signal.
    c['  the cells fill with a tint nothing else here uses'] = (
        bg(row) == 'var(--alv-tag-moss-soft)')"""

BAND_REJECT_WAS = """    # WHY NO FOURTH FILL. Kept as a measurement rather than as prose
    # so that a later round proposing one has to re-read the numbers.
    print('  rejected candidates for a fourth fill:')
    for name, c in (('surface-deep', deep),
                    ('pale accent, 45pc white', '#f0f8fa')):
        print('     %-22s dE pill %4.1f   dE is-out %4.1f'
              % (name, dE(soft, c), dE(surface, c)))
    ok(dE(surface, deep) < 5.0,
       '  surface-deep lands close to is-out, so "this week" and "not '
       'this month" would be two greys: dE %.1f' % dE(surface, deep))
    ok(dE(surface, '#f0f8fa') < 3.0,
       '  and a pale accent closes on surface before it clears the '
       'pill: dE %.1f' % dE(surface, '#f0f8fa'))"""

BAND_REJECT_NOW = """    # THE FOURTH FILL WAS FOUND - WF-1, 21 Oct 2026. These two
    # candidates really are too close, and that part of WT-1 stands.
    # What did not stand was the conclusion drawn from two: base
    # carries ten more pale tints in the tag palette and none of them
    # had been measured. test_week_fill asks all thirteen.
    print('  the two WT-1 measured, and both still fail:')
    for name, c in (('surface-deep', deep),
                    ('pale accent, 45pc white', '#f0f8fa')):
        print('     %-22s dE pill %4.1f   dE is-out %4.1f'
              % (name, dE(soft, c), dE(surface, c)))
    ok(dE(surface, deep) < 5.0,
       '  surface-deep lands close to is-out, so "this week" and "not '
       'this month" would be two greys: dE %.1f' % dE(surface, deep))
    ok(dE(surface, '#f0f8fa') < 3.0,
       '  and a pale accent closes on surface before it clears the '
       'pill: dE %.1f' % dE(surface, '#f0f8fa'))
    moss = token('--alv-tag-moss-soft')
    ok(moss and dE(soft, moss) >= VISIBLE * 2,
       '  AND THE ONE WF-1 FOUND CLEARS THE PILL BY %.1f - from a '
       'palette WT-1 never looked at'
       % (dE(soft, moss) if moss else 0.0))"""

# ---- AND WT-1's PUSH-GATE SENTINEL, WHICH THIS ROUND MADE STALE.
#
# WT-1 pinned the planner on the words "THE WEEK OWNS THE EDGE" - the
# heading of the comment this round rewrites, because the week owns
# both now. A sentinel that names text no longer on disk fails EVERY
# suite carrying the shared "all 560 rows still resolve" check: thirty
# of them in the 21 October sweep. Push 4 lost 22 suites to exactly
# this three days ago. The row moves with the text it points at, and
# its description moves with the behaviour.
GATE_WT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEK OWNS THE EDGE'; What = 'WT-1: the selected week in Month view is marked by an accent rule above and below rather than by a fill - it used to fill with the exact token the meal pills fill with, so a pill on that row was its 1px border and nothing else' },"""

GATE_WT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEK OWNS BOTH NOW'; What = 'WT-1 as WF-1 corrected it: the selected week in Month view wears an accent rule above and below AND a moss fill. WT-1 found the fault - it used to fill with the exact token the meal pills fill with, so a pill on that row was its 1px border and nothing else - and concluded there was no room for a fourth fill after measuring two candidates. There was: moss clears every fill on that grid by 6.9 dE' },"""


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
    raise SystemExit('WF-1 REFUSED: %s' % msg)


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


# ---- THE INSTRUMENT, so the gate measures rather than trusts.
def _rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab(h):
    import math
    r, g, b = [v / 255.0 for v in _rgb(h)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    X = r * 0.4124 + g * 0.3576 + b * 0.1805
    Y = r * 0.2126 + g * 0.7152 + b * 0.0722
    Z = r * 0.0193 + g * 0.1192 + b * 0.9505
    g2 = lambda t: t ** (1 / 3.0) if t > 0.008856 else 7.787 * t + 16 / 116.0
    fx, fy, fz = g2(X / 0.95047), g2(Y / 1.0), g2(Z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def dE(a, b):
    import math
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(_lab(a), _lab(b))))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'corrected by WF-1' in t:
        print('WF-1  already applied - the week band has a fill.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE TOKEN EXISTS, AND IT REALLY DOES CLEAR EVERYTHING.
    # Measured here, at apply time, against base as it stands - not
    # taken from the note above. A number in a comment is a claim; a
    # number the gate computes is a measurement.
    base = read(os.path.join(root, 'pages', 'templates', 'base.html'))
    tok = {}
    for m in re.finditer(r'(--alv-[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\s*;',
                         base):
        tok.setdefault(m.group(1), m.group(2))
    NEW = '--alv-tag-moss-soft'
    ON_GRID = ('--alv-paper', '--alv-surface', '--alv-accent-soft',
               '--alv-warn-soft', '--alv-surface-deep')
    if NEW not in tok:
        refuse('base does not declare %s' % NEW)
    missing = [k for k in ON_GRID if k not in tok]
    if missing:
        refuse('base does not declare %r' % missing)
    worst = min(dE(tok[NEW], tok[k]) for k in ON_GRID)
    if worst < 6.0:
        refuse('%s is only %.1f dE from the nearest fill already on the '
               'grid - WT-1 was right and there is no room' % (NEW, worst))

    code = T.code_only(t)
    if 'var(--alv-accent-soft);' not in code:
        refuse('%s: the pill token is gone from this page' % TPL)

    t = swap(t, CSS_WAS, CSS_NOW, '%s (the band)' % TPL)
    out[pt] = t

    # ---- WT-1's SUITE, CORRECTED IN THE SAME PATCHER
    pb = os.path.join(root, BAND)
    b = read(pb)
    b = swap(b, BAND_PAPER_WAS, BAND_PAPER_NOW, '%s (the fill)' % BAND)
    b = swap(b, BAND_REJECT_WAS, BAND_REJECT_NOW, '%s (the search)' % BAND)
    out[pb] = b

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_print_range.py'
)""", """    'test_print_range.py',
    # WF-1, 21 Oct 2026 - the week band gets the fill he asked for,
    # from the one palette WT-1 never measured.
    'test_week_fill.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'THE RANGE - RG-2';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'corrected by WF-1'; What = 'WF-1: the selected week in Month view fills with tag-moss-soft and keeps its accent rule - a tint that clears every other fill on that grid by 6.9 dE, from the decorative palette WT-1 never looked at' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'THE RANGE - RG-2';""",
             '%s (the sentinels)' % PS1)
    s = swap(s, GATE_WT_WAS, GATE_WT_NOW, '%s (WT-1 own sentinel)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # RG-2, 21 Oct 2026 - the range, and the second press explained.
    'test_print_range.py',
]""", """    # RG-2, 21 Oct 2026 - the range, and the second press explained.
    'test_print_range.py',
    # WF-1, 21 Oct 2026 - the fourth fill, found at the second ask.
    'test_week_fill.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # RG-2, 21 Oct 2026 - From, To, and what the second press is for.
    '.bak_printrange',
]""", """    # RG-2, 21 Oct 2026 - From, To, and what the second press is for.
    '.bak_printrange',
    # WF-1, 21 Oct 2026 - the week band gets its colour.
    '.bak_weekfill',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # WF-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    i = nc.index('.month-cell.in-week')
    row = nc[i:nc.index('}', i)]
    if 'var(--alv-tag-moss-soft)' not in row:
        refuse('%s: the band did not take the new fill' % TPL)
    if 'box-shadow' not in row or 'var(--alv-accent)' not in row:
        refuse('%s: the accent rule went - two signals, not one' % TPL)
    # THE PILL IS UNTOUCHED. Three views share that token and only
    # Month had the collision.
    j = nc.index('.month-chip {')
    chip = nc[j:nc.index('}', j)]
    if 'var(--alv-accent-soft)' not in chip:
        refuse('%s: the pill moved, and only the row was allowed to' % TPL)
    for sel, want in (('.month-cell {', 'var(--alv-paper)'),
                      ('.month-cell.is-out', 'var(--alv-surface)')):
        k = nc.index(sel)
        if want not in nc[k:nc.index('}', k)]:
            refuse('%s: %s no longer fills with %s' % (TPL, sel, want))
    # AND NOT ONE LITERAL COLOUR ARRIVED WITH IT.
    #
    # check_gates flags this pattern against BAND_REJECT_NOW, which
    # quotes #f0f8fa - the pale accent WT-1 rejected. That text goes
    # into test_week_band.py and this gate reads a slice of
    # meal_planner.html, so the two never meet. Recorded rather than
    # silenced: a flagged question answered is worth more than one
    # nobody wrote down.
    if re.search(r'#[0-9a-fA-F]{3,8}\b', row):
        refuse('%s: a literal colour in the band rule' % TPL)

    if CHECK:
        print('WF-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        %s clears every fill on the grid by %.1f dE'
              % (NEW, worst))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('WF-1  applied - the week band fills with moss, and keeps its '
          'edge.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
