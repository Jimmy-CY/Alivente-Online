# -*- coding: utf-8 -*-
"""test_personal_heads.py - Section E, round E1: the Personal side's
pop-up headers join the house.

    python test_personal_heads.py

Run from the repo root, after apply_personal_heads.py.

  1. All 32 wear .alv-modal-head; --danger goes exactly where the title
     says Delete, re-derived from the titles rather than trusted.
  2. RENDERED, every one of them, before and after - with the contrast
     of its own white title computed. Fifteen were failing; six were
     below 3.0, the bar for large text.
  3. The one LEAVE is untouched, and still invisible.
  4. Nothing else on those fourteen pages moved.
  5. Registered, and on the gate.

Run it against the REVERTED tree and it must FAIL, not crash.

NOTE: view_recipe carries an emoji in a modal title, which is why
the console-encoding preamble below matters here as much as it does
for the Greek heading it was written for. The preamble is reproduced
WORD FOR WORD - test_console_encoding checks that every tool carries
the same one, and a helpful edit to it is a failure.
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
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_pershead'
ME = 'test_personal_heads.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
HEAD, DANGER = 'alv-modal-head', 'alv-modal-head--danger'
LEAVE_FILE, LEAVE_MARK = 'recipe_management.html', 'id="recipeViewModalTitle"'
FILES = {
    'categories_management.html': 1, 'celebration_management.html': 5,
    'create_meal_plan.html': 1, 'household_member_management.html': 2,
    'ingredient_families.html': 2, 'meal_plan_calendar.html': 3,
    'meal_plans.html': 2, 'measurement_units_management.html': 1,
    'preview_imported_recipe.html': 4, 'recipe_management.html': 1,
    'unit_conversions_management.html': 3, 'view_meal_plan.html': 2,
    'view_recipe.html': 4, 'wcim_recipe_quick_view.html': 1,
}
TOTAL = sum(FILES.values())

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


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


OPEN = re.compile(r'<div\s+class="([^"]*\bmodal-header\b[^"]*)"([^>]*?)>')


def heads_of(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    out = []
    for m in OPEN.finditer(t):
        h = re.search(r'<(h[1-6])\b[^>]*>(.*?)</\1>', t[m.end():m.end() + 900],
                      re.S)
        title = re.sub(r'<[^>]+>|\s+', ' ', h.group(2)).strip() if h else ''
        out.append((m.group(1).split(), m.group(2), title,
                    LEAVE_MARK in t[m.end():m.end() + 300]))
    return out


# --- contrast, and a parser that refuses what it cannot read -------------
# D10's lesson: a helper that pulls [\d.]+ out of any string scored
# #ffffff as BLACK and color(srgb 0.09 ...) as black too, and never
# raised. Hex, rgb() and color(srgb ...) - anything else is an error.
def parse_rgb(s):
    s = s.strip().lower()
    m = re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    if s in ('white', 'black'):
        return (255, 255, 255) if s == 'white' else (0, 0, 0)
    m = re.match(r'^rgba?\(([^)]*)\)$', s)
    if m:
        v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))[:3]]
        return tuple(v) if len(v) == 3 else None
    m = re.match(r'^color\(srgb ([^)]*)\)$', s)
    if m:
        v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))[:3]]
        return tuple(x * 255 for x in v) if len(v) == 3 else None
    return None


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(a, b):
    ra, rb = parse_rgb(a), parse_rgb(b)
    if ra is None or rb is None:
        raise ValueError('unreadable colour: %r / %r' % (a, b))
    f = lambda v: 0.2126 * _lin(v[0]) + 0.7152 * _lin(v[1]) + 0.0722 * _lin(v[2])
    x, y = f(ra) + 0.05, f(rb) + 0.05
    return max(x, y) / min(x, y)


PAPER = (255, 255, 255)          # a modal's body, which these sit on


def over_paper(s):
    """A colour composited over the panel behind it.

    AN UNPAINTED HEADER IS NOT A BLACK ONE. `backgroundColor` on a header
    with no paint reads `rgba(0, 0, 0, 0)` - fully transparent - and
    treating those channels as a colour scores a dark title on a white
    modal as 1.36, a catastrophic failure that does not exist. A first
    run of this suite reported 19 failures before the round when the
    survey had measured 15, and every extra one was a bare header being
    called black. Alpha is composited over the modal's paper instead."""
    m = re.match(r'^rgba\(([^)]*)\)$', s.strip().lower())
    if not m:
        return s
    v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))]
    if len(v) < 4 or v[3] >= 1:
        return s
    a = v[3]
    return 'rgb(%d, %d, %d)' % tuple(
        round(v[i] * a + PAPER[i] * (1 - a)) for i in range(3))


