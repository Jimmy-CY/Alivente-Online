# -*- coding: utf-8 -*-
"""test_week_band.py - round WT-1, 21 Oct 2026.

THE SELECTED WEEK AND THE MEALS ON IT WERE THE SAME COLOUR.

Demetri, testing push 3:

    "Can the week highlight of the month view differ in colour to the
     colour of the pills for the recipes?"

Not "differ too little" - IDENTICAL. Both read
`background: var(--alv-accent-soft)`, which is dE 0.0 in CIE Lab. The
only thing separating a pill from the row under it was the 1px border
CL-1 added on 20 October, and CL-1's own note says it needed "borders
on tinted surfaces" - that round was treating the symptom.

CONTRAST RATIO IS THE WRONG INSTRUMENT HERE and this suite does not
use it. WCAG contrast is a legibility measure for ink on a ground;
two pale fills always score near 1:1 whether they are the same colour
or visibly different. The question "can I see this pill against that
row" is perceptual DIFFERENCE, so the number is dE.

THERE WAS NO FOURTH FILL TO TAKE. The month cell paints three states
in a narrow band of near-whites - paper, surface, accent-soft - and
section 3 re-measures the candidates that were rejected, so the
reason for the design survives in a form that can be re-run.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The row and the pill no longer share a fill, the
      row is marked by an accent edge, and the other three cell
      states are untouched.

  2   THE CONTROL. Re-asked of the pre-round file, where dE was 0.0.

  3   THE NUMBERS, re-measured: every pair of month-cell states, and
      why no fourth fill was available.

  4   RENDERED. The row and a pill on it, drawn and read back - a
      claim about a box-shadow is a claim about a layout engine.

  5   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import math
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_weekband'
ME = 'test_week_band.py'
PATCHER = 'apply_week_band.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'WT-1, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

# dE under about 2 is the threshold a trained eye can just detect.
# A pill on a row needs to clear it with room to spare.
VISIBLE = 2.0

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)
BASETXT = read(BASE)


# ---- COLOUR, PROPERLY ----------------------------------------------
def _rgb(h):
    h = h.strip().lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab(h):
    r, g, b = [c / 255.0 for c in _rgb(h)]
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    X = (r * .4124 + g * .3576 + b * .1805) / .95047
    Y = r * .2126 + g * .7152 + b * .0722
    Z = (r * .0193 + g * .1192 + b * .9505) / 1.08883
    t = lambda v: v ** (1 / 3.0) if v > 0.008856 else (7.787 * v) + 16 / 116.0
    X, Y, Z = t(X), t(Y), t(Z)
    return (116 * Y - 16, 500 * (X - Y), 200 * (Y - Z))


def dE(a, b):
    """CIE76. Crude next to dE2000 and ample for 'are these the same'."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(_lab(a), _lab(b))))


def token(name):
    """A token's value, read out of base rather than retyped."""
    m = re.search(r'%s\s*:\s*(#[0-9a-fA-F]{3,8})\s*[;}]' % re.escape(name),
                  BASETXT)
    return m.group(1) if m else None


def rule(text, sel):
    m = re.search(re.escape(sel) + r'\s*\{([^}]*)\}', text)
    return m.group(1) if m else None


def bg(body):
    m = re.search(r'background:\s*([^;]+);', body or '')
    return m.group(1).strip() if m else None


def resolve(val):
    """var(--alv-x) -> the hex base gives it."""
    if not val:
        return None
    m = re.match(r'var\((--alv-[a-z0-9-]+)\)', val.strip())
    if m:
        return token(m.group(1))
    return val.strip() if val.strip().startswith('#') else None


def claims(bundle):
    code = T.code_only(bundle[TPL])
    row = rule(code, '.month-cell.in-week')
    chip = rule(code, '.month-chip')
    c = {}
    c['THE ROW AND THE PILL NO LONGER SHARE A FILL - the finding'] = (
        row is not None and chip is not None and bg(row) != bg(chip))
    c['  the week is marked by an edge instead'] = (
        'box-shadow' in (row or ''))
    c['  and that edge is the accent, so it reads as a selection'] = (
        'var(--alv-accent)' in (row or ''))
    c['  the cells themselves are paper again'] = (
        bg(row) == 'var(--alv-paper)')
    # NOT HERE: "the pill was not touched". It is a GUARD - true
    # before this round and required after it - and a claims() dict is
    # a DELTA, re-asked of the pre-round file where every entry must
    # FAIL. A guard put in it fails the control for being correct.
    # Asked in section 1. (Fifth time this shape has come up today.)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

code = T.code_only(NOW[TPL])
# THE FIX BELONGS TO THE ROW. The pill colour is the meal vocabulary
# and Week and Day views use it too; only Month has the collision, so
# only Month may move.
ok(bg(rule(code, '.month-chip')) == 'var(--alv-accent-soft)',
   'the PILL was not touched - three views share that token',
   bg(rule(code, '.month-chip')))
for sel, want in (('.month-cell', 'var(--alv-paper)'),
                  ('.month-cell.is-out', 'var(--alv-surface)')):
    ok(bg(rule(code, sel)) == want,
       'the other cell states are untouched: %s is still %s'
       % (sel, want), bg(rule(code, sel)))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
