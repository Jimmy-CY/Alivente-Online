"""test_finance_headings.py - Financials heads its pages the way the system does.

    python test_finance_headings.py

Run from the repo root, after apply_finance_headings.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 RENDERS, because "the band is gone" is a computed value and
    "the heading is centred" is a measured position, not a class name. Both
    are taken from the browser, before and after, from the real stylesheets.

  * SECTION 4 IS THE CONTROL THAT MATTERS. This round must NOT touch the
    modal headers, which use the identical gradient and are the next round -
    three of the twenty pages have one. A patcher that swept every gradient
    would pass section 3 and quietly do work nobody agreed to. The suite
    counts them before and after and requires the same number.

  * SECTION 5 measures the .editing-pill on the six pages that carry one. It
    was rgba(255,255,255,0.22) with a white border: a shape only on a
    coloured ground, invisible on paper. Measured against what is actually
    behind it, not against its own background - reading rgba(0,0,0,0) as
    black is a mistake this project has already made once this week.

  * SECTION 6 asserts what the round left alone: the green and red row
    buttons, the pale property-header gradients, and every Django tag.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It renders base plus each page's own
<style> around that page's heading block. It is not the Django page: it
cannot tell whether Save saves. It also cannot check an icon - Font Awesome
is a CDN request and every render here refuses the network deliberately -
which matters here only in the negative: the round REMOVES icons, and their
absence from the markup is checked as text.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

REVENUE = ['finance_revenue.html', 'finance_revenue_add.html',
           'finance_revenue_edit.html', 'finance_revenue_line_types.html',
           'finance_revenue_line_types_add.html',
           'finance_revenue_line_types_edit.html',
           'finance_revenue_types.html', 'finance_revenue_types_add.html',
           'finance_revenue_types_edit.html']
EXPENSE = [n.replace('revenue', 'expense') for n in REVENUE]
OTHER = ['occupancy_trends.html', 'finance/vacancy_management.html']
PAGES = REVENUE + EXPENSE + OTHER
BAND = {'green': 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
        'red': 'linear-gradient(135deg, #dc3545 0%, #e83e8c 100%)',
        'teal': 'linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%)'}


def hue_of(rel):
    return 'green' if rel in REVENUE else 'red' if rel in EXPENSE else 'teal'


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


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def nocomment(t):
    return re.sub(r'/\*.*?\*/', '', re.sub(r'<!--.*?-->', '', t, flags=re.S),
                  flags=re.S)


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def path_of(rel):
    return os.path.join(T, rel.replace('/', os.sep))


for _r in PAGES:
    if not os.path.exists(path_of(_r)):
        sys.exit('! %s not found - run from the repo root' % _r)
    if not os.path.exists(path_of(_r) + '.bak_hdr'):
        sys.exit('! no %s.bak_hdr - run apply_finance_headings.py first.' % _r)

NOW = {r: read(path_of(r)) for r in PAGES}
WAS = {r: read(path_of(r) + '.bak_hdr') for r in PAGES}
BCSS = css_of(read(BASE))

# ===========================================================================
head('1. the band is gone, and only the band')
# ===========================================================================
check('CONTROL: the comment stripper strips',
      'THE COLOURED BANNER WENT' not in nocomment(NOW[PAGES[0]]))
check('CONTROL: .. and leaves the code',
      '<style' in nocomment(NOW[PAGES[0]]))

for rel in PAGES:
    css = css_of(nocomment(NOW[rel]))
    mk = markup_of(nocomment(NOW[rel]))
    hue = hue_of(rel)
    ok = True
    ok &= check('%-38s the .page-header div is gone' % rel,
                'page-header' not in mk)
    ok &= check('  and no .page-header rule survives',
                not re.search(r'(?m)^[ \t]*\.page-header\b', css))
    # ON A HEADER SELECTOR. The band's gradient also dresses three of these
    # pages' MODAL headers, which are the next round - a blanket check on
    # the string failed all three on a correct patch.
    for m in re.finditer(r'(?m)^[ \t]*([^{}\n@][^{\n]*)\{([^{}]*)\}', css):
        if 'modal' in m.group(1).lower():
            continue
        ok &= check('  no band gradient on %s' % m.group(1).strip()[:34],
                    BAND[hue] not in m.group(2)) if BAND[hue] in m.group(2) \
            else True
    check('  CONTROL: it WAS a %s band' % hue,
          BAND[hue] in css_of(nocomment(WAS[rel])))
    check('  the round says why', 'THE COLOURED BANNER WENT' in NOW[rel])

# ===========================================================================
head('2. the heading is the one 65 other pages use')
# ===========================================================================
for rel in PAGES:
    mk = markup_of(nocomment(NOW[rel]))
    was = markup_of(nocomment(WAS[rel]))
    h2 = re.search(r'<h2><center>(.*?)</center></h2>', mk, re.S)
    check('%-38s has a centred <h2>' % rel, h2 is not None)
    if h2:
        check('  with no icon in it', '<i ' not in h2.group(1),
              h2.group(1).strip()[:34])
        check('  and its words are the ones that were there',
              re.sub(r'<[^>]*>', '', re.search(r'<h1[^>]*>(.*?)</h1>', was,
                                               re.S).group(1)).strip()
              in re.sub(r'\s+', ' ', h2.group(1)).strip())
    check('  no <h1> survives', '<h1' not in mk)
    check('  CONTROL: there WAS one', '<h1' in was)
    # A subtitle becomes a centred h5 - and only where there was one.
    n_p = len(re.findall(r'<p>', re.search(
        r'<div class="page-header">(.*?)</div>\s*(?:<!--|<div|\{%)',
        was, re.S).group(1) if re.search(
        r'<div class="page-header">(.*?)</div>\s*(?:<!--|<div|\{%)', was, re.S)
        else ''))
    n_h5 = len(re.findall(r'<h5><center>', mk))
    check('  %d subtitle(s) became %d centred <h5>' % (n_p, n_h5),
          n_h5 >= (1 if n_p else 0), '%d -> %d' % (n_p, n_h5))

# ===========================================================================
head('3. what the browser paints')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed - sections 3 and 5 need it')
    sync_playwright = None

FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''
check('the Bootstrap fixture is present', bool(FIX))

_PW = _BR = None


def browser():
    global _PW, _BR
    if _BR is None:
        _PW = sync_playwright().start()
        _BR = _PW.chromium.launch()
    return _BR


def block_of(src, new):
    """The heading block: the .page-header div before, or the run from the
       first <h2> to the <br/> after."""
    mk = markup_of(src)
    if new:
        i = mk.find('<h2><center>')
        j = mk.find('<br/>', i)
        t = mk[i:j] if i >= 0 else ''
    else:
        i = mk.find('<div class="page-header">')
        if i < 0:
            return ''
        d, k = 1, mk.index('>', i) + 1
        for x in re.finditer(r'</?div\b', mk[k:]):
            d += 1 if x.group(0) == '<div' else -1
            if d == 0:
                k = k + x.start() + 6
                break
        t = mk[i:k]
    t = re.sub(r'\{%\s*if[^%]*%\}(.*?)\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}',
               lambda m: m.group(1), t, flags=re.S)
    t = re.sub(r'\{%[^%]*%\}', '', t)
    return re.sub(r'\{\{[^}]*\}\}', 'Apolloneon', t)


MEASURE = """() => {
    const h = document.querySelector('h1, h2');
    if (!h) return null;
    const c = getComputedStyle(h);
    const box = h.getBoundingClientRect();
    // GROUND, not backgroundColor: a heading on paper has none of its own.
    let g = 'rgb(255, 255, 255)';
    for (let e = h; e; e = e.parentElement) {
        const b = getComputedStyle(e).backgroundColor;
        const m = b.match(/[\\d.]+/g);
        if (m && (m.length < 4 || parseFloat(m[3]) > 0)) { g = b; break; }
    }
    const wrap = h.parentElement.getBoundingClientRect();
    // THE TEXT'S OWN BOX, NOT THE HEADING'S. A block <h1> fills its parent
    // whatever its alignment, so comparing the heading's box centre to the
    // parent's says "centred" for a left-aligned title too - which failed
    // every CONTROL on a correct patch. A Range measures the glyphs.
    const rng = document.createRange();
    rng.selectNodeContents(h);
    const tb = rng.getBoundingClientRect();
    const pill = document.querySelector('.editing-pill');
    return {ink: c.color, ground: g, align: c.textAlign,
            gradient: [...document.querySelectorAll('*')].some(
                e => getComputedStyle(e).backgroundImage.includes('gradient')),
            centred: tb.width > 0 && Math.abs((tb.left + tb.right) / 2
                              - (wrap.left + wrap.right) / 2) < 8,
            textLeft: Math.round(tb.left), textRight: Math.round(tb.right),
            pill: pill ? {bg: getComputedStyle(pill).backgroundColor,
                          ink: getComputedStyle(pill).color,
                          w: Math.round(pill.getBoundingClientRect().width),
                          cx: Math.round((pill.getBoundingClientRect().left
                              + pill.getBoundingClientRect().right) / 2)}
                       : null,
            wrapCx: Math.round((wrap.left + wrap.right) / 2)};
}"""


def paint(rel, new, width=1000):
    src = NOW[rel] if new else WAS[rel]
    doc = ('<!doctype html><meta charset=utf-8><style>%s</style>'
           '<style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:18px;background:#fff}</style>'
           '<body>%s</body>' % (FIX, BCSS, css_of(src), block_of(src, new)))
    pg = browser().new_page(viewport={'width': width, 'height': 420})
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    pg.set_content(doc, wait_until='domcontentloaded')
    try:
        return pg.evaluate(MEASURE)
    finally:
        pg.close()


def rgb(s):
    return tuple(int(x) for x in re.findall(r'\d+', s)[:3])


if sync_playwright is not None and FIX:
    for rel in PAGES:
        now, was = paint(rel, True), paint(rel, False)
        check('%-38s BEFORE the heading sat on a gradient' % rel,
              was is not None and was['gradient'])
        check('  AFTER it sits on none', now is not None and not now['gradient'])
        check('  BEFORE its ink was white',
              was is not None and rgb(was['ink']) == (255, 255, 255),
              str(was and was['ink']))
        check('  AFTER it is dark on paper',
              now is not None and sum(rgb(now['ink'])) < 330,
              str(now and now['ink']))
        check('  and it is centred in its container',
              now is not None and now['centred'])
        check('  CONTROL: it was NOT centred before',
              was is not None and not was['centred'])

# ===========================================================================
head('4. the modal headers are the NEXT round - untouched')
# ===========================================================================
_kept = 0
for rel in PAGES:
    hue = hue_of(rel)

    def modal_bands(src):
        return len([1 for m in re.finditer(
            r'(?m)^[ \t]*([^{}\n@][^{\n]*)\{([^{}]*)\}',
            css_of(nocomment(src)))
            if 'modal' in m.group(1).lower() and BAND[hue] in m.group(2)])

    a, b = modal_bands(WAS[rel]), modal_bands(NOW[rel])
    if a:
        _kept += 1
        check('%-38s its modal header kept its gradient' % rel, a == b,
              '%d -> %d' % (a, b))
check('CONTROL: some page actually had a modal to keep - otherwise the '
      'section above is vacuous', _kept >= 2, '%d page(s)' % _kept)

# ===========================================================================
head('5. the chip that only existed on a coloured ground')
# ===========================================================================
PILLED = [r for r in PAGES if 'editing-pill' in markup_of(NOW[r])]
check('the pages carrying an .editing-pill are still there', len(PILLED) >= 4,
      '%d: %s' % (len(PILLED), ', '.join(p.split('.')[0] for p in PILLED[:3])))


def lum(c):
    r, g, b = [x / 255.0 for x in rgb(c)]
    def f(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    x, y = sorted((lum(a), lum(b)))
    return (y + 0.05) / (x + 0.05)


if sync_playwright is not None and FIX:
    for rel in PILLED:
        now, was = paint(rel, True), paint(rel, False)
        check('%-38s the chip has an opaque ground now' % rel,
              now and now['pill'] and 'rgba' not in now['pill']['bg'],
              str(now and now['pill'] and now['pill']['bg']))
        check('  CONTROL: it was a translucent white',
              was and was['pill'] and 'rgba' in was['pill']['bg'],
              str(was and was['pill'] and was['pill']['bg']))
        if now and now['pill']:
            check('  and its text is legible on it',
                  contrast(now['pill']['ink'], now['pill']['bg']) >= 4.5,
                  '%.1f:1' % contrast(now['pill']['ink'], now['pill']['bg']))
            check('  and it is centred under the heading it belongs to',
                  abs(now['pill']['cx'] - now['wrapCx']) < 8,
                  '%d vs %d' % (now['pill']['cx'], now['wrapCx']))

if _BR is not None:
    _BR.close()
    _PW.stop()

# ===========================================================================
head('6. what the round left alone')
# ===========================================================================
for rel in PAGES:
    css = css_of(nocomment(NOW[rel]))
    was = css_of(nocomment(WAS[rel]))
    # Row buttons keep their green and red - they are not the heading.
    for sel in ('.btn-row-edit', '.property-header td'):
        if re.search(r'(?m)^[ \t]*' + re.escape(sel), was):
            check('%-38s keeps %s' % (rel, sel),
                  re.search(r'(?m)^[ \t]*' + re.escape(sel), css) is not None)
    stack, fault = [], None
    OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
            'with': 'endwith'}
    CLOSE = {v: k for k, v in OPEN.items()}
    for m in re.finditer(r'\{%\s*(\w+)', NOW[rel]):
        t = m.group(1)
        if t in OPEN:
            stack.append(t)
        elif t in CLOSE and (not stack or OPEN[stack.pop()] != t):
            fault = t
            break
    check('%-38s every Django tag balances' % rel,
          fault is None and not stack, fault or ','.join(stack))
    mk = markup_of(nocomment(NOW[rel]))
    check('  and every <div> is closed',
          len(re.findall(r'<div\b', mk)) == len(re.findall(r'</div>', mk)),
          '%d/%d' % (len(re.findall(r'<div\b', mk)),
                     len(re.findall(r'</div>', mk))))
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', NOW[rel], re.S):
        check('  and the stylesheet balances',
              blk.count('{') == blk.count('}'))

# THE COLOURED BANNERS THIS ROUND DID NOT REACH, as a report with a floor.
_left = []
for _d, _s, _fs in os.walk(T):
    for _f in _fs:
        if not _f.endswith('.html'):
            continue
        _rel = os.path.relpath(os.path.join(_d, _f), T).replace(os.sep, '/')
        if _rel in PAGES or _rel == 'base.html':
            continue
        _c = css_of(nocomment(read(os.path.join(_d, _f))))
        for _m in re.finditer(r'(?m)^[ \t]*([^{}\n@][^{\n]*)\{([^{}]*)\}', _c):
            if re.search(r'page-header|settings-header|celebration-header'
                         r'|calendar-header|hm-header|nm-header',
                         _m.group(1)) and 'linear-gradient' in _m.group(2):
                _left.append(_rel)
                break
print('        %d template(s) still carry a coloured page banner - the purple '
      'nine\n        in Administration, and the Personal ones. Their modules '
      'inherit this.' % len(_left))
check('and the number is a floor, not a silence', len(_left) >= 8,
      ', '.join(sorted(set(_left))[:5]))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that these pages still save, edit or list')
print('  anything. The render is base plus each page\'s own <style> around')
print('  its heading block - not the Django page.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
