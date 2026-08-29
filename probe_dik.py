"""Probe: why are the Dikaiosynis expense rows CLOSED and un-deletable?

Read-only. Touches nothing, writes nothing, ASCII output only (Windows console).

Run from the repo root:

    python manage.py shell -c "exec(open('probe_dik.py').read())"

NOT by piping into `manage.py shell`. Piped input is fed to an
InteractiveConsole a line at a time, so every indented block dies with
IndentationError; -c execs the file as one unit.

It answers three questions in one pass:

  1. What does the history for those rows actually contain, snapshot by
     snapshot, and which snapshots sit on FH_BASELINE_DATE (the sentinel).
  2. Does `fh_has_past` -- the delete guard -- come out TRUE only because of a
     baseline? That is the hypothesis.
  3. What year does the year-on-year matrix open on for the same line types,
     and would those rows appear in it?

If (2) is yes and (3) opens after the row went to zero, the Expenses list is
justifying itself with years the matrix has decided not to draw.
"""
from django.db.models import Q, Min

from pages.models import (expense, FinancialFigureHistory as H,
                          FH_BASELINE_DATE, _FH_MONTHS)

NAME = 'Dikaiosynis'

MONTHS = list(_FH_MONTHS)
FIELDS = ('amount',) + tuple(MONTHS)


def carrying(qs):
    """The house definition of 'this snapshot carries something'."""
    q = Q()
    for f in FIELDS:
        q |= Q(**{f + '__isnull': False}) & ~Q(**{f: 0})
    return qs.filter(q)


rows = list(expense.objects
            .select_related('prop', 'expense_line_types')
            .filter(prop__prop_name__icontains=NAME))

print('=' * 72)
print('%d expense row(s) on a property matching %r' % (len(rows), NAME))
print('FH_BASELINE_DATE (the sentinel) = %s' % FH_BASELINE_DATE)
print('=' * 72)

verdicts = []

for e in rows:
    lt = e.expense_line_types
    print('')
    print('--- expense_id=%s  %s  /  %s' % (
        e.expense_id,
        e.prop.prop_name if e.prop else '(no property)',
        lt.expense_line_types_name if lt else '(no line type)'))
    print('    live expense_amount = %s   pro-rata line = %s' % (
        e.expense_amount, getattr(lt, 'expense_line_types_prorata', None)))

    snaps = H.objects.filter(kind=H.KIND_BUDGET,
                             source_pk=e.expense_id).order_by('effective_date')
    if not snaps:
        print('    NO HISTORY AT ALL')
    for h in snaps:
        months = [getattr(h, m) for m in MONTHS]
        carries = any(v is not None and v != 0
                      for v in [h.amount] + months)
        print('    %s  %-8s  carries=%-5s  amount=%-10s  months=%s' % (
            h.effective_date,
            'BASELINE' if h.effective_date == FH_BASELINE_DATE else '',
            carries, h.amount,
            ','.join('.' if v in (None, 0) else str(v) for v in months)))

    # The two rules, side by side.
    base = H.objects.filter(kind=H.KIND_BUDGET, source_pk=e.expense_id)
    has_past_now = carrying(base).exists()
    has_past_ex_baseline = carrying(
        base.exclude(effective_date=FH_BASELINE_DATE)).exists()
    is_closed = not (e.expense_amount or 0)

    print('    is_closed              = %s' % is_closed)
    print('    fh_has_past  (shipped) = %s   -> Delete %s'
          % (has_past_now, 'GREYED' if (is_closed and has_past_now)
             or not is_closed else 'OFFERED'))
    print('    fh_has_past  (if the baseline did not count) = %s'
          % has_past_ex_baseline)
    if has_past_now and not has_past_ex_baseline:
        print('    >>> KEPT ONLY BY THE BASELINE. This is the hypothesis.')
        verdicts.append(('baseline-only', e))
    elif has_past_now:
        print('    >>> Has a real dated past. Being kept for a good reason.')
        verdicts.append(('real-past', e))
    else:
        print('    >>> No past at all; this row should already be deletable.')
        verdicts.append(('spent', e))

    # What the matrix would do with this line type.
    if lt:
        sib_ids = list(expense.objects
                       .filter(expense_line_types_id=lt.expense_line_types_id)
                       .values_list('expense_id', flat=True))
        first = (H.objects
                 .filter(kind=H.KIND_BUDGET, source_pk__in=sib_ids)
                 .exclude(effective_date=FH_BASELINE_DATE)
                 .aggregate(m=Min('effective_date'))['m'])
        first_all = (H.objects
                     .filter(kind=H.KIND_BUDGET, source_pk__in=sib_ids)
                     .aggregate(m=Min('effective_date'))['m'])
        print('    matrix for this line type: %d contributing row(s)'
              % len(sib_ids))
        print('      earliest NON-baseline change = %s  -> matrix opens on %s'
              % (first, first.year if first else 'the current year'))
        print('      earliest snapshot of any kind = %s' % first_all)

print('')
print('=' * 72)
for kind in ('baseline-only', 'real-past', 'spent'):
    n = len([v for v in verdicts if v[0] == kind])
    if n:
        print('%2d row(s): %s' % (n, kind))
print('=' * 72)
