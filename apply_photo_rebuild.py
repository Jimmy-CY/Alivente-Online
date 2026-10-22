# -*- coding: utf-8 -*-
"""apply_photo_rebuild.py - round SD-1, 22 Oct 2026.

--rebuild --write DOES NOT REBUILD. IT ACCUMULATES.

Found on 22 October while driving DP-1's suite, in a temporary media
volume, with two photos:

    after rebuild: recipe-1-alpha-20261022063218_xUkNf5M.jpg  stale? True
    after 2nd    : recipe-1-alpha-20261022063218_wEIntUA.jpg  stale? True
    on the volume: ...png  ...jpg  ..._wEIntUA.jpg  ..._xUkNf5M.jpg

DJANGO'S STORAGE DOES NOT OVERWRITE. FieldFile.save() asks the storage
for an AVAILABLE name, and FileSystemStorage answers a name that is not
taken - the original with a random seven-character suffix. Every caller
in this application that re-derives a file over itself gets that, and
nothing has ever said so.

THREE THINGS FOLLOW, AND ALL THREE ARE ON THE LIVE VOLUME'S PATH.

ONE. The old display copy is never deleted. A rebuild of 324 photos
leaves 324 orphans. Nothing references them and nothing will ever
collect them.

TWO. Every recipe becomes PERMANENTLY STALE. display_copy_is_stale()
compares the stored name with display_name_for(original), by design and
for good reasons - there is no column to forget to clear. But
..._xUkNf5M.jpg is never equal to ....jpg, so the answer is True for
ever after.

THREE. Permanently stale means Recipe.save() rebuilds the display copy
EVERY TIME the recipe is edited, because PX-1 put that rebuild in
save(). Another orphan each time, for as long as the recipe is used.

ONE PLACE THAT WRITES A DISPLAY COPY, AND IT WRITES THE NAME IT MEANS.
make_display_jpeg has been 'the ONE place that knows how a display copy
is MADE' since PX-1. store_display_jpeg is now the one place that knows
how it is STORED: it deletes what is at the target path and then writes
there, so the name on disk is the name display_copy_is_stale expects.
Both callers go through it - the command and Recipe.save() - because a
fix in one of two callers is the same bug with a smaller blast radius.

IT CHECKS RATHER THAN HOPES. After the write it compares the stored
basename with the name it asked for and returns False if they differ.
That is the thing nobody did before: this whole round is what happens
when a save() that cannot fail quietly returns a different name.

AND IT DELETES ONE FILE, WHICH IS A WRITE TO A VOLUME. The file it
deletes is the one it is about to replace at the same path, found by
asking the storage whether that exact path exists - not a pattern, not
a glob, not a listing. Nothing else on the volume can be reached from
here.

NO MIGRATION. No field changes; recipe_image_display already holds a
name and already means this.

Idempotent. Every file backed up to .bak_photorebuild.
"""
import os
import re
import sys

SUFFIX = '.bak_photorebuild'
MODELS = os.path.join('pages', 'models.py')
RP = 'test_recipe_photos.py'
CMD = os.path.join('pages', 'management', 'commands',
                   'convert_recipe_photos.py')
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_photo_rebuild.py'
PATCHER = 'apply_photo_rebuild.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'SD-1, 22 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# THE ONE PLACE THAT STORES ONE
# ==========================================================================
M_WAS = '''def display_name_for(original_name):'''

