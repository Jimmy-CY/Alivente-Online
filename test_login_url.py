# -*- coding: utf-8 -*-
"""test_login_url.py - Section LU round LU-1, 5 Oct 2026.

Demetri, minutes after rotating SECRET_KEY: "Logged Out... Got this
error." The error was alivente.online/accounts/login/?next=/logout/
answering `Not Found`.

The rotation did exactly what a rotation does - it invalidated every
session cookie in existence, his own included. He pressed Logout.
logout_user carried @login_required, nobody was logged in, and Django
redirected to settings.LOGIN_URL. That setting was COMMENTED OUT, so
Django used its own default of /accounts/login/, which this project has
never routed.

WHY THIS SUITE IS NOT ABOUT LOGOUT. There are 282 @login_required
decorators across 34 view modules. Every one of them answered a dead
session with that same 404, and had done for the life of the project. It
only ever showed today because today is the first time every session
ended at once. Section 4 counts them, so the number in that sentence is
measured rather than remembered.

HOW IT PROVES THE REDIRECT. Not by reading settings.LOGIN_URL back - that
proves the assignment, not the behaviour. Section 2 wraps a trivial view
in Django's REAL login_required, hands it an anonymous request through
RequestFactory, and reads the Location header off what comes back. No
middleware, no database, no network: the decorator is the thing under
test and nothing else runs. Section 3 then resolves both the new target
and the old one through the project's own URLconf, which is what turns
"the header says /login/" into "and that URL exists".

NO SETTINGS LINE IS EVER PRINTED. mysite/settings.py holds secrets and
this file reads it. Everything here asks a SHAPE question of it and
prints a verdict, which is SE-1's rule and the reason that round exists.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_loginurl'
ME = 'test_login_url.py'
PATCHER = 'apply_login_url.py'
PS1 = 'Push-PendingChanges.ps1'

SETTINGS = os.path.join(ROOT, 'mysite', 'settings.py')
AUTH = os.path.join(ROOT, 'pages', 'views', 'auth.py')

WANT = '/login/'
DJANGO_DEFAULT = '/accounts/login/'

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


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def live_lines(text):
    """The file with its # comment lines removed.

    Both halves of this round leave a block of comments EXPLAINING the
    thing they removed, so those comments contain the words the checks
    are looking for. A check that reads a round's own explanation as
    evidence is the mistake that produced the one factual error I had to
    correct to Demetri on 4 Oct, and the patcher hit the same shape in
    its own import gate. Strip them first, every time."""
    return '\n'.join(ln for ln in text.replace('\r\n', '\n').split('\n')
                     if not ln.lstrip().startswith('#'))


def assigned(text, name):
    """The right-hand side's SHAPE, never its value.

    Returns the quoted string if `name` is assigned a plain literal at
    the margin, '' if it is assigned something else, None if it is not
    assigned at all. Only ever called for LOGIN_URL and
    LOGIN_REDIRECT_URL, and no caller prints what it returns for
    anything else."""
    m = re.search(r'^%s\s*=\s*(.+?)[ \t\r]*$' % re.escape(name),
                  text, re.M)
    if not m:
        return None
    rhs = m.group(1).strip()
    lit = re.match(r'^[\'"]([^\'"]*)[\'"]$', rhs)
    return lit.group(1) if lit else ''


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the setting that was not set')

s_now = live_lines(now(SETTINGS))
s_was = live_lines(was(SETTINGS))

ok(assigned(s_was, 'LOGIN_URL') is None,
   'LOGIN_URL really was unset before this round',
   'it was already assigned - then the 404 had another cause and this '
   'round is aimed at the wrong thing')
ok(assigned(s_now, 'LOGIN_URL') == WANT,
   'and now names %s' % WANT,
   'LOGIN_URL is %r' % (assigned(s_now, 'LOGIN_URL'),))

# Demetri chose "LOGIN_URL and free the Logout view", not the variant
# that also turned LOGIN_REDIRECT_URL on. This asserts the choice.
ok(assigned(s_now, 'LOGIN_REDIRECT_URL') is None,
   'and LOGIN_REDIRECT_URL is still not set, which was the decision',
   'this app never reads it - login_user ends on _safe_next or home')
auth_src = read(AUTH)
ok('LOGIN_REDIRECT_URL' not in auth_src,
   '  nor does the login view consult it')
ok("_safe_next(request) or 'home'" in auth_src,
   '  it redirects to the safe ?next=, or home')

# ==========================================================================
head('2. what Django actually does with it now')

django_up = False
try:
    import django
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        # SE-1 - a suite that boots Django signs with its own throwaway
        # key, so an absent .env is not a failure. setdefault, so a real
        # key always wins; this one signs nothing that leaves the test.
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    # RequestFactory signs its requests 'testserver', and the decorator
    # calls build_absolute_uri() on the way past, which checks the host.
    # Without this the round's own check dies with DisallowedHost - a
    # crash, which blocks a push as hard as a failure and says far less.
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + ['testserver']
    # RESOLVING AGAINST pages.urls, AND SAYING SO. mysite/urls.py also
    # includes crs.urls, and the sandbox mirror does not carry the crs
    # view package - importing the project root URLconf here dies on
    # `from crs.views import main`, which is a gap in the mirror and not
    # a fact about the product. pages.urls is what mysite/urls.py mounts
    # at '', and every account URL in the app lives in it.
    #
    # What that substitution cannot see is whether some OTHER include
    # answers /accounts/login/. Section 3 reads mysite/urls.py and checks
    # the prefixes directly, which settles it without importing anything.
    dj_settings.ROOT_URLCONF = 'pages.urls'
    from django.contrib.auth.decorators import login_required
    from django.contrib.auth.models import AnonymousUser
    from django.http import HttpResponse
    from django.test import RequestFactory
    django_up = True
except Exception as exc:
    ok(False, 'Django could boot', '%s: %s' % (type(exc).__name__, exc))

if django_up:
    ok(dj_settings.LOGIN_URL == WANT,
       'settings.LOGIN_URL is %s as Django reads it' % WANT,
       'Django read %r' % (dj_settings.LOGIN_URL,))

    @login_required
    def guarded(request):
        return HttpResponse('the view body, which must not run')

    def bounce(path):
        """Where Django's own decorator sends an anonymous request."""
        rq = RequestFactory().get(path)
        rq.user = AnonymousUser()
        return guarded(rq)

    r = bounce('/logout/')
    ok(r.status_code == 302, 'an anonymous request to a guarded view redirects',
       'status %s' % r.status_code)
    loc = r.headers.get('Location', '')
    ok(loc.startswith(WANT + '?'),
       'to %s, carrying where it came from' % WANT, 'Location: %s' % loc)
    ok('next=%2Flogout%2F' in loc or 'next=/logout/' in loc,
       '  and the ?next= is the page that was asked for',
       'Location: %s' % loc)
    print('      %s' % loc)

    # THE SAME CALL, WITH THE SETTING PUT BACK AS IT WAS. This is the
    # 404 Demetri saw, reproduced - not described.
    keep = dj_settings.LOGIN_URL
    try:
        dj_settings.LOGIN_URL = DJANGO_DEFAULT
        before = bounce('/logout/').headers.get('Location', '')
    finally:
        dj_settings.LOGIN_URL = keep
    ok(before.startswith(DJANGO_DEFAULT),
       'and with the setting unset it went to %s - the 404' % DJANGO_DEFAULT,
       'Location was %s' % before)
    ok(dj_settings.LOGIN_URL == WANT, '  the setting was put back')

