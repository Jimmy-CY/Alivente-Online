# -*- coding: utf-8 -*-
"""apply_list_range.py - round SL-7, 20 Oct 2026.

THE SHOPPING LIST COVERS WHAT YOU ARE LOOKING AT.

Demetri: "We must also be able to select a day, or a couple of days or
a week for the Shopping List..." - and, asked which of those "a couple
of days" meant, "a from/to range".

THE SERVER HAS BEEN RIGHT SINCE MN-1. meal_shopping_list takes ?from=
and ?to=, swaps a reversed pair, and ceilings the range at 92 days
with a sentence. Nothing about the aggregation, the conversion or the
rounding changes here.

WHAT WAS WRONG WAS ONE LINE OF MARKUP:

    ?from={{ week_start }}&to={{ week_end }}

hard-wired to the week, on a screen that has had three views since
MV-1 shipped the switcher. In Month view it handed you a week of the
month you were looking at; in Day view, a week containing the day.

ONE PLACE DECIDES THE RANGE, AND IT IS THE VIEW. PB-2's lesson,
one screen over: eleven endpoints each built their own address and
eleven places forgot the same thing. So the range is computed beside
view_mode and handed to the template as two dates, rather than spelled
out in a three-branch template conditional that the next view would
have to be added to.

THE MONTH IS THE MONTH, NOT THE GRID. Month view draws whole weeks, so
the first and last rows carry days from the neighbouring months - up
to six of them. The bar says "October 2026" and a list that quietly
bought for 28 September would be a control that lies. The range is the
1st to the last, and the spillover days are not in it.

AND THE LIST PAGE CAN CHANGE ITS MIND. A range you can only choose
before you arrive is a range you have to go back to change, so the two
dates appear on the list itself as a pair of fields that re-ask the
same server with the same two parameters.

Idempotent. Every file backed up to .bak_listrange.
"""
import os
import re
import sys

SUFFIX = '.bak_listrange'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
SL = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')
ME = 'test_list_range.py'
PATCHER = 'apply_list_range.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'SL-7, 20 Oct 2026'
CHECK = False
CREATES = ()

CTX_WAS = """        'view_mode': view_mode,
        'anchor': anchor,"""
CTX_NOW = """        'view_mode': view_mode,
        'anchor': anchor,
        # THE SHOPPING LIST COVERS WHAT YOU ARE LOOKING AT - SL-7,
        # 20 Oct 2026. The button was hard-wired to the week on a
        # screen that has had three views since MV-1, so in Month it
        # bought for a week of the month and in Day for a week round
        # the day.
        #
        # DECIDED HERE, NOT IN THE TEMPLATE. PB-2's lesson one screen
        # over: eleven addresses built in eleven places, and eleven
        # places forgot the same thing. A fourth view would have to be
        # added to a template conditional; it only has to be added
        # here.
        #
        # THE MONTH IS THE MONTH. The grid draws whole weeks, so its
        # first and last rows hold up to six days of the neighbouring
        # months. The bar says October and a list that quietly bought
        # for 28 September would be a control that lies.
        'sl_from': sl_from,
        'sl_to': sl_to,"""

CALC_WAS = """    sel_date = anchor if week_start <= anchor <= week_end else week_start"""
CALC_NOW = """    sel_date = anchor if week_start <= anchor <= week_end else week_start

    # WHAT THE SHOPPING LIST SHOULD BUY FOR - SL-7, 20 Oct 2026.
    # Month: the month itself, 1st to last, NOT the grid - the grid
    # carries up to six days of the neighbouring months because it
    # draws whole weeks.
    # Week: the week on screen. Day: that one day.
    if view_mode == 'month':
        sl_from = date(anchor.year, anchor.month, 1)
        sl_to = (date(anchor.year + (anchor.month == 12),
                      anchor.month % 12 + 1, 1) - timedelta(days=1))
    elif view_mode == 'day':
        sl_from = sl_to = anchor
    else:
        sl_from, sl_to = week_start, week_end"""

BTN_WAS = """        <a href="{% url 'meal_shopping_list' %}?from={{ week_start|date:'Y-m-d' }}&amp;to={{ week_end|date:'Y-m-d' }}\""""
BTN_NOW = """        {# THE RANGE FOLLOWS THE VIEW - SL-7, 20 Oct 2026. This was  #}
        {# ?from=week_start&to=week_end on a screen with three views, #}
        {# so Month bought for a week and Day bought for a week.      #}
        {# The two dates are decided beside view_mode, where a fourth #}
        {# view would be added once rather than here as well.         #}
        <a href="{% url 'meal_shopping_list' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}\""""


RANGE_WAS = """<h4 class="page-subtitle-h4">{{ start|date:"j M" }} &ndash; {{ end|date:"j M Y" }} &mdash; {{ day_count }} day{{ day_count|pluralize }} &mdash; {{ meal_count }} meal{{ meal_count|pluralize }}</h4>"""
RANGE_NOW = """<h4 class="page-subtitle-h4">{{ start|date:"j M" }} &ndash; {{ end|date:"j M Y" }} &mdash; {{ day_count }} day{{ day_count|pluralize }} &mdash; {{ meal_count }} meal{{ meal_count|pluralize }}</h4>

{# AND YOU CAN CHANGE YOUR MIND HERE - SL-7, 20 Oct 2026.          #}
{# The button on the planner covers the view you were on, which    #}
{# answers a day, a week and a month. It cannot answer "Tuesday to #}
{# Thursday", and Demetri asked for "a day, or a couple of days or #}
{# a week". A range you can only choose before you arrive is a     #}
{# range you have to go back to change.                             #}
{#                                                                  #}
{# A GET, AND THE SAME TWO PARAMETERS THE SERVER HAS TAKEN SINCE    #}
{# MN-1. No new endpoint, no new aggregation path - this re-asks    #}
{# the page it is on.                                               #}
{#                                                                  #}
{# IT PRINTS NOTHING. SL-1 hides .page-action-buttons on paper and  #}
{# this belongs with them: a shopping list on the fridge does not   #}
{# need a form on it.                                                #}
<form method="get" action="" class="sl-range page-action-buttons">
    <label class="sl-range-label" for="slFrom">From</label>
    <input type="date" id="slFrom" name="from" class="form-control"
           value="{{ start|date:'Y-m-d' }}">
    <label class="sl-range-label" for="slTo">To</label>
    <input type="date" id="slTo" name="to" class="form-control"
           value="{{ end|date:'Y-m-d' }}">
    <button type="submit" class="btn action-primary">Show these days</button>
</form>"""

