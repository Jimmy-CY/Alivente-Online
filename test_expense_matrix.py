"""test_expense_matrix.py - one expense, every year, every property.

    python test_expense_matrix.py

Run from the project root, after apply_expense_matrix.py.

WHAT THIS SUITE IS FOR
----------------------
Three claims, and only one of them can be checked by reading the source.

  * SECTION 2 runs the helper against a real database with real
    FinancialFigureHistory rows, so "the figures are right" is measured
    rather than asserted. It includes the decision that was put back to the
    user because it moves money: NO PRO-RATING. The control runs the P&L's
    own property_annual_budgeted_expenses over the same data and shows the
    two deliberately disagree for a property's first year.
  * SECTION 4 SCROLLS THE TABLE IN A BROWSER. `position: sticky` inside
    `overflow-x: auto` is the single most confident-looking thing in CSS that
    silently does nothing - it is the same family of fault as the sticky
    headings, which looked correct in the stylesheet for months while
    `overflow: hidden` quietly stopped them working. The check scrolls 600px
    sideways and reads the property column's position back.
  * The rest is ownership: base defines the two components, the page uses
    them and does not redefine them.
"""
import os
import re
import sys
import ast
import tempfile
from decimal import Decimal
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(TPL, 'base.html')
PAGE = os.path.join(TPL, 'finance_expense.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')
SUFFIX = '.bak_expmatrix'

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
    text = re.sub(r'\{#[^\r\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


for p in (BASE, PAGE, VIEW):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root' % p)

BS, PG, VS = read(BASE), read(PAGE), read(VIEW)
BC, PC = nocomment(BS), nocomment(PG)

if 'def expense_matrix' not in VS:
    print('\n! not patched - run apply_expense_matrix.py first.')
    sys.exit(1)

# ===========================================================================
head('1. base owns the two components; the page only places them')
# ===========================================================================

check('base defines .alv-seg', '.alv-seg {' in BC)
check('  the current segment is filled, and by an ARIA state, not a class',
      re.search(r'\.alv-seg > \[aria-current="page"\]', BC) is not None)
check('  and it takes no semantic colour - a view is not a verdict',
      not re.search(r'\.alv-seg[^{]*\{[^}]*--alv-(good|bad|warn)', BC))
check('base defines .alv-matrix-scroll', '.alv-matrix-scroll {' in BC)
check('  and it scrolls sideways',
      re.search(r'\.alv-matrix-scroll\s*\{[^}]*overflow-x:\s*auto', BC)
      is not None)
check('  the first column freezes',
      re.search(r'\.alv-matrix-row-head[^{]*\{[^}]*position:\s*sticky', BC,
                re.S) is not None)
check('  and so does the total column',
      re.search(r'\.alv-matrix-total[^{]*\{[^}]*position:\s*sticky', BC, re.S)
      is not None)

# The reason there are two names at all.
check('.table-container was NOT given overflow-x - that would break every '
      'sticky heading in the system',
      not re.search(r'\.table-container\s*\{[^}]*overflow-x:\s*auto', BC))
check('  it still clips, which is what lets a heading pin',
      re.search(r'\.table-container\s*\{[^}]*overflow:\s*clip', BC) is not None)

for gone in ('.alv-seg {', 'table.alv-matrix {', '.alv-matrix-scroll {'):
    check('the page does NOT redefine %s' % gone, gone not in PC)
check('the page keeps only where they sit', '.expense-view-bar' in PC)
check('humanize is loaded, since intcomma is used',
      '{% load humanize %}' in PG)
check('base CSS braces still balance',
      sum(b.count('{') for b in re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S))
      == sum(b.count('}') for b in re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S)))

# ===========================================================================
# The database.
# ===========================================================================
import django                                                  # noqa: E402
from django.conf import settings                               # noqa: E402

