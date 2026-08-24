"""Trace one budgeted expense line on the LOCAL database. Read-only.

    python Show-LocalExpenseTrace.py "Company Tax"
    python Show-LocalExpenseTrace.py "Company Tax" 2025 2026 2027 2028

Prints, for the named Expense Line Type:

  A. the Line Type itself - pro-rata flag and amount
  B. every live expense row, its property AND that property's status, the
     months that carry a figure, and the row's yearly total
  C. every history snapshot per row - effective date, source, when it was
     written, and what it held
  D. what resolve_year_months_bulk actually returns per year, split into
     what the P&L will draw (Active properties only, exactly as
     finance_pl_act filters) and what it will silently leave out

Section D is the point. The P&L only ever draws Active properties, so a
pro-rata share allocated to an inactive one is money the report never shows -
and nothing else in the system says so.

Nothing is written. Run it from the project root with the local venv active.
"""

import os
import sys
from collections import defaultdict
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django                                                    # noqa: E402
django.setup()                                                   # noqa: E402

from pages.models import (expense, expense_line_types, props,     # noqa: E402
                          FinancialFigureHistory,
                          resolve_year_months_bulk)

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
BAR = '=' * 100

args = [a for a in sys.argv[1:]]
name = args[0] if args else 'Company Tax'
years = [int(a) for a in args[1:] if a.isdigit()] or [2025, 2026, 2027, 2028]


def d(v):
    return Decimal('0') if v in (None, '') else Decimal(str(v))


def money(v):
    return '{:>10,.2f}'.format(d(v))


def months_of(obj, prefix=''):
    """Non-empty months as 'Jan 3,500.00' strings."""
    out = []
    for i, m in enumerate(MONTHS):
        v = getattr(obj, prefix + m, None)
        if v not in (None, '') and d(v) != 0:
            out.append('%s %s' % (ABBR[i], '{:,.2f}'.format(d(v))))
    return ', '.join(out) if out else '(all empty or zero)'


# ------------------------------------------------------------------ SECTION A
lts = [lt for lt in expense_line_types.objects.all()
       if (lt.expense_line_types_name or '').strip().lower() == name.strip().lower()]
if not lts:
    print('! No Expense Line Type called %r. Available:' % name)
    for lt in expense_line_types.objects.all().order_by('expense_line_types_name'):
        print('   -', lt.expense_line_types_name)
    sys.exit(1)
lt = lts[0]

print(BAR)
print('A. LINE TYPE')
print(BAR)
print('  name        : %s' % lt.expense_line_types_name)
print('  id          : %s' % lt.expense_line_types_id)
print('  pro-rata    : %s' % (lt.expense_line_types_prorata or '(unset)'))
print('  pr amount   : %s' % money(lt.expense_line_types_pr_amount))

# ------------------------------------------------------------------ SECTION B
rows = list(expense.objects.select_related('prop', 'expense_types')
            .filter(expense_line_types=lt).order_by('expense_id'))

print('')
print(BAR)
print('B. LIVE EXPENSE ROWS  (%d)' % len(rows))
print(BAR)
print('  %-6s %-24s %-10s %-14s %11s  %s'
      % ('ID', 'PROPERTY', 'STATUS', 'TYPE', 'YEAR TOTAL', 'MONTHS'))
print('  ' + '-' * 96)

live_total = Decimal('0')
inactive_total = Decimal('0')
inactive = []
for e in rows:
    yr = sum(d(getattr(e, 'expense_' + m)) for m in MONTHS)
    live_total += yr
    status = (e.prop.prop_status or '?') if e.prop else '?'
    if status != 'Active':
        inactive.append((e, yr))
        inactive_total += yr
    print('  %-6s %-24s %-10s %-14s %11s  %s'
          % (e.expense_id, (e.prop.prop_name or '')[:24] if e.prop else '?',
             status, str(e.expense_types)[:14], '{:,.2f}'.format(yr),
             months_of(e, 'expense_')))
print('  ' + '-' * 96)
print('  %-58s %11s' % ('TOTAL across every row', '{:,.2f}'.format(live_total)))
if inactive:
    print('  %-58s %11s' % ('...of which sits on INACTIVE properties',
                            '{:,.2f}'.format(inactive_total)))

