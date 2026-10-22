# -*- coding: utf-8 -*-
"""apply_photo_floor.py - round PX-2, 21 Oct 2026.

NINETY-SEVEN PHOTOS ARE TOO SMALL FOR THE PHONE HERO, AND THE BROWSER
WAS MAKING A BAD JOB OF THE STRETCH.

    "With regards to the photos, I am not sure what to do. They are
     what they are. We can't change 100 photos. What do you suggest?"

WHERE IT ACTUALLY SHOWS - measured, after a first wrong answer. The
recipe header is a 200x200 thumbnail on a desktop and 150x150 on a
tablet: both DOWNSCALE every photo in the library, so all 324 are
sharp there. Below 768px it becomes `width: 100%; height: 240px;
object-fit: cover`. At 390 CSS px and device-pixel-ratio 3 that band
wants about 1170 real pixels, and 97 of the 324 originals are under
500 on the long edge. The browser stretches them 2.3x with a cheap
filter, every time the page loads.

SO THE FIX IS NOT A LAYOUT. Three frame treatments were rendered -
contained, blur-fill, and a sharp 250px card - and the first two are
pixel-identical to what is there now, because a 3:2 photo in a 1.6:1
band means contained and cover land on the same pixels. The only one
that is genuinely sharp is the 250px card, and it looks worse than
the soft hero does.

WHAT WORKS IS DOING THE UPSCALE ONCE, PROPERLY, ON THE SERVER.
make_display_jpeg already opens every photo and re-encodes it; it
just keeps every pixel and changes only the format. Give it a floor:
under 1200px on the long edge, resample UP with Lanczos and a light
unsharp mask on the way through. The browser then has enough pixels
and stops reaching for its own filter.

IT INVENTS NO DETAIL. A 500px photo will never be a 1600px photo.
This replaces a bad resampler with a good one, once, and the renders
he approved show the difference: the mat weave and the fork tines
come back.

THE ORIGINAL IS NEVER TOUCHED. recipe_image stays the master;
recipe_image_display is derived and rebuildable, which is the whole
reason PX-1 split them.

AND IT RUNS IN THE BATCH COMMAND, NEVER IN A DEPLOY. PX-1 was
explicit: 200 MB of re-encoding has no business running inside a
deploy where nobody is watching. The command gains --rebuild, because
staleness is decided from FILENAMES and the names have not changed -
without it the re-run would skip all 324.

Idempotent. Every file backed up to .bak_photofloor.
"""
import os
import re
import sys

SUFFIX = '.bak_photofloor'
MODELS = os.path.join('pages', 'models.py')
CMD = os.path.join('pages', 'management', 'commands',
                   'convert_recipe_photos.py')
PHOTOS = 'test_recipe_photos.py'
RETIRED = 'test_retired.py'
ME = 'test_photo_floor.py'
PATCHER = 'apply_photo_floor.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PX-2, 21 Oct 2026'
CHECK = False
CREATES = ()

# =====================================================================
# THE FUNCTION
# =====================================================================
FN_WAS = """    NO RESIZING. Measured 13 Oct: nothing in the library is over 1000px
    on the long edge, and the sizes the app draws want up to about 1170.
    Shrinking these would make a soft picture softer to save bytes that
    the encoder gives up for nothing."""

FN_NOW = """    NEVER SHRINKS, AND LIFTS THE SMALL ONES - PX-1 then PX-2.
    Measured 13 Oct: nothing in the library is over 1000px on the long
    edge, and the sizes the app draws want up to about 1170. Shrinking
    these would make a soft picture softer to save bytes the encoder
    gives up for nothing, so nothing is ever shrunk.

    AND 97 OF THE 324 ARE UNDER 500px, which is where PX-2 comes in.
    The recipe hero is 200x200 on a desktop and 150x150 on a tablet -
    both downscale, both sharp - but below 768px it is the full width
    of the screen at 240px tall. At 390 CSS px and device-pixel-ratio
    3 that wants about 1170 real pixels, so a 500px photo is stretched
    2.3x by the browser, with a cheap filter, on every page load.

    DOING IT ONCE, PROPERLY, HERE IS BETTER THAN BADLY, THERE. Lanczos
    plus a light unsharp mask invents no detail - a 500px photo will
    never be a 1600px photo - but it beats bilinear-in-a-browser, and
    the renders Demetri approved on 21 Oct show the difference: the
    weave of a tablecloth and the tines of a fork come back.

    THE FLOOR IS 1200 because 1170 is what the widest phone hero asks
    for and a round number is easier to check than a clever one."""

