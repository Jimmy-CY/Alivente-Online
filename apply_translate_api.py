"""TR-2 - TRANSLATE WITH THE API THIS APP ALREADY TALKS TO.

   Demetri, 4 Oct 2026, after testing TR-1 on Live:

       "So, that works. But now we need to fix the translation service.
        Can we not use our AI API for translation?"

   He saw exactly what TR-1 was built to produce - an amber "Translation
   failed" bar and the Greek field untouched - which is the honest answer
   and not a useful one. deep-translator could not reach Google from
   Railway. So the engine goes; the honesty stays.

   WHY THE API IS NOT JUST AN ALTERNATIVE BUT A BETTER FIT.

     deep-translator 1.9.1 scrapes translate.google.com with
     requests.get() and NO TIMEOUT, and exposes no way to pass one. That
     single fact is why TR-1 had to put the call in a thread pool and wait
     on a future - machinery that exists only to contain a library that
     cannot be told to give up. urllib.request.urlopen takes timeout= as
     an argument. The pool goes with the scraper.

     The dependency is already here: anthropic==0.72.0 in
     requirements.txt, ANTHROPIC_API_KEY already set on Railway, and
     pages/services/invoice_verification.py already calling
     api.anthropic.com with urllib and a 30s timeout. This round copies a
     pattern that is running in production rather than inventing one.

     And a translator can be told what it is reading. A property
     maintenance task list is full of words a generic engine mangles -
     Snagging, Backsplash, Unit, Granite Top Replacement. Demetri:
     "Tell it this is property maintenance (Recommended)".

   WHERE THE CODE GOES. pages/translation_service.py, which exists, is
   named for exactly this, and has carried the TODO

       TODO: replace googletrans with deep-translator and translate on
       demand when `stored` comes back blank.

   since the day googletrans was removed. This round closes it - with the
   API rather than deep-translator, which is the better answer to the same
   question. The view keeps translate_to_greek_service as its entry point
   and delegates, so the endpoint and its contract do not move.

   THE CONTRACT IS TR-1'S, UNCHANGED: (ok, text, reason), and on failure
   the second element is None and never the input. That is the rule that
   stopped a failure arriving as a green tick, and swapping the engine
   underneath it must not be allowed to quietly undo it.

   NO KEY IS A FAILURE, NOT A CRASH. Locally there is usually no
   ANTHROPIC_API_KEY, and a developer pressing the button should get
   "translation is not configured" rather than a traceback - the same
   call invoice_verification makes.

   FILES: pages/translation_service.py, pages/views/projects.py,
          requirements.txt.                   [test_translate_api.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_trapi'

SERVICE = 'pages/translation_service.py'
VIEWS = 'pages/views/projects.py'
REQS = 'requirements.txt'

# ---- the module gains the translator ------------------------------------

OLD_DOC_TAIL = '''TODO: replace googletrans with deep-translator and translate on demand
when `stored` comes back blank.
"""
'''

NEW_DOC_TAIL = '''TR-2, 4 Oct 2026 - the TODO above said "replace googletrans with
deep-translator". TR-1 did that and it could not reach Google from
Railway. translate_to_greek below uses the Anthropic Messages API
instead - the same endpoint, key and urllib call that
pages/services/invoice_verification.py has been making in production,
and unlike the scraper it can be given a timeout and told what it is
reading. Demetri: "Can we not use our AI API for translation?"
"""
import json
import os
import urllib.error
import urllib.request

# The same endpoint and default model invoice_verification uses. A task
# name is a handful of words, so haiku is the right weight; both are
# overridable by environment variable for the same reason that one is.
API_URL = 'https://api.anthropic.com/v1/messages'
DEFAULT_MODEL = 'claude-haiku-4-5'
DEFAULT_TIMEOUT = 20.0

# WHY THE PROMPT SAYS WHAT THE TEXT IS. A generic engine reads
# "Backsplash" as a splash of water and "Snagging" as catching on a nail.
# Naming the domain in one sentence is the whole difference between a
# translation a Greek builder would use and one he would laugh at.
#
# RETURN ONLY THE TRANSLATION is load-bearing. Anything conversational
# would be written straight into the Greek field as if it were the
# answer - the failure TR-1 existed to stop, arriving by a new route.
_PROMPT = """You are translating short text from English into Greek for a
property management and maintenance system used in Cyprus.

The text is a task name or a task description from a renovation or
maintenance project - things like Backsplash, Snagging, Granite Top
Replacement, Update Kitchen, Replace Unit. Translate them the way a Greek
builder or property manager would say them, not word by word.

Keep proper nouns, property names, people's names and numbers exactly as
they are. Keep the same capitalisation style. Do not add anything.

