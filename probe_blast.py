"""Probe 3: exactly which figures would move if the year became the unit?

Read-only. Writes nothing. ASCII output only.

    python manage.py shell -c "exec(open('probe_blast.py').read())"

Replays EVERY budgeted expense row through both rules, for every year the
history covers, and reports only the cells that differ.

  OLD (shipped): for month m of year y, choose the latest snapshot with
      (eff.year, eff.month) <= (y, m), then read THAT snapshot's column m.
      A change made in August cannot supply June of the same year.

  NEW (proposed): for year y, choose the latest snapshot effective on or
      before 31 Dec y, and read all twelve of its columns. The twelve columns
      are the shape of the year's budget; the latest word on that year wins.

Both rules are implemented HERE, independently of the code being changed, so
this measures the proposal rather than trusting it. A row with no history is
skipped: it falls back to live cells under both rules and cannot move.

Read the output as the blast radius. Any year printed as UNCHANGED is a year
the P&L will report identically after the change.
"""
from collections import defaultdict
from decimal import Decimal

from django.db import connection

from pages.models import (expense, FinancialFigureHistory as H,
                          FH_BASELINE_DATE, _FH_MONTHS)

# WHICH DATABASE IS THIS?
#
# Run under `railway run`, the intent is to read PRODUCTION. If the settings
# module does not actually switch, this reads the local database instead and
# reports local numbers under a heading everyone believes says Live. Print the
# connection first so the output carries its own provenance. No credentials:
# engine, name, host and port identify it well enough.
_db = connection.settings_dict
print('-' * 78)
print('DATABASE  engine=%s' % _db.get('ENGINE'))
print('          name=%s' % _db.get('NAME'))
print('          host=%s  port=%s'
      % (_db.get('HOST') or '(local socket / file)', _db.get('PORT') or ''))
print('-' * 78)

MONTHS = list(_FH_MONTHS)

# Rows listed per year, largest movement first. The net is always exact; only
# the listing is capped, so a big production database stays readable.
CAP = 25


def old_rule(versions, year):
    """Month by month, re-choosing the snapshot for each month."""
    vals = []
    for m in range(1, 13):
        chosen = None
        for v in versions:                       # ascending
            if (v.effective_date.year, v.effective_date.month) <= (year, m):
                chosen = v
            else:
                break
        vals.append(getattr(chosen, MONTHS[m - 1]) if chosen is not None else None)
    return vals


def new_rule(versions, year):
    """One snapshot governs the whole year: the latest one in or before it."""
    eligible = [v for v in versions if v.effective_date.year <= year]
    if not eligible:
        return [None] * 12
    chosen = eligible[-1]
    return [getattr(chosen, m) for m in MONTHS]


def total(vals):
    return sum((v or Decimal('0')) for v in vals)


# Every budget snapshot, grouped by the row it belongs to, ascending.
rows = list(H.objects.filter(kind=H.KIND_BUDGET)
            .order_by('source_pk', 'effective_date', 'changed_at'))
by_src = defaultdict(list)
for r in rows:
    by_src[r.source_pk].append(r)

# Label each source row.
labels = {}
for e in (expense.objects.select_related('prop', 'expense_line_types')
          .filter(expense_id__in=list(by_src.keys()))):
    labels[e.expense_id] = (
        (e.prop.prop_name if e.prop else '?'),
        (e.expense_line_types.expense_line_types_name
         if e.expense_line_types else '?'))

# Which years are worth testing: every year any non-baseline snapshot names,
# through next year. The baseline is a sentinel and names no year.
real_dates = [r.effective_date for r in rows
              if r.effective_date != FH_BASELINE_DATE]
if not real_dates:
    print('No non-baseline budget history at all; nothing can move.')
else:
    from datetime import date
    first = min(real_dates).year
    last = max(max(real_dates).year, date.today().year) + 1

    print('=' * 78)
    print('%d source row(s) with history; testing years %d..%d'
          % (len(by_src), first, last))
    print('=' * 78)

    grand = Decimal('0')
    moved_rows = set()
    for year in range(first, last + 1):
        diffs = []
        for src, versions in by_src.items():
            o, n = old_rule(versions, year), new_rule(versions, year)
            if total(o) != total(n):
                diffs.append((src, total(o), total(n)))
        if not diffs:
            print('')
            print('%d  UNCHANGED' % year)
            continue
        delta = sum((n - o) for _, o, n in diffs)
        grand += delta
        print('')
        print('%d  %d row(s) move, net %+.2f' % (year, len(diffs), delta))
        # Largest movements first, capped: production may carry hundreds of
        # rows and the net plus the biggest movers is what decides this.
        ordered = sorted(diffs, key=lambda d: abs(d[2] - d[1]), reverse=True)
        for src, o, n in ordered[:CAP]:
            name, lt = labels.get(src, ('(orphan snapshot)', '?'))
            print('     %-22s %-18s id=%-5s  %10s -> %-10s  %+.2f'
                  % (name[:22], lt[:18], src, o, n, n - o))
        if len(ordered) > CAP:
            rest = sum((n - o) for _, o, n in ordered[CAP:])
            print('     ... and %d more row(s), together %+.2f'
                  % (len(ordered) - CAP, rest))
        for src, _o, _n in diffs:
            moved_rows.add(src)

    print('')
    print('=' * 78)
    print('%d of %d source row(s) move in at least one year; net %+.2f overall'
          % (len(moved_rows), len(by_src), grand))
    print('A year listed UNCHANGED reports identically before and after.')
    print('=' * 78)
