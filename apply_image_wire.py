# -*- coding: utf-8 -*-
"""apply_image_wire.py - round RI-1, 17 Oct 2026.

EVERY JPEG RECIPE UPLOAD HAS ALWAYS FAILED.

Demetri, 17 Oct, uploading a photographed recipe:

    The recipe reader could not be reached. Error code: 400 -
    messages.0.content.0.image.source.base64: The image was specified
    using the image/jpeg media type, but the image appears to be a
    image/png image

His file is a genuine JPEG - Windows reports Type: JPEG File, 91.8 KB,
739 x 1600. Nothing is wrong with it.

THE READER CONVERTS EVERY IMAGE TO PNG:

    image = Image.open(file)
    buffered = BytesIO()
    image.save(buffered, format="PNG")        <- always PNG
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

AND THEN DECLARES THE MEDIA TYPE FROM THE FILENAME:

    file_ext = file_name.split('.')[-1].lower()     recipe_extras.py
    "media_type": MEDIA_TYPES[file_type],           ai_extract.py

Upload a .png and the two agree by coincidence. Upload a .jpg and the
call says JPEG while carrying PNG bytes, and the API - which reads the
bytes - refuses it. So the whole jpg/jpeg path has never worked, and
the only reason it is not reported constantly is that a screenshot
arrives as a PNG.

AND THE FILE SAYS SO ALREADY. Above the map:

    THE EXTENSION IS NOT THE MEDIA TYPE.

A previous round fixed the SPELLING - image/jpg is not registered, the
name is image/jpeg - and left the SOURCE OF THE DECISION alone. The
extension still chose. Half a fault fixed reads exactly like a whole
one until somebody uploads a photograph.

WHY NOT THE ONE-LINE FIX

    Writing 'image/png' at the call site works today and is wrong the
    day anyone changes the save format, because the two statements
    would be in different functions again. extract_text_from_image is
    the only thing that knows what it produced, so it RETURNS that
    alongside the bytes, and the call site uses what it was handed.
    One fact, declared once, by the function that owns it.

    The format itself is named once more - IMAGE_WIRE_FORMAT - and the
    save and the media type are both derived from it, so a change to
    one is a change to both.

    And the call REFUSES rather than guesses: an image with no media
    type raises instead of falling back to the extension, because a
    fallback that can be wrong is the thing being removed.

MEDIA_TYPES KEEPS BOTH JOBS AND GAINS A THIRD. Its keys are still the
extensions the view accepts - test_ai_models asserts the view and the
map agree, and that claim is untouched - and its values are now what
the wire media type is CHECKED against, so every one of them stays
live. A map nobody reads is dead weight.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_imagewire'
MOD = os.path.join('pages', 'views', 'recipes', 'ai_extract.py')
VIEW = os.path.join('pages', 'views', 'recipes', 'recipe_extras.py')
SUITE = 'test_ai_models.py'
ME = 'test_image_wire.py'
PATCHER = 'apply_image_wire.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 100, 101
ALIAS_WAS, ALIAS_NOW = 109, 111
ALIAS_P_WAS, ALIAS_S_WAS = 55, 54
ALIAS_P_NOW, ALIAS_S_NOW = 56, 55

# ------------------------------------------------------------- the format
FMT_WAS = """MEDIA_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}"""

FMT_NOW = """MEDIA_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}

