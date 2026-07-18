"""
show_financial_history — plain-English proof of the budget/revenue HISTORY and,
crucially, of exactly what the Profit & Loss will show for each year once Phase 2
reads this history. READ-ONLY: it changes nothing.

Put this file at:  pages/management/commands/show_financial_history.py

Run, for example:

    python manage.py show_financial_history --prop "Foti Pitta"
    python manage.py show_financial_history --prop "Foti Pitta" --years 2024 2025 2026
    python manage.py show_financial_history --prop-id 5
    python manage.py show_financial_history --all

It prints three things per property:
  1. THE TRAIL      — every budgeted-expense / revenue version we now keep, with
                      the date each takes effect (this is the append-only record).
  2. THE P&L VIEW   — for each year, the budgeted figure the P&L will use, worked
                      out MONTH BY MONTH so a mid-year change is visible flowing
                      forward. This is what Phase 2 will display.
  3. THE CHECK      — the current live cells vs the resolved current-year total,
                      so you can see they agree (until you make a dated change).
"""
from datetime import date

from django.core.management.base import BaseCommand

from pages.models import (
    props, expense, revenue,
    FinancialFigureHistory as H,
    figure_monthly_value_as_of,
)

MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
LOWER = [m.lower() for m in MON]


def money(n):
    return '€{:,.0f}'.format(float(n or 0))


class Command(BaseCommand):
    help = "Plain-English proof of budget/revenue history and the P&L it will drive (read-only)."

    def add_arguments(self, parser):
        parser.add_argument('--prop', type=str, help='Property name (partial match).')
        parser.add_argument('--prop-id', type=int, help='Property id.')
        parser.add_argument('--all', action='store_true', help='Every property in turn.')
        parser.add_argument('--years', nargs='+', type=int, help='Years to show (default 2024 2025 <this year>).')

    # ---- helpers -------------------------------------------------------
    def months_summary(self, obj):
        """Compact description of the twelve monthly cells on a history row."""
        vals = [getattr(obj, m) for m in LOWER]
        present = [(MON[i], vals[i]) for i in range(12) if vals[i]]
        if not present:
            return '(no monthly amounts)'
        distinct = set(float(v) for _, v in present)
        if len(present) == 12 and len(distinct) == 1:
            return 'every month %s' % money(present[0][1])
        if len(distinct) == 1:
            names = ', '.join(n for n, _ in present)
            return '%s in %s' % (money(present[0][1]), names)
        return ', '.join('%s %s' % (n, money(v)) for n, v in present)

    def resolved_year(self, prop, kind, source_pk, year, live_row=None, live_prefix=None):
        """Twelve monthly figures the P&L will use for this source in `year`.
        Falls back to the live cell for any month with no history yet."""
        out = []
        for m in range(1, 13):
            v = figure_monthly_value_as_of(prop, kind, source_pk, year, m)
            if v is None and live_row is not None:
                v = getattr(live_row, '%s_%s' % (live_prefix, LOWER[m - 1]))
            out.append(float(v or 0))
        return out

    # ---- entry ---------------------------------------------------------
    def handle(self, *args, **o):
        cur = date.today().year
        years = sorted(set(o['years'])) if o.get('years') else [2024, 2025, cur]

        qs = props.objects.all().order_by('prop_country', 'prop_name')
        if o.get('prop_id'):
            qs = qs.filter(prop_id=o['prop_id'])
        elif o.get('prop'):
            qs = qs.filter(prop_name__icontains=o['prop'])
        elif not o.get('all'):
            self.stdout.write('Choose a property:  --prop "name"  |  --prop-id N  |  --all')
            return

        plist = list(qs)
        if not plist:
            self.stdout.write('No matching property found.')
            return

        for p in plist:
            self.stdout.write('\n')
            self.report(p, years, cur)

    # ---- one property --------------------------------------------------
    def report(self, p, years, cur):
        w = self.stdout.write
        bar = '=' * 74
        w(bar)
        w('PROPERTY:  %s%s' % (p.prop_name or '(unnamed)',
                               ('    [%s]' % p.prop_country) if p.prop_country else ''))
        w(bar)

        # live source rows
        exp_rows = list(expense.objects.filter(prop=p).select_related('expense_line_types'))
        rev_rows = list(revenue.objects.filter(prop=p).select_related('revenue_line_types'))

        # ---------- 1. THE TRAIL ----------
        w('')
        w('1) THE TRAIL WE NOW KEEP  (each dated version of a budgeted figure)')
        self._trail(w, p, H.KIND_BUDGET, exp_rows, 'expense_id', 'expense_line_types')
        if rev_rows:
            w('')
            w('   Revenue versions:')
            self._trail(w, p, H.KIND_REVENUE, rev_rows, 'revenue_id', 'revenue_line_types', indent='   ')

        # ---------- 2. THE P&L VIEW ----------
        w('')
        w('2) WHAT THE P&L WILL SHOW  (budgeted expense, worked out month by month)')
        for y in years:
            w('')
            w('   %d' % y)
            grand = [0.0] * 12
            any_line = False
            for e in exp_rows:
                vals = self.resolved_year(p, H.KIND_BUDGET, e.expense_id, y,
                                          live_row=e, live_prefix='expense')
                if sum(vals) == 0:
                    continue
                any_line = True
                grand = [grand[i] + vals[i] for i in range(12)]
                label = str(e.expense_line_types) if e.expense_line_types else ('expense #%d' % e.expense_id)
                w('      %-26s %s   (year %s)' % (label[:26], self._mini(vals), money(sum(vals))))
            if not any_line:
                w('      (no budgeted expenses resolve for this year)')
            w('      %-26s %s   %s' % ('BUDGET TOTAL', ' ' * 0, money(sum(grand))))

        # ---------- 3. THE CHECK ----------
        w('')
        w('3) CHECK  (current live cells vs the resolved %d total)' % cur)
        live_total = 0.0
        for e in exp_rows:
            live_total += sum(float(getattr(e, 'expense_%s' % m) or 0) for m in LOWER)
        resolved_cur = 0.0
        for e in exp_rows:
            resolved_cur += sum(self.resolved_year(p, H.KIND_BUDGET, e.expense_id, cur,
                                                    live_row=e, live_prefix='expense'))
        w('   Live budget cells total : %s' % money(live_total))
        w('   Resolved %d total       : %s' % (cur, money(resolved_cur)))
        w('   %s' % ('MATCH ✔  (no dated change yet, so they agree)'
                     if abs(live_total - resolved_cur) < 0.5
                     else 'DIFFER — a mid-year dated change is in effect (expected once you edit).'))

    def _mini(self, vals):
        """One-line month strip, only showing where the value changes."""
        parts, last = [], None
        for i in range(12):
            if vals[i] != last:
                parts.append('%s %s' % (MON[i], money(vals[i])))
                last = vals[i]
        return ' | '.join(parts)

    def _trail(self, w, p, kind, live_rows, pk_attr, lt_attr, indent=''):
        rows = list(H.objects.filter(prop=p, kind=kind).order_by('source_pk', 'effective_date', 'changed_at'))
        if not rows:
            w('%s   (no history yet — make an edit, or run the seeder)' % indent)
            return
        by_src = {}
        for r in rows:
            by_src.setdefault(r.source_pk, []).append(r)
        for src_pk, versions in by_src.items():
            label = versions[0].line_type or ('#%d' % src_pk)
            w('%s   %s  (source #%d)' % (indent, label, src_pk))
            for r in versions:
                w('%s      eff %s  [%s]  %s' % (
                    indent, r.effective_date.isoformat(), r.source or '?', self.months_summary(r)))