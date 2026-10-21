# -*- coding: utf-8 -*-
"""apply_say_today.py - round SC-1, 21 Oct 2026.

TODAY, NOT TONIGHT - AND TWO SHORTCUTS, NOT THREE.

Demetri, testing AP-1 on Live:

    "On the Recipe Management, Add from Recipe Libraries, at the top,
     Tonight should be Today. Then let's remove This Saturday - it
     doesn't really add value."

THE LABEL AND THE VALUE DISAGREED. The button reads "Tonight" and its
data-plan-when is `today`; the date it computes is today's date, and
the toast that confirms it says the weekday. A meal plan has no idea
what time of day it is - there are no meal types, by his decision on
19 October - so "Tonight" was a word the model cannot back.

AND THE THIRD SHORTCUT WAS A GUESS. AP-1 offered Today, Tomorrow and
the coming Saturday. The first two are the two a person reaches for
while standing in the library; the third was me deciding that a week
has a shape, and he has now said it does not add value. The mini
month underneath reaches any date in two clicks, so nothing is lost -
and a row of two buttons is a row you read rather than scan.

WHAT GOES WITH IT. The Saturday branch of when(), which is the only
line of JavaScript on the page that knows what a weekend is, and the
sentence in the comment above it that explained the arithmetic. A
comment that outlives the code it explains is the next person's
wrong turn.

Idempotent. Every file backed up to .bak_saytoday.
"""
import os
import re
import sys

SUFFIX = '.bak_saytoday'
TPL = os.path.join('pages', 'templates', 'recipe_management.html')
ME = 'test_say_today.py'
PATCHER = 'apply_say_today.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'SC-1, 21 Oct 2026'
CHECK = False
CREATES = ()

# ---- THE THREE BUTTONS BECOME TWO, and the first says what it does.
QUICK_WAS = """        <button type="button" class="plan-quick" data-plan-when="today">Tonight</button>
        <button type="button" class="plan-quick" data-plan-when="tomorrow">Tomorrow</button>
        <button type="button" class="plan-quick" data-plan-when="saturday">This Saturday</button>"""

QUICK_NOW = """        {# TODAY, NOT TONIGHT - SC-1, 21 Oct 2026. The value was    #}
        {# already `today` and the date it computes is today's; only #}
        {# the word disagreed. There are no meal types in this       #}
        {# module - his decision, 19 Oct - so the planner does not   #}
        {# know morning from evening and must not imply that it does. #}
        {#                                                            #}
        {# AND TWO, NOT THREE. "This Saturday" was my guess at the    #}
        {# shape of a week; he has said it does not earn its place.   #}
        {# The month below reaches any date in two clicks.            #}
        <button type="button" class="plan-quick" data-plan-when="today">Today</button>
        <button type="button" class="plan-quick" data-plan-when="tomorrow">Tomorrow</button>"""

# ---- AND THE BRANCH THAT COMPUTED IT, with its explanation.
WHEN_WAS = """    // THE SHORTCUTS, AS DATES. "This Saturday" means the Saturday of
    // the week you are in, and on a Saturday it means today - not a
    // week away, which is what counting forward from tomorrow gives.
    function when(code) {
        var d = new Date();
        d.setHours(12, 0, 0, 0);
        if (code === 'tomorrow') { d.setDate(d.getDate() + 1); }
        if (code === 'saturday') { d.setDate(d.getDate() + ((6 - d.getDay()) + 7) % 7); }
        return d;
    }"""

