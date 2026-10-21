# -*- coding: utf-8 -*-
"""apply_bar_audit.py - round BA-1, 21 Oct 2026.

THE SUITE THAT OWNS BAR ORDER COULD NOT SEE THE BAR IT WAS ASKED
ABOUT, AND NOTHING ASKED WHETHER A MENU ITEM EXISTS OUTSIDE ITS MENU.

Three holes, found on 21 October while fixing four separate faults
that every one of them had let through.

HOLE 1 - A TREE-WIDE CLAIM READ THROUGH A HISTORICAL READER.

test_bar_order section 1 is headed EVERY BAR IN THE APP IS PRIMARY,
SECONDARIES, FILTER, BACK, and it walks alv_tree.templates() - the
LIVE list of 151 templates. But it reads each one through now(),
which is as_left_by(p, SUFFIX): the file as ITS OWN round left it.

So it walks today's file list and reads September's file contents.
PP-1 added a Print button to the planner on 20 October and the suite
ran that bar through a snapshot taken before the button existed: it
reported PSB while the markup said SPSB. Demetri found it by looking
at the screen.

now() IS RIGHT FOR A SCOPE GUARD and its own docstring explains why -
"a scope guard that reads the live file measures every round that
came after". That is a claim about the PAST. Section 1 is a claim
about TODAY. The call site is the only place that knows which, which
is the sentence this project has now paid for six times.

HOLE 2 - A BAR THAT IS A <form> IS INVISIBLE.

    BAR = re.compile(r'<div[^>]*class="[^"]*\\bpage-action-buttons\\b...')

SL-7 wrote the shopping list's date range as
`<form class="sl-range page-action-buttons">`, above the real bar.
The page had two bars and the suite could see one. SH-2 fixed the
page today; this fixes the instrument, so the next one is caught.

HOLE 3 - NOTHING ASKED THE MENU QUESTION IN REVERSE.

base hides every secondary below 768px in a bar with a More menu,
and the standard says "check the menu lists them". test_secondary_
visible asserts the MECHANISM and is correct. Nothing asserted the
CONSEQUENCE. Two faults lived in that gap:

  - Help on the planner, unreachable on a phone for two days (HP-1).
  - Copy this week to..., Save this week as a Menu and Apply a Menu,
    which MW-1 put IN the menu with no bar twin - and the menu is
    display:none above 768px, so for two days they could only be
    reached on a phone. Demetri: "I don't see Copy this week nor
    save this week as a menu???"

The second is the mirror of the first and is the worse of the two,
because the desktop is where he works. CP-2 brings them back; this
round makes both directions checkable:

    every .action-secondary in a bar WITH a menu has a twin IN it
    every .action-more-item has a twin OUTSIDE it

MATCHED BY IDENTITY, NOT BY LABEL. By label the audit said seven
bars were broken; by href, two; by identity - the modal opened, the
function called, the url named, arguments stripped - one, and one
was the truth. An instrument that reports six false positives is an
instrument nobody will act on.

Idempotent. Every file backed up to .bak_baraudit.
"""
import os
import re
import sys

SUFFIX = '.bak_baraudit'
BO = 'test_bar_order.py'
ME = 'test_bar_audit.py'
PATCHER = 'apply_bar_audit.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'BA-1, 21 Oct 2026'
CHECK = False
CREATES = ()

# ---- HOLE 2: the detector sees a form.
BAR_WAS = """BAR = re.compile(r'<div[^>]*class="[^"]*\\bpage-action-buttons\\b[^"]*"[^>]*>')"""

BAR_NOW = """# A BAR IS NOT ALWAYS A <div> - BA-1, 21 Oct 2026.
#
# This read `<div[^>]*...` and SL-7 wrote the shopping list's date
# range as `<form class="sl-range page-action-buttons">`, above the
# real bar. The page carried two bars and this suite could see one of
# them, so neither the duplicate nor its order was ever reported.
# SH-2 fixed that page; the instrument had to stop being able to miss
# the next one.
BAR = re.compile(r'<(?:div|form)[^>]*class="[^"]*\\bpage-action-buttons\\b[^"]*"[^>]*>')"""

# ---- HOLE 1: section 1 reads the live tree.
SEC1_WAS = """nbars = nvar = 0
unread = []
off = []
for p in alv_tree.templates():
    for b in bars(code_only(now(p))):"""

SEC1_NOW = """# THE LIVE FILE, NOT now() - BA-1, 21 Oct 2026.
#
# This loop walks alv_tree.templates(), which is TODAY's list of
# templates, and read each one through now() - which is
# as_left_by(p, SUFFIX), the file as THIS round left it. Today's file
# list, September's file contents.
#
# PP-1 added a Print button to the planner on 20 October and this
# section ran that bar through a snapshot taken before the button
# existed: it reported PSB where the markup said SPSB, and the
# violation shipped. Demetri found it by looking at the screen.
#
# now() is right for a SCOPE GUARD - its own docstring says why, and
# that reasoning is sound - but a scope guard is a claim about what
# this round touched, and section 1 is a claim about what the
# application is. The call site is the only place that knows which
# question is being asked.
nbars = nvar = 0
unread = []
off = []
for p in alv_tree.templates():
    for b in bars(code_only(read(alv_tree.last_path(alv_tree.rel(p))))):"""

