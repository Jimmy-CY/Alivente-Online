# -*- coding: utf-8 -*-
"""alv_run.py - the suite runner.  GT-2, 17 Oct 2026.

WHY THIS IS PYTHON AND NOT POWERSHELL.

The gate ran its suites from a `foreach` loop inside
Push-PendingChanges.ps1.  That loop is correct and has been for two
months, but it cannot be CHANGED safely from here: this sandbox has no
PowerShell, so every edit to that file ships untested.  A broken gate
does not cost an hour - it costs the ability to push at all.

So the loop moves into a file that can be run against the real 360
suites before it is delivered, and the PS1 keeps one line that calls it.

WHAT IT DOES THAT THE LOOP DID NOT

    PARALLEL, except where parallel is a lie.  Fourteen suites plant a
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
    explanation and not a sweep.

    RENDERS FIRST.  E17.  71% of the suites launch a browser; if the
    browser is missing or the fixture cannot be opened, that should
    show at suite 10 and not at suite 350.

    --resume.  E17 again.  A failure at 300 restarts at 300, not at 1 -
    but ONLY for suites that could not have been affected by what
    changed since the log was written.  Everything else re-runs.  A
    resume that skips a suite the fix broke is worse than no resume.

WHAT IT DOES NOT CHANGE

    Not one claim.  This file decides ORDER and CONCURRENCY.  Every
    suite asserts exactly what it asserted before, and a suite that
    passes here passes alone.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.abspath(__file__))
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
LOG = os.path.join(ROOT, '.alv_run_log.json')

# THE PLANTERS - LISTED, NOT GUESSED.
#
# A suite is here because it writes into a file the repo really owns and
# restores it afterwards.  That is a correct thing for a suite to do -
# test_css_order proves a selector collision by MAKING one - and it is
# the one thing that cannot share a tree with another reader.
#
# The list is explicit rather than detected, because a heuristic that
# silently stops matching gives you a race nobody can reproduce.
# test_gate_speed.py re-derives the signature and fails if a suite
# outside this list starts planting.
PLANTERS = [
    'test_auth_flow.py',
    'test_btn_border.py',
    'test_btn_info.py',
    'test_button_sweep.py',
    'test_css_order.py',
    'test_finance_rows.py',
    'test_form_wrap.py',
    'test_icon_names.py',
    'test_login_email.py',
    'test_ps1_comment.py',
    'test_row_exempt.py',
    'test_row_wrap.py',
    'test_submit_form.py',
    'test_warn_stripe.py',
    # GT-2's own suite joins them, and section 3 is what put it here.
    # It writes a probe file into the repo to prove the resume is keyed
    # on content rather than on a timestamp, and a suite that writes
    # into the repo cannot promise another suite is not reading while
    # it does - whether or not anything happens to read THAT file. The
    # signature caught it; arguing with the signature is how a race
    # nobody can reproduce gets written.
    'test_gate_speed.py',
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


def suites_from_ps1(path=PS1):
    """The suite list, read from the gate - not kept in a second place.

    test_sentinels already parses this file for its own table, and every
    round's suite asserts its own name is in it.  One source."""
    src = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'\$suites\s*=\s*@\((.*?)\n\)', src, re.S)
    if not m:
        raise SystemExit('alv_run: could not find $suites in %s' % path)
    return re.findall(r"'([^']+\.py)'", m.group(1))


def renders(name):
    """Does this suite launch a browser?  Asked of the file."""
    try:
        t = open(os.path.join(ROOT, name), encoding='utf-8',
                 errors='replace').read()
    except OSError:
        return False
    return 'sync_playwright' in t


def tree_stamp():
    """A cheap fingerprint of every file a suite could read."""
    h = hashlib.sha256()
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn
                 if d not in ('.git', '__pycache__', 'node_modules')]
        for f in sorted(fn):
            if f.endswith(('.bak_' + 'x')[:0] or '.pyc'):
                continue
            p = os.path.join(dp, f)
            if '.bak_' in f or f.endswith('.pyc'):
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue
            h.update(('%s|%d|%d\n' % (os.path.relpath(p, ROOT),
                                      st.st_size, int(st.st_mtime))).encode())
    return h.hexdigest()


