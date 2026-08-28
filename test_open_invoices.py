#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Open Invoices: the same invoices, and base's table.

Run from the repo root. Needs Playwright's chromium.

THE POINT. This round moved the table's row-building out of the template and
into the view. A styling round can be checked by rendering it; a view change
cannot - the only question that matters is whether the SAME INVOICES, in the
SAME ORDER, still appear. So section 1 runs the old triple loop and the new
view function side by side over generated data and compares the sequences.
The old loop is reimplemented here from the template it replaced, together
with the two template tags' arithmetic, so the comparison is against what the
page actually did rather than against what I remember it doing.
"""
import os, re, sys, random, asyncio
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'invoices.html')
BASEF = os.path.join(TPL, 'base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'invoices.py')

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


BASE, PT, VT = read(BASEF), read(PAGE), read(VIEW)
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''


# ---------------------------------------------------------------------------
# 1. THE ROWS
# ---------------------------------------------------------------------------
class Row(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


def old_due_date(invoice_date, payment_terms):
    """`calculate_due_date`, from pages/templatetags/invoice_tags.py."""
    if not invoice_date or payment_terms is None:
        return invoice_date
    return invoice_date + timedelta(days=int(payment_terms))


def old_days_overdue(due_date):
    """`calculate_days_overdue`, from the same file."""
    if not due_date:
        return 0
    today = date.today()
    return (today - due_date).days if today > due_date else 0


def reference_rows(open_invoices, shown_props, shown_tenants):
    """The template's three nested loops, exactly as they were written:

        {% for results in props %}
          {% for tresults in tenant %}
            {% for iresults in invoices %}
              {% if iresults.tenant_id == tresults.tenant_id
                    and tresults.prop_id == results.prop_id %}

    Property-major, then tenant, then the invoice queryset's own order.
    """
    out = []
    for p in shown_props:
        for t in shown_tenants:
            for inv in open_invoices:
                if inv.tenant_id == t.tenant_id and t.prop_id == p.prop_id:
                    due = old_due_date(inv.invoice_date, t.tenant_payment_terms)
                    out.append({
                        'invoice_id':   inv.invoice_id,
                        'prop_name':    p.prop_name,
                        'prop_country': p.prop_country,
                        'tenant_name':  t.tenant_name,
                        'amount':       inv.effective_amount,
                        'invoice_date': inv.invoice_date,
                        'due_date':     due,
                        'days_overdue': old_days_overdue(due),
                    })
    return out


def load_new_builder(view_src):
    """Lift `_open_invoice_rows` out of the view without importing Django."""
    i = view_src.find('def _open_invoice_rows')
    if i < 0:
        return None
    rest = view_src[i:]
    m = re.search(r'\n(?=@|def )', rest[1:])
    body = rest[:m.start() + 1] if m else rest
    ns = {'date': date, 'timedelta': timedelta}
    exec(compile(body, '<rowbuilder>', 'exec'), ns)
    return ns.get('_open_invoice_rows')


def same(a, b):
    """Compare on the fields BOTH sides produce - the new one adds is_overdue,
    which is days_overdue > 0 and is checked separately."""
    keys = ('invoice_id', 'prop_name', 'prop_country', 'tenant_name', 'amount',
            'invoice_date', 'due_date', 'days_overdue')
    if len(a) != len(b):
        return False, 'row count %d vs %d' % (len(a), len(b))
    for i, (x, y) in enumerate(zip(a, b)):
        for k in keys:
            if x.get(k) != y.get(k):
                return False, 'row %d, %s: %r vs %r' % (i, k, x.get(k), y.get(k))
    return True, '%d row(s)' % len(a)


def dataset(seed, nprops=6, ntenants=9, ninv=25, orphans=True):
    rnd = random.Random(seed)
    props = [Row(prop_id=i, prop_name='Prop %d' % i,
                 prop_country=rnd.choice(['Cyprus', 'Greece', 'Spain']))
             for i in range(1, nprops + 1)]
    tenants = [Row(tenant_id=100 + i, tenant_name='Tenant %02d' % i,
                   prop_id=rnd.choice(props).prop_id,
                   tenant_payment_terms=rnd.choice([0, 7, 30, 60, None]))
               for i in range(1, ntenants + 1)]
    ids = [t.tenant_id for t in tenants]
    if orphans:
        ids += [999]                      # an invoice whose tenant is gone
    inv = [Row(invoice_id=1000 + i, tenant_id=rnd.choice(ids),
               effective_amount=rnd.randrange(100, 5000),
               invoice_date=date(2026, 1, 1) + timedelta(days=rnd.randrange(0, 400)))
           for i in range(ninv)]
    inv.sort(key=lambda x: x.invoice_date)   # the queryset's order_by
    return inv, props, tenants


head('1. the rows: the old triple loop against the new view function')
NEW = load_new_builder(VT)
# NOT an early exit. On an un-migrated tree the row comparison cannot run,
# but every static check below still can and every one of them should fail -
# which is what proves this suite catches an un-migrated page rather than
# quietly reporting one failure and stopping.
if check('the view exposes _open_invoice_rows', NEW is not None,
         '(run apply_open_invoices.py first)'):
  _bad = 0
  for seed in range(60):
      inv, props, tenants = dataset(seed)
      ok, why = same(reference_rows(inv, props, tenants), NEW(inv, props, tenants))
      if not ok:
          _bad += 1
          if _bad <= 3:
              print('      seed %d: %s' % (seed, why))
  check('60 generated portfolios produce identical row sequences', _bad == 0,
        '%d differed' % _bad)

  # The awkward ones, by hand rather than by luck.
  inv, props, tenants = dataset(7)
  cases = [
      ('a property filtered out', (inv, props[:2], tenants)),
      ('a tenant filtered out', (inv, props, tenants[:3])),
      ('both filtered to one', (inv, props[:1], tenants[:1])),
      ('no properties at all', (inv, [], tenants)),
      ('no tenants at all', (inv, props, [])),
      ('no invoices at all', ([], props, tenants)),
      ('everything empty', ([], [], [])),
  ]
  # an invoice with no date - the old tag returned the date unchanged and 0
  # days overdue, so the row rendered blank rather than raising.
  _nodate = list(inv) + [Row(invoice_id=1, tenant_id=tenants[0].tenant_id,
                             effective_amount=50, invoice_date=None)]
  cases.append(('an invoice with no date', (_nodate, props, tenants)))
  # two properties sharing a name, which prop_name filtering really can return
  _dupe = list(props) + [Row(prop_id=99, prop_name=props[0].prop_name,
                             prop_country=props[0].prop_country)]
  cases.append(('two properties with the same name', (inv, _dupe, tenants)))
  for what, args in cases:
      try:
          ok, why = same(reference_rows(*args), NEW(*args))
      except Exception as e:
          ok, why = False, 'raised %s: %s' % (type(e).__name__, e)
      check('  %-32s' % what, ok, why)

  # is_overdue must be exactly days_overdue > 0, never its own opinion.
  inv, props, tenants = dataset(3)
  _rows = NEW(inv, props, tenants)
  check('is_overdue is days_overdue > 0 on every row',
        all(r['is_overdue'] == (r['days_overdue'] > 0) for r in _rows),
        '%d rows' % len(_rows))

  # CONTROL. If the comparison cannot fail it is not evidence. Feed the
  # reference a deliberately wrong order and confirm it is caught.
  _ref = reference_rows(inv, props, tenants)
  if len(_ref) > 2:
      _scrambled = [_ref[1], _ref[0]] + _ref[2:]
      check('CONTROL: swapping two rows IS detected',
            not same(_scrambled, _rows)[0])
      check('CONTROL: dropping a row IS detected', not same(_ref[:-1], _rows)[0])
      _changed = [dict(r) for r in _ref]
      _changed[0]['days_overdue'] = _changed[0]['days_overdue'] + 1
      check('CONTROL: a one-day difference IS detected',
            not same(_changed, _rows)[0])

head('2. the view is still guarded, and still says which rows')
check('invoices_page keeps @login_required',
      re.search(r'@login_required\s*\n@permission_required\([^)]*can_access_invoices'
                r'[^)]*\)\s*\ndef invoices_page', VT) is not None)
check('  the row helper carries NO decorators of its own',
      re.search(r'@\w+[^\n]*\n\s*def _open_invoice_rows', VT) is None)
check('the context sends rows', '"rows": _open_invoice_rows(' in VT)
check('  built from the FILTERED lists, so filtering still filters',
      '_open_invoice_rows(iresults, filtered_props, filtered_tenants)' in VT)
check('  and the dropdowns get the unfiltered ones',
      '"all_props": all_props' in VT and '"all_tenants": all_tenants' in VT)
check('the template asks for all_props / all_tenants',
      '{% for prop in all_props %}' in PT
      and '{% for tenant_item in all_tenants %}' in PT)
check('  and no longer for the filtered lists - the bug that trapped you '
      'on one property',
      '{% for prop in props %}' not in PT
      and '{% for tenant_item in tenant %}' not in PT)

head('3. the template stopped deciding its own rows')
check('one loop over rows', PT.count('{% for row in rows %}') == 1)
check('  the three nested loops are gone',
      'iresults' not in PT and 'tresults' not in PT)
check('  and the two template tags with them',
      'calculate_due_date' not in PT and 'calculate_days_overdue' not in PT
      and 'invoice_tags' not in PT)
check('an empty result says so, instead of looking like a failed load',
      '{% if not rows %}' in PT and 'alv-empty-title' in PT)
check('template if/endif balance',
      len(re.findall(r'\{%\s*if\b', PT)) == len(re.findall(r'\{%\s*endif\s*%\}', PT)))
check('template for/endfor balance',
      len(re.findall(r'\{%\s*for\b', PT)) == len(re.findall(r'\{%\s*endfor\s*%\}', PT)))
check('div tags balance',
      len(re.findall(r'<div\b', PT)) == len(re.findall(r'</div\s*>', PT)))
check('CSS braces balance',
      css_of(PT).count('{') == css_of(PT).count('}'))

head('4. the table joined the standard')
check('the table carries .alv-table', 'class="table alv-table invoices-table"' in PT)
check('  and dropped table-bordered / table-striped',
      'table-bordered' not in PT and 'table-striped' not in PT)
for dead in ('.table-container table thead th', '.table-container table tbody td',
             '.btn-paid', '.active-filters {', '.btn-info'):
    check('  %-32s is gone' % dead, dead not in css_of(PT))
check('the page no longer sets overflow on the container',
      not re.search(r'\.table-container\s*\{[^}]*overflow', css_of(PT)))
check('  which is the point: base needs clip for the sticky heading',
      'overflow: clip' in css_of(BASE))
check('Amount and Days Overdue are numbers',
      PT.count('class="num') >= 2 and '<th class="num"' in PT)
check('the Actions column uses the house classes',
      'desktop-action-cell cell-actions' in PT)
check('  the paid control is a POST form, as on every migrated page',
      "<form method=\"post\" action=\"{% url 'invoices_commit' row.invoice_id %}\"" in PT
      and '{% csrf_token %}' in PT)
check('  and no longer a bare link that mutates on GET',
      "<a href=\"{% url 'invoices_commit'" not in PT)
check('mobile gets a one-column action bar',
      'mobile-action-bar cols-1' in PT)
check('  and base defines cols-1 beside cols-2 and cols-4',
      '.mobile-action-bar.cols-1' in css_of(BASE)
      and '.mobile-action-bar.cols-2' in css_of(BASE))
check('overdue red is the token, not Bootstrap',
      'var(--alv-bad)' in css_of(PT) and '#dc3545' not in css_of(PT))
check('the dead filter-expand block is gone',
      'filterToggleIcon' not in PT and 'if (false)' not in PT)


# ---------------------------------------------------------------------------
# 5-6. WHAT IT LOOKS LIKE
# ---------------------------------------------------------------------------
FRAG = ("<div class='table-container'>"
        "<table class='table alv-table invoices-table'><thead><tr>"
        "<th>Property</th><th>Country</th><th>Tenant</th>"
        "<th class='num'>Amount</th><th>Invoice Date</th><th>Due Date</th>"
        "<th class='num'>Days Overdue</th>"
        "<th class='desktop-action-cell cell-actions'>Actions</th></tr></thead>"
        "<tbody><tr>"
        "<td data-label='Property'>12 Oak Avenue</td>"
        "<td data-label='Country'>Cyprus</td>"
        "<td data-label='Tenant'>J. Meyer</td>"
        "<td data-label='Amount' class='num amount-cell'>&euro;1,250</td>"
        "<td data-label='Invoice Date'>2026-05-01</td>"
        "<td data-label='Due Date'>2026-05-31</td>"
        "<td data-label='Days Overdue' class='num overdue-cell is-overdue' id='od'>89</td>"
        "<td data-label='Actions' class='desktop-action-cell cell-actions'>"
        "<form class='inv-inline-form'><button type='submit' "
        "class='icon-action-btn icon-approve' id='paid'>x</button></form></td>"
        "<td class='mobile-action-bar cols-1' id='mbar'>"
        "<button class='mobile-action-btn'>"
        "<i class='fas fa-check mobile-action-icon icon-color-approve' id='mi'>x</i>"
        "<span class='mobile-action-label'>Mark as Paid</span></button></td>"
        "</tr></tbody></table></div>")

PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const el = id => document.getElementById(id);
  const th = [...document.querySelectorAll('th')];
  const o = {};
  const head = th[0];
  o.headBg   = getComputedStyle(head).backgroundColor;
  o.headCol  = getComputedStyle(head).color;
  o.headPos  = getComputedStyle(head).position;
  o.overflow = getComputedStyle(document.querySelector('.table-container')).overflowY;
  o.odCol    = getComputedStyle(el('od')).color;
  o.odAlign  = getComputedStyle(el('od')).textAlign;
  const amt = document.querySelector('td.amount-cell');
  o.amtAlign = getComputedStyle(amt).textAlign;
  o.amtNums  = getComputedStyle(amt).fontVariantNumeric;
  o.paidCol  = getComputedStyle(el('paid')).color;
  o.mbar     = getComputedStyle(el('mbar')).display;
  o.mbarCols = getComputedStyle(el('mbar')).gridTemplateColumns;
  o.rowBg    = getComputedStyle(document.querySelector('tbody tr')).backgroundColor;
  for (const v of ['--alv-bad', '--alv-good', '--alv-surface', '--alv-paper'])
    o['T' + v] = tok(v);
  return o; }"""


