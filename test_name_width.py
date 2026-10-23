# -*- coding: utf-8 -*-
"""test_name_width.py - round NL-1, 22 Oct 2026.

A GENERATED NAME DID NOT FIT THE COLUMN IT WAS STORED IN.

Found on Live on 22 October, in the rebuild of 335 display copies.
Four came back like this:

    229  stored as recipe-new-potato-swirls-...-202_rRTWxeC.jpg
    248  stored as recipe-248-pork-shoulder-...-20260_ZrMplqr.jpg
    249  stored as recipe-249-pork-shoulder-...-updated_oK6zykl.jpg
    330  stored as recipe-330-chicken-thighs-...-to_8BzeTlF.jpg

THE TIMESTAMPS ARE CUT OFF MID-DIGIT. That is not SD-1's collision
suffixing - SD-1 clears the target first, so nothing was in the way.
It is max_length: an ImageField defaults to 100, recipe_images_display/
spends 22, and the longest recipe names do not fit. get_available_name
truncates the stem AND suffixes it rather than refusing.

AND IT LEFT SD-1 INCOMPLETE. display_copy_is_stale compares the stored
name with display_name_for(original) - on purpose, so there is no
column to forget to clear - and a truncated suffixed name can never
equal that. Those four rows are permanently stale, so Recipe.save()
rebuilds them on every edit and orphans another file each time.

SECTION 3 IS THE FOUR, REPRODUCED. A recipe named exactly like 248,
photographed, and then the questions nobody asked: is the stored name
the one that was wanted, and does the row think itself stale? Against
the backup the generated name is 116 characters and the answer to both
is no.

SECTION 4 DRIVES THE DETECTOR'S FOURTH QUESTION. Stale is not missing,
not shared and not orphaned - the file is there, one row names it,
nothing is loose - so none of SI-1's three headings could see those
four, and a fourth heading is what this round adds.
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
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_namewidth'
ME = 'test_name_width.py'
PATCHER = 'apply_name_width.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'NL-1, 22 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
CHECKER = os.path.join(ROOT, 'pages', 'management', 'commands',
                       'check_recipe_files.py')
MIG = os.path.join(ROOT, 'pages', 'migrations', '0102_nl1_name_width.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, CHECKER)

# THE NAME THAT OVERFLOWED, verbatim from Live.
LONG = 'Pork Shoulder (Deboned, Rind-off) - Oven and Gas Braai'
# WHAT A GENERATED BASENAME COSTS BEFORE ANY OF THE RECIPE NAME:
# 'recipe-' 7, a six digit id 6, two hyphens 2, a 14 digit stamp 14,
# '.jpeg' 5. And the longest directory is 'recipe_images_display/'.
FIXED = 34
LONGEST_DIR = len('recipe_images_display/')
OLD_WIDTH = 100

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


# ASKED OF EACH FIELD, NOT OF THE FILE. The first version of this
# counted 'max_length=255' in pages/models.py and called three enough -
# and the control refused it, because SIXTY-FOUR other fields in this
# file are already 255 characters wide. A count of a common string is
# not a claim about three particular fields.
def field_has_width(src, decl, width='max_length=255'):
    a = src.find(decl)
    if a < 0:
        return False
    depth, i = 0, src.find('(', a)
    if i < 0:
        return False
    for j in range(i, min(len(src), i + 2000)):
        if src[j] == '(':
            depth += 1
        elif src[j] == ')':
            depth -= 1
            if depth == 0:
                return width in src[a:j]
    return False


def claims(d):
    m = T.python_code_only(d[MODELS], payloads=True)
    c = T.python_code_only(d[CHECKER], payloads=True)
    return {
        'recipe_image holds 255':
            field_has_width(m, 'recipe_image = models.ImageField'),
        'recipe_image_display holds 255':
            field_has_width(m, 'recipe_image_display = models.ImageField'),
        'step_image holds 255':
            field_has_width(m, 'step_image = models.ImageField'),
        'all three upload paths bound the slug':
            m.count('[:NAME_SLUG_CAP]') == 3,
        '  from one constant, not three literals':
            'NAME_SLUG_CAP = ' in m,
        'the detector asks a fourth question':
            'display_copy_is_stale()' in c,
        '  and a stale row FAILS it':
            'if missing or shared or stale:' in c,
        '  and stale is counted separately from the other three':
            "'  missing %d   shared %d   stale %d   orphans %d'" in c,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

# READ OUT OF THE SOURCE, NOT IMPORTED. Section 1 runs before Django
# is configured - importing pages.models here asks for INSTALLED_APPS
# and raises - and reading the constant is the point either way: this
# suite must not carry its own copy of the number.
import re as _re_cap                                        # noqa: E402
_m_cap = _re_cap.search(r'NAME_SLUG_CAP = (\d+)', NOW[MODELS])
CAP = int(_m_cap.group(1)) if _m_cap else None
ok(CAP is not None, 'the cap is a constant this suite can read rather '
                    'than repeat', CAP)
if CAP:
    # THE ARITHMETIC THAT THE PATCHER'S OWN GATE REFUSED ONCE. 60 was
    # the first answer and it is 116, which still overflows the OLD
    # column - so a tree that had not run the migration would have gone
    # on truncating exactly as before.
    worst = CAP + FIXED + LONGEST_DIR
    ok(worst <= OLD_WIDTH,
       'a generated path fits the OLD 100 column too, so the fix does '
       'not depend on the migration having run',
       '%d + %d + %d = %d' % (CAP, FIXED, LONGEST_DIR, worst))


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(not held, 'CONTROL: not one of this round holds before it',
   '\n'.join(held))

oldm = T.python_code_only(OLD[MODELS], payloads=True)
ok(not any(field_has_width(oldm, decl) for decl in (
       'recipe_image = models.ImageField',
       'recipe_image_display = models.ImageField',
       'step_image = models.ImageField')),
   'CONTROL: not one image column was wider than the default 100')
ok('NAME_SLUG_CAP' not in oldm,
   'CONTROL: and no upload path bounded the recipe name')

# AND THE NAME THAT ACTUALLY OVERFLOWED, measured rather than asserted.
try:
    from django.utils.text import slugify as _slug
    bare = len(_slug(LONG))
    ok(bare + FIXED + LONGEST_DIR > OLD_WIDTH,
       'CONTROL: 248\'s own name generated %d characters, over the 100 '
       'the column held' % (bare + FIXED + LONGEST_DIR),
       '%r slugifies to %d' % (LONG, bare))
except Exception as e:
    skip('the measured overflow', str(e)[:60])


# ==========================================================================
head('3. DRIVEN - the name that overflowed, on a real volume')
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
    skip('sections 3 and 4', 'no database, or Pillow is not installed')
else:
    import shutil
    import tempfile
    from django.core.files.base import ContentFile
    import pages.models as PM

    MEDIA = tempfile.mkdtemp(prefix='nl1-media-')
    old_media = dj.MEDIA_ROOT
    dj.MEDIA_ROOT = MEDIA

    def png(px=60):
        img = Image.new('RGB', (px, px), (120, 160, 110))
        for x in range(0, px, 5):
            for y in range(0, px, 3):
                img.putpixel((x, y), ((x * 5) % 255, 40, (y * 9) % 255))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    try:
        r = PM.Recipe.objects.create(recipe_name=LONG, servings=6)
        r.recipe_image.save('a-very-long-original-name-indeed.png',
                            ContentFile(png()), save=True)
        r = PM.Recipe.objects.get(pk=r.pk)

        # THE MODEL ITSELF, not the text that declares it. A field can
        # read 255 in the source and still be 100 in the schema if the
        # migration disagrees, and section 5 checks the migration -
        # this checks what Django actually loaded.
        for mdl, fld in ((PM.Recipe, 'recipe_image'),
                         (PM.Recipe, 'recipe_image_display'),
                         (PM.RecipeInstruction, 'step_image')):
            ok(mdl._meta.get_field(fld).max_length == 255,
               'Django loaded %s at 255' % fld,
               mdl._meta.get_field(fld).max_length)

        orig = r.recipe_image.name
        disp = r.recipe_image_display.name
        ok(bool(orig), 'the long-named recipe has a photo', orig)

        # THE SUFFIX IS THE SYMPTOM. Seven random characters after an
        # underscore is what get_available_name adds when it has to
        # make room, and it is exactly what the four on Live wore.
        import re as _re
        ok(not _re.search(r'_[A-Za-z0-9]{7}\.', os.path.basename(orig)),
           'the stored original carries NO random suffix', orig)
        ok(len(orig) <= OLD_WIDTH,
           '  and the whole path fits even the old 100 column',
           '%d characters' % len(orig))

        ok(bool(disp), '  and a display copy was built', disp)
        want = PM.display_name_for(orig)
        ok(os.path.basename(disp) == want,
           'THE DISPLAY COPY HAS THE NAME ITS ORIGINAL IMPLIES',
           'got  %s\nwant %s' % (os.path.basename(disp), want))
        ok(not r.display_copy_is_stale(),
           '  SO THE ROW IS NOT STALE - this is the whole round',
           'stored %s' % disp)

        # AND IT STAYS THAT WAY. A permanently stale row rebuilds on
        # every edit and orphans a file each time; this proves the
        # second save is a no-op rather than another orphan.
        before = sorted(glob.glob(os.path.join(MEDIA, '**', '*'),
                                  recursive=True))
        r.servings = 8
        r.save()
        after = sorted(glob.glob(os.path.join(MEDIA, '**', '*'),
                                 recursive=True))
        ok(before == after,
           '  and editing it writes NO new file',
           '%d -> %d' % (len(before), len(after)))

        # ==============================================================
        head('4. DRIVEN - the detector names a stale row')
        # ==============================================================
        def detect():
            out = io.StringIO()
            code = 0
            try:
                call_command('check_recipe_files', stdout=out)
            except SystemExit as e:
                code = e.code or 0
            return code, out.getvalue()

        code, said = detect()
        ok(code == 0, 'a clean tree passes the detector', said[-300:])

        # PLANT: a display copy under a name the original does not
        # imply - which is what a truncated, suffixed name IS. The file
        # is put on the volume too, so this is STALE and not MISSING:
        # if the detector called it missing, the fourth question would
        # be doing nothing the first three did not.
        wrong = 'recipe_images_display/not-the-implied-name.jpg'
        os.makedirs(os.path.join(MEDIA, 'recipe_images_display'),
                    exist_ok=True)
        with open(os.path.join(MEDIA, wrong), 'wb') as fh:
            fh.write(png())
        PM.Recipe.objects.filter(pk=r.pk).update(
            recipe_image_display=wrong)
        try:
            code, said = detect()
            ok(code == 1, 'a stale display copy FAILS the detector',
               'exit %s' % code)
            ok('STALE' in said,
               '  named as stale, not as missing or orphaned',
               said[-500:])
            ok('MISSING' not in said,
               '  and the file really is there, so it is not missing')
        finally:
            PM.Recipe.objects.filter(pk=r.pk).update(
                recipe_image_display=disp)
    except Exception as exc:
        ok(False, 'sections 3 and 4 ran to the end', repr(exc)[:300])
    finally:
        dj.MEDIA_ROOT = old_media
        shutil.rmtree(MEDIA, ignore_errors=True)


# ==========================================================================
head('5. THE MIGRATION')
# ==========================================================================
ok(os.path.isfile(MIG), 'the round brings its own migration', MIG)
if os.path.isfile(MIG):
    g = read(MIG)
    ok(g.count('migrations.AlterField(') == 3,
       '  three AlterField, one per column',
       g.count('migrations.AlterField('))
    ok(not any(b in g for b in ('RunPython', 'RunSQL', 'DeleteModel',
                                'RemoveField')),
       '  and it touches no data and drops nothing')
    ok(g.count('max_length=255') == 3, '  widening all three to 255')
    # THE DEPENDENCY IS READ OFF DISK, NOT TYPED. A typed one is wrong
    # the moment somebody adds a migration.
    names = sorted(n[:-3] for n in
                   os.listdir(os.path.join(ROOT, 'pages', 'migrations'))
                   if n.endswith('.py') and n != '__init__.py'
                   and '.bak_' not in n and 'nl1_name_width' not in n)
    ok(names and ("'%s'" % names[-1]) in g,
       '  depending on the migration that really is latest',
       'latest on disk: %s' % (names[-1] if names else '(none)'))


# ==========================================================================
head('6. REGISTRATION')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1, '  exactly once')
ok('NAME_SLUG_CAP' in gate, 'and a sentinel watches the cap')

print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the four stale rows on Live are repaired. They are')
print('  repaired by a rebuild, which is a command Demetri runs when')
print('  he chooses - not a side effect of a deploy. Until then they')
print('  serve their full-size original, which is slow and not broken.')
print('')
print('  Not that the orphans those four left behind are collected.')
print('  Every edit of those recipes since they went stale wrote')
print('  another display copy nobody references. Counting them is')
print('  what the detector does; removing them is a decision nobody')
print('  has taken.')
print('')
print('  Not that 255 is enough for ever. It is enough for a bounded')
print('  slug plus 34 characters, which is the only thing that')
print('  generates these names today.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