STUB = tempfile.mkdtemp(prefix='expmatrix_')
with open(os.path.join(STUB, 'base.html'), 'w', encoding='utf-8') as _f:
    _f.write('<!doctype html><html><head><title>'
             '{% block title %}{% endblock %}</title></head><body>'
             '{% block content %}{% endblock %}</body></html>')

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                        'django.contrib.humanize',
                        'django.contrib.staticfiles', '__main__'],
        STATIC_URL='/static/', ROOT_URLCONF='__main__',
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [STUB, TPL], 'APP_DIRS': False,
                    # The page loads the project's own two tag libraries.
                    # Stubbing them here rather than importing pages.* keeps
                    # this suite from dragging the whole app in, and the two
                    # things they provide on this page - a sort and the help
                    # modal - are not what is being tested.
                    'OPTIONS': {'libraries': {
                        'custom_filters': '__main__',
                        'help_modal_tags': '__main__'}}}],
        USE_TZ=False, DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()

from django.db import models, connection                       # noqa: E402
from django.urls import path                                   # noqa: E402
from django.http import HttpResponse                           # noqa: E402


def _noop(request, *a, **k):                                   # pragma: no cover
    return HttpResponse('')


urlpatterns = [path('x/', _noop, name='finance_expense_add'),
               path('y/', _noop, name='finance')]

from django import template as _dt                             # noqa: E402

register = _dt.Library()


@register.filter
def sort_by_expense_line_type(value):
    """The page's own sort. Not what this suite is testing - it is here so
    the template compiles."""
    return sorted(value, key=lambda e: str(
        getattr(getattr(e, 'expense_line_types', None),
                'expense_line_types_name', '') or ''))


@register.simple_tag
def render_help_modal(*a, **k):
    return ''


MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


class props(models.Model):                              # noqa: N801
    prop_id = models.AutoField(primary_key=True)
    prop_name = models.CharField(max_length=255, blank=True, null=True)
    prop_status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = '__main__'


class expense_types(models.Model):                      # noqa: N801
    expense_types_id = models.AutoField(primary_key=True)
    expense_types_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = '__main__'


class expense_line_types(models.Model):                 # noqa: N801
    expense_line_types_id = models.AutoField(primary_key=True)
    expense_line_types_name = models.CharField(max_length=255, blank=True,
                                               null=True)

    class Meta:
        app_label = '__main__'


class expense(models.Model):                            # noqa: N801
    expense_id = models.AutoField(primary_key=True)
    expense_types = models.ForeignKey(expense_types, on_delete=models.CASCADE)
    expense_line_types = models.ForeignKey(expense_line_types,
                                           on_delete=models.CASCADE)
    expense_amount = models.DecimalField(max_digits=8, decimal_places=2,
                                         blank=True, null=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)

    class Meta:
        app_label = '__main__'


for _m in MONTHS:
    expense.add_to_class('expense_' + _m,
                         models.DecimalField(max_digits=8, decimal_places=2,
                                             blank=True, null=True))


class FinancialFigureHistory(models.Model):
    KIND_BUDGET = 'budget_expense'
    # The real model's primary key, named. A stub that lifts the real resolver
    # has to carry the fields that resolver names - and provenance names this
    # one. Django would otherwise supply an implicit `id`, and the lift would
    # die on an attribute the stub never declared.
    financial_figure_history_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32)
    source_pk = models.IntegerField()
    effective_date = models.DateField()
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = '__main__'


for _m in MONTHS:
    FinancialFigureHistory.add_to_class(
        'fh_' + _m, models.DecimalField(max_digits=8, decimal_places=2,
                                        blank=True, null=True))

with connection.schema_editor() as se:
    for m in (props, expense_types, expense_line_types, expense,
              FinancialFigureHistory):
        se.create_model(m)

_FH_MONTHS = ['fh_' + m for m in MONTHS]


# THE RESOLVER IS LIFTED, NOT MIRRORED.
#
# This was a hand-copy of the project's resolver, added with the words "the
# project's own resolver, mirrored field-for-field". It diverged the moment
# the real one gained an optional with_sources argument, and took fourteen
# unrelated checks down with a TypeError. A copy of a thing is not a test of
# the thing.
#
# The real function reads _FH_MONTHS, _fh_date and FinancialFigureHistory out
# of its globals, all of which this module defines, so lifting it is a
# drop-in. It is exec'd just below `lift`, where that helper exists.


def lift(src, name):
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return '\n'.join(src.split('\n')[node.lineno - 1:node.end_lineno])
    return ''


# The project's baseline sentinel. NOT a date: _ensure_baseline writes one
# row at it the first time a long-standing figure is edited, meaning "and it
# held this before anybody recorded a change".
FH_BASELINE_DATE = date(2000, 1, 1)