# WHAT ACTUALLY GOES ON THE WIRE, named once. RI-1, 17 Oct 2026.
#
# extract_text_from_image re-encodes every upload through PIL, so the
# bytes the API receives are this format whatever the file was called.
# The save and the media type are both derived from the one name, so a
# round that changes the format cannot change only half of it.
#
# This is the other half of the fault the note above describes. That
# round took `image/{ext}` out - a spelling no registry has - and left
# the EXTENSION choosing the media type, so a genuine .jpg announced
# JPEG while carrying PNG and the API refused it. Every photographed
# recipe failed; a screenshot worked, because a screenshot is a PNG.
IMAGE_WIRE_FORMAT = 'PNG'
IMAGE_WIRE_MEDIA_TYPE = 'image/' + IMAGE_WIRE_FORMAT.lower()"""

# ------------------------------------------------------------ the encoder
ENC_WAS = '''def extract_text_from_image(file):
    """For images, we'll pass directly to Claude's vision API"""
    # Convert to base64 for Claude API
    try:
        image = Image.open(file)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")'''

ENC_NOW = '''def extract_text_from_image(file):
    """Re-encode an upload for the vision API.

    RETURNS (base64, media_type). RI-1, 17 Oct 2026 - it returned the
    bytes alone, and the caller worked out the media type from the
    FILENAME. This function is the only thing that knows what it
    produced, so it is the only thing entitled to say so; a .jpg
    announced as JPEG while carrying PNG is what the API refused, and
    it refused every photographed recipe.
    """
    try:
        image = Image.open(file)
        buffered = BytesIO()
        image.save(buffered, format=IMAGE_WIRE_FORMAT)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64, IMAGE_WIRE_MEDIA_TYPE
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")'''

# --------------------------------------------------------------- the call
SIG_WAS = """def extract_recipe_with_ai(content, file_type):"""
SIG_NOW = """def extract_recipe_with_ai(content, file_type, media_type=None):"""

CALL_WAS = """                                        "media_type": MEDIA_TYPES[file_type],"""
CALL_NOW = """                                        "media_type": media_type,"""

GUARD_WAS = """    last = None
    for attempt in range(ATTEMPTS):"""

GUARD_NOW = """    # RI-1, 17 Oct 2026 - IT REFUSES RATHER THAN GUESSES.
    #
    # The media type is whatever extract_text_from_image produced, and
    # it is passed in. There is deliberately NO fallback to the map
    # keyed on the extension: that fallback is the fault this round
    # removes, and one that can be wrong is worse than none because it
    # fails at the API rather than here.
    #
    # The value is still checked against the map, so every registered
    # name in it stays live and a typo cannot reach the wire.
    if file_type in ('jpg', 'jpeg', 'png'):
        if not media_type:
            raise RecipeExtractionError(
                'The recipe reader was handed an image with no media '
                'type. Your file is fine - this is a fault on our side.')
        if media_type not in set(MEDIA_TYPES.values()):
            raise RecipeExtractionError(
                'The recipe reader produced an image format the API does '
                'not accept. Your file is fine - this is a fault on our '
                'side.')

    last = None
    for attempt in range(ATTEMPTS):"""

# --------------------------------------------------------------- the view
VIEW_WAS = """            elif file_ext in ['jpg', 'jpeg', 'png']:
                text_content = extract_text_from_image(uploaded_file)"""

VIEW_NOW = """            elif file_ext in ['jpg', 'jpeg', 'png']:
                # RI-1, 17 Oct 2026 - THE ENCODER SAYS WHAT IT MADE.
                # This took the bytes and left the media type to be
                # worked out from file_ext, which is how a genuine JPEG
                # came to be announced as JPEG while carrying PNG.
                text_content, image_media_type = \\
                    extract_text_from_image(uploaded_file)"""

VIEW_INIT_WAS = """            file_ext = file_name.split('.')[-1].lower()"""
VIEW_INIT_NOW = """            file_ext = file_name.split('.')[-1].lower()
            # The extension still decides WHETHER this is an image. It
            # no longer decides what the bytes are - see RI-1 below.
            image_media_type = None"""

VIEW_CALL_WAS = """            extracted_data = extract_recipe_with_ai(text_content, file_ext)"""
VIEW_CALL_NOW = """            extracted_data = extract_recipe_with_ai(
                text_content, file_ext, image_media_type)"""

# -------------------------------------------------------------- the suite
SUITE_WAS = """    r, e, calls = drive(json.dumps(GOOD), content='QUJD', ftype='jpg')
    src = calls[0]['messages'][0]['content'][0]['source'] if calls else {}
    ok(src.get('media_type') == 'image/jpeg',
       '  MEASURED: a .jpg upload sends media_type image/jpeg',
       src.get('media_type'))"""

SUITE_NOW = """    # RI-1, 17 Oct 2026 - THE EXTENSION NO LONGER DECIDES.
    #
    # This drove a .jpg and asserted the wire said image/jpeg, which
    # was true and was the bug: the reader re-encodes every upload to
    # PNG, so a .jpg announced JPEG while carrying PNG bytes and the
    # API refused it. The media type is passed in by the encoder now,
    # so what is asserted is that the wire carries WHAT IT WAS GIVEN
    # rather than what the filename implied.
    r, e, calls = drive(json.dumps(GOOD), content='QUJD', ftype='jpg',
                        media_type=mod.IMAGE_WIRE_MEDIA_TYPE)
    src = calls[0]['messages'][0]['content'][0]['source'] if calls else {}
    ok(src.get('media_type') == mod.IMAGE_WIRE_MEDIA_TYPE,
       '  MEASURED: a .jpg upload sends the media type the ENCODER '
       'produced, %s - not the one its name implies'
       % mod.IMAGE_WIRE_MEDIA_TYPE, src.get('media_type'))
    # AND IT REFUSES AN IMAGE WITH NO MEDIA TYPE rather than falling
    # back to the extension, which is the fault RI-1 removed.
    r2, e2, calls2 = drive(json.dumps(GOOD), content='QUJD', ftype='jpg')
    ok(r2 is None and e2 is not None and not calls2,
       '  and an image with no media type never reaches the API',
       (r2, e2, len(calls2)))"""

DRIVE_WAS = """def drive(reply, content='5 tablespoons Smoked Paprika', ftype='docx'):"""
DRIVE_NOW = """def drive(reply, content='5 tablespoons Smoked Paprika', ftype='docx',
          media_type=None):"""

DRIVE_CALL_WAS = """                return (mod.extract_recipe_with_ai(content, ftype), None,
                        client.calls)"""
DRIVE_CALL_NOW = """                return (mod.extract_recipe_with_ai(content, ftype,
                                                   media_type), None,
                        client.calls)"""


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
    raise SystemExit('RI-1 REFUSED: %s' % msg)


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


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    mp = os.path.join(root, MOD)
    vp = os.path.join(root, VIEW)
    sp = os.path.join(root, SUITE)

    if 'IMAGE_WIRE_FORMAT' in read(mp):
        print('RI-1  already applied - the encoder says what it made.')
        return 0

    out = {}

    # THE FAULT IS READ, NOT REMEMBERED.
    m = read(mp)
    if 'format="PNG"' not in m:
        refuse('%s does not re-encode to PNG, so the mismatch this round '
               'fixes is not the one on disk' % MOD)
    if 'MEDIA_TYPES[file_type]' not in m:
        refuse('%s no longer picks the media type from the extension'
               % MOD)
    v = read(vp)
    if "file_ext = file_name.split('.')[-1].lower()" not in v:
        refuse('%s no longer derives an extension from the name' % VIEW)

    m = swap(m, FMT_WAS, FMT_NOW, '%s (the wire format)' % MOD)
    m = swap(m, ENC_WAS, ENC_NOW, '%s (the encoder)' % MOD)
    m = swap(m, SIG_WAS, SIG_NOW, '%s (the signature)' % MOD)
    m = swap(m, GUARD_WAS, GUARD_NOW, '%s (the guard)' % MOD)
    m = swap(m, CALL_WAS, CALL_NOW, '%s (the call)' % MOD)
    out[mp] = m

    v = swap(v, VIEW_INIT_WAS, VIEW_INIT_NOW, '%s (the init)' % VIEW)
    v = swap(v, VIEW_WAS, VIEW_NOW, '%s (the image branch)' % VIEW)
    v = swap(v, VIEW_CALL_WAS, VIEW_CALL_NOW, '%s (the call)' % VIEW)
    out[vp] = v

    s = read(sp)
    s = swap(s, DRIVE_WAS, DRIVE_NOW, '%s (the driver)' % SUITE)
    s = swap(s, DRIVE_CALL_WAS, DRIVE_CALL_NOW, '%s (the driven call)'
             % SUITE)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the media-type claim)' % SUITE)
    out[sp] = s

    # ------------------------------------------------------- the gates
    for p, t, name in ((mp, m, MOD), (vp, v, VIEW), (sp, s, SUITE)):
        try:
            import ast
            ast.parse(t)
        except SyntaxError as e:
            refuse('%s would no longer parse - %s' % (name, e))
    if 'MEDIA_TYPES[file_type]' in m:
        refuse('%s still takes the media type from the extension' % MOD)
    if m.count('IMAGE_WIRE_FORMAT') < 2:
        refuse('%s: the format is not used where it is saved' % MOD)
    if 'format=IMAGE_WIRE_FORMAT' not in m:
        refuse('%s: the save does not use the named format' % MOD)
    if 'return img_base64, IMAGE_WIRE_MEDIA_TYPE' not in m:
        refuse('%s: the encoder does not report what it produced' % MOD)
    # THE MAP STAYS LIVE. Its values are what the wire is checked against.
    if 'set(MEDIA_TYPES.values())' not in m:
        refuse('%s: MEDIA_TYPES has no reader left, which makes it dead '
               'weight' % MOD)
    # The wire media type is DERIVED from the format, not typed twice.
    if "IMAGE_WIRE_MEDIA_TYPE = 'image/' + IMAGE_WIRE_FORMAT.lower()" \
            not in m:
        refuse('%s does not derive the wire media type from the format, '
               'so the two can drift' % MOD)

    # ------------------------------------------------------- registered
    p = os.path.join(root, PS1)
    t = read(p)
    t = swap(t, """    'test_danger_pair.py'
)""", """    'test_danger_pair.py',
    'test_image_wire.py'
)""", '%s ($suites)' % PS1)
    t = swap(t, """    # -------------------------------------------- HL-1, 12 Oct 2026""",
             """    # ------------------------------------------------- RI-1, 17 Oct 2026
    @{ File = 'pages\\views\\recipes\\ai_extract.py'; Text = 'IMAGE_WIRE_MEDIA_TYPE'; What = 'RI-1: the encoder says what it produced' },
    @{ File = 'pages\\views\\recipes\\ai_extract.py'; Text = 'MEDIA_TYPES[file_type]'; Absent = $true; What = 'RI-1: and the extension no longer picks the media type' },
    # -------------------------------------------- HL-1, 12 Oct 2026""",
             '%s ($sentinels)' % PS1)
    out[p] = t

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), """    'test_danger_pair.py',
]""", """    'test_danger_pair.py',
    # RI-1, 17 Oct 2026 - every JPEG recipe upload failed, because the
    # reader re-encodes to PNG and then announced the media type from
    # the filename. Wide from birth.
    'test_image_wire.py',
]""", '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), """    '.bak_dangerpair',""",
                  """    '.bak_dangerpair',
    # RI-1, 17 Oct 2026 - a live fault, found by uploading a recipe.
    '.bak_imagewire',""", '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'RI-1, 17 Oct 2026 - this round own suite',
                  '%s (CONVERTED_N)' % WD)

    import glob as _glob
    _al = [os.path.basename(f)
           for f in sorted(_glob.glob(os.path.join(root, '*.py')))
           if re.search(r'^code_only\s*=\s*alv_tree\.code_only',
                        read(f), re.M)]
    _pat = [f for f in _al if f.startswith('apply_')]
    _sui = [f for f in _al if f.startswith('test_')]
    if len(_al) < ALIAS_NOW or len(_pat) < ALIAS_P_NOW \
            or len(_sui) < ALIAS_S_NOW:
        refuse('the alias count on disk is %d (%d patchers, %d suites) and '
               'this round would write %d (%d, %d) - more than exist'
               % (len(_al), len(_pat), len(_sui),
                  ALIAS_NOW, ALIAS_P_NOW, ALIAS_S_NOW))

    p = os.path.join(root, CO)
    t2 = bump(read(p), 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
              'RI-1, 17 Oct 2026 - this round own patcher and suite',
              '%s (the alias count)' % CO)
    t2 = swap(t2, "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_WAS, ALIAS_S_WAS),
              "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_NOW, ALIAS_S_NOW),
              '%s (the alias split)' % CO)
    out[p] = t2

    if CHECK:
        print('RI-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v2 in out.items():
        backup(k)
        write(k, v2)
    print('RI-1 applied.')
    print('   the encoder returns the media type it produced')
    print('   the extension decides WHETHER, not WHAT')
    print('   and an image with no media type is refused, not guessed')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
