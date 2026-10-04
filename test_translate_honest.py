# -*- coding: utf-8 -*-
"""test_translate_honest.py - Section TR round TR-1, 4 Oct 2026.

Demetri:

    "When the Task Name is Blank and I press Translate Name to Greek, it
     insert the English Name, but it says that it has done the translation
     successfully. The same happens with the Description."

translate_to_greek_service caught every exception - ImportError included,
and googletrans has not been in requirements.txt for weeks - and returned
the input text. translate_text wrapped that in success: True. The browser,
which already branches on success correctly, was never given a false.

WHAT THIS SUITE CAN AND CANNOT PROVE, said plainly.

  It CAN prove the honesty half, and it does, by running the real function:
  section 3 calls translate_to_greek_service with the import broken and
  with the network unreachable, and requires (False, None, reason) both
  times. The old code returned the English here. That is the defect, and it
  is reproducible from a terminal.

  It CANNOT prove that translation now works. This sandbox has no route to
  translate.google.com, so a successful call cannot be made from here. The
  suite says so out loud rather than passing quietly and letting a green
  run imply something it did not test. That half is a LIVE test, and it is
  on the test list for this deploy.

HOW THE FUNCTION IS LOADED. pages/views/projects.py imports Django at module
scope, so importing it needs settings, a database and an app registry - all
to exercise twenty lines that touch none of them. Section 3 cuts the two
functions out of the source and execs them with stubs. That is a real
limitation: it tests the text of the function, not the module's wiring. So
section 1 checks the wiring separately - that the view calls the service,
unpacks three values, and returns success: False on the failure branch.
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
import json
import shutil
import tempfile

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

SUFFIX = '.bak_translate'
ME = 'test_translate_honest.py'
PATCHER = 'apply_translate_honest.py'
PS1 = 'Push-PendingChanges.ps1'

VIEWS = os.path.join(ROOT, 'pages', 'views', 'projects.py')
REQS = os.path.join(ROOT, 'requirements.txt')
EDIT_PAGE = os.path.join(alv_tree.roots()[0], 'projects',
                         'project_tasks_edit.html')

SCRATCH = tempfile.mkdtemp(prefix='alv_translate_')

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
    return read(p + SUFFIX)


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the view passes the failure on')
    src = now(VIEWS)

    ok('ok, translated_text, reason = translate_to_greek_service(text)' in src,
       'translate_text unpacks three values from the service',
       'if it still takes a string back, it cannot know whether it worked')
    ok(re.search(r"if not ok:\s*\r?\n\s*return JsonResponse\("
                 r"\{'success': False, 'error': reason\}\)", src) is not None,
       'and returns success: False with the reason',
       'this is the line that reaches the user')

    before = was(VIEWS)
    ok('return text  # Return original text if translation fails' in before,
       'the old code really did return the English on failure',
       'if not, this round was written against something else')
    ok('return text  # Return original text if translation fails' not in src,
       'and it no longer does')

    ok('googletrans' not in src,
       'googletrans is gone from the view',
       'it has not been in requirements.txt for weeks; importing it was '
       'the failure that was being reported as a success')
    ok('deep_translator' in src, 'deep-translator is what it imports now')

    # The timeout is the operational half of the round.
    ok('TRANSLATE_TIMEOUT' in src and 'FuturesTimeout' in src,
       'the call is bounded by a timeout',
       'deep-translator 1.9.1 calls requests.get with none of its own')
    ok('ThreadPoolExecutor' in src and 'max_workers=4' in src,
       'and runs in a bounded pool',
       'so a hung endpoint costs four threads, not a worker per press')


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. the browser leaves the Greek field alone on a failure')
    if not ok(os.path.isfile(EDIT_PAGE), 'project_tasks_edit.html found'):
        return
    js = read(EDIT_PAGE)

    # EVERY write of a translated value, not just the one on the button.
    # There are two: translateText() on the Translate buttons, and
    # autoTranslateField() on blur. The first build of this section looked
    # for `$('#' + targetFieldId).val(` and found only one of them -
    # autoTranslateField holds the field in a variable and writes
    # `targetField.val(`. A gate that checks one of two paths is worse
    # than no gate, because it reads like both were checked.
    writes = [m.start() for m in
              re.finditer(r"(?:\$\('#' \+ targetFieldId\)|targetField)"
                          r"\.val\(data\.translated_text\)", js)]
    ok(len(writes) == 2,
       'both paths that write the Greek field were found',
       'found %d - translateText and autoTranslateField are the two'
       % len(writes))
    for pos in writes:
        window = js[max(0, pos - 260):pos]
        ok('if (data.success)' in window,
           'the write at offset %d is inside if (data.success)' % pos,
           'Demetri chose "Leave it exactly as it was" - a write outside '
           'that branch is how English got into a Greek box')

    ok("showCopyMessage('Translation failed: '" in js,
       'and it already had a failure message to show',
       'the browser was never the problem; it was never given a false')


# ------------------------------------------------------------- section 3

HARNESS = '''
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
'''


def load_service(src):
    """The service function, cut out of the view module and exec'd.

    projects.py imports Django at module scope, so importing it properly
    would need settings, a database and the app registry to exercise twenty
    lines that touch none of them. The cost of this shortcut is that it
    tests the text of the function and not the module's wiring - which is
    why section 1 checks the wiring on its own."""
    m = re.search(r'# TR-1, 4 Oct 2026 - the pool.*?'
                  r'return \(True, str\(out\), \'\'\)', src, re.S)
    if not m:
        return None
    ns = {}
    exec(HARNESS + m.group(0), ns)
    return ns.get('translate_to_greek_service')


def section_3():
    print('\n3. the service, run')
    fn = load_service(now(VIEWS))
    if not ok(fn is not None,
              'the service could be loaded out of the view module',
              'the anchor comment moved - re-read the function before '
              'trusting section 1 alone'):
        return

    # (a) the import is broken. This is the case that has been happening on
    # every single call in production since googletrans was removed.
    real = __import__('builtins').__import__

    def no_translator(name, *a, **k):
        if name.startswith('deep_translator'):
            raise ImportError('blocked by test_translate_honest')
        return real(name, *a, **k)

    __import__('builtins').__import__ = no_translator
    try:
        res = fn('Update Kitchen')
    finally:
        __import__('builtins').__import__ = real

    ok(isinstance(res, tuple) and len(res) == 3,
       'it returns (ok, text, reason)', res)
    ok(res[0] is False, 'ok is False when the translator will not import',
       res)
    ok(res[1] is None,
       'and it does NOT hand back the English',
       'returning the input here is the entire defect: %r' % (res[1],))
    ok(isinstance(res[2], str) and res[2].strip(),
       'with a reason a user can read', res[2])
    ok('Update Kitchen' not in str(res[1]),
       'the English text is nowhere in the result')

    # (b) the network is unreachable - which is also true of this sandbox,
    # so this runs for real rather than being simulated.
    res2 = fn('Update Kitchen')
    ok(isinstance(res2, tuple) and len(res2) == 3,
       'an unreachable service also returns a result', res2)
    if res2[0]:
        print('        !! this machine REACHED the translator - '
              'the success path ran')
        ok(res2[1] and res2[1] != 'Update Kitchen',
           'and it came back translated, not echoed', res2)
    else:
        ok(res2[1] is None,
           'an unreachable service returns no text either', res2)
        print('        (no route to translate.google.com from here, which '
              'is why')
        print('         the SUCCESS path cannot be tested in this sandbox '
              '- see below)')


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. requirements.txt')
    raw = open(REQS, 'rb').read()
    ok(raw.startswith(b'\xff\xfe'),
       'requirements.txt is still UTF-16 LE with its BOM',
       'writing it back as UTF-8 hands Railway a file pip cannot read')
    text = raw.decode('utf-16')
    ok('deep-translator==1.9.1' in text, 'deep-translator is pinned in it')
    ok('googletrans' not in text, 'googletrans is not')

    before = open(REQS + SUFFIX, 'rb').read().decode('utf-16')
    added = [l for l in text.split('\r\n') if l not in before.split('\r\n')]
    ok(added == ['deep-translator==1.9.1'],
       'exactly one line was added', added)


# ------------------------------------------------------------- section 5

def section_5():
    print('\n5. what this suite did NOT test')
    print('      A successful translation. There is no route from this')
    print('      sandbox to translate.google.com, so the success path')
    print('      cannot be exercised here. On the deploy, press Translate')
    print('      Name to Greek on a task with an English name and check')
    print('      that Greek - not English - lands in the Greek field.')
    print('      If the service is down you should now see an amber')
    print('      "Translation failed" bar and an UNCHANGED Greek field.')


# ------------------------------------------------------------- section 6

def section_6():
    print('\n6. registration')
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
    print('test_translate_honest.py - TR-1, a failure arrives as a failure')
    for fn in (section_1, section_2, section_3, section_4, section_5,
               section_6):
        fn()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_translate_honest.py: all checks passed')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
