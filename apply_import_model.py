# -*- coding: utf-8 -*-
"""SECTION R, ROUND R1 - THE AI IMPORT TOOL HAS BEEN DEAD SINCE 15 JUNE

Demetri, 1 Oct 2026, with a Word document attached: "I am trying to
import the following recipe using the AI Import tool. I cannot understand
how this can not be working !!!"

The file is fine. python-docx reads BBQ_Chicken_Rub.docx here and returns
477 characters over 16 paragraphs - every ingredient, both instruction
steps, nothing malformed. No other file would have worked either.

-------------------------
WHAT IS ACTUALLY WRONG
-------------------------
ai_extract.py asked for the model `claude-sonnet-4-20250514`.

That model was RETIRED ON 15 JUNE 2026. Every call since has come back
model_not_found. The retry loop then tried twice more - sleeping 3s, then
6s - and returned None, and the view turned None into

    "Could not extract recipe data. Please try a different file."

which blames the file for a dead model, and takes nine seconds to do it.

------------------------------------------
WHY THIS CALL SITE AND NOT THE OTHER THREE
------------------------------------------
The tree calls Anthropic from four places and each HARD-CODES ITS OWN
MODEL STRING:

    recipe_ai.py            claude-sonnet-4-6     current
    invoice_verification.py claude-haiku-4-5      current
    portfolio_insights.py   claude-haiku-4-5      current
    ai_extract.py           claude-sonnet-4-...   RETIRED 15 Jun 2026

Three were moved forward and this one was missed, which is exactly what
four independent strings in four files produce. Its own docstring says
"Update via the model string in extract_recipe_with_ai when migrating to
a newer model" - a note to a future reader who never came.

Nothing in 207 suites could have caught it. A model id is just text.
test_ai_models.py is the answer to that and is the part of this round
that outlives it: every call site in the tree, read out of the source,
checked against ONE list of live models kept in one place.

--------------------------------
AND THE MESSAGE STOPS LYING
--------------------------------
extract_recipe_with_ai returned None for every distinct failure - a
retired model, a bad key, a rate limit, a malformed reply - and print()ed
the reason to a stdout nobody reads. One sentence covered all of them,
and it named the only thing that was NOT at fault.

So the failures are told apart now:

  * the file yielded no text      -> "try a different file" is TRUE here,
                                     and only here. Said BEFORE the API
                                     is called, not after three retries.
  * the service refused the call  -> says so, and carries the reason.
  * the reply was not JSON        -> says so.

RecipeExtractionError carries the reason; the view shows it and logs it.
The reason goes through `logger`, which Railway keeps and can be
searched, instead of print().

-----------------
THE MODEL STRING
-----------------
    MODEL = os.environ.get('RECIPE_IMPORT_MODEL', 'claude-sonnet-4-6')

The shape recipe_ai.py already uses for RECIPE_AI_MODEL, so the next
retirement is a Railway variable rather than a deploy. One constant, read
by both call sites - the text one and the image one, which had the same
literal typed twice.

claude-sonnet-4-6 rather than claude-haiku-4-5 because this call site has
a VISION path: a photographed recipe is OCR'd and parsed in one go.

Backups: .bak_importmodel. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_importmodel'
CRLF = {}
SENTINEL = 'test_ai_models.py'
ROOT = os.getcwd()

DEAD = 'claude-sonnet-4-20250514'
LIVE = 'claude-sonnet-4-6'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('R1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path, times=1):
    """Replace exactly `times` times, in the file's own line endings, and
    refuse an anchor that lands mid-line.

    A3's lesson: an anchor beginning with spaces matches inside a MORE
    deeply indented line, so it edits real code at the wrong indentation
    and leaves a file that will not parse."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != times:
        raise SystemExit('R1: %s appears %d times, not %d'
                         % (what, c, times))
    for m in re.finditer(re.escape(o), text):
        i = m.start()
        if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
            raise SystemExit('R1: the anchor for %s starts MID-LINE '
                             '(after %r)' % (what, text[i - 1]))
    return text.replace(o, n)