oldcode = T.code_only(BEFORE[TPL])
orow = bg(rule(oldcode, '.month-cell.in-week'))
ochip = bg(rule(oldcode, '.month-chip'))
ok(orow == ochip,
   'CONTROL: before this round the row and the pill filled with the '
   'SAME token', '%r vs %r' % (orow, ochip))
ok(resolve(orow) and dE(resolve(orow), resolve(ochip)) == 0.0,
   'CONTROL: dE 0.0 - not similar, identical',
   dE(resolve(orow), resolve(ochip)) if resolve(orow) else '?')
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: and not one of this round claims held',
   'what held: %r' % (held,))


# ==========================================================================
head('3. THE NUMBERS, RE-MEASURED')
# ==========================================================================
paper = token('--alv-paper')
surface = token('--alv-surface')
deep = token('--alv-surface-deep')
soft = token('--alv-accent-soft')
if not all((paper, surface, deep, soft)):
    skip('the measurements', 'a token is missing from base')
else:
    print('')
    print('  %-30s %-9s %8s' % ('month-cell state', 'hex', 'dE pill'))
    print('  ' + '-' * 50)
    for name, c in (('normal (paper)', paper),
                    ('hover / is-out (surface)', surface),
                    ('in-week BEFORE (accent-soft)', soft)):
        print('  %-30s %-9s %8.1f' % (name, c, dE(soft, c)))
    print('')
    ok(dE(soft, soft) < VISIBLE,
       'the pill against the OLD row is below the visible threshold - '
       'which is the finding, stated as a number', dE(soft, soft))
    ok(dE(soft, paper) >= VISIBLE,
       'and against the NEW row (paper) it is above it: %.1f'
       % dE(soft, paper))
    # WHY NO FOURTH FILL. Kept as a measurement rather than as prose
    # so that a later round proposing one has to re-read the numbers.
    print('  rejected candidates for a fourth fill:')
    for name, c in (('surface-deep', deep),
                    ('pale accent, 45pc white', '#f0f8fa')):
        print('     %-22s dE pill %4.1f   dE is-out %4.1f'
              % (name, dE(soft, c), dE(surface, c)))
    ok(dE(surface, deep) < 5.0,
       '  surface-deep lands close to is-out, so "this week" and "not '
       'this month" would be two greys: dE %.1f' % dE(surface, deep))
    ok(dE(surface, '#f0f8fa') < 3.0,
       '  and a pale accent closes on surface before it clears the '
       'pill: dE %.1f' % dE(surface, '#f0f8fa'))


# ==========================================================================
head('4. RENDERED - THE EDGE IS REALLY PAINTED')
# ==========================================================================
# A box-shadow inset over a 1px grid gap is a claim about a layout
# engine, not about a stylesheet. .month-grid is `gap: 1px` over a
# line-soft ground, so the band is interrupted six times across a
# week - the question is whether that reads as a line or as dashes.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the band renders', 'playwright or the Bootstrap fixture is absent')
else:
    PAGE = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                                NOW[TPL], re.S | re.I))
    BCSS = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                                BASETXT, re.S | re.I))
    cells = []
    for i in range(7):
        ks = 'month-cell in-week' + (' is-today' if i == 2 else '')
        chip = ('<div class="month-chip">Gemista</div>' if i in (0, 2, 4)
                else '')
        cells.append('<div class="%s"><span class="month-daynum">%d</span>'
                     '%s</div>' % (ks, 19 + i, chip))
    doc = ('<!doctype html><meta charset=utf-8>'
           '<style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:12px;background:#fff}</style>'
           '<body><div class="month-grid">%s</div>'
           % (read(FIXCSS), BCSS + '\n' + PAGE, ''.join(cells)))
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1100, 'height': 320})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(doc, wait_until='domcontentloaded')
        got = pg.evaluate("""() => {
            const c = document.querySelector('.month-cell.in-week');
            const p = document.querySelector('.month-chip');
            const cs = getComputedStyle(c), ps = getComputedStyle(p);
            return {rowBg: cs.backgroundColor, rowShadow: cs.boxShadow,
                    pillBg: ps.backgroundColor,
                    pillW: Math.round(p.getBoundingClientRect().width)};
        }""")
        br.close()
    print('')
    for k in ('rowBg', 'pillBg', 'rowShadow'):
        print('  %-10s %s' % (k, got[k][:76]))
    print('')
    ok(got['rowBg'] != got['pillBg'],
       'PAINTED: the row and the pill are different colours',
       '%s vs %s' % (got['rowBg'], got['pillBg']))
    ok(got['rowShadow'] and got['rowShadow'] != 'none',
       '  and the row really carries an inset edge', got['rowShadow'])
    ok('inset' in (got['rowShadow'] or ''),
       '  which is inset, so it draws inside the cell rather than '
       'over its neighbour')
    ok(got['pillW'] > 0, '  and the pill still has a box to be seen in',
       got['pillW'])


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_week_band as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
