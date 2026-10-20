# -*- coding: utf-8 -*-
"""apply_chip_left.py - round LO-1, 20 Oct 2026.

LEFTOVERS, FROM MONTH AND WEEK.

Demetri: "How can I add a Note or Leftovers from the month view or the
week view??"

He could not. Both verbs existed and both were trapped on one screen:

    openLeftover(...)   called only from the Day card's row actions
    openNote(...)       called only from the Day card's Add Note

and the chip menu RD-2 built offered exactly three things - View,
Move to... and Remove. This round is the first half of his answer.
NT-1 is the other.

HIS ANSWER WAS "each to the control that already fits", and Leftovers
fits the chip menu exactly: it acts on AN EXISTING MEAL, which is what
that menu is for and what Move to... already does. Nothing new appears
on the calendar.

A NOTE HAS NO LEFTOVERS, and the menu already knows how to say so.
RD-2 hides View when a chip carries no `data-chip-view`, because "Eat
out" has nothing to view; the same attribute answers this question,
because add_leftover refuses a note in as many words:

    "A note has no leftovers - there was nothing cooked."

A MENU ITEM THAT OPENS A DIALOG THAT REFUSES is worse than one that is
not offered, so it is hidden rather than disabled.

NOTHING NEW IS BUILT. openLeftover already takes the entry, the name
and the day it was cooked on, and the chip carries all three.

Idempotent. Every file backed up to .bak_chipleft.
"""
import os
import re
import sys

SUFFIX = '.bak_chipleft'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_chip_left.py'
PATCHER = 'apply_chip_left.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'LO-1, 20 Oct 2026'
CHECK = False
CREATES = ()

MENU_WAS = """    <button type="button" class="chip-menu-item" data-act="move" role="menuitem">
        <i class="fas fa-arrow-right"></i> Move to&hellip;
    </button>"""
MENU_NOW = """    <button type="button" class="chip-menu-item" data-act="move" role="menuitem">
        <i class="fas fa-arrow-right"></i> Move to&hellip;
    </button>
    {# LEFTOVERS - LO-1, 20 Oct 2026. Demetri: "How can I add a Note #}
    {# or Leftovers from the month view or the week view??" He could #}
    {# not: openLeftover was reachable only from the Day card.       #}
    {#                                                               #}
    {# HERE BECAUSE IT ACTS ON A MEAL, which is what this menu is    #}
    {# for - the same reason Move to... is on it.                    #}
    {#                                                               #}
    {# THE SAME ICON THE DAY CARD USES, so one verb keeps one        #}
    {# picture wherever you meet it. MO-1's lesson, and RD-2 paid it #}
    {# again on the 19th.                                            #}
    <button type="button" class="chip-menu-item" data-act="leftovers" role="menuitem">
        <i class="fas fa-redo"></i> Leftovers&hellip;
    </button>"""

HIDE_WAS = """            // A NOTE IS NOT A RECIPE. "Eat out" has nothing to view.
            view.hidden = !url;
            view.setAttribute('data-url', url || '');"""
HIDE_NOW = """            // A NOTE IS NOT A RECIPE. "Eat out" has nothing to view.
            view.hidden = !url;
            view.setAttribute('data-url', url || '');
            // AND IT HAS NOTHING TO HAVE AGAIN - LO-1, 20 Oct 2026.
            // add_leftover refuses a note in as many words, so the
            // same attribute that hides View hides this: a menu item
            // that opens a dialog which then refuses is worse than
            // one that was never offered.
            var again = menu.querySelector('[data-act="leftovers"]');
            if (again) { again.hidden = !url; }"""

ACT_WAS = """        } else if (act === 'remove') {
            removeMeal(chip.getAttribute('data-chip'),
                       chip.getAttribute('data-chip-name'));
        }"""
ACT_NOW = """        } else if (act === 'leftovers') {
            // THE DIALOG MO-1 ALREADY BUILT, with the three things it
            // has always taken. Nothing new is written here: the chip
            // carries the entry, the name and the day it was cooked.
            openLeftover(chip.getAttribute('data-chip'),
                         chip.getAttribute('data-chip-name'),
                         chip.getAttribute('data-chip-date'));
        } else if (act === 'remove') {
            removeMeal(chip.getAttribute('data-chip'),
                       chip.getAttribute('data-chip-name'));
        }"""


# ---- THE SUITE THAT COUNTS THE MENU
#
# test_chip_menu drives a real browser, clicks a chip and reads the
# data-act of every item the menu offers, in order. CH-1 pinned that
# list at three. This round adds a fourth, so the pin has to move with
# it - a round that changes a thing and leaves the count behind turns
# its own success into a red sweep, which is what happened here.
#
# THE ORDER IS THE ARGUMENT, and it still is: look, then change, then
# destroy. Leftovers is a change, and it sits with Move rather than
# after Remove, because nothing should sit after the destructive item.
CM = 'test_chip_menu.py'

CM_WAS = """            ok(items == ['view', 'move', 'remove'],
               'and it offers View, Move to and Remove, in that order - '
               'look, then change, then destroy',
               'offered %r' % (items,))"""

