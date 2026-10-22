# -*- coding: utf-8 -*-
"""convert_recipe_photos - give every recipe photo a light display copy.

    python manage.py convert_recipe_photos            DRY RUN
    python manage.py convert_recipe_photos --write    apply

DRY BY DEFAULT, AND THAT IS NOT A COURTESY. This writes files to the
media volume. The default run reports every recipe it would convert, the
bytes now and the bytes after, and --write is the only thing that turns
it into a write. The convention is backfill_task_rollup's, 20 Sep 2026,
and backfill_passport_holder's after it.

WHAT IT DOES. For each recipe with an original and no current display
copy, it re-encodes the original as JPEG and stores it in
recipe_images_display/. It never writes to recipe_images/ and never
deletes anything. The originals stay the masters.

SINCE PX-2, 21 Oct 2026, a photo under 1200px on the long edge is also
resampled UP with Lanczos and lightly sharpened, because the phone
hero asks for about 1170 real pixels and the browser was doing that
stretch itself, badly, on every page load. Nothing is ever shrunk.

    python manage.py convert_recipe_photos --rebuild --write

--rebuild is what you want after PX-2. Staleness is decided from the
FILENAMES and that round changed what a display copy CONTAINS without
changing its name, so a plain re-run would skip all 324 and report
success.

AND IT REALLY REPLACES THE FILE - SD-1, 22 Oct 2026. Until that round
it did not: Django storage does not overwrite, so each rebuild wrote
recipe-1-alpha-20261022063218_xUkNf5M.jpg beside the copy it meant to
replace, left the old one on the volume for ever, and left the row
permanently stale because staleness is a comparison of names. Running
it twice produced three JPEGs for one photo. See store_display_jpeg.

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

from django.core.management.base import BaseCommand

from pages.models import Recipe, make_display_jpeg, store_display_jpeg


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
            '--rebuild', action='store_true',
            help='Convert every photo, not only the ones whose display '
                 'copy is missing or stale. PX-2 changed what a display '
                 'copy CONTAINS without changing its name, and staleness '
                 'is decided from names - so a plain re-run after that '
                 'round would skip all 324 and report success. Since '
                 'SD-1 this really does replace the file rather than '
                 'writing a suffixed copy beside it.')
        parser.add_argument(
            '--quality', type=int, default=85,
            help='JPEG quality. Default 85, which Demetri reviewed '
                 'against real photos on 13 Oct 2026.')

    def handle(self, *args, **opts):
        write = opts['write']
        limit = opts['limit'] or 0
        quality = opts['quality']
        rebuild = opts.get('rebuild', False)

        done = skipped = failed = 0
        before = after = 0
        problems = []
        written = []

        qs = Recipe.objects.exclude(recipe_image='').exclude(
            recipe_image=None).order_by('recipe_id')

        self.stdout.write('')
        self.stdout.write('  %-6s %-34s %9s %9s'
                          % ('id', 'recipe', 'now', 'after'))
        self.stdout.write('  ' + '-' * 62)

        for recipe in qs.iterator():
            if limit and done + skipped >= limit:
                break
            if not rebuild and not recipe.display_copy_is_stale():
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
                # SD-1, 22 Oct 2026 - THROUGH THE ONE PLACE THAT STORES
                # ONE. This used to call field.save() directly and get
                # back a suffixed name on every rebuild, because Django
                # storage does not overwrite. A rebuild of 324 photos
                # left 324 orphans and 324 permanently stale rows.
                landed = store_display_jpeg(recipe, data)
                Recipe.objects.filter(pk=recipe.pk).update(
                    recipe_image_display=recipe.recipe_image_display.name)
                if not landed:
                    problems.append(
                        (recipe.recipe_id, recipe.recipe_name,
                         'stored as %s, which is not the name a rebuild '
                         'can recognise'
                         % os.path.basename(
                             recipe.recipe_image_display.name)))
                # DP-1, 22 Oct 2026 - REMEMBER WHAT WAS CLAIMED, so it
                # can be read back below. The name and the byte count
                # are what this run says it wrote; the database and the
                # volume are asked afterwards whether that is true.
                written.append((recipe.recipe_id, recipe.recipe_name,
                                recipe.recipe_image_display.name,
                                len(data)))

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
        else:
            self.report_what_landed(written)
        self.stdout.write('')

    # ----------------------------------------------------------------
    # DP-1, 22 Oct 2026 - ABSENCE IS NOT A REPORT.
    #
    # Demetri ran this with --write on 22 October and got back exactly
    # the table the dry run had printed, with the 'DRY RUN. Nothing was
    # written' line simply gone. Nothing said what had landed, nothing
    # said how big it was, and nothing would have said a word if the
    # save had silently failed.
    #
    # SO THE ROWS ARE READ BACK, not remembered. Each one is fetched
    # fresh from the database and its file measured on the volume. A
    # row whose display copy is not the name this run saved, or whose
    # file is not the size this run encoded, is named rather than
    # counted.
    # ----------------------------------------------------------------
    def report_what_landed(self, written):
        if not written:
            self.stdout.write('  WRITE RUN. Nothing needed writing - '
                              'every display copy was already current.')
            self.stdout.write('  Pass --rebuild to convert them anyway.')
            return

        confirmed = 0
        on_disk = 0
        wrong = []
        for rid, name, stored, claimed in written:
            row = Recipe.objects.filter(pk=rid).first()
            if row is None or row.recipe_image_display.name != stored:
                wrong.append((rid, name, 'the database does not point at '
                                         'the file this run saved'))
                continue
            try:
                size = row.recipe_image_display.size
            except Exception as exc:
                wrong.append((rid, name, 'not readable on the volume - %s'
                              % str(exc).split('\n')[0][:48]))
                continue
            on_disk += size
            if size != claimed:
                wrong.append((rid, name, 'on disk as %d bytes, encoded as '
                                         '%d' % (size, claimed)))
            else:
                confirmed += 1

        self.stdout.write('  WRITTEN. %d display cop%s read back from the '
                          'database' % (confirmed,
                                        'y' if confirmed == 1 else 'ies'))
        self.stdout.write('           and measured on the volume - '
                          '%.1f MB.' % (on_disk / 1048576.0))
        if wrong:
            self.stdout.write('')
            self.stdout.write('  DID NOT LAND AS CLAIMED - named, not '
                              'swallowed:')
            for rid, name, why in wrong[:20]:
                self.stdout.write('    %-6s %-30s %s'
                                  % (rid, (name or '')[:30], why))
