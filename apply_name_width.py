# -*- coding: utf-8 -*-
"""apply_name_width.py - round NL-1, 22 Oct 2026.

A GENERATED NAME DID NOT FIT THE COLUMN IT WAS STORED IN.

Found on Live on 22 October, in the run that rebuilt 335 display
copies. Four of them came back named like this:

    229  stored as recipe-new-potato-swirls-with-parmesan-cumin-and-smoky-paprika-202_rRTWxeC.jpg
    248  stored as recipe-248-pork-shoulder-deboned-rind-off-oven-and-gas-braai-20260_ZrMplqr.jpg
    249  stored as recipe-249-pork-shoulder-deboned-rind-off-weber-coal-braai-updated_oK6zykl.jpg
    330  stored as recipe-330-chicken-thighs-marsala-mediterranean-with-olives-and-to_8BzeTlF.jpg

LOOK AT WHERE THE TIMESTAMPS STOP. `-202`. `-20260`. These names are
CUT OFF MID-TIMESTAMP and then carry a random seven-character suffix.

THAT IS NOT COLLISION SUFFIXING, WHICH SD-1 FIXED YESTERDAY. SD-1
deletes the target path before writing it, so nothing is in the way.
This is `max_length`. An ImageField defaults to 100 characters,
`recipe_images_display/` spends 22 of them, and the four recipes with
the longest names generate a filename that does not fit. Django's
get_available_name truncates the stem to make room AND adds a suffix,
even when the path is free.

AND IT MEANS SD-1 IS INCOMPLETE. display_copy_is_stale compares the
stored name with display_name_for(original) - deliberately, so that
there is no column to forget to clear. A truncated, suffixed name can
NEVER equal that. So those four rows are permanently stale, and
permanently stale means Recipe.save() rebuilds the display copy on
every edit and leaves another orphan each time. Four recipes quietly
manufacturing rubbish for as long as they are used.

store_display_jpeg DID report it rather than hoping - the check SD-1
added returned False and the command printed all four. The round
worked. The column was too narrow.

TWO HALVES, AND BOTH ARE NEEDED.

WIDER COLUMNS. recipe_image, recipe_image_display and step_image go to
255. That is the half that makes the four heal: once the name fits,
the next rebuild stores it under the name display_name_for implies and
the rows stop being stale.

AND SHORTER NAMES. A column that merely has more room is a column
somebody will fill. The three upload-path functions bound the slug to
60 characters, so a generated basename is about 100 whatever the
recipe is called - comfortably inside 255, and inside 100 too, which
means a tree that somehow misses the migration still behaves.

A MIGRATION, WHICH DEPLOYS RUN BY THEMSELVES. Three AlterField, no
data touched. The files on the volume are not renamed and do not need
to be: the four stale rows are repaired by a rebuild, which is a
command Demetri runs when he wants to, not a side effect of a deploy.

AND THE DETECTOR LEARNS THE QUESTION. check_recipe_files asks about
MISSING, SHARED and ORPHANED files. None of those three sees a stale
display copy - the file is there, one row names it, nothing is loose.
It is a fourth kind of wrong and it now has a fourth heading.

Idempotent. Every file backed up to .bak_namewidth.
"""
import os
import re
import sys

SUFFIX = '.bak_namewidth'
MODELS = os.path.join('pages', 'models.py')
CHECKER = os.path.join('pages', 'management', 'commands',
                       'check_recipe_files.py')
MIG = os.path.join('pages', 'migrations', '0102_nl1_name_width.py')
PS1 = 'Push-PendingChanges.ps1'
MEALDROP = 'test_meal_drop.py'
ME = 'test_name_width.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'NL-1, 22 Oct 2026'
CHECK = False

# THE MIGRATION IS WRITTEN BY THIS ROUND, so it ships with it rather
# than being makemigrations' guess on somebody's laptop.
CREATES = (MIG,)

# A GENERATED BASENAME STAYS WELL INSIDE EVEN THE OLD WIDTH.
SLUG_CAP = 40

