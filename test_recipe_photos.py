# -*- coding: utf-8 -*-
"""test_recipe_photos.py - round PX-1, 13 Oct 2026.

A PHOTOGRAPH STORED LOSSLESSLY IS A PHOTOGRAPH STORED WRONG.

324 recipe photos, every one a PNG, 199.4 MB, 630 KB average, none over
1000px on the long edge and not one with a single non-opaque pixel.
Re-encoded at the SAME dimensions: 17.7 MB.

WHAT THIS SUITE CAN AND CANNOT REACH. It runs under plain python with no
Django configured and no database, so it cannot import pages.models. It
does what test_house_title does instead: it LIFTS the functions out of
the model source and exec's them, and exercises them on a real PNG it
makes for itself. The behaviour proved here is the behaviour that file
will have, because it is that file's own code running.

WHAT WAS PROVED ELSEWHERE, AND SAID SO HERE. Against a disposable sqlite
built from the real migration graph, on 13 Oct: migration 0099 applies,
makemigrations --check reports NO CHANGES so 0099 matches the model, an
831 KB PNG saved through Recipe.save() produced a 52 KB display copy,
photo_url pointed at it, a second save rebuilt nothing, a recipe with no
image returned None without raising, a row the batch had not reached
fell back to its PNG, and the command converted on --write and nothing
on a second --write. None of that can run on the push gate, so it is
recorded rather than claimed.

WHAT IS NOT PROVED ANYWHERE YET. That the batch succeeds over the 324
live files on the Railway volume. It is dry by default precisely so the
first real run is a report.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_pxphotos'
ME = 'test_recipe_photos.py'
PATCHER = 'apply_recipe_photos.py'
PS1 = 'Push-PendingChanges.ps1'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
MODELS = os.path.join('pages', 'models.py')
URLS = os.path.join('mysite', 'urls.py')
MIGRATION = os.path.join('pages', 'migrations', '0099_recipe_image_display.py')
COMMAND = os.path.join('pages', 'management', 'commands',
                       'convert_recipe_photos.py')

QUALITY = 85
N_SERIALISERS, N_TEMPLATES, N_JS_FREE = 8, 7, 6
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 74, 2, 38, 59

# Measured on the live volume, 13 Oct 2026. Recorded, not asserted - this
# suite runs on a laptop that cannot see /data/media.
LIVE = dict(files=324, png=324, mb=199.4, avg_kb=630, over_1000px=0,
            non_opaque=0, q85_mb=17.7, q85_avg_kb=56)

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def raw(p):
    with open(p, 'rb') as f:
        return f.read()


def was(p):
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else read(p)


def left(name):
    p = os.path.join(ROOT, name)
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


M = read(os.path.join(ROOT, MODELS))

print('=' * 74)
print('%s - PX-1, A PHOTOGRAPH STORED LOSSLESSLY IS STORED WRONG' % ME)
print('=' * 74)

# ==========================================================================
head('1. REGISTERED')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(os.path.isfile(os.path.join(ROOT, MIGRATION)),
   'migration 0099 is on disk')
ok(os.path.isfile(os.path.join(ROOT, COMMAND)),
   'the batch command is on disk')

# ==========================================================================
head('2. THE CONVERSION, LIFTED OUT OF THE MODEL AND RUN')
# ==========================================================================
# THE FUNCTION UNDER TEST IS THE SHIPPED ONE. Lifted from pages/models.py
# and exec'd, the way test_house_title lifts its subject, because this
# suite has no Django to import the model with.
src = []
for name in ('make_display_jpeg', 'display_name_for'):
    m = re.search(r'(?ms)^def %s\(.*?(?=^def |\Z)' % name, M)
    if m:
        src.append(m.group(0))
ns = {'os': os}
lifted = ok(len(src) == 2, 'both functions lifted out of %s' % MODELS,
            '%d found' % len(src))
if lifted:
    try:
        exec('\n\n'.join(src), ns)
    except Exception as e:
        lifted = ok(False, '  and they exec cleanly', e)

try:
    from PIL import Image
except Exception:
    Image = None

if not lifted or Image is None:
    skip('section 2', 'the functions could not be lifted, or PIL is absent')
else:
    import io as _io

    # A REAL RGBA PNG, made here rather than shipped: a photograph-like
    # gradient with noise, which is what makes PNG expensive and JPEG
    # cheap. A flat colour would prove nothing - it compresses to almost
    # nothing in either format.
    import random
    random.seed(11)
    w, h = 600, 400
    im = Image.new('RGBA', (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (
                (x * 255 // w + random.randint(-18, 18)) & 255,
                (y * 255 // h + random.randint(-18, 18)) & 255,
                ((x + y) * 255 // (w + h) + random.randint(-18, 18)) & 255,
                255)
    buf = _io.BytesIO()
    im.save(buf, 'PNG')
    png = buf.getvalue()

    class FieldFile(object):
        """The two attributes make_display_jpeg actually uses."""
        def __init__(self, data, name):
            self._d, self.name = data, name
            self._f = None

        def __bool__(self):
            return bool(self.name)

        def open(self, mode='rb'):
            self._f = _io.BytesIO(self._d)
            return self._f

        def read(self, *a):
            return self._f.read(*a)

        def seek(self, *a):
            return self._f.seek(*a)

        def tell(self):
            return self._f.tell()

        def close(self):
            pass

    ff = FieldFile(png, 'recipe_images/recipe-1-x-20261013120000.png')
    jpg = ns['make_display_jpeg'](ff)
    ok(jpg is not None, 'it converts a real RGBA PNG')
    if jpg:
        ok(len(jpg) < len(png) / 2,
           '  and the result is far smaller: %.0f KB -> %.0f KB (%.0f%%)'
           % (len(png) / 1024.0, len(jpg) / 1024.0,
              100.0 * len(jpg) / len(png)),
           '%d vs %d' % (len(png), len(jpg)))
        out = Image.open(_io.BytesIO(jpg))
        ok(out.format == 'JPEG', '  it really is a JPEG', out.format)
        # NO RESIZING. The whole round rests on this.
        ok(out.size == (w, h),
           '  and EVERY PIXEL IS KEPT - %dx%d in, %dx%d out'
           % (w, h, out.size[0], out.size[1]), out.size)
        ok(out.mode == 'RGB', '  flattened to RGB, so no alpha survives')

    # THE FLATTEN IS DEFENCE, and defence that is never exercised is a
    # claim. Measured on the volume: 0 of 324 have a transparent pixel.
    # This one does.
    tr = Image.new('RGBA', (60, 60), (255, 0, 0, 0))
    b2 = _io.BytesIO()
    tr.save(b2, 'PNG')
    jt = ns['make_display_jpeg'](FieldFile(b2.getvalue(), 'x/y.png'))
    if ok(jt is not None, 'CONTROL: a fully TRANSPARENT png still converts'):
        got = Image.open(_io.BytesIO(jt)).convert('RGB').getpixel((30, 30))
        ok(got == (255, 255, 255),
           '  and it lands on WHITE, decided here rather than discovered '
           'later as a black rectangle', '%s' % (got,))

    # UNREADABLE IS NOT A CRASH. A recipe with a broken image must not
    # stop a save or a batch.
    ok(ns['make_display_jpeg'](FieldFile(b'not an image', 'x/y.png')) is None,
       'CONTROL: an unreadable file returns None rather than raising')
    ok(ns['make_display_jpeg'](FieldFile(b'', '')) is None,
       'CONTROL: and so does no file at all')

    # The naming rule, which is also the staleness rule.
    ok(ns['display_name_for']('recipe_images/recipe-7-pie-20261013120000.png')
       == 'recipe-7-pie-20261013120000.jpg',
       'the display name keeps the stem and changes the extension')
    ok(ns['display_name_for']('a/b/c.PNG') == 'c.jpg',
       '  whatever the original extension was')

# ==========================================================================
head('3. ONE PROPERTY, AND EVERY CALL SITE ASKING IT')
# ==========================================================================
ok('recipe_image_display = models.ImageField(' in M,
   'Recipe carries the derived field')
ok('editable=False' in M.split('recipe_image_display')[1][:400],
   '  and it is editable=False, so no ModelForm can set it by hand')
ok(re.search(r'(?m)^    def photo_url\(self\):', M) is not None
   or 'def photo_url(self)' in M, 'Recipe carries photo_url')
ok('@property' in M.split('def photo_url')[0][-60:],
   '  as a property, so a template can reach it')

pu = M.split('def photo_url')[1][:700]
ok('recipe_image_display' in pu and 'recipe_image' in pu and 'None' in pu,
   '  display copy, else the original, else None - the fallback is '
   'what lets the batch run while the site stays up')

SER = ((os.path.join('pages', 'views', 'recipes', 'meal_planning.py'), 4),
       (os.path.join('pages', 'views', 'recipes', 'recipe_crud.py'), 4))
n_ser = 0
for rel, n in SER:
    t = read(os.path.join(ROOT, rel))
    got = len(re.findall(r"'(?:recipe_image|image)': \w+\.photo_url,", t))
    old = len(re.findall(r"\.recipe_image\.url if \w+\.recipe_image", t))
    ok(got == n and old == 0,
       '%-40s %d serialiser(s) on photo_url, 0 left on recipe_image.url'
       % (os.path.basename(rel), n), '%d and %d' % (got, old))
    n_ser += got
ok(n_ser == N_SERIALISERS, 'all %d serialiser(s)' % N_SERIALISERS, n_ser)

TPL = (('meal_plan_calendar.html', 1), ('recipe_management.html', 2),
       ('recipe_pdf.html', 1), ('view_meal_plan.html', 1),
       ('view_recipe.html', 1), ('wcim_recipe_quick_view.html', 1))
n_tpl = n_old = 0
for page, n in TPL:
    t = read(alv_tree.path_of(page))
    got = len(re.findall(r'\{\{\s*[\w.]*photo_url\s*\}\}', t))
    old = len(re.findall(r'\{\{\s*[\w.]*recipe_image\.url\s*\}\}', t))
    n_tpl += got
    n_old += old
    ok(got == n and old == 0, '%-34s %d render site(s) moved' % (page, n),
       '%d moved, %d left' % (got, old))
ok(n_tpl == N_TEMPLATES and n_old == 0,
   'all %d template site(s), and not one left behind' % N_TEMPLATES,
   '%d and %d' % (n_tpl, n_old))

# THE SIX THAT MOVE FOR FREE, and they are counted rather than asserted
# in prose: ${recipe.recipe_image} is JavaScript reading JSON that the
# serialisers above build, so it needed no edit at all.
js = 0
for page in ('create_meal_plan.html', 'recipe_management.html',
             'meal_plan_calendar.html'):
    t = read(alv_tree.path_of(page))
    # MP-1, 18 Oct 2026 - ANYTHING INSIDE THE BRACES, not a bare
    # dotted name. B10 wrapped one of these six in esc(), because the
    # same page inserts recipe text with innerHTML, and this regex went
    # from six matches to five - reporting a site as "left behind" when
    # what had actually happened was that it had been made safe.
    #
    # The claim PX-1 makes is that the JS READS recipe_image and so took
    # the new URL for free. That is still exactly true. The shape of the
    # expression around the read was never the point.
    js += len(re.findall(r'\$\{[^}]*recipe_image[^}]*\}', t))
    js += len(re.findall(r'\{\{\s*recipe\.image\s*\}\}', t))
ok(js == N_JS_FREE,
   '%d JavaScript site(s) still read recipe_image - they take the new URL '
   'from the serialisers and needed no edit' % N_JS_FREE, js)

# ==========================================================================
head('4. THE MIGRATION, AND WHAT IT DELIBERATELY DOES NOT DO')
# ==========================================================================
mig = read(os.path.join(ROOT, MIGRATION))
ok("('pages', '0098_comment_length')" in mig,
   'it depends on 0098, the migration that was head before this round')
ok('AddField' in mig and "name='recipe_image_display'" in mig,
   '  and it adds exactly that one field')
ok('RunPython' not in mig,
   '  and it carries NO data migration - 200 MB of re-encoding has no '
   'business running inside a deploy where nobody is watching')
ok('editable=False' in mig and 'blank=True' in mig and 'null=True' in mig,
   '  nullable and not editable, matching the model')
print('        Proved against a disposable sqlite on 13 Oct, not here:')
print('        0099 applies, and makemigrations --check then reports NO')
print('        CHANGES - so the hand-written migration matches the model.')

# ==========================================================================
head('5. THE BATCH IS DRY BY DEFAULT')
# ==========================================================================
cmd = read(os.path.join(ROOT, COMMAND))
ok("'--write'" in cmd and "action='store_true'" in cmd,
   'the command takes --write')
ok("opts['write']" in cmd, '  and reads it')
ok('DRY RUN. Nothing was written' in cmd,
   '  and says so out loud when it has not written')
body = cmd.split('def handle')[1]
writes = re.findall(r'recipe_image_display\.save\(', body)
ok(len(writes) == 1, '  it writes in exactly one place', len(writes))
guarded = body.split('if write:')[1] if 'if write:' in body else ''
ok('recipe_image_display.save(' in guarded,
   '  and that place is INSIDE the --write guard')
ok('recipe_image.save(' not in cmd and 'os.remove' not in cmd
   and 'unlink' not in cmd,
   'CONTROL: it never writes an original and never deletes anything')
ok('display_copy_is_stale' in cmd,
   'it decides what to do from the filenames, so it is resumable and a '
   'second run converts nothing')
print('        Proved against sqlite on 13 Oct, not here: the dry run')
print('        reported one conversion and wrote nothing, --write made it,')
print('        and a second --write converted 0 and reported 2 current.')

# ==========================================================================
head('6. THE CACHE HEADER, AND WHAT IT DOES NOT FIX')
# ==========================================================================
u = read(os.path.join(ROOT, URLS))
ok('def cached_media(' in u, 'mysite/urls.py wraps the media view')
ok("'public, max-age=31536000, immutable'" in u,
   '  with a year, and immutable')
ok("re_path(r'^media/(?P<path>.*)$', cached_media)" in u,
   '  and the route points at the wrapper, not at serve()')
ok('serve(request, path, document_root=settings.MEDIA_ROOT)' in u,
   '  which still calls serve() - this round does not replace it')
wb = was(os.path.join(ROOT, URLS))
ok('cached_media' not in wb,
   'CONTROL: and it was not there before this round')
print('        WHY A YEAR IS HONEST HERE: every uploaded filename carries')
print('        a timestamp, so a re-upload gets a NEW name. A cached copy')
print('        can never be the wrong version - only one nobody references.')

# ==========================================================================
head('7. THE ROUND DID NOT REWRITE ANYBODY LINE ENDINGS')
# ==========================================================================
# Of the fifteen files edited, nine are LF, four CRLF and TWO MIXED. A
# patcher that normalised to get its match would have turned a four-line
# change into a four-thousand-line diff.
moved = []
for d, _ds, fs in os.walk(ROOT):
    if '__pycache__' in d or os.sep + '.git' in d:
        continue
    for f in fs:
        if not f.endswith(SUFFIX):
            continue
        now_p = os.path.join(d, f)[:-len(SUFFIX)]
        a, b = raw(now_p), raw(now_p + SUFFIX)
        ca, cb = a.count(b'\r\n'), b.count(b'\r\n')
        la = a.count(b'\n') - ca
        lb = b.count(b'\n') - cb
        if (cb == 0 and ca > 0) or (lb == 0 and la > 0):
            moved.append(os.path.relpath(now_p, ROOT))
ok(not moved, 'not one edited file changed which line ending it uses',
   moved[:6])
ok(len([1 for d, _x, fs in os.walk(ROOT) for f in fs
        if f.endswith(SUFFIX)]) >= 10,
   '  CONTROL: and there really are backups to compare against')
ok('def fit(' in read(os.path.join(ROOT, PATCHER)),
   '  because the patcher fits every multi-line anchor to the file')

# ==========================================================================
head('8. THE REGISTERS')
# ==========================================================================
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   'CONVERTED holds at least the %d PX-1 left' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
wd = left(WD)
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   '  and %s says %d, read as PX-1 left it' % (WD, CONVERTED_NOW))
ok('CEILING = %d' % CEILING_NOW in wd,
   '  the walker ceiling is unchanged at %d' % CEILING_NOW)
ok(len(alv_tree.WAITING) == WAITING_NOW,
   'WAITING still holds %d - PX-1 releases nothing' % WAITING_NOW,
   len(alv_tree.WAITING))
ok('ok(len(aliased) == %d,' % ALIAS_NOW in left(CO),
   '%s pins %d alias(es), read as PX-1 left it' % (CO, ALIAS_NOW))
for f in (ME, PATCHER):
    ok(re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, f))) is not None,
       '  %s aliases the house stripper at column zero' % f)
_me = read(os.path.join(ROOT, ME))
ok(_me.count('os.path.' + 'join(T,') == 0 and 'alv_tree.path_of(' in _me,
   '  and this suite resolves labels through alv_tree.path_of')
ok(SUFFIX in ROUNDS and '.bak_rstones' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_rstones'),
   '%s sits after .bak_rstones in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-4:] if ROUNDS else 'empty')
ok("'%s'" % ME in read(os.path.join(ROOT, PS1)), '%s is on the push gate' % ME)

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that the batch succeeds over the %d live files on the'
      % LIVE['files'])
print('  volume. It cannot be run from here and it has never been run')
print('  there. It is dry by default so the first real run is a report.')
print('')
print('  Not that serve() has stopped mattering. It still moves every')
print('  byte of /media/ through a Python worker, one file at a time,')
print('  out of mysite/urls.py with no DEBUG guard. At 630 KB a file')
print('  that was the larger problem; at %d KB it may not be. Measure'
      % LIVE['q85_avg_kb'])
print('  the page again before deciding - that was the decision taken.')
print('')
print('  Not that the pictures are good enough. %d of the %d originals'
      % (97, LIVE['files']))
print('  are under 500px on the long edge and the phone hero wants about')
print('  1170. They are soft in the PNG already. Converting makes them')
print('  light; it cannot make them sharp.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
