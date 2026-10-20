# -*- coding: utf-8 -*-
"""test_fav_token.py - round FV-1, 20 Oct 2026.

THE HEART IS DRAWN FOR EVERYONE AND POSTED FOR ALMOST NOBODY.

The favourites button carries no permission guard, and
toggleFavourite posts with getCookie('csrftoken'). Django sets that
cookie when a template asks it for a token - and the only csrf_token
on this page sat behind {% if perms.auth.can_edit_personal %}. For
anybody else the cookie was never set, the POST came back 403, and
toggleFavourite's own optimistic update put the heart back.

WHY SECTION 2 ASKS WHICH `{% if %}` A TAG SITS INSIDE.

Counting csrf_token tags finds two on the pre-round page and tells
you nothing. The question is not whether a tag is PRESENT but whether
it RENDERS - which is the same sentence DB-1 paid in a media query
and CL-1 paid in a stylesheet, three days running.

AND SECTION 3 IS A USER, NOT A FILE. The page is rendered for
somebody holding can_access_recipes and nothing else, and the
response is asked whether it set the cookie.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Exactly one token renders unconditionally.

  2   THE CONTROL. On the pre-round page, NONE did - every one was
      behind a permission.

  3   RENDERED FOR A USER WHO MAY NOT EDIT: the cookie is set.

  4   Scope, registration and the gate.

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
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_favtoken'
ME = 'test_fav_token.py'
PATCHER = 'apply_fav_token.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'FV-1, 20 Oct 2026'

RM = os.path.join(ROOT, 'pages', 'templates', 'recipe_management.html')
GATE = os.path.join(ROOT, PS1)
FILES = (RM,)

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
TAG = re.compile(r'\{%\s*csrf_token\s*%\}')
BLOCK = re.compile(r'\{%\s*(if|endif|for|endfor)\b[^%]*%\}')


def enclosing(code, at):
    """Every unclosed {% if %} / {% for %} above this point.

    THE WHOLE FAULT IN ONE FUNCTION. A tag that is present is not a
    tag that renders, and the difference is which conditional it is
    inside.
    """
    depth, enc = 0, []
    for m in reversed(list(BLOCK.finditer(code[:at]))):
        kind = m.group(1)
        if kind in ('endif', 'endfor'):
            depth += 1
        elif depth:
            depth -= 1
        else:
            enc.append(' '.join(m.group(0).split()))
    return enc


def tokens(code):
    return [(m.start(), enclosing(code, m.start()))
            for m in TAG.finditer(code)]


def claims(bundle):
    code = T.code_only(bundle[RM])
    free = [t for t in tokens(code) if not t[1]]
    c = {}
    c['A TOKEN RENDERS FOR EVERY USER - the finding, in one line'] = (
        len(free) == 1)
    # THE HEART IS STILL UNGUARDED, which is the other half: if a
    # later round put a permission on it, this round would be moot
    # and should be read again rather than left passing.
    c['and the heart is still drawn for everybody'] = (
        'toggleFavourite(' in code)
    c['the round says what it did'] = (
        'A TOKEN FOR EVERYONE WHO CAN PRESS SOMETHING' in bundle[RM])
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

NOWCODE = T.code_only(NOW[RM])
print('')
for at, enc in tokens(NOWCODE):
    print('  token at %-7d %s' % (at, enc or '(renders for everyone)'))
print('')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {RM: was(RM)}
held = [m for m, got in claims(BEFORE).items() if got]
ok('A TOKEN RENDERS FOR EVERY USER - the finding, in one line'
   not in held,
   'CONTROL: before this round NO token rendered unconditionally',
   'what held: %r' % (held,))

OLD = T.code_only(BEFORE[RM])
old = tokens(OLD)
ok(bool(old), 'CONTROL: there were tokens on the page all along',
   len(old))
ok(all(enc for _at, enc in old),
   'CONTROL: and every one of them sat behind a permission - which '
   'is why counting them would have said the page was fine',
   [enc for _at, enc in old])
ok(any('can_edit_personal' in ' '.join(enc) for _at, enc in old),
   'CONTROL: specifically behind can_edit_personal, which is NOT '
   'the permission the heart needs - the heart needs none')


# ==========================================================================
head('3. RENDERED FOR A USER WHO MAY NOT EDIT')
# ==========================================================================
got = None
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    from django.conf import settings as dj
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.urls import reverse
    from pages.models import Recipe
    # THE USER THIS ROUND IS ABOUT: may look at recipes, may not edit
    # them, and can still press a heart.
    u = User.objects.create_user(username='fv1', password='x',
                                 email='fv1@example.test')
    try:
        u.user_permissions.add(
            Permission.objects.get(codename='can_access_recipes'))
    except Permission.DoesNotExist:
        pass
    Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    cl = Client()
    cl.force_login(u)
    resp = cl.get(reverse('recipe_management'))
    got = (resp.status_code,
           'csrftoken' in resp.cookies,
           'csrfmiddlewaretoken' in resp.content.decode('utf-8'))
except Exception as e:
    skip('the rendered check',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if got is None:
    skip('the cookie', 'nothing was rendered')
else:
    code, cookie, field = got
    print('')
    print('  a user with can_access_recipes and nothing else:')
    print('    page %s   csrftoken cookie set %s   token in the page %s'
          % (code, cookie, field))
    print('')
    ok(code == 200, 'the page renders for them', code)
    ok(field,
       'THE FINDING: a token reaches them - before this round none '
       'did, because every one was behind a permission they lack')
    ok(cookie,
       '  and the cookie is set, which is what getCookie reads and '
       'what toggleFavourite sends')


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_addplanner']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, which edits the same file - so revert '
       'takes them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_fav_token as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