def worst_contrast(bg, ink):
    """Against the WORST stop of the paint. A gradient has no
    backgroundColor - it reads rgba(0,0,0,0) and would score 21."""
    stops = re.findall(r'rgba?\([^)]*\)|color\(srgb [^)]*\)|#[0-9a-fA-F]{6}',
                       bg)
    if not stops:
        return contrast(over_paper(bg), ink)
    return min(contrast(over_paper(s), ink) for s in stops)


# ==========================================================================
head('1. ALL 32 WEAR THE CLASS, AND --danger GOES WHERE DELETE IS SAID')
# ==========================================================================
worn = danger = leaves = 0
bad, danger_wrong = [], []
for name in sorted(FILES):
    p = os.path.join(T, name)
    a, b = now(p), was(p)
    for cls, rest, title, is_leave in heads_of(a):
        if is_leave:
            leaves += 1
            ok(HEAD not in cls,
               '%-34s the Recipe View close strip is left bare, as decided'
               % name[:34], cls)
            continue
        worn += HEAD in cls
        if HEAD not in cls:
            bad.append('%s: %r has no %s' % (name, title[:24], HEAD))
        if [c for c in cls if c.startswith('bg-') or c == 'text-white']:
            bad.append('%s: %r keeps %s' % (name, title[:24], ' '.join(cls)))
        if re.search(r'style="[^"]*(background|color)\s*:', rest):
            bad.append('%s: %r keeps an inline paint' % (name, title[:24]))
        want = bool(re.search(r'\b(delete|remove)\b', title, re.I))
        danger += DANGER in cls
        if (DANGER in cls) != want:
            danger_wrong.append('%s: %r' % (name, title[:30]))
ok(worn == TOTAL and not bad,
   '%d header(s) on %d template(s) wear the class and nothing that fights '
   'it' % (worn, len(FILES)), '\n'.join(bad[:8]))
ok(danger == 6 and not danger_wrong,
   'the danger variant is on exactly the %d whose title says Delete'
   % danger, '\n'.join(danger_wrong[:6]))
ok(leaves == 1, 'and exactly one header is left bare', leaves)
# CONTROL, from the backups: what they wore before.
looks = set()
for name in sorted(FILES):
    for cls, rest, title, is_leave in heads_of(was(os.path.join(T, name))):
        if is_leave:
            continue
        st = re.search(r'style="([^"]*)"', rest)
        looks.add(' '.join(sorted(c for c in cls if c != 'modal-header'))
                  + ('|' + re.sub(r'\s+', '', st.group(1))[:40]
                     if st and re.search(r'background|color', st.group(1))
                     else ''))
ok(len(looks) >= 12,
   'CONTROL: before this round the same headers wore %d different looks'
   % len(looks))
ok(not any(HEAD in ' '.join(c) for name in FILES
           for c, _r, _t, _l in heads_of(was(os.path.join(T, name)))),
   '  CONTROL: and not one of them wore the house class')

