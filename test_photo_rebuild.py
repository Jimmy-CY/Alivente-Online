# -*- coding: utf-8 -*-
"""test_photo_rebuild.py - round SD-1, 22 Oct 2026.

--rebuild --write DID NOT REBUILD. IT ACCUMULATED.

Found on 22 October while driving DP-1's suite, in a temporary media
volume, with two photos. Section 3 is that session, written down:

    after rebuild: recipe-1-alpha-20261022063218_xUkNf5M.jpg  stale True
    after 2nd    : recipe-1-alpha-20261022063218_wEIntUA.jpg  stale True
    on the volume: ...png  ...jpg  ..._wEIntUA.jpg  ..._xUkNf5M.jpg

DJANGO'S STORAGE DOES NOT OVERWRITE. FieldFile.save() asks the storage
for an AVAILABLE name and FileSystemStorage answers one that is not
taken - the name you asked for with a random seven-character suffix.

THREE CONSEQUENCES, ALL ON THE LIVE VOLUME'S PATH, and section 3 counts
each of them rather than describing it:

  - the old display copy is never deleted, so a rebuild of 324 photos
    leaves 324 orphans;
  - display_copy_is_stale compares the stored name with
    display_name_for(original) - by design, so there is no column to
    forget to clear - and the suffixed name never equals it, so every
    recipe becomes PERMANENTLY stale;
  - permanently stale means Recipe.save() rebuilds the copy on EVERY
    edit, because PX-1 put that rebuild in save(). Another orphan each
    time, for as long as the recipe is used.

ONE PLACE THAT STORES ONE. make_display_jpeg has been 'the ONE place
that knows how a display copy is MADE' since PX-1; store_display_jpeg
is now the one place that knows how it is STORED. It deletes the target
path and then writes there, and then CHECKS THE NAME IT GOT - which is
the thing nobody did before, and the reason this round exists.

IT MAY TOUCH ONE PATH. Section 1 refuses any sign of a listing, a glob,
a walk or an rmtree inside it, and insists the single delete names the
target it is about to write. A delete on a media volume that takes
anything wider than that is a delete nobody can bound.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One place, one delete, one path, a name check, and
      both callers through it - the command AND Recipe.save().

  2   THE CONTROL. Re-asked of .bak_photorebuild, where both callers
      wrote the field directly and nothing looked at the result.

  3   DRIVEN, ON A REAL VOLUME. Two rebuilds, the files counted; the
      row's staleness after each; an edit after a rebuild; and the
      report when a store really does fail.

  4   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import glob
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_photorebuild'
ME = 'test_photo_rebuild.py'
PATCHER = 'apply_photo_rebuild.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'SD-1, 22 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
CMD = os.path.join(ROOT, 'pages', 'management', 'commands',
                   'convert_recipe_photos.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, CMD)

# A DELETE ON A MEDIA VOLUME MAY REACH ONE PATH.
TOO_WIDE = ('listdir', 'glob', 'walk', 'rmtree', 'os.remove', 'os.unlink',
            'shutil', 'iglob', 'scandir')

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


# SLICED TO THE NEXT TOP-LEVEL def. python_code_only blanks docstrings,
# so a slice taken to a run of blank lines runs on into the next
# function - which is how DP-1's own gate refused a round for a leak in
# somebody else's code. .find(), not .index(): against the reverted
# tree there is no such function and .index() would RAISE.
def one_place(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('def store_display_jpeg')
    if a < 0:
        return ''
    body = code[a:]
    nxt = re.search(r'\ndef \w+', body[1:])
    return body[:nxt.start() + 1] if nxt else body


def claims(d):
    m = d[MODELS]
    s = one_place(m)
    mc = T.python_code_only(m, payloads=True)
    c = T.python_code_only(d[CMD], payloads=True)
    return {
        'there is ONE place that stores a display copy':
            bool(s),
        '  and it clears the target path before writing it':
            'storage.exists(' in s and 'storage.delete(target)' in s,
        '  and CHECKS THE NAME IT GOT, which is the whole bug':
            'os.path.basename(field.name) == want' in s,
        '  answering False rather than raising':
            'return False' in s,
        'the command goes through it':
            'store_display_jpeg(recipe, data)' in c,
        '  and no longer writes the field itself':
            'recipe_image_display.save(' not in c,
        'Recipe.save() goes through it too':
            mc.count('store_display_jpeg(') >= 2,
        '  and no direct field write is left outside the one place':
            'recipe_image_display.save(' not in mc,
        'and a store that did not land is REPORTED, not counted':
            'which is not the name a rebuild' in d[CMD],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

S = one_place(NOW[MODELS])

# IT MAY TOUCH ONE PATH. Not a pattern, not a listing, not a tree.
ok(S.count('storage.delete(') == 1,
   'it deletes exactly once - one write, one path, one delete',
   S.count('storage.delete('))
for reach in TOO_WIDE:
    ok(reach not in S,
       'the one place does not name %s' % reach)
ok('recipe_display_upload_path(' in S,
   'and the path it clears is the one the FIELD would choose, asked of '
   'the same function the field uses - not spelled out here twice')

# NEVER RAISES. A picture is worth less than the recipe it belongs to,
# which is PX-1's rule and did not stop being true.
ok('except Exception:' in S,
   'it cannot raise - a failed picture must not lose the recipe '
   'somebody just saved')

# AND THE COMMAND REPORTS WHAT DID NOT LAND. DP-1 built the report;
# this round gives it a second thing to say.
ok('problems.append(' in NOW[CMD],
   'the command puts a store that did not land on the SAME list as an '
   'unreadable photo - named, not swallowed')
ok(NOW[CMD].count('problems.append(') == 2,
   '  and there are two ways to end up on that list: unreadable in, '
   'wrong name out', NOW[CMD].count('problems.append('))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

oldm = T.python_code_only(BEFORE[MODELS], payloads=True)
oldc = T.python_code_only(BEFORE[CMD], payloads=True)
ok('recipe_image_display.save(' in oldm and
   'recipe_image_display.save(' in oldc,
   'CONTROL: BOTH callers wrote the field directly - the command and '
   'Recipe.save()')
ok('storage.delete' not in oldm,
   'CONTROL: and nothing cleared the target, so the storage handed '
   'back a name nobody looked at')
ok('display_copy_is_stale' in oldm,
   'CONTROL: staleness was already decided by comparing names, which '
   'is what turned a suffix into a permanent condition')
ok('def make_display_jpeg' in oldm,
   'CONTROL: there was already ONE place that knew how to MAKE one - '
   'this round gives it a companion that knows how to STORE one')


# ==========================================================================
head('3. DRIVEN - TWO REBUILDS ON A REAL VOLUME')
# ==========================================================================
django_up = False
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
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

try:
    from PIL import Image
except Exception:
    Image = None

if not django_up or Image is None:
    skip('section 3', 'no database, or Pillow is not installed')
else:
    import shutil
    import tempfile
    from django.core.files.base import ContentFile
    import pages.models as PM

    MEDIA = tempfile.mkdtemp(prefix='sd1-media-')
    old_media = dj.MEDIA_ROOT
    dj.MEDIA_ROOT = MEDIA

    def on_volume():
        return sorted(os.path.basename(p) for p in
                      glob.glob(os.path.join(MEDIA, '**', '*'),
                                recursive=True) if os.path.isfile(p))

    def put(name, px):
        img = Image.new('RGB', (px, px), (180, 140, 90))
        for x in range(0, px, 9):
            for y in range(0, px, 7):
                img.putpixel((x, y), ((x * 7) % 255, (y * 3) % 255, 40))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        r = PM.Recipe.objects.create(recipe_name=name, servings=4)
        r.recipe_image.save('%s-20261022.png' % name.lower(),
                            ContentFile(buf.getvalue()), save=True)
        return r

    def run(*args):
        out = io.StringIO()
        call_command('convert_recipe_photos', *args, stdout=out)
        return out.getvalue()

    try:
        a = put('alpha', 700)
        a.refresh_from_db()
        want = PM.display_name_for(a.recipe_image.name)
        ok(on_volume() == sorted([os.path.basename(a.recipe_image.name),
                                  want]),
           'ONE PHOTO ON THE VOLUME is one original and one display '
           'copy - PX-1 builds it in save()', on_volume())
        ok(not a.display_copy_is_stale(),
           '  and the row is not stale')

        run('--rebuild', '--write')
        a.refresh_from_db()
        first = on_volume()
        ok(len(first) == 2,
           'AFTER ONE REBUILD there are still two files - %d: %r'
           % (len(first), first), first)
        ok(os.path.basename(a.recipe_image_display.name) == want,
           '  and the display copy still has the name a rebuild can '
           'recognise - %r' % os.path.basename(a.recipe_image_display.name))
        ok(not a.display_copy_is_stale(),
           '  SO THE ROW IS NOT STALE. Before this round it was, for '
           'ever, because the stored name carried a random suffix')

        run('--rebuild', '--write')
        a.refresh_from_db()
        second = on_volume()
        ok(second == first,
           'AFTER A SECOND REBUILD the volume is byte-for-byte the same '
           'LIST of files - %r' % second, (first, second))
        ok(not a.display_copy_is_stale(),
           '  and the row is still not stale. Run it ten times and the '
           'answer does not change')

        # ---- THE THIRD CONSEQUENCE: an edit after a rebuild. PX-1 put
        #      the rebuild in save(), so a permanently stale row left
        #      another orphan every time the recipe was touched.
        print('')
        a.recipe_name = 'alpha renamed'
        a.save()
        a.refresh_from_db()
        ok(on_volume() == first,
           'EDITING THE RECIPE after a rebuild adds no file at all - '
           '%r' % on_volume(), (first, on_volume()))
        ok(os.path.basename(a.recipe_image_display.name) == want,
           '  and leaves the display copy where it was')
        a.save()
        a.save()
        ok(on_volume() == first,
           '  nor does editing it twice more - this is where the real '
           'volume would have grown without anybody running a command')

        # ---- A PLAIN RUN AFTER A REBUILD HAS NOTHING TO DO, which is
        #      the one-line proof that staleness is cured.
        plain = run('--write')
        ok('Nothing needed writing' in plain,
           'AND A PLAIN --write AFTER A REBUILD converts nothing - '
           'before this round it converted every photo, for ever',
           plain[-300:])

        # ---- AND A STORE THAT REALLY FAILS IS REPORTED. The storage is
        #      made to hand back a different name, which is exactly what
        #      it used to do on its own.
        print('')
        PM.Recipe.objects.all().delete()
        b = put('beta', 700)
        # getattr, NOT an attribute. Against the reverted tree there is
        # no store_display_jpeg and the dotted form RAISES - a crash
        # blocks a push exactly as hard as a failure and says far less
        # about why. Seventh time this month.
        real_store = getattr(PM, 'store_display_jpeg', None)

        if real_store is None:
            skip('the failed store',
                 'there is no one place here to make fail')
        else:
            def never_lands(recipe, data):
                real_store(recipe, data)
                # The name it ends up with is not the name it asked
                # for, which is the whole shape of the bug.
                recipe.recipe_image_display.name = (
                    'recipe_images_display/not-the-name_xUkNf5M.jpg')
                return False

            import pages.management.commands.convert_recipe_photos as C
            had = getattr(C, 'store_display_jpeg', None)
            C.store_display_jpeg = never_lands
            try:
                said = run('--rebuild', '--write')
            finally:
                if had is None:
                    delattr(C, 'store_display_jpeg')
                else:
                    C.store_display_jpeg = had

            ok('COULD NOT BE READ - named, not swallowed:' in said
               or 'DID NOT LAND AS CLAIMED' in said,
               'A STORE THAT DID NOT LAND IS NAMED - it goes on the '
               'same list as a photo that could not be read',
               said[-600:])
            ok('not the name a rebuild can recognise' in said,
               '  saying WHY, in the words of the thing that went wrong',
               said[-600:])
            ok('beta' in said, '  and naming the recipe', said[-600:])

    finally:
        dj.MEDIA_ROOT = old_media
        shutil.rmtree(MEDIA, ignore_errors=True)


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# NO MIGRATION. recipe_image_display already holds a name and already
# meant this; what changed is what gets written into it.
ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'migrations') + SUFFIX),
   'NO MIGRATION - recipe_image_display already held a name and '
   'already meant this')
ok(not glob.glob(os.path.join(ROOT, 'pages', 'migrations',
                              '*' + SUFFIX)),
   'and no migration file was touched')

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
ok('def store_display_jpeg' in gate, 'the sentinel is on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_photo_rebuild as PATCH                         # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the Live volume is clean. It is not. Every rebuild')
print('  run before this round left an orphan per photo, and this')
print('  round deletes only the file it is about to replace - by')
print('  exact path, deliberately. Collecting the orphans already')
print('  there is a separate job with a separate decision behind it.')
print('')
print('  Not that nothing else in the application writes a file over')
print('  itself. Every FieldFile.save() in this tree has the same')
print('  behaviour available to it; this round fixed the one that')
print('  was measured doing it. The rest is a sweep nobody has run.')
print('')
print('  Not that the orphans cost anything but space. They are')
print('  unreferenced JPEGs. Nothing serves them and nothing links')
print('  to them.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
