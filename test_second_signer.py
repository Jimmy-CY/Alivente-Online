# -*- coding: utf-8 -*-
"""test_second_signer.py - round ES-6c, 25 Oct 2026.

A SECOND TENANT SIGNS ONLY WHEN THE TENANCY HAS ONE - DRIVEN.

Found by him on Live: a one-person tenancy on Send for Signature still
showed the Second Tenant boxes. ES-3b drew a blank second signer for
every one-person tenancy. His decision: the second row appears only when
the tenancy has a second tenant, and the server refuses one otherwise.

THE CLAIM WITH TEETH IS THE HAND-MADE POST. A page that draws no second
row proves nothing about a request that sends one anyway; section 3
sends one and asks whether an envelope was made.

AND A WEAK CLAIM, REPLACED. ES-3b's suite asserted "a tenancy with one
person offers one signer" by checking that the OTHER tenancy's second
tenant was not named on the page - true with the blank row drawn. This
suite asks for the row itself.
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

SUFFIX = '.bak_secondsigner'
ME = 'test_second_signer.py'
PATCHER = 'apply_second_signer.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-6c, 25 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'lease_signing_create.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_create.html')
SENT = os.path.join(ROOT, 'test_sentinels.py')
GATE = os.path.join(ROOT, PS1)

EDITED = (VIEW, PAGE, SENT)

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

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def claims(src):
    view = T.python_code_only(src[VIEW])
    page = src[PAGE]
    sent = T.python_code_only(src[SENT])
    return [
        ('while len(rows) < MAX_TENANT_SIGNERS' not in view
         and "'signers': rows," in view,
         'the prefill draws a second signer only when there is a second '
         'tenant - no blank row'),
        ('if not chosen.has_second_tenant and any(' in view,
         'the server refuses a second signer for a one-person tenancy'),
        ('{% if signers|length > 1 %}' in page
         and 'One tenant on this tenancy.' in page,
         'the note under the signers says which case this is'),
        ("'from .lease_signing_sign import _invite':" in sent
         # ES-10, 26 Oct 2026 - the second pin went with the code it
         # pinned; its retirement note stands in its place.
         and ("'ContentFile(stored.read())':" in sent
              or 'THE SEVENTEENTH - the COPY of a stored lease - WENT'
                 in src[SENT]),
         'ES-3b\'s two sentinels on lease_signing_create.py are pinned, '
         'revealed by ES-6\'s first backup of that file'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
_v = T.python_code_only(NOW[VIEW])
ok(0 <= _v.find('if not chosen.has_second_tenant and any(')
   < _v.find('with transaction.atomic():'),
   '  and the refusal comes before anything is created')
ok(all(MARK in NOW[p] for p in EDITED),
   'the round dates itself in every file it touched')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
ok('while len(rows) < MAX_TENANT_SIGNERS' in T.python_code_only(OLD[VIEW]),
   'CONTROL: the prefill really did pad a one-person tenancy with a blank '
   'second signer')


# ==========================================================================
# THE DRIVEN SECTION
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
    from django.core.files.base import ContentFile
    from django.db import transaction
    from django.test import Client
    from django.test.utils import override_settings
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
        from django.db import connection
        connection.ensure_connection()
        M.LeaseSigning.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


def a_pdf():
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 110), 'LEASE AGREEMENT', fontsize=14)
    raw = doc.tobytes()
    doc.close()
    return raw


if have_db:
    import datetime as dt
    head('3. DRIVEN - both tenancies, through the screen and a hand-made POST')
    tmp = tempfile.mkdtemp(prefix='alv_es6c_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            def a_prop(n):
                return M.props.objects.create(
                    prop_name='Flat %d, Strovolos' % n, prop_country='Cyprus')

            joint = M.tenant.objects.create(
                prop=a_prop(11), tenant_type='Individual',
                tenant_name='Ms. Katerina Hatzianastasiadou',
                tenant_email='katerina.h@example.com',
                tenant_2_name='Mr. Nikos Hatzianastasiadis',
                tenant_2_email='nikos.h@example.com',
                tenant_lease_start_date=dt.date(2026, 12, 1),
                tenant_lease_end_date=dt.date(2027, 11, 30),
                tenant_current='Yes')
            alone = M.tenant.objects.create(
                prop=a_prop(12), tenant_type='Individual',
                tenant_name='Ms. Maria Ioannou',
                tenant_email='maria.ioannou@example.com',
                tenant_lease_start_date=dt.date(2026, 12, 1),
                tenant_lease_end_date=dt.date(2027, 11, 30),
                tenant_current='Yes')

            user = User.objects.create_user(
                username='es6csender', password='not-a-real-password',
                email='es6c.sender@example.com', first_name='Demetri',
                last_name='Manias')
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Permission)
            for code in ('can_edit_tenants', 'can_access_tenants'):
                user.user_permissions.add(Permission.objects.get_or_create(
                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0])
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            user.is_superuser = True
            user.save()
            c = Client(SERVER_NAME='localhost')
            c.force_login(user)

            # ---- THE PAGE
            r = c.get('/lease-signing/new/?tenant=%d' % alone.pk)
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200, 'a one-person tenancy opens the form',
               r.status_code)
            ok('name="signer_1_name"' in body
               and 'maria.ioannou@example.com' in body,
               '  with its tenant filled in')
            ok('name="signer_2_name"' not in body
               and 'name="signer_2_email"' not in body,
               '  and NO second signer row - the boxes he found are gone')
            ok('One tenant on this tenancy.' in body
               and 'Two tenants need two different' not in body,
               '  and the note says how to add a second tenant instead')

            r = c.get('/lease-signing/new/?tenant=%d' % joint.pk)
            body = r.content.decode('utf-8', 'replace')
            ok('name="signer_2_name"' in body
               and 'Mr. Nikos Hatzianastasiadis' in body
               and 'nikos.h@example.com' in body,
               'a joint tenancy still gets its second signer, filled in')
            ok('Two tenants need two different' in body
               and 'One tenant on this tenancy.' not in body,
               '  with the two-addresses note')

            # ---- THE SAME PAGE, CHOSEN AGAIN - his exact path
            r = c.get('/lease-signing/new/?tenant=%d' % alone.pk)
            body = r.content.decode('utf-8', 'replace')
            ok('name="signer_2_name"' not in body,
               'joint first, then "Choose a different tenant" to a '
               'one-person tenancy: still no second row')

            # ---- A HAND-MADE POST
            n0 = M.LeaseSigning.objects.filter(tenant=alone).count()
            r = c.post('/lease-signing/new/?tenant=%d' % alone.pk, {
                'tenant_id': alone.pk, 'document': 'upload',
                'lease_pdf': ContentFile(a_pdf(), name='lease.pdf'),
                'house_name': 'Demetri Manias',
                'house_email': 'es6c.sender@example.com',
                'signer_1_name': 'Ms. Maria Ioannou',
                'signer_1_email': 'maria.ioannou@example.com',
                'signer_2_name': 'Somebody Else',
                'signer_2_email': 'somebody@example.com',
                'expiry_days': '7'})
            ok(r.status_code == 302
               and M.LeaseSigning.objects.filter(tenant=alone).count() == n0,
               'a second signer POSTED for a one-person tenancy is refused '
               '- no envelope made', r.status_code)
            msgs = [str(m) for m in r.wsgi_request._messages]
            ok(any('one tenant signs' in m for m in msgs),
               '  and the refusal says why', msgs)

            # ---- THE ORDINARY SENDS STILL WORK
            r = c.post('/lease-signing/new/?tenant=%d' % alone.pk, {
                'tenant_id': alone.pk, 'document': 'upload',
                'lease_pdf': ContentFile(a_pdf(), name='lease.pdf'),
                'house_name': 'Demetri Manias',
                'house_email': 'es6c.sender@example.com',
                'signer_1_name': 'Ms. Maria Ioannou',
                'signer_1_email': 'maria.ioannou@example.com',
                'expiry_days': '7'})
            env = M.LeaseSigning.objects.filter(tenant=alone).first()
            ok(env is not None and env.parties.filter(
                role=M.LeaseSigningParty.ROLE_TENANT).count() == 1,
               'a one-person send makes an envelope with one tenant signer',
               r.status_code)
            r = c.post('/lease-signing/new/?tenant=%d' % joint.pk, {
                'tenant_id': joint.pk, 'document': 'upload',
                'lease_pdf': ContentFile(a_pdf(), name='lease.pdf'),
                'house_name': 'Demetri Manias',
                'house_email': 'es6c.sender@example.com',
                'signer_1_name': 'Ms. Katerina Hatzianastasiadou',
                'signer_1_email': 'katerina.h@example.com',
                'signer_2_name': 'Mr. Nikos Hatzianastasiadis',
                'signer_2_email': 'nikos.h@example.com',
                'expiry_days': '7'})
            env2 = M.LeaseSigning.objects.filter(tenant=joint).first()
            ok(env2 is not None and env2.parties.filter(
                role=M.LeaseSigningParty.ROLE_TENANT).count() == 2,
               'a joint send still makes an envelope with both tenants',
               r.status_code)
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
ok("Text = 'if not chosen.has_second_tenant and any('" in gate,
   '  with a sentinel on the server-side refusal')
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