# ==========================================================================
head('2. RENDERED - THE CONTRAST OF EVERY TITLE, BEFORE AND AFTER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
OPEN_MODALS = ('<style>.modal{display:block!important;position:static'
               '!important;opacity:1!important}</style>')
LOOK = r"""() => Array.from(document.querySelectorAll('.modal-header'))
  .map(h => {
    const t = h.querySelector('h1,h2,h3,h4,h5,h6,.modal-title');
    const s = getComputedStyle(h), ts = t ? getComputedStyle(t) : null;
    return {bg: s.backgroundImage !== 'none' ? s.backgroundImage
                                             : s.backgroundColor,
            ink: ts ? ts.color : '', size: ts ? ts.fontSize : '',
            pad: s.paddingTop,
            title: t ? (t.innerText || '').trim().slice(0, 28) : ''};
  })"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2 and 3', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def look(br, base_css, page_css, markup):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_ph_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><head><meta charset="utf-8">'
                    '<title>p</title><style>%s</style><style>%s</style>%s%s'
                    '</head><body class="has-sidebar"><div class="main-content'
                    ' with-sidebar">%s</div></body></html>'
                    % (boot, base_css,
                       ''.join('<style>%s</style>' % c for c in page_css),
                       OPEN_MODALS, markup))
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
        B_NOW = '\n'.join(styles_of(now(BASE)))
        B_WAS = '\n'.join(styles_of(was(BASE)))
        fail_before, fail3_before, fail_after = [], [], []
        seen_after, unreadable = 0, []
        for name in sorted(FILES):
            p = os.path.join(T, name)
            a = look(br, B_NOW, styles_of(now(p)), body_markup(now(p)))
            b = look(br, B_WAS, styles_of(was(p)), body_markup(was(p)))
            for row, bucket in ((b, 'before'), (a, 'after')):
                for h in row:
                    if not h['ink']:
                        continue
                    try:
                        c = worst_contrast(h['bg'], h['ink'])
                    except ValueError as e:
                        unreadable.append('%s %s' % (name, e))
                        continue
                    # The Recipe View strip's title is display:none -
                    # there is no visible text to measure. Section 3
                    # checks it by its padding and its paint instead.
                    if not h['title']:
                        continue
                    if bucket == 'after':
                        seen_after += 1
                        if c < 4.5:
                            fail_after.append('%s %r %.2f'
                                              % (name, h['title'], c))
                    else:
                        if c < 4.5:
                            fail_before.append('%s %r %.2f'
                                               % (name, h['title'], c))
                        if c < 3.0:
                            fail3_before.append('%s %r %.2f'
                                                % (name, h['title'], c))
        ok(not unreadable, 'every colour measured was one the parser '
           'understands', '\n'.join(unreadable[:5]))
        print('')
        print('      BEFORE  %d header(s) below 4.5:1, %d of them below 3.0'
              % (len(fail_before), len(fail3_before)))
        for x in sorted(fail_before, key=lambda s: float(s.split()[-1]))[:8]:
            print('         %s' % x)
        print('      AFTER   %d below 4.5:1, of %d measured'
              % (len(fail_after), seen_after))
        print('')
        # THE SURVEY SAID FIFTEEN. Rendered, it is ELEVEN: four of the
        # class-based headers were counted by assuming bg-info and its
        # friends carry white text, and in those four the colour reaching
        # the h5 comes from somewhere else. The browser is the authority,
        # not the class list - lesson 20, on this round's own survey.
        ok(len(fail_before) == 11,
           'CONTROL: %d of them failed 4.5:1 against their own title - the '
           'survey said 15 by reading class names; the render says 11'
           % len(fail_before))
        ok(len(fail3_before) == 6,
           '  and %d were below 3.0 - the bar for LARGE text, so they '
           'failed for any text at all' % len(fail3_before))
        ok(not fail_after,
           'AFTER: not one header on the Personal side fails 4.5:1',
           '\n'.join(fail_after[:8]))
        ok(seen_after == TOTAL,
           '  and %d header(s) were measured' % seen_after, seen_after)

        # ==============================================================
        head('3. THE LEAVE IS STILL INVISIBLE')
        # ==============================================================
        rm = look(br, B_NOW, styles_of(now(os.path.join(T, LEAVE_FILE))),
                  body_markup(now(os.path.join(T, LEAVE_FILE))))
        strip = [h for h in rm if h['pad'] == '8px']
        ok(bool(strip),
           'the Recipe View close strip still has its 8px top padding - '
           'base\'s 16px 20px !important has not reached it',
           [h['pad'] for h in rm])
        if strip:
            ok(not strip[0]['bg'].startswith('linear-gradient'),
               '  and no teal banner was painted where the design has none',
               strip[0]['bg'][:50])
        br.close()

# ==========================================================================
head('4. NOTHING ELSE ON THOSE FOURTEEN PAGES MOVED')
# ==========================================================================
for name in sorted(FILES):
    p = os.path.join(T, name)
    if not os.path.isfile(p + SUFFIX):
        skip(name, 'no %s backup' % SUFFIX)
        continue
    a, b = now(p), was(p)
    ok(sorted(re.findall(r'\bid="([^"]+)"', a))
       == sorted(re.findall(r'\bid="([^"]+)"', b)),
       '%-34s every id is still there' % name[:34])
    ok(a.count('{%') == b.count('{%') and a.count('{{') == b.count('{{'),
       '  every Django tag is still there')
    ok(a.count('<div') == b.count('<div'),
       '  and the same number of divs', (b.count('<div'), a.count('<div')))
    ok('\n'.join(styles_of(a)) == '\n'.join(styles_of(b)),
       '  its <style> blocks are byte-for-byte unchanged - this round '
       'edits attributes, not CSS')

# ==========================================================================
head('5. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_contrast' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_contrast'),
   'alv_rounds lists %s after .bak_contrast' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
