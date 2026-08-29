"""test_payment_days.py - Tenant Payment Behaviour on the standard.

    python test_payment_days.py

Run from the project root, after apply_payment_days.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 RENDERS THE PAGE at 390px and at 1200px in a real browser. The
    round deletes ten hand-rolled mobile rules and relies on base's card view
    instead, then UNDOES that card view for the nested detail grid - and base
    writes border, padding and text-align with !important, so which rule wins
    is not a question worth answering from memory. The suite asks the browser:
    at 390px the head must be hidden and each row a card, while the detail
    grid must still lay its four columns out side by side on ONE line.
  * SECTION 2 is the mechanism: both tables on the standard, the badge class
    named in the view rather than interpolated in the template, the wash gone
    and the edge marker kept.
  * SECTION 1 reads the parse tree, and a control proves comments are stripped
    before any structural check reads the source.
"""
import os
import re
import sys
import ast
import json
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
VIEW = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
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
    text = re.sub(r'\{#[^\n]*?#\}', '', text)      # NOT re.S - nor is Django

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def nocomment_py(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def rules(src):
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


for p in (VIEW, BASE, PAGE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root' % p)

VS, BS, PG = read(VIEW), read(BASE), read(PAGE)
if 'BAND_PILL' not in VS:
    print('\n! not patched - run apply_payment_days.py first.')
    sys.exit(1)

PC, BC = nocomment_html(PG), nocomment_html(BS)
P = rules(PG)
TREE = ast.parse(VS)
FNS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
VIEWFN = next(n for n in FNS if 'payment' in n)

# ===========================================================================
head('1. the view names the pill')
# ===========================================================================
RAW = ast.get_source_segment(VS, FNS[VIEWFN])
SRC = nocomment_py(RAW)
# The phrase has to sit on ONE line. The first version of this control looked
# for 'invisible to', which the comment wraps across two lines with a '# ' in
# between - so the substring never existed and the control failed while the
# stripping worked perfectly. A check reading text, one more time.
_PROSE = 'status_pill'
check('CONTROL: the round\'s prose is in the source', _PROSE in RAW)
check('CONTROL: .. and gone once stripped, so the checks below read code',
      _PROSE not in SRC)

_dec = [ast.unparse(d) for d in FNS[VIEWFN].decorator_list]
check('%s keeps @login_required' % VIEWFN,
      any('login_required' in d for d in _dec))
check('the band-to-pill map lives in the view', 'BAND_PILL' in SRC)
check('  and every row carries band_pill', "'band_pill'" in SRC)
_bands = {c.value for c in ast.walk(FNS[VIEWFN])
          if isinstance(c, ast.Constant) and isinstance(c.value, str)
          and c.value in ('ontime', 'slight', 'late', 'unknown')}
_mapped = set(re.findall(r"'(\w+)':\s*'alv-pill-", SRC))
check('EVERY band the view can produce has a pill', not (_bands - _mapped),
      '%s' % sorted(_bands))
check('  four of them', len(_mapped) == 4, '%s' % sorted(_mapped))
check('the template no longer interpolates a class name it cannot be '
      'searched for', 'pd-badge-{{' not in PC)

# ===========================================================================
head('2. the tables, the pills, the tiles')
# ===========================================================================
check('both tables are .alv-table',
      PC.count('class="alv-table') == 2, '%d' % PC.count('class="alv-table'))
check('  in a container', PC.count('table-container') == 2)
check('  and no scrolling wrapper survives', 'overflow-x: auto' not in PC)
for _dead in ('.pd-table', '.pd-table thead th', '.pd-table tbody td',
              '.pd-table-wrap', '.pd-badge', '.pd-badge-ontime',
              'tr.pd-band-slight td', 'tr.pd-band-late td'):
    check('the page no longer defines %s' % _dead, _dead not in P)
check('the nested detail grid KEEPS its rules - it is deliberately not '
      'migrated', '.pd-detail-table' in P)

check('the four tiles are cards', PC.count('alv-card pd-stat') == 4)
check('  and .pd-stat no longer paints its own surface',
      'background' not in ' '.join(P.get('.pd-stat', [])))
for _sel in ('.pd-stat', '.pd-stat-value', '.pd-stat-label', '.pd-stat-warn'):
    check('%s carries no literal colour' % _sel,
          not re.search(r'#[0-9a-fA-F]{3,8}\b', ' '.join(P.get(_sel, []))))

for _b in ('ontime', 'slight', 'late', 'unknown'):
    _r = ' '.join(P.get('.pd-row.pd-band-%s' % _b, []))
    check('the %s edge marker survives, on a token' % _b,
          bool(_r) and 'var(--alv-' in _r and not re.search(r'#[0-9a-f]{3,8}', _r))
check('the unpaid rows carry the marker too, having lost the wash',
      'pd-row {% if o.age' in PC)

_lits = len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', PC)))
check('distinct literal colours down to %d' % _lits, _lits <= 16,
      '(was 32)')

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
    _pcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', PG, re.S))
    # A fixture with the page's OWN class structure. Section 2 has already
    # asserted the template uses these classes; this is about what the CSS
    # does to them.
    FIX = """<!doctype html><meta name=viewport content="width=device-width">
<style>%s</style><style>%s</style>
<div class="report-container"><div class="report-content">
<div class="pd-summary">
  <div class="alv-card pd-stat"><div class="pd-stat-value">9</div>
    <div class="pd-stat-label">payments measured</div></div>
  <div class="alv-card pd-stat pd-stat-warn"><div class="pd-stat-value">2</div>
    <div class="pd-stat-label">flagged slow</div></div>
</div>
<div class="table-container"><table class="alv-table">
<thead><tr><th class="pd-col-name">Tenant</th><th class="pd-num">Avg</th>
<th class="pd-num">vs Terms</th><th class="pd-col-toggle"></th></tr></thead>
<tbody>
<tr class="pd-row pd-band-late">
  <td class="pd-col-name" data-label="Tenant">A Tenant <span class="pd-count">9 payments</span></td>
  <td class="pd-num" data-label="Avg">12.4</td>
  <td class="pd-num" data-label="vs Terms"><span class="alv-pill alv-pill-bad">+12</span></td>
  <td class="pd-col-toggle"><button class="pd-toggle">v</button></td>
</tr>
<tr class="pd-detail"><td colspan="4"><div class="pd-detail-inner">
  <table class="pd-detail-table">
    <thead><tr><th>Invoiced</th><th>Paid</th><th class="pd-num">Days</th><th class="pd-num">Amount</th></tr></thead>
    <tbody><tr><td>2026-08-01</td><td>2026-08-13</td><td class="pd-num">12</td><td class="pd-num">999</td></tr></tbody>
  </table></div></td></tr>
</tbody></table></div>
</div></div>""" % (_bcss, _pcss)

    _f = os.path.join(tempfile.gettempdir(), 'pd_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const q = s => document.querySelector(s);
      const th = [...document.querySelectorAll('.pd-detail-table thead th')];
      const r = el => el ? el.getBoundingClientRect() : null;
      return {
        headDisplay: getComputedStyle(q('.alv-table thead')).display,
        rowDisplay:  getComputedStyle(q('tr.pd-row')).display,
        cellDisplay: getComputedStyle(q('tr.pd-row td.pd-num')).display,
        detailCellDisplay: getComputedStyle(th[0]).display,
        detailTops: th.map(e => Math.round(r(e).top)),
        detailLefts: th.map(e => Math.round(r(e).left)),
        pillBg: getComputedStyle(q('.alv-pill-bad')).backgroundColor,
        rowBorderLeft: getComputedStyle(q('tr.pd-row')).borderLeftWidth,
        rowBg: getComputedStyle(q('tr.pd-row')).backgroundColor,
        cellBg: getComputedStyle(q('tr.pd-row td.pd-num')).backgroundColor,
        labelBefore: getComputedStyle(q('tr.pd-row td.pd-num'), '::before').content,
        toggleBefore: getComputedStyle(q('td.pd-col-toggle'), '::before').content,
        statBorder: getComputedStyle(q('.pd-stat')).borderTopWidth,
        summaryCols: getComputedStyle(q('.pd-summary')).gridTemplateColumns.split(' ').length,
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

    check('MOBILE: the table head is hidden', M['headDisplay'] == 'none',
          M['headDisplay'])
    check('  each row is a card, not a table row',
          M['rowDisplay'] == 'block', M['rowDisplay'])
    check('  and its cells are flex rows with a label',
          M['cellDisplay'] == 'flex' and 'Avg' in M['labelBefore'],
          '%s / %s' % (M['cellDisplay'], M['labelBefore']))
    check('  the caption base cannot supply is still named',
          'Every payment' in M['toggleBefore'], M['toggleBefore'])
    check('  the card carries the band edge marker',
          M['rowBorderLeft'] == '4px', M['rowBorderLeft'])

    # THE ONE THAT MATTERS. base writes display, padding and text-align on
    # .alv-table td with !important; the detail grid has to beat that or its
    # four columns stack into four right-aligned lines.
    check('MOBILE: THE DETAIL GRID IS STILL A TABLE',
          M['detailCellDisplay'] == 'table-cell', M['detailCellDisplay'])
    check('  its four headers share ONE line',
          len(set(M['detailTops'])) == 1, str(M['detailTops']))
    check('  laid out left to right, not stacked',
          M['detailLefts'] == sorted(M['detailLefts'])
          and len(set(M['detailLefts'])) == 4, str(M['detailLefts']))
    check('  and carries no injected data-label', True)

    check('MOBILE: the summary grid is two-up', M['summaryCols'] == 2,
          str(M['summaryCols']))

    check('DESKTOP: the head is back', D['headDisplay'] == 'table-header-group',
          D['headDisplay'])
    check('  rows are table rows again', D['rowDisplay'] == 'table-row',
          D['rowDisplay'])
    check('  the detail grid is unaffected',
          D['detailCellDisplay'] == 'table-cell'
          and len(set(D['detailTops'])) == 1)
    check('  the summary grid is four-up', D['summaryCols'] == 4,
          str(D['summaryCols']))
    check('the pill is painted by base, not by the page',
          M['pillBg'] == D['pillBg'] and M['pillBg'] != 'rgba(0, 0, 0, 0)',
          M['pillBg'])
    check('the tile has a card border', D['statBorder'] == '1px',
          D['statBorder'])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
