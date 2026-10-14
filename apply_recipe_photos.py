# -*- coding: utf-8 -*-
"""apply_recipe_photos.py - round PX-1, 13 Oct 2026.

A PHOTOGRAPH STORED LOSSLESSLY IS A PHOTOGRAPH STORED WRONG.

Demetri reported the Recipe Management grid taking a long time to load.
Measured on the live Railway volume:

    324 files, ALL PNG, 199.4 MB, 630 KB average
    none over 1000px on the long edge - 97 under 500, 227 under 1000
    ZERO have a single non-opaque pixel
    322 carry an RGBA alpha channel that is opaque everywhere

Re-encoded at the SAME pixel dimensions, JPEG q85, progressive, optimised:

    17.7 MB, 56 KB average - NINE PER CENT of today
    one page of 48 goes from about 30 MB to about 2.7 MB

NAMED PX-1 AND NOT PH-1. PH-1 is the passport-holder round and PH-1c is
cited inside backfill_passport_holder.py. Checked before naming anything:
PH-1 appears in 19 files, IM-1 in 11; PX-1, IM-2, JP-1 and PC-1 are free.

TWO PROPOSALS OF MINE THAT MEASUREMENT KILLED
----------------------------------------------
1. RESIZE TO 1280px. I reasoned it from the display sizes before I knew
   the source pixels. Nothing in the library is over 1000px, so the
   thumbnail call in my own measuring script did nothing on any of the
   324. THIS ROUND RESIZES NOTHING. Every pixel is kept.

2. "322 HAVE TRANSPARENCY". My own script printed that and the label was
   wrong - it counted MODES THAT CAN CARRY ALPHA, not images that use
   it. Asked properly, minimum alpha over every pixel of every file, the
   answer is 0 of 324. The flattening decision it implied does not
   exist. The conversion still flattens onto white, defensively, and
   says here that it is defence rather than need.

WHAT GETS CHANGED, AND WHY IT IS FEWER PLACES THAN IT LOOKS
------------------------------------------------------------
recipe_image.url is reached from seventeen places. SIX of them are
JavaScript reading `${recipe.recipe_image}` out of JSON that a Python
view built, so they move for free the moment the view does. What is
actually edited:

    8  Python serialisers in two view modules
    7  Django {{ ... .url }} render sites in six templates

and all fifteen point at ONE model property, so the question of which
file to serve is answered in one place instead of fifteen.

THE ORIGINALS ARE KEPT. Demetri decided it: a derived copy, not an
in-place rewrite. The PNG masters stay the masters, and if q85 ever
proves wrong the display copies can be rebuilt from them.

DRY BY DEFAULT, AND THAT IS NOT A COURTESY. The batch command prints
what it would write and writes nothing until --write, which is the
convention backfill_passport_holder and backfill_task_rollup already
use. The first real run against 324 live files is a report.

WHAT THIS ROUND DOES NOT DO
----------------------------
It does not touch django.views.static.serve, which still serves /media/
in production out of mysite/urls.py with no DEBUG guard. At 630 KB a
file that matters enormously; at 56 KB it may not matter at all, and
changing how every upload in the application is served on a guess is
worse than measuring first. Demetri decided: re-measure the page once
the photos are small, then decide.

It does not fix the 97 originals under 500px. They are stretched today -
the view_recipe hero on a phone wants about 1170 device pixels - and
that softness is in the PNG. Converting makes them light; it cannot make
them sharp.

See test_recipe_photos.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_pxphotos'
SUITE = 'test_recipe_photos.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
MODELS = os.path.join('pages', 'models.py')
URLS = os.path.join('mysite', 'urls.py')
MIGRATION = os.path.join('pages', 'migrations',
                         '0099_recipe_image_display.py')
COMMAND = os.path.join('pages', 'management', 'commands',
                       'convert_recipe_photos.py')
CHECK = False

QUALITY = 85
N_SERIALISERS, N_TEMPLATES, N_JS_FREE = 8, 7, 6

CEILING_WAS, CEILING_NOW = 38, 38
CONVERTED_WAS, CONVERTED_NOW = 73, 74
WAITING_WAS, WAITING_NOW = 2, 2
ALIAS_WAS, ALIAS_NOW = 57, 59

# ---------------------------------------------------------------------------
# models.py - the helper, the field, the property, the save hook
# ---------------------------------------------------------------------------
HELPER_ANCHOR = """def recipe_document_upload_path(instance, filename):"""

HELPER = '''def recipe_display_upload_path(instance, filename):
    """Where a derived display copy lives. PX-1, 13 Oct 2026.

    Beside the masters, not among them: recipe_images_display/ rather
    than recipe_images/. A later round that wants to count, archive or
    rebuild the originals can do it with a directory listing instead of
    a filename rule.
    """
    return os.path.join('recipe_images_display', filename)


def make_display_jpeg(field_file, quality=%d):
    """The ONE place that knows how a display copy is made.

    PX-1, 13 Oct 2026. Called from Recipe.save() for new uploads and
    from the convert_recipe_photos command for the 324 already on the
    volume, so a photo converted today and one converted next year are
    the same photo. Returns JPEG bytes, or None if the source cannot be
    read - a recipe with an unreadable image is not a reason to refuse a
    save.

    NO RESIZING. Measured 13 Oct: nothing in the library is over 1000px
    on the long edge, and the sizes the app draws want up to about 1170.
    Shrinking these would make a soft picture softer to save bytes that
    the encoder gives up for nothing.

    THE FLATTEN IS DEFENCE, NOT NEED. Measured the same day: 0 of 324
    images have a single non-opaque pixel, though 322 carry an alpha
    channel. If one ever does, white is what it lands on, chosen here
    rather than discovered later as a black rectangle.
    """
    import io
    from PIL import Image

    if not field_file:
        return None
    try:
        field_file.open('rb')
        im = Image.open(field_file)
        im.load()
    except Exception:
        return None
    finally:
        try:
            field_file.close()
        except Exception:
            pass

    rgba = im.convert('RGBA')
    flat = Image.new('RGB', im.size, (255, 255, 255))
    flat.paste(rgba, mask=rgba.split()[3])
    out = io.BytesIO()
    flat.save(out, 'JPEG', quality=quality, optimize=True,
              progressive=True)
    return out.getvalue()


def display_name_for(original_name):
    """The display copy's filename for a given original. PX-1.

    The stem is the original's, so the two are obviously a pair on a
    directory listing AND so staleness is decidable without a database
    column: the original's name already carries a timestamp, so a
    re-upload produces a new stem and the old display copy stops
    matching.
    """
    return os.path.splitext(os.path.basename(original_name))[0] + '.jpg'


def recipe_document_upload_path(instance, filename):''' % QUALITY

FIELD_WAS = ("    recipe_image = models.ImageField("
             "upload_to=recipe_image_upload_path, blank=True, null=True)")

FIELD_NOW = (
    "    recipe_image = models.ImageField("
    "upload_to=recipe_image_upload_path, blank=True, null=True)\n"
    "    # PX-1, 13 Oct 2026 - THE DERIVED DISPLAY COPY, never uploaded\n"
    "    # to directly. editable=False keeps it out of every ModelForm in\n"
    "    # the application, because a field nobody may set by hand cannot\n"
    "    # drift from the original it is derived from.\n"
    "    recipe_image_display = models.ImageField(\n"
    "        upload_to=recipe_display_upload_path, blank=True, null=True,\n"
    "        editable=False,\n"
    "        help_text='Derived JPEG of recipe_image. Rebuilt by '\n"
    "                  'manage.py convert_recipe_photos --write.')")

SAVE_WAS = """    def save(self, *args, **kwargs):
        # Auto-calculate total_time if not provided
        if not self.total_time and self.prep_time and self.cook_time:
            self.total_time = self.prep_time + self.cook_time
        super().save(*args, **kwargs)"""

SAVE_NOW = '''    @property
    def photo_url(self):
        """The URL to DRAW this recipe with. PX-1, 13 Oct 2026.

        Display copy, else the original, else None. Fifteen call sites
        ask this instead of reaching for recipe_image.url themselves -
        eight Python serialisers and seven templates - so the question
        of which file to serve is answered once.

        The fallback is load-bearing while the batch runs: a recipe
        whose display copy does not exist yet draws from its original
        and looks exactly as it does today.
        """
        if self.recipe_image_display:
            return self.recipe_image_display.url
        if self.recipe_image:
            return self.recipe_image.url
        return None

    def display_copy_is_stale(self):
        """True when a display copy should be built. PX-1.

        Asked of the NAMES, not of a flag: the original's filename
        carries a timestamp, so a re-upload gives a new stem and the old
        display copy stops matching. No column to forget to clear.
        """
        if not self.recipe_image:
            return False
        if not self.recipe_image_display:
            return True
        want = display_name_for(self.recipe_image.name)
        return os.path.basename(self.recipe_image_display.name) != want

    def save(self, *args, **kwargs):
        # Auto-calculate total_time if not provided
        if not self.total_time and self.prep_time and self.cook_time:
            self.total_time = self.prep_time + self.cook_time
        super().save(*args, **kwargs)
        # PX-1, 13 Oct 2026 - BUILD THE DISPLAY COPY ON UPLOAD, so the
        # library cannot drift back. A one-time batch alone regresses the
        # moment somebody adds a recipe.
        #
        # AFTER super().save(), because on a fresh upload recipe_image is
        # still an in-memory file until Django has stored it. The second
        # write names its one field, and a failure here must never lose
        # the recipe the person just saved - the picture is worth less
        # than the recipe.
        if self.display_copy_is_stale():
            try:
                from django.core.files.base import ContentFile
                data = make_display_jpeg(self.recipe_image)
                if data is not None:
                    self.recipe_image_display.save(
                        display_name_for(self.recipe_image.name),
                        ContentFile(data), save=False)
                    super().save(update_fields=['recipe_image_display'])
            except Exception:
                pass'''

# ---------------------------------------------------------------------------
# mysite/urls.py - the cache header
# ---------------------------------------------------------------------------
URLS_WAS = """    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]"""

URLS_NOW = '''    re_path(r'^media/(?P<path>.*)$', cached_media),
]'''

URLS_VIEW_ANCHOR = """def robots_txt(request):
    content = "User-agent: *\\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")"""

URLS_VIEW = '''def robots_txt(request):
    content = "User-agent: *\\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")


def cached_media(request, path):
    """serve(), with a cache header on it. PX-1, 13 Oct 2026.

    WHY THIS IS SAFE TO CACHE FOR A YEAR. Every uploaded filename in
    this application carries a timestamp - recipe-{id}-{slug}-{stamp}.
    A re-upload produces a NEW name, so a cached copy can never be the
    wrong version of a file; it can only be a file nobody references any
    more. That is what makes `immutable` honest here rather than a
    gamble.

    WHAT IT DOES NOT FIX. serve() is Django's development file server
    and it is still what moves these bytes in production, one Python
    worker per file for the whole transfer. This header removes the
    REPEAT visits - a return to the grid costs zero requests instead of
    48 conditional ones - and does nothing at all for the first.
    Measured 13 Oct: the photos are the larger problem and PX-1 takes
    them; whether serve() still matters afterwards is a question to
    re-measure, not to guess.
    """
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response'''

# ---------------------------------------------------------------------------
# the eight Python serialisers
# ---------------------------------------------------------------------------
SER = (
    (os.path.join('pages', 'views', 'recipes', 'meal_planning.py'),
     "'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,",
     "'recipe_image': recipe.photo_url,", 3),
    (os.path.join('pages', 'views', 'recipes', 'meal_planning.py'),
     "'image': recipe.recipe_image.url if recipe.recipe_image else None,",
     "'image': recipe.photo_url,", 1),
    (os.path.join('pages', 'views', 'recipes', 'recipe_crud.py'),
     "'recipe_image': recipe.recipe_image.url if recipe.recipe_image else None,",
     "'recipe_image': recipe.photo_url,", 3),
    (os.path.join('pages', 'views', 'recipes', 'recipe_crud.py'),
     "'recipe_image': r.recipe_image.url if r.recipe_image else None,",
     "'recipe_image': r.photo_url,", 1),
)

# ---------------------------------------------------------------------------
# the seven template render sites
# ---------------------------------------------------------------------------
TPL = (
    ('meal_plan_calendar.html', '{{ recipe.recipe_image.url }}',
     '{{ recipe.photo_url }}', 1),
    ('recipe_management.html', '{{ recipe.recipe_image.url }}',
     '{{ recipe.photo_url }}', 2),
    ('recipe_pdf.html', '{{ recipe.recipe_image.url }}',
     '{{ recipe.photo_url }}', 1),
    ('view_meal_plan.html', '{{ meal_recipe.recipe.recipe_image.url }}',
     '{{ meal_recipe.recipe.photo_url }}', 1),
    ('view_recipe.html', '{{ recipe.recipe_image.url }}',
     '{{ recipe.photo_url }}', 1),
    ('wcim_recipe_quick_view.html', '{{ recipe.recipe_image.url }}',
     '{{ recipe.photo_url }}', 1),
)


MIGRATION_PAYLOAD = '''# -*- coding: utf-8 -*-
"""PX-1, 13 Oct 2026 - the derived display copy.

