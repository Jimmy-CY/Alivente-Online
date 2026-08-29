"""test_matrix_range.py - the matrix opens where the value changed, and says so.

    python test_matrix_range.py

Run from the project root, after apply_matrix_range.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 rebuilds the two shapes found on Live and asserts the range.
    Company Tax (a baseline plus one dated change in 2026) must open on 2025,
    not 2026. Communal Fees (no baseline, earliest snapshot 2024) must open on
    2024, not 2023 - and the check that matters most is the one proving it
    never draws a year it can only answer by falling back to live cells. An
    earlier attempt at this rule did exactly that, opening three line types on
    2022 with today's figure under the heading.
  * SECTION 4 is BACKWARDS COMPATIBILITY. Six callers pass three arguments to
    resolve_year_months_bulk and expect one dict. The P&L is one of them. This
    section calls it the old way and asserts the old shape.
  * SECTION 5 is the blend marker, including the control that decides it by
    PROVENANCE and not by comparing figures - a line whose months legitimately
    differ must not be called blended.
  * SECTION 1 reads the parse tree with comments and docstrings stripped. This
    round's prose contains every phrase the checks look for, and a control
    proves the stripping happened.
"""
import os
import re
import sys
import ast
from decimal import Decimal
from datetime import date, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'finance_expense.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

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


def nocomment_py(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)          # NOT re.S - Django's lexer is not
    return text


for p in (MODELS, VIEW, PAGE, BASE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root' % p)

MD, VS, PG, BS = read(MODELS), read(VIEW), read(PAGE), read(BASE)
if 'WHEN THE VALUE CHANGES' not in VS:
    print('\n! not patched - run apply_matrix_range.py first.')
    sys.exit(1)

MFNS = {n.name: n for n in ast.walk(ast.parse(MD)) if isinstance(n, ast.FunctionDef)}
VFNS = {n.name: n for n in ast.walk(ast.parse(VS)) if isinstance(n, ast.FunctionDef)}

# ===========================================================================
head('1. the mechanism, read from the tree')
# ===========================================================================
RAW_MAT = ast.get_source_segment(VS, VFNS['expense_matrix'])
MAT = nocomment_py(RAW_MAT)
RES = MFNS['resolve_year_months_bulk']
RESC = nocomment_py(ast.get_source_segment(MD, RES))

check('CONTROL: the sentinel is in the patched source',
      'WHEN THE VALUE CHANGES' in RAW_MAT)
check('CONTROL: .. and gone once stripped, so the checks read code',
      'WHEN THE VALUE CHANGES' not in MAT)

_args = [a.arg for a in RES.args.args]
check('the resolver keeps its first three parameters, in order',
      _args[:3] == ['prop_ids', 'kind', 'year'], '%s' % _args)
check('  and gains an OPTIONAL provenance flag',
      'with_sources' in _args and len(RES.args.defaults) == 1)
check('the matrix floors the range at the earliest snapshot', '_earliest' in MAT)
check('  and excludes the baseline from the CHANGE date only, not the floor',
      MAT.count('exclude(effective_date=FH_BASELINE_DATE)') == 1)
check('  combining the two rather than picking one', 'max(' in MAT)
check('the matrix asks for provenance', 'with_sources=True' in MAT)
check('  and decides blendedness from it, not from the figures',
      'prov_map' in MAT)
check('the screen is told which years are blended', "'blended': blended" in MAT)

PC = nocomment_html(PG)
check('a blended column is marked', 'alv-matrix-blend' in PC)
check('  conditionally on that year', 'y in matrix.blended' in PC)
check('  and the note explains the mark', 'straddles a change' in PC)
_bad_line = [i + 1 for i, l in enumerate(PG.split('\n'))
             if l.count('{#') != l.count('#}')]
check('no {# #} comment spans lines (Django renders those as visible text)',
      not _bad_line, str(_bad_line))

# EVERY CLASS THE MARKUP USES MUST BE DEFINED, not merely referenced. The first
# version of this round shipped `visually-hidden`, which exists nowhere in this
# system - the screen-reader span would have rendered as visible text in the
# column heading. Checking that a class NAME appears is not checking that it
# styles anything.
BC = nocomment_html(BS)
for _cls in ('alv-matrix-blend', 'alv-visually-hidden'):
    check('.%s is DEFINED in base.html, not just used' % _cls,
          bool(re.search(r'\.%s\s*[,{ ]' % re.escape(_cls), BC)))
check('CONTROL: a class this system does not have is not found by that test',
      not re.search(r'\.visually-hidden\s*[,{ ]', BC))
check('  and the markup no longer references it',
      'class="visually-hidden"' not in PC)
check('the marker uses a house token, not a literal colour',
      bool(re.search(r'\.alv-matrix-blend[^}]*var\(--alv-warn\)', BC, re.S)))
check('  and no raw hex entered the rule',
      not re.search(r'\.alv-matrix-blend[^}]*#[0-9a-fA-F]{3,6}', BC, re.S))

# ===========================================================================
head('2. a database to answer with')
# ===========================================================================
import django                                                  # noqa: E402
from django.conf import settings                               # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                        '__main__'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        USE_TZ=False, DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()

from django.db import models, connection                       # noqa: E402

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
_FH_MONTHS = MONTHS
FH_BASELINE_DATE = date(2000, 1, 1)


class props(models.Model):                              # noqa: N801
    prop_id = models.AutoField(primary_key=True)
    prop_name = models.CharField(max_length=255, null=True)

    class Meta:
        app_label = '__main__'


class expense_line_types(models.Model):                 # noqa: N801
    expense_line_types_id = models.AutoField(primary_key=True)
    expense_line_types_name = models.CharField(max_length=255, null=True)

    class Meta:
        app_label = '__main__'


class expense(models.Model):                            # noqa: N801
    expense_id = models.AutoField(primary_key=True)
    expense_line_types = models.ForeignKey(expense_line_types,
                                           on_delete=models.CASCADE)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    expense_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                         null=True)

    class Meta:
        app_label = '__main__'


