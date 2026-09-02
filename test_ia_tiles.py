"""test_ia_tiles.py - the Issues Analysis strip joins base's components.

    python test_ia_tiles.py

Run from the repo root, after apply_ia_tiles.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 RENDERS the strip at 960px (the modal) and 390px (a phone).
    It also records a decision that went the other way. A draft of this
    round shipped .alv-stats-sm, a compact density, arguing that base's
    .78rem uppercase label does not fit a 180px tile. The check for it
    passed - on the wrong branch of an `or`. Measured honestly, all five
    labels sit on ONE line at full size - the longest measuring 137px in a
    142px box on the build machine and 125px on Windows - and the variant
    bought 23px of strip height for a 9.9px label.
    So the suite now asserts the OPPOSITE: the labels fit, and base has no
    density variant. A later round that wants one has to argue for it.
  * SECTION 3 drives the ageing scale ARITHMETICALLY through the shipped
    ageBand(), including every boundary, and then renders one chip per band
    to confirm the class actually paints. A static verdict is what this
    round removed; a class that resolves to nothing would put it back.
  * SECTION 4 measures that base's EXISTING tiles did not move.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FSR = os.path.join(T, 'fsr.html')
BBAK = BASE + '.bak_iatile'

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


def nocomment(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


for p in (BASE, FSR):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)
BS, F = read(BASE), read(FSR)
if '.alv-stat-age' not in BS:
    print('\n! not patched - run apply_ia_tiles.py first.')
    sys.exit(1)
BC, FC = nocomment(BS), nocomment(F)

# ===========================================================================
head('1. the strip stops being a fifth implementation')
# ===========================================================================
check("CONTROL: the round's prose still names .ia-kpi", 'ia-kpi' in F)
check('CONTROL: .. and it is gone once stripped', 'ia-kpi' not in FC)

for dead in ('ia-kpis', 'ia-kpi', 'ia-badge', 'ia-age'):
    check('%s is gone' % dead,
          not re.search(r'(?<![\w-])%s(?![\w-])' % dead, FC))
for lit in ('#fff3d6', '#8a6100', '#d8f5da', '#0a6b1e'):
    check('  and the badge literal %s with it' % lit, lit not in FC)

check('the strip is base\'s, unmodified',
      'class="alv-stats"' in FC and 'alv-stats-sm' not in FC)
check('  five tiles, each with a value and a label',
      FC.count('class="alv-stat-value"') == 5
      and FC.count('class="alv-stat-label"') == 5)
check('  and the column count is a page rule, not an inline style',
      '#issuesAnalysisModal .alv-stats { --alv-stats-cols: 5; }' in FC
      and 'style="--alv-stats-cols' not in FC)

check('the two verdicts that point one way keep pointing',
      'alv-stat alv-stat-attn' in FC and 'alv-stat alv-stat-good' in FC)
check('  and NOTHING carries a fixed red any more',
      'alv-stat-bad' not in FC)
check('Oldest open is driven from the bands, not the markup',
      "$('iaKOldTile').className" in FC and 'ageBand(oldest).cls' in FC)
check('  and with nothing open it takes no band at all',
      "oldest!=null?' '+ageBand(oldest).cls:''" in FC.replace(' ', '')
      .replace('oldest!=null?', 'oldest!=null?') or
      re.search(r"oldest\s*!=\s*null\s*\?\s*'\s*'\s*\+\s*ageBand", FC)
      is not None)

check('the drill badges are house pills',
      'alv-pill alv-pill-good' in FC and 'alv-pill alv-pill-attn' in FC)
check('the age chip is the ageing scale\'s own pill',
      FC.count('alv-age-pill') == 1)
check('  and no inline colour survives in the modal script',
      'style="color:' not in FC)

check('every band carries its step class',
      all(("cls:'%s'" % c) in FC
          for c in ('alv-age-0', 'alv-age-2', 'alv-age-3', 'alv-age-4')))
check('  and alv-age-1 is absent - four bands, and the first is age-0',
      "cls:'alv-age-1'" not in FC)
check('one lookup feeds all three consumers',
      FC.count('function ageBand(') == 1
      and FC.count('ageBand(') >= 3)

# base's two additions.
check('base gains .alv-stat-age - --age on a figure',
      '.alv-stat-age .alv-stat-value' in BC and 'var(--age' in BC)
check('  and NOTHING else - the density variant was measured and rejected',
      'alv-stats-sm' not in BC)

# ===========================================================================
head('2. rendered: does the density earn its place?')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

BOOT = None
for _c in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           '/tmp/bootstrap.min.css'):
    if os.path.exists(_c):
        BOOT = open(_c, encoding='utf-8').read()
        break
if BOOT is None:
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
    sync_playwright = None

if sync_playwright is not None:
    def css_of(src):
        return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))

    TILES = [('iaKTotal', '1,284', 'Total issues', ''),
             ('iaKOpen', '42', 'Still open', ' alv-stat-attn'),
             ('iaKRes', '1,242', 'Resolved', ' alv-stat-good'),
             ('iaKMed', '17d', 'Median to resolve', ''),
             ('iaKOld', '226d', 'Oldest open', ' alv-stat-age alv-age-4')]

    def strip():
        out = ['<div class="alv-stats" style="--alv-stats-cols:5">']
        for i, (tid, v, l, extra) in enumerate(TILES):
            out.append('<div class="alv-stat%s" id="t_%d">'
                       '<div class="alv-stat-value" id="tv_%d">%s</div>'
                       '<div class="alv-stat-label" id="tl_%d">%s</div></div>'
                       % (extra, i, i, v, i, l))
        out.append('</div>')
        return '\n'.join(out)

    CHIPS = ''.join(
        '<span class="alv-age-pill %s" id="chip_%s">%sd</span> '
        % (c, c, d) for c, d in (('alv-age-0', 12), ('alv-age-2', 60),
                                 ('alv-age-3', 140), ('alv-age-4', 300)))

    FIX = """<!doctype html><meta charset=utf-8>
