"""
lease_coverage_audit — show, per property and year, exactly how lease-driven
Revenue will be worked out: which lease covers each month, at what rent + levies,
where the gaps (vacancies) fall, and where the current-year "assume we keep
renting to year-end" rule fills in. READ-ONLY.

Run this BEFORE switching the P&L revenue to leases, to confirm the historical
lease data is complete. A month showing VACANT where the property was really
rented means a historical lease is missing and should be entered.

Put at:  pages/management/commands/lease_coverage_audit.py

    python manage.py lease_coverage_audit --prop "Foti Pitta"
    python manage.py lease_coverage_audit --all
    python manage.py lease_coverage_audit --all --years 2023 2024 2025 2026

Tags per month:
  [lease]     a real lease covers the 1st of that month
  [assumed]   current-year future month, no later lease -> continued at last rent
  VACANT      no lease and not assumable (past gap, or a gap before a later lease)
  [seasonal]  property has no leases -> revenue from the Financials revenue table
"""
from calendar import monthrange
from datetime import date

from django.core.management.base import BaseCommand

from pages.models import props, tenant, revenue

MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
REVCOL = ['revenue_' + m.lower() for m in MON]


def money(n):
    return '€{:,.0f}'.format(float(n or 0))


def fmtdate(d):
    return d.strftime('%d %b %Y') if d else '—'


class Command(BaseCommand):
    help = "Show lease-driven Revenue per property/year: coverage, rent, levies, gaps (read-only)."

    def add_arguments(self, parser):
        parser.add_argument('--prop', type=str)
        parser.add_argument('--prop-id', type=int)
        parser.add_argument('--all', action='store_true')
        parser.add_argument('--years', nargs='+', type=int, default=[2024, 2025, 2026])

    def resolve_month(self, leases, y, m, today):
        """Return (tag, lease_or_None, rent, levies) for the 1st of month m/year y.

        Rules:
          - a lease overlapping ANY day of the month wins (full rent for that
            month); latest-starting lease wins if two overlap.
          - past months (prior years, or elapsed months of the current year) that
            are uncovered are VACANT (a real void).
          - future months of the CURRENT year that are uncovered:
              * if a later lease is loaded (a gap before it) -> VACANT.
              * else, if the property was rented at some point THIS year (a lease
                ended on/after 1 Jan of the current year) -> ASSUMED continuation
                at that most-recent rent to year-end.
              * else -> VACANT (property not rented this year; a lease may be missing).
          - future YEARS (next-year outlook) follow the same continuation rule, so an
            uncovered future month continues at the current rent when the property is
            rented this year and no later lease overrides it.
        """
        month_start = date(y, m, 1)
        month_end = date(y, m, monthrange(y, m)[1])
        overlapping = [l for l in leases
                       if l.tenant_lease_start_date and l.tenant_lease_end_date
                       and l.tenant_lease_start_date <= month_end
                       and l.tenant_lease_end_date >= month_start]
        if overlapping:
            lease = max(overlapping, key=lambda l: l.tenant_lease_start_date)
            return ('lease', lease, lease.tenant_rent or 0, lease.tenant_levies or 0)

        if (y, m) < (today.year, today.month):
            return ('vacant', None, 0, 0)   # past -> real vacancy; current/future -> continuation

        later = [l for l in leases
                 if l.tenant_lease_start_date and l.tenant_lease_start_date > month_end]
        if later:
            return ('vacant', None, 0, 0)

        year_start = date(today.year, 1, 1)
        active_this_year = [l for l in leases
                            if l.tenant_lease_end_date and l.tenant_lease_end_date >= year_start]
        if active_this_year:
            last = max(active_this_year, key=lambda l: l.tenant_lease_end_date)
            return ('assumed', last, last.tenant_rent or 0, last.tenant_levies or 0)
        return ('vacant', None, 0, 0)

    def rev_monthly(self, rev_rows):
        per = [0.0] * 12
        for r in rev_rows:
            for i, col in enumerate(REVCOL):
                v = getattr(r, col, 0)
                if v:
                    per[i] += float(v)
        return per

    def handle(self, *args, **o):
        today = date.today()
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

        for p in plist:
            self.stdout.write('\n' + '=' * 72)
            self.stdout.write('PROPERTY:  %s%s' % (p.prop_name or '(unnamed)',
                              ('    [%s]' % p.prop_country) if p.prop_country else ''))
            self.stdout.write('=' * 72)
            leases = list(tenant.objects.filter(prop=p).order_by('tenant_lease_start_date'))

            if not leases:
                rev_rows = list(revenue.objects.filter(
                    prop=p, revenue_line_types__revenue_line_types_name__iregex=r'rental|levies'))
                per = self.rev_monthly(rev_rows)
                self.stdout.write('  [seasonal / no leases] Revenue comes from the Financials revenue table:')
                self.stdout.write('    ' + ('  '.join('%s %s' % (MON[i], money(per[i]))
                                  for i in range(12) if per[i]) or '(none)'))
                self.stdout.write('    Full-year revenue: %s' % money(sum(per)))
                continue

            # lease list for reference
            self.stdout.write('  Leases on record:')
            for l in leases:
                self.stdout.write('    %-22s %s -> %s   rent %s  levies %s' % (
                    (l.tenant_name or 'Unnamed')[:22],
                    fmtdate(l.tenant_lease_start_date), fmtdate(l.tenant_lease_end_date),
                    money(l.tenant_rent), money(l.tenant_levies)))

            for y in years:
                is_cur = (y == today.year)
                self.stdout.write('')
                self.stdout.write('  %d%s' % (y, '   (in progress)' if y == today.year else ('   (future — outlook)' if y > today.year else '   (complete)')))
                rent_tot = lev_tot = 0.0
                gaps = []
                for m in range(1, 13):
                    tag, lease, rent, lev = self.resolve_month(leases, y, m, today)
                    rent_tot += float(rent); lev_tot += float(lev)
                    future = (y, m) >= (today.year, today.month)
                    if tag == 'lease':
                        who = (lease.tenant_name or 'Unnamed')[:20]
                        label = '[lease]' + (' (projected)' if future else '')
                    elif tag == 'assumed':
                        who = (lease.tenant_name or 'Unnamed')[:20]
                        label = '[assumed — continued to year-end]'
                    else:
                        who = 'VACANT'
                        label = '(projected)' if future else ''
                        gaps.append(MON[m - 1])
                    self.stdout.write('    %-4s %-22s rent %8s  levies %7s   %s'
                                      % (MON[m - 1], who, money(rent), money(lev), label))
                self.stdout.write('    %-4s %-22s rent %8s  levies %7s   TOTAL %s'
                                  % ('', 'YEAR', money(rent_tot), money(lev_tot),
                                     money(rent_tot + lev_tot)))
                if gaps:
                    self.stdout.write('    Vacant months: %s  (confirm these were truly empty; '
                                      'otherwise a lease is missing)' % ', '.join(gaps))