SLCSS_WAS = """    .page-action-buttons,
    .step-indicator,"""
SLCSS_NOW = """    .page-action-buttons,
    .sl-range,
    .step-indicator,"""


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
    raise SystemExit('SL-7 REFUSED: %s' % msg)


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

    pv = os.path.join(root, VIEW)
    v = read(pv)

    if 'sl_from' in v:
        print('SL-7  already applied - the list follows the view.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    code = T.python_code_only(v, payloads=True)
    # ---- THE GROUND. Everything this round leans on already exists;
    # asked for by name, because a template that reads a key nothing
    # sets renders an empty string and the link silently loses its
    # range.
    for probe, why in (('def meal_shopping_list', 'the list view'),
                       ("request.GET.get('from')", 'the from parameter'),
                       ("request.GET.get('to')", 'the to parameter'),
                       ('view_mode', 'the switcher'),
                       ('week_start', 'the week on screen')):
        if probe not in code:
            refuse('%s: %s is missing (%s)' % (VIEW, probe, why))
    for name in ('date', 'timedelta'):
        if not re.search(r'(?m)^from datetime import .*\b%s\b' % name,
                         code):
            refuse('%s: %s is not imported, and the month boundaries '
                   'need it' % (VIEW, name))

    v = swap(v, CALC_WAS, CALC_NOW, '%s (the range)' % VIEW)
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the context)' % VIEW)
    out[pv] = v

    pt = os.path.join(root, TPL)
    out[pt] = swap(read(pt), BTN_WAS, BTN_NOW, '%s (the button)' % TPL)

    psl = os.path.join(root, SL)
    sl = read(psl)
    sl = swap(sl, RANGE_WAS, RANGE_NOW, '%s (the pair)' % SL)
    sl = swap(sl, SLCSS_WAS, SLCSS_NOW, '%s (and it does not print)' % SL)
    out[psl] = sl

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_pick_note.py'
)""", """    'test_pick_note.py',
    # SL-7, 20 Oct 2026 - the shopping list covers what you are
    # looking at. Section 3 asks the three views for their link and
    # reads the dates out of it.
    'test_list_range.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerNote"';""",
             """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "'sl_from': sl_from"; What = 'SL-7: the Shopping List button covers the view you are on - it was hard-wired to the week, so Month bought for a week of the month and Day bought for a week round the day' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerNote"';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # NT-1, 20 Oct 2026 - and a note joins the picker, which is the
    # dialog that adds things to a day.
    'test_pick_note.py',
]""", """    # NT-1, 20 Oct 2026 - and a note joins the picker, which is the
    # dialog that adds things to a day.
    'test_pick_note.py',
    # SL-7, 20 Oct 2026 - the shopping list range follows the view,
    # decided in one place rather than spelled in the markup.
    'test_list_range.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # NT-1, 20 Oct 2026 - a note from Month and Week.
    '.bak_picknote',
]""", """    # NT-1, 20 Oct 2026 - a note from Month and Week.
    '.bak_picknote',
    # SL-7, 20 Oct 2026 - the list covers what you are looking at.
    '.bak_listrange',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # SL-7, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)
    nt = T.code_only(out[pt])

    # ALL THREE VIEWS ARE ANSWERED. A branch that forgets one leaves
    # that view buying for somebody else's dates.
    for branch in ("view_mode == 'month'", "view_mode == 'day'"):
        if branch not in nv:
            refuse('%s: %s is not answered, so that view falls through '
                   'to the week' % (VIEW, branch))
    if 'sl_from, sl_to = week_start, week_end' not in nv:
        refuse('%s: the week is not the fallback' % VIEW)

    # THE BUTTON READS THEM, and no longer reads the week directly.
    if 'sl_from' not in nt or 'sl_to' not in nt:
        refuse('%s: the button does not use the computed range' % TPL)
    if "?from={{ week_start" in nt:
        refuse('%s: the hard-wired week link survived' % TPL)

    # AND THE MONTH IS THE MONTH. Asked of the code: the first day is
    # built from day 1, not from the grid.
    if 'date(anchor.year, anchor.month, 1)' not in nv:
        refuse('%s: the month range is not the month itself' % VIEW)

    # THE PAIR ON THE LIST PAGE ASKS THE SAME SERVER THE SAME WAY.
    nsl = T.code_only(out[psl])
    for field in ('name="from"', 'name="to"'):
        if nsl.count(field) != 1:
            refuse('%s: expected exactly one %s' % (SL, field))
    if 'method="get"' not in nsl:
        refuse('%s: the pair posts, where the server reads a query '
               'string' % SL)
    # AND IT IS HIDDEN ON PAPER, with the rest of the chrome.
    pr = nsl.split('@media print', 1)
    if len(pr) < 2 or '.sl-range' not in pr[1][:900]:
        refuse('%s: the pair would print on the shopping list' % SL)

    if CHECK:
        print('SL-7  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('SL-7  applied - the shopping list covers what you are looking at.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
