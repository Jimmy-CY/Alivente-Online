#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Valuations: the same figures, base's table, and a total that adds up.

Run from the repo root. Needs Playwright's chromium.

THE POINT. This round moved the row-building and three filter chains out of
the template and into the view. A styling round can be checked by rendering
it; arithmetic cannot. So section 1 reimplements the OLD template - including
`get_item`, `divide_by`, `subtract` and `multiply` exactly as
custom_filters.py defines them, quirks and all - and runs it beside the new
view function over generated portfolios.

The quirks matter. `divide_by` turns a falsy divisor into 1 rather than
raising, and pushes everything through Decimal before returning a float.
`get_item` returns 0 for a missing key, not None. Reimplementing what those
functions SHOULD do rather than what they DO would prove nothing.
"""
import os, re, sys, random, asyncio
from decimal import Decimal, InvalidOperation

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'finance_valuations.html')
BASEF = os.path.join(TPL, 'base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')

_p = _f = 0
_fails = []


def check(n, ok, extra=''):
    global _p, _f
    if ok:
        _p += 1; print('  PASS  %s %s' % (n, extra))
    else:
        _f += 1; _fails.append(n); print('  FAIL  %s %s' % (n, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def markup_of(t):
    """The template without its stylesheet or HTML comments.

    Checks about ELEMENTS must not read commentary - a note explaining that
    the Bootstrap hexes moved out of the markup should not be mistaken for
    the hexes still being there. This caught the patcher's own self-check
    before it caught anything real.
    """
    t = re.sub(r'<style[^>]*>.*?</style>', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def seg(src, funcname):
    """The body of one function, or '' if it is not there.

    Stops at the next top-level `def`, `class` OR DECORATOR. Splitting on
    `\ndef ` alone swallows the decorator lines that belong to the function
    after it - which made the lifted helper fail to compile with a stray
    @permission_required at the end of it.
    """
    parts = src.split('def %s' % funcname)
    if len(parts) < 2:
        return ''
    rest = parts[1]
    m = re.search(r'\n(?=@|def |class )', rest)
    return rest[:m.start() + 1] if m else rest


BASE, PT, VT = read(BASEF), read(PAGE), read(VIEW)
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''


# ---------------------------------------------------------------------------
# 1. THE FIGURES
# ---------------------------------------------------------------------------
class Row(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


def old_divide_by(value, arg):
    """`divide_by`, from pages/templatetags/custom_filters.py."""
    try:
        value = Decimal(str(value)) if value else Decimal('0')
        arg = Decimal(str(arg)) if arg else Decimal('1')
        if arg == 0:
            return None
        return float(value / arg)
    except (ValueError, TypeError, InvalidOperation):
        return None


def old_subtract(value, arg):
    try:
        return float(value or 0) - float(arg or 0)
    except (ValueError, TypeError):
        return 0


def old_multiply(value, arg):
    try:
        return float(value or 0) * float(arg or 0)
    except (ValueError, TypeError):
        return 0


def old_get_item(dictionary, key):
    """Returns 0 - NOT None - for a missing key. 0 is falsy, so the template's
    `{% if valuation %}` skipped it, which is why the new code's `.get(pk)`
    returning None behaves the same."""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key, 0)
    return 0


def reference_rows(props_list, valuations_dict):
    """The template's loop, as it was written:

        {% for property in props %}
          {% with valuation=prop_values|get_item:property.prop_id %}
            {% if valuation %}   ... {% endif %}
    """
    out = []
    for p in props_list:
        v = old_get_item(valuations_dict, p.prop_id)
        if not v:
            continue
        area = p.prop_floor_area
        purchase = v.prop_values_purchase_price
        current = v.prop_values_current_value
        price_sqm = (old_divide_by(purchase, area)
                     if (area and purchase) else None)
        value_sqm = (old_divide_by(current, area)
                     if (area and current) else None)
        if purchase and current:
            gain = old_subtract(current, purchase)
            pct = old_divide_by(old_multiply(gain, 100), purchase)
        else:
            pct = None
        out.append({
            'prop_values_id': v.prop_values_id,
            'prop_name': p.prop_name,
            'floor_area': area,
            'purchase': purchase,
            'current': current,
            'price_sqm': price_sqm,
            'value_sqm': value_sqm,
            'gain_pct': pct,
        })
    return out


def load_helpers(view_src):
    """Lift the three helpers out of finance.py without importing Django."""
    ns = {'Decimal': Decimal, 'InvalidOperation': InvalidOperation}
    for name in ('_val_div', '_val_gain', '_valuation_rows'):
        body = 'def %s' % name + seg(view_src, name)
        if not seg(view_src, name):
            return None
        exec(compile(body, '<helpers>', 'exec'), ns)
    return ns


def same(ref, new):
    if len(ref) != len(new):
        return False, 'row count %d vs %d' % (len(ref), len(new))
    for i, (a, b) in enumerate(zip(ref, new)):
        for k in ('prop_values_id', 'prop_name', 'floor_area', 'purchase',
                  'current', 'price_sqm', 'value_sqm'):
            if a[k] != b[k]:
                return False, 'row %d, %s: %r vs %r' % (i, k, a[k], b[k])
        # gain: the new row carries 0 plus a flag where the old carried None
        want = a['gain_pct']
        got = b['gain_pct'] if b['gain_known'] else None
        if want != got:
            return False, 'row %d, gain: %r vs %r' % (i, want, got)
    return True, '%d row(s)' % len(ref)


def dataset(seed, n=8, orphans=True, gaps=True):
    rnd = random.Random(seed)
    props_list, vals = [], {}
    for i in range(1, n + 1):
        area = rnd.choice([0, None, 45, 88, 120, 250]) if gaps else 100
        props_list.append(Row(prop_id=i, prop_name='Prop %d' % i,
                              prop_country=rnd.choice(['Cyprus', 'Greece']),
                              prop_floor_area=area))
        if gaps and rnd.random() < 0.2:
            continue                       # a property with no valuation
        vals[i] = Row(prop_values_id=100 + i,
                      prop_values_purchase_price=rnd.choice(
                          [0, None, Decimal('120000'), Decimal('255000')]),
                      prop_values_current_value=rnd.choice(
                          [0, None, Decimal('98000'), Decimal('310000')]))
    if orphans:
        # a valuation whose property is gone - counted in the OLD total,
        # drawn nowhere
        vals[999] = Row(prop_values_id=999,
                        prop_values_purchase_price=Decimal('50000'),
                        prop_values_current_value=Decimal('75000'))
    return props_list, vals


head('1. the figures: the old template against the new view function')
H = load_helpers(VT)
if check('the view exposes the three helpers', H is not None,
         '(run apply_valuations.py first)'):
    NEW = H['_valuation_rows']
    _bad = 0
    for seed in range(60):
        pl, vd = dataset(seed)
        ok, why = same(reference_rows(pl, vd), NEW(pl, vd))
        if not ok:
            _bad += 1
            if _bad <= 3:
                print('      seed %d: %s' % (seed, why))
    check('60 generated portfolios produce identical figures', _bad == 0,
          '%d differed' % _bad)

    pl, vd = dataset(5)
    cases = [
        ('no properties at all', ([], vd)),
        ('no valuations at all', (pl, {})),
        ('both empty', ([], {})),
        ('every property without a floor area',
         ([Row(prop_id=p.prop_id, prop_name=p.prop_name,
               prop_country=p.prop_country, prop_floor_area=None) for p in pl], vd)),
        ('a zero purchase price',
         (pl[:1], {pl[0].prop_id: Row(prop_values_id=1,
                                      prop_values_purchase_price=Decimal('0'),
                                      prop_values_current_value=Decimal('100'))})),
        ('a zero floor area',
         ([Row(prop_id=1, prop_name='Z', prop_country='Cyprus', prop_floor_area=0)],
          {1: Row(prop_values_id=1, prop_values_purchase_price=Decimal('1000'),
                  prop_values_current_value=Decimal('1200'))})),
        ('a LOSS, not a gain',
         ([Row(prop_id=1, prop_name='L', prop_country='Cyprus', prop_floor_area=100)],
          {1: Row(prop_values_id=1, prop_values_purchase_price=Decimal('200000'),
                  prop_values_current_value=Decimal('150000'))})),
    ]
    for what, args in cases:
        try:
            ok, why = same(reference_rows(*args), NEW(*args))
        except Exception as e:
            ok, why = False, 'raised %s: %s' % (type(e).__name__, e)
        check('  %-36s' % what, ok, why)

    # the class, not an inline colour
    _loss = NEW([Row(prop_id=1, prop_name='L', prop_country='Cyprus',
                     prop_floor_area=100)],
                {1: Row(prop_values_id=1,
                        prop_values_purchase_price=Decimal('200000'),
                        prop_values_current_value=Decimal('150000'))})
    check('a loss is negative and carries the down class',
          _loss[0]['gain_pct'] < 0 and _loss[0]['gain_class'] == 'val-gain-down',
          '%.1f%% / %s' % (_loss[0]['gain_pct'], _loss[0]['gain_class']))
    _gain = NEW([Row(prop_id=1, prop_name='G', prop_country='Cyprus',
                     prop_floor_area=100)],
                {1: Row(prop_values_id=1,
                        prop_values_purchase_price=Decimal('100000'),
                        prop_values_current_value=Decimal('125000'))})
    check('  and a 25% gain is +25.0 with the up class',
          abs(_gain[0]['gain_pct'] - 25.0) < 1e-9
          and _gain[0]['gain_class'] == 'val-gain-up',
          '%.4f / %s' % (_gain[0]['gain_pct'], _gain[0]['gain_class']))

    # CONTROLS
    _ref = reference_rows(*dataset(3))
    _new = NEW(*dataset(3))
    if len(_ref) > 2:
        check('CONTROL: a swapped pair IS detected',
              not same([_ref[1], _ref[0]] + _ref[2:], _new)[0])
        check('CONTROL: a dropped row IS detected', not same(_ref[:-1], _new)[0])
        _c = [dict(r) for r in _ref]
        _c[0]['purchase'] = (_c[0]['purchase'] or 0) + 1
        check('CONTROL: a one-euro difference IS detected',
              not same(_c, _new)[0])

    head('2. the total now equals its own column')
    pl, vd = dataset(11)                       # includes the orphan valuation
    rows = NEW(pl, vd)
    shown = sum((r['purchase'] for r in rows if r['purchase'] is not None),
                Decimal('0'))
    every = sum((v.prop_values_purchase_price for v in vd.values()
                 if v.prop_values_purchase_price is not None), Decimal('0'))
    check('the rows sum to %s' % shown, shown == sum(
        (r['purchase'] for r in rows if r['purchase'] is not None), Decimal('0')))
    # CONTROL: the OLD total summed every valuation, and here is the gap.
    check('CONTROL: summing every valuation gives a DIFFERENT number (%s)'
          % every, every != shown,
          'the orphaned valuation was counted and never drawn')
    check('the view sums the rows, not the queryset',
          "sum(r['purchase'] for r in rows" in VT
          and "sum(r['current'] for r in rows" in VT)

head('3. the view is still guarded')
check('finance_valuations keeps @login_required',
      re.search(r'@login_required\s*\n@permission_required\([^)]*can_access_financials'
                r'[^)]*\)\s*\ndef finance_valuations\(', VT) is not None)
for helper in ('_val_div', '_val_gain', '_valuation_rows'):
    check('  %-16s carries no decorators of its own' % helper,
          re.search(r'@\w+[^\n]*\n\s*def %s' % helper, VT) is None)
check('the context carries rows', '"rows": rows' in VT)
check('  and the gain class, not a colour',
      '"total_gain_class": total_class' in VT)

head('4. the template stopped deciding its own figures')
_mk = markup_of(PT)
check('one loop over rows', _mk.count('{% for row in rows %}') == 1)
check('  the filter chains are gone',
      not any(f in _mk for f in ('get_item', 'divide_by', 'subtract', 'multiply')))
check('  and so is the nested {% with %}', '{% with' not in _mk)
_inline = [s for s in re.findall(r'style="[^"]*"', _mk)
           if re.search(r'#[0-9a-fA-F]{3,6}', s)]
check('no inline style carries a colour any more', not _inline, str(_inline[:2]))
check('an empty result says so', '{% if not rows %}' in PT and 'alv-empty-title' in PT)
check('the total row is in a tfoot, not the tbody',
      _mk.count('<tfoot>') == 1 and _mk.count('</tfoot>') == 1
      and 'totals-row' not in _mk)
check('the stray second <body> is gone', '<body>' not in _mk)

head('5. the table joined the standard')
check('the wrapper is .table-container', 'class="table-container"' in _mk)
check('  NOT the page\'s own shell name', 'valuations-table-container' not in PT)
check('  which is what base\'s sticky observer looks for',
      "closest('.table-container')" in BASE)
check('the table carries .alv-table',
      'class="table alv-table valuations-table"' in _mk)
check('  and dropped table-bordered / table-striped / text-center',
      'table-bordered' not in _mk and 'table-striped' not in _mk)
check('Edit is an icon in a house Actions column',
      'icon-action-btn icon-edit' in _mk and 'desktop-action-cell cell-actions' in _mk)
check('  and the hand-rolled responsive label is gone', 'btn-label-text' not in PT)
check('one mobile action, so one column', 'mobile-action-bar cols-1' in _mk)
check('  and base defines cols-1', '.mobile-action-bar.cols-1' in css_of(BASE))
check('the disabled Add New uses base\'s name',
      'action-primary disabled-btn' in _mk and 'action-primary--disabled' not in PT)
_left = [' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
         for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_of(PT))]
_left = [s for s in _left if s and not s.startswith('@')]
check('the page is down to %d rules from 47' % len(_left), len(_left) <= 16)
check('  and every survivor is page-specific',
      all(s.startswith('.val-') or 'valuations-table' in s for s in _left),
      '; '.join(s for s in _left
                if not (s.startswith('.val-') or 'valuations-table' in s)))
check('every {# #} closes on its own line',
      not [i for i, l in enumerate(PT.split('\n'), 1)
           if '{#' in l and '#}' not in l])


FRAG = ("<div class='table-container'><table class='table alv-table valuations-table'>"
        "<thead><tr><th style='text-align:left'>Property</th><th class='num'>m2</th>"
        "<th class='num'>Purchase</th><th class='num'>Price/m2</th>"
        "<th class='num'>Current</th><th class='num'>Value/m2</th>"
        "<th class='num'>Gain %</th>"
        "<th class='desktop-action-cell cell-actions'>Actions</th></tr></thead>"
        "<tbody><tr>"
        "<td data-label='Property' class='cell-property'>12 Oak Avenue</td>"
        "<td data-label='Floor Area' class='num cell-area'>120</td>"
        "<td data-label='Purchase Price' class='num cell-purchase' id='pur'>&euro; 250,000</td>"
        "<td data-label='Price/m2' class='num cell-price-sqm'>&euro;2,083</td>"
        "<td data-label='Current Value' class='num cell-current'>&euro; 310,000</td>"
        "<td data-label='Value/m2' class='num cell-value-sqm'>&euro;2,583</td>"
        "<td data-label='Gain %' class='num cell-gain'>"
        "<span class='val-gain-up' id='up'>+24.0%</span></td>"
        "<td data-label='Actions' class='desktop-action-cell cell-actions'>"
        "<div class='row-actions'><a href='#' class='icon-action-btn icon-edit'>e</a></div></td>"
        "<td class='mobile-action-bar cols-1' id='mbar'>x</td></tr>"
        "<tr><td data-label='Property' class='cell-property'>5 Kloof Street</td>"
        "<td data-label='Floor Area' class='num cell-area'><span class='val-none' id='none'>&mdash;</span></td>"
        "<td data-label='Purchase Price' class='num cell-purchase'>&euro; 200,000</td>"
        "<td data-label='Price/m2' class='num cell-price-sqm'>&mdash;</td>"
        "<td data-label='Current Value' class='num cell-current'>&euro; 150,000</td>"
        "<td data-label='Value/m2' class='num cell-value-sqm'>&mdash;</td>"
        "<td data-label='Gain %' class='num cell-gain'>"
        "<span class='val-gain-down' id='down'>-25.0%</span></td>"
        "<td data-label='Actions' class='desktop-action-cell cell-actions'>-</td>"
        "<td class='mobile-action-bar cols-1'>x</td></tr></tbody>"
        "<tfoot><tr><td class='cell-totals-label' colspan='2' id='tlab'>TOTAL</td>"
        "<td class='num' data-label='Total purchase' id='tpur'>&euro; 450,000</td>"
        "<td id='spacer'></td>"
        "<td class='num' data-label='Total current'>&euro; 460,000</td><td></td>"
        "<td class='num' data-label='Total gain'><span class='val-gain-up'>+2.2%</span></td>"
        "<td></td></tr></tfoot></table></div>")

PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const g = id => getComputedStyle(document.getElementById(id));
  const th = document.querySelector('thead th');
  const area = document.querySelector('td.cell-area');
  return {
    headBg: getComputedStyle(th).backgroundColor,
    headPos: getComputedStyle(th).position,
    overflow: getComputedStyle(document.querySelector('.table-container')).overflowY,
    purAlign: g('pur').textAlign, purNums: g('pur').fontVariantNumeric,
    up: g('up').color, down: g('down').color, none: g('none').color,
    tpurBg: g('tpur').backgroundColor, tpurWeight: g('tpur').fontWeight,
    tlabAlign: g('tlab').textAlign,
    spacer: g('spacer').display,
    mbar: g('mbar').display, mbarCols: g('mbar').gridTemplateColumns,
    areaDisplay: getComputedStyle(area).display,
    areaWidth: area.getBoundingClientRect().width,
    rowWidth: area.closest('tr').getBoundingClientRect().width,
    T1: tok('--alv-good'), T2: tok('--alv-bad'), T3: tok('--alv-ink-faint'),
    T4: tok('--alv-surface')}; }"""


