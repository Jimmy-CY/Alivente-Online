# -*- coding: utf-8 -*-
"""test_gate_speed.py - round GT-2, 17 Oct 2026.

THE GATE'S LOOP MOVES WHERE IT CAN BE TESTED.

Demetri, 17 Oct: "We are waiting 90 minutes for you to develop some
small change and then to do your sweep. Then it takes 60 minutes to run
it through the gates on my laptop. If it fails, then that takes another
60 minutes."

Sixty of those minutes were 360 suites run ONE AT A TIME by a `foreach`
loop inside Push-PendingChanges.ps1. The loop was correct. It could not
be improved from the sandbox these rounds are built in, because that
sandbox has no PowerShell - so every edit to it would ship untested, and
a broken gate does not cost an hour, it costs the ability to push.

So the loop moved into alv_run.py and the PowerShell kept a call.

WHAT THIS SUITE PROVES THAT READING THE DIFF CANNOT

    Section 4 proves the resume is keyed on CONTENT. It rewrites a real
    file with identical bytes and a newer timestamp and asserts that
    the runner does not call that a change - then appends one byte and
    asserts that it does. That is the bug that cost three resume chunks
    in a row: the fourteen planters restore a file by writing the
    original back, which bumps the mtime without changing a byte.

    Section 5 runs three suites through the runner and directly, and
    compares the verdicts. The claim of the round is that ORDER and
    CONCURRENCY changed and nothing else; this is that claim, measured.

    Section 3 re-derives the planting signature across every suite, so
    the explicit list of fourteen cannot silently go stale. A suite that
    starts planting tomorrow fails here today.

WHAT IT DOES NOT CLAIM

    It does not claim a speed. The trial that justified the round
    measured 1.5x in this CPU-starved container with six workers - his
    laptop has more cores and should do better, but that is not a number
    this suite can assert, and an unverifiable number is not worth
    asserting. What is asserted is that the answers are the same.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------


import json
import os
import re
import subprocess
import sys
import time

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)


SUFFIX = '.bak_gatespeed'
RUNNER = 'alv_run.py'
ME = 'test_gate_speed.py'
PATCHER = 'apply_gate_speed.py'
PS1 = 'Push-PendingChanges.ps1'

CONVERTED_NOW, ALIAS_NOW = 97, 103

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def as_gt2_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


P1 = os.path.join(ROOT, PS1)
NOW = read(P1)
APPLIED = os.path.isfile(P1 + SUFFIX)
WAS = read(P1 + SUFFIX) if APPLIED else NOW

print('')
print('test_gate_speed.py - round GT-2, 17 Oct 2026')
print('  gate     : %s' % PS1)
print('  runner   : %s' % RUNNER)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE GATE CALLS THE RUNNER, AND RUNS NO LOOP OF ITS OWN')
# ==========================================================================
ok(NOW.count('& python @runArgs') == 1,
   'the gate calls the runner exactly once',
   NOW.count('& python @runArgs'))
ok(not re.search(r'(?m)^foreach \(\$t in \$suites\) \{', NOW),
   'and runs no suite loop of its own')
ok(not re.search(r'(?m)^\$suiteWide\s*=', NOW),
   '  nor keeps the variables that loop needed')
ok('$skipped = @()' not in NOW,
   '  nor the skip list nothing fills any more')
ok(not APPLIED or re.search(r'(?m)^foreach \(\$t in \$suites\) \{', WAS),
   'CONTROL: it ran its own loop, one suite at a time, until this round')

# THE REQUEST THE NUMBERING EXISTS FOR SURVIVES.
ok('Demetri, 1 Oct 2026' in NOW,
   'and the request the numbering exists for is still written down')
ok('for every check of' in NOW,
   '  in his own words')

# THE SWITCHES.
ok('[switch]$Resume' in NOW, '-Resume is a switch on the gate')
ok("if ($Resume) { $runArgs += '--resume' }" in NOW,
   '  and reaches the runner')
ok("if ($Force)  { $runArgs += '--force' }" in NOW,
   '-Force still reaches it too')
ok('exit 1' in NOW, 'and a failing suite still stops the push')

# THE LIST STAYS IN ONE PLACE.
ok('$suites = @(' in NOW,
   'the suite list is still kept in the gate, and nowhere else')


# ==========================================================================
head('2. THE RUNNER READS THIS GATE, NOT A COPY OF IT')
# ==========================================================================
import alv_run

names = alv_run.suites_from_ps1(P1)
listed = re.findall(r"'([^']+\.py)'",
                    re.search(r'\$suites\s*=\s*@\((.*?)\n\)', NOW,
                              re.S).group(1))
ok(names == listed,
   'it reads all %d suite(s) out of the gate, in order' % len(names),
   (len(names), len(listed)))
ok(ME in names, '  including this one')
ok(len(names) == len(set(names)),
   '  and no suite is listed twice',
   [n for n in names if names.count(n) > 1][:4])


# ==========================================================================
head('3. THE FOURTEEN THAT MUST NOT SHARE A TREE')
# ==========================================================================
# A suite that plants a defect into a REAL file and restores it cannot
# run beside a suite reading that file. MEASURED on 16 Oct, not assumed:
# test_icon_names passes alone and FAILS beside five others.
ok(len(alv_run.PLANTERS) == 15,
   '%d planter(s) are named - the fourteen measured on 16 Oct, and '
   'this suite, which section 3 below caught writing into the repo '
   'itself' % len(alv_run.PLANTERS))
missing = [n for n in alv_run.PLANTERS if n not in names]
ok(not missing, '  and every one of them is a suite the gate runs',
   missing)

# AND NOTHING OUTSIDE THE LIST HAS STARTED PLANTING.
#
# The list is explicit because a heuristic that silently stops matching
# gives a race nobody can reproduce. But the signature is re-derived
# here, so a suite that starts planting tomorrow is caught today.
import glob
found = []
for f in sorted(glob.glob(os.path.join(ROOT, 'test_*.py'))):
    t = read(f)
    if re.search(r'\bvictim\b', t) or (
            'restore' in t.lower()
            and re.search(r"path_of\([^)]*\)[^\n]{0,40},\s*'w'", t)):
        found.append(os.path.basename(f))
stray = [f for f in found if f not in alv_run.PLANTERS]
ok(not stray,
   'and no suite outside the list carries the planting signature',
   stray)
ok(ME in found and ME in alv_run.PLANTERS,
   '  this suite among them, by its own signature - it was added '
   'because this check found it, not because anybody remembered')


# ==========================================================================
head('4. THE RESUME IS KEYED ON CONTENT, NOT ON A TIMESTAMP')
# ==========================================================================
# THIS IS THE BUG THAT COST THREE CHUNKS. A planter restores a file by
# writing the original back - same bytes, new mtime - so a resume keyed
# on mtime decided the tree had moved on every single run and put 46
# suites back in. Proven here by touching a file and asking.
probe = os.path.join(SCRATCH, 'touched.txt')
with open(probe, 'w', encoding='utf-8') as f:
    f.write('unchanged')
before = alv_run.file_table()
ok(isinstance(before, dict) and len(before) > 100,
   'the runner fingerprints %d file(s) it could read' % len(before))

# A FILE OF THIS SUITE'S OWN, INSIDE THE REPO.
#
# The obvious probe is to rewrite a tracked file with identical bytes
# and a new timestamp. That works, and it makes THIS SUITE a planter -
# a suite that changes the repo while others may be reading it, which
# is exactly the thing section 3 lists fourteen of. It would have had
# to join them, and section 3 caught it.
#
# A dotfile nothing else reads answers the same question and leaves the
# tree alone.
victim = os.path.join(ROOT, '.gt2_timestamp_probe')
with open(victim, 'w', encoding='utf-8') as f:
    f.write('the bytes do not change in this section\n')
base = alv_run.file_table()
body = open(victim, 'rb').read()
st = os.stat(victim)
try:
    with open(victim, 'wb') as f:          # same bytes, new timestamp
        f.write(body)
    os.utime(victim, (st.st_atime, st.st_mtime + 500))
    moved = alv_run.changed_since(base)
    ok(not moved,
       'a file rewritten with IDENTICAL BYTES and a newer timestamp is '
       'not a change', moved[:4])
    with open(victim, 'ab') as f:
        f.write(b'# one byte more\n')
    moved2 = alv_run.changed_since(base)
    ok('.gt2_timestamp_probe' in [m.replace('\\', '/') for m in moved2],
       '  CONTROL: and one byte different IS a change', moved2[:4])
finally:
    if os.path.isfile(victim):
        os.remove(victim)
ok(not os.path.isfile(victim),
   '  and the probe file is gone - this suite leaves the tree as it '
   'found it, which is why it is not one of the fourteen')

ok('as_completed' in read(os.path.join(ROOT, RUNNER)),
   'results are reported as each suite finishes, not in list order - a '
   'slow suite near the front used to hold back every finished one '
   'behind it, and a killed run lost them')
ok('line_buffering' in read(os.path.join(ROOT, RUNNER)),
   'and stdout is line-buffered, so the gate shows progress rather than '
   'nothing for minutes')

# AND THE HOUSE CHECK THIS ROUND TRIPPED OVER IS FIXED.
#
# test_code_only finds the line that sets the import path by asking
# whether the words 'sys.path' and 'insert' are on it - so a COMMENT
# explaining that a file does NOT set the import path matched, and the
# check refused a correct file. Sixth time in two days that something
# read prose instead of structure, and the first time it was the
# house's own tooling rather than a round's gate.
co_src = read(os.path.join(ROOT, 'test_code_only.py'))
ok("if 'sys.path' in ln and 'insert' in ln" not in co_src,
   'test_code_only no longer finds the import path by its WORDS')
ok('insert|append' in co_src and 'split(\'#\')[0]' in co_src,
   '  but by the shape of the call, with comments stripped first')
# ITS OWN BACKUP, READ DIRECTLY. as_gt2_left answers "as GT-2 left it",
# which walks forward to the NEXT round's backup and falls back to a
# LIVE read when there is no next round - so for the newest round it
# returns the file as it is NOW, and a CONTROL built on it can never
# fail. A round's own BEFORE is its own .bak_ file.
_co_bak = os.path.join(ROOT, 'test_code_only.py') + SUFFIX
co_was = read(_co_bak) if os.path.isfile(_co_bak) else ''
ok(not APPLIED or "if 'sys.path' in ln and 'insert' in ln" in co_was,
   'CONTROL: it read the words, until this round')


# ==========================================================================
head('5. IT RUNS THEM, AND GETS THE SAME ANSWERS')
# ==========================================================================
# The claim of this round is that ORDER and CONCURRENCY changed and
# nothing else. Three suites are run both ways and the verdicts compared.
TRIAL = ['test_url_names.py', 'test_icon_names.py', 'test_console_encoding.py']
TRIAL = [t for t in TRIAL if os.path.isfile(os.path.join(ROOT, t))]
if not TRIAL:
    skip('the runner against direct runs', 'no trial suite on disk')
else:
    direct = {}
    for t in TRIAL:
        p = subprocess.run([sys.executable, t], cwd=ROOT,
                           capture_output=True, text=True, timeout=300)
        direct[t] = p.returncode
    log = os.path.join(ROOT, '.alv_run_log.json')
    keep = open(log, 'rb').read() if os.path.isfile(log) else None
    try:
        p = subprocess.run([sys.executable, RUNNER, '--quiet', '--force',
                            '--workers', '3', '--only', ','.join(TRIAL)],
                           cwd=ROOT, capture_output=True, text=True,
                           timeout=600)
        through = p.returncode
    finally:
        if keep is None:
            if os.path.isfile(log):
                os.remove(log)
        else:
            open(log, 'wb').write(keep)
    ok(through == (1 if any(direct.values()) else 0),
       'the runner agrees with running the same %d suite(s) directly: '
       '%s' % (len(TRIAL), ', '.join('%s rc=%s' % (t, r)
                                     for t, r in direct.items())),
       'runner rc=%s' % through)
    ok('planter' in p.stdout or 'pool of' in p.stdout,
       '  and says how it ran them')


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_labellaw' in _r
       and _r.index(SUFFIX) > _r.index('.bak_labellaw'),
       '  and sits after .bak_labellaw', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ok("'%s'" % ME in NOW, '%s runs this suite' % PS1)
ok("Text = 'alv_run.py'" in NOW, 'and holds a sentinel on the call')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
ok(os.path.isfile(os.path.join(ROOT, RUNNER)),
   '%s is on disk - the gate calls it' % RUNNER)

wd = as_gt2_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when GT-2 left it'
   % CONVERTED_NOW)
co = as_gt2_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('')
    print('  WHAT THIS ROUND IS, in one line:')
    print('  The gate ran 360 suites one at a time from a PowerShell')
    print('  loop that could not be tested from here. The loop moved to')
    print('  alv_run.py - parallel, the 14 planters serial, renders')
    print('  first, and -Resume - and the PowerShell is one call.')
sys.exit(1 if failed else 0)