# ==========================================================================
# WIDER COLUMNS
# ==========================================================================
F1_WAS = '''    recipe_image = models.ImageField(upload_to=recipe_image_upload_path, blank=True, null=True)'''

F1_NOW = '''    # NL-1, 22 Oct 2026 - 255, NOT THE DEFAULT 100. Four recipes on
    # Live generated a display name that did not fit, and Django
    # truncated the stem mid-timestamp and suffixed it, which left
    # them permanently stale. See apply_name_width.
    recipe_image = models.ImageField(upload_to=recipe_image_upload_path, blank=True, null=True, max_length=255)'''

F2_WAS = '''    recipe_image_display = models.ImageField(
        upload_to=recipe_display_upload_path, blank=True, null=True,
        editable=False,'''

F2_NOW = '''    recipe_image_display = models.ImageField(
        upload_to=recipe_display_upload_path, blank=True, null=True,
        editable=False,
        # NL-1, 22 Oct 2026 - AND THIS IS THE ONE THAT OVERFLOWED.
        # recipe_images_display/ is 22 characters before the filename
        # starts, which is why this field hit the limit and
        # recipe_images/ did not.
        max_length=255,'''

F3_WAS = '''    step_image = models.ImageField(upload_to=instruction_image_upload_path, blank=True, null=True)'''

F3_NOW = '''    # NL-1, 22 Oct 2026 - 255, for the same reason as the other two.
    # No step image has overflowed yet; this one is widened because a
    # rule that holds for two of three fields is a rule somebody will
    # trip over on the third.
    step_image = models.ImageField(upload_to=instruction_image_upload_path, blank=True, null=True, max_length=255)'''

# ==========================================================================
# AND SHORTER NAMES
# ==========================================================================
U1_WAS = '''def recipe_image_upload_path(instance, filename):
    """Generate upload path for recipe images"""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')'''

U1_NOW = '''def recipe_image_upload_path(instance, filename):
    """Where a recipe's uploaded photo lives.

    THE SLUG IS BOUNDED - NL-1, 22 Oct 2026. Unbounded, a long recipe
    name generates a filename that does not fit the column, and Django
    truncates the stem and adds a random suffix rather than refusing.
    Four recipes on Live were left permanently stale that way, because
    display_copy_is_stale compares names and a truncated name can
    never match. NAME_SLUG_CAP keeps a generated basename near 100
    characters whatever the recipe is called.
    """
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')[:NAME_SLUG_CAP]'''

U2_WAS = '''def instruction_image_upload_path(instance, filename):
    """Generate upload path for instruction step images"""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe.recipe_name or 'recipe')'''

U2_NOW = '''def instruction_image_upload_path(instance, filename):
    """Where a step photo lives. Slug bounded - NL-1, 22 Oct 2026."""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe.recipe_name or 'recipe')[:NAME_SLUG_CAP]'''

U3_WAS = '''def recipe_document_upload_path(instance, filename):
    """Generate upload path for recipe documents"""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')'''

U3_NOW = '''def recipe_document_upload_path(instance, filename):
    """Where a recipe's document lives. Slug bounded - NL-1, 22 Oct 2026."""
    ext = filename.split('.')[-1]
    recipe_name_slug = slugify(instance.recipe_name or 'recipe')[:NAME_SLUG_CAP]'''

CAP_WAS = '''def recipe_image_upload_path(instance, filename):'''