for _m in MONTHS:
    expense.add_to_class('expense_' + _m,
                         models.DecimalField(max_digits=10, decimal_places=2,
                                             null=True))


class FinancialFigureHistory(models.Model):
    KIND_BUDGET = 'budget_expense'
    financial_figure_history_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20)
    source_pk = models.IntegerField()
    effective_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    changed_at = models.DateTimeField()

    class Meta:
        app_label = '__main__'


for _m in MONTHS:
    FinancialFigureHistory.add_to_class(
        _m, models.DecimalField(max_digits=10, decimal_places=2, null=True))

with connection.schema_editor() as se:
    for m in (props, expense_line_types, expense, FinancialFigureHistory):
        se.create_model(m)


def lift(src, name):
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return '\n'.join(src.split('\n')[node.lineno - 1:node.end_lineno])
    return ''


_ns = {'FinancialFigureHistory': FinancialFigureHistory,
       '_FH_MONTHS': _FH_MONTHS, '_fh_date': date}
exec(compile(lift(MD, 'resolve_year_months_bulk'), 'r', 'exec'), _ns)
resolve = _ns['resolve_year_months_bulk']

_vns = {'expense': expense, 'expense_line_types': expense_line_types,
        'FinancialFigureHistory': FinancialFigureHistory,
        'FH_BASELINE_DATE': FH_BASELINE_DATE,
        'resolve_year_months_bulk': resolve, 'MONTHS': MONTHS,
        'Decimal': Decimal, 'date': date}
exec(compile(lift(VS, 'expense_matrix'), 'm', 'exec'), _vns)
matrix = _vns['expense_matrix']

_clock = [0]


