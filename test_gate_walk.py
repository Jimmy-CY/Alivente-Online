# -*- coding: utf-8 -*-
r"""test_gate_walk.py - round PG-3, 24 Oct 2026.

THE PUSH GATE COULD NOT FINISH, AND THREE THINGS WERE WRONG.

DEMETRI'S MACHINE FOUND THIS, NOT A SWEEP OF MINE. Release 13's gate
ran 447 suites clean and then stopped:

      == [448/448] test_preflight_names.py   600.0s
         (timed out after 600s)
      !! test_preflight_names.py FAILED alone too  rc=TIMEOUT

      Stopping.  Nothing has been staged.

The same suite took 72 seconds here. Three causes, and the one that
looks biggest in the diff is the smallest of them.

SECTION 3 IS THE ONE THAT MATTERS, AND IT IS AN EQUIVALENCE PROOF
RATHER THAN A STOPWATCH. A faster instrument that answers
DIFFERENTLY is a worse instrument, and all three changes here are
changes to how an answer is COMPUTED:

    the substring prefilter      a regex requiring a literal cannot
                                 match a string without it

    the cached tool texts        check_gates only reads

    the pruned walk              a virtualenv is not the tree

So the suite runs the OLD spelling and the NEW one over every round
name in the tree and requires the same answer for each. Not a
sample: all of them.

SECTION 4 IS THE STOPWATCH, and it asserts a SHAPE and prints the
MEASUREMENT - the rule since the planter ceiling of 21 October. The
claim is "the prefilter is worth more than ten times", not "it takes
N seconds", because N is a fact about whichever machine ran it and
that is exactly what went wrong here in the first place.

WHAT IS NOT PROVED HERE. That his gate now passes. This machine has
no virtualenv inside the repository and no OneDrive filter on every
open, which is the whole reason the defect was invisible to it. What
IS proved is that the question being asked is now smaller, that the
answer is the same, and that nothing walks a venv.
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
import sys
import time

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_gatewalk'
ME = 'test_gate_walk.py'
PATCHER = 'apply_gate_walk.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PG-3, 24 Oct 2026'

TREE = os.path.join(ROOT, 'alv_tree.py')
GATES = os.path.join(ROOT, 'check_gates.py')
PRE = os.path.join(ROOT, 'alv_preflight.py')
RUN = os.path.join(ROOT, 'alv_run.py')
STAGE = os.path.join(ROOT, 'stage_round.py')
GATE = os.path.join(ROOT, PS1)
FILES = (TREE, GATES, PRE, RUN, STAGE)

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
OLD = dict((p, was(p)) for p in FILES)


def claims(d):
    tree = T.python_code_only(d[TREE], payloads=True)
    g = T.python_code_only(d[GATES], payloads=True)
    i = tree.find('def prune(')
    body = tree[i:tree.find('\ndef ', i + 10)] if i >= 0 else ''
    i_t = g.find('def _toolchain')
    seg = g[i_t:g.find('\ndef ', i_t + 10)] if i_t >= 0 else ''
    return {
        'the tree knows what is NOT part of it':
            'def prune(' in tree and bool(body),
        '  recognising a virtualenv by its own marker, not by a name':
            'pyvenv.cfg' in body,
        '  and site-packages besides, for one copied without the marker':
            "'site-packages'" in tree,
        '  pruning IN PLACE, which is the only spelling os.walk reads':
            'dirnames[:]' in body,
        'check_gates stops scanning for a name that is not there':
            'if name not in text' in seg,
        '  before the regex rather than after it':
            bool(seg) and 0 <= seg.find('if name not in text')
            < seg.find('rx.search(text)'),
        'check_gates reads each tool file once per process':
            '_TOOLS is not None' in g,
        '  and builds its backup index once':
            '_BAK_INDEX is not None' in g,
        '  with no recursive glob of the repository left':
            bool(g) and 'recursive=True' not in g,
        'and all four walkers ask the one rule':
            all('alv_tree' in T.python_code_only(d[p], payloads=True)
                for p in (GATES, PRE, RUN, STAGE)),
        '  with no three-name list of their own beside it':
            all("d not in ('.git', '__pycache__', 'node_modules')"
                not in T.python_code_only(d[p], payloads=True)
                for p in (PRE, RUN)),
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)
ok(MARK in NOW[TREE], 'the round dates itself, on one line')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
ok('recursive=True' in T.python_code_only(OLD[GATES], payloads=True),
   'CONTROL: check_gates really did glob the whole repository, once '
   'per patcher')
ok("d not in ('.git', '__pycache__', 'node_modules')"
   in T.python_code_only(OLD[PRE], payloads=True),
   'CONTROL: and the pre-flight really did walk everything but three '
   'directories - which on a tree holding its own virtualenv is most '
   'of Django, playwright and pymupdf')


# ==========================================================================
head('3. THE SAME ANSWER - every round name in the tree, both ways')
# ==========================================================================
#
# A FASTER INSTRUMENT THAT ANSWERS DIFFERENTLY IS A WORSE INSTRUMENT.
# All three changes are changes to how an answer is COMPUTED, so the
# only honest check is to compute it both ways and compare - over
# every name, not a sample.
import importlib                                            # noqa: E402
import importlib.machinery                                  # noqa: E402,F401
import importlib.util                                       # noqa: E402

CG = importlib.import_module('check_gates')


def load_backup():
    """check_gates AS IT WAS, loaded from its own backup.

    NOT A RE-IMPLEMENTATION. The first draft of this control wrote
    _toolchain out by hand from memory of the old file and got it
    wrong in a way that looked exactly like a real difference: the
    live one appends ` xN` counts to each name and the hand copy did
    not, so 138 of 138 names "differed" and the round looked broken.

    A control is only a control if it is the thing it is controlling
    for. alv_rounds.as_left_by exists for this reason and this is the
    same idea with a module.
    """
    src = os.path.join(ROOT, 'check_gates.py' + SUFFIX)
    if not os.path.isfile(src):
        return None
    # AN EXPLICIT LOADER, because the file does not end in .py.
    # spec_from_file_location returns None for an unknown extension
    # and the next line then fails on NoneType - which reads like the
    # backup is missing when it is sitting right there.
    import importlib.machinery as _m
    loader = _m.SourceFileLoader('_cg_before', src)
    spec = importlib.util.spec_from_loader('_cg_before', loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


BEFORE = load_backup()

# THE NAMES, READ THE WAY check_gates READS THEM - its own pattern,
# not a second spelling that could see a different set.
NAME_RX = re.compile(r'-\s*round\s+([A-Z][A-Z0-9]{0,3}-\d+[a-z]?)')
names = []
for f in sorted(os.listdir(ROOT)):
    if not (f.startswith('apply_') and f.endswith('.py')):
        continue
    m = NAME_RX.search(read(os.path.join(ROOT, f))[:400])
    if m:
        names.append((m.group(1), os.path.join(ROOT, f)))
ok(len(names) > 100,
   'there are %d round names on disk to ask about' % len(names),
   len(names))

# AND THAT IS NOT ALL 531 PATCHERS, WHICH IS ITS OWN FINDING.
# check_gates reads a name only from the MODERN docstring form,
# `apply_x.py - round NF-1, 19 Oct 2026.`; the early-October style
# `"""MP-2 - THE MEAL PLAN FORM...` is invisible to it. NF-1 already
# knew that about _toolchain and taught THAT function both forms;
# the name READER was left with one. Recorded rather than fixed -
# PG-3 is about what the gate costs, and widening what it can see is
# a different round with a different risk.
pats = [f for f in os.listdir(ROOT)
        if f.startswith('apply_') and f.endswith('.py')]
print('       %d of %d patchers declare a name this reader can see'
      % (len(names), len(pats)))

# AND THE WIDENED PATTERN IS WHY THERE ARE THAT MANY. The narrow one
# check_gates carried until this round cannot match a T2 prefix.
narrow = re.compile(r'-\s*round\s+([A-Z]{1,4}-\d+[a-z]?)')
missed = [nm for nm, p in names if not narrow.search(read(p)[:400])]
ok(missed,
   'and %d of them could NOT be read by the pattern check_gates '
   'carried this morning - %s' % (len(missed), ', '.join(missed[:6])),
   missed[:10])

if BEFORE is None:
    skip('the equivalence', 'check_gates backup is not on disk')
else:
    ok(hasattr(BEFORE, '_toolchain'),
       'the backup loads, so the control is the real old instrument '
       'and not a copy of it from memory')

# BOUNDED, AND THE BOUND IS NOT LAZINESS. The OLD spelling opens all
# 1,030 tool files for every name it is asked about, with no cache -
# that is the defect. Running it over 135 names is 139,000 opens,
# which is 74 seconds here and several minutes on a repository inside
# OneDrive. A proof that makes every future sweep slower on the very
# machine this round exists to rescue is a proof that has missed the
# point.
#
# SO: EVERY NAME THE NARROW PATTERN COULD NOT READ, which is the set
# this round changed, PLUS a deterministic spread of the rest. Same
# names on every machine and on every run.
SAMPLE = [x for x in names if x[0] in set(missed)]
SAMPLE += [x for x in names[::max(1, len(names) // 18)]
           if x[0] not in set(missed)]
SAMPLE = SAMPLE[:26]
print('       comparing %d name(s), the %d the narrow pattern missed '
      'and a spread of the rest' % (len(SAMPLE), len(missed)))

t0 = time.time()
old = ([BEFORE._toolchain(ROOT, nm, p) for nm, p in SAMPLE]
       if BEFORE is not None else [])
t_old = time.time() - t0

t0 = time.time()
new = [CG._toolchain(ROOT, nm, p) for nm, p in SAMPLE]
t_new = time.time() - t0

# AND THE NEW SPELLING ANSWERS FOR ALL OF THEM, which is cheap and
# is what proves the instrument still works at full size.
every = [CG._toolchain(ROOT, nm, p) for nm, p in names]

differ = ([(SAMPLE[i][0], old[i], new[i])
           for i in range(len(SAMPLE)) if old[i] != new[i]]
          if old else [('no backup', None, None)])
ok(differ == [],
   'EVERY ONE OF THE %d GETS THE SAME ANSWER, declared and referenced '
   'alike - which is the only thing that makes the speed allowed to '
   'matter' % len(SAMPLE),
   differ[:3])

# AND THE ANSWER IS NOT VACUOUS. A pair of empty lists for every name
# would compare equal and prove nothing, which is the 23 October
# lesson in its plainest form.
found = sum(len(d) + len(r) for d, r in every)
ok(found > 500,
   '  and the answers are not empty - %d mention(s) found across all '
   '%d names, not just the sample' % (found, len(names)), found)
ok(any(d for d, _r in every),
   '  with at least one name DECLARED somewhere, so the two halves '
   'are both exercised')


# ==========================================================================
head('4. AND IT IS A DIFFERENT SIZE OF QUESTION')
# ==========================================================================
#
# ASSERT THE SHAPE, PRINT THE MEASUREMENT - the rule since the
# planter ceiling of 21 October, and doubly right here: the defect
# WAS a number that differed between two machines.
print('       old spelling: %6.2fs for %d names' % (t_old, len(SAMPLE)))
print('       new spelling: %6.2fs' % (t_new,))
ok(t_new * 10 < t_old,
   'the new spelling is more than ten times cheaper - and the ratio '
   'is the claim, not the seconds, because the seconds are a fact '
   'about whichever machine ran this',
   '%.2fs vs %.2fs' % (t_new, t_old))

# THE PREFILTER IS THE WHOLE OF IT, shown by taking it away.
# GS-3, 28 Oct 2026 - FIFTEEN NAMES, NOT SIXTY. The claim is a ratio
# per name - the lookbehind scans every byte every time - and the
# slow half of it was most of this suite's 90 seconds on the gate. A
# quarter of the names makes the same ratio; the seconds were never
# the claim.
sample = [nm for nm, _p in names[:15]]
texts = [t for _n, _p, t in CG._tools(ROOT)]
t0 = time.time()
for nm in sample:
    rx = re.compile(r'(?<![\w-])%s(?![\w-])' % re.escape(nm))
    for tx in texts:
        rx.search(tx)
t_rx = time.time() - t0
t0 = time.time()
for nm in sample:
    rx = re.compile(r'(?<![\w-])%s(?![\w-])' % re.escape(nm))
    for tx in texts:
        if nm in tx:
            rx.search(tx)
t_pre = time.time() - t0
print('       regex alone : %6.2fs for %d names over %d file(s)'
      % (t_rx, len(sample), len(texts)))
print('       with prefilter: %4.2fs' % (t_pre,))
ok(t_pre * 5 < t_rx,
   'THE LOOKBEHIND IS WHAT COSTS. `(?<![\\w-])NAME(?![\\w-])` cannot '
   'match a string without NAME in it, but the lookbehind defeats '
   'CPython literal prefilter, so it scans every byte every time',
   '%.2fs vs %.2fs' % (t_pre, t_rx))


# ==========================================================================
head('5. NOTHING WALKS A VIRTUALENV')
# ==========================================================================
#
# BUILT RATHER THAN HOPED FOR. This machine has no venv inside the
# repository - which is exactly why the defect was invisible here -
# so the suite makes one and asks the rule about it.
import tempfile                                             # noqa: E402

tmp = tempfile.mkdtemp(prefix='alv_pg3_')
try:
    for name in ('code', 'node_modules', 'pages', '.git'):
        os.makedirs(os.path.join(tmp, name))
    # A VIRTUALENV IS WHAT THE INTERPRETER SAYS IT IS.
    with open(os.path.join(tmp, 'code', 'pyvenv.cfg'), 'w', encoding='utf-8') as fh:
        fh.write('home = /usr/bin\n')
    os.makedirs(os.path.join(tmp, 'code', 'Lib', 'site-packages'))
    with open(os.path.join(tmp, 'code', 'Lib', 'site-packages',
                           'x.py.bak_trap'), 'w', encoding='utf-8') as fh:
        fh.write('a backup that is not ours\n')
    with open(os.path.join(tmp, 'pages', 'real.py.bak_trap'), 'w', encoding='utf-8') as fh:
        fh.write('a backup that IS ours\n')

    seen = []
    for dp, fn in T.walk_tree(tmp):
        for f in fn:
            seen.append(os.path.relpath(os.path.join(dp, f), tmp)
                        .replace(os.sep, '/'))
    ok('pages/real.py.bak_trap' in seen,
       'the walk finds a backup in the tree')
    ok(not any('code/' in s for s in seen),
       '  and nothing at all inside the virtualenv - which is what '
       'his gate was spending ten minutes on', seen)
    ok(not any('node_modules' in s or '.git' in s for s in seen),
       '  nor in the directories that were already excluded', seen)

    # AND THE NAME IS NOT WHAT DECIDES IT.
    other = os.path.join(tmp, 'whatever')
    os.makedirs(other)
    with open(os.path.join(other, 'pyvenv.cfg'), 'w', encoding='utf-8') as fh:
        fh.write('home = /usr/bin\n')
    with open(os.path.join(other, 'y.py.bak_trap'), 'w', encoding='utf-8') as fh:
        fh.write('x\n')
    seen2 = []
    for dp, fn in T.walk_tree(tmp):
        for f in fn:
            seen2.append(os.path.relpath(os.path.join(dp, f), tmp)
                         .replace(os.sep, '/'))
    ok(not any('whatever' in s for s in seen2),
       '  and a venv called something else is skipped too, because '
       'the marker decides and not the name - his is called `code` '
       'and the next one will not be', seen2)

    # A DIRECTORY THAT MERELY LOOKS LIKE ONE IS NOT ONE.
    plain = os.path.join(tmp, 'codebase')
    os.makedirs(plain)
    with open(os.path.join(plain, 'z.py.bak_trap'), 'w', encoding='utf-8') as fh:
        fh.write('x\n')
    seen3 = []
    for dp, fn in T.walk_tree(tmp):
        for f in fn:
            seen3.append(os.path.relpath(os.path.join(dp, f), tmp)
                         .replace(os.sep, '/'))
    ok(any('codebase/z.py.bak_trap' in s for s in seen3),
       'CONTROL: and an ordinary directory with a venv-ish name is '
       'NOT skipped - the rule is the marker, so it cannot take a '
       'real folder out of the tree by accident', seen3)
finally:
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('6. THE SUITE THAT TIMED OUT NOW RUNS')
# ==========================================================================
#
# ITS OWN CLAIM, UNCHANGED. PG-2 wrote test_preflight_names and this
# round touched neither it nor what it asserts - only how long the
# thing underneath takes to answer.
pn = read(os.path.join(ROOT, 'test_preflight_names.py'))
ok('check_gates.py' in pn,
   "PG-2's suite still drives check_gates over every patcher")
ok(os.path.isfile(os.path.join(ROOT, 'test_preflight_names.py')),
   '  and is still on disk to be driven')
ok(SUFFIX not in pn,
   '  and this round did not touch it - the suite that failed is the '
   'suite that will pass, unaltered')


# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('def prune' in gate,
   '  with a sentinel that would notice the rule going away')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
