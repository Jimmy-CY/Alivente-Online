# -*- coding: utf-8 -*-
"""test_house_marks.py - round ES-7, 25 Oct 2026.

HIS SIGNATURE AND THE COMPANY STAMP - AND WHAT A TENANT IS SHOWN.

His decisions of 25 October:
  - his signature (blue) and the stamp, "ALIVENTE LIMITED" only, placed
    on the signature page ONLY when he signs for Alivente himself -
    decided by the signed-in account, never by a typed name;
  - stored securely: in the database, never media, never by URL;
    managed by a superuser only;
  - offered as "Use my saved signature" beside Draw and Type, chosen by
    default; the record says "saved", the printed page says "Signed";
  - a tenant never sees the property's internal NAME - the address;
  - a link stays open to the END of the day it names, Cyprus time.

AND A LIVE BUG, FOUND BY HIM THE SAME DAY: the signing page sent
"Origin: null", so Django's CSRF check refused every signature. Section
6 loads the real page in a real browser and reads the Origin header the
browser actually sends - the one thing the test client cannot tell us.

THE CLAIMS WITH TEETH: another account signing for Alivente gets
neither mark, even by a hand-made POST (section 4); and the browser's
Origin (section 6).
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

import base64
import io
import os
import re
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_housemarks'
ME = 'test_house_marks.py'
PATCHER = 'apply_house_marks.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-7, 25 Oct 2026'

J = os.path.join
MODELS = J(ROOT, 'pages', 'models.py')
SEAL = J(ROOT, 'pages', 'services', 'lease_sealing.py')
SIGN = J(ROOT, 'pages', 'views', 'lease_signing_sign.py')
REG = J(ROOT, 'pages', 'views', 'lease_signing.py')
CREATE = J(ROOT, 'pages', 'views', 'lease_signing_create.py')
URLS = J(ROOT, 'pages', 'urls.py')
VINIT = J(ROOT, 'pages', 'views', '__init__.py')
ADMIN = J(ROOT, 'pages', 'templates', 'admin_apms.html')
PAD = J(ROOT, 'pages', 'templates', 'lease_sign.html')
CLOSED = J(ROOT, 'pages', 'templates', 'lease_sign_closed.html')
DONE = J(ROOT, 'pages', 'templates', 'lease_sign_done.html')
STYLES = J(ROOT, 'pages', 'templates', 'lease_sign_styles.html')
DETAIL = J(ROOT, 'pages', 'templates', 'lease_signing_detail.html')
VIEW = J(ROOT, 'pages', 'views', 'house_marks.py')
PAGE = J(ROOT, 'pages', 'templates', 'house_marks.html')
MIG = J(ROOT, 'pages', 'migrations', '0108_es7_house_marks.py')
MAILER = J(ROOT, 'pages', 'services', 'lease_email.py')
GATE = J(ROOT, PS1)

EDITED = (MODELS, SEAL, SIGN, REG, CREATE, URLS, VINIT, ADMIN, PAD, CLOSED,
          DONE, STYLES, DETAIL)
SHIPPED = (VIEW, PAGE, MIG, MAILER)
TENANT_FACING = (PAD, CLOSED, DONE)

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
              (MODELS, SEAL, SIGN, REG, CREATE, URLS, VINIT))
    mk = dict((p, T.code_only(src[p])) for p in
              (ADMIN, PAD, CLOSED, DONE))
    return [
        ('class HouseMark(models.Model):' in py[MODELS]
         and 'def for_signer(cls, user, kind):' in py[MODELS]
         and 'image = models.BinaryField(' in py[MODELS],
         'the marks are a table of PNG bytes, asked by ACCOUNT'),
        ("KIND_SAVED = 'saved'" in py[MODELS]
         and 'mark_signature = models.BinaryField(' in py[MODELS]
         and 'mark_stamp = models.BinaryField(' in py[MODELS],
         'a party records a saved signature, and COPIES both marks'),
        ('def _house_mark(party, request, how, kind):' in py[SIGN]
         and "if how != 'session' or party.role != LeaseSigningParty.ROLE_ALIVENTE:"
         in py[SIGN],
         'only the Alivente party signing BY SESSION can ever get a mark'),
        ('party.mark_stamp = _house_mark(party, request, how,' in py[SIGN]
         and 'if kind == LeaseSigningParty.KIND_SAVED:' in py[SIGN],
         '  the stamp whenever he signs, the saved signature when chosen'),
        ("'saved_signature': _offers_saved(party, request, how)" in py[SIGN]
         and 'id="ls-tab-saved"' in mk[PAD],
         'the page offers "Use my saved signature" - to him only'),
        ("p.signature_kind == 'saved'" in py[SEAL]
         and 'bytes(p.mark_stamp)' in py[SEAL]
         and 'house_stamp' not in py[SEAL],
         'the sealed page prints the COPIES on the party, nothing else'),
        ('def _when(moment, fmt):' in py[SEAL]
         and "cols = (56, 162, 310, w - 56 - 76)" in py[SEAL],
         'the sealed page reads local time with its zone, in four columns'),
        ('def tenant_address(self):' in py[MODELS]
         and 'def _place(env):' in py[SIGN]
         and 'prop.tenant_address' in mk[PAD]
         and 'prop.tenant_address' in mk[CLOSED]
         and 'prop.tenant_address' in mk[DONE],
         'a tenant is shown the ADDRESS, in every email and page'),
        ('def closing_moment(cls, days, now=None):' in py[MODELS]
         and 'LeaseSigning.closing_moment(days)' in py[CREATE]
         and 'LeaseSigning.closing_moment(env.SIGNING_DAYS, now)' in py[REG],
         'links close at the END of the day, from Send and from Extend'),
        ("path('administration/signature-and-stamp/', views.house_marks,"
         in py[URLS] and 'from .house_marks import *' in py[VINIT]
         and "{% url 'house_marks' %}" in mk[ADMIN],
         'the superuser screen is routed and on the Administration page'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
# NOT A CLAIM OF THIS ROUND - the referrer fix shipped in Release 16, the
# day he found it on Live - so it is asserted here and not in claims(),
# whose control would rightly say it held before. Section 6 proves it in
# a real browser.
ok('content="same-origin"' in NOW[PAD]
   and 'content="no-referrer"' not in NOW[PAD],
   'the signing page lets the browser name its origin (Release 16 fix)')
for p in TENANT_FACING:
    ok('prop_name' not in T.code_only(NOW[p]),
       '%s never prints the internal property name'
       % os.path.basename(p))
_sign = T.python_code_only(NOW[SIGN])
_inv = _sign[_sign.index('def _invite('):_sign.index('def _advance(')]
_cpy = _sign[_sign.index('def _signed_copy('):_sign.index('def _invite(')]
ok('prop_name' not in _inv and 'prop_name' not in _cpy,
   '  and nor does any email a tenant receives')
_view = T.python_code_only(NOW[VIEW])
ok('@user_passes_test(lambda u: u.is_superuser)' in _view
   and 'HttpResponse' not in _view and 'FileResponse' not in _view,
   'the screen is superuser-only and returns no image - only a page')
ok("'preview': (_as_data_uri(row)" in _view
   and 'if row and row.owner_id == request.user.pk' in _view,
   '  and shows the preview to the OWNER only, inline')
_mig = T.python_code_only(NOW[MIG])
ok(_mig.count('migrations.AddField(') == 2
   and _mig.count('migrations.CreateModel(') == 1
   and _mig.count('migrations.AlterField(') == 1
   and 'RunPython' not in _mig and 'RunSQL' not in _mig
   and '"0107_es6_lease_approval"' in _mig,
   'the migration is a new table, two nullable columns and one choice - '
   'no data touched, after 0107')
_mailer = T.python_code_only(NOW[MAILER])
ok('class BrandedEmail(EmailMessage):' in _mailer
   and 'PHYSICAL_INVOICE_EMAIL_LOGO' in _mailer
   and 'from ..services.lease_email import BrandedEmail as EmailMessage'
   in T.python_code_only(NOW[SIGN]),
   'every e-signing email is built by the one branded helper, with the '
   'logo the invoice emails already use')
ok(all(MARK in NOW[p] for p in EDITED + SHIPPED if p != MIG)
   and 'ES-7, 25 Oct 2026' in NOW[MIG],
   'the round dates itself in every file it touched')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
_old = dict(OLD)
_old.update((p, '') for p in SHIPPED)
held = [m for c, m in claims(_old) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
ok('content="no-referrer"' in OLD[PAD] or 'content="same-origin"' in OLD[PAD],
   'CONTROL: the backup is the page as Release 16 left it')
ok('prop.prop_name' in OLD[CLOSED],
   'CONTROL: the expired page really did name the property by its '
   'internal name')
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
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.db import transaction
    from django.test import Client
    from django.test.utils import override_settings
    from django.utils import timezone
    import pages.models as M
    from pages.services import lease_sealing as LS
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
        M.HouseMark.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('sections 3 to 6', 'no database (is 0108 applied?): %s'
             % str(_e).split('\n')[0][:70])


def a_pdf(pages=2):
    import pymupdf
    doc = pymupdf.open()
    for n in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 110), 'LEASE AGREEMENT page %d' % (n + 1),
                         fontsize=14)
    raw = doc.tobytes()
    doc.close()
    return raw


def a_mark(rgb, size=(360, 90), flat=False):
    """A drawn mark - on transparency, or on white paper (flat)."""
    from PIL import Image, ImageDraw
    im = Image.new('RGB' if flat else 'RGBA', size,
                   (255, 255, 255) if flat else (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(20, 60), (120, 20), (220, 70), (330, 30)],
           fill=rgb if flat else rgb + (255,), width=8)
    out = io.BytesIO()
    im.save(out, 'PNG')
    return out.getvalue()


HOST = {'SERVER_NAME': 'localhost'}
page_html = None


def link_in(text):
    return bool(re.search(r'/sign/[A-Za-z0-9_-]{20,}/', text or ''))

if have_db:
    import datetime as dt
    import pymupdf
    from PIL import Image
    tmp = tempfile.mkdtemp(prefix='alv_es7_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Permission)

            def perm(code):
                return Permission.objects.get_or_create(
                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0]

            boss = User.objects.create_superuser(
                'es7boss', 'es7.boss@example.com', 'not-a-real-password',
                first_name='Demetri', last_name='Manias')
            other = User.objects.create_user(
                'es7other', 'es7.other@example.com', 'not-a-real-password',
                first_name='Stella', last_name='Simitopoulou')
            for u in (boss, other):
                for code in ('can_edit_tenants', 'can_access_tenants'):
                    u.user_permissions.add(perm(code))
            c = Client(**HOST)
            c.force_login(boss)
            o = Client(**HOST)
            o.force_login(other)

            # ==========================================================
            head('3. THE SCREEN - SUPERUSER ONLY, AND THE MARKS ARE CLEANED')
            # ==========================================================
            ok(o.get('/administration/signature-and-stamp/').status_code
               in (302, 403),
               'a user who is not a superuser cannot open the screen')
            M.HouseMark.objects.all().delete()
            r = c.post('/administration/signature-and-stamp/', {
                'kind': 'signature', 'action': 'upload',
                'image': SimpleUploadedFile(
                    'sig.png', a_mark((46, 90, 164)), 'image/png')})
            r2 = c.post('/administration/signature-and-stamp/', {
                'kind': 'stamp', 'action': 'upload',
                'image': SimpleUploadedFile(
                    'stamp.jpg', a_mark((2, 96, 177), flat=True),
                    'image/png')})
            sig = M.HouseMark.objects.filter(kind='signature').first()
            stamp = M.HouseMark.objects.filter(kind='stamp').first()
            ok(r.status_code == 302 and sig and sig.owner_id == boss.pk,
               'a superuser saves the signature, and OWNS it', r.status_code)
            ok(r2.status_code == 302 and stamp and stamp.owner_id == boss.pk,
               '  and the stamp')
            im = Image.open(io.BytesIO(bytes(stamp.image)))
            ok(im.mode == 'RGBA'
               and im.convert('RGBA').getpixel((1, 1))[3] == 0,
               'a stamp scanned on WHITE PAPER is stored transparent - the '
               'paper would print as a white box', im.mode)
            ok(im.width < 360 and im.height < 90,
               '  and cropped to the ink', im.size)
            body = c.get('/administration/signature-and-stamp/') \
                .content.decode('utf-8', 'replace')
            ok(body.count('data:image/png;base64,') == 2,
               'the owner sees both marks - inline, not by a link')
            ok('/media/' not in body or 'house' not in body,
               '  and nothing points at a file')

            # ==========================================================
            head('4. ONLY WHEN HE SIGNS - BY ACCOUNT, NEVER BY NAME')
            # ==========================================================
            prop = M.props.objects.create(
                prop_name='Internal Name - Do Not Show',
                prop_address1='15 Afaias Street', prop_city='Nicosia',
                prop_pcode='2408', prop_country='Cyprus')
            ten = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Ms. Maria Ioannou',
                tenant_email='maria.es7@example.com',
                tenant_lease_start_date=dt.date(2026, 12, 1),
                tenant_lease_end_date=dt.date(2027, 11, 30),
                tenant_current='Yes')

            def envelope(house_name, house_email):
                e = M.LeaseSigning.objects.create(
                    tenant=ten, source=M.LeaseSigning.SOURCE_UPLOADED,
                    status=M.LeaseSigning.DRAFT, created_by=boss,
                    expires_at=M.LeaseSigning.closing_moment(7))
                e.original_pdf.save('lease.pdf', ContentFile(a_pdf()),
                                    save=True)
                e.page_count = LS.render_pages(e)
                e.save(update_fields=['page_count'])
                h = M.LeaseSigningParty.objects.create(
                    signing=e, role=M.LeaseSigningParty.ROLE_ALIVENTE,
                    order=0, name=house_name, email=house_email)
                t = M.LeaseSigningParty.objects.create(
                    signing=e, role=M.LeaseSigningParty.ROLE_TENANT,
                    order=1, name='Ms. Maria Ioannou',
                    email='maria.es7@example.com')
                return e, h, t

            e1, h1, t1 = envelope('Demetri Manias', 'es7.boss@example.com')
            page = c.get('/lease-signing/%d/sign/' % e1.pk) \
                .content.decode('utf-8', 'replace')
            ok('Use my saved signature' in page
               and 'id="ls-kind" value="saved"' in page,
               'HE is offered his saved signature, chosen by default')
            ok('data:image/png' not in page,
               '  and the image itself is never on the signing page')
            mail.outbox = []
            r = c.post('/lease-signing/%d/sign/' % e1.pk, {
                'consent': '1', 'read_to_end': '1',
                'signature_kind': 'saved', 'seconds_open': '20'})
            h1.refresh_from_db()
            ok(r.status_code == 200 and h1.signature_kind == 'saved'
               and bytes(h1.mark_signature) == bytes(sig.image)
               and bytes(h1.mark_stamp) == bytes(stamp.image)
               and not h1.signature_image,
               'he signs with it: the record says SAVED, and both marks '
               'are COPIED onto his party - nothing written to media',
               (r.status_code, h1.signature_kind))

            # THE LINK EMAIL - the address, not the name, and the whole day
            inv = [m for m in mail.outbox if 'maria.es7@example.com' in m.to]
            ok(inv and '15 Afaias Street, Nicosia' in inv[0].subject
               and 'Internal Name' not in inv[0].subject + inv[0].body,
               'the tenant\'s email names the ADDRESS, never the internal '
               'name', inv[0].subject if inv else mail.outbox)
            # BRANDED, SMALL, NO CONTACT DETAILS - his decisions of 25 Oct.
            if inv:
                raw_msg = inv[0].message()
                types = [p.get_content_type() for p in raw_msg.walk()]
                ok('text/plain' in types and 'text/html' in types,
                   'the email carries a plain version AND a small HTML one',
                   types)
                logo_parts = [p for p in raw_msg.walk()
                              if p.get('Content-ID') == '<alivente_logo>']
                ok(len(logo_parts) == 1
                   and 'cid:alivente_logo' in inv[0].html,
                   '  with the Alivente logo INSIDE the message, not linked',
                   [p.get_content_type() for p in logo_parts])
                ok(link_in(inv[0].html) and link_in(inv[0].body),
                   '  and the signing link in both versions')
                ok(not re.search(r'Tel:|Mobile:|\+357|mailto:',
                                 inv[0].html + inv[0].body),
                   '  and NO contact details - his decision')
            close = timezone.localtime(e1.expires_at)
            ok(inv and ('stays open until the end of %s'
                        % close.strftime('%d %B %Y')) in inv[0].body
               and (close.hour, close.minute) == (23, 59),
               '  and says the link stays open to the END of the day - '
               'which is when it closes', close)
            link = re.search(r'/sign/([^/\s]+)/', inv[0].body).group(1) \
                if inv else ''

            # THE TENANT SIGNS; THE PAGE IS SEALED
            pub = Client(**HOST)
            tp = pub.get('/sign/%s/' % link).content.decode('utf-8', 'replace')
            page_html = tp
            ok('15 Afaias Street' in tp and 'Internal Name' not in tp,
               'the signing page shows the address, not the internal name')
            ok('Use my saved signature' not in tp,
               '  and a tenant is never offered a saved signature')
            r = pub.post('/sign/%s/' % link, {
                'consent': '1', 'read_to_end': '1',
                'signature_kind': 'drawn', 'seconds_open': '30',
                'signature_data': 'data:image/png;base64,'
                + base64.b64encode(a_mark((30, 40, 60))).decode()})
            e1.refresh_from_db()
            ok(e1.status == M.LeaseSigning.COMPLETED and e1.sealed_pdf,
               'the tenant signs and the envelope seals', e1.status)
            e1.sealed_pdf.open('rb')
            doc = pymupdf.open(stream=e1.sealed_pdf.read(), filetype='pdf')
            e1.sealed_pdf.close()
            last = doc[doc.page_count - 1]
            imgs = last.get_images(full=True)
            text = last.get_text()
            ok(len(imgs) == 3,
               'the signature page carries THREE images: his saved '
               'signature, the stamp, and the tenant\'s drawn mark',
               len(imgs))
            ok('Saved' not in text and 'saved' not in text,
               '  and the printed page says nothing about "saved" - his '
               'decision; the record keeps it')
            ok(re.search(r'\d\d:\d\d EES?T', text),
               '  and its times carry the zone they were read in')
            cpy = [m for m in mail.outbox if m.attachments]
            ok(cpy and '15 Afaias Street, Nicosia' in cpy[-1].subject
               and 'Internal Name' not in cpy[-1].subject,
               'the signed-copy email names the address too',
               cpy[-1].subject if cpy else '-')

            # SOMEBODY ELSE SIGNING FOR ALIVENTE
            e2, h2, t2 = envelope('Demetri Manias', 'es7.other@example.com')
            page = o.get('/lease-signing/%d/sign/' % e2.pk)
            ok(page.status_code == 200
               and 'Use my saved signature' not in
               page.content.decode('utf-8', 'replace'),
               'ANOTHER ACCOUNT, even under his NAME, is not offered it',
               page.status_code)
            r = o.post('/lease-signing/%d/sign/' % e2.pk, {
                'consent': '1', 'read_to_end': '1',
                'signature_kind': 'saved', 'seconds_open': '20'})
            h2.refresh_from_db()
            ok(r.status_code == 400 and not h2.signed_at,
               '  and a HAND-MADE POST asking for it is refused, nothing '
               'signed', r.status_code)
            r = o.post('/lease-signing/%d/sign/' % e2.pk, {
                'consent': '1', 'read_to_end': '1',
                'signature_kind': 'typed', 'typed_name': 'Stella S',
                'seconds_open': '20'})
            h2.refresh_from_db()
            ok(h2.signed_at and not h2.mark_stamp and not h2.mark_signature,
               '  and when they sign their own way, NO stamp is copied')

            # ==========================================================
            head('5. THE EXPIRED PAGE, AND THE DAY THE LINK CLOSES')
            # ==========================================================
            e3, h3, t3 = envelope('Demetri Manias', 'es7.boss@example.com')
            M.LeaseSigning.objects.filter(pk=e3.pk).update(
                status='sent', expires_at=timezone.now()
                - timezone.timedelta(hours=2))
            raw3 = t3.issue_token()
            t3.save(update_fields=['token_hash', 'token_issued_at'])
            gone = pub.get('/sign/%s/' % raw3)
            gbody = gone.content.decode('utf-8', 'replace')
            ok(gone.status_code == 410 and '15 Afaias Street' in gbody
               and 'Internal Name' not in gbody,
               'the expired page asks the tenant to quote the ADDRESS',
               gone.status_code)
            now = timezone.now()
            cm = timezone.localtime(M.LeaseSigning.closing_moment(7, now))
            ok(cm.date() == timezone.localdate(now)
               + dt.timedelta(days=7)
               and (cm.hour, cm.minute, cm.second) == (23, 59, 59),
               'closing_moment(7) is 23:59:59 local, seven days on', cm)
            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('6. A REAL BROWSER - WHAT ORIGIN DOES THE FORM SEND?')
# ==========================================================================
# THE LIVE BUG OF 25 OCTOBER. Django's test client sends no Origin, so it
# cannot see this; a browser does, and with <meta referrer=no-referrer>
# it sends "Origin: null", which Django's CSRF check refuses. The real
# page is served to Chromium from memory and the POST is caught before
# it leaves, so nothing here needs a server.
def origin_sent(html):
    from playwright.sync_api import sync_playwright
    seen = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()

        def handle(route):
            req = route.request
            if req.method == 'POST':
                seen['origin'] = req.headers.get('origin')
                route.fulfill(status=200, body='caught')
            elif req.url.startswith('http://localhost/sign/'):
                route.fulfill(status=200, body=html,
                              headers={'Content-Type': 'text/html'})
            else:
                route.abort()
        pg.route('**/*', handle)
        pg.goto('http://localhost/sign/x/')
        pg.evaluate("document.getElementById('ls-form').submit()")
        pg.wait_for_timeout(500)
        b.close()
    return seen.get('origin')


if page_html:
    try:
        got = origin_sent(page_html)
        ok(got == 'http://localhost',
           'the signing form sends a REAL origin, so CSRF accepts it',
           got)
        bad = origin_sent(page_html.replace('content="same-origin"',
                                            'content="no-referrer"'))
        ok(bad == 'null',
           '  CONTROL: with no-referrer the same browser sends "null" - '
           'exactly what Live refused', bad)
    except Exception as exc:                                 # noqa: BLE001
        skip('the browser check', 'Chromium would not start: %s'
             % str(exc).split('\n')[0][:80])
else:
    skip('the browser check', 'no signing page was rendered (no database)')


# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def _house_mark(party, request, how, kind):'" in gate,
   '  with a sentinel on the one place that decides who gets the marks')
ok("Text = 'content=\"same-origin\"'" in gate,
   '  and one on the referrer policy that let nobody sign')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