<style>%s</style><style>%s</style><style>%s</style>
<style>body{margin:0;padding:0;background:#eef1f2}
 #modal{width:960px;padding:16px;background:#fff}
 #loud{font-size:31px;font-weight:800}
</style>
<div id="modal">
  <div id="issuesAnalysisModal"><div class="ia-body">
    <div id="wrap">%s</div>
    <div id="chips">%s</div>
  </div></div>
</div>
<div id="loud">control</div>
""" % (BOOT, css_of(BS), css_of(F), strip(), CHIPS)

    _f = os.path.join(tempfile.gettempdir(), 'ia_tiles_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const cs = s => getComputedStyle(document.querySelector(s));
      const box = s => { const e = document.querySelector(s);
        const r = e.getBoundingClientRect();
        return {w: Math.round(r.width), h: Math.round(r.height)}; };
      // Does the text fit on one line inside its own box?
      const lines = s => { const e = document.querySelector(s);
        const r = document.createRange(); r.selectNodeContents(e);
        return r.getClientRects().length; };
      const overflows = s => { const e = document.querySelector(s);
        return e.scrollWidth > e.clientWidth + 1; };
      const chip = c => { const e = document.querySelector('#chip_' + c);
        const g = getComputedStyle(e);
        return {color: g.color, bg: g.backgroundColor}; };
      const labelW = s => { const e = document.querySelector(s);
        const r = document.createRange(); r.selectNodeContents(e);
        return Math.round(r.getBoundingClientRect().width); };
      return {
        smTile: box('#t_3'),
        labelLines: [0,1,2,3,4].map(i => lines('#tl_' + i)),
        widestLabel: Math.max(...[0,1,2,3,4].map(i => labelW('#tl_' + i))),
        labelBox: box('#tl_3').w,
        heights: [0,1,2,3,4].map(i => Math.round(
            document.querySelector('#t_' + i).getBoundingClientRect().height)),
        value: cs('#tv_3').fontSize, label: cs('#tl_3').fontSize,
        oldFigure: cs('#tv_4').color,
        totalFigure: cs('#tv_0').color,
        openFigure: cs('#tv_1').color,
        doneFigure: cs('#tv_2').color,
        tileBg: cs('#t_4').backgroundColor,
        chips: {a0: chip('alv-age-0'), a2: chip('alv-age-2'),
                a3: chip('alv-age-3'), a4: chip('alv-age-4')},
        loud: cs('#loud').fontSize,
        cols: cs('#wrap > .alv-stats').gridTemplateColumns.split(' ').length,
      };
    }"""

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1100, 'height': 900})
        pg.goto('file://' + _f)
        D = pg.evaluate(PROBE)
        # Stepped, not sampled at one width - see the note in section 2.
        WIDTHS = [900, 850, 800, 780]
        NARROW = {}
        for _w in WIDTHS:
            pg.evaluate("w => document.getElementById('modal')"
                        ".style.width = w + 'px'", _w)
            NARROW[_w] = pg.evaluate(PROBE)
        pg.evaluate("() => document.getElementById('modal').style.width='960px'")
        pg.set_viewport_size({'width': 390, 'height': 900})
        pg.evaluate("() => document.getElementById('modal').style.width='auto'")
        P = pg.evaluate(PROBE)
        b.close()

    check('CONTROL: the probe reads a deliberately sized element',
          D['loud'] == '31px', D['loud'])

    # THE CASE AGAINST A COMPACT VARIANT, which is why none shipped. The
    # draft argued base's label does not fit a 180px tile. It does.
    check('the modal strip really is ~180px a tile',
          160 <= D['smTile']['w'] <= 200, '%dpx' % D['smTile']['w'])
    check('  and base\'s FULL label fits it on ONE line - all five of them',
          D['labelLines'] == [1, 1, 1, 1, 1], str(D['labelLines']))
    check('  the longest label clears its box - by however much this '
          'machine\'s font leaves',
          D['widestLabel'] < D['labelBox'],
          '%dpx of text in a %dpx box, %dpx of slack'
          % (D['widestLabel'], D['labelBox'], D['labelBox'] - D['widestLabel']))
    check('  so base has no density variant, and this round did not add one',
          '.alv-stats-sm' not in BC)
    check('  the five tiles are all the same height',
          len(set(D['heights'])) == 1, str(D['heights']))
    check('  five columns in the modal', D['cols'] == 5, str(D['cols']))

    # A VERDICT COLOURS THE FIGURE, NOT THE BOX - base's rule, kept.
    check('the tile surface stays plain under a severity class',
          D['tileBg'] in ('rgb(255, 255, 255)', 'rgba(0, 0, 0, 0)'),
          D['tileBg'])
    check('  while the FIGURE takes the colour',
          D['oldFigure'] != D['totalFigure'],
          'oldest %s vs plain %s' % (D['oldFigure'], D['totalFigure']))
    check('  Still open is the warn tone and Resolved the good one',
          D['openFigure'] != D['totalFigure']
          and D['doneFigure'] != D['totalFigure']
          and D['openFigure'] != D['doneFigure'])

    # THE PHONE. base's two-across wins, and the compact sizes must relax.
    check('PHONE: base\'s two-across rule wins over the page',
          P['cols'] == 2, '%d columns' % P['cols'])
    # base shrinks the figure on a phone by its own rule (1.7rem -> 1.4rem).
    # A first draft asserted "one size at both widths", which is not what
    # base does and never was - dropping the variant did not make the tile
    # size-invariant, it made this page follow base at BOTH widths.
    check('  and the figure follows base\'s phone size, not a page override',
          float(P['value'][:-2]) < float(D['value'][:-2]),
          'modal %s -> phone %s' % (D['value'], P['value']))
    check('  labels still fit, two across on a phone',
          P['labelLines'] == [1, 1, 1, 1, 1], str(P['labelLines']))

    # THE SLACK IS FONT-DEPENDENT, AND THAT IS THE LESSON.
    #
    # A first draft asserted "the longest label wraps at 900px". On the build
    # machine it did - the label measured 137px in a 142px box, 5px of slack.
    # On the first other machine this suite ran on the same label rendered
    # 125px, 17px of slack, and it did not wrap. The check was asserting a
    # FONT METRIC dressed up as a layout claim, and it failed correctly.
    #
    # .modal-xl is a MAX-width, so the tiles do narrow between base's 768px
    # breakpoint and 960px, and somewhere in there any font runs out of room.
    # WHERE is not this suite's business. The INVARIANT is: wherever the
    # label wraps, the strip must stay even and stay five across - a grid
    # property, true on every font. So the dialogue is stepped down to the
    # breakpoint, the wrap is required to happen SOMEWHERE in that range, and
    # evenness is checked at every step.
    _wrapped = [w for w in WIDTHS if NARROW[w]['labelLines'] != [1, 1, 1, 1, 1]]
    check('NARROW DESKTOP: the longest label runs out of room somewhere '
          'above base\'s breakpoint (the WIDTH is font-dependent, so it is '
          'not asserted)',
          bool(_wrapped),
          'wrapped at %s' % (_wrapped or 'no width down to %dpx' % WIDTHS[-1]))
    for _w in WIDTHS:
        check('  %dpx: the five tiles stay exactly the same height' % _w,
              len(set(NARROW[_w]['heights'])) == 1, str(NARROW[_w]['heights']))
    check('  and it is still five across at every one of them - it degrades '
          'by growing, not by breaking',
          all(NARROW[_w]['cols'] == 5 for _w in WIDTHS),
          str([NARROW[_w]['cols'] for _w in WIDTHS]))

    # The chips must actually paint - a class resolving to nothing would put
    # the static verdict straight back.
    _seen = [D['chips'][k]['color'] for k in ('a0', 'a2', 'a3', 'a4')]
    check('all four ageing chips paint a DIFFERENT colour',
          len(set(_seen)) == 4, str(_seen))
    check('  and none of them is transparent or unset',
          all(c not in ('rgba(0, 0, 0, 0)', '') for c in _seen))
    check('  each has a tint behind it too',
          all(D['chips'][k]['bg'] not in ('rgba(0, 0, 0, 0)', '')
              for k in ('a0', 'a2', 'a3', 'a4')))

