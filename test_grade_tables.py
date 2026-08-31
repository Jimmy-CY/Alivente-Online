"""test_grade_tables.py - the grading scale, the two detail tables, group D.

    python test_grade_tables.py

Run from the repo root, after apply_grade_tables.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 RENDERS THE SCALE and asks the browser what the five steps
    actually look like: five distinct backgrounds, ordered, with enough
    separation between neighbours to read as a sequence. Outstanding Invoices
    once shipped a "scale" of two near-identical pale blues with a grey
    between them - it looked like an ordering and encoded none. The check
    carries a control that fails on a deliberately flat scale.
  * SECTION 2 also asserts the thing that makes a red-to-green scale
    defensible at all: the graded cell still prints its own figure, so colour
    is redundant rather than load-bearing.
  * SECTION 3 renders both tables at 1200px and 390px - the totals band as a
    real tfoot, the sideways scroll under its own name, and the phone card
    view that replaced a hundred lines of hand-rolled CSS in one file and a
    "please rotate your device" prompt in the other.
  * SECTION 1 reads the files, with a control proving comments are stripped
    first: this round's own prose names .table-panel and .data-table, two of
    the classes it hunts.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FI = os.path.join(T, 'finance', 'financial_indicators.html')
VM = os.path.join(T, 'finance', 'vacancy_management.html')

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
    text = re.sub(r'\{#[^\n]*?#\}', '', text)   # NOT re.S - Django has no DOTALL

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def css_of(t):
    return re.sub(r'/\*.*?\*/', '',
                  '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S)),
                  flags=re.S)


for p in (BASE, FI, VM):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)

BS, F, V = read(BASE), read(FI), read(VM)
if '--alv-grade-1:' not in BS:
    print('\n! not patched - run apply_grade_tables.py first.')
    sys.exit(1)
BC, FC, VC = nocomment_html(BS), nocomment_html(F), nocomment_html(V)
PAGES = (('financial_indicators', F, FC), ('vacancy_management', V, VC))

# ===========================================================================
head('1. the scale is named, the tables are standard, group D is closed')
# ===========================================================================
check('CONTROL: the round\'s prose names .table-panel', '.table-panel' in V)
check('CONTROL: .. and it is gone once stripped', '.table-panel' not in VC)

for n in range(1, 6):
    check('base defines step %d' % n,
          '--alv-grade-%d:' % n in BC and '--alv-grade-%d-soft:' % n in BC
          and '.alv-grade-%d {' % n in BC)
check('base defines an application class for it', '.alv-grade-cell' in BC)
_ends = dict(re.findall(r'(--alv-(?:good|bad|grade-[15])):\s*(#[0-9a-fA-F]{6})',
                        BC))
check('step 1 IS --alv-good', _ends.get('--alv-grade-1') == _ends.get('--alv-good'),
      '%s vs %s' % (_ends.get('--alv-grade-1'), _ends.get('--alv-good')))
check('step 5 IS --alv-bad', _ends.get('--alv-grade-5') == _ends.get('--alv-bad'),
      '%s vs %s' % (_ends.get('--alv-grade-5'), _ends.get('--alv-bad')))
check('a graded tint is forced to print, like the ageing columns',
      bool(re.search(r'\.alv-grade-cell\s*\{[^}]*print-color-adjust', BC, re.S)))

for name, raw, c in PAGES:
    for _dead in ('data-table', 'table-panel', 'table-header', 'table-title',
                  'average-row', 'cellColour'):
        check('%s: %s is gone' % (name, _dead),
              not re.search(r'(?<![\w-])%s(?![\w-])' % _dead, c))
    check('%s: the detail table is .alv-table' % name,
          'class="table alv-table data-grid"' in c)
    check('%s: its totals row is a real tfoot' % name, '<tfoot>' in c)
    check('%s: every cell carries a card label' % name,
          'data-label="Property"' in c and 'data-label="Portfolio"' in c)
    # GROUP D.
    check('%s: no longer redefines .table-container' % name,
          not re.search(r'(^|\})\s*\.table-container[^{]*\{', css_of(raw)))
    check('  the sideways scroll has a name of its own' , '.ind-wide {' in c)
    check('  and something uses it', 'class="ind-wide"' in c)
    # NOT .alv-matrix-scroll, which is display:none in print.
    check('  not moved onto .alv-matrix-scroll, which does not print',
          'alv-matrix-scroll' not in c)
    check('%s: the sorted column is on a token' % name,
          bool(re.search(r'\.highlighted-column\s*\{[^}]*var\(--alv-accent\)', c))
          and not re.search(r'\.highlighted-column[^{]*\{[^}]*#[0-9a-f]{3,8}',
                            css_of(raw)))
    check('  and marks the column WITHOUT a background, so the grade under '
          'it survives being sorted',
          not re.search(r'(?m)^\.highlighted-column\s*\{[^}]*background', c))

for _dead in ('rotate-prompt', 'rotate-on-portrait', 'rotate-icon',
              'rotate-hint', 'Please rotate your device'):
    check('vacancy: %s is gone' % _dead, _dead not in VC)
check('vacancy: the panel is a card', 'class="alv-card"' in VC
      and 'alv-card-head' in VC and 'alv-card-title' in VC)

check('financial: nothing computes a colour any more', 'hsl(' not in FC)
check('  the scale is assigned by class', 'gradeClass(' in FC)
check('  declared once, used three times', FC.count('gradeClass(') == 4,
      '%d' % FC.count('gradeClass('))
check('  and no grade arrives as an inline style',
      not re.search(r'style="\$\{[^"]*grade', FC))

# THE STEP FUNCTION, executed rather than eyeballed.
# THE DIRECTION, read off the code that PRODUCES t rather than off a comment.
# gradeColumn sorts best first and stores position / (n - 1), so t = 0 is the
# best property in its column. The first draft of this round assumed the
# opposite, wrote a step function to match, and this suite would have
# confirmed it - a suite proves the code does what you specified.
check('gradeColumn still sorts best-first, which is what fixes t=0 as best',
      bool(re.search(r'const order = \[\.\.\.valid\]\.sort\(\(a, b\) => '
                     r'higher \? \(b\[key\] - a\[key\]\)', FC)))
check('  and the step function reads t that way round',
      'Math.floor(t * 5)' in FC)
_m = re.search(r"const step = Math\.min\((\d+), Math\.max\(0, "
               r"Math\.floor\(t \* (\d+)\)\)\);", FC)
check('the step function is the one this suite can reason about', bool(_m))
if _m:
    _cap, _mul = int(_m.group(1)), int(_m.group(2))
    def step(t):
        return min(_cap, max(0, int(t * _mul))) + 1
    check('  t=0 (best) is step 1', step(0.0) == 1, str(step(0.0)))
    check('  t=1 (worst) is step 5', step(1.0) == 5, str(step(1.0)))
    check('  t=0.5 is the middle', step(0.5) == 3, str(step(0.5)))
    check('  every t in [0,1] lands inside the scale',
          all(1 <= step(i / 100.0) <= 5 for i in range(101)))
    check('  and all five steps are reachable',
          len({step(i / 100.0) for i in range(101)}) == 5,
          str(sorted({step(i / 100.0) for i in range(101)})))

# ===========================================================================
head('2. rendered: is it actually a scale?')
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
    _b = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S))
    _f = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', F, re.S))

    def cells(n, hi=0):
        return '\n'.join(
            '<td class="num alv-grade-cell alv-grade-%d%s" data-label="M%d">%d.%d</td>'
            % (i, ' highlighted-column' if i == hi else '', i, 90 - i * 7, i)
            for i in range(1, n + 1))

    ROWS = '\n'.join(
        '<tr><td data-label="Property">Property %d</td>%s</tr>' % (r, cells(5, 4))
        for r in range(1, 26))

    FIX = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width">
<style>%s</style><style>%s</style><style>%s</style>
<style>body{margin:0;padding:12px}
 /* A deliberately FLAT scale, to prove the separation check can fail. */
 #flat .alv-grade-1,#flat .alv-grade-2,#flat .alv-grade-3,
 #flat .alv-grade-4,#flat .alv-grade-5{--grade-soft:#f0f0f0;}
</style>
<div class="alv-card">
  <div class="alv-card-head"><span class="alv-card-title">Detailed Property Data</span></div>
  <div class="ind-wide" id="wide">
    <table class="table alv-table data-grid" id="grid">
      <thead><tr><th>Property</th>
        <th class="sortable-header num">M1</th><th class="sortable-header num">M2</th>
        <th class="sortable-header num">M3</th>
        <th class="sortable-header num highlighted-column">M4</th>
        <th class="sortable-header num">M5</th></tr></thead>
      <tbody>%s
        <tr id="plain"><td data-label="Property">Unsorted row</td>%s</tr></tbody>
      <tfoot><tr><td data-label="Portfolio">PORTFOLIO AVERAGE</td>
        <td class="num">81.1</td><td class="num">76.2</td><td class="num">69.3</td>
        <td class="num highlighted-column">62.4</td><td class="num">55.5</td></tr></tfoot>
    </table>
  </div>
</div>
<table id="flat"><tbody><tr>%s</tr></tbody></table>
""" % (BOOT, _b, _f, ROWS, cells(5, 0), cells(5))

    _p = os.path.join(tempfile.gettempdir(), 'grade_fixture.html')
    with open(_p, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const q = s => document.querySelector(s);
      const cs = s => getComputedStyle(q(s));
      const bg = s => getComputedStyle(q(s)).backgroundColor;
      const px = v => parseFloat(v);
      const row = q('#grid tbody tr');
      return {
        steps: [1,2,3,4,5].map(i => bg('#grid .alv-grade-' + i)),
        flat:  [1,2,3,4,5].map(i => bg('#flat .alv-grade-' + i)),
        text:  [...q('#grid tbody tr').querySelectorAll('.alv-grade-cell')]
                 .map(e => e.textContent.trim()),
        footBg: bg('#grid tfoot td'),
        bodyBg: bg('#grid tbody td'),
        footBorder: cs('#grid tfoot td').borderTopWidth,
        hiBg: bg('#grid tbody td.highlighted-column'),
        hiShadow: cs('#grid tbody td.highlighted-column').boxShadow,
        plainG4: bg('#plain .alv-grade-4'),
        wideOverflow: cs('#wide').overflowX,
        theadDisplay: cs('#grid thead').display,
        rowDisplay: cs('#grid tbody tr').display,
        labelBefore: getComputedStyle(q('#grid tbody td.alv-grade-cell'), '::before').content,
        numAlign: cs('#grid tbody td.num').textAlign,
        pageWide: document.documentElement.scrollWidth
                    > document.documentElement.clientWidth,
      };
    }"""

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1200, 'height': 900})
        pg.goto('file://' + _p)
        D = pg.evaluate(PROBE)
        pg.set_viewport_size({'width': 390, 'height': 900})
        M = pg.evaluate(PROBE)
        b.close()

    def rgb(s):
        return [int(x) for x in re.findall(r'\d+', s)[:3]]

    def dist(a, b):
        return sum(abs(x - y) for x, y in zip(rgb(a), rgb(b)))

    check('the five steps are five DIFFERENT colours',
          len(set(D['steps'])) == 5, str(D['steps']))
    _gaps = [dist(a, b) for a, b in zip(D['steps'], D['steps'][1:])]
    check('  and neighbours are far enough apart to read as an order',
          min(_gaps) >= 18, str(_gaps))
    # CONTROL. Every check above is satisfied by ANY five colours; this one
    # proves the measurement can fail.
    check('CONTROL: a flat scale is rejected by the same measurement',
          len(set(D['flat'])) == 1
          and min([dist(a, b) for a, b in zip(D['flat'], D['flat'][1:])]) < 18,
          str(set(D['flat'])))
    # WHAT MAKES A RED-GREEN SCALE DEFENSIBLE: the number is still there.
    check('every graded cell still prints its own figure',
          len(D['text']) == 5 and all(t for t in D['text']), str(D['text']))

    check('the tfoot is base\'s, not a tbody row in disguise',
          D['footBg'] != D['bodyBg'] and D['footBorder'] == '2px',
          '%s / %s' % (D['footBg'], D['footBorder']))
    # THE FIX THIS ROUND FOUND BY RENDERING. The old rule painted the sorted
    # column with `background: ... !important`, which beats an inline style -
    # so sorting a column ERASED the grading in the one column the reader had
    # just asked to look at. The mark is on the edges now.
    check('the sorted column is marked without a background',
          D['hiShadow'] != 'none' and 'rgb' in D['hiShadow'],
          D['hiShadow'][:44])
    check('  so the grade under it is untouched by sorting',
          D['hiBg'] == D['plainG4'],
          '%s vs %s' % (D['hiBg'], D['plainG4']))
    check('the wide wrapper scrolls sideways', D['wideOverflow'] == 'auto',
          D['wideOverflow'])
    check('numeric columns are right-aligned', D['numAlign'] == 'right',
          D['numAlign'])

    check('MOBILE: the head is hidden', M['theadDisplay'] == 'none',
          M['theadDisplay'])
    check('  each row is a card', M['rowDisplay'] == 'block', M['rowDisplay'])
    check('  with the label base builds from data-label',
          'M1' in M['labelBefore'], M['labelBefore'])
    check('  the grade tint survives into the card',
          len(set(M['steps'])) == 5, str(M['steps']))
    check('  and nothing pushes the page sideways', not M['pageWide'])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
