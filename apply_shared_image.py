# -*- coding: utf-8 -*-
"""apply_shared_image.py - round SI-1, 22 Oct 2026.

A COPIED RECIPE SHARES ITS PHOTO, AND CHANGING ONE DESTROYS THE OTHER.

Found on 22 October on Live, by a rebuild of 335 photos that named two
it could not read:

    71     Cottage Pie                 recipe_images/recipe-cottage-pie-20260213.png
    336    Beans, Edamame - Frozen     recipe_images/recipe-336-beans-edamame-frozen-20261018152727.png

Neither file was on the volume. Demetri recognised the shape at once:
"These were recipes that I copied from other recipes and I then removed
the original image and uploaded a new image."

THE MECHANISM, WHICH IS FOUR LINES OF duplicate_recipe:

    original_recipe.pk = None
    original_recipe.recipe_id = None
    original_recipe.recipe_name = f"{original_recipe.recipe_name} (Copy)"
    original_recipe.save()

Setting pk to None and saving copies every field value, and an image
field's value IS JUST A PATH STRING. The copy does not get a picture;
it gets the original's address. Two rows, one file. Then the edit
screen's

    recipe.recipe_image.delete(save=False)

removes the bytes with no question asked about who else is pointing at
them, and the other recipe has been showing a broken image ever since.
The volume proved it: the only cottage file left on disk belongs to
329, Cottage Pie - Keto, which is the COPY. 71 is the source, and 71 is
the one that lost its photo.

IT IS NOT ONLY recipe_image. The same save copies recipe_image_display,
and the instruction loop passes step_image=inst.step_image straight into
the new rows. Three fields, one fault.

THREE PARTS, AND THE THIRD IS THE ONE THAT MATTERS.

ONE. THE COPY TAKES ITS OWN FILE. unshare_file reads the bytes and
saves them back through the field, which runs upload_to - and
recipe_image_upload_path builds the name from the NEW recipe's id and a
fresh timestamp, so a distinct name falls out without inventing a
naming scheme here.

The display copy is NOT copied. It is derived, so the copy simply
clears it, and display_copy_is_stale() returns True on an empty display
field, so the copy's own save() rebuilds it through SD-1's
store_display_jpeg under its own proper name. A derived thing should be
re-derived, not duplicated, and this reuses the round that shipped
yesterday rather than opening a second way to make one.

TWO. A DELETE ASKS WHO ELSE IS LOOKING, AND WAITS UNTIL THE SAVE IS
SAFE. It is a pair. let_go_of_file clears the reference and returns
the name, touching nothing; delete_unheld runs after recipe.save() has
committed and removes only the names no row still holds.

BOTH HALVES ANSWER A FAULT THAT WAS MEASURED. Counting first protects
the copies that ALREADY exist - part one does nothing for a pair made
last month. Waiting for the save answers the other one: edit_recipe
deleted the bytes and then called recipe.save(), so a save that failed
left the file gone and the row still naming it, which is the same
broken image arrived at from the other side. That was demonstrated on
22 October by a test POST missing difficulty_level - the except fired,
the redirect looked exactly like success, and the photo was already
destroyed.

On Live today that count is zero - asked on 22 October, 337 rows with
an image, 0 shared paths. That is not evidence the fault is rare. A
share only EXISTS between the duplicate and the next photo change, and
both known casualties went through that window and out the other side.
Zero means nobody is standing on the trapdoor right now.

AND THE DISPLAY COPY IS DROPPED WITH THE ORIGINAL. Removing or
replacing a recipe photo has never removed its display copy, so the old
one has stayed on the volume for ever. That is three of the orphans
counted on Live on 22 October - 338 files against 335 referenced - and
one line here closes the leak.

THREE. AN INSTRUMENT, SO THE NEXT ONE IS NOT FOUND BY LUCK.
check_recipe_files asks the storage three questions about the three
fields: which rows name a file that is not there, which path is named
by more than one row, and which file on the volume is named by nothing.
It exits non-zero on the first two so a gate can ASK rather than parse.

It has no --write and will not be given one. Demetri declined orphan
deletion on 22 October and was right to: a tool that deletes files off
a media volume is a different risk class from one that counts them, and
the three strays are worth less than the certainty that this command
can never be the thing that lost a photo.

THE REBUILD FOUND THIS AT ALL ONLY BECAUSE IT HAPPENS TO OPEN EVERY
FILE. That is luck. Part three is the replacement for luck.

NO MIGRATION. No field changes - SI-1 changes who writes what, not what
is stored.

Idempotent. Every file backed up to .bak_sharedimage.
"""
import os
import sys