def changed_since(stamp_files):
    """Which recorded files have really CHANGED since the log was written.

    BY CONTENT, NOT BY mtime.  The fourteen planters write a defect into
    a real file and then write the original back - which bumps the
    mtime without changing a byte.  A resume keyed on mtime therefore
    decided the tree had moved every single run, put 46 suites back in,
    and re-ran the planters serially before doing any new work.  It made
    no progress at all between two chunks, which is how it was found.

    A file is changed when its CONTENT is different.  Nothing else."""
    out = []
    now = file_table()
    for rel, sig in stamp_files.items():
        if now.get(rel) != (sig if isinstance(sig, str) else tuple(sig)):
            out.append(rel)
    for rel in now:
        if rel not in stamp_files:
            out.append(rel)
    return out


SKIP_DIRS = ('.git', '__pycache__', 'node_modules', '.pytest_cache')


def file_table():
    """Content fingerprint of every file a suite could read.

    The run log itself is excluded - it is written by this process on
    every suite that passes, so including it would mean the tree had
    always just changed."""
    t = {}
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if '.bak_' in f or f.endswith('.pyc'):
                continue
            p = os.path.join(dp, f)
            if os.path.abspath(p) == os.path.abspath(LOG):
                continue
            try:
                with open(p, 'rb') as fh:
                    t[os.path.relpath(p, ROOT).replace(os.sep, '/')] = (
                        hashlib.sha256(fh.read()).hexdigest()[:16])
            except OSError:
                continue
    return t


def run_one(name):
    t0 = time.time()
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        return {'name': name, 'rc': None, 'out': '', 'secs': 0.0}
    try:
        p = subprocess.run([sys.executable, name], cwd=ROOT,
                           capture_output=True, text=True, timeout=600)
        out, rc = p.stdout + p.stderr, p.returncode
    except subprocess.TimeoutExpired:
        out, rc = '(timed out after 600s)', 'TIMEOUT'
    return {'name': name, 'rc': rc, 'out': out,
            'secs': round(time.time() - t0, 1)}


