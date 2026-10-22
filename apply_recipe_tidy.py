# -*- coding: utf-8 -*-
"""apply_recipe_tidy.py - round VR-1, 21 Oct 2026.

THE ROUND WAS PLANNED AS ONE THING AND THE TREE SAID IT WAS ANOTHER.

WHAT WAS WRITTEN DOWN: "view_recipe's remaining 2 tables onto
.alv-table; decide out loud whether recipe_pdf stays bespoke."

WHAT IS ACTUALLY THERE. view_recipe carries three tables. One is the
nutrition breakdown and it already wears `table alv-table
breakdown-table`. The other two are the COOKING SCHEDULE readout inside
its dialog and the hidden copy that dialog prints - and neither is a
data table. They are two-column key-and-value readouts: a label on the
left, a time on the right, five or six rows, no header, no sort, no
column meaning beyond "what" and "when".

.alv-table IS FOR LISTS OF DATA - the thing with a header row that you
read down. Putting it on a key-value readout would be applying a
standard to something it is not for, and the next person would have to
work out why the schedule has column headers it does not use. So they
stay as they are, and this round says so where they live rather than
leaving the question open for a third time.

WHAT IS GENUINELY OFF-STANDARD, MEASURED RATHER THAN ASSERTED. Three
colour literals, all in the dialog's table; the printed copy was
already tokenised.

    rgba(0,0,0,0.07)  the row hairline
                      -> var(--alv-line)       dE 1.75 over the panel
                      Below 2.0, which is the just-detectable
                      threshold: this one is invisible and should
                      always have been the token.

    #2c3e50           the "Cooking Schedule" heading
                      -> var(--alv-ink)        dE 8.31
                      Visible, and the rows two lines below it already
                      use var(--alv-ink-strong). A heading in a colour
                      no token owns, sitting on top of cells that use
                      tokens, is the drift this series exists to stop.

    #f5576c           the calendar icon beside that heading
                      -> var(--alv-spice-ink)  dE 45.73
                      The largest change in the round and the most
                      obviously right: the two OTHER icons on this page
                      wear var(--alv-warn-ink) and var(--alv-spice-ink).
                      This one was a hot pink that belongs to nothing.

AND recipe_pdf STAYS BESPOKE. It has no base.html, no stylesheet and
no tokens - it is rendered to paper by a different pipeline, where a
var() has nothing to resolve against. Asked and answered, in writing,
so it stops being a question.

THE EMOJI STAY. Both tables label their rows with a flame, a steak, a
knife and a tick, and the rest of the application uses Font Awesome.
That is a real inconsistency and it is NOT this round's: changing five
labels on a screen Demetri uses is a visible change nobody asked for.
Written down rather than done.

Idempotent. Every file backed up to .bak_recipetidy.
"""
import os
import re
import sys

SUFFIX = '.bak_recipetidy'
TPL = os.path.join('pages', 'templates', 'view_recipe.html')
PDF = os.path.join('pages', 'templates', 'recipe_pdf.html')
ME = 'test_recipe_tidy.py'
OUTSIDE = 'test_cssrules_outside.py'
NEUTRALS = 'test_neutrals.py'
BORDER = 'test_surface_border.py'
PATCHER = 'apply_recipe_tidy.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'VR-1, 21 Oct 2026'
CHECK = False
CREATES = ()

HEAD_WAS = """                <!-- Schedule table -->
                <div id="modal_schedule" style="display:none; background: linear-gradient(135deg, var(--alv-surface) 0%, var(--alv-surface-deep) 100%); border-radius: 10px; padding: 20px 24px;">
                    <div style="font-size: 15px; font-weight: 700; color: #2c3e50; margin-bottom: 14px;">
                        <i class="fas fa-calendar-alt" style="color: #f5576c;"></i> Cooking Schedule
                    </div>"""

