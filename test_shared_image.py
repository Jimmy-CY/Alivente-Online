# -*- coding: utf-8 -*-
"""test_shared_image.py - round SI-1, 22 Oct 2026.

A COPIED RECIPE SHARED ITS PHOTO, AND CHANGING ONE DESTROYED THE OTHER.

Found on Live on 22 October by a rebuild of 335 photos, which named two
it could not read:

    71     Cottage Pie                 recipe_images/recipe-cottage-pie-20260213.png
    336    Beans, Edamame - Frozen     recipe_images/recipe-336-beans-edamame-frozen-20261018152727.png

Neither file was on the volume. Demetri named the cause immediately:
"These were recipes that I copied from other recipes and I then removed
the original image and uploaded a new image."

The volume agreed. The only cottage file left on disk belonged to 329,
Cottage Pie - Keto - the COPY. 71 is the source, and 71 is the one that
lost its picture.

THE MECHANISM IS FOUR LINES. duplicate_recipe sets pk to None and
saves, which copies every field VALUE, and an image field's value is a
path string. The copy does not get a picture; it gets the original's
address. Then the edit screen's recipe_image.delete(save=False) removes
the bytes with no question asked about who else points at them.

SECTION 3 IS THAT, DRIVEN. A recipe, a real PNG on a real volume, the
duplicate view called through the test client as a signed-in user, and
then the question nobody asked: are these two paths the same? Section 4
removes the photo from the copy and asks whether the original still has
one. Against the backup those sections FAIL, which is what makes them
worth running.

SECTION 5 DRIVES THE DETECTOR, because an instrument nobody has seen
fail is not an instrument. It plants a file deletion behind a row's
back and requires check_recipe_files to name it and exit non-zero.

WHAT THE SHARE COUNT ON LIVE MEANT. Asked on 22 October: 337 rows with
an image, 0 shared paths. That is not evidence the fault is rare. A
share EXISTS ONLY between the duplicate and the next photo change, and
both known casualties went through that window and out the other side.
Zero means nobody is standing on the trapdoor at this moment.
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

SUFFIX = '.bak_sharedimage'
ME = 'test_shared_image.py'
PATCHER = 'apply_shared_image.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'SI-1, 22 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
CRUD = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py')
CHECKER = os.path.join(ROOT, 'pages', 'management', 'commands',
                       'check_recipe_files.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, CRUD)

# A DELETE ON A MEDIA VOLUME MAY REACH ONE PATH - SD-1's list, and the
# reason is unchanged: a delete that takes a pattern is a delete nobody
# can bound.
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


# SLICED TO THE NEXT TOP-LEVEL def, for the same reason SD-1 slices:
# python_code_only blanks docstrings, so a slice taken to a run of
# blank lines runs on into the next function. .find(), not .index():
# against the reverted tree there is no such function and .index()
# would RAISE rather than fail a claim.
def body_of(src, name):
    code = T.python_code_only(src, payloads=True)
    a = code.find('def %s' % name)
    if a < 0:
        return ''
    body = code[a:]
    nxt = re.search(r'\ndef \w+', body[1:])
    return body[:nxt.start() + 1] if nxt else body


def claims(d):
    m = d[MODELS]
    mc = T.python_code_only(m, payloads=True)
    c = T.python_code_only(d[CRUD], payloads=True)
    go = body_of(m, 'let_go_of_file')
    drop = body_of(m, 'delete_unheld')
    unshare = body_of(m, 'unshare_file')
    raw = d[CRUD]
    i_save = raw.find('\n            recipe.save()')
    i_del = raw.find('delete_unheld(Recipe')
    return {
        'there is one place that counts who holds a file':
            'def file_holders' in mc,
        'there is one place that lets a file go':
            bool(go),
        '  and it touches no storage at all':
            bool(go) and '.delete(' not in go and 'storage' not in go,
        'there is one place that deletes the bytes':
            bool(drop),
        '  and it COUNTS before it deletes, not after':
            ('file_holders(' in drop
             and '.delete(' in drop
             and drop.index('file_holders(') < drop.index('.delete(')),
        '  and asks the storage whether anything is there':
            'default_storage.exists(' in drop,
        # bool(drop) FIRST. Without it an ABSENT delete_unheld gives an
        # empty body, and 'no wide reach in an empty string' is true -
        # so the control read this as a claim that held before the
        # round. A vacuous pass is worse than a failure.
        '  and it reaches exactly one path at a time':
            bool(drop) and not any(w in drop for w in TOO_WIDE),
        'and the bytes go AFTER the save, not before':
            i_save >= 0 and i_del > i_save,
        'there is one place that gives a row its own copy':
            bool(unshare),
        '  and it does NOT invent a second naming scheme':
            'field.save(' in unshare and 'upload_to' not in unshare,
        '  and a file it cannot read CLEARS the field':
            'setattr(instance, field_name, None)' in unshare,
        'the duplicate takes its own photo':
            "unshare_file(original_recipe, 'recipe_image')" in c,
        '  and does not carry the display copy forward':
            'original_recipe.recipe_image_display = None' in c,
        '  and the step photos too':
            "unshare_file(fresh, 'step_image')" in c,
        # NOT a bare 'RecipeInstruction.objects.filter(' - the view has
        # queried that since long before this round, to COLLECT the
        # originals, and the control caught the claim holding already.
        '  re-queried, because bulk_create sets no pk on MySQL':
            'for fresh in RecipeInstruction.objects.filter(' in c,
        'no unconditional image delete is left in the edit screen':
            'recipe_image.delete(save=False)' not in c,
        '  and removing a photo releases its display copy':
            c.count("let_go_of_file(recipe, 'recipe_image_display')") == 2,
        'the detector exists':
            os.path.isfile(CHECKER),
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

K = T.python_code_only(read(CHECKER), payloads=True) if os.path.isfile(
    CHECKER) else ''
ok('default_storage.exists(' in K,
   'the detector ASKS THE STORAGE whether a file is there')
ok('default_storage.listdir(' in K,
   '  and asks it what is on the volume, for the orphans')
ok('raise SystemExit(1)' in K,
   '  and exits non-zero on a fault, so a gate need not parse it')
ok(not any(w in K for w in ('.delete(', 'os.remove', 'os.unlink',
                            'rmtree', "'--write'")),
   '  and it deletes NOTHING - Demetri declined a --write, 22 Oct')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
# IF ANY OF THESE HELD BEFORE THE ROUND, THE ROUND PROVED NOTHING.
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items()
        if v and not m.startswith('the detector')]
ok(not held, 'CONTROL: not one of this round holds before it',
   '\n'.join(held))

oldc = T.python_code_only(OLD[CRUD], payloads=True)
ok('recipe_image.delete(save=False)' in oldc,
   'CONTROL: the edit screen DID delete unconditionally')
ok(oldc.count('recipe_image.delete(save=False)') == 2,
   '  in both branches - remove, and replace',
   oldc.count('recipe_image.delete(save=False)'))
ok('original_recipe.pk = None' in oldc,
   'CONTROL: and the duplicate copied the row wholesale')
ok("unshare_file(" not in oldc,
   '  with nothing between that and the save')


# ==========================================================================
head('3. DRIVEN - a duplicate on a real volume')
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
    skip('sections 3, 4 and 5', 'no database, or Pillow is not installed')
else:
    import shutil
    import tempfile
    from django.core.files.base import ContentFile
    from django.contrib.auth.models import User
    from django.test import Client
    import pages.models as PM

    MEDIA = tempfile.mkdtemp(prefix='si1-media-')
    old_media = dj.MEDIA_ROOT
    dj.MEDIA_ROOT = MEDIA

    def on_volume():
        return sorted(os.path.relpath(p, MEDIA).replace('\\', '/')
                      for p in glob.glob(os.path.join(MEDIA, '**', '*'),
                                         recursive=True)
                      if os.path.isfile(p))

    def png(px=40):
        img = Image.new('RGB', (px, px), (180, 140, 90))
        for x in range(0, px, 9):
            for y in range(0, px, 7):
                img.putpixel((x, y), ((x * 7) % 255, (y * 3) % 255, 40))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    def put(name):
        r = PM.Recipe.objects.create(recipe_name=name, servings=4)
        r.recipe_image.save('%s.png' % name.lower().replace(' ', '-'),
                            ContentFile(png()), save=True)
        return PM.Recipe.objects.get(pk=r.pk)

    try:
        boss = User.objects.create_superuser(
            'si1boss', 'si1@example.com', 'x')
        cl = Client()
        cl.force_login(boss)

        source = put('Cottage Pie')
        src_image = source.recipe_image.name
        ok(bool(src_image), 'a source recipe has a photo on the volume',
           src_image)

        resp = cl.post('/recipes/duplicate/%s/' % source.recipe_id)
        ok(resp.status_code == 200,
           'the duplicate view answers', resp.status_code)
        body = resp.json() if resp.status_code == 200 else {}
        new_id = body.get('new_recipe_id')
        ok(bool(body.get('success')) and new_id,
           '  and reports a new recipe', body)

        if new_id:
            copy = PM.Recipe.objects.get(pk=new_id)
            source = PM.Recipe.objects.get(pk=source.pk)

            # THE QUESTION NOBODY ASKED.
            ok(copy.recipe_image.name != source.recipe_image.name,
               'THE COPY DOES NOT SHARE THE SOURCE PHOTO PATH',
               'source %s\ncopy   %s' % (source.recipe_image.name,
                                         copy.recipe_image.name))
            ok(source.recipe_image.name == src_image,
               '  and the source still names the file it always named')
            for who, r in (('source', source), ('copy', copy)):
                ok(os.path.isfile(os.path.join(MEDIA, r.recipe_image.name)),
                   '  and the %s photo is REALLY on the volume' % who,
                   r.recipe_image.name)

            # AND THE DISPLAY COPY IS RE-DERIVED, NOT SHARED.
            ok(copy.recipe_image_display.name
               != source.recipe_image_display.name,
               '  and the display copies are two files, not one',
               'source %s\ncopy   %s'
               % (source.recipe_image_display.name,
                  copy.recipe_image_display.name))
            ok(not copy.display_copy_is_stale(),
               '  and the copy is NOT stale, so save() will not churn it')

            # ==========================================================
            head('4. DRIVEN - and removing one does not destroy the other')
            # ==========================================================
            before = on_volume()
            r2 = cl.post('/recipe/%s/edit/' % copy.recipe_id, {
                'recipe_name': 'Cottage Pie (Copy)',
                'servings': '4',
                'author': 'General',
                'remove_image': '1',
                # NOT NULL, and leaving it out made edit_recipe's except
                # fire - which redirects to the same page success does,
                # so the section passed while nothing had happened.
                'difficulty_level': 'Easy',
            })
            # 302 ONLY. A 200 here is the edit form redisplayed after an
            # error, which is how this section first passed while the
            # removal had not happened - and the detector in section 5
            # is what caught it.
            # THE STATUS SAYS NOTHING HERE. edit_recipe redirects to
            # recipe_management on success AND in its except, so the
            # only difference between a saved edit and a crashed one
            # is the message. Reading it is the difference between
            # this section testing the round and testing nothing.
            from django.contrib.messages import get_messages
            said = [str(m) for m in get_messages(r2.wsgi_request)]
            ok(r2.status_code == 302 and not any(
                'Error updating' in s for s in said),
               'the edit screen accepts a photo removal',
               '%s %s' % (r2.status_code, ' | '.join(said)))
            copy = PM.Recipe.objects.get(pk=copy.pk)
            ok(not copy.recipe_image.name,
               '  and the copy now names NO original',
               copy.recipe_image.name)
            ok(not copy.recipe_image_display.name,
               '  and no display copy either',
               copy.recipe_image_display.name)

            source = PM.Recipe.objects.get(pk=source.pk)
            ok(source.recipe_image.name == src_image,
               'THE SOURCE STILL NAMES ITS PHOTO after the copy let go')
            ok(os.path.isfile(os.path.join(MEDIA, src_image)),
               '  AND THE FILE IS STILL THERE - this is the whole round',
               src_image)
            gone = [p for p in before if p not in on_volume()]
            ok(src_image not in gone,
               '  so the removal took the copy\'s files and not the '
               'source\'s', 'removed: %s' % ', '.join(gone) or '(nothing)')

            # ==========================================================
            head('5. DRIVEN - a save that fails does not cost the photo')
            # ==========================================================
            # THE OTHER WAY A ROW ENDS UP NAMING NOTHING. edit_recipe
            # used to delete the bytes and THEN call recipe.save(), so
            # a save that raised left the file gone and the row still
            # pointing at it - the same broken image, arrived at from
            # the other side. It was found on 22 October by a test POST
            # that omitted difficulty_level, which is NOT NULL: the
            # except fired, the redirect was identical to a successful
            # one, and the picture had already been destroyed.
            #
            # SO THE FAILURE IS DRIVEN ON PURPOSE HERE, by omitting the
            # same field. The round is the claim that the photo
            # survives it.
            keeper = put('Keeper')
            keeper_file = keeper.recipe_image.name
            r3 = cl.post('/recipe/%s/edit/' % keeper.recipe_id, {
                'recipe_name': 'Keeper',
                'servings': '4',
                'author': 'General',
                'remove_image': '1',
                # difficulty_level DELIBERATELY ABSENT - this is the
                # failure being driven, not an oversight.
            })
            said3 = [str(m) for m in get_messages(r3.wsgi_request)]
            ok(any('Error updating' in s for s in said3),
               'the save really did fail', ' | '.join(said3) or '(none)')
            keeper = PM.Recipe.objects.get(pk=keeper.pk)
            ok(keeper.recipe_image.name == keeper_file,
               '  and the row still names its photo, as it must')
            ok(os.path.isfile(os.path.join(MEDIA, keeper_file)),
               '  AND THE FILE IS STILL THERE - a failed save costs '
               'nothing', keeper_file)

            # ==========================================================
            head('6. DRIVEN - the detector names a planted fault')
            # ==========================================================
            # AN INSTRUMENT NOBODY HAS SEEN FAIL IS NOT AN INSTRUMENT.
            def detect():
                out = io.StringIO()
                code = 0
                try:
                    call_command('check_recipe_files', stdout=out)
                except SystemExit as e:
                    code = e.code or 0
                return code, out.getvalue()

            code, said = detect()
            ok(code == 0,
               'a clean tree passes the detector', said[-300:])

            # PLANT: take the file away behind the row's back, which is
            # exactly what the duplicate did on Live.
            # DELIBERATELY NOT NAMED THE WORD test_gate_speed LOOKS
            # FOR - and the rename is the point, not a dodge.
            #
            # That suite derives the planting signature from one
            # reserved identifier, because in this tree it means a file
            # planted in the REPO and restored in a finally, and such a
            # suite must not share a pool with one reading that file.
            # It flagged this suite on 22 October and was right to ask.
            #
            # THE WORD IS NOT WRITTEN HERE EITHER, not even to explain
            # the rename: the signature is a regex over the raw text
            # and a comment is text. The first version of this note
            # said the word and the gate went on failing - which is
            # the same lesson SB-2 learned an hour earlier, when a
            # template tag inside a JavaScript comment turned out to
            # still be a template tag.
            #
            # This file is in tempfile.mkdtemp(prefix='si1-media-'). No
            # other suite can see it, alv_plant.fingerprint() walks the
            # repo and never reaches it, and nothing here needs
            # serialising. Adding this suite to PLANTERS would have
            # made that list's own claim - "they write into real files
            # and put them back" - untrue, and a list that lies is
            # worse than a variable with a different name.
            taken = os.path.join(MEDIA, source.recipe_image.name)
            keep = open(taken, 'rb').read()
            os.remove(taken)
            try:
                code, said = detect()
                ok(code == 1,
                   'a row pointing at a missing file FAILS the detector',
                   'exit %s' % code)
                ok('MISSING' in said and source.recipe_image.name in said,
                   '  and the detector NAMES the file', said[-400:])
                ok('Cottage Pie' in said,
                   '  and the recipe, so a person can go and look')
            finally:
                with open(taken, 'wb') as fh:
                    fh.write(keep)

            # PLANT: two rows, one path - the state a duplicate used to
            # leave behind.
            twin = PM.Recipe.objects.create(recipe_name='Twin', servings=2)
            PM.Recipe.objects.filter(pk=twin.pk).update(
                recipe_image=source.recipe_image.name)
            try:
                code, said = detect()
                ok(code == 1, 'and a SHARED path fails it too',
                   'exit %s' % code)
                ok('SHARED' in said,
                   '  named as shared rather than as missing', said[-400:])
            finally:
                PM.Recipe.objects.filter(pk=twin.pk).delete()

            code, said = detect()
            ok(code == 0, 'and the tree is clean again afterwards',
               said[-300:])
    except Exception as exc:
        ok(False, 'sections 3 to 5 ran to the end', repr(exc)[:300])
    finally:
        dj.MEDIA_ROOT = old_media
        shutil.rmtree(MEDIA, ignore_errors=True)


# ==========================================================================
head('7. REGISTRATION')
# ==========================================================================
ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'migrations') + SUFFIX),
   'this round backed up no migrations directory')
ok(not glob.glob(os.path.join(ROOT, 'pages', 'migrations',
                              '*' + SUFFIX)),
   '  and no migration file - SI-1 changes who writes what, not what '
   'is stored')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1, '  exactly once')
ok('unshare_file(original_recipe' in gate,
   'and a sentinel watches the duplicate')
ok('def delete_unheld' in gate, 'and one watches the delete')
ok('delete_unheld(Recipe, released' in gate,
   'and one watches that it runs AFTER the save')
ok('def held_names' in gate, 'and one watches the detector')

print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the two photos lost on Live come back. They do not.')
print('  The bytes were deleted off the volume in a session nobody')
print('  recorded, and 71 Cottage Pie and 336 Beans, Edamame need a')
print('  fresh upload. This round stops the third one.')
print('')
print('  Not that every pair made BEFORE it is safe. Part two - the')
print('  delete that counts first - is what protects those, and it')
print('  protects them only from this deploy onwards.')
print('')
print('  Not that duplicate_recipe is the only place in this tree')
print('  that copies a row with pk = None. It is the only one that')
print('  was measured destroying a file.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
