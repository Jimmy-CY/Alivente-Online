# -*- coding: utf-8 -*-
"""apply_stat_cols.py - round PJ-2, 15 Oct 2026.

THREE TILES IN A THIRD OF A COLUMN.

Demetri, after a full check of the Projects module:

  "I don't like it when COMPLETED cuts off in the box. The same happens
   with Greek. We need to find a Solution."


IT IS NOT CUT OFF, AND IT IS NOT SPILLING ANY MORE                MEASURED
============================================================================
SL-1 stopped the spill on 4 Oct by giving `.alv-stat-label` an
`overflow-wrap: break-word`. That worked: the label no longer draws 41px
past its own tile. It WRAPS instead - and because the lever is
break-word, the wrap lands inside the word.

    COMPLETE
    D

SL-1'S SUITE ASKED THE WRONG QUESTION, AND PASSED. It compared
scrollWidth against clientWidth at six widths, and after the round it was
zero everywhere, truthfully. A block element with break-word can never
report a scrollWidth past its box: it wraps rather than overflows. The
question that would have found this is HOW MANY LINES, and nothing asked
it.

                A control that asks the wrong question passes
                while the defect stands.


WHERE THE STRIP ACTUALLY LIVES
============================================================================
Two renders of this were untrustworthy before the third was believed.

  1. The first did not apply the override at all: before and after came
     out identical and the round was nearly built on that.
  2. The second applied it and measured the strip at the full content
     width. THE STRIP IS NOT THERE. It sits in a col-md-4 inside
     .task-list-header > .row, so three tiles share ONE THIRD of the
     content column.

Rebuilt with the real ancestry, real Bootstrap 4.1.3, the page's own CSS
and base's, in both languages:

    width   tile    label box   COMPLETED needs   EN lines   GR lines
    1024     62px      28px          82px            4          6
    1180     80px      46px          82px            2          4
    1280     91px      57px          82px            2          3
    1440    108px      74px          82px            2          2
    1600    126px      92px          82px            1          2
    1920    162px     128px          82px            1          2

A 28px box, an 82px word. The Greek for Completed - OLOKLIROMENES, one
word, 142px uppercase - takes SIX lines at 1024 and is still on two at
1920.


WHAT ONE COLUMN DOES
============================================================================
    width   tile    label box   longest Greek needs   lines   slack
    1024    211px     177px           142px             1     +35px
    1280    296px     262px           142px             1    +120px
    1920    509px     475px           142px             1    +333px

One line at every width in both languages. THE COST IS HEIGHT: the header
goes from 188px to 344px at 1280, so the table starts 156px lower.

HIS OWN WORDING WAS MEASURED TOO - "the number first and then the Status",
a row tile rather than a centred stack. It costs only 64px of header
instead of 156. It was rejected on the numbers: the Greek label breaks to
two lines at 1024 (131px box, 142px needed) and English clears by ONE
pixel. That is CC-1's clamp lesson a day later - a box that is exactly its
content wraps the first time a font does. Demetri was shown both sets of
numbers and chose the stack.


ONE CHARACTER, AND WHY NOTHING ELSE
============================================================================
The tile could be tightened - 10px of padding instead of 14 saves 24px of
header and keeps 39px of Greek slack. It is not done here. base's padding
is the house tile, a second rule on this page to save 24px is drift, and
.task-summary has exactly one job that test_task_table names out loud.


THE PHONE IS NOT TOUCHED, AND NOT BY LUCK
============================================================================
base's `.alv-stats.is-3up` declares `grid-template-columns` DIRECTLY, at
specificity 0-2-0, inside its `max-width: 768px` block. A custom property
set on this page cannot reach past a direct declaration, so below 768px
the strip is still three across at the tightened type SL-1 and P5
measured. Asserted by rendering it: 320, 360, 390 and 414 are identical
before and after, column for column and line for line.

WHICH ALSO MEANS SL-1'S BREAK-WORD IS STILL LOAD-BEARING and this round
must not be read as retiring it. It is on the base COMPONENT; fsr's five
tiles, property_detail's three and the two finance pages still have narrow
tiles, and the phone still has three across. test_stat_label keeps
measuring the component in a narrow tile, which is what it should have
been saying it measured all along.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_statcols'
PAGE = 'projects/project_task_list.html'
ME = 'test_stat_cols.py'
PATCHER = 'apply_stat_cols.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 81, 82
ALIAS_WAS, ALIAS_NOW = 73, 75
ALIAS_P_WAS, ALIAS_S_WAS = 36, 37
ALIAS_P_NOW, ALIAS_S_NOW = 37, 38

# ---------------------------------------------------------------- the page
CSS_WAS = """/* Three stats, so three columns - fsr sets 5 and the two finance pages
   set 3 the same way. base takes it to 2 on a phone by itself.
                                            [test_task_table.py] */
.task-summary { --alv-stats-cols: 3; }"""

CSS_NOW = """/* ONE COLUMN, NOT THREE - PJ-2, 15 Oct 2026. Demetri: "I do not like it
   when COMPLETED cuts off in the box. The same happens with Greek."

   It is not cut off, and since SL-1 it does not spill either. It WRAPS,
   and because the lever SL-1 reached for is overflow-wrap: break-word,
   the wrap lands inside the word: COMPLETE / D.

   THE STRIP LIVES IN A col-md-4, so three tiles share one third of the
   content column. Measured in Chromium inside the real
   .task-list-header > .row > .col-md-4, with base's CSS and this page's:

       width   tile    label box   COMPLETED needs   EN lines  GR lines
       1024     62px      28px          82px            4         6
       1280     91px      57px          82px            2         3
       1440    108px      74px          82px            2         2
       1920    162px     128px          82px            1         2

   A 28px box and an 82px word. One column gives a 177px label box at
   1024, which holds the longest Greek label - OLOKLIROMENES, 142px
   uppercase - on ONE line with 35px to spare, at every width in both
   languages. The cost is height: this header goes from 188px to 344px
   at 1280.

   THE PHONE IS NOT TOUCHED. base's .alv-stats.is-3up declares
   grid-template-columns directly, at 0-2-0, inside its max-width: 768px
   block, so a custom property on this page cannot reach past it. 320,
   360, 390 and 414 measure identical before and after.

   AND NOTHING ELSE MOVES. 10px of padding instead of base's 14 would
   save 24px of header, and is not taken: the house tile's padding is
   base's, and this rule has exactly one job.
                                 [test_stat_cols.py, test_task_table.py] */