# ===========================================================================
head('3. the ageing scale, driven through the shipped code')
# ===========================================================================
if sync_playwright is not None:
    m = re.search(r'(var AGE_BANDS=\[.*?\];)', F, re.S)
    n = re.search(r'(function ageBand\(a\)\{.*?\n  \})', F, re.S)
    if not (m and n):
        check('the bands and the lookup could be lifted out', False)
    else:
        check('the bands and the lookup could be lifted out', True)
        SRC = ("var GOOD='g',WARN='w',SERIOUS='s',CRIT='c';\n"
               + m.group(1) + '\n' + n.group(1) + '\nreturn ageBand;')
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page()
            pg.goto('about:blank')
            got = pg.evaluate(
                """([src, days]) => { const f = new Function(src)();
                     return days.map(d => f(d).cls); }""",
                [SRC, [0, 1, 30, 31, 89, 90, 91, 179, 180, 181, 5000]])
            b.close()
        WANT = ['alv-age-0', 'alv-age-0', 'alv-age-0',   # 0, 1, 30
                'alv-age-2', 'alv-age-2', 'alv-age-2',   # 31, 89, 90
                'alv-age-3', 'alv-age-3', 'alv-age-3',   # 91, 179, 180
                'alv-age-4', 'alv-age-4']                # 181, 5000
        for d, w, g in zip([0, 1, 30, 31, 89, 90, 91, 179, 180, 181, 5000],
                           WANT, got):
            check('  %4dd -> %s' % (d, w), w == g, '' if w == g else 'got ' + g)
        # THE BOUNDARY THE LABEL USED TO LIE ABOUT.
        check('  90d and 91d land in DIFFERENT bands, as the labels say',
              got[5] != got[6], '%s / %s' % (got[5], got[6]))

