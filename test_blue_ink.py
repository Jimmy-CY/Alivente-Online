# -*- coding: utf-8 -*-
"""test_blue_ink.py - round ES-6b, 25 Oct 2026.

EVERY DRAWN SIGNATURE IS BLUE - ON THE PAD AND ON THE SIGNATURE PAGE.

His instruction of 25 October: "All signatures that have been drawn,
need to display in Blue."

THE CLAIM WITH TEETH IS SECTION 3's SEALED PAGE. A mark captured in the
OLD dark grey is sealed, the page is rasterised, and the suite counts
the ink pixels by colour. Reading the source would pass with the call
in place and the colour wrong; only the picture says what was printed.

WHAT IS NOT PROVED HERE. That a browser's canvas honours strokeStyle -
the page is asked what it TELLS the canvas, which is the part this
application owns.
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

import io
import os
import re
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_blueink'
ME = 'test_blue_ink.py'
PATCHER = 'apply_blue_ink.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-6b, 25 Oct 2026'

SEAL = os.path.join(ROOT, 'pages', 'services', 'lease_sealing.py')
SIGN = os.path.join(ROOT, 'pages', 'views', 'lease_signing_sign.py')
PAD = os.path.join(ROOT, 'pages', 'templates', 'lease_sign.html')
GATE = os.path.join(ROOT, PS1)

EDITED = (SEAL, SIGN, PAD)

# THE OLD INK, which the control proves was there and section 3 seals.
OLD_INK = (0x21, 0x34, 0x3c)

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
    seal = T.python_code_only(src[SEAL])
    sign = T.python_code_only(src[SIGN])
    pad = T.code_only_js(src[PAD])
    return [
        (seal.count('SIGNATURE_INK = (') == 1
         and 'SIGNATURE_INK_HEX =' in seal,
         'ONE ink, named once in lease_sealing, with its hex beside it'),
        ('stream=_in_blue(img)' in seal,
         'the signature page prints every drawn mark through it'),
        ("'ink': lease_sealing.SIGNATURE_INK_HEX" in sign,
         'the signing page is handed the same ink'),
        ("ctx.strokeStyle = '{{ ink|escapejs }}'" in pad,
         '  and the pad draws with it'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
_pad = T.code_only_js(NOW[PAD])
ok(not re.search(r"strokeStyle\s*=\s*'#", _pad),
   'the pad carries no ink of its own - a second spelling is a second '
   'answer')
ok('_in_blue' not in T.python_code_only(NOW[SIGN]),
   'the capture path stores what the device sent; blue is applied only '
   'when the page is printed')
ok(all(MARK in NOW[p] for p in EDITED),
   'the round dates itself in every file it touched')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
ok("ctx.strokeStyle = '#21343c';" in OLD[PAD],
   'CONTROL: the pad really did draw in the house dark grey')
ok('page.insert_image(rect, stream=img, keep_proportion=True)'
   in OLD[SEAL],
   'CONTROL: and the signature page printed the mark in whatever colour '
   'it was drawn')


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
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from django.db import transaction
    from django.test import Client
    from django.test.utils import override_settings
    from django.utils import timezone
    import pages.models as M
    from pages.services import lease_sealing as LS
    from PIL import Image, ImageDraw
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('sections 3 and 4', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


def scribble(rgb, flat=False):
    """A drawn mark in `rgb` - on transparency like the pad's, or on
    white paper (`flat`) like a flattened image."""
    if flat:
        im = Image.new('RGB', (300, 90), (255, 255, 255))
        ink = rgb
    else:
        im = Image.new('RGBA', (300, 90), (0, 0, 0, 0))
        ink = rgb + (255,)
    d = ImageDraw.Draw(im)
    d.line([(20, 60), (80, 20), (140, 65), (200, 25), (280, 55)],
           fill=ink, width=6)
    out = io.BytesIO()
    im.save(out, 'PNG')
    return out.getvalue()


def strokes(im):
    """The pixels that are clearly ink, not paper or a soft edge."""
    rgba = im.convert('RGBA')
    return [px for px in rgba.getdata() if px[3] > 200]


if django_up:
    # ======================================================================
    head('3. THE INK ITSELF')
    # ======================================================================
    blue = LS.SIGNATURE_INK
    ok(blue[2] - max(blue[0], blue[1]) >= 80,
       'SIGNATURE_INK is unmistakably blue, %r' % (blue,))
    ok(LS.SIGNATURE_INK_HEX == '#%02x%02x%02x' % blue,
       '  and its hex is the same colour, %s' % LS.SIGNATURE_INK_HEX)

    src = scribble(OLD_INK)
    got = Image.open(io.BytesIO(LS._in_blue(src)))
    ink = strokes(got)
    ok(ink and all(px[:3] == blue for px in ink),
       'a mark drawn in the OLD dark grey comes back blue, every stroke '
       'pixel', '%d stroke pixels, first %r' % (len(ink), ink[:1]))
    a0 = Image.open(io.BytesIO(src)).convert('RGBA').getchannel('A')
    ok(list(got.getchannel('A').getdata()) == list(a0.getdata()),
       '  with its shape untouched - the alpha, edges and all, is the '
       'mark\'s own')

    flat = Image.open(io.BytesIO(LS._in_blue(scribble(OLD_INK,
                                                       flat=True))))
    corner = flat.convert('RGBA').getpixel((2, 2))
    ok(corner[3] == 0,
       'a FLATTENED mark loses its white paper', corner)
    ok(strokes(flat) and all(px[:3] == blue for px in strokes(flat)),
       '  and keeps its ink, in blue')

    junk = b'not an image at all'
    ok(LS._in_blue(junk) == junk,
       'bytes that are not an image come back as they were - a mark in '
       'the wrong colour is cosmetic, a missing one is not')

    # ======================================================================
    head('4. DRIVEN - the pad, and a sealed page, through the application')
    # ======================================================================
    have_db = False
    try:
        from django.db import connection
        connection.ensure_connection()
        M.LeaseSigning.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 4', 'no database: %s'
             % str(_e).split('\n')[0][:70])

    if have_db:
        import datetime as dt
        import pymupdf

        def a_pdf():
            doc = pymupdf.open()
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 110), 'LEASE AGREEMENT', fontsize=14)
            raw = doc.tobytes()
            doc.close()
            return raw

        tmp = tempfile.mkdtemp(prefix='alv_es6b_')
        over = override_settings(
            MEDIA_ROOT=tmp,
            EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
        over.enable()
        try:
            with transaction.atomic():
                prop = M.props.objects.create(prop_name='Flat 3, Engomi',
                                              prop_country='Cyprus')
                ten = M.tenant.objects.create(
                    prop=prop, tenant_type='Individual',
                    tenant_name='Ms. Eleni Pavlou',
                    tenant_email='eleni.pavlou@example.com',
                    tenant_lease_start_date=dt.date(2026, 11, 1),
                    tenant_lease_end_date=dt.date(2027, 10, 31),
                    tenant_current='Yes')
                user = User.objects.create_user(
                    username='es6bsigner', password='not-a-real-password',
                    email='es6b.signer@example.com', first_name='Demetri',
                    last_name='Manias')
                env = M.LeaseSigning.objects.create(
                    tenant=ten, source=M.LeaseSigning.SOURCE_UPLOADED,
                    status=M.LeaseSigning.DRAFT, created_by=user,
                    expires_at=timezone.now() + dt.timedelta(days=7))
                env.original_pdf.save('lease.pdf', ContentFile(a_pdf()),
                                      save=True)
                env.page_count = LS.render_pages(env)
                env.save(update_fields=['page_count'])
                house = M.LeaseSigningParty.objects.create(
                    signing=env, role=M.LeaseSigningParty.ROLE_ALIVENTE,
                    order=0, name='Demetri Manias',
                    email='es6b.signer@example.com')
                M.LeaseSigningParty.objects.create(
                    signing=env, role=M.LeaseSigningParty.ROLE_TENANT,
                    order=1, name='Ms. Eleni Pavlou',
                    email='eleni.pavlou@example.com')

                # ---- THE PAD
                c = Client(SERVER_NAME='localhost')
                c.force_login(user)
                r = c.get('/lease-signing/%d/sign/' % env.pk)
                body = r.content.decode('utf-8', 'replace')
                ok(r.status_code == 200,
                   'the signing page opens for the house signer',
                   r.status_code)
                ok("ctx.strokeStyle = '%s';" % LS.SIGNATURE_INK_HEX
                   in body,
                   '  and tells the pad to draw in %s'
                   % LS.SIGNATURE_INK_HEX)
                ok("strokeStyle = '#21343c'" not in body,
                   '  and not in the old dark grey')

                # ---- A SEALED PAGE, WITH A MARK IN THE OLD INK
                house.signed_at = timezone.now()
                house.signature_kind = 'drawn'
                house.signed_auth = 'session'
                house.read_to_end = True
                house.signature_image.save(
                    'signature.png', ContentFile(scribble(OLD_INK)),
                    save=False)
                house.save()
                raw, n = LS.build_sealed(env)
                doc = pymupdf.open(stream=raw, filetype='pdf')
                pix = doc[doc.page_count - 1].get_pixmap(dpi=110)
                page = Image.frombytes('RGB', (pix.width, pix.height),
                                       pix.samples)
                doc.close()
                dark = [px for px in page.getdata() if min(px) < 140]
                bluish = [px for px in dark if px[2] - px[0] >= 70]
                greyish = [px for px in dark
                           if abs(px[2] - px[0]) < 40
                           and abs(px[1] - px[0]) < 40]
                # THE MARK IS WHERE THE BLUE IS. Names, dates and the
                # trail are near-black text, so grey pixels are
                # expected; what must not exist is the mark's own grey
                # where the mark is.
                box = page.crop((int(56 * 110 / 72), int(120 * 110 / 72),
                                 int(246 * 110 / 72), int(180 * 110 / 72)))
                # BY DIRECTION, NOT BY DISTANCE. A stroke's soft edge
                # is the ink blended towards white paper, which shrinks
                # every channel gap - so a fixed gap calls a blue edge
                # grey. How far blue leans over red, against how far
                # the pixel is from white, does not shrink: about 0.58
                # for this ink at any blend, 0.12 for the old grey.
                def lean(px):
                    return (px[2] - px[0]) / float(max(1, 255 - px[0]))
                bdark = [px for px in box.getdata() if min(px) < 140]
                bblue = [px for px in bdark if lean(px) >= 0.2]
                ok(len(bluish) > 50,
                   'the sealed page carries a blue mark',
                   '%d blue pixels of %d dark' % (len(bluish), len(dark)))
                ok(bdark and len(bblue) == len(bdark),
                   '  and inside the signature box EVERY ink pixel is '
                   'blue - none of the grey it was drawn in',
                   '%d blue of %d ink pixels in the box'
                   % (len(bblue), len(bdark)))
                ok(lean(OLD_INK) < 0.2 <= lean(LS.SIGNATURE_INK),
                   '  CONTROL: and that test calls the old grey grey and '
                   'the new ink blue, %.2f against %.2f'
                   % (lean(OLD_INK), lean(LS.SIGNATURE_INK)))
                ok(len(greyish) > 0,
                   '  CONTROL: the page does have dark grey text, so the '
                   'colour test can tell the two apart')
                stored = house.signature_image
                stored.open('rb')
                kept = stored.read()
                stored.close()
                ok(kept == scribble(OLD_INK),
                   'the STORED mark is byte for byte what the device sent '
                   '- the evidence is not re-coloured, only the page')
                raise Rollback
        except Rollback:
            pass
        finally:
            over.disable()
            shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'stream=_in_blue(img)'" in gate,
   '  with a sentinel on the re-inking of every drawn mark')
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
