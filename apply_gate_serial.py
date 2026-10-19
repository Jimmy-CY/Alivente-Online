# -*- coding: utf-8 -*-
"""apply_gate_serial.py - round GS-1, 19 Oct 2026.

RELEASE 3, PUSH 3. A RESCUE CANNOT UNDO A STOP.

THE COST, FIRST. Every push for the last three pushes, Demetri's gate
has stopped at about 262 of 377 suites, printed

    !! the sweep stopped early: 262 of 377 suite(s) ran. The one that
       failed passed when run alone, so nothing is known to be wrong -
       but nothing is known to be right either.

and asked him to run it again with --resume. That second run is about
twenty minutes of his time, on every push, to be told something the
first run already knew.

THE SUITE. test_print_queries.py. Measured in this sandbox today:

    alone            137s   19 of 19 passed
    pool of six      530s   reported a failed check

It is not broken. It boots Django and counts queries, and a query
count taken while five other workers are booting Django is a number
about the machine.

WHY THE RESCUE DOES NOT ALREADY FIX THIS, which is the whole round.
AR-1 built phase 3 on 17 Oct: every suite that fails in the pool is
re-run once, alone, and a suite that passes alone is named in the
summary and removed from `failed`. That is correct and it works -
test_print_queries is rescued on every single push.

But look at WHEN it runs. Without --force the pool stops dead at the
first failure:

    if not report(fut.result()) and not a.force:
        stop = True
        for f2 in futures:
            f2.cancel()

So by the time phase 3 proves the pool was the cause, a hundred and
fifteen suites have already been cancelled and will never run. The
rescue explains the stop; it cannot prevent it. AR-1's own summary
line says so out loud - "a rescue over a stopped sweep is NOT called
green" - and that line is right. The fix is not to trust the rescue
more. It is to stop the suite reaching the pool.

WHAT THIS ROUND DOES. One list, and three use sites.

    CONTENDED = ['test_print_queries.py']

A second reason to run alone, and NOT the planters' reason. A planter
runs alone because it WRITES into a real file and another reader must
not see the plant. These run alone because their VERDICT changes with
load. Two different faults, two different lists, two different
sentences in the output - because a list that collects "suites that
are special somehow" stops explaining anything the first time someone
has to decide whether a new suite belongs in it.

WHAT IT DOES NOT DO. It does not touch phase 3. The rescue stays
exactly where it is, for the suites nobody has measured yet - and the
line in the summary that says "if the same name keeps appearing here,
that suite is too heavy to share a machine" is how the NEXT member of
CONTENDED gets found. This round takes the one name that line has
already printed three times.

Not one claim moves. test_print_queries asserts exactly what it
asserted before, and so does every other suite. This file decides
ORDER and CONCURRENCY - GT-2's words, still true.

Idempotent. Every file backed up to .bak_gateserial.
"""
import ast
import os
import sys

SUFFIX = '.bak_gateserial'
RUN = 'alv_run.py'
ME = 'test_gate_serial.py'
PATCHER = 'apply_gate_serial.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'GS-1, 19 Oct 2026'
SLOW = ['test_print_buttons.py', 'test_print_queries.py']
CHECK = False


# ========================================================== THE DOCSTRING
# THE FILE'S OWN DESCRIPTION OF ITSELF STAYS TRUE. GT-2 wrote "the
# planters run first, alone, and everything else runs in a pool", and
# after this round that sentence is no longer the whole of it. A
# comment about a thing is the thing.
DOC_WAS = """    PARALLEL, except where parallel is a lie.  Fourteen suites plant a
    defect into a REAL file, read it, and put it back.  Run one of those
    beside a suite that reads the same file and the second one sees the
    plant.  That is not a theory - test_icon_names passes alone and
    FAILS beside five others, measured 16 Oct.  So the planters run
    first, alone, and everything else runs in a pool."""