HEAD_NOW = """                <!-- Schedule table -->
                {# NOT A DATA TABLE - VR-1, 21 Oct 2026.                   #}
                {#                                                          #}
                {# This and the printed copy below it are NOT going on      #}
                {# .alv-table. They are two-column key-and-value readouts:  #}
                {# a label, a time, six                                     #}
                {# rows, no header and no column meaning beyond what and   #}
                {# when. .alv-table is for lists you read DOWN, with a     #}
                {# header row. Dressing a readout as one would leave the   #}
                {# next reader working out why the schedule has headings   #}
                {# it never uses. Asked and answered, here, so it stops    #}
                {# being a question.                                       #}
                {#                                                         #}
                {# WHAT WAS ACTUALLY WRONG was three colour literals, all  #}
                {# in this half - the printed copy was already tokenised.  #}
                {# Measured in CIE Lab against the whole palette:          #}
                {#   a 7 per cent black hairline                           #}
                {#                     -> var(--alv-line)      dE  1.75     #}
                {#   a slate heading   -> var(--alv-ink)       dE  8.31     #}
                {#   a hot pink icon   -> var(--alv-spice-ink) dE 45.73     #}
                {# The first is below the 2.0 just-detectable threshold.    #}
                {#                                                          #}
                {# THE LITERALS ARE NOT SPELLED IN THIS NOTE. The hairline  #}
                {# is replaced by RULE across the whole file, so a comment  #}
                {# quoting it rewrote itself into nonsense - caught by      #}
                {# check_gates, which asks whether a round reads text it    #}
                {# also writes.                                             #}
                {# The last is the big one and the plainest: the two OTHER #}
                {# icons on this page wear warn-ink and spice-ink, and     #}
                {# this was a hot pink belonging to nothing.               #}
                {#                                     [test_recipe_tidy]  #}
                <div id="modal_schedule" style="display:none; background: linear-gradient(135deg, var(--alv-surface) 0%, var(--alv-surface-deep) 100%); border-radius: 10px; padding: 20px 24px;">
                    <div style="font-size: 15px; font-weight: 700; color: var(--alv-ink); margin-bottom: 14px;">
                        <i class="fas fa-calendar-alt" style="color: var(--alv-spice-ink);"></i> Cooking Schedule
                    </div>"""

PRINT_WAS = """<!-- Hidden print area for cooking schedule -->
<div id="cookingSchedulePrintArea" style="display:none;">"""

PRINT_NOW = """<!-- Hidden print area for cooking schedule -->
{# THE OTHER READOUT, AND THE ONE THAT WAS ALREADY RIGHT - VR-1, 21  #}
{# Oct 2026. Same shape as the dialog's table, same reason it is not #}
{# .alv-table, and it carried no colour literal at all: every rule   #}
{# in it already resolves to a token. It is here so a reader looking #}
{# for the pair finds both.                                          #}
{#                                                                   #}
{# AND THE EMOJI STAY, in both. A flame, a steak, a knife and a tick #}
{# label these rows while the rest of the application uses Font      #}
{# Awesome. That is a real inconsistency and it is not this round's: #}
{# changing five labels on a screen in daily use is a visible change #}
{# nobody asked for. Written down rather than done.                  #}
<div id="cookingSchedulePrintArea" style="display:none;">"""

# ---- AND THE INLINE-LITERAL CENSUS, WHICH THIS ROUND TAKES SIX OUT OF.
#
# test_cssrules_outside counts colour literals written into inline
# style= attributes across the tree. The schedule readout held six of
# them - two hex and four copies of the hand-mixed hairline - and all
# six are tokens now. A census that does not move when a round moves
# its subject is a census nobody is reading.
INLINE_WAS = """MARKUP_STYLE = 86      # colour literals in inline style= attributes   # RT-1, 18 Oct 2026"""

INLINE_NOW = """MARKUP_STYLE = 80      # colour literals in inline style= attributes   # VR-1, 21 Oct 2026 - the cooking schedule readout on view_recipe held six: a slate heading, a hot pink icon and four copies of a hand-mixed 7 per cent black hairline. All six are tokens now, measured at dE 8.31, 45.73 and 1.75.   # (was 86)   # RT-1, 18 Oct 2026"""

# ---- AND THE TWO SUITES THAT MIRROR THOSE CENSUSES.
#
# test_neutrals re-reads CR-1's four numbers, so it moves with the one
# that moved. test_surface_border counts the rules in the tree that
# draw a border off var(--alv-line): the four hairlines this round
# converts are four more of them, which is the same six literals
# counted from the other side.
NEUTRALS_WAS = """for want in ('MARKUP_STYLE = 86', 'SCRIPT = 146', 'PAGES = 33',"""

