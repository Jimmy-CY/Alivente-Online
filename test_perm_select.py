# -*- coding: utf-8 -*-
"""test_perm_select.py - round NV-1a, 16 Oct 2026.

A TICKED BOX IS A SELECTION. IT IS NOT A VERDICT.

Demetri: "whay are the Modules on the User Permission Page Green. They
should be teal."

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 4 COMPUTES the contrast ratios out of base's own token
    values rather than quoting the numbers this round wrote down, so a
    later change to a token is caught here and not on a screen.
    Section 6 RENDERS the tile and TOGGLES THE CLASS, because the whole
    justification for deleting the script's four assignments is that the
    class alone paints both states. Its CONTROL puts the inline style
    back and shows the class doing nothing - which is what was actually
    on the screen before this round.

A COLOUR IS A FACT AND IS THE SAME ON EVERY MACHINE - unlike a text
width, which is why section 6 asserts computed colours and never a
measured string. See the sixth failure in standard_delivery_preflight.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The six edits are this round's snapshot: before is .bak_permselect,
    after is the file. The token values, the contrast arithmetic and the
    gate registration are INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That every --alv-good in the application is a verdict. Eight
    references on this page, seven sites, measured one at a time. The
    general sweep would be a census round and is not this one.
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
    from alv_rounds import as_left_by
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_permselect'
PAGE = 'user_permissions.html'
ME = 'test_perm_select.py'
PATCHER = 'apply_perm_select.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 85, 81
NOTE = 'NV-1a, 16 Oct 2026 - this round own'
N_GOOD_WAS, N_GOOD_NOW = 8, 1

DOT = ("color:{% if target_user.is_active %}var(--alv-good)"
       "{% else %}var(--alv-bad){% endif %}")

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


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t, re.S))


def rule(css, sel):
    """The one rule body for a selector, or None."""
    m = re.search(re.escape(sel) + r'\s*\{([^}]*)\}', css)
    return m.group(1) if m else None


PATH = alv_tree.path_of(PAGE)
NOW = read(PATH)

# THIS ROUND'S OWN BACKUP IS THE BEFORE, AND as_left_by IS NOT IT.
# as_left_by(path, suffix, read) answers "as the round with this suffix
# LEFT it" - it walks ROUNDS FORWARD and returns the NEXT round's
# backup, falling back to the live file when no later round exists. For
# the newest round in the list that is the file itself, so every CONTROL
# built on it compared the page with the page and failed while the round
# was correct. The first cut of this suite did exactly that, in seven
# places.
#
# as_left_by is for reading ANOTHER round's snapshot. A round's own
# before is its own .bak_ file, read directly - and when it is absent
# the live file is the honest answer, so the controls FAIL and nothing
# raises. See step 4 of standard_delivery_preflight.
WAS = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else read(PATH)
BACKED_OUT = not os.path.isfile(PATH + SUFFIX)
C_NOW, C_WAS = css_of(code_only(NOW)), css_of(code_only(WAS))
J_NOW, J_WAS = js_of(code_only(NOW)), js_of(code_only(WAS))
B_NOW, B_WAS = code_only(NOW), code_only(WAS)

BASE = read(alv_tree.path_of('base.html'))


# ==========================================================================
head('1. A GRANTED MODULE WEARS THE ACCENT, AND DID NOT')
# ==========================================================================
for sel, tok, what in (
        ('.permission-item.granted', '--alv-accent-soft', 'the row wash'),
        ('.permission-item.granted .permission-icon', '--alv-accent',
         'the icon tile'),
        ('.permission-status.granted', '--alv-accent-ink',
         'the 11px status line')):
    body_now, body_was = rule(C_NOW, sel), rule(C_WAS, sel)
    ok(body_now is not None and re.search(
        re.escape(tok) + r'(?![\w-])', body_now),
       '%-22s %s takes %s' % (what, sel.split()[-1], tok), body_now)
    ok(body_was is not None and '--alv-good' in body_was,
       '  CONTROL: it read the good family before this round', body_was)

ok('--alv-accent-ink' in (rule(C_NOW, '.permission-status.granted') or ''),
   'and the 11px line takes the INK token, not the accent itself - 11px '
   'is the smallest type on the page')

ok(re.search(r'color:var\(--alv-accent-ink\)', B_NOW)
   and 'fa-crown' in B_NOW,
   'the superuser note beside the bar takes the ink token too, which is '
   'what .superuser-notice above it has carried since B-3')


# ==========================================================================
head('2. AND THE ONE REAL VERDICT ON THE PAGE KEEPS GREEN')
# ==========================================================================
n_was = len(re.findall(r'--alv-good(?:-soft)?', B_WAS))
n_now = len(re.findall(r'--alv-good(?:-soft)?', B_NOW))
ok(n_was == N_GOOD_WAS,
   'CONTROL: the page named the good family %d time(s) before this round'
   % N_GOOD_WAS, n_was)
ok(n_now == N_GOOD_NOW,
   'and names it %d time(s) now' % N_GOOD_NOW, n_now)
ok(DOT in B_NOW,
   '  and the survivor is the account active/inactive dot - a user either '
   'IS or IS NOT active, and nothing on this screen changes it')
ok('--alv-bad' in B_NOW,
   '  which still has --alv-bad on its other arm, so the dot is a pair '
   'and not a decoration')


# ==========================================================================
head('3. THE COLOUR WAS DECLARED THREE TIMES. IT IS DECLARED ONCE.')
# ==========================================================================
ok('icon.style.' in J_WAS,
   'CONTROL: the script wrote the tile colour before this round',
   re.search(r'icon\.style\.[^\n]*', J_WAS).group(0) if 'icon.style.'
   in J_WAS else '')
ok('icon.style.' not in J_NOW,
   'the script writes no colour at all now')
ok(re.search(r'class="permission-icon"[^>]*style=', B_WAS) is not None,
   'CONTROL: and the icon carried an inline style, which BEAT the rule')
ok(re.search(r'class="permission-icon"[^>]*style=', B_NOW) is None,
   'the icon carries no inline style now')

# FOUR, NOT TWO. The denied branch's pair had to go with the granted
# pair: left behind, it would put an inline background on the element
# that .granted cannot beat, so one toggle off would be permanent.
gone = len(re.findall(r'icon\.style\.\w+\s*=', J_WAS))
ok(gone == 4,
   'FOUR assignments went, not the two in the granted branch - the '
   'denied pair would have left an inline background the class cannot '
   'beat', gone)

for keep in ("item.classList.add('granted')",
             "item.classList.remove('granted')",
             "status.className = 'permission-status granted'",
             "status.className = 'permission-status denied'"):
    ok(keep in J_NOW, '  and %s stays - it is what the deleted '
                      'assignments stood in front of' % keep)


# ==========================================================================
head('4. THE CONTRAST, COMPUTED FROM BASE RATHER THAN QUOTED')
# ==========================================================================
def tokval(name):
    m = re.search(r'--' + name + r'\s*:\s*(#[0-9a-fA-F]{3,6})', BASE)
    return m.group(1) if m else None


def lum(hexv):
    h = hexv.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.03928
                   else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


TOK = {n: tokval(n) for n in ('alv-accent', 'alv-accent-ink',
                              'alv-accent-soft', 'alv-good',
                              'alv-good-soft', 'alv-ink', 'alv-on-accent')}
missing = [k for k, v in TOK.items() if not v]
if missing:
    skip('the contrast arithmetic', 'base does not declare %s'
         % ', '.join(missing))
else:
    r_glyph = ratio(TOK['alv-on-accent'], TOK['alv-accent'])
    r_glyph_was = ratio(TOK['alv-on-accent'], TOK['alv-good'])
    r_line = ratio(TOK['alv-accent-ink'], '#ffffff')
    r_line_was = ratio(TOK['alv-good'], '#ffffff')
    r_row = ratio(TOK['alv-ink'], TOK['alv-accent-soft'])
    r_row_was = ratio(TOK['alv-ink'], TOK['alv-good-soft'])

    ok(r_glyph >= 4.5,
       'white on the accent tile is %.2f:1 - AA for the 15px glyph'
       % r_glyph, '%s on %s' % (TOK['alv-on-accent'], TOK['alv-accent']))
    ok(abs(r_glyph - r_glyph_was) < 0.5,
       '  and it was %.2f:1 on the good token, so the tile did not get '
       'worse' % r_glyph_was)
    ok(r_line >= 4.5,
       'the accent ink on paper is %.2f:1 for the 11px status line'
       % r_line, TOK['alv-accent-ink'])
    ok(r_line > r_line_was,
       '  which is BETTER than the %.2f:1 it had, and 11px is where that '
       'matters most' % r_line_was, '%.2f -> %.2f' % (r_line_was, r_line))
    ok(abs(r_row - r_row_was) < 0.5,
       'and the row wash is %.2f:1 against %.2f:1 - unchanged to the eye'
       % (r_row, r_row_was))
    # A CONTROL ON THE ARITHMETIC ITSELF. A ratio function that always
    # answers comfortably reads exactly like a palette that passes.
    ok(ratio('#ffffff', '#f5f5f5') < 1.2,
       'CONTROL: white on near-white computes %.2f:1, so this is a real '
       'measurement and not a probe that always passes'
       % ratio('#ffffff', '#f5f5f5'))


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok(ME in ps, '%s runs this suite' % PS1)
ok(ME in read(os.path.join(ROOT, 'alv_tree.py')),
   'alv_tree.CONVERTED names it')
# A FLOOR, NOT A PIN. Three later rounds ship in the same push and each
# moves these counters, so a suite that pins the number it set fails as
# soon as its sibling applies. The house shape is `at least`, plus the
# round's OWN NOTE, which is permanent.
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  and CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
   'alv_rounds.ROUNDS names %s' % SUFFIX)
ok("Text = 'font-size:12px; color:var(--alv-accent-ink)'" in ps,
   'and the gate carries a row for a string THIS ROUND introduced - the '
   'selector .permission-item.granted was there long before it, so a '
   'row naming that could never have failed')
ok("Text = 'icon.style.background'" in ps,
   '  and one that refuses the colour being written in three places again')
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
ok(NOTE in wd,
   'the converted count carries this round\'s note, so the number it '
   'moved to is recorded whatever later rounds do to it')
co = read(os.path.join(ROOT, 'test_code_only.py'))
ok(NOTE in co, 'and so does the alias count')
ok(re.search(r'CONVERTED_N = (\d+)', wd)
   and int(re.search(r'CONVERTED_N = (\d+)', wd).group(1)) >= CONVERTED_NOW,
   '  and the live count is at least %d' % CONVERTED_NOW,
   re.search(r'CONVERTED_N = (\d+)', wd).group(1))
ok(re.search(r'ok\(len\(aliased\) == (\d+),', co)
   and int(re.search(r'ok\(len\(aliased\) == (\d+),',
                     co).group(1)) >= ALIAS_NOW,
   '  and the live alias count is at least %d' % ALIAS_NOW)


# ==========================================================================
head('6. RENDERED - AND THE CLASS ALONE PAINTS BOTH STATES')
# ==========================================================================
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

MARKUP = """<label class="permission-item" id="row">
  <div class="permission-icon" id="tile"><i></i></div>
  <div><div class="permission-label">Invoices</div>
  <div class="permission-status" id="line">no access</div></div>
