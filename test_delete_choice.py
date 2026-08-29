"""test_delete_choice - does "delete" now mean what the user chose?

    python test_delete_choice.py

finance_expense_delete and delete_expense_line_type are lifted verbatim out of
pages/views/finance.py and exec'd against a stub ORM, alongside
purge_figure_history and resolve_year_months_bulk from pages/models.py. So the
behaviour below is the shipping code's, not a re-implementation.

The example: one property, Insurance, 100 a month = 1,200 a year, seeded at
2024-01-01. Deleted on 22 Aug 2026, both ways.
"""

import json
import os
import re
import sys
from datetime import date, datetime
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates')

for p in (MODELS, FINANCE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

MODELS_SRC = open(MODELS, encoding='utf-8').read().replace('\r\n', '\n')
FIN_SRC = open(FINANCE, encoding='utf-8').read().replace('\r\n', '\n')

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
KIND = 'budget_expense'
WHEN = date(2026, 8, 22)

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def grab(src, name, where):
    m = re.search(r'^def %s\(.*?\n(?=\S)' % re.escape(name), src, re.S | re.M)
    if not m:
        sys.exit('! %s not found in %s - has apply_delete_choice.py been run?'
                 % (name, where))
    return m.group(0)


# ============================================================== the stub ORM
_clock = [0]
HISTORY = []
EXPENSES = []
LINE_TYPES = []
COMMITS = []
MESSAGES = []


class HRow:
    def __init__(self, **kw):
        prop = kw.pop('prop', None)
        self.prop_id = getattr(prop, 'pk', 1)
        for k, v in kw.items():
            setattr(self, k, v)
        for m in MONTHS:
            if not hasattr(self, m):
                setattr(self, m, None)
        _clock[0] += 1
        self.changed_at = datetime(2026, 1, 1).replace(microsecond=_clock[0])


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

    def delete(self):
        n = 0
        for r in list(self):
            if r in HISTORY:
                HISTORY.remove(r)
                n += 1
        return n, {'pages.FinancialFigureHistory': n}


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
    pk = 1
    prop_name = 'Palikaridi'


class LineType:
    def __init__(self, pk, name, prorata='No'):
        self.expense_line_types_id = pk
        self.expense_line_types_name = name
        self.expense_line_types_prorata = prorata
        self.alive = True

    def __str__(self):
        return self.expense_line_types_name

    def delete(self):
        self.alive = False


class ExpType:
    expense_types_id = 9
    expense_types_name = 'Monthly'

    def __str__(self):
        return 'Monthly'


class ExpRow:
    _next = [700]

    def __init__(self, line_type, amount):
        self.expense_id = ExpRow._next[0]
        ExpRow._next[0] += 1
        self.prop = Prop()
        self.prop_id = 1
        self.expense_line_types = line_type
        self.expense_line_types_id = line_type.expense_line_types_id
        self.expense_types = ExpType()
        self.expense_types_id = 9
        self.expense_amount = amount
        self.alive = True
        for m in MONTHS:
            setattr(self, 'expense_' + m, amount)

    def save(self):
        pass

    def delete(self):
        self.alive = False


class EQS(list):
    def filter(self, **kw):
        out = EQS(r for r in self if r.alive)
        for k, v in kw.items():
            if k == 'expense_line_types':
                out = EQS(r for r in out if r.expense_line_types is v)
            else:
                out = EQS(r for r in out if getattr(r, k) == v)
        return out

    def order_by(self, *keys):
        return self

    def count(self):
        return len(self)

    def delete(self):
        for r in self:
            r.alive = False


class EManager:
    def filter(self, **kw):
        return EQS(EXPENSES).filter(**kw)


class ExpModel:
    objects = EManager()

    class DoesNotExist(Exception):
        pass


class LTManager:
    def filter(self, **kw):
        return [lt for lt in LINE_TYPES if lt.alive]


class LTModel:
    objects = LTManager()

    class DoesNotExist(Exception):
        pass


class Http404(Exception):
    pass


def get_object_or_404(model, **kw):
    if model is ExpModel:
        hit = [e for e in EXPENSES if e.alive
               and e.expense_id == kw.get('expense_id')]
    else:
        hit = [lt for lt in LINE_TYPES if lt.alive
               and lt.expense_line_types_id == kw.get('expense_line_types_id')]
    if not hit:
        raise Http404('not found')
    return hit[0]


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


def redirect(name, **kw):
    return 'redirect:' + name


class JsonResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status


class _Logger:
    @staticmethod
    def exception(*a, **k):
        pass


class Request:
    def __init__(self, post=None, body=None):
        self.method = 'POST'
        self.POST = post or {}
        self.body = body or b''
        self.user = None


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
             'record_expense_history', 'purge_figure_history',
             'resolve_year_months_bulk'):
    exec(compile(grab(MODELS_SRC, name, 'models.py'), name, 'exec'), NS)

