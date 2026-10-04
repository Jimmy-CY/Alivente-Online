# -*- coding: utf-8 -*-
"""test_translate_api.py - Section TR round TR-2, 4 Oct 2026.

Demetri, having tested TR-1 on Live:

    "So, that works. But now we need to fix the translation service. Can we
     not use our AI API for translation?"

He saw the amber bar and an untouched Greek field, which is what TR-1 was
for. deep-translator could not reach Google from Railway, so the engine
goes and the honesty stays.

WHAT THIS SUITE GUARDS, in order of how much it matters.

  SECTION 3, THE CONTRACT. TR-1's rule is that on failure the second
  element is None and never the input - that rule is the only reason a
  failed translation stopped arriving as a green tick with English in the
  Greek box. Swapping the engine underneath a contract is exactly when a
  contract gets quietly broken, so section 3 RUNS the new translator down
  every failure path there is - no key, blank input, oversized input, and
  a key the API will reject - and requires (False, None, reason) from all
  four. Not a string that happens to be falsy. None.

  SECTION 3 MAKES ONE REAL NETWORK CALL, and its assertion does not depend
  on the network. With a deliberately invalid key the API answers 401 and
  the translator must report that honestly; with no route at all it must
  report that honestly instead. Either is a pass. What the section PRINTS
  tells you which happened, and that line is worth reading: a 401 means
  this machine reached api.anthropic.com and the request body was accepted
  as far as authentication, which is the half of "does it work" that can
  be established without a real key.

  SECTION 2, THE MACHINERY THAT SHOULD BE GONE. TR-1 put the call in a
  ThreadPoolExecutor and waited on a future, for one reason: deep-
  translator calls requests.get() with no timeout and no way to pass one.
  urllib.request.urlopen takes timeout= as an argument. If the pool is
  still there after the scraper has gone, something was copied rather than
  replaced.

WHAT THIS SUITE CANNOT TEST, said plainly rather than passed over: a
successful translation. That needs a real ANTHROPIC_API_KEY, which does
not belong in a test run and is not going to be put in one. The success
path is a LIVE test and it is on the list for this deploy.
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
import os
import re
import sys
import importlib.util

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_trapi'
ME = 'test_translate_api.py'
PATCHER = 'apply_translate_api.py'
PS1 = 'Push-PendingChanges.ps1'

SERVICE = os.path.join(ROOT, 'pages', 'translation_service.py')
VIEWS = os.path.join(ROOT, 'pages', 'views', 'projects.py')
REQS = os.path.join(ROOT, 'requirements.txt')
EDIT_PAGE = os.path.join(alv_tree.roots()[0], 'projects',
                         'project_tasks_edit.html')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines():
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """read(p + SUFFIX) - the file as TR-2 found it."""
    return read(p + SUFFIX)


def load_service():
    """The module, loaded directly off disk.

    It imports nothing from Django - deliberately, so the translator can
    be exercised without settings, a database or an app registry. If that
    ever stops being true this load will fail and say so, which is the
    right moment to notice."""
    spec = importlib.util.spec_from_file_location('alv_ts_probe', SERVICE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the translator lives in the module named for it')
    src = now(SERVICE)

    ok('def translate_to_greek(' in src,
       'translation_service declares translate_to_greek')
    ok('api.anthropic.com/v1/messages' in src,
       'and calls the Messages API')
    ok("'anthropic-version': '2023-06-01'" in src,
       'with the version header invoice_verification uses')
    ok("os.environ.get('ANTHROPIC_API_KEY')" in src,
       'reading the key from the environment, not from settings',
       'settings.py carries a hard-coded copy that is in git history; '
       'the environment is the one Railway sets')
    ok('urllib.request.urlopen(req, timeout=timeout)' in src,
       'and passing a real timeout',
       'this is the whole reason the thread pool can go')

    before = was(SERVICE)
    ok('TODO: replace googletrans with deep-translator' in before,
       'the module really did carry that TODO',
       'if not, this round closed something else')
    ok('TODO: replace googletrans with deep-translator' not in src,
       'and the round closed it')
    ok('deep_translator' not in src and 'GoogleTranslator' not in src,
       'nothing of the scraper is left in the module')


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. the view delegates, and the pool is gone')
    src = now(VIEWS)
    before = was(VIEWS)

    ok('from ..translation_service import translate_to_greek' in src,
       'the view imports the translator')
    ok('return translate_to_greek(text)' in src,
       'and returns what it returns, unchanged',
       'the endpoint and its contract must not move with the engine')

    ok('ThreadPoolExecutor' in before,
       'TR-1 really did use a pool',
       'if not, section 2 is guarding nothing')
    for gone in ('ThreadPoolExecutor', 'FuturesTimeout', '_TRANSLATE_POOL',
                 'deep_translator', 'GoogleTranslator'):
        ok(gone not in src, '%s is gone from the view' % gone,
           'urlopen takes timeout= - the pool existed only to contain a '
           'library that could not be told to stop')

    # The endpoint itself must still branch the way TR-1 left it.
    ok('ok, translated_text, reason = translate_to_greek_service(text)' in src,
       'translate_text still unpacks three values')
    ok(re.search(r"if not ok:\s*\r?\n\s*return JsonResponse\("
                 r"\{'success': False, 'error': reason\}\)", src) is not None,
       'and still returns success: False with the reason')


# ------------------------------------------------------------- section 3

def section_3():
    print('\n3. every failure path, run, returns (False, None, reason)')
    try:
        mod = load_service()
    except Exception as e:
        ok(False, 'translation_service could be loaded without Django', e)
        return

    saved = os.environ.get('ANTHROPIC_API_KEY')
    try:
        os.environ.pop('ANTHROPIC_API_KEY', None)
        cases = [
            ('no key at all', 'Update Kitchen'),
            ('blank input', '   '),
            ('oversized input', 'x' * 5000),
        ]
        for label, text in cases:
            r = mod.translate_to_greek(text)
            ok(isinstance(r, tuple) and len(r) == 3,
               '%s returns a 3-tuple' % label, r)
            if isinstance(r, tuple) and len(r) == 3:
                ok(r[0] is False, '%s: ok is False' % label, r)
                ok(r[1] is None,
                   '%s: no text comes back' % label,
                   'returning the input here is the defect TR-1 removed - '
                   'got %r' % (r[1],))
                ok(isinstance(r[2], str) and r[2].strip(),
                   '%s: with a reason a user can read' % label, r[2])

        # THE ONE REAL CALL. The assertion is about the contract, not the
        # network: 401 if this machine reached the API, "could not be
        # reached" if it did not. Both are honest and both pass.
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-invalid-probe-key'
        r = mod.translate_to_greek('Update Kitchen')
        ok(isinstance(r, tuple) and len(r) == 3,
           'a rejected key returns a 3-tuple', r)
        if isinstance(r, tuple) and len(r) == 3:
            ok(r[0] is False, 'a rejected key is not a success', r)
            ok(r[1] is None, 'and brings back no text', r)
            ok('Update Kitchen' not in str(r[1]),
               'the English is nowhere in the result')
        reason = r[2] if isinstance(r, tuple) and len(r) == 3 else ''
        if 'HTTP 401' in str(reason):
            print('        reached api.anthropic.com - it answered 401, so '
                  'the request')
            print('        body and headers were accepted as far as '
                  'authentication.')
        else:
            print('        no route to api.anthropic.com from this machine: '
                  '%s' % reason)
            print('        The contract still held, which is what this '
                  'section tests.')
    finally:
        if saved is None:
            os.environ.pop('ANTHROPIC_API_KEY', None)
        else:
            os.environ['ANTHROPIC_API_KEY'] = saved


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. the prompt says what the round claims it says')
    src = now(SERVICE)
    m = re.search(r'_PROMPT = """(.*?)"""', src, re.S)
    if not ok(m is not None, 'the prompt is there'):
        return
    p = m.group(1)
    ok('property management' in p.lower() or 'maintenance' in p.lower(),
       'it names the domain',
       'Demetri chose "Tell it this is property maintenance" - a generic '
       'engine reads Backsplash as a splash of water')
    ok('Greek' in p, 'and the target language')
    ok(re.search(r'return only', p, re.I) is not None,
       'and that ONLY the translation comes back',
       'anything conversational would be written straight into the Greek '
       'field as though it were the answer')
    ok('Cyprus' in p or 'proper noun' in p.lower(),
       'and tells it to leave names alone')


# ------------------------------------------------------------- section 5

def section_5():
    print('\n5. requirements.txt')
    raw = open(REQS, 'rb').read()
    ok(raw.startswith(b'\xff\xfe'),
       'still UTF-16 LE with its BOM',
       'writing it back as UTF-8 hands Railway a file pip cannot read')
    text = raw.decode('utf-16')
    ok('deep-translator' not in text,
       'deep-translator is gone',
       'TR-1 added it yesterday and it never worked from Railway')
    ok('anthropic==' in text,
       'anthropic is still pinned',
       'the new translator needs it no more than invoice_verification '
       'does - both call the API over urllib - but it is what the rest '
       'of the app uses and it stays')
    before = open(REQS + SUFFIX, 'rb').read().decode('utf-16')
    removed = [l for l in before.split('\r\n') if l not in text.split('\r\n')]
    ok(removed == ['deep-translator==1.9.1'],
       'exactly one line was removed', removed)


# ------------------------------------------------------------- section 6

def section_6():
    print('\n6. the browser still leaves the Greek field alone on a failure')
    if not os.path.isfile(EDIT_PAGE):
        ok(False, 'project_tasks_edit.html found')
        return
    js = read(EDIT_PAGE)
    writes = [m.start() for m in
              re.finditer(r"(?:\$\('#' \+ targetFieldId\)|targetField)"
                          r"\.val\(data\.translated_text\)", js)]
    ok(len(writes) == 2, 'both write paths are still there', len(writes))
    for pos in writes:
        ok('if (data.success)' in js[max(0, pos - 260):pos],
           'the write at offset %d is inside if (data.success)' % pos)


# ------------------------------------------------------------- section 7

def section_7():
    print('\n7. what this suite did NOT test')
    print('      A successful translation. That needs a real')
    print('      ANTHROPIC_API_KEY, which does not belong in a test run.')
    print('      On the deploy: Edit a task, the Greek tab, Translate Name')
    print('      to Greek with an English name present. Greek should land')
    print('      in the Greek field within a second or two. Try a')
    print('      maintenance word - Backsplash, Snagging - and see whether')
    print('      it reads the way you would say it.')


# ------------------------------------------------------------- section 8

def section_8():
    print('\n8. registration')
    for f in (PATCHER, ME):
        ok(os.path.isfile(os.path.join(ROOT, f)), '%s is on disk' % f)
    try:
        ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
           '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
    except Exception as e:
        ok(False, 'alv_rounds.py readable', e)
    try:
        ok(ME in read(os.path.join(ROOT, PS1)),
           '%s is in the push suites' % ME)
    except Exception as e:
        ok(False, '%s readable' % PS1, e)


def main():
    print('test_translate_api.py - TR-2, translation on the house API')
    for fn in (section_1, section_2, section_3, section_4, section_5,
               section_6, section_7, section_8):
        fn()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_translate_api.py: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