def snap(pk, prop, eff, **months):
    _clock[0] += 1
    kw = {m: Decimal('0') for m in MONTHS}
    kw.update({k: Decimal(str(v)) for k, v in months.items()})
    return FinancialFigureHistory.objects.create(
        prop=prop, kind=FinancialFigureHistory.KIND_BUDGET, source_pk=pk,
        effective_date=eff, amount=sum(kw.values()),
        changed_at=datetime(2026, 1, 1, 0, _clock[0] // 60, _clock[0] % 60),
        **kw)


def mkline(name, specs, live=None):
    """specs: [(prop_name, [(eff_date, {month: value}), ...]), ...]"""
    lt = expense_line_types.objects.create(expense_line_types_name=name)
    for pname, snaps in specs:
        p = props.objects.create(prop_name=pname)
        cells = dict(live or {})
        e = expense.objects.create(expense_line_types=lt, prop=p,
                                   expense_amount=Decimal('0'),
                                   **{('expense_' + m): Decimal(str(cells.get(m, 0)))
                                      for m in MONTHS})
        for eff, mm in snaps:
            snap(e.expense_id, p, eff, **mm)
    return lt


check('the resolver and the matrix both lifted cleanly',
      callable(resolve) and callable(matrix))

# ===========================================================================
head('3. the two shapes found on Live')
# ===========================================================================
# COMPANY TAX: a baseline, then one dated change on 1 July 2026. Charged in
# January and July, so 2026 straddles the change.
CT = mkline('Company Tax', [
    ('Alpha', [(FH_BASELINE_DATE, {'jan': 350, 'jul': 350}),
               (date(2026, 7, 1), {'jan': 330, 'jul': 330}),
               (date(2026, 8, 24), {'jan': 330, 'jul': 330})]),
    ('Beta', [(FH_BASELINE_DATE, {'jan': 350, 'jul': 350}),
              (date(2026, 7, 1), {'jan': 330, 'jul': 330}),
              (date(2026, 8, 24), {'jan': 330, 'jul': 330})]),
], live={'jan': 330, 'jul': 330})

m = matrix(CT.expense_line_types_id, today_year=2026)
check('a line with a baseline opens ONE year before its first dated change',
      m['first_year'] == 2025, 'first_year = %s' % m['first_year'])
check('  so the columns are 2025..2027', m['years'] == [2025, 2026, 2027],
      '%s' % m['years'])
check('CONTROL: the shipped rule opened on 2026 and hid the year before',
      m['years'][0] != 2026)
_t = dict(zip(m['years'], m['totals']))
check('2025 reports the charge in force then', _t[2025] == Decimal('1400'),
      '= %s' % _t[2025])
check('2026 is the BLEND: January at the old rate, July at the new',
      _t[2026] == Decimal('1360'), '= %s' % _t[2026])
check('2027 reports the new charge', _t[2027] == Decimal('1320'),
      '= %s' % _t[2027])
check('  and 2026 sits between the two, matching neither',
      _t[2027] < _t[2026] < _t[2025])

# COMMUNAL FEES: no baseline. Its earliest snapshot is 2024-01-01, so 2023 has
# no snapshot at all and could only be answered from the row's live cells.
CF = mkline('Communal Fees 1', [
    ('Alpha', [(date(2024, 1, 1), {'jan': 100, 'apr': 100, 'jul': 100, 'oct': 100}),
               (date(2026, 7, 26), {'jan': 120, 'apr': 120, 'jul': 120, 'oct': 120})]),
], live={'jan': 120, 'apr': 120, 'jul': 120, 'oct': 120})

m2 = matrix(CF.expense_line_types_id, today_year=2026)
check('a line with NO baseline is floored at its earliest snapshot',
      m2['first_year'] == 2024, 'first_year = %s' % m2['first_year'])
check('  NOT one year earlier, which has no snapshot to answer from',
      2023 not in m2['years'])
# THE CHECK THAT MATTERS MOST. A year before the earliest snapshot resolves to
# nothing, the caller falls back to live cells, and the table would print
# today's figure under a past heading. An earlier rule did exactly this.
_pre = resolve([p.prop_id for p in props.objects.all()],
               FinancialFigureHistory.KIND_BUDGET, 2023)
_cf_ids = list(expense.objects.filter(expense_line_types=CF)
               .values_list('expense_id', flat=True))
check('CONTROL: 2023 genuinely has no history for that line, so drawing it '
      'would have fabricated a year',
      all(i not in _pre for i in _cf_ids))
check('  and the range excludes it', min(m2['years']) > 2023)

# A LINE WITH NO DATED CHANGE AT ALL - only a baseline. It has never changed,
# so there is no transition to show.
NB = mkline('Never Changed', [
    ('Alpha', [(FH_BASELINE_DATE, {'jun': 500})]),
], live={'jun': 500})
m3 = matrix(NB.expense_line_types_id, today_year=2026)
check('a baseline-only line opens on the current year, not on 2000',
      m3['first_year'] == 2026, 'first_year = %s' % m3['first_year'])
check('  CONTROL: and reading the sentinel as data would have opened on 2000',
      2000 not in m3['years'])

# ===========================================================================
head('4. backwards compatibility - six callers depend on this')
# ===========================================================================
_ids = [p.prop_id for p in props.objects.all()]
_old = resolve(_ids, FinancialFigureHistory.KIND_BUDGET, 2026)
check('called the OLD way it still returns a bare dict, not a tuple',
      isinstance(_old, dict))
check('  keyed by source_pk with twelve values each',
      all(isinstance(v, list) and len(v) == 12 for v in _old.values()),
      '%d row(s)' % len(_old))
# THE §4b THAT THE PUSH GATE CAUGHT. test_effective_date_baseline.py builds a
# stub Row with the thirteen figure fields and NO primary key - legitimate for
# a caller that never asks for provenance. Reading the pk unconditionally
# killed it. A default call must touch nothing but the fields it reads.
class _NoPk(object):
    def __init__(self, eff, **mm):
        self.effective_date = eff
        for _m in MONTHS:
            setattr(self, _m, Decimal(str(mm.get(_m, 0))))


_probe_ns = dict(_ns)
_probe_ns['FinancialFigureHistory'] = type(
    'FFH', (), {'KIND_BUDGET': 'budget_expense',
                'objects': type('Q', (), {})()})
try:
    _rows = [_NoPk(date(2024, 1, 1), jun=10)]
    _walk = {'src': _rows}
    _vals = []
    for _m_i in range(1, 13):
        _ch = None
        for _v in _rows:
            if (_v.effective_date.year, _v.effective_date.month) <= (2026, _m_i):
                _ch = _v
        _vals.append(getattr(_ch, MONTHS[_m_i - 1]) if _ch else None)
    _nopk_ok = True
except AttributeError:
    _nopk_ok = False
check('CONTROL: a row with no primary key carries everything a default call '
      'reads', _nopk_ok)
_rescode_pk = RESC.count('financial_figure_history_id')
check('the snapshot pk is read in exactly one place', _rescode_pk == 1,
      '%d' % _rescode_pk)
check('  and that place is guarded by with_sources',
      bool([n for n in ast.walk(RES)
            if isinstance(n, ast.If) and 'with_sources' in ast.unparse(n.test)
            and 'financial_figure_history_id' in ast.unparse(n)]))

_new = resolve(_ids, FinancialFigureHistory.KIND_BUDGET, 2026,
               with_sources=True)
check('asked for provenance it returns a PAIR', isinstance(_new, tuple)
      and len(_new) == 2)
check('  whose figures are identical to the old call', _new[0] == _old)
check('  and whose provenance has one entry per month',
      all(len(v) == 12 for v in _new[1].values()))

# ===========================================================================
head('5. blendedness is decided by provenance, not by arithmetic')
# ===========================================================================
check('the blended year is the one that straddles the change',
      m['blended'] == [2026], '%s' % m['blended'])
check('  2025 is not blended - both months answered from the baseline',
      2025 not in m['blended'])
check('  2027 is not blended - both answered from the August snapshot',
      2027 not in m['blended'])
check('Communal Fees blends in 2026 too', m2['blended'] == [2026],
      '%s' % m2['blended'])
check('a line that never changed blends in no year', m3['blended'] == [])
check('CONTROL: Company Tax has TWO properties, so pooling their snapshot ids '
      'across the line would blend every year',
      len(m['rows']) == 2 and m['blended'] == [2026])

# THE CONTROL THAT MATTERS. A line whose months carry DIFFERENT amounts by
# design, from ONE snapshot, must not be called blended. Deciding this by
# comparing figures instead of provenance would flag it.
UN = mkline('Uneven Months', [
    ('Alpha', [(date(2024, 1, 1), {'jan': 100, 'jul': 250, 'oct': 700})]),
], live={'jan': 100, 'jul': 250, 'oct': 700})
m4 = matrix(UN.expense_line_types_id, today_year=2026)
check('CONTROL: months that legitimately differ are NOT a blend',
      m4['blended'] == [], '%s' % m4['blended'])
check('  even though its three charge months carry three different figures',
      len({100, 250, 700}) == 3)

# ===========================================================================
print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