# ==========================================================================
head('3. and that URL exists, which the old one never did')

if django_up:
    from django.urls import resolve, Resolver404
    keep_conf = dj_settings.ROOT_URLCONF

    def routed(path):
        try:
            return resolve(path).view_name
        except Resolver404:
            return None

    hit = routed(WANT)
    ok(hit is not None, '%s resolves, to %s' % (WANT, hit),
       'nothing in mysite/urls.py answers it')
    ok(routed(DJANGO_DEFAULT) is None,
       '%s resolves to nothing in pages.urls' % DJANGO_DEFAULT,
       'something answers it - then the 404 had another cause')
    ok(dj_settings.ROOT_URLCONF == keep_conf, '  the URLconf was not disturbed')

# AND NOTHING ELSE MOUNTED AT THE ROOT COULD ANSWER IT EITHER. This is
# the half pages.urls cannot speak for, so it is read off mysite/urls.py
# rather than resolved: every include has a prefix, and a prefix that is
# not '' and is not a prefix of 'accounts/' can never produce the URL.
root_urls = live_lines(now(os.path.join(ROOT, 'mysite', 'urls.py')))
prefixes = re.findall(r'(?:path|re_path)\(\s*r?[\'"]([^\'"]*)[\'"]', root_urls)
ok(prefixes.count('') == 1,
   'mysite/urls.py mounts exactly one URLconf at the root',
   'prefixes: %s' % prefixes)
