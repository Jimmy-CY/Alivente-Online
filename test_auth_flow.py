# -*- coding: utf-8 -*-
"""test_auth_flow.py - Section A round A1, 1 Oct 2026.

Demetri, in three findings: the word Login showed twice; a failed login
showed no red message and a stale success bar turned up on the NEXT visit
instead; and resetting somebody's password should email them a link to a
page where they type a new one twice.

WHY THIS SUITE IS DIFFERENT FROM EVERY OTHER SUITE IN THIS REPO.

Almost all of them read templates and measure rendered CSS, because almost
every round changes what a page LOOKS like. This round changes what the
system DOES, and the parts that can be wrong are not visible in any
markup: whether a token is really single-use, whether it really dies after
three days, whether four password validators that have been configured
since the project started actually run, whether a person who is logged out
can even reach the page the email points at.

So section 5 BUILDS A DATABASE AND DRIVES THE REAL VIEWS. It loads the
project's own settings, swaps DATABASES to sqlite in memory, runs every
migration (which also proves 0096 applies), and puts requests through
Django's test Client - the real URLconf, the real middleware stack, the
real templates. Nothing is re-implemented here; the thing under test is
the thing that ships.

THAT IS NOT GOLD-PLATING, AND HERE IS THE PROOF. While this was being
written, the flow was complete and correct: URLs resolved, templates
compiled, tokens checked out, views were right. And the feature did not
work at all, because ModuleAccessMiddleware bounces any path not on its
exempt list to the login page when the caller is anonymous - and somebody
following an emailed password link is anonymous by definition. Every
static check passed. The round was dead. Only driving it found that.
Section 5b is the control for it: it puts the exemption back and shows the
link redirecting to a login page the person cannot use.

AND THE OTHER THING THAT NEARLY GOT THROUGH. `'alv-message' in html` is
True on every page in this system whether a bar rendered or not, because
base.html's own stylesheet and its own fade script both contain the
string. Section 5a matches the rendered ELEMENT. A check that is true no
matter what is not a check.

SECTION 4 OWNS THE CLOCK. Expiry is proved by moving the token
generator's idea of now, so the suite can show the link alive at three
days and dead at four without waiting three days and without ever being
able to age.

SECTION 6 IS THE PHONE, and it renders the page WITH DJANGO rather than
with a fixture that resolves {% if %} by hand. The P5 lesson one round
ago was that a fixture picks a branch and a suite then reports one branch
as the page. Letting Django render it removes the whole class of error.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import datetime
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_authflow'
ME = 'test_auth_flow.py'
PATCHER = 'apply_auth_flow.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
BOOTP = os.path.join(ROOT, BOOT)
WIDTHS = (320, 360, 386, 414)

NEW_FILES = (
    'pages/password_reset.py',
    'pages/templates/password_set.html',
    'pages/templates/password_set_invalid.html',
    'pages/templates/password_set_done.html',
    'pages/templates/password_forgot.html',
    'pages/migrations/0096_notification_type_password_reset.py',
)
TOUCHED = (
    'pages/templates/login.html',
    'pages/templates/user_add.html',
    'pages/templates/user_edit.html',
    'pages/templates/user_administration.html',
    'pages/templates/base.html',
    'pages/views/auth.py',
    'pages/views/users.py',
    'pages/views/notifications.py',
    'pages/urls.py',
    'pages/middleware.py',
    'pages/models.py',
    'pages/email_utils.py',
    'mysite/settings.py',
    # TWO SUITES THAT KEEP A NUMBER. A round that adds pages has to move
    # the counts those numbers are about, in the same round - the ledger
    # pattern P2 and N3 followed. See section 8b.
    'test_house_title.py',
    'test_modal_heads.py',
    'test_tree_roots.py',
    'test_subtree_tones.py',
    'test_save_and_cancel.py',
)
VALIDATORS = ('UserAttributeSimilarityValidator', 'MinimumLengthValidator',
              'CommonPasswordValidator', 'NumericPasswordValidator')

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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def _probe_failed(path, err):
    """A browser that cannot start is not the same news as a measurement
    that disagrees, and the two must not print the same way."""
    print('  !! the browser could not measure %s' % os.path.basename(path))
    print('     %s' % str(err).split('\n')[0][:120])


def abspath(rel):
    return os.path.join(ROOT, rel.replace('/', os.sep))


def markup_of(t):
    """Markup with comments, script and style removed.

    {# #} FIRST, and this is not cosmetic: round P3's suite counted its own
    round's sentinel comment as page markup and reported three Bootstrap
    classes that were not there. A check that reads text catches prose."""
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def styles_raw(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in re.finditer(r'<style\b[^>]*>(.*?)</style\s*>',
                                          t, re.S | re.I))


def fresh(u):
    """The user as the DATABASE has them, before a token is made from them.

    NOT HOUSEKEEPING - A TOKEN BINDS TO last_login. Django's
    PasswordResetTokenGenerator hashes the user's password hash, pk, email
    AND last_login, so a token made from a stale in-memory user hashes the
    last_login that user had when it was loaded, while check_token loads
    the row fresh and hashes the real one. The two disagree and the link
    says it cannot be used.

    This cost twenty minutes: section 5b logged a user in, then made a
    token from the Python object it still had, and the suite reported a
    good link as broken. The code was right; the suite was holding a stale
    user. It is also a real property worth knowing - logging in
    invalidates any outstanding set-password link for that account."""
    u.refresh_from_db()
    return u


def bars(html):
    """The message bars that actually RENDERED, as (tag, text).

    NOT `'alv-message' in html`. base.html's own stylesheet carries
    `.alv-message { text-align: center; }` and its fade script carries
    `.alv-message.alert-success`, so that substring is present on every
    page in the system whether a bar rendered or not. This matches the
    element. The weaker check was in this file for twenty minutes and
    reported a message bar on a page that had none."""
    return [(m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip())
            for m in re.finditer(
                r'class="alert alert-(\w+)[^"]*alv-message"[^>]*>\s*'
                r'([^<]{3,600})', html)]


# ==========================================================================
head('1. THE FIVE NEW FILES ARE THERE, AND EACH ONE SAYS WHY IT EXISTS')
# ==========================================================================
for rel in NEW_FILES:
    p = abspath(rel)
    if not ok(os.path.isfile(p), '%s' % rel):
        continue
    src = read(p)
    ok(ME in src, '  and names this suite, so a reader can find the checks')

for rel in TOUCHED:
    p = (alv_tree.path_of(rel[len('pages/templates/'):])
         if rel.startswith('pages/templates/') else abspath(rel))
    ok(os.path.isfile(p + SUFFIX), '%-40s has its backup' % rel)

# ==========================================================================
head('2. THE LOGIN SCREEN - ONE HEADING, AND A BAR IT CAN SHOW')
# ==========================================================================
LP = alv_tree.path_of('login.html')
now = read(LP)
was = read(LP + SUFFIX) if os.path.isfile(LP + SUFFIX) else None
m = markup_of(now)

ok(m.count('>LOGIN<') == 1 and '<h3 class="text-center">Login</h3>' not in m,
   'the word Login appears as ONE heading, not two',
   'page-title %d, h3 present %s'
   % (m.count('>LOGIN<'), '<h3 class="text-center">Login</h3>' in m))
ok('{% for msg in messages %}' in m and 'alv-message' in m,
   'it has the house message loop - which is what makes the red bar possible')
ok('btn action-secondary" type="button" id="togglePassword"' in m,
   'the eye toggle wears the house neutral button, not btn-outline-secondary')
ok('btn-outline-secondary' not in m, '  and Bootstrap\'s raw outline is gone')
ok('fas fa-eye' in m and '"fa fa-eye"' not in m,
   '  and the glyph is fas, the family the rest of the system uses')
ok("{% url 'password_forgot' %}" in m, 'Forgot password is linked')
ok('New account and never set one' in m,
   '  and the new-account line is PERMANENT, not conditional - a hint shown '
   'only when the username exists would answer whether it exists')
ok('name="next"' in m, 'a safe ?next= is carried through the form')

# THE CONTROL. The backup must NOT have had a message loop, or the claim
# that finding 2 was caused by finding 1 is a story rather than a finding.
if was is None:
    skip('the control', 'no backup of login.html')
else:
    bm = markup_of(was)
    ok('{% for msg in messages %}' not in bm,
       'CONTROL: the backup had NO message loop at all - which is why the '
       'error the view queued surfaced on a later page')
    ok('<h3 class="text-center">Login</h3>' in bm,
       'CONTROL: and it really did carry the second heading')

# ==========================================================================
head('3. THE ADMINISTRATOR STOPS TYPING PASSWORDS')
# ==========================================================================
# Every template in the tree, not the three that were edited, because the
# next screen to grow a password field has to fail here and not on Live.
offenders = {}
for q in alv_tree.templates():
    rel = alv_tree.rel(q).replace(os.sep, '/')
    if rel == 'password_set.html':
        continue
    hits = sorted(set(re.findall(
        r'name="(password1|password2|new_password1|new_password2)"',
        markup_of(read(q)))))
    if hits:
        offenders[rel] = hits
ok(not offenders,
   'no template outside password_set.html posts a password field', offenders)

UP = abspath('pages/views/users.py')
users_src = read(UP)
nocomment = re.sub(r'#.*', '', users_src)
ok(not re.search(r'\bset_password\s*\(', nocomment),
   'views/users.py calls set_password NOWHERE - the four validators cannot '
   'be walked round from the admin screens')
ok('set_unusable_password' in users_src or 'password=None' in nocomment,
   '  and user_add creates the account with no usable password')
ok('email__iexact' in nocomment,
   '  and the duplicate-email check is case-insensitive, like the lookup '
   'Forgot Password does')

add_now = read(alv_tree.path_of('user_add.html'))
edit_now = read(alv_tree.path_of('user_edit.html'))
for name, src in (('user_add.html', add_now), ('user_edit.html', edit_now)):
    ok('checkPasswordStrength' not in src,
       '%-20s the dead strength-meter script went with the fields' % name)
    ok('.password-strength {' not in src,
       '%-20s   and so did its stylesheet - six literal hexes fewer' % '')
ok('required' in re.search(r'name="email"[^>]*>', add_now).group(0),
   'user_add marks email required in the markup as well as the view')
ok('required' in re.search(r'name="email"[^>]*>', edit_now).group(0),
   'user_edit does too - an edit that could CLEAR it would undo the rule')

# The reset trigger, and the popup Demetri asked for.
ua = read(alv_tree.path_of('user_administration.html'))
ok('icon-reset-pw' in markup_of(ua),
   'the user list has a Reset Password row action')
ok('resetPwModal' in ua and 'resetPwEmail' in ua,
   '  behind a dialog that NAMES THE ADDRESS before anything is sent')
base_src = read(alv_tree.path_of('base.html'))
ok('.icon-reset-pw' in styles_raw(base_src),
   '  and its colour is a name in base, not a hex on the page')
ok(re.search(r'\.icon-reset-pw\s*\{[^}]*var\(--alv-warn\)', styles_raw(base_src))
   is not None,
   '  aliased onto --alv-warn: no new hex entered the palette')

# user_edit's reset form must sit OUTSIDE the edit form.
i_end = edit_now.rfind('</form>')
i_modal = edit_now.find('resetPwModal')
ok(i_modal > 0 and i_modal > edit_now.find('</form>'),
   'user_edit\'s reset form is OUTSIDE the edit form - a form inside a form '
   'is invalid HTML and the browser drops the inner one')

st = read(abspath('mysite/settings.py'))
ok('PASSWORD_RESET_TIMEOUT = 259200' in st,
   'the three-day expiry is written down, not inherited from a Django default')
for v in VALIDATORS:
    ok(v in st, '  %s is configured' % v)

# ==========================================================================
head('4. THE TOKEN, DRIVEN FOR REAL')
# ==========================================================================
# pages/password_reset.py imports django.contrib.auth and NOTHING from
# pages.models, which is the whole reason it is its own module: it can be
# driven here against a real sqlite database. The project's settings point
# at MySQL, which no suite can reach.
django_up = False
try:
    import django
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        # SE-1 - a test run signs with its own throwaway key. SECRET_KEY
        # reads the environment now, and a suite that boots Django must
        # not fall over because a .env is absent. setdefault, so a real
        # key always wins; this one signs nothing that leaves the test.
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    # SQLITE, IN MEMORY, AFTER setup(). The handler caches both its
    # settings and its wrappers, so all three have to be dropped or the
    # first query still goes to MySQL - which is exactly what happened the
    # first time this was tried.
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    # THE REAL ROOT URLconf, since E-2c, 6 Oct 2026. This read 'pages.urls'
    # because the sandbox mirror did not carry crs/forms.py, so
    # importing mysite.urls died on it - a gap in the mirror, not a
    # fact about the product; the laptop has always had the file.
    # Measured both ways before the line moved: under pages.urls
    # /crs/ answers 404 and crs:index does not reverse at all, so a
    # suite resolving against it is blind to every URL the project
    # mounts outside that one include.               [E-2c]
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + ['testserver']
    # MD5 only here, and only to keep 20-odd set_password calls fast. It
    # changes nothing about what is being tested: a validator refuses a
    # password before any hasher sees it.
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    _quiet = _io.StringIO()
    call_command('migrate', run_syncdb=True, verbosity=0, stdout=_quiet)
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    from django.contrib.auth.models import User, Permission
    from django.contrib.auth.tokens import default_token_generator as gen
    from django.contrib.contenttypes.models import ContentType
    from django.test import Client
    import pages.email_utils as email_utils
    from pages import password_reset as pwr

    ok(True, 'every migration applied to a fresh database - including 0096, '
             'the one this round adds')

    u = User.objects.create_user('probe_bob', 'bob@example.test',
                                 'OldPass!2026x')
    # THE INSTANT THE TOKEN WAS MADE - TC-1, 3 Oct 2026, and the whole
    # of the repair below. Captured once, here, because it is the only
    # instant the three-day arithmetic is about.
    t_made = gen._now()
    tok = gen.make_token(u)
    ok(pwr.token_ok(u, tok), 'a fresh token checks out')
    ok(pwr.user_from_uid(pwr.uid_of(u)) == u,
       'the uid in a link round-trips to the right user')

    # THE CLOCK IS OURS. Alive at three days, dead at four - which is the
    # decision ("3 days is fine") proved rather than asserted.
    #
    # ANCHORED ON THE TOKEN, NOT ON NOW - TC-1, 3 Oct 2026. This used to
    # read `real_now() + timedelta(days=d)`, with real_now() called at
    # CHECK time, so what check_token measured was
    #
    #     3 days + (the time between make_token and this check)
    #
    # and Django's token stores whole seconds. Run alone that gap is a
    # few milliseconds and truncates to zero, so the sum is exactly
    # 259 200 and the timeout lets it through. Run in a six-way parallel
    # sweep it crosses a second - 259 201, one past the boundary - and
    # sweep 15 duly reported "after 3 day(s) the link is still good" as
    # a FAIL against a product that had not changed.
    #
    # A fixture that is right about the boundary and wrong about which
    # clock it is reading is the same shape as nine other instruments
    # this week. This one needed a machine under load before it would
    # say so.
    real_now = gen._now
    try:
        for days, want in ((2, True), (3, True), (4, False)):
            gen._now = (lambda d=days: t_made
                        + datetime.timedelta(days=d))
            ok(gen.check_token(u, tok) is want,
               'after %d day(s) the link is %s'
               % (days, 'still good' if want else 'dead'))
    finally:
        gen._now = real_now
    ok(pwr.token_ok(u, tok), '  and the clock was put back')

    # SINGLE USE BY CONSTRUCTION. The token hashes the password hash, so
    # the moment a new password is saved the token that set it is dead -
    # with no used-tokens table to keep in step.
    u.set_password('Zephyr!2026q')
    u.save()
    ok(not pwr.token_ok(u, tok),
       'saving a new password kills the token that set it - single use, with '
       'nothing to keep in step')

    v = User.objects.create_user('probe_eve', 'eve@example.test',
                                 'EvePass!2026x')
    ok(not pwr.token_ok(v, gen.make_token(u)),
       'one user\'s token does not open another user\'s account')
    for junk in ('zzzz', '', '!!!', 'OTk5OTk5OTk5OTk5OTk5OTk5'):
        ok(pwr.user_from_uid(junk) is None,
           'a mangled uid %-26r answers None, not an exception' % junk)
    ok(pwr.token_ok(None, 'anything') is False,
       '  and a None user answers False rather than raising')

# ==========================================================================
head('5. THE WHOLE FLOW, THROUGH THE REAL VIEWS AND THE REAL MIDDLEWARE')
# ==========================================================================
if not django_up:
    skip('the flow', 'Django would not start')
else:
    SENT = []

    def fake_send(subject, html, text, recipients):
        SENT.append({'subject': subject, 'to': list(recipients.get('all') or []),
                     'html': html, 'text': text})
        return True

    # WHY PATCHING pages.email_utils IS ENOUGH. password_reset.py imports
    # send_html_email INSIDE the function, so the name is looked up at call
    # time. That deferred import is there to keep the module light for
    # section 4; making it patchable is a second thing it buys.
    real_send = email_utils.send_html_email
    email_utils.send_html_email = fake_send

    ct = ContentType.objects.get_for_model(User)
    Permission.objects.get_or_create(
        codename='can_access_administration', content_type=ct,
        defaults={'name': 'Can access administration'})
    admin = User.objects.create_superuser('probe_admin', 'admin@example.test',
                                          'AdminPass!2026x')
    boss = Client()
    boss.force_login(admin)

    # ---- 5a THE TWO MESSAGE FINDINGS -----------------------------------
    print('')
    print('  5a  the login screen\'s messages')
    joe = User.objects.create_user('probe_joe', 'joe@example.test',
                                   'JoePass!2026x')
    c = Client()
    r = c.post('/login/', {'username': 'probe_joe', 'password': 'WRONG'},
               follow=True)
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(len(got) == 1 and got[0][0] in ('danger', 'error'),
       'a wrong password shows exactly one RED bar, on the login screen',
       got)
    ok(got and 'incorrect' in got[0][1].lower()
       and 'double-check' in got[0][1].lower(),
       '  and it says what Demetri asked it to say', got)
    r = c.post('/login/', {'username': 'probe_joe',
                           'password': 'JoePass!2026x'}, follow=True)
    ok(bars(r.content.decode('utf-8', 'replace')) == [],
       'a SUCCESSFUL login shows no bar at all - landing on the app is the '
       'confirmation', bars(r.content.decode('utf-8', 'replace')))
    r = c.get('/logout/', follow=True)
    ok(bars(r.content.decode('utf-8', 'replace')) == [],
       'and logging out shows none either')

    # ---- 5b THE CONTROL: THE MIDDLEWARE EXEMPTION ----------------------
    print('')
    print('  5b  the control - what the round looked like before the '
          'middleware line')
    from pages.middleware import ModuleAccessMiddleware
    link = pwr.link_for(fresh(joe), pwr.make_token(joe))
    anon = Client()
    r = anon.get(link)
    ok(r.status_code == 302 and '/set-password/' in (r.get('Location') or ''),
       'as it ships, the emailed link reaches the page (via the redirect '
       'that strips the token from the address bar)',
       '%s %s' % (r.status_code, r.get('Location')))

    # Now take the exemption away, exactly as the file was before A1.
    victim = ModuleAccessMiddleware(lambda req: None)
    saved = list(victim.EXEMPT_URL_PATTERNS)
    try:
        patched = [p for p in ModuleAccessMiddleware(
            lambda req: None).EXEMPT_URL_PATTERNS
            if p not in ('set-password/', 'forgot-password/')]

        class Before(ModuleAccessMiddleware):
            def __init__(self, get_response=None):
                super().__init__(get_response)
                self.EXEMPT_URL_PATTERNS = patched

        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        req = RequestFactory().get(link)
        req.user = AnonymousUser()
        resp = Before(lambda r: None).process_view(
            req, (lambda *a, **k: None), (), {})
        ok(resp is not None and resp.status_code == 302
           and '/login/' in resp['Location'],
           'CONTROL: without the exempt line the SAME link is bounced to the '
           'login page the person cannot use - the round was dead and every '
           'static check passed',
           'got %r' % (resp,))
        ok('set-password/' in saved and 'forgot-password/' in saved,
           '  and the shipped list really does carry both patterns', saved)
        ok(not any(p for p in saved
                   if 'reset-password' in p or 'user-administration' in p),
           '  while user-administration/<id>/reset-password/ is NOT exempt - '
           'the administrator\'s trigger keeps all four decorators')
    finally:
        pass

    # ---- 5c THE SET-PASSWORD PAGE --------------------------------------
    print('')
    print('  5c  the page the link opens')
    anon = Client()
    tok = pwr.make_token(fresh(joe))
    link = pwr.link_for(joe, tok)
    r = anon.get(link)
    parked = r.get('Location') or ''
    ok(r.status_code == 302 and parked.endswith('/set-password/'),
       'the first hit parks the token and redirects, so it leaves the '
       'address bar, the history and any Referer', '%s %s'
       % (r.status_code, parked))
    ok(tok not in parked, '  and the redirect really does not carry it')
    r = anon.get(parked)
    h = r.content.decode('utf-8', 'replace')
    ok(r.status_code == 200 and h.count('name="new_password1"') == 1
       and h.count('name="new_password2"') == 1,
       'the page renders TWO password fields - Demetri: "forced to re-enter '
       'a new password (twice)"',
       '%s %d %d' % (r.status_code, h.count('name="new_password1"'),
                     h.count('name="new_password2"')))

    # THE FOUR VALIDATORS, WHICH NOTHING IN THIS PROJECT RAN BEFORE TODAY.
    for pw, why in (('password', 'too common'),
                    ('12345678', 'entirely numeric'),
                    ('short1!', 'too short'),
                    ('probe_joe', 'too similar to the username')):
        r = anon.post(parked, {'new_password1': pw, 'new_password2': pw})
        got = bars(r.content.decode('utf-8', 'replace'))
        ok(r.status_code == 200 and got,
           'refused %-12r - %s' % (pw, why),
           'status %s, bars %s' % (r.status_code, got))
    r = anon.post(parked, {'new_password1': 'Abc!2026xy',
                           'new_password2': 'Abc!2026zz'})
    ok(bars(r.content.decode('utf-8', 'replace')),
       'refused two that do not match')
    joe.refresh_from_db()
    ok(joe.check_password('JoePass!2026x'),
       '  and after five refusals the password is still the old one')

    r = anon.post(parked, {'new_password1': 'Quartz!Lagoon26',
                           'new_password2': 'Quartz!Lagoon26'}, follow=True)
    h = r.content.decode('utf-8', 'replace')
    ok('PASSWORD SAVED' in h, 'a good password is accepted and confirmed')
    joe.refresh_from_db()
    ok(joe.check_password('Quartz!Lagoon26') and
       not joe.check_password('JoePass!2026x'),
       '  the new password works and the old one does not')
    r = anon.get(link)
    ok(r.status_code == 400 and 'cannot be used' in
       r.content.decode('utf-8', 'replace'),
       'the same link a second time says so, and answers 400 not 404 - the '
       'URL exists, the credential in it does not')
    r = Client().get(parked)
    ok(r.status_code == 400,
       'and the parked URL typed by hand, with no session, is refused too')
    r = Client().post('/login/', {'username': 'probe_joe',
                                  'password': 'Quartz!Lagoon26'}, follow=True)
    ok(r.redirect_chain and r.redirect_chain[-1][0] == '/',
       'Joe can now log in with the password he chose', r.redirect_chain)

    # ---- 5d ADD A USER -------------------------------------------------
    print('')
    print('  5d  adding a user')
    r = boss.post('/user-administration/add/', {
        'username': 'probe_carol', 'email': '', 'first_name': 'Carol',
        'last_name': 'X', 'role': 'user', 'is_active': '1'})
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(any('Email address is required' in t for _, t in got),
       'an empty email is refused - "Email must be required on Add User"',
       got)
    ok(not User.objects.filter(username='probe_carol').exists(),
       '  and nothing was created')
    SENT[:] = []
    r = boss.post('/user-administration/add/', {
        'username': 'probe_carol', 'email': 'carol@example.test',
        'first_name': 'Carol', 'last_name': 'X', 'role': 'user',
        'is_active': '1'}, follow=True)
    carol = User.objects.filter(username='probe_carol').first()
    ok(carol is not None, 'with an email, the account is created')
    ok(carol is not None and not carol.has_usable_password(),
       '  with NO USABLE PASSWORD - the invitation is the only way in')
    ok(len(SENT) == 1 and SENT[0]['to'] == ['carol@example.test'],
       '  and one email went to that address',
       [s['to'] for s in SENT])
    ok(SENT and 'set your password' in SENT[0]['subject'].lower(),
       '  worded as a welcome, not as a reset',
       SENT[0]['subject'] if SENT else None)
    found = re.search(r'/set-password/[\w\-]+/[\w\-]+/', SENT[0]['html'])
    ok(found is not None, '  and it carries a link to this system')
    cc = Client()
    r = cc.post('/login/', {'username': 'probe_carol', 'password': 'anything'},
                follow=True)
    ok(bars(r.content.decode('utf-8', 'replace')),
       '  Carol cannot log in before she uses it')
    r = cc.get(found.group(0))
    r = cc.post(r.get('Location'), {'new_password1': 'Marigold!Fen26',
                                    'new_password2': 'Marigold!Fen26'},
                follow=True)
    ok('PASSWORD SAVED' in r.content.decode('utf-8', 'replace'),
       '  the link from the real email works')
    r = cc.post('/login/', {'username': 'probe_carol',
                            'password': 'Marigold!Fen26'}, follow=True)
    ok(r.redirect_chain and r.redirect_chain[-1][0] == '/',
       '  and then she is in')

    # ---- 5e RESET, FROM THE ADMIN LIST ---------------------------------
    print('')
    print('  5e  Reset Password')
    r = boss.get('/user-administration/%d/reset-password/' % carol.pk)
    ok(r.status_code == 405,
       'a GET is refused 405 - require_POST, innermost, below the auth '
       'decorators', r.status_code)
    r = Client().post('/user-administration/%d/reset-password/' % carol.pk)
    ok(r.status_code in (302, 403) and 'login' in (r.get('Location') or 'x'),
       '  and a logged-out POST is sent to log in, not told the URL exists',
       '%s %s' % (r.status_code, r.get('Location')))
    SENT[:] = []
    before = fresh(carol).password
    r = boss.post('/user-administration/%d/reset-password/' % carol.pk,
                  follow=True)
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(any('emailed to carol@example.test' in t for _, t in got), 'the '
       'administrator is told where it went', got)
    carol.refresh_from_db()
    ok(carol.password == before and carol.check_password('Marigold!Fen26'),
       'A RESET DOES NOT TAKE THE OLD PASSWORD AWAY - so a send that fails '
       'cannot lock anybody out of a system they could reach a minute ago')
    ok(len(SENT) == 2, '  two emails: the link, and the courtesy notice',
       [s['to'] for s in SENT])
    ok(SENT and SENT[0]['to'] == ['carol@example.test'],
       '  the link to the user')
    ok(len(SENT) > 1 and 'carol@example.test' not in SENT[1]['to'],
       '  and the notice NOT to the user it is about', SENT[1]['to']
       if len(SENT) > 1 else None)
    # SUPPRESSED WHEN THE REQUESTER IS THE RECIPIENT - Demetri: "Agreed.
    # Suppress."
    SENT[:] = []
    boss.post('/user-administration/%d/reset-password/' % admin.pk,
              follow=True)
    ok(len(SENT) == 1 and SENT[0]['to'] == ['admin@example.test'],
       'an administrator resetting THEMSELF gets the link and no notice '
       'about it', [s['to'] for s in SENT])
    # AND THE ADMINISTRATOR IS NOT A SPECIAL CASE ANYWHERE ELSE EITHER.
    ok('is_superuser' not in re.sub(r'#.*', '', read(
        abspath('pages/password_reset.py'))),
       'the token module branches on is_superuser nowhere - Demetri asked '
       'whether the admin user is treated exactly the same way, and this is '
       'what "yes" has to mean')
    # NO EMAIL, NO LINK, AND SAID SO.
    nomail = User.objects.create_user('probe_ghost', '', 'GhostPass!2026x')
    SENT[:] = []
    r = boss.post('/user-administration/%d/reset-password/' % nomail.pk,
                  follow=True)
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(not SENT and any('no email address' in t for _, t in got),
       'an account with no address is refused in words, not silently',
       '%s %s' % ([s['to'] for s in SENT], got))

    # ---- 5f A DISABLED ACCOUNT -----------------------------------------
    print('')
    print('  5f  the disabled account - Demetrios\'s case')
    dave = User.objects.create_user('probe_dave', 'dave@example.test',
                                    'DavePass!2026x')
    dave.is_active = False
    dave.save()
    cd = Client()
    r = cd.post('/login/', {'username': 'probe_dave',
                            'password': 'DavePass!2026x'}, follow=True)
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(any('disabled' in t.lower() for _, t in got),
       'the RIGHT password on a disabled account says the account is '
       'disabled, instead of lying about the password', got)
    r = cd.post('/login/', {'username': 'probe_dave', 'password': 'nope'},
                follow=True)
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(got and 'disabled' not in got[0][1].lower(),
       '  and a WRONG password gets the generic sentence - so the message '
       'never answers "does this username exist"', got)
    r = cd.post('/login/', {'username': 'probe_nobody_at_all',
                            'password': 'nope'}, follow=True)
    got2 = bars(r.content.decode('utf-8', 'replace'))
    ok(got2 and got2[0][1] == got[0][1],
       '  a username that does not exist gets THE SAME SENTENCE, character '
       'for character', '%r vs %r' % (got2, got))

    # ---- 5g EDIT ACCEPTS NO PASSWORD -----------------------------------
    print('')
    print('  5g  the edit screen')
    r = boss.post('/user-administration/%d/edit/' % carol.pk, {
        'first_name': 'Carol', 'last_name': 'X',
        'email': 'carol@example.test', 'role': 'user', 'is_active': '1',
        'password1': 'Smuggled!2026x', 'password2': 'Smuggled!2026x'},
        follow=True)
    carol.refresh_from_db()
    ok(not carol.check_password('Smuggled!2026x'),
       'a password posted to user_edit anyway is IGNORED - the field is gone '
       'from the form and from the view, not just from the form')
    r = boss.post('/user-administration/%d/edit/' % carol.pk, {
        'first_name': 'Carol', 'last_name': 'X', 'email': '',
        'role': 'user', 'is_active': '1'})
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(any('Email address is required' in t for _, t in got),
       'and an edit cannot CLEAR the address, which would take away the '
       'account\'s only route in', got)

    # ---- 5h FORGOT PASSWORD --------------------------------------------
    print('')
    print('  5h  Forgot password')
    SENT[:] = []
    r = Client().post('/forgot-password/',
                      {'email': 'nobody@nowhere.test'}, follow=True)
    unknown = bars(r.content.decode('utf-8', 'replace'))
    ok(not SENT, 'an address nobody has sends nothing')
    SENT[:] = []
    r = Client().post('/forgot-password/',
                      {'email': 'CAROL@EXAMPLE.TEST'}, follow=True)
    known = bars(r.content.decode('utf-8', 'replace'))
    ok(SENT and SENT[0]['to'] == ['carol@example.test'],
       'a real address sends the link - and matching is case-insensitive',
       [s['to'] for s in SENT])
    ok(known and unknown and known[0][1] == unknown[0][1],
       'THE SAME SENTENCE EITHER WAY, character for character - otherwise '
       'this page is an address checker', '%r vs %r' % (known, unknown))
    SENT[:] = []
    r = Client().post('/forgot-password/',
                      {'email': 'dave@example.test'}, follow=True)
    ok(not SENT, 'a DISABLED account is sent nothing - the link would end at '
                 'a page telling them the account is disabled')

    email_utils.send_html_email = real_send

# ==========================================================================
head('6. THE SET-PASSWORD PAGE ON A PHONE')
# ==========================================================================
# RENDERED BY DJANGO, not by a fixture. P5's lesson one round ago: a
# fixture resolves {% if %} by hand, which picks a branch, and the suite
# then reports one branch as the page. Letting Django render it removes the
# whole class of error - and this page has three branches (valid, invalid,
# and the no-messages case).
try:
    from playwright.sync_api import sync_playwright
    have_pw = True
except Exception:
    have_pw = False

if not (django_up and have_pw and os.path.isfile(BOOTP)):
    skip('the page in a browser',
         'Django, playwright or %s is absent' % BOOT)
else:
    # Font Awesome is not in the fixture, so an <i> has no size and every
    # button collapses to its padding. P3 measured a button "smaller" for
    # exactly that reason and the answer was wrong. A 14px stand-in.
    GLYPH = ('.fa, .fas, .far { display:inline-block; width:14px; '
             'height:14px; }')
    anon2 = Client()
    jim = User.objects.create_user('probe_jim', 'jim@example.test',
                                   'JimPass!2026x')
    r = anon2.get(pwr.link_for(jim, pwr.make_token(fresh(jim))))
    page_html = anon2.get(r['Location']).content.decode('utf-8', 'replace')
    page_html = page_html.replace(
        '</head>', '<style>%s</style><style>%s</style></head>'
        % (read(BOOTP), GLYPH))
    probe = os.path.join(SCRATCH, 'pwset.html')
    with open(probe, 'w', encoding='utf-8') as fh:
        fh.write(page_html)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            for w in WIDTHS:
                cx = br.new_context(viewport={'width': w, 'height': 760})
                cx.route(re.compile(r'^https?://'), lambda rt: rt.abort())
                pg = cx.new_page()
                _goto(pg, probe)
                over = pg.evaluate(
                    'Math.max(0, document.documentElement.scrollWidth - '
                    'document.documentElement.clientWidth)')
                boxes = pg.eval_on_selector_all(
                    '#new_password1, #new_password2, button[type=submit]',
                    'es => es.map(e => [Math.round('
                    'e.getBoundingClientRect().width), Math.round('
                    'e.getBoundingClientRect().height)])')
                ok(over == 0, '%dpx  no sideways scrolling' % w,
                   '%dpx of overflow' % over)
                ok(len(boxes) == 3 and all(b[1] >= 38 for b in boxes),
                   '%dpx    both fields and the button clear the 38px tap '
                   'target' % w, boxes)
                print('       %dpx  %s' % (w, boxes))
                cx.close()
            br.close()
    except Exception as e:
        _probe_failed(probe, e)
        skip('the page in a browser', 'the browser could not run')

# ==========================================================================
head('7. THE SECOND SMTP BLOCK HAS NOT DRIFTED FROM THE FIRST')
# ==========================================================================
# send_html_email() is a SECOND copy of the SMTP dance in
# send_issue_comments_email(). Rewriting that one to call this one is the
# obvious tidy and was deliberately not done in this round - it is what the
# daily cron and Notify Urgent use. A copy nobody is watching drifts; this
# one is watched.
eu = read(abspath('pages/email_utils.py'))
blocks = {}
for name in ('send_html_email', 'send_issue_comments_email'):
    i = eu.find('def %s(' % name)
    if i < 0:
        continue
    j = eu.find('\ndef ', i + 1)
    blocks[name] = eu[i:j if j > 0 else len(eu)]
ok(len(blocks) == 2, 'both senders are in the file', sorted(blocks))
if len(blocks) == 2:
    for var, default in (("EMAIL_HOST", "'smtp.gmail.com'"),
                         ("EMAIL_PORT", "465"),
                         ("EMAIL_USER", "'demetrimanias@gmail.com'"),
                         ("EMAIL_USE_SSL", "'True'"),
                         ("EMAIL_USE_TLS", "'False'")):
        both = all(("'%s', %s" % (var, default)) in b
                   or ("'%s')" % var) in b for b in blocks.values())
        ok(both, '  %-14s reads the same name with the same default in both'
           % var)
    ok(all('EMAIL_PASSWORD' in b and 'return False' in b
           for b in blocks.values()),
       '  and both refuse to try without EMAIL_PASSWORD, returning False')
    ok("MIMEText(text_body, 'plain'" in blocks['send_html_email']
       and blocks['send_html_email'].index("'plain'")
       < blocks['send_html_email'].index("'html'"),
       '  text is attached BEFORE html - multipart/alternative shows the '
       'LAST part it understands, so the other order shows everybody the '
       'plain text')
    ok('send_mail' not in eu,
       'and Django\'s send_mail appears nowhere - this project authenticates '
       'SMTP itself, so send_mail would report success and deliver nothing')

# ==========================================================================
head('8. THE 16TH NOTIFICATION TYPE IS IN ALL THREE PLACES')
# ==========================================================================
# Adding a choice to the model is HALF a change. notification_settings()
# filters the choices through a hardcoded admin_types list, and a type
# missing from it renders on no screen and reports no error.
TYPE = 'password_reset_requested'
mod = read(abspath('pages/models.py'))
nots = read(abspath('pages/views/notifications.py'))
mig = read(abspath('pages/migrations/'
                   '0096_notification_type_password_reset.py'))
ok(TYPE in mod, 'it is in NotificationRecipient.NOTIFICATION_TYPES')
ok(TYPE in nots, 'it is in notification_settings()\'s admin_types list - the '
                 'half that is easy to forget')
ok(TYPE in mig, 'it is in migration 0096')
ok(TYPE not in re.search(r'PERSONAL_NOTIFICATION_TYPES = frozenset\(\{[^}]*\}',
                         mod, re.S).group(0),
   'and NOT in PERSONAL_NOTIFICATION_TYPES - it is a global admin notice, '
   'not a workspace-scoped one')
if django_up:
    from pages.models import NotificationRecipient as NR
    codes = [c for c, _ in NR.NOTIFICATION_TYPES]
    ok(TYPE in codes and len(codes) == 16,
       'the model really offers 16 types, with this one among them',
       '%d: %s' % (len(codes), codes[-2:]))
    ok(len(set(codes)) == len(codes), '  and no code appears twice')
    # ONLY the choices list. The first version of this read the whole
    # file and matched ('pages', '0095_none_columns') out of dependencies,
    # then reported the migration as having a type the model did not.
    choice_block = mig[mig.index('choices=['):mig.index('max_length=50')]
    mig_codes = re.findall(r"\('([a-z_]+)', '", choice_block)
    ok(set(mig_codes) == set(codes),
       '  and the migration lists exactly the same set as the model, so '
       'makemigrations will not find a change nobody made',
       'model-only %s | migration-only %s'
       % (sorted(set(codes) - set(mig_codes)),
          sorted(set(mig_codes) - set(codes))))

# ==========================================================================
head('9. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)

print('')
print('  ON THE RECORD, FOR THE NEXT ROUND:')
print('  * send_issue_comments_email() still carries its own copy of the')
print('    SMTP block. Section 7 watches the two for drift; migrating it')
print('    onto send_html_email() is a follow-up, kept out of this round')
print('    because it is the daily cron\'s path.')
print('  * Demetrios is a SUPERUSER with ACTIVE=NO who has never logged in.')
print('    A reset will not let that account in - the login screen now says')
print('    the account is disabled instead of lying about the password, but')
print('    whether the account should exist at all is still unanswered.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