_MODELS_SRC = os.path.join(ROOT, 'pages', 'models.py')
if not os.path.exists(_MODELS_SRC):
    sys.exit('! pages/models.py not found - run from the project root')
with open(_MODELS_SRC, encoding='utf-8', errors='replace') as _f:
    _MD_SRC = _f.read().replace(chr(13) + chr(10), chr(10))
_res_ns = {'FinancialFigureHistory': FinancialFigureHistory,
           '_FH_MONTHS': _FH_MONTHS, '_fh_date': date}
exec(compile(lift(_MD_SRC, 'resolve_year_months_bulk'), 'resolver', 'exec'),
     _res_ns)
resolve_year_months_bulk = _res_ns['resolve_year_months_bulk']

_ns = {'expense': expense, 'expense_line_types': expense_line_types,
       'props': props, 'FinancialFigureHistory': FinancialFigureHistory,
       'resolve_year_months_bulk': resolve_year_months_bulk,
       'FH_BASELINE_DATE': FH_BASELINE_DATE,
       'Decimal': Decimal, 'date': date, 'MONTHS': MONTHS}
exec(compile(lift(VS, 'expense_matrix'), 'matrix', 'exec'), _ns)
expense_matrix = _ns['expense_matrix']

NOW = 2026


def seed():
    """Company Tax across five years, with three shapes worth drawing.

    Ionion carries throughout; Dikaiosynis carried 2023-24 and was released;
    Spain joined in 2025. Every figure is entered as history so the resolver
    - not the live row - is what produces the table.
    """
    for m in (FinancialFigureHistory, expense, expense_line_types,
              expense_types, props):
        m.objects.all().delete()
    et = expense_types.objects.create(expense_types_name='June')
    lt = expense_line_types.objects.create(expense_line_types_name='Company Tax')
    other = expense_line_types.objects.create(
        expense_line_types_name='Communal fees')
    made = {}
    plan = {
        # name: {year: annual figure}   (spread evenly over twelve months)
        'Ionion - Villa 24': {2023: 1200, 2024: 1200, 2025: 2400,
                              2026: 2400, 2027: 2400},
        'Dikaiosynis':       {2023: 2400, 2024: 2400, 2025: 0,
                              2026: 0, 2027: 0},
        'Spain - Eusebi Guell': {2025: 1200, 2026: 1200, 2027: 1200},
    }
    for name, years in plan.items():
        p = props.objects.create(prop_name=name, prop_status='Active')
        made[name] = p
        e = expense.objects.create(prop=p, expense_types=et,
                                   expense_line_types=lt,
                                   expense_amount=Decimal('100'))
        for y, annual in sorted(years.items()):
            per = Decimal(annual) / 12
            kw = {('fh_' + m): per for m in MONTHS}
            FinancialFigureHistory.objects.create(
                prop=p, kind=FinancialFigureHistory.KIND_BUDGET,
                source_pk=e.expense_id, effective_date=date(y, 1, 1), **kw)
    # A second line type, so the picker has something to pick and the matrix
    # is proved to be filtering rather than showing everything.
    p2 = props.objects.create(prop_name='Palikaridi', prop_status='Active')
    made['Palikaridi'] = p2
    expense.objects.create(prop=p2, expense_types=et, expense_line_types=other,
                           expense_amount=Decimal('50'))
    return made, lt, other


# ===========================================================================
head('2. the figures - resolved from history, and NOT pro-rated')
# ===========================================================================

MADE, LT, OTHER = seed()
M = expense_matrix(LT.expense_line_types_id, today_year=NOW)

check('the years start at the earliest CHANGE and run to NEXT year',
      M['years'] == [2023, 2024, 2025, 2026, 2027], str(M['years']))
check('  which is five columns, not "every year since records began"',
      len(M['years']) == 5)

# THE SENTINEL. FH_BASELINE_DATE is 2000-01-01 and means "and it held this
# before anybody recorded a change" - it reaches back indefinitely, so it
# gives no earliest year at all. The first version of this helper read it as
# data and opened the table on the year 2000 with twenty-eight identical
# columns: one baseline resolved forward a quarter of a century.
_p0 = list(MADE.values())[0]
_e0 = expense.objects.filter(prop=_p0,
                             expense_line_types=LT).first()
