"""test_tenant_payment_days - scope rules for the payment-behaviour screen.

    python test_tenant_payment_days.py

Exercises the real tenant_payment_days_view against stubbed data.

The function source is lifted verbatim out of the generated pages/views/tenants.py
and exec'd with stub ORM objects, so this tests the code that actually ships -
not a re-implementation that could agree with a bug.

What is being pinned down is the 1 Aug 2026 cutoff, which has four distinct
cases and it is easy to get one of them backwards:

  pre-cutoff,  marked paid, no paid date  -> invisible entirely
  pre-cutoff,  unpaid                     -> counted and totalled, NOT listed
  in-scope,    paid with a date           -> measured
  in-scope,    unpaid                     -> listed in the unpaid table
"""

import os
import re
import sys
from datetime import date

# Resolve from this file, not the shell's cwd, so it runs from anywhere.
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, 'pages', 'views', 'tenants.py')

if not os.path.exists(TARGET):
    sys.exit('! %s not found - run from the project root' % TARGET)

SRC = open(TARGET, encoding='utf-8').read().replace('\r\n', '\n')

# Pull out the constants and the function body, verbatim.
const = re.search(r'^PAYMENT_GRACE_DAYS = .*?^PAYMENT_DATA_STARTS = date\([^)]*\)',
                  SRC, re.S | re.M)
fn = re.search(r'^def tenant_payment_days_view\(request\):.*?(?=\n\n\n|\Z)', SRC, re.S | re.M)
assert const, 'constants not found in tenants.py'
assert fn, 'view function not found in tenants.py'


class Prop:
    def __init__(self, name):
        self.prop_name = name


class Tenant:
    def __init__(self, tid, name, current='Yes', terms=0):
        self.tenant_id, self.tenant_name = tid, name
        self.tenant_current, self.tenant_payment_terms = current, terms
        self.prop = Prop('Prop %s' % tid)


class Invoice:
    def __init__(self, tenant, d, paid, paid_date, amount):
        self.tenant, self.invoice_date = tenant, d
        self.invoice_paid, self.invoice_paid_date = paid, paid_date
        self.effective_amount = amount


class QS(list):
    """Just enough queryset for this view: filter / order_by / select_related."""

    def select_related(self, *a):
        return self

    def order_by(self, *a):
        return QS(sorted(self, key=lambda o: (getattr(o, 'invoice_date', None)
                                              or getattr(o, 'tenant_name', ''))))

    def filter(self, **kw):
        out = self
        for k, v in kw.items():
            if k == 'tenant':
                out = QS([o for o in out if o.tenant is v])
            elif k == 'tenant_current__iexact':
                out = QS([o for o in out if (o.tenant_current or '').lower() == v.lower()])
            else:
                raise AssertionError('unhandled filter %r - the stub needs updating' % k)
        return out


T_MEASURED = Tenant(1, 'Measured Tenant')
T_ONLY_OLD = Tenant(2, 'Only Old History')
T_OLD_DEBT = Tenant(3, 'Owes From June')
T_PAST = Tenant(4, 'Past Tenant', current='No')

INVOICES = [
    # pre-cutoff, marked paid but no date -> must vanish
    Invoice(T_MEASURED, date(2026, 7, 1), 'Yes', None, 1000),
    # in-scope, paid with a date -> the one measurement
    Invoice(T_MEASURED, date(2026, 8, 1), 'Yes', date(2026, 8, 14), 1000),

    # only pre-cutoff history -> tenant absent, counted
    Invoice(T_ONLY_OLD, date(2026, 6, 1), 'Yes', None, 800),
    Invoice(T_ONLY_OLD, date(2026, 7, 1), 'Yes', None, 800),

    # pre-cutoff and STILL UNPAID -> counted + totalled, never listed
    Invoice(T_OLD_DEBT, date(2026, 6, 1), 'No', None, 640),
    # in-scope and unpaid -> listed
    Invoice(T_OLD_DEBT, date(2026, 8, 1), 'No', None, 660),

    Invoice(T_PAST, date(2026, 8, 1), 'Yes', date(2026, 8, 3), 500),
]


class Objects:
    def __init__(self, rows):
        self.rows = rows

    @property
    def objects(self):
        return QS(self.rows)


class Request:
    def __init__(self, **get):
        self.GET = get


captured = {}


def fake_render(request, template, context):
    captured['template'] = template
    captured['context'] = context
    return context


ns = {
    'date': date,
    'render': fake_render,
    'invoices': Objects(INVOICES),
    'tenant': Objects([T_MEASURED, T_ONLY_OLD, T_OLD_DEBT, T_PAST]),
    'login_required': lambda f: f,
    'permission_required': lambda *a, **k: (lambda f: f),
}
exec(compile(const.group(0), 'consts', 'exec'), ns)
exec(compile(fn.group(0), 'view', 'exec'), ns)
view = ns['tenant_payment_days_view']

ctx = view(Request())
s = ctx['summary']
rows = ctx['rows']
names = [r['tenant'].tenant_name for r in rows]
unpaid_dates = [o['invoice'].invoice_date for o in ctx['outstanding']]

checks = [
    ('cutoff is 1 Aug 2026', ctx['data_starts'] == date(2026, 8, 1)),

    ('only the in-scope measurement counts', s['payments_measured'] == 1),
    ('measured tenant is in the table', names == ['Measured Tenant']),
    ('its one measurement is 13 days',
     rows[0]['measured'][0]['days'] == 13 and rows[0]['n'] == 1),
    ('pre-cutoff paid-with-no-date is invisible',
     all(m['invoice_date'] >= date(2026, 8, 1)
         for r in rows for m in r['measured'])),

    ('tenant with only old history is absent', 'Only Old History' not in names),

    # The "not shown" counter means "awaiting a payment", not "absent". A tenant
    # whose invoices all predate the cutoff is not waiting for anything - their
    # lease ended before the report's era. Counting them made the figure read 19
    # when exactly one tenant was actually pending.
    ('only tenants with an in-scope invoice are counted as pending',
     s['no_measurement_yet'] == 1),

    ('pre-cutoff unpaid is NOT listed', date(2026, 6, 1) not in unpaid_dates),
    ('...but its count is kept', s['old_unpaid_count'] == 1),
    ('...and its money is kept', abs(s['old_unpaid_total'] - 640.0) < 0.005),
    ('in-scope unpaid IS listed', unpaid_dates == [date(2026, 8, 1)]),
    ('unpaid total covers only listed rows',
     abs(s['outstanding_total'] - 660.0) < 0.005),

    ('past tenant excluded by default', 'Past Tenant' not in names),
    ('no_data is gone from the context', 'no_data' not in ctx),
]

# ?all=1 must widen the tenant set without weakening the date cutoff.
ctx_all = view(Request(all='1'))
names_all = [r['tenant'].tenant_name for r in ctx_all['rows']]
checks += [
    ('?all=1 includes past tenants', 'Past Tenant' in names_all),
    ('?all=1 still respects the cutoff',
     all(m['invoice_date'] >= date(2026, 8, 1)
         for r in ctx_all['rows'] for m in r['measured'])),
]

print('')
bad = 0
for label, ok in checks:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d check(s) failed' % bad if bad else 'All %d checks passed.' % len(checks))
sys.exit(1 if bad else 0)
