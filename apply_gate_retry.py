# -*- coding: utf-8 -*-
"""apply_gate_retry.py - round GS-4, 16 Nov 2026.

RELEASE 91 - A TIMING CHECK MEASURES TWICE BEFORE IT STOPS A PUSH.

    16 Nov: the R90 gate stopped at 19 of 530 on test_gate_walk's speed
    ratio - 7.78s against 33.95s, 4.4 where it asks for 10 - on a busy
    laptop, and the same suite passed alone a minute later. Demetri: "Do
    it after R90 deploys".

    - test_gate_walk: a ratio short of ten is measured once more, both
      spellings, the same names; the claim fails only if the second
      measurement agrees. A real loss of the cache is slow both times and
      still fails.

New files ship beside this patcher. Stands on TR-10 (apply_travel_ten.py).
Idempotent. Edits backed up to .bak_gateretry. No migration.
"""
import os
import sys

SUFFIX = '.bak_gateretry'
MARK = 'GS-4, 16 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_gate_retry.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_nine.py',
    # TR-10, 16 Nov 2026 - Release 90: drag a day into order, phone too.
    'test_travel_ten.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_nine.py',
    # TR-10, 16 Nov 2026 - Release 90: drag a day into order, phone too.
    'test_travel_ten.py',
    # GS-4, 16 Nov 2026 - Release 91: a timing ratio measured twice.
    'test_gate_retry.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-10, 16 Nov 2026 - Release 90: drag a day into order, phone too.
    '.bak_travel10',
]

''',
         r'''    # TR-10, 16 Nov 2026 - Release 90: drag a day into order, phone too.
    '.bak_travel10',
    # GS-4, 16 Nov 2026 - Release 91: test_gate_walk measures its speed
    # ratio twice before it stops a push.
    '.bak_gateretry',
]

'''),
    ]),
    (os.path.join('test_gate_walk.py'), [
        (r'''print('       old spelling: %6.2fs for %d names' % (t_old, len(SAMPLE)))
print('       new spelling: %6.2fs' % (t_new,))
ok(t_new * 10 < t_old,
   'the new spelling is more than ten times cheaper - and the ratio '
''',
         r'''print('       old spelling: %6.2fs for %d names' % (t_old, len(SAMPLE)))
print('       new spelling: %6.2fs' % (t_new,))
# GS-4, 16 Nov 2026 - MEASURED TWICE BEFORE IT FAILS. On 16 Nov this
# check stopped Demetri's R90 gate at 19 of 530: 7.78s against 33.95s,
# a ratio of 4.4 on a laptop that was busy, and the same suite PASSED
# when the gate ran it alone a minute later. Nothing in the tree had
# changed - the picture moved, not the code (the F2a-1 pixel lesson).
# So a ratio short of ten is measured once more, both spellings again,
# and the claim fails only if the second measurement agrees with the
# first. A real loss of the cache is still caught: it would be slow
# both times.
if BEFORE is not None and not t_new * 10 < t_old:
    print('       the ratio was %.1f - measuring once more before '
          'deciding' % (t_old / max(t_new, 1e-9),))
    t0 = time.time()
    [BEFORE._toolchain(ROOT, nm, p) for nm, p in SAMPLE]
    t_old2 = time.time() - t0
    t0 = time.time()
    [CG._toolchain(ROOT, nm, p) for nm, p in SAMPLE]
    t_new2 = time.time() - t0
    print('       again: old %6.2fs, new %6.2fs' % (t_old2, t_new2))
    if t_new2 * 10 < t_old2:
        t_old, t_new = t_old2, t_new2
ok(t_new * 10 < t_old,
   'the new spelling is more than ten times cheaper - and the ratio '
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
    raise SystemExit('GS-4 REFUSED: %s' % msg)


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
    if "'test_gate_retry.py'" in read(pq):
        print('GS-4 already applied.')
        return 0
    if "'test_travel_ten.py'" not in read(pq):
        refuse('TR-10 (apply_travel_ten.py, Release 90) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('GS-4 --check: %d file(s) would change, none written; %d '
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
    print('GS-4 applied - test_gate_walk measures its speed ratio twice before it fails. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
