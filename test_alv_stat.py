"""test_alv_stat.py - the stat tile, and the decision inside it.

    python test_alv_stat.py

Run from the repo root, after apply_alv_stat.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 RENDERS THE COMPONENT in a real browser and asks it the question
    the round exists to settle: does a verdict wash the TILE or colour the
    FIGURE? Two of the four implementations .alv-stat replaces washed the tile.
    A CSS check could only ask whether the string `background` appears in a
    rule; the browser can be asked what colour actually lands on the box, with
    the cascade, the media query and the print block all in play.
  * SECTION 3 ALSO CARRIES ITS OWN CONTROL. A tile with a deliberate red
    background is rendered beside the real ones, and the probe must SEE it.
    Without that, "no wash" passes just as happily on a probe that is blind,
    which is the failure mode of a control that cannot fail.
  * SECTION 2 asks whether the component is anchored on the system's own
    tokens - not merely that it names them, but that the three verdict colours
    resolve to three DIFFERENT values. Outstanding Invoices shipped a "scale"
    of two near-identical pale blues with a grey between them; it looked like
    an ordering and encoded none.
  * SECTION 1 reads the CSS and the template, with a control proving comments
    are stripped first. This round's own prose in base names .pd-stat, the
    class it deletes, so an unstripped check would read the prose and report a
    class that is gone.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant_payment_days.html')

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NOT re.S: Django's {# #} does not span lines, and a stripper more
    # permissive than the lexer it models certifies the faults it catches.
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def rules(src):
    """selector -> [declaration block, ...], media queries flattened."""
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'@media[^{]*\{', '', css)
    out = {}
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        for sel in m.group(1).split(','):
            sel = ' '.join(sel.split())
            if sel:
                out.setdefault(sel, []).append(' '.join(m.group(2).split()))
    return out


for p in (BASE, PAGE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)

BS, PG = read(BASE), read(PAGE)
if '.alv-stats {' not in BS:
    print('\n! not patched - run apply_alv_stat.py first.')
    sys.exit(1)

BC, PC = nocomment_html(BS), nocomment_html(PG)
B, P = rules(BS), rules(PG)

# The one literal that is house style: the grey every .alv-card prints with.
PRINT_GREY = '#9aa5ab'

# ===========================================================================
head('1. base owns the tile, the page owns none of it')
# ===========================================================================
# CONTROL FIRST. The round's prose in base names the class it deletes, so if
# comments were not stripped every "is gone" check below would read the prose.
check('CONTROL: the round\'s prose in base names .pd-stat', '.pd-stat' in BS)
check('CONTROL: .. and it is gone once stripped', '.pd-stat' not in BC)

for _sel in ('.alv-stats', '.alv-stat', '.alv-stat-value', '.alv-stat-label'):
    check('base defines %s' % _sel, bool(B.get(_sel)),
          '%d rule(s)' % len(B.get(_sel, [])))
for _v in ('good', 'attn', 'bad'):
    check('base defines .alv-stat-%s' % _v,
          bool(B.get('.alv-stat-%s .alv-stat-value' % _v)))

check('the tile brings its own surface', 'background' in ' '.join(B['.alv-stat']))
check('  and its own border', 'border' in ' '.join(B['.alv-stat']))
check('the tile prints in the same grey as a card',
      PRINT_GREY in ' '.join(B['.alv-stat']))

# NOT the string `background` in a rule - a verdict must not paint a surface
# by any route. This is the round's whole decision, stated in CSS.
for _v in ('good', 'attn', 'bad'):
    _all = ' '.join(B.get('.alv-stat-%s' % _v, [])
                    + B.get('.alv-stat-%s .alv-stat-value' % _v, []))
    check('.alv-stat-%s paints no surface' % _v, 'background' not in _all,
          _all[:60])
    check('  it sets a colour', 'color:' in _all, _all[:60])

for _sel in ('.alv-stats', '.alv-stat', '.alv-stat-value', '.alv-stat-label'):
    _decl = ' '.join(B.get(_sel, [])).replace(PRINT_GREY, '')
    check('%s carries no literal colour' % _sel,
          not re.search(r'#[0-9a-fA-F]{3,8}\b', _decl), _decl[:50])

# The page.
_tiles = len(re.findall(r'class="alv-stat[" ]', PC))
check('the page carries four tiles', _tiles == 4, '%d' % _tiles)
check('  in exactly one grid', PC.count('class="alv-stats"') == 1)
check('  each with a figure and a label',
      PC.count('alv-stat-value') == 4 and PC.count('alv-stat-label') == 4)
check('  and the flagged one carries a verdict', 'alv-stat-attn' in PC)
check('the page defines no tile CSS of its own',
      not [s for s in P if 'pd-stat' in s or 'pd-summary' in s],
      str([s for s in P if 'pd-stat' in s or 'pd-summary' in s]))
check('  no tile borrows .alv-card', 'alv-card' not in PC)
check('  and the amber wash is gone from the page', 'alv-warn-soft' not in PC)

# ===========================================================================
head('2. anchored on the system\'s tokens, and a real ordering')
# ===========================================================================
_blk = ' '.join(B['.alv-stat'] + B['.alv-stat-value'] + B['.alv-stat-label']
                + B['.alv-stats']
                + [' '.join(B['.alv-stat-%s .alv-stat-value' % v])
                   for v in ('good', 'attn', 'bad')])
for _tok in ('--alv-paper', '--alv-line', '--alv-ink-strong', '--alv-ink-soft',
             '--alv-good', '--alv-warn', '--alv-bad'):
    check('the component uses %s' % _tok, _tok in _blk)

# A TOKEN MUST BE DEFINED, NOT MERELY REFERENCED. `visually-hidden` was
# referenced and defined nowhere, and would have rendered as visible text.
# Vars used WITH a fallback are excluded: --alv-stats-cols is the component's
# parameter and nothing defines it on purpose.
for _tok in sorted(set(re.findall(r'var\((--alv-[a-z0-9-]+)\s*\)', _blk))):
    check('%s is defined, not just referenced' % _tok, '%s:' % _tok in BC)
check('--alv-stats-cols is used WITH a fallback, so no page must set it',
      'var(--alv-stats-cols, 4)' in BC)

check('the figures use tabular figures', 'tabular-nums' in ' '.join(B['.alv-stat-value']))

# ===========================================================================
head('3. rendered, at 390px and 1200px')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

if sync_playwright is not None:
    _bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S))

    # Four tiles as the page builds them, the three verdicts, a five-column
    # strip driven by the fallback property, and a CONTROL tile whose wash is
    # written inline so the probe has something it MUST see.
    FIX = """<!doctype html><meta name=viewport content="width=device-width">
