# -*- coding: utf-8 -*-
"""test_gate_retry.py - round GS-4, 16 Nov 2026.

A TIMING CHECK MEASURES TWICE BEFORE IT STOPS A PUSH.
16 Nov: the R90 gate stopped at 19 of 530 on test_gate_walk's speed
ratio (7.78s against 33.95s - 4.4, it asks for 10) on a busy laptop; the
same suite passed alone a minute later. Demetri: "Do it after R90
deploys". The ratio is measured once more before it fails.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_gateretry'
ME = 'test_gate_retry.py'
PATCHER = 'apply_gate_retry.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

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
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)






print(__doc__.strip().splitlines()[0])
WALK = J(ROOT, 'test_gate_walk.py')
w = read(WALK)
head('1. THE CHECK')
ok('# GS-4, 16 Nov 2026 - MEASURED TWICE BEFORE IT FAILS.' in w,
   'test_gate_walk says why it measures twice, with the date and the run')
ok('if BEFORE is not None and not t_new * 10 < t_old:' in w and
   'BEFORE._toolchain(ROOT, nm, p) for nm, p in SAMPLE]\n    t_old2' in w
   and 'CG._toolchain(ROOT, nm, p) for nm, p in SAMPLE]\n    t_new2' in w,
   'a ratio short of ten is measured again - BOTH spellings, the same names')
ok('if t_new2 * 10 < t_old2:\n        t_old, t_new = t_old2, t_new2' in w,
   'only a second measurement that clears ten replaces the first')
ok(w.count('ok(t_new * 10 < t_old,') == 1,
   'and the claim itself is unchanged: still more than ten times cheaper')
head('2. CONTROL')
try:
    b = was(WALK)
    ok('t_old2' not in b and 'ok(t_new * 10 < t_old,' in b,
       'before this round: one measurement decided - a busy minute could '
       'stop a push')
    ok(w.replace(w[w.index('# GS-4, 16 Nov 2026'):w.index(
        'ok(t_new * 10 < t_old,')], '') == b,
       'nothing else in test_gate_walk changed')
except IOError as _e:
    skip('control', str(_e))
head('3. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
