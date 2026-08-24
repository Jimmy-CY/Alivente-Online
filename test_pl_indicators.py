"""test_pl_indicators - do the consolidated indicators describe the year?

    python test_pl_indicators.py

The contribution gate is lifted verbatim out of pages/views/finance.py and run
against stub data, so this exercises the shipping code rather than a copy of it.
The chips themselves are rendered through Django's own template engine, and the
picker JS is driven in a real Chromium - a claim about JS that has never run in
a browser is a guess.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html')
TPLDIR = os.path.join(ROOT, 'pages', 'templates')

for p in (FINANCE, TPL):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

FIN_SRC = open(FINANCE, encoding='utf-8').read().replace('\r\n', '\n')
TPL_SRC = open(TPL, encoding='utf-8').read().replace('\r\n', '\n')

results = []


class _SkipBrowser(Exception):
    """Raised when playwright is not installed. Not a failure - the browser
    checks are a dev-machine extra, and a missing local tool must not block a
    push. A browser check that RUNS and fails is still a failure."""


def check(label, ok):
    results.append((label, bool(ok)))


# ============================================ LIFT THE GATE OUT OF THE SOURCE
# The trailing `ind_value_count` line is optional so this suite still lifts a
# correct block whether or not apply_pl_value_basis.py has run. Stopping one
# line short would silently exclude the counter from the lifted code and make
# every assertion about it read zero - a green-looking test of nothing.
m = re.search(r'^    ind_props, ind_skipped = \[\], \[\]\n(.*?)'
              r'^            ind_value_purchase \+= _purchase\n'
              r'(?:            ind_value_count \+= 1\n)?',
              FIN_SRC, re.S | re.M)
if not m:
    sys.exit('! the contribution gate was not found in finance.py '
             '- has apply_pl_indicators.py been run?')

GATE_SRC = '\n'.join(
    line[4:] if line.startswith('    ') else line
    for line in m.group(0).split('\n'))
GATE = compile(GATE_SRC, 'contribution_gate', 'exec')


class P:
    """Just enough of a property for the gate to walk."""

    def __init__(self, pid, name, area, purchase, value_as_of=None):
        self.prop_id = pid
        self.prop_name = name
        self.prop_floor_area = area
        self._purchase = purchase
        self._value_as_of = value_as_of


class PV:
    def __init__(self, purchase):
        self.prop_values_purchase_price = purchase


def run_gate(properties, rev, exp, act, year=2027):
    """Execute the shipped block against stub totals."""
    ns = {
        'properties': properties,
        'revenue_prop_totals': rev,
        'expense_prop_totals': exp,
        'actual_expense_prop_totals': act,
        'prop_values_map': {p.prop_id: (PV(p._purchase) if p._purchase is not None
                                        else None) for p in properties},
        'selected_year': year,
        'property_value_as_of': lambda prop, yr: prop._value_as_of,
    }
    exec(GATE, ns)
    return ns


# ================================================================ THE BASICS
A = P(1, 'Palikaridi', 100, 200000, 300000)
B = P(2, 'Athens First', 80, 320000, 400000)
C = P(3, 'Dikaiosynis', 60, 250000, 260000)

ZERO = {'year': 0}

ns = run_gate([A, B, C],
              rev={1: {'year': 12000}, 2: ZERO, 3: ZERO},
              exp={1: ZERO, 2: {'year': 3000}, 3: ZERO},
              act={1: ZERO, 2: ZERO, 3: ZERO})

check('revenue alone keeps a property in', A in ns['ind_props'])
check('expenses alone keep a property in', B in ns['ind_props'])
check('nothing at all drops it out', C not in ns['ind_props'])
check('  and it is NAMED, not silently dropped',
      ns['ind_skipped'] == ['Dikaiosynis'])
check('the purchase denominator excludes it',
      ns['ind_purchase_total'] == 200000 + 320000)
check('the area denominator excludes it',
      ns['ind_area_total'] == 100 + 80)

# an actual-expense amendment is contribution too - in Actuals view a property
# can have no budget at all and still have cost real money
ns = run_gate([A, C],
              rev={1: {'year': 12000}, 3: ZERO},
              exp={1: ZERO, 3: ZERO},
              act={1: ZERO, 3: {'year': 42}})
check('an actual expense alone keeps a property in', C in ns['ind_props'])
check('  so nothing is skipped', ns['ind_skipped'] == [])

# ============================================================== NULL SAFETY
ns = run_gate([A, B],
              rev={1: {'year': None}, 2: {}},
              exp={}, act={1: None, 2: None})
check('None totals count as zero, not as contribution', ns['ind_props'] == [])
check('a missing per-property entry does not raise',
      ns['ind_skipped'] == ['Palikaridi', 'Athens First'])

NOPRICE = P(4, 'No valuation row', 50, None)
ns = run_gate([NOPRICE], rev={4: {'year': 5000}}, exp={}, act={})
check('a property with no prop_values row still counts as held',
      ns['ind_props'] == [NOPRICE])
check('  and contributes 0 to the purchase denominator',
      ns['ind_purchase_total'] == 0)
check('  but still contributes its floor area', ns['ind_area_total'] == 50)

# ========================================================== VALUE INCREASE
# Apples-to-apples: a property with no dated valuation for the year must drop
# out of BOTH sides, or the ratio compares one set of properties' value against
# a different set's cost.
UNDATED = P(5, 'Never valued', 70, 150000, None)
ns = run_gate([A, UNDATED],
              rev={1: {'year': 12000}, 5: {'year': 9000}},
              exp={}, act={})
check('both properties count for the money denominators',
      ns['ind_purchase_total'] == 200000 + 150000)
check('but an undated valuation leaves BOTH sides of Value Increase',
      ns['ind_value_purchase'] == 200000)
check('  so the two sides describe the same properties',
      ns['ind_value_total'] == 300000)
check('  giving +50%, not a figure mixing two different sets',
      round((ns['ind_value_total'] - ns['ind_value_purchase'])
            / ns['ind_value_purchase'] * 100, 2) == 50.0)
# What the half-gated version would have said: 300,000 of value against
# 350,000 of cost reads as a portfolio that LOST money, purely because one
# property had no valuation on file.
check('  (the half-gated version would have read -14.29%)',
      round((ns['ind_value_total'] - ns['ind_purchase_total'])
            / ns['ind_purchase_total'] * 100, 2) == -14.29)
check('  and the chip reports its own coverage: 1 of 2',
      ns.get('ind_value_count') == 1 and len(ns['ind_props']) == 2)

# the year is passed through, not hardcoded to today
seen = {}


def _spy(prop, yr):
    seen['year'] = yr
    return 999


ns2 = {'properties': [A], 'revenue_prop_totals': {1: {'year': 1}},
       'expense_prop_totals': {}, 'actual_expense_prop_totals': {},
       'prop_values_map': {1: PV(100)}, 'selected_year': 2022,
       'property_value_as_of': _spy}
exec(GATE, ns2)
check('the valuation is read AS AT the selected year (2022, not today)',
      seen.get('year') == 2022)

# ==================================================== THE 2027 CASE ON SCREEN
# Ten properties; the two inactive ones contribute nothing to 2027 but their
# purchase prices used to sit in every denominator.
LIVE = [P(i, 'Prop %d' % i, 100, 300000, 450000) for i in range(1, 9)]
DEAD = [P(9, 'Dikaiosynis', 90, 250000, 260000),
        P(10, 'Ionion Villa H4', 110, 275000, 300000)]
ALL = LIVE + DEAD
rev = {p.prop_id: {'year': 17300} for p in LIVE}
rev.update({p.prop_id: ZERO for p in DEAD})
exp = {p.prop_id: {'year': 5700} for p in LIVE}
exp.update({p.prop_id: ZERO for p in DEAD})

ns = run_gate(ALL, rev=rev, exp=exp, act={})
revenue_year = sum(v['year'] for v in rev.values())

before = revenue_year / sum(p._purchase for p in ALL) * 100
after = revenue_year / ns['ind_purchase_total'] * 100

check('2027: the two silent properties are out (8 of 10)',
      len(ns['ind_props']) == 8)
check('  Gross ROI rises once they leave the divisor (%.2f%% -> %.2f%%)'
      % (before, after), after > before)
check('  and the numerator is untouched - only the divisor moved',
      ns['ind_purchase_total'] == sum(p._purchase for p in LIVE))
check('  Expenses to Revenue is unchanged by the gate',
      round(sum(v['year'] for v in exp.values()) / revenue_year * 100, 2)
      == round(45600 / 138400 * 100, 2))

# A held property that is genuinely empty must NOT be hidden: it has expenses,
# so the gate keeps it and the ROI it drags down is real.
IDLE = P(11, 'Empty but held', 95, 400000, 400000)
ns = run_gate(LIVE + [IDLE],
              rev={**{p.prop_id: {'year': 17300} for p in LIVE},
                   11: ZERO},
              exp={**{p.prop_id: {'year': 5700} for p in LIVE},
                   11: {'year': 800}},
              act={})
check('an idle property that still costs money is KEPT (no flattering)',
      IDLE in ns['ind_props'])

# ============================================================ IS IT WIRED IN?
chips = TPL_SRC[TPL_SRC.index('CONSOLIDATED FINANCIAL INDICATORS'):
                TPL_SRC.index('<!-- Loading Indicator -->')
                if '<!-- Loading Indicator -->' in TPL_SRC else None]

# Three, not one: Gross ROI once, Net ROI twice (the budget and actuals
# branches). Asserting mere presence would let one chip slip back onto the
# ungated divisor while its neighbour kept the test green.
check('all three ROI branches divide by the gated total',
      TPL_SRC.count('divide:ind_purchase_total') == 3)
check('Rent per sqm divides by the gated area',
      'divide:ind_area_total' in TPL_SRC)
check('Value Increase uses the matched purchase base',
      'divide:ind_value_purchase' in TPL_SRC)
check('no chip sums every selected property any more',
      'properties|sum_purchase_prices' not in TPL_SRC
      and "properties|sum_attr:'prop_floor_area'" not in TPL_SRC)
check('Expenses to Revenue still divides this year by this year',
      'divide:total_revenue' in TPL_SRC)
check('  and was NOT gated', 'ind_' not in TPL_SRC[
    TPL_SRC.index('Expenses to Revenue'):
    TPL_SRC.index('Rent (€/m')])
check('the basis note exists', 'roi-basis' in TPL_SRC)
check('  and only renders when something was left out',
      '{% if ind_skipped %}' in TPL_SRC)
check('  naming the properties', 'ind_skipped' in TPL_SRC
      and 'roi-basis-names' in TPL_SRC)
check('  and saying Expenses to Revenue is unaffected',
      'Expenses to Revenue is unaffected' in TPL_SRC)
check('the view no longer reads current value for the chips',
      'total_current_value|subtract' not in TPL_SRC)
# Scoped to the lifted block, NOT to the whole file: financial_indicators_view
# contains the same call, so a file-wide search would stay green even if the
# P&L's own copy were hardcoded to a year.
check('the P&L gate asks for the value as at the SELECTED year',
      'property_value_as_of(prop, selected_year)' in GATE_SRC)
check('Value Increase counts the properties it actually covers',
      'ind_value_count' in GATE_SRC)
check('  and the note reports that second denominator too',
      'ind_value_count < ind_count' in TPL_SRC)
check('  the note now renders for EITHER gate',
      '{% if ind_skipped or ind_value_count < ind_count %}' in TPL_SRC)

# every Django comment must open and close on ONE line - a multi-line {# #} is
# rendered as literal text, which broke a table row once already
bad_comments = []
for f in sorted(os.listdir(TPLDIR)):
    if not f.endswith('.html'):
        continue
    s = open(os.path.join(TPLDIR, f), encoding='utf-8').read()
    for i, line in enumerate(s.split('\n'), 1):
        if line.count('{#') != line.count('#}'):
            bad_comments.append('%s:%d' % (f, i))
check('no template opens a {# comment it fails to close on the same line%s'
      % (' (%s)' % ', '.join(bad_comments[:3]) if bad_comments
         else ' (none)'), not bad_comments)

# ============================================================== THE PICKER
check('Select All has a sibling for the inactive ones',
      'selectAllIncBtn' in TPL_SRC)
check('  which only renders when there ARE inactive properties',
      '{% if has_inactive %}' in TPL_SRC)
check('  and the view supplies that flag', "'has_inactive'" in FIN_SRC)
check('an active-only id list is built from prop_status',
      'activePropertyIds' in TPL_SRC
      and "{% if prop.prop_status == 'Active' %}" in TPL_SRC)
check('Select All ticks the active ones only',
      'activePropertyIds.includes(id)' in TPL_SRC)
check('the page default still selects everything (history is not dropped)',
      re.search(r'if \(!hasPropertiesParam && !selectionMade\) \{\s*'
                r'allPropertyIds\.forEach', TPL_SRC) is not None)

check('the panel state is written before both navigations',
      TPL_SRC.count('markPanelState();') == 2)
check('  and read back exactly once on load',
      TPL_SRC.count('restorePanelState();') == 1)
check('  the flag is consumed, so a real reload starts collapsed',
      re.search(r'restorePanelState[\s\S]{0,400}?removeItem\(PL_PANEL_KEY\)',
                TPL_SRC) is not None)
check('  storage failures are swallowed, not thrown',
      TPL_SRC.count('catch (e)') >= 2)

# ================================================== RENDER THE REAL CHIPS
try:
    import django
    from django.conf import settings
    from django.template import Context, Engine, Library

    register = Library()

    @register.filter
    def divide(a, b):
        try:
            return float(a) / float(b)
        except (TypeError, ValueError, ZeroDivisionError):
            return ''

    @register.filter
    def multiply(a, b):
        try:
            return float(a) * float(b)
        except (TypeError, ValueError):
            return ''

    @register.filter
    def subtract(a, b):
        try:
            return float(a) - float(b)
        except (TypeError, ValueError):
            return ''

    @register.filter(name='add')
    def add_(a, b):
        try:
            return float(a) + float(b)
        except (TypeError, ValueError):
            return ''

    if not settings.configured:
        settings.configure(DEBUG=True, USE_I18N=False)
        django.setup()

    frag = TPL_SRC[TPL_SRC.index('<!-- CONSOLIDATED ROI CALCULATIONS -->'):]
    frag = frag[:frag.index('</div>\n</div>') + len('</div>\n</div>')]

    engine = Engine(libraries={'x': __name__}, debug=True)
    sys.modules.setdefault(__name__, sys.modules['__main__'])
    tmpl = engine.from_string('{% load x %}' + frag)

    ctx = {
        'revenue_totals': {'year': 138400},
        'expense_totals': {'year': 45600},
        'actual_expense_totals': {'year': 0},
        'view_mode': 'budget',
        'selected_year': 2027,
        'ind_purchase_total': 2400000,
        'ind_area_total': 800,
        'ind_value_total': 3600000,
        'ind_value_purchase': 2400000,
        'ind_count': 8,
        'ind_total_count': 10,
        'ind_skipped': ['Dikaiosynis', 'Ionion Villa H4'],
        'ind_value_count': 8,
    }
    out = tmpl.render(Context(ctx))

    check('the chips render without a template error', 'Gross ROI' in out)
    check('  Gross ROI reads 5.77% (138,400 / 2,400,000)', '5.77%' in out)
    check('  Net ROI reads 3.87%', '3.87%' in out)
    check('  Expenses to Revenue reads 32.95%', '32.95%' in out)
    check('  Rent per sqm reads 14.42', '14.42' in out)
    check('  Value Increase reads 50.00%', '50.00%' in out)
    check('  the basis line names both excluded properties',
          'Dikaiosynis' in out and 'Ionion Villa H4' in out
          and '8</strong> of' not in out and '8 of' in out.replace(
              '<strong>', '').replace('</strong>', ''))
    check('  and reads "them", not "it", for two',
          'spent on\n            them' in out or 'them:' in out)

    ctx_none = dict(ctx, ind_skipped=[], ind_count=10, ind_total_count=10,
                    ind_value_count=10)
    out_none = tmpl.render(Context(ctx_none))
    check('nothing excluded -> no basis line at all',
          'roi-basis' not in out_none)

    ctx_one = dict(ctx, ind_skipped=['Dikaiosynis'], ind_count=9,
                   ind_value_count=9)
    out_one = tmpl.render(Context(ctx_one))
    check('one excluded -> "it", not "them"',
          'it:' in out_one and 'them:' not in out_one)

    ctx_partial = dict(ctx, ind_value_count=6)
    out_partial = tmpl.render(Context(ctx_partial))
    check('a partially-valued year says which chip covers fewer properties',
          '% Value Increase covers' in out_partial
          and '6 of 8' in out_partial)
    check('  and still reports the contribution gate alongside it',
          'Dikaiosynis' in out_partial)

    ctx_valonly = dict(ctx, ind_skipped=[], ind_count=10, ind_total_count=10,
                       ind_value_count=7)
    out_valonly = tmpl.render(Context(ctx_valonly))
    check('the note appears for the valuation gate ALONE',
          'roi-basis' in out_valonly and '% Value Increase covers' in out_valonly)
    check('  without claiming anything was left out of the year',
          'nothing was earned or spent' not in out_valonly)

    ctx_full = dict(ctx, ind_skipped=[], ind_count=10, ind_total_count=10,
                    ind_value_count=10)
    check('both gates clean -> still no note at all',
          'roi-basis' not in tmpl.render(Context(ctx_full)))

    ctx_noval = dict(ctx, ind_value_purchase=0, ind_value_total=0)
    out_noval = tmpl.render(Context(ctx_noval))
    check('no dated valuation -> says so, rather than showing 0%',
          'No valuation dated 2027' in out_noval)

    ctx_empty = dict(ctx, ind_purchase_total=0, ind_area_total=0,
                     ind_value_purchase=0, ind_count=0)
    out_empty = tmpl.render(Context(ctx_empty))
    check('an empty selection is N/A, never a divide-by-zero',
          out_empty.count('N/A') >= 3)

    ctx_act = dict(ctx, view_mode='actuals',
                   actual_expense_totals={'year': 10000})
    out_act = tmpl.render(Context(ctx_act))
    check('the Actuals view subtracts actuals from Net ROI',
          '3.45%' in out_act)

except Exception as exc:                                   # pragma: no cover
    check('rendering the chips raised %s: %s' % (type(exc).__name__, exc),
          False)

# ====================================================== DRIVE THE PICKER JS
try:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # Playwright is a dev-machine convenience, not a dependency of the app.
        # Where it is absent these checks simply do not run, and that is
        # reported as SKIP so a missing local tool cannot block a push. Only
        # the IMPORT is forgiven: a browser check that runs and fails is still
        # a failure.
        results.append(('Chromium checks skipped - playwright not installed '
                        '(pip install playwright, then playwright install '
                        'chromium)', None))
        raise _SkipBrowser()

    # Pull the three handlers out of the template and run them for real. The
    # template tags are substituted with the values Django would have produced.
    js = TPL_SRC
    js = js.replace(
        "[{% for prop in all_properties %}'{{ prop.prop_id }}'"
        "{% if not forloop.last %}, {% endif %}{% endfor %}]",
        "['1','2','3','4']")
    js = re.sub(r"\[\{% for prop in all_properties %\}\{% if prop\.prop_status"
                r" == 'Active' %\}'\{\{ prop\.prop_id \}\}', \{% endif %\}"
                r"\{% endfor %\}\]", "['1','2']", js)

    body = js[js.index('function togglePropSelection()'):]
    body = body[:body.index('function restorePanelState()')]
    restore = js[js.index('function restorePanelState()'):]
    restore = restore[:restore.index('\n}') + 2]

    page_html = """<!doctype html><html><body>
    <div class="property-selection-panel collapsed" id="propSelectionPanel">
      <div id="head"></div>
    </div>
    <input type="checkbox" id="prop-1"><input type="checkbox" id="prop-2">
    <input type="checkbox" id="prop-3"><input type="checkbox" id="prop-4">
    <div style="height:3000px"></div>
    <script>
    %s
    %s
    var allPropertyIds = ['1','2','3','4'];
    var activePropertyIds = ['1','2'];
    function selectAll() {
        allPropertyIds.forEach(function (id) {
            document.getElementById('prop-' + id).checked =
                activePropertyIds.includes(id);
        });
    }
    function selectAllInc() {
        allPropertyIds.forEach(function (id) {
            document.getElementById('prop-' + id).checked = true;
        });
    }
    </script></body></html>""" % (body, restore)

    path = os.path.join(ROOT, '_pl_picker_probe.html')
    open(path, 'w', encoding='utf-8').write(page_html)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path='/opt/pw-browsers/chromium/chrome-linux/chrome'
            if os.path.exists('/opt/pw-browsers/chromium/chrome-linux/chrome')
            else None)
        pg = browser.new_page(viewport={'width': 1366, 'height': 768})
        pg.goto('file://' + path)

        pg.evaluate('selectAll()')
        ticked = pg.evaluate(
            "allPropertyIds.filter(i => document.getElementById"
            "('prop-'+i).checked)")
        check('Chromium: Select All ticks the active two only',
              ticked == ['1', '2'])

        pg.evaluate('selectAllInc()')
        ticked = pg.evaluate(
            "allPropertyIds.filter(i => document.getElementById"
            "('prop-'+i).checked)")
        check('Chromium: + Inactive ticks all four',
              ticked == ['1', '2', '3', '4'])

        # collapsed panel -> nothing stored
        pg.evaluate('markPanelState()')
        check('Chromium: a collapsed panel stores nothing',
              pg.evaluate("sessionStorage.getItem('plPanelOpen')") is None)

        # open it, scroll, mark, then simulate the navigation
        pg.evaluate('togglePropSelection()')
        pg.evaluate('window.scrollTo(0, 640)')
        pg.evaluate('markPanelState()')
        check('Chromium: an open panel stores the scroll position',
              pg.evaluate("sessionStorage.getItem('plPanelOpen')") == '640')

        pg.reload()
        collapsed_before = pg.evaluate(
            "document.getElementById('propSelectionPanel')"
            ".classList.contains('collapsed')")
        pg.evaluate('restorePanelState()')
        check('Chromium: the panel renders collapsed, as the server sends it',
              collapsed_before is True)
        check('Chromium: restoring re-opens it after the navigation',
              pg.evaluate("!document.getElementById('propSelectionPanel')"
                          ".classList.contains('collapsed')"))
        pg.wait_for_timeout(120)
        check('Chromium: and the scroll position comes back (%s)'
              % pg.evaluate('Math.round(window.scrollY)'),
              abs(pg.evaluate('window.scrollY') - 640) < 3)
        check('Chromium: the flag is consumed - it is one-shot',
              pg.evaluate("sessionStorage.getItem('plPanelOpen')") is None)

        # a genuine reload finds no flag
        pg.reload()
        pg.evaluate('restorePanelState()')
        check('Chromium: a real reload leaves it collapsed',
              pg.evaluate("document.getElementById('propSelectionPanel')"
                          ".classList.contains('collapsed')"))

        browser.close()
    os.remove(path)
except _SkipBrowser:
    pass
except Exception as exc:                                   # pragma: no cover
    check('driving the picker raised %s: %s' % (type(exc).__name__, exc), False)

# ====================================================================== out
print('')
bad = skipped = 0
for label, ok in results:
    if ok is None:
        print('  SKIP  %s' % label)
        skipped += 1
        continue
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
ran = len(results) - skipped
if bad:
    print('%d of %d failed' % (bad, ran))
else:
    print('All %d checks passed.%s'
          % (ran, ' (%d skipped)' % skipped if skipped else ''))
sys.exit(1 if bad else 0)
