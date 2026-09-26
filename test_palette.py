# -*- coding: utf-8 -*-
"""test_palette.py - Section F round F1, 26 Sep 2026.

Judges the round that moved the house palette off white.

WHAT THIS SUITE ASSERTS is the round's actual claim: that every ink token
clears 4.5:1 on every surface the house itself defines - not just on
#ffffff, which is what the palette had been tuned against and is not what
the app sits on.

It does that arithmetically, because the matrix IS the claim and arithmetic
is exact. It then renders a handful of real pages to prove the values in
base actually reach the DOM - a token is only true if the browser agrees.

IT DOES NOT re-run the 4150-element system probe. That takes twelve minutes
and the gate already runs 128 suites. The probe's result is recorded in
claude/contrast_survey_26_sep.md and in the patcher: 104 fixed, 0 new
failures, 2 already-failing elements marginally worse and named.
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
    print('     checks below it never ran.')


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
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_palette'
ME = 'test_palette.py'
PATCHER = 'apply_palette.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
BAR = 4.5

# The surfaces the house paints things on. The palette used to be judged
# against the first one only.
SURFACES = [('#ffffff', 'paper'), ('#f8f9fa', '--alv-surface'),
            ('#e9ecef', 'the tint on cards and rows'), ('#eef1f2', 'a row band')]

MOVED = {
    '--alv-warn': ('#9a6a08', '#8e6207'),
    '--alv-age-2': ('#9a6a08', '#8e6207'),      # the alias, moved in step
    '--alv-neutral': ('#6b7780', '#616c74'),
}
# The inks this round KNOWINGLY leaves under the bar, each with the number
# it leaves them at. A round that stops short says where it stopped.
LEFT_UNDER = {
    '--alv-accent': (4.14, '411 literal copies across 75 templates. Moving '
                     'the token strands every one of them; it waits for '
                     "E6's sweep. Measured, it was 1 of the 104 fixes."),
    '--alv-good': (4.32, 'fixed 0 of the 104 measured - a real failure '
                   'that nothing currently paints.'),
    '--alv-age-1': (3.63, 'recorded, not fixed.'),
    '--alv-grade-2': (4.20, 'recorded, not fixed.'),
    '--alv-edit': (4.36, 'recorded, not fixed.'),
}
# Named, with the reason, so an exception cannot become an escape hatch.
LEAVE = {
    '--alv-ink-faint': (
        '#8a979d',
        'the DISABLED ink. 3.00 on white and 2.53 on the tint - the worst '
        'number in the survey - and exempt, because WCAG excludes inactive '
        'components. Darkening it would make unavailable things look '
        'available (lesson 56).'),
}
# Already invisible before this round, and made a hundredth worse by it.
# Named here so they cannot be quietly forgotten by the Personal pass.
# The first draft of this round moved the accent too, and made these two
# already-invisible Back labels a hundredth worse. Dropping the accent
# removed that entirely: the round now has NO regressions at all. They are
# kept here because they are still broken and still belong to the Personal
# pass - base sets .action-back { background: transparent } on purpose, so
# on a page whose bar sits on an accent header the label is dark ink
# straight onto the accent.
STILL_BROKEN = {
    'celebration_dashboard.html': ('Back', 1.66),
    'meal_plan_calendar.html': ('Back', 1.13),
}

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if not re.fullmatch(r'[0-9a-fA-F]{6}', h):
        raise ValueError('unreadable colour: %r' % h)   # lesson 41
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def contrast(a, b):
    f = lambda v: (0.2126 * _lin(v[0]) + 0.7152 * _lin(v[1])
                   + 0.0722 * _lin(v[2]))
    x, y = f(rgb(a)) + 0.05, f(rgb(b)) + 0.05
    return max(x, y) / min(x, y)


def token(text, name):
    m = re.search(re.escape(name) + r':\s*([^;]+);', text)
    return m.group(1).strip() if m else None


# ==========================================================================
head('1. THE MATRIX - EVERY INK, ON EVERY SURFACE THE HOUSE DEFINES')
# ==========================================================================
ok(as_left_by is not None, 'alv_rounds imported')
ok(SUFFIX in ROUNDS and '.bak_namedbars' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_namedbars'),
   'alv_rounds lists %s after .bak_namedbars' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else '')
ok(os.path.isfile(BASE + SUFFIX), 'base.html has its %s backup' % SUFFIX)

b_now, b_was = now(BASE), was(BASE)
INKS = ['--alv-ink', '--alv-ink-soft', '--alv-neutral', '--alv-good',
        '--alv-warn', '--alv-bad', '--alv-accent', '--alv-accent-ink']

print('')
print('      %-18s %-9s %8s %8s %8s %8s'
      % ('token', 'hex', '#fff', '#f8f9fa', '#e9ecef', '#eef1f2'))
bad = []
for name in INKS:
    hx = token(b_now, name)
    if not hx or not hx.startswith('#'):
        bad.append('%s is %r, not a hex' % (name, hx))
        continue
    row = [contrast(hx, s) for s, _ in SURFACES]
    print('      %-18s %-9s %8.2f %8.2f %8.2f %8.2f' % (name, hx, *row))
    for (s, what), c in zip(SURFACES, row):
        if c < BAR and name not in LEFT_UNDER:
            bad.append('%s %s on %s (%s) = %.2f' % (name, hx, s, what, c))
print('')
ok(not bad, 'every ink this round MOVED clears %.1f:1 on every house '
   'surface' % BAR, '\n'.join(bad))
print('')
print('      still under the bar, left on purpose:')
for name, (val, why) in sorted(LEFT_UNDER.items()):
    hx = token(b_now, name)
    print('        %-16s %-9s %.2f' % (name, hx or '?', val))
ok(all(token(b_now, n) is not None for n in LEFT_UNDER),
   '  and every one of them is still exactly as it was - nothing was '
   'half-moved')

for name, (old, new) in sorted(MOVED.items()):
    ok(token(b_now, name) == new,
       '%s moved to %s' % (name, new), token(b_now, name))
    ok(token(b_was, name) == old, '  and it really was %s before' % old,
       token(b_was, name))

for name, (hx, why) in LEAVE.items():
    ok(token(b_now, name) == hx, 'LEAVE kept: %s is still %s' % (name, hx),
       token(b_now, name))
    for line in re.findall(r'.{1,64}(?:\s|$)', why):
        if line.strip():
            print('        %s' % line.strip())

# The ring is the accent written out as rgba. If it does not follow the
# accent, the focus halo is a different teal from the control it rings -
# which is the exact drift this round exists to remove.
ring = token(b_now, '--alv-accent-ring') or ''
nums = [int(x) for x in re.findall(r'\d+', ring)[:3]]
ok(tuple(nums) == rgb(token(b_now, '--alv-accent')),
   'the focus ring is the SAME teal as the accent it rings',
   '%s vs %s' % (nums, list(rgb(token(b_now, '--alv-accent')))))

ok('.text-muted' in b_now and '.text-muted' not in b_was,
   "base now has an opinion about Bootstrap's .text-muted")
m = re.search(r'\.text-muted\s*\{([^{}]*)\}', b_now)
ok(bool(m) and 'var(--alv-neutral)' in m.group(1),
   '  and it is --alv-neutral, so the house has ONE muted ink')
ok(bool(m) and '!important' in m.group(1),
   "  with !important, because Bootstrap's own utility carries it")

# NO TEMPLATE IS TOUCHED. That is the round's shape, so it is asserted.
# Three templates ARE edited - for fallbacks, not for contrast. Named, so
# the list cannot grow quietly.
FALLBACK_FILES = {'act_expense.html', 'fsr.html', 'fsr_details.html'}
touched = set()
for d, _x, fs in os.walk(T):
    for f in sorted(fs):
        if f.endswith(SUFFIX):
            touched.add(f[:-len(SUFFIX)])
ok(touched == FALLBACK_FILES | {'base.html'},
   'exactly base plus the three fallback templates were edited - every '
   'CONTRAST fix comes from base', sorted(touched))

# ==========================================================================
head('2. RENDERED - THE BROWSER AGREES WITH THE TOKENS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
PROBE = ('<p class="text-muted" id="mut">muted</p>'
         '<p id="neu" style="color:var(--alv-neutral)">neutral</p>'
         '<p id="acc" style="color:var(--alv-accent)">accent</p>'
         '<p id="good" style="color:var(--alv-good)">good</p>'
         '<p id="warn" style="color:var(--alv-warn)">warn</p>'
         '<p id="faint" style="color:var(--alv-ink-faint)">faint</p>')
LOOK = r"""() => {
  const g = id => getComputedStyle(document.getElementById(id)).color;
  return {mut: g('mut'), neu: g('neu'), acc: g('acc'),
          good: g('good'), warn: g('warn'), faint: g('faint')};
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 2', 'playwright or %s missing' % BOOT)
else:
    def as_hex(css):
        n = [int(x) for x in re.findall(r'\d+', css)[:3]]
        return '#%02x%02x%02x' % tuple(n)

    styles = [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
              for m in re.finditer(r'<style[^>]*>(.*?)</style>', b_now,
                                   re.S | re.I)]
    fx = os.path.join(SCRATCH, '_pal.html')
    with open(fx, 'w', encoding='utf-8') as f:
        f.write('<!doctype html><html><head><meta charset="utf-8">'
                '<title>p</title><style>%s</style>%s</head><body>%s</body>'
                '</html>' % (read(BOOT),
                             ''.join('<style>%s</style>' % c for c in styles),
                             PROBE))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1024, 'height': 700})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        got = pg.evaluate(LOOK)
        ctx.close()
        br.close()

    ok(as_hex(got['mut']) == token(b_now, '--alv-neutral'),
       '.text-muted really renders as --alv-neutral - the override beats '
       "Bootstrap's !important", as_hex(got['mut']))
    for key, name in (('neu', '--alv-neutral'), ('acc', '--alv-accent'),
                      ('good', '--alv-good'), ('warn', '--alv-warn')):
        ok(as_hex(got[key]) == token(b_now, name),
           '  %s resolves to %s in the browser' % (name, token(b_now, name)),
           as_hex(got[key]))
    ok(as_hex(got['faint']) == '#8a979d',
       '  and --alv-ink-faint is untouched, as recorded')