<style>%s</style>
<div class="alv-stats" id="four">
  <div class="alv-stat"><div class="alv-stat-value">1284</div>
    <div class="alv-stat-label">payments measured</div></div>
  <div class="alv-stat alv-stat-good"><div class="alv-stat-value">31</div>
    <div class="alv-stat-label">excellent</div></div>
  <div class="alv-stat alv-stat-attn"><div class="alv-stat-value">4</div>
    <div class="alv-stat-label">flagged slow</div></div>
  <div class="alv-stat alv-stat-bad"><div class="alv-stat-value">2</div>
    <div class="alv-stat-label">needs improvement, a deliberately long one</div></div>
</div>
<div class="alv-stats" id="five" style="--alv-stats-cols: 5;">
  <div class="alv-stat"><div class="alv-stat-value">1</div><div class="alv-stat-label">a</div></div>
  <div class="alv-stat"><div class="alv-stat-value">2</div><div class="alv-stat-label">b</div></div>
  <div class="alv-stat"><div class="alv-stat-value">3</div><div class="alv-stat-label">c</div></div>
  <div class="alv-stat"><div class="alv-stat-value">4</div><div class="alv-stat-label">d</div></div>
  <div class="alv-stat"><div class="alv-stat-value">5</div><div class="alv-stat-label">e</div></div>
</div>
<div class="alv-stats" id="ctl">
  <div class="alv-stat" id="washed" style="background: rgb(255, 0, 0);">
    <div class="alv-stat-value">9</div><div class="alv-stat-label">control</div></div>