FinancialFigureHistory.objects.create(
    prop=_p0, kind=FinancialFigureHistory.KIND_BUDGET,
    source_pk=_e0.expense_id, effective_date=FH_BASELINE_DATE,
    **{('fh_' + m): Decimal('100') for m in MONTHS})
_withbase = expense_matrix(LT.expense_line_types_id, today_year=NOW)
check('A BASELINE STILL DOES NOT OPEN THE TABLE ON 2000',
      _withbase['years'][0] > 2000, str(_withbase['years'][:3]))
# SUPERSEDED, deliberately. It used to assert the range was UNCHANGED by a
# baseline. It is not, any more: the floor is now the earliest snapshot of any
# kind, and a baseline is one - so the table can finally show the year BEFORE
# the first dated change, which is the year the reader needs in order to see
# what the figure changed FROM. Without a baseline that year cannot be
# answered at all and is still excluded.
check('  it opens exactly ONE year earlier, showing what came before',
      _withbase['years'][0] == M['years'][0] - 1,
      '%s vs %s' % (_withbase['years'][0], M['years'][0]))
check('  and gains exactly one column, not a reach back to the sentinel',
      len(_withbase['years']) == len(M['years']) + 1)
check('  CONTROL: the baseline row really is in the database',
      FinancialFigureHistory.objects.filter(
          effective_date=FH_BASELINE_DATE).count() == 1)
# ... and it changes no figure either, for a reason worth stating: the
# resolver takes the LATEST row at or before each month, and every year in
# range already has a later one. A baseline only speaks for the years before
# the first real change - which are precisely the years this table no longer
# draws. The first version of this check expected the totals to MOVE, which
# would have meant the baseline was overriding a later figure.
# Every year the table ALREADY drew reports exactly what it did before: the
# resolver takes the latest row at or before each month, and those years all
# have a later one. The baseline speaks only for the new leading column.
check('  and it changes no figure in any year the table already drew',
      _withbase['totals'][1:] == M['totals'],
      str(_withbase['totals'][:2]))
check('  the new leading column is the one the baseline answers',
      _withbase['totals'][0] is not None)
FinancialFigureHistory.objects.filter(
    effective_date=FH_BASELINE_DATE).delete()

# With nothing but baselines, nothing has ever changed: no past worth a column.
# THE FIXTURE WAS WRONG, and the check passed anyway. It cleared history for
# ONE property, so the line type still had a dated change on a sibling row -
# so "only baselines" was never the case being tested, and `>= 2023` was
# satisfied by the ordinary range. Every dated row on the line has to go.
FinancialFigureHistory.objects.all().delete()
for _e in expense.objects.filter(expense_line_types=LT):
    FinancialFigureHistory.objects.create(
        prop=_e.prop, kind=FinancialFigureHistory.KIND_BUDGET,
        source_pk=_e.expense_id, effective_date=FH_BASELINE_DATE,
        **{('fh_' + m): Decimal('100') for m in MONTHS})
_baseonly = expense_matrix(LT.expense_line_types_id, today_year=NOW)
check('a line type whose only history is baselines starts at the CURRENT year',
      _baseonly['years'][0] == NOW, str(_baseonly['years']))
check('  CONTROL: and there really is no dated change left to open on',
      not FinancialFigureHistory.objects.exclude(
          effective_date=FH_BASELINE_DATE).exists())
MADE, LT, OTHER = seed()
M = expense_matrix(LT.expense_line_types_id, today_year=NOW)

_by = {r['prop_name']: r for r in M['rows']}
check('three properties contribute; the fourth is on another line type',
      sorted(_by) == ['Dikaiosynis', 'Ionion - Villa 24',
                      'Spain - Eusebi Guell'], str(sorted(_by)))
check('  so the matrix really is filtered to ONE line type',
      'Palikaridi' not in _by)

check('a property that carried throughout has a figure in every year',
      all(c is not None for c in _by['Ionion - Villa 24']['cells']))
check('THE RELEASED ONE: figures for 2023-24, then ABSENT',
      [c is not None for c in _by['Dikaiosynis']['cells']]
      == [True, True, False, False, False],
      str(_by['Dikaiosynis']['cells']))
