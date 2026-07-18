"""
analysis_audit — a plain-English proof of the Expenses-vs-Rent Analysis figures.

READ-ONLY. It changes nothing. For a property it shows, in simple terms, exactly
where every number on the Analysis graph comes from:

  Step 1  the leases on record          (check against your Tenants screen)
  Step 2  who paid rent each month, and how much  -> the Rent total
  Step 3  the ad-hoc expenses, and which ones count (Approved AND Paid) -> Actual
  Step 4  the final numbers the graph uses, and the change vs the year before

Put this file at:  pages/management/commands/analysis_audit.py

Then run, for example:

    python manage.py analysis_audit --prop "Foti Pitta"
    python manage.py analysis_audit --prop "Athens - Second Floor" --years 2024 2025 2026
    python manage.py analysis_audit --prop-id 5
    python manage.py analysis_audit --all
"""
from datetime import date

from django.core.management.base import BaseCommand

from pages.models import props, tenant, act_expense, revenue

MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
REVCOL = ['revenue_' + m.lower() for m in MON]


def money(n):
    return '€{:,.0f}'.format(float(n or 0))


def fmtdate(d):
    return d.strftime('%d %b %Y') if d else '—'


class Command(BaseCommand):
    help = "Plain-English proof of a property's Analysis figures (read-only)."

    def add_arguments(self, parser):
        parser.add_argument('--prop', type=str, help='Property name (partial match is fine).')
        parser.add_argument('--prop-id', type=int, help='Property id.')
        parser.add_argument('--all', action='store_true', help='Every property in turn.')
        parser.add_argument('--years', nargs='+', type=int, help='Specific years to show.')

    # ---- data helpers --------------------------------------------------
    def monthly(self, leases, y, m):
        """Which lease covered the 1st of month m/year y, and its monthly amount
        (rent + levies). Returns (lease_or_None, amount)."""
        d = date(y, m, 1)
        cover = [l for l in leases
                 if l.tenant_lease_start_date and l.tenant_lease_end_date
                 and l.tenant_lease_start_date <= d <= l.tenant_lease_end_date]
        if not cover:
            return None, 0.0
        lease = max(cover, key=lambda l: l.tenant_lease_start_date)
        return lease, float((lease.tenant_rent or 0) + (lease.tenant_levies or 0))

    def rev_monthly(self, rev_rows):
        per = [0.0] * 12
        for r in rev_rows:
            for i, col in enumerate(REVCOL):
                v = getattr(r, col, 0)
                if v:
                    per[i] += float(v)
        return per

    def rent_total(self, leases, has_lease, rev_rows, y, upto):
        """Sum the monthly rent Jan..upto. Returns (total, months_let, rows)."""
        rows, total, let = [], 0.0, 0
        per = None if has_lease else self.rev_monthly(rev_rows)
        for m in range(1, upto + 1):
            if has_lease:
                lease, amt = self.monthly(leases, y, m)
                who = (lease.tenant_name or 'Unnamed tenant') if lease else '(empty — no tenant)'
            else:
                amt = per[m - 1]
                who = 'Seasonal revenue' if amt else '(no revenue this month)'
            if amt:
                total += amt
                let += 1
            rows.append(('%s %d' % (MON[m - 1], y), who, amt))
        return total, let, rows

    def expenses(self, p, y, upto):
        """All act_expense rows in Jan..upto of year y. Returns (counted_total, listing)."""
        qs = (act_expense.objects
              .filter(prop=p, act_expense_date__year=y, act_expense_date__month__lte=upto)
              .order_by('act_expense_date'))
        counted, listing = 0.0, []
        for e in qs:
            ok = (e.act_expense_approved == 'Yes' and e.act_expense_paid == 'Yes')
            if ok:
                counted += float(e.act_expense_amount or 0)
            listing.append((e, ok))
        return counted, listing

    # ---- command entry -------------------------------------------------
    def handle(self, *args, **o):
        today = date.today()
        cutoff = today.month - 1     # last completed month of the current year
        cur = today.year

        qs = props.objects.all().order_by('prop_country', 'prop_name')
        if o.get('prop_id'):
            qs = qs.filter(prop_id=o['prop_id'])
        elif o.get('prop'):
            qs = qs.filter(prop_name__icontains=o['prop'])
        elif not o.get('all'):
            self.stdout.write('Please choose a property:  --prop "name"  |  --prop-id N  |  --all')
            return

        plist = list(qs)
        if not plist:
            self.stdout.write('No matching property found.')
            return

        self.stdout.write('')
        self.stdout.write('HOW TO READ THIS: each number the graph shows is built up below from your')
        self.stdout.write('own leases and expenses. If Step 1 matches your Tenants screen and Step 3')
        self.stdout.write('matches your Expenses screen, then the totals in Step 4 are proven correct.')

        for i, p in enumerate(plist):
            self.stdout.write('\n')
            self.audit(p, o.get('years'), cutoff, cur)

    # ---- one property --------------------------------------------------
    def audit(self, p, years, cutoff, cur):
        w = self.stdout.write
        leases = list(tenant.objects.filter(prop=p).order_by('-tenant_lease_start_date'))
        has_lease = bool(leases)
        rev_rows = [] if has_lease else list(revenue.objects.filter(
            prop=p, revenue_line_types__revenue_line_types_name__iregex=r'rental|levies'))

        # Which years to show
        if years:
            yrs = sorted(set(years))
        else:
            yset = set(d.year for d in act_expense.objects.filter(prop=p)
                       .exclude(act_expense_date__isnull=True)
                       .dates('act_expense_date', 'year'))
            for l in leases:
                if l.tenant_lease_start_date and l.tenant_lease_end_date:
                    for yy in range(l.tenant_lease_start_date.year,
                                    min(l.tenant_lease_end_date.year, cur) + 1):
                        yset.add(yy)
            yrs = sorted(y for y in yset if y <= cur) or [cur]

        bar = '=' * 70
        w(bar)
        w('PROPERTY:  %s%s' % (p.prop_name or '(unnamed)',
                               ('    [%s]' % p.prop_country) if p.prop_country else ''))
        w('Rent comes from: %s' % (
            "the tenants' leases below (each month = rent + levies)."
            if has_lease else
            "the Financials revenue table (Rental + Levies lines) — seasonal."))
        w(bar)

        # STEP 1 — leases (or revenue)
        if has_lease:
            w('')
            w('STEP 1 — Leases on record   (tick these off against your Tenants screen)')
            w('')
            w('  %-24s %-12s %-12s %10s %10s %10s' %
              ('Tenant', 'Starts', 'Ends', 'Rent/mo', 'Levies/mo', 'Total/mo'))
            w('  ' + '-' * 80)
            for l in leases:
                tot = (l.tenant_rent or 0) + (l.tenant_levies or 0)
                w('  %-24s %-12s %-12s %10s %10s %10s' % (
                    (l.tenant_name or 'Unnamed')[:24],
                    fmtdate(l.tenant_lease_start_date),
                    fmtdate(l.tenant_lease_end_date),
                    money(l.tenant_rent), money(l.tenant_levies), money(tot)))
        else:
            per = self.rev_monthly(rev_rows)
            w('')
            w('STEP 1 — Seasonal revenue on record (Rental + Levies lines)')
            w('  ' + ('  '.join('%s %s' % (MON[i], money(per[i])) for i in range(12) if per[i])
                      or '(none)'))
            w('  Full-year revenue total: %s' % money(sum(per)))

        # Per-year proof
        for y in yrs:
            ytd = (y == cur)
            upto = cutoff if ytd else 12
            if ytd and cutoff < 1:
                continue  # in January nothing has completed yet
            basis = ('Year-to-date, Jan–%s %d' % (MON[cutoff - 1], y)) if ytd \
                else ('Full year %d' % y)
            denom = upto

            w('')
            w('-' * 70)
            w('  %d   —   %s' % (y, basis))
            if ytd:
                w('  (Only Jan–%s is counted, because %d is not finished yet.)'
                  % (MON[cutoff - 1], y))
            w('-' * 70)

            # STEP 2 — rent month by month
            total, let, rows = self.rent_total(leases, has_lease, rev_rows, y, upto)
            w('')
            w('  STEP 2 — Who paid rent each month, and how much:')
            for (mlabel, who, amt) in rows:
                w('    %-9s  %-28s %10s' % (mlabel, who, money(amt)))
            w('    %-9s  %-28s %10s' % ('', 'RENT TOTAL', money(total)))
            w('    Months with a paying tenant: %d of %d' % (let, denom))

            ptotal, _plet, _pr = self.rent_total(leases, has_lease, rev_rows, y - 1, upto)
            if ptotal:
                dpct = (total - ptotal) / ptotal * 100.0
                w('    Rent change vs %d (same period, %s): %s%.1f%%'
                  % (y - 1, money(ptotal), '+' if dpct >= 0 else '', dpct))
            else:
                w('    Rent change vs %d: — (no rent recorded that period)' % (y - 1))

            # STEP 3 — expenses
            counted, listing = self.expenses(p, y, upto)
            w('')
            w('  STEP 3 — Ad-hoc expenses  (only "Approved AND Paid" ones count):')
            if not listing:
                w('    (none recorded for this period)')
            else:
                for (e, ok) in listing:
                    if ok:
                        tag = 'counts'
                    elif e.act_expense_approved != 'Yes':
                        tag = 'excluded — not approved'
                    else:
                        tag = 'excluded — not paid'
                    w('    %-12s %-26s %10s   [%s]' % (
                        fmtdate(e.act_expense_date),
                        (e.act_expense_description or '')[:26],
                        money(e.act_expense_amount), tag))
            w('    ACTUAL (the ones that count) = %s' % money(counted))

            # STEP 4 — the graph's numbers
            pct = (counted / total * 100.0) if total else None
            w('')
            w('  STEP 4 — The numbers the graph shows for %d:' % y)
            w('    Rent      = %s   (%d of %d months let)' % (money(total), let, denom))
            w('    Actual    = %s' % money(counted))
            w('    %% of rent = %s' % ('%.1f%%' % pct if pct is not None else '—'))

        w('')
        w('  PROVEN when: Step 1 matches your Tenants screen, Step 3 matches your')
        w('  Expenses screen (Approved + Paid), and Step 4 matches the graph/table.')