def main(argv=None):
    # LINE-BUFFERED, ALWAYS. Piped into the gate's Say helper, Python
    # block-buffers stdout and the user sees nothing for minutes - which
    # is exactly what a progress counter exists to prevent.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='keep going after a failure')
    ap.add_argument('--only', default='',
                    help='comma-separated subset, for trials')
    ap.add_argument('--quiet', action='store_true',
                    help='print each suite tally, not its whole output')
    a = ap.parse_args(argv)

    names = ([s.strip() for s in a.only.split(',') if s.strip()]
             if a.only else suites_from_ps1())
    total = len(names)

    # ---------------------------------------------------------- resume
    done = {}
    if a.resume and os.path.isfile(LOG):
        old = json.load(open(LOG))
        moved = changed_since(old.get('files', {}))
        # A SUITE IS ONLY SKIPPED IF NOTHING IT COULD READ HAS MOVED.
        # alv_impact already answers that question for the rest of the
        # project; it answers it here too.  A resume that skips a suite
        # the fix broke is worse than no resume at all.
        forced = set()
        if moved:
            try:
                import alv_impact
                picked, _named, _why = alv_impact.select(moved)
                forced = set(picked)
            except Exception as e:
                print('  !! alv_impact could not be asked (%s) - '
                      'nothing will be skipped' % e)
                forced = set(names)
        done = {k: v for k, v in old.get('passed', {}).items()
                if k not in forced}
        print('  resuming: %d suite(s) passed last run and nothing they '
              'read has moved' % len(done))
        if moved:
            print('            %d file(s) changed since, which puts %d '
                  'suite(s) back in the run'
                  % (len(moved), len(forced & set(names))))

    todo = [n for n in names if n not in done]

    # ------------------------------------------------- order and split
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
    rest.sort(key=lambda n: (not renders(n), n))

    def _save(d):
        # WRITTEN AS IT GOES. A run killed at suite 300 - by a timeout,
        # a closed laptop, a Ctrl-C - must still resume from 300. A log
        # written only at the end is a log that exists only when it was
        # not needed.
        json.dump({'passed': d, 'files': FILES, 'when': time.time()},
                  open(LOG, 'w'))

    FILES = file_table()
    wide = len(str(total))
    no = [len(done)]
    failed, skipped, died, rescued = [], [], [], []
    t0 = time.time()

    def report(r):
        no[0] += 1
        label = '[%s/%d]' % (str(no[0]).rjust(wide), total)
        if r['rc'] is None:
            skipped.append(r['name'])
            print('  -- %s %s not present - skipped' % (label, r['name']))
            return True
        print('')
        print('  == %s %s   %.1fs' % (label, r['name'], r['secs']))
        if a.quiet:
            tail = [l for l in r['out'].split('\n') if 'passed,' in l]
            if tail:
                print('     %s' % tail[-1].strip())
            else:
                # 38 of the suites do not print "N passed, N failed".
                # AS-1 measured that on 16 Oct and had to add an
                # exit-code fallback; so does this.
                last = [l for l in r['out'].rstrip().split('\n') if l.strip()]
                print('     %s' % (last[-1].strip()[:90] if last
                                   else '(no output)  rc=%s' % r['rc']))
        else:
            for line in r['out'].rstrip().split('\n'):
                print('     %s' % line)
        if r['rc'] != 0:
            failed.append(r['name'])
            # THE RETURN CODE, ALWAYS. 17 Oct: a suite failed on his
            # laptop having printed no FAIL line and no traceback -
            # stdout stopped mid-section and stderr held only a
            # deprecation warning. The one fact that would have said
            # what happened was the exit code, and the gate did not
            # print it. On Windows a silent kill IS the code: 3221225477
            # is an access violation, 3221225725 a blown stack, 1 an
            # ordinary failed check. Four characters of output.
            print('  !! %s %s FAILED  rc=%s' % (label, r['name'], r['rc']))
            if r['rc'] not in (0, 1) and '\n' in r['out']:
                print('     last line of its output: %r'
                      % r['out'].rstrip().split('\n')[-1][:100])
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
            died.append(r['name'])
            return bool(a.force)
        done[r['name']] = True
        _save(done)
        return True

    # ---- phase 1: the planters and the contended, one at a time
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
            break

    # ---- phase 2: everything else, in a pool
    if not failed or a.force:
        if rest:
            nr = sum(1 for n in rest if renders(n))
            print('')
            print('  -- %d suite(s) in a pool of %d; the %d that launch a '
                  'browser go first, so a bad environment shows now and '
                  'not at suite %d' % (len(rest), a.workers, nr, total))
        # AS COMPLETED, NOT IN ORDER.
        #
        # ThreadPoolExecutor.map yields results in the order of the LIST,
        # so a slow suite near the front holds back every finished one
        # behind it - they sit unreported, unsaved, and a run killed by
        # a timeout loses all of them. Three resume chunks in a row made
        # no progress at all before this was found.
        #
        # A suite reports the moment it finishes, and the log is written
        # then. The number on the line is a counter, not a position.
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futures = {ex.submit(run_one, n): n for n in rest}
            stop = False
            for fut in as_completed(futures):
                if stop:
                    fut.cancel()
                    continue
                if not report(fut.result()) and not a.force:
                    stop = True
                    for f2 in futures:
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
                    for line in r['out'].rstrip().split('\n'):
                        print('     %s' % line)

    # ------------------------------------------------------------- log
    _save(done)

    secs = time.time() - t0
    print('')
    if rescued:
        print('  ** %d suite(s) failed in the pool and PASSED when '
              'run alone. The tree is not what was wrong with them:'
              % len(rescued))
        for n, sec in rescued:
            print('       %-34s %.1fs alone' % (n, sec))
        print('     If the same name keeps appearing here, that '
              'suite is too heavy to share a machine.')
    if skipped:
        print('  !! %d of %d suite(s) were not on disk and did not run:'
              % (len(skipped), total))
        for n in skipped:
            print('       %s' % n)
    if failed:
        print('  !! %d suite(s) FAILED: %s' % (len(failed),
                                               ', '.join(failed)))
        print('     Re-run with --resume once fixed; only the suites that '
              'could be affected will run again.')
    # A RESCUE IS NOT A GREEN SWEEP. Without --force the pool stops at
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
        print('  OK  all %d suite(s) ran and passed' % (total - len(skipped)))
    print('      %.0fs wall clock, %d worker(s)' % (secs, a.workers))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