M_NOW = '''def store_display_jpeg(recipe, data):
    """Put JPEG bytes at the display copy's PROPER name. SD-1, 22 Oct 2026.

    THE ONE PLACE THAT KNOWS HOW A DISPLAY COPY IS STORED, as
    make_display_jpeg has been the one place that knows how one is made
    since PX-1. Both callers go through it: the convert_recipe_photos
    command and Recipe.save().

    WHY IT EXISTS. FieldFile.save() asks the storage for an AVAILABLE
    name, and FileSystemStorage answers one that is not taken - the name
    you asked for with a random seven-character suffix on it. Writing a
    display copy over itself therefore produced

        recipe-1-alpha-20261022063218_xUkNf5M.jpg

    and three consequences. The old copy was never deleted, so a rebuild
    of 324 photos left 324 orphans. display_copy_is_stale compares the
    stored name with display_name_for(original) - by design, so that
    there is no column to forget to clear - and the suffixed name is
    never equal to it, so every recipe became permanently stale. And
    permanently stale means save() rebuilds the copy every time the
    recipe is edited, leaving another orphan each time.

    SO IT DELETES THE TARGET PATH FIRST and then writes there. One
    path, asked of the storage by exact name - not a pattern, not a
    glob, not a listing. The file deleted is the one about to be
    replaced at the same path, and nothing else on the volume can be
    reached from here.

    AND IT CHECKS RATHER THAN HOPES. If the stored name still is not
    the name asked for, this returns False and says nothing more; the
    caller decides. That check is the thing nobody did before, and it
    is why this round exists.

    Returns True when the display copy is on the volume under its
    proper name, False otherwise. Never raises: a picture is worth less
    than the recipe it belongs to, which is PX-1's rule and still true.
    """
    from django.core.files.base import ContentFile
    try:
        want = display_name_for(recipe.recipe_image.name)
        field = recipe.recipe_image_display
        target = recipe_display_upload_path(recipe, want)
        if field.storage.exists(target):
            field.storage.delete(target)
        field.save(want, ContentFile(data), save=False)
        return os.path.basename(field.name) == want
    except Exception:
        return False


def display_name_for(original_name):'''

# ==========================================================================
# THE TWO CALLERS
# ==========================================================================
SAVE_WAS = """        if self.display_copy_is_stale():
            try:
                from django.core.files.base import ContentFile
                data = make_display_jpeg(self.recipe_image)
                if data is not None:
                    self.recipe_image_display.save(
                        display_name_for(self.recipe_image.name),
                        ContentFile(data), save=False)
                    super().save(update_fields=['recipe_image_display'])
            except Exception:
                pass"""

SAVE_NOW = """        #
        # THROUGH store_display_jpeg SINCE SD-1, 22 Oct 2026. This block
        # used to call field.save() directly, which asks the storage for
        # an AVAILABLE name and gets the one you asked for with a random
        # suffix whenever the target already exists. A recipe left
        # permanently stale by that - see store_display_jpeg - came
        # through here on EVERY edit and left another orphan each time.
        if self.display_copy_is_stale():
            try:
                data = make_display_jpeg(self.recipe_image)
                if data is not None and store_display_jpeg(self, data):
                    super().save(update_fields=['recipe_image_display'])
            except Exception:
                pass"""

CMD_WAS = """            if write:
                recipe.recipe_image_display.save(
                    display_name_for(recipe.recipe_image.name),
                    ContentFile(data), save=False)
                Recipe.objects.filter(pk=recipe.pk).update(
                    recipe_image_display=recipe.recipe_image_display.name)"""

CMD_NOW = """            if write:
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
                             recipe.recipe_image_display.name)))"""

CMD_IMP_WAS = """from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from pages.models import Recipe, display_name_for, make_display_jpeg"""

CMD_IMP_NOW = """from django.core.management.base import BaseCommand

from pages.models import Recipe, make_display_jpeg, store_display_jpeg"""

# WHAT THE COMMAND SAYS ABOUT ITSELF. --rebuild's help promised a thing
# it did not do.
CMD_HELP_WAS = """            help='Convert every photo, not only the ones whose display '
                 'copy is missing or stale. PX-2 changed what a display '
                 'copy CONTAINS without changing its name, and staleness '
                 'is decided from names - so a plain re-run after that '
                 'round would skip all 324 and report success.')"""

CMD_HELP_NOW = """            help='Convert every photo, not only the ones whose display '
                 'copy is missing or stale. PX-2 changed what a display '
                 'copy CONTAINS without changing its name, and staleness '
                 'is decided from names - so a plain re-run after that '
                 'round would skip all 324 and report success. Since '
                 'SD-1 this really does replace the file rather than '
                 'writing a suffixed copy beside it.')"""

CMD_DOC_WAS = """--rebuild is what you want after PX-2. Staleness is decided from the
FILENAMES and that round changed what a display copy CONTAINS without
changing its name, so a plain re-run would skip all 324 and report
success."""

CMD_DOC_NOW = """--rebuild is what you want after PX-2. Staleness is decided from the
FILENAMES and that round changed what a display copy CONTAINS without
changing its name, so a plain re-run would skip all 324 and report
success.

AND IT REALLY REPLACES THE FILE - SD-1, 22 Oct 2026. Until that round
it did not: Django storage does not overwrite, so each rebuild wrote
recipe-1-alpha-20261022063218_xUkNf5M.jpg beside the copy it meant to
replace, left the old one on the volume for ever, and left the row
permanently stale because staleness is a comparison of names. Running
it twice produced three JPEGs for one photo. See store_display_jpeg."""


