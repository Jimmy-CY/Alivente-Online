# -*- coding: utf-8 -*-
"""test_settings_env.py - Section SE round SE-1, 4 Oct 2026.

Demetri: "Let's fix this now as well."

Two settings in mysite/settings.py were quoted literals - SECRET_KEY at
line 28 and USDA_API_KEY at 355 - and both are in every commit ever pushed.
SE-1 moves them to os.getenv. ANTHROPIC_API_KEY (345), GEOAPIFY_KEY (353)
and DEBUG (31) already read the environment and are not this round's.

THIS SUITE NEVER PRINTS A VALUE, AND THAT IS THE POINT OF IT.

While working out which settings were literals I printed two real secrets
into the conversation - the USDA key, because a sed pattern matched one
line shape and not another, and SECRET_KEY, because it is written with
double quotes and the pattern only matched single ones. I also told Demetri
the Anthropic key was hard-coded when it never was, having read my own
broken masking back as evidence.

So this suite asks SHAPE questions and prints VERDICTS. `is_env(name)`
returns True or False; the right-hand side of the assignment never leaves
the function that reads it, never reaches a message, never reaches an
assertion's detail string. Section 5 is a guard on the suite itself: it
scans this file and the patcher for any construct that could put a matched
value into output, and fails if one appears. A test that can leak the thing
it is protecting is worse than no test, because it is trusted.

WHAT IT CANNOT CHECK. Whether the variables are actually set in Railway.
Nothing in this repo can see that. If they are missing, Django refuses to
start on an empty SECRET_KEY and usda_client says its key is not
configured - both clear failures, neither silent, and both are why this
round was held until Demetri confirmed he had set them.

Nor does it make the old values safe. They are in git history and in a
chat transcript. Only rotation does that, and rotation is his to do -
claude/secrets_to_environment_4_oct.md has the order and the checks.
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
import ast
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_setenv'
ME = 'test_settings_env.py'
PATCHER = 'apply_settings_env.py'
PS1 = 'Push-PendingChanges.ps1'

SETTINGS = os.path.join(ROOT, 'mysite', 'settings.py')
USDA = os.path.join(ROOT, 'pages', 'usda_client.py')

# Moved by this round.
MOVED = ['SECRET_KEY', 'USDA_API_KEY']
# Already environment-read before it, and left alone. ANTHROPIC_API_KEY is
# on this list because I claimed the opposite once and was wrong.
ALREADY = ['ANTHROPIC_API_KEY', 'GEOAPIFY_KEY', 'DEBUG']

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


# --------------------------------------------------------- shape, not value

def is_env(text, name):
    """True if `name` reads the environment, False if it is a literal,
    None if it is not assigned at module level.

    THE RIGHT-HAND SIDE NEVER LEAVES THIS FUNCTION. It is not returned,
    not formatted into a message, not raised. Every caller gets a verdict.
    """
    m = re.search(r'(?m)^%s[ \t]*=[ \t]*(.*)$' % re.escape(name), text)
    if not m:
        return None
    rhs = m.group(1)
    return ('getenv' in rhs) or ('environ' in rhs)


def literal_names(text):
    """The NAMES - only ever the names - of module-level settings assigned
    a quoted literal and called something credential-shaped."""
    out = []
    for m in re.finditer(r'(?m)^([A-Z][A-Z0-9_]*)[ \t]*=[ \t]*'
                         r'(?:"[^"\n]*"|\'[^\'\n]*\')[ \t\r]*$', text):
        name = m.group(1)
        if any(w in name for w in ('KEY', 'SECRET', 'TOKEN', 'PASSWORD',
                                   'PASS', 'CREDENTIAL')):
            out.append(name)
    return out


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the two literals became environment reads')
    if not ok(os.path.isfile(SETTINGS), 'settings.py found'):
        return
    src = now(SETTINGS)
    before = was(SETTINGS)

    for name in MOVED:
        ok(is_env(before, name) is False,
           '%s really was a literal before the round' % name,
           'if it was not, this round is claiming work it did not do')
        ok(is_env(src, name) is True,
           '%s now reads the environment' % name)

    for name in ALREADY:
        ok(is_env(before, name) is True,
           '%s already read the environment before the round' % name,
           'ANTHROPIC_API_KEY is on this list because I told Demetri it '
           'was hard-coded and it never was')
        ok(is_env(src, name) is True,
           '%s still does - untouched' % name)


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. nothing credential-shaped is left as a literal')
    src = now(SETTINGS)
    left = literal_names(src)
    ok(not left,
       'no module-level setting named like a credential holds a literal',
       'still literal: %s' % left)

    before = literal_names(was(SETTINGS))
    ok(sorted(before) == sorted(MOVED),
       'and before the round there were exactly the two',
       'found %s, expected %s' % (sorted(before), sorted(MOVED)))
    print('      (names only - this suite never reads a value out)')


# ------------------------------------------------------------- section 3

def section_3():
    print('\n3. the file still works, and the readers still find their names')
    src = now(SETTINGS)
    try:
        ast.parse(src)
        ok(True, 'settings.py parses')
    except SyntaxError as e:
        ok(False, 'settings.py parses', 'line %s: %s' % (e.lineno, e.msg))

    ok(re.search(r'(?m)^import os$|^import os\b', src) is not None,
       'os is imported, so os.getenv resolves')
    ok('load_dotenv()' in src,
       'load_dotenv is still called',
       'that is what makes the local .env work in development')

    # The NAMES had to survive, because these are read through settings.
    if os.path.isfile(USDA):
        u = read(USDA)
        ok("getattr(settings, 'USDA_API_KEY'" in u,
           'usda_client still reads settings.USDA_API_KEY',
           'deleting the setting rather than re-sourcing it would have '
           'broken the nutrition lookup')
        ok('not configured' in u,
           'and already says so clearly when it is missing',
           'which is why this round invents no guard of its own')

    ai = os.path.join(ROOT, 'pages', 'views', 'recipes', 'ai_extract.py')
    if os.path.isfile(ai):
        ok("getattr(settings, 'ANTHROPIC_API_KEY'" in read(ai),
           'ai_extract still reads settings.ANTHROPIC_API_KEY',
           'the setting name has two kinds of reader and both must work')

    # CRLF: 106 of 142 templates are CRLF and so is this file.
    a = open(SETTINGS, 'rb').read()
    b = open(SETTINGS + SUFFIX, 'rb').read()
    ok((b'\r\n' in a) == (b'\r\n' in b),
       'the file did not change line endings')


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. the change is small and local')
    a = was(SETTINGS).splitlines()
    b = now(SETTINGS).splitlines()
    import difflib
    changed = [l for l in difflib.unified_diff(a, b, lineterm='', n=0)
               if l.startswith(('+', '-'))
               and not l.startswith(('+++', '---'))]
    ok(len(changed) <= 20,
       'at most 20 changed lines in settings.py',
       '%d changed' % len(changed))
    # The removed lines held the secrets, so they are counted, not shown.
    removed = [l for l in changed if l.startswith('-')]
    added = [l for l in changed if l.startswith('+')]
    print('      %d line(s) removed, %d added - contents deliberately '
          'not printed' % (len(removed), len(added)))
    ok(len(removed) == 2,
       'exactly two lines were removed',
       'one per secret - %d removed' % len(removed))


# ------------------------------------------------------------- section 5

def section_4b():
    print('\n4b. the trap this round would otherwise have set')
    import glob
    from apply_settings_env import BOOT_ANCHOR, BOOT_COUNT

    boots = [p for p in sorted(glob.glob(os.path.join(ROOT, 'test_*.py')))
             if BOOT_ANCHOR in read(p)]
    ok(len(boots) == BOOT_COUNT,
       '%d suites boot Django' % BOOT_COUNT,
       'found %d: %s' % (len(boots),
                         [os.path.basename(p) for p in boots]))

    missing = [os.path.basename(p) for p in boots
               if "os.environ.setdefault('SECRET_KEY'" not in read(p)]
    ok(not missing,
       'and every one of them supplies its own test key first',
       'without it, the moment SECRET_KEY reads the environment these die '
       'with ImproperlyConfigured on any machine with no .env:\n        %s'
       % missing)

    # It must come BEFORE django.setup is reached, not merely exist.
    late = []
    for p in boots:
        src = read(p)
        a = src.index("os.environ.setdefault('SECRET_KEY'")
        b = src.index(BOOT_ANCHOR)
        if a > b:
            late.append(os.path.basename(p))
    ok(not late,
       'and supplies it before the settings module is named', late)

    ok('setdefault' in read(os.path.join(ROOT, 'apply_settings_env.py')),
       'the test key is a setdefault, so a real key always wins',
       'a plain assignment would override the environment in a real run')
    print('      test_auth_flow found this within minutes of SE-1 being')
    print('      applied, making a password-reset token. On a laptop with')
    print('      a .env it would never have shown.')


def section_5():
    print('\n5. the guard on this suite itself')
    me = read(os.path.join(ROOT, ME))
    pat = read(os.path.join(ROOT, PATCHER))

    # A matched right-hand side must never reach output. These are the
    # shapes that would put one there.
    leaky = re.compile(
        r'print\([^)]*\bm\.group\(|'
        r'print\([^)]*\brhs\b|'
        r'SystemExit\([^)]*\bm\.group\(|'
        r'%\s*\(?\s*rhs\b')
    for name, src in (('this suite', me), ('the patcher', pat)):
        hits = [src[max(0, m.start() - 40):m.start() + 50]
                for m in leaky.finditer(src)]
        ok(not hits,
           '%s never prints a matched right-hand side' % name,
           '\n'.join(hits[:3]))

    ok('return (\'getenv\' in rhs) or (\'environ\' in rhs)' in me
       or "return ('getenv' in rhs) or ('environ' in rhs)" in me,
       'is_env answers with a verdict, not the text',
       'the whole lesson of this round is in that one return')

    # And the names of the moved settings must not appear beside a quoted
    # literal anywhere in the round's own files.
    for name, src in (('this suite', me), ('the patcher', pat)):
        bad = []
        for setting in MOVED:
            if re.search(r'%s[ \t]*=[ \t]*(?:"[^"\n]{12,}"|\'[^\'\n]{12,}\')'
                         % setting, src):
                bad.append(setting)
        # The patcher's replacement lines are os.getenv calls, which are
        # short and contain no secret; the 12-character floor keeps them
        # out of this without exempting anything real.
        ok(not bad,
           '%s holds no literal for a moved setting' % name, bad)


# ------------------------------------------------------------- section 6

def section_6():
    print('\n6. what this round did NOT do')
    print('      It did not make the old values safe. Both are in git')
    print('      history and both were printed into the conversation that')
    print('      produced this round. Rotating them is what ends that, and')
    print('      rotation is Demetri\'s: the USDA key at FoodData Central,')
    print('      the Anthropic key in the console, and SECRET_KEY with')
    print('      get_random_secret_key() at a quiet hour, because it logs')
    print('      everyone out. Order and checks:')
    print('      claude/secrets_to_environment_4_oct.md')
    print('')
    print('      It also cannot see Railway. If a variable is missing there,')
    print('      Django refuses to start on an empty SECRET_KEY and')
    print('      usda_client says its key is not configured. Both loud.')


# ------------------------------------------------------------- section 7

def section_7():
    print('\n7. registration')
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
    print('test_settings_env.py - SE-1, two secrets leave settings.py')
    for fn in (section_1, section_2, section_3, section_4, section_4b,
               section_5,
               section_6, section_7):
        fn()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_settings_env.py: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