async def render(page_css, width=1300):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': width, 'height': 900})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), page_css, FRAG))
        await pg.wait_for_timeout(60)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


async def main():
    head('5. what a reader actually sees')
    now = await render(css_of(PT))
    check('the header is base\'s quiet surface, not the navy band',
          now['headBg'] == now['T--alv-surface'], now['headBg'])
    check('  and its text is ink, not white',
          now['headCol'] != 'rgb(255, 255, 255)', now['headCol'])
    check('the heading can actually stick', now['headPos'] == 'sticky', now['headPos'])
    check('  because the container clips rather than hides',
          now['overflow'] == 'clip', now['overflow'])
    check('Amount is right-aligned with tabular figures',
          now['amtAlign'] == 'right' and 'tabular-nums' in now['amtNums'],
          '%s / %s' % (now['amtAlign'], now['amtNums']))
    check('Days Overdue is right-aligned', now['odAlign'] == 'right', now['odAlign'])
    check('  and an overdue count is the bad token, not Bootstrap red',
          now['odCol'] == now['T--alv-bad'] and now['odCol'] != 'rgb(220, 53, 69)',
          now['odCol'])
    check('the paid tick is the house green', now['paidCol'] == now['T--alv-good'],
          now['paidCol'])
    check('no zebra survives on the desktop row',
          now['rowBg'] in ('rgba(0, 0, 0, 0)', 'transparent', now['T--alv-paper']),
          now['rowBg'])
    check('the mobile bar is hidden on desktop', now['mbar'] == 'none', now['mbar'])

    mob = await render(css_of(PT), width=420)
    check('on a phone it appears as ONE full-width column',
          mob['mbar'] == 'grid' and len(mob['mbarCols'].split()) == 1,
          '%s / %s' % (mob['mbar'], mob['mbarCols']))

    head('6. the negative controls')
    bak = PAGE + '.bak_openinv'
    if not check('the backup exists to compare against', os.path.exists(bak),
                 '(run apply_open_invoices.py first)'):
        return
    was = await render(css_of(read(bak)))
    check('CONTROL: the header WAS a navy band',
          was['headBg'] == 'rgb(44, 62, 80)', was['headBg'])
    check('  in white text', was['headCol'] == 'rgb(255, 255, 255)', was['headCol'])
    check('CONTROL: the container DID hide its overflow, which kills sticky',
          was['overflow'] == 'hidden', was['overflow'])
    check('CONTROL: overdue WAS Bootstrap red',
          was['odCol'] == 'rgb(220, 53, 69)', was['odCol'])
    # constructed: the finished page minus the one line under test
    _css = css_of(BASE).replace('.mobile-action-bar.cols-1 '
                                '{ grid-template-columns: 1fr; }', '')
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 420, 'height': 900})
        await pg.set_content("<style>%s</style><style>%s</style><style>%s</style>"
                             "<body>%s</body>"
                             % (BOOTSTRAP, _css, css_of(PT), FRAG))
        await pg.wait_for_timeout(60)
        cols = await pg.evaluate(
            "()=>getComputedStyle(document.getElementById('mbar')).gridTemplateColumns")
        await br.close()
    check('CONTROL: without cols-1 the button is a third of the card wide',
          len(cols.split()) == 3, cols)

    old = read(bak)
    _probes = [('on .alv-table', lambda t: 'alv-table' in t),
               ('one loop', lambda t: '{% for row in rows %}' in t),
               ('an empty state', lambda t: 'alv-empty-title' in t),
               ('a POST form', lambda t: 'inv-inline-form' in t)]
    _would = sum(1 for _, fn in _probes if not fn(old))
    check('  and %d of the static checks above fail on the old page' % _would,
          _would >= 4)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
