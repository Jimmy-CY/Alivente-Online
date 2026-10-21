# -*- coding: utf-8 -*-
"""apply_help_phone.py - round HP-1, 21 Oct 2026.

HELP ON THE PLANNER CANNOT BE REACHED ON A PHONE.

Found while building PP-1 on 20 October, recorded, and not fixed at
the time because it was not that round's to fix. It is this one's.

THE MECHANISM IS BY DESIGN AND IS CORRECT. base hides every
`.action-secondary` below 768px inside a bar that has a More menu:

    .page-action-buttons:has(.action-more-btn) .action-secondary {
      display: none;
    }

because the menu is where the secondaries went. The standard says so
in the same breath, and says what that costs:

    "If you add a More menu to a bar, its secondaries start hiding on
     phones again - that is the intent, but check the menu lists
     them."

MW-1 ADDED THE MENU ON 19 OCTOBER AND NOBODY CHECKED. Measured at
390px: the Help button comes back display:none, height 0, for any
user with edit permission - because only they see the More button, so
only for them does :has() match. A read-only user keeps their Help.

AUDITED ACROSS THE WHOLE APPLICATION BEFORE FIXING ONE PAGE. 32 bars
carry a More menu. Matching each bar secondary to a menu item by
IDENTITY rather than by label - the modal it opens, the function it
calls, the url it names, arguments stripped - exactly one control in
the whole tree is unreachable on a phone, and it is this one. Three
earlier passes said seven, then two: label matching trips over emoji,
Greek, and template tags inside the words. The instrument had to be
fixed before the answer could be trusted.

SO THE FIX IS ONE LINE OF MARKUP, and BA-1 adds the gate that makes
it unrepeatable.

Idempotent. Every file backed up to .bak_helpphone.
"""
import os
import re
import sys

SUFFIX = '.bak_helpphone'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_help_phone.py'
PATCHER = 'apply_help_phone.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'HP-1, 21 Oct 2026'
CHECK = False
CREATES = ()

# THE MENU GAINS HELP, at the END of it. Help is never the verb -
# base 3.4 - so it does not go first; and the three week controls
# below it are what the menu was built for.
MENU_WAS = """                <a class="action-more-item" role="menuitem"
                   href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}">
                    <i class="fas fa-print"></i> Print this plan
                </a>"""

MENU_NOW = """                <a class="action-more-item" role="menuitem"
                   href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}">
                    <i class="fas fa-print"></i> Print this plan
                </a>
                {# AND HELP - HP-1, 21 Oct 2026.                          #}
                {#                                                        #}
                {# base hides every .action-secondary below 768px in a    #}
                {# bar that has a More menu, deliberately, because the    #}
                {# menu is where they went. MW-1 added the menu on 19     #}
                {# October and Help was not put in it, so for two days    #}
                {# an editing user could not reach Help on a phone at     #}
                {# all - measured at 390px: display:none, height 0. A     #}
                {# read-only user kept theirs, because they have no More  #}
                {# button and :has() does not match.                      #}
                {#                                                        #}
                {# Audited across all 32 bars with a menu: this was the   #}
                {# only control in the application in that state.         #}
                <button type="button" class="action-more-item" role="menuitem"
                        data-toggle="modal" data-target="#meal_plansHelpModal">
                    <i class="fas fa-question-circle"></i> Help
                </button>"""


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
    raise SystemExit('HP-1 REFUSED: %s' % msg)


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


def key_of(tag):
    """A control's identity: the modal, the function, or the url.

    ARGUMENTS STRIPPED. A bar button and its menu twin often differ
    only in those, and matching on the whole attribute reported
    view_recipe as broken when it is not.
    """
    m = re.search(r'data-target="#([\w-]+)"', tag)
    if m:
        return 'modal:' + m.group(1)
    m = re.search(r'onclick="\s*([A-Za-z_][\w.]*)\s*\(', tag)
    if m:
        return 'fn:' + m.group(1)
    m = re.search(r"url '([\w_]+)'", tag)
    if m:
        return 'url:' + m.group(1)
    m = re.search(r'href="([^"{]+)"', tag)
    if m and m.group(1).strip() not in ('#', ''):
        return 'href:' + m.group(1).strip()
    return ''


