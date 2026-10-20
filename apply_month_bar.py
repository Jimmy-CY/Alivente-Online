# -*- coding: utf-8 -*-
"""apply_month_bar.py - round MB-2, 19 Oct 2026.

RELEASE 4, PUSH 2. THE DATE BAR IS A BAR.

Demetri, testing the live planner: "I don't like the way it displays
October 2026, the left and right arrow and the Today button."

MEASURED BEFORE ANYTHING WAS PROPOSED, from the real page:

    the Month / Week / Day switcher     32px tall
    the <, > and Today boxes            44px tall
    "October 2026"                      17px text

THE FAULT IS THE OPPOSITE OF WHAT IT LOOKS LIKE. The arrows are not
small - they are the BIGGEST things in the header. Three identical
44px boxes shouting over a 17px label; "Today", which is an ACTION,
dressed as a third direction; and the whole row floating with no
surface of its own between two bordered panels.

Three options were rendered from the real page and Demetri chose B.

AND B IS THE APPLICATION'S OWN ANSWER, which is the part worth
recording. `celebration_calendar.html` - the other month grid in this
project - has always done it this way: the month as a centred heading,
the navigation at the ends, the whole thing on a padded surface. MV-2
built a different bar for the planner without looking at the one that
already existed, exactly as PK-1's picker ignored the filter panel the
library already had.

> The second time in this release that a round invented something the
> application already owned. Both were found by Demetri looking at the
> result rather than by anything in the gate.

THE SURFACE IS FOR THE MONTH HEADER ONLY, and the suite is what
established that. The first cut gave .week-detail-header the same
treatment and the rendered measurement refused it: the Week and Day
header ALREADY sits inside .week-detail-panel - paper, a radius, a
shadow - with its own tinted background and bottom border, declared a
thousand lines further down where it beat this round's rule anyway.

> It did not need a surface. It had a better one. The round that was
> written to stop a bar floating was about to give a bar that was not
> floating a second skin.

WHAT DOES APPLY TO ALL THREE: Today leaving its navigation group, and
the arrows coming down from 44px. Those were wrong everywhere.

Idempotent. Every file backed up to .bak_monthbar.
"""
import os
import re
import sys

SUFFIX = '.bak_monthbar'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_month_bar.py'
PATCHER = 'apply_month_bar.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MB-2, 19 Oct 2026'
CHECK = False
CREATES = ()

N_TODAY = 3


# ===================================================== THE THREE TODAYS
#
# ONE SHAPE, COUNTED. The Month button calls goDay(date, 'month'), the
# Day button goDay(date) and the Week button goWeek(date) - three
# different errands, one piece of furniture. Matching the shape and
# STATING THE COUNT is honest where three near-identical literals
# would be three chances to mistype an indent.
TODAY_RE = re.compile(
    r'(?P<indent>[ \t]*)<button type="button" class="week-nav-btn"\n'
    r'[ \t]*onclick="(?P<call>go(?:Day|Week)\([^"]*\))">\n'
    r'[ \t]*Today\n'
    r'[ \t]*</button>\n'
    r'(?P<close>[ \t]*</div>\n)')


def move_todays(text):
    """Today leaves the navigation group and becomes an action."""
    hits = list(TODAY_RE.finditer(text))
    if len(hits) != N_TODAY:
        refuse('%s holds %d Today button(s) of the expected shape and '
               'this round is written for exactly %d - one per view'
               % (TPL, len(hits), N_TODAY))

    def rebuild(m):
        ind = m.group('indent')
        outer = ind[:-4] if len(ind) >= 4 else ind
        return (
            '%s{# TODAY IS AN ACTION, NOT A DIRECTION - MB-2,     #}\n'
            '%s{# 19 Oct 2026. It sat between the two arrows      #}\n'
            '%s{# wearing the same box, so pressing it looked     #}\n'
            '%s{# like a third way to move.                       #}\n'
            '%s<button type="button" class="week-nav-btn is-today"\n'
            '%s        onclick="%s">\n'
            '%s    Today\n'
            '%s</button>\n'
            % (outer, outer, outer, outer,
               outer, outer, m.group('call'), outer, outer))

    out = []
    last = 0
    for m in hits:
        out.append(text[last:m.start()])
        out.append(m.group('close'))     # close .week-nav FIRST
        out.append(rebuild(m))           # then Today, outside it
        last = m.end()
    out.append(text[last:])
    return ''.join(out)


