# -*- coding: utf-8 -*-
"""test_generate_esign.py - round GE-1 (with GL-2), 28 Oct 2026.

RELEASE 35 - GENERATE -> E-SIGNING, AND THE GREEK LEASE IN GREEK. His
decisions of 28 October:

    - Generate gets two buttons: Send for e-signing and Download Word. Send
      builds the lease without the hand-signature and witness lines - one
      "Signed electronically" line instead - turns it into a PDF with
      LibreOffice on the server (his option A), and opens the Send screen
      with it attached, to be read before anything is sent.
    - Existing tenants only, with a warning for anything else (a new tenant,
      a Spanish lease, a user who cannot reach the Send screen).
    - The Word version is kept with the envelope ("Absolutely").
    - The server installs LibreOffice and Inter, which stands in for the
      templates' Trebuchet MS in the PDF.
    - GL-2: a Greek lease writes amounts with a dot (€1.250) and the
      address in Greek - the property's new Address (Greek), filled for the
      Athens floors with «οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, 154 52».
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
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_genesign'
ME = 'test_generate_esign.py'
PATCHER = 'apply_generate_esign.py'
PS1 = 'Push-PendingChanges.ps1'
MARKS = ('GE-1, 28 Oct 2026', 'GL-2, 28 Oct 2026')

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
MODELS = J(ROOT, 'pages', 'models.py')
FORMS = J(ROOT, 'pages', 'forms.py')
LEASE = J(ROOT, 'pages', 'views', 'lease_template.py')
CREATE = J(ROOT, 'pages', 'views', 'lease_signing_create.py')
URLS = J(ROOT, 'pages', 'urls.py')
GEN = J(TPL, 'generate_lease_agreement.html')
SEND = J(TPL, 'lease_signing_create.html')
DETAIL = J(TPL, 'lease_signing_detail.html')
PEDIT = J(TPL, 'properties_edit.html')
PADD = J(TPL, 'properties_add.html')
DOCKER = J(ROOT, 'Dockerfile')
HELP = J(ROOT, 'pages', 'help_content', 'administration.html')
GATE = J(ROOT, PS1)
EDITED = [MODELS, FORMS, LEASE, CREATE, URLS, GEN, SEND, DETAIL, PEDIT,
          PADD, DOCKER]
UNDATED = [HELP]
MIGRATION = J(ROOT, 'pages', 'migrations',
              '0114_greek_address_generated_lease.py')
SERVICE = J(ROOT, 'pages', 'services', 'lease_generated.py')
FONTCONF = J(ROOT, 'deploy', 'fonts', '50-alivente-trebuchet.conf')
SHIPS = (MIGRATION, SERVICE, FONTCONF)

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

print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402
from alv_rounds import as_left_by                          # noqa: E402

NOW = dict((p, as_left_by(p, SUFFIX, read)) for p in EDITED + UNDATED)
OLD = dict((p, was(p)) for p in EDITED + UNDATED)


def py(src):
    return T.python_code_only(src)


def claims(src):
    out = []
    m = py(src[MODELS])
    out.append(('prop_address_greek = models.CharField(' in m
                and 'word_docx = models.FileField(' in m
                and 'class GeneratedLease(models.Model):' in m,
                'the property keeps a Greek address, an envelope its Word '
                'version, and a generated lease waits in GeneratedLease'))
    out.append(('"prop_address_greek",' in py(src[FORMS]),
                'PropForm keeps the Greek address'))
    lt = py(src[LEASE])
    out.append(('def esign_refusal(' in lt and 'def _prepare_for_esign(' in lt
                and "request.POST.get('action') == 'esign'" in lt,
                'Generate has a Send for e-signing path, with its refusals'))
    out.append(("s.replace(',', '.') if language == 'greek' else s" in lt
                and "'rental_amount': f'{_n(monthly_rent)}'," in lt,
                'a Greek lease writes its amounts with a dot'))
    out.append(("tenant_address = property_obj.prop_address_greek.strip()"
                in lt, '  and its address in Greek'))
    c = py(src[CREATE])
    out.append(('def _generated(' in c and 'LeaseSigning.SOURCE_GENERATED'
                in c and 'env.word_docx.save(' in c
                and 'def generated_lease_file(' in c
                and 'def lease_signing_word(' in c,
                'the Send screen takes the generated lease, keeps its Word '
                'version, and serves both behind its own gate'))
    u = py(src[URLS])
    out.append(("name='lease_signing_word'" in u
                and "name='generated_lease_file'" in u, '  with routes'))
    g = src[GEN]
    out.append(('id="esign-btn"' in g and 'value="esign"' in g
                and 'value="word"' in g and 'function glEsign()' in g,
                'Generate shows Send for e-signing and Download Word, and says '
                'why Send is off when it is'))
    s = src[SEND]
    out.append(('id="ls-gen-card"' in s and 'name="generated_id"' in s
                and '{% if not generated %} required{% endif %}' in s
                and 'id="ls-gen-other"' in s,
                'the Send screen shows the generated lease, with Read it, '
                'Word version and Attach a different PDF instead'))
    out.append(("{% url 'lease_signing_word' env.pk %}" in src[DETAIL],
                'the envelope page offers the Word version'))
    for pth, name in ((PEDIT, 'Property Edit'), (PADD, 'Property Add')):
        out.append(('id="prop_address_greek"' in T.code_only(src[pth]),
                    '%s has Address (Greek)' % name))
    d = src[DOCKER]
    out.append(('libreoffice-writer-nogui' in d and 'fonts-inter' in d
                and '50-alivente-trebuchet.conf' in d and 'fc-cache' in d,
                'the server installs LibreOffice and Inter'))
    out.append(('<strong>Send for e-signing</strong>' in src[HELP]
                and 'Company Details' in src[HELP],
                'the Help describes both buttons and where the landlord '
                'comes from'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
for p in SHIPS:
    ok(os.path.isfile(p), '%s ships with the round' % os.path.relpath(p, ROOT))
mig = read(MIGRATION) if os.path.isfile(MIGRATION) else ''
ok('"pages", "0113_greek_lease_fields"' in mig
   and "name=\"GeneratedLease\"" in mig
   and "GREEK_ADDRESS = 'οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, 154 52'" in mig
   and "prop_address_greek=''" in mig,
   'migration 0114: the three, after 0113, his address into blanks only')
fc = read(FONTCONF) if os.path.isfile(FONTCONF) else ''
ok('<family>Trebuchet MS</family>' in fc and '<family>Inter</family>' in fc,
   'Trebuchet MS is mapped to Inter on the server')
dated = [os.path.relpath(p, ROOT) for p in EDITED
         if not any(mk in NOW[p] for mk in MARKS)]
ok(not dated, 'the round dates itself in every file it edited',
   ', '.join(dated))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round\'s claims held before it',
   '\n'.join(held))

# ==========================================================================
head('3. DRIVEN - the e-signing version, the PDF, the flow')
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
    from django.test.utils import override_settings
    import pages.models as M
    from pages.views import lease_template as LT
    from pages.services import lease_generated as LG
    from docx import Document
    connection.ensure_connection()
    M.props.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


def doc_text(path):
    return '\n'.join(p.text for p in Document(path).paragraphs)


def a_pdf(label):
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 110), label, fontsize=14)
    raw = doc.tobytes()
    doc.close()
    return raw


if have_db:
    import datetime as dt
    import json
    tmp = tempfile.mkdtemp(prefix='alv_ge1_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    real_pdf = LG.docx_to_pdf
    try:
        with transaction.atomic():
            cy = M.props.objects.create(
                prop_name='GE1 Flat', prop_country='Cyprus',
                prop_available_for_rent='Yes', prop_address1='Foti Pitta 13')
            gr = M.props.objects.create(
                prop_name='GE1 Athens', prop_country='Greece',
                prop_available_for_rent='Yes', prop_address1='Afaias 15',
                prop_floor='3', prop_parking_space='P3',
                prop_deh_number='3138574',
                prop_address_greek='οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, '
                                   '154 52')
            L = dict(tenant_type='Individual', tenant_current='Yes',
                     tenant_rental_type='Monthly',
                     tenant_lease_start_date=dt.date(2026, 7, 1),
                     tenant_lease_end_date=dt.date(2027, 6, 30),
                     tenant_rent=1250, tenant_deposit=2500)
            tc = M.tenant.objects.create(prop=cy, tenant_name='GE1 Tenant',
                                         tenant_email='t@example.com', **L)
            tg = M.tenant.objects.create(prop=gr, tenant_name='GE1 Greek',
                                         tenant_email='g@example.com',
                                         tenant_father_name='Γεωργίου',
                                         tenant_afm='1', tenant_doy='Ψ', **L)
            ad = {'existing_tenant_data': {'tenant_passport_id': 'K1',
                                           'tenant_passport_country': 'Cyprus'},
                  'start_date': '2026-07-01', 'end_date': '2027-06-30',
                  'monthly_rent': '1250', 'security_deposit': '2500',
                  'communal_expenses': '0', 'extension_period': '12',
                  'rental_increase': '0'}

            # ---- THE E-SIGNING VERSION
            p_en = LT.generate_lease_document('cyprus', 'english', cy, tc, ad)
            ok('WITNESSES' in doc_text(p_en),
               'CONTROL: the Word version keeps its witness lines')
            LG.strip_signature_block(p_en, 'english')
            t_en = doc_text(p_en)
            ok('WITNESSES' not in t_en and 'In witness whereof' not in t_en
               and t_en.rstrip().endswith('the fingerprint of this document.')
               and 'Signed electronically.' in t_en,
               'the e-signing version ends with the "Signed electronically" '
               'line - no signature or witness lines')
            ok('1,250' in t_en, '  and an English lease keeps €1,250')
            p_gr = LT.generate_lease_document(
                'greece', 'greek', gr, tg,
                dict(ad, signed_electronically=True))
            LG.strip_signature_block(p_gr, 'greek')
            t_gr = doc_text(p_gr)
            ok('ΟΙ ΣΥΜΒΑΛΛΟΜΕΝΟΙ' not in t_gr
               and 'το υπέγραψαν ηλεκτρονικά.' in t_gr
               and 'Υπογράφηκε ηλεκτρονικά.' in t_gr,
               'the Greek one too, and clause 44 says signed electronically')
            ok('€1.250' in t_gr, 'GL-2: a Greek lease writes €1.250')
            ok('κάτοικος οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, 154 52' in t_gr,
               '  and the address in Greek')
            try:
                LG.strip_signature_block(p_en, 'english')
                ok(False, 'a lease with no signature block is refused')
            except ValueError:
                ok(True, 'a lease with no signature block is refused, not '
                         'sent with an unknown ending')

            # ---- THE PDF
            if LG.soffice():
                pdf = real_pdf(p_en)
                ok(pdf[:5] == b'%PDF-' and LG.page_count(pdf) >= 1,
                   'LibreOffice turns it into a PDF (%d pages)'
                   % LG.page_count(pdf))
            else:
                skip('the real conversion', 'LibreOffice is not installed '
                     'here - it is on the server (Dockerfile)')
            import shutil as _sh
            _which = _sh.which
            _sh.which = lambda name: None
            try:
                LG.docx_to_pdf(p_en)
                ok(False, 'no LibreOffice: a sentence, not a crash')
            except LG.LeasePdfError as exc:
                ok('Download Word' in str(exc),
                   'no LibreOffice: a sentence that says what to do instead')
            finally:
                _sh.which = _which

            # ---- THE REFUSALS
            ok('tenant on record' in (LT.esign_refusal('cyprus', 'new_tenant')
                                      or '')
               and 'Spanish' in (LT.esign_refusal('spain', '5') or '')
               and 'superusers' in (LT.esign_refusal('cyprus', '5', False)
                                    or '')
               and LT.esign_refusal('greece', '5') is None,
               'refused, with the reason: a new tenant, Spain, a user who '
               'cannot reach the Send screen; Greece and Cyprus go through')

            # ---- THE FLOW
            LG.docx_to_pdf = lambda path, timeout=0: a_pdf('GE1 lease')
            u = User.objects.create_user('ge1', 'ge1@example.com', 'x',
                                         is_superuser=True, is_staff=True)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            post = {'country': 'cyprus', 'language': 'english',
                    'property': cy.pk, 'tenant': tc.pk,
                    'additional_data': json.dumps(ad), 'action': 'esign'}
            r = c.post('/generate-lease-agreement/', post)
            gl = M.GeneratedLease.objects.filter(tenant=tc).first()
            ok(r.status_code == 302 and gl is not None
               and r['Location'].endswith('?tenant=%d&generated=%d'
                                          % (tc.pk, gl.pk)),
               'Send for e-signing keeps both versions and opens the Send '
               'screen with them')
            ok(gl and gl.pdf and gl.docx and gl.page_count == 1,
               '  the PDF and the Word version both stored')
            body = c.get(r['Location']).content.decode()
            ok('id="ls-gen-card"' in body
               and 'name="generated_id" id="ls-generated-id" value="%d"'
               % gl.pk in body and 'Read it before sending' in body,
               'the Send screen shows the generated lease, ready to read')
            ok(c.get('/lease-signing/generated/%d/pdf/' % gl.pk)
               .content[:5] == b'%PDF-',
               '  and serves it for the viewer')
            r = c.post('/generate-lease-agreement/',
                       dict(post, tenant='new_tenant',
                            additional_data=json.dumps(dict(
                                ad, is_new_tenant=True,
                                new_tenant_data={'tenant_name': 'X'}))))
            ok(r.status_code == 200 and 'tenant on record' in
               r.content.decode(), 'a new tenant is refused with the reason')
            ok(M.GeneratedLease.objects.count() == 1,
               '  and nothing is built for it')
            r = c.post('/generate-lease-agreement/', dict(post, action='word'))
            ok(r.status_code == 200 and 'attachment' in
               r.get('Content-Disposition', ''),
               'Download Word still downloads the document')

            send = {'tenant_id': tc.pk, 'generated_id': gl.pk,
                    'house_name': 'Someone Else',
                    'house_email': 'other@example.com',
                    'signer_1_name': 'GE1 Tenant',
                    'signer_1_email': 't@example.com', 'expiry_days': '7'}
            r = c.post('/lease-signing/new/?tenant=%d&generated=%d'
                       % (tc.pk, gl.pk), send)
            env = M.LeaseSigning.objects.filter(tenant=tc).first()
            gl.refresh_from_db()
            ok(env is not None and env.source == M.LeaseSigning.SOURCE_GENERATED
               and env.original_pdf and env.word_docx
               and gl.envelope_id == env.pk,
               'Create and sign makes the envelope from it - source '
               '"generated", the Word version kept')
            ok(c.get('/lease-signing/%d/word/' % env.pk).status_code == 200
               and 'Word version' in c.get('/lease-signing/%d/' % env.pk)
               .content.decode(),
               '  and the envelope page offers the Word version')
            body = c.get('/lease-signing/new/?tenant=%d&generated=%d'
                         % (tc.pk, gl.pk)).content.decode()
            ok('id="ls-gen-card"' not in body,
               'a generated lease is used once - it never makes a second '
               'envelope')
            ok(LG.page_count(a_pdf('x')) == 1, 'CONTROL: the stand-in PDF '
                                               'is a real one-page PDF')
            plain = User.objects.create_user('ge1b', 'b@example.com', 'x')
            c2 = Client(SERVER_NAME='localhost')
            c2.force_login(plain)
            ok(c2.get('/lease-signing/generated/%d/pdf/' % gl.pk).status_code
               in (302, 403), 'and the files are behind the Send screen\'s '
                              'gate')
            raise Rollback()
    except Rollback:
        pass
    finally:
        LG.docx_to_pdf = real_pdf
        over.disable()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def _prepare_for_esign('" in gate,
   '  with a sentinel on the e-signing path')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED + UNDATED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
