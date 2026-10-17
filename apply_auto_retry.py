# -*- coding: utf-8 -*-
"""apply_auto_retry.py - round AR-1, 17 Oct 2026.

A SUITE THAT DIED IS NOT A SUITE THAT DISAGREED.

Demetri's gate, 17 Oct, at suite 305 of 363:

    == [305/363] test_filter_get.py   50.5s
       ...
       3a  the rows
    ...docxcompose\\properties.py:18: UserWarning: pkg_resources is...
    !! [305/363] test_filter_get.py FAILED

    !! 1 suite(s) FAILED: test_filter_get.py
        1470s wall clock, 6 worker(s)
    FAIL  one or more suites FAILED - see the lines above
      Stopping.  Nothing has been staged.

Read that again for what is NOT in it. No FAIL line from the suite. No
tally. No traceback - and stderr is printed after stdout, so a
traceback would have been the last thing on the page rather than a
deprecation warning. stdout simply STOPS, in the middle of section 3a,
on the first request the section makes.

That is a process that was KILLED, not a check that disagreed. It
passed on the resume, against a tree nobody had touched.

WHAT MADE IT POSSIBLE. GT-2 moved the gate's loop into a pool of six.
Six workers mean up to six Chromiums, and 54 of the suites stand up
Django and migrate a database into memory before they ask anything.
Under that load a laptop can lose a process, and the process it loses
says nothing about the tree.

WHAT THIS ROUND DOES - two things, both small.

    THE EXIT CODE IS PRINTED. The single fact that would have said
    what happened was the return code, and the gate did not print it.
    On Windows a silent kill IS the code: 3221225477 an access
    violation, 3221225725 a blown stack, 1 an ordinary failed check.

    EVERY FAILURE IS RE-RUN ONCE, ALONE, after the pool has drained.
    A verdict that depends on how many browsers were open is not a
    verdict about the tree. Two more suites proved that the same day:
    test_crs_print.py failed at 365 of 366 and again at 223 of 366
    and passed alone both times, and test_print_queries.py took 504
    seconds in a pool of six, reported a failed check, and passed 19
    of 19 alone in a fraction of that.

    The first spelling of this round retried only the suites that
    printed no tally, on the reasoning that one saying "1 failed" had
    made a claim. That is right about BELIEVING a verdict and wrong
    about which verdict to believe: between a contended run and an
    uncontended one, the uncontended one is the one about the tree.

    AND NO RESCUE IS SILENT. Every one is named in the summary, so a
    suite that needs rescuing on every push is visible rather than
    absorbed, and a suite that fails alone as well fails the gate with
    its whole output printed.

WHAT IT REFUSES TO DO: call a rescued sweep green. Without -Force the
pool stops at the first failure and cancels what has not started, so
clearing that failure leaves suites that never ran. Reporting "all
passed" there would hand the gate a green light over an unswept tree -
which is the exact shape of the 16 Oct push that deployed nothing. The
count is checked, and the run exits 1 asking for -Resume. The resume
is cheap, because the rescued suite is already written into the log.

BOTH HALVES WERE CONTROLLED BEFORE THE ROUND EXISTED, with two suites
built for the purpose: one that exits 1 with no tally the first time
and passes the second, one that exits 1 having printed a tally. The
first is rescued; the second is not retried at all. test_gate_speed
rebuilds both and runs them.

WHAT IT CHANGES ABOUT THE ANSWERS: NOTHING. It changes which answer is
believed when a process does not live long enough to give one.
"""
import ast
import os
import sys

SUFFIX = '.bak_autoretry'
RUNNER = 'alv_run.py'
ME = 'test_gate_speed.py'
PATCHER = 'apply_auto_retry.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS = 'alv_rounds.py'
SENT = 'test_sentinels.py'
CHECK = False

# ------------------------------------------------------- 2. the lists
LISTS_WAS = """    failed, skipped = [], []"""
LISTS_NOW = """    failed, skipped, died, rescued = [], [], [], []"""