# ============================================================== THE BAR
CSS_WAS = """.month-header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}"""
CSS_NOW = """/* THE DATE BAR - MB-2, 19 Oct 2026, and it is the shape
   celebration_calendar.html has used since it was written: the period
   as a centred heading, the navigation at the ends, on a surface of
   its own. MV-2 built a different one for this screen without looking
   at the one the application already had.

   MEASURED, which is what Demetri's finding came down to: the
   switcher above this bar is 32px and the three boxes in it were
   44px, so the navigation was louder than the month it navigated. */
.month-header {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 0;
    padding: 12px 14px;
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-bottom: 0;
    border-radius: var(--alv-radius-sm) var(--alv-radius-sm) 0 0;
}
/* JOINED TO WHAT IT HEADS. The bar's bottom edge IS the grid's top
   edge, so the month reads as the grid's heading rather than as a
   label floating above it. */
.month-grid {
    border-top-left-radius: 0;
    border-top-right-radius: 0;
}
.week-nav { flex: 1 1 auto; }
.week-nav-btn.is-today {
    min-width: auto;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 600;
    color: var(--alv-ink);
}
@media screen and (max-width: 767px) {
    /* THE PHONE KEEPS 44px. The bar is quieter at every width, but a
       thumb is the same size on all of them. */
    .month-header { padding: 10px; }
}"""

NAVBTN_WAS = """.week-nav-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        height: 44px;
        padding: 0 10px;
        border: 1px solid var(--alv-line);
        border-radius: var(--alv-radius-sm);
        background: var(--alv-paper);
        color: var(--alv-ink);
        font-size: 15px;
        cursor: pointer;
    }"""
NAVBTN_NOW = """.week-nav-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        /* 36px, NOT 44px - MB-2, 19 Oct 2026. The switcher above this
           bar is 32px and these were 44px, which made the arrows the
           loudest thing on the page. 36px sits between the two and
           still clears a thumb at the phone width below, where the
           media query puts them back to 44. */
        min-width: 36px;
        height: 36px;
        padding: 0 8px;
        border: 1px solid var(--alv-line);
        border-radius: var(--alv-radius-sm);
        background: var(--alv-surface);
        color: var(--alv-ink-soft);
        font-size: 13px;
        cursor: pointer;
    }"""

HOVER_WAS = """.week-nav-btn:hover { background: var(--alv-surface); }"""
HOVER_NOW = """.week-nav-btn:hover {
        background: var(--alv-paper);
        color: var(--alv-ink);
    }"""

PHONE_WAS = """.week-nav-btn { padding: 0 8px; }"""
PHONE_NOW = """.week-nav-btn {
            /* A THUMB IS THE SAME SIZE AT EVERY WIDTH. The bar is
               quieter on the desktop; it is not smaller to press. */
            min-width: 44px;
            height: 44px;
            padding: 0 8px;
        }"""


# ================================== THE TITLE, WHERE IT IS DECLARED
#
# NOT A NEW RULE EARLIER IN THE FILE. The first cut added
# `.week-title { font-size: 20px }` beside .month-header, a thousand
# lines above the rule that already set 17px - so the old value won on
# order and the rendered measurement reported the heading was still
# 17px. The suite caught it; nothing in the source could have.
TITLE_WAS = """.week-title {
        font-size: 17px;
        font-weight: 600;
        color: var(--alv-ink);
        margin: 0 8px;
    }"""
TITLE_NOW = """.week-title {
        /* THE PERIOD IS THE HEADING - MB-2, 19 Oct 2026. It was 17px
           sitting between two 44px boxes, so the navigation read as
           more important than the month it navigated. */
        flex: 1 1 auto;
        text-align: center;
        font-size: 20px;
        font-weight: 600;
        color: var(--alv-ink);
        margin: 0;
    }"""

TITLEPHONE_WAS = """.week-title { font-size: 15px; margin: 0 4px; }"""
TITLEPHONE_NOW = """.week-title { font-size: 16px; margin: 0; }"""


