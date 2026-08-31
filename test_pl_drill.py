"""test_pl_drill.py - the P&L drill-down modals on the table standard.

    python test_pl_drill.py

Run from the repo root, after apply_pl_drill.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 SCROLLS THE WRAPPER IN A REAL BROWSER. The round's headline claim
    is that .pl-drill scrolls, and that because it scrolls base's sticky
    .alv-table heading finally has something to stick TO. Both halves are
    asserted by scrolling the element and reading where things ended up - and
    the check demands that the ROWS moved while the HEADING did not, because
    "the heading is at the top" is true for free if the scroll never happened.
    A CONTROL renders the same table inside .table-container, which is
    `overflow: clip` by design, and requires that it does NOT scroll.
  * SECTION 2 reads the two fragments. They were copies of each other and must
    stay copies: a shape comparison with the loop variable and the empty-state
    sentence removed. If a later round fixes one and not the other, this fails.
  * SECTION 1 reads the page: one wrapper name, three users of it, no Bootstrap
    .table-responsive left in the drill-downs, and the P&L's own grid untouched.
    A control proves comments are stripped before any of it - the fragments'
    new prose names table-responsive and container-fluid, two of the classes
    these checks hunt for.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(T, 'finance_pl_act.html')
REV = os.path.join(T, 'revenue_details.html')
BUD = os.path.join(T, 'budget_expense_details.html')
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
    # NOT re.S: Django's {# #} does not span lines. This round proved why -
    # its first draft wrote a five-line {# #} that Django would have printed
    # above the table, and the patcher's own balance check caught it.
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


def skeleton(frag):
    s = re.sub(r'<!--.*?-->', '', frag, flags=re.S)
    s = re.sub(r'\{[{%].*?[%}]\}', '{}', s, flags=re.S)
    s = re.sub(r'>[^<]*<', '><', s)
    return ' '.join(s.split())


for p in (PAGE, REV, BUD, BASE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)

PG, RV, BD, BS = read(PAGE), read(REV), read(BUD), read(BASE)
if '.pl-drill {' not in PG:
    print('\n! not patched - run apply_pl_drill.py first.')
    sys.exit(1)

PC, RC, BDC = nocomment_html(PG), nocomment_html(RV), nocomment_html(BD)
P, B = rules(PG), rules(BS)

# ===========================================================================
head('1. the page: one wrapper, three users, no Bootstrap left')
# ===========================================================================
check('CONTROL: the fragment prose names table-responsive',
      'table-responsive' in RV)
check('CONTROL: .. and it is gone once stripped',
      'table-responsive' not in RC)

check('.pl-drill is defined once', PC.count('.pl-drill {') == 1)
check('  and the three drill-downs all use it',
      PC.count('class="pl-drill"') == 3, '%d' % PC.count('class="pl-drill"'))
_d = ' '.join(P.get('.pl-drill', []))
check('  it scrolls rather than clips', 'overflow: auto' in _d, _d)
check('  and keeps the 60vh it always had', 'max-height: 60vh' in _d)
check('  on house tokens', 'var(--alv-paper)' in _d and 'var(--alv-radius)' in _d)

_tail = PC[PC.find('DRILL-DOWN MODALS'):]
check('no drill-down wraps in Bootstrap .table-responsive any more',
      'table-responsive' not in _tail)
# Out of scope, and it must stay that way: line 225 is the P&L's OWN grid.
check("the P&L's own grid keeps its wrapper - this round is the modals",
      'table-responsive pl-table-wrap' in PC)

check('the column widths no longer key off nth-child',
      not [s for s in P if 'DetailsModal' in s and 'nth-child' in s],
      str([s for s in P if 'DetailsModal' in s and 'nth-child' in s]))
check('  and the page no longer re-aligns what .num aligns',
      not [s for s in P
           if 'DetailsModal' in s and 'text-align' in ' '.join(P[s])])
check('base owns .num, so there is one alignment rule not four',
      any('.num' in s for s in B))

# ===========================================================================
head('2. the two fragments, which are copies and must stay copies')
# ===========================================================================
for name, f in (('revenue_details', RC), ('budget_expense_details', BDC)):
    check('%s: exactly one table' % name,
          len(re.findall(r'<table\b', f)) == 1)
    # The page scrapes with table.table first. Dropping the Bootstrap class
    # sends it down the untested fallback branch.
    check('  it keeps `table` beside `alv-table` for the scraper',
          'class="table alv-table"' in f)
    check('  the totals row is a real tfoot', '<tfoot>' in f)
    check('  the money column is .num in head, body and foot',
          f.count('class="num"') >= 3, '%d' % f.count('class="num"'))
    check('  every cell carries a data-label for the phone card view',
          f.count('data-label=') == 2, '%d' % f.count('data-label='))
    check('  the empty state is base\'s, and INSIDE the table',
          'alv-empty' in f[f.find('<table'):f.find('</table>')])
    for _dead in ('thead-light', 'table-bordered', 'table-sm', 'text-right',
                  'font-weight-bold', 'alert alert-info', 'table-responsive',
                  'container-fluid'):
        check('  %s is gone' % _dead, _dead not in f)
    check('  no inline background', not re.search(r'style="[^"]*background', f))
    check('  no literal colour', not re.search(r'#[0-9a-fA-F]{3,8}\b', f))

check('THE TWO FRAGMENTS ARE STILL THE SAME SHAPE',
      skeleton(RV) == skeleton(BD))
# And a control for THAT: the comparison must be capable of noticing.
check('  CONTROL: the comparison can tell two shapes apart',
      skeleton(RV) != skeleton(RV.replace('<tfoot>', '')))

# ===========================================================================
head('3. rendered: does the wrapper actually scroll, and does the head stick?')
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
    _pcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', PG, re.S))

    _rows = '\n'.join(
        '<tr><td data-label="Property">Property %d</td>'
        '<td class="num" data-label="Amount (&euro;)">%s</td></tr>'
        % (i, format(1000 + i * 37.5, ',.2f')) for i in range(1, 41))

    TABLE = ("""<table class="table alv-table">
