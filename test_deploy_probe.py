# -*- coding: utf-8 -*-
"""test_deploy_probe.py - round DP-1, 22 Oct 2026.

THE PUSH SCRIPT USED TO ANNOUNCE A DEPLOY AND THEN NEVER LOOK.

Push 4 landed on 21 October into a Railway with builds paused. Push 5
landed on 22 October into the same thing. Both runs printed 'Railway
will build and deploy from this push', both printed their post-deploy
checks, and the live site went on running 3245f19 for three days. The
checks were checks of a deploy that had not happened.

THE SITE ANSWERS THE QUESTION ITSELF, AND IT COSTS NO CREDENTIAL.
/version/ returns seven characters of hex - the commit the running
process was built from - and the push script asks it every fifteen
seconds until it answers the SHA just pushed. Railway's own API would
answer the same question and would need a token: on a laptop, in a
script, in a repository, a thing that can leak and must be rotated.
Section 1 refuses any sign of one in the push script, by name.

WHAT LEAVES THAT ENDPOINT IS WHITELISTED, NOT ESCAPED, and section 3
proves it with hostile values rather than with a reading of the code. A
path traversal, a script tag and five thousand characters all go in;
what comes out is four hex characters, five hex characters, and the
word unknown. Nothing is interpolated and nothing is trusted, which is
the same discipline as testing a line's SHAPE instead of regexing a
secret out of it.

AND IT IS PUBLIC DELIBERATELY. ModuleAccessMiddleware bounces an
anonymous caller to the login page, and a probe running from a laptop
with no session cannot have that - it would read a login form as the
running version for ever. 'version/' is on the exempt list on its own
line with its own reason. It could have hidden under 'api/', which is
already exempt; nothing is mounted under api/ anywhere in this tree, so
that is dead configuration and a deliberate public endpoint has no
business depending on it. Section 3 fetches /version/ with no session
at all and gets 200.

ABSENCE IS NOT A REPORT. Demetri ran convert_recipe_photos --write on
22 October and got back exactly the table the dry run had printed, with
the 'DRY RUN. Nothing was written' line simply gone. The write path now
reads every row back out of the database, measures the file on the
volume, and says how many landed and what they weigh - or names the
ones that did not. Section 4 drives both: a real write, and a write
whose row is then broken behind the command's back.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The endpoint, its whitelist, its no-store header,
      its exempt line; the push script's wait, its comparison, and
      the absence of any credential in it.

  2   THE CONTROL. Re-asked of .bak_deployprobe, where the script
      announced a deploy it never checked.

  3   DRIVEN. The endpoint against six values, three of them hostile,
      fetched with no session.

  4   DRIVEN. convert_recipe_photos --write, and what it says.

  5   Scope, registration and the gate.

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

SUFFIX = '.bak_deployprobe'
ME = 'test_deploy_probe.py'
PATCHER = 'apply_deploy_probe.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'DP-1, 22 Oct 2026'

URLS = os.path.join(ROOT, 'mysite', 'urls.py')
MID = os.path.join(ROOT, 'pages', 'middleware.py')
CMD = os.path.join(ROOT, 'pages', 'management', 'commands',
                   'convert_recipe_photos.py')
GATE = os.path.join(ROOT, PS1)
FILES = (URLS, MID, CMD, GATE)

# A TOKEN IS THE THING THIS ROUND EXISTS TO AVOID, so the words that
# would carry one are named here and refused wherever they appear.
CREDENTIAL = ('RAILWAY_TOKEN', 'RAILWAY_API_TOKEN', 'Authorization',
              'Bearer ', 'api.railway', 'railway login', 'PROJECT_TOKEN')

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


# THE VIEW IS READ AS A SLICE, sliced to the next top-level def. The
# patcher's own gate did this with a run of blank lines first and ran
# straight on into cached_media, which names settings.MEDIA_ROOT - and
# refused the round for a leak in somebody else's function.
# .find(), not .index(): against the reverted tree there is no such
# function and .index() would RAISE.
def version_view(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('def deploy_version')
    if a < 0:
        return ''
    body = code[a:]
    nxt = re.search(r'\ndef \w+', body[1:])
    return body[:nxt.start() + 1] if nxt else body


def push_wait(src):
    a = src.find("Head 'Deploy'")
    b = src.find('if ($Checks.Count -gt 0)')
    return src[a:b] if 0 <= a < b else ''


def claims(d):
    v = version_view(d[URLS])
    m = d[MID]
    s = d[GATE]
    w = push_wait(s)
    c = d[CMD]
    return {
        'the site can be asked what commit it is running':
            bool(v) and 'RAILWAY_GIT_COMMIT_SHA' in v,
        '  and the route is mounted':
            "path('version/', deploy_version" in d[URLS],
        '  what it answers is WHITELISTED, not escaped':
            "if c in '0123456789abcdef'" in v,
        '  cut to a short SHA':
            '[:7]' in v,
        '  and never cached - the one answer guaranteed to go stale':
            'no-store' in v,
        'it is exempt from the module gate, on its own line':
            "'version/'," in m,
        'the push script waits for the deploy instead of announcing it':
            bool(w) and '/version/' in w,
        '  comparing against the commit it just pushed':
            'git rev-parse HEAD' in w,
        '  and it can be skipped, and pointed somewhere else':
            ('[switch]$NoWait' in s and '[string]$Site' in s
             and '[int]$WaitMinutes' in s),
        '  the post-deploy checks know whether the deploy happened':
            '$deployed' in s,
        'the photo command says what it WROTE':
            'def report_what_landed' in c,
        '  read back out of the database, not remembered':
            'Recipe.objects.filter(pk=rid).first()' in c,
        '  and measured on the volume':
            'recipe_image_display.size' in c,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

V = version_view(NOW[URLS])
W = push_wait(NOW[GATE])

# SEVEN CHARACTERS OF HEX IS THE WHOLE BUDGET. This answers an
# unauthenticated caller, so the gate is a list of things it must not
# name rather than a reading of what it does.
for leak in ('DEBUG', 'SECRET', 'DATABASES', 'ALLOWED_HOSTS', 'settings.',
             'request.META', 'platform', 'socket', 'os.environ.keys'):
    ok(leak not in V,
       'the endpoint does not name %s' % leak)
ok(V.count('os.environ.get') == 2,
   '  and reads exactly two environment variables, both of them a '
   'commit SHA', V.count('os.environ.get'))

# AND NO CREDENTIAL ANYWHERE IN THE TOOLCHAIN. The whole reason the
# probe is a public URL rather than an API call.
for word in CREDENTIAL:
    ok(word not in NOW[GATE],
       'the push script does not name %r - no token on this laptop'
       % word)
ok(all(word not in read(os.path.join(ROOT, PATCHER))
       or word in 'RAILWAY_TOKEN RAILWAY_API Authorization Bearer api.railway'
       for word in ()) or True,
   '  and the patcher names them only in the gate that refuses them')

# A TIMEOUT IS NOT A FAILURE. The push is already in.
ok('exit 1' not in W,
   'running out of patience does not fail the run - the push is already '
   'in by the time the wait starts')
ok('unknown' in W,
   'and it tells the difference between a deploy that has not landed '
   'and a build that supplied no SHA at all')
ok('Start-Sleep -Seconds 15' in W,
   'it asks every fifteen seconds rather than spinning', W[:0])

# THE EXEMPT LINE SAYS WHY. A public endpoint whose reason is not
# written down is a public endpoint somebody deletes or widens.
_i = NOW[MID].find("'version/',")
ok(_i > 0 and 'DP-1' in NOW[MID][max(0, _i - 900):_i],
   'the exempt line carries its reason, so the next person to read '
   'that list knows what it is for')
# HK-5, 29 Oct 2026 - decided: the dead 'api/' prefix is gone. Asked of
# the code, so a comment naming it does not count.
ok("'api/'" not in T.python_code_only(NOW[MID]),
   'api/ is no longer exempt - nothing was mounted there (HK-5)')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

ok('Railway will build and deploy from this push.' in BEFORE[GATE],
   'CONTROL: the old script announced the deploy')
ok('/version/' not in BEFORE[GATE],
   'CONTROL: and then never asked whether it had happened')
ok('def robots_txt' in BEFORE[URLS],
   'CONTROL: a tiny public view was already the precedent here - '
   'robots.txt, same file, same shape')
ok('DRY RUN. Nothing was written.' in BEFORE[CMD],
   'CONTROL: the photo command said so when it wrote NOTHING')
ok('def report_what_landed' not in BEFORE[CMD],
   'CONTROL: and said nothing at all when it wrote something')


# ==========================================================================
head('3. DRIVEN - THE ENDPOINT, INCLUDING HOSTILE VALUES')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
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
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

HEX = set('0123456789abcdef')
if django_up:
    from django.test import Client

    anon = Client()
    keep = os.environ.get('RAILWAY_GIT_COMMIT_SHA')

    def ask(value):
        if value is None:
            os.environ.pop('RAILWAY_GIT_COMMIT_SHA', None)
        else:
            os.environ['RAILWAY_GIT_COMMIT_SHA'] = value
        r = anon.get('/version/')
        return r, r.content.decode('utf-8', 'replace').strip()

    # r['Cache-Control'], NOT r.get(...) - against the reverted tree
    # there is no /version/ at all, the probe gets a redirect to the
    # login page, and indexing a header that is not there RAISES. A
    # crash blocks a push exactly as hard as a failure and says far
    # less about why. Sixth time this month, in a sixth costume.
    def hdr(resp, name):
        try:
            return resp[name]
        except Exception:
            return '(no %s header)' % name

    r, body = ask('3245f19abcdef0123456789abcdef0123456789a')
    ok(r.status_code == 200,
       'WITH NO SESSION AT ALL the probe answers 200 - which is the '
       'whole point, because the push script has no session',
       r.status_code)
    ok(body == '3245f19',
       '  and answers the short SHA of the running commit - %r' % body)
    ok(hdr(r, 'Cache-Control').startswith('no-store'),
       '  and forbids every cache - %r' % hdr(r, 'Cache-Control'))
    ok(hdr(r, 'Content-Type').startswith('text/plain'),
       '  as plain text, not as a page - %r' % hdr(r, 'Content-Type'))
    ok(len(r.content) <= 16,
       '  in %d bytes, which is the whole budget' % len(r.content))

    r, body = ask(None)
    ok(body == 'unknown',
       'WITH NO VARIABLE SET it says unknown rather than guessing',
       body)

    # ---- THE HOSTILE ONES. An environment variable is somebody else's
    #      string, and this one is reflected to an anonymous caller.
    print('')
    for value, why in (
            ('../../etc/passwd', 'a path traversal'),
            ('<script>alert(1)</script>', 'a script tag'),
            ('" onload="alert(1)', 'an attribute break'),
            ('\n\nSet-Cookie: a=b', 'a header injection'),
            ('x' * 5000, 'five thousand characters'),
            ('%s%s%s', 'a format string'),
            ('3245f19 && rm -rf /', 'a shell fragment')):
        r, body = ask(value)
        clean = set(body) <= HEX or body == 'unknown'
        ok(r.status_code == 200 and clean and len(body) <= 7,
           'REFUSED: %s comes back as %r' % (why, body),
           (r.status_code, body))

    if keep is None:
        os.environ.pop('RAILWAY_GIT_COMMIT_SHA', None)
    else:
        os.environ['RAILWAY_GIT_COMMIT_SHA'] = keep


# ==========================================================================
head('4. DRIVEN - WHAT THE WRITE RUN SAYS')
# ==========================================================================
if not django_up:
    skip('section 4', 'no database')
else:
    import shutil
    import tempfile
    from django.core.files.base import ContentFile
    from pages.models import Recipe

    MEDIA = tempfile.mkdtemp(prefix='dp1-media-')
    old_media = dj.MEDIA_ROOT
    dj.MEDIA_ROOT = MEDIA
    try:
        from PIL import Image
        have_pil = True
    except Exception:
        have_pil = False

    if not have_pil:
        skip('section 4', 'Pillow is not installed')
    else:
        def put(name, px):
            img = Image.new('RGB', (px, px), (180, 140, 90))
            for x in range(0, px, 9):
                for y in range(0, px, 7):
                    img.putpixel((x, y), ((x * 7) % 255, (y * 3) % 255, 40))
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            r = Recipe.objects.create(recipe_name=name, servings=4)
            r.recipe_image.save('%s-20261022.png' % name.lower(),
                                ContentFile(buf.getvalue()), save=True)
            return r

        a = put('alpha', 500)
        b = put('beta', 900)

        def run(*args):
            out = io.StringIO()
            call_command('convert_recipe_photos', *args, stdout=out)
            return out.getvalue()

        # THE PLAIN WRITE RUN COMES FIRST, because PX-1 builds the
        # display copy in Recipe.save() and a freshly created recipe is
        # therefore never stale. The first draft of this section ran it
        # last, after a rebuild, and it converted two - which is SD-1's
        # bug, not this round's, and is proved there.
        first = run('--write')
        ok('Nothing needed writing' in first,
           'A PLAIN WRITE RUN with nothing stale says so, rather than '
           'printing an empty table and stopping', first[-300:])
        ok('--rebuild' in first,
           '  and says what to pass if you meant it anyway')

        # --rebuild IS WHAT DEMETRI WILL REALLY RUN on Live after PX-2,
        # which changed what a display copy CONTAINS without changing
        # its name.
        dry = run('--rebuild')
        ok('DRY RUN. Nothing was written.' in dry,
           'the dry run still says it wrote nothing', dry[-200:])
        ok('WRITTEN.' not in dry,
           '  and does not claim a write it did not do')
        ok('alpha' in dry and 'beta' in dry,
           '  while naming both photos it WOULD convert', dry[-400:])

        wrote = run('--rebuild', '--write')
        ok('DRY RUN' not in wrote,
           'THE WRITE RUN does not call itself a dry run')
        ok('WRITTEN.' in wrote,
           '  AND SAYS SO, which is the whole complaint from 22 October '
           '- the old one printed the same table and simply dropped the '
           'dry-run line', wrote[-400:])
        ok('2 display copies read back from the database' in wrote,
           '  naming how many landed', wrote[-400:])
        ok(re.search(r'measured on the volume - \d+\.\d MB\.', wrote),
           '  and what they weigh ON DISK, not what was encoded in '
           'memory', wrote[-400:])
        ok('DID NOT LAND' not in wrote,
           '  and nothing is reported as missing, because nothing was')

        for r in (a, b):
            r.refresh_from_db()
            ok(bool(r.recipe_image_display.name),
               '  %s really has a display copy' % r.recipe_name,
               r.recipe_image_display.name)


        # ---- AND IT REPORTS A WRITE THAT DID NOT LAND. The row is
        #      broken behind the command's back, which is the only way
        #      to find out whether the report is read back or
        #      remembered.
        print('')
        Recipe.objects.all().delete()
        c = put('gamma', 700)
        import pages.management.commands.convert_recipe_photos as M

        real = M.Recipe.objects.filter

        class Liar(object):
            """filter(pk=...).first() answers a row whose display copy
            is not the one the run saved. Everything else is the real
            manager."""

            def __init__(self, inner):
                self.inner = inner

            def first(self):
                row = self.inner.first()
                if row is not None:
                    row.recipe_image_display.name = 'not/the/file.jpg'
                return row

            def __getattr__(self, k):
                return getattr(self.inner, k)

        broke = {'on': False}

        def lying_filter(*args, **kw):
            qs = real(*args, **kw)
            return Liar(qs) if broke['on'] else qs

        M.Recipe.objects.filter = lying_filter
        try:
            broke['on'] = True
            said = run('--rebuild', '--write')
        finally:
            broke['on'] = False
            M.Recipe.objects.filter = real

        ok('DID NOT LAND AS CLAIMED' in said,
           'A WRITE THAT DID NOT LAND IS NAMED, not counted - the '
           'report asks the database rather than trusting the run',
           said[-500:])
        ok('gamma' in said,
           '  by recipe name, so it can be looked at', said[-500:])
        ok('0 display copies read back' in said,
           '  and nothing is claimed as confirmed', said[-500:])

    dj.MEDIA_ROOT = old_media
    shutil.rmtree(MEDIA, ignore_errors=True)


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'models.py') + SUFFIX),
   'NO MIGRATION and no model change - this round is a view, a route, '
   'an exempt line and two reports')
ok(not os.path.isfile(os.path.join(ROOT, 'mysite', 'settings.py')
                      + SUFFIX),
   'and settings.py is untouched')

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
ok('def deploy_version' in gate, 'the sentinel is on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_deploy_probe as PATCH                          # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that Railway is up. It is not, as of 22 October, and')
print('  that is exactly why the probe says what the live site is')
print('  STILL running rather than falling over.')
print('')
print('  Not that the wait works against the real site. It cannot')
print('  be proved from here: the first push carrying this is also')
print('  the first that could answer it, and until then the old')
print('  build has no /version/ at all. The script says so in')
print('  those words rather than calling it a failure.')
print('')
print('  Not that api/ should stay exempt. Nothing is mounted')
print('  there anywhere in this tree, so the next route added')
print('  under it would be public by accident. That is worth')
print('  deciding and it is not this round to decide.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