CAP_NOW = '''# HOW MUCH OF A RECIPE NAME GOES INTO A FILENAME - NL-1, 22 Oct 2026.
#
# A generated basename is recipe-{id}-{slug}-{14 digit stamp}.{ext}:
# 'recipe-' is 7, a six digit id is 6, two hyphens are 2, the stamp is
# 14, and '.jpeg' is 5 - 34 characters before any of the name. The
# longest directory, 'recipe_images_display/', is 22 more.
#
# 40 IS NOT A ROUND NUMBER, IT IS THE ONE THAT FITS. 40 + 34 + 22 = 96,
# inside the 255 the fields now hold AND inside the 100 they used to,
# so a tree that has somehow not run the migration still behaves
# rather than silently truncating. The first draft said 60, which is
# 116, and the gate below refused the round - correctly.
#
# The filename is not shown to anybody. A recipe called 'Pork Shoulder
# (Deboned, Rind-off) - Oven and Gas Braai' losing its last few words
# HERE costs nothing; losing its display copy cost four recipes a
# rebuild on every edit.
#
# A module constant and not a literal inside three functions, so a
# suite can read it and so the three agree by construction.
NAME_SLUG_CAP = %d


def recipe_image_upload_path(instance, filename):''' % SLUG_CAP

# ==========================================================================
# AND THE DETECTOR LEARNS THE FOURTH QUESTION
# ==========================================================================
C_WAS = '''        missing = []
        shared = []
        orphans = []'''

C_NOW = '''        missing = []
        shared = []
        orphans = []
        # NL-1, 22 Oct 2026 - A FOURTH KIND OF WRONG. A display copy
        # whose name is not the name its original implies is not
        # missing, not shared and not orphaned: the file is there, one
        # row names it, nothing is loose. It is STALE, and stale means
        # Recipe.save() rebuilds it on every edit and orphans another
        # file each time. Four recipes on Live were in this state and
        # none of the three questions above could see them.
        stale = []'''

C2_WAS = '''            for name in sorted(disk - set(held)):
                orphans.append((field_name, name))'''

C2_NOW = '''            for name in sorted(disk - set(held)):
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
                                      or '(none)'))'''

C3_WAS = '''        if orphans:
            self.stdout.write(
                '  ORPHANS - on the volume, named by nothing. Not deleted:')
            for field_name, name in orphans:
                self.stdout.write('    %-22s %s' % (field_name, name))

        self.stdout.write('')
        self.stdout.write('  missing %d   shared %d   orphans %d'
                          % (len(missing), len(shared), len(orphans)))

        if missing or shared:'''

C3_NOW = '''        if stale:
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

        if missing or shared or stale:'''

# ==========================================================================
# AND MX-1's CLAIM STOPS NAMING A PARTICULAR MIGRATION
# ==========================================================================
# test_meal_drop requires the migration graph to have ONE leaf and for
# that leaf to be 0101. The invariant it cares about is the ONE - two
# leaves is a branched history and Railway refuses to migrate it. The
# NAME was incidental, and it was only ever going to be true until the
# next migration, which is this one.
#
# PRINT THE MEASUREMENT, ASSERT THE SHAPE. The same lesson as the
# planter ceiling on 21 October and the 324 photo count this morning:
# a number that was measured once is a claim about that one moment.
# The leaf is still printed, so a branched history is still readable
# at a glance; what is ASSERTED is that there is exactly one of it.
MX_WAS = '''    ok(leaves == [('pages', '0101_drop_meal_plan')],
       'the migration graph has ONE leaf and it is 0101 - a second leaf '
       'is a branched history and the deploy refuses it', leaves)'''

MX_NOW = '''    # ONE LEAF, NOT ONE NAMED LEAF - NL-1, 22 Oct 2026. This read
    # == [('pages', '0101_drop_meal_plan')] and so it failed the day a
    # migration was added, which NL-1 does. The branched history is
    # what Railway refuses; which migration happens to be last is not
    # this suite's business. The leaf is still PRINTED.
    ok(len(leaves) == 1,
       'the migration graph has exactly ONE leaf - a second leaf is a '
       'branched history and the deploy refuses it', leaves)
    ok(leaves and leaves[0][0] == 'pages',
       '  and it belongs to pages', leaves)'''