# ===========================================================================
head('4. base\'s existing tiles did not move')
# ===========================================================================
if sync_playwright is not None and os.path.exists(BBAK):
    OLD = read(BBAK)
    OFIX = """<!doctype html><meta charset=utf-8><style>%s</style><style>%s</style>
<div style="width:900px"><div class="alv-stats">
  <div class="alv-stat"><div class="alv-stat-value" id="v">1,284</div>
    <div class="alv-stat-label" id="l">Total issues</div></div>
  <div class="alv-stat alv-stat-good"><div class="alv-stat-value" id="g">99</div>
    <div class="alv-stat-label">Good</div></div>
</div></div>"""
    _o = os.path.join(tempfile.gettempdir(), 'ia_tiles_before.html')
    _n = os.path.join(tempfile.gettempdir(), 'ia_tiles_after.html')
    with open(_o, 'w', encoding='utf-8') as fh:
        fh.write(OFIX % (BOOT, css_of(OLD)))
    with open(_n, 'w', encoding='utf-8') as fh:
        fh.write(OFIX % (BOOT, css_of(BS)))
    Q = """() => { const cs = s => getComputedStyle(document.querySelector(s));
        const r = document.querySelector('.alv-stat').getBoundingClientRect();
        return {v: cs('#v').fontSize, l: cs('#l').fontSize,
                good: cs('#g').color, w: Math.round(r.width),
                h: Math.round(r.height),
                cols: cs('.alv-stats').gridTemplateColumns}; }"""
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1100, 'height': 800})
        pg.goto('file://' + _o)
        WAS = pg.evaluate(Q)
        pg.goto('file://' + _n)
        NOW = pg.evaluate(Q)
        b.close()
    for k in ('v', 'l', 'good', 'w', 'h', 'cols'):
        check('a plain .alv-stat is unchanged (%s)' % k, WAS[k] == NOW[k],
              '%s vs %s' % (WAS[k], NOW[k]))
    check('CONTROL: the two stylesheets really do differ',
          css_of(OLD) != css_of(BS))