ok("include('pages.urls')" in root_urls or 'include("pages.urls")' in root_urls,
   '  and it is pages.urls, the one resolved against above')
strays = [p for p in prefixes
          if p and ('accounts/'.startswith(p) or p.startswith('accounts/'))]
ok(not strays,
   '  no other mount could reach %s' % DJANGO_DEFAULT,
   'these could: %s' % strays)
print('      mounted: %s' % ', '.join(repr(p) for p in prefixes))

# ==========================================================================
head('4. the 282, which is the actual size of this')

VIEWS = os.path.join(ROOT, 'pages', 'views')
guards, files = 0, set()
for base in (VIEWS, os.path.join(ROOT, 'crs')):
    if not os.path.isdir(base):
        continue
    for dirpath, _dirs, names in os.walk(base):
        for n in names:
            if not n.endswith('.py'):
                continue
            p = os.path.join(dirpath, n)
            src = live_lines(now(p))
            c = len(re.findall(r'^@login_required', src, re.M))
            if c:
                guards += c
                files.add(os.path.relpath(p, ROOT))
ok(guards > 100,
   'the tree carries %d @login_required decorators over %d module(s)'
   % (guards, len(files)),
   'that is far fewer than expected - has the census stopped finding them?')
print('      every one of them pointed at the 404 until this round')

# ==========================================================================
head('5. logging out when you are already out')

a_now = now(AUTH)
a_was = was(AUTH)

ok(re.search(r'^@login_required[ \t\r]*\r?\ndef logout_user', a_was, re.M)
   is not None,
   'logout_user really did carry @login_required before',
   'it did not - then step 3 of the diagnosis is wrong')
ok(re.search(r'^@\w+[ \t\r]*\r?\ndef logout_user', a_now, re.M) is None,
   'and carries no decorator at all now')
ok('def logout_user(request):' in a_now, '  the view itself is still there')
ok('login_required' not in live_lines(a_now),
   '  and the import it was the only user of has gone with it')
ok('from django.contrib.auth import' in a_now and 'logout' in a_now,
   '  while logout() itself is still imported')

if django_up:
    # RUN IT, anonymously, which is the case that produced the 404.
    try:
        from importlib import import_module
        from django.contrib.sessions.backends.db import SessionStore
        mod = import_module('pages.views.auth')
        rq = RequestFactory().get('/logout/')
        rq.user = AnonymousUser()
        rq.session = SessionStore()
        out = mod.logout_user(rq)
        ok(out.status_code == 302,
           'calling it with nobody logged in redirects rather than raising',
           'status %s' % out.status_code)
        ok(out.headers.get('Location', '') == '/',
           '  to the public home page, where a Login link is',
           'Location: %s' % out.headers.get('Location', ''))
    except Exception as exc:
        ok(False, 'logout_user survives an anonymous request',
           '%s: %s' % (type(exc).__name__, exc))

# ==========================================================================
head('6. the control - a LOGIN_URL that names nothing')

# A suite that reports the redirect target without ever checking the
# target EXISTS would have passed on the broken tree, because
# /accounts/login/ is a perfectly good-looking string. The control plants
# exactly that: a setting that is set, that the decorator honours, and
# that resolves to nothing. Section 3's check is the one that must catch
# it, and it must catch it by FAILING rather than by raising.
if django_up:
    keep = dj_settings.LOGIN_URL
    caught = None
    try:
        dj_settings.LOGIN_URL = '/accounts/login/'
        rq = RequestFactory().get('/logout/')
        rq.user = AnonymousUser()
        planted = guarded(rq).headers.get('Location', '')
        target = planted.split('?')[0]
        try:
            caught = resolve(target).view_name
        except Resolver404:
            caught = None
    finally:
        dj_settings.LOGIN_URL = keep
    ok(planted.startswith('/accounts/login/'),
       'the control could be planted - the decorator honoured it')
    ok(caught is None,
       'and the check catches a LOGIN_URL that routes nowhere',
       'it resolved to %s, so the check cannot tell good from bad' % caught)
    ok(dj_settings.LOGIN_URL == WANT, 'the setting was put back exactly')
    ok(resolve(WANT).view_name is not None, 'and the tree is clean again')

# ==========================================================================
head('7. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