C4_WAS = '''EXIT CODE. Non-zero when anything MISSING or SHARED is found, zero
otherwise - orphans alone do not fail. That is what lets the suite run
it as a gate rather than read its output and guess.'''


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('NL-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


MIGRATION = '''# -*- coding: utf-8 -*-
"""NL-1, 22 Oct 2026 - a generated name fits the column it is stored in.

Three AlterField, 100 -> 255. No data is touched and no file on the
volume is renamed. The four rows left permanently stale by the old
width are repaired by `manage.py convert_recipe_photos --rebuild
--write`, which is a command somebody runs on purpose rather than a
side effect of a deploy.
"""
from django.db import migrations, models

import pages.models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '%s'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='recipe_image',
            field=models.ImageField(
                blank=True, max_length=255, null=True,
                upload_to=pages.models.recipe_image_upload_path),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='recipe_image_display',
            field=models.ImageField(
                blank=True, editable=False, max_length=255, null=True,
                help_text='Derived JPEG of recipe_image. Rebuilt by '
                          'manage.py convert_recipe_photos --write.',
                upload_to=pages.models.recipe_display_upload_path),
        ),
        migrations.AlterField(
            model_name='recipeinstruction',
            name='step_image',
            field=models.ImageField(
                blank=True, max_length=255, null=True,
                upload_to=pages.models.instruction_image_upload_path),
        ),
    ]
'''


def latest_migration(root):
    """The migration this one depends on, READ OFF DISK.

    Typed, it is a guess that is wrong the moment somebody adds one.
    """
    d = os.path.join(root, 'pages', 'migrations')
    names = sorted(n[:-3] for n in os.listdir(d)
                   if n.endswith('.py') and n != '__init__.py'
                   and '.bak_' not in n)
    if not names:
        refuse('pages/migrations holds no migration to depend on')
    return names[-1]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pm = os.path.join(root, MODELS)
    m = read(pm)
    if MARK in m:
        print('NL-1  already applied - a generated name fits its column.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # SI-1 GOES FIRST IN THIS PUSH. This round edits the detector SI-1
    # brings with it, and registers after SI-1's own entries.
    pk = os.path.join(root, CHECKER)
    if not os.path.isfile(pk):
        refuse('%s is not on disk - SI-1 brings it, and this round '
               'teaches it a fourth question' % CHECKER)
    ptr = os.path.join(root, TREE)
    if "'test_shared_image.py'" not in read(ptr):
        refuse('%s: SI-1 is not applied, and NL-1 registers after it '
               'in this push' % TREE)

    m = swap(m, CAP_WAS, CAP_NOW, '%s (the cap)' % MODELS)
    m = swap(m, U1_WAS, U1_NOW, '%s (the photo path)' % MODELS)
    m = swap(m, U2_WAS, U2_NOW, '%s (the step path)' % MODELS)
    m = swap(m, U3_WAS, U3_NOW, '%s (the document path)' % MODELS)
    m = swap(m, F1_WAS, F1_NOW, '%s (recipe_image)' % MODELS)
    m = swap(m, F2_WAS, F2_NOW, '%s (recipe_image_display)' % MODELS)
    m = swap(m, F3_WAS, F3_NOW, '%s (step_image)' % MODELS)
    out[pm] = m

    c = read(pk)
    c = swap(c, C_WAS, C_NOW, '%s (the fourth list)' % CHECKER)
    c = swap(c, C2_WAS, C2_NOW, '%s (the fourth question)' % CHECKER)
    c = swap(c, C3_WAS, C3_NOW, '%s (the fourth heading)' % CHECKER)
    c = swap(c, C4_WAS, C4_WAS.replace(
        'anything MISSING or SHARED is found',
        'anything MISSING, SHARED or STALE is found'),
        '%s (the docstring)' % CHECKER)
    out[pk] = c

    # AND MX-1'S LEAF CLAIM STOPS NAMING A PARTICULAR MIGRATION.
    pmx = os.path.join(root, MEALDROP)
    out[pmx] = swap(read(pmx), MX_WAS, MX_NOW,
                    '%s (the one leaf)' % MEALDROP)

    # ---- THE MIGRATION
    pg = os.path.join(root, MIG)
    if not CHECK:
        if not os.path.exists(pg):
            write_file(pg, MIGRATION % latest_migration(root))

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_shared_image.py'
)""", """    'test_shared_image.py',
    # NL-1, 22 Oct 2026 - a generated name fits the column it is
    # stored in, and the names got shorter as well as the column wider.
    'test_name_width.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/models.py'; Text = 'NAME_SLUG_CAP'; What = 'NL-1: four recipes on Live generated a display filename longer than the 100-character column, and Django truncated the stem mid-timestamp and added a random suffix rather than refusing - which left them permanently stale, because display_copy_is_stale compares names. The columns are 255 and the slug is bounded, so both halves have to fail before it can happen again' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    out[ptr] = swap(read(ptr), """    # SI-1, 22 Oct 2026 - a copied recipe does not share its photo.
    'test_shared_image.py',
]""", """    # SI-1, 22 Oct 2026 - a copied recipe does not share its photo.
    'test_shared_image.py',
    # NL-1, 22 Oct 2026 - a generated name fits the column.
    'test_name_width.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_sharedimage',
]""", """    '.bak_sharedimage',
    # NL-1, 22 Oct 2026 - a generated name fits the column.
    '.bak_namewidth',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # NL-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nm = T.python_code_only(out[pm], payloads=True)

    # ALL THREE FIELDS, OR NONE. A round that widens two of three
    # leaves the third as the one that overflows next.
    if nm.count('max_length=255') < 3:
        refuse('%s: only %d field(s) widened, and there are three'
               % (MODELS, nm.count('max_length=255')))

    # AND ALL THREE PATHS BOUNDED. A wider column that somebody fills
    # is the same fault with more room.
    if nm.count('[:NAME_SLUG_CAP]') != 3:
        refuse('%s: %d upload path(s) bound the slug, and there are '
               'three' % (MODELS, nm.count('[:NAME_SLUG_CAP]')))
    if 'NAME_SLUG_CAP = ' not in nm:
        refuse('%s: the cap is a literal in three places rather than '
               'one constant the three share' % MODELS)

    # THE BOUND MUST LEAVE THE OLD WIDTH SAFE TOO. 'recipe-' + a six
    # digit id + two hyphens + a 14 digit stamp + '.jpeg' is 34, and
    # 'recipe_images_display/' is 22.
    if SLUG_CAP + 34 + 22 > 100:
        refuse('a %d character slug still overflows the OLD 100 '
               'character column, so a tree that misses the migration '
               'would go on truncating' % SLUG_CAP)

    # THE MIGRATION MUST NOT INVENT ITS OWN DEPENDENCY.
    if not CHECK:
        g = read(pg)
        # THE CALL, NOT THE WORD. The first version of this counted
        # 'AlterField' and found four, because the migration's own
        # docstring says what it does - and refused the round for it.
        if g.count('migrations.AlterField(') != 3:
            refuse('%s: expected three AlterField calls, counted %d'
                   % (MIG, g.count('migrations.AlterField(')))
        for banned in ('RunPython', 'RunSQL', 'DeleteModel',
                       'RemoveField'):
            if banned in g:
                refuse('%s names %r. This migration widens three '
                       'columns and touches no data' % (MIG, banned))

    nc = T.python_code_only(out[pk], payloads=True)
    if 'display_copy_is_stale()' not in nc:
        refuse('%s: the stale question re-implements the comparison '
               'instead of asking the model that owns it' % CHECKER)
    if 'if missing or shared or stale:' not in nc:
        refuse('%s: a stale row does not fail the detector, so the '
               'gate would pass a tree with four of them' % CHECKER)

    if CHECK:
        print('NL-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        plus %s, which this round CREATES' % MIG)
        print('        a generated name fits the column it is stored in')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('NL-1  applied - a generated name fits the column it is '
          'stored in.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      plus %s, which this round CREATES' % MIG)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