.task-summary { --alv-stats-cols: 1; }"""

# ------------------------------------------------------------- the gate row
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------- PJ-2, 15 Oct 2026
    # Demetri: "I do not like it when COMPLETED cuts off in the box. The
    # same happens with Greek." Three tiles in a col-md-4 gave the label
    # a 28px box for an 82px word, and SL-1's break-word made the wrap
    # land mid-word. One column, measured: one line at every width in
    # both languages.
    @{ File = 'pages\\templates\\projects\\project_task_list.html'; Text = '--alv-stats-cols: 1'; What = 'the three task tiles stack, so COMPLETED stops breaking in half' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

# PJ-1 SHIPS WITH THIS ROUND AND IS APPLIED FIRST, so these three
# anchors are PJ-1's own register lines rather than CC-1's. Said here
# because an anchor that silently depends on another round is how a
# patcher comes to report "already applied" on a tree where it is not.
SUITE_WAS = """    'test_project_origin.py'
)"""

SUITE_NOW = """    'test_project_origin.py',
    'test_stat_cols.py'
)"""

TREE_WAS = """    'test_project_origin.py',
]"""

TREE_NOW = """    'test_project_origin.py',
    # PJ-2, 15 Oct 2026 - three stat tiles in a third of a column. The
    # label had a 28px box for an 82px word, and SL-1's break-word made
    # the wrap land mid-word. Wide from birth.
    'test_stat_cols.py',
]"""

ROUNDS_WAS = """    '.bak_prjorigin',
]"""

ROUNDS_NOW = """    '.bak_prjorigin',
    # PJ-2, 15 Oct 2026 - the Task List's three stat tiles stack into one
    # column, so a label that had a 28px box for an 82px word stops
    # wrapping inside itself. One character; the phone is untouched.
    '.bak_statcols',
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
    raise SystemExit('PJ-2 REFUSED: %s' % msg)


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


def markup_of(t):
    import re
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.join(PAGE.replace('/', os.sep))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, asked of the TREE and of the code
    # rather than of the file - a comment quoting the old declaration
    # must not be able to answer this question. CRLF-safe because the
    # literal is one line.
    if '--alv-stats-cols: 1' in code_only(read(page)):
        print('PJ-2  already applied - the task tiles are one column.')
        return 0

    # PJ-1 FIRST. This round's register anchors are PJ-1's lines, and a
    # swap() against a missing anchor refuses with a confusing message
    # about a literal rather than about the order.
    if 'test_project_origin.py' not in read(os.path.join(root, PS1)):
        refuse('PJ-1 is not applied - it ships with this round and its '
               'register lines are this round\'s anchors')

    out = {}

    # ---------------------------------------------------------------- 1
    s = read(page)
    before_markup = markup_of(s)
    s = swap(s, CSS_WAS, CSS_NOW, '%s (the column count)' % PAGE)

    # ---------------------------------------------------------------- 2
    # GATES. Each refuses the whole round rather than writing half.
    body = code_only(s)
    if '--alv-stats-cols: 3' in body:
        refuse('%s: the three-column declaration is still live' % PAGE)
    if body.count('--alv-stats-cols') != 1:
        refuse('%s: expected exactly one column declaration, found %d'
               % (PAGE, body.count('--alv-stats-cols')))
    # .task-summary HAS EXACTLY ONE JOB, and test_task_table says so out
    # loud. A round that gave it a second rule would have to re-point that
    # suite, and 24px of header is not worth it.
    import re
    rules = re.findall(r'\.task-summary(?![\w-])[^{}]*\{([^}]*)\}',
                       re.sub(r'/\*.*?\*/', ' ', body, flags=re.S))
    if len(rules) != 1 or '--alv-stats-cols' not in rules[0]:
        refuse('%s: .task-summary must keep exactly one rule carrying the '
               'column count, found %d' % (PAGE, len(rules)))
    # THE MARKUP DOES NOT MOVE. This round is a stylesheet change; the
    # strip keeps is-3up because the phone still wants three across.
    if markup_of(s) != before_markup:
        refuse('%s: this round must not touch the markup' % PAGE)
    if 'alv-stats task-summary is-3up' not in markup_of(s):
        refuse('%s: the strip no longer opts into base\'s phone 3-up'
               % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 3
    # the registers, and the two counters these rounds keep by hand
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_stat_cols.py' in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate row)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'PJ-2, 15 Oct 2026 - this round own suite. Three stat '
                  'tiles in a third of a column, after Demetri said he '
                  'does not like COMPLETED cutting off in the box.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'PJ-2, 15 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('PJ-2 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('PJ-2 applied.')
    print('   the three task tiles stack into one column: a 28px label')
    print('         box for an 82px word becomes 177px at 1024, one line')
    print('         at every width in English AND Greek')
    print('   the cost is 156px of header at 1280, measured and accepted')
    print('   the phone is untouched - is-3up declares its columns')
    print('         directly and a custom property cannot reach past it')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
