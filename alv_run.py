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
    plant = [n for n in todo if n in PLANTERS]
    rest = [n for n in todo if n not in PLANTERS]
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
    failed, skipped = [], []
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
            print('  !! %s %s FAILED' % (label, r['name']))
            return bool(a.force)
        done[r['name']] = True
        _save(done)
        return True

    # ---- phase 1: the planters, one at a time, in a quiet tree
    if plant:
        print('')
        print('  -- %d planter(s) first, serially: they write into real '
              'files and put them back, so nothing else may be reading '
              'while they do' % len(plant))
    for n in plant:
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

    # ------------------------------------------------------------- log
    _save(done)

    secs = time.time() - t0
    print('')
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
    else:
        print('  OK  all %d suite(s) ran and passed' % (total - len(skipped)))
    print('      %.0fs wall clock, %d worker(s)' % (secs, a.workers))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
