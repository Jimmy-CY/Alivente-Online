# -*- coding: utf-8 -*-
"""apply_back_date.py - round PB-3, 20 Oct 2026.

A WRITE LEAVES YOU ON THE DAY YOU WERE ON.

Demetri, testing push 2 on production:

    "When I added Leftovers to a recipe, it disappeared from the
     current day. When I went back to Week view though it showed again
     on the day, with the Leftovers a couple of days later."

DRIVEN, NOT READ. A real server, a real session, a real browser:

    standing on   ?view=day&date=2026-10-20
    leftovers for 2026-10-22
    came back at  ?view=day&date=2026-10-19   <- Monday of the
                                                 LEFTOVERS' week
    meals listed  0
    showing       Mon 19 Oct

Nothing disappeared. He was moved to a different day, and Week view
showed it again because a week contains both days.

PB-2 SAID THIS WOULD HAPPEN, in its own docstring:

    "`when` is whatever the call site already passed - some of them a
     day, some the Monday of a week... Which date an action should
     return to is a separate question from whether the VIEW survives,
     and this round answers only the second."

It fixed the view and left the date to sixteen call sites that were
already guessing. Two of them guess from the WRITE rather than from
the reader:

    add_leftover     planner_back(request, monday_of(when))
    add_meal_note    planner_back(request, monday_of(when))

where `when` is the date being written to. In Week view that is
invisible, because the Monday of the leftovers' week is usually the
week you are looking at. In Day view it is wrong by up to six days,
which is the report.

THE FIX IS IN ONE PLACE, NOT SIXTEEN. The forms already carry the view
- PB-2 put a hidden `view` on nine of them - so they carry the date
too, and planner_back prefers what the reader sent over what the write
computed. Every call site becomes right at once, and no call site has
to be judged individually.

NAMED from_date, NOT date. The leftovers form already posts `date` and
it means the day the leftovers are FOR. Two different dates under one
name is how this class of bug is made, not fixed.

ONE CALL SITE OPTS OUT, and says why. copy_meal_week lands you on the
week it copied TO - seeing the copy is the point of the action, not a
side effect of it - so it passes stay=False. That is a decision with a
reason beside it rather than an accident of which date was in scope.

RECORDED IN PASSING, NOT FIXED HERE: week_of's docstring says it
returns "the Monday of its week" and its body returns the date
unchanged. The callers compensate with monday_of, so nothing is
broken, but the sentence is false and the next person to trust it will
write this bug again. It wants a round of its own rather than a quiet
edit inside this one.

Idempotent. Every file backed up to .bak_backdate.
"""
import os
import re
import sys

SUFFIX = '.bak_backdate'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
ME = 'test_back_date.py'
PATCHER = 'apply_back_date.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PB-3, 20 Oct 2026'
CHECK = False
CREATES = ()

N_FORMS = 9          # PB-2 put a hidden view on exactly these

# ---- the function, which is the whole fix
FN_WAS = '''def planner_back(request, when=None):
    """The planner, at the view and the date you came from.

    `when` is whatever the call site already passed - some of them a
    day, some the Monday of a week, because they are week-level
    operations. Which date an action should return to is a separate
    question from whether the VIEW survives, and this round answers
    only the second.
    """
    params = {'view': planner_view(request)}
    if when is not None:
        params['date'] = when.strftime('%Y-%m-%d')
    return '%s?%s' % (reverse('meal_planner'), urlencode(params))'''
FN_NOW = '''def planner_back(request, when=None, stay=True):
    """The planner, at the view and the DAY you came from.

    PB-2 answered half of this and said so: it kept the VIEW across a
    write and left the date to whatever each call site had in scope.
    Two of them had the date being WRITTEN rather than the date being
    READ - add_leftover and add_meal_note both passed
    monday_of(when), where `when` is the day the new row lands on.

    In Week view that is invisible: the Monday of the new row's week
    is usually the week already on screen. In Day view it is wrong by
    up to six days, and Demetri reported it as a meal disappearing
    from the day he was standing on. Nothing had disappeared; he had
    been moved.

    SO THE READER SAYS WHERE THEY WERE, and that beats anything the
    write computed. The forms already carry the view; PB-3 gives them
    the date as well, which fixes every call site at once instead of
    asking sixteen of them to each be right.

    NAMED from_date BECAUSE date IS TAKEN. The leftovers form posts
    `date` and it means the day the leftovers are for. Two different
    dates under one name is how this bug is made.

    stay=False is for an action whose POINT is to move you -
    copy_meal_week lands on the week it copied to. One call site, with
    its reason written beside it.
    """
    if stay:
        raw = request.POST.get('from_date') or request.GET.get('from_date')
        seen = week_of(raw, None) if raw else None
        if seen is not None:
            when = seen
    params = {'view': planner_view(request)}
    if when is not None:
        params['date'] = when.strftime('%Y-%m-%d')
    return '%s?%s' % (reverse('meal_planner'), urlencode(params))'''

