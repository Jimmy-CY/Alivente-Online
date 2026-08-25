"""test_help_pl - does the P&L help describe the P&L that shipped?

    python test_help_pl.py

Two kinds of check, and the second is the point:

  1. The modal still parses - through the app's OWN help_renderer, not a guess
     about the format. A tab that fails to parse does not error; it silently
     vanishes from the modal.

  2. Every concrete claim the help makes is checked against the SHIPPING
     TEMPLATE. Help drifts because nothing tells it to. If someone renames the
     "+ Inactive" button or rewords the basis note, these fail and the help
     gets corrected in the same change rather than a year later.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HELP = os.path.join(ROOT, 'pages', 'help_content', 'reports.html')
TPL = os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')

for p in (HELP, TPL, FINANCE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

HELP_SRC = open(HELP, encoding='utf-8').read().replace('\r\n', '\n')
TPL_SRC = open(TPL, encoding='utf-8').read().replace('\r\n', '\n')
FIN_SRC = open(FINANCE, encoding='utf-8').read().replace('\r\n', '\n')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


# ============================================= PARSE IT THE WAY THE APP DOES
# Loaded by PATH, not as pages.services.help_renderer: importing the `pages`
# package runs its __init__, which pulls in pymysql. The renderer itself needs
# nothing but BeautifulSoup, so there is no reason to drag a database driver
# into a test about help text.
try:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        '_help_renderer',
        os.path.join(ROOT, 'pages', 'services', 'help_renderer.py'))
    _hr = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_hr)
    _hr.clear_cache()
    module = _hr.get_help_module('finance_pl_act')
except Exception as exc:                                   # pragma: no cover
    module = None
    check('help_renderer could parse the file (%s: %s)'
          % (type(exc).__name__, exc), False)

if module:
    check('the P&L modal is found by its slug', True)
    check('  it is titled Profit & Loss Statement',
          'Profit' in (module.get('name') or ''))

    tabs = module.get('tabs') or []
    slugs = [t.get('slug') for t in tabs]
    check('  six tabs survive (%s)' % ', '.join(slugs), len(tabs) == 6)
    for want in ('pl-overview', 'pl-filters', 'pl-grid', 'pl-drilling',
                 'pl-kpis', 'pl-tips'):
        check('    %s is present' % want, want in slugs)

    for t in tabs:
        body = t.get('content_html') or ''
        check('  %s has content (%d chars)' % (t.get('slug'), len(body)),
              len(body) > 200)
        # An unclosed <div> swallows everything after it in the modal.
        opens = len(re.findall(r'<div\b', body))
        closes = len(re.findall(r'</div>', body))
        check('    %s: its divs balance (%d/%d)' % (t.get('slug'), opens,
                                                    closes), opens == closes)

    by_slug = {t.get('slug'): (t.get('content_html') or '') for t in tabs}
else:
    by_slug = {}

KPI = by_slug.get('pl-kpis', '')
FIL = by_slug.get('pl-filters', '')
OV = by_slug.get('pl-overview', '')
TIPS = by_slug.get('pl-tips', '')

# =========================================== THE STALE STATEMENTS MUST BE GONE
check('the old "Budget mode vs Year mode" section is gone',
      'Budget mode vs Year mode' not in HELP_SRC)
check('  because the year dropdown no longer offers "Budget"',
      'view=budget' in TPL_SRC and 'pl-view-toggle' in TPL_SRC)
check('Gross ROI no longer documents an ungated divisor',
      'Total Revenue &divide; Total Purchase Price' not in HELP_SRC)
check('% Value Increase no longer documents Total Current Value',
      'Total Current Value &minus; Total Purchase Price' not in HELP_SRC)
check('Select All is no longer described as ticking everything',
      'Select All</strong> &mdash; ticks every property' not in HELP_SRC)

# ============================== EVERY CLAIM CHECKED AGAINST WHAT SHIPPED
# --- the contribution gate
check('the Indicators tab states the rule',
      'earned <strong>nothing</strong> and cost <strong>nothing</strong>'
      in KPI)
check('  and the code applies exactly that test',
      re.search(r'if _rev or _exp or _act:', FIN_SRC) is not None)
check('  the help says Expenses to Revenue is NOT filtered',
      'deliberately not filtered' in KPI)
check('  and the template really does leave it ungated',
      'divide:total_revenue' in TPL_SRC)
check('  the help says a held-but-empty property is kept',
      'cannot quietly hide an underperformer' in KPI)

# --- the basis note. Quote it in the help ONLY if the page says it.
for phrase in ('Based on', 'Left out of', 'nothing was earned or spent'):
    check('  the note wording "%s" matches the page' % phrase,
          phrase in KPI and phrase in TPL_SRC)

check('the help quotes the Value Increase coverage line',
      '% Value Increase covers' in KPI)
check('  and the page emits it', '% Value Increase covers' in TPL_SRC)

# --- year-aware valuation
check('the help says the valuation is read at the end of the selected year',
      'value at the end of the selected year' in KPI)
check('  and the code asks for exactly that',
      'property_value_as_of(prop, selected_year)' in FIN_SRC)
check('the help explains why BOTH halves drop together',
      'its value <em>and</em> its purchase price' in KPI)
check('  and the code drops them together',
      re.search(r'ind_value_total \+= _as_of\s*\n\s*ind_value_purchase'
                r' \+= _purchase', FIN_SRC) is not None)
check('  it warns growth could otherwise read as a loss',
      'look as though it has shrunk' in KPI)

# --- the picker
check('the Filters tab documents the split Select All',
      'ticks the <strong>active</strong> properties' in FIL)
# Matched as the button's TEXT, not just as a string somewhere in the file -
# the sibling button's title attribute also mentions "+ Inactive", so a loose
# search stayed green when the label itself was renamed.
check('  and "+ Inactive" is the real button label',
      '+ Inactive' in FIL and '>+ Inactive</button>' in TPL_SRC)
check('  the help says it only appears when needed',
      'only appears when you actually have an inactive property' in FIL)
check('  and the template really does hide it',
      '{% if has_inactive %}' in TPL_SRC)
check('the help says the panel stays open',
      'stays open' in FIL and 'scroll position' in FIL)
check('  and the page carries the state across the reload',
      'markPanelState' in TPL_SRC and 'restorePanelState' in TPL_SRC)
check('  the help says a reload closes it again',
      'until you close it yourself or reload the page' in FIL)
check('the help mentions the Inactive pill',
      'Inactive</strong> pill' in FIL)
check('  and the picker renders one', 'pl-inactive-pill' in TPL_SRC)

# --- the toggle
check('the Overview describes Budget vs Actuals',
      'Always a year, then Budget or Actuals' in OV)
check('  and the toggle exists with both labels',
      '>\n            Budget\n        </a>' in TPL_SRC
      and '>\n            Actuals\n        </a>' in TPL_SRC)
check('the Overview says a past year reports as it was',
      'Past years are reported as they were' in OV)

# --- tips
check('the Tips tab gives more than one cause for N/A',
      'nothing to divide by' in TIPS)
check('  and points at the basis line', 'Read the line under the tiles' in TIPS)
check('  and explains partial Value Increase coverage',
      'no valuation dated that year or earlier' in TIPS)
check('  calling it deliberate, not a fault',
      'declining to guess' in TIPS)

# --- no stray template syntax leaked into the help
check('no Django tag leaked into the help content',
      '{%' not in HELP_SRC and '{{' not in HELP_SRC)

# ====================================================================== out
print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
