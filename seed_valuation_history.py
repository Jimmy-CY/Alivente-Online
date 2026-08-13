"""
seed_valuation_history — lay down the baseline effective-dated valuation rows.

Property valuations (prop_values.current_value) were stored undated. This creates
ONE 'seed' valuation history row per property that has a current value, stamped
with that property's START DATE, so the Financial-Indicators "Value Increase %"
resolves for every year the property has been held (constant until a real dated
valuation is entered later).

Start date per property:
  - Leased property     -> its FIRST-EVER lease start date (min lease start).
  - Seasonal / no-lease -> the earliest first-lease date across the whole
                           portfolio (so it lines up with everything else);
                           if there are no leases at all, --default-year 1 Jan.

Idempotent: a property that already has a 'valuation' 'seed' row is skipped, so
re-running is safe. Real dated valuations you enter on the edit form are separate
('valuation' source) and are never touched.

    python manage.py seed_valuation_history --dry-run
    python manage.py seed_valuation_history
    python manage.py seed_valuation_history --default-year 2020
"""
from collections import defaultdict
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from pages.models import (
    props, prop_values, tenant,
    FinancialFigureHistory, KIND_VALUATION,
    record_valuation_history,
)


class Command(BaseCommand):
    help = "Seed baseline effective-dated valuation rows (one per property) from each property's start date."

    def add_arguments(self, parser):
        parser.add_argument('--default-year', type=int, default=2020,
                            help='Fallback year (1 Jan) for properties with no leases anywhere. Default 2020.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be seeded; write nothing.')

    def handle(self, *args, **o):
        dry = o['dry_run']
        default_year = o['default_year']

        # First lease-start date per property, and the portfolio's earliest.
        lease_starts = defaultdict(list)
        for t in tenant.objects.all():
            if getattr(t, 'tenant_lease_start_date', None):
                lease_starts[t.prop_id].append(t.tenant_lease_start_date)
        all_starts = [d for lst in lease_starts.values() for d in lst]
        portfolio_earliest = min(all_starts) if all_starts else date(default_year, 1, 1)

        # Properties already seeded (skip on re-run).
        already = set(FinancialFigureHistory.objects
                      .filter(kind=KIND_VALUATION, source='seed')
                      .values_list('source_pk', flat=True))

        pvs = list(prop_values.objects.select_related('prop').all())
        to_seed = []
        for pv in pvs:
            if pv.prop_values_current_value is None:
                continue
            if pv.prop_values_id in already:
                continue
            starts = lease_starts.get(pv.prop_id)
            anchor = min(starts) if starts else portfolio_earliest
            to_seed.append((pv, anchor, 'lease-start' if starts else 'portfolio-earliest'))

        self.stdout.write('')
        self.stdout.write('Portfolio earliest lease start : %s' % portfolio_earliest.isoformat())
        self.stdout.write('Valuations to seed             : %d  (skipping %d already seeded)'
                          % (len(to_seed), len(already)))

        if not to_seed:
            self.stdout.write(self.style.SUCCESS('Nothing to seed.'))
            return

        for pv, anchor, basis in to_seed:
            name = (pv.prop.prop_name if pv.prop else '?') or ('Property %s' % pv.prop_id)
            self.stdout.write('   %-26s value=%-10s eff %s  (%s)'
                              % (name[:26], pv.prop_values_current_value, anchor.isoformat(), basis))

        if dry:
            self.stdout.write('\n[dry-run] nothing written.')
            return

        made = 0
        with transaction.atomic():
            for pv, anchor, _basis in to_seed:
                if record_valuation_history(pv, anchor, source='seed', user=None):
                    made += 1
        self.stdout.write(self.style.SUCCESS('Done. %d baseline valuation row(s) written.' % made))