SUFFIX = '.bak_sharedimage'
MODELS = os.path.join('pages', 'models.py')
CRUD = os.path.join('pages', 'views', 'recipes', 'recipe_crud.py')
CHECKER = os.path.join('pages', 'management', 'commands',
                       'check_recipe_files.py')
PS1 = 'Push-PendingChanges.ps1'
# test_sentinels' LIST OF ROWS THAT CANNOT YET DISCRIMINATE.
#
# A sentinel row on a file the round CREATES has no earlier version to
# be compared against, so it can never fail and test_sentinels says so
# - by name, in a list, with a reason. GT-2 was the seventh of these
# and RD-1 the eighth; this round's detector is the ninth. Adding it
# is how the mechanism is meant to be answered: the row stays, and the
# fact that it is blind is written down rather than discovered again.
SENTINELS = 'test_sentinels.py'
ME = 'test_shared_image.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'SI-1, 22 Oct 2026'
CHECK = False

# THE ROUND BRINGS THE DETECTOR WITH IT, the way LK-1 brought
# alv_plant.py. It is a file on disk rather than a string in here: a
# management command that is only ever read as a patcher payload is a
# command nobody can run while they are writing it.
CREATES = (CHECKER,)


# ==========================================================================
# THE THREE THINGS THAT KNOW ABOUT A SHARED FILE
# ==========================================================================
M_WAS = '''def display_name_for(original_name):'''

M_NOW = '''def file_holders(model, name, fields):
    """How many rows of this model name this file, across these fields.

    SI-1, 22 Oct 2026. Asked of the DATABASE, by exact path, because
    that is the only place the answer lives: a file on a media volume
    carries no record of who points at it.

    ACROSS FIELDS, not one field. A display copy's path can be named by
    recipe_image_display on any row, and asking about one field would
    answer 'nobody' while somebody was plainly standing there.
    """
    if not name:
        return 0
    total = 0
    for field_name in fields:
        total += model._default_manager.filter(**{field_name: name}).count()
    return total


def let_go_of_file(instance, field_name):
    """Clear the reference and return the name. DELETES NOTHING. SI-1.

    THE BYTES MUST OUTLIVE THE SAVE. edit_recipe used to call
    field.delete(save=False) and then recipe.save(), and a save that
    fails after that leaves the file gone and the row still naming it -
    which is exactly the MISSING state the 22 October rebuild found on
    Live. It was demonstrated on 22 October by a test POST that omitted
    difficulty_level: the except fired, the redirect looked like
    success, and the photo was already destroyed.

    So this half only lets go. delete_unheld does the other half, after
    the save has committed, and a failed save therefore costs nothing.
    """
    field = getattr(instance, field_name, None)
    name = getattr(field, 'name', None)
    if not name:
        return None
    setattr(instance, field_name, None)
    return name


def delete_unheld(model, names, fields):
    """Delete the bytes of each name no row still holds. SI-1.

    CALLED AFTER THE SAVE, never before - see let_go_of_file.

    AND IT COUNTS FIRST. A duplicated recipe used to share its photo
    path with the recipe it came from, so deleting on the strength of
    one row letting go destroyed the other row's picture. That is how
    71 Cottage Pie and 336 Beans, Edamame lost theirs.

    One name at a time, by exact path, asked of the storage. No
    pattern, no listing, no glob: a delete on a media volume that takes
    anything wider than a path is a delete nobody can bound.

    Returns the names whose bytes were removed. Never raises - a
    leftover file costs disk, and an exception here would lose the edit
    that has already been saved.
    """
    from django.core.files.storage import default_storage

    gone = []
    for name in [n for n in names if n]:
        if file_holders(model, name, fields):
            # SOMEBODY ELSE IS STANDING ON IT. The last row out turns
            # off the light.
            continue
        try:
            if default_storage.exists(name):
                default_storage.delete(name)
                gone.append(name)
        except Exception:
            pass
    return gone


def unshare_file(instance, field_name):
    """Give this row its OWN copy of the file its field names. SI-1.

    For a row made by copying another - duplicate_recipe sets pk to
    None and saves, which copies the PATH, not the picture.

    THE NEW NAME IS NOT INVENTED HERE. The bytes are saved back through
    the field, which runs upload_to, and recipe_image_upload_path
    builds its name from the row's own id and a fresh timestamp. A
    second naming scheme in this function is a second thing to keep in
    agreement with display_name_for.

    Returns True when the field now names a file of its own. On a file
    that cannot be read the field is CLEARED and False returned: a row
    pointing at nothing is honest, and leaving it pointing at somebody
    else's file is the fault this round exists to end.
    """
    from django.core.files.base import ContentFile

    field = getattr(instance, field_name, None)
    old = getattr(field, 'name', None)
    if not old:
        return False
    try:
        field.open('rb')
        data = field.read()
    except Exception:
        setattr(instance, field_name, None)
        return False
    finally:
        try:
            field.close()
        except Exception:
            pass
    field.save(os.path.basename(old), ContentFile(data), save=False)
    return field.name != old


def display_name_for(original_name):'''

