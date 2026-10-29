# -*- coding: utf-8 -*-
"""test_esign_pdf.py - round ES-2, 23 Oct 2026.

E-SIGNING, RUNG TWO: THE TWO THINGS THE FLOW DOES TO A PDF.

  render_pages   the lease, as page images, so the signing page shows
                 the document INSIDE itself
  seal           one appended page, and the sha256 of the result

THE CLAIM THIS SUITE EXISTS TO TEST. The original is never touched.
Everything about this design rests on that: signatures go on an
APPENDED page so the lease everybody signed stays the lease that was
sent, which is also why it works on a PDF nobody here produced.
Section 4 does not take that on trust - it reads every original page
back out of the sealed file and compares the RENDERED PIXELS, which is
the strongest form of the question available.

AND THE ONE THAT CAUGHT A DEFECT. Section 5 prints a Greek name,
because the first draft of this module drew the page in Helvetica -
Base-14, no Greek glyphs - and `Ανδρέας Γεωργίου` came out as
`······· ········`. It did not raise. It produced a signature page
that looked finished and named nobody. This is a Cyprus letting
company; a Greek name on a lease is the ordinary case.

WHAT IS DELIBERATELY NOT HERE. No view, no screen, no route, no
email. ES-1 was the shape of the data and this is the machinery. ES-3
upward is what calls it.
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

import hashlib
import io
import os
import re
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_esignpdf'
ME = 'test_esign_pdf.py'
PATCHER = 'apply_esign_pdf.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-2, 23 Oct 2026'

SEAL = os.path.join(ROOT, 'pages', 'services', 'lease_sealing.py')
REQ = os.path.join(ROOT, 'mysite', 'cron-requirements.txt')
RAIL = os.path.join(ROOT, 'railway.json')
GATE = os.path.join(ROOT, PS1)
FILES = (REQ,)

# THE GREEK NAME IS NOT DECORATION. It is the case the first draft got
# wrong, and a suite that only ever printed ASCII would have passed.
GREEK_TENANT = 'Ανδρέας Γεωργίου'
GREEK_SECOND = 'Μαρία Γεωργίου'

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
SRC = read(SEAL)
CODE = T.python_code_only(SRC, payloads=True)


def fn_body(code, name):
    a = code.find('def %s(' % name)
    if a < 0:
        return ''
    rest = code[a:]
    nxt = re.search(r'\ndef \w+', rest[1:])
    return rest[:nxt.start() + 1] if nxt else rest


def claims(d):
    """Everything this round says about the PIN - the one file it
    EDITS. lease_sealing.py is CREATED by this round, so there is
    nothing to ask these of beforehand; section 2 proves that rather
    than pretending otherwise."""
    r = d[REQ]
    return {
        'pymupdf is pinned': 'pymupdf==1.28.2' in r,
        '  and so are its fonts': 'pymupdf-fonts==1.0.5' in r,
        # NOT `'pymupdf==2.0' not in r`, WHICH IS VACUOUS.
        #
        # That was the first spelling and the control caught it: a
        # file with no pymupdf line at all satisfies it, so the claim
        # held BEFORE the round and would have gone on holding if the
        # pin were deleted tomorrow. Same shape as the `not any(w in
        # drop ...)` that passed against a tree with no drop_file.
        # A claim has to require the thing to be there.
        '  at the last release with NO dependencies of its own':
            'pymupdf==' in r and not re.search(r'pymupdf==2\.', r),
        '  in the file railway.json installs from':
            'pymupdf==1.28.2' in r and 'cron-requirements.txt'
            in read(RAIL),
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

ok(os.path.isfile(SEAL),
   'the service module is on disk', SEAL)
ok('def render_pages(' in CODE and 'def seal(' in CODE,
   '  and carries both halves - render_pages and seal')
ok('pymupdf' in CODE and not re.search(r'(^|\n)\s*import fitz\b', CODE),
   '  opening PDFs as pymupdf, not the deprecated fitz alias')

# THE FONT, WHICH IS WHAT THE DEFECT WAS.
ok("FONT = 'notos'" in CODE and "FONT_BOLD = 'notosbo'" in CODE,
   'it draws with Noto Sans, which carries Greek')
b14 = [f for f in ('helvetica', 'helv', 'times-roman', 'courier',
                   'symbol', 'zapfdingbats')
       if re.search(r"fontname\s*=\s*['\"]%s" % re.escape(f), CODE)]
ok(not b14,
   '  and NOT with a Base-14 font, which has no Greek glyphs and '
   'draws dots instead of raising', b14)

# A STORAGE KEY IS NOT A FILESYSTEM PATH.
pn = fn_body(CODE, 'page_name')
ok('os.path.join' not in pn,
   'the page key is built with slashes, not os.path.join - Windows '
   'here, Linux on Live, and os.path.join gives each a different key')

# SD-1's RULE, IN BOTH PLACES THAT STORE A FILE.
for fn in ('render_pages', 'seal'):
    b = fn_body(CODE, fn)
    d_, s_ = b.find('.delete('), b.find('.save(')
    ok(d_ >= 0 and s_ >= 0 and d_ < s_,
       '%s deletes before it saves - SD-1, because Django storage does '
       'not overwrite' % fn)

ok(MARK in SRC or MARK in NOW[REQ],
   'the round dates itself')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of the pin claims held before this round', held)
ok('pymupdf' not in OLD[REQ],
   'CONTROL: nothing in the requirements named pymupdf at all')

# AND THE SERVICE MODULE GENUINELY DID NOT EXIST.
#
# It is a CREATES file, so there is no backup of it to interrogate -
# and that absence is itself the control, provable rather than
# asserted. A backup WOULD mean the file was here before and this
# round edited it, which would make every claim in section 1 a claim
# about somebody else's work.
ok(not os.path.exists(SEAL + SUFFIX),
   'CONTROL: there is no backup of the service module, because this '
   'round creates it rather than editing something that was here')
ok(PATCHER in os.listdir(ROOT) and 'CREATES' in read(
       os.path.join(ROOT, PATCHER)),
   '  and the patcher declares it as a CREATES file')

# THE DEAD CERTIFICATE PACKAGES ARE STILL THERE, UNTOUCHED.
#
# pyHanko, pyhanko-certvalidator and oscrypto are in both requirement
# files and no Python file in this tree imports any of them. They are
# the certificate-based approach decided against on 23 October.
# Removing three packages is a different claim from adding two, so
# this round leaves them exactly where they are - and says so here,
# so the finding is not lost between rounds.
#
# HK-5, 29 Oct 2026 - AND THEY MUST STAY. xhtml2pdf 0.2.16 (receipts and
# the PDF reports) declares Requires-Dist pyHanko >=0.12.1 and
# pyhanko-certvalidator >=0.19.5. Nothing imports them because xhtml2pdf
# does; taking the pins out would not remove them, it would only let pip
# choose their versions.
ok('pyHanko' in NOW[REQ] and 'pyHanko' in OLD[REQ],
   'CONTROL: the unused pyHanko pins are left alone - removing them '
   'is its own round, named here so it is not forgotten')


# ==========================================================================
head('3. DRIVEN - a real multi-page PDF')
# ==========================================================================
django_up = False
MEDIA = None
# NAMED BEFORE THEY ARE FILLED, so a failure in section 3 produces a
# clean FAIL in section 4 rather than a NameError that says nothing.
ORIGINAL = SEALED = None
env = t_party = None
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
    # THE PAGES GO SOMEWHERE DISPOSABLE. A suite that writes into the
    # real MEDIA_ROOT leaves rendered lease pages in the developer's
    # media folder, which is both litter and, one day, confusing.
    # SETTING MEDIA_ROOT IS NOT ENOUGH, which the first run of this
    # suite proved by leaving three lease PDFs in the developer's own
    # media folder. FileSystemStorage resolves base_location and
    # location as cached_property, ONCE, the first time anything
    # touches storage - and settings are read long before this line.
    # Dropping the cached values is what actually moves the storage.
    MEDIA = tempfile.mkdtemp(prefix='es2_media_')
    dj.MEDIA_ROOT = MEDIA
    from django.core.files.storage import default_storage
    for _attr in ('base_location', 'location'):
        default_storage.__dict__.pop(_attr, None)
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
    skip('sections 3, 4 and 5', 'no database')
else:
    import pymupdf
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from django.utils import timezone
    from pages.models import (LeaseSigning, LeaseSigningParty,
                              LeaseSigningEvent, props,
                              tenant as Tenant)
    from pages.services import lease_sealing as LS

    def make_pdf(pages=3):
        """A lease-shaped PDF: several A4 pages, each with its own
        text, so a page that went missing or moved can be named."""
        d = pymupdf.open()
        for i in range(pages):
            p = d.new_page(width=595, height=842)
            p.insert_text((72, 100), 'CLAUSE %d OF THE AGREEMENT' % (i + 1),
                          fontsize=14, fontname='notosbo')
            p.insert_text((72, 140),
                          'The tenant shall pay rent monthly in advance.',
                          fontsize=10, fontname='notos')
        raw = d.tobytes()
        d.close()
        return raw

    try:
        me = User.objects.create_superuser('es2', 'es2@x.test', 'x')
        pr = props.objects.create(prop_name='Flat 3, Nikis Avenue',
                                  prop_country='Cyprus')
        tn = Tenant.objects.create(tenant_name=GREEK_TENANT, prop=pr)

        ORIGINAL = make_pdf(3)
        env = LeaseSigning.objects.create(tenant=tn, created_by=me)
        env.original_pdf.save('lease.pdf', ContentFile(ORIGINAL),
                              save=True)

        # ---- render_pages
        n = LS.render_pages(env)
        ok(n == 3, 'a three page lease renders three page images', n)
        names = [LS.page_name(env, i + 1) for i in range(3)]
        ok(all(default_storage.exists(nm) for nm in names),
           '  and every one of them is at its DERIVED name, so the '
           'signing page can ask for page 3 without a second list')
        ok(all('\\' not in nm for nm in names),
           '  with slashes in the key, not backslashes', names[0])

        first = default_storage.open(names[0], 'rb').read()
        ok(first[:8] == b'\x89PNG\r\n\x1a\n',
           '  and page one really is a PNG', first[:8])
        px = pymupdf.open(stream=first, filetype='png')
        w = px[0].rect.width
        ok(600 <= w <= LS.MAX_PAGE_PX,
           '  wide enough to read 9pt lease text on a phone, and under '
           'the ceiling', w)
        px.close()

        # SD-1: RE-RENDERING OVERWRITES, it does not multiply.
        before = len(default_storage.listdir(
            os.path.dirname(names[0]))[1])
        LS.render_pages(env)
        after = len(default_storage.listdir(
            os.path.dirname(names[0]))[1])
        ok(before == after == 3,
           're-rendering overwrites at the same three names - Django '
           'storage does not overwrite, so this is SD-1 or nothing',
           '%s then %s' % (before, after))

        # ---- the parties and the trail
        a_party = LeaseSigningParty.objects.create(
            signing=env, role=LeaseSigningParty.ROLE_ALIVENTE, order=0,
            name='Demetri Manias', email='demetri@alivente.online',
            signed_at=timezone.now(), typed_name='Demetri Manias',
            signature_kind=LeaseSigningParty.KIND_TYPED,
            signed_auth=LeaseSigningParty.AUTH_SESSION,
            signed_by_user=me, signed_ip='10.0.0.1')
        t_party = LeaseSigningParty.objects.create(
            signing=env, role=LeaseSigningParty.ROLE_TENANT, order=1,
            name=GREEK_TENANT, email='a.georgiou@example.com',
            signed_at=timezone.now(), typed_name=GREEK_TENANT,
            signature_kind=LeaseSigningParty.KIND_TYPED,
            signed_auth=LeaseSigningParty.AUTH_TOKEN,
            signed_ip='81.4.2.9')
        for kind in ('created', 'sent', 'viewed', 'signed'):
            LeaseSigningEvent.objects.create(signing=env, kind=kind,
                                             party=t_party, ip='81.4.2.9')

        # ---- seal
        digest = LS.seal(env)
        env.save()
        ok(len(digest) == 64 and re.fullmatch(r'[0-9a-f]{64}', digest or ''),
           'sealing returns a sha256 hex digest', (digest or '')[:20])
        ok(env.pdf_sha256 == digest,
           '  and the envelope keeps it, because the file cannot prove '
           'anything on its own')

        env.sealed_pdf.open('rb')
        SEALED = env.sealed_pdf.read()
        env.sealed_pdf.close()
        ok(hashlib.sha256(SEALED).hexdigest() == digest,
           'THE HASH IS OF THE BYTES THAT WERE STORED - not of some '
           'other copy, which is the only version of this claim worth '
           'making')
    except Exception as e:
        ok(False, 'section 3 ran to the end',
           '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('4. DRIVEN - and the original is untouched')
# ==========================================================================
if not django_up:
    skip('the whole section', 'no database')
else:
    try:
        o = pymupdf.open(stream=ORIGINAL, filetype='pdf')
        s = pymupdf.open(stream=SEALED, filetype='pdf')

        ok(s.page_count == o.page_count + 1,
           'the sealed lease has exactly ONE page more than the '
           'original', '%d then %d' % (o.page_count, s.page_count))

        same_text = all(o[i].get_text() == s[i].get_text()
                        for i in range(o.page_count))
        ok(same_text,
           '  and every original page still says exactly what it said')

        same_size = all(
            abs(o[i].rect.width - s[i].rect.width) < 0.01
            and abs(o[i].rect.height - s[i].rect.height) < 0.01
            for i in range(o.page_count))
        ok(same_size, '  at exactly the same size')

        # THE STRONGEST FORM OF THE QUESTION. Text can match while the
        # page has been re-laid-out, re-fonted or had something drawn
        # over it. Pixels cannot.
        def shot(doc, i):
            return hashlib.sha256(
                doc[i].get_pixmap(dpi=72).tobytes('png')).hexdigest()

        pixels = [(shot(o, i), shot(s, i)) for i in range(o.page_count)]
        bad = [i for i, (a, b) in enumerate(pixels) if a != b]
        ok(not bad,
           '  AND RENDERS PIXEL FOR PIXEL THE SAME - which is the whole '
           'basis of appending rather than stamping: the lease '
           'everybody signed is the lease that was sent', bad)

        app = s[s.page_count - 1].get_text()
        ok('Signatures' in app,
           'the appended page is the one carrying the signatures')
        ok('unchanged' in app,
           '  and says so on its face, for whoever reads the PDF alone')
        o.close()
        s.close()
    except Exception as e:
        ok(False, 'section 4 ran', '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('5. DRIVEN - the Greek name, which is what the defect was')
# ==========================================================================
if not django_up:
    skip('the whole section', 'no database')
else:
    try:
        s = pymupdf.open(stream=SEALED, filetype='pdf')
        app = s[s.page_count - 1].get_text()

        ok(GREEK_TENANT in app,
           'the tenant name is on the page IN GREEK - the first draft '
           'drew this in Helvetica and printed a row of dots',
           app[:120])
        ok('·' not in app and '\x00' not in app,
           '  with no dot-rows and no nulls anywhere on the page')
        greek = len(re.findall(r'[Ͱ-Ͽ]', app))
        ok(greek >= len(re.findall(r'[Ͱ-Ͽ]', GREEK_TENANT)),
           '  and every Greek character survived the draw', greek)

        ok('Demetri Manias' in app,
           'the Alivente signer is named too')
        ok('signed in to Alivente' in app,
           '  and the page says HOW each of them proved who they were')
        ok('by emailed link' in app,
           '  which is not the same answer for both of them')
        ok('81.4.2.9' in app,
           '  with the address it was done from')
        ok('What happened' in app and 'Opened' in app,
           'the audit trail is printed ON the document, because with '
           'no certificate a copy must carry its own provenance')
        ok('Envelope %s' % env.pk in app,
           '  and the page names the envelope it belongs to')

        # A MISSING MARK IS NOT A MISSING SIGNATURE.
        s.close()
        raw2, _ = LS.build_sealed(
            env, parties=[t_party], events=list(env.events.all()))
        s2 = pymupdf.open(stream=raw2, filetype='pdf')
        ok(GREEK_TENANT in s2[s2.page_count - 1].get_text(),
           'a party with a typed mark and no drawn image still appears '
           'by name - the row says they signed, the picture is the '
           'decoration')
        s2.close()

        # RE-SEALING LANDS ON ITS OWN NAME - SD-1 again.
        name_before = env.sealed_pdf.name
        LS.seal(env)
        env.save()
        ok(env.sealed_pdf.name == name_before,
           're-sealing lands on the SAME name, so the row never points '
           'at a file one suffix out of date',
           '%s then %s' % (name_before, env.sealed_pdf.name))
    except Exception as e:
        ok(False, 'section 5 ran', '%s: %s' % (type(e).__name__, e))
    finally:
        if MEDIA and os.path.isdir(MEDIA):
            shutil.rmtree(MEDIA, ignore_errors=True)


# ==========================================================================
head('6. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ps1 = read(GATE)
tree = read(os.path.join(ROOT, 'alv_tree.py'))
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
patch = read(os.path.join(ROOT, PATCHER))

ok(ME in ps1, 'the suite is on the gate')
ok(ME in tree, 'and in alv_tree.CONVERTED')
ok(tree.count("'%s'" % ME) == 1, '  exactly once')
ok("'.bak_esignpdf'" in rounds, 'and the round is in alv_rounds.ROUNDS')
ok('lease_sealing.py' in ps1,
   'and the sentinel names the service module on the push gate')
ok('cron-requirements' in ps1,
   '  and a second one says WHY the pin is in that file and not the '
   'other')

for f in ('alv_tree.py', 'alv_rounds.py', 'test_waiting_down.py',
          PS1, os.path.join('mysite', 'cron-requirements.txt')):
    ok(os.path.exists(os.path.join(ROOT, f) + SUFFIX),
       'backed up: %s' % f)

ok(MARK in patch, 'the patcher dates itself')
ok('already applied' in patch, 'and has an already-applied path')
ok('CREATES = (SEAL,)' in patch,
   'and declares the one file it creates')
ok('NO VIEW' in patch.upper() or 'No view' in patch,
   'and says what it deliberately leaves to ES-3')

n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(bool(n) and tree.count(".py',") >= int(n.group(1)) - 2,
   'test_waiting_down.CONVERTED_N moved with the register',
   n.group(1) if n else '?')


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print("""
  Not that a real scanned lease renders well. It proves a PDF
  this suite built renders, at a size a phone can read. A
  200dpi scan of a stapled lease is a different document and
  nobody has put one through this yet.

  Not that the appended page looks right. It proves what the
  page SAYS - the names, the trail, the envelope. Whether it
  looks like an Alivente document is a render Demetri has to
  see, and that is a before-and-after, not an assertion.

  Not that pymupdf installs on Railway. It proves the pin is
  in the file railway.json names. The build is the proof of
  the build, and DP-1 is what will say so.

  Not that the three dead pyHanko pins are harmless. It
  proves nothing in this tree imports them. Removing them is
  its own round.
""")

print('=' * 74)
print('%s   %d passed, %d failed, %d skipped'
      % (ME, passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