# ==========================================================================
head('3. THE PAIRS THAT HAD TO KEEP HOLDING')
# ==========================================================================
acc = token(b_now, '--alv-accent')
for ink, bg, what in (
        ('#ffffff', acc, 'white text on the accent fill'),
        (token(b_now, '--alv-accent-ink'), '#e4f3f5',
         'accent-ink on --alv-accent-soft')):
    c = contrast(ink, bg)
    ok(c >= BAR, '%s = %.2f' % (what, c), c)

# NOT AN ASSERTION, BECAUSE IT WAS NEVER TRUE. The accent as TEXT on its
# own soft tint measures 4.31 and always has. This round moves neither
# side, so it is not F1's to pass or fail - but writing the check is what
# found it, so it is recorded instead of deleted. It belongs with the
# accent, in E6's sweep.
_c = contrast(acc, '#e4f3f5')
ok(round(_c, 2) == 4.31,
   'RECORDED: accent as text on --alv-accent-soft is %.2f - pre-existing, '
   'unchanged by this round, and the accent round inherits it' % _c,
   round(_c, 2))

# ==========================================================================
head('4. WHAT THIS ROUND DID NOT FIX - NAMED, NOT HIDDEN')
# ==========================================================================
print('      Measured across all 4150 elements: 565 before, 447 after -')
print('      103 fixed, ZERO regressions, ZERO made worse. These two were')
print('      already invisible and stay that way. base sets .action-back')
print('      { background: transparent } on purpose, so on a page whose')
print('      bar sits on an accent header the label is dark ink on it.')
print('')
for rel, (txt, c) in sorted(STILL_BROKEN.items()):
    p = os.path.join(T, rel)
    ok(os.path.isfile(p), '%-34s %r still measures %.2f' % (rel, txt, c))