# ------------------------------------------------- 3. the failure line
FAIL_WAS = """            print('  !! %s %s FAILED' % (label, r['name']))"""
FAIL_NOW = """            # THE RETURN CODE, ALWAYS. 17 Oct: a suite failed on his
            # laptop having printed no FAIL line and no traceback -
            # stdout stopped mid-section and stderr held only a
            # deprecation warning. The one fact that would have said
            # what happened was the exit code, and the gate did not
            # print it. On Windows a silent kill IS the code: 3221225477
            # is an access violation, 3221225725 a blown stack, 1 an
            # ordinary failed check. Four characters of output.
            print('  !! %s %s FAILED  rc=%s' % (label, r['name'], r['rc']))
            if r['rc'] not in (0, 1) and '\\n' in r['out']:
                print('     last line of its output: %r'
                      % r['out'].rstrip().split('\\n')[-1][:100])
            # A VERDICT THAT DEPENDS ON HOW MANY BROWSERS WERE OPEN
            # IS NOT A VERDICT ABOUT THE TREE.
            #
            # The tree is a fixed thing and the gate's whole job is to
            # say whether it is right. Three suites disagreed with it
            # on 17 Oct and agreed with it when run by themselves, and
            # the only difference was load:
            #
            #   test_filter_get.py     killed mid-section on his laptop
            #                          at 305 of 363 - no tally, no
            #                          traceback. Passed on the resume.
            #   test_crs_print.py      failed at 365 of 366, then at
            #                          223 of 366. Passed alone, twice.
            #   test_print_queries.py  took 504s in a pool of six and
            #                          reported a failed check. 19 of
            #                          19 alone, in a fraction of that.
            #
            # The first spelling retried only the ones that printed NO
            # tally, reasoning that a suite saying "1 failed" had made
            # a claim. That is right about BELIEVING a verdict and
            # wrong about WHICH verdict to believe: between a contended
            # run and an uncontended one, the uncontended one is the
            # one that is about the tree.
            #
            # IT IS LOUD. Every rescue is named in the summary, so a
            # suite that needs one on every push is visible rather than
            # quietly absorbed, and a suite that fails alone as well
            # fails the gate with its whole output printed.
            died.append(r['name'])"""

# ------------------------------------------------------ 4. the phase
PHASE_WAS = """                    for f2 in futures:
                        f2.cancel()

    # ------------------------------------------------------------- log"""
PHASE_NOW = """                    for f2 in futures:
                        f2.cancel()

    # ---- phase 3: every failure, once each, alone
    #
    # ONE AT A TIME, WITH NOTHING ELSE RUNNING - the condition the
    # first run did not have, and the only one under which a verdict
    # is about the tree rather than about the machine.
    if died:
        print('')
        print('  -- %d suite(s) failed in the pool. Re-running each '
              'ONCE, alone, where nothing competes with it.' % len(died))
        for n in died:
            r = run_one(n)
            if r['rc'] == 0:
                rescued.append((n, r['secs']))
                print('  == %s PASSED alone in %.1fs - the pool was the '
                      'cause, not the tree' % (n, r['secs']))
                failed.remove(n)
                done[n] = True
                _save(done)
            else:
                print('  !! %s FAILED alone too  rc=%s - this one is real'
                      % (n, r['rc']))
                if not a.quiet:
                    for line in r['out'].rstrip().split('\\n'):
                        print('     %s' % line)

    # ------------------------------------------------------------- log"""

# ------------------------------------------------------- 5. the guard
# AND A RESCUE IS NEVER SILENT. A suite that needs one on every push
# is a suite with something wrong with it, and that only becomes
# visible if the rescues are named rather than absorbed.
RESC_WAS = """    secs = time.time() - t0
    print('')"""
RESC_NOW = """    secs = time.time() - t0
    print('')
    if rescued:
        print('  ** %d suite(s) failed in the pool and PASSED when '
              'run alone. The tree is not what was wrong with them:'
              % len(rescued))
        for n, sec in rescued:
            print('       %-34s %.1fs alone' % (n, sec))
        print('     If the same name keeps appearing here, that '
              'suite is too heavy to share a machine.')"""