WHEN_NOW = """    // THE SHORTCUTS, AS DATES - SC-1, 21 Oct 2026.
    //
    // There were three, and the third computed the Saturday of the
    // week you are standing in. It is gone with its button, and so is
    // the paragraph that explained the arithmetic: a comment that
    // outlives the code it describes is the next person's wrong turn.
    //
    // Midday, not midnight, because a date built at 00:00 and then
    // formatted in a timezone behind UTC is yesterday.
    function when(code) {
        var d = new Date();
        d.setHours(12, 0, 0, 0);
        if (code === 'tomorrow') { d.setDate(d.getDate() + 1); }
        return d;
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
    raise SystemExit('SC-1 REFUSED: %s' % msg)


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

    if 'data-plan-when="today">Today<' in t:
        print('SC-1  already applied - the shortcut says Today.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE GROUND. Both halves must be there, or AP-1 is not the
    # round this one is amending.
    code = T.code_only(t)
    if 'data-plan-when="saturday"' not in code:
        refuse('%s: there is no Saturday shortcut to remove' % TPL)
    if '>Tonight<' not in code:
        refuse('%s: the first shortcut does not say Tonight' % TPL)

    t = swap(t, QUICK_WAS, QUICK_NOW, '%s (the buttons)' % TPL)
    t = swap(t, WHEN_WAS, WHEN_NOW, '%s (the dates)' % TPL)
    out[pt] = t

    # ---- THE PIN AP-1 LEFT, MOVED IN THE SAME PATCHER
    #
    # test_add_planner counts the shortcuts above the picker's date
    # grid and names all three. There are two now. A round that takes
    # a control away owes the suite that counts it the line, or the
    # next sweep reports today's decision as a regression - which is
    # exactly what it did.
    pa = os.path.join(root, 'test_add_planner.py')
    a = read(pa)
    a = swap(a, """    c['the three shortcuts are there'] = all(
        'data-plan-when="%s"' % w in rm
        for w in ('today', 'tomorrow', 'saturday'))""",
             """    # SC-1, 21 Oct 2026 - TWO. Demetri: "Tonight should be Today.
    # Then let's remove This Saturday - it doesn't really add value."
    # The third button and its when() branch both went.
    c['the two shortcuts are there'] = all(
        'data-plan-when="%s"' % w in rm
        for w in ('today', 'tomorrow'))
    c['  and the third one is gone, with its branch'] = (
        'data-plan-when="saturday"' not in rm)""",
             'test_add_planner.py (the shortcuts)')
    a = swap(a, """        ok(len(seen['quick']) == 3,
           'with the three shortcuts above it', seen['quick'])""",
             """        ok(len(seen['quick']) == 2,
           'with the two shortcuts above it - SC-1, 21 Oct 2026, '
           'took This Saturday away', seen['quick'])""",
             'test_add_planner.py (the driven count)')
    out[pa] = a

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_meal_guide5.py'
)""", """    'test_meal_guide5.py',
    # SC-1, 21 Oct 2026 - the library shortcut says Today, and the
    # third one that nobody wanted is gone.
    'test_say_today.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-slug="mp-print"';""",
             """    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-when="today">Today<'; What = 'SC-1: the add-to-planner shortcut says Today rather than Tonight - the value was always today, and this module has no meal types, so it cannot know morning from evening' },
    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-slug="mp-print"';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # MH-5, 20 Oct 2026 - the guide describes the calendar that is
    # there, rather than the one that was there on 19 October.
    'test_meal_guide5.py',
]""", """    # MH-5, 20 Oct 2026 - the guide describes the calendar that is
    # there, rather than the one that was there on 19 October.
    'test_meal_guide5.py',
    # SC-1, 21 Oct 2026 - a label that disagreed with its own value.
    'test_say_today.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # MH-5, 20 Oct 2026 - the guide catches up with the calendar.
    '.bak_mealguide5',
]""", """    # MH-5, 20 Oct 2026 - the guide catches up with the calendar.
    '.bak_mealguide5',
    # SC-1, 21 Oct 2026 - Today, not Tonight, and two not three.
    '.bak_saytoday',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # SC-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nt = T.code_only(out[pt])
    # THE BRANCH AND THE BUTTON, NOT THE WORD.
    #
    # This gate first read `if 'saturday' in nt.lower()` and refused
    # its own output - because the comment above when(), which exists
    # to say WHY the third shortcut went, names the day it removed.
    # T.code_only strips Django's {# #} but a JavaScript // comment is
    # code as far as it is concerned, so prose inside the script block
    # is visible to every gate that greps.
    #
    # A thing and something that merely NAMES the thing are not two
    # things. Ask for the button, and ask for the branch.
    if re.search(r'data-plan-when="saturday"', nt):
        refuse('%s: the Saturday shortcut button is still there' % TPL)
    if re.search(r"code\s*===\s*'saturday'", nt):
        refuse('%s: when() still has a branch for the third shortcut'
               % TPL)
    if '>Tonight<' in nt:
        refuse('%s: a shortcut still says Tonight' % TPL)
    # TWO BUTTONS, counted as buttons rather than as the word.
    quick = re.findall(r'<button[^>]*class="plan-quick"', nt)
    if len(quick) != 2:
        refuse('%s: %d shortcut button(s), expected 2' % (TPL, len(quick)))
    # AND THE TWO THAT ARE LEFT STILL HAVE A BRANCH TO MATCH. A round
    # that removed the Saturday button and left its branch would pass
    # every check above.
    for code_ in ('today', 'tomorrow'):
        if 'data-plan-when="%s"' % code_ not in nt:
            refuse('%s: the %s shortcut is gone too' % (TPL, code_))
    if "code === 'tomorrow'" not in nt:
        refuse('%s: when() no longer computes tomorrow' % TPL)

    if CHECK:
        print('SC-1  --check: %d file(s) would change, none written.'
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
    print('SC-1  applied - the shortcut says Today, and there are two.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
