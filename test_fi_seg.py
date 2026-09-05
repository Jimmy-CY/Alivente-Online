"""test_fi_seg.py - Financial Indicators takes the house switch.

    python test_fi_seg.py

Run from the repo root, after apply_fi_seg.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 RENDERS the four controls. The round's central claim is that
    the two All/None pairs, which were built differently on the same page,
    now look THE SAME - and "the same" is a comparison of computed styles,
    not of class names. The CONTROL renders the same four from .bak_fiseg,
    where the two pairs must DIFFER; without it, "they match" would pass on
    a probe that returned nothing twice.

  * IT ALSO CHECKS THE SEGMENT IS A SEGMENT. base's own note says the
    current one is filled and the rest are quiet, and that nothing in the
    component carries a semantic colour. Both are measured: the pressed
    segment takes the accent, the other takes the paper, and neither takes
    good / warn / bad.

  * SECTION 3 is the ARITHMETIC the round nearly got wrong. A draft claimed
    deleting three rules "took the accent out of the page". It did not -
    eighteen #0e7c8b sat in that stylesheet and only two were in the deleted
    rules. The suite asserts the DELTA is exactly two and that the other
    sixteen are still there, so the page's own palette round still has its
    work and nobody reads this round as having done it.

  * SECTION 4 asserts base's component is untouched and its note now tells
    the truth about who asked for it.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FI = os.path.join(T, 'finance', 'financial_indicators.html')
BBAK, FBAK = BASE + '.bak_fiseg', FI + '.bak_fiseg'

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
    return re.sub(r'/\*.*?\*/', '', text, flags=re.S)


for p in (BASE, FI):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)
BS, F = read(BASE), read(FI)
if 'alv-seg' not in F:
    print('\n! not patched - run apply_fi_seg.py first.')
    sys.exit(1)
BC, FC = nocomment(BS), nocomment(F)

# ===========================================================================
head('1. the page stops hand-rolling what base already had')
# ===========================================================================
check("CONTROL: the round's prose still names btn-info", 'btn-info' in F)
check('CONTROL: .. and it is gone once stripped', 'btn-info' not in FC)

for dead in ('btn-info', 'btn-outline-info', 'btn-secondary',
             'btn-outline-secondary', 'btn-sm', 'btn-group'):
    check('%-22s is gone' % dead,
          not re.search(r'(?<![\w-])%s(?![\w-])' % dead, FC))

check('the switch is base\'s', 'class="alv-seg"' in FC)
check('  and it says which view you are on, twice',
      FC.count('aria-current="page"') == 2)
check('  the basis links keep their query strings',
      '?year={{ selected_year }}&basis=budget' in FC
      and '?year={{ selected_year }}&basis=actuals' in FC)

check('five buttons joined the house set',
      FC.count('class="btn action-secondary"') == 8,
      '%d, of which 3 were already there' % FC.count('class="btn action-secondary"'))

# THE IDS ARE THE PAGE'S WIRING. Lose one and its script stops finding it.
for _id in ('fiCompareBtn', 'fiTrendAll', 'fiTrendNone', 'selectAllBtn',
            'selectNoneBtn'):
    check('  the id %s survives' % _id, _id in FC)
check('  and its script still reaches for them',
      all(("'%s'" % i) in F or ('"%s"' % i) in F
          for i in ('fiCompareBtn', 'fiTrendAll', 'selectAllBtn')))

# ===========================================================================
head('2. rendered: do the two All/None pairs finally agree?')
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

    AFTER = ('<div class="alv-seg" id="seg"><a href="#" id="on" '
             'aria-current="page">Budget</a><a href="#" id="off">Actuals</a></div>'
             '<button class="btn action-secondary" id="a1">All</button>'
             '<button class="btn action-secondary" id="n1">None</button>'
             '<button class="btn action-secondary" id="a2">Select All</button>'
             '<button class="btn action-secondary" id="n2">Select None</button>')
    BEFORE = ('<div class="btn-group" id="seg"><a href="#" id="on" '
              'class="btn btn-info">Budget</a><a href="#" id="off" '
              'class="btn btn-outline-info">Actuals</a></div>'
              '<button class="btn btn-sm btn-outline-info" id="a1">All</button>'
              '<button class="btn btn-sm btn-outline-secondary" id="n1">None</button>'
              '<button class="btn btn-info btn-sm" id="a2">Select All</button>'
              '<button class="btn btn-secondary btn-sm" id="n2">Select None</button>')

    FIX = ('<!doctype html><meta charset=utf-8><style>%s</style>'
           '<style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:16px;background:#fff}'
           '#loud{font-size:29px;font-weight:800}</style>%s'
           '<div id="loud">control</div>')

    PROBE = """() => {
      // STYLE, not geometry. A first draft compared the whole box and
      // failed on width, because "All" and "Select All" are different words
      // - which is a fact about English, not about the round.
      const g = s => { const e = document.getElementById(s);
        const c = getComputedStyle(e); const r = e.getBoundingClientRect();
        return {bg: c.backgroundColor, fg: c.color,
                bd: c.borderTopColor + '|' + c.borderTopWidth,
                fw: c.fontWeight, h: Math.round(r.height),
                w: Math.round(r.width)}; };
      const skin = o => ({bg: o.bg, fg: o.fg, bd: o.bd, fw: o.fw, h: o.h});
      return {on: g('on'), off: g('off'), seg: g('seg'),
              a1: skin(g('a1')), n1: skin(g('n1')),
              a2: skin(g('a2')), n2: skin(g('n2')),
              loud: getComputedStyle(document.getElementById('loud')).fontSize,
              segDisplay: getComputedStyle(document.getElementById('seg')).display};
    }"""

    def render(pw, bs, fs, markup):
        f = os.path.join(tempfile.gettempdir(), 'fiseg.html')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(FIX % (BOOT, css_of(bs), css_of(fs), markup))
        pg = pw.new_page(viewport={'width': 900, 'height': 400})
        pg.goto('file://' + f)
        r = pg.evaluate(PROBE)
        pg.close()
        return r

    with sync_playwright() as p:
        b = p.chromium.launch()
        NOW = render(b, BS, F, AFTER)
        WAS = None
        if os.path.exists(BBAK) and os.path.exists(FBAK):
            WAS = render(b, read(BBAK), read(FBAK), BEFORE)
        b.close()

    check('CONTROL: the probe reads a deliberately sized element',
          NOW['loud'] == '29px', NOW['loud'])

    # THE ROUND'S CENTRAL CLAIM.
    check('the two All/None pairs now render IDENTICALLY',
          NOW['a1'] == NOW['a2'] and NOW['n1'] == NOW['n2'],
          '%s / %s' % (NOW['a1']['bg'], NOW['a2']['bg']))
    check('  and All and None are peers - neither shouts',
          NOW['a1'] == NOW['n1'],
          '%s vs %s' % (NOW['a1']['bg'], NOW['n1']['bg']))
    if WAS:
        check('  CONTROL: before the round the two pairs DIFFERED',
              WAS['a1'] != WAS['a2'] or WAS['n1'] != WAS['n2'],
              'All was %s in one panel and %s in the other'
              % (WAS['a1']['bg'], WAS['a2']['bg']))
        check('  CONTROL: and All shouted louder than None',
              WAS['a2'] != WAS['n2'],
              '%s vs %s' % (WAS['a2']['bg'], WAS['n2']['bg']))

    # THE SEGMENT IS A SEGMENT - base's own description, measured.
    check('the current segment is FILLED and the other is not',
          NOW['on']['bg'] != NOW['off']['bg'],
          '%s vs %s' % (NOW['on']['bg'], NOW['off']['bg']))
    check('  the quiet one is not transparent-on-nothing either',
          NOW['off']['fg'] != NOW['on']['fg'])
    check('  the control is INLINE, not stretched across the row',
          NOW['segDisplay'] == 'inline-flex' and NOW['seg']['w'] < 400,
          '%s, %dpx' % (NOW['segDisplay'], NOW['seg']['w']))
    check('  and it carries no semantic colour',
          not re.search(r'\.alv-seg[^{]*\{[^}]*var\(--alv-(good|warn|bad)',
                        BC))

# ===========================================================================
head('3. the arithmetic this round nearly got wrong')
# ===========================================================================
# A draft of the push body said deleting three rules "took the accent out of
# this page". Eighteen #0e7c8b were in that stylesheet and TWO were in the
# deleted rules. Both halves are asserted: the two went, the sixteen stayed.
if os.path.exists(FBAK):
    FB = nocomment(read(FBAK))
    _gone = FB.count('#0e7c8b') - FC.count('#0e7c8b')
    check('exactly two accent literals were removed', _gone == 2, str(_gone))
    check('  and the page palette is untouched - its own round still has '
          'its work', FC.count('#0e7c8b') >= 15,
          '%d left' % FC.count('#0e7c8b'))
    check('  CONTROL: there really were more to leave behind',
          FB.count('#0e7c8b') > 10, '%d before' % FB.count('#0e7c8b'))
else:
    check('a .bak_fiseg to measure the delta against', False)

for lit in ('#0a5e6a', '#5a6268', '#545b62'):
    check('%s left the page entirely' % lit, lit not in FC)
check('#6c757d did NOT - it has many other homes here',
      FC.count('#6c757d') >= 10, '%d left' % FC.count('#6c757d'))

# ===========================================================================
head('4. base: the component is untouched, its note is now true')
# ===========================================================================
check('.alv-seg itself is unchanged',
      '.alv-seg {' in BC and '.alv-seg > * + * ' in BC
      and 'aria-current="page"' in BC)
if os.path.exists(BBAK):
    _ob = nocomment(read(BBAK))

    def rules(t):
        i = t.index('.alv-seg {')
        return t[i:i + 1400]
    check('  byte-for-byte, once the comments come off',
          rules(_ob) == rules(BC))
    # The raw files, not the stripped ones. This round changes NOTHING in
    # base but a comment, so once comments come off the two are identical -
    # a first draft asserted they differ and failed, which was the round
    # behaving correctly and the check asking the wrong question.
    check('  CONTROL: and the raw files DO differ, because the note changed',
          read(BBAK) != BS)
    check('  .. by comment only - no rule in base moved',
          nocomment(read(BBAK)) == BC)

check('the note stops naming an asker that never existed',
      'AMENDED 2 Sep' in BS)
check('  and says what tenant_payment_days actually has',
      '.pd-toggle' in BS and 'aria-expanded' in BS)
check('  and records why the Analysis tabs were left',
      'NOT A TAB BAR' in BS)

# PROSE THAT CONTAINS MARKUP IS MARKUP.
for _n, _t in (('base.html', BS), ('financial_indicators.html', F)):
    _bad = [m.group(0)[:60] for m in re.finditer(r'/\*.*?\*/', _t, re.S)
            if re.search(r'</?(?:script|style)\b', m.group(0))]
    check('%s: no CSS comment spells a script or style tag' % _n, not _bad,
          _bad[0] if _bad else '')

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
