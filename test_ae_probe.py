# -*- coding: utf-8 -*-
"""test_ae_probe.py - round AE-4, 16 Oct 2026.

THE SUITE WAS MEASURING AN IMITATION OF THE CONTROL.

`test_ae_line` asked what a date input needs by BUILDING one: a fresh
<input type=date> dressed in typed padding and a `font: inherit` that
picked up the grid's 16px rather than the input's 14px. That stand-in
measures 21px wider than the control it stood for, and those 21 pixels
were six failures against a page that was correct.

WHAT THIS SUITE PROVES THAT READING THE DIFF CANNOT
    Section 2 rebuilds all three in one browser - the old imitation, a
    clone of the real control, and the control itself - and reports the
    gap. The round's reason is therefore RE-MEASURED on whatever machine
    runs it, not remembered from the machine that found it. If Chromium
    ever changes how it sizes a date input, this says so.

    Section 3 proves the check that was WRITTEN AND THROWN AWAY. The
    obvious instrument for "wide enough to show a date" is "does it
    overflow its own box", and it cannot work here: an <input type=date>
    never reports a scrollWidth larger than its clientWidth, because the
    date widget compresses its own fields instead of overflowing. Drawn
    at 150px, 170px and 171px: equal every time. A check that cannot
    fail is not a check, and this section is why it is not in the suite.

WHAT THE ROUND DOES NOT DO
    It does not move the 170px pin - the pin is correct, and section 4
    asserts that not one line of live CSS changed on the page. All six
    intrinsic candidates were drawn before this was written; every one
    of them is NARROWER than 170.

E23 - THE CENSUS THAT HAD TO FOLLOW
    Population of one. Section 5 re-runs it, so a suite that starts
    imitating a control tomorrow is caught by this one.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    The asserted numbers here are RELATIONS between three renders taken
    in the same browser in the same run - imitation wider than clone,
    clone no wider than the pin. There is no absolute text width
    asserted anywhere in this file, which is the fault it exists to
    correct. See claude/e18_ae_line_probe_16_oct.md.
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


import glob
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

SUFFIX = '.bak_aeprobe'
PAGE = 'act_expense.html'
SUITE = 'test_ae_line.py'
ME = 'test_ae_probe.py'
PATCHER = 'apply_ae_probe.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
STYLE = re.compile(r'<style[^>]*>(.*?)</style>', re.S | re.I)

CONVERTED_NOW, ALIAS_NOW = 95, 101
PIN = 170

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


def as_ae4_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


S_PATH = os.path.join(ROOT, SUITE)
P_PATH = alv_tree.path_of(PAGE)
S_NOW = read(S_PATH)
P_NOW = read(P_PATH)
APPLIED = os.path.isfile(S_PATH + SUFFIX)
S_WAS = read(S_PATH + SUFFIX) if APPLIED else S_NOW
P_WAS = read(P_PATH + SUFFIX) if os.path.isfile(P_PATH + SUFFIX) else P_NOW

print('')
print('test_ae_probe.py - round AE-4, 16 Oct 2026')
print('  suite    : %s' % SUITE)
print('  page     : %s' % PAGE)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE PROBE IS A CLONE, NOT A COPY MADE BY HAND')
# ==========================================================================
ok('cloneNode(true)' in S_NOW,
   '%s clones the control it measures' % SUITE)
ok(S_NOW.count('cloneNode(true)') == 1,
   '  once - one instrument, not two', S_NOW.count('cloneNode(true)'))
ok("getElementById('fromDateInput')" in S_NOW,
   '  and clones THE control on the page, by id')
ok('createElement' not in S_NOW,
   'and builds no control of its own anywhere in the file')
ok(not APPLIED or 'createElement' in S_WAS,
   'CONTROL: it built one, until this round')
ok(not APPLIED or 'padding:10px 14px' in S_WAS,
   'CONTROL: dressed in padding typed in by hand')
# ASKED OF THE CODE, NOT OF THE PROSE. The replacement NAMES the old
# spelling in its own comment, explaining what went wrong - so a gate
# that searched the whole file would refuse its own output. That fault
# was hit three times on 16 Oct; this one tests where the spelling
# sits.
_live = [ln for ln in S_NOW.split('\n')
         if 'padding:10px 14px' in ln and not ln.strip().startswith('//')
         and not ln.strip().startswith('#')]
ok(not _live,
   'and that spelling survives only in the comment that explains it',
   _live)

# THE CLAIM DID NOT CHANGE, only the instrument under it.
ok('ALL FIVE ARE ON ONE LINE' in S_NOW,
   "AE-1's claim is untouched - five controls, one line")
ok(S_NOW.count('>= need') == 1,
   "and AE-3's claim is still made exactly once",
   S_NOW.count('>= need'))

# scrollWidth IS NOT IN THE FILE, and section 3 says why.
ok(not re.search(r'\.scrollWidth\b', S_NOW),
   'the suite does not measure scrollWidth - see section 3')


# ==========================================================================
head('2. THE 21 PIXELS, RE-MEASURED HERE')
# ==========================================================================
# The round's reason is not remembered from the machine that found it.
# All three are drawn in one browser in one run, and what is asserted is
# the RELATION between them.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

_src = read(os.path.join(ROOT, SUITE))
_i = _src.index('def fixture_panel')
_j = _src.index('\n\n\n', _i)
_ns = {'re': re, 'os': os, 'code_only': code_only, 'alv_tree': alv_tree}
exec(_src[_i:_j], _ns)
fixture_panel = _ns['fixture_panel']

THREE = """() => {
  const real = document.getElementById('fromDateInput');
  real.value = '2026-12-31';
  const g = e => getComputedStyle(e);
  const w = e => Math.ceil(e.getBoundingClientRect().width);

  /* THE IMITATION, exactly as test_ae_line used to build it. */
  const probe = document.createElement('input');
  probe.type = 'date'; probe.value = '2026-12-31';
  probe.style.cssText = 'position:absolute;left:-9999px;width:auto;'
    + 'font:inherit;padding:10px 14px;border:2px solid;box-sizing:border-box';
  real.parentNode.appendChild(probe);

  /* THE CLONE, exactly as it builds it now. */
  const twin = real.cloneNode(true);
  twin.removeAttribute('id');
  twin.value = '2026-12-31';
  twin.style.cssText = 'position:absolute;left:-9999px;width:auto';
  real.parentNode.appendChild(twin);

  const out = {
    real: {w: w(real), pad: g(real).paddingLeft, font: g(real).fontSize},
    probe: {w: w(probe), pad: g(probe).paddingLeft, font: g(probe).fontSize},
    twin: {w: w(twin), pad: g(twin).paddingLeft, font: g(twin).fontSize}};
  probe.remove(); twin.remove();
  return out;
}"""


def fixture(name, text, extra_css=''):
    f = os.path.join(SCRATCH, name)
    base_css = '\n'.join(STYLE.findall(read(alv_tree.path_of('base.html'))))
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style><style>%s</style>'
                 '<style>%s</style></head>'
                 '<body><div class="main-content with-topnav"><br/>'
                 '<div class="container">%s</div></div></body></html>'
                 % (read(BOOT), base_css,
                    '\n'.join(STYLE.findall(text)), extra_css,
                    fixture_panel(text)))
    return f


if not have_pw or not os.path.isfile(BOOT):
    skip('the three measurements', 'playwright or the fixture is absent')
    three = None
else:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fixture('ae4.html', P_NOW))
        pg.wait_for_timeout(80)
        three = pg.evaluate(THREE)
        ctx.close()

        # Section 3 runs in the same browser, below.
        CLIP = """(px) => {
          const e = document.getElementById('fromDateInput');
          e.value = '2026-12-31';
          e.style.width = px + 'px';
          return {w: px, clientW: e.clientWidth, scrollW: e.scrollWidth};
        }"""
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fixture('ae4b.html', P_NOW))
        pg.wait_for_timeout(80)
        clips = [pg.evaluate(CLIP, px) for px in (120, 150, 170, 171, 240)]
        ctx.close()
        br.close()

if three:
    for k in ('real', 'probe', 'twin'):
        print('      %-6s %4dpx   padding-left %-6s font %s'
              % (k, three[k]['w'], three[k]['pad'], three[k]['font']))
    ok(three['probe']['w'] > three['twin']['w'],
       'the hand-built imitation is WIDER than the control it stood for: '
       '%d against %d' % (three['probe']['w'], three['twin']['w']))
    ok(three['probe']['pad'] != three['twin']['pad'],
       '  because its padding was typed in, not inherited: %s against %s'
       % (three['probe']['pad'], three['twin']['pad']))
    ok(three['probe']['font'] != three['twin']['font'],
       '  and `font: inherit` took the GRID font, not the control font: '
       '%s against %s' % (three['probe']['font'], three['twin']['font']))
    ok(three['twin']['pad'] == three['real']['pad']
       and three['twin']['font'] == three['real']['font'],
       'while the clone carries the real cascade exactly: %s / %s'
       % (three['twin']['pad'], three['twin']['font']))
    # THE RELATION THAT MATTERS, and the reason the page is correct.
    ok(three['real']['w'] >= three['twin']['w'],
       'and the pin clears what the control asks for: %d >= %d'
       % (three['real']['w'], three['twin']['w']))
    # WHETHER THE IMITATION CLEARS THE PIN IS A FACT ABOUT THE MACHINE,
    # and asserting it was the third layer of this round to make that
    # mistake. Here the stand-in measures 175 against a 170px pin, so
    # the suite was red. On Demetri's Chromium it measures 169 against
    # the same 170, so the suite was GREEN there - which is exactly why
    # test_ae_line passed every push while failing every sweep.
    #
    # The gap is under one percent on his machine. The two renderers
    # differ by about eleven. A margin thinner than the disagreement
    # between the machines is not a claim, it is noise with a decimal
    # point, and every assertion in this file that survived is a
    # relation wide enough to outlive it:
    #
    #     padding   14px against 12px   - exact, both machines
    #     font      16px against 14px   - exact, both machines
    #     probe > twin   175/149 here, 169/149 there - 13% and 13%
    #     pin >= twin    170/149 and 170/149          - clears either way
    print('      and whether that stand-in CLEARS the 170px pin is a '
          'fact about')
    print('      the machine: %d against 170 here. The sweep was red and '
          'his gate' % three['probe']['w'])
    print('      was green on the same file, and this is the whole of '
          'why.')


# ==========================================================================
head('3. THE CHECK THAT WAS WRITTEN AND THROWN AWAY')
# ==========================================================================
# "Wide enough to show a date" sounds like "does not overflow its own
# box", and that check was written first. It cannot work: an
# <input type=date> compresses its own fields rather than overflowing,
# so scrollWidth never exceeds clientWidth however narrow the control
# gets. This section is the evidence, kept so nobody writes it again.
if not three:
    skip('scrollWidth against clientWidth', 'no browser')
else:
    for c in clips:
        print('      width %3dpx   clientWidth %3d   scrollWidth %3d'
              % (c['w'], c['clientW'], c['scrollW']))
    ok(all(c['scrollW'] <= c['clientW'] + 1 for c in clips),
       'at every width drawn, scrollWidth never exceeds clientWidth',
       [(c['w'], c['clientW'], c['scrollW']) for c in clips])
    narrow = [c for c in clips if c['w'] < three['twin']['w']]
    ok(bool(narrow) and all(c['scrollW'] <= c['clientW'] + 1
                            for c in narrow),
       '  INCLUDING below what the control asks for - %s - where a '
       'clipping control is exactly what we have'
       % ', '.join('%dpx' % c['w'] for c in narrow))
    ok(True,
       'so a scrollWidth test could not have failed, and a check that '
       'cannot fail is not a check')


# ==========================================================================
head('4. THE PAGE STOPS QUOTING AN IMITATION AS A MEASUREMENT')
# ==========================================================================
ok('A date input needs 165' not in P_NOW,
   'the AE-1 note no longer states 165 as a measured fact')
ok(not APPLIED or 'A date input needs 165' in P_WAS,
   'CONTROL: it did, in those words')
ok('162px on a phone' not in P_NOW,
   "and no longer calls the phone width a defect - it was not one")
ok('IMITATION' in P_NOW.upper() and '154' in P_NOW,
   'it says what the number really was, and what a clone asks for')

# THE PIN DID NOT MOVE, and no live CSS did either.
#
# AS AE-4 LEFT THE PAGE, NOT LIVE. This compared the LIVE page against
# AE-4's backup, so the moment another round touched act_expense.html
# the claim "this round changed no live code" was reading SOMEBODY
# ELSE'S change. DG-1 added a class to one button on 17 Oct and that is
# exactly what happened.
#
# Every "nothing else moved" claim has this shape, and every one of
# them is true on the day it is written - because the round that wrote
# it is the newest round. as_left_by is what makes it stay true.
_p_left = (as_left_by(alv_tree.path_of(PAGE), SUFFIX, read)
           if as_left_by else P_NOW)
live_now = [ln.strip() for ln in code_only(_p_left).split('\n') if ln.strip()]
live_was = [ln.strip() for ln in code_only(P_WAS).split('\n') if ln.strip()]
ok(any('%dpx %dpx' % (PIN, PIN) in ln for ln in live_now),
   'the %dpx pin is still there' % PIN)
ok(live_now == live_was,
   'and NOT ONE LINE OF LIVE CSS CHANGED - this round is prose on the '
   'page and an instrument in the suite',
   '\n'.join(set(live_now) ^ set(live_was)) or 'no differing lines')


# ==========================================================================
head('5. E23 - HOW MANY OTHER SUITES MEASURE AN IMITATION')
# ==========================================================================
# A fault found in one file is a hypothesis about the others, not a
# finding about them. This counts rather than guesses, and keeps
# counting - a suite that starts imitating a control tomorrow fails here.
builds, clones = [], []
for f in sorted(glob.glob(os.path.join(ROOT, 'test_*.py'))):
    t = read(f)
    n = os.path.basename(f)
    if re.search(r"createElement\(\s*['\"](input|select|textarea)", t):
        builds.append(n)
    if 'cloneNode(' in t:
        clones.append(n)
# THIS FILE IS EXEMPT, AND SAYS SO. Section 2 rebuilds the imitation on
# purpose, because the round's reason has to be re-measurable rather
# than remembered. It is the one place in the repo where building a
# control is the point, so the census names it rather than quietly
# skipping it.
ok(ME in builds,
   'this suite builds one - on purpose, to re-measure the gap in '
   'section 2')
others = [b for b in builds if b != ME]
ok(not others,
   'and NO OTHER suite builds an input, select or textarea to measure '
   'it', others)
ok(len(clones) >= 4,
   'and %d suite(s) clone the real control instead: %s'
   % (len(clones), ', '.join(c[:-3] for c in clones[:6])))
ok(ME in clones or 'cloneNode(' in read(os.path.join(ROOT, SUITE)),
   '  this round put %s among them' % SUITE)


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_wsmembers' in _r
       and _r.index(SUFFIX) > _r.index('.bak_wsmembers'),
       '  and sits after .bak_wsmembers', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'const twin = model.cloneNode(true)'" in ps1,
   'and holds a sentinel on the clone')
ok("Text = 'createElement'; Absent = $true" in ps1,
   'and an ABSENT one on createElement - the CONSTRUCT, not the prose: '
   'a sentinel on the old padding spelling refused this round own '
   'output in seven suites at once')
ok("Text = 'A date input needs 165'; Absent = $true" in ps1,
   'and another on the number the page used to quote')
# AND THAT ONE IS NOT A Code SENTINEL, which would be vacuous: the note
# lives in a CSS comment and code_only BLANKS those, so the row would be
# absent in every version ever written and discriminate in none.
# test_sentinels catches exactly that by trying each row against 45
# older copies - and it did, in this round.
_row = [ln for ln in ps1.split('\n') if 'A date input needs 165' in ln
        and 'Absent' in ln]
ok(len(_row) == 1 and 'Code = $true' not in _row[0],
   '  and reads the RAW file, not code_only - a Code sentinel on a CSS '
   'comment can never fail', _row)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

wd = as_ae4_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when AE-4 left it'
   % CONVERTED_NOW)
co = as_ae4_left('test_code_only.py')
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
    print('  test_ae_line was measuring a date input it built itself,')
    print('  21px wider than the control it stood for. It clones the')
    print('  control now. The page was always correct, and the 170px')
    print('  pin does not move - only the sentence under it that quoted')
    print('  the imitation as a measurement.')
sys.exit(1 if failed else 0)
