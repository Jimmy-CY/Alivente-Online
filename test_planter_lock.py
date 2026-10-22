# -*- coding: utf-8 -*-
"""test_planter_lock.py - round LK-1, 22 Oct 2026.

A PLANTER KILLED MID-PLANT LEFT A DEFECT ON DISK AND NOTHING NOTICED.

Fifteen suites in this tree write into a real file to prove a detector
catches something, and restore it in a finally. A finally does not run
after a SIGKILL. Logged on 17 October, when that explanation was
proposed for a mismatched backup, fitted the evidence, and turned out
to be untrue - which is why it was logged rather than built.

SECTION 3 REALLY KILLS SOMETHING. It spawns a child that arms the
lock, writes a defect into a file, and then os._exit(9) without
unwinding - no finally, no atexit, no flush. Then recover() is asked
what it finds. A mock would prove that a mock works.

AND IT KILLS A CHILD, NOT THIS PROCESS, and the file it damages is one
this suite made for the purpose. A suite that proved the lock by
leaving real damage in the tree would be the fault it is testing.

IT NAMES AND DOES NOT TOUCH. The lock holds a fingerprint - sha256 per
file - not the bytes. Section 1 refuses any write shape in
alv_plant.py at all, because a tool in this tree that silently rewrote
source files would be a worse thing to own than the problem it fixed.
`git checkout -- <file>` is the fix, and it belongs to whoever can see
whether that file has other work in it.

AND IT CATCHES THE QUIET VERSION. disarm() compares after EVERY
planter, not only after a kill. A planter that completes and restores
imperfectly - a different line ending, one of two victims missed - has
never been checked by anything in this tree.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The module exists, names the damage, writes
      nothing; the runner arms around the PLANTERS list and asks
      before the first suite runs.

  2   THE CONTROL. Re-asked of .bak_planterlock, where the runner
      knew which suites planted and did nothing about it.

  3   DRIVEN. A real child, really killed, and the lock it left.
      Then a clean plant, and a plant that restores imperfectly.

  4   WHAT IT COSTS - asked as a SHAPE. Two fingerprints in a sweep,
      not two per planter; and a virtual environment is skipped by
      its marker, because his is called `code`.

  5   Scope, registration and the gate.

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

import os
import subprocess
import sys
import time

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_planterlock'
ME = 'test_planter_lock.py'
PATCHER = 'apply_planter_lock.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'LK-1, 22 Oct 2026'

RUN = os.path.join(ROOT, 'alv_run.py')
PLANT = os.path.join(ROOT, 'alv_plant.py')
GATE = os.path.join(ROOT, PS1)
FILES = (RUN,)

# THE PROBE. A file this suite makes, damages and removes - never a
# file the application owns. .py so the fingerprint sees it.
PROBE = os.path.join(ROOT, 'alv_plant_probe_lk1.py')
CHILD = os.path.join(ROOT, 'alv_plant_child_lk1.py')

# A TOOL THAT RESTORES SILENTLY IS WORSE THAN THE FAULT IT FIXES.
NO_WRITE = ("open(path, 'w'", 'shutil.copy', 'shutil.move', 'os.replace',
            'subprocess', 'git ', 'os.rename', 'truncate')

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


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)
HAS_PLANT = os.path.isfile(PLANT)
PLANT_SRC = read(PLANT) if HAS_PLANT else ''


def claims(d, plant_src):
    r = T.python_code_only(d[RUN], payloads=True)
    return {
        'there is a module that knows what a planter left':
            'def recover' in plant_src and 'def arm' in plant_src,
        '  and it fingerprints rather than copies':
            'sha256' in plant_src,
        'the runner asks it before any suite runs':
            'alv_plant.recover()' in r,
        '  and arms it around the planters':
            'alv_plant.arm(' in r and 'def planting' in r,
        '  clearing it afterwards, so a kill is what leaves one':
            'alv_plant.disarm(' in r,
        'and a planter that did not put a file back stops the run':
            'did not put back' in r,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
ok(HAS_PLANT, 'alv_plant.py is on disk - this round brings it')
for msg, got in claims(NOW, PLANT_SRC).items():
    ok(got, msg)

R = T.python_code_only(NOW[RUN], payloads=True)
_rec = R.find('alv_plant.recover()')
_ser = R.find('for outcome in planting(')
ok(0 <= _rec < _ser,
   'the recovery runs BEFORE the first suite - a tree that is wrong is '
   'wrong for suite 1 as much as for suite 421', (_rec, _ser))
ok('planting(plant, run_one)' in R,
   'the lock is armed around the PLANTERS list as a phase, so all '
   'sixteen are covered and the seventeenth is covered the day it '
   'joins - and they share two fingerprints rather than paying for '
   'thirty-two')
ok('PLANTERS' in R and 'def planting' in R,
   '  and no suite needed an edit of its own - fifteen bespoke edits '
   'in fifteen shapes would be fifteen chances to get one wrong')

if HAS_PLANT:
    P = T.python_code_only(PLANT_SRC, payloads=True)
    for shape in NO_WRITE:
        ok(shape not in P,
           'alv_plant.py does not name %r' % shape)
    ok('json.dump' in P,
       'the one thing it writes is its own lock')
    ok("'.bak_' in name" in P,
       'and the fingerprint skips backups - a round record is not a '
       'planter victim, and they change for ordinary reasons')
else:
    skip('what the module may do', 'alv_plant.py is not here')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE, '').items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

OLDR = T.python_code_only(BEFORE[RUN], payloads=True)
ok('PLANTERS' in OLDR,
   'CONTROL: the runner already KNEW which suites write into the tree')
ok('alv_plant' not in OLDR,
   'CONTROL: and did nothing whatever about one being killed')
ok('plant = [n for n in todo if n in PLANTERS]' in OLDR,
   'CONTROL: it used the list only to decide the order they ran in')


# ==========================================================================
head('3. DRIVEN - A CHILD, REALLY KILLED')
# ==========================================================================
if not HAS_PLANT:
    skip('section 3', 'alv_plant.py is not here')
else:
    import alv_plant

    # ITS OWN LOCK, NOT THE REAL ONE. This suite is on the PLANTERS
    # list - test_gate_speed caught it writing into the repo, which is
    # how test_gate_speed itself got there - so alv_run has the REAL
    # lock armed around this very run. Arming over it would make the
    # suite destroy the lock that is watching the suite, and a kill
    # after that would leave nothing behind. One line: it drives its
    # own lock file and section 5 checks the real one is untouched.
    REAL_LOCK = alv_plant.LOCK
    real_before = os.path.isfile(REAL_LOCK)
    alv_plant.LOCK = os.path.join(ROOT, '.alv_plant_lock_lk1_probe.json')

    def clean():
        for p in (PROBE, CHILD):
            if os.path.isfile(p):
                os.remove(p)
        alv_plant.release()
        if os.path.isfile(alv_plant.LOCK):
            os.remove(alv_plant.LOCK)

    clean()
    try:
        # ---- THE PROBE EXISTS FIRST, so the damage below is a CHANGE
        #      to a file the fingerprint already knows, which is the
        #      shape a real planter produces. A file that merely
        #      appeared would test the easy half.
        with open(PROBE, 'w', encoding='utf-8') as fh:
            fh.write('# LK-1 probe - whole\nWHOLE = True\n')

        # ---- A CHILD THAT ARMS, DAMAGES, AND DIES WITHOUT UNWINDING.
        #      os._exit, not sys.exit: no finally, no atexit, no flush.
        #      That is what a SIGKILL looks like from the inside, and
        #      it is what no planter's finally survives.
        with open(CHILD, 'w', encoding='utf-8') as fh:
            fh.write(
                'import os, sys\n'
                'sys.path.insert(0, %r)\n'
                'import alv_plant\n'
                # THE CHILD DRIVES THE PROBE LOCK TOO. A fresh import
                # would take the real path and the child would arm the
                # lock alv_run has open around this suite.
                'alv_plant.LOCK = %r\n'
                'alv_plant.arm("test_planter_lock.py (the child)")\n'
                'open(%r, "w", encoding="utf-8").write('
                '"# LK-1 probe - PLANTED\\nWHOLE = False\\n")\n'
                'os._exit(9)\n' % (ROOT, alv_plant.LOCK, PROBE))
        p = subprocess.run([sys.executable, CHILD], cwd=ROOT,
                           capture_output=True, timeout=120)
        ok(p.returncode == 9,
           'the child died without unwinding - rc %s, which is os._exit '
           'and not sys.exit' % p.returncode, p.returncode)
        ok('PLANTED' in read(PROBE),
           '  and left the defect in the file, exactly as a killed '
           'planter does')

        left = alv_plant.recover()
        ok(left is not None,
           'THE LOCK IS STILL THERE after the kill - which is the whole '
           'mechanism: it is written before and cleared after')
        if left is not None:
            suite, changed, vanished, appeared = left
            ok('child' in suite,
               '  and it names the suite that was planting - %r' % suite)
            rel = os.path.basename(PROBE)
            ok(any(rel in c for c in changed),
               '  AND NAMES THE FILE IT DAMAGED - %r' % (changed,),
               changed)
            ok(len(changed) == 1 and not vanished and not appeared,
               '  and names nothing else - one file, and it is the '
               'right one', (changed, vanished, appeared))

        # ---- IT RESTORED NOTHING, which is the design.
        ok('PLANTED' in read(PROBE),
           'and the file is STILL damaged - this names the damage and '
           'does not touch it, because a tool that rewrote source '
           'silently is worse than the fault')

        # ---- PUT IT BACK BY HAND, as the operator would, and ask
        #      again.
        with open(PROBE, 'w', encoding='utf-8') as fh:
            fh.write('# LK-1 probe - whole\nWHOLE = True\n')
        again = alv_plant.recover()
        ok(again is not None and not again[1] and not again[2]
           and not again[3],
           'ONCE THE FILE IS BACK the same lock reports nothing - so '
           'the runner clears it and carries on rather than refusing '
           'for ever', again)
        alv_plant.release()

        # ---- A PLANTER THAT BEHAVES LEAVES NOTHING.
        print('')
        armed = alv_plant.arm('a well-behaved planter')
        original = read(PROBE)
        with open(PROBE, 'w', encoding='utf-8') as fh:
            fh.write('# LK-1 probe - PLANTED\nWHOLE = False\n')
        with open(PROBE, 'w', encoding='utf-8') as fh:
            fh.write(original)
        ch, va, ap = alv_plant.disarm('a well-behaved planter', armed)
        ok(not ch and not va and not ap,
           'A PLANTER THAT PUTS THE FILE BACK leaves nothing for disarm '
           'to report', (ch, va, ap))
        ok(not os.path.exists(alv_plant.LOCK),
           '  and the lock is gone, so the next run finds nothing')

        # ---- AND THE QUIET VERSION: a planter that completes and
        #      restores IMPERFECTLY. Nothing in this tree checked that
        #      before, and no finally would have caught it.
        armed = alv_plant.arm('a careless planter')
        with open(PROBE, 'w', encoding='utf-8') as fh:
            fh.write(original.replace('\n', '\r\n'))
        ch, va, ap = alv_plant.disarm('a careless planter', armed)
        ok(len(ch) == 1 and os.path.basename(PROBE) in ch[0],
           'A PLANTER THAT RESTORES A DIFFERENT LINE ENDING IS CAUGHT - '
           'it completed, its finally ran, and the file is still not '
           'what it was', (ch, va, ap))

        # ---- AND ONE THAT DELETES ITS VICTIM.
        armed = alv_plant.arm('a destructive planter')
        os.remove(PROBE)
        ch, va, ap = alv_plant.disarm('a destructive planter', armed)
        ok(len(va) == 1 and os.path.basename(PROBE) in va[0],
           'AND A PLANTER THAT DELETES ITS VICTIM is named too',
           (ch, va, ap))
    finally:
        clean()

    ok(not os.path.isfile(PROBE) and not os.path.isfile(CHILD),
       'the probe and the child are gone - this suite leaves nothing '
       'in the tree, which is the fault it exists to test')
    ok(not os.path.exists(alv_plant.LOCK),
       'and so is the probe lock')
    # AND THE REAL ONE IS AS IT WAS. If alv_run armed it around this
    # suite it is still armed; if it did not, it is still absent.
    ok(os.path.isfile(REAL_LOCK) == real_before,
       'and the REAL lock is exactly as this suite found it - %s'
       % ('armed' if real_before else 'absent'))
    alv_plant.LOCK = REAL_LOCK


# ==========================================================================
head('4. WHAT IT COSTS')
# ==========================================================================
if not HAS_PLANT:
    skip('section 4', 'alv_plant.py is not here')
else:
    t0 = time.time()
    fp = alv_plant.fingerprint()
    secs = time.time() - t0
    ok(len(fp) > 500,
       'the fingerprint covers %d files' % len(fp), len(fp))

    # THE SHAPE, NOT THE SECONDS. The first spelling of this section
    # asserted one fingerprint under a second - a number measured in
    # the mirror, which holds 1,395 files. Demetri's laptop holds 8,392
    # and took 3.26s, and HIS GATE caught it. That is the 22 October
    # lesson twice in one week: a measurement with no headroom is a
    # coin toss, and a ceiling taken off one machine is a claim about
    # that machine.
    #
    # So what is asked is the thing that is true on every machine:
    # TWO fingerprints in a sweep, not two per planter. Sixteen
    # planters made that the difference between 6 seconds and 97 on
    # his.
    import alv_run
    src = read(os.path.join(ROOT, 'alv_run.py'))
    code = T.python_code_only(src, payloads=True)
    ok(code.count('alv_plant.arm(') == 1,
       'the lock is armed ONCE in a sweep, not once per planter',
       code.count('alv_plant.arm('))
    ok(code.count('alv_plant.disarm(') == 1,
       '  and cleared once', code.count('alv_plant.disarm('))
    ok(len(alv_run.PLANTERS) >= 15,
       '  which is %d planters sharing two fingerprints instead of '
       'paying for %d' % (len(alv_run.PLANTERS),
                          2 * len(alv_run.PLANTERS)))
    print('       one fingerprint here: %d files, %.2fs - so the whole '
          'mechanism' % (len(fp), secs))
    print('       costs about %.1fs of a sweep that takes twenty-nine '
          'minutes.' % (secs * 2))

    # AND A CEILING WITH REAL HEADROOM ON THE BIGGER OF THE TWO TREES.
    # 3.26s was his worst case BEFORE the virtual environment came out
    # of the walk; sixty seconds for the whole mechanism is 9x that and
    # still 3% of a sweep. A later round that makes this genuinely
    # expensive fails here rather than in the sweep.
    ok(secs * 2 < 60.0,
       'and the whole mechanism costs %.1fs, well inside the sixty '
       'that would make it worth noticing' % (secs * 2), secs)

    # A VIRTUAL ENVIRONMENT IS NOT SOURCE, AND IT IS NOT CALLED venv.
    # Demetri's lives in a directory called `code`. Driven, because a
    # skip list of names passed every reading of the code and hashed
    # 7,000 files in site-packages anyway.
    import shutil
    import tempfile
    env = os.path.join(ROOT, 'alv_plant_env_lk1')
    try:
        os.makedirs(os.path.join(env, 'Lib'), exist_ok=True)
        # encoding NAMED, both of them. test_console_encoding refuses a
        # text open that does not, and these two were written in the
        # 22 October correction without it - caught by test_ce_scratch,
        # which runs that suite as a probe and reported it exiting 1.
        with open(os.path.join(env, 'pyvenv.cfg'), 'w',
                  encoding='utf-8') as fh:
            fh.write('home = somewhere\n')
        with open(os.path.join(env, 'Lib', 'pretend_package.py'), 'w',
                  encoding='utf-8') as fh:
            fh.write('# site-packages, not source\n')
        after = alv_plant.fingerprint()
        inside = [p for p in after if p.startswith('alv_plant_env_lk1')]
        ok(not inside,
           'A DIRECTORY HOLDING pyvenv.cfg IS SKIPPED whatever it is '
           'called - his is called `code`, and a skip list of names '
           'walked into it', inside[:4])
        ok(len(after) == len(fp),
           '  so the count does not move when one appears - %d and %d'
           % (len(fp), len(after)))
        ok('pyvenv.cfg' in PLANT_SRC,
           '  asked of the MARKER rather than of a name, which is the '
           'only version that survives the next machine')
    finally:
        shutil.rmtree(env, ignore_errors=True)

    ok('.alv_run_log.json' not in fp,
       'and it ignores the run log, which is rewritten after every '
       'suite by design')
    ok(not [p for p in fp if '.bak_' in p],
       'and every backup in the tree', len([p for p in fp
                                            if '.bak_' in p]))


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ok(not os.path.isfile(PLANT + SUFFIX),
   'alv_plant.py has NO backup, because this round created it - and '
   'the patcher declares that in CREATES rather than leaving the '
   'pre-flight to find a file it cannot pair')

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
ok('def recover' in gate, 'the sentinel is on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_planter_lock as PATCH                          # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == ('alv_plant.py',),
   'and declares the one file it creates', PATCH.CREATES)


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that it can put a file back. It deliberately cannot.')
print('  It names the file; git checkout puts it back, run by')
print('  somebody who can see whether that file has other work in')
print('  it. A tool here that rewrote source silently would be a')
print('  worse thing to own than the fault.')
print('')
print('  Not that a planter has ever been killed. None has, as far')
print('  as anybody knows - which is exactly the state in which a')
print('  thing like this gets built, rather than after a day lost')
print('  to diagnosing the wrong file.')
print('')
print('  Not that the fifteen planters are the only writers. The')
print('  list is explicit and test_gate_speed re-derives the')
print('  signature, so a sixteenth that starts planting fails')
print('  there first. That is the guard this one leans on.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
