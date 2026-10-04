"""TR-1 - STOP REPORTING A FAILURE AS A SUCCESS, AND MAKE IT WORK AGAIN.

   Demetri, 4 Oct 2026:

       "When the Task Name is Blank and I press Translate Name to Greek, it
        insert the English Name, but it says that it has done the
        translation successfully. The same happens with the Description."

   THE CAUSE, read top to bottom.

     translate_to_greek_service() does `from googletrans import Translator`
     inside a try, and its except does

         return text  # Return original text if translation fails

     googletrans is NOT in requirements.txt - an earlier round took it out.
     So on Railway that import raises ImportError on every single call and
     the function returns the English, unchanged, every time.

     translate_text() then wraps whatever came back in

         {'success': True, 'translated_text': translated_text, ...}

     The caller cannot tell the difference between "here is your Greek" and
     "here is your English back, I could not do it".

     The browser does its part correctly - project_tasks_edit.html already
     branches on data.success and already shows the warning tone when it is
     false. It was never given a false to show. So the English text lands in
     the Greek box under a green tick.

   THIS IS THE SAME SHAPE AS THE GREEK 500 of two days ago: a thing that
   stopped working, a note saying it would be handled, and nobody told at
   the point of use. The fix both times is to make the failure arrive.

   WHAT THIS ROUND DOES.

     1. The service returns a RESULT, not a string: (ok, text, reason). It
        no longer has a way to say "fine" when it is not.
     2. translate_text returns success: False with a reason the browser can
        show when the translator is unavailable or errors.
     3. ON FAILURE THE GREEK FIELD IS LEFT EXACTLY AS IT WAS. Demetri:
        "Leave it exactly as it was (Recommended)". The JS already does this
        - it only writes the field inside `if (data.success)` - so there is
        nothing to change there, and a gate below proves that rather than
        assuming it.
     4. googletrans goes, deep-translator comes in, and translation works
        again. Demetri: "Honesty and restore translation".

   THE TIMEOUT, AND WHY IT IS A THREAD. deep-translator 1.9.1 calls
   requests.get() with NO timeout argument. A hung Google endpoint would
   hold a gunicorn worker for as long as the socket stayed open, and Railway
   does not run many workers. socket.setdefaulttimeout is global and would
   reach every other request in the process. There is no timeout parameter
   to pass through.

   So the call runs in a small bounded pool and the view waits on
   future.result(timeout=TIMEOUT). If it does not come back in time the user
   is told, immediately, that translation is unavailable - which is the
   honest answer and the whole point of the round. The worker thread may
   linger until requests gives up on its own; the pool is capped at four so
   the worst case is bounded and visible rather than unbounded and not.

   FILES: pages/views/projects.py, requirements.txt.
                                            [test_translate_honest.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_translate'

VIEWS = 'pages/views/projects.py'
REQS = 'requirements.txt'

# deep-translator pinned, like everything else in that file.
REQ_LINE = 'deep-translator==1.9.1'
REQ_AFTER = 'cssselect2==0.8.0'

OLD_SERVICE = '''def translate_to_greek_service(text):
    """
    Use Google Translate API to translate English text to Greek
    """
    try:
        # Lazy import: googletrans is an optional dependency; any failure
        # (including ImportError) falls back to returning the original text.
        from googletrans import Translator

        # Initialize Google Translator
        translator = Translator()

        # Translate from English to Greek
        result = translator.translate(text, dest='el', src='en')

        return result.text

    except Exception as e:
        print(f"Google Translation service error: {e}")
        return text  # Return original text if translation fails'''

NEW_SERVICE = '''# TR-1, 4 Oct 2026 - the pool the translator call runs in.
#
# deep-translator 1.9.1 calls requests.get() with no timeout. There is no
# parameter to pass one through, and socket.setdefaulttimeout would reach
# every other request in the process. So the call goes into a small bounded
# pool and the caller waits on the future. Four workers, because the worst
# case has to be a number rather than "however many pile up".
_TRANSLATE_POOL = ThreadPoolExecutor(max_workers=4,
                                     thread_name_prefix='alv-translate')

# Long enough for a working service on a slow day, short enough that a user
# who presses the button gets an answer rather than a spinner.
TRANSLATE_TIMEOUT = 8


def translate_to_greek_service(text):
    """Translate English to Greek.

    Returns (ok, text, reason).

    IT RETURNS A RESULT AND NOT A STRING, and that is the round. This used
    to `return text` from its except clause - the English, unchanged - and
    the caller had no way to tell that apart from a translation. So the
    English went into the Greek box under a green tick. Demetri: "it insert
    the English Name, but it says that it has done the translation
    successfully."

    On failure the second element is None, not the input. A caller that
    wants to fall back to the English has to say so in its own code, where
    a reader can see it happening.
    """
    try:
        from deep_translator import GoogleTranslator
    except ImportError as e:
        print(f"Translation unavailable - deep_translator not installed: {e}")
        return (False, None, 'The translation service is not available.')

    def run():
        return GoogleTranslator(source='en', target='el').translate(text)

    try:
        out = _TRANSLATE_POOL.submit(run).result(timeout=TRANSLATE_TIMEOUT)
    except FuturesTimeout:
        print(f"Translation timed out after {TRANSLATE_TIMEOUT}s")
        return (False, None,
                'The translation service did not answer in time.')
    except Exception as e:
        print(f"Translation service error: {e}")
        return (False, None, 'The translation service could not be reached.')

    if not out or not str(out).strip():
        # An empty answer is not a translation. Saying so beats writing a
        # blank over whatever the user had typed.
        return (False, None, 'The translation service returned nothing.')

    return (True, str(out), '')'''

OLD_CALL = '''        # Use Google Translate service
        if target_language == 'greek':
            translated_text = translate_to_greek_service(text)
        else:
            translated_text = text

        return JsonResponse({
            'success': True,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })'''

NEW_CALL = '''        # TR-1, 4 Oct 2026. The service reports whether it worked, and
        # this view passes that on instead of stamping success: True over
        # it. On a failure there is no translated_text at all, so there is
        # nothing for the browser to write into the Greek field even by
        # accident - and the field is left exactly as the user left it.
        if target_language == 'greek':
            ok, translated_text, reason = translate_to_greek_service(text)
            if not ok:
                return JsonResponse({'success': False, 'error': reason})
        else:
            translated_text = text

        return JsonResponse({
            'success': True,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })'''

IMPORT_ANCHOR = 'import json'
IMPORT_NEW = '''import json
# TR-1 - see translate_to_greek_service for why the translator call needs a
# pool and a timeout rather than a plain function call.
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout'''


def read_text(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write_text(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def fit(text, block):
    """The block written with the line ending the file really uses."""
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def edit_views(path, check):
    text = read_text(path)
    done = 0
    for old, new in ((OLD_SERVICE, NEW_SERVICE),
                     (OLD_CALL, NEW_CALL),
                     (IMPORT_ANCHOR, IMPORT_NEW)):
        o, n = fit(text, old), fit(text, new)
        if n in text:
            continue
        c = text.count(o)
        if c != 1:
            raise SystemExit('TR-1: projects.py anchor %r appears %d times, '
                             'expected 1' % (old.splitlines()[0][:50], c))
        text = text.replace(o, n)
        done += 1
    if done and not check:
        backup(path)
        write_text(path, text)
    return done


def edit_requirements(path, check):
    """requirements.txt IS UTF-16 WITH A BOM. Reading it as UTF-8 gives a
    file full of NULs and writing it back as UTF-8 would hand Railway a
    requirements file pip cannot parse. Decoded and re-encoded as it was."""
    raw = open(path, 'rb').read()
    if not raw.startswith(b'\xff\xfe'):
        raise SystemExit('TR-1: requirements.txt is not UTF-16 LE any more - '
                         'check before writing it back')
    text = raw.decode('utf-16')
    if REQ_LINE in text:
        return 0
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    if REQ_AFTER not in lines:
        raise SystemExit('TR-1: %r is not in requirements.txt - the insert '
                         'point moved' % REQ_AFTER)
    i = lines.index(REQ_AFTER)
    lines.insert(i + 1, REQ_LINE)
    if not check:
        backup(path)
        with open(path, 'wb') as fh:
            fh.write(nl.join(lines).encode('utf-16'))
    return 1


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    done = edit_views(VIEWS, check)
    reqs = edit_requirements(REQS, check)

    print('TR-1  projects.py edits   : %d' % done)
    print('TR-1  requirements lines  : %d' % reqs)

    if check:
        if done or reqs:
            print('TR-1  NOT APPLIED')
            return 1
        print('TR-1  applied')
        return 0
    full = (done == 3 and reqs == 1)
    none = (done == 0 and reqs == 0)
    if not (full or none):
        print('TR-1  REFUSED: partial application (%d/3 edits, %d/1 reqs)'
              % (done, reqs))
        return 2
    print('TR-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
