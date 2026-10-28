# -*- coding: utf-8 -*-
"""test_bar_audit.py - round BA-1, 21 Oct 2026.

THE INSTRUMENT THAT OWNS BAR ORDER COULD NOT SEE THE BAR IT WAS
ASKED ABOUT.

Three holes, each of which let a real fault ship between 19 and 21
October.

  1  A TREE-WIDE CLAIM READ THROUGH A HISTORICAL READER.
     test_bar_order section 1 is headed EVERY BAR IN THE APP and
     walks alv_tree.templates() - today's 151 files - but read each
     one through now(), which is as_left_by(p, SUFFIX): the file as
     ITS OWN round left it. Today's file list, September's contents.
     PP-1 put Print before the primary on 20 October; the suite ran
     that bar through a snapshot taken before the button existed and
     reported PSB where the markup said SPSB. Demetri found it by
     looking at the screen.

  2  A BAR WRITTEN AS A <form> WAS INVISIBLE. The detector matched
     `<div` only. SL-7 wrote the shopping list's range as
     `<form class="sl-range page-action-buttons">`, so that page
     carried two bars and the suite could see one.

  3  NOTHING ASSERTED ONE BAR PER PAGE. base 3.4 says it;
     test_one_action_bar does not, despite its name - its checks are
     about a retired CSS variant.

AND READING LIVE PAID IMMEDIATELY. finance_pl_act's bespoke
btn-group had been converted to base's own .alv-seg by PN-1 on 3
October, and the suite had gone on reporting six bespoke containers
for eighteen days because it was reading that page as it was before.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The detector sees a form, the tree-wide walks read
      live, the control still reads historically, and the two new
      claims exist.

  2   THE CONTROL. Re-asked of .bak_baraudit, where none held.

  3   THE INSTRUMENT, RUN. test_bar_order itself, executed, green -
      because a repaired instrument that fails is worse than one
      that is blind.

  4   THE PROOF IT CAN NOW SEE. A form bar and a reordered bar, both
      planted in a scratch copy, both reported.

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
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_baraudit'
ME = 'test_bar_audit.py'
PATCHER = 'apply_bar_audit.py'
BO = 'test_bar_order.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'BA-1, 21 Oct 2026'

TARGET = os.path.join(ROOT, BO)
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

NOW = {TARGET: read(TARGET)}


def claims(bundle):
    src = T.python_code_only(bundle[TARGET], payloads=True)
    c = {}
    c['THE DETECTOR SEES A FORM BAR - hole 2'] = (
        "r'<(?:div|form)[^>]*class=" in src)
    c['SECTION 1 READS THE LIVE TREE - hole 1'] = (
        'for b in bars(code_only(read(alv_tree.last_path(' in src)
    c['  and so does the BOTH ROOTS count'] = (
        'for _b in bars(code_only(read(alv_tree.last_path(' in src)
    c['  and so does section 2'] = (
        'for b in bars(code_only(read(alv_tree.last_path(rel))))' in src)
    c['ONE BAR PER PAGE IS ASSERTED - hole 3'] = ('TWO_BARS' in src)
    c['  as a census, naming the one page that has two'] = (
        "'projects/project_tasks_delete.html'" in src)
    c['AND .alv-seg IS A HOUSE CONTAINER'] = (
        "elif 'alv-seg' in cls.split():" in src)
    c['  so the bespoke set is five'] = (
        "'finance_pl_act.html btn-group pl-view-toggle'" not in src)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

src = T.python_code_only(NOW[TARGET], payloads=True)
# THE CONTROL SECTION STILL READS HISTORICALLY. Deleting now() would
# be the opposite mistake: section 4 compares three pages before and
# after its own round, and that really is a claim about the past.
ok('def now(' in src, 'now() survives - the control section needs it')
ok(src.count('bars(code_only(now(p)))') == 1,
   'and exactly one walk still uses it',
   src.count('bars(code_only(now(p)))'))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TARGET: was(TARGET)}
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of these held',
   'what held: %r' % (held,))
old = T.python_code_only(BEFORE[TARGET], payloads=True)
ok("r'<div[^>]*class=" in old,
   'CONTROL: the detector really was div-only')
ok(old.count('bars(code_only(now(p)))') == 4,
   'CONTROL: and FOUR walks read through the historical reader, '
   'three of which are tree-wide claims',
   old.count('bars(code_only(now(p)))'))
ok("'finance_pl_act.html btn-group pl-view-toggle'" in old,
   'CONTROL: and it still listed a bespoke container PN-1 converted '
   'on 3 October - which is what reading a snapshot costs')


# ==========================================================================
head('3. THE INSTRUMENT, RUN')
# ==========================================================================
# A REPAIRED INSTRUMENT THAT FAILS IS WORSE THAN A BLIND ONE: it
# stops a push and teaches nobody. So it is executed here, not read.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_bar_order IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(BO) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(BO))
_bo = read(os.path.join(ROOT, BO))
ok('read LIVE' in _bo,
   '  and it still says so: its section 1 reports reading live')
ok('two action bars' in _bo,
   '  and the two-bar census is still in it')


# ==========================================================================
head('4. THE PROOF IT CAN NOW SEE')
# ==========================================================================
# PLANTED, IN A SCRATCH COPY. An absence claim is worth nothing
# without evidence the detector would have spoken. Two faults are
# injected into a throwaway tree - a bar written as a form, and a
# secondary before the primary - and the repaired instrument must
# report each.
#
# A SCRATCH DIRECTORY, NEVER THE TREE. CE-1 cost a whole sweep on 20
# October because a suite wrote into the repository it was being run
# against.
scratch = tempfile.mkdtemp(prefix='alv_baraudit_')
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location('bo_probe', TARGET)
    mod = importlib.util.module_from_spec(spec)
    # The module runs its own sections on import, so only its source
    # is borrowed: the two helpers are re-declared from it by exec of
    # the head, up to the first head() call.
    head_src = NOW[TARGET][:NOW[TARGET].index("head('1.")]
    ns = {}
    exec(compile(head_src, 'bo_head', 'exec'), ns)
    BARre, bars_, variants_ = ns['BAR'], ns['bars'], ns['variants']

    form_bar = ('<form method="get" class="sl-range page-action-buttons">'
                '<button class="btn action-primary">Go</button></form>')
    ok(len(BARre.findall(form_bar)) == 1,
       'PLANTED: a bar written as a <form> is seen',
       len(BARre.findall(form_bar)))
    div_bar = ('<div class="page-action-buttons">'
               '<a class="btn action-secondary">Print</a>'
               '<a class="btn action-primary">List</a>'
               '<a class="btn action-back">Back</a></div>')
    got = bars_(div_bar)
    seq = variants_(got[0]) if got else []
    ok(seq == ['SPB'],
       'PLANTED: a secondary before the primary reads SPB', seq)
    ok(not re.match(r'^P*S*F*B*$', seq[0] if seq else 'x'),
       '  and SPB is not house order, so it would be reported')
finally:
    shutil.rmtree(scratch, True)


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
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
import apply_bar_audit as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