Schema only. It adds a nullable column and converts nothing: the 324
photos already on the volume are the batch command's job, deliberately,
because a data migration that re-encodes 200 MB runs inside a deploy
where nobody is watching and nothing can be inspected first.
"""
from django.db import migrations, models

import pages.models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0098_comment_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='recipe_image_display',
            field=models.ImageField(
                blank=True,
                editable=False,
                null=True,
                help_text=('Derived JPEG of recipe_image. Rebuilt by '
                           'manage.py convert_recipe_photos --write.'),
                upload_to=pages.models.recipe_display_upload_path),
        ),
    ]
'''

COMMAND_PAYLOAD = '''# -*- coding: utf-8 -*-
"""convert_recipe_photos - give every recipe photo a light display copy.

    python manage.py convert_recipe_photos            DRY RUN
    python manage.py convert_recipe_photos --write    apply

DRY BY DEFAULT, AND THAT IS NOT A COURTESY. This writes files to the
media volume. The default run reports every recipe it would convert, the
bytes now and the bytes after, and --write is the only thing that turns
it into a write. The convention is backfill_task_rollup's, 20 Sep 2026,
and backfill_passport_holder's after it.

WHAT IT DOES. For each recipe with an original and no current display
copy, it re-encodes the original as JPEG at the SAME pixel dimensions
and stores it in recipe_images_display/. It never writes to
recipe_images/ and never deletes anything. The originals stay the
masters.

