# -*- coding: utf-8 -*-
"""apply_bar_first.py - round BO-1, 21 Oct 2026.

THE PRIMARY COMES FIRST, AND ON THIS BAR IT DID NOT.

Demetri, testing PP-1 on Live:

    "The Month and Week View, the Print Button should not be to the
     left of the Shopping List button. This is not as per our
     standards."

HE IS RIGHT, AND THE STANDARD SAYS IT IN base's OWN WORDS:

    "One `.page-action-buttons` row per page. Exactly one
     `.action-primary` - the page's verb."                      (3.4)

and test_bar_order's section 1 heading is the rule itself:

    EVERY BAR IN THE APP IS PRIMARY, SECONDARIES, FILTER, BACK

PP-1 inserted Print ABOVE the Shopping List link, because that is
where the anchor it matched happened to be, and the bar came out

    Print(S)  Shopping List(P)  Help(S)  More  Back        = SPSB

A role recurring after a different one has started is exactly what
HOUSE = ^P*S*F*B*$ forbids. It should read

    Shopping List(P)  Print(S)  Help(S)  More  Back        = PSSB

WHY NOTHING CAUGHT IT IS THE PART WORTH WRITING DOWN, and BA-1 fixes
it rather than this round: test_bar_order reads every page through
now(), which is `as_left_by(p, SUFFIX)` - the file as ITS OWN round
left it. Section 1 walks today's 151 templates and reads their text
as of .bak_barorder, so it ran PP-1's new bar through a snapshot
taken before that bar existed and reported PSB. The claim says EVERY
BAR IN THE APP; the reader says every bar as it was in September.

This round moves the button. BA-1 makes the suite able to see it.

Idempotent. Every file backed up to .bak_barfirst.
"""
import os
import re
import sys

SUFFIX = '.bak_barfirst'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_bar_first.py'
PATCHER = 'apply_bar_first.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'BO-1, 21 Oct 2026'
CHECK = False
CREATES = ()

# THE WHOLE RUN, SWAPPED AS ONE PIECE. Two separate swaps - delete
# Print here, insert it there - would leave a window in which the
# anchor for the second was ambiguous, and PP-1's own comment block
# travels with its button rather than being orphaned above whatever
# ends up first.
PAIR_WAS = """        {# PRINT WHAT YOU ARE LOOKING AT - PP-1, 20 Oct 2026. The    #}
        {# same two dates SL-7 computes, handed to a page built for   #}
        {# paper. There was no way to print a plan at all before this: #}
        {# the only mention of print on this screen was a comment.     #}
        <a href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}"
           class="btn action-secondary">
            <i class="fas fa-print"></i> Print
        </a>
        {# THE RANGE FOLLOWS THE VIEW - SL-7, 20 Oct 2026. This was  #}
        {# ?from=week_start&to=week_end on a screen with three views, #}
        {# so Month bought for a week and Day bought for a week.      #}
        {# The two dates are decided beside view_mode, where a fourth #}
        {# view would be added once rather than here as well.         #}
        <a href="{% url 'meal_shopping_list' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}"
           class="btn action-primary">
            <i class="fas fa-shopping-cart"></i> Shopping List
        </a>"""

PAIR_NOW = """        {# THE PRIMARY FIRST - BO-1, 21 Oct 2026.                    #}
        {#                                                            #}
        {# PP-1 put Print above this link and the bar read SPSB. The  #}
        {# standard is PRIMARY, SECONDARIES, FILTER, BACK, and the    #}
        {# page's verb is Shopping List: it is the thing this screen  #}
        {# exists to produce. Print is a secondary and sits after it. #}
        {#                                                            #}
        {# THE RANGE FOLLOWS THE VIEW - SL-7, 20 Oct 2026. This was  #}
        {# ?from=week_start&to=week_end on a screen with three views, #}
        {# so Month bought for a week and Day bought for a week.      #}
        {# The two dates are decided beside view_mode, where a fourth #}
        {# view would be added once rather than here as well.         #}
        <a href="{% url 'meal_shopping_list' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}"
           class="btn action-primary">
            <i class="fas fa-shopping-cart"></i> Shopping List
        </a>
        {# PRINT WHAT YOU ARE LOOKING AT - PP-1, 20 Oct 2026. The    #}
        {# same two dates SL-7 computes, handed to a page built for   #}
        {# paper. There was no way to print a plan at all before this: #}
        {# the only mention of print on this screen was a comment.     #}
        <a href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}"
           class="btn action-secondary">
            <i class="fas fa-print"></i> Print
        </a>"""


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
    raise SystemExit('BO-1 REFUSED: %s' % msg)


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


