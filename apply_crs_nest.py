# -*- coding: utf-8 -*-
"""apply_crs_nest.py - round CP-1, 17 Oct 2026.

A CLAIM THE GATE ALREADY MAKES, MADE AGAIN WHERE IT CAN ONLY FLAKE.

test_crs_print.py section 4 proves its guard can now see the six CRS
pages. It does that by RUNNING the guard:

    r = subprocess.run([sys.executable, GUARD], ...)
    ok(m and int(m.group(1)) >= N_TEMPLATES_MIN, '... reports N ...')
    ok(r.returncode == 0, '  and it passes on this tree', ...)

The first of those two is a reading: how many templates the guard sees,
151 where it used to see 143. That is section 4's actual claim and it
is this suite's to make.

THE SECOND IS A DUPLICATE. test_print_queries.py is one of the 366
suites the gate runs in its own right. Its verdict is already reported,
by name, every push. Asserting it a second time from inside another
suite adds nothing - and it adds nothing in the most expensive possible
way, because the guard launches a browser, and it is being launched
from inside a worker that is already holding one, inside a pool of six.

MEASURED: it failed on 17 Oct at suite 365 of 366 and again at 223 of
366, and passed every single time it was run alone, and passed under
five concurrent browser suites. Nothing about the tree was different.

SO THE DUPLICATE GOES, AND TWO THINGS TAKE ITS PLACE.

    THE GUARD'S OWN FAILING LINES ARE PRINTED. When the nested run
    failed, all this suite said was the tally - "18 passed, 1 failed" -
    and which check disagreed was lost. Twice. Whatever the nested run
    says now, its FAIL lines are on the page.

    AND THE CLAIM IS REPLACED BY THE CLAIM THAT IT IS MADE ELSEWHERE.
    Dropping an assertion because something else makes it is only
    honest if the something else is checked. So this suite now asks
    whether the guard is on the gate at all. If somebody takes
    test_print_queries.py out of $suites, this fails - which is more
    than the old line did, because the old line would have gone on
    passing while the guard stopped being run on every push.

WHAT IT DOES NOT DO: retry. AR-1 re-runs a suite that died without
printing a tally; this one printed one. The difference is not the
flakiness - it is that this particular verdict is a copy, and a copy
can be dropped where an original cannot.
"""
import os
import sys

SUFFIX = '.bak_crsnest'
ME = 'test_crs_print.py'
PATCHER = 'apply_crs_nest.py'
ROUNDS = 'alv_rounds.py'
CHECK = False

BLOCK_WAS = """ok(r.returncode == 0, '  and it passes on this tree',
   out.strip().split('\\n')[-1][:70])"""
BLOCK_NOW = """# CP-1, 17 Oct 2026 - THE VERDICT IS NOT THIS SUITE'S TO GIVE.
#
# This line used to assert, on the nested return code, that
# test_print_queries.py passes - which the gate asserts every push, by
# running it as one of its 366 suites. The duplicate flaked twice in
# one day (suite 365 of 366, then 223 of 366) and passed every time it
# was run alone: a browser suite launched from inside a browser suite
# inside a pool of six is the seventh Chromium, and that says nothing
# about the tree.
#
# So the nested run is a READING now, not a verdict, and whatever it
# says is printed in full rather than compressed into a tally.
print('')
print('  the guard, run here to be READ - its verdict belongs to the')
print('  gate, which runs it as a suite of its own every push:')
_tally = [l.strip() for l in out.split('\\n') if 'passed,' in l]
print('     %s' % (_tally[-1] if _tally else '(no tally printed)'))
if r.returncode != 0:
    print('     IT DID NOT PASS WHEN RUN FROM HERE. Its own words:')
    for _l in out.split('\\n'):
        if _l.strip().startswith('FAIL'):
            print('       %s' % _l.strip()[:150])
    print('     The gate runs it by name; believe that run, not this')
    print('     one. If the gate agrees, it is a real failure.')

# AND THE CLAIM THAT REPLACES IT. Dropping an assertion because
# something else makes it is only honest if the something else is
# checked - so this asks whether the guard is still on the gate. The
# old line would have gone on passing while the guard quietly stopped
# being run on every push; this one will not.
_ps1 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % GUARD in _ps1,
   '  and the gate runs %s by name, every push - which is where its '
   'verdict is given' % GUARD)"""

REG_WAS = """    # CC-3, 17 Oct 2026 - CC-2's modal opened empty on the live site:
    # cloneNode copies the inline style toggleView writes.
    '.bak_contactwire',
]"""
REG_NOW = """    # CC-3, 17 Oct 2026 - CC-2's modal opened empty on the live site:
    # cloneNode copies the inline style toggleView writes.
    '.bak_contactwire',
    # CP-1, 17 Oct 2026 - a browser suite run from inside a browser
    # suite; the verdict was a duplicate and it was the half that flaked.
    '.bak_crsnest',
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
    raise SystemExit('CP-1 REFUSED: %s' % msg)


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

    p = os.path.join(root, ME)
    t = read(p)

    # ---------------------------------------------------------------- 0
    if 'CP-1' in t:
        print('CP-1  already applied - the nested verdict is a reading.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE READING MUST SURVIVE. This round drops the verdict, not the
    # measurement, and a tree where the measurement has already gone is
    # not the tree this round was written against.
    if 'N_TEMPLATES_MIN' not in t:
        refuse('%s no longer reads the guard template count - the half '
               'this round keeps is already gone' % ME)
    if 'subprocess.run' not in t:
        refuse('%s no longer runs the guard at all' % ME)

    t = swap(t, BLOCK_WAS, BLOCK_NOW, '%s (the nested verdict)' % ME)
    if 'ok(r.returncode == 0' in t:
        refuse('the nested verdict survived the swap')
    import ast
    try:
        ast.parse(t)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (ME, e.lineno, e.msg))
    out[p] = t

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    # ---------------------------------------------------------------- 3
    if CHECK:
        print('CP-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('CP-1 applied.')
    print('   the nested guard is READ, not judged')
    print('   its FAIL lines are printed when there are any')
    print('   and the suite now checks the gate still runs it by name')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