# ==========================================================================
# PX-1's OWN SUITE, WHICH ASKED ABOUT A WRITE THAT HAS MOVED
# ==========================================================================
# Three claims in test_recipe_photos are about where the display copy is
# written, and this round moved that. They move with it rather than
# being relaxed: the thing each one protects is still true, it is just
# true somewhere else now.
RP_FIELD_WAS = """ok('editable=False' in M.split('recipe_image_display')[1][:400],
   '  and it is editable=False, so no ModelForm can set it by hand')"""

# AND IT SPLITS ON THE FIELD, NOT ON THE NAME. This round put
# store_display_jpeg ABOVE the model, and it mentions
# recipe_image_display - so [1] stopped being the declaration and the
# claim read 400 characters of somebody else's function. The anchor is
# now the declaration itself, which there is exactly one of.
RP_FIELD_NOW = """ok('editable=False' in
   M.split('recipe_image_display = models.ImageField(')[1][:400],
   '  and it is editable=False, so no ModelForm can set it by hand')"""

RP_WRITE_WAS = """body = cmd.split('def handle')[1]
writes = re.findall(r'recipe_image_display\\.save\\(', body)
ok(len(writes) == 1, '  it writes in exactly one place', len(writes))
guarded = body.split('if write:')[1] if 'if write:' in body else ''
ok('recipe_image_display.save(' in guarded,
   '  and that place is INSIDE the --write guard')"""

