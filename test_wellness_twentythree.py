# -*- coding: utf-8 -*-
"""test_wellness_twentythree.py - round WL-19, 12 Nov 2026.

RELEASE 68 - WELLNESS: PROGRESS PHOTOS AND DOWNLOAD YOUR DATA.
Demetri, 11:18: "I want to include progress photos, as well as an export
functions."
  - Photos are locked like the journal (encrypted with its key), kept
    beside - not inside - the public media folder, and sent only to their
    owner. Grid, a photo large, compare any two.
  - Settings > Download your data: one ZIP of spreadsheets, the journal
    opened, photos if asked for.
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

SUFFIX = '.bak_wellness23'
ME = 'test_wellness_twentythree.py'
PATCHER = 'apply_wellness_twentythree.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

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
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
ph = read(J(APP, 'photos.py'))
ok("os.path.join(os.path.dirname(media), 'wellness_private')" in ph and
   'crypto.seal_bytes(data)' in ph and 'ImageOps.exif_transpose' in ph,
   'PHOTOS: beside the media folder, not in it; locked; turned upright')
vp = read(J(APP, 'views_photos.py'))
ok(vp.count('user=request.user') >= 5 and
   "resp['Cache-Control'] = 'private, max-age=86400'" in vp,
   '  every photo page and picture is looked up by its owner')
u = read(J(APP, 'urls.py'))
ok(all(n in u for n in ("name='photos'", "name='photo_new'",
                        "name='photo_compare'", "name='photo_detail'",
                        "name='photo_image'", "name='photo_delete'",
                        "name='export'")),
   '  seven addresses: the grid, add, compare, one photo, its picture, '
   'delete, the download')
ok("'wellness:photos'" in read(J(WT, 'body.html')) and
   "'wellness:export'" in read(J(WT, 'settings.html')),
   '  reached from Body, and the download from Settings')
ok('/wellness_private/' in read(J(ROOT, '.gitignore')),
   '  and a laptop never commits its photos')
ex = read(J(WT, 'export.html'))
ok('The file is not locked.' in ex and 'name="journal"' in ex and
   'name="photos"' in ex and 'data-download' in ex,
   'DOWNLOAD: says plainly the file is not locked; journal and photos '
   'are choices')
js = read(J(APP, 'assets', 'wellness.js'))
ok("form.hasAttribute('data-download')" in js and
   "form.hasAttribute('data-confirm')" in js and '[data-photo-input]' in js,
   '  a download does not leave its button pressing; delete asks first; '
   'a photo shows before Save')
css = read(J(APP, 'assets', 'wellness.css'))
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px')
base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
# Loosened by MS-1: a later round bumps the version again.
ok(vv and len(set(vv)) == 1 and vv[0] not in ('wl20-1',) and
   ("SW_VERSION = '%s'" % vv[0]) in read(J(APP, 'views.py')),
   'the app files carry a new version', vv)

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
import tempfile                                             # noqa: E402
TMP = tempfile.mkdtemp(prefix='w23_')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
_dj.WELLNESS_PRIVATE_ROOT = TMP
import io                                                   # noqa: E402
import datetime as dt                                       # noqa: E402
from wellness import crypto, photos as PH                   # noqa: E402
tok = crypto.seal_bytes(b'\xff\xd8 a picture')
ok(tok != b'\xff\xd8 a picture' and
   crypto.open_bytes(tok) == b'\xff\xd8 a picture' and
   crypto.open_bytes(b'nonsense') is None,
   'THE LOCK: bytes in, a token out, and back; nonsense opens to nothing')
ok(not os.path.normpath(PH.root()).startswith(
    os.path.normpath(str(_dj.MEDIA_ROOT))),
   'the private folder is not inside MEDIA_ROOT')
from PIL import Image                                       # noqa: E402


def jpeg(w=1200, h=1600, colour=(120, 150, 170)):
    b = io.BytesIO()
    Image.new('RGB', (w, h), colour).save(b, 'JPEG')
    b.seek(0)
    b.name = 'p.jpg'
    return b


stem, w, h = PH.store(jpeg(3000, 4000))
raw = open(os.path.join(PH.root(), stem + '-full.bin'), 'rb').read()
ok(max(w, h) == 1600 and not raw.startswith(b'\xff\xd8'),
   'A PHOTO is shrunk to 1600 px and what is on disk is not a JPEG', (w, h))
full, thumb = PH.read(stem, 'full'), PH.read(stem, 'thumb')
ok(full.startswith(b'\xff\xd8') and thumb.startswith(b'\xff\xd8') and
   max(Image.open(io.BytesIO(thumb)).size) == 480,
   '  and opens as a JPEG, with a 480 px copy for the grid')
try:
    PH.store(io.BytesIO(b'not a picture'))
    ok(False, 'a file that is not a photo is refused')
except PH.NotAPhoto as e:
    ok('JPEG, PNG, WebP or HEIC' in str(e),
       'a file that is not a photo is refused, in words')
PH.remove(stem)
ok(PH.read(stem) is None, '  and a removed photo is gone')
ok(PH.read('../../etc', 'full') is None and PH.read(stem, 'huge') is None,
   'a name with a path in it, or a size it never made, opens nothing')
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok(all(HELP.for_url_name(n) for n in ('photos', 'photo_new',
                                      'photo_compare', 'photo_detail',
                                      'export')) and
   'Download your data' in ' '.join(HELP.for_url_name('settings')['steps']),
   'HELP: every new screen has its own; Settings mentions the download')
qs = {h['q']: h for h in G.HOWTO}
ok(qs.get('Set up: progress photos', {}).get('topic') == 'body' and
   qs.get('Can I download everything I put into Wellness?', {})
   .get('topic') == 'privacy',
   '  and the general questions, under Body and Privacy')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile, ProgressPhoto
    connection.ensure_connection()
    ProgressPhoto.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

if have_db:
    import zipfile
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            a = User.objects.create_user('w23_a', 'w23a@example.com', 'x')
            b = User.objects.create_user('w23_b', 'w23b@example.com', 'x')
            for x in (a, b):
                x.user_permissions.add(perm)
                WellnessProfile.objects.create(user=x, onboarded=True)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            day = timezone.localdate()

            def up(d, pose='front'):
                f = jpeg()
                return ca.post('/wellness/body/photos/new/', {
                    'photo': SimpleUploadedFile('p.jpg', f.read(),
                                                'image/jpeg'),
                    'pose': pose, 'date': d.isoformat(), 'note': 'n'})
            r = up(day - dt.timedelta(days=60))
            r2 = up(day)
            mine = list(ProgressPhoto.objects.filter(user=a)
                        .order_by('date'))
            ok(r.status_code == 302 and r2.status_code == 302 and
               len(mine) == 2,
               'ADD: two photos saved, sixty days apart')
            t = ca.get('/wellness/body/photos/').content.decode()
            ok(t.count('class="w-photo"') == 2 and 'Compare two photos' in t,
               '  the grid shows both, and offers to compare')
            img = ca.get('/wellness/body/photos/%d/thumb.jpg' % mine[0].pk)
            ok(img.status_code == 200 and img['Content-Type'] ==
               'image/jpeg' and img.content.startswith(b'\xff\xd8'),
               '  each picture comes to its owner as a JPEG')
            ok(cb.get('/wellness/body/photos/%d/full.jpg' % mine[0].pk)
               .status_code == 404 and
               cb.get('/wellness/body/photos/%d/' % mine[0].pk)
               .status_code == 404,
               '  and to nobody else - not the picture, not its page')
            r = ca.post('/wellness/body/photos/new/', {
                'photo': SimpleUploadedFile('x.txt', b'hello', 'text/plain'),
                'pose': 'front', 'date': day.isoformat()})
            ok(r.status_code == 200 and 'not a photo Wellness can read' in
               r.content.decode(), '  a file that is not a photo says so')
            t = ca.get('/wellness/body/photos/compare/').content.decode()
            ok('60 days apart' in t and t.count('<figure>') == 2,
               'COMPARE: the first and the latest, side by side, "60 days '
               'apart"')
            ca.post('/wellness/journal/new/', {
                'kind': 'note', 'mood': '4', 'text': 'Walked by the sea',
                'note': 'Walked by the sea', 'date': day.isoformat()})
            r = ca.post('/wellness/settings/export/', {'journal': '1',
                                                       'photos': '1'})
            z = zipfile.ZipFile(io.BytesIO(r.content))
            names = z.namelist()
            ok(r['Content-Type'] == 'application/zip' and
               'wellness/habits.csv' in names and
               'wellness/workout_sets.csv' in names and
               'wellness/README.txt' in names and
               sum(1 for n in names if n.startswith('wellness/photos/')) == 2,
               'DOWNLOAD: one ZIP - spreadsheets, a README and the photos',
               names)
            jt = z.read('wellness/journal.csv').decode('utf-8-sig')
            ok('Walked by the sea' in jt and 'Good' in jt,
               '  the journal opened, with its mood')
            r = ca.post('/wellness/settings/export/', {})
            names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
            ok('wellness/journal.csv' not in names and
               not any(n.startswith('wellness/photos/') for n in names),
               '  untick both and neither is in it')
            stem = mine[0].stem
            r = ca.post('/wellness/body/photos/%d/delete/' % mine[0].pk)
            ok(r.status_code == 302 and
               not ProgressPhoto.objects.filter(pk=mine[0].pk).exists() and
               PH.read(stem) is None,
               'DELETE: the row and both files go')
            ok(cb.post('/wellness/body/photos/%d/delete/' % mine[1].pk)
               .status_code == 404, '  and nobody else can delete yours')
            for p in ProgressPhoto.objects.filter(user=a):
                PH.remove(p.stem)
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL')
# ==========================================================================
try:
    ok('ProgressPhoto' not in was(J(APP, 'models.py')) and
       "name='export'" not in was(J(APP, 'urls.py')),
       'before this round: no photos and no download')
except IOError as _e:
    skip('section 4', str(_e))

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def seal_bytes('" in gate, '  with a sentinel on the photo lock')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

import shutil                                               # noqa: E402
shutil.rmtree(TMP, ignore_errors=True)
print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
