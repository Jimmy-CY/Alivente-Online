# -*- coding: utf-8 -*-
"""apply_week_click.py - round WC-1, 19 Oct 2026.

RELEASE 4, PUSH 2. A DAY IS A DAY IN EVERY VIEW.

Demetri, testing the live planner: "In the week view, I can click to
view a recipe or remove it and I am forced to click on the '+' button
to add a recipe. Why does this change from the month view?"

HE IS RIGHT AND THERE IS NO REASON FOR IT.

    Month   click anywhere in the day            -> the picker
    Week    only the small + at the foot         -> the picker

His Q2 answer was "I want it to go straight to the Picker, when I
click a day". MV-2 built that for the month cell. MV-3 built the week
column an hour later, in a separate round, and gave it a button
instead - and nothing in the gate asks whether the same action behaves
the same way in two views, because no suite judges two rounds at once.

THE + STAYS. Offered for removal and Demetri expressed no preference,
so the safer answer stands: on a touch screen there is no hover, so
the + is the only thing that SAYS a day can be added to. The month
cell has no such affordance, which is arguably the month's weakness
rather than the week's.

AND THE CHIPS ARE ALREADY SAFE. RD-2 put a capture-phase listener in
front of the chips, so a click on a meal never reaches the thing
around it. This round would have needed that listener; it happens to
be two rounds earlier in the same push.

Idempotent. Every file backed up to .bak_weekclick.
"""
import os
import re
import sys

SUFFIX = '.bak_weekclick'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_week_click.py'
PATCHER = 'apply_week_click.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'WC-1, 19 Oct 2026'
CHECK = False
CREATES = ()


BODY_WAS = """                        <div class="week-col-body">"""
BODY_NOW = """                        {# A DAY IS A DAY IN EVERY VIEW - WC-1,      #}
                        {# 19 Oct 2026. Demetri: "why does this        #}
                        {# change from the month view?" It did not     #}
                        {# need to. The month cell has carried this    #}
                        {# since MV-2; the week column got a button    #}
                        {# instead because it was a different round.   #}
                        {#                                             #}
                        {# THE CHIPS INSIDE ARE SAFE. RD-2's listener  #}
                        {# captures, so a click on a meal never        #}
                        {# reaches this.                               #}
                        <div class="week-col-body"
                             {% if perms.auth.can_edit_recipes %}role="button" tabindex="0"
                             aria-label="{{ day.entries|length }} meal{{ day.entries|length|pluralize }} on {{ day.date|date:'l j F' }} - add one"
                             onclick="openPicker('{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }} {{ day.day_num }}')"{% endif %}>"""

CSS_WAS = """.week-col-body {"""
CSS_NOW = """/* THE BODY IS A TARGET - WC-1, 19 Oct 2026, and it is the month
   cell's own rule, because the two are the same gesture. */
.week-col-body[role="button"] { cursor: pointer; }
.week-col-body[role="button"]:hover { background: var(--alv-accent-soft); }
.week-col-body[role="button"]:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: -2px;
}
.week-col-body {"""


SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'week-nav-btn is-today'; What = 'MB-2: Today is an action, not a third direction - it sat between the two arrows wearing the same 44px box' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'week-nav-btn is-today'; What = 'MB-2: Today is an action, not a third direction - it sat between the two arrows wearing the same 44px box' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-col-body"'; What = 'WC-1: clicking a day opens the picker in WEEK view too - it only did so in Month, because the two views were built in different rounds' },"""

SUITE_WAS = """    'test_month_bar.py'
)"""
SUITE_NOW = """    'test_month_bar.py',
    # WC-1, 19 Oct 2026 - a day is a day in every view. Section 3
    # clicks a day in BOTH views and asks whether the picker opened,
    # which is the comparison no suite was making.
    'test_week_click.py'
)"""

TREE_WAS = """    # MB-2, 19 Oct 2026 - the date bar, on celebration_calendar's
    # shape. Measured against the switcher it sits under.
    'test_month_bar.py',
]"""
TREE_NOW = """    # MB-2, 19 Oct 2026 - the date bar, on celebration_calendar's
    # shape. Measured against the switcher it sits under.
    'test_month_bar.py',
    # WC-1, 19 Oct 2026 - the same gesture in Month and Week.
    'test_week_click.py',
]"""

RD_WAS = """    '.bak_monthbar',
]"""
RD_NOW = """    '.bak_monthbar',
    # WC-1, 19 Oct 2026 - clicking a day opens the picker in Week too.
    '.bak_weekclick',
]"""

WD_WAS = """CONVERTED_N = 123   # MB-2, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 124   # WC-1, 19 Oct 2026 - this round own suite   # (was 123)"""


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
    raise SystemExit('WC-1 REFUSED: %s' % msg)


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

    if 'class="week-col-body"\n' in t.replace('\r\n', '\n') and \
            'A DAY IS A DAY IN EVERY VIEW' in t:
        print('WC-1  already applied - a day is a day in every view.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    markup = T.code_only(t)

    # THE FAULT MUST BE THERE: the month cell has the click and the
    # week column does not.
    if 'class="month-cell' not in markup or \
            'role="button"' not in markup:
        refuse('%s: the month cell is not a click target, so there is '
               'nothing for the week column to match - MV-2 goes first'
               % TPL)
    if re.search(r'<div class="week-col-body"\s+\{%', markup):
        refuse('%s: the week column body is already a target' % TPL)
    if 'data-chip=' not in markup:
        refuse('%s: the chips are not yet captured by RD-2, so making '
               'the column clickable would make every meal open the '
               'picker' % TPL)

    t = swap(t, BODY_WAS, BODY_NOW, '%s (the column body)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the rules)' % TPL)
    out[pt] = t

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

    # ---- THE GATES
    nt = T.code_only(out[pt])

    # THE SAME GESTURE, AND THE SAME ERRAND. Both views must call the
    # same function with a date, or they are two behaviours that merely
    # look alike.
    month_call = re.search(
        r'class="month-cell[^>]*?onclick="(openPicker\([^"]*\))', nt,
        re.S)
    week_call = re.search(
        r'class="week-col-body"[^>]*?onclick="(openPicker\([^"]*\))', nt,
        re.S)
    if not month_call or not week_call:
        refuse('%s: one of the two views does not open the picker from '
               'the day itself (month=%s, week=%s)'
               % (TPL, bool(month_call), bool(week_call)))

    # AND THE PERMISSION IS ASKED IN BOTH. A read-only user given a
    # click target that refuses is worse than no target.
    body = nt.split('class="week-col-body"', 1)[1][:400]
    if 'perms.auth.can_edit_recipes' not in body:
        refuse('%s: the week column is a target for somebody who may '
               'not add a meal' % TPL)

    # THE + SURVIVES. It is the only affordance on a touch screen.
    if 'week-col-add' not in nt:
        refuse('%s: the + went. It was kept on purpose - without hover '
               'there is nothing else that says a day is addable.' % TPL)

    if CHECK:
        print('WC-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    print('WC-1  applied - clicking a day opens the picker in Week too.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
