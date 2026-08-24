"""test_pl_historical - does a sold property keep its past and lose its future?

    python test_pl_historical.py

_lease_month and lease_monthly_rent_levies are lifted verbatim out of
pages/models.py and run against stub leases, so this exercises the shipping
code. The source assertions then check that only the P&L stopped filtering on
prop_status, and that the forward-looking screens still do.

The example: a property let at 1,000/month on a lease running to 30 Jun 2026,
seen from 24 Aug 2026 - so July 2026 onward is a month no lease covers.
"""

import calendar
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
PL = os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html')

for p in (MODELS, FINANCE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

MODELS_SRC = open(MODELS, encoding='utf-8').read().replace('\r\n', '\n')
FIN_SRC = open(FINANCE, encoding='utf-8').read().replace('\r\n', '\n')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def grab(src, name, where):
    m = re.search(r'^def %s\(.*?\n(?=\S)' % re.escape(name), src, re.S | re.M)
    if not m:
        sys.exit('! %s not found in %s - has the patch been applied?'
                 % (name, where))
    return m.group(0)


# ============================================================== the stubs
class Lease:
    def __init__(self, start, end, rent, levies=0):
        self.tenant_lease_start_date = start
        self.tenant_lease_end_date = end
        self.tenant_rent = rent
        self.tenant_levies = levies


class Prop:
    def __init__(self, status):
        self.prop_id = 1
        self.prop_status = status


LEASES = []


class TenantManager:
    def filter(self, **kw):
        return list(LEASES)


class TenantModel:
    objects = TenantManager()


NS = {
    '_fh_date': date,
    '_fh_monthrange': calendar.monthrange,
    'tenant': TenantModel,
}
for name in ('_lease_month', 'lease_monthly_rent_levies'):
    exec(compile(grab(MODELS_SRC, name, 'models.py'), name, 'exec'), NS)

monthly = NS['lease_monthly_rent_levies']
TODAY = date(2026, 8, 24)

# A lease that ran to the end of June 2026 and was not replaced.
LEASES[:] = [Lease(date(2023, 1, 1), date(2026, 6, 30), 1000, 100)]


def year(status, y):
    rent, lev, has = monthly(Prop(status), y, TODAY)
    return sum(rent), sum(lev), has


# ================================================ THE PAST IS UNTOUCHED
for status in ('Active', 'Inactive'):
    r, v, has = year(status, 2025)
    check('%s: 2025 rent is the full 12,000' % status, r == 12000)
    check('%s: 2025 levies are the full 1,200' % status, v == 1200)
    check('%s: it still reads as a leased property' % status, has)

# ================================ THE CURRENT YEAR: REAL MONTHS, THEN PROJECTION
r_active, _, _ = year('Active', 2026)
r_inactive, _, _ = year('Inactive', 2026)
# Jan-Jun are real lease months. July is a PAST month nothing covered, so it
# is a genuine vacancy and stays zero for both. The projection only begins at
# the current month, so Aug-Dec is what differs.
check('Active: 2026 = 6 real + 0 for the past vacancy + 5 projected = 11,000',
      r_active == 11000)
check('Inactive: 2026 = the 6 months it really was let = 6,000',
      r_inactive == 6000)
check('  the difference is exactly the 5 projected months',
      r_active - r_inactive == 5000)

# ============================================ THE FUTURE: NOTHING IS INVENTED
r_active, _, _ = year('Active', 2027)
r_inactive, _, _ = year('Inactive', 2027)
check('Active: 2027 is projected forward (12,000)', r_active == 12000)
check('Inactive: 2027 invents nothing (0)', r_inactive == 0)

# a property with no lease at all is unaffected either way
LEASES[:] = []
for status in ('Active', 'Inactive'):
    r, v, has = year(status, 2026)
    check('%s: no leases -> not a leased property' % status, has is False)
LEASES[:] = [Lease(date(2023, 1, 1), date(2026, 6, 30), 1000, 100)]

# a lease with a missing date matches nothing - unchanged behaviour
LEASES[:] = [Lease(date(2023, 1, 1), None, 1000, 100)]
r, _, _ = year('Active', 2025)
check('a lease with no end date still resolves to nothing', r == 0)
LEASES[:] = [Lease(date(2023, 1, 1), date(2026, 6, 30), 1000, 100)]

# ================================================== WHAT THE SOURCE SAYS
m = re.search(r'all_properties = props\.objects\.([a-z_]+)\(', FIN_SRC)
check('the P&L no longer filters on prop_status (%s)'
      % (m.group(1) if m else 'not found'),
      m and m.group(1) == 'all')

active_filters = (FIN_SRC.count("prop_status='Active'")
                  + FIN_SRC.count('prop_status="Active"'))
check('the forward-looking screens still filter (%d left)' % active_filters,
      active_filters >= 3)

check('models.py suppresses the projection for an inactive property',
      '_projectable' in MODELS_SRC and "== 'Active'" in MODELS_SRC)

if os.path.exists(PL):
    s = open(PL, encoding='utf-8').read()
    check('the picker badges an inactive property', 'pl-inactive-pill' in s)
    check('  and the badge is conditional on status',
          "prop.prop_status != 'Active'" in s)
else:
    check('finance_pl_act.html exists', False)

# ====================================================================== out
print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
