# -*- coding: utf-8 -*-
"""apply_home_open.py - round HM-4, 16 Oct 2026.

THE WORD GOES IN THE BOX.

Demetri, testing Home: *"can we put the OPEN in the box. Something like:
'OPEN: 9 Today ...'"*

The Open figures sit in a bordered strip with their label on a line of
its own above it, so the strip costs two lines where it carries one row
of numbers.

WHAT MOVES, AND WHAT MUST NOT
    The label becomes the first term INSIDE .iss-strip. It keeps its own
    type - 11px, 600, uppercase, the same tracking and the same ink -
    because that treatment is what makes it read as a label rather than
    as another number. It loses its block margin, because a flex child
    does not need one.

THIS DOES NOT UNDO HM-3, AND THAT NEEDS SAYING
    HM-3 gave Open its own header rather than sharing one with the table
    below, and wrote the reason down: *"Open is a LEVEL at three moments
    and Logged and Closed are RATES over three periods, so they no
    longer share a header."* Open still has its own header here. Only
    the line break goes. The distinction HM-3 drew survives intact.

ONE USE, COUNTED
    `.iss-head` appears exactly once in the markup. Logged and Closed
    are in the .ins-kpis block above and carry their own labels, so
    nothing else is reachable from this change - which the gate checks
    rather than assumes.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_homeopen'
PAGE = 'home.html'
ME = 'test_home_open.py'
PATCHER = 'apply_home_open.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 92, 93
ALIAS_WAS, ALIAS_NOW = 95, 97
ALIAS_P_WAS, ALIAS_S_WAS = 47, 48
ALIAS_P_NOW, ALIAS_S_NOW = 48, 49

MARKUP_WAS = """        <p class="iss-head">Open</p>
        <div class="iss-strip">"""

MARKUP_NOW = """        {# HM-4, 16 Oct 2026 - the label is the first term in the strip #}
        {# now, not a line above it. Demetri: can we put the OPEN in the #}
        {# box. It keeps its own type, so it still reads as a label and #}
        {# not as another figure. #}
        {# #}
        {# AND THIS DOES NOT UNDO HM-3. That round gave Open its own #}
        {# header rather than sharing one with the table below, because #}
        {# Open is a LEVEL at three moments while Logged and Closed are #}
        {# RATES over three periods. It still has its own header. Only #}
        {# the line break is gone. #}
        <div class="iss-strip">
          <span class="iss-head">Open</span>"""

CSS_WAS = """    .iss-head { font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--alv-ink-soft); margin: 8px 0 3px; }"""

CSS_NOW = """    /* HM-4, 16 Oct 2026 - a term inside the strip, not a block above
       it. The type is untouched - 11px, 600, uppercase, the same
       tracking and ink - because that is what makes it read as a label.
       The block margin goes, because a flex child does not need one,
       and align-self keeps it on the baseline the figures sit on. */
    .iss-head { font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--alv-ink-soft); margin: 0;
      align-self: baseline; }"""


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
    raise SystemExit('HM-4 REFUSED: %s' % msg)


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


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


SUITE_WAS = """    'test_admin_behaviour.py'
)"""
SUITE_NOW = """    'test_admin_behaviour.py',
    'test_home_open.py'
)"""

TREE_WAS = """    'test_admin_behaviour.py',
]"""
TREE_NOW = """    'test_admin_behaviour.py',
    # HM-4, 16 Oct 2026 - the Open label moves inside its own strip, so
    # the figures and the word they belong to read as one line. Wide
    # from birth.
    'test_home_open.py',
]"""

ROUNDS_WAS = """    '.bak_adminbehav',
]"""
ROUNDS_NOW = """    '.bak_adminbehav',
    # HM-4, 16 Oct 2026 - home.html's Open label becomes the first term
    # inside .iss-strip instead of a block above it. HM-3's decision -
    # that Open has a header of its OWN - is untouched; only the line
    # break goes.
    '.bak_homeopen',
]"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""
SENT_NEW = """    # ------------------------------------------------- HM-4, 16 Oct 2026
    # Demetri, testing Home: can we put the OPEN in the box.
    @{ File = 'pages\\templates\\home.html'; Text = '<span class="iss-head">Open</span>'; What = 'HM-4: the Open label is a term inside its strip' },
    @{ File = 'pages\\templates\\home.html'; Text = '<p class="iss-head">'; Absent = $true; Code = $true; What = 'HM-4: and is no longer a block on a line of its own' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    if '<span class="iss-head">Open</span>' in code_only(read(page)):
        print('HM-4  already applied - the label is in the strip.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # ONE USE, COUNTED. If a second .iss-head ever appears this round is
    # reaching further than it was told to.
    s = read(page)
    body = code_only(s)
    n = len(re.findall(r'class="iss-head"', body))
    if n != 1:
        refuse('%s: %d .iss-head use(s), expected 1 - this round moves '
               'ONE label' % (PAGE, n))
    if 'ins-kpi__k' not in body:
        refuse('%s: the Logged/Closed labels are not where HM-3 left '
               'them, so the claim that this round does not touch them '
               'cannot be made' % PAGE)

    s = swap(s, MARKUP_WAS, MARKUP_NOW, '%s (the label)' % PAGE)
    s = swap(s, CSS_WAS, CSS_NOW, '%s (the label rule)' % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 2
    # GATES.
    b = code_only(s)
    if '<p class="iss-head">' in b:
        refuse('%s: the label is still a block' % PAGE)
    if b.count('class="iss-head"') != 1:
        refuse('%s: the label was copied rather than moved' % PAGE)
    # IT IS INSIDE THE STRIP, which is the whole request.
    i_strip = b.find('<div class="iss-strip">')
    i_head = b.find('class="iss-head"')
    i_first = b.find('class="iss-pt"')
    if not (i_strip < i_head < i_first):
        refuse('%s: the label is not the first term inside the strip '
               '(strip %d, label %d, first figure %d)'
               % (PAGE, i_strip, i_head, i_first))
    # AND THE FIGURES ARE UNTOUCHED.
    if b.count('class="iss-pt"') != 3:
        refuse('%s: %d figure(s) in the strip, expected 3'
               % (PAGE, b.count('class="iss-pt"')))
    if b.count('class="iss-sep"') != 2:
        refuse('%s: the separators moved' % PAGE)
    # EVERY {# #} CLOSES ON ITS OWN LINE - test_crs_comment_fix.
    bad = [i + 1 for i, ln in enumerate(s.split('\n'))
           if ln.count('{#') != ln.count('#}')]
    if bad:
        refuse('%s: a Django comment outlives its line, at %s' % (PAGE, bad))

    # ---------------------------------------------------------------- 3
    p = os.path.join(root, PS1)
    t = read(p)
    if ME in t:
        refuse('%s already lists this round' % PS1)
    t = swap(t, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    t = swap(t, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = t

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'HM-4, 16 Oct 2026 - this round own suite. The Open '
                  'label moves into its strip, after Demetri asked to '
                  'put the OPEN in the box.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    t = read(p)
    t = bump(t, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'HM-4, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    t = swap(t, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = t

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('HM-4 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('HM-4 applied.')
    print('   the Open label is the first term INSIDE .iss-strip')
    print('   it keeps its type and loses its block margin')
    print('   the three figures and two separators are untouched')
    print("   HM-3's decision stands - Open still has a header of its own")
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
