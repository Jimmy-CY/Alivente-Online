# -*- coding: utf-8 -*-
"""test_label_law.py - round LF-1, 17 Oct 2026.

AN ABSOLUTE TEXT WIDTH IS A FACT ABOUT THE MACHINE THAT MEASURED IT.

`test_label_fit` asserted that no label in a rebuilt four-across row
wraps, at every width from 1366 down to 992. At 992 a col-md-3 is 168px
and `Include in Occupancy` wraps HERE and does not wrap on Demetri's
Chromium, which renders text about 11% narrower. Neither machine is
wrong; the claim was.

LF-1 keeps the absolute claim at 1024 and above - true on both machines,
and the claim push 2 was about - and asks PJ-2's WRAP LAW at 992.

WHAT THIS SUITE PROVES THAT READING THE DIFF CANNOT

    Section 3 is the one that matters. The obvious form of the law -
    "a wrap is lawful when the box is narrower than the label needs" -
    CANNOT FAIL on a wrapped label, because a box narrower than the
    label is exactly why it wrapped. Written that way the sweep would
    have asserted nothing at all at 992.

    So the round added the half that can fail: a label on ONE line whose
    box is well below what it needs is not fitting, it is being clipped.
    Section 3 RENDERS such a label and shows the check catching it.

    That is the third check found this week that could not fail - a
    Code sentinel on a CSS comment, a scrollWidth test on a date input,
    and this one. The difference is that this one was mine, and it was
    caught before it shipped.

NUMBERS, AND WHICH MACHINE MEASURED THEM

    Every assertion here is a relation between two measurements taken
    in the same browser in the same run. There is no absolute text
    width asserted anywhere in this file, which is the fault it exists
    to correct. See claude/e18_ae_line_probe_16_oct.md for the first of
    the three.
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

SUFFIX = '.bak_labellaw'
SUITE = 'test_label_fit.py'
ME = 'test_label_law.py'
PATCHER = 'apply_label_law.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 96, 102

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


def as_lf1_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


S_PATH = os.path.join(ROOT, SUITE)
NOW = read(S_PATH)
APPLIED = os.path.isfile(S_PATH + SUFFIX)
WAS = read(S_PATH + SUFFIX) if APPLIED else NOW

print('')
print('test_label_law.py - round LF-1, 17 Oct 2026')
print('  suite    : %s' % SUITE)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE NEED IS MEASURED ON THE LABEL, IN THIS BROWSER')
# ==========================================================================
ok(NOW.count('cloneNode(true)') == 2,
   'both probes clone the label they measure - section 4 and the sweep',
   NOW.count('cloneNode(true)'))
ok('white-space:nowrap' in NOW,
   '  with the width released, so it reports what the label asks for')
ok('createElement' not in NOW,
   'and nothing is built by hand - the fault AE-4 took out of '
   'test_ae_line on 16 Oct')
ok(not APPLIED or 'cloneNode' not in WAS,
   'CONTROL: there was no clone in this file before the round')


# ==========================================================================
head('2. THE ABSOLUTE CLAIM SURVIVES WHERE IT IS TRUE')
# ==========================================================================
# 1366, 1280, 1152 and 1024 still assert one line and aligned controls.
# Those hold on both machines, and they are what push 2 was about.
ok('if vw > NARROWEST:' in NOW,
   'above the narrowest width the claim is still absolute')
ok("'%-32s %4d wide  col=%3dpx  one line, aligned'" in NOW,
   '  one line, aligned - word for word as it was')
ok('NARROWEST' in NOW and 'wrap law' in NOW.lower(),
   'and only the narrowest width asks the law')

# THE CONTROL IS UNTOUCHED. Section 5 renders the OLD labels and
# requires them to wrap - it is the half that proves section 4 can fail,
# and a round that quietly softened it would have broken the guard while
# appearing to fix it.
ok('5. THE CONTROL' in NOW, 'section 5 CONTROL is still there')
ok("ok(any(h > ONE_LINE for h in m['labH']) and not m['aligned']," in NOW,
   '  and asserts exactly what it asserted before')
if APPLIED:
    a = WAS[WAS.find('5. THE CONTROL'):WAS.find('6.', WAS.find('5. THE'))]
    b = NOW[NOW.find('5. THE CONTROL'):NOW.find('6.', NOW.find('5. THE'))]
    ok(a == b, '  byte for byte', 'the CONTROL section changed')
else:
    skip('the CONTROL is byte-identical', 'not applied')


# ==========================================================================
head('3. THE HALF OF THE LAW THAT CAN FAIL')
# ==========================================================================
# A WRAPPED LABEL ALWAYS HAS A BOX NARROWER THAN IT NEEDS. That is why
# it wrapped. So "a wrap is lawful when box < need" exempts every wrap
# there can be, and a sweep written that way asserts nothing.
#
# The round therefore added the other direction: a label on ONE line
# whose box is well below what it needs is not fitting - it is clipped.
# This section renders one and shows the check catching it.
ok('clipped, not wrapped' in NOW,
   'the sweep looks for a label that is CLIPPED rather than wrapped')
ok('not bad and not clipped' in NOW,
   '  and fails the width when it finds one')

try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

PROBE = """() => {
  const r = e => e.getBoundingClientRect(), o = {};
  document.querySelectorAll('label[data-k]').forEach(l => {
    const twin = l.cloneNode(true);
    twin.style.cssText = 'position:absolute;left:-9999px;width:auto;'
      + 'white-space:nowrap';
    l.parentNode.appendChild(twin);
    const need = Math.ceil(r(twin).width);
    twin.remove();
    o[l.dataset.k] = [Math.round(r(l).height), Math.round(r(l).width), need];
  });
  return o;
}"""

# THE BOX IS PINNED NARROW ON PURPOSE, and 90px is a fixture constant
# rather than a claim about the application: it only has to be less than
# the label needs in whatever browser runs this, and the suite MEASURES
# that rather than assuming it. Section 3's first check fails loudly if
# it ever stops being narrow enough.
ROW = ('<div class="form-row">'
       '<div style="width:90px"><div class="form-group">'
       '<label data-k="0">Include in Occupancy</label>'
       '<input type="text" class="form-control"></div></div>'
       '<div style="width:90px"><div class="form-group">'
       '<label data-k="1" style="white-space:nowrap;overflow:hidden;'
       'display:block">Include in Occupancy</label>'
       '<input type="text" class="form-control"></div></div>'
       '</div>')

if not have_pw or not os.path.isfile(BOOT):
    skip('the clipped label in a browser', 'playwright or fixture absent')
else:
    from playwright.sync_api import sync_playwright

    base_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                    read(alv_tree.path_of('base.html')),
                                    re.S | re.I))
    fx = os.path.join(SCRATCH, 'lf1.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head>'
                 '<body><div class="main-content with-sidebar">'
                 '<div class="container-fluid">%s</div></div></body></html>'
                 % (read(BOOT), base_css, ROW))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 992, 'height': 800})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        pg.wait_for_timeout(90)
        got = pg.evaluate(PROBE)
        br.close()

    ONE_LINE = 26
    free_h, free_w, free_need = got['0']
    clip_h, clip_w, clip_need = got['1']
    print('      free    h %2d  box %3d  needs %3d' % (free_h, free_w,
                                                       free_need))
    print('      clipped h %2d  box %3d  needs %3d' % (clip_h, clip_w,
                                                       clip_need))

    ok(clip_need > clip_w + 4,
       'the fixture box IS narrower than the label needs: %d against %d'
       % (clip_w, clip_need), (clip_w, clip_need))
    ok(clip_w < clip_need - 4 and clip_h <= ONE_LINE,
       '  and the label is held to ONE LINE in it - the defect the new '
       'check looks for', (clip_w, clip_need, clip_h))
    ok(free_w < free_need and free_h > ONE_LINE,
       '  and the same label left alone WRAPS instead, in the same box',
       (free_w, free_need, free_h))
    # THE TWO ARE TOLD APART BY THE RULE THE ROUND WROTE.
    def verdict(h, w, need):
        if h > ONE_LINE:
            return 'lawful wrap' if w < need else 'wrapped with room'
        return 'clipped' if w < need - 4 else 'fits'
    ok(verdict(clip_h, clip_w, clip_need) == 'clipped',
       '  and the rule calls it: %s' % verdict(clip_h, clip_w, clip_need))
    ok(verdict(free_h, free_w, free_need) == 'lawful wrap',
       '  and the other: %s' % verdict(free_h, free_w, free_need))
    ok(verdict(40, 200, 150) == 'wrapped with room',
       '  a wrap with room to spare is still a defect, and still named')


# ==========================================================================
head('4. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_aeprobe' in _r
       and _r.index(SUFFIX) > _r.index('.bak_aeprobe'),
       '  and sits after .bak_aeprobe - AE-4 took the first of the three '
       'font-register suites, this one takes the second', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'white-space:nowrap'" in ps1,
   'and holds a sentinel on the clone that measures the need')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

wd = as_lf1_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when LF-1 left it'
   % CONVERTED_NOW)
co = as_lf1_left('test_code_only.py')
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
    print('  test_label_fit asserted an absolute text width at the one')
    print('  viewport where this sandbox and his Chromium disagree.')
    print('  Above it the claim is unchanged. At 992 a wrap must have a')
    print('  reason - and a label held to one line in a box too narrow')
    print('  for it is the reason that can fail.')
sys.exit(1 if failed else 0)