DOC_NOW = """    PARALLEL, except where parallel is a lie.  Fourteen suites plant a
    defect into a REAL file, read it, and put it back.  Run one of those
    beside a suite that reads the same file and the second one sees the
    plant.  That is not a theory - test_icon_names passes alone and
    FAILS beside five others, measured 16 Oct.  So the planters run
    first, alone, and everything else runs in a pool.

    AND SO DOES ANYTHING WHOSE VERDICT MOVES WITH THE LOAD.  GS-1,
    19 Oct.  A planter runs alone because it WRITES; a CONTENDED suite
    runs alone because the number it measures is only about the tree
    when nothing else is running.  test_print_queries.py takes 137s
    alone and passes 19 of 19; in a pool of six it takes 530s and
    reports a failed check.  Phase 3 would rescue it - but the pool has
    already cancelled 115 suites by then, so the rescue buys an
    explanation and not a sweep."""


# =============================================================== THE LIST
LIST_WAS = """    'test_gate_speed.py',
]


def suites_from_ps1(path=PS1):"""
LIST_NOW = """    'test_gate_speed.py',
]

# THE CONTENDED - a SECOND reason to run alone, and not the planters'.
#
# A planter is here because it WRITES into a file the repo owns. A
# suite is HERE because its VERDICT changes with machine load: it
# passes by itself and fails in a pool of six, and between those two
# answers the uncontended one is the one that is about the tree.
#
# Keeping them in two lists rather than one is the point. They are
# fixed by different things - a planter needs a quiet TREE, these need
# a quiet MACHINE - and the next person deciding whether a new suite
# belongs has to answer which fault they have.
#
# WHY THE PHASE 3 RESCUE IS NOT ENOUGH, which is the whole of GS-1.
# AR-1 re-runs every pool failure alone and clears the ones that pass.
# It works, and test_print_queries has been rescued on every push since
# 17 Oct. But the pool STOPS at the first failure and cancels every
# future still queued, so the rescue runs over a sweep that already
# gave up - 262 of 377 suites on Demetri's laptop, three pushes in a
# row, and a --resume each time.
#
# THE RESCUE EXPLAINS THE STOP. Only this list prevents it.
#
# Measured, 19 Oct 2026, in the sandbox:
#
#   test_print_queries.py   137s alone, 19 of 19 passed
#                           530s in a pool of six, a failed check
#
#   test_print_buttons.py   204s alone, passed
#                           TIMED OUT in a pool of six, at 313 of 380
#
# Both drive Chromium over a census of pages. A verdict reached while
# five other workers are also launching browsers is a number about the
# machine.
#
# THE SECOND NAME WAS FOUND BY PHASE 3, ON THE FIRST SWEEP AFTER THIS
# ROUND WAS WRITTEN - which is exactly how the list is meant to grow.
# Its summary says "if the same name keeps appearing here, that suite
# is too heavy to share a machine", and test_print_buttons appeared
# there with a timeout and a 204s solo run. Without --force that
# timeout stops the sweep at 313 and costs a --resume: the same twenty
# minutes this round exists to remove, from a different suite.
#
# test_picker_grid.py is NOT here. It failed in one pool and passed in
# the next, and passed alone in 14.1s - a light suite having a bad
# moment is not a contended one. One observation is not a measurement.
#
# Phase 3 is deliberately LEFT ALONE: it is how the next name gets
# found, and it has already found one.
CONTENDED = [
    'test_print_buttons.py',
    'test_print_queries.py',
]


def suites_from_ps1(path=PS1):"""


# ============================================================== THE SPLIT
SPLIT_WAS = """    # ------------------------------------------------- order and split
    # RENDERS FIRST (E17), and the planters before everything, alone.
    plant = [n for n in todo if n in PLANTERS]
    rest = [n for n in todo if n not in PLANTERS]
    rest.sort(key=lambda n: (not renders(n), n))"""
SPLIT_NOW = """    # ------------------------------------------------- order and split
    # RENDERS FIRST (E17), and the planters before everything, alone.
    # GS-1, 19 Oct 2026 - and the contended beside them, for the other
    # reason. Planters first within the serial phase, because a planter
    # wants the quietest tree there is and the contended only want the
    # pool to not exist yet.
    plant = [n for n in todo if n in PLANTERS]
    slow = [n for n in todo if n in CONTENDED and n not in PLANTERS]
    serial = plant + slow
    rest = [n for n in todo
            if n not in PLANTERS and n not in CONTENDED]
    rest.sort(key=lambda n: (not renders(n), n))"""