resolve = NS['resolve_year_months_bulk']

from django.db.models import Q as _Q          # noqa: E402

VIEW_NS = {
    'expense': ExpModel,
    'expense_line_types': LTModel,
    'transaction': _Transaction,
    'messages': _Messages,
    'redirect': redirect,
    'get_object_or_404': get_object_or_404,
    'JsonResponse': JsonResponse,
    'json': json,
    'MONTHS': MONTHS,
    'logger': _Logger,
    'date': date,
    'datetime': datetime,
    'FinancialFigureHistory': FFH,
    'ensure_expense_baseline': NS['ensure_expense_baseline'],
    'ensure_expense_opening': NS['ensure_expense_opening'],
    'record_expense_history': NS['record_expense_history'],
    'purge_figure_history': NS['purge_figure_history'],
    '_fh_user': lambda request: None,
    # Q and the month names are here because a LATER round put them in the
    # view. The spent-row round gave finance_expense_delete a helper,
    # _expense_has_past, which asks whether a row's history carries anything -
    # and this namespace was built when the view called nothing of the kind.
    # The lifted function then died with a NameError on every case, which is
    # why fourteen unrelated checks failed at once. Section 4b of
    # outstanding_items.md, in its stale-HARNESS shape rather than its stale-
    # expectation one.
    'Q': _Q,
    '_FH_MONTHS': MONTHS,
}
for name in ('_fh_date_or_today', '_fh_eff_date', '_fh_save_expense',
             '_fh_close_expense', '_expense_has_past',
             'finance_expense_delete',
             'delete_expense_line_type'):
    exec(compile(grab(FIN_SRC, name, 'finance.py'), name, 'exec'), VIEW_NS)

expense_delete = VIEW_NS['finance_expense_delete']
line_type_delete = VIEW_NS['delete_expense_line_type']


# ================================================================ the world
def reset(rows=1, prorata='No'):
    del HISTORY[:]
    del EXPENSES[:]
    del LINE_TYPES[:]
    del COMMITS[:]
    del MESSAGES[:]
    ExpRow._next[0] = 700
    lt = LineType(7, 'Insurance', prorata)
    LINE_TYPES.append(lt)
    for _ in range(rows):
        e = ExpRow(lt, 100)
        EXPENSES.append(e)
        NS['record_expense_history'](e, date(2024, 1, 1), source='seed')
    return lt


def flush():
    for fn in list(COMMITS):
        fn()
    del COMMITS[:]


def year_total(year):
    live = [e for e in EXPENSES if e.alive]
    resolved = resolve([1], KIND, year)
    total = Decimal('0')
    for e in live:
        vals = resolved.get(e.expense_id)
        if vals is None:
            vals = [getattr(e, 'expense_' + m) for m in MONTHS]
        total += sum(Decimal(str(v)) for v in vals if v is not None)
    return total


def orphans():
    live = {e.expense_id for e in EXPENSES if e.alive}
    return [h for h in HISTORY if h.kind == KIND and h.source_pk not in live]


def eq(a, b):
    return Decimal(str(a)) == Decimal(str(b))


# ======================================================== CLOSE, one expense
reset()
pk = EXPENSES[0].expense_id
expense_delete(Request({'delete_mode': 'close',
                        'effective_date': WHEN.isoformat()}), pk)
flush()

check('close: the row survives', EXPENSES[0].alive)
check('close: every month is zeroed',
      all(getattr(EXPENSES[0], 'expense_' + m) == 0 for m in MONTHS))
check('close: a closing snapshot is written',
      [h for h in HISTORY if h.source == 'closed'])
check('close: the seed is untouched',
      [h for h in HISTORY if h.source == 'seed'])
