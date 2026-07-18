"""
audit_pl_history — compare the BUDGETED P&L across 2024 / 2025 / 2026 and
highlight (and explain) every cross-year difference. READ-ONLY.

It uses the SAME resolver the P&L uses (resolve_year_months_bulk), so it is the
source of truth for what the P&L should show per year — handy for confirming the
web page (and catching a stale dev server, which will disagree with this).

Put at:  pages/management/commands/audit_pl_history.py

    python manage.py audit_pl_history --prop "Apolloneon"
    python manage.py audit_pl_history --all
    python manage.py audit_pl_history --all --years 2024 2025 2026
"""
from datetime import date

from django.core.management.base import BaseCommand

from pages.models import (
    props, expense, revenue,
    FinancialFigureHistory as H,
    resolve_year_months_bulk,
)


def money(n):
    return '{:,.0f}'.format(float(n or 0))


class Command(BaseCommand):
    help = "Cross-year comparison of the budgeted P&L (read-only), with differences explained."

    def add_arguments(self, parser):
        parser.add_argument('--prop', type=str)
        parser.add_argument('--prop-id', type=int)
        parser.add_argument('--all', action='store_true')
        parser.add_argument('--years', nargs='+', type=int, default=[2024, 2025, 2026])

    def annual_by_line(self, prop, rows, kind, id_attr, lt_attr, mon_prefix, year):
        """{line_label: annual_total} resolved for `year` (falls back to live cells)."""
        vmap = resolve_year_months_bulk([prop.prop_id], kind, year)
        out = {}
        for r in rows:
            vals = vmap.get(getattr(r, id_attr))
            if vals is None:
                vals = [getattr(r, '%s_%s' % (mon_prefix, m)) for m in
                        ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']]
            total = sum(float(v or 0) for v in vals)
            label = str(getattr(r, lt_attr)) if getattr(r, lt_attr) else ('#%d' % getattr(r, id_attr))
            out[label] = out.get(label, 0.0) + total
        return out

    def handle(self, *args, **o):
        years = sorted(set(o['years']))
        qs = props.objects.all().order_by('prop_country', 'prop_name')
        if o.get('prop_id'):
            qs = qs.filter(prop_id=o['prop_id'])
        elif o.get('prop'):
            qs = qs.filter(prop_name__icontains=o['prop'])
        elif not o.get('all'):
            self.stdout.write('Choose:  --prop "name" | --prop-id N | --all')
            return
        plist = list(qs)
        if not plist:
            self.stdout.write('No matching property.')
            return

        portfolio = {y: {'rev': 0.0, 'exp': 0.0} for y in years}
        total_diffs = 0

        for p in plist:
            exp_rows = list(expense.objects.filter(prop=p).select_related('expense_line_types'))
            rev_rows = list(revenue.objects.filter(prop=p).select_related('revenue_line_types'))
            if not exp_rows and not rev_rows:
                continue

            exp_by_year = {y: self.annual_by_line(p, exp_rows, H.KIND_BUDGET,
                            'expense_id', 'expense_line_types', 'expense', y) for y in years}
            rev_by_year = {y: self.annual_by_line(p, rev_rows, H.KIND_REVENUE,
                            'revenue_id', 'revenue_line_types', 'revenue', y) for y in years}

            bar = '=' * (30 + 12 * len(years))
            self.stdout.write('')
            self.stdout.write(bar)
            self.stdout.write('PROPERTY:  %s%s' % (p.prop_name or '(unnamed)',
                              ('    [%s]' % p.prop_country) if p.prop_country else ''))
            self.stdout.write(bar)

            header = '  %-26s' % 'Budgeted line' + ''.join('%10s' % y for y in years) + '   diff?'
            self.stdout.write(header)
            self.stdout.write('  ' + '-' * (26 + 10 * len(years) + 8))

            diffs = []
            for section, by_year in (('EXPENSES', exp_by_year), ('REVENUE', rev_by_year)):
                self.stdout.write('  %s' % section)
                labels = sorted({lbl for y in years for lbl in by_year[y]})
                for lbl in labels:
                    vals = [by_year[y].get(lbl, 0.0) for y in years]
                    differs = len(set(round(v, 2) for v in vals)) > 1
                    mark = '  <-- differs' if differs else ''
                    if differs:
                        diffs.append((section, lbl, vals))
                    self.stdout.write('    %-24s' % lbl[:24]
                                      + ''.join('%10s' % money(v) for v in vals) + mark)

            # totals
            self.stdout.write('  ' + '-' * (26 + 10 * len(years) + 8))
            rev_tot = [sum(rev_by_year[y].values()) for y in years]
            exp_tot = [sum(exp_by_year[y].values()) for y in years]
            prof = [rev_tot[i] - exp_tot[i] for i in range(len(years))]
            self.stdout.write('  %-26s' % 'BUDGETED REVENUE' + ''.join('%10s' % money(v) for v in rev_tot))
            self.stdout.write('  %-26s' % 'BUDGETED EXPENSES' + ''.join('%10s' % money(v) for v in exp_tot))
            self.stdout.write('  %-26s' % 'BUDGETED PROFIT' + ''.join('%10s' % money(v) for v in prof))
            for i, y in enumerate(years):
                portfolio[y]['rev'] += rev_tot[i]
                portfolio[y]['exp'] += exp_tot[i]

            # explain differences
            self.stdout.write('')
            if not diffs:
                self.stdout.write('  No cross-year differences — this property\'s budget is unchanged across %s.'
                                  % ('/'.join(str(y) for y in years)))
            else:
                total_diffs += len(diffs)
                self.stdout.write('  DIFFERENCES (confirm each is intentional):')
                for section, lbl, vals in diffs:
                    changes = self.explain(p, section, lbl, years, vals)
                    self.stdout.write('   - %s [%s]: %s' % (
                        lbl, section.lower(),
                        ', '.join('%d=%s' % (years[i], money(vals[i])) for i in range(len(years)))))
                    for c in changes:
                        self.stdout.write('       %s' % c)

        # portfolio summary
        self.stdout.write('')
        self.stdout.write('=' * (30 + 12 * len(years)))
        self.stdout.write('PORTFOLIO TOTALS')
        self.stdout.write('  %-26s' % 'Budgeted revenue' + ''.join('%10s' % money(portfolio[y]['rev']) for y in years))
        self.stdout.write('  %-26s' % 'Budgeted expenses' + ''.join('%10s' % money(portfolio[y]['exp']) for y in years))
        self.stdout.write('  %-26s' % 'Budgeted profit'
                          + ''.join('%10s' % money(portfolio[y]['rev'] - portfolio[y]['exp']) for y in years))
        self.stdout.write('')
        self.stdout.write('  %d line(s) differ across years. A difference is CORRECT when it matches a dated'
                          % total_diffs)
        self.stdout.write('  change you made (shown above with its effective date). No differences = budgets')
        self.stdout.write('  identical across those years (expected until you record a dated change).')

    def explain(self, prop, section, label, years, vals):
        """Pull the history trail for this line to show the effective date(s) behind a difference."""
        kind = H.KIND_BUDGET if section == 'EXPENSES' else H.KIND_REVENUE
        rows = list(H.objects.filter(prop=prop, kind=kind, line_type=label)
                    .order_by('effective_date', 'changed_at'))
        out = []
        for r in rows:
            months = [m for m in ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
                      if getattr(r, m)]
            amt = getattr(r, months[0]) if months else r.amount
            out.append('version eff %s [%s] = %s' % (r.effective_date.isoformat(), r.source or '?', money(amt)))
        if not out:
            out.append('(no history rows found for this label — check the seeder ran)')
        return out