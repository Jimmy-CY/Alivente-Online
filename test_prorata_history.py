"""test_prorata_history - does a pro-rata edit still lose its history?

    python test_prorata_history.py

Everything under test is lifted verbatim out of the tree and exec'd against a
stub ORM, so this exercises what ships rather than a re-implementation:

    from pages/views/finance.py   finance_expense_edit_commit
                                  _fh_save_expense, _fh_new_expense,
                                  _fh_close_expense
    from pages/models.py          _ensure_baseline, ensure_expense_baseline,
                                  _open_baseline, ensure_expense_opening,
                                  record_expense_history,
                                  resolve_year_months_bulk

The example is the real one: Company Tax, Six Monthly (January + July),
pro-rated by current value across four properties. 3,500 an instalment =
7,000 a year, changing to 3,300 = 6,600, effective 1 July 2026. Every row
starts with a seed snapshot at 2024-01-01, exactly as Live has.

    Palikaridi        300,000        Pindarou          200,000
    Foti Pitta        300,000        Ionion Villa 24   200,000
    (Athens First     250,000  - only in the "added" scenarios)

Five scenarios, then the four date cases for a newly created row.
"""

import json
import os
import re
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')

for p in (MODELS, FINANCE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

MODELS_SRC = open(MODELS, encoding='utf-8').read().replace('\r\n', '\n')
FIN_SRC = open(FINANCE, encoding='utf-8').read().replace('\r\n', '\n')

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
PAY = ['jan', 'jul']
KIND = 'budget_expense'
EFF = date(2026, 7, 1)
YEARS = [2024, 2025, 2026, 2027]

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def grab(src, name, where):
    m = re.search(r'^def %s\(.*?\n(?=\S)' % re.escape(name), src, re.S | re.M)
    if not m:
        sys.exit('! %s not found in %s - has the patch been applied?'
                 % (name, where))
    return m.group(0)


# ============================================================== the stub ORM
_clock = [0]
HISTORY = []
EXPENSES = []
COMMITS = []
MESSAGES = []


class HRow:
    def __init__(self, **kw):
        prop = kw.pop('prop', None)
        if prop is None:
            raise ValueError('prop_id cannot be NULL')
        self.prop_id = prop.pk
        for k, v in kw.items():
            setattr(self, k, v)
        for m in MONTHS:
            if not hasattr(self, m):
                setattr(self, m, None)
        _clock[0] += 1
        self.changed_at = datetime(2026, 1, 1) .replace(microsecond=_clock[0])


class HQS(list):
    def filter(self, **kw):
        out = self
        if 'prop_id__in' in kw:
            out = HQS(r for r in out if r.prop_id in kw['prop_id__in'])
        if 'kind' in kw:
            out = HQS(r for r in out if r.kind == kw['kind'])
        if 'source_pk' in kw:
            out = HQS(r for r in out if r.source_pk == kw['source_pk'])
        if 'effective_date__lte' in kw:
            out = HQS(r for r in out if r.effective_date <= kw['effective_date__lte'])
        return out

    def order_by(self, *keys):
        cur = list(self)
        for k in reversed(keys):
            cur = sorted(cur, key=lambda r, k=k: getattr(r, k))
        return HQS(cur)

    def exists(self):
        return len(self) > 0


class HManager:
    def filter(self, **kw):
        return HQS(HISTORY).filter(**kw)

    def create(self, **kw):
        r = HRow(**kw)
        HISTORY.append(r)
        return r


class FFH:
    objects = HManager()
    KIND_BUDGET = KIND
    KIND_REVENUE = 'revenue'


class Prop:
    def __init__(self, pk, name, value):
        self.pk, self.prop_name, self.value = pk, name, value

    def __str__(self):
        return self.prop_name


PROPS = {
    1: Prop(1, 'Palikaridi', 300000),
    2: Prop(2, 'Foti Pitta', 300000),
    3: Prop(3, 'Pindarou', 200000),
    4: Prop(4, 'Ionion Villa 24', 200000),
    5: Prop(5, 'Athens First', 250000),
}
BASE = [1, 2, 3, 4]


class ExpRow:
    _next = [500]

    def __init__(self, **kw):
        self.expense_id = ExpRow._next[0]
        ExpRow._next[0] += 1
        self.alive = True
        self.prop_id = kw.get('prop_id')
        self.expense_line_types_id = kw.get('expense_line_types_id')
        self.expense_types_id = kw.get('expense_types_id')
        self.expense_amount = kw.get('expense_amount')
        for m in MONTHS:
            setattr(self, 'expense_' + m, kw.get('expense_' + m))
        self.saves = 0

    @property
    def prop(self):
        return PROPS[self.prop_id]

    @property
    def expense_line_types(self):
        return 'Company Tax'

    def save(self):
        self.saves += 1


class EQS(list):
    def filter(self, **kw):
        out = EQS(r for r in self if r.alive)
        for k, v in kw.items():
            out = EQS(r for r in out if getattr(r, k) == v)
        return out

    def order_by(self, *keys):
        cur = list(self)
        for k in reversed(keys):
            cur = sorted(cur, key=lambda r, k=k: getattr(r, k))
        return EQS(cur)

    def values_list(self, field, flat=False):
        return [getattr(r, field) for r in self]

    def delete(self):
        for r in self:
            r.alive = False


class EManager:
    def filter(self, **kw):
        return EQS(EXPENSES).filter(**kw)

    def get(self, **kw):
        hit = self.filter(**kw)
        if not hit:
            raise ExpModel.DoesNotExist()
        return hit[0]

    def create(self, **kw):
        r = ExpRow(**kw)
        EXPENSES.append(r)
        return r


class ExpModel:
    objects = EManager()

    class DoesNotExist(Exception):
        pass


class ExpType:
    """Six Monthly: January and July."""
    expense_types_id = 9
    def __init__(self):
        for m in MONTHS:
            setattr(self, 'expense_types_' + m, 'Yes' if m in PAY else 'No')

    def __str__(self):
        return 'Six Monthly'


class ETManager:
    def get(self, **kw):
        return ExpType()


class ExpTypesModel:
    objects = ETManager()

    class DoesNotExist(Exception):
        pass


class _Atomic:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Transaction:
    @staticmethod
    def atomic():
        return _Atomic()

    @staticmethod
    def on_commit(fn):
        COMMITS.append(fn)


class _Messages:
    @staticmethod
    def error(request, msg):
        MESSAGES.append(('error', msg))

    @staticmethod
    def success(request, msg):
        MESSAGES.append(('success', msg))


class Request:
    def __init__(self, post):
        self.method = 'POST'
        self.POST = post
        self.user = None


def redirect(name, **kw):
    return 'redirect:' + name


class _Logger:
    @staticmethod
    def exception(*a, **k):
        pass


# ============================================================ lift the code
NS = {
    'FinancialFigureHistory': FFH,
    '_fh_date': date,
    '_FH_MONTHS': MONTHS,
    '_fh_log': type('L', (), {'exception': staticmethod(lambda *a, **k: None)})(),
    'FH_BASELINE_DATE': date(2000, 1, 1),
    'Decimal': Decimal,
}
for name in ('_ensure_baseline', 'ensure_expense_baseline',
             '_open_baseline', 'ensure_expense_opening',
             'record_expense_history', 'resolve_year_months_bulk'):
    exec(compile(grab(MODELS_SRC, name, 'models.py'), name, 'exec'), NS)

resolve = NS['resolve_year_months_bulk']

VIEW_NS = {
    'expense': ExpModel,
    'expense_types': ExpTypesModel,
    'transaction': _Transaction,
    'messages': _Messages,
    'redirect': redirect,
    'json': json,
    'MONTHS': MONTHS,
    'logger': _Logger,
    'ensure_expense_baseline': NS['ensure_expense_baseline'],
    'ensure_expense_opening': NS['ensure_expense_opening'],
    'record_expense_history': NS['record_expense_history'],
    '_fh_eff_date': lambda request: date(*[int(x) for x in
                                           request.POST['effective_date'].split('-')]),
    '_fh_user': lambda request: None,
}
for name in ('_fh_save_expense', '_fh_new_expense', '_fh_close_expense',
             'finance_expense_edit_commit'):
    exec(compile(grab(FIN_SRC, name, 'finance.py'), name, 'exec'), VIEW_NS)

edit_commit = VIEW_NS['finance_expense_edit_commit']


# ================================================================ the world
def distribute(instalment, prop_ids):
    total = sum(PROPS[p].value for p in prop_ids)
    out, running, q = {}, Decimal('0'), Decimal('0.01')
    for p in prop_ids:
        share = (Decimal(instalment) * Decimal(PROPS[p].value) / Decimal(total))
        out[p] = share.quantize(q, rounding=ROUND_HALF_UP)
        running += out[p]
    if running != Decimal(instalment):
        out[max(prop_ids, key=lambda p: PROPS[p].value)] += Decimal(instalment) - running
    return out


def reset():
    del HISTORY[:]
    del EXPENSES[:]
    del COMMITS[:]
    del MESSAGES[:]
    ExpRow._next[0] = 500
    amounts = distribute(3500, BASE)
    for p in BASE:
        kw = {'prop_id': p, 'expense_line_types_id': 7, 'expense_types_id': 9,
              'expense_amount': amounts[p]}
        for m in MONTHS:
            kw['expense_' + m] = amounts[p] if m in PAY else None
        row = ExpModel.objects.create(**kw)
        NS['record_expense_history'](row, date(2024, 1, 1), source='seed')
    return amounts


def run_edit(instalment, selected, eff=EFF):
    """POST the pro-rata edit form, then flush the on_commit hooks."""
    amounts = distribute(instalment, selected)
    payload = {'selected_properties': [
        {'prop_id': p, 'calculated_amount': float(amounts[p])} for p in selected]}
    anchor = EQS(EXPENSES).filter(prop_id=selected[0])[0]
    request = Request({
        'prop': str(anchor.prop_id),
        'expense_line_types': 7,
        'expense_types': 9,
        'expense_amount': str(instalment),
        'effective_date': eff.isoformat(),
        'prorata_calculation_data': json.dumps(payload),
    })
    out = edit_commit(request, anchor.expense_id)
    for fn in list(COMMITS):
        fn()
    del COMMITS[:]
    return out


def year_total(year):
    live = [e for e in EXPENSES if e.alive]
    resolved = resolve([p for p in PROPS], KIND, year)
    total = Decimal('0')
    for e in live:
        vals = resolved.get(e.expense_id)
        if vals is None:
            vals = [getattr(e, 'expense_' + m) for m in MONTHS]
        total += sum(Decimal(str(v)) for v in vals if v is not None)
    return total.quantize(Decimal('0.01'))


def prop_year(prop_id, year):
    resolved = resolve([p for p in PROPS], KIND, year)
    total = Decimal('0')
    for e in EXPENSES:
        if not e.alive or e.prop_id != prop_id:
            continue
        vals = resolved.get(e.expense_id)
        if vals is None:
            vals = [getattr(e, 'expense_' + m) for m in MONTHS]
        total += sum(Decimal(str(v)) for v in vals if v is not None)
    return total.quantize(Decimal('0.01'))


def eq(a, b):
    return Decimal(str(a)).quantize(Decimal('0.01')) == Decimal(str(b)).quantize(Decimal('0.01'))


def orphans():
    live = {e.expense_id for e in EXPENSES if e.alive}
    return [h for h in HISTORY if h.kind == KIND and h.source_pk not in live]


# ================================================================ SCENARIO 1
reset()
ids_before = sorted(e.expense_id for e in EXPENSES)
run_edit(3300, BASE)
ids_after = sorted(e.expense_id for e in EXPENSES if e.alive)

check('1. every expense_id survives the edit', ids_before == ids_after)
check('1. no history orphaned', not orphans())
for y, want in ((2024, 7000), (2025, 7000), (2026, 6800), (2027, 6600)):
    check('1. %d = %s' % (y, '{:,}'.format(want)), eq(year_total(y), want))
check('1. no baseline written (the seed already covers it)',
      not [h for h in HISTORY if h.source == 'baseline'])
check('1. the new snapshots are tagged prorata',
      len([h for h in HISTORY if h.source == 'prorata']) == 4)

# ================================================================ SCENARIO 2
reset()
run_edit(3500, [1, 2, 3])
check('2. Ionion is zeroed, not deleted',
      any(e.alive and e.prop_id == 4 for e in EXPENSES))
check('2. no history orphaned', not orphans())
check('2. Ionion keeps its January 2026 payment', eq(prop_year(4, 2026), 700))
check('2. Ionion contributes nothing in 2027', eq(prop_year(4, 2027), 0))
check('2. Ionion still shows 1,400 in 2024', eq(prop_year(4, 2024), 1400))
for y in YEARS:
    check('2. %d = 7,000 (nothing lost, nothing invented)' % y,
          eq(year_total(y), 7000))

# ================================================================ SCENARIO 3
reset()
run_edit(3500, BASE + [5])
check('3. Athens First was created', any(e.alive and e.prop_id == 5 for e in EXPENSES))
check('3. no history orphaned', not orphans())
check('3. Athens gets an opening snapshot',
      [h for h in HISTORY if h.source == 'opening' and h.effective_date == date(2000, 1, 1)])
check('3. Athens is absent from 2024', eq(prop_year(5, 2024), 0))
check('3. Athens joins in July 2026', eq(prop_year(5, 2026), 700))
check('3. Athens carries a full year in 2027', eq(prop_year(5, 2027), 1400))
for y in YEARS:
    check('3. %d = 7,000 (adding a property does not inflate the past)' % y,
          eq(year_total(y), 7000))

# ================================================================ SCENARIO 4
reset()
run_edit(3300, [1, 2, 3])
check('4. no history orphaned', not orphans())
check('4. Ionion keeps its January 2026 payment', eq(prop_year(4, 2026), 700))
for y, want in ((2024, 7000), (2025, 7000), (2026, 6800), (2027, 6600)):
    check('4. %d = %s' % (y, '{:,}'.format(want)), eq(year_total(y), want))

# ================================================================ SCENARIO 5
reset()
run_edit(3300, BASE + [5])
check('5. no history orphaned', not orphans())
check('5. Athens is absent from 2024', eq(prop_year(5, 2024), 0))
for y, want in ((2024, 7000), (2025, 7000), (2026, 6800), (2027, 6600)):
    check('5. %d = %s' % (y, '{:,}'.format(want)), eq(year_total(y), want))

# ====================================================== THE ORIGINAL FAILURE
# The row edited through the pro-rata screen must keep the money it held
# before. This is the incident, replayed end to end.
reset()
run_edit(3300, BASE)
check('!! the 7,000 survives a pro-rata edit (2025)', eq(year_total(2025), 7000))
check('!! 2026 blends rather than blanking', eq(year_total(2026), 6800))

# ============================================ A LINE TYPE CHANGE MOVES A GROUP
reset()
amounts = distribute(3300, BASE)
payload = {'selected_properties': [
    {'prop_id': p, 'calculated_amount': float(amounts[p])} for p in BASE]}
anchor = EQS(EXPENSES).filter(prop_id=1)[0]
edit_commit(Request({
    'prop': '1', 'expense_line_types': 99, 'expense_types': 9,
    'expense_amount': '3300', 'effective_date': EFF.isoformat(),
    'prorata_calculation_data': json.dumps(payload),
}), anchor.expense_id)
for fn in list(COMMITS):
    fn()
del COMMITS[:]
moved = [e for e in EXPENSES if e.alive and e.expense_line_types_id == 99]
left = [e for e in EXPENSES if e.alive and e.expense_line_types_id == 7]
check('6. the group moved to the new line type', len(moved) == 4)
check('6. the old rows were kept, not deleted', len(left) == 4)
check('6. the old rows were zeroed',
      all(all(getattr(e, 'expense_' + m) in (0, None) for m in MONTHS) for e in left))
check('6. no history orphaned by the move', not orphans())

# ==================================================== THE FOUR DATE CASES
# A brand new row, 100 a month, created on 22 Aug 2026 - only the date typed
# into "Applies from" differs. Exercises _fh_new_expense + the resolver.
def date_case(eff):
    del HISTORY[:]
    del EXPENSES[:]
    ExpRow._next[0] = 900
    kw = {'prop_id': 1, 'expense_line_types_id': 7, 'expense_types_id': 9,
          'expense_amount': 100}
    for m in MONTHS:
        kw['expense_' + m] = 100
    row = ExpModel.objects.create(**kw)
    VIEW_NS['_fh_new_expense'](row, eff, None, 'budget', True)
    return {y: year_total(y) for y in (2024, 2025, 2026, 2027)}

r = date_case(date(2026, 8, 22))
check('7. default date: 2024 = 0 (not retro-applied)', eq(r[2024], 0))
check('7. default date: 2026 = 500 (Aug-Dec)', eq(r[2026], 500))
check('7. default date: 2027 = 1,200', eq(r[2027], 1200))

r = date_case(date(2026, 1, 1))
check('7. 1 Jan this year: 2025 = 0', eq(r[2025], 0))
check('7. 1 Jan this year: 2026 = 1,200 (full year)', eq(r[2026], 1200))

r = date_case(date(2024, 1, 1))
check('7. backdated catch-up: 2024 = 1,200', eq(r[2024], 1200))
check('7. backdated catch-up: 2026 = 1,200', eq(r[2026], 1200))

r = date_case(date(2027, 1, 1))
check('7. forward-dated budget: 2026 = 0', eq(r[2026], 0))
check('7. forward-dated budget: 2027 = 1,200', eq(r[2027], 1200))

# ================================================================ THE FORMS
TPL = os.path.join(ROOT, 'pages', 'templates')
for f, want in (('finance_expense_add.html', "{% now 'Y' %}-01-01"),
                ('finance_revenue_add.html', "{% now 'Y' %}-01-01"),
                ('finance_expense_edit.html', "{% now 'Y-m-d' %}"),
                ('finance_revenue_edit.html', "{% now 'Y-m-d' %}")):
    p = os.path.join(TPL, f)
    if not os.path.exists(p):
        check('8. %s exists' % f, False)
        continue
    s = open(p, encoding='utf-8').read()
    check('8. %s prefills %s' % (f, '1 January' if 'add' in f else 'today'),
          want in s)
    if 'add' in f:
        check('8.   %s explains starting something new' % f,
              'Starting something new' in s)

# ================================== 9. THE LAST UNDATED SCREEN, AND on_commit
# For a pro-rata line the Expense Amount is read-only on the Edit Expense
# screen - the figure belongs to the line type. So Edit Expense Line Type is
# the only place it can change, and it must be datable.
LT_FORM = os.path.join(TPL, 'finance_expense_line_types_edit.html')
if not os.path.exists(LT_FORM):
    check('9. finance_expense_line_types_edit.html exists', False)
else:
    s = open(LT_FORM, encoding='utf-8').read()
    check('9. line-type form has the effective-date field',
          'name="effective_date"' in s)
    check('9.   it prefills today (a change, not a creation)',
          "{% now 'Y-m-d' %}" in s)
    check('9.   it is hidden until the amount changes',
          'id="fh-applies-from"' in s and 'display:none' in s)
    check('9.   a reveal script binds to the amount input',
          'syncAppliesFrom' in s and 'originalPrAmount' in s)

# Request state read inside an on_commit callback runs after the response is
# on its way. Every call site should resolve it first.
leaky = re.findall(r'lambda [^\n]*_fh_(?:eff_date|user)\(request\)', FIN_SRC)
check('9. no on_commit callback reads request state (%d found)' % len(leaky),
      not leaky)

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
