# -*- coding: utf-8 -*-
"""test_held_contrast.py - round E-1b, 11 Oct 2026.

THREE MORE OFF WAITING. TWO NEEDED NO APPLICATION CHANGE AT ALL.

    python test_held_contrast.py

Run from the repo root, after apply_held_contrast.py.

SECTION 3 IS THE ONE WORTH READING. test_contrast reported SEVEN live
white-on-colour failures when it was widened, one of them at 1.63 - a
ratio the colour involved cannot produce. It was reading each CRS page
through as_left_by, which for a page THIS round never touched returns
the backup taken by the first LATER round that did. That is somebody
else's moment. Live, those rules do not exist: the CRS colour rounds
converted them. No colour changes in this round, because nothing is
wrong with any colour.

SECTION 4 RECORDS A MISTAKE OF MY OWN. A suite need not call its
template root `T` - button_sweep says TPL, modal_heads says ROOT - and
a survey that assumed T found no sites, changed nothing, and reported
"passes widened" about a file it had not altered. One of the two it
cleared that way really does still fail.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import alv_cssrules                                             # noqa: E402
import alv_rounds                                               # noqa: E402
import alv_tree                                                 # noqa: E402

SUFFIX = '.bak_heldcon'
PATCHER = 'apply_held_contrast.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

RELEASED = ('test_contrast.py', 'test_compound_rules.py')
# test_modal_heads still fails when widened, on the reason recorded
# against it. test_button_sweep PASSES widened and is still held, for a
# better reason: its narrow root rebuilds a pre-sweep tree from that
# round's own backups, so it is a stated position and not debt.
# MH-2, 13 Oct 2026 - test_modal_heads comes off this list. E-1b
# wrote that it STILL FAILED WIDENED, on the reason recorded
# against it, and that was true: widened it found the Recipe View
# close strip. What E-1b could not see is that widening it also
# found four Bootstrap danger headers in the second root. MH-2
# converted those and left the close strip on the LEAVE list with
# its reason, which is what E-1b was waiting for.
STILL_HELD = ('test_button_sweep.py',)
DEAD_PAGE = 'crs/submission_detail.html'
WAITING_AFTER = 6
CEILING_AFTER = 43

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ok   %s' % name)
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL %s%s' % (name, ('  [%s]' % extra) if extra else ''))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def before(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced,')
        print('     so it cannot run until %s has.' % PATCHER)
        sys.exit(1)
    return read(b)


def css_of(text):
    return '\n'.join(re.sub(r'/\*.*?\*/', '', text[a:b], flags=re.S)
                     for a, b in alv_cssrules.style_spans(text))


print(__doc__.strip().split('\n')[0])

# ---------------------------------------------------------------------- 1
head('1. SCOPE')

check('%s is on disk' % PATCHER, os.path.isfile(os.path.join(ROOT, PATCHER)))
for n in RELEASED + STILL_HELD:
    check('  %s is still here' % n, os.path.isfile(os.path.join(ROOT, n)))

# ---------------------------------------------------------------------- 2
head('2. THE DEAD HALF OF THE SELECTOR')

p = alv_tree.path_of(DEAD_PAGE)
now, was = read(p), before(p)
check('the .form-field half is gone', '.form-field' not in now)
check('  CONTROL: and the backup proves it was there',
      '.form-field .field-error' in was)

# THE HALF THAT STAYS MUST BE THE WORKING ONE.
m = re.search(r'(?<![-\w])\.field-error\s*\{([^{}]*)\}', css_of(now))
check('  and .field-error still carries the rule', m is not None,
      'the rule went with it')
if m:
    check('    unchanged - size, colour and weight',
          'font-size' in m.group(1) and 'color' in m.group(1)
          and 'font-weight' in m.group(1),
          ' '.join(m.group(1).split())[:50])

worn = sum(len(re.findall(r'class="[^"]*\bfield-error\b[^"]*"',
                          alv_tree.code_only(read(q))))
           for q in alv_tree.templates())
ff = sum(len(re.findall(r'(?<![-\w])form-field(?![-\w])', read(q)))
         for q in alv_tree.templates())
check('field-error is worn by %d element(s) across the tree' % worn,
      worn >= 20, '%d' % worn)
check('  and form-field is now worn, declared and mentioned NOWHERE',
      ff == 0, '%d left' % ff)
print('        It appeared once in the whole tree - in that selector -')
print('        and never in markup. The third dead selector in three')
print('        rounds, after the .req rule and the ecipe-header corpse.')

# ---------------------------------------------------------------------- 3
head('3. test_contrast READS A PAGE IT NEVER TOUCHED, LIVE')

ct = read(os.path.join(ROOT, 'test_contrast.py'))
check('it has a scoped reader', 'def scoped(p):' in ct)
check('  which falls back to the live file when there is no backup',
      re.search(r'return now\(p\) if os\.path\.exists\(p \+ SUFFIX\) '
                r'else read\(p\)', ct) is not None)
check('  and the corpus walk uses it', 'styles_of(scoped(' in ct)
check('  CONTROL: while the checks about pages the round DID touch still '
      'use now()', 'styles_of(now(BASE))' in ct)
print('        as_left_by is right for a page this round touched and')
print('        wrong for one it did not: for an untouched page it freezes')
print('        at the first LATER round that happened to open it. Widened,')
print('        this suite read the CRS pages at PQ-1 moment and reported')
print('        seven white-on-colour failures already fixed, one scoring')
print('        1.63 - a number the colour involved cannot produce.')

# A GATE READS CODE, NOT THE RECORD OF CODE. The replacement keeps a
# comment saying WAS `len(found) == 3`, so searching the whole file for
# that string finds the obituary and calls it the corpse. This is the
# rule this project keeps relearning, and the first draft of this very
# check broke it.
# E15, 13 Oct 2026 - WAS a private copy. Nine had grown
# under four names and three algorithms, and all three
# algorithms were wrong. alv_tree owns it now.
# payloads=True, the default: this file asks what the code
# DOES, so a triple-quoted payload is code and survives.
code_lines = alv_tree.python_code_only


check('  and the count of what remains is derived, not pinned',
      'len(found) == 3' not in code_lines(ct)
      and 'are all named dead' in ct)
check('    CONTROL: and the backup proves it WAS pinned at three',
      'len(found) == 3' in code_lines(
          before(os.path.join(ROOT, 'test_contrast.py'))))

# ---------------------------------------------------------------------- 4
head('4. THREE WIDENED AND RELEASED - AND ONE THAT IS NOT')

for n in RELEASED:
    src = read(os.path.join(ROOT, n))
    check('  %s walks through alv_tree' % n, 'alv_tree.walk3()' in src)
    # A SUITE MAY NOT CALL ITS ROOT `T`. button_sweep says TPL and
    # modal_heads says ROOT. A survey that assumed T found no sites,
    # changed nothing, and reported "passes widened" - which was true
    # of a file it had not altered.
    own = re.findall(r'os\.walk\((T|TPL|ROOT)\)', src)
    check('    and walks no root of its own', not own, '%s' % own)
    check('    off alv_tree.WAITING', n not in alv_tree.WAITING)
    check('    on alv_tree.CONVERTED', n in alv_tree.CONVERTED)

for n in STILL_HELD:
    check('%s is STILL held' % n, n in alv_tree.WAITING)
# MH-2, 13 Oct 2026 - the reason did not go away, it MOVED. It
# used to be a line on alv_tree.WAITING explaining why the suite
# could not be widened; it is now a named entry on that suite's
# own LEAVE list, which is a stronger place for it - a reader of
# the suite finds it, where a reader of alv_tree never would.
# Asking the live WAITING for it after the suite is released is
# asking the wrong object.
check('  and the Recipe View reason moved onto the suite LEAVE '
      'list, where a reader of the suite will find it',
      'Recipe View' in read(os.path.join(ROOT,
                                        'test_modal_heads.py')),
      'not on the LEAVE list either')
print('        modal_heads, widened against ROOT - which is what IT calls')
print('        the template directory - still fails on the Recipe View')
print('        close strip. That reason is not stale.')
print('        button_sweep PASSES widened and is held anyway: its')
print('        os.walk(TPL) rebuilds a PRE-SWEEP tree from that round own')
print('        backups. Widening it would copy CRS files into a tree the')
print('        sweep never covered. A narrow root that is a stated')
print('        position is not debt, and X0 said so before I did.')

# E-10, 11 Oct 2026 - WAS `len(WAITING) == WAITING_AFTER`. E-1b
# repaired this exact shape in test_held_four and wrote the rule down
# in the same round: a pinned AGGREGATE was never a count or a
# decision. What E-1b claims is that ITS TWO came off, checked one by
# one above, and that claim is true forever.
check('neither of the two this round released is still held',
      not [n for n in RELEASED if n in alv_tree.WAITING],
      '%s' % [n for n in RELEASED if n in alv_tree.WAITING])
check('  CONTROL: and WAITING is not empty - %d still held'
      % len(alv_tree.WAITING), len(alv_tree.WAITING) > 0)

# ---------------------------------------------------------------------- 5
head('5. THE CEILING FELL, AND BOTH PLACES THAT PIN IT AGREE')

x0 = read(os.path.join(ROOT, 'test_tree_roots.py'))
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))


def pin(text, name):
    m2 = re.search(r'%s = (\d+)' % name, text)
    return int(m2.group(1)) if m2 else None


# E-10, 11 Oct 2026 - WAS `== CEILING_AFTER`, pinned at 43. The
# ceiling is the whole programme's number and it falls every time any
# round converts a census. What matters here - that the two files
# agree, and that E-1b's conversion made it FALL - is checked below
# and against this round's own backup, and both hold forever.
check('the walker ceiling is a real number in both places',
      pin(x0, 'WALKERS_OWN_ROOT_MAX') is not None,
      '%s' % pin(x0, 'WALKERS_OWN_ROOT_MAX'))
check('  and test_waiting_down agrees',
      pin(wd, 'CEILING') == pin(x0, 'WALKERS_OWN_ROOT_MAX'),
      '%s vs %s' % (pin(wd, 'CEILING'), pin(x0, 'WALKERS_OWN_ROOT_MAX')))
check('  CONTROL: and it FELL - the file says it may only fall',
      pin(x0, 'WALKERS_OWN_ROOT_MAX')
      < pin(before(os.path.join(ROOT, 'test_tree_roots.py')),
            'WALKERS_OWN_ROOT_MAX'))
check('CONVERTED_N agrees with the live register',
      pin(wd, 'CONVERTED_N') == len(alv_tree.CONVERTED),
      '%s vs %d' % (pin(wd, 'CONVERTED_N'), len(alv_tree.CONVERTED)))
check('  and WAITING_N too',
      pin(wd, 'WAITING_N') == len(alv_tree.WAITING),
      '%s vs %d' % (pin(wd, 'WAITING_N'), len(alv_tree.WAITING)))

# ---------------------------------------------------------------------- 6
head('6. REGISTERED, ON THE GATE')

ps = read(PS1)
check('%s is in the $suites list' % ME, "'%s'" % ME in ps)
check('  and this round is on alv_rounds.ROUNDS', SUFFIX in alv_rounds.ROUNDS)
check('  and this suite is on alv_tree.CONVERTED', ME in alv_tree.CONVERTED)

# ----------------------------------------------------------------------
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
print('=' * 74)
if FAILED:
    print('')
    for f in FAILED:
        print('  FAILED  %s' % f)
print('')
print('  NOT PROVED HERE: that the four still held are stale or')
print('  real. Three of them have never been widened against the')
print('  root they actually use, which is the mistake this round')
print('  exists partly to record.')
sys.exit(1 if FAIL else 0)
