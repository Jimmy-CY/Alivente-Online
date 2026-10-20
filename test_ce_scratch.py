# -*- coding: utf-8 -*-
"""test_ce_scratch.py - round CE-1, 20 Oct 2026.

A SUITE THAT WRITES INTO THE TREE IT IS BEING RUN AGAINST.

This stopped a push at 290 of 395 with nothing staged:

    FileNotFoundError: ...\\Alivente-Online\\tmpzv3mfgnd.py
    test_code_only.py PASSED alone in 9.5s - the pool was the cause

test_console_encoding wrote a throwaway script into the repository
with dir=ROOT; test_code_only lists the repository for *.py and reads
what it finds. Between the listing and the read, the file was gone.

SECTION 3 REPRODUCES IT RATHER THAN ARGUING ABOUT IT. The probe is
run as a subprocess while this suite watches the directory, and the
claim is that no temporary ever appears in it. Before CE-1 that watch
catches one; after it, there is nothing to catch.

A WATCH CAN MISS. The window is milliseconds wide and a sampler is not
a guarantee - so section 1 asks the stronger question of the source as
well: does ANY file in the tree write a temporary into it. The two
together are worth more than either: one proves the pattern is gone,
the other proves the behaviour is.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Nothing writes a temporary into the tree, the probe
      has a directory of its own, and it is cleaned up.

  2   THE CONTROL. Re-asked of the pre-round file, which did.

  3   WATCHED: run the probe, and look for what it leaves.

  4   Scope, registration and the gate.

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
import re
import subprocess
import sys
import threading
import time

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_cescratch'
ME = 'test_ce_scratch.py'
PATCHER = 'apply_ce_scratch.py'
CE = 'test_console_encoding.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CE-1, 20 Oct 2026'

TARGET = os.path.join(ROOT, CE)
GATE = os.path.join(ROOT, PS1)
FILES = (TARGET,)

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
INTO_TREE = re.compile(r'mk[sd]te?mp\([^)]*dir\s*=\s*ROOT')


def claims(bundle):
    src = T.python_code_only(bundle[TARGET], payloads=True)
    c = {}
    c['THE PROBE WRITES OUTSIDE THE TREE - the finding'] = (
        not INTO_TREE.search(src))
    c['it has a directory of its own'] = (
        'tempfile.mkdtemp(prefix=' in src)
    c['and that directory is removed afterwards'] = (
        '_atexit.register' in src)
    # A ROUND THAT FIXED THE RACE BY DELETING THE PROBE would pass
    # everything above and test nothing at all.
    c['and it still runs the script it is about'] = (
        'subprocess.run' in src)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# THE STRONGER QUESTION, asked of every file rather than this one.
# The watch in section 3 is a sampler; this is not.
writers = []
for name in sorted(n for n in os.listdir(ROOT) if n.endswith('.py')):
    if name in (PATCHER, ME):
        # THIS ROUND'S OWN FILES ARE NOT THE TREE. The patcher holds
        # the pattern as the literal it replaces, and this suite holds
        # it as the thing it searches for. The patcher's own gate
        # refused itself over this before it excluded them.
        continue
    if INTO_TREE.search(T.python_code_only(
            read(os.path.join(ROOT, name)), payloads=True)):
        writers.append(name)
ok(not writers,
   'NO file in the tree writes a temporary into it',
   ', '.join(writers))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TARGET: was(TARGET)}
held = [m for m, got in claims(BEFORE).items() if got]
ok('THE PROBE WRITES OUTSIDE THE TREE - the finding' not in held,
   'CONTROL: before this round it wrote into the repository',
   'what held: %r' % (held,))
OLD = T.python_code_only(BEFORE[TARGET], payloads=True)
ok(bool(INTO_TREE.search(OLD)),
   'CONTROL: with dir=ROOT, in as many words',
   (INTO_TREE.search(OLD) or [''])[0] if INTO_TREE.search(OLD) else '')
ok("suffix='.py'" in OLD,
   'CONTROL: and a .py suffix, which is exactly what test_code_only '
   'lists for')


# ==========================================================================
head('3. WATCHED - RUN THE PROBE AND LOOK AT THE DIRECTORY')
# ==========================================================================
# NOT A PROOF ON ITS OWN. The window is milliseconds wide, so a
# sampler can miss it; that is why section 1 asks the source too. What
# this adds is behaviour: the probe really is run, and really leaves
# nothing.
seen = []
stop = threading.Event()


def watch():
    while not stop.is_set():
        try:
            for n in os.listdir(ROOT):
                if n.startswith('tmp') and n.endswith('.py'):
                    seen.append(n)
        except OSError:
            pass
        time.sleep(0.001)


try:
    before = set(n for n in os.listdir(ROOT) if n.endswith('.py'))
    t = threading.Thread(target=watch)
    t.start()
    r = subprocess.run([sys.executable, CE], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=300)
    stop.set()
    t.join(timeout=5)
    after = set(n for n in os.listdir(ROOT) if n.endswith('.py'))
    print('')
    print('  the probe exited %d' % r.returncode)
    print('  temporaries seen in the tree while it ran: %d %s'
          % (len(set(seen)), sorted(set(seen))[:3]))
    print('  .py files before %d, after %d' % (len(before), len(after)))
    print('')
    ok(r.returncode == 0,
       'the probe still passes - this round moved where it writes, '
       'not what it checks', r.returncode)
    ok(not seen,
       'THE FINDING: nothing of its appeared in the tree while it ran',
       sorted(set(seen))[:5])
    ok(before == after,
       '  and the tree holds exactly the files it held before',
       sorted(after - before) + sorted(before - after))
except Exception as e:
    stop.set()
    skip('the watch', '%s' % str(e)[:70])


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
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
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_ce_scratch as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
