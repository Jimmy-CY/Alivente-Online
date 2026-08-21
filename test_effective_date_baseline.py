"""test_effective_date_baseline - does the fix actually stop the failure?

    python test_effective_date_baseline.py

Two things are checked, both against code lifted verbatim out of the tree so
this tests what ships rather than a re-implementation:

  1. `_ensure_baseline` and `resolve_year_months_bulk` from pages/models.py are
     exec'd against a stub ORM, and the ORIGINAL Company Tax failure is replayed
     end to end: a long-standing line, edited once, with the change dated in the
     middle of a year. Without a baseline that produced a blank year. With one
     it must produce the correct blend.

  2. The four finance forms are read from disk and asserted to contain the
     effective-date field. That field is the whole reason the date was wrong;
     a patcher that silently missed one form would leave the bug alive on that
     screen.
"""

import os
import re
import sys
from datetime import date
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
TPL = os.path.join(ROOT, 'pages', 'templates')
FORMS = ['finance_expense_add.html', 'finance_expense_edit.html',
         'finance_revenue_add.html', 'finance_revenue_edit.html']

if not os.path.exists(MODELS):
    sys.exit('! %s not found - run from the project root' % MODELS)

SRC = open(MODELS, encoding='utf-8').read().replace('\r\n', '\n')

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def grab(name):
    """Pull one top-level function out of models.py, verbatim."""
    m = re.search(r'^def %s\(.*?\n(?=\S)' % re.escape(name), SRC, re.S | re.M)
    assert m, 'function %s not found in models.py' % name
    return m.group(0)


# ---------------------------------------------------------------- stub ORM
class Row:
    def __init__(self, **kw):
        self.pk = kw.pop('pk', None)
        for k, v in kw.items():
            setattr(self, k, v)
        for m in MONTHS:
            if not hasattr(self, m):
                setattr(self, m, None)


class QS(list):
    def filter(self, **kw):
        out = self
        if 'prop_id__in' in kw:
            out = QS(r for r in out if r.prop_id in kw['prop_id__in'])
        if 'kind' in kw:
            out = QS(r for r in out if r.kind == kw['kind'])
        if 'source_pk' in kw:
            out = QS(r for r in out if r.source_pk == kw['source_pk'])
        if 'effective_date__lte' in kw:
            out = QS(r for r in out if r.effective_date <= kw['effective_date__lte'])
        return out

    def order_by(self, *keys):
        cur = list(self)
        for k in reversed(keys):
            cur = sorted(cur, key=lambda r, k=k: getattr(r, k))
        return QS(cur)

    def exists(self):
        return len(self) > 0


STORE = []


class Objects:
    def filter(self, **kw):
        return QS(STORE).filter(**kw)

    def create(self, **kw):
        kw.setdefault('changed_at', date(2026, 8, 19))
        prop = kw.pop('prop', None)
        if prop is None:
            # Mirrors the real NOT NULL on prop_id. Without this the stub is
            # more forgiving than the database, and the fail-safe test passes
            # for the wrong reason - it never actually fails.
            raise ValueError('prop_id cannot be NULL')
        r = Row(prop_id=getattr(prop, 'pk', 1), **kw)
        STORE.append(r)
        return r


class FFH:
    objects = Objects()
    KIND_BUDGET = 'budget_expense'
    KIND_REVENUE = 'revenue'


class Prop:
    pk = 1
    prop_name = 'Test Property'


class Exp:
    """A budgeted expense row, mid-edit."""
    def __init__(self, months):
        self.prop = Prop()
        self.expense_id = 187
        self.expense_line_types = 'Company Tax'
        self.expense_amount = sum(v for v in months.values() if v)
        for m in MONTHS:
            setattr(self, 'expense_' + m, months.get(m))


ns = {
    'FinancialFigureHistory': FFH,
    '_fh_date': date,
    '_FH_MONTHS': MONTHS,
    '_fh_log': type('L', (), {'exception': staticmethod(lambda *a, **k: None)})(),
    'FH_BASELINE_DATE': date(2000, 1, 1),
}
for name in ('_ensure_baseline', 'ensure_expense_baseline',
             'resolve_year_months_bulk'):
    exec(compile(grab(name), name, 'exec'), ns)