check('  and absent is None, not zero - the whole point of the dash',
      _by['Dikaiosynis']['cells'][2] is None)
check('THE LATE JOINER: absent for 2023-24, then figures',
      [c is not None for c in _by['Spain - Eusebi Guell']['cells']]
      == [False, False, True, True, True])

check('Dikaiosynis carried 2,400 in 2023',
      _by['Dikaiosynis']['cells'][0] == Decimal('2400'),
      str(_by['Dikaiosynis']['cells'][0]))
check('  and its row total is the sum of its own cells',
      _by['Dikaiosynis']['total'] == Decimal('4800'))
for r in M['rows']:
    if not check('  %s: row total equals its own cells' % r['prop_name'],
                 r['total'] == sum((c for c in r['cells'] if c is not None),
                                   Decimal('0'))):
        break

for i, y in enumerate(M['years']):
    _col = sum((r['cells'][i] for r in M['rows'] if r['cells'][i] is not None),
               Decimal('0'))
    if not check('%d: the footer equals its own column (%s)' % (y, _col),
                 M['totals'][i] == _col):
        break
check('the grand total is the sum of the columns',
      M['grand_total'] == sum(M['totals'], Decimal('0')))
check('  and of the rows - the two agree',
      M['grand_total'] == sum((r['total'] for r in M['rows']), Decimal('0')))

# THE DECISION THAT MOVES MONEY.
check('NO PRO-RATING: a full twelve months is counted in every year',
      _by['Ionion - Villa 24']['cells'][2] == Decimal('2400'))
# The DOCSTRING names the pro-rating helper while explaining why the matrix
# does not use it, and ast.unparse includes docstrings - thirteenth instance
# of a check reading prose. Ask the CALLS.
_h = ast.parse(lift(VS, 'expense_matrix')).body[0]
_called = {n.func.id for n in ast.walk(_h)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
check('  and the helper calls no in-service helper at all',
      'property_annual_budgeted_expenses' not in _called,
      str(sorted(_called))[:70])

# The control lives in models.py, not finance.py - that is where the P&L's
# annual helper is. Reading the wrong file made this fail while the thing it
# describes was true all along.
_MODELS = os.path.join(ROOT, 'pages', 'models.py')
if os.path.exists(_MODELS):
    _ms = read(_MODELS)
    check('  CONTROL: the P&L DOES pro-rate, which is why this had to be decided',
          'def property_annual_budgeted_expenses' in _ms
          and 'tenant_lease_start_date' in _ms
          and 'in service' in _ms.lower())
else:
    print('  .. pages/models.py not here, the pro-rating control is skipped')

# A line type nobody carries.
_empty = expense_matrix(OTHER.expense_line_types_id, today_year=NOW)
check('a line type whose only property carries nothing draws no rows',
      _empty['rows'] == [], str(_empty['rows']))
check('  and one nobody has at all comes back empty rather than raising',
      expense_matrix(99999, today_year=NOW)['years'] == [])

# ===========================================================================
head('3. the view wires it up, and did not lose its guards')
# ===========================================================================

_t = ast.parse(VS)
_fns = {n.name: n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef)}
_decs = [getattr(d, 'id', getattr(getattr(d, 'func', None), 'id', ''))
         for d in _fns['finance_expense'].decorator_list]
check('finance_expense keeps @login_required', 'login_required' in _decs)
check('  and @permission_required', 'permission_required' in _decs)
check('expense_matrix carries NO decorator - it is a helper',
      not _fns['expense_matrix'].decorator_list)
_fe = ast.unparse(_fns['finance_expense'])
check('the view only builds the matrix when it is being looked at',
      re.search(r"if view_mode == 'matrix'", _fe) is not None)
check('  the mode comes from the URL, so the view can be linked and reloaded',
      "request.GET.get('view')" in _fe)
check('  an unknown lt falls back to the first, rather than 500ing',
      'matrix_line_types[0]' in _fe)

# ===========================================================================
head('4. rendered - and the frozen column actually freezes')
# ===========================================================================

from django.template import engines                            # noqa: E402


class Row(dict):
    __getattr__ = dict.get