BODY_WAS = """    rgba = im.convert('RGBA')
    flat = Image.new('RGB', im.size, (255, 255, 255))
    flat.paste(rgba, mask=rgba.split()[3])
    out = io.BytesIO()
    flat.save(out, 'JPEG', quality=quality, optimize=True,
              progressive=True)
    return out.getvalue()"""

BODY_NOW = """    rgba = im.convert('RGBA')
    flat = Image.new('RGB', im.size, (255, 255, 255))
    flat.paste(rgba, mask=rgba.split()[3])

    # THE FLOOR - PX-2, 21 Oct 2026. Up only, never down.
    #
    # FLATTENED FIRST, SO THE SHARPEN HAS REAL PIXELS UNDER IT. An
    # unsharp mask over an alpha edge haloes the transparency rather
    # than the subject, and 322 of the 324 carry an alpha channel.
    long_edge = max(flat.size)
    if long_edge and long_edge < DISPLAY_FLOOR:
        scale = DISPLAY_FLOOR / float(long_edge)
        flat = flat.resize((max(1, int(round(flat.size[0] * scale))),
                            max(1, int(round(flat.size[1] * scale)))),
                           Image.LANCZOS)
        # A LIGHT HAND. 110 per cent at radius 1.6 was chosen against
        # real renders at device-pixel-ratio 3; heavier than this and
        # the edges ring, which reads as worse than soft.
        flat = flat.filter(ImageFilter.UnsharpMask(
            radius=1.6, percent=110, threshold=2))

    out = io.BytesIO()
    flat.save(out, 'JPEG', quality=quality, optimize=True,
              progressive=True)
    return out.getvalue()"""

IMPORT_WAS = """    import io
    from PIL import Image

    if not field_file:
        return None"""

IMPORT_NOW = """    import io
    from PIL import Image, ImageFilter

    if not field_file:
        return None"""

FLOOR_WAS = """def make_display_jpeg(field_file, quality=85):"""

FLOOR_NOW = """# THE PHONE HERO ASKS FOR ABOUT 1170 REAL PIXELS - PX-2, 21 Oct 2026.
# Full-width at 390 CSS px and device-pixel-ratio 3. A round number is
# easier to check than a clever one, and it is a module constant
# rather than a literal inside the function so a suite can read it.
DISPLAY_FLOOR = 1200


def make_display_jpeg(field_file, quality=85):"""


# =====================================================================
# THE BATCH COMMAND
# =====================================================================
# STALENESS IS DECIDED FROM FILENAMES, and this round changes the
# CONTENT of a display copy without changing its name. Without
# --rebuild the re-run would skip all 324 and report success.
CMD_ARG_WAS = """        parser.add_argument(
            '--quality', type=int, default=85,"""

CMD_ARG_NOW = """        parser.add_argument(
            '--rebuild', action='store_true',
            help='Convert every photo, not only the ones whose display '
                 'copy is missing or stale. PX-2 changed what a display '
                 'copy CONTAINS without changing its name, and staleness '
                 'is decided from names - so a plain re-run after that '
                 'round would skip all 324 and report success.')
        parser.add_argument(
            '--quality', type=int, default=85,"""

CMD_HANDLE_WAS = """        write = opts['write']
        limit = opts['limit'] or 0
        quality = opts['quality']"""

CMD_HANDLE_NOW = """        write = opts['write']
        limit = opts['limit'] or 0
        quality = opts['quality']
        rebuild = opts.get('rebuild', False)"""

CMD_STALE_WAS = """            if not recipe.display_copy_is_stale():
                skipped += 1
                continue"""

CMD_STALE_NOW = """            if not rebuild and not recipe.display_copy_is_stale():
                skipped += 1
                continue"""

CMD_DOC_WAS = """WHAT IT DOES. For each recipe with an original and no current display
copy, it re-encodes the original as JPEG at the SAME pixel dimensions
and stores it in recipe_images_display/. It never writes to
recipe_images/ and never deletes anything. The originals stay the
masters."""

CMD_DOC_NOW = """WHAT IT DOES. For each recipe with an original and no current display
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
success."""


