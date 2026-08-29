"""Probe 2: is the whole 2026 Company Tax column resolving to zero?

Read-only. Writes nothing. ASCII output only.

    python manage.py shell -c "exec(open('probe_matrix.py').read())"

The claim under test: a snapshot dated in month M cannot supply a figure to
any month earlier than M in the same year, because resolve_year_months_bulk
chooses a snapshot by effective_date and then reads THAT snapshot's column for
the month being resolved. A June charge recalculated in August therefore
resolves to nothing for June.

If the claim holds, every row below shows a live June cell with money in it
and a resolved June of 0 or None, and the matrix column for the charge year
comes out empty across the portfolio - not just for Dikaiosynis.
"""
from pages.models import (expense, expense_line_types,
                          FinancialFigureHistory as H, FH_BASELINE_DATE,
                          _FH_MONTHS, resolve_year_months_bulk)
from pages.views.finance import expense_matrix

MONTHS = list(_FH_MONTHS)
LINE_TYPE_NAME = 'Company Tax'
YEAR = 2026


def cells_of(obj, prefix):
    return [getattr(obj, prefix + m, None) for m in MONTHS]


def fmt(vals):
    return ','.join('.' if v in (None, 0) else str(v) for v in vals)


lt = expense_line_types.objects.filter(
    expense_line_types_name=LINE_TYPE_NAME).first()
if lt is None:
    print('No line type named %r' % LINE_TYPE_NAME)
else:
    rows = list(expense.objects.select_related('prop')
                .filter(expense_line_types_id=lt.expense_line_types_id))
    prop_ids = [r.prop_id for r in rows]
    resolved = resolve_year_months_bulk(prop_ids, H.KIND_BUDGET, YEAR)

    print('=' * 78)
    print('%s -- %d row(s), resolving year %d' % (LINE_TYPE_NAME, len(rows), YEAR))
    print('months are jan..dec left to right; "." means None or zero')
    print('=' * 78)

    stranded = []
    for r in sorted(rows, key=lambda r: (r.prop.prop_name or '').lower()
                    if r.prop else ''):
        live = cells_of(r, 'expense_')
        res = resolved.get(r.expense_id)
        print('')
        print('%-24s expense_id=%s  live amount=%s'
              % ((r.prop.prop_name if r.prop else '?')[:24],
                 r.expense_id, r.expense_amount))
        print('    live cells     = %s' % fmt(live))
        print('    resolved %d    = %s'
              % (YEAR, fmt(res) if res is not None
                 else '(no history -> live cells used)'))

        # Which months hold money on a snapshot that is dated too late to
        # ever supply them?
        for h in H.objects.filter(kind=H.KIND_BUDGET, source_pk=r.expense_id):
            if h.effective_date == FH_BASELINE_DATE:
                continue
            for i, m in enumerate(MONTHS):
                v = getattr(h, m)
                if v not in (None, 0) and (i + 1) < h.effective_date.month \
                        and h.effective_date.year == YEAR:
                    stranded.append((r.prop.prop_name if r.prop else '?',
                                     r.expense_id, h.effective_date, m, v))

    print('')
    print('=' * 78)
    if stranded:
        print('STRANDED FIGURES -- money in a month EARLIER than the snapshot')
        print('that carries it, so no month of %d can ever resolve to it:' % YEAR)
        for name, eid, eff, m, v in stranded:
            print('   %-24s id=%-5s eff %s carries %s=%s'
                  % (name[:24], eid, eff, m, v))
    else:
        print('No stranded figures found. The claim does NOT hold.')
    print('=' * 78)

    # And what the screen actually draws.
    m = expense_matrix(lt.expense_line_types_id)
    print('')
    print('expense_matrix() says: years %s' % (m['years'],))
    print('%-24s %s' % ('property', '  '.join('%10s' % y for y in m['years'])))
    for row in m['rows']:
        print('%-24s %s' % (row['prop_name'][:24],
                            '  '.join('%10s' % ('-' if c is None else c)
                                      for c in row['cells'])))
    print('%-24s %s' % ('TOTAL',
                        '  '.join('%10s' % t for t in m['totals'])))
    print('grand total = %s' % m['grand_total'])
