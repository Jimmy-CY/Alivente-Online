# -*- coding: utf-8 -*-
"""test_owned_from.py - round OF-3, 28 Oct 2026.

RELEASE 33 - OWNED FROM. His decisions of 28 October, from the Live
before/after report (Show-OwnedFrom.ps1):

    - Every property has an Owned From date (migration 0112): its first
      lease start - "the date of the first rental for that property as the
      date that we owned it from" - or, for the two seasonal villas, the
      dates he gave: Ionion - Villa 24 2010, Ionion - Villa H4 2014.
      Editable on the property; blank falls back to the first lease.
    - No budget and no revenue counts in a month before it.
    - OPTION B for pro-rata lines: each owned property keeps its own share
      and the share of a property not yet owned drops - "the earlier years
      would be more accurate because we don't burden them with the full
      amount."
    - ONE helper, budget_year_months, behind the P&L, both of its
      drill-downs, the expense matrix and Financial Indicators.
    - Add Expense and Add Revenue suggest the property's Owned From month
      as Applies from when its first lines go on.
    - Ships Show-OwnedFrom.ps1 and Fix-CompanyTaxCent.ps1 (read-only
      report, and the dry-run-first cent fix).
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ownedfrom'
ME = 'test_owned_from.py'
PATCHER = 'apply_owned_from.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'OF-3, 28 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
MODELS = J(ROOT, 'pages', 'models.py')
FORMS = J(ROOT, 'pages', 'forms.py')
FIN = J(ROOT, 'pages', 'views', 'finance.py')
PROPS = J(ROOT, 'pages', 'views', 'properties.py')
PEDIT = J(TPL, 'properties_edit.html')
PADD = J(TPL, 'properties_add.html')
DASH = J(TPL, 'property_detail.html')
PREP = J(TPL, 'property_report.html')
MATRIX = J(TPL, 'finance_expense.html')
EADD = J(TPL, 'finance_expense_add.html')
RADD = J(TPL, 'finance_revenue_add.html')
TMX = J(ROOT, 'test_expense_matrix.py')
TMR = J(ROOT, 'test_matrix_range.py')
TRM = J(ROOT, 'test_req_marker.py')
GATE = J(ROOT, PS1)
EDITED = (MODELS, FORMS, FIN, PROPS, PEDIT, PADD, DASH, PREP, MATRIX, EADD,
          RADD, TMX, TMR, TRM)
MIGRATION = J(ROOT, 'pages', 'migrations', '0112_prop_owned_from.py')
SHIPS = (MIGRATION, J(ROOT, 'Show-OwnedFrom.ps1'),
         J(ROOT, 'Fix-CompanyTaxCent.ps1'))

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402
from alv_rounds import as_left_by                          # noqa: E402

NOW = dict((p, as_left_by(p, SUFFIX, read)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def py(src):
    return T.python_code_only(src)


def claims(src):
    out = []
    m = py(src[MODELS])
    out.append(('prop_owned_from = models.DateField(' in m,
                'the property keeps an Owned From date'))
    out.append((all('def %s(' % f in m for f in (
        'property_owned_from', 'owned_from_map', 'owned_months',
        'apply_owned_from', 'budget_year_months')),
        'one set of helpers decides which months a property owns'))
    out.append(('budget_year_months(prop.expense_set.all(), year)' in m,
                'Financial Indicators counts through it'))
    out.append(('_mask = owned_months(property_owned_from(prop), year)' in m
                and 'def _owned_copy(' in m,
                'revenue rows are held to Owned From, as copies - the '
                'database row is never touched'))
    out.append(('"prop_owned_from",' in py(src[FORMS]),
                'PropForm names it, so a save keeps it'))
    f = py(src[FIN])
    out.append(('_fh_exp_map = budget_year_months(expenses, selected_year)'
                in f, 'the P&L counts through it'))
    out.append(('budget_year_months(expenses, _year_int)' in f
                and 'budget_year_months(budget_expenses, _year_int)' in f,
                '  and so do both drill-downs it opens'))
    out.append(('vals_map, prov_map = budget_year_months(' in f,
                '  and so does the expense matrix'))
    out.append(('"owned_info": _owned_info(expense)' in f
                and '"owned_info": _owned_info(revenue)' in f,
                'Add Expense and Add Revenue are told each property\'s '
                'Owned From'))
    p = py(src[PROPS])
    out.append(('"first_lease": _first_lease,' in p
                and "'prop_owned_from'," in p,
                'Property Edit shows the first lease it falls back to, and '
                'the report fetches the date with the rest'))
    for pth, name in ((PEDIT, 'Property Edit'), (PADD, 'Property Add')):
        t = T.code_only(src[pth])
        out.append(('<input type="date" class="form-control" '
                    'id="prop_owned_from" name="prop_owned_from"' in t,
                    '%s has the Owned From box' % name))
    for pth, name in ((DASH, 'Property Dashboard'), (PREP, 'Property report')):
        out.append(("{{ property.prop_owned_from|date:'j M Y'|default:'First "
                    "lease' }}" in T.code_only(src[pth]),
                    '%s shows it' % name))
    for pth, name in ((EADD, 'Add Expense'), (RADD, 'Add Revenue')):
        t = src[pth]
        out.append(('{{ owned_info|json_script:"alv-owned-from" }}' in t
                    and "eff.addEventListener('input'" in t,
                    '%s suggests Owned From as Applies from, and stops once '
                    'the date is typed' % name))
    out.append(('Owned From</strong> month' in src[MATRIX],
                'the matrix note says it counts from Owned From'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
for p in SHIPS:
    ok(os.path.isfile(p), '%s ships with the round' % os.path.relpath(p, ROOT))
mig = read(MIGRATION) if os.path.isfile(MIGRATION) else ''
ok("('pages', '0111_tenant_id_country')" in mig
   and mig.count('migrations.AddField(') == 1
   and "name='prop_owned_from'" in mig
   and 'migrations.RunPython(fill, migrations.RunPython.noop)' in mig,
   'migration 0112 adds the column after 0111 and fills it')
ok("'Ionion - Villa 24': datetime.date(2010, 1, 1)" in mig
   and "'Ionion - Villa H4': datetime.date(2014, 1, 1)" in mig
   and 'filter(prop_owned_from__isnull=True)' in mig,
   '  with his two villa dates, and only ever into a blank')
dated = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not dated, 'the round dates itself in every file it edited',
   ', '.join(dated))
cent = read(SHIPS[2]) if os.path.isfile(SHIPS[2]) else ''
ok('[switch] $Write' in cent and 'class DryRun(Exception)' in cent
   and 'EXPECT = 10' in cent,
   'the cent fix is a dry run unless -Write, and refuses unless it finds '
   'exactly ten snapshots')
rep = read(SHIPS[1]) if os.path.isfile(SHIPS[1]) else ''
ok(not re.search(r'\.(save|delete|update|create)\(', rep),
   'the Owned From report writes nothing')

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round\'s claims held before it',
   '\n'.join(held))

# ==========================================================================
head('3. DRIVEN - the months, the shares, the screens')
# ==========================================================================


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.contrib.auth.models import User
    from django.db import connection, transaction
    from django.test import Client
    import pages.models as M
    connection.ensure_connection()
    M.props.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    import datetime as dt
    import json
    from decimal import Decimal as D
    from pages.views.finance import expense_matrix
    try:
        with transaction.atomic():
            mk = lambda n, **k: M.props.objects.create(               # noqa
                prop_name=n, prop_country='Cyprus', prop_status='Active',
                **k)
            a = mk('OF3 Early')                       # lease 2016-02
            b = mk('OF3 Late')                        # lease 2024-10-15
            c = mk('OF3 Seasonal', prop_owned_from=dt.date(2010, 1, 1))
            d = mk('OF3 Typed', prop_owned_from=dt.date(2020, 6, 9))
            e = mk('OF3 Nothing')                     # no lease, no date
            L = dict(tenant_type='Individual', tenant_current='Yes',
                     tenant_rental_type='Monthly')
            M.tenant.objects.create(prop=a, tenant_name='x',
                                    tenant_lease_start_date=dt.date(2016, 2, 25),
                                    tenant_lease_end_date=dt.date(2030, 1, 1), **L)
            M.tenant.objects.create(prop=b, tenant_name='y',
                                    tenant_lease_start_date=dt.date(2024, 10, 15),
                                    tenant_lease_end_date=dt.date(2030, 1, 1), **L)
            M.tenant.objects.create(prop=d, tenant_name='z',
                                    tenant_lease_start_date=dt.date(2015, 1, 1),
                                    tenant_lease_end_date=dt.date(2030, 1, 1), **L)

            of = M.owned_from_map([a.pk, b.pk, c.pk, d.pk, e.pk])
            ok(of[a.pk] == dt.date(2016, 2, 25) and of[b.pk] ==
               dt.date(2024, 10, 15),
               'no date typed: Owned From is the first lease start')
            ok(of[c.pk] == dt.date(2010, 1, 1),
               '  a typed date with no lease is used')
            ok(of[d.pk] == dt.date(2020, 6, 9),
               '  a typed date wins over an earlier lease')
            ok(of[e.pk] is None and M.property_owned_from(e) is None,
               '  and no lease, no date is "owned all along"')
            ok(M.owned_months(dt.date(2024, 10, 15), 2024) ==
               [False] * 9 + [True] * 3,
               'any part of a month counts as the month (15 Oct -> Oct)')
            ok(M.owned_months(None, 1999) == [True] * 12,
               '  and owned all along means every month')

            lt = M.expense_line_types.objects.create(
                expense_line_types_name='OF3 Company Tax',
                expense_line_types_prorata='Yes')
            et = M.expense_types.objects.create(
                expense_types_name='OF3 Six Monthly')
            rows = {}
            for p, amt in ((a, '100.00'), (b, '200.00'), (c, '300.00'),
                           (d, '400.00'), (e, '500.00')):
                rows[p.pk] = M.expense.objects.create(
                    prop=p, expense_line_types=lt, expense_types=et,
                    expense_jan=D(amt), expense_jul=D(amt))

            def tot(year):
                mm = M.budget_year_months(M.expense.objects.filter(
                    expense_line_types=lt), year)
                return dict((pid, sum(mm[r.expense_id], D('0')))
                            for pid, r in rows.items())
            t16, t24, t25 = tot(2016), tot(2024), tot(2025)
            ok(t16[a.pk] == D('100.00'),
               'OPTION B: Early carries only July of 2016 - its January '
               'share drops, it is not handed anybody else\'s')
            ok(t16[b.pk] == 0 and t16[d.pk] == 0,
               '  a property not yet owned carries no share at all')
            ok(t16[c.pk] == D('600.00') and t16[e.pk] == D('1000.00'),
               '  and an owned property keeps exactly its own share - '
               'nothing is re-split onto it')
            ok(sum(t16.values()) == D('1700.00'),
               '  so the 2016 company total is smaller than the charge '
               '(1,700 of 3,000)', str(sum(t16.values())))
            ok(t24[b.pk] == 0 and t25[b.pk] == D('400.00'),
               'Late (first lease Oct 2024) carries nothing in 2024 - its '
               'months are Jan and Jul - and all of 2025')
            ok(sum(t25.values()) == D('3000.00'),
               '  and once all are owned the charge is whole again')

            ok(str(M.property_annual_budgeted_expenses(a, 2016)) == '100.00'
               and str(M.property_annual_budgeted_expenses(b, 2024)) == '0',
               'Financial Indicators agrees month for month')

            mx = expense_matrix(lt.pk, today_year=2026)
            ok(mx['years'] and all(
                cell == (sum(M.budget_year_months([rows[r['prop_id']]], y)
                             [rows[r['prop_id']].expense_id], D('0')) or None)
                for r in mx['rows']
                for y, cell in zip(mx['years'], r['cells'])),
               'the expense matrix draws the same figure as the P&L, every '
               'cell')

            # revenue held too
            rlt = M.revenue_line_types.objects.create(
                revenue_line_types_name='OF3 Seasonal Income')
            rty = M.revenue_types.objects.create(revenue_types_name='OF3 M')
            M.props.objects.filter(pk=e.pk).update(
                prop_owned_from=dt.date(2025, 4, 1))
            e.refresh_from_db()
            rv = M.revenue.objects.create(prop=e, revenue_line_types=rlt,
                                          revenue_types=rty,
                                          revenue_jan=D('10'),
                                          revenue_may=D('20'))
            got = M.lease_revenue_rows(e, 2025)
            ok(len(got) == 1 and got[0].revenue_jan == 0
               and got[0].revenue_may == D('20'),
               'revenue before Owned From counts for nothing; after it, '
               'in full')
            rv.refresh_from_db()
            ok(rv.revenue_jan == D('10'),
               '  and the database row still holds its figure - only a '
               'copy was trimmed')
            ok(M.lease_revenue_rows(e, 2026)[0].pk == rv.pk
               and M.lease_revenue_rows(e, 2026)[0].revenue_jan == D('10'),
               '  a fully owned year gets the row itself, untouched')

            u = User.objects.create_superuser('of3', 'of3@example.com', 'x')
            cl = Client(SERVER_NAME='localhost')
            cl.force_login(u)
            body = cl.get('/finance_expense_add/').content.decode()
            mt = re.search(r'id="alv-owned-from"[^>]*>(.*?)</script>', body,
                           re.S)
            info = json.loads(mt.group(1)) if mt else {}
            ok(info.get(str(b.pk)) == {'from': '2024-10-01', 'lines': True},
               'Add Expense is told Late\'s Owned From month and that it '
               'has lines', str(info.get(str(b.pk))))
            M.expense.objects.filter(prop=b).delete()
            info = json.loads(re.search(
                r'id="alv-owned-from"[^>]*>(.*?)</script>',
                cl.get('/finance_expense_add/').content.decode(),
                re.S).group(1))
            ok(info.get(str(b.pk), {}).get('lines') is False,
               '  and that it has none once they are gone - so its first '
               'line is dated from Owned From')
            ok(info.get(str(e.pk), {}).get('from') == '2025-04-01',
               '  a typed date reaches the screen as its month')
            rb = cl.get('/finance_revenue_add/').content.decode()
            ok('id="alv-owned-from"' in rb, 'Add Revenue is told too')

            pe = cl.get('/properties_edit/%d' % b.pk).content.decode()
            ok('The first lease started 15 Oct 2024.' in pe,
               'Property Edit names the first lease it falls back to')
            raise Rollback()
    except Rollback:
        pass

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def budget_year_months('" in gate,
   '  with a sentinel on the one helper')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
