"""
tenant_payment_days - how quickly does each tenant actually pay?

Read-only. Writes nothing, sends nothing.

    python manage.py tenant_payment_days              # current tenants
    python manage.py tenant_payment_days --all        # include past tenants
    python manage.py tenant_payment_days --detail     # list every invoice
    python manage.py tenant_payment_days --months 12  # only the last N months

Measures `invoice_paid_date - invoice_date` per invoice and summarises it per
tenant, against the payment terms agreed in their lease
(`tenant.tenant_payment_terms`).

Scope starts hard at DATA_STARTS
--------------------------------
Nothing dated earlier is in scope. The paid date only began being recorded when
the feature went live, so every earlier invoice can say exactly one thing -
unknown - and a list of unknowns is not information.

The single exception is money. An unpaid invoice from before the cutoff is
still a debt, so it is counted and totalled rather than dropped; it just is not
listed, because it illustrates no payment behaviour.

Reading the numbers
-------------------
Rent is monthly, so each tenant yields roughly one data point a month: expect
this to become meaningful around six months in, and genuinely interesting after
a year. `n` is printed on every row so a thin average is never mistaken for a
solid one.

Terms of 0 days is a real answer - due on the invoice date - so every test here
is `is not None`, never truthiness. Across this portfolio every tenant is on
0-day terms, which is exactly why a truthiness test would have emptied the
whole VS TERMS column.

The paid date is stamped when the invoice is marked Paid. At Alivente the bank
is checked and invoices marked daily, so that is a faithful proxy for the date
the money arrived.
"""

from datetime import date

from django.core.management.base import BaseCommand

from pages.models import invoices, tenant

BAR = '=' * 100

# Nothing before this date is in scope. See the module docstring.
DATA_STARTS = date(2026, 8, 1)

# Days past the agreed terms before a tenant is called slow. Not zero: terms
# across this portfolio are 0 (rent due on the invoice date), so a knife-edge
# at zero would flag everyone who pays on the 2nd rather than the 1st. A week
# absorbs weekends and bank value dating without hiding real drift.
GRACE_DAYS = 7


def _median(values):
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