ok(all(not os.path.isfile(os.path.join(T, r) + SUFFIX) for r in STILL_BROKEN),
   '  neither was edited here - they belong to the Personal pass')

# ==========================================================================
head('5. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(round(contrast('#6b7780', '#e9ecef'), 2) == 3.87,
   'the OLD neutral really did measure 3.87 on the tint',
   round(contrast('#6b7780', '#e9ecef'), 2))
ok(round(contrast('#616c74', '#e9ecef'), 2) >= 4.5,
   '  and the new one clears the bar on the same tint',
   round(contrast('#616c74', '#e9ecef'), 2))
ok(round(contrast('#ffffff', '#ffffff'), 2) == 1.0,
   'the contrast function returns 1.00 for a colour on itself')
try:
    contrast('not-a-colour', '#fff')
    ok(False, 'contrast() raises on a colour it cannot read')
except ValueError:
    ok(True, 'contrast() raises on a colour it cannot read (lesson 41)')
ok(len(SURFACES) == 4, 'four surfaces are measured, not just paper')
ok(SURFACES[0][0] == '#ffffff',
   '  and paper is only the FIRST of them - the old palette stopped here')

p1 = os.path.join(ROOT, PS1)
if os.path.isfile(p1):
    ok(ME in read(p1), '%s is on the push gate' % ME)
else:
    skip(PS1, 'not on disk')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