def render(view_mode='matrix'):
    return engines['django'].get_template('finance_expense.html').render({
        'perms': {'auth': {'can_access_financials': True,
                           'can_edit_financials': True}},
        'props_data': [],
        'messages': [],
        'view_mode': view_mode,
        'matrix': M if view_mode == 'matrix' else None,
        'matrix_line_types': [LT, OTHER],
        'selected_lt': LT.expense_line_types_id,
        'csrf_token': 'test-token',
    })


HTML = render()
check('the matrix view renders', 'alv-matrix-scroll' in HTML)
check('  with a segmented control, current segment marked',
      'alv-seg' in HTML and 'aria-current="page"' in HTML)
check('  and a picker holding both line types',
      HTML.count('<option') == 2)
# Counted from the DATA, not pinned to a literal. The first version of this
# asserted 4 and the data had 5 - the hardcoded number was wrong while the
# derived one beside it was right, which is the argument for deriving it.
_gaps = sum(1 for r in M['rows'] for c in r['cells'] if c is None)
check('a dash is drawn for every absent cell (%d)' % _gaps,
      HTML.count('alv-matrix-absent') == _gaps,
      str(HTML.count('alv-matrix-absent')))
check('  and there ARE gaps, so that check is not passing on an empty set',
      _gaps > 0)
check('  no cell renders a bare 0.00 - absent is absent, not zero',
      not re.search(r'<td>0\.00</td>', HTML))
check('the note says the figures are not pro-rated',
      'not pro-rated' in HTML and 'P&amp;L pro-rates' in HTML)
check('  and says what a dash means',
      'not that it cost nothing' in HTML)
check('the by-property view still renders', 'alv-matrix-scroll'
      not in render(view_mode='property'))

_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S))

try:
    from playwright.sync_api import sync_playwright
except Exception:                                          # pragma: no cover
    sync_playwright = None

if sync_playwright is None:
    print('  .. Playwright unavailable - the scroll measurement is SKIPPED,')
    print('     which is the only check here that can tell sticky from decoration.')
else:
    _table = re.search(r'(<div class="alv-matrix-scroll".*?</table>\s*</div>)',
                       HTML, re.S)
    check('the matrix markup could be cut out to render', _table is not None)
    if _table:
        HARNESS = ("""<!doctype html><meta charset="utf-8"><style>%s
        body { margin: 0; } .alv-matrix-scroll { width: 420px; }</style>
        <body>%s</body>""" % (_css, _table.group(1)))
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False,
                                         encoding='utf-8') as f:
            f.write(HARNESS)
            _p = f.name
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg_ = br.new_page(viewport={'width': 900, 'height': 600})
            pg_.goto('file://' + _p)
            r = pg_.evaluate("""() => {
                const box = document.querySelector('.alv-matrix-scroll');
                const head = document.querySelector('td.alv-matrix-row-head');
                const tot  = document.querySelector('td.alv-matrix-total');
                const at0  = head.getBoundingClientRect().left;
                const t0   = tot.getBoundingClientRect().right;
                const wide = box.scrollWidth > box.clientWidth;
                box.scrollLeft = 600;
                return {wide, at0, t0,
                        at1: head.getBoundingClientRect().left,
                        t1:  tot.getBoundingClientRect().right,
                        scrolled: box.scrollLeft,
                        sticky: getComputedStyle(head).position,
                        overflow: getComputedStyle(box).overflowX};
            }""")
            br.close()
        os.unlink(_p)

        check('the table is WIDER than its box - there is something to scroll',
              r['wide'] is True)
        check('  and it really scrolled (%dpx)' % r['scrolled'],
              r['scrolled'] > 0)
        check('THE PROPERTY COLUMN STAYED PUT (%0.0f -> %0.0f)'
              % (r['at0'], r['at1']), abs(r['at0'] - r['at1']) < 1)
        check('  and so did the Total column (%0.0f -> %0.0f)'
              % (r['t0'], r['t1']), abs(r['t0'] - r['t1']) < 1)
        check('  computed position really is sticky, not just declared',
              r['sticky'] == 'sticky', r['sticky'])
        check('  on a box that really does scroll sideways',
              r['overflow'] == 'auto', r['overflow'])

# ===========================================================================
print('\n' + '=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for n in FAILED:
        print('   FAILED: %s' % n)
print('=' * 72)
sys.exit(1 if FAIL else 0)
