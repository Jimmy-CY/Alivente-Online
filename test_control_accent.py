# -*- coding: utf-8 -*-
"""test_control_accent.py - Section P round P7, 29 Sep 2026.

Demetri, on Household Members: the Save button is green on Add and Edit,
and the Celebrations / Doc Expiry tickboxes are green.

The buttons were one page's drift. The tickbox was not: accent-color was
written on NINE pages in FIVE values, and base owned none of it. A
browser paints a checkbox, a radio and a range with that one property and
nothing else, so what every tick in the system looks like was being
decided nine times over.

base owns it now. Four copies said nothing base does not say and went.
Two - the expense screens' red, with a grey disabled state beside it -
are REPORTED and left, because somebody meant them.

SECTION 3 asks Chromium what colour the tickbox actually is, before and
after. Reading the stylesheet would have missed that three of the nine
copies were the accent written longhand and therefore already correct.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_ctlaccent'
ME = 'test_control_accent.py'
PATCHER = 'apply_control_accent.py'
BASE = 'base.html'
PAGE = 'household_member_management.html'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
ACCENT = 'rgb(14, 124, 139)'
KEEP = ['finance_expense_add.html', 'finance_expense_edit.html']
DROPPED = ['finance_pl_act.html', 'finance/financial_indicators.html',
           'finance/vacancy_management.html',
           'finance/cashflow_forecast.html']

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


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


base = read(alv_tree.path_of(BASE))
page = read(alv_tree.path_of(PAGE))

print('=' * 74)
print('%s - P7, THE TICKBOX TAKES THE HOUSE ACCENT' % ME)
print('=' * 74)

# ==========================================================================
head('1. ONE RULE, IN base')
# ==========================================================================
bb = re.sub(r'/\*.*?\*/', '', css_of(base), flags=re.S)
ok(len(re.findall(r'accent-color\s*:', bb)) == 1,
   'base declares accent-color exactly once',
   re.findall(r'accent-color\s*:[^;]+', bb))
m = re.search(r'input\[type="checkbox"\],\s*input\[type="radio"\],\s*'
              r'input\[type="range"\]\s*\{([^}]*)\}', bb)
ok(m is not None,
   '  and it covers the three controls a browser paints with it - '
   'checkbox, radio and range')
ok(m and 'var(--alv-accent)' in m.group(1),
   '  from the token, not a literal', m.group(1) if m else '')

# ==========================================================================
head('2. NINE COPIES IN FIVE VALUES')
# ==========================================================================
now = {}
for p in alv_tree.templates():
    if alv_tree.rel(p) == BASE:
        continue
    vals = [x.strip() for x in
            re.findall(r'accent-color\s*:\s*([^;}]+)', read(p))]
    if vals:
        now[alv_tree.rel(p)] = vals
ok(sorted(now) == sorted(KEEP),
   'only the two expense screens still paint their own, and they do it '
   'on purpose', sorted(now))
for k in KEEP:
    ok('#dc3545' in now.get(k, []),
       '  %-28s keeps its red' % k, now.get(k))
    ok('#adb5bd' in now.get(k, []),
       '    and its grey for a disabled tick - somebody meant that')

b = alv_tree.path_of(BASE) + SUFFIX
if os.path.isfile(b):
    was = {}
    for p in alv_tree.templates():
        try:
            from alv_rounds import as_left_by
            t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else read(p)
        except Exception:
            t = read(p)
        vals = [x.strip() for x in
                re.findall(r'accent-color\s*:\s*([^;}]+)', t)]
        if vals and alv_tree.rel(p) != BASE:
            was[alv_tree.rel(p)] = vals
    ok(len(was) == 7 and sum(len(v) for v in was.values()) == 9,
       'CONTROL: before this round it was on %d page(s), %d declaration(s), '
       'and base had none' % (len(was), sum(len(v) for v in was.values())),
       sorted(was))
    ok(len(set(v for vs in was.values() for v in vs)) == 5,
       '  in five different values - a tick was green on one screen and '
       'teal on another', sorted(set(v for vs in was.values() for v in vs)))
    ok('accent-color' not in read(b),
       '  and base declared none of it')
else:
    skipped += 3

for name in DROPPED:
    t = read(alv_tree.path_of(name))
    ok('accent-color' not in t,
       '%-34s dropped its copy' % name)

# ==========================================================================
head('3. CHROMIUM PAINTS IT')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def accents(base_text, page_text):
    fx = os.path.join(SCRATCH, 'ctl_%d.html' % len(base_text))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>'
                 '<input type="checkbox" class="sub-check" id="sub">'
                 '<input type="checkbox" id="plain">'
                 '<input type="radio" id="radio">'
                 '<input type="range" id="range">'
                 '</body></html>' % (css_of(base_text), css_of(page_text)))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 900, 'height': 400})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate('''() => {
            const o = {};
            ['sub', 'plain', 'radio', 'range'].forEach(id => {
              o[id] = getComputedStyle(document.getElementById(id))
                        .accentColor;
            });
            return o;
        }''')
        br.close()
    return out


if HAVE_PW:
    got = accents(base, page)
    for k, what in (('sub', 'the Celebrations / Doc Expiry tickbox'),
                    ('plain', 'any other checkbox'),
                    ('radio', 'a radio'),
                    ('range', 'a range slider')):
        ok(got[k] == ACCENT, '%-38s is the house accent' % what, got[k])

    bp = alv_tree.path_of(PAGE) + SUFFIX
    if os.path.isfile(b) and os.path.isfile(bp):
        old = accents(read(b), read(bp))
        ok(old['sub'] != ACCENT,
           'CONTROL: before this round the same tickbox painted %s - the '
           'green Demetri reported' % old['sub'], old)
        ok(old['plain'] != ACCENT,
           '  and a plain checkbox anywhere got whatever the browser '
           'chose, because base said nothing', old['plain'])
    else:
        skipped += 2
else:
    skipped += 6

# ==========================================================================
head('4. THE TWO BUTTONS HE REPORTED')
# ==========================================================================
mk = re.sub(r'<style\b.*?</style>', '', page, flags=re.S)
ok('btn-success' not in mk,
   'neither Save is green any more')
# COUNT THE SAVES, NOT EVERY PRIMARY. The page's own Add Person button
# was already action-primary, so counting the class found three where
# this round changed two.
_saves = mk.count('class="btn action-primary"><i class="fas fa-save">')
ok(_saves == 2,
   '  both SAVE buttons are the house primary - Add and Edit', _saves)
ok(mk.count('class="btn action-primary"') == 3,
   '  alongside Add Person, which already was one',
   mk.count('class="btn action-primary"'))
ok(mk.count('class="btn action-secondary" data-dismiss="modal"') == 2,
   '  and both Cancels are the house secondary')
ok('btn btn-secondary' not in mk,
   '  with no Bootstrap secondary left on the page')

bp = alv_tree.path_of(PAGE) + SUFFIX
if os.path.isfile(bp):
    was = re.sub(r'<style\b.*?</style>', '', read(bp), flags=re.S)
    ok(was.count('btn btn-success') == 2,
       'CONTROL: both Saves were green before this round',
       was.count('btn btn-success'))
    ok('accent-color:#28a745' in read(bp),
       '  and the tickbox was painted #28a745 by the page itself')
else:
    skipped += 2

# ==========================================================================
head('5. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2

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
print('  NOT PROVED HERE: that the expense screens SHOULD keep a red')
print('  tick. They are reported, not judged. Red on a checkbox is not')
print('  a standard this system has - but the grey disabled state beside')
print('  it says somebody was thinking, so it is Demetri\'s call.')
print('=' * 74)
sys.exit(1 if failed else 0)
