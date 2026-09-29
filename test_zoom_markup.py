# -*- coding: utf-8 -*-
"""test_zoom_markup.py - Section P round P5, 29 Sep 2026.

test_zoom_guards.py rendered each page it had touched under base-then and
base-now and required every control to come out identical. It used
TODAY'S markup for both - safe until a later round put a control on a
page that only today's base can style.

P1 did that this afternoon. Celebration Management's filter panel holds a
.filter-input and two .filter-selects, and .filter-input is not in base as
the zoom round left it: ALV FILTER FIELD v1 landed five rounds later. Old
base cannot style it, new base does, and the suite failed - correctly by
its own rule, and wrongly about the world. The font-size, which is the
thing it is actually about, was 16px under both.

So the comparison moved to the markup as that round left it, and a NEW
check asks today's markup the question that matters: at 375, is every
control 16px or more? Nothing had been asking it of a control added
later.

This suite is short on purpose. It judges the edit, not the zoom round -
that one runs on the gate in its own right.
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

SUFFIX = '.bak_zoommk'
ME = 'test_zoom_markup.py'
PATCHER = 'apply_zoom_markup.py'
TARGET = 'test_zoom_guards.py'
PS1 = 'Push-PendingChanges.ps1'

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
    return cond


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


zg = read(os.path.join(ROOT, TARGET))

print('=' * 74)
print('%s - P5, THE ZOOM SUITE JUDGES ITS OWN MARKUP' % ME)
print('=' * 74)

# ==========================================================================
head('1. LIKE COMPARED WITH LIKE')
# ==========================================================================
ok('mk = body_markup(as_left_by(p, SUFFIX, read))' in zg,
   "%s renders the page AS ITS OWN ROUND LEFT IT" % TARGET)
ok('mk = body_markup(after)' not in zg,
   '  and no longer renders today\'s markup under a base from five rounds '
   'earlier')
ok('from alv_rounds import as_left_by' in zg,
   '  with as_left_by imported, which it already was for the section above')
ok('ALV FILTER FIELD v1' in zg,
   '  and the note names the component that exposed this')

# THE CLAIM, MEASURED HERE RATHER THAN ASSERTED THERE.
was = read(os.path.join(ROOT, 'pages', 'templates',
                        'base.html' + '.bak_zoomguard'))
now = read(os.path.join(ROOT, 'pages', 'templates', 'base.html'))
ok('.filter-input' not in was and '.filter-input' in now,
   'base as the zoom round left it has NO .filter-input, and base now '
   'does - which is the whole reason the comparison had to move',
   'was: %s  now: %s' % ('.filter-input' in was, '.filter-input' in now))
ok('.filter-select' not in was,
   '  nor .filter-select - ALV FILTER FIELD v1 landed five rounds later')

# ==========================================================================
head('2. AND THE PROMISE IS NOW ASKED OF THE PAGE AS IT STANDS')
# ==========================================================================
ok('small_now = []' in zg, 'the new check is there')
ok('body_markup(t_now)' in zg,
   '  and it reads TODAY\'s markup, which is what nothing was asking')
ok(zg.count('body_markup(t_now)') == 1,
   '  exactly once', zg.count('body_markup(t_now)'))
ok('ok(not small_now' in zg,
   '  and it FAILS on a control under 16px - it is not another note')
ok('small_after' in zg,
   '  while small_after stays a note, because it asks a different '
   'question: the markup as the round left it')
ok('notes.append' in zg[zg.index('small_after'):],
   '    and it is still appended to the notes, not to the failures')

# ==========================================================================
head('3. CONTROLS, AND THE GATE')
# ==========================================================================
b = os.path.join(ROOT, TARGET + SUFFIX)
if os.path.isfile(b):
    old = read(b)
    ok('mk = body_markup(after)' in old,
       'CONTROL: the backup still renders today\'s markup under the old '
       'base, so section 1 would FAIL - a revert is caught')
    ok('small_now' not in old,
       '  and it never asked the 16px question of today\'s markup')
else:
    skipped += 2
    print('  skip the revert controls  (no backup yet)')

ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(TARGET in t, 'the suite this round edits is on the gate  %s' % PS1)
    ok(ME in t, '  and so is this one')
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 3
    print('  skip the gate checks  (%s not staged)' % PS1)

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that the zoom suite passes. It runs on the')
print('  gate in its own right, and it takes eleven minutes; proving it')
print('  twice would only make the gate slower.')
print('=' * 74)
sys.exit(1 if failed else 0)