class Command(BaseCommand):
    help = 'Average days each tenant takes to pay, measured against their agreed terms.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true',
                            help='Include past tenants, not just current ones.')
        parser.add_argument('--detail', action='store_true',
                            help='List every measured invoice per tenant.')
        parser.add_argument('--months', type=int, default=None,
                            help='Only invoices dated within the last N months.')

    def handle(self, *args, **opts):
        today = date.today()

        # --months narrows the window; it can never widen it past DATA_STARTS.
        floor = DATA_STARTS
        if opts['months']:
            months = opts['months']
            year = today.year - ((12 - today.month + months) // 12)
            month = today.month - months % 12
            if month <= 0:
                month += 12
                year -= 1
            floor = max(floor, date(year, month, 1))

        tenants = tenant.objects.select_related('prop').order_by('tenant_name')
        if not opts['all']:
            tenants = tenants.filter(tenant_current__iexact='Yes')

        self.stdout.write(BAR)
        self.stdout.write('TENANT PAYMENT BEHAVIOUR - days from invoice date to payment')
        self.stdout.write('In scope from %s onwards. Earlier invoices had no paid date '
                          'recorded and are excluded.' % floor.isoformat())
        self.stdout.write(BAR)

        rows, outstanding_rows = [], []
        no_measurement_yet = []
        old_unpaid_count, old_unpaid_total = 0, 0.0

        for t in tenants:
            measured = []
            for inv in invoices.objects.filter(tenant=t).order_by('invoice_date'):
                if inv.invoice_date is None:
                    continue

                in_scope = inv.invoice_date >= floor
                is_paid = (inv.invoice_paid or '').strip().lower() == 'yes'

                if in_scope and inv.invoice_paid_date:
                    measured.append((inv.invoice_date, inv.invoice_paid_date,
                                     (inv.invoice_paid_date - inv.invoice_date).days,
                                     inv.effective_amount))

                if not is_paid:
                    if in_scope:
                        outstanding_rows.append((t, inv, (today - inv.invoice_date).days))
                    else:
                        old_unpaid_count += 1
                        old_unpaid_total += float(inv.effective_amount or 0)

            if not measured:
                no_measurement_yet.append(t)
                continue

            days = [m[2] for m in measured]
            terms = t.tenant_payment_terms
            rows.append({
                'tenant': t,
                'n': len(days),
                'avg': sum(days) / float(len(days)),
                'median': _median(days),
                'best': min(days),
                'worst': max(days),
                'last': days[-1],
                'terms': terms,
                # `is not None`, not a truth test: 0 days is a real answer
                # ("due on the invoice date"), not a missing one. Treating it
                # as unset silently hid every tenant who pays on presentation.
                'vs_terms': (sum(days) / float(len(days)) - terms) if terms is not None else None,
                'measured': measured,
            })

        if not rows:
            self.stdout.write('')
            self.stdout.write('No measurable payments yet. Every measured payment needs an')
            self.stdout.write('invoice dated %s or later with a paid date against it.'
                              % floor.isoformat())
        else:
            # Slowest first - that is the order worth reading.
            rows.sort(key=lambda r: r['avg'], reverse=True)

            self.stdout.write('')
            self.stdout.write('%-28s %-20s %3s %7s %7s %5s %6s %6s %9s'
                              % ('TENANT', 'PROPERTY', 'n', 'AVG', 'MEDIAN',
                                 'BEST', 'WORST', 'LAST', 'VS TERMS'))
            self.stdout.write('-' * 100)
            for r in rows:
                t = r['tenant']
                vs = ('%+.1f' % r['vs_terms']) if r['vs_terms'] is not None else '  n/a'
                line = ('%-28s %-20s %3d %7.1f %7.1f %5d %6d %6d %9s'
                        % ((t.tenant_name or '')[:28], (t.prop.prop_name or '')[:20],
                           r['n'], r['avg'], r['median'], r['best'], r['worst'],
                           r['last'], vs))
                if r['vs_terms'] is None:
                    self.stdout.write(line)
                elif r['vs_terms'] > GRACE_DAYS * 2:
                    self.stdout.write(self.style.ERROR(line))
                elif r['vs_terms'] > GRACE_DAYS:
                    self.stdout.write(self.style.WARNING(line))
                else:
                    self.stdout.write(self.style.SUCCESS(line))

            self.stdout.write('-' * 100)
            self.stdout.write('n = payments measured.  VS TERMS = average minus the agreed '
                              'payment terms on the lease;')
            self.stdout.write('positive means slower than agreed. Flagged only beyond a '
                              '%d-day grace: green within,' % GRACE_DAYS)
            self.stdout.write('amber to %d days, red beyond.  Rows with n below about 6 are '
                              'indicative only.' % (GRACE_DAYS * 2))

            if opts['detail']:
                self.stdout.write('')
                self.stdout.write(BAR)
                self.stdout.write('EVERY MEASURED PAYMENT')
                for r in rows:
                    self.stdout.write('')
                    self.stdout.write('%s  (%s)  terms: %s'
                                      % (r['tenant'].tenant_name, r['tenant'].prop.prop_name,
                                         'not set' if r['terms'] is None else r['terms']))
                    for inv_date, paid_date, days, amount in r['measured']:
                        self.stdout.write('    invoiced %s  paid %s  = %3d days   EUR %s'
                                          % (inv_date, paid_date, days, amount))

        # Counted, never silently dropped: a suppressed row that leaves no
        # trace reads as "there was nothing".
        if no_measurement_yet:
            self.stdout.write('')
            self.stdout.write('%d tenant(s) not shown - no payment recorded yet since %s:'
                              % (len(no_measurement_yet), floor.isoformat()))
            for t in no_measurement_yet:
                self.stdout.write('    %-28s %s' % ((t.tenant_name or '')[:28],
                                                    t.prop.prop_name or ''))

        if outstanding_rows:
            outstanding_rows.sort(key=lambda x: x[2], reverse=True)
            self.stdout.write('')
            self.stdout.write(BAR)
            self.stdout.write('CURRENTLY UNPAID - oldest first')
            for t, inv, age in outstanding_rows:
                style = self.style.ERROR if age > 30 else (
                    self.style.WARNING if age > GRACE_DAYS else lambda s: s)
                self.stdout.write(style('    %-28s %-20s invoiced %s  %4d days ago  EUR %s'
                                        % ((t.tenant_name or '')[:28],
                                           (t.prop.prop_name or '')[:20],
                                           inv.invoice_date, age, inv.effective_amount)))

        if old_unpaid_count:
            self.stdout.write('')
            self.stdout.write('    Plus %d unpaid invoice(s) dated before %s, totalling '
                              'EUR %.2f -' % (old_unpaid_count, floor.isoformat(),
                                              old_unpaid_total))
            self.stdout.write('    not listed (they predate the payment tracking), but '
                              'still outstanding.')

        self.stdout.write('')
        self.stdout.write(BAR)
        self.stdout.write('Rent is monthly, so each tenant contributes about one measurement a')
        self.stdout.write('month. Around six is enough to trust an average; a year lets you see')
        self.stdout.write('drift. Until then, read the ranking rather than the absolute numbers.')
        self.stdout.write(BAR)