check('models.py defines FH_BASELINE_DATE', 'FH_BASELINE_DATE = _fh_date(' in SRC)
check('FH_BASELINE_DATE is far enough back',
      re.search(r'FH_BASELINE_DATE = _fh_date\((\d{4})', SRC)
      and int(re.search(r'FH_BASELINE_DATE = _fh_date\((\d{4})', SRC).group(1)) <= 2000)


def resolved(year):
    out = ns['resolve_year_months_bulk']([1], FFH.KIND_BUDGET, year)
    vals = out.get(187)
    if vals is None:
        return None                      # source absent -> caller keeps live
    return {m: vals[i] for i, m in enumerate(MONTHS)}


def total(year):
    r = resolved(year)
    if r is None:
        return None
    return sum(Decimal(v) for v in r.values() if v is not None)


# ============================================================ THE FAILURE
# Replay it exactly: a long-standing line at 3500/3500, edited once, with the
# change dated mid-year. No baseline.
STORE[:] = []
OLD = {'jan': Decimal('3500'), 'jul': Decimal('3500')}
NEW = {'jan': Decimal('3300'), 'jul': Decimal('3300')}

after_edit = Exp(NEW)
FFH.objects.create(prop=Prop(), kind=FFH.KIND_BUDGET, source_pk=187,
                   line_type='Company Tax', effective_date=date(2026, 8, 5),
                   amount=Decimal('6600'), source='budget', changed_by=None,
                   **{m: NEW.get(m) for m in MONTHS})

check('WITHOUT a baseline, 2026 collapses to zero', total(2026) == 0)
check('WITHOUT a baseline, 2025 falls back to live (source absent)',
      resolved(2025) is None)

# ============================================================ THE FIX
# Same edit, but the baseline is written first — which is what _fh_save_expense
# now does, and in that order.
STORE[:] = []
ns['ensure_expense_baseline'](after_edit, {m: OLD.get(m) for m in MONTHS},
                              Decimal('7000'), user=None)
FFH.objects.create(prop=Prop(), kind=FFH.KIND_BUDGET, source_pk=187,
                   line_type='Company Tax', effective_date=date(2026, 7, 1),
                   amount=Decimal('6600'), source='budget', changed_by=None,
                   **{m: NEW.get(m) for m in MONTHS})

check('baseline written exactly once', len([r for r in STORE if r.source == 'baseline']) == 1)
check('baseline dated 2000-01-01',
      [r for r in STORE if r.source == 'baseline'][0].effective_date == date(2000, 1, 1))

for y in (2022, 2024, 2025):
    check('%d = 7000 (old rate reaches back)' % y, total(y) == Decimal('7000'))
check('2026 = 6800 (blend, not blank)', total(2026) == Decimal('6800'))
check('  2026 Jan at the OLD rate', resolved(2026)['jan'] == Decimal('3500'))
check('  2026 Jul at the NEW rate', resolved(2026)['jul'] == Decimal('3300'))
for y in (2027, 2028):
    check('%d = 6600 (new rate carries forward)' % y, total(y) == Decimal('6600'))

# ============================================================ IDEMPOTENCE
before = len(STORE)
ns['ensure_expense_baseline'](after_edit, {m: OLD.get(m) for m in MONTHS},
                              Decimal('7000'), user=None)
check('a second edit does NOT write another baseline', len(STORE) == before)

# ============================================================ EDGE CASES
STORE[:] = []
empty = Exp({})
ns['ensure_expense_baseline'](empty, {m: None for m in MONTHS}, None, user=None)
check('nothing budgeted before -> no baseline written', len(STORE) == 0)

STORE[:] = []
broken = Exp(OLD)
broken.prop = None                      # force an internal failure
r = ns['ensure_expense_baseline'](broken, {m: OLD.get(m) for m in MONTHS},
                                  Decimal('7000'), user=None)
check('a baseline failure is swallowed, never raised', r is None)

# ============================================================ THE FORMS
for f in FORMS:
    p = os.path.join(TPL, f)
    if not os.path.exists(p):
        check('%s exists' % f, False)
        continue
    s = open(p, encoding='utf-8').read()
    check('%s has the effective-date field' % f, 'name="effective_date"' in s)
    check('  %s prefills a date' % f, "{% now 'Y-m-d' %}" in s)
    check('  %s explains change vs correction' % f,
          'Correcting a mistake' in s and 'Changing a figure' in s)

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
