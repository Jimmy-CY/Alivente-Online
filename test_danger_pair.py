# -*- coding: utf-8 -*-
"""test_danger_pair.py - round DG-1, 17 Oct 2026.

ONE DELETE BUTTON NEVER JOINED THE PAIR.

E12, banked 12 Oct as "invisible to the height census". Re-measured on
17 Oct it is sharper: the house form for a destructive button is BOTH
classes, because base draws `.action-danger` outlined at rest and
filled only on hover - a MODIFIER on a secondary button, not a tone of
its own.

    act_expense.html        btn action-danger btn-sm              <- this
    import_recipe.html      btn action-secondary action-danger btn-sm
    preview_imported_recipe btn action-secondary action-danger btn-sm

Its own sibling, two lines above it in the same row, is
`btn action-secondary btn-sm`. The row was written one button at a time.

CC-2 met the same rule from the other side yesterday: a footer Delete
written as `action-danger` alone made the button GATE call the page
drifting.

WHY NOTHING CAUGHT IT. The button is inside a JavaScript template
string, so every census that walks markup is blind to it - E11's
standing finding - and D-1's height census selects on position tones,
of which this button has none.

AND THE SUITE THAT COUNTS LV-1's WORK

    test_leave_decided compared the LIVE file against LV-1's backup and
    counted 25 changed classes. Adding one class to a 26th button on
    one of LV-1's seventeen templates made that 26 - not because LV-1
    did more, but because a question about 16 October was being asked
    of today's tree. Section 3 proves the re-point by rendering the
    count both ways.
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

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_dangerpair'
PAGE = 'act_expense.html'
SUITE = 'test_leave_decided.py'
ME = 'test_danger_pair.py'
PATCHER = 'apply_danger_pair.py'
PS1 = 'Push-PendingChanges.ps1'
PEERS = ('import_recipe.html', 'preview_imported_recipe.html')

CONVERTED_NOW, ALIAS_NOW = 100, 109

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


def as_dg1_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


PATH = alv_tree.path_of(PAGE)
NOW = read(PATH)
APPLIED = os.path.isfile(PATH + SUFFIX)
WAS = read(PATH + SUFFIX) if APPLIED else NOW
B_NOW, B_WAS = code_only(NOW), code_only(WAS)

print('')
print('test_danger_pair.py - round DG-1, 17 Oct 2026')
print('  page     : %s' % PAGE)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE DELETE BUTTON WEARS THE PAIR')
# ==========================================================================
ok('action-secondary action-danger btn-sm" onclick="deleteInvoice' in B_NOW,
   'the script-built Delete button carries both classes')
ok(not re.search(r'class="btn action-danger\b', B_NOW),
   '  and nothing on the page wears the modifier alone')
ok(not APPLIED or re.search(r'class="btn action-danger\b', B_WAS),
   'CONTROL: it did, until this round')

# ITS OWN SIBLING, which is how the row gave itself away.
ok('class="btn action-secondary btn-sm" onclick="showReplaceUpload()"'
   in B_NOW,
   'the Replace button beside it is action-secondary, and always was')

# AND THE PAGES THAT ALREADY HAD IT - read, not remembered.
for rel in PEERS:
    ok('action-secondary action-danger'
       in code_only(read(alv_tree.path_of(rel))),
       '%s carries the pair' % rel)
ok('.action-danger' in read(alv_tree.path_of('base.html')),
   'and base declares .action-danger, outlined at rest')

# AND THE PAGE ALREADY HAD ONE PAIR, which is the evidence that this
# row was written one button at a time rather than to a rule nobody
# knew: #confirmDeleteBtn in the delete-confirmation footer has worn
# both classes all along, in the same file.
ok(B_NOW.count('action-secondary action-danger') == 2,
   'the page now carries two paired buttons', 
   B_NOW.count('action-secondary action-danger'))
ok(not APPLIED or B_WAS.count('action-secondary action-danger') == 1,
   '  and carried one before - the delete confirmation, which was '
   'right all along in the same file')


# ==========================================================================
head('2. WHY NOTHING SAW IT')
# ==========================================================================
# The button lives in a JavaScript template string, so every census that
# walks markup is blind to it. That is E11, and this is one of them.
scripts = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>',
                               B_NOW, re.S))
ok('deleteInvoiceDocument(${expenseId})' in scripts,
   'the button is built inside a script, not written in markup')
markup = re.sub(r'<script\b[^>]*>.*?</script\s*>', '', B_NOW, flags=re.S)
ok('deleteInvoiceDocument' not in markup,
   '  so a census that walks the markup alone cannot reach it - E11')


# ==========================================================================
head('3. test_leave_decided COUNTS LV-1 WORK, AS LV-1 LEFT IT')
# ==========================================================================
lv = read(os.path.join(ROOT, SUITE))
ok('a, b = code_only(read(p)), code_only(read(p + SUFFIX))' not in lv,
   '%s no longer reads the live tree for LV-1 count' % SUITE)
ok('as_left_by(p, SUFFIX, read) if as_left_by else read(p)' in lv,
   '  but the file as that round left it')
lv_was = (read(os.path.join(ROOT, SUITE) + SUFFIX)
          if os.path.isfile(os.path.join(ROOT, SUITE) + SUFFIX) else '')
ok(not APPLIED or
   'a, b = code_only(read(p)), code_only(read(p + SUFFIX))' in lv_was,
   'CONTROL: it read the live tree, until this round')

# AND THE NUMBER IT ASSERTS IS STILL LV-1's.
ok('N_EDITS' in lv, '  and the number it asserts is unchanged')
ok(re.search(r'N_EDITS\s*=\s*25', lv) is not None,
   '  25 - what LV-1 planned and did, not what the tree has since '
   'accumulated', re.search(r'N_EDITS\s*=\s*\d+', lv))


# ==========================================================================
head('4. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_invoiceicon' in _r
       and _r.index(SUFFIX) > _r.index('.bak_invoiceicon'),
       '  and sits after .bak_invoiceicon', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'action-secondary action-danger btn-sm'" in ps1,
   'and holds a sentinel on the pair')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

wd = as_dg1_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when DG-1 left it'
   % CONVERTED_NOW)
co = as_dg1_left('test_code_only.py')
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
    print('  A script-built Delete button wore action-danger without')
    print('  action-secondary, which base needs because danger is a')
    print('  modifier and not a tone. Its own sibling two lines up was')
    print('  already right.')
sys.exit(1 if failed else 0)