COPY_WAS = """    back = planner_back(request, dst)"""
COPY_NOW = """    # stay=False - PB-3, 20 Oct 2026. SEEING THE COPY IS THE POINT.
    # Every other write on this screen returns you to the day you were
    # on; this one deliberately does not, because an action whose
    # whole purpose is to fill another week should show you that week.
    back = planner_back(request, dst, stay=False)"""

# ---- the nine forms. Two indentations, and the count of each is
# pinned: a round that reaches eight of nine leaves one form that
# still moves you, which is the bug surviving in a place nobody looks.
# ANCHORED ON THE NEWLINE, so the indentation is part of the match.
# Without it the four-space literal is a SUBSTRING of the sixteen-space
# one and counted 9 where 2 were meant - the prefix trap, which this
# repo has now paid for in six different spellings.
FORM_WAS_DEEP = """
                <input type="hidden" name="view" value="{{ view_mode }}">"""
FORM_NOW_DEEP = """
                <input type="hidden" name="view" value="{{ view_mode }}">
                {# AND THE DAY YOU WERE ON - PB-3, 20 Oct 2026.     #}
                {# from_date, not date: this form may already post  #}
                {# a `date` and mean a different one by it.         #}
                <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">"""
FORM_WAS_FLAT = """
    <input type="hidden" name="view" value="{{ view_mode }}">"""
FORM_NOW_FLAT = """
    <input type="hidden" name="view" value="{{ view_mode }}">
    {# AND THE DAY YOU WERE ON - PB-3, 20 Oct 2026. #}
    <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">"""

N_DEEP, N_FLAT = 7, 2


SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = "document.addEventListener('DOMContentLoaded', bind)"; What = 'RL-1: the picker reload is bound after the document is parsed - base loads jQuery near the end, so PS-1 guard found none and silently bound nothing, and the month grid stayed stale until a hand refresh' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = "document.addEventListener('DOMContentLoaded', bind)"; What = 'RL-1: the picker reload is bound after the document is parsed - base loads jQuery near the end, so PS-1 guard found none and silently bound nothing, and the month grid stayed stale until a hand refresh' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def planner_back(request, when=None, stay=True)'; What = 'PB-3: a write returns you to the DAY you were on, not to a date computed from the write - adding leftovers in Day view moved you to the Monday of the leftovers week, which read as the meal vanishing' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'name="from_date"'; What = 'PB-3: and the reader tells the server where they were, on the same nine forms PB-2 gave the view - one place instead of sixteen call sites each guessing' },"""

SUITE_WAS = """    'test_pick_reload.py'
)"""
SUITE_NOW = """    'test_pick_reload.py',
    # PB-3, 20 Oct 2026 - a write leaves you on the day you were on.
    # Section 3 POSTS from a day and reads the Location header, which
    # is the only place this fault is visible.
    'test_back_date.py'
)"""

TREE_WAS = """    # RL-1, 20 Oct 2026 - a guard that asked "is jQuery here" when it
    # meant "will it be", and bound nothing for a day.
    'test_pick_reload.py',
]"""
TREE_NOW = """    # RL-1, 20 Oct 2026 - a guard that asked "is jQuery here" when it
    # meant "will it be", and bound nothing for a day.
    'test_pick_reload.py',
    # PB-3, 20 Oct 2026 - the half of PB-2 that PB-2 said it was not
    # doing: the DATE a write returns you to.
    'test_back_date.py',
]"""

RD_WAS = """    # RL-1, 20 Oct 2026 - the picker reload actually binds.
    '.bak_pickreload',
]"""
RD_NOW = """    # RL-1, 20 Oct 2026 - the picker reload actually binds.
    '.bak_pickreload',
    # PB-3, 20 Oct 2026 - a write leaves you on the day you were on.
    '.bak_backdate',
]"""


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
    raise SystemExit('PB-3 REFUSED: %s' % msg)


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


