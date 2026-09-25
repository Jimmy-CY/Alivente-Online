# -*- coding: utf-8 -*-
"""test_avatar.py - Section D, round D9: one avatar, not five.

    python test_avatar.py

Run from the repo root, after apply_avatar.py.

  1. Base owns it once, painted from the tokens, and no page keeps a copy.
  2. RENDERED: the five discs, before and after - shape, size, paint, and
     THE CONTRAST OF THE INITIALS, which is what the round is for.
  3. The sidebar constraint: the disc still separates from #343a40 behind
     it. That is what ruled out the house gradient, so it is measured.
  4. Every disc kept its class and its initials; base kept no inline hex.
  5. Scope, registered, on the gate.

Run it against the REVERTED tree and it must FAIL, not crash.
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

import math
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
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_avatar'
ME = 'test_avatar.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
WSE = os.path.join(T, 'workspace_edit.html')
UAD = os.path.join(T, 'user_administration.html')
PRO = os.path.join(T, 'my_profile.html')
SIDEBAR = '#343a40'          # what the sidebar disc sits on

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


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def css_of(t):
    return '\n'.join(styles_of(t))


def nocomment(c):
    return re.sub(r'/\*.*?\*/', '', c, flags=re.S)


# --- the colour maths, run rather than quoted ----------------------------
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _nums(s):
    return [float(x) for x in re.findall(r'[\d.]+', s)[:3]]


def _relL(s):
    v = _nums(s)
    if len(v) < 3:
        return 0.0
    r, g, b = (_lin(x) for x in v)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    x, y = _relL(a) + 0.05, _relL(b) + 0.05
    return max(x, y) / min(x, y)


def worst_contrast(bg, ink):
    """The text against the WORST part of its background.

    A gradient has no backgroundColor - it reads rgba(0,0,0,0), which
    scores as a perfect pass. D8 met that from the other side; here it
    would have hidden the very fault this round exists to fix, because
    four of the five discs were painted with one."""
    stops = re.findall(r'rgba?\([^)]*\)', bg)
    if not stops:
        return contrast(bg, ink)
    return min(contrast(s, ink) for s in stops)


def _oklab(s):
    v = _nums(s)
    r, g, b = (_lin(x) for x in v)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    t = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, t = (x ** (1.0 / 3) if x > 0 else 0 for x in (l, m, t))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * t,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * t,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * t)


def dE(a, b):
    x, y = _oklab(a), _oklab(b)
    return 100 * math.sqrt(sum((p - q) ** 2 for p, q in zip(x, y)))


def hexrgb(h):
    h = h.lstrip('#')
    return 'rgb(%d, %d, %d)' % tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


B_NOW, B_WAS = now(BASE), was(BASE)
MARK = re.compile(r'/\* ===== ALV AVATAR v1\b.*?'
                  r'/\* ===== /ALV AVATAR v1 ===== \*/', re.S)
# name, file, old class, new class list, size, font
FIVE = [
    ('sidebar   ', BASE, 'sidebar-avatar',
     'alv-avatar alv-avatar--ring', 32, '12px'),
    ('nav inline', BASE, None,
     'alv-avatar alv-avatar--md alv-avatar--ring', 36, '13px'),
    ('member    ', WSE, 'member-avatar', 'alv-avatar', 32, '12px'),
    ('user admin', UAD, 'user-avatar', 'alv-avatar alv-avatar--lg',
     38, '15px'),
    ('my profile', PRO, 'photo-placeholder', 'alv-avatar alv-avatar--xl',
     80, '28px'),
]

# ==========================================================================
head('1. BASE OWNS IT ONCE, AND NO PAGE KEEPS A COPY')
# ==========================================================================
blocks = MARK.findall(B_NOW)
ok(len(blocks) == 1, 'base carries the ALV AVATAR block, opened and closed, '
   'once', len(blocks))
ok(not MARK.search(B_WAS), '  CONTROL: it was not there before this round')
BODY = nocomment(blocks[0]) if blocks else ''
for sel in ('.alv-avatar {', '.alv-avatar img {', '.alv-avatar--md {',
            '.alv-avatar--lg {', '.alv-avatar--xl {',
            '.alv-avatar--ring {'):
    ok(sel in BODY, 'it defines %s' % sel[:-2])
ok('var(--alv-accent)' in BODY and 'var(--alv-on-accent)' in BODY,
   'painted from the tokens')
ok('linear-gradient' not in BODY,
   'and FLAT - the house gradient ends on accent-ink, 11.7 from the '
   'sidebar, so the disc would have melted into it')
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', BODY)))
ok(not hexes, 'no hex literal survives in the rules', hexes)

for label, path, oldcls, newcls, _s, _f in FIVE:
    src_now, src_was = now(path), was(path)
    if oldcls:
        ok(('.%s' % oldcls) not in nocomment(css_of(src_now)),
           '%s: .%s is gone from the page' % (label, oldcls))
        ok(('.%s' % oldcls) in nocomment(css_of(src_was)),
           '  CONTROL: it was there before')
    ok('class="%s"' % newcls in src_now
       or 'class="%s" id=' % newcls in src_now,
       '%s: the disc wears %s' % (label, newcls),
       [ln.strip()[:70] for ln in src_now.split('\n')
        if 'alv-avatar' in ln][:3])

for label, path, _o, _n, _s, _f in FIVE:
    if path is BASE:
        continue
    ok('#667eea' not in now(path) and '#764ba2' not in now(path),
       '%s: no purple left on the page at all' % label)
ok('#667eea' not in nocomment(B_NOW) and '#764ba2' not in nocomment(B_NOW),
   'base: no purple left in its CSS or markup')
ok('#667eea' in B_NOW,
   '  and the block still SAYS #667eea, in the paragraph recording why it '
   'went - which is why every check above strips comments first')
ok(re.search(r'style="[^"]*linear-gradient[^"]*"', B_NOW) is None,
   'base writes no inline gradient any more - it told every page not to '
   'and was doing it itself')
ok(re.search(r'style="[^"]*linear-gradient[^"]*"', B_WAS) is not None,
   '  CONTROL: it did before')

# ==========================================================================
head('2. RENDERED - THE FIVE DISCS, AND THE CONTRAST OF THE INITIALS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'

LOOK = r"""() => Array.from(document.querySelectorAll('.probe')).map(e => {
  const s = getComputedStyle(e), r = e.getBoundingClientRect();
  return {w: Math.round(r.width), h: Math.round(r.height),
          radius: s.borderTopLeftRadius,
          bg: s.backgroundImage !== 'none' ? s.backgroundImage
                                           : s.backgroundColor,
          ink: s.color, size: s.fontSize, weight: s.fontWeight,
          display: s.display, border: s.borderTopWidth};
})"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2 and 3', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def look(br, css_blocks, markup):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_av_%04d.html' % n[0])
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>a</title><style>%s</style>%s</head>'
                '<body style="background:%s">%s</body></html>'
                % (boot, ''.join('<style>%s</style>' % c
                                 for c in css_blocks), SIDEBAR, markup))
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        # --- AFTER: the component, from base alone -------------------
        after_mk = ''.join('<div class="probe %s">DM</div>' % f[3]
                           for f in FIVE)
        after = look(br, styles_of(B_NOW), after_mk)
        ok(len(after) == 5, 'five discs render from base alone', len(after))

        # --- BEFORE: each old rule, from the page that owned it ------
        before, names = [], []
        for label, path, oldcls, _n, _s, _f in FIVE:
            if oldcls:
                rows = look(br, styles_of(B_WAS) + styles_of(was(path)),
                            '<div class="probe %s">DM</div>' % oldcls)
            else:
                # the inline one: the style attribute IS the rule
                m = re.search(r'<div style="(width:36px[^"]*)">',
                              was(BASE))
                rows = look(br, styles_of(B_WAS),
                            '<div class="probe" style="%s">DM</div>'
                            % (m.group(1) if m else ''))
            before += rows
            names.append(label)
        ok(len(before) == 5, 'and five rendered as they were', len(before))

        if len(after) == 5 and len(before) == 5:
            print('')
            print('      %-11s %-7s %-30s %s' % ('disc', 'size', 'paint',
                                                 'initials'))
            for tag, rows in (('BEFORE', before), ('AFTER', after)):
                for nm, c in zip(names, rows):
                    print('      %-6s %-11s %3dx%-3d %-30s %5.2f'
                          % (tag, nm, c['w'], c['h'],
                             ','.join(x.replace(' ', '') for x in
                                      (re.findall(r'rgba?\([^)]*\)', c['bg'])
                                       or [c['bg']]))[:30],
                             worst_contrast(c['bg'], c['ink'])))
            print('')
            bad = [(nm, round(worst_contrast(c['bg'], c['ink']), 2))
                   for nm, c in zip(names, before)
                   if float(c['size'][:-2]) < 24
                   and worst_contrast(c['bg'], c['ink']) < 4.5]
            ok(len(bad) == 4,
               'CONTROL: FOUR of the five failed 4.5:1 against their own '
               'initials - %s' % bad, bad)
            big = [(nm, round(worst_contrast(c['bg'], c['ink']), 2))
                   for nm, c in zip(names, before)
                   if float(c['size'][:-2]) >= 24]
            ok(len(big) == 1 and big[0][1] >= 3.0,
               '  and the fifth is LARGE text at 28px, where 3.0 is the '
               'bar and it passed - %s' % big, big)
            worst = min(worst_contrast(c['bg'], c['ink']) for c in after)
            ok(worst >= 4.5, 'AFTER: every disc passes 4.5:1 - worst %.2f'
               % worst,
               [(nm, round(worst_contrast(c['bg'], c['ink']), 2))
                for nm, c in zip(names, after)])
            ok(len(set(c['bg'] for c in after)) == 1,
               '  and all five are the SAME paint')
            ok(after[0]['bg'] == hexrgb('#0e7c8b'),
               '  and it is the accent', after[0]['bg'])
            ok(all(c['ink'] == 'rgb(255, 255, 255)' for c in after),
               '  with white initials on all five')
            ok(all(c['radius'] == '50%' for c in after),
               '  every one still a circle')
            ok(all(c['display'] == 'flex' for c in after),
               '  and still flex-centred')
            got = [(c['w'], c['h']) for c in after]
            wantsz = [(f[4], f[4]) for f in FIVE]
            ok(got == wantsz,
               '  the five sizes survive as modifiers: %s'
               % ', '.join('%d' % f[4] for f in FIVE), (wantsz, got))
            ok([c['size'] for c in after] == [f[5] for f in FIVE],
               '  and each size draws its own text size',
               ([f[5] for f in FIVE], [c['size'] for c in after]))
            ok(after[0]['border'] == '2px' and after[2]['border'] == '0px',
               '  the ring is a modifier - the sidebar disc has one, the '
               'member disc does not',
               (after[0]['border'], after[2]['border']))

            # ==========================================================
            head('3. IT STILL SEPARATES FROM THE SIDEBAR BEHIND IT')
            # ==========================================================
            # This is what ruled out the house gradient, so it is measured
            # rather than recorded in a comment.
            d = dE(after[0]['bg'], hexrgb(SIDEBAR))
            ok(d >= 15, 'the disc is %.1f from the sidebar %s (floor 15)'
               % (d, SIDEBAR))
            ink = dE(hexrgb('#0a5e6a'), hexrgb(SIDEBAR))
            ok(ink < 15,
               '  CONTROL: --alv-accent-ink would have been %.1f - which '
               'is why the gradient ending on it was rejected' % ink)
            soft = dE(hexrgb('#55606b'), hexrgb(SIDEBAR))
            ok(soft < 15,
               '  CONTROL: and --alv-ink-soft %.1f, rejected the same way'
               % soft)
        br.close()