<thead><tr><th>Property</th><th class="num">Amount (&euro;)</th></tr></thead>
<tbody>%s</tbody>
<tfoot><tr><td>Total</td><td class="num">61,750.00</td></tr></tfoot>
</table>""" % _rows)

    EMPTY = """<table class="table alv-table">
<thead><tr><th>Property</th><th class="num">Amount (&euro;)</th></tr></thead>
<tbody><tr><td colspan="2"><div class="alv-empty">
  <i class="fas fa-info-circle"></i>
  <div class="alv-empty-title">Nothing to show</div>
  <div class="alv-empty-hint">No revenue was recorded.</div>
</div></td></tr></tbody></table>"""

    # The modal is reproduced as the page builds it: an id-scoped dialog, the
    # wrapper the JS creates, and the scraped table inside it.
    FIX = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width">
<style>%s</style><style>%s</style><style>%s</style>
<style>body{margin:0}#revenueDetailsModal{display:block;width:600px}
 #ctlbox{width:600px}</style>
<div id="revenueDetailsModal"><div class="modal-body">
  <div class="pl-drill" id="drill">%s</div>
</div></div>
<div id="ctlbox"><div class="table-container" id="clipped">%s</div></div>
<div id="emptybox"><div class="pl-drill">%s</div></div>
""" % (BOOT, _bcss, _pcss, TABLE, TABLE, EMPTY)

    _f = os.path.join(tempfile.gettempdir(), 'pl_drill_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const q = s => document.querySelector(s);
      const top = s => Math.round(q(s).getBoundingClientRect().top);
      const d = q('#drill');
      return {
        drillOverflow: getComputedStyle(d).overflowY,
        drillScrollable: d.scrollHeight > d.clientHeight + 4,
        clippedScrollable: q('#clipped').scrollHeight
                             > q('#clipped').clientHeight + 4
                           && getComputedStyle(q('#clipped')).overflowY !== 'clip'
                           && getComputedStyle(q('#clipped')).overflowY !== 'hidden',
        clippedOverflow: getComputedStyle(q('#clipped')).overflowY,
        thPos: getComputedStyle(q('#drill thead th')).position,
        thTop: top('#drill thead th'),
        firstRowTop: top('#drill tbody tr'),
        drillTop: top('#drill'),
        headAlign: getComputedStyle(q('#drill thead th.num')).textAlign,
        cellAlign: getComputedStyle(q('#drill tbody td.num')).textAlign,
        footAlign: getComputedStyle(q('#drill tfoot td.num')).textAlign,
        footBg: getComputedStyle(q('#drill tfoot td')).backgroundColor,
        bodyBg: getComputedStyle(q('#drill tbody td')).backgroundColor,
        footBorder: getComputedStyle(q('#drill tfoot td')).borderTopWidth,
        theadDisplay: getComputedStyle(q('#drill thead')).display,
        rowDisplay: getComputedStyle(q('#drill tbody tr')).display,
        labelBefore: getComputedStyle(q('#drill tbody td.num'), '::before').content,
        emptyVisible: q('#emptybox .alv-empty').offsetHeight > 20,
        firstColWidth: Math.round(
          q('#drill tbody td').getBoundingClientRect().width),
        drillWidth: Math.round(q('#drill').getBoundingClientRect().width),
      };
    }"""

    SCROLL = """() => { document.querySelector('#drill').scrollTop = 400;
                        return null; }"""

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg_ = b.new_page(viewport={'width': 1200, 'height': 800})
        pg_.goto('file://' + _f)
        D0 = pg_.evaluate(PROBE)
        pg_.evaluate(SCROLL)
        D1 = pg_.evaluate(PROBE)
        pg_.set_viewport_size({'width': 390, 'height': 800})
        M = pg_.evaluate(PROBE)
        b.close()

    check('the wrapper is a scroll container', D0['drillOverflow'] == 'auto',
          D0['drillOverflow'])
    check('  and forty rows actually overflow it', D0['drillScrollable'])
    # CONTROL. .table-container is overflow: clip BY DESIGN. If it scrolled,
    # the distinction this round rests on would not exist.
    check('CONTROL: .table-container does NOT scroll, it clips',
          not D0['clippedScrollable'], D0['clippedOverflow'])

    # THE CLAIM. Scroll the wrapper: the rows must move and the heading must
    # not. "The heading is at the top" is true for free if nothing scrolled,
    # so both halves are required.
    _moved = D0['firstRowTop'] - D1['firstRowTop']
    check('SCROLLED: the rows moved', _moved > 100, '%dpx' % _moved)
    # It settles by the wrapper's 1px border when sticky pins it to the
    # padding box - 2px against the rows' 400px, not a failure to stick.
    check('  the heading did NOT', abs(D1['thTop'] - D0['thTop']) <= 4
          and abs(D1['thTop'] - D0['thTop']) * 20 < _moved,
          '%d -> %d' % (D0['thTop'], D1['thTop']))
    check('  because base makes it sticky', D0['thPos'] == 'sticky',
          D0['thPos'])
    check('  and it is still at the top of the wrapper',
          abs(D1['thTop'] - D1['drillTop']) <= 2,
          '%d vs %d' % (D1['thTop'], D1['drillTop']))

    check('the money column is right-aligned in the head',
          D0['headAlign'] == 'right', D0['headAlign'])
    check('  in the body', D0['cellAlign'] == 'right', D0['cellAlign'])
    check('  and in the foot', D0['footAlign'] == 'right', D0['footAlign'])
    check('the tfoot is base\'s, not a tbody row in disguise',
          D0['footBg'] != D0['bodyBg'] and D0['footBorder'] == '2px',
          '%s / %s' % (D0['footBg'], D0['footBorder']))
    # WHAT THE WIDTH RULE ACTUALLY DOES. table-layout is auto, so a width
    # percentage is advisory and short content wins - true of the old
    # :nth-child rule as well. What the rule really guarantees is the 200px
    # floor and that Property stays the wider column, so that is what is
    # asserted rather than a 70% the browser never promised.
    check('the property column holds its 200px floor',
          D0['firstColWidth'] >= 200, '%dpx' % D0['firstColWidth'])
    check('  and stays wider than the money column',
          D0['firstColWidth'] > D0['drillWidth'] - D0['firstColWidth'],
          '%d of %d' % (D0['firstColWidth'], D0['drillWidth']))
    check('the empty state renders as a panel, not a bare row',
          D0['emptyVisible'])

    check('MOBILE: the head is hidden', M['theadDisplay'] == 'none',
          M['theadDisplay'])
    check('  each row is a card', M['rowDisplay'] == 'block', M['rowDisplay'])
    check('  and the data-label supplies the missing heading',
          'Amount' in M['labelBefore'], M['labelBefore'])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
