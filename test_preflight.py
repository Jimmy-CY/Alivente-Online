# -*- coding: utf-8 -*-
"""test_preflight.py - round PG-1, 18 Oct 2026.  E24.

DOES THE TREE KNOW THE ROUNDS THE SUBJECT LINE SAYS IT IS PUSHING?

Twice in two days a push went through with a subject naming rounds the
tree did not contain, and both times everything downstream was honestly
green:

    16 OCT  three rounds were delivered as a zip, the zip was never
            extracted, and the commit changed one file - the archive.
            The gate ran the OLD suite list, because the gate is itself
            a file the rounds would have changed.

    17 OCT  six rounds were delivered by writing the applied files
            straight into the repo, and their .bak_ files were left
            behind. as_left_by() fell back to reading live files, so
            every "as the round left it" check became a file compared
            with itself, and the gate failed at suite 15 of 366.

WHAT THIS SUITE ASKS

    THE PARSE. alv_rounds.py's own comments map a round name to a
    suffix. Nothing is hand-kept, and the OWNER of an entry is the
    name written first in its comment block - matching the whole
    comment made .bak_contactwire belong to CC-2 as well as CC-3.

    THE REAL TREE. Every round the register names, run through the
    check, against the repo as it stands.

    THE TWO FAILURES, REBUILT. A tree where the register has no entry
    for the round (16 Oct) and a tree where it has the entry but not
    one backup on disk (17 Oct). Both must be refused, and the reason
    printed must be the right one of the two.

    AND THAT IT CANNOT REFUSE A ROUND THAT IS FINE. The first spelling
    required a sentinel naming the round, and the first real subject it
    saw refused CP-1, which correctly has none. That check is a note
    now, and this suite holds the reason so it is not re-tightened.
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

import os
import re
import sys
import json
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_tree                                             # noqa: E402
import alv_preflight                                        # noqa: E402

try:
    from alv_rounds import as_left_by                       # noqa: F401
except Exception:
    as_left_by = None

SUFFIX = '.bak_preflight'
MOD = 'alv_preflight.py'
ME = 'test_preflight.py'
PATCHER = 'apply_preflight.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDSPY = 'alv_rounds.py'

passed = failed = skipped = 0


def ok(cond, msg, got=None):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if got is not None:
            print('         %s' % str(got)[:180])


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


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)


NOW = read(os.path.join(ROOT, PS1))
APPLIED = os.path.isfile(os.path.join(ROOT, PS1) + SUFFIX)

print('')
print('test_preflight.py - round PG-1, 18 Oct 2026   (E24)')
print('  module   : %s' % MOD)
print('  claim    : a subject naming a round the tree does not have is refused')


# ==========================================================================
head('1. THE REGISTER PARSES, AND THE OWNER IS THE ONE WRITTEN FIRST')
# ==========================================================================
reg = alv_preflight.register(ROOT)
print('      %d round name(s) resolve to a suffix' % len(reg))
ok(len(reg) > 50,
   'the register maps round names to suffixes, read out of %s' % ROUNDSPY,
   len(reg))
for name, suf in (('GT-2', '.bak_gatespeed'), ('AR-1', '.bak_autoretry'),
                  ('CC-3', '.bak_contactwire'), ('RI-1', '.bak_imagewire')):
    ok(reg.get(name) and suf in reg[name],
       '  %-5s -> %s' % (name, suf), reg.get(name))
# THE OWNER, NOT EVERY NAME THE COMMENT MENTIONS.
ok(reg.get('CC-2') == ['.bak_contactmodal'],
   '  CC-2 owns only its own suffix - CC-3 names CC-2 in its comment '
   'and that does not make the entry CC-2 own', reg.get('CC-2'))
ok(not any(len(v) > 2 for v in reg.values()),
   '  and no name claims more than two suffixes',
   [(k, v) for k, v in reg.items() if len(v) > 2][:3])


# ==========================================================================
head('2. THE REAL TREE - EVERY ROUND THE REGISTER NAMES')
# ==========================================================================
names = sorted(reg)
bad, say = alv_preflight.check(' '.join(names) + ' - every round at once')
missing = [b for b in bad if 'NOT ONE of those files' in b]
unknown = [b for b in bad if 'no entry for it' in b]
print('      %d round(s) checked, %d with no backup on disk'
      % (len(names), len(missing)))
ok(not unknown,
   'not one of the %d names the register holds is unknown to it - the '
   'parse agrees with itself' % len(names), unknown[:2])
ok(len(missing) <= 2,
   'and at most two have no backup left on disk (an old round whose '
   'backups were tidied away is not this round\'s business)',
   [m[:60] for m in missing[:3]])
b2, _ = alv_preflight.check('no round named here at all')
ok(not b2, 'a subject with no round name in it is not refused', b2)
b3, _ = alv_preflight.check('E24 and E25 are findings, not rounds')
ok(not b3,
   'and a finding written E24 is not mistaken for a round - a round '
   'carries a hyphen', b3)


# ==========================================================================
head('3. THE TWO FAILURES, REBUILT - AND REFUSED FOR THE RIGHT REASON')
# ==========================================================================
# A guard that cannot be seen to refuse is not a guard. Both shapes are
# built as real trees in a scratch directory and run through the same
# function the gate calls.
def tree(entry, make_backup):
    d = os.path.join(SCRATCH, 'tree_%s_%s' % (bool(entry), bool(make_backup)))
    if not os.path.isdir(d):
        os.makedirs(d)
    write(os.path.join(d, ROUNDSPY),
          "ROUNDS = [\n"
          + ("    # XY-7, 18 Oct 2026 - a round built for this check.\n"
             "    '.bak_xyseven',\n" if entry else "")
          + "]\n")
    write(os.path.join(d, PS1),
          "$sentinels = @(\n"
          "    @{ File = 'x.html'; Text = 'q'; What = 'XY-7: the round' },\n"
          ")\n")
    if make_backup:
        write(os.path.join(d, 'something.py.bak_xyseven'), 'x\n')
    return d

SUBJ = 'XY-7 - a round that may or may not be in this tree'

# 16 OCT: nothing arrived, so the register has no entry.
d = tree(entry=False, make_backup=False)
bad, say = alv_preflight.check(SUBJ, root=d)
print('')
print('      16 Oct shape - no register entry:')
for s in say:
    print('     %s' % s)
ok(bad, 'CONTROL: a round the register has never heard of is REFUSED')
ok(any('no entry for it' in b for b in bad),
   '  and the reason given is the missing entry, not the backups',
   bad[:1])

# 17 OCT: the files arrived, the backups did not.
d = tree(entry=True, make_backup=False)
bad, say = alv_preflight.check(SUBJ, root=d)
print('')
print('      17 Oct shape - entry present, no backup on disk:')
for s in say:
    print('     %s' % s)
ok(bad, 'CONTROL: a round delivered without its backups is REFUSED')
ok(any('NOT ONE of those files' in b for b in bad),
   '  and the reason names the backups, not the register', bad[:1])
ok(any('as_left_by' in b for b in bad),
   '  and says what goes wrong when they are missing - every "as the '
   'round left it" check becomes a file compared with itself')

# AND THE TREE THAT IS FINE.
d = tree(entry=True, make_backup=True)
bad, say = alv_preflight.check(SUBJ, root=d)
ok(not bad,
   'and a round that IS in the register and DOES have a backup passes',
   bad[:1])


# ==========================================================================
head('4. IT CANNOT REFUSE A ROUND THAT IS FINE')
# ==========================================================================
# The first spelling required a sentinel naming the round, and the first
# real subject it saw refused CP-1 - which correctly carries none,
# because it changes one suite and asserts its own shape. The reason is
# kept here so the check is not quietly re-tightened.
src = read(os.path.join(ROOT, MOD))
ok('THE SENTINEL IS A NOTE, NOT A REFUSAL' in src,
   'the module records why the sentinel is a note rather than a gate')
ok('no sentinel names it' in src,
   '  and prints it as a note when there is none')
bad, say = alv_preflight.check('CP-1 - a round with no sentinel of its own')
ok(not bad,
   'CP-1 passes - it has a register entry and backups, and no sentinel',
   bad[:1])
ok(any('no sentinel names it' in s for s in say),
   '  and the pre-flight says so rather than staying quiet', say)


# ==========================================================================
head('5. ONE WALK, NOT ONE PER ROUND')
# ==========================================================================
ok('ONE walk' in src,
   'the backups are counted in a single pass over the tree')
ok(src.count('os.walk(') == 1,
   '  and there is exactly one os.walk in the module',
   src.count('os.walk('))


# ==========================================================================
head('6. THE GATE CALLS IT, EARLY')
# ==========================================================================
ok('alv_preflight.py' in NOW, '%s calls %s' % (PS1, MOD))
i = NOW.find('alv_preflight.py')
j = NOW.find('$sentinels = @(')
ok(i >= 0 and j >= 0 and i < j,
   '  before the sentinel table, so a wrong subject costs seconds '
   'rather than the whole sweep', '%d vs %d' % (i, j))
# THE LINE THAT RUNS THE SUITES, NOT THE FIRST MENTION OF IT.
# `alv_run.py` is named in the -Resume parameter comment at the top of
# the gate, 80 lines above anything that executes, so find() on the
# name answered a question about prose.
k = NOW.find('$runArgs = @(')
ok(i >= 0 and k >= 0 and i < k,
   '  and long before the 367 suites are run', '%d vs %d' % (i, k))
ok(re.search(r'if \(\$Apply -and \$Message\)', NOW) is not None,
   '  and only when there is a subject and the run would commit')
ok(not APPLIED or 'alv_preflight.py' not in
   (read(os.path.join(ROOT, PS1) + SUFFIX) if APPLIED else ''),
   'CONTROL: the gate did not call it before this round')


# ==========================================================================
head('7. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    ok(SUFFIX in alv_rounds.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    skip('the round register', str(e)[:60])
ok("'%s'" % ME in NOW, '%s runs this suite' % PS1)
ok("File = 'alv_preflight.py'" in NOW, '  and holds a sentinel on it')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(alv_tree.CONVERTED),
   '  test_waiting_down CONVERTED_N agrees with alv_tree.CONVERTED, '
   'which holds %d' % len(alv_tree.CONVERTED), m.group(1) if m else '?')


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that the round is CORRECT - only that the tree contains')
print('  it. A round can be present, backed up, registered and wrong,')
print('  and that is what the 367 suites are for.')
print('')
print('  Not that the subject line is accurate. A push whose subject')
print('  names no round at all passes here, because there is nothing')
print('  to compare. The guard answers a question the subject asks;')
print('  it cannot make it ask one.')
print('')
print('  Not that backups are CORRECT, only that they exist. A backup')
print('  that is a copy of the applied file would satisfy this and')
print('  still make as_left_by useless. That is a different check and')
print('  it belongs with the delivery, not the push.')


print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
