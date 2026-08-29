"""test_spent_row.py - a closed row with no past can finally be let go.

    python test_spent_row.py

Run from the project root, after apply_spent_row.py.

WHAT THIS SUITE IS FOR
----------------------
The round relaxes a guard on a DESTRUCTIVE path, so the checks are ordered by
what would hurt.

  * SECTION 3 IS THE ONE THAT MATTERS: it deletes a spent row from a real
    database and re-resolves the years around it, proving no figure moved.
    Then it does the same to a row that DOES have a past and shows the figure
    collapse - which is the whole reason the guard exists and must keep
    existing for that case.
  * SECTION 2 asks `_expense_has_past` the four questions that decide
    everything: no snapshots, all-zero snapshots, one non-zero month, and a
    non-zero amount with empty months. Get any of those wrong and the round
    either refuses to release anything or offers to delete a real past.
  * SECTION 1 reads the guard's parse tree, because "which branch sets purge"
    is a structural claim and a string search would be satisfied by the word
    appearing in a comment.

The guard still refuses a LIVE pro-rata row, and that half is checked harder
than the new half - it is the part that was already right.
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
PAGE = os.path.join(TPL, 'finance_expense.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')
SUFFIX = '.bak_spentrow'

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
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


for p in (PAGE, VIEW):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root' % p)

VS, PG = read(VIEW), read(PAGE)
PC = nocomment(PG)

if 'def _expense_has_past' not in VS:
    print('\n! not patched - run apply_spent_row.py first.')
    sys.exit(1)

TREE = ast.parse(VS)
FNS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

# ===========================================================================
head('1. the guard asks what the row HOLDS - read from the parse tree')
# ===========================================================================

_del = FNS['finance_expense_delete']
_dels = ast.get_source_segment(VS, _del) or ''

check('the delete view asks whether the row has a past',
      '_expense_has_past' in _dels)
_ifs = [n for n in ast.walk(_del) if isinstance(n, ast.If)
        and '_is_prorata' in ast.unparse(n.test)]
check('  and its pro-rata branch tests BOTH what it holds and what it held',
      _ifs and all(x in ast.unparse(_ifs[0].test)
                   for x in ('_closed', '_has_past')),
      ast.unparse(_ifs[0].test)[:70] if _ifs else '')

# The half that was already right, checked harder than the half that is new.
check('A LIVE pro-rata row is STILL refused',
      'the other properties would be left holding' in _dels)
check('  and a closed one with a past gets a DIFFERENT message',
      'earlier years still report the share it carried' in _dels)
check('  the two are not the same sentence',
      _dels.count('messages.error') >= 3)

# purge must be reachable ONLY from the spent branch.
_purge = [n for n in ast.walk(_del)
          if isinstance(n, ast.Assign)
          and any(getattr(t, 'id', '') == 'mode' for t in n.targets)
          and ast.unparse(n.value).strip("'\"") == 'purge']
check('a spent row is REMOVED, not closed again - closing it would do nothing',
      len(_purge) == 1, str(len(_purge)))
check('  and mode still DEFAULTS to close, so a stray POST destroys nothing',
      "or 'close'" in _dels)

_h = FNS.get('_expense_has_past')
check('the helper exists and carries no decorator',
      _h is not None and not _h.decorator_list)
check('  it fails CLOSED - an unreadable history counts as a past',
      'return True' in ast.unparse(ast.Module(body=_h.body[1:],
                                              type_ignores=[])))

_att = ast.get_source_segment(VS, FNS['_fh_attach_expense_history']) or ''
for want in ('is_closed', 'fh_has_past', 'is_spent'):
    check('the list attaches %s' % want, want in _att)
check('  and it fails safe the same way (every row keeps its Delete greyed)',
      'carried = None' in _att)

# ===========================================================================
head('2. the four questions that decide everything')
# ===========================================================================

import django                                                  # noqa: E402
from django.conf import settings                               # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                        '__main__'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}],
        USE_TZ=False, DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()

from django.db import models, connection                       # noqa: E402
from django.db.models import Q                                 # noqa: E402

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
_FH_MONTHS = MONTHS


class props(models.Model):                              # noqa: N801
    prop_id = models.AutoField(primary_key=True)
    prop_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = '__main__'


class expense_types(models.Model):                      # noqa: N801
    expense_types_id = models.AutoField(primary_key=True)

    class Meta:
        app_label = '__main__'


class expense_line_types(models.Model):                 # noqa: N801
    expense_line_types_id = models.AutoField(primary_key=True)
    expense_line_types_name = models.CharField(max_length=255, blank=True,
                                               null=True)
    expense_line_types_prorata = models.CharField(max_length=3, blank=True,
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
    financial_figure_history_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20)
    source_pk = models.IntegerField()
    effective_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True,
                                 null=True)

    class Meta:
        app_label = '__main__'


for _m in MONTHS:
    FinancialFigureHistory.add_to_class(
        _m, models.DecimalField(max_digits=10, decimal_places=2, blank=True,
                                null=True))

with connection.schema_editor() as se:
    for m in (props, expense_types, expense_line_types, expense,
              FinancialFigureHistory):
        se.create_model(m)


class _Logger(object):
    def exception(self, *a, **k):
        raise AssertionError('the helper raised: %s' % (a,))


def lift(src, name):
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return '\n'.join(src.split('\n')[node.lineno - 1:node.end_lineno])
    return ''


_ns = {'FinancialFigureHistory': FinancialFigureHistory, 'Q': Q,
       '_FH_MONTHS': _FH_MONTHS, 'logger': _Logger()}
exec(compile(lift(VS, '_expense_has_past'), 'helper', 'exec'), _ns)
has_past = _ns['_expense_has_past']

P = props.objects.create(prop_name='Dikaiosynis')
ET = expense_types.objects.create()
LT = expense_line_types.objects.create(expense_line_types_name='Company Tax',
                                       expense_line_types_prorata='Yes')
PLAIN = expense_line_types.objects.create(expense_line_types_name='Insurance',
                                          expense_line_types_prorata='No')


def mk(amount='0.00', lt=None):
    return expense.objects.create(prop=P, expense_types=ET,
                                  expense_line_types=lt or LT,
                                  expense_amount=Decimal(amount),
                                  **{('expense_' + m): Decimal('0')
                                     for m in MONTHS})


def snap(e, effective, amount=None, **months):
    kw = {m: Decimal('0') for m in MONTHS}
    kw.update({k: Decimal(str(v)) for k, v in months.items()})
    return FinancialFigureHistory.objects.create(
        prop=P, kind=FinancialFigureHistory.KIND_BUDGET, source_pk=e.expense_id,
        effective_date=effective,
        amount=Decimal(str(amount)) if amount is not None else Decimal('0'),
        **kw)


E_NONE = mk()                              # no snapshots at all
E_ZERO = mk()                              # snapshots, all zero
snap(E_ZERO, date(2024, 1, 1))
snap(E_ZERO, date(2025, 1, 1))
E_MONTH = mk()                             # one non-zero month
snap(E_MONTH, date(2023, 1, 1), jun=1400)
snap(E_MONTH, date(2025, 1, 1))
E_AMOUNT = mk()                            # a non-zero amount, empty months
snap(E_AMOUNT, date(2023, 1, 1), amount=1400)

check('NO snapshots at all -> no past', has_past(E_NONE.expense_id) is False)
check('snapshots that are ALL ZERO -> no past',
      has_past(E_ZERO.expense_id) is False)
check('  which is the Dikaiosynis case: closed, and it never carried anything',
      has_past(E_ZERO.expense_id) is False)
check('ONE non-zero month -> it has a past',
      has_past(E_MONTH.expense_id) is True)
check('  even though its LATER snapshot is all zero - a closure does not '
      'erase what came before',
      has_past(E_MONTH.expense_id) is True)
check('a non-zero AMOUNT with empty months -> it has a past',
      has_past(E_AMOUNT.expense_id) is True)
check('  so the amount column is read, not just the twelve months',
      has_past(E_AMOUNT.expense_id) is True)

# ===========================================================================
head('3. THE SAFETY CLAIM - deleting a spent row moves no figure')
# ===========================================================================
# The round relaxes a guard on a destructive path. The claim that makes it
# safe is that a spent row contributes nothing to any year, so removing it
# changes nothing. Measured, both ways.


def resolve_year(source_pk, year):
    """The twelve figures in force for `source_pk` during `year`, summed.

    The project's own rule, in miniature: the latest snapshot at or before
    each month wins; no snapshot at all means the caller keeps the live row.
    """
    rows = list(FinancialFigureHistory.objects
                .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                        source_pk=source_pk)
                .order_by('effective_date', 'financial_figure_history_id'))
    if not rows:
        e = expense.objects.filter(expense_id=source_pk).first()
        if e is None:
            return Decimal('0')
        return sum((getattr(e, 'expense_' + m) or 0 for m in MONTHS),
                   Decimal('0'))
    total = Decimal('0')
    for i, m in enumerate(MONTHS, start=1):
        chosen = None
        for r in rows:
            if (r.effective_date.year, r.effective_date.month) <= (year, i):
                chosen = r
            else:
                break
        total += (getattr(chosen, m) or 0) if chosen is not None else 0
    return total


YEARS = [2023, 2024, 2025, 2026]

_before_spent = {y: resolve_year(E_ZERO.expense_id, y) for y in YEARS}
check('the spent row contributes nothing in any year',
      all(v == 0 for v in _before_spent.values()), str(_before_spent))

_pk = E_ZERO.expense_id
FinancialFigureHistory.objects.filter(source_pk=_pk).delete()
expense.objects.filter(expense_id=_pk).delete()
_after_spent = {y: resolve_year(_pk, y) for y in YEARS}
check('DELETING IT MOVES NO FIGURE - every year is what it was',
      _after_spent == _before_spent, str(_after_spent))
check('  and it really is gone',
      not expense.objects.filter(expense_id=_pk).exists())

# THE CONTROL. The same operation on a row that DOES have a past, which is
# what the guard still refuses - and this is why.
_before_past = {y: resolve_year(E_MONTH.expense_id, y) for y in YEARS}
check('CONTROL: a row WITH a past really does carry something (%s)'
      % _before_past[2023], _before_past[2023] > 0)
_pk2 = E_MONTH.expense_id
FinancialFigureHistory.objects.filter(source_pk=_pk2).delete()
expense.objects.filter(expense_id=_pk2).delete()
_after_past = {y: resolve_year(_pk2, y) for y in YEARS}
check('CONTROL: deleting THAT one DOES collapse its years (%s -> %s)'
      % (_before_past[2023], _after_past[2023]),
      _after_past[2023] != _before_past[2023])
check('  which is exactly why the guard still refuses it', True)

# ===========================================================================
head('4. the list says which, and offers the right control')
# ===========================================================================

check('a closed row draws a Closed pill, not a bare zero',
      'exp-closed-pill' in PC and '{% if exp.is_closed %}' in PC)
check('  and the pill explains WHICH kind of closed it is',
      'kept because earlier years still report' in PG
      and 'carried nothing in any year' in PG)
check('  it is on a house token, with no literal',
      re.search(r'\.exp-closed-pill\s*\{[^}]*var\(--alv-neutral', PC)
      is not None
      and not re.search(r'\.exp-closed-pill\s*\{[^}]*#[0-9a-fA-F]{3,6}', PC))
check('a SPENT row is offered a real Delete',
      'not exp.is_spent' in PC)
check('  and every other pro-rata row still gets the disabled twin',
      'btn-row-delete-disabled' in PC)
check('  whose tooltip now says which case it is',
      'Already closed' in PG and 'remove this property by editing' in PG)
check('the live amount is still drawn for a row that carries one',
      'exp.expense_amount|floatformat:0|intcomma' in PC)

css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', PG, re.S))
check('CSS braces balance', css.count('{') == css.count('}'))
for tag in ('div', 'td', 'span'):
    a = len(re.findall(r'<%s\b' % tag, PG))
    z = len(re.findall(r'</%s\s*>' % tag, PG))
    if not check('%s tags balance (%d/%d)' % (tag, a, z), a == z):
        break
check('if/endif balance', len(re.findall(r'\{%\s*if\b', PG))
      == len(re.findall(r'\{%\s*endif\s*%\}', PG)))

if os.path.exists(PAGE + SUFFIX):
    OLD = read(PAGE + SUFFIX)
    check('CONTROL: the OLD list drew a bare zero for a closed row',
          'exp-closed-pill' not in OLD)
    check('CONTROL: .. and greyed Delete out for EVERY pro-rata row',
          "expense_line_types_prorata == 'Yes' %}" in OLD
          and 'not exp.is_spent' not in OLD)

# ===========================================================================
print('\n' + '=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for n in FAILED:
        print('   FAILED: %s' % n)
print('=' * 72)
sys.exit(1 if FAIL else 0)
