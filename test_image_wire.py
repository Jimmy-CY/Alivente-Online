# -*- coding: utf-8 -*-
"""test_image_wire.py - round RI-1, 17 Oct 2026.

EVERY JPEG RECIPE UPLOAD HAS ALWAYS FAILED.

Demetri, 17 Oct, uploading a photographed recipe:

    The image was specified using the image/jpeg media type, but the
    image appears to be a image/png image

His file is a genuine JPEG - Windows reports Type: JPEG File, 91.8 KB,
739 x 1600. Nothing was wrong with it.

The reader re-encodes EVERY upload through PIL to PNG, and then took
the media type from the FILENAME. A .png agreed by coincidence. A .jpg
announced JPEG while carrying PNG, and the API reads the bytes.

WHAT THIS SUITE PROVES THAT READING THE DIFF CANNOT

    Section 2 encodes a REAL JPEG - three by three pixels, built here,
    saved as JPEG by PIL - and asserts two things about what comes
    back: the bytes begin with the PNG signature, and the media type
    returned beside them says PNG. That is the whole fault in two
    measurements, and it needs an image to make.

    Section 3 drives the extractor against a fake client and reads the
    media type off the wire, then drives it again with none and asserts
    the call never happens. A fallback that can be wrong is what this
    round removed, so "it refuses" is a claim worth holding.

WHAT IT CANNOT PROVE
    That the API accepts the result. That needs the API, a key, and his
    network, none of which belong in a suite. What it proves is that
    the bytes and the declaration now come from the same place, which
    is the only thing that was ever wrong.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------


import base64
import io
import json
import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_imagewire'
MOD = os.path.join('pages', 'views', 'recipes', 'ai_extract.py')
VIEW = os.path.join('pages', 'views', 'recipes', 'recipe_extras.py')
ME = 'test_image_wire.py'
PATCHER = 'apply_image_wire.py'
PS1 = 'Push-PendingChanges.ps1'

CONVERTED_NOW, ALIAS_NOW = 101, 111
PNG_SIG = b'\x89PNG\r\n\x1a\n'
JPEG_SIG = b'\xff\xd8\xff'

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def as_ri1_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


M_PATH = os.path.join(ROOT, MOD)
V_PATH = os.path.join(ROOT, VIEW)
M_NOW, V_NOW = read(M_PATH), read(V_PATH)
APPLIED = os.path.isfile(M_PATH + SUFFIX)
M_WAS = read(M_PATH + SUFFIX) if APPLIED else M_NOW
V_WAS = read(V_PATH + SUFFIX) if os.path.isfile(V_PATH + SUFFIX) else V_NOW

print('')
print('test_image_wire.py - round RI-1, 17 Oct 2026')
print('  reader   : %s' % MOD)
print('  view     : %s' % VIEW)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE ENCODER SAYS WHAT IT PRODUCED')
# ==========================================================================
ok('IMAGE_WIRE_FORMAT' in M_NOW,
   'the wire format is named once')
ok("IMAGE_WIRE_MEDIA_TYPE = 'image/' + IMAGE_WIRE_FORMAT.lower()" in M_NOW,
   '  and the media type is DERIVED from it, not typed twice')
ok('format=IMAGE_WIRE_FORMAT' in M_NOW,
   '  and the save uses the same name, so the two cannot drift')
ok('return img_base64, IMAGE_WIRE_MEDIA_TYPE' in M_NOW,
   'the encoder returns the media type beside the bytes')

ok('MEDIA_TYPES[file_type]' not in M_NOW,
   'and the EXTENSION no longer picks the media type')
ok(not APPLIED or 'MEDIA_TYPES[file_type]' in M_WAS,
   'CONTROL: it did, which is why a genuine .jpg was announced as JPEG '
   'while carrying PNG')
ok(not APPLIED or 'image.save(buffered, format="PNG")' in M_WAS,
   'CONTROL: and the same file re-encoded every upload to PNG, two '
   'functions away from where the media type was decided')

# THE MAP KEEPS A READER, so it is not dead weight.
ok('set(MEDIA_TYPES.values())' in M_NOW,
   'MEDIA_TYPES still has a reader - the wire value is checked against '
   'it, so every registered name in it stays live')

# THE VIEW PASSES IT THROUGH.
ok('text_content, image_media_type' in V_NOW,
   '%s takes both from the encoder' % VIEW)
ok('extract_recipe_with_ai(\n                text_content, file_ext, '
   'image_media_type)' in V_NOW
   or 'image_media_type)' in V_NOW,
   '  and hands the media type on')
ok("file_ext = file_name.split('.')[-1].lower()" in V_NOW,
   'the extension still decides WHETHER a file is an image')


# ==========================================================================
head('2. A REAL JPEG, ENCODED, AND WHAT COMES BACK')
# ==========================================================================
# The fault needs an image to show. This builds a genuine JPEG, runs it
# through the reader's own encoder, and asks two questions of the
# result: what are the bytes, and what does it say they are.
try:
    from PIL import Image
    have_pil = True
except Exception:
    have_pil = False

mod = None
try:
    # The reader reads settings.ANTHROPIC_API_KEY at call time.  Imported
    # standalone there is no Django, so configure a placeholder the way
    # test_ai_models.py already does - otherwise the very first line of
    # the function under test raises and every check below passes or
    # fails for the wrong reason.
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        dj_settings.configure(ANTHROPIC_API_KEY='test-key-not-a-real-one',
                              DEBUG=False)
    sys.path.insert(0, os.path.join(ROOT, 'pages', 'views', 'recipes'))
    import importlib.util as _u
    _spec = _u.spec_from_file_location('ri1_ai_extract', M_PATH)
    mod = _u.module_from_spec(_spec)
    _spec.loader.exec_module(mod)
except Exception as e:
    print('  !! the reader could not be imported: %s' % str(e)[:120])

if not have_pil or mod is None:
    skip('a real JPEG through the encoder', 'PIL or the module is absent')
else:
    buf = io.BytesIO()
    Image.new('RGB', (3, 3), (200, 40, 40)).save(buf, format='JPEG')
    raw = buf.getvalue()
    ok(raw.startswith(JPEG_SIG),
       'the fixture really is a JPEG - it starts %r' % raw[:3])

    got = mod.extract_text_from_image(io.BytesIO(raw))
    ok(isinstance(got, tuple) and len(got) == 2,
       'the encoder returns the bytes AND what they are', type(got))
    if isinstance(got, tuple) and len(got) == 2:
        b64, media = got
        out_bytes = base64.b64decode(b64)
        print('      in  : %r  (%d bytes)' % (raw[:4], len(raw)))
        print('      out : %r  (%d bytes), declared %s'
              % (out_bytes[:4], len(out_bytes), media))
        ok(out_bytes.startswith(PNG_SIG),
           'a JPEG goes in and PNG BYTES come out - the re-encode this '
           'round did not change')
        ok(media == 'image/png',
           '  and the media type beside them says png, which is what '
           'they are', media)
        ok(media == mod.IMAGE_WIRE_MEDIA_TYPE,
           '  and it is the one name, not a second opinion')
        # THE FAULT, STATED AS THE COMPARISON IT WAS.
        ok(mod.MEDIA_TYPES.get('jpg') != media,
           'the extension would have said %s for this file, which is '
           'what the API refused'
           % mod.MEDIA_TYPES.get('jpg'))


# ==========================================================================
head('3. THE WIRE CARRIES WHAT THE ENCODER SAID')
# ==========================================================================
# Driven against a fake client, so the media type can be read off the
# call rather than inferred from the source.
if mod is None:
    skip('the extractor against a fake client', 'the module is absent')
else:
    class _Reply(object):
        def __init__(self, text):
            self.content = [type('C', (), {'text': text})()]

    class _Msgs(object):
        def __init__(self, outer):
            self.outer = outer

        def create(self, **kw):
            self.outer.calls.append(kw)
            return _Reply(self.outer.reply)

    class _Client(object):
        def __init__(self, reply):
            self.reply, self.calls = reply, []
            self.messages = _Msgs(self)

    GOOD = {"name": "X", "ingredients": [], "instructions": []}

    def drive(ftype, media_type=None):
        c = _Client(json.dumps(GOOD))
        real, real_sleep = mod.anthropic.Anthropic, mod.time.sleep
        mod.anthropic.Anthropic = lambda **kw: c
        mod.time.sleep = lambda *a, **k: None
        try:
            try:
                return mod.extract_recipe_with_ai('QUJD', ftype,
                                                  media_type), None, c.calls
            except Exception as e:
                return None, e, c.calls
        finally:
            mod.anthropic.Anthropic = real
            mod.time.sleep = real_sleep

    r, e, calls = drive('jpg', mod.IMAGE_WIRE_MEDIA_TYPE)
    src = (calls[0]['messages'][0]['content'][0]['source']
           if calls else {})
    ok(src.get('media_type') == mod.IMAGE_WIRE_MEDIA_TYPE,
       'a .jpg upload puts %s on the wire - what the encoder made, not '
       'what the name implied' % mod.IMAGE_WIRE_MEDIA_TYPE,
       src.get('media_type'))

    r2, e2, calls2 = drive('jpg', None)
    ok(r2 is None and e2 is not None and not calls2,
       'and an image with no media type is REFUSED, never guessed - the '
       'call does not happen', (r2, type(e2).__name__, len(calls2)))
    ok(e2 is not None and 'fault on our side' in str(e2),
       '  with a reason fit to show the person who uploaded',
       str(e2)[:90])


# ==========================================================================
head('4. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_dangerpair' in _r
       and _r.index(SUFFIX) > _r.index('.bak_dangerpair'),
       '  and sits after .bak_dangerpair', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'IMAGE_WIRE_MEDIA_TYPE'" in ps1,
   'and holds a sentinel on the one name')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

wd = as_ri1_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when RI-1 left it'
   % CONVERTED_NOW)
co = as_ri1_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('')
    print('  WHAT THIS ROUND IS, in one line:')
    print('  The recipe reader re-encodes every upload to PNG and then')
    print('  announced the media type from the filename, so every')
    print('  genuine JPEG was sent as JPEG while carrying PNG and the')
    print('  API refused it. The encoder says what it made now.')
sys.exit(1 if failed else 0)
