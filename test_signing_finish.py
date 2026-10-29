# -*- coding: utf-8 -*-
"""test_signing_finish.py - round ES-8, 25 Oct 2026.

LEASE SIGNING, FINISHED - SUPERUSER ONLY, TOLD AS EACH PERSON SIGNS, AND HELP.

His decisions of 25 October, evening:
    - "for now, only Superusers can see the register and an envelope's
      page or start the e-signing, etc." - signing from an emailed link
      stays open to whoever is named;
    - "Yes, email me" each time somebody signs; the last one says it is
      ready for approval;
    - the button reads Start e-signing; the Done page has a Back for him;
      hovering a signer dot says who and when; the signed lease is one
      click from its register row (Share = the phone's own share sheet);
    - the three report tables stretch full width like every other list;
    - and a Help section for Lease Signing.

THE CLAIMS WITH TEETH: a member of staff who CAN edit tenants is refused
every Lease Signing screen and sees no approval notice; a tenant signing
from a link still works; Alivente is emailed when a tenant signs and never
about its own signature; the Alivente signer's invitation no longer tells
them the lease is already signed by Alivente.
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

SUFFIX = '.bak_signfinish'
ME = 'test_signing_finish.py'
PATCHER = 'apply_signing_finish.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-8, 25 Oct 2026'

J = os.path.join
V = J(ROOT, 'pages', 'views')
TPL = J(ROOT, 'pages', 'templates')
LIST_V = J(V, 'lease_signing.py')
CREATE_V = J(V, 'lease_signing_create.py')
APPROVE_V = J(V, 'lease_signing_approve.py')
SIGN_V = J(V, 'lease_signing_sign.py')
CTX = J(ROOT, 'mysite', 'context_processors.py')
LIST_T = J(TPL, 'lease_signing_list.html')
CREATE_T = J(TPL, 'lease_signing_create.html')
DETAIL_T = J(TPL, 'lease_signing_detail.html')
TLA_T = J(TPL, 'tenant_lease_agreement.html')
ADMIN_T = J(TPL, 'admin_apms.html')
DONE_T = J(TPL, 'lease_sign_done.html')
STYLES_T = J(TPL, 'lease_sign_styles.html')
PD_T = J(TPL, 'tenant_payment_days.html')
OI_T = J(TPL, 'open_invoices_report.html')
CR_T = J(TPL, 'comments_report.html')
HELP = J(ROOT, 'pages', 'help_content', 'administration.html')
GATE = J(ROOT, PS1)
EDITED = (LIST_V, CREATE_V, APPROVE_V, SIGN_V, CTX, LIST_T, CREATE_T,
          DETAIL_T, TLA_T, ADMIN_T, DONE_T, STYLES_T, PD_T, OI_T, CR_T, HELP)
REPORTS = (PD_T, OI_T, CR_T)

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
    lv = T.python_code_only(src[LIST_V])
    cv = T.python_code_only(src[CREATE_V])
    av = T.python_code_only(src[APPROVE_V])
    sv = T.python_code_only(src[SIGN_V])
    cx = T.python_code_only(src[CTX])
    lt = T.code_only(src[LIST_T])
    dn = T.code_only(src[DONE_T])
    tla = T.code_only(src[TLA_T])
    adm = T.code_only(src[ADMIN_T])
    hp = src[HELP]
    return [
        ('def superuser_only(view):' in lv
         and lv.count('@superuser_only') == 3
         # GE-1, 28 Oct 2026 - the Send screen's module gains the
         # generated lease's files and the envelope's Word version, both
         # behind the same gate: three.
         and cv.count('@superuser_only') in (1, 3)
         and av.count('@superuser_only') == 3
         and 'permission_required' not in lv + cv + av,
         'every staff Lease Signing view is superuser only - register, '
         'Start, Extend, Cancel, envelope page, signed PDF, Approve'),
        ('if request.user.is_superuser:' in cx
         and "has_perm('auth.can_access_tenants')" not in cx,
         '  and so is the approval count behind Home and Notifications'),
        ("{% if user.is_superuser %}\n        <a href=\"{% url 'lease_signing_list' %}\"" in adm
         and 'Lease signing is for superusers' in adm,
         '  the Administration tile greys out for anybody else'),
        # HK-1, 26 Oct 2026 - or it is not there at all: the paper-plane
        # left Manage Lease Agreements, his decision. Either way nobody
        # but a superuser can start e-signing from that page.
        (("{% if user.is_superuser %}\n                    <a href=\"{% url 'lease_signing_create' %}" in tla
          and 'E-signing is for superusers' in tla)
         or ('lease_signing_create' not in tla
             and 'HK-1, 26 Oct 2026' in src[TLA_T]),
         '  and so does the paper-plane on Manage Lease Agreements - or, '
         'since HK-1, it is gone'),
        ('Start e-signing' in lt and 'Send a lease for signature' not in lt,
         'the button reads Start e-signing'),
        ("{% if user.is_superuser %}" in dn
         and "{% url 'lease_signing_list' %}" in dn
         and 'Back to Lease Signing' in dn,
         'the Done page offers Back to the register - to a superuser'),
        ("'state_text': _mark_text(p)" in lv and '{{ m.state_text }}' in lt,
         'hovering a signer dot says who and when'),
        ('icon-action-btn icon-pdf' in lt
         and "openPdfViewer('{% url 'lease_signing_sealed' r.env.pk" in lt
         and "{% include 'components/pdf_viewer.html' %}" in lt,
         'the signed lease opens from its register row, in the shared '
         'viewer that shares'),
        ("_tell_house_signed(env, party, 'part', request)" in sv
         and "_tell_house_signed(env, party, 'completed', request)" in sv
         and "'Lease signed by everybody - ready for approval'" in sv,
         'Alivente is emailed as each person signs; the last says ready '
         'for approval'),
        ("'Please sign a lease agreement for Alivente Limited'" in sv,
         'the Alivente signer gets an invitation of its own'),
        (all('<table class="alv-table">' not in src[p]
             and 'class=\\"alv-table\\"' not in src[p]
             and '<table class="table alv-table' in src[p] for p in REPORTS),
         'the three report tables stretch full width'),
        ('data-module-slug="lease_signing"' in hp
         and '{% render_help_modal "lease_signing" %}' in lt,
         'Lease Signing has a Help section, opened from its own page'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
# HK-1, 26 Oct 2026 took this round's block off Manage Lease Agreements,
# date and all; that file now carries HK-1's date instead.
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]
           and not (p == TLA_T and 'HK-1, 26 Oct 2026' in NOW[p])]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))

# THE HELP SAYS WHAT THE SCREENS DO. A help page is a promise, and these
# are the promises most likely to drift from the code under them.
hp = NOW[HELP]
sec = hp[hp.index('data-module-slug="lease_signing"'):]
sec = sec[:sec.index('</section>')]
for words, why in (
        ('Superuser only', 'who may use it'),
        ('Start e-signing', 'the button by its new name'),
        ('Use my saved signature', 'the saved signature'),
        ('day 3', 'when the reminders go'),
        ('seven days from today', 'what Extend does'),
        ('Approve and attach', 'the approval control by its label'),
        ('Share', 'sharing the signed lease'),
        ('type the envelope number', 'what a delete asks for')):
    ok(words in sec, '  the help names %s' % why, words)
ok(sec.count('<article data-tab-slug="lsg-') == 9,
   '  in nine tabs', sec.count('<article data-tab-slug="lsg-'))


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))


# ==========================================================================
# DRIVEN
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
    from django.db import connection, transaction
    from django.test import Client, RequestFactory
    from django.test.utils import override_settings
    from django.utils import timezone
    import pages.models as M
    from pages.services import lease_sealing as LS
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


def a_pdf():
    import pymupdf
    doc = pymupdf.open()
    for n in range(2):
        doc.new_page(width=595, height=842).insert_text(
            (72, 110), 'LEASE page %d' % (n + 1), fontsize=14)
    raw = doc.tobytes()
    doc.close()
    return raw


SIGN = {'consent': '1', 'read_to_end': '1', 'seconds_open': '60',
        'signature_kind': 'typed'}

if have_db:
    import datetime as dt
    head('3. DRIVEN - who may, and who is told')
    tmp = tempfile.mkdtemp(prefix='alv_es8_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Permission)
            boss = User.objects.create_superuser(
                'es8boss', 'es8.boss@example.com', 'not-a-real-password')
            boss.first_name, boss.last_name = 'Demetri', 'Manias'
            boss.save()
            staff = User.objects.create_user(
                'es8staff', 'es8.staff@example.com', 'not-a-real-password')
            for code in ('can_edit_tenants', 'can_access_tenants',
                         'can_access_administration'):
                staff.user_permissions.add(Permission.objects.get_or_create(
                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0])
            staff = User.objects.get(pk=staff.pk)   # drop the perm cache
            HOST = {'SERVER_NAME': 'localhost'}
            c = Client(**HOST)
            c.force_login(boss)
            s = Client(**HOST)
            s.force_login(staff)
            prop = M.props.objects.create(prop_name='Flat 8 Internal',
                                          prop_country='Cyprus')
            ten = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Ms. Elena Test', tenant_email='e.test@example.com',
                tenant_lease_start_date=dt.date(2026, 12, 1),
                tenant_lease_end_date=dt.date(2027, 11, 30),
                tenant_current='Yes')

            def envelope(status=M.LeaseSigning.DRAFT, house_email=None):
                e = M.LeaseSigning.objects.create(
                    tenant=ten, source=M.LeaseSigning.SOURCE_UPLOADED,
                    status=status, created_by=boss,
                    expires_at=M.LeaseSigning.closing_moment(7))
                e.original_pdf.save('lease.pdf', ContentFile(a_pdf()),
                                    save=True)
                e.page_count = LS.render_pages(e)
                e.save(update_fields=['page_count'])
                h = M.LeaseSigningParty.objects.create(
                    signing=e, role=M.LeaseSigningParty.ROLE_ALIVENTE,
                    order=0, name='Demetri Manias',
                    email=house_email or boss.email)
                t1 = M.LeaseSigningParty.objects.create(
                    signing=e, role=M.LeaseSigningParty.ROLE_TENANT,
                    order=1, name='Ms. Elena Test', email='e.test@example.com')
                t2 = M.LeaseSigningParty.objects.create(
                    signing=e, role=M.LeaseSigningParty.ROLE_TENANT,
                    order=2, name='Mr. Pavlos Test', email='p.test@example.com')
                M.LeaseSigningEvent.objects.create(signing=e, kind='created')
                return e, h, t1, t2

            # ---- (a) THE GATE
            env, house, t1, t2 = envelope()
            urls = [('/lease-signing/', 'the register'),
                    ('/lease-signing/new/', 'Start e-signing'),
                    ('/lease-signing/%d/' % env.pk, 'the envelope page')]
            for url, what in urls:
                ok(s.get(url).status_code == 403,
                   'staff who can edit tenants are REFUSED %s' % what)
                ok(c.get(url).status_code == 200,
                   '  while a superuser opens it')
            for url, what in (('/lease-signing/%d/extend/' % env.pk, 'Extend'),
                              ('/lease-signing/%d/cancel/' % env.pk, 'Cancel'),
                              ('/lease-signing/%d/approve/' % env.pk,
                               'Approve')):
                ok(s.post(url, {'action': 'approve'}).status_code == 403,
                   '  and a hand-made POST to %s is refused too' % what)
            env.refresh_from_db()
            ok(env.status == M.LeaseSigning.DRAFT,
               '  and changed nothing', env.status)
            page = s.get('/admin_apms/').content.decode('utf-8', 'replace')
            ok('Lease signing is for superusers' in page,
               'on Administration the tile is greyed for them',
               page[:0])

            # ---- (b) THE REGISTER ITSELF, FOR HIM
            page = c.get('/lease-signing/').content.decode('utf-8', 'replace')
            ok('Start e-signing' in page and 'lease_signingHelpModal' in page,
               'the register offers Start e-signing and its Help')
            ok('Demetri Manias (Alivente Limited) &mdash; still to sign'
               in page,
               '  and a dot says who it is and that they are still to sign')

            # ---- (c) THE HOUSE SIGNS BY SESSION: nobody told about himself
            mail.outbox = []
            r = c.post('/lease-signing/%d/sign/' % env.pk,
                       dict(SIGN, typed_name='Demetri Manias'))
            env.refresh_from_db()
            to = sorted(sum([list(m.to) for m in mail.outbox], []))
            ok(r.status_code == 200 and env.status == M.LeaseSigning.SENT,
               'Alivente signs, and the envelope goes out', env.status)
            ok(to == ['e.test@example.com', 'p.test@example.com'],
               '  only the TENANTS are emailed - nobody is told about '
               'their own signature', to)
            body = r.content.decode('utf-8', 'replace')
            ok('Back to Lease Signing' in body,
               '  and the Done page offers him Back to the register')

            # ---- (d) A TENANT SIGNS FROM A LINK: Alivente is told
            raw = t1.issue_token()
            t1.save(update_fields=['token_hash', 'token_issued_at'])
            anon = Client(**HOST)
            mail.outbox = []
            r = anon.post('/sign/%s/' % raw,
                          dict(SIGN, typed_name='Elena Test'))
            env.refresh_from_db()
            ok(r.status_code == 200 and env.status == M.LeaseSigning.PART,
               'a tenant still signs from the link, logged out - the gate '
               'never touched signing', (r.status_code, env.status))
            ok('Back to Lease Signing' not in r.content.decode('utf-8',
                                                               'replace'),
               '  and is offered no Back to a register they cannot open')
            told = [m for m in mail.outbox if boss.email in m.to]
            ok(len(told) == 1
               and told[0].subject.startswith('Lease signed by Ms. Elena Test')
               and 'Still to sign: Mr. Pavlos Test' in told[0].body,
               'Alivente is emailed that she signed, and who is still to '
               'sign', [m.subject for m in mail.outbox])
            ok(len(told) == 1 and '/lease-signing/%d/' % env.pk in told[0].body,
               '  with a link to the envelope')

            # ---- (e) THE LAST SIGNATURE: ready for approval
            raw = t2.issue_token()
            t2.save(update_fields=['token_hash', 'token_issued_at'])
            mail.outbox = []
            anon.post('/sign/%s/' % raw, dict(SIGN, typed_name='Pavlos Test'))
            env.refresh_from_db()
            told = [m for m in mail.outbox
                    if m.subject.startswith('Lease signed by everybody')]
            ok(env.status == M.LeaseSigning.COMPLETED and len(told) == 1
               and boss.email in told[0].to
               and 'waiting for your approval' in told[0].body,
               'the last signature tells Alivente it is READY FOR APPROVAL',
               [m.subject for m in mail.outbox])

            # ---- (f) THE NOTICE AND THE ROW, ONLY FOR HIM
            from mysite.context_processors import notification_count
            rf = RequestFactory()
            rq = rf.get('/')
            rq.user = staff
            ok(notification_count(rq)['lease_approvals_waiting'] == 0,
               'staff see NO approval waiting - the notice would point at '
               'a page they are refused')
            rq.user = boss
            ok(notification_count(rq)['lease_approvals_waiting'] >= 1,
               '  while he does')
            # ?all=1 - a signed envelope is FINISHED, behind the toggle.
            page = c.get('/lease-signing/?all=1').content.decode('utf-8',
                                                                 'replace')
            ok('icon-action-btn icon-pdf' in page
               and '/lease-signing/%d/signed.pdf' % env.pk in page,
               'the signed lease opens from its register row')
            ok('Ms. Elena Test (Tenant) &mdash; signed ' in page,
               '  and her dot says when she signed')

            # ---- (g) SOMEBODY ELSE SIGNS FOR ALIVENTE: their own words
            mail.outbox = []
            from pages.views.lease_signing_sign import _invite
            env2, h2, _a, _b = envelope(house_email='stella@example.com')
            _invite(env2, h2, rf.get('/', SERVER_NAME='localhost'))
            m = mail.outbox[-1] if mail.outbox else None
            ok(m is not None
               and m.subject.startswith('Please sign a lease agreement for '
                                        'Alivente Limited')
               and 'already been signed by Alivente' not in m.body
               and 'Nothing is sent to the tenant' in m.body,
               'the Alivente signer is asked to sign FOR Alivente - not told '
               'it is already signed', m.subject if m else 'no email')
            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def superuser_only(view):'" in gate,
   '  with a sentinel on the superuser gate')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), '  %s has its backup' % os.path.relpath(p, ROOT))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