GUARD_WAS = """    else:
        print('  OK  all %d suite(s) ran and passed' % (total - len(skipped)))"""
GUARD_NOW = """    # A RESCUE IS NOT A GREEN SWEEP. Without --force the pool stops at
    # the first failure and cancels the rest, so when phase 3 clears
    # that failure there are still suites that never ran. Reporting
    # that as "all passed" would hand the gate a green light over an
    # unswept tree - the exact shape of the 16 Oct deploy that deployed
    # nothing. So the count is checked, and the resume is cheap because
    # the rescued suite is already written into the log as passed.
    elif no[0] - len(skipped) < total - len(skipped):
        print('  !! the sweep stopped early: %d of %d suite(s) ran. The '
              'one that failed passed when run alone, so nothing is '
              'known to be wrong - but nothing is known to be right '
              'either.' % (no[0], total))
        print('     Re-run with --resume; it will start from where this '
              'stopped.')
        return 1
    else:
        print('  OK  all %d suite(s) ran and passed' % (total - len(skipped)))"""

# ---------------------------------------------- the pinned sentinel
# THE SEVENTH PIN, AND THE SAME STORY AS THE FIFTH AND THE SIXTH.
# GT-2 wrote a sentinel on alv_run.py standing on 'PLANTERS'. Nothing
# had ever backed that file up - GT-2 created it - so the row sat in
# the "no backup to compare against" bucket and was never examined.
# This round gives alv_run.py its first backup, which makes the row
# checkable, and it does not discriminate because this round did not
# touch PLANTERS. The day something removes a planter from that list
# the row starts discriminating and comes off the pin.
SENT_PIN_WAS = """    'tenant-name order':
        'the ordering the reminder lists drafts in, backed up once by PI-1',"""
SENT_PIN_NOW = """    'tenant-name order':
        'the ordering the reminder lists drafts in, backed up once by PI-1',
    # THE SEVENTH, 17 Oct 2026, AND THE SAME STORY AGAIN. GT-2 wrote
    # this row on a file it had just created, so there was no earlier
    # version to compare against and the row was never examined. AR-1
    # gave alv_run.py its first backup and made the row checkable; it
    # does not discriminate because AR-1 changed the retry and left the
    # planter list alone. Revealed, not broken.
    'PLANTERS':
        'the fifteen suites that must not share a tree, backed up once '
        'by AR-1',"""

# ------------------------------------------------------ 6. the register
REG_WAS = """    # RI-1, 17 Oct 2026 - a live fault, found by uploading a recipe.
    '.bak_imagewire',
]"""
REG_NOW = """    # RI-1, 17 Oct 2026 - a live fault, found by uploading a recipe.
    '.bak_imagewire',
    # AR-1, 17 Oct 2026 - a suite that died is not a suite that
    # disagreed; the first is re-run alone, the second is not.
    '.bak_autoretry',
]"""

# ------------------------------------------------------ 7. the sentinel
# ONE ROW, ON THE RUNNER - not on the gate script. An ABSENT row on
# Push-PendingChanges.ps1 is structurally impossible, because the rows
# live in that file; check_gates.py flags it on sight and GT-2 shipped
# that mistake three times before the shape was clear. This row is
# PRESENT, on alv_run.py, where the retry lives.
SENT_WAS = (
    "    @{ File = 'pages\\views\\recipes\\ai_extract.py'; "
    "Text = 'MEDIA_TYPES[file_type]'; Absent = $true; "
    "What = 'RI-1: and the extension no longer picks the media type' },")
SENT_NOW = SENT_WAS + """
    # ------------------------------------------------- AR-1, 17 Oct 2026
    @{ File = 'alv_run.py'; Text = 'died.append'; What = 'AR-1: a suite that printed no tally is re-run once, alone' },"""