# ==========================================================================
head('4. EVERY DISC KEPT ITS INITIALS, AND ITS id')
# ==========================================================================
for label, path, _o, _n, _s, _f in FIVE:
    a, b = now(path), was(path)
    ok(sorted(re.findall(r'\bid="([^"]+)"', a))
       == sorted(re.findall(r'\bid="([^"]+)"', b)),
       '%s: every id is still there' % label)
ok('id="photoPlaceholder"' in now(PRO),
   '  including photoPlaceholder, which my_profile addresses by id')
for label, path, _o, _n, _s, _f in FIVE:
    a, b = now(path), was(path)
    ok(a.count('first_name|first|upper') == b.count('first_name|first|upper'),
       '%s: the initials are still built the same way' % label)

# ==========================================================================
head('5. SCOPE, THEN REGISTERED AND ON THE GATE')
# ==========================================================================
for label, path, _o, _n, _s, _f in FIVE:
    if path is BASE:
        continue
    a, b = now(path), was(path)
    # BALANCED IN ITSELF, not EQUAL TO THE BACKUP. A first draft compared
    # the counts to the backup's and failed on all three pages - of course
    # they differ: the round deleted a rule, so the braces that opened and
    # closed it are gone in pairs. What has to hold is that none is left
    # half-open.
    ok(a.count('{') == a.count('}'),
       '%s: braces balance' % label, (a.count('{'), a.count('}')))
    ok(b.count('{') - a.count('{') == b.count('}') - a.count('}'),
       '  and what went, went in matched pairs (%d)'
       % (b.count('{') - a.count('{')))
    ok(a.count('{%') == b.count('{%') and a.count('{{') == b.count('{{'),
       '  every Django tag is still there')
