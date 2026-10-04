# -*- coding: utf-8 -*-
"""test_age_tone.py - Section AG round AG-1, 4 Oct 2026.

Demetri, of the Outstanding Invoices Report: "I don't like these colours
any more. They don't fit within our team and grey theme... I have decided
that I don't need a green and red scale. Also, the total outstanding
figures must not be in blue, but fit into our standard."

==========================================================================
WHAT THIS SUITE ASKS
==========================================================================
Section 1 renders the five steps in a browser and reads the computed
background off each one, then computes the contrast of --alv-ink against
it. The claim is not "the file says #f2f1ee"; it is "every step clears
AA, and the five backgrounds get monotonically darker". A scale that
reversed at one step, or that two steps shared, would pass a text check.

Section 2 is the one the round needed. .alv-age-pill wrote its text in
var(--age), and carried over literally into a one-tone scale that puts
#8a979d on #fafaf9 - 2.87, failing AA on a pill that exists to be read.
So the gate is CONTRAST, asked of the rendered pill, not of the rule.

Section 4 reads the total figure's colour off the DESKTOP table and the
PHONE card and requires them to agree, because they did not: one was
--alv-edit and the other a raw #007bff.
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
import os
import re
import sys
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_agetone'
ME = 'test_age_tone.py'
PATCHER = 'apply_age_tone.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_agetone_')

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
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
OIR = alv_tree.path_of('open_invoices_report.html')

SRC = alv_tree.code_only(now(BASE))
OLD = alv_tree.code_only(was(BASE)) if was(BASE) else ''
OIRC = alv_tree.code_only(now(OIR))
OIRW = alv_tree.code_only(was(OIR)) if was(OIR) else ''


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def rgb(s):
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', s or '')
    return tuple(int(m.group(i)) for i in (1, 2, 3)) if m else None


def lum(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def cr(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

FRAG = ''.join(
    '<span class="alv-age-pill alv-age-%d" id="pill%d">%d days</span>'
    '<span class="alv-age-dot alv-age-%d" id="dot%d"></span>'
    '<span class="alv-age-cell alv-age-%d" id="cell%d">1,234</span>' % (
        i, i, i * 30, i, i, i, i)
    for i in range(5))


def paint(basecss):
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style></head>'
            '<body style="margin:0;padding:8px;background:#fff">%s</body>'
            '</html>' % (read(BOOT), css_of(basecss), FRAG))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 900, 'height': 300})
        pg.set_content(html)
        pg.wait_for_timeout(120)
        r = pg.evaluate("""() => {
          const o = {};
          for (let i = 0; i < 5; i++) {
            const p = getComputedStyle(document.getElementById('pill'+i));
            const d = getComputedStyle(document.getElementById('dot'+i));
            const c = getComputedStyle(document.getElementById('cell'+i));
            o[i] = {pbg: p.backgroundColor, pfg: p.color,
                    pbd: p.borderTopColor, pbw: p.borderTopWidth,
                    dot: d.backgroundColor, cell: c.backgroundColor};
          }
          const ink = document.createElement('span');
          ink.style.color = 'var(--alv-ink)';
          document.body.appendChild(ink);
          o.ink = getComputedStyle(ink).color;
          return o;
        }""")
        b.close()
    # JS object keys arrive as STRINGS. Normalised here rather than at
    # twenty call sites - the first run of this suite indexed A[0] and
    # raised KeyError, which is the least useful thing a check can do.
    return {(int(k) if k.isdigit() else k): v for k, v in r.items()}


# ==========================================================================
head('1. FIVE STEPS OF ONE TONE, DEEPENING')
# ==========================================================================
if sync_playwright is None or not OLD:
    for _ in range(8):
        skip('the five steps', 'playwright or backup missing')
    A = None
else:
    A = paint(now(BASE))
    B = paint(was(BASE))
    ink = rgb(A['ink'])
    print('   step  cell background      ink contrast   pill fg / bg')
    for i in range(5):
        cell = rgb(A[i]['cell'])
        print('   %d     %-20s %5.2f          %s on %s'
              % (i, A[i]['cell'], cr(ink, cell), A[i]['pfg'], A[i]['pbg']))

    cells = [rgb(A[i]['cell']) for i in range(5)]
    ok(all(c is not None for c in cells), 'all five steps paint a cell')
    lums = [lum(c) for c in cells]
    ok(lums == sorted(lums, reverse=True),
       'and they get darker at every step, with no reversal',
       ['%.3f' % l for l in lums])
    ok(len({tuple(c) for c in cells}) == 5,
       '  five distinct backgrounds, so no two steps look the same')

    # ONE TONE. The hue is what Demetri objected to, so it is what is
    # measured: in a neutral the three channels stay close together, and
    # across the scale the ORDER of the channels does not change.
    def spread(c):
        return max(c) - min(c)
    ok(all(spread(c) <= 20 for c in cells),
       'every step is a neutral - no channel more than 20 from another',
       ['%s spread %d' % (c, spread(c)) for c in cells])
    ok(all(c[0] >= c[2] for c in cells),
       '  and all five are WARM, red at or above blue, so they separate '
       'from the page\'s own cool wash')

    oldcells = [rgb(B[i]['cell']) for i in range(5)]
    ok(any(spread(c) > 30 for c in oldcells),
       'CONTROL: the scale this replaced was not one tone',
       ['%s spread %d' % (c, spread(c)) for c in oldcells])

    worst = min(cr(ink, c) for c in cells)
    ok(worst >= 4.5,
       'the figures in those cells clear AA on every step - worst %.2f'
       % worst)
    ok(worst >= 7.0,
       '  and clear AAA as well: %.2f' % worst)

# ==========================================================================
head('2. THE PILL IS READABLE AT EVERY STEP')
# ==========================================================================
# The round's own near-miss. .alv-age-pill wrote its text in var(--age);
# carried over literally, steps 0 and 1 would have measured 2.87 and
# 3.26 on their own tints. The gate is the CONTRAST, not the rule.
if A is None:
    for _ in range(4):
        skip('the pill', 'playwright or backup missing')
else:
    rows = [(i, cr(rgb(A[i]['pfg']), rgb(A[i]['pbg']))) for i in range(5)]
    for i, c in rows:
        print('   pill %d  %.2f' % (i, c))
    ok(all(c >= 4.5 for _, c in rows),
       'every ageing pill clears AA - worst %.2f'
       % min(c for _, c in rows),
       '\n'.join('step %d: %.2f' % r for r in rows if r[1] < 4.5))
    ok(len({A[i]['pfg'] for i in range(5)}) == 1,
       '  and all five write their text in one colour, which is the point '
       'of a one-tone scale')
    # THE STEP IS ENCODED TWICE - background AND a border of --age - so a
    # pill on a tinted row still shows which step it is.
    ok(all(float(A[i]['pbw'].replace('px', '')) >= 1 for i in range(5)),
       '  the pill carries a border')
    ok(len({A[i]['pbd'] for i in range(5)}) == 5,
       '  in five distinct colours, so the step is encoded twice')

# ==========================================================================
head('3. THE DOT AND THE BAR STILL DEEPEN')
# ==========================================================================
# --age is no longer the pill's text, but it still drives the dot and the
# bar fill. Those are SHAPES, so 3:1 against paper is the bar they have
# to clear, not 4.5.
if A is None:
    for _ in range(3):
        skip('the dot', 'playwright or backup missing')
else:
    dots = [rgb(A[i]['dot']) for i in range(5)]
    white = (255, 255, 255)
    for i, d in enumerate(dots):
        print('   dot %d  %-18s on paper %.2f' % (i, A[i]['dot'], cr(d, white)))
    ok(all(d is not None for d in dots), 'all five steps paint a dot')
    dl = [lum(d) for d in dots]
    ok(dl == sorted(dl, reverse=True),
       '  and they deepen too, in the same direction as the tints')
    ok(all(cr(d, white) >= 3.0 for d in dots),
       '  every one clears 3:1 against paper, which is the bar for a '
       'shape - worst %.2f' % min(cr(d, white) for d in dots))

# ==========================================================================
head('4. THE TOTAL IS NOT BLUE, AND IS ONE COLOUR')
# ==========================================================================
# Demetri: "the total outstanding figures must not be in blue, but fit
# into our standard." There were TWO blues: --alv-edit on the desktop
# table and a raw #007bff on the phone card, so one number read
# differently depending on which screen you held.
ok('color: var(--alv-accent);' in
   (re.search(r'\.clickable-amount\s*\{[^}]*\}', OIRC) or
    type('x', (), {'group': lambda s, n=0: ''})()).group(0),
   'the drill-down figure is var(--alv-accent)',
   (re.search(r'\.clickable-amount\s*\{[^}]*\}', OIRC) or
    type('x', (), {'group': lambda s, n=0: '(no rule)'})()).group(0))
ok('text-decoration: underline' in
   (re.search(r'\.clickable-amount\s*\{[^}]*\}', OIRC) or
    type('x', (), {'group': lambda s, n=0: ''})()).group(0),
   '  and underlined, so the colour is not what says it can be pressed')
ok('#007bff' not in OIRC,
   'and the phone card no longer writes a raw Bootstrap blue')
ok('var(--alv-edit)' not in
   (re.search(r'\.clickable-amount\s*\{[^}]*\}', OIRC) or
    type('x', (), {'group': lambda s, n=0: ''})()).group(0),
   '  nor the pencil colour, which is what an EDIT wears here')
if OIRW:
    ok('#007bff' in OIRW,
       'CONTROL: the backup had the raw blue')
    ok('var(--alv-edit)' in
       (re.search(r'\.clickable-amount\s*\{[^}]*\}', OIRW) or
        type('x', (), {'group': lambda s, n=0: ''})()).group(0),
       '  and the pencil blue, on the same number')

# ==========================================================================
head('5. NO HUE IS LEFT IN THE SCALE, AND THE PAGES FOLLOW')
# ==========================================================================
blk = re.search(r'--alv-age-0:.*?--alv-age-4-soft:[^;]*;', SRC, re.S)
ok(blk is not None, 'the ageing tokens are one block')
if blk:
    hexes = re.findall(r'#[0-9a-fA-F]{6}', blk.group(0))
    ok(len(hexes) == 10, '  ten values, five steps and five tints',
       hexes)
    bad = [h for h in hexes
           if max(int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
           - min(int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)) > 25]
    ok(not bad, '  and not one of them is a hue', bad)
ok('--age: var(--alv-good)' not in SRC,
   'step 0 is no longer the good token - a ledger column is not a '
   'health verdict')
if OLD:
    ok('--age: var(--alv-good)' in OLD, '  CONTROL: it was')

# THE THREE PAGES THAT USE THE SCALE, asked of the tree.
# BASE IS NOT A USER OF THE SCALE, it is where the scale is. Its 28
# mentions are the component itself, and counting them makes the census
# grow by the round that was meant to leave it alone - the same mistake
# CR-1's census made an hour earlier, in another component.
users = {}
own = []
for p in alv_tree.templates():
    if os.path.abspath(p) == os.path.abspath(BASE):
        continue
    body = alv_tree.code_only(now(p))
    n = len(re.findall(r'alv-age-[0-4]\b', body))
    if not n:
        continue
    users[alv_tree.rel(p).replace(os.sep, '/')] = n
    # A PAGE THAT REDEFINES A STEP outranks base by coming later, and
    # this round would be invisible there. Asked of the page already in
    # hand, never resolved by basename afterwards.
    if re.search(r'\.alv-age-[0-4]\s*\{', body):
        own.append(alv_tree.rel(p).replace(os.sep, '/'))
for k, v in sorted(users.items()):
    print('   %-44s %d' % (k, v))
ok(len(users) == 3, 'the scale is used on %d pages, base aside' % len(users))
ok(any('open_invoices' in k for k in users),
   '  the Outstanding Invoices report among them')
ok(not own, '  and none of them redefines a step locally', ', '.join(own))

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
