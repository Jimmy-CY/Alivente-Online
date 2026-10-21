# -*- coding: utf-8 -*-
"""apply_msg_bar.py - round MG-1, 21 Oct 2026.

THREE PAGES WROTE MESSAGES AND NONE OF THEM COULD SHOW ONE.

Demetri, testing push 3 on Live:

    "The success messages for the Add recipe to Meal Plan, Delete
     recipe from meal plan, all land on future screen (e.g Recipe
     Management, or Logout screen, if the system auto-logs me out)."

MEASURED, AND HE IS EXACTLY RIGHT. Django's messages framework stores
a message in the session and hands it to the next template that
RENDERS one. 78 of the 151 live templates carry the loop. The
planner, the shopping list and the printable plan carry none.

So every messages.success() in meal_planning.py - and there are
twelve, across add, remove, move, copy, save-a-menu, apply-a-menu,
note and leftover - went into the session and waited. It surfaced on
whatever page he reached next that HAD a bar. Recipe Management has
one. So does the logout screen.

THE LIBRARY ROUTE IS NOT AFFECTED and is left alone: AP-1's add
returns JsonResponse BEFORE the messages.success() line, so the toast
is the only thing that fires. That was already right.

WHAT THIS ROUND DOES NOT DO. It does not move the loop into base.
That is the real fix - 78 copies of one block, in two spellings
(`msg` on 73 pages, `message` on 5) - and it is a round of its own
that has to delete 78 copies in the same breath as it adds one, or
every page renders its messages twice. Recorded, not attempted here.

THE SHAPE IS THE HOUSE SHAPE, not a new one: the 73-page spelling,
byte for byte, so these three join the majority rather than founding
a third dialect.

Idempotent. Every file backed up to .bak_msgbar2.
"""
import os
import re
import sys

SUFFIX = '.bak_msgbar2'
PLANNER = os.path.join('pages', 'templates', 'meal_planner.html')
SHOP = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')
PRINT = os.path.join('pages', 'templates', 'meal_plan_print.html')
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
ME = 'test_msg_bar.py'
PATCHER = 'apply_msg_bar.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MG-1, 21 Oct 2026'
CHECK = False
CREATES = ()

PAGES = (PLANNER, SHOP, PRINT)

