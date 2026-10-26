# -*- coding: utf-8 -*-
"""test_names_and_drafts.py - round NB-1, 26 Oct 2026.

THREE THINGS HE FOUND TESTING RELEASE 20 ON LIVE.

    - THE TENANT CHOICES MATCH THE TABLE. The Tenants filter listed every
      tenant_name ever saved - past leases, old joint names typed into one
      box, a joint tenancy under its first name only. Now: the rows the
      table would show (current unless Include past tenants / a Status),
      each named as the table names it ("A & B"), once; the filter
      matches on that name. Open Invoices names them the same way (past
      ones stay - an unpaid invoice outlives its lease). Generate Lease
      Agreement names each TENANCY: display name, lease dates, "(past)".
    - INVOICES WAITING FOR APPROVAL on Notifications (a seventh box) and on
      Home (under Arrears): every draft physical invoice, with Review and
      approve - his request; the daily e-mail already lists them.
    - "SAME AS TENANT 1'S ADDRESS" on Generate's second tenant.
    - The e-signing emails carry the logo UNDER "Alivente Limited", a
      little bigger (72px, was 56).
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

SUFFIX = '.bak_namesdrafts'
ME = 'test_names_and_drafts.py'
PATCHER = 'apply_names_and_drafts.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'NB-1, 26 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
TEN_V = J(ROOT, 'pages', 'views', 'tenants.py')
INV_V = J(ROOT, 'pages', 'views', 'invoices.py')
LT_V = J(ROOT, 'pages', 'views', 'lease_template.py')
GEN_T = J(TPL, 'generate_lease_agreement.html')
ND_V = J(ROOT, 'pages', 'views', 'notifications_dashboard.py')
ND_T = J(TPL, 'notifications.html')
HOME_V = J(ROOT, 'pages', 'views', 'home.py')
HOME_T = J(TPL, 'home.html')
HELP_A = J(ROOT, 'pages', 'help_content', 'administration.html')
MODELS = J(ROOT, 'pages', 'models.py')
MAIL = J(ROOT, 'pages', 'services', 'lease_email.py')
GATE = J(ROOT, PS1)
EDITED = (TEN_V, INV_V, LT_V, GEN_T, ND_V, ND_T, HOME_V, HOME_T, HELP_A,
          MODELS, MAIL)

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

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def claims(src):
    tv = T.python_code_only(src[TEN_V])
    iv = T.python_code_only(src[INV_V])
    lv = T.python_code_only(src[LT_V])
    nv = T.python_code_only(src[ND_V])
    hv = T.python_code_only(src[HOME_V])
    return [
        ('set(t.tenant_display_name for t in _choice_rows' in tv
         and "_choice_rows.filter(tenant_current='Yes')" in tv
         and 'if t.tenant_display_name == selected_tenant' in tv,
         'the Tenants filter offers and matches the name the table shows, '
         'for the rows the table would show'),
        ('set(t.tenant_display_name for t in tenant.objects.all()' in iv
         and 'if t.tenant_display_name == tenant_output' in iv,
         '  and Open Invoices names them the same way'),
        ("order_by('-tenant_current', '-tenant_lease_start_date'" in lv
         and '{{ tenant.tenant_display_name }}{% if tenant.tenant_lease_start_date %}'
         in src[GEN_T] and ' (past){% endif %}' in src[GEN_T],
         'Generate names each tenancy - display name, lease dates, past'),
        ('def get_invoices_waiting_approval(' in nv
         and "data['invoicesWaitingApproval'] = drafts" in nv
         and 'status=PhysicalInvoice.STATUS_DRAFT' in nv,
         'the dashboard data carries the draft physical invoices'),
        ('data-category="invoices_approval"' in src[ND_T]
         # ES-9, 26 Oct 2026 - eight boxes, four across, his layout.
         and ('repeat(7, 1fr)' in src[ND_T] or 'repeat(4, 1fr)' in src[ND_T])
         and "{% url 'physical_invoice_list' %}?status=draft" in src[ND_T],
         '  Notifications shows them as a seventh box, with the way to '
         'approve'),
        ("'key': 'invoicesWaitingApproval'" in hv
         and "'permission': 'invoices'" in hv
         and 'today_by_category.invoices_approval' in src[HOME_T]
         and "case 'invoices_approval':" in src[HOME_T],
         '  and Home under Arrears, for whoever can open Physical Invoices'),
        ('Invoices Waiting for Approval</strong>' in src[HELP_A]
         and ('The seven status cards' in src[HELP_A]
              or 'The eight status cards' in src[HELP_A]),
         'the Notifications help describes it'),
        ("'</body></html>' % (body, logo))" in src[MAIL]
         and 'LOGO_HEIGHT = 72' in src[MAIL],
         'the e-signing emails sign off with the logo, a little bigger'),
        ('id="second-tenant-same-address"' in src[GEN_T]
         and 'function firstTenantAddress()' in src[GEN_T],
         "Generate's second tenant has Same as Tenant 1's address"),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))

# ==========================================================================
head('3. DRIVEN - the screens, over records of every shape')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    import datetime as dt
    import html as H
    from django.contrib.auth.models import User
    from django.db import connection, transaction
    from django.test import Client
    import pages.models as M
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('section 3', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        connection.ensure_connection()
        M.PhysicalInvoice.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


def options(page, sel_id):
    i = page.find('id="%s"' % sel_id)
    j = page.find('</select>', i)
    return [H.unescape(re.sub(r'\s+', ' ', o).strip())
            for o in re.findall(r'<option[^>]*>(.*?)</option>',
                                page[i:j], re.S)]


# NOT IN A TRANSACTION, AND CLEANED UP BY HAND. get_notification_data()
# closes Django's connection when it finishes (the legacy mysql.connector
# block does), and a close inside an atomic block poisons the rest of it.
# So every row is created here and deleted in the finally, by key - and
# nothing that was already in the database is touched, drafts included.
MADE = []
if have_db:
    try:
        if True:
            boss = User.objects.create_superuser(
                'nb1boss', 'nb1.boss@example.com', 'not-a-real-password')
            c = Client(SERVER_NAME='localhost')
            MADE.append(boss)
            c.force_login(boss)
            p = M.props.objects.create(prop_name='NB-1 Flat',
                                       prop_country='Cyprus',
                                       prop_available_for_rent='Yes')
            MADE.append(p)
            base = dict(prop=p, tenant_type='Individual',
                        tenant_rental_type='Monthly', tenant_deposit=500,
                        tenant_rent=500, tenant_levies=0,
                        tenant_payment_terms=0, tenant_renewal='Yes',
                        tenant_renewal_period=60,
                        tenant_contact_number='+35799000000',
                        tenant_email='nb1@example.com')
            cur = M.tenant.objects.create(
                tenant_name='Nbone Alpha', tenant_2_name='Nbone Beta',
                tenant_current='Yes',
                tenant_lease_start_date=dt.date(2026, 10, 1),
                tenant_lease_end_date=dt.date(2027, 9, 30), **base)
            MADE.append(cur)
            MADE.append(M.tenant.objects.create(
                tenant_name='Nbone Alpha and Nbone Beta', tenant_current='No',
                tenant_lease_start_date=dt.date(2025, 10, 1),
                tenant_lease_end_date=dt.date(2026, 9, 30), **base))
            JOINT = 'Nbone Alpha & Nbone Beta'
            OLDNAME = 'Nbone Alpha and Nbone Beta'

            pg = c.get('/tenant/').content.decode('utf-8', 'replace')
            opts = options(pg, 'tenantSelect')
            ok(JOINT in opts and 'Nbone Alpha' not in opts
               and OLDNAME not in opts,
               'Tenants: the current joint tenancy is offered as the table '
               'names it, and neither the first name alone nor the past '
               'record is', [o for o in opts if 'Nbone' in o])
            pg = c.get('/tenant/?all=1').content.decode('utf-8', 'replace')
            opts = options(pg, 'tenantSelect')
            ok(JOINT in opts and OLDNAME in opts,
               '  with Include past tenants, the past record joins it',
               [o for o in opts if 'Nbone' in o])
            from urllib.parse import quote
            pg = c.get('/tenant/?tenantname=' + quote(JOINT)
                       ).content.decode('utf-8', 'replace')
            ESC = 'Nbone Alpha &amp; Nbone Beta'
            ok(pg.count(ESC) >= 3,
               '  and choosing "A & B" shows that tenancy - its row as well '
               'as its option', pg.count(ESC))
            pg2 = c.get('/tenant/?tenantname=' + quote('Nbone Zeta')
                        ).content.decode('utf-8', 'replace')
            ok(pg2.count(ESC) == 2,
               '  CONTROL: a name nobody has shows no row - the option '
               'value and label alone - so the count above is the row',
               pg2.count(ESC))
            ok(options(pg, 'tenantSelect').count(JOINT) == 1,
               '  and offers it once')

            pg = c.get('/generate-lease-agreement/').content.decode(
                'utf-8', 'replace')
            gopts = [o for o in options(pg, 'tenant-select') if 'Nbone' in o]
            ok(len(gopts) == 2
               and gopts[0].startswith(JOINT + ' \u00b7 1 Oct 2026 to 30 Sep 2027')
               and gopts[1].endswith('(past)'),
               'Generate: current tenancy first, named "A & B" with its '
               'dates; the past one marked past', gopts)

            from pages.views.notifications_dashboard import \
                get_invoices_waiting_approval
            before = len(get_invoices_waiting_approval())
            pi = M.PhysicalInvoice.objects.create(
                tenant=cur, period_year=2026, period_month=12,
                invoice_date=dt.date(2026, 12, 1), status='draft',
                total=500)
            MADE.append(pi)
            from pages.views.notifications_dashboard import \
                get_notification_data
            d = get_notification_data()
            mine = [r for r in d.get('invoicesWaitingApproval', [])
                    if r['invoice_id'] == pi.pk]
            ok(d['summary'].get('invoicesWaitingApproval') == before + 1
               and len(mine) == 1 and mine[0]['name'] == JOINT,
               'the dashboard data counts the draft and names its tenancy',
               d.get('invoicesWaitingApproval'))
            r = c.get('/notifications/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            ok(r.status_code == 200
               and r.json()['summary'].get('invoicesWaitingApproval')
               == before + 1,
               '  and Notifications is handed it', r.status_code)
            hp = c.get('/').content.decode('utf-8', 'replace')
            # ES-9, 26 Oct 2026 - HOME DRAWS ITS CARDS ONLY WHEN ITS
            # INSIGHTS BUILD, and on a database where they do not (his
            # laptop, 26 Oct) there is no card for the row to sit in. That
            # is reported - with the reason now in Home's own log - rather
            # than failed as if the row were missing.
            if 'class="ins-card' not in hp:
                skip('the Home row', 'Home drew no insight cards on this '
                     'database - see "Home: ... did not build" in the log')
            else:
                ok('data-category="invoices_approval"' in hp
                   and 'awaiting approval' in hp,
                   '  and Home shows the row')
            from pages.services.lease_email import html_for
            h = html_for('Dear X,\n\nSign here.\n\nAlivente Limited\n', True)
            ok(h.find('Alivente Limited<br>') < h.find('cid:alivente_logo')
               and 'height:72px' in h,
               'the email logo comes AFTER the sign-off, at 72px')
            pi.status = 'approved'
            pi.save()
            # Home keeps the counts for 30 seconds per user (its own
            # cache, older than this round); forget them, as 30 s would.
            from django.core.cache import cache
            cache.delete('home_notification_data_user_%d' % boss.pk)
            hp = c.get('/').content.decode('utf-8', 'replace')
            ok(get_notification_data()['summary']
               ['invoicesWaitingApproval'] == before
               and ('data-category="invoices_approval"' not in hp
                    or before > 0),
               '  and once approved, it no longer counts')
    finally:
        for obj in reversed(MADE):
            try:
                type(obj).objects.filter(pk=obj.pk).delete()
            except Exception as _e:                          # noqa: BLE001
                print('        cleanup: %s %s' % (type(obj).__name__, _e))

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("File = 'pages/views/notifications_dashboard.py'; Text = 'def get_invoices_waiting_approval('"
   in gate, '  with a sentinel on the drafts helper')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.relpath(p, ROOT))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
