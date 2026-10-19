# -*- coding: utf-8 -*-
"""test_gate_serial.py - round GS-1, 19 Oct 2026.

RELEASE 3, PUSH 3. A RESCUE CANNOT UNDO A STOP.

Demetri's gate has stopped at about 262 of 377 suites on three pushes
in a row, printed "the sweep stopped early", and asked him to run it
again with --resume. Twenty minutes of his time per push.

The suite is test_print_queries.py. Measured here today: 137s alone,
19 of 19 passed; 530s in a pool of six, a failed check. It boots
Django and counts queries, and a query count taken while five other
workers are also booting Django is a number about the machine.

WHY THE EXISTING RESCUE DOES NOT ALREADY FIX IT. AR-1 re-runs every
pool failure alone and clears the ones that pass, and it rescues this
suite on every push. But without --force the pool CANCELS every future
still queued the moment one fails, so phase 3 runs over a sweep that
already gave up. The rescue explains the stop. It cannot give the
hundred and fifteen cancelled suites back.

GS-1 adds one list, CONTENDED, and keeps it SEPARATE from PLANTERS on
purpose: a planter runs alone because it WRITES, and these run alone
because their VERDICT moves with the load. Different faults, different
remedies, and the next person deciding where a new suite belongs has
to answer which one they have.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. CONTENDED is a real module-level list - parsed, not
      string-matched - holding exactly the measured name. Phase 1
      prints its two reasons separately. Phase 3 is untouched.

  2   THE CONTROL. Every claim re-asked of alv_run.py as it was before
      this round, where there is no CONTENDED and the suite is pooled.

  3   RUN, TWICE, AGAINST A REAL RUNNER. The whole mechanism, built
      small in a temp directory: nine probe suites, one of which fails
      only when others are running beside it - which is the real fault,
      modelled. In the pool it fails and takes the sweep down with it.
      In CONTENDED it passes and all nine run. Two processes, two
      exit codes, nothing asserted from reading the source.

  4   WIDE. Every suite in the gate asked whether it carries the
      contended signature while sitting outside the list - the way
      test_gate_speed does for the planters.

  5   Scope, registration and the gate.

NOTHING HERE IS WRITTEN INTO THE REPO. Section 3's probes live in a
temp directory that is removed afterwards, which is the one reason
this suite is NOT a planter and must not become one.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_gateserial'
ME = 'test_gate_serial.py'
PATCHER = 'apply_gate_serial.py'
PS1 = 'Push-PendingChanges.ps1'
RUNNER = 'alv_run.py'
MARK = 'GS-1, 19 Oct 2026'
SLOW = ['test_print_buttons.py', 'test_print_queries.py']

RUN = os.path.join(ROOT, RUNNER)
GATE = os.path.join(ROOT, PS1)
FILES = (RUN,)

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
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def listed(src, name):
    """A module-level list, PARSED out of the source.

    Asked of the syntax tree and never of a substring, because a
    comment that mentions CONTENDED is not a CONTENDED - that
    confusion has cost this project five repairs in two days."""
    for node in ast.parse(src).body:
        if (isinstance(node, ast.Assign)
                and any(getattr(t, 'id', '') == name for t in node.targets)
                and isinstance(node.value, ast.List)):
            return [e.value for e in node.value.elts
                    if isinstance(e, ast.Constant)]
    return None


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = read(RUN)
APPLIED = 'CONTENDED = [' in NOW


# ==========================================================================
head('1. THE SOURCE - ONE LIST, AND IT IS A LIST')
# ==========================================================================
contended = listed(NOW, 'CONTENDED')
ok(contended is not None,
   'alv_run.py declares CONTENDED as a module-level list - parsed out '
   'of the syntax tree, not found as a string')
ok(contended == sorted(SLOW),
   '  and it holds exactly the names that were MEASURED: %s'
   % ', '.join(SLOW), 'got %r' % (contended,))

# THE MEASUREMENT IS IN THE FILE. A list of names with no numbers
# beside them is a list nobody can audit later - the next reader has
# to be able to ask whether the reason still holds.
ok('137s alone' in NOW and '530s in a pool of six' in NOW,
   '  and test_print_queries cites what put it there - 137s alone '
   'against 530s in a pool of six')
# THE SECOND NAME WAS FOUND BY PHASE 3, which is the point of leaving
# phase 3 alone. It timed out at 313 of 380 on the first sweep after
# this round was written, and passed alone in 204s - and without
# --force that timeout stops the sweep and costs a --resume, the same
# twenty minutes from a different suite.
ok('204s alone' in NOW and 'TIMED OUT in a pool of six' in NOW,
   '  and test_print_buttons cites its own - 204s alone against a '
   'timeout in a pool of six')
ok('test_picker_grid.py is NOT here' in NOW,
   '  and the list records what it REFUSED as well: a suite that '
   'failed one pool, passed the next and runs alone in 14s is a light '
   'suite having a bad moment, not a contended one')

# THE TWO REASONS ARE KEPT APART.
ok('a SECOND reason to run alone' in NOW,
   'the list says why it is not the planters list')
planters = listed(NOW, 'PLANTERS')
ok(planters is not None
   and not [s for s in SLOW if s in planters],
   '  and neither was quietly filed as a planter - they do not write '
   'into anything')
ok(planters is not None and len(planters) == 15,
   '  the fifteen planters are untouched; this round adds a reason, it '
   'does not re-file the old one',
   '%s planter(s)' % (len(planters) if planters else '?'))

# PHASE 1 SAYS BOTH THINGS, SEPARATELY.
ok('%d planter(s) - they write into real files' in NOW,
   'phase 1 names the planters by their own reason')
ok('%d contended - they pass alone and fail in a ' in NOW,
   '  and the contended by theirs, in a second line - one number for '
   'both would teach the next reader there is one kind of suite here')

# PHASE 3 IS THE INSTRUMENT THAT FINDS THE NEXT ONE. A round that
# used its reading and then removed it would be taking the thermometer
# away while quoting the temperature.
for keep, why in (
        ('died.append', 'a pool failure is still remembered'),
        ('Re-running each', '  and every failure is still re-run alone'),
        ('rescued.append', '  and a rescue is still named in the summary'),
        ('failed.remove(', '  and a suite that passes alone still stops '
                           'counting as failed'),
        ('the sweep stopped early', '  and a rescue over a stopped sweep '
                                    'is still not called green')):
    ok(keep in NOW, '%s' % why)
ok('too heavy to share a machine' in NOW,
   '  and the line that will name the NEXT member of CONTENDED is '
   'still printed')

# THE FILE'S OWN DESCRIPTION OF ITSELF MOVED WITH IT.
doc = ast.get_docstring(ast.parse(NOW)) or ''
ok('AND SO DOES ANYTHING WHOSE VERDICT MOVES WITH THE LOAD' in doc,
   "alv_run's own docstring no longer says the planters are the only "
   'reason to leave the pool')


# ==========================================================================
head('2. THE CONTROL - THE SAME QUESTIONS, ASKED OF THE BACKUP')
# ==========================================================================
# EVERY CLAIM, RE-ASKED. Not a sample. The 17 Oct push shipped a round
# whose control section never ran, and the rule since is that a
# round proves what it changed by asking the before.
BEFORE = was(RUN)
ok(listed(BEFORE, 'CONTENDED') is None,
   'CONTROL: before this round there was no CONTENDED list at all')
ok('137s alone' not in BEFORE,
   'CONTROL: and no measurement recorded for it')
ok('%d contended - they pass alone and fail in a pool' not in BEFORE,
   'CONTROL: and phase 1 printed one reason, because there was one')
bp = listed(BEFORE, 'PLANTERS')
ok(bp == planters,
   'CONTROL: the planters are byte-for-byte the same list before and '
   'after - %d names' % len(bp or []),
   '%r != %r' % (bp, planters))

# AND THE SUITE REALLY WAS IN THE POOL. Asked by running the BEFORE
# file's own split against the real suite list, not by reading it.
bsplit = re.search(r'rest = \[n for n in todo if n not in PLANTERS\]',
                   BEFORE)
ok(bsplit is not None,
   'CONTROL: before this round the pool was everything that was not a '
   'planter - so %s was in it' % SLOW)

# THE COST WAS REAL AND IT IS WRITTEN DOWN.
ok('f2.cancel()' in BEFORE,
   'CONTROL: and the pool cancelled its queued futures on the first '
   'failure, both before this round and after it - that is the '
   'mechanism GS-1 routes around rather than removes')
ok('f2.cancel()' in NOW, '  still true after')


# ==========================================================================
head('3. RUN IT - A REAL RUNNER, A REAL POOL, TWO EXIT CODES')
# ==========================================================================
# THE WHOLE MECHANISM, BUILT SMALL. Nine probe suites in a temp
# directory. Eight are cheap and hold a marker file while they run.
# The ninth sleeps briefly and then FAILS IF ANY MARKER IS PRESENT -
# which is test_print_queries' real behaviour, modelled: a verdict
# that is about the machine and not about the tree.
#
# Run A puts it in the pool, where the eight are running beside it.
# Run B puts it in CONTENDED, where it runs first and alone.
#
# NOTHING IS WRITTEN INTO THE REPO. That is deliberate and it is why
# this suite is not a planter - test_gate_speed became one by writing
# a probe into the tree, and that was the right call for what it
# needed to prove. This needs a whole runnable directory, so it builds
# one somewhere else.
SLOWP = 'test_gs1_probe_a_slow.py'
CHEAP = ['test_gs1_probe_z%d.py' % i for i in range(1, 9)]

# THE SIBLING COUNT RIDES ON THE TALLY LINE. The runner is called with
# --quiet, which prints only the line containing "passed," - so a
# finding on its own line is swallowed. A probe that reports into a
# channel nobody reads is a probe that proves nothing.
PROBE_SLOW = '''import glob, os, sys, time
d = os.path.dirname(os.path.abspath(__file__))
time.sleep(0.6)
busy = glob.glob(os.path.join(d, '.gs1_running_*'))
print('%d passed, %d failed, 0 skipped  (%d sibling(s) running beside me)'
      % (0 if busy else 1, 1 if busy else 0, len(busy)))
sys.exit(1 if busy else 0)
'''

PROBE_CHEAP = '''import os, sys, time
d = os.path.dirname(os.path.abspath(__file__))
m = os.path.join(d, '.gs1_running_%d' % os.getpid())
open(m, 'w').write('x')
try:
    time.sleep(1.8)
finally:
    try:
        os.remove(m)
    except OSError:
        pass
print('1 passed, 0 failed, 0 skipped')
sys.exit(0)
'''


def build(tmp, contend):
    """A runnable copy of the runner, with its own tiny $suites."""
    shutil.copy(RUN, os.path.join(tmp, RUNNER))
    src = read(os.path.join(tmp, RUNNER))
    # THE LIST IS REPLACED, THE RUNNER IS NOT REWRITTEN. The code
    # under test is the code that shipped.
    src = re.sub(r'CONTENDED = \[\n(?:.*\n)*?\]',
                 'CONTENDED = %r' % (contend,), src, count=1)
    src = re.sub(r'PLANTERS = \[\n(?:.*\n)*?\]',
                 'PLANTERS = []', src, count=1)
    with open(os.path.join(tmp, RUNNER), 'w', encoding='utf-8') as f:
        f.write(src)
    names = [SLOWP] + CHEAP
    with open(os.path.join(tmp, PS1), 'w', encoding='utf-8') as f:
        f.write('$suites = @(\n%s\n)\n'
                % ',\n'.join("    '%s'" % n for n in names))
    with open(os.path.join(tmp, SLOWP), 'w', encoding='utf-8') as f:
        f.write(PROBE_SLOW)
    for n in CHEAP:
        with open(os.path.join(tmp, n), 'w', encoding='utf-8') as f:
            f.write(PROBE_CHEAP)
    return names


def sweep(contend):
    tmp = tempfile.mkdtemp(prefix='gs1_')
    try:
        names = build(tmp, contend)
        p = subprocess.run([sys.executable, RUNNER, '--quiet',
                            '--workers', '6'],
                           cwd=tmp, capture_output=True, text=True,
                           timeout=240)
        ran = len(re.findall(r'^  == \[', p.stdout, re.M))
        return p.returncode, p.stdout, ran, len(names)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


try:
    rcA, outA, ranA, totA = sweep([])
    rcB, outB, ranB, totB = sweep([SLOWP])
    BUILT = True
except Exception as e:                                    # pragma: no cover
    BUILT = False
    skip('the runner could not be exercised in a temp directory',
         str(e)[:90])

if BUILT:
    print('')
    print('   RUN A - the probe in the pool, with eight running beside it')
    ok(rcA != 0,
       '  the sweep FAILS: a verdict reached under load is not a '
       'verdict about the tree', 'rc=%s' % rcA)
    ok('stopped early' in outA,
       '  and it says so - "the sweep stopped early"')
    ok(ranA < totA,
       '  and %d of %d suite(s) ran. The rest were cancelled by the '
       'one failure, which is the twenty minutes.' % (ranA, totA),
       outA[-400:] if ranA >= totA else '')
    ok('PASSED alone' in outA,
       "  phase 3 then rescued it, proving the pool was the cause - "
       'and the sweep was already over')

    print('')
    print('   RUN B - the same probe, the same eight, one list entry')
    ok(rcB == 0,
       '  the sweep PASSES', 'rc=%s\n%s' % (rcB, outB[-500:]))
    ok(ranB == totB,
       '  and all %d of %d suite(s) ran' % (ranB, totB),
       outB[-400:] if ranB != totB else '')
    ok('1 contended' in outB,
       '  the runner named it as contended, in its own line')
    ok('0 sibling(s) running beside me' in outB,
       '  and the probe itself reports nothing was running beside it - '
       'which is the whole of the fix')
    ok('stopped early' not in outB,
       '  nothing stopped early, so there is no --resume to run')
    ok('PASSED alone' not in outB,
       '  and phase 3 was never needed: a suite that does not fail is '
       'not a suite that has to be rescued')


# ==========================================================================
head('4. THIS LIST CANNOT BE DERIVED - SO THE ENTRY FEE IS EVIDENCE')
# ==========================================================================
# test_gate_speed RE-DERIVES the planter list: a planter writes into a
# real file and puts it back, and that leaves a signature in the
# source, so a suite that starts planting while outside the list is
# caught. The first draft of this section tried the same trick and it
# was wrong twice over - it matched four innocent suites and MISSED
# the one name in the list.
#
# Because being contended is not a property of the source. It is an
# empirical fact about a machine. Measured here while writing this:
#
#   262 of the 377 suites launch a browser, so "renders" does not
#   discriminate. test_print_queries drives Chromium over 76 pages at
#   several widths - but it does it through a loop over a census, so
#   the static call count is five, lower than suites that are not slow
#   at all.
#
# There is no honest regex for "this verdict moves with the load", and
# a dishonest one is worse than none: a signature that quietly stops
# matching gives you a race nobody can reproduce, which is the exact
# sentence the PLANTERS list already carries.
#
# SO THE GUARD IS NOT DERIVATION, IT IS EVIDENCE. A name may only be
# in CONTENDED if the measurement that put it there is written beside
# it. That makes the list auditable by the next reader, who can ask
# whether the reason still holds - and it makes adding a name on a
# hunch fail this suite.
every = []
try:
    m = re.search(r'\$suites\s*=\s*@\((.*?)\n\)', read(GATE), re.S)
    every = re.findall(r"'([^']+\.py)'", m.group(1)) if m else []
except Exception:
    pass

ok(every and all(n in every for n in (contended or [])),
   'every name in CONTENDED is a suite the gate actually runs - '
   'a list about a suite nobody runs is a list about nothing',
   'missing from $suites: %s'
   % ', '.join(n for n in (contended or []) if n not in every))
ok(all(os.path.isfile(os.path.join(ROOT, n)) for n in (contended or [])),
   '  and is on disk')

both = sorted(set(contended or []) & set(planters or []))
ok(not both,
   'no suite is in BOTH lists - they are fixed by different things, a '
   'planter by a quiet tree and these by a quiet machine, and a name '
   'in both would be filed by whichever reason was noticed first',
   'in both: %s' % ', '.join(both))

# THE ENTRY FEE. For each name, a comment line carrying that name and
# a duration - the reading that justified the entry.
block = NOW[:NOW.find('CONTENDED = [')]
block = block[block.rfind('\n\n# THE CONTENDED'):]
for n in (contended or []):
    cited = [ln for ln in block.split('\n')
             if n in ln and re.search(r'\d+s\b', ln)]
    ok(bool(cited),
       '%s cites the measurement that put it in the list' % n,
       'no comment line above CONTENDED names it with a duration')
    nums = re.findall(r'(\d+)s\b', block)
    ok(len(nums) >= 2 and max(int(x) for x in nums)
       > min(int(x) for x in nums) * 2,
       '  and the two readings differ by more than a factor of two - '
       '%s against %s' % (max(nums, key=int) + 's',
                          min(nums, key=int) + 's'),
       'readings found: %s' % ', '.join(nums))

# AND THE INSTRUMENT THAT WILL FIND THE NEXT ONE IS NAMED IN THE FILE,
# because a list that cannot be derived has to say how it IS grown.
ok('Phase 3 is deliberately LEFT ALONE' in NOW,
   'the list says where the next name will come from: phase 3, which '
   'is the only thing in the project that measures this property')


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# WHAT THIS ROUND MAY TOUCH. alv_run decides order; it must not have
# acquired an opinion about what a suite CLAIMS.
#
# ENUMERATED FROM THE BACKUPS ON DISK, NEVER TYPED - the standing rule.
# alv_tree.touched_by walks the TEMPLATE roots, which is right for a
# round that moves markup and blind to one that only moves tooling:
# it answered 0 here and the check passed by seeing nothing. So this
# round asks the repo root, which is where its five backups are.
touched = sorted(f[:-len(SUFFIX)] for f in os.listdir(ROOT)
                 if f.endswith(SUFFIX))
allowed = {RUNNER, PS1, 'alv_tree.py', 'alv_rounds.py',
           'test_waiting_down.py'}
ok(len(touched) == 5,
   'five backups are on disk, counted and not typed - %s'
   % ', '.join(touched),
   '%d found' % len(touched))
extra = set(touched) - allowed
ok(not extra,
   '  and every one of them is the runner or the register',
   'unexpected: %s' % ', '.join(sorted(extra)))

ok('.bak_gateserial' in __import__('alv_rounds').ROUNDS,
   'alv_rounds knows the round')
ok(ME in T.CONVERTED, 'alv_tree knows this suite')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the gate runs this suite')
ok(all("'%s'" % s in gate for s in SLOW),
   '  and still runs both suites this round moved - GS-1 changes WHEN '
   'they run, never WHETHER')
ok('CONTENDED = [' in gate and 'Only this list prevents it' in gate,
   'both sentinels are pinned in the gate')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))

# NOT ONE CLAIM MOVED. The suite this round re-files must be exactly
# the file it was; GS-1 is about order and concurrency, which is
# GT-2's sentence and still the rule.
ok(not [s for s in SLOW
        if os.path.isfile(os.path.join(ROOT, s) + SUFFIX)],
   'neither suite was EDITED by this round - they are run '
   'differently, not written differently')


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  A RESCUE CANNOT UNDO A STOP. AR-1 re-runs every pool failure')
print('  alone and has rescued test_print_queries on every push since')
print('  17 October. It was never enough: the pool cancels the rest of')
print('  the sweep before phase 3 begins, so the rescue buys an')
print('  explanation and not a swept tree.')
print('')
print('  262 OF 377, THREE PUSHES RUNNING, and a --resume each time.')
print('  One list entry, and section 3 ran both halves of it against a')
print('  real runner: nine probes, one that fails only with company.')
print('  In the pool it failed and took the sweep with it. In')
print('  CONTENDED it passed and all nine ran.')
print('')
print('  PHASE 3 STAYS. It is the instrument that found this name and')
print('  it is how the next one will be found - the summary already')
print('  says so, and today is the first time anyone acted on it.')
print('=' * 74)
sys.exit(1 if failed else 0)