# ============================================================== PHASE ONE
PH1_WAS = """    # ---- phase 1: the planters, one at a time, in a quiet tree
    if plant:
        print('')
        print('  -- %d planter(s) first, serially: they write into real '
              'files and put them back, so nothing else may be reading '
              'while they do' % len(plant))
    for n in plant:
        if not report(run_one(n)):
            break"""
PH1_NOW = """    # ---- phase 1: the planters and the contended, one at a time
    #
    # TWO REASONS, SAID SEPARATELY - GS-1, 19 Oct 2026. Printing one
    # number for both would make the next reader think there is one
    # kind of suite in here, and there are two.
    if serial:
        print('')
        print('  -- %d suite(s) first, one at a time:' % len(serial))
        if plant:
            print('       %d planter(s) - they write into real files and '
                  'put them back, so nothing else may be reading while '
                  'they do' % len(plant))
        if slow:
            print('       %d contended - they pass alone and fail in a '
                  'pool, and a pool failure CANCELS the rest of the '
                  'sweep, so running them here is the difference between '
                  'a swept tree and a --resume' % len(slow))
    for n in serial:
        if not report(run_one(n)):
            break"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "prefetch_related('courses')"; What = 'PK-1: the course ids come from one query, not one per card' },"""
SENT_NOW = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "prefetch_related('courses')"; What = 'PK-1: the course ids come from one query, not one per card' },
    # ------------------------------------------------- GS-1, 19 Oct 2026
    @{ File = 'alv_run.py'; Text = 'CONTENDED = ['; What = 'GS-1: a suite whose verdict moves with the load runs alone, because a pool failure cancels the rest of the sweep' },
    @{ File = 'alv_run.py'; Text = 'Only this list prevents it'; What = 'GS-1: and the phase 3 rescue is left alone - it explains a stop, it cannot undo one' },"""

SUITE_WAS = """    'test_picker_grid.py'
)"""
SUITE_NOW = """    'test_picker_grid.py',
    # GS-1, 19 Oct 2026 - the contended list. This suite RUNS the
    # runner against a planted slow suite and counts which phase
    # it landed in, because a list nobody reads is a list that
    # stops being true.
    'test_gate_serial.py'
)"""

TREE_WAS = """    'test_picker_grid.py',
]"""
TREE_NOW = """    'test_picker_grid.py',
    # GS-1, 19 Oct 2026 - test_print_queries out of the pool. Its
    # section 4 re-derives the contended signature across every
    # suite, the way test_gate_speed does for the planters.
    'test_gate_serial.py',
]"""

RD_WAS = """    '.bak_pickergrid',
]"""
RD_NOW = """    '.bak_pickergrid',
    # GS-1, 19 Oct 2026 - a rescue cannot undo a stop. The pool
    # cancelled 115 of 377 suites on three pushes in a row because
    # test_print_queries fails under contention; AR-1's phase 3 proved
    # the pool was the cause and could not give the sweep back. Twenty
    # minutes of Demetri's gate time per push.
    '.bak_gateserial',
]"""

WD_WAS = """CONVERTED_N = 112   # PK-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 113   # GS-1, 19 Oct 2026 - this round own suite   # (was 112)   # PK-1, 19 Oct 2026 - this round own suite"""