print('=' * 74)
print('SECTION R, ROUND R1 - THE AI IMPORT TOOL%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)
print('')
print('  THE DEAD MODEL')
print('  ' + '-' * 70)

AI = os.path.join(ROOT, 'pages', 'views', 'recipes', 'ai_extract.py')
at, araw = read(AI)

if 'RECIPE_IMPORT_MODEL' in at:
    print('  pages/views/recipes/ai_extract.py  already done')
else:
    # ----------------------------------------------------------------
    # 1. the module docstring tells the truth about the model now
    # ----------------------------------------------------------------
    at = swap(at, '''Currently uses claude-sonnet-4-20250514. Update via the model string
in extract_recipe_with_ai when migrating to a newer model.
''', '''THE MODEL IS NOT TYPED INTO THE CALL ANY MORE. It is MODEL, below,
which reads RECIPE_IMPORT_MODEL from the environment and falls back to
claude-sonnet-4-6 - the shape recipe_ai.py already uses for its own
RECIPE_AI_MODEL. This note used to read "Update via the model string in
extract_recipe_with_ai when migrating to a newer model", and nobody did:
the string stayed on the dated Sonnet 4 snapshot (the 14 May 2025 build)
past that model's retirement on 15 June 2026, so every import from that
day until 1 October failed with model_not_found and told the user to try
a different file.

THE EXACT DEAD ID IS NOT WRITTEN ANYWHERE IN THIS FILE, on purpose. It
is spelled out in apply_import_model.py, which is the round's record;
here it is described instead, so that a gate can assert the literal
appears nowhere in the tree and mean it.

Sonnet rather than Haiku because this module has a VISION path - a
photographed recipe is read and parsed in one call.
                                                 [test_ai_models.py]
''', 'the docstring model note', AI)

    # ----------------------------------------------------------------
    # 2. logging, and the module constants
    # ----------------------------------------------------------------
    at = swap(at, '''import base64
import json
import time
import traceback
from io import BytesIO
''', '''import base64
import json
import logging
import os
import time
from io import BytesIO
''', 'the stdlib imports', AI)

    at = swap(at, '''from django.conf import settings


# ============================================
# FILE EXTRACTION FUNCTIONS
# ============================================
''', '''from django.conf import settings

logger = logging.getLogger(__name__)

# THE ONE PLACE THE MODEL IS NAMED.
#
# It was typed twice - once in the image branch and once in the text
# branch - and both named the dated Sonnet 4 snapshot, which Anthropic
# retired on 15 June 2026. The API answered model_not_found, the retry
# loop tried three times over nine seconds, and the view said "Could not
# extract recipe data. Please try a different file." for three and a half
# months, about files that were perfectly fine.
#
# FROM THE ENVIRONMENT, so the next retirement is a Railway variable
# rather than a deploy. recipe_ai.py has read RECIPE_AI_MODEL this way
# all along; this is the same shape.          [test_ai_models.py]
MODEL = os.environ.get('RECIPE_IMPORT_MODEL', 'claude-sonnet-4-6')

# How many times the API call is retried, and the backoff between them.
# Named rather than computed inside the loop so the suite can read them
# and so the nine-second wait is visible from here.
ATTEMPTS = 3
BACKOFF = 3

# THE EXTENSION IS NOT THE MEDIA TYPE. The media type used to be built
# by interpolating the file extension into a format string, so a file
# ending in .jpg - which is what phones and scanners produce - asked the
# API for a media type spelled with that extension, and no such media
# type is registered. The right name is image/jpeg; the three-letter
# spelling is a leftover from eight-character filenames. The other two
# extensions worked only because for them the two strings coincide.
#
# Like the retired model id above, the broken spelling is DESCRIBED here
# rather than written out, so a gate can assert it appears nowhere in the
# tree and mean it. apply_import_model.py carries the literal.
#                                               [test_ai_models.py]
MEDIA_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}


class RecipeExtractionError(Exception):
    """A reason the import failed, fit to show the person who uploaded.

    THE POINT OF THIS CLASS IS THAT THE REASONS ARE DIFFERENT.
    extract_recipe_with_ai used to return None for all of them - a
    retired model, a missing key, a rate limit, a reply that was not
    JSON - and the view turned every None into one sentence blaming the
    file. The file is the one thing that is usually innocent.
    """


# ============================================
# FILE EXTRACTION FUNCTIONS
# ============================================
''', 'the module header', AI)

    # ----------------------------------------------------------------
    # 3. both call sites read MODEL
    # ----------------------------------------------------------------
    at = swap(at, '                    model="claude-sonnet-4-20250514",\n',
              '                    model=MODEL,\n',
              'the two model arguments', AI, times=2)

    # ----------------------------------------------------------------
    # 3b. image/jpg IS NOT A MEDIA TYPE, AND NEVER WAS
    # ----------------------------------------------------------------
    # Found while fixing the model, in the branch right beside it. The
    # media type was interpolated straight from the file extension:
    #
    #     "media_type": f"image/{file_type}"
    #
    # so a file called anything.jpg - which is what a phone camera and
    # every scanner produce - asked the API for `image/jpg`. There is no
    # such media type. The registered name is image/jpeg; jpg is an
    # artefact of 8.3 filenames. The API answers 400 invalid_request,
    # the loop retries three times, and the person is told to try a
    # different file.
    #
    # So the image path has ALSO been broken, for every .jpg ever
    # uploaded, and unlike the model this one was broken from the day it
    # was written. .png and .jpeg happen to work because their extension
    # and their media type coincide.
    at = swap(at, '''                                    "source": {
                                        "type": "base64",
                                        "media_type": f"image/{file_type}",
                                        "data": content,
                                    },
''', '''                                    "source": {
                                        "type": "base64",
                                        "media_type": MEDIA_TYPES[file_type],
                                        "data": content,
                                    },
''', 'the image media type', AI)

    # ----------------------------------------------------------------
    # 3c. a PDF page with no text returns None, not ''
    # ----------------------------------------------------------------
    # PyPDF2's extract_text() returns None for a page it cannot read -
    # an image-only page in an otherwise textual PDF is the common case -
    # and `text += None` is a TypeError. It surfaced as "Error reading
    # PDF: unsupported operand type(s) for +=: 'str' and 'NoneType'",
    # which tells the person nothing they can act on. With `or ''` the
    # unreadable pages contribute nothing, the readable ones still count,
    # and a PDF with NO readable page at all now falls into the
    # empty-text guard below, which says the useful thing.
    at = swap(at, '''        for page in pdf_reader.pages:
            text += page.extract_text()
''', '''        for page in pdf_reader.pages:
            # `or ''` - extract_text() returns None for a page with no
            # text layer, and `str += None` is a TypeError. [R1]
            text += page.extract_text() or ''
''', 'the pdf page loop', AI)

    # ----------------------------------------------------------------
    # 4. the key check, and the empty-text guard
    # ----------------------------------------------------------------
    at = swap(at, '''    # Get API key from settings
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not found in settings")

    client = anthropic.Anthropic(api_key=api_key)
''', '''    # NOTHING TO SEND IS THE ONE CASE WHERE THE FILE IS AT FAULT.
    #
    # A scanned PDF with no text layer is the real example: PyPDF2 walks
    # its pages, finds no extractable text, and returns ''. Asking the
    # model to find a recipe in an empty string wastes three attempts and
    # nine seconds to arrive at the same answer. Said here, before the
    # call, and said as itself - this is the ONLY failure for which "try
    # a different file" is true.
    if file_type not in ('jpg', 'jpeg', 'png') and not (content or '').strip():
        raise RecipeExtractionError(
            'No text could be read out of that file. If it is a scan or a '
            'photograph saved as a PDF, there is no text layer to read - '
            'upload it as an image instead and it will be read by eye.')

    # Get API key from settings
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    if not api_key:
        raise RecipeExtractionError(
            'The recipe reader is not configured on this server: no '
            'Anthropic API key is set.')

    client = anthropic.Anthropic(api_key=api_key)
''', 'the key check', AI)

    # ----------------------------------------------------------------
    # 5. the loop, and the end of returning None
    # ----------------------------------------------------------------
    at = swap(at, '    for attempt in range(3):\n',
              '    last = None\n    for attempt in range(ATTEMPTS):\n',
              'the retry loop head', AI)

    at = swap(at, '''        except json.JSONDecodeError as e:
            print(f"AI JSON Parse Error: {str(e)}")
            print(f"Raw response was: {response_text}")
            return None
        except Exception as e:
            print(f"AI Extraction Error (attempt {attempt + 1}): {str(e)}")
            if attempt < 2:
                wait_time = (attempt + 1) * 3  # 3s, then 6s
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(traceback.format_exc())
                return None''', '''        except json.JSONDecodeError as e:
            # NOT RETRIED, AND THAT IS DELIBERATE: the call succeeded and
            # the model answered, so asking again costs money to get the
            # same shape back. The raw reply goes to the log, where it
            # can be read; it does NOT go to the screen, because it can
            # run to thousands of characters.
            logger.error('recipe import: reply was not JSON (%s); raw '
                         'reply was %r', e, response_text[:2000])
            raise RecipeExtractionError(
                'The recipe reader answered, but not in a form this page '
                'could read. Nothing is wrong with your file - please try '
                'once more.')
        except Exception as e:
            # THE REASON IS KEPT, not printed and dropped. `last` is what
            # the person is told if every attempt fails, so a retired
            # model says it is a retired model instead of arriving as
            # "try a different file" nine seconds later.
            last = e
            logger.warning('recipe import: attempt %d of %d failed on '
                           'model %s: %s', attempt + 1, ATTEMPTS, MODEL, e)
            if attempt < ATTEMPTS - 1:
                time.sleep((attempt + 1) * BACKOFF)
    logger.error('recipe import: gave up after %d attempts on model %s',
                 ATTEMPTS, MODEL, exc_info=last)
    raise RecipeExtractionError(
        'The recipe reader could not be reached (model %s). Your file is '
        'fine - this is a fault on our side. The reason was: %s'
        % (MODEL, last))''', 'the two except branches', AI)

    if not CHECK:
        back_up(AI, araw)
        write(AI, at)
    print('  pages/views/recipes/ai_extract.py  %s -> MODEL (env, %s)'
          % (DEAD, LIVE))

# ==========================================================================
print('')
print('  THE MESSAGE THAT BLAMED THE FILE')
print('  ' + '-' * 70)

RX = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_extras.py')
rt, rraw = read(RX)

if 'RecipeExtractionError' in rt:
    print('  pages/views/recipes/recipe_extras.py  already done')
else:
    rt = swap(rt, '''from .ai_extract import (
    extract_recipe_with_ai,
    extract_text_from_docx,
    extract_text_from_image,
    extract_text_from_pdf,
)
''', '''from .ai_extract import (
    RecipeExtractionError,
    extract_recipe_with_ai,
    extract_text_from_docx,
    extract_text_from_image,
    extract_text_from_pdf,
)

logger = logging.getLogger(__name__)
''', 'the ai_extract import', RX)

    rt = swap(rt, 'import json\nimport uuid\n',
              'import json\nimport logging\nimport uuid\n',
              'the stdlib imports', RX)

    rt = swap(rt, '''            # Use Claude AI to extract
            extracted_data = extract_recipe_with_ai(text_content, file_ext)

            if not extracted_data:
                messages.error(request, 'Could not extract recipe data. Please try a different file.')
                return redirect('import_recipe')
''', '''            # Use Claude AI to extract. It RAISES with a reason now
            # rather than returning None - see the note on
            # RecipeExtractionError. The old code turned every failure
            # into one sentence telling the person to try a different
            # file, which is why a model retired on 15 June 2026 read as
            # a bad Word document for three and a half months.
            #
            # THAT SENTENCE IS DESCRIBED, NOT QUOTED, and deliberately:
            # test_ai_models.py asserts it appears nowhere in this file,
            # and a comment quoting it would fail that check while
            # looking like prose. Three notes in this round tripped over
            # the same thing - a record of a string is not the place to
            # write the string. apply_import_model.py carries the exact
            # wording.
            extracted_data = extract_recipe_with_ai(text_content, file_ext)
''', 'the extraction call', RX)

    rt = swap(rt, '''        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('import_recipe')

    return render(request, 'import_recipe.html')
''', '''        except RecipeExtractionError as e:
            # A reason written to be read by the person who uploaded the
            # file. It is already logged where it was raised.
            messages.error(request, str(e))
            return redirect('import_recipe')

        except Exception as e:
            # Anything else really is about the file - a PDF that will
            # not open, an image in a format PIL cannot decode - so this
            # one keeps its wording. It is logged with a traceback now,
            # which it never was.
            logger.exception('recipe import: %s could not be read',
                             getattr(uploaded_file, 'name', '?'))
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('import_recipe')

    return render(request, 'import_recipe.html')
''', 'the except branches', RX)

    if not CHECK:
        back_up(RX, rraw)
        write(RX, rt)
    print('  pages/views/recipes/recipe_extras.py  the file is no longer '
          'blamed')

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
# X0's REGISTER. Every suite that walks the tree has to be in exactly one
# of its five lists, and a new census that builds its own root is the
# mistake X0 exists to catch. test_ai_models.py walks the REPO - a model
# id can be typed into any file, and a census that only looked under
# pages/ would miss the fifth call site, which is the whole failure this
# round is about - so it belongs with the two that were already wide.
AT = os.path.join(ROOT, 'alv_tree.py')
avt, avraw = read(AT)
if SENTINEL in avt:
    print('  alv_tree.py                        already done')
else:
    avt = swap(avt,
               "ALREADY_WIDE = ['test_banner_pages.py', "
               "'test_standards_block.py']\n",
               "ALREADY_WIDE = ['test_banner_pages.py',\n"
               "                'test_standards_block.py',\n"
               "                # Walks the repo for .py, not the template\n"
               "                # roots: it censuses every Anthropic call\n"
               "                # site, and one of those can be written in\n"
               "                # any file. Pointing it at the template\n"
               "                # tree would blind it. [R1]\n"
               "                'test_ai_models.py']\n",
               'the ALREADY_WIDE register', AT)
    if not CHECK:
        back_up(AT, avraw)
        write(AT, avt)
    print('  alv_tree.py                        on the ALREADY_WIDE register')

for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_filtersinrc',\n]\n",
         "    '.bak_filtersinrc',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_filters_in_rc.py'\n)\n",
         "    'test_filters_in_rc.py'\n"
         "    # EVERY ANTHROPIC CALL SITE IN THE TREE, AGAINST ONE LIST.\n"
         "    # Four files each hard-coded their own model id and one of\n"
         "    # them sat on a model retired on 15 June 2026, so the AI\n"
         "    # Import tool answered 'try a different file' for three and\n"
         "    # a half months. No suite could see it: a model id is text.\n"
         "    # This one reads the source and says so.\n"
         "    'test_ai_models.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in tt:
        print('  %-34s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-34s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

import ast  # noqa: E402

for rel in ('pages/views/recipes/ai_extract.py',
            'pages/views/recipes/recipe_extras.py'):
    ast.parse(read(os.path.join(ROOT, *rel.split('/')))[0])
print('  both modules parse')

# THE DEAD MODEL IS GONE FROM THE TREE - not just from the call, from
# every file that is not a backup or a record of this round.
dead = []
for d, subs, fs in os.walk(ROOT):
    subs[:] = [s for s in subs
               if s not in ('.git', '__pycache__', 'node_modules', 'media',
                            'staticfiles')]
    for f in fs:
        if (f.endswith(SUFFIX) or f in ('apply_import_model.py',
                                        'test_ai_models.py')
                or '.bak_' in f):
            continue
        if not f.endswith(('.py', '.html', '.ps1', '.md', '.txt')):
            continue
        p = os.path.join(d, f)
        try:
            with open(p, encoding='utf-8', errors='replace') as fh:
                if DEAD in fh.read():
                    dead.append(os.path.relpath(p, ROOT))
        except OSError:
            pass
if dead:
    raise SystemExit('R1: %s is still named in %s' % (DEAD, dead[:6]))
print('  %s is named nowhere but this round\'s own record' % DEAD)

# AND NOT ONE CALL SITE TYPES A MODEL INTO THE CALL ANY MORE. This is the
# defect, stated as a gate: a model id belongs to a named constant, so
# that `grep MODEL` finds all four of them at once.
at_now = read(AI)[0]
if re.search(r'model\s*=\s*["\']', at_now):
    raise SystemExit('R1: ai_extract.py still types a model into a call')
print('  and ai_extract.py names no model inside a call - both read MODEL')

# NO MEDIA TYPE IS BUILT OUT OF A FILE EXTENSION.
if 'f"image/{file_type}"' in at_now or "f'image/{file_type}'" in at_now:
    raise SystemExit('R1: a media type is still interpolated from the '
                     'file extension')
if 'image/jpg' in at_now:
    raise SystemExit('R1: image/jpg is still named - there is no such '
                     'media type')
print('  and no media type is built out of a file extension')

# THE THREE EXTENSIONS THE VIEW ACCEPTS ARE THE THREE THE MAP ANSWERS.
# Two lists of image formats in two files is how they drift apart; this
# reads both out of the source and refuses if they differ.
rx_now = read(RX)[0]
m = re.search(r"elif file_ext in \[([^\]]*)\]:\s*\n\s*text_content = "
              r"extract_text_from_image", rx_now)
if not m:
    raise SystemExit('R1: could not find the image branch of import_recipe')
view_exts = set(re.findall(r"'([a-z]+)'", m.group(1)))
m2 = re.search(r'MEDIA_TYPES = \{(.*?)\}', at_now, re.S)
map_exts = set(re.findall(r"'([a-z]+)':", m2.group(1))) if m2 else set()
if view_exts != map_exts:
    raise SystemExit('R1: the view accepts %s but MEDIA_TYPES answers %s'
                     % (sorted(view_exts), sorted(map_exts)))
print('  and the view\'s image formats are exactly MEDIA_TYPES\' keys: %s'
      % ', '.join(sorted(map_exts)))

print('-' * 74)
print('  The AI Import tool asks for a model that exists. When it cannot be')
print('  reached it says so, with the reason, instead of blaming the file.')
print('=' * 74)
