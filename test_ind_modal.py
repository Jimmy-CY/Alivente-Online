"""test_ind_modal.py - the indicator drill-down modal, in both files at once.

    python test_ind_modal.py

Run from the repo root, after apply_ind_modal.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 1 asserts THE POINT OF THE ROUND: the modal markup in
    financial_indicators.html and vacancy_management.html is now byte-identical.
    Two files carried the same modal and had already drifted - one converted
    the table to cards in CSS, the other built a second DOM in JavaScript. The
    comparison carries its own control, because a comparison that cannot tell
    two strings apart passes for ever.
  * SECTION 2 reads the JavaScript with a regex over the BANDS, not over the
    markup: every value performanceClass can be assigned must have an entry in
    PERF_PILL. That is the check that would catch a fourth band being added
    with no colour - the same shape as the BAND_PILL check on the tenants view.
  * SECTION 3 RENDERS the modal at 1200px and 390px. The round's decision is
    that a verdict is a PILL and nothing else, so the browser is asked whether
    every row has the same background; a control row with an inline wash proves
    the probe can see one. The phone view is checked for the thing that is easy
    to get wrong: base promotes the FIRST cell to the card title, and here the
    first cell is the rank, which is hidden - so the NAME has to be the title.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
FI = os.path.join(T, 'finance', 'financial_indicators.html')
VM = os.path.join(T, 'finance', 'vacancy_management.html')
BASE = os.path.join(T, 'base.html')

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
    text = re.sub(r'\{#[^\n]*?#\}', '', text)      # NOT re.S - Django's {# #}

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


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


def modal_markup(raw):
    c = nocomment_html(raw)
    i = c.find('<div class="ind-drill">')
    j = c.find('</div>', c.find('id="poorCount"'))
    return ' '.join(c[i:j].split())


for p in (FI, VM, BASE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)

F, V, BS = read(FI), read(VM), read(BASE)
if '.ind-drill {' not in F:
    print('\n! not patched - run apply_ind_modal.py first.')
    sys.exit(1)

FC, VC, BC = nocomment_html(F), nocomment_html(V), nocomment_html(BS)
FR, VR, B = rules(F), rules(V), rules(BS)
FILES = (('financial_indicators', F, FC, FR), ('vacancy_management', V, VC, VR))

# ===========================================================================
head('1. one modal, and now literally one markup')
# ===========================================================================
check('CONTROL: the round\'s prose names performance-badge',
      'performance-badge' in F)
check('CONTROL: .. and it is gone once stripped',
      'performance-badge' not in FC)

check('THE TWO MODALS ARE NOW THE SAME MARKUP',
      modal_markup(F) == modal_markup(V),
      '%d vs %d chars' % (len(modal_markup(F)), len(modal_markup(V))))
check('  CONTROL: the comparison can tell two apart',
      modal_markup(F) != modal_markup(F.replace('cell-rank', 'cell-rankX')))
check('  and it is not comparing two empty strings',
      len(modal_markup(F)) > 400, '%d' % len(modal_markup(F)))

for name, raw, c, R in FILES:
    for _dead in ('performance-excellent', 'performance-good',
                  'performance-poor', 'performance-badge', 'legend-color',
                  'legend-item', 'modal-legend', 'summary-stat',
                  'modal-summary', 'stat-value', 'stat-label'):
        # Word boundaries: the replacements are alv-stat-value / alv-stat-label
        # and a bare substring test reports the class it just introduced.
        check('%s: %s is gone' % (name, _dead),
              not re.search(r'(?<![\w-])%s(?![\w-])' % _dead, c))
    check('%s: the table is .alv-table' % name,
          'class="table alv-table" id="modalPropertyTable"' in c)
    check('%s: in a wrapper of its own, not .table-container' % name,
          '<div class="ind-drill">' in c
          and c.find('ind-drill') < c.find('id="modalPropertyTable"'))
    _d = ' '.join(R.get('.ind-drill', []))
    check('%s: the wrapper scrolls' % name, 'overflow: auto' in _d, _d)
    check('%s: the tiles are the component' % name,
          'class="alv-stats ind-stats"' in c)
    check('%s: three-up' % name,
          '--alv-stats-cols: 3' in ' '.join(R.get('.ind-stats', [])))
    for _v, _id in (('good', 'excellentCount'), ('attn', 'goodCount'),
                    ('bad', 'poorCount')):
        check('%s: the %s tile keeps id #%s the JS fills' % (name, _v, _id),
              'alv-stat alv-stat-%s' % _v in c and 'id="%s"' % _id in c)

# vacancy only: the second DOM, root and branch
for _dead in ('modalPropertyCards', 'modal-mobile-cards', 'modal-desktop-table',
              'modal-property-card', 'mpc-header', 'mpc-name', 'mpc-rank',
              'mpc-row', 'mpc-label', 'mpc-value', 'mpc-badge-row',
              'cardsContainer'):
    check('vacancy: the hand-built card\'s %s is gone' % _dead, _dead not in VC)

# SUPERSEDED 1 Sep: the next round landed. These four asserted that the detail
# table, its rotate-to-landscape prompt and the group D name collision were
# still ahead - a scope guard, and one that has to invert the moment the work
# it was guarding is done. The screen it names is still there; what carried it
# is not.
check('vacancy: the detail table is still on the page',
      'Detailed Property Data' in V)
for _gone in ('rotate-prompt', 'rotate-on-portrait', 'data-table'):
    check('vacancy: %s went with the detail-table round' % _gone,
          _gone not in VC)
check('vacancy: group D is closed - the page no longer redefines the name',
      '.table-container { overflow-x: auto; }' not in V)

# ===========================================================================
head('2. every band the code can produce has a pill')
# ===========================================================================
for name, raw, c, R in FILES:
    _js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', c, re.S))
    _bands = set(re.findall(r"performanceClass\s*=\s*'(\w+)'", _js))
    _map = dict(re.findall(r"(\w+):\s*'(alv-pill-\w+)'", _js))
    check('%s: PERF_PILL is declared once and used once' % name,
          _js.count('PERF_PILL') == 2, '%d' % _js.count('PERF_PILL'))
    check('%s: EVERY band it can assign has a pill' % name,
          bool(_bands) and not (_bands - set(_map)),
          'bands %s / mapped %s' % (sorted(_bands), sorted(_map)))
    check('  three of them' , len(_map) == 3, '%s' % sorted(_map))
    check('  and every pill is one base defines',
          all(('.%s' % p) in BC for p in _map.values()),
          '%s' % sorted(set(_map.values())))
    # The value column stops carrying an inline colour. SCOPED to that cell -
    # indicator.color still paints the indicator cards and the single
    # Portfolio Average figure, and neither is the fault.
    check('%s: the value column takes no inline colour' % name,
          'cell-perf-value num" data-label="Performance"><strong style='
          not in c)
    # Deliberately not re-measuring the literal-colour drop here: it can only
    # be measured against the PRE-patch file, which this suite does not have.
    # The patcher asserts it, where the before-text exists. A check written
    # here would have to compare the file with itself.

# ===========================================================================
head('3. rendered, at 1200px and 390px')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

BOOT = None
for _cand in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
              '/tmp/bootstrap.min.css'):
    if os.path.exists(_cand):
        BOOT = open(_cand, encoding='utf-8').read()
        break
if BOOT is None:
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
    sync_playwright = None

if sync_playwright is not None:
    _bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S))
    _pcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', F, re.S))

    def row(i, name, val, diff, level, pill, extra=''):
        return ("""<tr%s>
  <td class="cell-rank">%d</td>
  <td class="cell-prop-name" data-label="Property">%s</td>
  <td class="cell-perf-value num" data-label="Performance"><strong>%s</strong></td>
  <td class="cell-vs-avg num" data-label="vs Portfolio Avg">%s</td>
  <td class="cell-perf-level" data-label="Level"><span class="alv-pill %s">%s</span></td>
