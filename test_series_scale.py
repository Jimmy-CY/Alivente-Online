# -*- coding: utf-8 -*-
"""test_series_scale.py - Section D, round D5: the series scale.

    python test_series_scale.py

Run from the repo root, after apply_series_scale.py.

  1. Base carries eight series hues, and THE COLOUR MATHS IS RUN HERE
     rather than quoted from the tool that first validated it: lightness
     band, chroma floor, adjacent separation in ordinary sight and under
     three kinds of colour blindness. A nudged token fails this suite with
     the pair it broke and the number it broke it by. CONTROLS, from the
     backups: the twelve colours each page used to carry, the portfolio
     line that was delta-E 2.0 from a property, and act_expense's pair at
     5.0.
  2. The house tag inks are re-measured, because "they were tried and they
     fail" is the reason this scale is louder than the rest of the palette
     and a reason is worth keeping checkable.
  3. The helpers RUN, in a browser, against base's real tokens: slot to
     colour, the wrap at eight, and the second mark - a shape where a
     property is a dot, a dash where it is a line.
  4. Colour follows the property: both views pass a slot that is a rank
     among ALL properties, and neither chart takes a colour by position
     any more.
  5. The portfolio line is heavier than a property line.
  6. The status literals: the dead rules are gone, the swept literals are
     gone, and what is left on those two pages is named rather than spelt.
  7. Scope, then registered in alv_rounds and on the gate.
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
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
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

SUFFIX = '.bak_series'
ME = 'test_series_scale.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
ACT = os.path.join(T, 'act_expense.html')
FI = os.path.join(T, 'finance', 'financial_indicators.html')
CFF = os.path.join(T, 'finance', 'cashflow_forecast.html')
VAC = os.path.join(T, 'finance', 'vacancy_management.html')
EXP_VIEW = os.path.join(ROOT, 'pages', 'views', 'expenses.py')
FIN_VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')

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
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def js_of(t):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', t, re.S))


# ==========================================================================
# THE COLOUR MATHS, RUN RATHER THAN QUOTED.
#
# The scale in base was validated once, by a tool that is not in this repo.
# A number in a comment is a measurement somebody took; this is the
# measurement, taken again, every time the gate runs - so the day a token
# is nudged "just a little", the suite says which pair it broke and by how
# much rather than the standard quietly lapsing.
#
# sRGB -> linear -> OKLab, and the distance between two colours is the
# euclidean distance in OKLab x100. The CVD simulations are the Brettel /
# Vienot style matrices used by the validator this scale came from.
# ==========================================================================
def _srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgb(h):
    h = h.strip().lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def oklab(rgb):
    r, g, b = (_srgb_to_lin(x) for x in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (x ** (1.0 / 3) if x > 0 else -((-x) ** (1.0 / 3))
               for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def dE(a, b):
    """OKLab distance x100 - the same scale the floors below are quoted in."""
    x, y = oklab(hex_rgb(a)), oklab(hex_rgb(b))
    return 100 * math.sqrt(sum((p - q) ** 2 for p, q in zip(x, y)))


def chroma(h):
    _L, a, b = oklab(hex_rgb(h))
    return math.sqrt(a * a + b * b)


def lightness(h):
    return oklab(hex_rgb(h))[0]


_CVD = {
    'protan': ((0.0, 1.05118294, -0.05116099),
               (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    'deutan': ((1.0, 0.0, 0.0), (0.9513092, 0.0, 0.04866992),
               (0.0, 0.0, 1.0)),
    'tritan': ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
               (-0.86744736, 1.86727089, 0.0)),
}


def simulate(h, kind):
    """The colour as a reader with that form of colour blindness sees it."""
    r, g, b = (_srgb_to_lin(x) for x in hex_rgb(h))
    L = 0.31399022 * r + 0.63951294 * g + 0.04649755 * b
    M = 0.15537241 * r + 0.75789446 * g + 0.08670142 * b
    S = 0.01775239 * r + 0.10944209 * g + 0.87256922 * b
    m = _CVD[kind]
    L2 = m[0][0] * L + m[0][1] * M + m[0][2] * S
    M2 = m[1][0] * L + m[1][1] * M + m[1][2] * S
    S2 = m[2][0] * L + m[2][1] * M + m[2][2] * S
    r2 = 5.47221206 * L2 - 4.6419601 * M2 + 0.16963708 * S2
    g2 = -1.1252419 * L2 + 2.29317094 * M2 - 0.1678952 * S2
    b2 = 0.02980165 * L2 - 0.19318073 * M2 + 1.16364789 * S2

    def back(c):
        c = max(0.0, min(1.0, c))
        c = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
        return int(round(max(0.0, min(1.0, c)) * 255))
    return '#%02x%02x%02x' % (back(r2), back(g2), back(b2))

B_NOW, B_WAS = now(BASE), was(BASE)
SERIES = re.findall(r'--alv-series-(\d):\s*(#[0-9a-fA-F]{6});', B_NOW)
HUES = [h for _n, h in sorted(SERIES, key=lambda x: int(x[0]))]

# ==========================================================================
head('1. BASE CARRIES A SCALE, AND IT STILL MEASURES UP')
# ==========================================================================
ok('ALV SERIES SCALE v1' in B_NOW, 'base carries the ALV SERIES SCALE block')
ok(B_NOW.count('ALV SERIES SCALE v1') == 1,
   '  once', B_NOW.count('ALV SERIES SCALE v1'))
ok('ALV SERIES SCALE v1' not in B_WAS,
   '  CONTROL: it was not there before the round')
ok(len(HUES) == 8, 'eight slots, numbered 1 to 8', len(HUES))
ok(len(set(HUES)) == 8, '  and no two are the same colour', HUES)

if len(HUES) == 8:
    # --- the six checks, run -------------------------------------------
    lows = [(h, round(lightness(h), 3)) for h in HUES
            if not 0.43 <= lightness(h) <= 0.77]
    ok(not lows, 'LIGHTNESS BAND   all eight inside L 0.43-0.77', lows)
    greys = [(h, round(chroma(h), 3)) for h in HUES if chroma(h) < 0.1]
    ok(not greys, 'CHROMA FLOOR     all eight at or above 0.1 - none of them '
       'reads as grey on a chart', greys)
    adj = list(zip(HUES, HUES[1:]))
    worst_n = min(((dE(a, b), a, b) for a, b in adj))
    ok(worst_n[0] >= 15,
       'NORMAL VISION    worst adjacent pair %.1f (floor 15) - %s next to %s'
       % worst_n)
    # The GATE is protan and deutan - red-blindness and green-blindness,
    # between them about 1 man in 12. Tritan is rarer by two orders of
    # magnitude and is REPORTED rather than gated, which is how the tool
    # that first validated this scale treats it too: it passed this order
    # at protan 9.1 while printing tritan 5.8 beside it.
    worst_c = min(((dE(simulate(a, k), simulate(b, k)), k, a, b)
                   for a, b in adj for k in ('protan', 'deutan')))
    ok(worst_c[0] >= 8,
       'CVD SEPARATION   worst adjacent pair %.1f (target 8) under %s - '
       '%s next to %s' % worst_c)
    worst_t = min(((dE(simulate(a, 'tritan'), simulate(b, 'tritan')), a, b)
                   for a, b in adj))
    print('  ..   REPORTED, NOT GATED: worst adjacent tritan pair %.1f - '
          '%s next to %s' % worst_t)
    # The one hue that is close to the accent must be LAST, where a chart
    # only reaches it with eight properties on screen.
    acc = re.search(r'--alv-accent:\s*(#[0-9a-fA-F]{6});', B_NOW)
    if ok(acc is not None, 'base still names an accent'):
        near = [h for h in HUES if dE(h, acc.group(1)) < 15]
        ok(len(near) <= 1,
           'at most one hue comes within 15 of the accent (%d)' % len(near),
           [(h, round(dE(h, acc.group(1)), 1)) for h in near])
        ok(not near or near[0] == HUES[-1],
           '  and it is the LAST slot, so a chart only reaches it with '
           'eight properties on screen', near)

# --- the CONTROLS: what the two charts used to say ----------------------
_old_fi = re.search(r"var PALETTE = \[(.*?)\];", was(FI), re.S)
_old_act = re.search(r"var PALETTE = \[(.*?)\];", was(ACT), re.S)
if _old_fi and _old_act:
    fi_old = re.findall(r'#[0-9a-fA-F]{6}', _old_fi.group(1))
    act_old = re.findall(r'#[0-9a-fA-F]{6}', _old_act.group(1))
    _port = re.search(r"var PORT = '(#[0-9a-fA-F]{6})'", was(FI))
    ok(_port is not None and len(fi_old) == 12 and len(act_old) == 12,
       'CONTROL: both pages carried twelve hardcoded colours')
    ok(not (set(fi_old) & set(act_old)),
       '  CONTROL: and the two lists shared not one of them')
    if _port:
        d = dE(_port.group(1), fi_old[11])
        ok(d < 15,
           '  CONTROL: the PORTFOLIO line and the 12th property were %.1f '
           'apart - the same colour to anyone looking' % d)
    worst_old = min(((dE(a, b), a, b)
                     for a, b in zip(act_old, act_old[1:])))
    ok(worst_old[0] < 15,
       '  CONTROL: act_expense had a pair %.1f apart - %s next to %s'
       % worst_old)
    # Guarded: on a reverted tree there are no series tokens, and a suite
    # that raises says far less than one that fails (this one did, once).
    _pairs = list(zip(HUES, HUES[1:]))
    ok(bool(_pairs) and min(dE(a, b) for a, b in _pairs) > worst_old[0],
       '  and the new scale\'s worst pair is further apart than that',
       'no series tokens to compare' if not _pairs else '')

# ==========================================================================
head('2. THE HOUSE INKS WERE TRIED FIRST, AND THEY FAIL')
# ==========================================================================
# Not a claim in a comment - the reason the scale is louder than the rest
# of the palette is re-measured here, from the tokens base still carries.
INKS = [m.group(1) for m in
        re.finditer(r'--alv-tag-\w+-ink:\s*(#[0-9a-fA-F]{6});', B_NOW)]
ok(len(INKS) >= 5, 'base still carries the five tag inks', len(INKS))
if len(INKS) >= 5:
    grey = [h for h in INKS if chroma(h) < 0.1]
    ok(len(grey) == len(INKS),
       'every one of them is BELOW the chroma floor - on a chart they read '
       'as grey (%d of %d)' % (len(grey), len(INKS)),
       [(h, round(chroma(h), 3)) for h in INKS])
    worst = min(((dE(a, b), a, b) for i, a in enumerate(INKS)
                 for b in INKS[i + 1:]))
    ok(worst[0] < 15,
       '  and the closest pair is %.1f apart - %s and %s' % worst)
    ok(bool(HUES) and all(chroma(h) >= 0.1 for h in HUES),
       '  which is why the series scale is louder than they are',
       'no series tokens' if not HUES else '')

# ==========================================================================
head('3. THE HELPERS RUN - IN A BROWSER, AGAINST BASE\'S OWN TOKENS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'


def grab_fn(js, name):
    """A function lifted out of the page by brace-matching, not by regex:
       these are indented differently on the two pages."""
    i = js.find('function %s(' % name)
    if i < 0:
        return ''
    j, d = js.find('{', i), 0
    for k in range(j, len(js)):
        if js[k] == '{':
            d += 1
        elif js[k] == '}':
            d -= 1
            if d == 0:
                return js[i:k + 1]
    return ''


def boot_of(src, fns):
    js = js_of(src)
    out = ['var AN_CS = getComputedStyle(document.documentElement);',
           grab_fn(js, 'anTok')]
    i = js.find('var SERIES_FALLBACK = [')
    if i < 0:
        return ''
    out.append(js[i:js.find('];', i) + 2])
    i = js.find('var SERIES = SERIES_FALLBACK')
    if i < 0:
        return ''
    out.append(js[i:js.find('});', i) + 3])
    m = re.search(r"var SERIES_SHAPES = (\[[^\]]*\]);", js)
    if m:
        out.append('var SERIES_SHAPES = %s;' % m.group(1))
    out += [grab_fn(js, f) for f in fns]
    return '\n'.join(x for x in out if x)


if sync_playwright is None:
    skip('the helper checks', 'playwright missing')
else:
    # Concatenated, NOT %-formatted: base's stylesheet contains a data:
    # URI full of percent escapes, and %-formatting a string that holds
    # `%3csvg` raises before the browser ever sees it.
    _HEAD = ('<!doctype html><html><head><meta charset="utf-8"><style>'
             + '\n'.join(styles_of(B_NOW)) + '</style>')
    _FOOT = '</head><body></body></html>'
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page()
        k = [0]

        def load(extra=''):
            k[0] += 1
            fx = os.path.join(SCRATCH, '_series_%04d.html' % k[0])
            with open(fx, 'w', encoding='utf-8') as f:
                f.write(_HEAD + extra + _FOOT)
            _goto(pg, fx)

        for label, path, second in (('act_expense', ACT, 'seriesShape'),
                                    ('financial_indicators', FI,
                                     'seriesDash')):
            src = now(path)
            boot = boot_of(src, ['seriesColour', second])
            if not ok(bool(boot), '%s: its helpers could be lifted' % label):
                continue
            load()
            pg.evaluate(boot)
            got = [pg.evaluate('seriesColour(%d)' % s) for s in range(8)]
            ok([g.lower() for g in got] == [h.lower() for h in HUES],
               '%-21s slots 0-7 are base\'s eight hues, in order' % label,
               '\n'.join('%d %s vs %s' % (i, a, b)
                         for i, (a, b) in enumerate(zip(got, HUES)) if a != b))
            ok(pg.evaluate('seriesColour(8)') == got[0]
               and pg.evaluate('seriesColour(15)') == got[7],
               '  slot 8 takes slot 0\'s hue again - no ninth colour is '
               'invented')
            marks = [pg.evaluate('JSON.stringify(%s(%d))' % (second, s))
                     for s in (0, 7, 8, 15, 16)]
            ok(marks[0] == marks[1] and marks[2] == marks[3]
               and marks[0] != marks[2] and marks[4] == marks[0],
               '  and the second lap carries a different %s - %s then %s'
               % ('shape' if second == 'seriesShape' else 'dash',
                  marks[0], marks[2]), marks)
            # THE TOKEN IS WHAT DRIVES IT. Override one in the page and the
            # helper must follow - otherwise base owns the comment and the
            # page owns the colour.
            load('<style>:root{--alv-series-1:#123456}</style>')
            pg.evaluate(boot)
            ok(pg.evaluate('seriesColour(0)') == '#123456',
               '  the colour comes from the TOKEN, not from the fallback '
               'beside it', pg.evaluate('seriesColour(0)'))
        br.close()

# ==========================================================================
head('4. COLOUR FOLLOWS THE PROPERTY, NOT ITS PLACE IN A FILTERED LIST')
# ==========================================================================
for label, p in (('expenses.py', EXP_VIEW), ('finance.py ', FIN_VIEW)):
    v = read(p)
    ok("slot_of = {pid: i for i, pid in enumerate(" in v,
       '%s builds a slot for every property' % label)
    ok("props.objects.order_by('prop_id')" in v,
       '  ordered by prop_id - the one thing about a property that never '
       'changes')
    ok(v.count("'slot': slot_of.get(") == 1,
       '  and passes it exactly once', v.count("'slot': slot_of.get("))
    try:
        compile(v, p, 'exec')
        err = None
    except SyntaxError as e:
        err = 'line %s: %s' % (e.lineno, e.msg)
    ok(err is None, '  and still compiles', err)
for label, path in (('act_expense         ', ACT),
                    ('financial_indicators', FI)):
    src, old = now(path), was(path)
    ok('PALETTE' not in src, '%s has no PALETTE of its own' % label,
       [ln.strip()[:60] for ln in src.split('\n') if 'PALETTE' in ln][:2])
    ok('PALETTE' in old, '  CONTROL: it had one before')
    ok(re.search(r'\w+\[\s*\w+\s*%\s*\w+\.length\s*\]', js_of(src)
                 .replace('SERIES[(slot || 0) % SERIES.length]', '')) is None,
       '  and no colour is taken by POSITION any more',
       [ln.strip()[:70] for ln in src.split('\n')
        if re.search(r'\[\s*\w+\s*%\s*\w+\.length\s*\]', ln)
        and 'slot' not in ln][:3])
    ok('p.slot' in js_of(src) or '(slot' in js_of(src),
       '  the slot the view sends is what picks the colour')
_fi = js_of(now(FI))
ok('var ids = selectedIds();' in _fi and 'ci = 0' not in _fi,
   'financial_indicators no longer counts over the TICKED properties')
ok('ci = 0' in js_of(was(FI)),
   '  CONTROL: it did before - which is why unticking one repainted the '
   'rest')

# ==========================================================================
head('5. THE PORTFOLIO LINE IS THE BASELINE, AND LOOKS LIKE IT')
# ==========================================================================
_style = re.search(r'function styleFor\(color, years(, opts)?\) \{(.*?)\n    \}',
                   js_of(now(FI)), re.S)
ok(_style is not None and _style.group(1) is not None,
   'styleFor takes the options that carry a width and a dash')
if _style:
    ok('borderWidth: opts.width || 2' in _style.group(2),
       '  a property line is 2px unless it is told otherwise')
    ok('borderDash: opts.dash || []' in _style.group(2),
       '  and solid unless it is told otherwise')
ok(re.search(r"label: 'Portfolio'.*?styleFor\(PORT, vYears, \{ width: 4 \}\)",
             js_of(now(FI)), re.S) is not None,
   'the Portfolio line is drawn at 4px - twice a property\'s')
_old_style = re.search(r'function styleFor\(color, years\) \{(.*?)\n    \}',
                       js_of(was(FI)), re.S)
ok(_old_style is not None and 'borderWidth' not in _old_style.group(1),
   'CONTROL: it set no width at all before, so the portfolio was told '
   'apart by colour alone')

# ==========================================================================
head('6. THE STATUS LITERALS - NAMED, NOT SPELT')
# ==========================================================================
_cff, _cff_was = now(CFF), was(CFF)
for dead in ('.legend-color.red', '.legend-color.orange',
             '.legend-color.green', '.timeline-bar.red',
             '.timeline-bar.orange', '.timeline-bar.green'):
    ok(dead not in _cff, 'cashflow: %-22s is gone' % dead)
    ok(dead in _cff_was, '  CONTROL: it was there before')
# It was DEAD, and that is why it could go. Re-proved, not trusted.
_mk = re.sub(r'<style\b.*?</style>', '', _cff_was, flags=re.S | re.I)
for word in ('red', 'orange', 'green'):
    ok(not re.search(r'[\'"`][^\'"`]*\b%s\b[^\'"`]*[\'"`]' % word,
                     re.sub(r'<script\b.*?</script>', '', _mk,
                            flags=re.S | re.I))
       and not re.search(r'class="[^"]*\b%s\b' % word, _mk),
       '  CONTROL: nothing on the page ever wore .%s' % word)
ok('.summary-card.current-month .card-header' in _cff,
   'cashflow: the summary-card headers KEEP theirs - those are applied, '
   'and they are a question for their own round')

for lit in ('#0f766e', '#c0392b', '#2c3e50', '#0e7c8b', '#0a5e6a'):
    ok(lit not in _cff, 'cashflow: %s is gone' % lit,
       [ln.strip()[:64] for ln in _cff.split('\n') if lit in ln][:2])
    ok(lit in _cff_was, '  CONTROL: it was there before')
ok('var(--alv-accent)' in _cff and 'var(--alv-bad)' in _cff
   and 'var(--alv-ink)' in _cff,
   'cashflow: and the tokens are there instead')
ok('.legend-color.income{background:var(--alv-accent);}' in _cff,
   'cashflow: money in is the accent - the colour it already was')
ok('.legend-color.outflow{background:var(--alv-bad);}' in _cff,
   '  and money out is the bad token - likewise')
ok('linear-gradient' not in _cff.split('.legend-color.income')[1][:400],
   '  the two bars are flat now: there is no token for a gradient\'s '
   'light end')

_vac, _vac_was = now(VAC), was(VAC)
ok('const AN_CS = getComputedStyle' in _vac and 'function anTok' in _vac,
   'vacancy: it can read a token now')
for tok in ('series-1', 'series-2', 'series-3'):
    ok("anTok('%s'" % tok in _vac,
       'vacancy: an indicator takes %s - it is a CATEGORY' % tok)
for g in ('grade-1', 'grade-3', 'grade-5'):
    ok("anTok('%s'" % g in _vac,
       'vacancy: a bar takes %s - it is a GRADING' % g)
ok("anTok('ink-soft'" in _vac,
   'vacancy: the portfolio average line takes ink - it is what the bars '
   'are measured against, not one of them')
ok('#ff6b35' not in _vac, '  and its orange is gone')
ok('#ff6b35' in _vac_was, '  CONTROL: it was there before')
for lit in ('#28a745', '#ffc107', '#dc3545', '#fd7e14', '#e74c3c'):
    ok(lit not in _vac, 'vacancy: %s is gone' % lit,
       [ln.strip()[:64] for ln in _vac.split('\n') if lit in ln][:2])
_ind = _vac_was[_vac_was.find('this.indicators = ['):]
ok(_ind[:2000].count("'#28a745'") >= 1,
   'CONTROL: an indicator and a bar really did share one colour before')

# ==========================================================================
head('7. SCOPE, THEN REGISTERED AND ON THE GATE')
# ==========================================================================
for label, path in (('base.html           ', BASE),
                    ('act_expense         ', ACT),
                    ('financial_indicators', FI),
                    ('cashflow_forecast   ', CFF),
                    ('vacancy_management  ', VAC)):
    if not os.path.isfile(path + SUFFIX):
        skip('scope on %s' % label.strip(), 'no %s backup' % SUFFIX)
        continue
    a, b = now(path), was(path)
    ok(a.count('{') == a.count('}'),
       '%s braces balanced' % label, (a.count('{'), a.count('}')))
    ok(sorted(re.findall(r'\bid="([^"]+)"', a))
       == sorted(re.findall(r'\bid="([^"]+)"', b)),
       '  every id is still there')
    ok(a.count('{%') == b.count('{%') and a.count('{{') == b.count('{{'),
       '  every Django tag is still there')
    ok(re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                  a)
       == re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                     b),
       '  every control is still there, in order')

# The standards block INDEXES base's vocabulary and states how many tokens
# base carries. A new family that the index does not name is a family the
# standard does not know about, and the count is a measurement like any
# other - it moves with the decision (lesson 14).
_doc = B_NOW[B_NOW.find('THE STANDARDS'):B_NOW.find('COMPONENTS')]
ok('--alv-series-1 .. --alv-series-8' in B_NOW,
   'the standards index names the series family')
ok('never a status, never cycled past eight' in B_NOW,
   '  and says what it is for, and what it is not')
_said = re.search(r'(\d+) design tokens', B_NOW)
_decl = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:',
                           '\n'.join(styles_of(B_NOW)))))
ok(_said is not None and int(_said.group(1)) == _decl,
   'the block still states the right number of tokens (%s says, %d declared)'
   % (_said.group(1) if _said else '?', _decl))
_was_said = re.search(r'(\d+) design tokens', B_WAS)
ok(_was_said is not None and _said is not None
   and int(_said.group(1)) - int(_was_said.group(1)) == 8,
   '  and it moved by exactly the eight this round added',
   (_was_said.group(1) if _was_said else '?',
    _said.group(1) if _said else '?'))

ok(SUFFIX in ROUNDS and '.bak_field' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_field'),
   'alv_rounds lists %s after .bak_field' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