Return ONLY the Greek translation, with no quotes, no explanation and no
alternatives."""

# Long enough for a description, short enough that a runaway answer
# cannot be mistaken for a task name.
MAX_TOKENS = 1000

# Anything longer than this is not a task name and is not what this was
# built for; refusing is cheaper than a surprise bill.
MAX_CHARS = 4000


def _config():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    model = os.environ.get('TRANSLATE_MODEL', DEFAULT_MODEL)
    try:
        timeout = float(os.environ.get('TRANSLATE_TIMEOUT', DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT
    return api_key, model, timeout


def translate_to_greek(text):
    """English to Greek. Returns (ok, text, reason).

    THE CONTRACT IS TR-1'S AND IT DOES NOT MOVE. On failure the second
    element is None - never the input. Returning the English from here
    is what made a failed translation arrive as a green tick with the
    English sitting in the Greek box, and the engine changing underneath
    is not a reason to let that back in.
    """
    text = (text or '').strip()
    if not text:
        return (False, None, 'There is nothing to translate.')
    if len(text) > MAX_CHARS:
        return (False, None,
                'That text is too long to translate (%d characters).'
                % len(text))

    api_key, model, timeout = _config()
    if not api_key:
        return (False, None, 'Translation is not configured on this server.')

    body = json.dumps({
        'model': model,
        'max_tokens': MAX_TOKENS,
        'system': _PROMPT,
        'messages': [{'role': 'user', 'content': text}],
    }).encode('utf-8')

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        print('Translation API returned HTTP %s' % exc.code)
        return (False, None,
                'The translation service refused the request (HTTP %s).'
                % exc.code)
    except Exception as exc:                                # noqa: BLE001
        print('Translation call failed: %s' % exc)
        return (False, None, 'The translation service could not be reached.')

    blocks = data.get('content') or []
    out = ''.join(b.get('text', '') for b in blocks
                  if b.get('type') == 'text').strip()
    if not out:
        return (False, None, 'The translation service returned nothing.')
    return (True, out, '')
'''

# ---- the view delegates --------------------------------------------------

OLD_POOL = '''# TR-1, 4 Oct 2026 - the pool the translator call runs in.
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


def translate_to_greek_service(text):'''

NEW_POOL = '''def translate_to_greek_service(text):'''

OLD_BODY = '''    try:
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

NEW_BODY = '''    # TR-2, 4 Oct 2026. The work moved to translation_service, which is
    # named for it and had carried the TODO since googletrans was removed.
    # This stays as the view's entry point so the endpoint and every
    # caller keep the shape TR-1 gave them.
    from ..translation_service import translate_to_greek
    return translate_to_greek(text)'''

OLD_IMPORTS = '''import json
# TR-1 - see translate_to_greek_service for why the translator call needs a
# pool and a timeout rather than a plain function call.
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout'''

NEW_IMPORTS = '''import json'''

# The docstring's first line changes too - it described the scraper.
OLD_SIG_DOC = '''    """Translate English to Greek.

    Returns (ok, text, reason).'''

NEW_SIG_DOC = '''    """Translate English to Greek, via translation_service.

    Returns (ok, text, reason).'''

VIEW_EDITS = [
    ('the pool', OLD_POOL, NEW_POOL),
    ('the body', OLD_BODY, NEW_BODY),
    ('the imports', OLD_IMPORTS, NEW_IMPORTS),
    ('the docstring', OLD_SIG_DOC, NEW_SIG_DOC),
]

REQ_LINE = 'deep-translator==1.9.1'


def read_text(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write_text(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def fit(text, block):
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def edit_file(path, pairs, check, label):
    text = read_text(path)
    done = 0
    for name, old, new in pairs:
        o, n = fit(text, old), fit(text, new)
        if n in text and o not in text:
            continue
        c = text.count(o)
        if c != 1:
            raise SystemExit('TR-2: %s anchor %r appears %d times, expected 1'
                             % (label, name, c))
        text = text.replace(o, n)
        done += 1
    if done and not check:
        backup(path)
        write_text(path, text)
    return done


def edit_requirements(path, check):
    """UTF-16 LE with a BOM. Decoded and re-encoded as it was - writing it
    back as UTF-8 hands Railway a file pip cannot parse."""
    raw = open(path, 'rb').read()
    if not raw.startswith(b'\xff\xfe'):
        raise SystemExit('TR-2: requirements.txt is not UTF-16 LE any more')
    text = raw.decode('utf-16')
    if REQ_LINE not in text:
        return 0
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = [l for l in text.split(nl) if l != REQ_LINE]
    if not check:
        backup(path)
        with open(path, 'wb') as fh:
            fh.write(nl.join(lines).encode('utf-16'))
    return 1


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    svc = edit_file(SERVICE, [('the module', OLD_DOC_TAIL, NEW_DOC_TAIL)],
                    check, 'translation_service.py')
    views = edit_file(VIEWS, VIEW_EDITS, check, 'projects.py')
    reqs = edit_requirements(REQS, check)

    print('TR-2  translation_service edits : %d' % svc)
    print('TR-2  projects.py edits         : %d' % views)
    print('TR-2  deep-translator removed   : %d' % reqs)

    if check:
        if svc or views or reqs:
            print('TR-2  NOT APPLIED')
            return 1
        print('TR-2  applied')
        return 0
    full = (svc == 1 and views == len(VIEW_EDITS) and reqs == 1)
    none = (svc == 0 and views == 0 and reqs == 0)
    if not (full or none):
        print('TR-2  REFUSED: partial application (%d/1, %d/%d, %d/1)'
              % (svc, views, len(VIEW_EDITS), reqs))
        return 2
    print('TR-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
