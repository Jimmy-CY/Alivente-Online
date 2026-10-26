# -*- coding: utf-8 -*-
"""test_never_overwrite.py - round ES-9, 26 Oct 2026.

A LEASE IS NEVER OVERWRITTEN - his decisions of 26 October, from Envelope 5
on Live.

    - Approve and attach goes onto ONE tenancy chosen on the envelope page,
      and only a tenancy at that property with NO lease attached is offered
      or accepted. Nothing replaces or deletes a lease that is there; the
      old one is removed by hand (Manage Lease Agreements) first.
    - A renewal is a new tenancy: Start e-signing lists current AND upcoming
      tenancies with their dates, says which already have a lease, and warns
      (does not refuse) when the chosen one does.
    - Manage Lease Agreements refuses an Upload over a lease on the server
      too, not only by hiding the button.
    - The signed copy goes to the people who SIGNED, at the addresses their
      links went to, and to Alivente - never to the tenant record's
      addresses, which is how a test envelope reached the real tenant.
    - Home: WAITING FOR YOU replaces the Churn-risk flags card (his
      decision, bundled into this release): signed leases, invoices in
      draft, expenses to approve and to pay, in one card.
    - Notifications: EIGHT boxes, four across and two high; the eighth is
      LEASES NEEDING ACTION - signed and awaiting approval, or declined /
      expired and not yet dealt with. Superuser only; others see it greyed.
    - FOUND BY HIS RELEASE 22 PUSH: get_overdue_invoices read its columns
      one place off since T2-4 added tenant_2_name to the SELECT (and the
      tenant model it asks was never imported), so ANY unpaid invoice of a
      current tenant made every Notifications box read zero. Fixed and
      driven here with a cursor that returns the SELECT's real shape.

The approval itself is driven in test_lease_approval.py section 4, which
ES-9 rewrote; this suite owns the rest.
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

SUFFIX = '.bak_neveroverwrite'
ME = 'test_never_overwrite.py'
PATCHER = 'apply_never_overwrite.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-9, 26 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
APPROVE = J(ROOT, 'pages', 'views', 'lease_signing_approve.py')
DETAIL = J(TPL, 'lease_signing_detail.html')
SIGN = J(ROOT, 'pages', 'views', 'lease_signing_sign.py')
TEN_V = J(ROOT, 'pages', 'views', 'tenants.py')
CREATE = J(ROOT, 'pages', 'views', 'lease_signing_create.py')
CREATE_T = J(TPL, 'lease_signing_create.html')
HELP_A = J(ROOT, 'pages', 'help_content', 'administration.html')
HOME_T = J(TPL, 'home.html')
ND_V = J(ROOT, 'pages', 'views', 'notifications_dashboard.py')
HOME_V = J(ROOT, 'pages', 'views', 'home.py')
ND_T = J(TPL, 'notifications.html')
GATE = J(ROOT, PS1)
EDITED = (APPROVE, DETAIL, SIGN, TEN_V, CREATE, CREATE_T, HELP_A, HOME_T,
          ND_V, ND_T, HOME_V)

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


def between(s, a, b):
    i = s.find(a)
    j = s.find(b, i + 1) if i >= 0 else -1
    return s[i:j] if i >= 0 and j > i else ''


def claims(src):
    ap = T.python_code_only(src[APPROVE])
    att = between(ap, 'def _attach(', '\ndef ')
    sg = T.python_code_only(src[SIGN])
    sc = between(sg, 'def _signed_copy(', '\ndef ')
    tv = T.python_code_only(src[TEN_V])
    cv = T.python_code_only(src[CREATE])
    return [
        ('raise LeaseAlreadyAttached(' in att and 'let_go_of_file' not in ap
         and 'delete_unheld' not in ap and 'select_for_update()' in att,
         'approval refuses a tenancy that holds a lease, under a lock, and '
         'nothing in it lets go of or deletes an old lease'),
        ('def _free_tenancies(env)' in ap
         and "if target_id not in free_ids:" in ap,
         '  and attaches only to a FREE tenancy at that property, asked '
         'again on the server'),
        ('name="target" form="lsd-approve-form"' in src[DETAIL]
         and '{% if can_approve %}' in src[DETAIL] and ' disabled' in src[DETAIL],
         'the envelope page chooses the tenancy, and greys Approve when '
         'none is free'),
        ('for p in env.parties.order_by(' in sc
         and 'tenant_emails' not in T.python_code_only(sc),
         'the signed copy goes to the people who signed, not the tenant '
         'record'),
        ('if tenant_obj.tenant_lease_agreement:' in tv
         and "'lease is never replaced.'" in src[TEN_V],
         'Manage Lease Agreements refuses an upload over a lease on the '
         'server'),
        ('Q(tenant_lease_start_date__gt=_dt.date.today())' in cv
         and '(lease attached)' in src[CREATE_T]
         and '{% if chosen.tenant_lease_agreement %}' in src[CREATE_T],
         'Start e-signing lists upcoming tenancies with dates, marks a '
         'leased one, and warns when it is chosen'),
        ('Waiting for you' in src[HOME_T] and 'insights.churn' not in src[HOME_T]
         and 'data-href="{% url \'lease_signing_list\' %}"' in src[HOME_T]
         and 'today_by_category.invoices_approval' in src[HOME_T],
         'Home: Waiting for you replaces the Churn-risk card'),
        ('def get_leases_needing_action(' in T.python_code_only(src[ND_V])
         and "notification_data.pop('leasesNeedingAction', None)"
         in T.python_code_only(src[ND_V])
         and 'data-category="lease_action"' in src[ND_T]
         and 'indicator-card locked' in src[ND_T]
         and 'grid-template-columns: repeat(4, 1fr);' in src[ND_T],
         'Notifications: eight boxes, four across; Leases Needing Action, '
         'superuser only, greyed for anybody else'),
        ("'Home: the portfolio insights did not build'" in src[HOME_V],
         'Home logs why its cards are missing, instead of swallowing it'),
        ('a lease is <strong>never replaced</strong>' in src[HELP_A]
         and 'A renewal is a new tenancy.' in src[HELP_A],
         'the Lease Signing help says so'),
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
head('3. DRIVEN')
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
    import shutil
    import tempfile
    from django.contrib.auth.models import User
    from django.core import mail
    from django.core.files.base import ContentFile
    from django.db import connection, transaction
    from django.test import Client, override_settings
    from django.utils import timezone
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
        M.LeaseSigning.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    tmp = tempfile.mkdtemp(prefix='es9_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            boss = User.objects.create_superuser(
                'es9boss', 'es9.boss@example.com', 'not-a-real-password')
            c = Client(SERVER_NAME='localhost')
            c.force_login(boss)
            prop = M.props.objects.create(prop_name='ES-9 Flat',
                                          prop_country='Cyprus')
            today = timezone.localdate()
            old = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Esnine Tenant', tenant_current='Yes',
                tenant_email='real.tenant@example.com',
                tenant_lease_start_date=today - dt.timedelta(days=200),
                tenant_lease_end_date=today + dt.timedelta(days=30))
            old.tenant_lease_agreement.save('old.pdf',
                                            ContentFile(b'%PDF-1.4 OLD'),
                                            save=True)
            new = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Esnine Tenant', tenant_current='No',
                tenant_email='real.tenant@example.com',
                tenant_lease_start_date=today + dt.timedelta(days=31),
                tenant_lease_end_date=today + dt.timedelta(days=396))

            # THE SIGNED COPY - to the envelope's addresses, not the record.
            now = timezone.now()
            env = M.LeaseSigning.objects.create(
                tenant=old, status='completed', created_by=boss,
                sent_at=now, completed_at=now, page_count=1,
                expires_at=now + dt.timedelta(days=7))
            env.sealed_pdf.save('s.pdf', ContentFile(b'%PDF-1.4 SIGNED'),
                                save=True)
            M.LeaseSigningParty.objects.create(
                signing=env, role='alivente', order=0, name='House',
                email='house@example.com', signed_at=now)
            M.LeaseSigningParty.objects.create(
                signing=env, role='tenant', order=1, name='Esnine Tenant',
                email='test.address@example.com', signed_at=now)
            from pages.views.lease_signing_sign import _signed_copy
            mail.outbox = []
            _signed_copy(env)
            to = [x.lower() for m in mail.outbox for x in m.to]
            ok('test.address@example.com' in to
               and 'house@example.com' in to
               and 'real.tenant@example.com' not in to,
               'the signed copy reaches the address the tenant SIGNED from, '
               'and Alivente - and NOT the tenant record\'s address', to)

            # THE ENVELOPE PAGE OFFERS ONLY THE FREE TENANCY.
            pg = c.get('/lease-signing/%d/' % env.pk).content.decode(
                'utf-8', 'replace')
            sel = between(pg, 'name="target"', '</select>')
            ok('value="%d"' % new.pk in sel and 'value="%d"' % old.pk
               not in sel and ' selected' in sel,
               'the envelope page offers the renewal, already chosen, and '
               'not the tenancy holding a lease', re.findall(r'value="\d+"', sel))

            # START E-SIGNING: upcoming listed, dated, the leased one marked.
            pg = c.get('/lease-signing/new/').content.decode('utf-8',
                                                              'replace')
            opts = [H.unescape(re.sub(r'\s+', ' ', o)).strip() for o in
                    re.findall(r'<option value="\d+">(.*?)</option>', pg,
                               re.S)]
            mine = [o for o in opts if 'Esnine' in o]
            ok(len(mine) == 2 and any('(lease attached)' in o for o in mine)
               and any(' to ' in o and '(lease attached)' not in o
                       for o in mine),
               'Start e-signing lists both tenancies with dates, the '
               'upcoming one included, and marks the one with a lease', mine)
            pg = c.get('/lease-signing/new/?tenant=%d' % old.pk
                       ).content.decode('utf-8', 'replace')
            ok('already has a lease agreement attached' in pg,
               '  and warns - without refusing - when that one is chosen')

            # MANAGE LEASE AGREEMENTS: an upload over a lease is refused.
            from django.core.files.uploadedfile import SimpleUploadedFile
            keep = old.tenant_lease_agreement.name
            c.post('/tenant_lease_agreement/', {
                'action': 'upload', 'tenant_id': str(old.pk),
                'lease_agreement': SimpleUploadedFile(
                    'x.pdf', b'%PDF-1.4 NEW', content_type='application/pdf')})
            old.refresh_from_db()
            ok(old.tenant_lease_agreement.name == keep
               and old.tenant_lease_agreement.open('rb').read()
               == b'%PDF-1.4 OLD',
               'an upload over a lease is refused by the server, byte for '
               'byte')
            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# HOME, OUTSIDE ANY TRANSACTION. get_notification_data() closes Django's
# connection when it is done (the legacy mysql.connector block), and a
# close inside an atomic block poisons the rest of it - so this part
# creates its rows plainly and deletes them by key afterwards.
if have_db:
    MADE = []
    try:
        hb = User.objects.create_superuser(
            'es9home', 'es9.home@example.com', 'not-a-real-password')
        MADE.append(hb)
        hc = Client(SERVER_NAME='localhost')
        hc.force_login(hb)
        hp_ = M.props.objects.create(prop_name='ES-9 Home', prop_country='Cyprus')
        MADE.append(hp_)
        ht = M.tenant.objects.create(prop=hp_, tenant_type='Individual',
                                     tenant_name='Esnine Home',
                                     tenant_current='Yes')
        MADE.append(ht)
        MADE.append(M.PhysicalInvoice.objects.create(
            tenant=ht, period_year=2027, period_month=1,
            invoice_date=dt.date(2027, 1, 1), status='draft', total=1))
        # A DECLINED ENVELOPE ON A TENANCY WITH NO LEASE needs action.
        denv = M.LeaseSigning.objects.create(
            tenant=ht, status='declined', created_by=hb)
        MADE.append(denv)
        r = hc.get('/notifications/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        d = r.json()
        mine = [x for x in d.get('leasesNeedingAction', [])
                if x['envelope_id'] == denv.pk]
        ok(len(mine) == 1 and 'Declined' in mine[0]['status']
           and d['summary'].get('leasesNeedingAction', 0) >= 1,
           'Notifications: a declined envelope on a tenancy with no lease is '
           'a lease needing action', mine)
        newer = M.LeaseSigning.objects.create(tenant=ht, status='draft',
                                              created_by=hb)
        MADE.append(newer)
        d = hc.get('/notifications/',
                   HTTP_X_REQUESTED_WITH='XMLHttpRequest').json()
        ok(not [x for x in d.get('leasesNeedingAction', [])
                if x['envelope_id'] == denv.pk],
           '  and stops counting once a newer envelope is started for it')
        from django.contrib.auth.models import Permission
        from pages.permissions import ensure_permissions
        ensure_permissions()        # SY-1's rows, as migrate would make them
        staff = User.objects.create_user('es9staff', 'es9.staff@example.com',
                                         'not-a-real-password')
        MADE.append(staff)
        staff.user_permissions.add(*Permission.objects.filter(
            codename='can_access_dashboard'))
        sc = Client(SERVER_NAME='localhost')
        sc.force_login(staff)
        r = sc.get('/notifications/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok(r.status_code == 200 and 'leasesNeedingAction' not in r.json()
           and 'leasesNeedingAction' not in r.json().get('summary', {}),
           '  and somebody who is not a superuser is handed neither the rows '
           'nor the count', r.status_code)
        pg = sc.get('/notifications/').content.decode('utf-8', 'replace')
        ok('indicator-card locked' in pg
           and 'data-category="lease_action"' not in pg,
           '  and sees the box greyed, with nothing to open')
        from django.core.cache import cache
        cache.delete('home_notification_data_user_%d' % hb.pk)
        hp = hc.get('/').content.decode('utf-8', 'replace')
        card = between(hp, 'Waiting for you', '</section>')
        if 'class="ins-card' not in hp:
            # Home draws its cards only when its insights build; where
            # they do not, home.py now logs why (ES-9) - reported, not
            # failed as if the card were wrong.
            skip('the Home card', 'Home drew no insight cards on this '
                 'database - see "Home: ... did not build" in the log')
        else:
            ok('data-category="invoices_approval"' in card
               and 'awaiting approval' in card
               and 'class="ins-ic ins-ic--churn"' not in hp,
               'Home: Waiting for you shows the draft invoice, and the '
               'Churn-risk card is gone')
    finally:
        for obj in reversed(MADE):
            try:
                type(obj).objects.filter(pk=obj.pk).delete()
            except Exception as _e:                          # noqa: BLE001
                print('        cleanup: %s %s' % (type(obj).__name__, _e))

# THE OVERDUE LIST, DRIVEN WITH THE SELECT'S REAL SHAPE - no MySQL here,
# so a cursor hands back exactly the nine columns the query names.
if django_up:
    import datetime as _dt
    from pages.views.notifications_dashboard import get_overdue_invoices

    class _Cur:
        def execute(self, q):
            self.q = q

        def fetchall(self):
            return [('Pindarou', 'Cyprus', 'Capacitor Partners Limited', None,
                     5, 1500, _dt.date(2026, 9, 1), 77, 1711.0),
                    ('Flat', 'Cyprus', 'Esnine A', 'Esnine B', 0, 500,
                     _dt.date(2026, 10, 25), 78, None)]
    try:
        got = get_overdue_invoices(_Cur(), _dt.date(2026, 10, 26))
        ok(len(got) == 2 and got[0]['due_date'] == '2026-09-06'
           and got[0]['tenant_rent'] == 1711.0
           and got[1]['tenant_display_name'] == 'Esnine A & Esnine B',
           'the overdue list reads each column where the SELECT puts it - '
           'an unpaid invoice no longer zeroes every Notifications box', got)
    except Exception as _e:                                  # noqa: BLE001
        ok(False, 'the overdue list survives an unpaid invoice',
           '%s: %s' % (type(_e).__name__, _e))
    ok('payment_terms = int(row[4])' in NOW[ND_V]
       and 'payment_terms = int(row[3])' in OLD[ND_V],
       '  CONTROL: before this round it read the second tenant\'s name as '
       'the payment terms')

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'raise LeaseAlreadyAttached('" in gate,
   '  with a sentinel on the refusal')
ok("let_go_of_file(ten, 'tenant_lease_agreement')" not in gate,
   '  and none left asking for the old replace')
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