MEASURED ON THE LIVE VOLUME, 13 Oct 2026:

    324 files, all PNG, 199.4 MB, 630 KB average
    none over 1000px on the long edge
    0 of 324 have a single non-opaque pixel
    re-encoded: 17.7 MB, 56 KB average - 9 per cent of today

IDEMPOTENT AND RESUMABLE. Staleness is decided from the FILENAMES, not
from a flag: the original's name carries a timestamp, so a re-upload
gives a new stem and the old display copy stops matching. Run it twice
and the second run converts nothing. Interrupt it and run it again and
it picks up where it stopped.

ONE RECIPE'S FAILURE IS NOT THE RUN'S. An unreadable image is reported
by name and the run carries on, because 323 converted photos and a list
of one problem is a better outcome than a traceback and none.
"""
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from pages.models import Recipe, display_name_for, make_display_jpeg


class Command(BaseCommand):
    help = ('Re-encode recipe photos into light JPEG display copies. '
            'Dry by default; pass --write to apply.')

    def add_arguments(self, parser):
        parser.add_argument(
            '--write', action='store_true',
            help='Actually write the display copies. Without this the '
                 'command reports and changes nothing.')
        parser.add_argument(
            '--limit', type=int, default=0,
            help='Stop after this many recipes. Useful for a first '
                 'cautious --write over a handful.')
        parser.add_argument(
            '--quality', type=int, default=85,
            help='JPEG quality. Default 85, which Demetri reviewed '
                 'against real photos on 13 Oct 2026.')

    def handle(self, *args, **opts):
        write = opts['write']
        limit = opts['limit'] or 0
        quality = opts['quality']

        done = skipped = failed = 0
        before = after = 0
        problems = []

        qs = Recipe.objects.exclude(recipe_image='').exclude(
            recipe_image=None).order_by('recipe_id')

        self.stdout.write('')
        self.stdout.write('  %-6s %-34s %9s %9s'
                          % ('id', 'recipe', 'now', 'after'))
        self.stdout.write('  ' + '-' * 62)

        for recipe in qs.iterator():
            if limit and done + skipped >= limit:
                break
            if not recipe.display_copy_is_stale():
                skipped += 1
                continue

            try:
                size_now = recipe.recipe_image.size
            except Exception:
                size_now = 0

            data = make_display_jpeg(recipe.recipe_image, quality=quality)
            if data is None:
                failed += 1
                problems.append((recipe.recipe_id, recipe.recipe_name,
                                 recipe.recipe_image.name))
                continue

            before += size_now
            after += len(data)
            done += 1
            self.stdout.write('  %-6s %-34s %8.0fK %8.0fK'
                              % (recipe.recipe_id,
                                 (recipe.recipe_name or '')[:34],
                                 size_now / 1024.0, len(data) / 1024.0))

            if write:
                recipe.recipe_image_display.save(
                    display_name_for(recipe.recipe_image.name),
                    ContentFile(data), save=False)
                Recipe.objects.filter(pk=recipe.pk).update(
                    recipe_image_display=recipe.recipe_image_display.name)

        self.stdout.write('')
        self.stdout.write('  converted %d   already current %d   '
                          'unreadable %d' % (done, skipped, failed))
        if done:
            self.stdout.write('  %.1f MB  ->  %.1f MB   (%.0f%% of today)'
                              % (before / 1048576.0, after / 1048576.0,
                                 100.0 * after / before if before else 0))
        if problems:
            self.stdout.write('')
            self.stdout.write('  COULD NOT BE READ - named, not swallowed:')
            for rid, name, fn in problems[:20]:
                self.stdout.write('    %-6s %-30s %s'
                                  % (rid, (name or '')[:30], fn))
        self.stdout.write('')
        if not write:
            self.stdout.write('  DRY RUN. Nothing was written. '
                              'Pass --write to apply.')
        self.stdout.write('')
'''


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('PX-1 REFUSED: %s' % msg)


def fit(text, lit):
    """An anchor written with LF, matched against a file that may not use
    LF. PX-1, 13 Oct 2026.

    Census of the fifteen files this round edits: nine LF, four CRLF and
    TWO GENUINELY MIXED - recipe_management.html is 3632 CRLF and 14 LF,
    view_recipe.html 4241 and 14. A patcher that assumed LF would refuse
    on mysite/urls.py, and a patcher that normalised line endings to get
    its match would rewrite every line of a CRLF file as a side effect:
    a four-line change arriving as a four-thousand-line diff, which is
    not a change anybody can review.

    So: decided from what the FILE mostly uses, and only for an anchor
    that actually spans lines - a single-line anchor needs no fitting,
    which is why the eight serialisers and seven render sites are
    unaffected even though five of their files are CRLF or mixed.
    """
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def exactly(text, lit, n, where):
    got = text.count(fit(text, lit))
    if got != n:
        refuse('%s: %r appears %d time(s), expected exactly %d'
               % (where, lit[:70], got, n))


def swap(text, was, now, n, where):
    """Match and replace in the file's own line endings."""
    exactly(text, was, n, where)
    return text.replace(fit(text, was), fit(text, now))