# ==========================================================================
# THE COPY TAKES ITS OWN FILES
# ==========================================================================
D_WAS = '''            original_recipe.save()

            new_recipe_id = original_recipe.recipe_id'''

D_NOW = '''            original_recipe.save()

            # SI-1, 22 Oct 2026 - THE COPY TAKES ITS OWN FILES.
            #
            # pk = None and save() copied the field VALUES, and an
            # image field's value is a path. Until these two lines run,
            # this recipe and the one it was copied from are pointing
            # at one file, and whichever of them changes its photo
            # first deletes the other's. That is how 71 Cottage Pie and
            # 336 Beans, Edamame lost theirs.
            #
            # AFTER THE SAVE, NOT BEFORE: recipe_image_upload_path
            # builds the name from recipe_id, which does not exist
            # until the row does. Hence the second save below.
            #
            # THE DISPLAY COPY IS CLEARED RATHER THAN COPIED. It is
            # derived from the original, and an empty display field
            # makes display_copy_is_stale() true, so the save below
            # rebuilds it through SD-1's store_display_jpeg under this
            # recipe's own proper name.
            unshare_file(original_recipe, 'recipe_image')
            original_recipe.recipe_image_display = None
            original_recipe.save()

            new_recipe_id = original_recipe.recipe_id'''

I_WAS = '''            if new_instructions:
                RecipeInstruction.objects.bulk_create(new_instructions)'''

I_NOW = '''            if new_instructions:
                RecipeInstruction.objects.bulk_create(new_instructions)

            # SI-1, 22 Oct 2026 - AND THE STEP PHOTOS TOO. The list
            # above passes step_image=inst.step_image, which is the
            # same path-copying fault one level down.
            #
            # RE-QUERIED RATHER THAN USING new_instructions: bulk_create
            # does not set primary keys on MySQL, so the objects in that
            # list cannot be saved back. The rows on disk can.
            for fresh in RecipeInstruction.objects.filter(
                    recipe=original_recipe):
                if fresh.step_image and unshare_file(fresh, 'step_image'):
                    fresh.save(update_fields=['step_image'])'''

# ==========================================================================
# AND A DELETE ASKS FIRST
# ==========================================================================
R_WAS = '''            # Image handling
            if request.POST.get('remove_image') == '1':
                if recipe.recipe_image:
                    recipe.recipe_image.delete(save=False)
                    recipe.recipe_image = None

            if 'recipe_image' in request.FILES:
                if recipe.recipe_image:
                    recipe.recipe_image.delete(save=False)
                recipe.recipe_image = request.FILES['recipe_image']'''

