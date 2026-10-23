# -*- coding: utf-8 -*-
"""check_recipe_files.py - SI-1, 22 Oct 2026.

ASK THE DISK WHETHER THE FILES ARE THERE.

On 22 October a rebuild of 335 recipe photos on Live named two it
could not read:

    71     Cottage Pie                 recipe_images/recipe-cottage-pie-20260213.png
    336    Beans, Edamame - Frozen     recipe_images/recipe-336-beans-edamame-frozen-20261018152727.png

Neither file was on the volume. Both rows had pointed at a file that a
DUPLICATE of the recipe later deleted - see SI-1 in apply_shared_image
for the mechanism - and both recipes had been showing a broken image
for months. Nothing said so. The rebuild only found them because it
happened to open every file, which is luck, not instrumentation.

THIS IS THE INSTRUMENT. It asks three questions of the three image
fields a recipe owns, and answers each by asking the STORAGE rather
than by reasoning about names:

  MISSING  a row names a path and the storage says nothing is there.
           The screen shows a broken image. This is damage.

  SHARED   two or more rows name the SAME path. No damage yet, and
           that is the point: a share is the state a recipe sits in
           between being duplicated and having its photo changed, and
           changing the photo is what destroys the other row's file.
           A share is a fault that has not gone off.

  ORPHAN   a file on the volume that no row names. Harmless, costs
           disk, and is the same drift running the other way.

IT DELETES NOTHING, and it is not given a --write. Demetri declined
one on 22 October and he was right to: a tool that deletes files off a
media volume is a different risk class from a tool that counts them,
and the three strays it finds today are worth less than the certainty
that this command can never be the thing that lost a photo.

EXIT CODE. Non-zero when anything MISSING, SHARED or STALE is found, zero
otherwise - orphans alone do not fail. That is what lets the suite run
it as a gate rather than read its output and guess.
"""
import os

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from pages.models import Recipe, RecipeInstruction


# THE THREE FIELDS A RECIPE'S PICTURES LIVE IN, and the directory each
# one writes into. The directory is named here rather than derived from
# a sample row, because a field with no rows at all still has a
# directory that can hold orphans.
FIELDS = (
    (Recipe, 'recipe_image', 'recipe_images'),
    (Recipe, 'recipe_image_display', 'recipe_images_display'),
    (RecipeInstruction, 'step_image', 'recipe_instructions'),
)


def label(model, row):
    """How a row is named in a report, so a person can go and look."""
    if model is Recipe:
        return '%s  %s' % (str(row.pk).ljust(6), row.recipe_name or '?')
    return '%s  %s step %s' % (str(row.pk).ljust(6),
                               row.recipe.recipe_name or '?',
                               row.step_number)


def held_names(model, field_name):
    """(name -> [rows]) for every row of this model that names a file."""
    out = {}
    for row in model.objects.all():
        field = getattr(row, field_name, None)
        name = getattr(field, 'name', None)
        if name:
            out.setdefault(name, []).append(row)
    return out


def on_disk(folder):
    """Every file the storage holds in this folder, as relative names."""
    try:
        _dirs, files = default_storage.listdir(folder)
    except Exception:
        # A FOLDER THAT IS NOT THERE HOLDS NOTHING, which is true and
        # is not an error - a fresh volume has no recipe_instructions
        # directory until the first step photo is uploaded.
        return set()
    return set(os.path.join(folder, f).replace('\\', '/') for f in files)


class Command(BaseCommand):
    help = ('Report recipe image files that are missing, shared by more '
            'than one row, or on the volume with nothing pointing at '
            'them. Writes nothing and deletes nothing. SI-1.')

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet', action='store_true',
            help='Print only the counts and the faults, not the clean lines.')

    def handle(self, *args, **options):
        quiet = options.get('quiet')
        missing = []
        shared = []
        orphans = []
        # NL-1, 22 Oct 2026 - A FOURTH KIND OF WRONG. A display copy
        # whose name is not the name its original implies is not
        # missing, not shared and not orphaned: the file is there, one
        # row names it, nothing is loose. It is STALE, and stale means
        # Recipe.save() rebuilds it on every edit and orphans another
        # file each time. Four recipes on Live were in this state and
        # none of the three questions above could see them.
        stale = []

        for model, field_name, folder in FIELDS:
            held = held_names(model, field_name)
            disk = on_disk(folder)

            for name, rows in sorted(held.items()):
                if not default_storage.exists(name):
                    for row in rows:
                        missing.append((field_name, label(model, row), name))
                if len(rows) > 1:
                    shared.append((field_name, name,
                                   [label(model, r) for r in rows]))

            for name in sorted(disk - set(held)):
                orphans.append((field_name, name))

            # ASKED OF THE MODEL, NOT OF THE NAME. display_copy_is_stale
            # is where that comparison lives and it is not re-implemented
            # here - a second copy of the rule is a second thing to keep
            # in agreement with the first.
            if model is Recipe and field_name == 'recipe_image_display':
                for row in model.objects.all():
                    if row.recipe_image and row.display_copy_is_stale():
                        stale.append((label(model, row),
                                      row.recipe_image_display.name
                                      or '(none)'))

            if not quiet:
                self.stdout.write(
                    '  %-22s %4d row(s) with a file, %4d file(s) in %s'
                    % (field_name, len(held), len(disk), folder))

        self.stdout.write('')
        if missing:
            self.stdout.write(self.style.ERROR(
                '  MISSING - the row points at a file that is not there:'))
            for field_name, who, name in missing:
                self.stdout.write('    %-22s %s' % (field_name, who))
                self.stdout.write('      %s' % name)
        if shared:
            self.stdout.write(self.style.ERROR(
                '  SHARED - one file, more than one row. Changing the '
                'photo on either destroys it for the other:'))
            for field_name, name, who in shared:
                self.stdout.write('    %-22s %s' % (field_name, name))
                for one in who:
                    self.stdout.write('      %s' % one)
        if stale:
            self.stdout.write(self.style.ERROR(
                '  STALE - the display copy is not the name its original '
                'implies, so save() rebuilds it on every edit:'))
            for who, name in stale:
                self.stdout.write('    %s' % who)
                self.stdout.write('      %s' % name)
        if orphans:
            self.stdout.write(
                '  ORPHANS - on the volume, named by nothing. Not deleted:')
            for field_name, name in orphans:
                self.stdout.write('    %-22s %s' % (field_name, name))

        self.stdout.write('')
        self.stdout.write('  missing %d   shared %d   stale %d   orphans %d'
                          % (len(missing), len(shared), len(stale),
                             len(orphans)))

        if missing or shared or stale:
            # NON-ZERO, so a gate can ASK rather than parse. Orphans
            # alone are not a failure: they cost disk and nothing else.
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(
            '  OK every recipe image file is where its row says it is.'))