# =====================================================================
# PX-1's OWN SUITE, CORRECTED IN THE SAME PATCHER
# =====================================================================
PHOTOS_SIZE_WAS = """        # NO RESIZING. The whole round rests on this.
        ok(out.size == (w, h),
           '  and EVERY PIXEL IS KEPT - %dx%d in, %dx%d out'
           % (w, h, out.size[0], out.size[1]), out.size)"""

PHOTOS_SIZE_NOW = """        # NEVER SHRUNK, AND LIFTED IF IT IS SMALL - PX-1, then PX-2
        # on 21 Oct 2026. The 600x400 fixture is under the 1200px
        # floor, so it comes back larger in the same proportion. What
        # PX-1 actually rested on was that nothing is ever LOST, and
        # that is what is asked here.
        ok(out.size[0] >= w and out.size[1] >= h,
           '  and NO PIXEL IS LOST - %dx%d in, %dx%d out'
           % (w, h, out.size[0], out.size[1]), out.size)
        ok(abs(out.size[0] / float(out.size[1]) - w / float(h)) < 0.01,
           '  at the same shape - %.3f in, %.3f out'
           % (w / float(h), out.size[0] / float(out.size[1])))"""

PHOTOS_SMALL_WAS = """        ok(len(jpg) < len(png) / 2,
           '  and the result is far smaller: %.0f KB -> %.0f KB (%.0f%%)'
           % (len(png) / 1024.0, len(jpg) / 1024.0,
              100.0 * len(jpg) / len(png)),
           '%d vs %d' % (len(png), len(jpg)))"""

PHOTOS_SMALL_NOW = """        # PX-2, 21 Oct 2026 - the fixture is 600px and the floor is
        # 1200, so this one is now resampled up four times the area
        # before it is encoded. It is STILL smaller than the PNG,
        # which is the claim PX-1 was making; the margin is just not
        # a half any more.
        ok(len(jpg) < len(png),
           '  and the result is still smaller: %.0f KB -> %.0f KB (%.0f%%)'
           % (len(png) / 1024.0, len(jpg) / 1024.0,
              100.0 * len(jpg) / len(png)),
           '%d vs %d' % (len(png), len(jpg)))"""

# ---- AND PX-1's CLOSING NOTE, WHICH IS NOW HALF WRONG. It said a
# conversion cannot make a soft photo sharp. That is still true of the
# originals, but it stopped being the end of the story the moment the
# upscale moved onto the server: the stretch happens once, with Lanczos
# and a measured sharpen, instead of on every page load with whatever
# the browser uses. A suite that goes on disclaiming something the
# round now does is a suite nobody reads.
PHOTOS_NOTE_WAS = """print('  1170. They are soft in the PNG already. Converting makes them')
print('  light; it cannot make them sharp.')"""

PHOTOS_NOTE_NOW = """print('  1170. They are soft in the PNG already, and PX-2 cannot invent')
print('  detail that was never photographed - a 500px picture will never')
print('  be a 1600px picture. What PX-2 does is move the stretch off the')
print('  browser and onto the server, done once with Lanczos and a')
print('  measured sharpen rather than every page load with whatever the')
print('  browser reaches for. Better, not fixed. See test_photo_floor.')"""

# ---- AND THE LIFT ITSELF. PX-1's suite execs the two functions out of
# pages/models.py into a namespace holding nothing but os, because that
# was everything they referenced. make_display_jpeg reads a module
# constant now, so the lift has to bring it along - and must read it
# out of the module rather than type it here, or this suite would go on
# passing on a floor of 1200 while the shipped one said something else.
PHOTOS_LIFT_WAS = """ns = {'os': os}
lifted = ok(len(src) == 2, 'both functions lifted out of %s' % MODELS,
            '%d found' % len(src))"""

PHOTOS_LIFT_NOW = """ns = {'os': os}
# PX-2, 21 Oct 2026 - THE FLOOR IS LIFTED TOO, NOT TYPED. It is read
# out of the module so that this suite exercises the number the app
# actually ships; a floor written in here would pass whatever the
# model said.
cm = re.search(r'(?m)^DISPLAY_FLOOR = (\\d+)\\s*$', M)
if cm:
    ns['DISPLAY_FLOOR'] = int(cm.group(1))
lifted = ok(len(src) == 2 and cm is not None,
            'both functions and the floor lifted out of %s' % MODELS,
            '%d function(s), floor %s'
            % (len(src), cm.group(1) if cm else 'absent'))"""