</tr>""" % (extra, i, name, val, diff, pill, level))

    ROWS = '\n'.join([
        row(1, 'Dikaiosynis 12', '100.0%', 'Perfect', 'Excellent',
            'alv-pill-good'),
        row(2, 'Kifissias 44', '97.4%', '+2.1%', 'Good', 'alv-pill-attn'),
        row(3, 'Ermou 3', '81.0%', '-14.9%', 'Needs Improvement',
            'alv-pill-bad'),
        row(4, 'Solonos 21', '78.2%', '-17.8%', 'Needs Improvement',
            'alv-pill-bad', ' id="washed" style="background: rgb(255,0,0)"'),
    ] + [row(i, 'Filler %d' % i, '90.0%', '-1.0%', 'Good', 'alv-pill-attn')
         for i in range(5, 35)])

    FIX = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width">
<style>%s</style><style>%s</style><style>%s</style>
<style>body{margin:0}#propertyDetailsModal{display:block;width:900px;max-width:100%%}</style>
<div id="propertyDetailsModal"><div class="modal-body">
  <div class="ind-drill" id="drill">
    <table class="table alv-table" id="modalPropertyTable">
      <thead><tr>
        <th class="cell-rank">#</th>
        <th class="cell-prop-name">Property Name</th>
        <th class="cell-perf-value num">Performance</th>
        <th class="cell-vs-avg num">vs Portfolio Avg</th>
        <th class="cell-perf-level">Performance Level</th>
      </tr></thead>
      <tbody id="modalPropertyTableBody">%s</tbody>
    </table>
  </div>
  <div class="alv-stats ind-stats">
    <div class="alv-stat alv-stat-good"><div class="alv-stat-value" id="excellentCount">1</div><div class="alv-stat-label">Excellent</div></div>
    <div class="alv-stat alv-stat-attn"><div class="alv-stat-value" id="goodCount">31</div><div class="alv-stat-label">Good</div></div>
    <div class="alv-stat alv-stat-bad"><div class="alv-stat-value" id="poorCount">2</div><div class="alv-stat-label">Needs Improvement</div></div>
  </div>
</div></div>
<span id="tokgood" style="color: var(--alv-good)"></span>
<span id="tokattn" style="color: var(--alv-warn)"></span>
<span id="tokbad"  style="color: var(--alv-bad)"></span>
""" % (BOOT, _bcss, _pcss, ROWS)

    _f = os.path.join(tempfile.gettempdir(), 'ind_modal_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const q = s => document.querySelector(s);
      const cs = s => getComputedStyle(q(s));
      const rows = [...document.querySelectorAll('#modalPropertyTableBody tr')];
      const top = s => Math.round(q(s).getBoundingClientRect().top);
      return {
        rowBgs: [...new Set(rows.slice(0,3).map(r => getComputedStyle(r).backgroundColor))],
        washedBg: getComputedStyle(q('#washed')).backgroundColor,
        pillGood: cs('.alv-pill-good').backgroundColor,
        pillAttn: cs('.alv-pill-attn').backgroundColor,
        pillBad:  cs('.alv-pill-bad').backgroundColor,
        rankDisplay: cs('#modalPropertyTableBody td.cell-rank').display,
        nameDisplay: cs('#modalPropertyTableBody td.cell-prop-name').display,
        nameBefore: getComputedStyle(q('#modalPropertyTableBody td.cell-prop-name'), '::before').content,
        nameSize: cs('#modalPropertyTableBody td.cell-prop-name').fontSize,
        valueBefore: getComputedStyle(q('#modalPropertyTableBody td.cell-perf-value'), '::before').content,
        valueAlign: cs('#modalPropertyTableBody td.cell-perf-value').textAlign,
        theadDisplay: cs('#modalPropertyTable thead').display,
        cellTops: [...q('#modalPropertyTableBody tr').children].map(
          e => Math.round(e.getBoundingClientRect().top)),
        statCols: cs('.ind-stats').gridTemplateColumns.split(' ').length,
        statGood: cs('.alv-stat-good .alv-stat-value').color,
        statBad:  cs('.alv-stat-bad .alv-stat-value').color,
        statBgGood: cs('.alv-stat-good').backgroundColor,
        statBgPlain: cs('.alv-stat').backgroundColor,
        tokGood: cs('#tokgood').color,
        tokAttn: cs('#tokattn').color,
        tokBad:  cs('#tokbad').color,
        drillScrolls: q('#drill').scrollHeight > q('#drill').clientHeight + 4,
        thTop: top('#modalPropertyTable thead th'),
        firstRowTop: top('#modalPropertyTableBody tr'),
        wide: document.documentElement.scrollWidth
                > document.documentElement.clientWidth,
      };
    }"""

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1200, 'height': 800})
        pg.goto('file://' + _f)
        D = pg.evaluate(PROBE)
        pg.evaluate("() => { document.querySelector('#drill').scrollTop = 300; }")
        D2 = pg.evaluate(PROBE)
        pg.set_viewport_size({'width': 390, 'height': 800})
        M = pg.evaluate(PROBE)
        b.close()

    # THE DECISION. A verdict is a pill and nothing else.
    check('CONTROL: the probe can see a row wash when there is one',
          D['washedBg'] == 'rgb(255, 0, 0)', D['washedBg'])
    check('THREE VERDICTS, ONE ROW BACKGROUND',
          len(D['rowBgs']) == 1, str(D['rowBgs']))
    check('  and the pills carry the colour instead',
          len({D['pillGood'], D['pillAttn'], D['pillBad']}) == 3,
          '%s' % [D['pillGood'], D['pillAttn'], D['pillBad']])

    check('the tiles are three-up', D['statCols'] == 3, str(D['statCols']))
    check('  their figures ARE the house tokens',
          D['statGood'] == D['tokGood'] and D['statBad'] == D['tokBad'],
          '%s / %s' % (D['statGood'], D['statBad']))
    check('  and a verdict tile is not washed either',
          D['statBgGood'] == D['statBgPlain'],
          '%s vs %s' % (D['statBgGood'], D['statBgPlain']))

    check('DESKTOP: the rank column is shown', D['rankDisplay'] != 'none',
          D['rankDisplay'])
    check('  five cells on one line', len(set(D['cellTops'])) == 1,
          str(D['cellTops']))
    check('  the numeric columns are right-aligned',
          D['valueAlign'] == 'right', D['valueAlign'])
    check('  the wrapper scrolls', D['drillScrolls'])
    _moved = D['firstRowTop'] - D2['firstRowTop']
    check('  SCROLLED: rows moved, heading did not',
          _moved > 100 and abs(D2['thTop'] - D['thTop']) <= 4,
          '%dpx / %d -> %d' % (_moved, D['thTop'], D2['thTop']))

    check('MOBILE: the head is hidden', M['theadDisplay'] == 'none',
          M['theadDisplay'])
    check('  the rank is hidden with it', M['rankDisplay'] == 'none',
          M['rankDisplay'])
    # base makes the FIRST cell the card title, and the first cell is the
    # hidden rank - so the name must have been promoted deliberately.
    check('  THE NAME IS THE CARD TITLE, not a labelled row',
          M['nameDisplay'] == 'block' and M['nameBefore'] in ('none', 'normal'),
          '%s / %s' % (M['nameDisplay'], M['nameBefore']))
    check('  and it is bigger than the rows under it',
          float(M['nameSize'][:-2]) >= 15, M['nameSize'])
    check('  the other cells keep their labels',
          'Performance' in M['valueBefore'], M['valueBefore'])
    check('  and nothing pushes the page sideways', not M['wide'])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