# ============================================================== HELPERS
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
    raise SystemExit('GS-1 REFUSED: %s' % msg)


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

    pr = os.path.join(root, RUN)
    r = read(pr)

    # ---------------------------------------------------------------- 0
    # ASK THE TREE FIRST, always.
    if 'CONTENDED = [' in r:
        print('GS-1  already applied - %s run outside the pool.'
              % ', '.join(SLOW))
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE, and here the fault is a SHAPE: the pool
    # cancels its futures on the first failure, and the suite this
    # round moves is in the pool. Both are checked, because a round
    # that fixes nothing is a round whose suite measures the weather.
    if 'f2.cancel()' not in r:
        refuse('%s does not cancel the pool on a failure, so a slow '
               'suite there would not be costing the sweep - this round '
               'was written for a runner that stops' % RUN)
    import alv_run as _run
    already = [s for s in SLOW if s in getattr(_run, 'PLANTERS', [])]
    if already:
        refuse('%s is already a planter, so it already runs alone and '
               'this round has nothing to do' % ', '.join(already))

    # AND IT MUST BE A SUITE THE GATE REALLY RUNS. A contended list
    # naming a suite that is not in $suites would be a list about
    # nothing.
    pp = os.path.join(root, PS1)
    s = read(pp)
    for one in SLOW:
        if "'%s'" % one not in s:
            refuse('%s does not run %s, so moving it between phases '
                   'changes nothing' % (PS1, one))
        if not os.path.isfile(os.path.join(root, one)):
            refuse('%s is not on disk' % one)

    # ---------------------------------------------------------------- 2
    r = swap(r, DOC_WAS, DOC_NOW, '%s (the docstring)' % RUN)
    r = swap(r, LIST_WAS, LIST_NOW, '%s (the CONTENDED list)' % RUN)
    r = swap(r, SPLIT_WAS, SPLIT_NOW, '%s (the split)' % RUN)
    r = swap(r, PH1_WAS, PH1_NOW, '%s (phase 1)' % RUN)
    out[pr] = r

    # ---------------------------------------------------------------- 3
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    pt = os.path.join(root, TREE)
    out[pt] = swap(read(pt), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nr = out[pr]

    # THE LIST IS REAL AND HOLDS THE MEASURED NAME. Asked of the
    # patched source by PARSING it, not by searching for a string -
    # a comment about a list is not a list.
    tree = ast.parse(nr)
    found = None
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and any(getattr(t, 'id', '') == 'CONTENDED'
                        for t in node.targets)):
            found = [e.value for e in node.value.elts]
    if found is None:
        refuse('%s: CONTENDED is not a module-level list after the '
               'patch' % RUN)
    if found != sorted(SLOW):
        refuse('%s: CONTENDED holds %r, expected exactly %r'
               % (RUN, found, sorted(SLOW)))

    # NOTHING LEFT THE POOL BY ACCIDENT. The planters are untouched -
    # this round adds a reason, it does not re-file the old one.
    pl_before = getattr(_run, 'PLANTERS', [])
    pl_after = None
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and any(getattr(t, 'id', '') == 'PLANTERS'
                        for t in node.targets)):
            pl_after = [e.value for e in node.value.elts]
    if pl_after != list(pl_before):
        refuse('%s: PLANTERS moved from %d name(s) to %s. This round '
               'does not touch the planters.'
               % (RUN, len(pl_before), pl_after))

    # PHASE 3 IS UNTOUCHED. The rescue is how the next contended suite
    # gets found, and a round that quietly removed it would take the
    # instrument away while using its reading.
    for keep in ('died.append', 'Re-running each', 'rescued.append',
                 'failed.remove(', 'the sweep stopped early'):
        if keep not in nr:
            refuse('%s: %r is gone. GS-1 keeps phase 3 exactly as AR-1 '
                   'left it - it is how the next name in CONTENDED is '
                   'found.' % (RUN, keep))

    # THE SPLIT REALLY EXCLUDES IT. Checked by running the two
    # comprehensions against the real suite list, not by reading them.
    names = _run.suites_from_ps1()
    plant = [n for n in names if n in pl_before]
    slow = [n for n in names if n in found and n not in pl_before]
    rest = [n for n in names if n not in pl_before and n not in found]
    for one in SLOW:
        if one in rest:
            refuse('%s: %s is still in the pool after the split'
                   % (RUN, one))
        if one not in slow:
            refuse('%s: %s did not land in the serial phase'
                   % (RUN, one))
    if len(plant) + len(slow) + len(rest) != len(names):
        refuse('%s: the three phases hold %d + %d + %d of %d suites - a '
               'suite is in two phases or in none'
               % (RUN, len(plant), len(slow), len(rest), len(names)))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('GS-1 --check')
        print('  %s: %s' % (RUN, 'CONTENDED = %r' % found))
        print('  phases     : %d planter(s) + %d contended + %d pooled '
              '= %d' % (len(plant), len(slow), len(rest), len(names)))
        print('  the pool loses %s' % ', '.join(SLOW))
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('GS-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_gate_serial.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