# THE BLOCK, in the spelling 73 of the 78 pages already use.
BLOCK = """{# THE MESSAGE BAR - MG-1, 21 Oct 2026.                             #}
{#                                                                  #}
{# This page wrote messages and could not show one. Django keeps a  #}
{# message in the session until a template RENDERS it, and 78 of    #}
{# the 151 live templates carry this loop - the planner, the        #}
{# shopping list and the printable plan carried none between them.  #}
{# So twelve messages.success() calls in meal_planning.py queued up #}
{# and surfaced on whatever page came next: Recipe Management, or   #}
{# the logout screen. Demetri reported exactly that.                #}
{#                                                                  #}
{# `msg`, not `message`: 73 pages spell it this way and 5 do not.   #}
{# This is not the place to found a third dialect.                  #}
{% for msg in messages %}
    <div class="alert alert-{{ msg.tags }} alert-dismissible fade show alv-message" role="alert">
      {{ msg }}
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  {% endfor %}
"""


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
    raise SystemExit('MG-1 REFUSED: %s' % msg)


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

    first = read(os.path.join(root, PLANNER))
    if 'THE MESSAGE BAR - MG-1' in first:
        print('MG-1  already applied - the three pages can show a message.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING. Asked of the three pages, and of the view that
    # writes to them: a round that added a bar to a page which never
    # queues a message would be decoration.
    for rel in PAGES:
        if 'alv-message' in T.code_only(read(os.path.join(root, rel))):
            refuse('%s already renders a message bar' % rel)
    vsrc = T.python_code_only(read(os.path.join(root, VIEW)),
                              payloads=True)
    n_msgs = len(re.findall(r'messages\.(?:success|info|error|warning)\(',
                            vsrc))
    if n_msgs < 1:
        refuse('%s writes no messages, so there is nothing to show'
               % VIEW)

    # ---- AND THE BLOCK IS THE HOUSE BLOCK. Read the majority shape
    # off the tree rather than trusting the literal above.
    import collections
    shapes = collections.Counter()
    for p in T.templates():
        s = read(p).replace('\r\n', '\n')
        if 'alv-message' not in s:
            continue
        i = s.index('alv-message')
        j = s.rfind('{% for', 0, i)
        if j < 0:
            continue
        k = s.find('{% endfor %}', i)
        shapes[re.sub(r'\s+', ' ', s[j:k + 12]).strip()] += 1
    if not shapes:
        refuse('no page in the tree renders a message bar, so there is '
               'no house shape to copy')
    house, n = shapes.most_common(1)[0]
    mine = re.sub(r'\s+', ' ',
                  BLOCK[BLOCK.index('{% for'):]).strip()
    if mine != house:
        refuse('the block this round writes is not the one %d pages '
               'already use:\n  house: %s\n  mine : %s'
               % (n, house[:90], mine[:90]))

    for rel in PAGES:
        p = os.path.join(root, rel)
        out[p] = swap(read(p), '{% block content %}\n',
                      '{% block content %}\n\n' + BLOCK,
                      '%s (the bar)' % rel)

    # ---- AND THE PRINTABLE PAGE DOES NOT PRINT IT.
    #
    # Its own gate below caught this: a dismissible alert on paper is
    # a coloured box with a close cross in it, and the whole point of
    # that page is what comes out of the printer. SL-1 hides the
    # chrome on the shopping list the same way.
    ppr = os.path.join(root, PRINT)
    out[ppr] = swap(out[ppr],
                    """    nav, .navbar, header, footer,
    .page-action-buttons, .pp-noprint { display: none !important; }""",
                    """    nav, .navbar, header, footer,
    /* .alv-message - MG-1, 21 Oct 2026. This page can show a message
       now, and a dismissible alert on paper is a coloured box with a
       close cross in it. */
    .alv-message,
    .page-action-buttons, .pp-noprint { display: none !important; }""",
                    '%s (the message bar on paper)' % PRINT)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_sl_range_row.py'
)""", """    'test_sl_range_row.py',
    # MG-1, 21 Oct 2026 - three meal-plan pages wrote messages and
    # none of them could show one.
    'test_msg_bar.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_plan_shopping_list.html'; Text = 'UNDER THE BAR - SH-2';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE MESSAGE BAR - MG-1'; What = 'MG-1: the planner, the shopping list and the printable plan render Django messages - between them they carried none, so twelve messages.success() calls queued in the session and surfaced on whatever screen came next' },
    @{ File = 'pages/templates/meal_plan_shopping_list.html'; Text = 'UNDER THE BAR - SH-2';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # SH-2, 21 Oct 2026 - one bar per page, and the range under it.
    'test_sl_range_row.py',
]""", """    # SH-2, 21 Oct 2026 - one bar per page, and the range under it.
    'test_sl_range_row.py',
    # MG-1, 21 Oct 2026 - a page that writes a message can show one.
    'test_msg_bar.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # SH-2, 21 Oct 2026 - the range row stops being a second bar.
    '.bak_slrangerow',
]""", """    # SH-2, 21 Oct 2026 - the range row stops being a second bar.
    '.bak_slrangerow',
    # MG-1, 21 Oct 2026 - the message bar the meal plans never had.
    '.bak_msgbar2',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    nn = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % nn.group(1),
                   'CONVERTED_N = %d   # MG-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(nn.group(1)) + 1, nn.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    for rel in PAGES:
        nc = T.code_only(out[os.path.join(root, rel)])
        # COUNT THE LOOP, NOT THE NAME. On the print page
        # 'alv-message' now appears twice - once as the element and
        # once as the selector that hides it on paper - and a count
        # of the name reported two bars where there is one.
        # The element and a rule naming the element are not two
        # elements. Ask for the thing that can only be the bar.
        nloops = nc.count('{% for msg in messages %}')
        if nloops != 1:
            refuse('%s: %d message bar(s), expected exactly 1'
                   % (rel, nloops))
        if 'class="alert' not in nc or 'alv-message' not in nc:
            refuse('%s: the bar is not the house alert' % rel)
        # IT IS THE FIRST THING IN THE CONTENT. A message that renders
        # below the fold is a message nobody reads.
        body = out[os.path.join(root, rel)]
        i = body.index('{% block content %}')
        if body.index('alv-message') - i > 1400:
            refuse('%s: the bar is %d characters into the content block, '
                   'which is not the top of the page'
                   % (rel, body.index('alv-message') - i))
    # AND THE PRINT PAGE DOES NOT PRINT IT. A dismissible alert on
    # paper is a box with an x in it.
    npr = T.code_only(out[os.path.join(root, PRINT)])
    pb = npr[npr.index('@media print'):] if '@media print' in npr else ''
    if 'alv-message' not in pb:
        refuse('%s: the message bar is not hidden on paper' % PRINT)

    if CHECK:
        print('MG-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        %d messages.*() in the view had nowhere to land'
              % n_msgs)
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('MG-1  applied - three pages can show a message now.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
