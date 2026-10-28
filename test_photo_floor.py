# -*- coding: utf-8 -*-
"""test_photo_floor.py - round PX-2, 21 Oct 2026.

THE STRETCH WAS ALWAYS HAPPENING. IT JUST HAPPENED IN THE WRONG PLACE.

    "With regards to the photos, I am not sure what to do. They are
     what they are. We can't change 100 photos. What do you suggest?"
    ... "yes, upscale"

PX-1 MEASURED THE LIBRARY AND SAID THE REST OUT LOUD: 97 of the 324
photos are under 500px on the long edge, nothing is over 1000px, and
the phone hero wants about 1170 real pixels. Then it closed by saying a
conversion cannot make a soft photo sharp, and left it there.

THAT WAS HALF AN ANSWER. Nothing can invent detail nobody photographed.
But the browser was already doing the upscale - 2.3x, with whatever
filter it reaches for, on every page load, on every phone - and nobody
had asked whether doing it once on the server was better. It is, and
section 4 measures by how much rather than claiming it.

SO THE DISPLAY COPY GETS A FLOOR. 1200px on the long edge, because the
widest phone hero asks for about 1170 and a round number is easier to
check than a clever one. Up only. Lanczos, then a light unsharp mask -
110 per cent at radius 1.6, chosen against renders he looked at.

AND THE BATCH COMMAND GETS --rebuild, because staleness is decided from
FILENAMES and this round changes what a display copy CONTAINS without
changing its name. Without the flag the 324 copies already on the
volume would never be replaced and the round would ship to new uploads
only.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The floor is a module constant, the function guards
      on being UNDER it, the resample is Lanczos, the sharpen is
      there, and the command can rebuild.

  2   THE CONTROL. Every claim re-asked of .bak_photofloor, where
      there was no floor at all.

  3   THE FUNCTION, LIFTED AND RUN. Under the floor it comes up; at
      the floor and over it nothing moves; the shape never changes;
      alpha still lands on white; an unreadable file still returns
      None rather than raising.

  4   BETTER THAN THE BROWSER, MEASURED. A detailed 1200px source is
      the truth, downscaled to 500/700/900 to stand in for the
      library, then brought back up both ways and compared against
      the truth it came from. If the server upscale were not closer
      than a bilinear stretch, this round would be moving work for
      nothing.

  5   THE COMMAND. --rebuild reaches the skip and nothing else; still
      dry by default; the originals are still never written.

  6   PX-1's OWN SUITE, RUN. This round corrects four of its claims
      in the same patcher - the half-size margin, the every-pixel-kept
      claim, the lift, and the closing note that disclaimed exactly
      what this round now does.

  7   Scope, registration and the gate.

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

import io
import math
import os
import random
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_photofloor'
ME = 'test_photo_floor.py'
PATCHER = 'apply_photo_floor.py'
PS1 = 'Push-PendingChanges.ps1'
PHOTOS = 'test_recipe_photos.py'
MARK = 'PX-2, 21 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
CMD = os.path.join(ROOT, 'pages', 'management', 'commands',
                   'convert_recipe_photos.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, CMD)

# WHAT THE PHONE HERO ACTUALLY ASKS FOR. 390 CSS px wide at
# device-pixel-ratio 3 is 1170 real pixels; the floor is the next round
# number above it. Both are written here so the suite fails if either
# the floor or the reasoning behind it is changed on its own.
HERO_CSS_PX = 390
HERO_DPR = 3
WANTS = HERO_CSS_PX * HERO_DPR

passed = failed = skipped = 0
# What section 4 measured, for the closing note to quote. Set there,
# defaulted here so a skipped section does not take the summary with it.
GAIN = '27 and 76 per cent (not measured on this run)'


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


def fn(text):
    """make_display_jpeg and nothing around it.

    The round is about ONE function, so every claim about the model is
    asked of that function rather than of the file - a floor added to
    some other method would otherwise pass section 1.
    """
    code = T.python_code_only(text, payloads=True)
    if 'def make_display_jpeg' not in code:
        return ''
    seg = code[code.index('def make_display_jpeg'):]
    return seg[:seg.index('\ndef ', 1)] if '\ndef ' in seg[1:] else seg


def claims(d):
    """THE DELTA. Every one of these is false before this round and
    true after it, which is what makes section 2 worth running."""
    m, c = d[MODELS], d[CMD]
    f = fn(m)
    code = T.python_code_only(m, payloads=True)
    cc = T.python_code_only(c, payloads=True)
    return {
        'the floor is a MODULE CONSTANT, not a number buried in a call':
            bool(re.search(r'(?m)^DISPLAY_FLOOR = \d+\s*$', code)),
        '  and the function reads it':
            'DISPLAY_FLOOR' in f,
        'the floor guards on being UNDER it, so nothing is ever shrunk':
            'long_edge < DISPLAY_FLOOR' in f,
        'the resample is Lanczos':
            'Image.LANCZOS' in f,
        'and the sharpen is an unsharp mask at radius 1.6, 110 per cent':
            ('ImageFilter.UnsharpMask' in f
             and 'radius=1.6' in f and 'percent=110' in f),
        '  which means ImageFilter had to be imported':
            'ImageFilter' in f,
        'the batch command can --rebuild':
            "'--rebuild'" in cc,
        '  and the flag reaches the staleness skip':
            'not rebuild and not recipe.display_copy_is_stale()' in cc,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

F = fn(NOW[MODELS])
CODE = T.python_code_only(NOW[MODELS], payloads=True)
CC = T.python_code_only(NOW[CMD], payloads=True)

mfl = re.search(r'(?m)^DISPLAY_FLOOR = (\d+)\s*$', CODE)
FLOOR = int(mfl.group(1)) if mfl else 0
ok(FLOOR >= WANTS,
   'the floor clears what the phone hero asks for: %d >= %dx%d = %d'
   % (FLOOR, HERO_CSS_PX, HERO_DPR, WANTS), FLOOR)
ok(FLOOR < WANTS * 1.5,
   '  without overshooting it - %d is a floor, not a new maximum'
   % FLOOR, FLOOR)

# ORDER MATTERS, AND IT IS NOT OBVIOUS. An unsharp mask run over an
# alpha edge haloes the transparency instead of the subject, and 322 of
# the 324 carry an alpha channel. So: flatten, THEN lift, THEN encode.
# find(), NOT index(). On the reverted tree there is no resize to find
# and index() would raise - a crash blocks a push exactly as hard as a
# failure and says far less about why. Third time today.
_at = [F.find(s) for s in ('flat.paste(', 'flat.resize(', 'flat.save(out')]
ok(all(i >= 0 for i in _at) and _at == sorted(_at),
   'the order is flatten, lift, encode - a sharpen over an alpha edge '
   'haloes the transparency rather than the subject', _at)

# GUARDS. True before this round and true after it, so they do not
# belong in claims() - a guard in a delta dict fails the control for
# being correct. Seventh time this shape has come up today.
ok('return out.getvalue()' in F,
   'GUARD: the function still returns BYTES - the caller decides where '
   'they land, which is what PX-1 split apart')
ok('.save(' not in F.replace('flat.save(out', ''),
   'GUARD: and it writes nothing but its own buffer, so no original is '
   'touched')
ok('return None' in F,
   'GUARD: an unreadable image is still not a reason to refuse a save')
ok("opts['write']" in CC and "'--write'" in CC,
   'GUARD: the batch command is still DRY by default')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

oldf = fn(BEFORE[MODELS])
ok(oldf, 'CONTROL: make_display_jpeg was already there - this round '
         'changes one function rather than adding one')
ok('resize(' not in oldf,
   'CONTROL: and it resampled NOTHING. The stretch was happening in '
   'the browser, which is the whole finding', oldf[:200])
ok('ImageFilter' not in oldf,
   'CONTROL: and ImageFilter was not even imported')


# ==========================================================================
head('3. THE FUNCTION, LIFTED AND RUN')
# ==========================================================================
# THE FUNCTION UNDER TEST IS THE SHIPPED ONE, lifted out of
# pages/models.py and exec'd the way PX-1's suite does it, because this
# suite has no Django to import the model with. The floor is lifted
# with it rather than typed here - a number written in this file would
# pass whatever the model said.
src = []
for name in ('make_display_jpeg', 'display_name_for'):
    mm = re.search(r'(?ms)^def %s\(.*?(?=^def |\Z)' % name, NOW[MODELS])
    if mm:
        src.append(mm.group(0))
ns = {'os': os, 'DISPLAY_FLOOR': FLOOR}
lifted = ok(len(src) == 2 and FLOOR > 0,
            'the two functions and the floor lifted out of pages/models.py',
            '%d function(s), floor %s' % (len(src), FLOOR))
if lifted:
    try:
        exec('\n\n'.join(src), ns)
    except Exception as e:
        lifted = ok(False, '  and they exec cleanly', e)

try:
    from PIL import Image, ImageFilter
except Exception:
    Image = ImageFilter = None

if not lifted or Image is None:
    skip('sections 3 and 4',
         'the function could not be lifted, or PIL is absent')
else:
    class FieldFile(object):
        """The two attributes make_display_jpeg actually uses."""

        def __init__(self, data, name):
            self._d, self.name = data, name
            self._f = None

        def __bool__(self):
            return bool(self.name)

        def open(self, mode='rb'):
            self._f = io.BytesIO(self._d)
            return self._f

        def read(self, *a):
            return self._f.read(*a)

        def seek(self, *a):
            return self._f.seek(*a)

        def tell(self):
            return self._f.tell()

        def close(self):
            pass

    def photo(n, m=None):
        """A PHOTOGRAPH-LIKE FIXTURE, not noise.

        A woven cloth, a hard edge and soft shading. A resampler is
        judged on structured detail; pure noise is unfair to all of
        them equally and so tells you nothing about which is better.
        """
        m = m or n
        im = Image.new('RGB', (n, m))
        px = im.load()
        random.seed(7)
        for y in range(m):
            for x in range(n):
                w = 26 if ((x // 3) + (y // 3)) % 2 == 0 else -26
                w += 18 if (x // 9) % 2 == 0 else -18
                s = 120 + 70 * math.sin(x / 190.0) * math.cos(y / 240.0)
                e = 60 if (n // 3) - 4 < x < (n // 3) + 4 else 0
                g = int(max(0, min(255, s + w + e
                                   + random.randint(-4, 4))))
                px[x, y] = (g, int(g * 0.92), int(g * 0.80))
        return im

    def png_of(im):
        b = io.BytesIO()
        im.save(b, 'PNG')
        return b.getvalue()

    def through(im, name='recipe_images/recipe-1-x-20261013120000.png'):
        out = ns['make_display_jpeg'](FieldFile(png_of(im), name))
        return out, (Image.open(io.BytesIO(out)) if out else None)

    # UNDER THE FLOOR: IT COMES UP. The 97 photos this round is for.
    for n in (320, 500, 900):
        raw, got = through(photo(n, int(n * 2 / 3)))
        if not ok(got is not None, 'a %dpx photo converts' % n):
            continue
        ok(max(got.size) == FLOOR,
           '  %dpx -> %dx%d: the long edge lands exactly on the floor'
           % (n, got.size[0], got.size[1]), got.size)
        ok(abs(got.size[0] / float(got.size[1]) - n / float(int(n * 2 / 3)))
           < 0.01,
           '  and the shape is unchanged - %.3f in, %.3f out'
           % (n / float(int(n * 2 / 3)),
              got.size[0] / float(got.size[1])))
        ok(got.mode == 'RGB' and got.format == 'JPEG',
           '  still a flattened JPEG', '%s %s' % (got.mode, got.format))

    # AT THE FLOOR AND OVER IT: NOTHING MOVES. A round that shrank the
    # library to save bytes would undo PX-1 and nobody would notice
    # until a phone.
    for n in (FLOOR, FLOOR + 400):
        raw, got = through(photo(n, n // 2))
        if ok(got is not None, 'a %dpx photo converts' % n):
            ok(got.size == (n, n // 2),
               '  %dpx is at or over the floor, so it is LEFT ALONE - '
               '%dx%d in, %dx%d out' % (n, n, n // 2,
                                        got.size[0], got.size[1]),
               got.size)

    # THE SMALLEST THING THAT CAN ARRIVE. A 1px image is a real upload
    # if somebody drags a tracking pixel in; the floor must not divide
    # by zero or round to nothing.
    raw, got = through(photo(1, 1))
    if ok(got is not None, 'CONTROL: a 1x1 image still converts'):
        ok(min(got.size) >= 1 and max(got.size) == FLOOR,
           '  and comes out %dx%d - no zero dimension, no crash'
           % got.size, got.size)

    # THE FLATTEN IS STILL DEFENCE, and the sharpen must not have
    # turned the white into a grey halo.
    tr = Image.new('RGBA', (60, 60), (255, 0, 0, 0))
    raw = ns['make_display_jpeg'](FieldFile(png_of(tr), 'x/y.png'))
    if ok(raw is not None,
          'CONTROL: a fully TRANSPARENT png still converts'):
        pxl = Image.open(io.BytesIO(raw)).convert('RGB').getpixel((30, 30))
        ok(max(abs(v - 255) for v in pxl) <= 2,
           '  and still lands on WHITE after the lift and the sharpen - '
           '%s' % (pxl,), '%s' % (pxl,))

    # UNREADABLE IS STILL NOT A CRASH.
    ok(ns['make_display_jpeg'](FieldFile(b'not an image', 'x/y.png'))
       is None,
       'CONTROL: an unreadable file still returns None rather than '
       'raising')
    ok(ns['make_display_jpeg'](FieldFile(b'', '')) is None,
       'CONTROL: and so does no file at all')


# ==========================================================================
head('4. BETTER THAN THE BROWSER, MEASURED')
# ==========================================================================
# THE CLAIM IS COMPARATIVE, SO THE MEASUREMENT HAS TO BE TOO. Nothing
# invents detail. What this round says is that doing the stretch once
# on the server beats the browser doing it on every page load - and
# that is a claim with a number attached.
#
# THE METHOD. A detailed 1200px photograph is the TRUTH. Downscale it
# to 500/700/900 to stand in for what is actually on the volume, then
# bring each one back up to the floor twice: once the way this round
# does it, once with the bilinear stretch a browser reaches for. Then
# measure each result against the truth it came from. Lower is closer.
if not lifted or Image is None:
    skip('section 4', 'PIL is absent')
else:
    def rms(a, b):
        pa, pb = a.convert('L').load(), b.convert('L').load()
        w, h = a.size
        xs, ys = range(0, w, 3), range(0, h, 3)
        t = 0
        for y in ys:
            for x in xs:
                d = pa[x, y] - pb[x, y]
                t += d * d
        return math.sqrt(t / float(len(list(xs)) * len(list(ys))))

    truth = photo(FLOOR, FLOOR)
    print('')
    print('    source   server      browser     server is')
    print('             (this round) (bilinear)  closer by')
    print('    ' + '-' * 48)
    wins = []
    for n in (500, 700, 900):
        small = truth.resize((n, n), Image.LANCZOS)
        raw, srv = through(small)
        if srv is None:
            ok(False, 'the %dpx stand-in converts' % n)
            continue
        srv = srv.convert('RGB')
        bro = small.resize(srv.size, Image.BILINEAR)
        a, b = rms(truth, srv), rms(truth, bro)
        gain = 100.0 * (b - a) / b if b else 0.0
        wins.append((n, a, b, gain))
        print('    %4dpx   %8.2f     %8.2f     %5.1f%%'
              % (n, a, b, gain))
    print('')
    for n, a, b, gain in wins:
        ok(a < b,
           'a %dpx photo is CLOSER to the truth done here than stretched '
           'in the browser - %.2f against %.2f' % (n, a, b),
           '%.2f vs %.2f' % (a, b))
    if wins:
        GAIN = '%.0f and %.0f per cent' % (
            min(g for _, _, _, g in wins), max(g for _, _, _, g in wins))
    ok(wins and min(g for _, _, _, g in wins) > 10.0,
       'and the worst of the three still beats it by more than 10 per '
       'cent, which is why this round is worth the bytes',
       '%r' % ([round(g, 1) for _, _, _, g in wins],))

    # AND WHAT IT COSTS. The honest other half: the files get bigger.
    #
    # THIS ASKED THE WRONG QUESTION UNTIL 22 OCT 2026, and the push gate
    # caught it on Demetri's laptop while it passed on the machine that
    # wrote it. It compared the 1200px JPEG with the PNG of the 500px
    # ORIGINAL - two different pictures - and PX-1's `jpg < png` was a
    # fair comparison only because PX-1 resized nothing. Once this round
    # quadruples the area the answer lands on a knife edge, and which
    # side it lands on is decided by the PNG ENCODER: 421 KB here, 357
    # KB there, from the same generator and the same seed. The JPEG was
    # 372,420 bytes on both.
    #
    # SO ASK IT LIKE FOR LIKE. The same pixels, both ways. That is a
    # claim about the format rather than about whoever built zlib, and
    # it is the claim that actually justifies shipping JPEG at all.
    #
    # THE LESSON IS IN THE SHAPE, not the subject. Every other
    # measurement in this section is an inequality with room in it -
    # "closer than the browser", "more than 10 per cent" - and all of
    # them survived the move between machines. This one was a bare
    # `a < b` with nothing to spare.
    small = truth.resize((500, 500), Image.LANCZOS)
    raw, lifted = through(small)
    png_in = png_of(small)
    png_same = png_of(lifted.convert('RGB'))
    print('')
    print('    the cost, and it is a real one:')
    print('      500px PNG in      %7d  (%4.0f KB)'
          % (len(png_in), len(png_in) / 1024.0))
    print('      1200px JPEG out   %7d  (%4.0f KB)   %+.0f%% on the '
          'original' % (len(raw), len(raw) / 1024.0,
                        100.0 * (len(raw) - len(png_in)) / len(png_in)))
    print('      the SAME pixels as PNG %7d  (%4.0f KB)'
          % (len(png_same), len(png_same) / 1024.0))
    print('')
    ok(len(raw) < len(png_same) / 2.0,
       'at the size it now ships, the JPEG is %.0f per cent of the PNG '
       'of the SAME pixels - %.0f KB against %.0f KB'
       % (100.0 * len(raw) / len(png_same), len(raw) / 1024.0,
          len(png_same) / 1024.0),
       '%d vs %d' % (len(raw), len(png_same)))
    # AND THE COST IS NAMED RATHER THAN DISCLAIMED. A round that makes
    # files bigger should say by how much, every time it runs, on the
    # machine it ran on.
    ok(len(raw) < 4 * len(png_in),
       '  and the cost of the lift is bounded - it is not four times '
       'the area in four times the bytes',
       '%d vs %d' % (len(raw), len(png_in)))


# ==========================================================================
head('5. THE COMMAND')
# ==========================================================================
# WHY THE FLAG EXISTS AT ALL. display_copy_is_stale() decides from the
# FILENAME - stem plus .jpg - and this round changes what a display
# copy CONTAINS without changing what it is called. So every one of the
# copies already on the volume looks fresh and would never be replaced.
ok('display_copy_is_stale' in CODE,
   'staleness is still decided by display_copy_is_stale')
stale = re.search(r'(?ms)def display_copy_is_stale.*?(?=\n    def |\Z)',
                  CODE)
ok(stale and 'display_name_for' in stale.group(0),
   'and it still decides from the NAME, which is exactly why --rebuild '
   'had to exist')
ok('--rebuild' in NOW[CMD] and 'store_true' in NOW[CMD],
   'the flag is a switch, not a value')
# IT MUST NOT IMPLY --write. A rebuild that wrote without being asked
# would be the one command in the house that does.
ok("opts['write']" in CC,
   'and --write is still read separately, so --rebuild alone is a '
   'REPORT of what would change')
ok(not re.search(r"rebuild.{0,40}opts\['write'\]\s*=", CC),
   '  and nothing lets a rebuild turn writing on by itself')
ok('.save(' not in CC.replace('display.save(', '')
   or 'recipe_image.save' not in CC,
   'the command still never writes an ORIGINAL')
ok('PX-2' in NOW[CMD], 'and the command says which round gave it the flag')


# ==========================================================================
head("6. PX-1's OWN SUITE, RUN")
# ==========================================================================
# FOUR OF ITS CLAIMS MOVED IN THIS ROUND's PATCHER. A claim moved is a
# claim that has to still fit, so the suite it was moved in is run here
# rather than trusted.
PP = os.path.join(ROOT, PHOTOS)
nowp, wasp = read(PP), was(PP)
ok('len(jpg) < len(png) / 2' in wasp,
   'CONTROL: PX-1 asked for HALF the bytes, which a four-times-the-area '
   'upscale cannot give')
ok('len(jpg) < len(png) / 2' not in nowp and 'len(jpg) < len(png)' in nowp,
   '  corrected to the claim it was really making: still smaller')
ok('EVERY PIXEL IS KEPT' in wasp or 'out.size == (w, h)' in wasp,
   'CONTROL: and it asked that the size come back IDENTICAL')
ok('NO PIXEL IS LOST' in nowp,
   '  corrected to what PX-1 actually rested on: nothing is lost')
ok("ns = {'os': os}" in wasp and 'DISPLAY_FLOOR' not in wasp,
   'CONTROL: and its lift carried nothing but os, because that was '
   'everything the function referenced')
ok('DISPLAY_FLOOR' in nowp and "re.search(r'(?m)^DISPLAY_FLOOR" in nowp,
   '  corrected to lift the floor out of the module rather than type it')
ok('it cannot make them sharp' in wasp,
   'CONTROL: and it closed by disclaiming exactly what this round does')
ok('it cannot make them sharp' not in nowp
   and 'Better, not fixed' in nowp,
   '  corrected, not quietly dropped - and it still refuses to oversell')
ok(MARK in nowp, '  and it says which round corrected it and why')

# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN PX-1's own suite IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(PHOTOS) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(PHOTOS))



# ==========================================================================
head('7. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# WHAT THIS ROUND DID NOT TOUCH. The templates draw the hero; the
# geometry is PX-1's and unchanged. This round changes the PIXELS
# behind it, not the box in front of it.
HERO = os.path.join(ROOT, 'pages', 'templates', 'view_recipe.html')
if os.path.isfile(HERO):
    ok(not os.path.isfile(HERO + SUFFIX),
       'no template was touched - the hero geometry is PX-1 and stands')

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES + (PP,):
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
ok('DISPLAY_FLOOR' in gate and '--rebuild' in gate,
   'both sentinels are on the push gate, so a half-applied round is '
   'caught before it is pushed')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_photo_floor as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the 324 copies on the volume have been rebuilt.')
print('  The command can do it and has never been run there. It is')
print('  dry by default, so the first real run is a report - and the')
print('  round ships to new uploads only until it is run with')
print('  --rebuild --write.')
print('')
print('  Not that a soft photo is now a sharp photo. A 500px picture')
print('  will never be a 1600px picture. What is proved above is the')
print('  comparative claim: closer to the truth than the browser got,')
# MEASURED, NOT TYPED - 22 Oct 2026. This read "between 27 and 76 per
# cent", which were the numbers on the machine that wrote the round.
# Demetri's laptop measures 30 to 68 for the same fixture, because
# Lanczos is not identical between Pillow builds. A range typed into
# prose is a number nobody updates.
print('  by between %s on the fixture, done once' % GAIN)
print('  instead of on every page load.')
print('')
print('  Not that the files are small. THEY GET BIGGER - four times')
print('  the area for the ones under the floor, and section 4 prints')
print('  by how much. This used to end "and they are still under the')
print('  PNGs they replaced", which was true of the machine it was')
print('  written on and false on the next one. A 1200px JPEG is not')
print('  comparable with the PNG of the 500px picture it came from;')
print('  what it is comparable with is the PNG of ITSELF, and against')
print('  that it is a small fraction.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