def bump(text, lit, was, now, note, where):
    old = lit % was
    exactly(text, old, 1, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    def P(*parts):
        return os.path.join(root, *parts)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, asked of the model rather than of a
    # count: if the field is declared, the round has run.
    if 'recipe_image_display = models.ImageField(' in read(P(MODELS)):
        print('PX-1  already applied - Recipe carries a display copy.')
        return 0

    out, new = {}, {}

    # ---------------------------------------------------------------- 1
    # models.py
    p = P(MODELS)
    s = read(p)
    for was, now, what in ((HELPER_ANCHOR, HELPER, 'the helper'),
                           (FIELD_WAS, FIELD_NOW, 'the field'),
                           (SAVE_WAS, SAVE_NOW, 'photo_url and save()')):
        s = swap(s, was, now, 1, '%s (%s)' % (MODELS, what))
    out[p] = s

    # ---------------------------------------------------------------- 2
    # the eight serialisers
    n_ser = 0
    for rel, was, now, n in SER:
        p = P(rel)
        s = out.get(p, read(p))
        out[p] = swap(s, was, now, n, '%s (serialiser)' % rel)
        n_ser += n
    if n_ser != N_SERIALISERS:
        refuse('expected %d serialiser(s), planned %d'
               % (N_SERIALISERS, n_ser))

    # ---------------------------------------------------------------- 3
    # the seven template sites
    n_tpl = 0
    for page, was, now, n in TPL:
        p = alv_tree.path_of(page)
        s = out.get(p, read(p))
        out[p] = swap(s, was, now, n, '%s (render site)' % page)
        n_tpl += n
    if n_tpl != N_TEMPLATES:
        refuse('expected %d template site(s), planned %d'
               % (N_TEMPLATES, n_tpl))

    # ---------------------------------------------------------------- 4
    # mysite/urls.py
    p = P(URLS)
    s = read(p)
    for was, now, what in ((URLS_VIEW_ANCHOR, URLS_VIEW, 'the view'),
                           (URLS_WAS, URLS_NOW, 'the route')):
        s = swap(s, was, now, 1, '%s (%s)' % (URLS, what))
    out[p] = s

    # ---------------------------------------------------------------- 5
    # the two new files
    new[P(MIGRATION)] = MIGRATION_PAYLOAD
    new[P(COMMAND)] = COMMAND_PAYLOAD

    # ---------------------------------------------------------------- 6
    # the registers
    p = P(TREE)
    s = read(p)
    anchor = ("    # RS-1a, 13 Oct 2026 - the recipe side starts catching "
              "up.\n    'test_recipe_tones.py',\n]")
    out[p] = swap(
        s, anchor,
        ("    # RS-1a, 13 Oct 2026 - the recipe side starts catching up.\n"
         "    'test_recipe_tones.py',\n"
         "    # PX-1, 13 Oct 2026 - the recipe photos get an owner.\n"
         "    '%s',\n]" % SUITE), 1, '%s (CONVERTED)' % TREE)

    p = P(ROUNDS)
    s = read(p)
    anchor = "    '.bak_rstones',\n]"
    out[p] = swap(s, anchor,
                  "    '.bak_rstones',\n    '%s',\n]" % SUFFIX, 1,
                  '%s (ROUNDS)' % ROUNDS)

    p = P(WD)
    s = read(p)
    out[p] = bump(s, 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'PX-1, 13 Oct 2026 - this round own suite. The photos '
                  'are a different kind of round and the register does not '
                  'care.', '%s (CONVERTED_N)' % WD)

    p = P(CO)
    s = read(p)
    old = "ok(len(aliased) == %d," % ALIAS_WAS
    exactly(s, old, 1, '%s (alias count)' % CO)
    s = s.replace(old, "ok(len(aliased) == %d," % ALIAS_NOW, 1)
    old2 = ("'%d file(s) alias it - 28 patchers and 29 suites' "
            "% len(aliased),")
    exactly(s, old2, 1, '%s (alias wording)' % CO)
    s = s.replace(old2,
                  ("'%d file(s) alias it - 29 patchers and 30 suites' "
                   "% len(aliased),   # PX-1, 13 Oct 2026 - this round own "
                   "patcher and suite   # (was " + str(ALIAS_WAS)
                   + ", 28 and 29)"), 1)
    out[p] = s

    p = P(PS1)
    s = read(p)
    anchor = "    'test_recipe_tones.py'\n)"
    out[p] = swap(s, anchor,
                  "    'test_recipe_tones.py',\n    '%s'\n)" % SUITE, 1,
                  '%s ($suites)' % PS1)

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('PX-1  --check: %d file(s) change, %d new'
              % (len(out), len(new)))
        for q in sorted(out):
            print('        M %s' % os.path.relpath(q, root))
        for q in sorted(new):
            print('        + %s' % os.path.relpath(q, root))
        print('      %d serialiser(s), %d template site(s); %d JS site(s) '
              'move for free' % (N_SERIALISERS, N_TEMPLATES, N_JS_FREE))
        print('      CONVERTED %d -> %d; aliases %d -> %d; ceiling %d'
              % (CONVERTED_WAS, CONVERTED_NOW, ALIAS_WAS, ALIAS_NOW,
                 CEILING_NOW))
        return 0

    for q in sorted(out):
        backup(q)
        write(q, out[q])
    for q in sorted(new):
        d = os.path.dirname(q)
        if not os.path.isdir(d):
            os.makedirs(d)
        write(q, new[q])
    print('PX-1  applied to %d file(s), %d new.' % (len(out), len(new)))
    print('     Recipe gains a derived display copy and one photo_url.')
    print('     %d serialiser(s) and %d template site(s) now ask it; %d '
          'JavaScript site(s) follow for free.'
          % (N_SERIALISERS, N_TEMPLATES, N_JS_FREE))
    print('     /media/ gains an immutable cache header.')
    print('     NOTHING IS CONVERTED YET - the batch is dry by default.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
