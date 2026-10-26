# -*- coding: utf-8 -*-
"""test_attach_only.py - round ES-10, 26 Oct 2026.

START E-SIGNING ATTACHES THE LEASE, ALWAYS - his decision of 26 October,
from the Start e-signing screen on Live.

    "We are never going to use the lease that is already on the tenant
    record. We will either attach a pdf file, or we will generate it from
    the Lease Generation module."

Since ES-9 a lease is never overwritten, so the file on a tenant record is
the lease that tenancy has ALREADY signed, or nothing. Offering it as the
document to sign could only ever send a signed lease out to be signed
again. So:

    - The screen draws ONE document field: attach the lease as a PDF, and
      it is required. The "use the lease already on this tenant record"
      choice, and the script that hid the upload behind it, are gone.
    - The server agrees: a POST that names the stored lease, with nothing
      attached, comes back to the form and makes nothing.
    - The help says so, and says how a lease from Generate gets here
      (it downloads as Word; save it as a PDF and attach that).
    - Generate -> e-signing stays parked; when it is unparked it becomes
      the second way in.
    - His follow-up the same afternoon: once a PDF is chosen, its name
      appears with a PDF viewer icon that opens that file in the app's own
      PDF viewer modal (components/pdf_viewer.html, like the rest of the
      viewers), straight from the browser, so he can check it is the right
      one before anything is sent.
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

SUFFIX = '.bak_attachonly'
ME = 'test_attach_only.py'
PATCHER = 'apply_attach_only.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-10, 26 Oct 2026'

J = os.path.join
CREATE = J(ROOT, 'pages', 'views', 'lease_signing_create.py')
CREATE_T = J(ROOT, 'pages', 'templates', 'lease_signing_create.html')
HELP_A = J(ROOT, 'pages', 'help_content', 'administration.html')
TSL = J(ROOT, 'test_send_lease.py')
GATE = J(ROOT, PS1)
EDITED = (CREATE, CREATE_T, HELP_A, TSL)

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
    cv = T.python_code_only(src[CREATE])
    tp = T.code_only_js(src[CREATE_T])
    return [
        ('def _stored_pdf(' not in cv and "== 'stored'" not in cv
         and 'ContentFile' not in cv
         and "uploaded = request.FILES.get('lease_pdf')" in cv,
         'the view reads only an attached PDF - nothing in it reads the '
         'lease on the tenant record'),
        ('value="stored"' not in tp and 'lsDoc' not in tp
         and 'name="lease_pdf" accept="application/pdf,.pdf" required' in tp,
         'the screen draws one document field, and it is required'),
        ('id="ls-pdf-view"' in tp and 'class="icon-action-btn icon-pdf"' in tp
         and 'URL.createObjectURL(f)' in tp and 'URL.revokeObjectURL(' in tp
         and "window.openPdfViewer(blobUrl, 'Attached lease', f.name)" in tp
         and "{% include 'components/pdf_viewer.html' %}" in tp
         and 'target="_blank"' not in tp,
         '  and once a PDF is chosen, its name and a viewer icon open THAT '
         'file in the app\'s PDF viewer modal, before anything is sent'),
        ('use the lease already on the tenant record' not in src[HELP_A]
         and 'A lease made in <strong>Generate</strong> downloads as a '
             'Word file' in src[HELP_A],
         'the help says the lease is attached, and how one from Generate '
         'gets here'),
        ("'document': 'stored'" in src[TSL] and 'makes NO envelope' in src[TSL]
         and 'ContentFile(stored.read())' not in src[TSL],
         'test_send_lease no longer asks for the stored lease, and asks '
         'that naming it makes nothing'),
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
ok('Use the lease already on this tenant record' in OLD[CREATE_T],
   'CONTROL: and the screen before it really did offer the stored lease')

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
    import shutil
    import tempfile
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from django.db import connection, transaction
    from django.test import Client, override_settings
    import pages.models as M
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('section 3', 'Django would not start: %s'
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


have_db = False
if django_up:
    try:
        connection.ensure_connection()
        M.LeaseSigning.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    tmp = tempfile.mkdtemp(prefix='es10_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            prop = M.props.objects.create(prop_name='Flat 10, Afaias',
                                          prop_country='Greece')
            ten = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Katerina Example',
                tenant_email='katerina@example.com',
                tenant_lease_start_date=dt.date(2025, 12, 1),
                tenant_lease_end_date=dt.date(2026, 11, 30),
                tenant_current='Yes')
            # THE SIGNED LEASE ALREADY ON THE RECORD - the thing this
            # round stops offering.
            ten.tenant_lease_agreement.save(
                'katerina_signed.pdf', ContentFile(a_pdf(1)), save=True)
            held_name = ten.tenant_lease_agreement.name

            user = User.objects.create_user(
                username='es10sender', password='not-a-real-password',
                email='sender@example.com', first_name='Demetri',
                last_name='Manias')
            user.is_superuser = True
            user.save()
            c = Client(SERVER_NAME='localhost')
            c.force_login(user)

            r = c.get('/lease-signing/new/?tenant=%d' % ten.pk)
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200, 'the form opens for a tenancy that '
               'already has a lease on its record', r.status_code)
            ok('already on this tenant record' not in body
               and 'katerina_signed' not in body
               and 'value="stored"' not in body,
               '  and does NOT offer that lease, nor name its file')
            ok(re.search(r'<input[^>]*name="lease_pdf"[^>]*required', body)
               is not None,
               '  the one document field is there, and required')
            ok('id="ls-pdf-view"' in body and 'id="ls-pdf-name"' in body
               and 'id="pdfViewerModal"' in body,
               '  with the viewer icon waiting for a file to be chosen, and '
               'the app\'s PDF viewer on the page')

            base = {'tenant_id': ten.pk, 'house_name': 'Demetri Manias',
                    'house_email': 'sender@example.com',
                    'signer_1_name': 'Katerina Example',
                    'signer_1_email': 'katerina@example.com',
                    'expiry_days': '7'}
            post = dict(base, document='stored')
            r = c.post('/lease-signing/new/?tenant=%d' % ten.pk, post)
            ok(r.status_code == 302
               and not M.LeaseSigning.objects.filter(tenant=ten).exists(),
               'a POST naming the stored lease, with nothing attached, '
               'comes back and makes NOTHING', r.status_code)

            post = dict(base, lease_pdf=ContentFile(a_pdf(3),
                                                    name='renewal.pdf'))
            r = c.post('/lease-signing/new/?tenant=%d' % ten.pk, post)
            env = M.LeaseSigning.objects.filter(tenant=ten).first()
            ok(env is not None and env.page_count == 3,
               'an attached PDF makes the envelope, from THAT file '
               '(three pages, not the one-page lease on the record)',
               '%s %s' % (r.status_code, env and env.page_count))
            ten.refresh_from_db()
            ok(ten.tenant_lease_agreement.name == held_name,
               '  and the lease on the record is untouched',
               ten.tenant_lease_agreement.name)
            if env is not None:
                ok(env.events.filter(kind='created',
                                     detail__contains='uploaded').exists(),
                   '  and the trail says the document was uploaded')
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
ok("Text = \"request.POST.get('document') == 'stored'\"; Absent = $true"
   in gate, '  with a sentinel that would notice the stored lease coming '
   'back')
ok('ContentFile(stored.read())' not in gate,
   '  and none left asking for the old copy')
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