# ===========================================================================
head('5. scope, and the lesson from C1')
# ===========================================================================
check('.ia-tab is untouched - the segmented control is its own round',
      '.ia-tab{border:none;background:transparent' in FC)
check('the .ia-drill overlay and its table are untouched - C3',
      'table.ia-tbl{' in FC and '.ia-drill{' in FC)
check('the page-local @media still prints - the scanner round owns it',
      '@media (max-width:768px){' in F)
check('C1 survives: the charts still read base tokens',
      'iaTok(' in FC and 'AGE_BANDS' in FC)

# PROSE THAT CONTAINS MARKUP IS MARKUP.
for _name, _txt in (('fsr.html', F), ('base.html', BS)):
    _bad = [m.group(0)[:70] for m in re.finditer(r'/\*.*?\*/', _txt, re.S)
            if re.search(r'</?(?:script|style)\b', m.group(0))]
    check('%s: no CSS comment spells a script or style tag' % _name,
          not _bad, _bad[0] if _bad else '')

if sync_playwright is not None:
    def _flat(t):
        t = re.sub(r'\{%[^%]*%\}', '', t)
        return re.sub(r'\{\{[^}]*\}\}', 'x', t)
    _blocks = [_flat(x) for x in re.findall(
        r'<script(?![^>]*src=)[^>]*>(.*?)</script>', F, re.S)]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto('about:blank')
        _errs = [pg.evaluate(
            "s => { try { new Function(s); return '' } catch (e) "
            "{ return e instanceof SyntaxError ? String(e.message) : '' } }", x)
            for x in _blocks]
        b.close()
    check('every script block in fsr.html still parses',
          not any(_errs), '; '.join(e for e in _errs if e)
          or '%d blocks' % len(_blocks))

for blk in re.findall(r'<style[^>]*>(.*?)</style>', F, re.S):
    check('braces balance in a style block', blk.count('{') == blk.count('}'))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