# ------------------------------------------------------------------ SECTION C
pks = [e.expense_id for e in rows]
hist = defaultdict(list)
for h in (FinancialFigureHistory.objects
          .filter(kind=FinancialFigureHistory.KIND_BUDGET, source_pk__in=pks)
          .order_by('source_pk', 'effective_date', 'changed_at')):
    hist[h.source_pk].append(h)

print('')
print(BAR)
print('C. HISTORY SNAPSHOTS')
print(BAR)
if not hist:
    print('  (none - every year will fall back to the live cells above)')
for e in rows:
    hs = hist.get(e.expense_id, [])
    label = (e.prop.prop_name or '')[:24] if e.prop else '?'
    print('')
    print('  #%-5s %-24s  %d snapshot(s)' % (e.expense_id, label, len(hs)))
    if not hs:
        print('      (none - this row has no history at all)')
    for h in hs:
        print('      %-12s %-16s written %s  %s'
              % (h.effective_date, h.source or '(none)',
                 h.changed_at.strftime('%Y-%m-%d %H:%M'), months_of(h)))

# ------------------------------------------------------------------ SECTION D
active_ids = set(props.objects.filter(prop_status='Active')
                 .values_list('prop_id', flat=True))
all_ids = list(props.objects.values_list('prop_id', flat=True))

print('')
print(BAR)
print('D. WHAT EACH YEAR RESOLVES TO')
print(BAR)
print('  "P&L draws" uses Active properties only, exactly as finance_pl_act does.')
print('')
print('  %-6s %14s %14s %14s   %s'
      % ('YEAR', 'P&L DRAWS', 'NOT DRAWN', 'ALL ROWS', 'NOTE'))
print('  ' + '-' * 96)

for y in years:
    resolved = resolve_year_months_bulk(all_ids,
                                        FinancialFigureHistory.KIND_BUDGET, y)
    drawn = Decimal('0')
    skipped = Decimal('0')
    from_live = 0
    for e in rows:
        vals = resolved.get(e.expense_id)
        if vals is None:
            vals = [getattr(e, 'expense_' + m) for m in MONTHS]
            from_live += 1
        total = sum(d(v) for v in vals)
        if e.prop and e.prop_id in active_ids:
            drawn += total
        else:
            skipped += total
    note = []
    if from_live:
        note.append('%d row(s) had no history in range -> live cells used' % from_live)
    if skipped:
        note.append('%s on inactive properties' % '{:,.2f}'.format(skipped))
    print('  %-6s %14s %14s %14s   %s'
          % (y, '{:,.2f}'.format(drawn), '{:,.2f}'.format(skipped),
             '{:,.2f}'.format(drawn + skipped), '; '.join(note)))

print('')
print('  Per-property detail, %d:' % years[-1])
resolved = resolve_year_months_bulk(all_ids, FinancialFigureHistory.KIND_BUDGET,
                                    years[-1])
print('  %-6s %-24s %-10s %11s  %s'
      % ('ID', 'PROPERTY', 'STATUS', 'RESOLVED', 'MONTHS IN FORCE'))
print('  ' + '-' * 96)
for e in rows:
    vals = resolved.get(e.expense_id)
    src = 'history'
    if vals is None:
        vals = [getattr(e, 'expense_' + m) for m in MONTHS]
        src = 'LIVE ROW'
    total = sum(d(v) for v in vals)
    shown = ', '.join('%s %s' % (ABBR[i], '{:,.2f}'.format(d(v)))
                      for i, v in enumerate(vals) if v not in (None, '') and d(v) != 0)
    status = (e.prop.prop_status or '?') if e.prop else '?'
    print('  %-6s %-24s %-10s %11s  %s%s'
          % (e.expense_id, (e.prop.prop_name or '')[:24] if e.prop else '?',
             status, '{:,.2f}'.format(total), shown or '(nothing)',
             '' if src == 'history' else '   <- ' + src))

print('')
print(BAR)
print('Nothing was written.')
print(BAR)