# ===================================================== THE REGISTRATIONS
SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-chip='; What = 'RD-2: a meal in Month or Week is a button with a menu - View, Move to and Remove - because a 152px column has room for a name and nothing else' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-chip='; What = 'RD-2: a meal in Month or Week is a button with a menu - View, Move to and Remove - because a 152px column has room for a name and nothing else' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'week-nav-btn is-today'; What = 'MB-2: Today is an action, not a third direction - it sat between the two arrows wearing the same 44px box' },"""

SUITE_WAS = """    'test_chip_menu.py'
)"""
SUITE_NOW = """    'test_chip_menu.py',
    # MB-2, 19 Oct 2026 - the date bar. Section 3 RENDERS the three
    # views and measures the bar against the switcher above it,
    # because "I do not like how it displays" came down to 44px
    # against 32px.
    'test_month_bar.py'
)"""

TREE_WAS = """    # RD-2, 19 Oct 2026 - the chip menu, and the move behind it.
    # Leftovers travel with their parent and cannot overtake it.
    'test_chip_menu.py',
]"""
TREE_NOW = """    # RD-2, 19 Oct 2026 - the chip menu, and the move behind it.
    # Leftovers travel with their parent and cannot overtake it.
    'test_chip_menu.py',
    # MB-2, 19 Oct 2026 - the date bar, on celebration_calendar's
    # shape. Measured against the switcher it sits under.
    'test_month_bar.py',
]"""

RD_WAS = """    '.bak_chipmenu',
]"""
RD_NOW = """    '.bak_chipmenu',
    # MB-2, 19 Oct 2026 - the date bar is a bar, in all three views.
    '.bak_monthbar',
]"""

WD_WAS = """CONVERTED_N = 122   # RD-2, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 123   # MB-2, 19 Oct 2026 - this round own suite   # (was 122)"""


# ============================================================== HELPERS
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
    raise SystemExit('MB-2 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    # ---------------------------------------------------------------- 0
    if 'week-nav-btn is-today' in t:
        print('MB-2  already applied - the date bar is a bar.')
        return 0

    # ---------------------------------------------------------------- 1
    sys.path.insert(0, root)
    import alv_tree as T
    markup = T.code_only(t)
    if 'class="week-nav"' not in markup:
        refuse('%s has no .week-nav to rebuild - MV-1 goes first' % TPL)

    # ---------------------------------------------------------------- 2
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the bar)' % TPL)
    t = swap(t, NAVBTN_WAS, NAVBTN_NOW, '%s (the arrows)' % TPL)
    t = swap(t, HOVER_WAS, HOVER_NOW, '%s (the hover)' % TPL)
    t = swap(t, PHONE_WAS, PHONE_NOW, '%s (the phone)' % TPL)
    t = swap(t, TITLE_WAS, TITLE_NOW, '%s (the title)' % TPL)
    t = swap(t, TITLEPHONE_WAS, TITLEPHONE_NOW,
             '%s (the title on a phone)' % TPL)
    t = move_todays(t)
    out[pt] = t

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    nt = T.code_only(out[pt])

    # THREE TODAYS, EACH OUTSIDE ITS NAVIGATION GROUP. A Today still
    # inside .week-nav would be flexed along with the arrows and land
    # back in the middle, which is the thing Demetri objected to.
    if nt.count('week-nav-btn is-today') != N_TODAY:
        refuse('%s carries %d Today button(s) marked as an action, '
               'expected %d' % (TPL, nt.count('week-nav-btn is-today'),
                                N_TODAY))
    for block in re.findall(r'<div class="week-nav">(.*?)</div>', nt,
                            re.S):
        if 'is-today' in block:
            refuse('%s: a Today button is still inside .week-nav. It '
                   'would be flexed with the arrows and sit back in '
                   'the middle of them.' % TPL)

    # THE LAST .week-title RULE IN THE FILE IS THIS ROUND'S.
    #
    # CSS is won by whoever is last, and a rule added a thousand lines
    # above the one it means to replace loses silently. The first cut
    # of this round did exactly that and only the rendered measurement
    # noticed.
    titles = re.findall(r'\.week-title\s*\{[^}]*\}', nt, re.S)
    if not titles:
        refuse('%s declares no .week-title at all' % TPL)
    if 'font-size: 20px' not in titles[-1] and \
            'font-size: 16px' not in titles[-1]:
        refuse('%s: the LAST .week-title rule is %r - this round wrote '
               'a new one earlier in the file and the old value still '
               'wins' % (TPL, ' '.join(titles[-1].split())[:90]))

    # AND THE BAR IS JOINED TO WHAT IT HEADS.
    if 'border-bottom: 0;' not in nt:
        refuse('%s: the bar keeps its bottom border, so it is a box '
               'above the grid rather than its heading' % TPL)

    # THE PHONE KEEPS 44px. The bar got quieter; a thumb did not.
    phone = nt.split('@media screen and (max-width: 767px)')
    if not any('min-width: 44px' in chunk for chunk in phone[1:]):
        refuse('%s: the phone rule does not put the arrows back to '
               '44px. The bar is quieter at every width; a thumb is '
               'the same size at all of them.' % TPL)

    # AND screen, NOT a bare max-width - the 21 Sep print-leak round.
    if '@media (max-width' in nt:
        refuse('%s has a bare max-width clause, which matches print '
               'as well' % TPL)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('MB-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)

    print('MB-2  applied - the date bar is a bar, in all three views.')
    print('      Today left the arrows; the period is the heading.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