ROLES = (('action-primary', 'P'), ('action-secondary', 'S'),
         ('action-filter', 'F'), ('action-back', 'B'))


def roles_in(bar):
    """The bar's roles in MARKUP ORDER, one letter each.

    Deliberately simple and deliberately NOT test_bar_order's parser:
    a gate that borrows the instrument it is trying to outrun proves
    nothing. This reads the order the file is written in, which is
    the thing the finding is about.
    """
    out = []
    for m in re.finditer(r'class="([^"]*)"', bar):
        cls = m.group(1).split()
        for name, k in ROLES:
            if name in cls:
                out.append(k)
                break
    return ''.join(out)


def bar_of(text):
    i = text.index('<div class="page-action-buttons">')
    j = text.index('{# THE VIEW SWITCHER', i)
    return text[i:j]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    sys.path.insert(0, root)
    import alv_tree as T

    was = roles_in(T.code_only(bar_of(t)))
    if was.startswith('P'):
        print('BO-1  already applied - the bar reads %s.' % was)
        return 0

    # ---- THE FINDING MUST BE THERE. A round that reorders a bar
    # already in order is a round that moved something for no reason.
    if was != 'SPSB':
        refuse('%s: the bar reads %r, and this round is about SPSB. '
               'Something else has moved it.' % (TPL, was))

    t = swap(t, PAIR_WAS, PAIR_NOW, '%s (the primary and the print)' % TPL)
    out[pt] = t

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_say_today.py'
)""", """    'test_say_today.py',
    # BO-1, 21 Oct 2026 - the planner bar reads primary first, which
    # is what the standard has said since 7 September.
    'test_bar_first.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-when="today">Today<';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE PRIMARY FIRST - BO-1'; What = 'BO-1: the planner bar reads PRIMARY, SECONDARIES, BACK - Shopping List is the page verb and Print follows it, where PP-1 had put Print above it' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-when="today">Today<';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # SC-1, 21 Oct 2026 - a label that disagreed with its own value.
    'test_say_today.py',
]""", """    # SC-1, 21 Oct 2026 - a label that disagreed with its own value.
    'test_say_today.py',
    # BO-1, 21 Oct 2026 - the planner bar in house order.
    'test_bar_first.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # SC-1, 21 Oct 2026 - Today, not Tonight, and two not three.
    '.bak_saytoday',
]""", """    # SC-1, 21 Oct 2026 - Today, not Tonight, and two not three.
    '.bak_saytoday',
    # BO-1, 21 Oct 2026 - the primary comes first.
    '.bak_barfirst',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # BO-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    now_roles = roles_in(T.code_only(bar_of(out[pt])))
    if now_roles != 'PSSB':
        refuse('%s: the bar reads %r after this round, expected PSSB'
               % (TPL, now_roles))
    if not re.match(r'^P*S*F*B*$', now_roles):
        refuse('%s: %r is not house order' % (TPL, now_roles))
    # NOTHING LEFT THE BAR. A reorder that drops a control would
    # satisfy the pattern above and lose a feature.
    if sorted(now_roles) != sorted(was):
        refuse('%s: the bar held %r and now holds %r - this round moves '
               'a control, it does not add or remove one'
               % (TPL, was, now_roles))
    # AND BOTH LINKS STILL CARRY SL-7's RANGE.
    nt = T.code_only(out[pt])
    for url in ('meal_shopping_list', 'meal_plan_print'):
        seg = nt[nt.index(url):][:260]
        if 'sl_from' not in seg or 'sl_to' not in seg:
            refuse('%s: %s lost the range SL-7 computes' % (TPL, url))

    if CHECK:
        print('BO-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        the bar: %s -> %s' % (was, now_roles))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('BO-1  applied - the bar reads %s, not %s.' % (now_roles, was))
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