ok(B_NOW.count('{') == B_NOW.count('}'), 'base braces balance')
# WHAT IS LEFT OF THE PURPLE, asked of what it PAINTS rather than what it
# is called - which is how the fifth avatar was found at all, after a
# search for "avatar" in the class name returned four.
circles, others = [], 0
for d, _x, fs in os.walk(T):
    for f in sorted(fs):
        if not f.endswith('.html') or '.bak' in f:
            continue
        t = read(os.path.join(d, f))
        if '667eea' not in t and '764ba2' not in t:
            continue
        c = nocomment(css_of(t))
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', c):
            if '667eea' in m.group(2) or '764ba2' in m.group(2):
                if '50%' in m.group(2) and 'border-radius' in m.group(2):
                    circles.append('%s %s' % (f, ' '.join(m.group(1).split())))
                else:
                    others += 1
ok(not circles,
   'NOT ONE purple rule paints a circle any more - every avatar in the '
   'system is base\'s', circles[:5])
# LATER - Section E round E2, 25 Sep. 2.K ARRIVED. This held the
# deferral by requiring that forty-odd purple rules still existed.
# E2 took the imported palette out of the system, so the floor is
# now a ceiling of zero: not one rule anywhere paints with #667eea
# or #764ba2. The two literals that survive E2 are a mention inside
# D9's own comment (stripped by nocomment above) and a metric colour
# in financial_indicators - neither is a rule, and neither is here.
ok(others == 0,
   'not one rule anywhere still paints with the imported purple - '
   'E2 took the palette out, and D9\'s deferral to 2.K is spent',
   others)

ok(SUFFIX in ROUNDS and '.bak_horizon' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_horizon'),
   'alv_rounds lists %s after .bak_horizon' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s2 = ps[ps.find('$suites = @('):]
_m2 = re.search(r'\n\)\s*?\n', _s2)
ok(_m2 is not None and "'%s'" % ME in _s2[:_m2.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
