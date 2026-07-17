"""
analysis_report — read-only check of the data behind the Expenses-vs-Rent
Analysis view.

Prints, per property and year: annual rent (collected — the rent of the lease
covering each month, so 0 for vacant months), the "Let" coverage (months a
lease was in force, x/12), actual (ad-hoc) expenses, and actual as a % of rent.
Rent comes from the lease rows for tenanted properties (year-aware); for
seasonal properties with no tenant it falls back to the Financials revenue
"Rental" line (current figure only, until the revenue history table is added).
Nothing is written.

    python manage.py analysis_report
    python manage.py analysis_report --years 2024 2025 2026
"""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum

from pages.models import props, tenant, act_expense, revenue

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def annual_rent_from_leases(prop, year):
    """Collected rent: sum the monthly rent of the lease covering each month
    of `year` (0 for vacant months). Returns (total: Decimal, months_let: int)."""
    total = Decimal('0')
    months_let = 0
    for m in range(1, 13):
        d = date(year, m, 1)
        lease = (tenant.objects
                 .filter(prop=prop,
                         tenant_lease_start_date__lte=d,
                         tenant_lease_end_date__gte=d)
                 .order_by('-tenant_lease_start_date')
                 .first())
        if lease and lease.tenant_rent:
            total += Decimal(lease.tenant_rent)
            months_let += 1
    return total, months_let


def annual_rent_from_revenue(prop):
    """Seasonal / direct fallback: per-month sum across the property's "Rental"
    revenue line(s). Returns (total: Decimal, months_with_rent: int)."""
    per_month = [Decimal('0')] * 12
    rows = revenue.objects.filter(
        prop=prop,
        revenue_line_types__revenue_line_types_name__icontains='rental',
    )
    for r in rows:
        for i, m in enumerate(MONTHS):
            v = getattr(r, f'revenue_{m}')
            if v:
                per_month[i] += Decimal(v)
    total = sum(per_month, Decimal('0'))
    months = sum(1 for v in per_month if v > 0)
    return total, months


class Command(BaseCommand):
    help = "Read-only: rent (collected), months let, actual expenses, % of rent per property/year."

    def add_arguments(self, parser):
        parser.add_argument('--years', nargs='+', type=int,
                            help="Years to report (default: years found in actual expenses).")

    def handle(self, *args, **options):
        years = options.get('years')
        if not years:
            dates = (act_expense.objects
                     .exclude(act_expense_date__isnull=True)
                     .dates('act_expense_date', 'year'))
            years = sorted({d.year for d in dates})
        if not years:
            self.stdout.write("No actual-expense dates found — nothing to report.")
            return

        self.stdout.write(f"Years: {', '.join(str(y) for y in years)}")
        self.stdout.write("")

        header = (f"{'Property':28} {'Year':>4} {'Rent':>12} {'Let':>5} "
                  f"{'Actual':>10} {'% rent':>8}  Rent source")
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        for p in props.objects.all().order_by('prop_country', 'prop_name'):
            printed = False
            for y in years:
                actual = (act_expense.objects
                          .filter(prop=p, act_expense_date__year=y)
                          .aggregate(t=Sum('act_expense_amount'))['t'] or Decimal('0'))

                rent, months_let = annual_rent_from_leases(p, y)
                source = 'lease'
                if months_let == 0:
                    rent, months_let = annual_rent_from_revenue(p)
                    source = 'revenue' if rent else '(none)'

                if rent == 0 and actual == 0:
                    continue  # nothing to show for this property/year

                pct = (Decimal(actual) / rent * 100) if rent else None
                pct_str = f"{pct:.1f}%" if pct is not None else "—"
                let_str = f"{months_let}/12"
                self.stdout.write(
                    f"{(p.prop_name or '')[:28]:28} {y:>4} "
                    f"{rent:>12,.0f} {let_str:>5} {actual:>10,.0f} "
                    f"{pct_str:>8}  {source}")
                printed = True
            if printed:
                self.stdout.write("")

        self.stdout.write(
            "Let = months a lease was in force (x/12). A number below 12 means a "
            "part-year: a mid-year first lease or a vacancy — not a rent cut.")
        self.stdout.write(
            "Rent source: 'lease' is year-accurate; 'revenue' is the seasonal/current "
            "figure (same every year until revenue history is added).")