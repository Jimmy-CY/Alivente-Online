# -*- coding: utf-8 -*-
"""test_report_names.py - round T2-4, 24 Oct 2026.

THE FOUR REPORTS NAME BOTH PEOPLE, AND EVERY MATCH SITE IS UNTOUCHED.

THE SECOND HALF IS THE HARD HALF AND IT IS WHY THIS SUITE EXISTS.

tenant_name appears 485 times across 99 files in this tree, and many
of them are IDENTITY rather than label - things are MATCHED on it.
Four of those sit inside these same four reports:

    open_invoices_report matches  t.tenant_name === tenantName  to
    find a tenant's invoices, and carries data-tenant-name
    attributes that feed that match

    lease_agreement_report builds a download filename from it

Put a joined name into any of them and the match finds nothing. The
report does not break. It just stops mentioning somebody - which is
the worst way for a report to be wrong, because nothing says so.

So section 3 names all four MATCH sites and requires them present and
unchanged, and section 5 DRIVES the open-invoices lookup in a real
browser with a two-person tenancy: the card still resolves by the
stored name while the table shows both. A round that "finished the
job" by replacing those four would pass every other check here.

SECTION 4 IS ABOUT COST, NOT CORRECTNESS. Two of these reports fetch
their tenant with .only(), which DEFERS every column it does not
name. Reading a deferred field fires a second query per row - the
report would print both names and be quietly twice as expensive doing
it. The check counts queries against a real database rather than
reading the list, and its control is the same fetch without the
columns, which really does cost the extra query.

WHAT IS NOT PROVED HERE. That the OTHER 95 files are right - they are
not this round's, and section 6 asserts they are untouched.
portfolio_insights joins SQL rows to ORM leases on tenant_name and
must keep doing so; the Tenants register has printed both names since
T2-2; the mailer is T2-5.
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

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_reportnames'
ME = 'test_report_names.py'
PATCHER = 'apply_report_names.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-4, 24 Oct 2026'

ISSUES = os.path.join(ROOT, 'pages', 'views', 'issues.py')
INSIGHTS = os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py')
ND = os.path.join(ROOT, 'pages', 'views', 'notifications_dashboard.py')
PHYS = os.path.join(ROOT, 'pages', 'views', 'physical_invoices.py')
TENANTS_V = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
PROPS_V = os.path.join(ROOT, 'pages', 'views', 'properties.py')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
INVOICES = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
T_REP = os.path.join(ROOT, 'pages', 'templates', 'tenant_report.html')
L_REP = os.path.join(ROOT, 'pages', 'templates',
                     'lease_agreement_report.html')
R_REP = os.path.join(ROOT, 'pages', 'templates',
                     'lease_renewal_report.html')
O_REP = os.path.join(ROOT, 'pages', 'templates',
                     'open_invoices_report.html')
GATE = os.path.join(ROOT, PS1)
def TPL(n_):
    return os.path.join(ROOT, 'pages', 'templates', n_)


# THE SIXTEEN SCREENS, named. The round began as four and was scoped
# by a census only after four screenshots each found another.
SCREENS = tuple(TPL(n_) for n_ in (
    'tenant_report.html', 'lease_agreement_report.html',
    'lease_renewal_report.html', 'open_invoices_report.html',
    'lease_timeline.html', 'tenant_payment_days.html',
    'home.html', 'property_detail.html', 'notifications.html',
    'invoices.html', 'physical_invoice_edit.html',
    'cash_receipt_detail.html', 'cash_receipt_add.html',
    'lease_signing_list.html', 'tenant_lease_agreement.html',
    'generate_lease_agreement.html'))

REPORTS = (T_REP, L_REP, R_REP, O_REP)
FILES = ((MODELS, ISSUES, INVOICES, INSIGHTS, ND, PHYS, TENANTS_V,
          PROPS_V) + SCREENS)

GREEK_1 = 'Ανδρέας Γεωργίου'
GREEK_2 = 'Μαρία Γεωργίου'
BOTH = GREEK_1 + ' & ' + GREEK_2

SCRATCH = os.environ.get('ALV_SCRATCH') or os.path.join(ROOT, '_scratch')
EXE = os.path.join(ROOT, 'chromium', 'chrome.exe')

# THE MATCH SITES, WRITTEN OUT. These are what a tidy-up would
# "finish" and break, and breaking one raises nothing at all: the
# filter returns nothing, the join finds nothing, the lookup opens an
# empty panel, and the screen stops naming somebody.
MATCHES = (
    (O_REP, 'if (t.tenant_name === tenantName || t.tenant_id == tenantId) {',
     'the invoice lookup'),
    (O_REP, 'data-tenant-name="{{ debtor.tenant_name }}"',
     'what the lookup is given'),
    (L_REP, 'const tenantName = "{{ tenant.tenant_name|escapejs }}";',
     'the lease download filename'),
    (TPL('tenant_add.html'), 'value="{{ form_data.tenant_name }}"',
     'the Add Tenant form value'),
    (TPL('tenant_edit.html'), 'value="{{tresults.tenant_name}}"',
     'the Edit Tenant form value'),
    (TPL('tenant.html'), '{% for name in all_tenant_names %}',
     'the register filter list'),
    # NB-1, 26 Oct 2026 - THE TWO FILTERS MATCH ON THE SHOWN NAME NOW,
    # his decision: the choices became tenant_display_name ("A & B"),
    # so the match moved with them - choice and match are one name,
    # which is this table's rule from the other side.
    (TENANTS_V, 'if t.tenant_display_name == selected_tenant',
     'the register filter'),
    (INVOICES, 'if t.tenant_display_name == tenant_output',
     'the invoices filter'),
    (INSIGHTS, '_norm(x.tenant_name) == _norm(l.tenant_name)',
     'the arrears join'),
    (os.path.join(ROOT, 'pages', 'admin.py'),
     "search_fields = ['tenant_name', 'tenant_2_name']",
     'the admin search'),
)

# NB-1, 26 Oct 2026 - the two match sites it moved, and what each was.
MOVED_BY_NB1 = {
    TENANTS_V: 'filtered_tenants.filter(tenant_name=selected_tenant)',
    INVOICES: 'tenant.objects.filter(tenant_name=tenant_output)',
}

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
    with open(p, encoding='utf-8', errors='replace') as f:
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

NOW = dict((p, read(p)) for p in FILES)


def claims(d):
    scr = dict((os.path.basename(k), v) for k, v in d.items())
    return {
        'the four reports name both people':
            all('tenant_display_name' in d[p] for p in REPORTS),
        'and so does the Lease Timeline':
            'tenant_display_name' in scr['lease_timeline.html'],
        '  and Payment Behaviour':
            'tenant_display_name' in scr['tenant_payment_days.html'],
        '  and the landing page insight cards':
            'tenant_display_name' in scr['home.html'],
        '  and property detail, the densest screen of the lot':
            scr['property_detail.html'].count('tenant_display_name') >= 6,
        '  and the notifications tables':
            scr['notifications.html'].count('tenant_display_name') == 3,
        '  and the invoices table':
            'tenant_display_name' in scr['invoices.html'],
        '  and the lease signing register':
            'tenant_display_name' in scr['lease_signing_list.html'],
        '  and the lease agreements table':
            'tenant_display_name' in scr['tenant_lease_agreement.html'],
        '  and Generate two preview panes':
            scr['generate_lease_agreement.html'].count(
                'tenantData.tenant_display_name') == 2,
        'a VAT invoice names both liable people':
            'tenant_obj.tenant_display_name' in d[PHYS],
        '  and a receipt prefills both':
            'tenant_display_name' in scr['cash_receipt_add.html'],
        'the Cash Flow Forecast breakdown names both':
            'lease.tenant_display_name' in d[INSIGHTS],
        'and the join has a name of its own':
            'def joint_name' in d[MODELS],
        '  which the raw-sql overdue rows can ask':
            'tenant.joint_name(' in d[ND],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

ok(MARK in NOW[ISSUES], 'the round dates itself')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
for p, nm in ((T_REP, 'tenant_report'), (L_REP, 'lease_agreement_report'),
              (R_REP, 'lease_renewal_report'),
              (O_REP, 'open_invoices_report')):
    ok('tenant_name' in OLD[p],
       'CONTROL: %s printed one name' % nm)


# ==========================================================================
head('3. EVERY MATCH SITE IS EXACTLY WHERE IT WAS')
# ==========================================================================
#
# THIS IS THE SECTION THE ROUND EXISTS TO SURVIVE. Replacing any of
# these four produces no error: the lookup finds nothing, and the
# report quietly stops naming somebody.
# SOME MATCH SITES ARE IN FILES THIS ROUND NEVER OPENS - which is
# exactly the claim. They are read from disk, and their "before" is
# the backup when one exists and the file itself when it does not,
# because a file with no backup is one the round did not touch.
for p, lit, what in MATCHES:
    cur = NOW.get(p) or read(p)
    ok(lit in cur,
       '%-28s is untouched - %s' % (os.path.basename(p), what))
    before = OLD.get(p)
    if before is None:
        before = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else cur
        ok(not os.path.isfile(p + SUFFIX),
           '  CONTROL: and this round has no backup of that file at '
           'all, so it never opened it')
    else:
        # NB-1 moved two of them; their "before" is what they replaced.
        ok(MOVED_BY_NB1.get(p, lit) in before,
           '  CONTROL: and it was there before this round too')

# AND THE ROUND ADDED A KEY RATHER THAN RENAMING ONE.
for p, nm in ((ISSUES, 'issues.py'), (INVOICES, 'invoices.py')):
    ok("'tenant_name'" in NOW[p],
       '%s still carries the match key alongside the display one' % nm)

# THE JAVASCRIPT LIST CARRIES BOTH, AND THE LOOKUP STILL READS THE
# MATCH ONE.
i = NOW[O_REP].find('tenant_display_name:')
ok(i > 0 and 'tenant_name:' in NOW[O_REP][max(0, i - 400):i],
   'the javascript tenant list carries BOTH keys, display beside '
   'match')


# ==========================================================================
head('4. THE COST - .only() DEFERS WHAT IT DOES NOT NAME')
# ==========================================================================
#
# THIS IS ABOUT COST, NOT CORRECTNESS, and it is the half a reading of
# the source cannot answer. .only() defers every column it does not
# name; reading a deferred field fires a SECOND query to fetch it. The
# report would print both names and be quietly twice as expensive.
#
# So this COUNTS QUERIES against a real database, and its control is
# the identical fetch WITHOUT the columns - which really does cost the
# extra one.
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if not django_up:
    skip('sections 4 and 5', 'no database')
else:
    import datetime as dt
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    from pages.models import props, tenant as Tenant

    p = props.objects.create(prop_name='Flat 3, Nikis Avenue',
                             prop_country='Cyprus')
    row = Tenant(prop=p, tenant_type='Individual', tenant_name=GREEK_1,
                 tenant_2_name=GREEK_2,
                 tenant_2_contact_number='+357 99 333444',
                 tenant_2_email='m.georgiou@example.com',
                 tenant_lease_start_date=dt.date(2026, 12, 1),
                 tenant_lease_end_date=dt.date(2027, 11, 30),
                 tenant_current='Yes')
    row.save()

    # THE LISTS, READ OUT OF THE FILE AND RUN - not retyped here. A
    # fixture that retyped the column list would be testing itself.
    code = T.python_code_only(NOW[ISSUES], payloads=True)
    lists = []
    at = 0
    while True:
        at = code.find('tenant.objects.only(', at)
        if at < 0:
            break
        lists.append(code[at + len('tenant.objects.only('):
                          code.find(')', at)])
        at += 10
    ok(len(lists) == 2,
       'both tenant .only() lists are readable out of the view',
       len(lists))

    def cost(cols):
        """Queries to fetch a tenant with `cols` and read both names."""
        names = [c.strip().strip("',\"") for c in cols.split(',')
                 if c.strip().strip("',\"")
                 and not c.strip().startswith('#')]
        names = [n for n in names if n and not n.startswith('#')]
        with CaptureQueriesContext(connection) as q:
            t_ = Tenant.objects.only(*names).get(pk=row.pk)
            _ = t_.tenant_display_name
        return len(q), t_.tenant_display_name

    for n, cols in enumerate(lists, 1):
        try:
            q, shown = cost(cols)
            ok(q == 1,
               '.only() list %d reads both names in ONE query - a '
               'deferred field that is then read costs a second one '
               'per row' % n, '%d queries' % q)
            ok(shown == BOTH,
               '  and the name it reads is both people', shown)
        except Exception as e:
            ok(False, '.only() list %d ran' % n,
               '%s: %s' % (type(e).__name__, e))

    # THE CONTROL, AND WITHOUT IT THE CHECK ABOVE PROVES NOTHING. If
    # the same fetch WITHOUT the columns also cost one query, then
    # .only() is not deferring anything and the lists did not matter.
    try:
        q2, shown2 = cost("'tenant_id', 'prop_id', 'tenant_name'")
        ok(q2 > 1,
           'CONTROL: the same fetch WITHOUT the columns costs %d '
           'queries - so .only() really is deferring, and naming them '
           'really is what makes the report cheap' % q2, q2)
        ok(shown2 == BOTH,
           '  (it still prints the right name - it just pays for it)',
           shown2)
    except Exception as e:
        ok(False, 'CONTROL ran', '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('5. THE LOOKUP STILL RESOLVES, DRIVEN')
# ==========================================================================
#
# THE ONE THING THAT WOULD NOT ANNOUNCE ITSELF. Replace tenant_name in
# the javascript list and findTenantData returns null: the click opens
# an empty modal, no error is raised, nothing is logged, and a tenant
# simply has no invoices as far as the screen is concerned.
#
# So this drives the REAL functions, lifted whole out of the page, with
# a list shaped exactly as the template builds one - matched by the
# STORED name while the card shows BOTH.
try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None


def fn_source(src, name):
    a = src.find('function %s(' % name)
    if a < 0:
        return ''
    depth, i, started = 0, a, False
    while i < len(src):
        if src[i] == '{':
            depth += 1
            started = True
        elif src[i] == '}':
            depth -= 1
            if started and depth == 0:
                return src[a:i + 1]
        i += 1
    return ''


FIND = fn_source(NOW[O_REP], 'findTenantData')
CARD = fn_source(NOW[O_REP], 'generateTenantHTML')
ok(FIND and CARD,
   'findTenantData and generateTenantHTML are readable out of the page')

# THE HELPERS THOSE TWO LEAN ON, so the fixture runs the real code
# rather than a rewrite of it.
HELPERS = '\n'.join(fn_source(NOW[O_REP], n)
                    for n in ('ageStep', 'formatAmount'))

DRIVE_JS = """() => {
  // The list exactly as the template builds one: BOTH keys.
  tenantDataList = [{
    prop_name: 'Flat 3, Nikis Avenue',
    prop_country: 'Cyprus',
    tenant_id: 7,
    tenant_name: %s,
    tenant_display_name: %s,
    tenant_contact_person: 'A',
    tenant_contact_number: '+357',
    tenant_email: 'a@x.com',
    tenant_rent: 950,
    tenant_payment_terms: 1,
    invoices: []
  }];
  // Clicked with the STORED name, which is what data-tenant-name holds.
  const found = findTenantData(%s, null);
  return {
    resolved: !!found,
    byId: !!findTenantData('something else entirely', 7),
    card: found ? generateTenantHTML(found, true) : ''
  };
}""" % (repr(GREEK_1), repr(BOTH), repr(GREEK_1))

if sync_playwright is None:
    skip('section 5', 'playwright is not installed')
elif not (FIND and CARD):
    ok(False, 'section 5 cannot run without the two functions')
else:
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    html = ('<!doctype html><html><head><meta charset="utf-8"></head>'
            '<body><script>var tenantDataList = [];\n%s\n%s\n%s</script>'
            '</body></html>' % (HELPERS, FIND, CARD))
    fx = os.path.join(SCRATCH, '_t24_lookup.html')
    with open(fx, 'w', encoding='utf-8') as f:
        f.write(html)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1280, 'height': 800})
        pg = ctx.new_page()
        pg.goto('file://' + fx.replace(os.sep, '/'))
        r = pg.evaluate(DRIVE_JS)

        ok(r['resolved'],
           'a tenancy is still FOUND by the stored name - which is '
           'what data-tenant-name carries and what the click hands in')
        ok(r['byId'],
           '  and still found by id, the other half of the same test')
        ok(GREEK_1 in r['card'] and GREEK_2 in r['card'],
           '  while the card it builds shows BOTH people', r['card'][:140])
        ok(BOTH in r['card'],
           '  joined the one way the model joins them')
        ctx.close()
        br.close()


# ==========================================================================
head('6. ONE FILE THAT DOES BOTH JOBS, AND THE ONE LEFT ALONE')
# ==========================================================================
#
# portfolio_insights.py IS EDITED BY THIS ROUND - four payloads and
# the Cash Flow Forecast breakdown - AND IT IS ALSO WHERE THE ARREARS
# JOIN LIVES. The same file both shows names and matches on them,
# which is the clearest possible statement of this round's rule.
ins = NOW[INSIGHTS]
ok('tenant_display_name' in ins,
   'portfolio_insights CARRIES display keys - the forecast breakdown '
   'and four payload rows')
ok('_norm(x.tenant_name) == _norm(l.tenant_name)' in ins,
   '  AND still joins sql rows to orm leases on the STORED name, in '
   'the same file')
ok('_norm(x.tenant_display_name)' not in ins
   and '_norm(l.tenant_display_name)' not in ins,
   '  and the join was never handed a joined name to join on, which '
   'would have matched nothing')

# THE ONE THAT REALLY IS UNTOUCHED.
mail = os.path.join(ROOT, 'pages', 'management', 'commands',
                    'send_physical_invoices.py')
ok(not os.path.isfile(mail) or MARK not in read(mail),
   'the invoice mailer is untouched - who RECEIVES scheduled mail is '
   'T2-5, on a job that runs every five minutes')
ok(not os.path.isfile(mail + SUFFIX),
   '  and this round has no backup of it at all, so it never opened '
   'it')

# AND THE FORM VALUES STILL CARRY THE STORED NAME. An input whose
# value is a joined name would save that joined name back into
# tenant_name the next time somebody pressed Save.
for nm_ in ('tenant_add.html', 'tenant_edit.html'):
    src = read(TPL(nm_))
    ok('tenant_display_name' not in src,
       '%s keeps the STORED name in its form value - an input '
       'carrying a joined name would write it back into the column '
       'on the next Save' % nm_)


# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('tenant_display_name' in gate,
   '  with a sentinel that would notice it being taken out')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