SEC1_MSG_WAS = """ok(not off, 'and all %d variants of all %d bars are in house order'
   % (nvar, nbars), '\\n'.join(sorted(set(off))[:8]))"""

SEC1_MSG_NOW = """ok(not off, 'and all %d variants of all %d bars are in house order, '
   'read LIVE' % (nvar, nbars), '\\n'.join(sorted(set(off))[:8]))

# ONE BAR PER PAGE - BA-1, 21 Oct 2026.
#
# base 3.4 says "One `.page-action-buttons` row per page" and nothing
# in the project asserted it. test_one_action_bar does not, despite
# the name: its eleven checks are about a retired CSS variant.
# The shopping list carried two from 19 to 21 October.
#
# A CENSUS, NOT AN EXCEPTION. One page carries two bars and is right
# to: projects/project_tasks_delete puts a Back-only bar at the top
# and the confirm/cancel pair BELOW the warnings, because by then the
# reader has seen what the button will do. Its own comment says so.
#
# Naming it keeps the claim able to FAIL - a second page appearing is
# reported on the day it is written, which "delete pages may have
# two" would never do. A gate with an exception in it is a gate
# somebody will widen.
TWO_BARS = ('projects/project_tasks_delete.html',)
doubled = []
for p in alv_tree.templates():
    if len(BAR.findall(code_only(read(alv_tree.last_path(
            alv_tree.rel(p)))))) > 1:
        doubled.append(alv_tree.rel(p))
ok(sorted(doubled) == sorted(TWO_BARS),
   'and the only page carrying two action bars is the delete '
   'confirmation, which puts its verb below the warnings',
   '\\n'.join(sorted(set(doubled) ^ set(TWO_BARS))[:6]))"""

# ---- AND THE OTHER TWO TREE-WIDE WALKS.
#
# Section 1 was not the only one. The BOTH ROOTS check and section 2
# ("every control in a bar wears exactly one of the four roles") walk
# the live template list through the same historical reader.
#
# THE FOURTH USE IS LEFT ALONE, deliberately. Section 4 compares the
# three MOVED pages before and after, and that IS a claim about what
# this round did - the one question now() is the right answer to.
ROOTS_WAS = """roots = {('crs/' in alv_tree.rel(p)) for p in alv_tree.templates()
         for _b in bars(code_only(now(p)))}"""
ROOTS_NOW = """roots = {('crs/' in alv_tree.rel(p)) for p in alv_tree.templates()
         for _b in bars(code_only(read(alv_tree.last_path(
             alv_tree.rel(p)))))}"""

SEC2_WAS = """for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    for b in bars(code_only(now(p))):"""
SEC2_NOW = """# LIVE, like section 1 - BA-1, 21 Oct 2026. Same reasoning: this is
# a claim about what every bar in the application IS, not about what
# this round changed.
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    for b in bars(code_only(read(alv_tree.last_path(rel)))):"""

# ---- WHAT READING LIVE IMMEDIATELY REVEALED.
#
# Two pins in this suite were wrong, and the historical reader was
# the reason nobody knew. Both are repaired here rather than
# weakened, because a pin that is moved with the thing it pins stays
# a pin.
#
# (a) finance_pl_act's bespoke btn-group IS ALREADY GONE. PN-1
#     converted it to base's own .alv-seg on 3 October - its note
#     says "a segment in a bar takes the bar height" - and the
#     bespoke set has been five, not six, ever since. Read through
#     .bak_barorder it still looked like six. .alv-seg is a HOUSE
#     container like .action-more-wrapper, so it is recognised as
#     one rather than counted as a stray.
#
# (b) ONE PAGE REALLY DOES CARRY TWO BARS, and it is right to.
#     projects/project_tasks_delete puts a Back-only bar at the top
#     and the confirm/cancel pair BELOW the warnings, and says why in
#     its own comment: "the delete lives BELOW the warnings, where
#     the reader has already seen what it will do." That is good
#     design, and base 3.4 did not anticipate it.
#
#     SO THE CLAIM IS A CENSUS, NOT AN EXCEPTION. "These pages carry
#     two, and they are these" breaks the day a third appears. "Two
#     bars are allowed on delete pages" would not - and a gate with
#     an exception in it is a gate somebody will widen.
WRAP_WAS = """                    nwrap += 1
                else:"""
WRAP_NOW = """                    nwrap += 1
                # .alv-seg IS A HOUSE CONTAINER - BA-1, 21 Oct 2026.
                # base owns it, its rules and its pressed state. PN-1
                # converted finance_pl_act's bespoke btn-group to it
                # on 3 October; this suite went on counting that page
                # as bespoke because it was reading a September
                # snapshot of it.
                elif 'alv-seg' in cls.split():
                    nwrap += 1
                else:"""