check('close: nothing is orphaned', not orphans())
check('close: 2024 still shows 1,200', eq(year_total(2024), 1200))
check('close: 2025 still shows 1,200', eq(year_total(2025), 1200))
check('close: 2026 shows Jan-Jul only (700)', eq(year_total(2026), 700))
check('close: 2027 shows nothing', eq(year_total(2027), 0))
check('close: the message says what happened',
      MESSAGES and 'stopped from' in MESSAGES[-1][1])

# ======================================================== PURGE, one expense
reset()
pk = EXPENSES[0].expense_id
expense_delete(Request({'delete_mode': 'purge'}), pk)
flush()

check('purge: the row is gone', not EXPENSES[0].alive)
check('purge: its history is gone too',
      not [h for h in HISTORY if h.source_pk == pk])
check('purge: nothing is orphaned', not orphans())
check('purge: 2024 no longer shows it', eq(year_total(2024), 0))
check('purge: the message says history went with it',
      MESSAGES and 'history included' in MESSAGES[-1][1])

# ============================================== THE DEFAULT IS THE SAFE ONE
reset()
pk = EXPENSES[0].expense_id
expense_delete(Request({}), pk)          # no delete_mode at all
flush()
check('a POST with no mode CLOSES rather than purges', EXPENSES[0].alive)
check('  ...and keeps 2024 intact', eq(year_total(2024), 1200))

reset()
expense_delete(Request({'delete_mode': 'PURGE'}), EXPENSES[0].expense_id)
flush()
check('mode matching is case-insensitive', not EXPENSES[0].alive)

# ==================================================== CLOSE, a whole line type
reset(rows=3)
resp = line_type_delete(Request(body=json.dumps(
    {'mode': 'close', 'effective_date': WHEN.isoformat()}).encode()), 7)
flush()

check('line type close: the line type is kept', LINE_TYPES[0].alive)
check('line type close: all three rows survive',
      all(e.alive for e in EXPENSES) and len(EXPENSES) == 3)
check('line type close: all three are zeroed',
      all(getattr(e, 'expense_' + m) == 0 for e in EXPENSES for m in MONTHS))
check('line type close: three closing snapshots',
      len([h for h in HISTORY if h.source == 'closed']) == 3)
check('line type close: nothing orphaned', not orphans())
check('line type close: 2024 still shows 3,600', eq(year_total(2024), 3600))
check('line type close: 2027 shows nothing', eq(year_total(2027), 0))
check('line type close: the response is a success',
      getattr(resp, 'payload', {}).get('success') is True)
check('line type close: the message explains the line type was kept',
      MESSAGES and 'line type was kept' in MESSAGES[-1][1])

# ==================================================== PURGE, a whole line type
reset(rows=3)
line_type_delete(Request(body=json.dumps({'mode': 'purge'}).encode()), 7)
flush()

check('line type purge: the line type is gone', not LINE_TYPES[0].alive)
check('line type purge: every row is gone', not any(e.alive for e in EXPENSES))
check('line type purge: every snapshot is gone',
      not [h for h in HISTORY if h.kind == KIND])
check('line type purge: nothing orphaned', not orphans())

# =============================== A LINE TYPE WITH NOTHING ON IT JUST GOES
reset(rows=0)
line_type_delete(Request(body=json.dumps({'mode': 'close'}).encode()), 7)
flush()
check('an empty line type is deleted even in close mode',
      not LINE_TYPES[0].alive)

# ============================== A MALFORMED BODY MUST NOT PURGE BY ACCIDENT
reset(rows=2)
line_type_delete(Request(body=b'not json at all'), 7)
flush()
check('an unparseable body falls back to close', LINE_TYPES[0].alive)
check('  ...and the rows survive', all(e.alive for e in EXPENSES))

reset(rows=2)
line_type_delete(Request(body=b''), 7)
flush()
check('an empty body falls back to close', LINE_TYPES[0].alive)

# ============================== A PRO-RATA ROW CANNOT BE DELETED ON ITS OWN
# It is a SHARE of the line type's amount. Removing one row leaves the others
# holding shares of a larger split, so the line stops adding up to the charge
# actually owed - silently. Un-ticking on the edit screen is the right move.
for mode in ('close', 'purge'):
    reset(prorata='Yes')
    pk = EXPENSES[0].expense_id
    snapshots_before = len(HISTORY)
    expense_delete(Request({'delete_mode': mode,
                            'effective_date': WHEN.isoformat()}), pk)
    flush()
    check('pro-rata + %s: the row is untouched' % mode,
          EXPENSES[0].alive
          and all(getattr(EXPENSES[0], 'expense_' + m) == 100 for m in MONTHS))
    check('pro-rata + %s: no snapshot written' % mode,
          len(HISTORY) == snapshots_before)
    check('pro-rata + %s: it is refused, not silently ignored' % mode,
          MESSAGES and MESSAGES[-1][0] == 'error'
          and 'un-tick' in MESSAGES[-1][1])