R_NOW = '''            # Image handling
            #
            # SI-1, 22 Oct 2026 - NOTHING IS DELETED HERE ANY MORE.
            #
            # Both branches used to call recipe_image.delete(save=False),
            # which destroyed the bytes immediately and asked nothing
            # about who else was pointing at them. Two faults in one
            # line. A duplicate of this recipe shares the path, so the
            # delete took ITS photo too - that is how 71 Cottage Pie and
            # 336 Beans, Edamame lost theirs. And the delete happened
            # BEFORE recipe.save(), so a save that failed left the file
            # gone and the row still naming it, which is the same
            # broken-image state arrived at from the other direction.
            #
            # So this half only lets go, and remembers what it let go
            # of. The bytes are dealt with after the save commits.
            #
            # AND THE DISPLAY COPY GOES WITH THE ORIGINAL. Neither
            # branch has ever released it, so every removed or replaced
            # photo has left its shrunken twin on the volume for ever.
            # On a replace, save() rebuilds a fresh one from the new
            # upload; on a removal there is nothing left to display.
            released = []
            if request.POST.get('remove_image') == '1':
                if recipe.recipe_image:
                    released.append(let_go_of_file(recipe, 'recipe_image'))
                    released.append(
                        let_go_of_file(recipe, 'recipe_image_display'))

            if 'recipe_image' in request.FILES:
                if recipe.recipe_image:
                    released.append(let_go_of_file(recipe, 'recipe_image'))
                released.append(
                    let_go_of_file(recipe, 'recipe_image_display'))
                recipe.recipe_image = request.FILES['recipe_image']'''

S_WAS = '''            # Save recipe
            recipe.save()'''

S_NOW = '''            # Save recipe
            recipe.save()

            # SI-1, 22 Oct 2026 - AND ONLY NOW DO THE OLD BYTES GO.
            #
            # After the save, so a save that raises costs a leftover
            # file rather than a photo. Counting first, so a recipe
            # duplicated from this one keeps the picture it is still
            # pointing at. Both image fields are asked, because a
            # display copy's path is named by recipe_image_display.
            delete_unheld(Recipe, released,
                          ('recipe_image', 'recipe_image_display'))'''

SN_WAS = """    'ingredient_rows':
        'the shared recipe read, on a file RD-1 created - no earlier '
        'version exists to discriminate against',
}"""

SN_NOW = """    'ingredient_rows':
        'the shared recipe read, on a file RD-1 created - no earlier '
        'version exists to discriminate against',
    # THE NINTH, 22 Oct 2026, and the same story again. SI-1 pins
    # `def held_names` on check_recipe_files.py, which SI-1 CREATES,
    # so there is no earlier version and the row has one version to
    # try. It becomes checkable the moment any later round backs that
    # file up - which NL-1 does in this same push, but a round may not
    # assume the one after it applied.
    'held_names':
        'the recipe file detector, on a file SI-1 created - no earlier '
        'version exists to discriminate against',
}"""

IMP_WAS = '''    UnitConversion,
)'''