CM_NOW = """            # LO-1, 20 Oct 2026 - FOUR, NOT THREE. Leftovers
            # joined the menu, and it is a CHANGE, so it sits with
            # Move and before Remove: nothing belongs after the
            # destructive item. The order is still the argument CH-1
            # made - look, then change, then destroy.
            ok(items == ['view', 'move', 'leftovers', 'remove'],
               'and it offers View, Move to, Leftovers and Remove, in '
               'that order - look, then change, then destroy',
               'offered %r' % (items,))"""


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
    raise SystemExit('LO-1 REFUSED: %s' % msg)


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

    if "data-act=\"leftovers\"" in t:
        print('LO-1  already applied - leftovers are on the chip menu.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)
    js = T.code_only_js(t)

    # ---- THE GROUND: the menu, and the dialog it will open.
    if 'id="chipMenu"' not in code:
        refuse('%s: there is no chip menu, so RD-2 has not run' % TPL)
    # A DECLARATION IS NOT A USE, and the reverse here: the function
    # must EXIST, so the declaration is exactly what is looked for.
    if not re.search(r'function openLeftover\(', js):
        refuse('%s: openLeftover is not defined, so this menu item '
               'would call nothing' % TPL)
    if 'data-chip-date=' not in code:
        refuse('%s: a chip does not carry its date, which openLeftover '
               'needs as the day it was cooked on' % TPL)

    t = swap(t, MENU_WAS, MENU_NOW, '%s (the menu)' % TPL)
    t = swap(t, HIDE_WAS, HIDE_NOW, '%s (a note has none)' % TPL)
    t = swap(t, ACT_WAS, ACT_NOW, '%s (the action)' % TPL)
    out[pt] = t

    # ---- AND THE SUITE THAT COUNTS THE MENU
    pcm = os.path.join(root, CM)
    out[pcm] = swap(read(pcm), CM_WAS, CM_NOW, '%s (the items)' % CM)

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_fav_token.py'
)""", """    'test_fav_token.py',
    # LO-1, 20 Oct 2026 - leftovers from Month and Week. Section 3
    # opens the menu on a RECIPE chip and on a NOTE chip and asks
    # which items each one offers.
    'test_chip_left.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/recipe_management.html'; Text = 'A TOKEN FOR EVERYONE WHO CAN PRESS SOMETHING';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-act="leftovers"'; What = 'LO-1: leftovers can be added from Month and Week - openLeftover was reachable only from the Day card, so Demetri asked how to do it from the calendar and the answer was that he could not' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'A TOKEN FOR EVERYONE WHO CAN PRESS SOMETHING';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # FV-1, 20 Oct 2026 - the heart could not post for anybody who
    # may not edit recipes, because the token was behind that.
    'test_fav_token.py',
]""", """    # FV-1, 20 Oct 2026 - the heart could not post for anybody who
    # may not edit recipes, because the token was behind that.
    'test_fav_token.py',
    # LO-1, 20 Oct 2026 - leftovers join the chip menu, so the verb
    # is reachable from every view rather than one.
    'test_chip_left.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # FV-1, 20 Oct 2026 - a token for everyone who can press one.
    '.bak_favtoken',
]""", """    # FV-1, 20 Oct 2026 - a token for everyone who can press one.
    '.bak_favtoken',
    # LO-1, 20 Oct 2026 - leftovers from Month and Week.
    '.bak_chipleft',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # LO-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nc = T.code_only(out[pt])
    njs = T.code_only_js(out[pt])

    # COUNTED AS AN ELEMENT, NOT AS A STRING. The first spelling
    # counted two: the button, and the JavaScript SELECTOR that finds
    # the button. A thing and a reference to it are not two things -
    # the fourth time in one day a count has been polluted this way,
    # after a CSS rule, a function declaration and two comments.
    n_item = len(re.findall(r'<button[^>]*data-act="leftovers"', nc))
    if n_item != 1:
        refuse('%s: %d leftovers item(s), expected 1' % (TPL, n_item))

    # IT IS BEHIND THE SAME PERMISSION AS THE REST OF THE MENU. View
    # is offered to everyone; Move and Remove are not, and neither is
    # this.
    seg = nc[nc.index('id="chipMenu"'):]
    seg = seg[:seg.index('</div>')]
    if seg.index('data-act="leftovers"') < seg.index('data-act="move"'):
        refuse('%s: leftovers sits before Move to..., which puts a '
               'guarded item outside the guard' % TPL)

    # AND IT IS HIDDEN FOR A NOTE, which is the one thing that makes
    # this different from just adding a button.
    if "menu.querySelector('[data-act=\"leftovers\"]')" not in njs:
        refuse('%s: nothing hides the item for a note, and '
               'add_leftover refuses one' % TPL)

    if 'openLeftover(chip.getAttribute' not in njs:
        refuse('%s: the item does not call the dialog MO-1 built' % TPL)

    if CHECK:
        print('LO-1  --check: %d file(s) would change, none written.'
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
    print('LO-1  applied - leftovers from Month and Week.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