def many(text, old, new, n, where):
    """Replace EXACTLY n occurrences, or refuse.

    once() is the house helper and it is the wrong one here: nine
    forms carry the same line and all nine need the field. A loop that
    replaced "all of them" would be silent about finding eight, and
    one form that still moves you is this bug surviving somewhere
    nobody tests.
    """
    got = text.count(fit(text, old))
    if got != n:
        refuse('%s: the anchor appears %d time(s), expected exactly %d '
               '- %r' % (where, got, n, old[:60]))
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    v = read(pv)

    if 'def planner_back(request, when=None, stay=True)' in v:
        print('PB-3  already applied - a write leaves you where you were.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FAULT MUST BE THERE, and it is two call sites, not one.
    code = T.python_code_only(v, payloads=True)
    guessers = len(re.findall(r'planner_back\(request, monday_of\(', code))
    if guessers < 2:
        refuse('%s: %d call site(s) derive the return date from the '
               'write, expected the 2 this round was written for'
               % (VIEW, guessers))
    if 'from_date' in code:
        refuse('%s: something already reads from_date' % VIEW)

    v = swap(v, FN_WAS, FN_NOW, '%s (planner_back)' % VIEW)
    v = swap(v, COPY_WAS, COPY_NOW, '%s (the one that moves you)' % VIEW)
    out[pv] = v

    pt = os.path.join(root, TPL)
    t = read(pt)
    t = many(t, FORM_WAS_DEEP, FORM_NOW_DEEP, N_DEEP,
             '%s (the nested forms)' % TPL)
    t = many(t, FORM_WAS_FLAT, FORM_NOW_FLAT, N_FLAT,
             '%s (the top-level forms)' % TPL)
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
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # PB-3, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)
    nt = T.code_only(out[pt])

    # EVERY FORM THAT CARRIES THE VIEW CARRIES THE DAY. One without it
    # is one action that still moves you.
    n_view = nt.count('name="view"')
    n_date = nt.count('name="from_date"')
    if n_view != N_FORMS or n_date != N_FORMS:
        refuse('%s: %d form(s) send the view and %d send the day - '
               'they must be the same %d forms'
               % (TPL, n_view, n_date, N_FORMS))

    # AND IT IS THE READER'S DATE, not the anchor of whatever the
    # server happened to compute: the value comes from `anchor`, which
    # is what the view was rendered for.
    if nt.count("name=\"from_date\" value=\"{{ anchor|date:'Y-m-d' }}\"") \
            != N_FORMS:
        refuse('%s: a from_date is filled from something other than '
               'the anchor the page was rendered at' % TPL)

    # THE PREFERENCE IS REAL, and it reads BOTH verbs - a GET redirect
    # back from the shopping list carries it in the query string.
    if "request.POST.get('from_date')" not in nv or \
            "request.GET.get('from_date')" not in nv:
        refuse('%s: planner_back does not read from_date from both a '
               'POST and a GET' % VIEW)

    # EXACTLY ONE CALL SITE OPTS OUT, and it is the copy.
    outs = re.findall(r'planner_back\([^)]*stay=False', nv)
    if len(outs) != 1:
        refuse('%s: %d call site(s) opt out of staying put, expected '
               'the 1 that means to move you' % (VIEW, len(outs)))
    i = nv.index('stay=False')
    if 'def copy_meal_week' not in nv[:i].rsplit('def ', 1)[-1] and \
            'copy_meal_week' not in nv[max(0, i - 2000):i]:
        refuse('%s: the opt-out is not in copy_meal_week' % VIEW)

    # THE TWO GUESSERS ARE STILL THERE AND NOW HARMLESS. They are not
    # edited: the call site's date is the right FALLBACK for a request
    # that carries no from_date, such as an old open tab.
    if len(re.findall(r'planner_back\(request, monday_of\(', nv)) != \
            guessers:
        refuse('%s: a call site was rewritten - this round changes the '
               'function, not the sixteen places that call it' % VIEW)

    if CHECK:
        print('PB-3  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        %d form(s) gain the day you were on' % N_FORMS)
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('PB-3  applied - a write leaves you on the day you were on.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
