# -*- coding: utf-8 -*-
"""test_gate_solo.py - round GS-2, 2 Nov 2026.

RELEASE 63 - THE PUSH GATE: TWO MORE SUITES RUN ALONE.
Two pushes in two days stopped part-way on a suite that failed in the pool
and passed by itself - each costing a --resume:
    test_signing_finish.py  Release 59, 460/500: the process crashed
                            (rc 3221227274), passed alone in 9.6s.
    test_gate_walk.py       Release 62, 357/503: a timing ratio of 5.6
                            against a claim of 10, passed alone in 46.1s.
Demetri, 21:32: "Yes please" to pinning both to the serial phase, beside
test_print_buttons and test_print_queries (GS-1).
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

SUFFIX = '.bak_gatesolo'
ME = 'test_gate_solo.py'
PATCHER = 'apply_gate_solo.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(ROOT, 'alv_run.py'), J(ROOT, 'test_gate_serial.py')]

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


import ast                                                  # noqa: E402

print(__doc__.strip().splitlines()[0])


def listed(src, name):
    for node in ast.parse(src).body:
        if (isinstance(node, ast.Assign)
                and any(getattr(t, 'id', '') == name for t in node.targets)
                and isinstance(node.value, ast.List)):
            return [e.value for e in node.value.elts
                    if isinstance(e, ast.Constant)]
    return None


# ==========================================================================
head('1. THE LIST')
# ==========================================================================
run = read(J(ROOT, 'alv_run.py'))
c = listed(run, 'CONTENDED') or []
ok('test_gate_walk.py' in c and 'test_signing_finish.py' in c,
   'CONTENDED now holds test_gate_walk.py and test_signing_finish.py', c)
ok('test_print_buttons.py' in c and 'test_print_queries.py' in c,
   '  and still the two GS-1 measured')
ok(c == sorted(c) and len(c) == len(set(c)) == 4,
   '  four names, sorted, none twice')
ok('5.6 times, FAILED' in run and 'passed in 46.1s' in run and
   'rc 3221227274' in run and 'passed in 9.6s' in run,
   'THE MEASUREMENTS are beside the names, so the reason can be audited')
names = set()
gate = read(J(ROOT, PS1))
import re as _re                                             # noqa: E402
names = set(_re.findall(r"'(test_[\w]+\.py)'", gate))
ok(all(n in names for n in c),
   'every contended suite is on the push gate suite list - a name the gate '
   'does not run would be a promise about nothing')
ok("slow = [n for n in todo if n in CONTENDED and n not in PLANTERS]" in run
   and 'serial = plant + slow' in run,
   'the runner still sends CONTENDED to the serial phase, before the pool')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
was_list = listed(was(J(ROOT, 'alv_run.py')), 'CONTENDED') or []
ok('test_gate_walk.py' not in was_list and
   'test_signing_finish.py' not in was_list,
   'CONTROL: before this round both ran in the pool')
gs = read(J(ROOT, 'test_gate_serial.py'))
ok('set(SLOW) <= set(contended or [])' in gs,
   'test_gate_serial asks for its two measured names, not the whole list')

# ==========================================================================
head('2. REGISTERED')
# ==========================================================================
sys.path.insert(0, ROOT)
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = \"    'test_gate_walk.py',\"" in gate,
   '  with a sentinel on the new names')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