# ---- AND test_retired's REGISTER, WHICH THIS ROUND MAKES PX-1 LEAVE.
#
# test_retired holds 22 HISTORICAL suites to keeping every integer they
# ever had: a census of what a round did is a claim about the past, and
# the past does not change. This round corrects four of PX-1's claims
# and three of them carry numbers - the half-size margin, a size
# comparison and the lifted floor - so test_recipe_photos stops being a
# record of 13 October and becomes a claim about today's tree.
#
# THE REGISTER HAS A PLACE FOR THAT ALREADY. RD-3 moved
# test_personal_heads out of KEPT on 20 October for the same reason,
# and RD-1 moved three censuses out the day before. MOVED is where a
# suite goes when a later round changed what it is about.
RETIRED_WAS = """    'test_recipe_photos.py', 'test_recipe_spice.py', 'test_retone.py',"""

RETIRED_NOW = """    'test_recipe_spice.py', 'test_retone.py',"""

RETIRED_MOVED_WAS = """MOVED = (
    # PP-1, 20 Oct 2026 - moved out of KEPT by RD-3, earlier in this
    # same push."""

RETIRED_MOVED_NOW = """MOVED = (
    # PX-2, 21 Oct 2026 - moved out of KEPT, where RT-1 filed it.
    # PX-1 measured the library on 13 October and its numbers were a
    # record of that day. PX-2 gives the display copy a 1200px floor
    # and corrects four of PX-1's claims in the same patcher - three
    # of them carrying integers, because a 600px fixture is resampled
    # to 1200 before it is encoded and the old margins cannot hold. A
    # suite whose subject a later round CHANGED cannot keep every
    # number it had; what it can do, and does, is say which round
    # changed it and why.
    'test_recipe_photos.py',
    # PP-1, 20 Oct 2026 - moved out of KEPT by RD-3, earlier in this
    # same push."""


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
    raise SystemExit('PX-2 REFUSED: %s' % msg)


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

    if 'DISPLAY_FLOOR' in m:
        print('PX-2  already applied - the display copy has a floor.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING, ASKED OF THE FUNCTION. make_display_jpeg is
    # the one place that knows how a display copy is made, and PX-1
    # says so in its own docstring - so this round changes one
    # function or it is in the wrong place.
    code = T.python_code_only(m, payloads=True)
    if 'def make_display_jpeg' not in code:
        refuse('%s: make_display_jpeg is gone' % MODELS)
    seg = code[code.index('def make_display_jpeg'):]
    seg = seg[:seg.index('\ndef ', 1)] if '\ndef ' in seg[1:] else seg
    # check_gates flags this against BODY_NOW, which does resample. It
    # is not the same reading: seg comes from the tree as it stands,
    # BEFORE any swap, so this is the precondition - nobody else has
    # put a resample in here - not a claim about the round's output.
    if 'resize(' in seg:
        refuse('%s: make_display_jpeg already resizes something' % MODELS)
    if 'flat.save(out' not in seg:
        refuse('%s: the encode is not where this round expects it'
               % MODELS)

    m = swap(m, FLOOR_WAS, FLOOR_NOW, '%s (the constant)' % MODELS)
    m = swap(m, FN_WAS, FN_NOW, '%s (the note)' % MODELS)
    m = swap(m, IMPORT_WAS, IMPORT_NOW, '%s (the filter)' % MODELS)
    m = swap(m, BODY_WAS, BODY_NOW, '%s (the floor)' % MODELS)
    out[pm] = m

    # ---- THE BATCH COMMAND
    pc = os.path.join(root, CMD)
    c = read(pc)
    c = swap(c, CMD_DOC_WAS, CMD_DOC_NOW, '%s (the doc)' % CMD)
    c = swap(c, CMD_ARG_WAS, CMD_ARG_NOW, '%s (the flag)' % CMD)
    c = swap(c, CMD_HANDLE_WAS, CMD_HANDLE_NOW, '%s (the option)' % CMD)
    c = swap(c, CMD_STALE_WAS, CMD_STALE_NOW, '%s (the skip)' % CMD)
    out[pc] = c

    # ---- PX-1's SUITE, CORRECTED IN THE SAME PATCHER
    pp = os.path.join(root, PHOTOS)
    s = read(pp)
    s = swap(s, PHOTOS_LIFT_WAS, PHOTOS_LIFT_NOW, '%s (the lift)' % PHOTOS)
    s = swap(s, PHOTOS_NOTE_WAS, PHOTOS_NOTE_NOW, '%s (the note)' % PHOTOS)
    s = swap(s, PHOTOS_SMALL_WAS, PHOTOS_SMALL_NOW, '%s (the size)' % PHOTOS)
    s = swap(s, PHOTOS_SIZE_WAS, PHOTOS_SIZE_NOW, '%s (the pixels)' % PHOTOS)
    out[pp] = s

    # ---- THE HISTORICAL REGISTER
    pr = os.path.join(root, RETIRED)
    rt = read(pr)
    rt = swap(rt, RETIRED_WAS, RETIRED_NOW, '%s (out of KEPT)' % RETIRED)
    rt = swap(rt, RETIRED_MOVED_WAS, RETIRED_MOVED_NOW,
              '%s (into MOVED)' % RETIRED)
    out[pr] = rt

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_print_compact.py'
)""", """    'test_print_compact.py',
    # PX-2, 21 Oct 2026 - a floor under the display copy, so the
    # browser stops upscaling 97 photos badly on every page load.
    'test_photo_floor.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'RG-3, 21 Oct 2026';""",
             """    @{ File = 'pages/models.py'; Text = 'DISPLAY_FLOOR'; What = 'PX-2: a photo under 1200px on the long edge is resampled up once, on the server, with Lanczos and a light sharpen - the phone hero asks for about 1170 and the browser was doing that stretch itself on every page load' },
    @{ File = 'pages/management/commands/convert_recipe_photos.py'; Text = '--rebuild'; What = 'PX-2: the batch command can rebuild every display copy, because staleness is decided from filenames and this round changed what a display copy contains without changing its name' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'RG-3, 21 Oct 2026';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # RG-3, 21 Oct 2026 - a sheet as tall as what is on it.
    'test_print_compact.py',
]""", """    # RG-3, 21 Oct 2026 - a sheet as tall as what is on it.
    'test_print_compact.py',
    # PX-2, 21 Oct 2026 - the upscale done once, properly, here.
    'test_photo_floor.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # RG-3, 21 Oct 2026 - the printed week and day stop at the end.
    '.bak_printcompact',
]""", """    # RG-3, 21 Oct 2026 - the printed week and day stop at the end.
    '.bak_printcompact',
    # PX-2, 21 Oct 2026 - a floor under every display copy.
    '.bak_photofloor',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # PX-2, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.python_code_only(out[pm], payloads=True)
    nseg = nc[nc.index('def make_display_jpeg'):]
    nseg = nseg[:nseg.index('\ndef ', 1)] if '\ndef ' in nseg[1:] else nseg
    # UP ONLY. A round that shrank the library to save bytes would
    # undo PX-1 and nobody would see it until a phone.
    if 'long_edge < DISPLAY_FLOOR' not in nseg:
        refuse('%s: the floor does not guard on being UNDER it - this '
               'would shrink the big ones' % MODELS)
    if 'ImageFilter.UnsharpMask' not in nseg:
        refuse('%s: the sharpen is missing, and Lanczos alone is softer '
               'than the browser at this scale' % MODELS)
    if 'Image.LANCZOS' not in nseg:
        refuse('%s: the resample is not Lanczos' % MODELS)
    # THE ORIGINAL IS NEVER TOUCHED. This function takes a file and
    # returns bytes; if it ever writes, PX-1's split has gone.
    # check_gates flags this against BODY_NOW's own encode. That one
    # is taken out of the segment on the line below before the question
    # is asked, so what is left is any OTHER write - which is the thing
    # this gate is actually about.
    if '.save(' in nseg.replace('flat.save(out', ''):
        refuse('%s: make_display_jpeg writes something other than its '
               'own buffer' % MODELS)
    # AND THE COMMAND CAN REBUILD.
    ncmd = T.python_code_only(out[pc], payloads=True)
    if "'--rebuild'" not in ncmd:
        refuse('%s: the command cannot rebuild, so the 324 copies this '
               'round supersedes would never be replaced' % CMD)
    if 'not rebuild and not recipe.display_copy_is_stale()' not in ncmd:
        refuse('%s: --rebuild does not reach the skip' % CMD)
    # STILL DRY BY DEFAULT.
    if "opts['write']" not in ncmd or "'--write'" not in ncmd:
        refuse('%s: the command stopped being dry by default' % CMD)

    if CHECK:
        print('PX-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        floor 1200px, Lanczos + unsharp, up only')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('PX-2  applied - a small photo is lifted once, here, instead '
          'of badly in a browser.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