KNOWN_WAS = """KNOWN = sorted((
    'finance_pl_act.html dropdown pl-year-dropdown',
    'finance_pl_act.html btn-group pl-view-toggle',
    'fsr.html ui-menu',
    'recipe_management.html dropdown-btn-container',
    'recipe_management.html dropdown-btn-container',
    'tenant.html ui-menu',
))"""
KNOWN_NOW = """# FIVE, NOT SIX - BA-1, 21 Oct 2026. finance_pl_act's
# `btn-group pl-view-toggle` left this list on 3 October, when PN-1
# converted it to base's .alv-seg, and nobody knew because section 2
# was reading the page as it stood in September.
KNOWN = sorted((
    'finance_pl_act.html dropdown pl-year-dropdown',
    'fsr.html ui-menu',
    'recipe_management.html dropdown-btn-container',
    'recipe_management.html dropdown-btn-container',
    'tenant.html ui-menu',
))"""

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
    raise SystemExit('BA-1 REFUSED: %s' % msg)


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

    pb = os.path.join(root, BO)
    b = read(pb)

    if 'A BAR IS NOT ALWAYS A <div>' in b:
        print('BA-1  already applied - the instrument can see them all.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE THREE HOLES MUST BE THERE.
    src = T.python_code_only(b, payloads=True)
    if "r'<div[^>]*class=" not in src:
        refuse('%s: its BAR detector is not div-only, so hole 2 is '
               'already closed by something else' % BO)
    if 'for b in bars(code_only(now(p)))' not in src:
        refuse('%s: section 1 does not read through now(), so hole 1 is '
               'already closed' % BO)

    b = swap(b, BAR_WAS, BAR_NOW, '%s (the detector)' % BO)
    b = swap(b, SEC1_WAS, SEC1_NOW, '%s (section 1 reads live)' % BO)
    b = swap(b, SEC1_MSG_WAS, SEC1_MSG_NOW, '%s (one bar per page)' % BO)
    b = swap(b, ROOTS_WAS, ROOTS_NOW, '%s (both roots, live)' % BO)
    b = swap(b, SEC2_WAS, SEC2_NOW, '%s (section 2, live)' % BO)
    b = swap(b, WRAP_WAS, WRAP_NOW, '%s (alv-seg is a house wrapper)' % BO)
    b = swap(b, KNOWN_WAS, KNOWN_NOW, '%s (five bespoke, not six)' % BO)
    out[pb] = b

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_help_phone.py'
)""", """    'test_help_phone.py',
    # BA-1, 21 Oct 2026 - the bar instrument could not see a form
    # bar, read a tree-wide claim through a historical reader, and
    # nobody asked whether a menu item exists outside its menu.
    'test_bar_audit.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'AND HELP - HP-1';""",
             """    @{ File = 'test_bar_order.py'; Text = 'A BAR IS NOT ALWAYS A <div>'; What = 'BA-1: the bar-order instrument reads the LIVE tree for its tree-wide claim, sees a bar written as a form, and asserts one bar per page - three holes that let four separate faults ship between 19 and 21 October' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'AND HELP - HP-1';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # HP-1, 21 Oct 2026 - a control nobody on a phone could reach.
    'test_help_phone.py',
]""", """    # HP-1, 21 Oct 2026 - a control nobody on a phone could reach.
    'test_help_phone.py',
    # BA-1, 21 Oct 2026 - the instrument that could not see the bar.
    'test_bar_audit.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # HP-1, 21 Oct 2026 - Help, reachable on a phone.
    '.bak_helpphone',
]""", """    # HP-1, 21 Oct 2026 - Help, reachable on a phone.
    '.bak_helpphone',
    # BA-1, 21 Oct 2026 - three holes in the bar instrument.
    '.bak_baraudit',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # BA-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nb = T.python_code_only(out[pb], payloads=True)
    if '<(?:div|form)' not in nb:
        refuse('%s: the detector still cannot see a form bar' % BO)
    # EXACTLY ONE now() WALK LEFT, and it is the control's.
    left = nb.count('bars(code_only(now(p)))')
    if left != 1:
        refuse('%s: %d tree-wide walk(s) still read through now(), '
               'expected only section 4 control' % (BO, left))
    if 'CONTROL:' not in nb[nb.index('bars(code_only(now(p)))') - 600:]:
        refuse('%s: the surviving now() walk is not the control' % BO)
    if 'TWO_BARS' not in nb:
        refuse('%s: nothing censuses the pages carrying two bars' % BO)
    # AND now() SURVIVES FOR THE SCOPE GUARDS. Deleting it would be
    # the opposite mistake - those claims really are about the past.
    if 'def now(' not in nb:
        refuse('%s: now() was removed, and the scope guards need it' % BO)
    if nb.count('now(') < 2:
        refuse('%s: only %d use(s) of now() left - the control section '
               'should still be reading it' % (BO, nb.count('now(')))

    if CHECK:
        print('BA-1  --check: %d file(s) would change, none written.'
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
    print('BA-1  applied - the instrument can see every bar now.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
