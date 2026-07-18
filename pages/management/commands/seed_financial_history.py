"""
seed_financial_history — lay down the baseline history rows.

Creates ONE 'seed' history row for every existing budgeted expense and every
existing direct/seasonal revenue, stamped with a baseline effective date so the
P&L can resolve past years immediately. Idempotent: a source row that already
has a 'seed' row is skipped, so re-running is safe.

Why the default date is 1 Jan 2024: today we hold only the CURRENT budget
figures, so both 2024 and 2025 must resolve to that same baseline until real
changes accumulate going forward. Seeding at the start of 2024 makes the
immediate 2024-vs-2025 comparison work. Override with --effective if you want a
different anchor, or hand-add an earlier-dated row later to make a year differ.

    python manage.py seed_financial_history --dry-run
    python manage.py seed_financial_history
    python manage.py seed_financial_history --effective 2024-01-01
"""
from datetime import datetime, date

from django.core.management.base import BaseCommand
from django.db import transaction

from pages.models import (
    expense, revenue,
    FinancialFigureHistory,
    record_expense_history, record_revenue_history,
)

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


class Command(BaseCommand):
    help = "Seed baseline FinancialFigureHistory rows from current budgeted expenses and revenue."

    def add_arguments(self, parser):
        parser.add_argument('--effective', type=str, default='2024-01-01',
                            help='Baseline effective date (YYYY-MM-DD). Default 2024-01-01.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be seeded; write nothing.')

    def handle(self, *args, **o):
        try:
            eff = datetime.strptime(o['effective'], '%Y-%m-%d').date()
        except ValueError:
            self.stderr.write("Bad --effective date; use YYYY-MM-DD.")
            return
        dry = o['dry_run']

        seeded_exp_pks = set(FinancialFigureHistory.objects
                             .filter(kind=FinancialFigureHistory.KIND_BUDGET, source='seed')
                             .values_list('source_pk', flat=True))
        seeded_rev_pks = set(FinancialFigureHistory.objects
                             .filter(kind=FinancialFigureHistory.KIND_REVENUE, source='seed')
                             .values_list('source_pk', flat=True))

        exp_rows = [e for e in expense.objects.select_related('prop', 'expense_line_types').all()
                    if e.expense_id not in seeded_exp_pks]
        rev_rows = [r for r in revenue.objects.select_related('prop', 'revenue_line_types').all()
                    if r.revenue_id not in seeded_rev_pks]

        self.stdout.write('')
        self.stdout.write('Baseline effective date : %s' % eff.isoformat())
        self.stdout.write('Budgeted expenses to seed: %d  (skipping %d already seeded)'
                          % (len(exp_rows), len(seeded_exp_pks)))
        self.stdout.write('Revenue rows to seed     : %d  (skipping %d already seeded)'
                          % (len(rev_rows), len(seeded_rev_pks)))

        if dry:
            for e in exp_rows[:8]:
                self.stdout.write('   would seed EXP  %-22s %-22s amount=%s'
                                  % ((e.prop.prop_name if e.prop else '?')[:22],
                                     str(e.expense_line_types)[:22], e.expense_amount))
            if len(exp_rows) > 8:
                self.stdout.write('   ... and %d more expenses' % (len(exp_rows) - 8))
            self.stdout.write('\n[dry-run] nothing written.')
            return

        made = 0
        with transaction.atomic():
            for e in exp_rows:
                if record_expense_history(e, eff, source='seed', user=None):
                    made += 1
            for r in rev_rows:
                if record_revenue_history(r, eff, source='seed', user=None):
                    made += 1
        self.stdout.write(self.style.SUCCESS('Done. %d baseline history row(s) written.' % made))