reset(prorata='yes')          # the flag is not always capitalised
expense_delete(Request({'delete_mode': 'purge'}), EXPENSES[0].expense_id)
flush()
check('the pro-rata check is case-insensitive', EXPENSES[0].alive)

reset(prorata='No')
expense_delete(Request({'delete_mode': 'purge'}), EXPENSES[0].expense_id)
flush()
check('a line type no longer marked pro-rata IS deletable',
      not EXPENSES[0].alive)

# ================================================================ THE SCREENS
p = os.path.join(TPL, 'finance_expense.html')
if not os.path.exists(p):
    check('finance_expense.html exists', False)
else:
    s = open(p, encoding='utf-8').read()
    check('expenses list: the confirm() dialog is gone',
          "confirm('Delete this expense?" not in s)
    check('expenses list: a delete dialog replaces it',
          'id="expenseDeleteModal"' in s)
    check('expenses list: close is preselected',
          'value="close" checked' in s)
    check('expenses list: remove-completely is offered',
          'value="purge"' in s)
    check('expenses list: the form carries the mode and the date',
          'name="delete_mode"' in s and 'name="effective_date"' in s)
    check('expenses list: the dialog reports how much history there is',
          'data-history=' in s)
    # SUPERSEDED by the spent-row round. This pinned the disabled span with
    # its title attribute ATTACHED - `btn-row-delete-disabled" title="Pro-rata`
    # - and that title is now conditional, so the two are no longer adjacent
    # while the claim is untouched. Pin the ADVICE and the narrowing, which
    # are the things worth guarding.
    check('expenses list: Delete is greyed out on a pro-rata row',
          "expense_line_types.expense_line_types_prorata == 'Yes'" in s
          and 'btn-row-delete-disabled' in s
          and 'Pro-rata expense &mdash; remove this property by editing' in s)
    check('  .. unless it is SPENT - closed, and carrying nothing behind it',
          'not exp.is_spent' in s)
    check('  and a closed row says which kind of closed it is',
          'exp-closed-pill' in s)

p = os.path.join(TPL, 'finance_expense_edit.html')
if not os.path.exists(p):
    check('finance_expense_edit.html exists', False)
else:
    s = open(p, encoding='utf-8').read()
    check('edit screen: the pro-rata panel explains un-ticking',
          'take up its share' in s)
    check('edit screen:   ...and warns the total stays the same',
          'The total stays the same' in s)

p = os.path.join(TPL, 'finance_expense_line_types.html')
if not os.path.exists(p):
    check('finance_expense_line_types.html exists', False)
else:
    s = open(p, encoding='utf-8').read()
    check('line types: the choice is in the modal', 'id="ltd-choice"' in s)
    check('line types: close is preselected', 'value="close" checked' in s)
    check('line types: the fetch sends the mode', 'mode: ltdMode()' in s)
    check('line types: the choice is hidden with no linked expenses',
          'ltdSetChoice(false)' in s)

# ============================ DJANGO COMMENTS CANNOT SPAN LINES
# `{# ... #}` is single-line only. Open one and close it on the next line and
# the parser never sees a comment at all - it renders the whole thing as text
# in the page. That happened once, inside a narrow table cell, and blew the
# row's height out to half a screen. One aggregate check over every template.
import glob                                                    # noqa: E402

leaky_comments = []
for _path in sorted(glob.glob(os.path.join(TPL, '*.html'))):
    with open(_path, encoding='utf-8', errors='replace') as _fh:
        for _i, _line in enumerate(_fh, 1):
            if '{#' in _line and '#}' not in _line:
                leaky_comments.append('%s:%d' % (os.path.basename(_path), _i))
check('no template opens a {# comment it fails to close on the same line (%s)'
      % (', '.join(leaky_comments) if leaky_comments else 'none checked clean'),
      not leaky_comments)

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
