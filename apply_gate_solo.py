# -*- coding: utf-8 -*-
"""apply_gate_solo.py - round GS-2, 2 Nov 2026.

RELEASE 63 - THE PUSH GATE: TWO MORE SUITES RUN ALONE.

    test_gate_walk.py and test_signing_finish.py each stopped a push in
    the pool and passed alone (Release 62 and Release 59). Pinned to the
    serial phase beside the GS-1 pair (Demetri, 2 Nov 21:32: "Yes please").

New files ship beside this patcher. Stands on Release 62. Idempotent.
Edits backed up to .bak_gatesolo. No migration. Nothing on the site changes.
"""
import os
import sys

SUFFIX = '.bak_gatesolo'
MARK = 'GS-2, 2 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_gate_solo.py',
)

SWAPS = [
    (os.path.join('alv_run.py'), [
        (r'''# Phase 3 is deliberately LEFT ALONE: it is how the next name gets
# found, and it has already found one.
CONTENDED = [
    'test_print_buttons.py',
    'test_print_queries.py',
]

''',
         r'''# Phase 3 is deliberately LEFT ALONE: it is how the next name gets
# found, and it has already found one.
#
# GS-2, 2 Nov 2026 - TWO MORE, BOTH FOUND BY PHASE 3 ON DEMETRI'S LAPTOP,
# each costing a stopped sweep and a --resume. Demetri, 21:32: "Yes
# please" to pinning them.
#
#   test_gate_walk.py       46.1s alone, passed; 7.19s vs 40.58s in a pool. It
#                           measures a RATIO of two timings - the claim
#                           is "more than ten times cheaper". Pool of
#                           three, push of Release 62 (2 Nov, 357/503):
#                           7.19s vs 40.58s, 5.6 times, FAILED. Alone:
#                           passed in 46.1s. A ratio of two timings taken
#                           while other workers share the CPU is a number
#                           about the machine.
#
#   test_signing_finish.py  9.6s alone, passed; crashed in a pool. Push of
#                           Release 59 (1 Nov, 460/500): the
#                           process itself died, rc 3221227274 (Windows
#                           0xC0000409, a fast-fail crash), not a failed
#                           check. Alone: passed in 9.6s. A crash under
#                           load and a clean pass alone.
CONTENDED = [
    'test_gate_walk.py',
    'test_print_buttons.py',
    'test_print_queries.py',
    'test_signing_finish.py',
]

'''),
    ]),
    (os.path.join('test_gate_serial.py'), [
        (r'''   'alv_run.py declares CONTENDED as a module-level list - parsed out '
   'of the syntax tree, not found as a string')
ok(contended == sorted(SLOW),
   '  and it holds exactly the names that were MEASURED: %s'
   % ', '.join(SLOW), 'got %r' % (contended,))

''',
         r'''   'alv_run.py declares CONTENDED as a module-level list - parsed out '
   'of the syntax tree, not found as a string')
# GS-2, 2 Nov 2026: the list grows as phase 3 finds names (it has found
# test_gate_walk and test_signing_finish since) - so the two measured
# here must still be there, in order, rather than be the whole list.
ok(set(SLOW) <= set(contended or []) and contended == sorted(contended),
   '  and it holds the names that were MEASURED: %s'
   % ', '.join(SLOW), 'got %r' % (contended,))

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # ------------------------------------------------- GS-1, 19 Oct 2026
    @{ File = 'alv_run.py'; Text = 'CONTENDED = ['; What = 'GS-1: a suite whose verdict moves with the load runs alone, because a pool failure cancels the rest of the sweep' },
    @{ File = 'alv_run.py'; Text = 'Only this list prevents it'; What = 'GS-1: and the phase 3 rescue is left alone - it explains a stop, it cannot undo one' },
    # ------------------------------------------------- MX-1, 19 Oct 2026
''',
         r'''    # ------------------------------------------------- GS-1, 19 Oct 2026
    @{ File = 'alv_run.py'; Text = 'CONTENDED = ['; What = 'GS-1: a suite whose verdict moves with the load runs alone, because a pool failure cancels the rest of the sweep' },
    @{ File = 'alv_run.py'; Text = "    'test_gate_walk.py',"; What = 'GS-2: the ratio suite and the e-sign suite run alone - each stopped a push in a pool and passed by itself' },
    @{ File = 'alv_run.py'; Text = 'Only this list prevents it'; What = 'GS-1: and the phase 3 rescue is left alone - it explains a stop, it cannot undo one' },
    # ------------------------------------------------- MX-1, 19 Oct 2026
'''),
        (r'''    'test_wellness_eighteen.py',
    # WL-15, 2 Nov 2026 - Wellness: sounds, movement, Saved.
    'test_wellness_nineteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_eighteen.py',
    # WL-15, 2 Nov 2026 - Wellness: sounds, movement, Saved.
    'test_wellness_nineteen.py',
    # GS-2, 2 Nov 2026 - two more suites that only pass alone run alone.
    'test_gate_solo.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-15, 2 Nov 2026 - Wellness: sounds, movement, Saved.
    '.bak_wellness19',
]

''',
         r'''    # WL-15, 2 Nov 2026 - Wellness: sounds, movement, Saved.
    '.bak_wellness19',
    # GS-2, 2 Nov 2026 - two more suites pinned to run alone.
    '.bak_gatesolo',
]

'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('GS-2 REFUSED: %s' % msg)


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

    pq = os.path.join(root, PS1)
    if "'test_gate_solo.py'" in read(pq):
        print('GS-2 already applied.')
        return 0
    if "'test_wellness_nineteen.py'" not in read(pq):
        refuse('Release 62 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new wellness files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('GS-2 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('GS-2 applied - the push gate: two more suites run alone.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