IMP_NOW = '''    UnitConversion,
    delete_unheld,
    let_go_of_file,
    unshare_file,
)'''


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
    raise SystemExit('SI-1 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pm = os.path.join(root, MODELS)
    m = read(pm)
    if MARK in m:
        print('SI-1  already applied - a copied recipe does not share '
              'its photo.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE DETECTOR IS A FILE, NOT A STRING IN HERE. If it is not on
    # disk this round registers a command that does not exist.
    pk = os.path.join(root, CHECKER)
    if not os.path.isfile(pk):
        refuse('%s is not on disk, and this round registers it' % CHECKER)

    # SD-1 PUT store_display_jpeg IN, AND THE COPY LEANS ON IT. Clearing
    # the display field is only a fix because something rebuilds it.
    if 'def store_display_jpeg' not in m:
        refuse('%s: SD-1 is not applied, and this round clears a display '
               'copy expecting SD-1 to rebuild it' % MODELS)

    # SB-2 GOES FIRST IN THIS PUSH. Its registration lines are what the
    # ones below anchor on, so a tree without it is a tree where this
    # round would silently register in the wrong place.
    ptr = os.path.join(root, TREE)
    if "'test_shop_bar2.py'" not in read(ptr):
        refuse('%s: SB-2 is not applied, and SI-1 registers after it '
               'in this push' % TREE)

    m = swap(m, M_WAS, M_NOW, '%s (the three helpers)' % MODELS)
    out[pm] = m

    pc = os.path.join(root, CRUD)
    c = read(pc)
    c = swap(c, IMP_WAS, IMP_NOW, '%s (the imports)' % CRUD)
    c = swap(c, D_WAS, D_NOW, '%s (the copy takes its own)' % CRUD)
    c = swap(c, I_WAS, I_NOW, '%s (and the step photos)' % CRUD)
    c = swap(c, R_WAS, R_NOW, '%s (nothing is deleted here)' % CRUD)
    c = swap(c, S_WAS, S_NOW, '%s (and only now do the bytes go)' % CRUD)
    out[pc] = c

    # AND THE BLIND ROW IS WRITTEN DOWN RATHER THAN LEFT TO BE FOUND.
    psn = os.path.join(root, SENTINELS)
    out[psn] = swap(read(psn), SN_WAS, SN_NOW,
                    '%s (the rows that cannot discriminate)' % SENTINELS)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_shop_bar2.py'
)""", """    'test_shop_bar2.py',
    # SI-1, 22 Oct 2026 - a copied recipe takes its own photo, and a
    # delete asks who else is holding the file.
    'test_shared_image.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'unshare_file(original_recipe'; What = 'SI-1: duplicate_recipe set pk to None and saved, which copies the PATH of the photo and not the photo - two rows, one file. Changing the picture on either then deleted it for the other, which is how 71 Cottage Pie and 336 Beans, Edamame lost theirs on Live' },
    @{ File = 'pages/models.py'; Text = 'def delete_unheld'; What = 'SI-1: and a delete counts the rows naming that path before it removes the bytes - the copies made BEFORE this round are the ones that line protects' },
    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'delete_unheld(Recipe, released'; What = 'SI-1: and it runs AFTER recipe.save(), not before. The old order deleted the photo and then saved, so a save that raised - a missing difficulty_level does it - left the file gone and the row still naming it, which is the same broken image from the other direction' },
    @{ File = 'pages/management/commands/check_recipe_files.py'; Text = 'def held_names'; What = 'SI-1: the instrument. Missing, shared and orphaned, asked of the storage rather than reasoned about - the rebuild found the first two by luck, which is not a detector' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    out[ptr] = swap(read(ptr), """    # SB-2, 22 Oct 2026 - one primary on the shopping bar.
    'test_shop_bar2.py',
]""", """    # SB-2, 22 Oct 2026 - one primary on the shopping bar.
    'test_shop_bar2.py',
    # SI-1, 22 Oct 2026 - a copied recipe does not share its photo.
    'test_shared_image.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_shopbar2',
]""", """    '.bak_shopbar2',
    # SI-1, 22 Oct 2026 - a copied recipe does not share its photo.
    '.bak_sharedimage',
]""", '%s (ROUNDS)' % ROUNDS)

    import re
    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # SI-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    #
    # check_gates says SI-1 is already named on disk. It is, in two
    # files, and both are this round's own: check_recipe_files.py,
    # which the round CREATES and which says in its docstring which
    # round brought it, and test_shared_image.py, which is the suite.
    # Neither is a second round wearing this name. The 18 October
    # collision that rule exists for was apply_compliance_tab using
    # PR-1 forty-five times since 3 October, which is a different
    # thing entirely.
    nm = T.python_code_only(out[pm], payloads=True)
    for want in ('def file_holders', 'def let_go_of_file',
                 'def delete_unheld', 'def unshare_file'):
        if want not in nm:
            refuse('%s: %s is not there' % (MODELS, want))

    # let_go_of_file MUST NOT DELETE. It is half of a pair, and the
    # whole point of the pair is that the bytes outlive the save.
    go = nm[nm.index('def let_go_of_file'):]
    nxt = re.search(r'\ndef \w+', go[1:])
    go = go[:nxt.start() + 1] if nxt else go
    if '.delete(' in go or 'storage' in go:
        refuse('%s: let_go_of_file touches the storage. It clears a '
               'reference and returns a name; deleting here is the '
               'fault that destroyed a photo when the save then failed'
               % MODELS)

    # delete_unheld MUST COUNT BEFORE IT DELETES. One that deletes
    # unconditionally is .delete(save=False) with a longer name, and
    # would ship looking like a fix.
    body = nm[nm.index('def delete_unheld'):]
    nxt = re.search(r'\ndef \w+', body[1:])
    body = body[:nxt.start() + 1] if nxt else body
    if 'file_holders(' not in body:
        refuse('%s: delete_unheld deletes without counting the rows '
               'that hold the file, which is the fault it exists to end'
               % MODELS)
    if body.index('file_holders(') > body.index('.delete('):
        refuse('%s: delete_unheld counts AFTER it deletes, which is not '
               'counting' % MODELS)
    if 'default_storage.exists(' not in body:
        refuse('%s: delete_unheld deletes without asking whether '
               'anything is there' % MODELS)

    # AND IT REACHES ONE FILE AT A TIME. Everything a media volume can
    # be walked with is refused here, as in SD-1.
    for reach in ('listdir', 'glob', 'walk', 'rmtree', 'os.remove',
                  'os.unlink', 'shutil'):
        if reach in body:
            refuse('%s: delete_unheld names %r, and it is allowed to '
                   'touch exactly one path at a time' % (MODELS, reach))

    # AND THE DELETE HAPPENS AFTER THE SAVE. This is the ordering the
    # whole second half of the round is about, so it is asked of the
    # text rather than assumed from the diff.
    # Asked of the RAW text, not of python_code_only: the save is found
    # by its indentation inside edit_recipe, and stripping comments
    # would not change that but re-indenting nothing else would help.
    raw = out[pc]
    i_save = raw.find('\n            recipe.save()')
    i_del = raw.find('delete_unheld(Recipe')
    if i_save < 0 or i_del < 0 or i_del < i_save:
        refuse('%s: delete_unheld is not called after recipe.save(), '
               'which is the ordering that destroyed a photo when the '
               'save then failed' % CRUD)

    # THE COPY MUST NOT CARRY THE DISPLAY COPY FORWARD.
    nc = T.python_code_only(out[pc], payloads=True)
    if "unshare_file(original_recipe, 'recipe_image')" not in nc:
        refuse('%s: the copy still takes the original path' % CRUD)
    if 'original_recipe.recipe_image_display = None' not in nc:
        refuse('%s: the copy carries the original display copy forward, '
               'which is the same share one field over' % CRUD)
    if "unshare_file(fresh, 'step_image')" not in nc:
        refuse('%s: the step photos still share' % CRUD)
    # AND NO DELETE IN THIS FILE MAY STILL BE THE UNCONDITIONAL ONE.
    if 'recipe_image.delete(save=False)' in nc:
        refuse('%s: an unconditional image delete is still here, and it '
               'is what destroyed two photos on Live' % CRUD)

    # THE DETECTOR ASKS THE STORAGE, AND DELETES NOTHING.
    nk = T.python_code_only(read(pk), payloads=True)
    for want in ('default_storage.exists(', 'default_storage.listdir('):
        if want not in nk:
            refuse('%s: it does not %s - a detector that reasons about '
                   'names instead of asking the disk is a detector that '
                   'can be wrong' % (CHECKER, want))
    for reach in ('.delete(', 'os.remove', 'os.unlink', 'rmtree',
                  "'--write'", 'shutil'):
        if reach in nk:
            refuse('%s names %r. It counts files; it does not remove '
                   'them, and Demetri declined a --write on 22 October'
                   % (CHECKER, reach))
    if 'raise SystemExit(1)' not in nk:
        refuse('%s: it does not exit non-zero on a fault, so a gate '
               'would have to parse its output and guess' % CHECKER)

    if CHECK:
        print('SI-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        plus %s, which this round CREATES' % CHECKER)
        print('        a copied recipe does not share its photo')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('SI-1  applied - a copied recipe takes its own photo, and a '
          'delete asks who else is holding the file.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      plus %s, which this round CREATES' % CHECKER)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