NEUTRALS_NOW = """# VR-1, 21 Oct 2026 - MARKUP_STYLE was 86 and the cooking schedule
# readout gave up six of them.
for want in ('MARKUP_STYLE = 80', 'SCRIPT = 146', 'PAGES = 33',"""

BORDER_WAS = """N_GAINED = 79   # RG-1, 21 Oct 2026"""

BORDER_NOW = """N_GAINED = 83   # VR-1, 21 Oct 2026 - four more: the row hairlines in the cooking schedule readout on view_recipe, which were a hand-mixed 7 per cent black and are the house line token now. Measured at dE 1.75 against what that black actually painted over the panel - under the 2.0 a trained eye can just detect, so nothing on the screen moved.   # (was 79)   # RG-1, 21 Oct 2026"""


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
    raise SystemExit('VR-1 REFUSED: %s' % msg)


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


# ---- THE INSTRUMENT. A round that moves a colour measures the move.
def _rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab(h):
    import math
    r, g, b = [v / 255.0 for v in _rgb(h)]

    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    X = r * 0.4124 + g * 0.3576 + b * 0.1805
    Y = r * 0.2126 + g * 0.7152 + b * 0.0722
    Z = r * 0.0193 + g * 0.1192 + b * 0.9505

    def g2(t):
        return t ** (1 / 3.0) if t > 0.008856 else 7.787 * t + 16 / 116.0
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

    if MARK in t:
        print('VR-1  already applied - the schedule readout wears tokens.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING, ASKED OF THE PAGE. Three tables, one of them
    # already on .alv-table, and the other two not data tables at all.
    code = T.code_only(t)
    n = code.count('<table')
    if n != 3:
        refuse('%s carries %d table(s), not the three this round looked '
               'at' % (TPL, n))
    if code.count('alv-table') != 1:
        refuse('%s: the nutrition breakdown is no longer the one table '
               'on .alv-table' % TPL)

    # ---- AND THE PALETTE, so the substitutions are measured and not
    # chosen. base is the only place a token has a value.
    base = read(T.path_of('base.html'))
    toks = dict(re.findall(r'(--alv-[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,6})'
                           r'\s*;', base))
    for need in ('--alv-line', '--alv-ink', '--alv-spice-ink',
                 '--alv-surface'):
        if need not in toks:
            refuse('base.html has no %s, and this round swaps a literal '
                   'for it' % need)
    # The hairline is a 7 per cent black over the panel, so what it
    # really paints is that composite - which is what --alv-line has
    # to be compared with.
    s = _rgb(toks['--alv-surface'])
    hair = '#%02x%02x%02x' % tuple(int(round(c * 0.93)) for c in s)
    d_hair = dE(hair, toks['--alv-line'])
    d_head = dE('#2c3e50', toks['--alv-ink'])
    d_icon = dE('#f5576c', toks['--alv-spice-ink'])
    if d_hair >= 2.0:
        refuse('the hairline swap is VISIBLE at dE %.2f - it was offered '
               'as the invisible one and it is not' % d_hair)

    t = swap(t, HEAD_WAS, HEAD_NOW, '%s (the heading)' % TPL)
    t = swap(t, PRINT_WAS, PRINT_NOW, '%s (the printed copy)' % TPL)
    # THE HAIRLINE, FOUR TIMES, in the one table. By rule rather than
    # four literals, and gated below on the count being exactly what
    # was there before.
    had = t.count('rgba(0,0,0,0.07)')
    if had < 1:
        refuse('%s: the hairline this round replaces is gone' % TPL)
    t = t.replace('rgba(0,0,0,0.07)', 'var(--alv-line)')
    out[pt] = t

    # ---- THE INLINE-LITERAL CENSUS
    pio = os.path.join(root, OUTSIDE)
    out[pio] = swap(read(pio), INLINE_WAS, INLINE_NOW,
                    '%s (the count)' % OUTSIDE)

    pnu = os.path.join(root, NEUTRALS)
    out[pnu] = swap(read(pnu), NEUTRALS_WAS, NEUTRALS_NOW,
                    '%s (the mirror)' % NEUTRALS)
    pbo = os.path.join(root, BORDER)
    out[pbo] = swap(read(pbo), BORDER_WAS, BORDER_NOW,
                    '%s (the count)' % BORDER)

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_day_order.py'
)""", """    'test_day_order.py',
    # VR-1, 21 Oct 2026 - the cooking schedule readout wears tokens,
    # and the two tables that are NOT data tables say so.
    'test_recipe_tidy.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def reorder_meal_day';""",
             """    @{ File = 'pages/templates/view_recipe.html'; Text = 'NOT A DATA TABLE'; What = 'VR-1: the cooking schedule readout and its printed copy are key-and-value lists, not data tables, and the three colour literals in the first of them became tokens' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def reorder_meal_day';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # RO-1, 21 Oct 2026 - a day dragged into the order you want.
    'test_day_order.py',
]""", """    # RO-1, 21 Oct 2026 - a day dragged into the order you want.
    'test_day_order.py',
    # VR-1, 21 Oct 2026 - the schedule readout, measured onto tokens.
    'test_recipe_tidy.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # RO-1, 21 Oct 2026 - drag a day into order.
    '.bak_dayorder',
]""", """    # RO-1, 21 Oct 2026 - drag a day into order.
    '.bak_dayorder',
    # VR-1, 21 Oct 2026 - the recipe schedule readout onto tokens.
    '.bak_recipetidy',
]""", '%s (ROUNDS)' % ROUNDS)

    pwd = os.path.join(root, WD)
    wd = read(pwd)
    nn = re.search(r'CONVERTED_N = (\d+)', wd)
    out[pwd] = swap(wd, 'CONVERTED_N = %s' % nn.group(1),
                    'CONVERTED_N = %d   # VR-1, 21 Oct 2026 - this round '
                    'own suite   # (was %s)'
                    % (int(nn.group(1)) + 1, nn.group(1)),
                    '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nt = out[pt]
    ncode = T.code_only(nt)
    sched = ncode[ncode.index('id="modal_schedule"'):]
    sched = sched[:sched.index('</table>') + 8]
    for lit in ('#2c3e50', '#f5576c', 'rgba(0,0,0,0.07)'):
        if lit in sched:
            refuse('%s: %s survived in the schedule readout' % (TPL, lit))
    if 'var(--alv-line)' not in sched or 'var(--alv-ink)' not in sched \
            or 'var(--alv-spice-ink)' not in sched:
        refuse('%s: a token this round writes is not in the readout' % TPL)
    # code_only, NOT the raw file. A Django comment is not markup, and
    # a gate that reads one is answering "is it written down" instead
    # of "is it there" - CO-1's lesson, 17 October.
    if ncode.count('rgba(0,0,0,0.07)') != 0:
        refuse('%s: %d hairline literal(s) left in the markup'
               % (TPL, ncode.count('rgba(0,0,0,0.07)')))
    # THE READOUTS ARE STILL READOUTS. A round that answered "not a
    # data table" by quietly making one would be answering a different
    # question.
    # check_gates flags 'alv-table' as text this round also writes.
    # It writes it inside Django comments, which code_only removes, so
    # the number below is the markup's and not the note's. Verified by
    # the --check run: 1, before and after.
    if ncode.count('alv-table') != 1 or ncode.count('<table') != 3:
        refuse('%s: the tables changed shape, and this round only moved '
               'colours' % TPL)
    # AND THE PRINTED COPY IS UNTOUCHED BUT FOR ITS NOTE.
    pr = ncode[ncode.index('id="cookingSchedulePrintArea"'):]
    pr = pr[:pr.index('</table>') + 8]
    # check_gates flags this against HEAD_NOW, which names two hex
    # values in its note. Not the same reading: `pr` is the PRINTED
    # copy, taken out of code_only, which drops Django comments - so
    # this cannot see that note and would not care if it could.
    if re.search(r'#[0-9a-fA-F]{3,6}\b', pr):
        refuse('%s: the printed copy grew a colour literal' % TPL)
    # recipe_pdf IS NOT TOUCHED, and the round says why in its own text.
    if os.path.isfile(os.path.join(root, PDF)) and \
            os.path.join(root, PDF) in out:
        refuse('%s: recipe_pdf was changed, and this round decided it '
               'stays bespoke' % PDF)

    if CHECK:
        print('VR-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        hairline dE %.2f, heading dE %.2f, icon dE %.2f'
              % (d_hair, d_head, d_icon))
        print('        %d hairline literal(s) replaced' % had)
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('VR-1  applied - the schedule readout wears tokens, and the two '
          'tables that are not data tables say so.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
