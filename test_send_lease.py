# -*- coding: utf-8 -*-
"""test_send_lease.py - round ES-3b, 24 Oct 2026.

THE SCREEN THAT MAKES AN ENVELOPE, DRIVEN.

ES-3a shipped a register on 23 October with no way to put a row in
it. This is the suite for the thing that was missing, and section 3
drives it the same way ES-4's does: a real tenancy, a real PDF, a
real POST, and then the envelope is asked what it became.

    A DRY RUN IS NOT A RUN - SB-2, 23 October.

SECTION 4 IS THE PREFILL, AND IT IS WHY THIS ROUND CAME AFTER T2-1.
The 23 October draft of this screen said the tenant model "carries
one email and no second-tenant fields". That was true when it was
written and false by lunchtime. The joint tenant Demetri splits by
hand on the Tenants screen is the person this screen must offer, and
the suite asks it over a tenancy that has one and a tenancy that
does not.

SECTION 5 IS THE DOCUMENT, AND THE CLAIM IS THAT IT IS COPIED. A
stored lease that was merely REFERENCED could be replaced or deleted
from Manage Lease Agreements afterwards, and the document would
change under a signature. The suite deletes the original out from
under the envelope and requires the envelope to still have its own.

SECTION 6 ASKS THE INSTRUMENT where the new row action goes.
alv_rowactions owns LOOK, CHANGE, COPY, ADVANCE, DESTROY; this suite
does not hold a second opinion about it.

WHAT IS NOT PROVED HERE. That a long lease renders quickly. The
pages are rasterised at creation deliberately - slow once, for the
person who chose the file, rather than slow for a tenant on a phone -
and how slow that is depends on the document.
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

SUFFIX = '.bak_sendlease'
ME = 'test_send_lease.py'
PATCHER = 'apply_send_lease.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-3b, 24 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'lease_signing_create.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_create.html')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
VINIT = os.path.join(ROOT, 'pages', 'views', '__init__.py')
REGISTER = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_list.html')
MANAGE = os.path.join(ROOT, 'pages', 'templates',
                      'tenant_lease_agreement.html')
GATE = os.path.join(ROOT, PS1)

EDITED = (URLS, VINIT, REGISTER, MANAGE)
SHIPPED = (VIEW, PAGE)

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

import alv_rowactions as RA                                 # noqa: E402
import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in EDITED + SHIPPED)
OLD = dict((p, was(p)) for p in EDITED)


def row_cell(src):
    """The Manage Lease Agreements desktop action cell."""
    i = src.find('<span class="row-actions">')
    if i < 0:
        return ''
    j = src.find('</span>', src.find('icon-delete', i))
    return src[i:j] if j > 0 else ''


def claims(d):
    code = T.python_code_only(d.get(VIEW, ''), payloads=True)
    mk = T.code_only_js(d.get(PAGE, ''))
    u = T.python_code_only(d[URLS], payloads=True)
    return {
        'an envelope can be made at all':
            "name='lease_signing_create'" in u
            and 'def lease_signing_create(' in code,
        # ES-8, 25 Oct 2026 - or the superuser gate that replaced it,
        # his decision: Lease Signing is superuser only.
        '  behind a login and the tenants edit permission':
            bool(code) and '@login_required' in code
            and ('permission_required' in code
                 or '@superuser_only' in code),
        '  and NOT under the public sign/ prefix ES-4 opened':
            "path('lease-signing/new/'" in u,
        'the signers prefill from the tenancy T2-1 made real':
            'tenant_2_name' in code and 'tenant_2_email' in code,
        '  asking the model whether there IS a second person':
            'has_second_tenant' in code,
        '  and reading the first address through tenant_emails':
            'tenant_emails' in code,
        'the lease already on the record can be used':
            'tenant_lease_agreement' in code and 'stored' in mk,
        '  and is COPIED onto the envelope, never referenced':
            'ContentFile(stored.read())' in code,
        'the pages are rendered when the envelope is made':
            'render_pages' in code,
        'no tenant link is minted here':
            bool(code) and 'issue_token' not in code,
        '  and the house signer is emailed only when it is not you':
            '_invite(' in code and '_is_me(' in code,
        'the register button goes somewhere':
            "{% url 'lease_signing_create' %}" in T.code_only_js(
                d[REGISTER]),
        # HK-1, 26 Oct 2026 - THE SEND ROW ACTION ON MANAGE LEASE
        # AGREEMENTS IS GONE, his decision ("if a Lease Agreement is in
        # here, it has already been signed"). Its three claims went with
        # it; test_housekeeping.py asserts the absence. The way in is the
        # register button above.
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)
ok(MARK in NOW[URLS], 'the round dates itself, on one line')
ok("'lease_signing_create'" in T.python_code_only(NOW[VIEW], payloads=True),
   'the view is in __all__, so the URLconf can see it')

# THE ORDER, PRINTED RATHER THAN ASSERTED BLIND - the house rule since
# the planter ceiling of 21 October: print the measurement, assert the
# shape.
#
# HK-1, 26 Oct 2026 - send left the row, his decision; what remains must
# still be in house order.
verbs = RA.verbs_of(row_cell(T.code_only_js(NOW[MANAGE])))
print('       row actions now: %s' % ' -> '.join(verbs))
ok('send' not in verbs and RA.in_order(verbs),
   '  Manage Lease Agreements offers no send since HK-1, and what is left '
   'is in house order', verbs)


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
before = dict(OLD)
before[VIEW] = ''
before[PAGE] = ''
held = [m for m, v in claims(before).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
ok("name='lease_signing_create'" not in
   T.python_code_only(OLD[URLS], payloads=True),
   'CONTROL: there really was no way to create an envelope')
ok("{% url 'lease_signing_list' %}\" class=\"btn action-primary"
   in T.code_only_js(OLD[REGISTER]).replace('\n', ' ').replace('  ', ' ')
   or 'lease_signing_create' not in T.code_only_js(OLD[REGISTER]),
   "CONTROL: and ES-3a's own button pointed back at its own page, "
   'because the screen it wanted did not exist yet')
ok('icon-send' not in row_cell(T.code_only_js(OLD[MANAGE])),
   'CONTROL: Manage Lease Agreements had no way to send anything')
for p in SHIPPED:
    ok(not os.path.isfile(p + SUFFIX),
       'CONTROL: %s has no backup, because this round INVENTED it'
       % os.path.basename(p))


# ==========================================================================
head('3. DRIVEN - a real envelope, made through the screen')
# ==========================================================================
django_up = False
try:
    import datetime as dt
    import shutil
    import tempfile

    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.contrib.auth.models import Permission, User
    from django.core import mail
    from django.core.files.base import ContentFile
    from django.db import transaction
    from django.test import Client
    from django.test.utils import override_settings
    import pages.models as M
    django_up = True
except Exception as e:
    skip('sections 3 to 6', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


def a_pdf(pages=2):
    import pymupdf
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 110), 'LEASE AGREEMENT', fontsize=18)
        page.insert_text((72, 150), 'Page %d' % (i + 1), fontsize=11)
    raw = doc.tobytes()
    doc.close()
    return raw


class Rollback(Exception):
    """Nothing this suite writes survives it."""


if not django_up:
    skip('the flow', 'no Django')
else:
    try:
        from django.db import connection
        connection.ensure_connection()
        have_db = True
    except Exception as _e:                            # noqa: BLE001
        have_db = False
        skip('sections 3 to 6, the whole driven flow',
             'no database: %s' % str(_e).split('\n')[0][:70])

    tmp = tempfile.mkdtemp(prefix='alv_es3b_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        if not have_db:
            raise Rollback
        with transaction.atomic():
            HOST = {'SERVER_NAME': 'localhost'}

            # ONE PROPERTY EACH. tenant.clean() refuses two ACTIVE
            # tenancies on one property over the same period - the
            # model doing its job, and the first draft of this fixture
            # asking it the wrong question.
            def a_prop(n):
                return M.props.objects.create(
                    prop_name='Flat %d, Palikaridi' % n,
                    prop_country='Cyprus')

            prop = a_prop(7)
            joint = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Mr. Dorian Tirouard',
                tenant_email='dorian.tirouard@example.com',
                tenant_2_name='Mr. Antoine Madelbos',
                tenant_2_email='antoine.madelbos@example.com',
                tenant_lease_start_date=dt.date(2026, 9, 1),
                tenant_lease_end_date=dt.date(2028, 8, 31),
                tenant_current='Yes')
            alone = M.tenant.objects.create(
                prop=a_prop(8), tenant_type='Individual',
                tenant_name='Elisavet Solomonidou',
                tenant_email='elisavet@example.com',
                tenant_lease_start_date=dt.date(2026, 7, 1),
                tenant_lease_end_date=dt.date(2027, 6, 30),
                tenant_current='Yes')
            # THE STORED LEASE, so the second half of the document
            # decision has something to be about.
            alone.tenant_lease_agreement.save(
                'solomonidou.pdf', ContentFile(a_pdf(1)), save=True)

            user = User.objects.create_user(
                username='es3bsender', password='not-a-real-password',
                email='sender@example.com', first_name='Demetri',
                last_name='Manias')
            # THE PERMISSIONS, AND A FINDING THAT CAME OUT OF MAKING
            # THEM.
            #
            # create_module_permissions makes the ten can_access_*
            # rows. It makes NO can_edit_* row, and neither does any
            # migration: grep the tree and can_edit_tenants appears
            # only in the views that REQUIRE it. It exists on Live
            # because somebody created it by hand in the Django admin.
            #
            # So a fresh deployment of this application has ten access
            # permissions and no edit permissions at all, and every
            # @permission_required('auth.can_edit_*') view answers 403
            # to everybody who is not a superuser. Recorded here
            # rather than fixed - it is its own round, and it is not
            # ES-3b's to take.
            from django.contrib.contenttypes.models import ContentType
            from django.core.management import call_command
            call_command('create_module_permissions', verbosity=0)
            ct = ContentType.objects.get_for_model(Permission)
            made_by_hand = Permission.objects.get_or_create(
                codename='can_edit_tenants',
                defaults={'name': 'Can edit Tenants', 'content_type': ct})[1]
            # PRINTED, NOT ASSERTED (25 Oct). Whether this get_or_create
            # MADE the row is a fact about the DATABASE the suite runs
            # against, not about the round: an empty sandbox database
            # has no can_edit_tenants, and his local database mirrors
            # Live, where it was made by hand. Asserting it failed the
            # Release 14 gate on his machine with 69 of 70 green. The
            # finding stands - nothing in the TREE creates the row -
            # and is still its own round.
            print('  note can_edit_tenants %s in this database; nothing '
                  'in the tree creates it (its own round)'
                  % ('was ABSENT' if made_by_hand else 'already exists'))
            for code in ('can_edit_tenants', 'can_access_tenants'):
                p_ = Permission.objects.filter(codename=code).first()
                if p_:
                    user.user_permissions.add(p_)
            user = User.objects.get(pk=user.pk)
            ok(user.has_perm('auth.can_edit_tenants')
               and user.has_perm('auth.can_access_tenants'),
               'and the fixture holds both, so what follows is about '
               'the screen and not about permissions')
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            user.is_superuser = True
            user.save()

            c = Client(**HOST)
            c.force_login(user)

            # ---- (a) THE PICKER
            r = c.get('/lease-signing/new/')
            ok(r.status_code == 200, 'the send screen opens',
               r.status_code)
            body = r.content.decode('utf-8', 'replace')
            ok('Mr. Dorian Tirouard' in body,
               '  listing current tenancies to choose from')

            # ---- (b) A TENANCY WITH A JOINT TENANT
            r = c.get('/lease-signing/new/?tenant=%d' % joint.pk)
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200, 'choosing a tenancy opens the form',
               r.status_code)
            ok('Mr. Antoine Madelbos' in body
               and 'antoine.madelbos@example.com' in body,
               'THE SECOND TENANT IS PREFILLED - which is the whole '
               'reason this round waited for T2-1')
            ok('dorian.tirouard@example.com' in body,
               '  and so is the first')
            ok('Demetri Manias' in body,
               '  with the creator named as the Alivente signer')

            # ---- (c) A TENANCY WITH ONE PERSON AND A STORED LEASE
            r = c.get('/lease-signing/new/?tenant=%d' % alone.pk)
            body = r.content.decode('utf-8', 'replace')
            ok('Antoine' not in body,
               'a tenancy with one person offers one signer, not a blank '
               'second one pretending to be somebody')
            ok('already on this tenant record' in body,
               '  and the lease already on the record is offered')

            # ---- (d) THE REFUSALS
            n0 = M.LeaseSigning.objects.count()
            r = c.post('/lease-signing/new/?tenant=%d' % joint.pk, {
                'tenant_id': joint.pk, 'document': 'upload',
                'house_name': 'Demetri Manias',
                'house_email': 'sender@example.com',
                'signer_1_name': 'A', 'signer_1_email': 'a@example.com',
                'expiry_days': '7'})
            ok(r.status_code == 302
               and M.LeaseSigning.objects.count() == n0,
               'a send with no document attached makes nothing, and '
               'comes BACK to the form rather than erroring',
               r.status_code)

            r = c.post('/lease-signing/new/?tenant=%d' % joint.pk, {
                'tenant_id': joint.pk, 'document': 'upload',
                'lease_pdf': ContentFile(b'not a pdf', name='scan.jpg'),
                'house_name': 'Demetri Manias',
                'signer_1_name': 'A', 'signer_1_email': 'a@example.com',
                'expiry_days': '7'})
            ok(r.status_code == 302
               and M.LeaseSigning.objects.count() == n0,
               'and nor does a JPEG - ES-2 rasterises the original, and '
               'a photograph of a lease has no pages to show',
               r.status_code)

            r = c.post('/lease-signing/new/?tenant=%d' % joint.pk, {
                'tenant_id': joint.pk, 'document': 'upload',
                'lease_pdf': ContentFile(a_pdf(1), name='l.pdf'),
                'house_name': 'Demetri Manias',
                'signer_1_name': 'A', 'signer_1_email': 'same@example.com',
                'signer_2_name': 'B', 'signer_2_email': 'SAME@example.com',
                'expiry_days': '7'})
            ok(r.status_code == 302
               and M.LeaseSigning.objects.count() == n0,
               'and nor do two tenants sharing one address - one link '
               'would sign for both and the trail could not tell them '
               'apart', r.status_code)

            r = c.post('/lease-signing/new/?tenant=%d' % joint.pk, {
                'tenant_id': joint.pk, 'document': 'upload',
                'lease_pdf': ContentFile(a_pdf(1), name='l.pdf'),
                'house_name': 'Demetri Manias',
                'signer_1_name': 'A', 'signer_1_email': '',
                'expiry_days': '7'})
            ok(r.status_code == 302
               and M.LeaseSigning.objects.count() == n0,
               'and nor does a signer with no address - the link is how '
               'they reach the document', r.status_code)


            # ==========================================================
            head('4. AND THEN, PROPERLY')
            # ==========================================================
            mail.outbox = []
            r = c.post('/lease-signing/new/?tenant=%d' % joint.pk, {
                'tenant_id': joint.pk, 'document': 'upload',
                'lease_pdf': ContentFile(a_pdf(2), name='lease.pdf'),
                'house_name': 'Demetri Manias',
                'house_email': 'sender@example.com',
                'signer_1_name': 'Mr. Dorian Tirouard',
                'signer_1_email': 'dorian.tirouard@example.com',
                'signer_2_name': 'Mr. Antoine Madelbos',
                'signer_2_email': 'antoine.madelbos@example.com',
                'expiry_days': '7'})
            env = M.LeaseSigning.objects.filter(tenant=joint).first()
            ok(env is not None, 'an envelope is made', r.status_code)
            if env is None:
                raise AssertionError('nothing below can be asked')

            ok(r.status_code == 302
               and r['Location'] == '/lease-signing/%d/sign/' % env.pk,
               '  and the creator is handed STRAIGHT to the signing '
               'page, because the Alivente signer is them - no email, '
               'no round trip',
               '%s %s' % (r.status_code, r.get('Location')))
            ok(env.status == M.LeaseSigning.DRAFT,
               '  the envelope is a DRAFT until the house signs', env.status)
            ok(env.page_count == 2,
               '  with its pages already rendered, so a tenant on a '
               'phone does not wait for it', env.page_count)
            ok(env.expires_at is not None,
               '  and an expiry date STORED, not computed from sent_at - '
               'an extension moves it and the tenant was told a date')

            parties = list(env.parties.order_by('order'))
            ok([p.role for p in parties] == ['alivente', 'tenant', 'tenant'],
               '  three signers, Alivente first at order 0',
               [(p.order, p.role, p.name) for p in parties])
            ok(parties[2].name == 'Mr. Antoine Madelbos',
               '  the joint tenant among them, by name',
               parties[2].name)
            ok(not any(p.token_hash for p in parties if p.role == 'tenant'),
               'NO TENANT LINK IS LIVE YET - "it is only then sent to '
               'the tenant". A token minted now is a credential for a '
               'document nobody has committed to')
            ok(mail.outbox == [],
               '  and nothing was emailed, because the signer is the '
               'person at the keyboard', [m.to for m in mail.outbox])
            ok(env.events.filter(kind='created').exists(),
               '  while the trail records that it was made')

            # ---- THE OTHER SIGNER
            mail.outbox = []
            r = c.post('/lease-signing/new/?tenant=%d' % alone.pk, {
                'tenant_id': alone.pk, 'document': 'upload',
                'lease_pdf': ContentFile(a_pdf(1), name='l.pdf'),
                'house_name': 'Someone Else',
                'house_email': 'colleague@example.com',
                'signer_1_name': 'Elisavet Solomonidou',
                'signer_1_email': 'elisavet@example.com',
                'expiry_days': '7'})
            ok(r.status_code == 302 and '/lease-signing/' in r['Location']
               and '/sign/' not in r['Location'],
               'naming somebody ELSE as the Alivente signer lands you '
               'back on the register instead', r.get('Location'))
            ok(len(mail.outbox) == 1
               and mail.outbox[0].to == ['colleague@example.com'],
               '  and emails THEM the link - one page, two ways in',
               [m.to for m in mail.outbox])


            # ==========================================================
            head('5. THE STORED LEASE IS COPIED, NOT REFERENCED')
            # ==========================================================
            #
            # A reference would let Manage Lease Agreements replace or
            # delete the document AFTER it had been signed, and a lease
            # that changed under a signature is the one thing ES-2's
            # hash exists to make impossible.
            alone2 = M.tenant.objects.create(
                prop=a_prop(9), tenant_type='Individual',
                tenant_name='Anastasia Spiropoulou',
                tenant_email='anastasia@example.com',
                tenant_lease_start_date=dt.date(2026, 7, 1),
                tenant_lease_end_date=dt.date(2027, 6, 30),
                tenant_current='Yes')
            alone2.tenant_lease_agreement.save(
                'spiropoulou.pdf', ContentFile(a_pdf(3)), save=True)
            stored_name = alone2.tenant_lease_agreement.name

            r = c.post('/lease-signing/new/?tenant=%d' % alone2.pk, {
                'tenant_id': alone2.pk, 'document': 'stored',
                'house_name': 'Demetri Manias',
                'house_email': 'sender@example.com',
                'signer_1_name': 'Anastasia Spiropoulou',
                'signer_1_email': 'anastasia@example.com',
                'expiry_days': '7'})
            env2 = M.LeaseSigning.objects.filter(tenant=alone2).first()
            ok(env2 is not None,
               'the lease already on the record makes an envelope with '
               'no upload at all', r.status_code)
            if env2 is not None:
                ok(env2.page_count == 3,
                   '  and it is really that document, three pages of it',
                   env2.page_count)
                ok(env2.original_pdf.name != stored_name,
                   '  stored under its OWN name, not the record one',
                   env2.original_pdf.name)

                # NOW TAKE THE ORIGINAL AWAY.
                alone2.tenant_lease_agreement.delete(save=True)
                env2.refresh_from_db()
                env2.original_pdf.open('rb')
                try:
                    kept = env2.original_pdf.read()
                finally:
                    env2.original_pdf.close()
                ok(kept[:4] == b'%PDF',
                   '  and DELETING the lease off the tenant record leaves '
                   'the envelope intact - which a reference would not '
                   'have done, and a signature over a vanished document '
                   'is the failure ES-2 hash exists to prevent')

            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('6. THE WAYS IN')
# ==========================================================================
# HK-1, 26 Oct 2026 - ONE WAY IN NOW: Lease Signing > Start e-signing.
# The Manage Lease Agreements row action and its phone twin went, his
# decision; the phone bar says two again, because base sizes it from that.
ok('lease_signing_create' not in T.code_only_js(NOW[MANAGE]),
   'Manage Lease Agreements no longer starts e-signing (HK-1)')
bar_i = T.code_only_js(NOW[MANAGE]).find('mobile-action-bar')
bar = T.code_only_js(NOW[MANAGE])[bar_i:bar_i + 2400]
ok('fa-paper-plane' not in bar and 'cols-2' in bar[:60],
   '  nor its phone bar, which says it holds two', bar[:60])

# THE ICON VOCABULARY IS NOT A FREE CHOICE. icon-send wears
# fa-paper-plane everywhere in this tree and test_icon_names fails any
# class that wears two glyphs.
#
# HK-1, 26 Oct 2026 - asked of the register's Resend now, the one
# icon-send left in this flow.
reg = T.code_only_js(NOW[REGISTER])
i_s = reg.find('icon-send')
ok(i_s >= 0 and 'fa-paper-plane' in reg[i_s:i_s + 320],
   'the register Resend wears the house glyph for send')


# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('ContentFile(stored.read())' in gate,
   '  with a sentinel that would notice the stored lease becoming a '
   'reference')
ok('from .lease_signing_sign import _invite' in gate,
   '  and one that would notice a second spelling of mint-and-send')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
import importlib                                            # noqa: E402
_p = importlib.import_module(PATCHER[:-3])
ok(sorted(os.path.basename(x) for x in _p.CREATES)
   == sorted(os.path.basename(x) for x in SHIPPED),
   '  and declares every file it ships, so stage_round cannot leave '
   'one behind', list(_p.CREATES))
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