</div>
<span id="tokgood" style="color: var(--alv-good)"></span>
<span id="tokattn" style="color: var(--alv-warn)"></span>
<span id="tokbad"  style="color: var(--alv-bad)"></span>""" % _bcss

    _f = os.path.join(tempfile.gettempdir(), 'alv_stat_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const q = s => document.querySelector(s);
      const cs = s => getComputedStyle(q(s));
      const tiles = [...document.querySelectorAll('#four .alv-stat')];
      const r = el => el.getBoundingClientRect();
      return {
        cols4: cs('#four').gridTemplateColumns.split(' ').length,
        cols5: cs('#five').gridTemplateColumns.split(' ').length,
        tileTops: tiles.map(e => Math.round(r(e).top)),
        tileWidths: tiles.map(e => Math.round(r(e).width)),
        plainBg: cs('#four .alv-stat').backgroundColor,
        goodBg:  cs('.alv-stat-good').backgroundColor,
        attnBg:  cs('.alv-stat-attn').backgroundColor,
        badBg:   cs('.alv-stat-bad').backgroundColor,
        washedBg: cs('#washed').backgroundColor,
        plainVal: cs('#four .alv-stat .alv-stat-value').color,
        goodVal:  cs('.alv-stat-good .alv-stat-value').color,
        attnVal:  cs('.alv-stat-attn .alv-stat-value').color,
        badVal:   cs('.alv-stat-bad .alv-stat-value').color,
        goodLbl:  cs('.alv-stat-good .alv-stat-label').color,
        plainLbl: cs('#four .alv-stat .alv-stat-label').color,
        tokGood: cs('#tokgood').color,
        tokAttn: cs('#tokattn').color,
        tokBad:  cs('#tokbad').color,
        valueSize: cs('#four .alv-stat .alv-stat-value').fontSize,
        numeric: cs('#four .alv-stat .alv-stat-value').fontVariantNumeric,
        bodyWide: document.documentElement.scrollWidth
                    > document.documentElement.clientWidth,
      };
    }"""

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg_ = b.new_page(viewport={'width': 390, 'height': 900})
        pg_.goto('file://' + _f)
        M = pg_.evaluate(PROBE)
        pg_.set_viewport_size({'width': 1200, 'height': 900})
        D = pg_.evaluate(PROBE)
        b.close()

    # THE CONTROL. Everything below asserts an ABSENCE of colour, and an
    # absence is exactly what a broken probe reports for free.
    check('CONTROL: the probe can see a wash when there is one',
          M['washedBg'] == 'rgb(255, 0, 0)', M['washedBg'])
    check('CONTROL: .. and the plain tile is not that colour',
          M['plainBg'] != M['washedBg'], M['plainBg'])

    # THE DECISION OF 30 AUG.
    for _v in ('good', 'attn', 'bad'):
        check('a %s verdict does NOT wash the tile' % _v,
              D['%sBg' % _v] == D['plainBg'],
              '%s vs %s' % (D['%sBg' % _v], D['plainBg']))
        check('  it colours the figure', D['%sVal' % _v] != D['plainVal'],
              D['%sVal' % _v])
    check('and it leaves the label alone',
          D['goodLbl'] == D['plainLbl'], '%s vs %s' % (D['goodLbl'], D['plainLbl']))

    # The verdict colours ARE the system's, not lookalikes.
    check('good IS --alv-good', D['goodVal'] == D['tokGood'],
          '%s vs %s' % (D['goodVal'], D['tokGood']))
    check('attn IS --alv-warn', D['attnVal'] == D['tokAttn'],
          '%s vs %s' % (D['attnVal'], D['tokAttn']))
    check('bad IS --alv-bad', D['badVal'] == D['tokBad'],
          '%s vs %s' % (D['badVal'], D['tokBad']))
    # Two near-identical pale blues with a grey between them looked like a
    # scale and encoded no ordering at all. Three verdicts, three colours.
    check('the three verdicts are three DIFFERENT colours',
          len({D['goodVal'], D['attnVal'], D['badVal'], D['plainVal']}) == 4,
          str(sorted({D['goodVal'], D['attnVal'], D['badVal']})))

    # Layout.
    check('DESKTOP: four tiles on one line',
          D['cols4'] == 4 and len(set(D['tileTops'])) == 1,
          str(D['tileTops']))
    check('  of equal width, so a long label cannot starve its neighbours',
          len(set(D['tileWidths'])) == 1, str(D['tileWidths']))
    check('  and the fallback property drives a five-up strip',
          D['cols5'] == 5, str(D['cols5']))
    check('MOBILE: the grid drops to two-up', M['cols4'] == 2, str(M['cols4']))
    check('  in two rows of two', len(set(M['tileTops'])) == 2,
          str(M['tileTops']))
    check('  the figure shrinks with it',
          float(M['valueSize'][:-2]) < float(D['valueSize'][:-2]),
          '%s -> %s' % (D['valueSize'], M['valueSize']))
    check('  and nothing pushes the page sideways', not M['bodyWide'])
    check('the figures are tabular', 'tabular-nums' in D['numeric'],
          D['numeric'])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