</label>"""

# THE CONTROL'S markup is the page as it was: the inline style that beat
# the rule, spelled out, so the probe shows what was actually on screen.
MARKUP_WAS = MARKUP.replace(
    '<div class="permission-icon" id="tile">',
    '<div class="permission-icon" id="tile" '
    'style="background:var(--alv-surface);">')

LOOK = """() => {
  const row = document.getElementById('row');
  const tile = document.getElementById('tile');
  const line = document.getElementById('line');
  const g = e => getComputedStyle(e);
  const grab = () => ({row: g(row).backgroundColor,
                       edge: g(row).borderTopColor,
                       tile: g(tile).backgroundColor,
                       line: g(line).color});
  const off = grab();
  row.classList.add('granted');
  line.className = 'permission-status granted';
  const on = grab();
  return {off: off, on: on};
}"""

if not have_pw or not os.path.isfile(BOOT):
    skip('the tile in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright

    def fixture(name, markup):
        p = os.path.join(SCRATCH, name)
        with open(p, 'w', encoding='utf-8') as fh:
            # TRANSITIONS OFF, AND THIS IS NOT TIDINESS.
            # .permission-item carries `transition: all 0.2s`, so
            # getComputedStyle read straight after a class change
            # returns the FIRST FRAME of the transition - the colour the
            # element is leaving, not the one it arrives at. The first
            # cut of section 6 read transparent for the row and surface
            # for the tile and reported that the class paints nothing,
            # on a tree where it paints correctly.
            #
            # Waiting 300ms would also work and would be a timing race.
            # The claim is WHICH COLOUR THE CLASS ARRIVES AT, so the
            # animation is removed rather than waited out.
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<style>%s</style><style>%s</style><style>%s</style>'
                     '<style>body{margin:0;background:#fff}'
                     '*,*::before,*::after{transition:none !important;'
                     'animation:none !important}</style>'
                     '</head><body>%s</body></html>'
                     % (read(BOOT), css_of(BASE), C_NOW, markup))
        return p

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            ctx = br.new_context(viewport={'width': 1280, 'height': 600})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, fixture('perm.html', MARKUP))
            pg.wait_for_timeout(50)
            m = pg.evaluate(LOOK)
            a, b = m['on'], m['off']

            ok(a['tile'] != b['tile'],
               'adding the class alone repaints the tile: %s -> %s'
               % (b['tile'], a['tile']), m)
            ok(a['row'] != b['row'],
               '  and the row wash: %s -> %s' % (b['row'], a['row']))
            ok(a['line'] != b['line'],
               '  and the 11px line: %s -> %s' % (b['line'], a['line']))
            if TOK['alv-accent']:
                want = tuple(int(TOK['alv-accent'].lstrip('#')[i:i + 2], 16)
                             for i in (0, 2, 4))
                got = tuple(int(x) for x in
                            re.findall(r'\d+', a['tile'])[:3])
                ok(got == want,
                   '  and the tile computes to --alv-accent %s, not a '
                   'colour near it' % TOK['alv-accent'], '%s vs %s'
                   % (got, want))
            if TOK['alv-accent-ink']:
                want = tuple(int(TOK['alv-accent-ink']
                                 .lstrip('#')[i:i + 2], 16)
                             for i in (0, 2, 4))
                got = tuple(int(x) for x in
                            re.findall(r'\d+', a['line'])[:3])
                ok(got == want,
                   '  and the line computes to --alv-accent-ink %s'
                   % TOK['alv-accent-ink'], '%s vs %s' % (got, want))
            ctx.close()

            # ------------------------------------------------- CONTROL
            # THE INLINE STYLE BEAT THE RULE, and this is the whole
            # reason the markup edit and the script deletions are part
            # of the same round. With it present, the class does
            # nothing to the tile - which is what was on the screen.
            ctx = br.new_context(viewport={'width': 1280, 'height': 600})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, fixture('perm_was.html', MARKUP_WAS))
            pg.wait_for_timeout(50)
            w = pg.evaluate(LOOK)
            ok(w['on']['tile'] == w['off']['tile'],
               'CONTROL: put the inline style back and the class changes '
               'the tile NOT AT ALL - so a round that edited only the '
               'CSS would have changed nothing on screen',
               '%s / %s' % (w['off']['tile'], w['on']['tile']))
            ok(w['on']['row'] != w['off']['row'],
               '  while the ROW still repaints, because nothing was '
               'inline there - which is how one element came to be '
               'painted by three declarations and the others by one')
            ctx.close()
        finally:
            br.close()


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NV-1a: a granted permission module is a SELECTION and wears the')
print('  accent. Green is a verdict in this system - paid, passing,')
print('  healthy - and the only verdict on this page is the account')
print('  active/inactive dot, which keeps --alv-good and is now the only')
print('  good reference left.')
print('')
print('  The icon colour was declared in THREE places, and the inline')
print('  style beat the other two. It is declared once, in the')
print('  stylesheet, and section 6 proves the class alone paints both')
print('  states.')
print('')
sys.exit(1 if failed else 0)