RP_WRITE_NOW = """# SD-1, 22 Oct 2026 - THE WRITE MOVED, AND THE CLAIM MOVED WITH IT.
# This asked for exactly one recipe_image_display.save( in handle(),
# which was right until the command stopped writing the field at all.
# Django storage does not overwrite: that call handed back a suffixed
# name on every rebuild, left the old copy on the volume and left the
# row permanently stale. store_display_jpeg in models.py is the one
# place now, and what this asks is that the command goes through it
# and does not reach past it.
body = cmd.split('def handle')[1]
writes = re.findall(r'store_display_jpeg\\(', body)
ok(len(writes) == 1, '  it writes in exactly one place', len(writes))
ok('recipe_image_display.save(' not in cmd,
   '  and that place is NOT a field write of its own - see SD-1')
guarded = body.split('if write:')[1] if 'if write:' in body else ''
ok('store_display_jpeg(' in guarded,
   '  and it is INSIDE the --write guard')"""


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
    raise SystemExit('SD-1 REFUSED: %s' % msg)


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
        print('SD-1  already applied - a rebuild replaces the file.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # DP-1 PUT THE REPORT IN. This round changes what it reports ON, so
    # it must be there.
    pc = os.path.join(root, CMD)
    c = read(pc)
    if 'def report_what_landed' not in c:
        refuse('%s: DP-1 write report is not here, and this round adds '
               'to it rather than replacing it' % CMD)

    m = swap(m, M_WAS, M_NOW, '%s (the one place)' % MODELS)
    m = swap(m, SAVE_WAS, SAVE_NOW, '%s (save)' % MODELS)
    out[pm] = m

    c = swap(c, CMD_IMP_WAS, CMD_IMP_NOW, '%s (the imports)' % CMD)
    c = swap(c, CMD_WAS, CMD_NOW, '%s (the write)' % CMD)
    c = swap(c, CMD_HELP_WAS, CMD_HELP_NOW, '%s (the help)' % CMD)
    c = swap(c, CMD_DOC_WAS, CMD_DOC_NOW, '%s (the docstring)' % CMD)
    out[pc] = c

    pr = os.path.join(root, RP)
    r = read(pr)
    r = swap(r, RP_FIELD_WAS, RP_FIELD_NOW, '%s (the field)' % RP)
    r = swap(r, RP_WRITE_WAS, RP_WRITE_NOW, '%s (the one write)' % RP)
    out[pr] = r

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_deploy_probe.py'
)""", """    'test_deploy_probe.py',
    # SD-1, 22 Oct 2026 - a rebuild replaces the file it rebuilds.
    'test_photo_rebuild.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'mysite/urls.py'; Text = 'def deploy_version';""",
             """    @{ File = 'pages/models.py'; Text = 'def store_display_jpeg'; What = 'SD-1: the ONE place that stores a display copy. Django storage does not overwrite, so --rebuild --write used to write a suffixed copy beside the one it meant to replace, leave the old on the volume and leave the row permanently stale. This deletes the target path first and checks the name it got' },
    @{ File = 'mysite/urls.py'; Text = 'def deploy_version';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # DP-1, 22 Oct 2026 - and the push finds out whether it deployed.
    'test_deploy_probe.py',
]""", """    # DP-1, 22 Oct 2026 - and the push finds out whether it deployed.
    'test_deploy_probe.py',
    # SD-1, 22 Oct 2026 - a rebuild replaces rather than accumulates.
    'test_photo_rebuild.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # DP-1, 22 Oct 2026 - the site says what it is running.
    '.bak_deployprobe',
]""", """    # DP-1, 22 Oct 2026 - the site says what it is running.
    '.bak_deployprobe',
    # SD-1, 22 Oct 2026 - a rebuild replaces the file it rebuilds.
    '.bak_photorebuild',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # SD-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    #
    # check_gates says SD-1 is already named in test_deploy_probe.py.
    # It is, once, and on purpose: DP-1's section 4 ran a plain --write
    # after a rebuild, converted two photos that should have been
    # current, and says in a comment that this is SD-1's bug rather
    # than its own. That is a forward reference from the round that
    # FOUND the bug to the round that fixes it, which is what the
    # register is for. The first name chosen here was PR-1, which
    # apply_compliance_tab.py has used 45 times since 3 October.
    nm = T.python_code_only(out[pm], payloads=True)
    if 'def store_display_jpeg' not in nm:
        refuse('%s: the one place is not there' % MODELS)

    body = nm[nm.index('def store_display_jpeg'):]
    nxt = re.search(r'\ndef \w+', body[1:])
    body = body[:nxt.start() + 1] if nxt else body
    if 'storage.delete(' not in body:
        refuse('%s: it does not clear the target, so the storage will '
               'hand it a suffixed name exactly as before' % MODELS)
    if 'storage.exists(' not in body:
        refuse('%s: it deletes without asking whether anything is there'
               % MODELS)
    # THE DELETE REACHES ONE PATH, AND IT IS THE ONE BEING WRITTEN.
    if body.count('storage.delete(') != 1:
        refuse('%s: store_display_jpeg deletes %d time(s). One write, '
               'one path, one delete.'
               % (MODELS, body.count('storage.delete(')))
    if 'storage.delete(target)' not in body:
        refuse('%s: the delete does not name the target it is about to '
               'write - a delete that takes anything else is a delete '
               'nobody can bound' % MODELS)
    for reach in ('listdir', 'glob', 'walk', 'rmtree', 'os.remove',
                  'os.unlink', 'shutil'):
        if reach in body:
            refuse('%s: store_display_jpeg names %r, and it is allowed '
                   'to touch exactly one path' % (MODELS, reach))
    if 'os.path.basename(field.name) == want' not in body:
        refuse('%s: it does not check the name it actually got, which '
               'is the entire bug it exists to fix' % MODELS)

    # BOTH CALLERS, NOT ONE. A fix in one of two callers is the same
    # bug with a smaller blast radius.
    if nm.count('store_display_jpeg(') < 2:
        refuse('%s: only %d caller(s) go through it - Recipe.save() and '
               'the command are both callers'
               % (MODELS, nm.count('store_display_jpeg(')))
    # check_gates flags the next two: this round writes the string
    # 'recipe_image_display.save(' and these gates refuse it. Both are
    # benign, and for the same reason - the string is written into
    # test_recipe_photos.py, as the text of a CLAIM that the command no
    # longer contains it, while the gates are asked of the command and
    # of models.py. Three different files. The gate below is the real
    # one; the claim is PX-1's suite keeping watch afterwards.
    nc = T.python_code_only(out[pc], payloads=True)
    if 'store_display_jpeg(recipe, data)' not in nc:
        refuse('%s: the command still writes the field itself' % CMD)
    if 'recipe_image_display.save(' in nc:
        refuse('%s: a direct field write is still in here, and it is '
               'what produced the suffixes' % CMD)
    if 'recipe_image_display.save(' in nm:
        refuse('%s: a direct field write is still outside the one '
               'place' % MODELS)

    if CHECK:
        print('SD-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        one place that stores a display copy, and it '
              'checks the name it got')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('SD-1  applied - a rebuild replaces the file it rebuilds.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
