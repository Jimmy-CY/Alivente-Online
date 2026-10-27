# -*- coding: utf-8 -*-
"""test_lease_approval.py - round ES-6, 25 Oct 2026.

A SIGNED LEASE IS APPROVED ONTO ITS TENANT, OR DECLINED - DRIVEN.

His decision of 23 October: a completed envelope writes nothing onto
the tenant until somebody approves it. His decisions of 25 October:
approving REPLACES whatever lease is attached, and declining is FINAL.

THE CLAIM WITH TEETH IS SECTION 4's FAILED SAVE. UO-1 fixed the manual
upload so that a save which raises leaves the old lease in place; this
round writes to the same field by a second door, so the suite makes the
save raise and asks whether the old lease survived and the new bytes
were cleaned up. A happy-path test passes with the bug in place.

ALSO HERE, BECAUSE THEY SHIPPED WITH THIS ROUND:
  - the signed copy goes to Alivente as well (decision 2 of 23 Oct)
  - reminders follow ANY window length: day 3, and the day before the
    link lapses (ES-5 assumed seven days; the Send screen allows 1-60)
  - the Send screen says what the reminders really do

WHAT IS NOT PROVED HERE. How the bell looks with the extra count; the
context processor is asked directly, and the strip's markup is read.
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
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_leaseapprove'
ME = 'test_lease_approval.py'
PATCHER = 'apply_lease_approval.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-6, 25 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
SIGN = os.path.join(ROOT, 'pages', 'views', 'lease_signing_sign.py')
REG_VIEW = os.path.join(ROOT, 'pages', 'views', 'lease_signing.py')
CREATE = os.path.join(ROOT, 'pages', 'views', 'lease_signing_create.py')
CREATE_T = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_create.html')
VINIT = os.path.join(ROOT, 'pages', 'views', '__init__.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
REG_PAGE = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_list.html')
HOME = os.path.join(ROOT, 'pages', 'templates', 'home.html')
NOTIF = os.path.join(ROOT, 'pages', 'templates', 'notifications.html')
CTX = os.path.join(ROOT, 'mysite', 'context_processors.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'lease_signing_approve.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_detail.html')
MIG = os.path.join(ROOT, 'pages', 'migrations', '0107_es6_lease_approval.py')
GATE = os.path.join(ROOT, PS1)

EDITED = (MODELS, SIGN, REG_VIEW, CREATE, CREATE_T, VINIT, URLS, REG_PAGE,
          HOME, NOTIF, CTX)
SHIPPED = (VIEW, PAGE, MIG)

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

NOW = dict((p, read(p)) for p in EDITED + SHIPPED)
OLD = dict((p, was(p)) for p in EDITED)


def claims(src):
    py = dict((p, T.python_code_only(src[p])) for p in
              (MODELS, SIGN, REG_VIEW, CREATE, VINIT, URLS, CTX))
    mk = dict((p, T.code_only_js(src[p])) for p in
              (REG_PAGE, HOME, NOTIF, CREATE_T))
    return [
        ('approved_at = models.DateTimeField' in py[MODELS]
         and 'approval_declined_at = models.DateTimeField' in py[MODELS],
         'an envelope records who approved or declined its result, and when'),
        ('def awaiting_approval(self)' in py[MODELS]
         and 'def pending_approval(cls)' in py[MODELS],
         'ONE answer to "is this waiting for approval", for a row and for '
         'the table'),
        ("('approved', 'Approved onto the tenant')" in py[MODELS]
         and "('rejected', 'Approval declined')" in py[MODELS],
         'and the trail can say approved, or approval declined'),
        ('from .lease_signing_approve import *' in py[VINIT],
         'the approval views are exported'),
        ("name='lease_signing_detail'" in py[URLS]
         and "name='lease_signing_approve'" in py[URLS]
         and "name='lease_signing_sealed'" in py[URLS],
         '  and routed'),
        ("{% url 'lease_signing_detail' r.env.pk %}" in mk[REG_PAGE],
         'the register\'s View icon goes somewhere at last'),
        ("'awaiting_approval': env.awaiting_approval" in py[REG_VIEW],
         '  and the register asks the model whether a row is waiting'),
        # ES-11, 26 Oct 2026 - THE YELLOW BAR WENT, his decision: the
        # count is shown by Home's Waiting for you row and the
        # Notifications Leases Needing Action box instead.
        ('Signed lease{{ lease_approvals_waiting|pluralize }} awaiting '
         'approval' in mk[HOME]
         and 'data-category="lease_action"' in mk[NOTIF],
         'Home and Notifications both show the waiting count'),
        ('pending_approval().count()' in py[CTX]
         and "'lease_approvals_waiting'" in py[CTX],
         '  from the context processor, which also adds it to the bell'),
        # THE LOOP OVER THE EXTRA RECIPIENTS, which is this round's -
        # ES-5's decline email reads the same two fields, so a needle on
        # the fields alone held before this round too. The control
        # section caught it.
        ('for extra in ((getattr(env.created_by' in py[SIGN],
         'the signed copy goes to Alivente as well as the tenants'),
        ('FIRST_REMINDER_DAY = 3' in py[MODELS]
         and 'LAST_REMINDER_DAYS_BEFORE = 1' in py[MODELS]
         and 'def window_start(self)' in py[MODELS],
         'reminders are day 3 and the day before it lapses, of the REAL '
         'window'),
        ("'reminder_rule': LeaseSigning.REMINDER_RULE" in py[CREATE]
         and '{{ reminder_rule }}' in mk[CREATE_T]
         and 'remind_every' not in mk[CREATE_T],
         'the Send screen says what the reminders really do'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
mig = T.python_code_only(NOW[MIG])
ok(mig.count('migrations.AddField(') == 4
   and mig.count('migrations.AlterField(') == 1
   and 'RunPython' not in mig and 'RunSQL' not in mig,
   'the migration is four nullable columns and one choice change - no '
   'data touched')
ok('"0106_es5_signing_lifecycle"' in mig,
   '  and follows the one immediately before it')
ok(all(MARK in NOW[p] for p in EDITED + (VIEW, PAGE)),
   'the round dates itself in every file it touched')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
_old = dict(OLD)
_old.update((p, '') for p in SHIPPED)
held = [m for c, m in claims(_old) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
ok('Every {{ remind_every }} days until they sign' in OLD[CREATE_T],
   'CONTROL: the Send screen really did say "every 2 days" after ES-5 '
   'had built day 3 and day 6')
ok("'awaiting_approval': (env.status == LeaseSigning.COMPLETED" in
   OLD[REG_VIEW],
   'CONTROL: and the register really did guess "waiting" from whether '
   'any lease was attached')
for p in SHIPPED:
    ok(not os.path.isfile(p + SUFFIX),
       'CONTROL: %s has no backup, because this round INVENTED it'
       % os.path.basename(p))


# ==========================================================================
# THE DRIVEN SECTIONS
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.contrib.auth.models import Permission, User
    from django.core import mail
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from django.db import transaction
    from django.test import Client, RequestFactory
    from django.test.utils import override_settings
    from django.utils import timezone
    import pages.models as M
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('sections 3 to 6', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        from django.db import connection
        connection.ensure_connection()
        M.LeaseSigning.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('sections 3 to 6, the whole driven flow',
             'no database: %s' % str(_e).split('\n')[0][:70])


def a_pdf(label):
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 110), label, fontsize=14)
    raw = doc.tobytes()
    doc.close()
    return raw


if have_db:
    tmp = tempfile.mkdtemp(prefix='alv_es6_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            HOST = {'SERVER_NAME': 'localhost'}
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Permission)

            def perm(code):
                return Permission.objects.get_or_create(
                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0]

            boss = User.objects.create_user(
                username='es6boss', password='not-a-real-password',
                email='house@example.com', first_name='Demetri',
                last_name='Manias')
            for code in ('can_edit_tenants', 'can_access_tenants'):
                boss.user_permissions.add(perm(code))
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            boss.is_superuser = True
            boss.save()
            viewer = User.objects.create_user(
                username='es6viewer', password='not-a-real-password')
            viewer.user_permissions.add(perm('can_access_tenants'))
            boss = User.objects.get(pk=boss.pk)
            staff = Client(**HOST)
            staff.force_login(boss)
            look = Client(**HOST)
            look.force_login(viewer)

            n = [0]

            def signed_envelope(with_lease=False):
                n[0] += 1
                prop = M.props.objects.create(
                    prop_name='Flat %d, Apolloneon' % n[0],
                    prop_country='Cyprus')
                ten = M.tenant.objects.create(
                    prop=prop, tenant_type='Individual',
                    tenant_name='Chrystalla Katelari %d' % n[0],
                    tenant_email='chrystalla%d@example.com' % n[0],
                    tenant_lease_start_date=timezone.now().date(),
                    tenant_lease_end_date=(timezone.now()
                                           + timezone.timedelta(days=365)
                                           ).date(),
                    tenant_current='Yes')
                if with_lease:
                    ten.tenant_lease_agreement.save(
                        'old.pdf', ContentFile(a_pdf('OLD LEASE')),
                        save=True)
                now = timezone.now()
                env = M.LeaseSigning(tenant=ten, status='completed',
                                     created_by=boss, sent_at=now,
                                     completed_at=now, page_count=1,
                                     expires_at=now
                                     + timezone.timedelta(days=7))
                env.save()
                env.original_pdf.save('lease.pdf',
                                      ContentFile(a_pdf('LEASE')), save=True)
                env.sealed_pdf.save('sealed.pdf',
                                    ContentFile(a_pdf('SIGNED LEASE %d'
                                                      % env.pk)), save=True)
                M.LeaseSigningParty.objects.create(
                    signing=env, role='alivente', order=0,
                    name='Demetri Manias', email='house@example.com',
                    signed_at=now)
                M.LeaseSigningParty.objects.create(
                    signing=env, role='tenant', order=1,
                    name=ten.tenant_name, email=ten.tenant_email,
                    signed_at=now)
                return env, ten

            def sealed_bytes(env):
                env.sealed_pdf.open('rb')
                try:
                    return env.sealed_pdf.read()
                finally:
                    env.sealed_pdf.close()

            # ==============================================================
            head('3. WAITING, AND WHERE IT SHOWS')
            # ==============================================================
            env, ten = signed_envelope(with_lease=True)
            ok(env.awaiting_approval, 'a completed, sealed envelope is '
               'awaiting approval')
            ok(M.LeaseSigning.pending_approval().filter(pk=env.pk).exists(),
               '  and the table agrees')
            from mysite.context_processors import notification_count
            rq = RequestFactory().get('/')
            rq.user = boss
            ctx = notification_count(rq)
            ok(ctx.get('lease_approvals_waiting', 0) >= 1
               and ctx.get('notification_count', 0) >= 1,
               'the bell counts it, and the dashboards get the number', ctx)
            anon = RequestFactory().get('/')
            from django.contrib.auth.models import AnonymousUser
            anon.user = AnonymousUser()
            ok(notification_count(anon).get('lease_approvals_waiting') == 0,
               '  and nobody signed out is told anything')

            r = staff.get('/lease-signing/%s/' % env.pk)
            page = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and 'Approve and attach' in page
               and 'value="decline"' in page,
               'the envelope page offers Approve and Decline', r.status_code)
            # ES-9, 26 Oct 2026 - NEVER OVER A LEASE: with the envelope's
            # tenancy holding one and no other free at the property,
            # Approve is greyed out and the note names the lease and the
            # way to remove it.
            ok('old' in page and 'disabled' in page
               and 'Manage Lease Agreements' in page,
               '  and, the tenancy holding a lease and nothing else free, '
               'Approve is greyed and the note names the lease - ES-9')
            # ES-8, 25 Oct 2026 - NOBODY BUT A SUPERUSER SEES IT AT ALL.
            # This said a look-only account saw the page without the
            # controls; his decision made the whole page superuser only.
            r = look.get('/lease-signing/%s/' % env.pk)
            ok(r.status_code == 403,
               'somebody who is not a superuser is refused the page '
               'outright - ES-8', r.status_code)

            r = staff.get('/lease-signing/%s/signed.pdf' % env.pk)
            ok(r.status_code == 200 and r['Content-Type'] == 'application/pdf'
               and r.content[:4] == b'%PDF'
               and 'no-store' in r.get('Cache-Control', ''),
               'the signed PDF is served through a permission check and '
               'never cached', r.status_code)
            r = Client(**HOST).get('/lease-signing/%s/signed.pdf' % env.pk)
            ok(r.status_code in (302, 403),
               '  and not to anybody signed out', r.status_code)

            # ==============================================================
            head('4. APPROVE NEVER REPLACES - ES-9 - AND A FAILED SAVE COSTS NOTHING')
            # ==============================================================
            # ES-9, 26 Oct 2026 - his decision on Live: "we must NEVER
            # overwrite a lease". Until ES-9 this section asserted the
            # opposite - approve REPLACED the attached lease and deleted
            # the old file.
            old_name = ten.tenant_lease_agreement.name
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'approve'})
            ten.refresh_from_db()
            env.refresh_from_db()
            ok(r.status_code == 302 and env.approved_at is None
               and env.awaiting_approval
               and ten.tenant_lease_agreement.name == old_name
               and default_storage.exists(old_name),
               'APPROVE OVER A LEASE IS REFUSED: nothing attached, the old '
               'lease attached and on disk, the envelope still waiting')
            # THE RENEWAL: a new tenancy at the same property, no lease.
            renew = M.tenant.objects.create(
                prop=ten.prop, tenant_type='Individual',
                tenant_name=ten.tenant_name, tenant_email=ten.tenant_email,
                tenant_lease_start_date=ten.tenant_lease_end_date
                + timezone.timedelta(days=1),
                tenant_lease_end_date=ten.tenant_lease_end_date
                + timezone.timedelta(days=366), tenant_current='No')
            page = staff.get('/lease-signing/%s/' % env.pk).content.decode(
                'utf-8', 'replace')
            ok('name="target"' in page and 'value="%d"' % renew.pk in page
               and 'value="%d"' % ten.pk not in page.split('name="target"')[1]
               .split('</select>')[0],
               '  and the page offers the FREE tenancy at that property under '
               'Attach to - not the one holding a lease')
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'approve', 'target': ten.pk})
            env.refresh_from_db()
            ok(env.approved_at is None,
               '  and a POST that names the leased tenancy anyway is refused')
            other = M.props.objects.create(prop_name='Elsewhere',
                                           prop_country='Cyprus')
            stray = M.tenant.objects.create(
                prop=other, tenant_type='Individual', tenant_name='Stray',
                tenant_current='Yes')
            staff.post('/lease-signing/%s/approve/' % env.pk,
                       {'action': 'approve', 'target': stray.pk})
            env.refresh_from_db()
            stray.refresh_from_db()
            ok(env.approved_at is None and not stray.tenant_lease_agreement,
               '  and so is one at another property')

            real_save = M.tenant.save

            def boom(self, *a, **k):
                raise RuntimeError('the database went away')
            M.tenant.save = boom
            try:
                with transaction.atomic():
                    r = staff.post('/lease-signing/%s/approve/' % env.pk,
                                   {'action': 'approve', 'target': renew.pk})
            finally:
                M.tenant.save = real_save
            renew.refresh_from_db()
            env.refresh_from_db()
            ok(not renew.tenant_lease_agreement and env.approved_at is None
               and env.awaiting_approval,
               'WHEN THE SAVE RAISES, nothing is attached and the envelope is '
               'still waiting')
            _dir = os.path.join(tmp, 'tenants', 'lease_agreements')
            leftovers = [f for f in (os.listdir(_dir)
                                     if os.path.isdir(_dir) else [])
                         if f != os.path.basename(old_name)]
            ok(not leftovers,
               '  and the new bytes it wrote were removed again - nothing '
               'orphaned', leftovers)

            mail.outbox = []
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'approve', 'target': renew.pk})
            ten.refresh_from_db()
            renew.refresh_from_db()
            env.refresh_from_db()
            ok(r.status_code == 302 and env.approved_at is not None
               and env.approved_by_id == boss.pk,
               'APPROVED onto the renewal, by whom and when', r.status_code)
            renew.tenant_lease_agreement.open('rb')
            try:
                attached = renew.tenant_lease_agreement.read()
            finally:
                renew.tenant_lease_agreement.close()
            ok(attached == sealed_bytes(env),
               '  and the renewal\'s lease IS the sealed copy, byte for byte')
            ok(ten.tenant_lease_agreement.name == old_name
               and default_storage.exists(old_name),
               '  and the OLD tenancy keeps its lease, attached and on disk')
            ok(env.tenant_id == renew.pk
               and env.events.filter(kind='approved',
                                     detail__contains='sent for').exists(),
               '  and the envelope now names where it went; the trail keeps '
               'where it was sent for')
            ok(not env.awaiting_approval and not M.LeaseSigning
               .pending_approval().filter(pk=env.pk).exists(),
               '  and it is no longer waiting')
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'decline'})
            env.refresh_from_db()
            ok(env.approval_declined_at is None,
               'a second press - or a page left open - cannot reverse it')

            # ==============================================================
            head('5. DECLINE IS FINAL AND WRITES NOTHING')
            # ==============================================================
            env2, ten2 = signed_envelope(with_lease=True)
            keep = ten2.tenant_lease_agreement.name
            staff.post('/lease-signing/%s/approve/' % env2.pk,
                       {'action': 'decline'})
            env2.refresh_from_db()
            ten2.refresh_from_db()
            ok(env2.approval_declined_at is not None
               and env2.approval_declined_by_id == boss.pk,
               'declined, by whom and when')
            ok(ten2.tenant_lease_agreement.name == keep
               and default_storage.exists(keep),
               '  and nothing was written to the tenant')
            ok(env2.events.filter(kind='rejected').exists(),
               '  and the trail says so')
            staff.post('/lease-signing/%s/approve/' % env2.pk,
                       {'action': 'approve'})
            env2.refresh_from_db()
            ok(env2.approved_at is None,
               'FINAL - approving afterwards is refused, his decision')

            env3, ten3 = signed_envelope()
            r = look.post('/lease-signing/%s/approve/' % env3.pk,
                          {'action': 'approve'})
            env3.refresh_from_db()
            ok(r.status_code == 403 and env3.approved_at is None,
               'somebody without the edit permission cannot approve',
               r.status_code)
            ok(staff.get('/lease-signing/%s/approve/' % env3.pk).status_code
               == 405, '  and a GET changes nothing - POST only')

            # ==============================================================
            head('6. THE SIGNED COPY, THE REMINDERS AND THE SEND SCREEN')
            # ==============================================================
            from pages.views.lease_signing_sign import _signed_copy
            mail.outbox = []
            _signed_copy(env3)
            to = sorted(sum([list(m.to) for m in mail.outbox], []))
            ok('house@example.com' in to and ten3.tenant_email in to,
               'the signed copy goes to the tenant AND to Alivente - '
               'decision 2 of 23 October', to)
            ok(len(to) == len(set(x.lower() for x in to)),
               '  once each, though the sender and the house signer are '
               'the same person here')

            def window(days):
                n[0] += 1
                prop = M.props.objects.create(prop_name='W%d' % n[0],
                                              prop_country='Cyprus')
                t = M.tenant.objects.create(
                    prop=prop, tenant_type='Individual',
                    tenant_name='W %d' % n[0], tenant_email='w@example.com',
                    tenant_lease_start_date=timezone.now().date(),
                    tenant_lease_end_date=(timezone.now()
                                           + timezone.timedelta(days=365)
                                           ).date(), tenant_current='Yes')
                # ES-7, 25 Oct 2026 - SENT AT 10:00 LOCAL AND CLOSING AT THE
                # END OF THE LAST DAY, the way the Send screen now makes
                # every envelope; probes are local clock times, so the
                # answer cannot depend on what hour the suite runs at.
                import datetime as _dt
                day0 = timezone.localdate()
                start = timezone.make_aware(
                    _dt.datetime.combine(day0, _dt.time(10, 0)))
                e = M.LeaseSigning.objects.create(
                    tenant=t, status='sent', sent_at=start,
                    expires_at=M.LeaseSigning.closing_moment(days, start),
                    original_pdf='x.pdf')

                def at(d, hh=11, mm=0):
                    return timezone.make_aware(_dt.datetime.combine(
                        day0 + _dt.timedelta(days=d), _dt.time(hh, mm)))
                return e, at

            e14, at14 = window(14)
            ok(e14.reminder_due(at14(3)) == 3
               and e14.reminder_due(at14(6)) == 3
               and e14.reminder_due(at14(13, 0, 30)) == 13,
               'FOURTEEN DAYS: day 3 and day 13 - not day 6, which is what '
               'ES-5\'s fixed pair would have sent',
               [e14.reminder_due(x) for x in (at14(3), at14(6),
                                              at14(13, 0, 30))])
            e3, at3 = window(3)
            ok(e3.reminder_due(at3(1, 12)) is None
               and e3.reminder_due(at3(2, 0, 30)) == 2
               and e3.reminder_due(at3(3, 12)) == 2,
               'THREE DAYS: only the day before it lapses - day 3 is the '
               'deadline itself, and since ES-7 the link is open all of it',
               [e3.reminder_due(x) for x in (at3(1, 12), at3(2, 0, 30),
                                             at3(3, 12))])
            e7, at7 = window(7)
            ok(e7.reminder_due(at7(3)) == 3
               and e7.reminder_due(at7(6)) == 6,
               'SEVEN DAYS: still day 3 and day 6, exactly as he decided')
            M.LeaseSigningEvent.objects.create(signing=e7, kind='extended')
            e7.expires_at = timezone.now() + timezone.timedelta(days=7)
            e7.save()
            ok(e7.reminder_due(timezone.now() + timezone.timedelta(days=1))
               is None, 'an extension opens a new window - day 1 of it is '
               'not a reminder day')

            r = staff.get('/lease-signing/new/?tenant=%s' % ten3.pk)
            body = r.content.decode('utf-8', 'replace')
            ok(M.LeaseSigning.REMINDER_RULE in body
               and 'Every 2 days' not in body,
               'the Send screen says "%s"' % M.LeaseSigning.REMINDER_RULE)

            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def awaiting_approval(self):'" in gate,
   '  with a sentinel on the one answer to "is this waiting"')
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
import importlib                                            # noqa: E402
_p = importlib.import_module(PATCHER[:-3])
ok(sorted(os.path.basename(x) for x in _p.CREATES)
   == sorted(os.path.basename(x) for x in SHIPPED),
   '  and declares every file it ships', list(_p.CREATES))
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