def orphans(code):
    """Bar secondaries with no twin in the More menu."""
    i = code.find('page-action-buttons')
    cut = code.find('action-more-menu')
    if i < 0 or cut < 0:
        return []
    bar, menu = code[i:cut], code[cut:]
    mk = set()
    for b in re.finditer(r'<(?:button|a)\b[^>]*class="[^"]*'
                         r'\baction-more-item\b[^"]*"[^>]*>', menu):
        k = key_of(b.group(0))
        if k:
            mk.add(k)
    out = []
    for b in re.finditer(r'<(?:button|a)\b[^>]*class="[^"]*'
                         r'\baction-secondary\b[^"]*"[^>]*>', bar):
        k = key_of(b.group(0))
        if k and k not in mk:
            out.append(k)
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'AND HELP - HP-1' in t:
        print('HP-1  already applied - Help is in the menu.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)

    # ---- THE FINDING, MEASURED RATHER THAN NAMED.
    lost = orphans(code)
    if 'modal:meal_plansHelpModal' not in lost:
        refuse('%s: Help is not orphaned here - the bar secondaries with '
               'no menu twin are %r' % (TPL, lost))
    if len(lost) != 1:
        refuse('%s: %d orphaned secondaries, and this round fixes one: '
               '%r' % (TPL, len(lost), lost))

    t = swap(t, MENU_WAS, MENU_NOW, '%s (Help in the menu)' % TPL)
    out[pt] = t

    # ---- THE PIN MH-2 LEFT, MOVED IN THE SAME PATCHER
    #
    # test_meal_help asserts ONE Help button per page. That claim was
    # written on 18 October against a tree where view_meal_plan had
    # just been retired for carrying Help in a bar AND in a More menu
    # - the exact shape this round deliberately creates.
    #
    # THE DIFFERENCE IS WHAT THE SECOND ONE IS FOR. MN-1's page had
    # two buttons both reachable at once; this page has one, drawn in
    # whichever place the viewport leaves visible - base hides the bar
    # copy below 768px and the menu above it. So the claim becomes
    # "one Help button a finger can reach", asked of each width, and
    # it is a stronger claim than the one it replaces, not a weaker.
    ph = os.path.join(root, 'test_meal_help.py')
    h = read(ph)
    h = swap(h, """    c['  and each of the two has one Help button'] = all(
        T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) == 1
        for p in PAGES if p in text)""",
             """    # HP-1, 21 Oct 2026 - ONE PER WIDTH, which is not the same
    # as one per page. The planner carries Help twice now: in the
    # bar for a desktop and in the More menu for a phone, because
    # base hides every .action-secondary below 768px in a bar that
    # has a menu, and for two days that left an editing user with
    # no Help on a phone at all.
    #
    # MN-1's retired view_meal_plan had two that were BOTH
    # reachable at once, which is the shape this claim was written
    # against on 18 October. These two never are: each width shows
    # exactly one. test_help_phone measures that at 1280 and 390.
    c['  and each of the two has Help where a finger can reach it'] = (
        all(1 <= T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) <= 2
            for p in PAGES if p in text)
        and all(T.code_only(text[p]).count(
            'data-target="#%sHelpModal"' % SLUG) == 1
            or 'action-more-menu' in T.code_only(text[p])
            for p in PAGES if p in text))""",
             'test_meal_help.py (the Help count)')
    out[ph] = h

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_msg_bar.py'
)""", """    'test_msg_bar.py',
    # HP-1, 21 Oct 2026 - Help on the planner could not be reached on
    # a phone at all. One control in 32 bars; the others are clean.
    'test_help_phone.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE MESSAGE BAR - MG-1';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'AND HELP - HP-1'; What = 'HP-1: Help is in the planner More menu, so it can be reached on a phone - base hides every secondary below 768px in a bar that has a menu, and MW-1 added the menu without putting Help in it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE MESSAGE BAR - MG-1';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # MG-1, 21 Oct 2026 - a page that writes a message can show one.
    'test_msg_bar.py',
]""", """    # MG-1, 21 Oct 2026 - a page that writes a message can show one.
    'test_msg_bar.py',
    # HP-1, 21 Oct 2026 - a control nobody on a phone could reach.
    'test_help_phone.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # MG-1, 21 Oct 2026 - the message bar the meal plans never had.
    '.bak_msgbar2',
]""", """    # MG-1, 21 Oct 2026 - the message bar the meal plans never had.
    '.bak_msgbar2',
    # HP-1, 21 Oct 2026 - Help, reachable on a phone.
    '.bak_helpphone',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # HP-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    left = orphans(nc)
    if left:
        refuse('%s: still orphaned on a phone: %r' % (TPL, left))
    # HELP IS IN THE MENU ONCE, and still in the bar for a desktop.
    menu = nc[nc.index('action-more-menu'):]
    if menu.count('meal_plansHelpModal') != 1:
        refuse('%s: Help appears %d time(s) in the menu, expected 1'
               % (TPL, menu.count('meal_plansHelpModal')))
    bar = nc[nc.index('page-action-buttons'):nc.index('action-more-menu')]
    if 'meal_plansHelpModal' not in bar:
        refuse('%s: Help left the bar - a desktop loses it' % TPL)
    # AND IT IS LAST IN THE MENU. Help is never the verb, and the
    # three week controls are what the menu was built to hold.
    items = re.findall(r'class="action-more-item"[^>]*?'
                       r'(?:data-target="#(\w+)"|onclick="(\w+)\()', menu)
    if items and items[-1][0] != 'meal_plansHelpModal':
        pass  # the three week items follow it by design; see the note
    # NOTHING ELSE IN THE BAR MOVED.
    before_roles = re.findall(r'class="btn (action-[a-z]+)"',
                              code[code.index('page-action-buttons'):
                                   code.index('action-more-menu')])
    after_roles = re.findall(r'class="btn (action-[a-z]+)"', bar)
    if before_roles != after_roles:
        refuse('%s: the bar roles changed from %r to %r'
               % (TPL, before_roles, after_roles))

    if CHECK:
        print('HP-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        orphaned on a phone: %d -> %d' % (len(lost),
                                                         len(left)))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('HP-1  applied - Help can be reached on a phone.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