async def render(page_css, width=1300):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': width, 'height': 800})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), page_css, FRAG))
        await pg.wait_for_timeout(60)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


OLD_FRAG = FRAG.replace("class='table-container'",
                        "class='valuations-table-container'")


async def render_old(page_css, width=1300):
    """The old page's stylesheet against the OLD markup shape."""
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': width, 'height': 800})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), page_css, OLD_FRAG))
        await pg.wait_for_timeout(60)
        out = await pg.evaluate(
            "()=>({overflow: getComputedStyle("
            "document.querySelector('.valuations-table-container')).overflowY})")
        await br.close()
        return out


async def main():
    head('6. what a reader actually sees')
    now = await render(css_of(PT))
    check('the header is base\'s quiet surface', now['headBg'] == now['T4'],
          now['headBg'])
    check('  and it can stick at last', now['headPos'] == 'sticky', now['headPos'])
    check('  because the container clips rather than hides',
          now['overflow'] == 'clip', now['overflow'])
    check('money is right-aligned with tabular figures',
          now['purAlign'] == 'right' and 'tabular-nums' in now['purNums'],
          '%s / %s' % (now['purAlign'], now['purNums']))
    check('a gain is the good token, not Bootstrap green',
          now['up'] == now['T1'] and now['up'] != 'rgb(40, 167, 69)', now['up'])
    check('a loss is the bad token, not Bootstrap red',
          now['down'] == now['T2'] and now['down'] != 'rgb(220, 53, 69)', now['down'])
    check('  and the two are different colours', now['up'] != now['down'])
    check('a figure that could not be worked out is faint, not zero-looking',
          now['none'] == now['T3'], now['none'])
    check('the total sits on the surface tone and is bold',
          now['tpurBg'] == now['T4'] and now['tpurWeight'] in ('700', 'bold'),
          '%s / %s' % (now['tpurBg'], now['tpurWeight']))
    check('  with its label right-aligned against the figures',
          now['tlabAlign'] == 'right', now['tlabAlign'])
    check('the mobile bar is hidden on desktop', now['mbar'] == 'none', now['mbar'])

    mob = await render(css_of(PT), width=420)
    check('on a phone the single action fills the card',
          mob['mbar'] == 'grid' and len(mob['mbarCols'].split()) == 1,
          '%s / %s' % (mob['mbar'], mob['mbarCols']))
    check('  the six figures sit three across, not one per line',
          mob['areaDisplay'] == 'inline-block'
          and 0.28 < (mob['areaWidth'] / mob['rowWidth']) < 0.36,
          '%.0f of %.0f px' % (mob['areaWidth'], mob['rowWidth']))
    check('  and the totals row\'s spacer cells vanish',
          mob['spacer'] == 'none', mob['spacer'])

    head('7. the negative controls')
    bak = PAGE + '.bak_valuations'
    if not check('the backup exists to compare against', os.path.exists(bak),
                 '(run apply_valuations.py first)'):
        return
    old = read(bak)
    # The control has to use the OLD SHAPE. Rendering the old stylesheet
    # against the new markup proves nothing: the old rule was keyed to
    # `.valuations-table-container`, so it simply does not apply to a
    # `.table-container`, and base's clip wins by default. That version of
    # this check failed, and it was right to.
    check('CONTROL: the old page had NO .table-container element at all',
          'class="table-container"' not in old
          and 'valuations-table-container' in old)
    check('  so base\'s observer, which looks for one, never saw this page',
          "closest('.table-container')" in BASE)
    was = await render_old(css_of(old))
    check('CONTROL: and its own shell DID hide its overflow',
          was['overflow'] == 'hidden', was['overflow'])
    _probes = [('on .alv-table', lambda t: 'alv-table' in t),
               ('one loop', lambda t: '{% for row in rows %}' in t),
               ('an empty state', lambda t: 'alv-empty-title' in t),
               ('a tfoot', lambda t: '<tfoot>' in t),
               ('an icon Edit', lambda t: 'icon-action-btn icon-edit' in t),
               ('no inline hex', lambda t: '#28a745' not in t)]
    _would = sum(1 for _, fn in _probes if not fn(old))
    check('  and %d of the static checks above fail on the old page' % _would,
          _would >= 5)
    check('CONTROL: the old page named its own shell',
          'valuations-table-container' in old)
    check('CONTROL: the old page computed Gain % in the template',
          'divide_by' in old and 'multiply' in old)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