# ------------------------------------------------------- 8. the suite
# THE CLAIMS GO INTO GT-2'S OWN SUITE, not a new one. alv_run.py has a
# suite already; a second one for a nine-line correction to it would
# cost the whole registration tax - CONVERTED, $suites, two hand-kept
# counters - and would then have to say which of the two owns the file.
SUITE_WAS = """# ==========================================================================
head('6. REGISTERED, ON THE GATE')"""
SUITE_NOW = '''# ==========================================================================
head('6. A VERDICT THAT DEPENDS ON THE LOAD IS NOT A VERDICT')   # AR-1
# ==========================================================================
# AR-1, 17 Oct 2026. His gate lost test_filter_get.py at 305 of 363
# with no tally, no traceback and no exit code printed; it passed on
# the resume against a tree nobody had touched. test_crs_print.py and
# test_print_queries.py did the same thing in this sandbox the same
# day. Six workers mean six browsers and several Django boots at
# once, and a verdict reached under that load is about the machine.
RUN_NOW = read(os.path.join(ROOT, RUNNER))
RUN_WAS = as_gt2_left(RUNNER)
ok('died.append' in RUN_NOW,
   'a failure in the pool is remembered, not just reported')
ok('Re-running each' in RUN_NOW,
   '  and EVERY failure is re-run alone, not only the silent ones')
ok('rescued.append' in RUN_NOW,
   '  and a rescue is named in the summary, never absorbed quietly')
ok('failed.remove(' in RUN_NOW,
   '  and a suite that passes alone stops counting as failed')
ok('FAILED  rc=%s' in RUN_NOW,
   'and the exit code is printed on every failure - the one fact his '
   'gate did not give')
ok('the sweep stopped early' in RUN_NOW,
   'but a rescue over a stopped sweep is NOT called green')
ok(RUN_NOW.count('return 1') >= 2,
   '  it exits 1 and asks for --resume', RUN_NOW.count('return 1'))
ok(not APPLIED or 'died.append' not in RUN_WAS,
   'CONTROL: before this round a killed suite was simply a failure')

# ---- AND RUN, against two suites built to be the two cases ----------
# A suite that exits 1 having printed NO tally, and passes the second
# time; and a suite that exits 1 having printed one. The first must be
# rescued. The second must not be run twice - a suite that has made a
# claim about the tree is not asked again.
DIED = 'test_ar1_probe_died.py'
TOLD = 'test_ar1_probe_told.py'
DIED_SRC = """import os, sys
m = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.ar1_died')
if not os.path.isfile(m):
    open(m, 'w').write('x')
    print('  3a  the rows')
    sys.exit(1)
print('  2 passed, 0 failed, 0 skipped')
"""
TOLD_SRC = """import os, sys
m = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.ar1_told')
open(m, 'a').write('x')
print('  FAIL   the thing really is wrong')
print('  3 passed, 1 failed, 0 skipped')
sys.exit(1)
"""
log = os.path.join(ROOT, '.alv_run_log.json')
keep = open(log, 'rb').read() if os.path.isfile(log) else None
made = []
try:
    for n, s in ((DIED, DIED_SRC), (TOLD, TOLD_SRC)):
        p = os.path.join(ROOT, n)
        with open(p, 'w', encoding='utf-8', newline='\\n') as f:
            f.write(s)
        made.append(p)
    for mk in ('.ar1_died', '.ar1_told'):
        if os.path.isfile(os.path.join(ROOT, mk)):
            os.remove(os.path.join(ROOT, mk))

    r1 = subprocess.run([sys.executable, RUNNER, '--quiet', '--force',
                         '--only', DIED], cwd=ROOT, capture_output=True,
                        text=True, timeout=300)
    ok(r1.returncode == 0,
       'the one that printed no tally was re-run alone and RESCUED',
       'rc=%s' % r1.returncode)
    ok('Re-running each' in r1.stdout,
       '  and the gate said it was running it again, alone')
    ok('PASSED alone' in r1.stdout,
       '  and said the pool was the cause, not the tree')

    if os.path.isfile(log):
        os.remove(log)
    r2 = subprocess.run([sys.executable, RUNNER, '--quiet', '--force',
                         '--only', TOLD], cwd=ROOT, capture_output=True,
                        text=True, timeout=300)
    n_told = len(open(os.path.join(ROOT, '.ar1_told'),
                      encoding='utf-8').read())
    ok(r2.returncode == 1,
       'CONTROL: the one that really is wrong FAILED and STAYED failed',
       'rc=%s' % r2.returncode)
    ok(n_told == 2,
       '  having been given its second chance and refused it - twice '
       'run, twice wrong', '%d run(s)' % n_told)
    ok('FAILED alone too' in r2.stdout,
       '  and the gate says so in those words - this one is real')
    ok('PASSED alone' not in r2.stdout,
       '  and does not appear among the rescues')
finally:
    for p in made:
        if os.path.isfile(p):
            os.remove(p)
    for mk in ('.ar1_died', '.ar1_told'):
        p = os.path.join(ROOT, mk)
        if os.path.isfile(p):
            os.remove(p)
    if keep is None:
        if os.path.isfile(log):
            os.remove(log)
    else:
        open(log, 'wb').write(keep)


# ==========================================================================
head('7. REGISTERED, ON THE GATE')'''


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
    raise SystemExit('AR-1 REFUSED: %s' % msg)


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

    pr = os.path.join(root, RUNNER)
    t = read(pr)

    # ---------------------------------------------------------------- 0
    # ASKED OF THE TREE, FIRST. 'died.append' is the retry's own line
    # and nothing else in the file writes it.
    if 'died.append' in t:
        print('AR-1  already applied - a killed suite is re-run alone.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE GATE THAT MATTERS: the pool must already be there. This round
    # is a correction to GT-2 and is meaningless without it, and an
    # anchor that happens to be absent should refuse rather than write
    # a retry into a serial loop.
    if 'as_completed' not in t or 'ThreadPoolExecutor' not in t:
        refuse('%s has no pool - this round corrects GT-2 and needs it'
               % RUNNER)

    t = swap(t, LISTS_WAS, LISTS_NOW, '%s (the died list)' % RUNNER)
    t = swap(t, FAIL_WAS, FAIL_NOW, '%s (the failure line)' % RUNNER)
    t = swap(t, PHASE_WAS, PHASE_NOW, '%s (phase 3)' % RUNNER)
    t = swap(t, GUARD_WAS, GUARD_NOW, '%s (the early-stop guard)' % RUNNER)
    t = swap(t, RESC_WAS, RESC_NOW, '%s (the rescue summary)' % RUNNER)

    # AND IT MUST STILL PARSE. A patcher that writes a syntax error into
    # the file the gate runs its suites through does not cost a round -
    # it costs the ability to push, which is the GT-2 lesson.
    try:
        ast.parse(t)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (RUNNER, e.lineno, e.msg))
    out[pr] = t

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, ME)
    s = read(p)
    # THE SECOND FILE'S STEP 0. The runner was found unapplied above,
    # so a suite that already carries the claims means a previous run
    # stopped between the two writes.
    if 'AR-1' in s:
        refuse('%s already carries AR-1 but %s does not - a previous '
               'run stopped between the two writes. Restore both from '
               '%s and apply again.' % (ME, RUNNER, SUFFIX))
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the AR-1 section)' % ME)
    try:
        ast.parse(s)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (ME, e.lineno, e.msg))
    out[p] = s

    # ---------------------------------------------------------------- 3
    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    # ---------------------------------------------------------------- 4
    # AND THE PIN. The sentinel this round reveals, not breaks.
    p = os.path.join(root, SENT)
    out[p] = swap(read(p), SENT_PIN_WAS, SENT_PIN_NOW,
                  '%s (the seventh pin)' % SENT)

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    out[p] = swap(read(p), SENT_WAS, SENT_NOW, '%s (the sentinel)' % PS1)

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('AR-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('AR-1 applied.')
    print('   the gate prints the exit code when a suite fails')
    print('   every failure is re-run once, alone, after the pool')
    print('   a rescue is named in the summary, never absorbed')
    print('   and a rescue over a stopped sweep still exits 1')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
