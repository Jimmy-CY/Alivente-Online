# -*- coding: utf-8 -*-
"""test_login_email.py - Section A round A3, 1 Oct 2026.

Demetri reset the password on demetri.manias@alivente.com, set it, and
could not log in: that account's USERNAME is `Demetrios`. He reached for
the address because the reset was about the address, and the login screen
asked for something else.

The box now takes either. So does Forgot Password.

SECTION 2 IS THE CONTROL, AND IT IS THE ONE THAT MATTERS. Django's own
ModelBackend is asked to authenticate the EMAIL and must return None. If
it ever stopped doing so, every check below would pass for a reason that
has nothing to do with this round, and the round would be untested while
looking tested.

SECTION 3 IS THE ORDER, which is the whole design:

    1. if it names an account, it IS a username - checked first and
       exactly, so nobody can shadow somebody else's login by choosing
       an email address
    2. no @, no lookup
    3. exactly one match, case-insensitively
    4. TWO MATCHES REFUSE - guessing which account was meant is worse
       than failing

SECTION 5 IS WHAT THE ROUND MUST NOT HAVE DONE. A new way IN must not be
a new way to ask whether an account exists: a wrong email and a wrong
username are compared character for character, and the only conditional
message in the system - the disabled-account one - still appears solely
to somebody who typed the correct password.

AND SECTION 6 IS A BROWSER PROBLEM, NOT A DJANGO ONE. Forgot Password's
field was <input type="email" required>. No browser submits `Demetrios`
from one of those, so the form would never have reached the view and no
amount of work there would have shown.
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
import ast
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
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []

SUFFIX = '.bak_loginemail'
ME = 'test_login_email.py'
PATCHER = 'apply_login_email.py'
PS1 = 'Push-PendingChanges.ps1'
AUTH = os.path.join(ROOT, 'pages', 'views', 'auth.py')

NAME = 'Demetrios'
MAIL = 'demetri.manias@alivente.com'
PASS = 'Zephyr!Lagoon26'

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


def bars(html):
    """The message bars that RENDERED, as (tag, text).

    NOT `'alv-message' in html` - base's own stylesheet and its fade
    script both contain that string, so it is true on every page in the
    system whether a bar rendered or not."""
    return [(m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip())
            for m in re.finditer(
                r'class="alert alert-(\w+)[^"]*alv-message"[^>]*>\s*'
                r'([^<]{3,600})', html)]


# ==========================================================================
head('1. THE TWO FIELDS SAY THEY TAKE EITHER')
# ==========================================================================
login_now = read(alv_tree.path_of('login.html'))
ok('Username or Email' in login_now,
   'the login box is labelled Username or Email')
ok('username or email address' in login_now,
   '  and its placeholder says so too')

forgot_now = read(alv_tree.path_of('password_forgot.html'))
ok('Email Address or Username' in forgot_now,
   'Forgot Password takes either as well')
# THE BROWSER WOULD HAVE BLOCKED IT. type="email" refuses to submit a
# username, so the view would never have seen one.
ok(not re.search(r'<input type="email"[^>]*name="email"', forgot_now),
   '  and its field is NOT type="email", which no browser submits a '
   'username from')
ok(re.search(r'<input type="text"[^>]*name="email"', forgot_now) is not None,
   '  it is type="text"')

for p, label in ((alv_tree.path_of('login.html'), 'login.html'),
                 (alv_tree.path_of('password_forgot.html'),
                  'password_forgot.html')):
    bak = p + SUFFIX
    if not os.path.isfile(bak):
        skip('%-22s the control' % label, 'no backup')
        continue
    was = read(bak)
    ok('or Email' not in was and 'or Username' not in was,
       'CONTROL: %-22s asked for one thing before this round' % label)

# ==========================================================================
head('2. THE CONTROL - DJANGO ITSELF REFUSES THE ADDRESS')
# ==========================================================================
# If ModelBackend ever authenticated an email on its own, every check
# below would pass for a reason that has nothing to do with this round.
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        # SE-1 - a test run signs with its own throwaway key. SECRET_KEY
        # reads the environment now, and a suite that boots Django must
        # not fall over because a .env is absent. setdefault, so a real
        # key always wins; this one signs nothing that leaves the test.
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                                'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'pages.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO())
    from django.test.utils import setup_test_environment
    setup_test_environment()
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    from django.contrib.auth import authenticate
    from django.contrib.auth.models import User
    from django.test import Client
    import pages.email_utils as email_utils
    from pages.views.auth import account_for

    who = User.objects.create_user(NAME, MAIL, PASS)
    User.objects.create_user('lexi', 'leximanias@example.test', 'Lexi!2026qq')

    ok(authenticate(username=MAIL, password=PASS) is None,
       'CONTROL: Django\'s own backend authenticates the EMAIL as nothing - '
       'so the resolution step is provably what makes this round work')
    ok(authenticate(username=NAME, password=PASS) is not None,
       '  while the username works, as it always did')

# ==========================================================================
head('3. THE ORDER account_for RESOLVES IN')
# ==========================================================================
if not django_up:
    skip('the resolution', 'Django would not start')
else:
    ok(account_for(NAME) == NAME,
       'a username comes back unchanged', account_for(NAME))
    ok(account_for(MAIL) == NAME,
       'an address resolves to its username', account_for(MAIL))
    ok(account_for(MAIL.upper()) == NAME,
       '  case-insensitively, the spelling the rest of the system uses',
       account_for(MAIL.upper()))
    ok(account_for('  %s  ' % MAIL) == NAME, '  and it is stripped first')
    for junk in ('nobody@nowhere.test', 'no_such_user', '', '   ', '@'):
        ok(account_for(junk) == junk.strip(),
           'nothing matches %-22r so it passes straight through' % junk,
           account_for(junk))

    # A USERNAME BEATS AN ADDRESS. Somebody whose USERNAME is another
    # person's EMAIL must not be able to intercept their login.
    victim = User.objects.create_user('victim', 'shared@example.test', 'V!26qqx')
    impostor = User.objects.create_user('shared@example.test',
                                        'impostor@example.test', 'I!26qqx')
    ok(account_for('shared@example.test') == 'shared@example.test',
       'a USERNAME that looks like an address wins over the account that '
       'really owns that address', account_for('shared@example.test'))
    ok(authenticate(username=account_for('shared@example.test'),
                    password='I!26qqx') == impostor,
       '  so it reaches the account that is named that, not the one '
       'addressed that')
    impostor.delete()

    # TWO ACCOUNTS, ONE ADDRESS: refuse, do not guess.
    twin = User.objects.create_user('twin', MAIL, 'Twin!2026qq')
    ok(account_for(MAIL) == MAIL,
       'when TWO accounts share an address it refuses - the identifier '
       'falls through unchanged and authenticate() says no',
       account_for(MAIL))
    c = Client()
    r = c.post('/login/', {'username': MAIL, 'password': PASS}, follow=True)
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(not r.redirect_chain or r.redirect_chain[-1][0] != '/',
       '  and a sign-in with it is refused rather than sent to either one',
       r.redirect_chain)
    ok(got and 'incorrect' in got[0][1].lower(),
       '  with the ordinary sentence, saying nothing about why', got)
    twin.delete()
    victim.delete()

# ==========================================================================
head('4. SIGNING IN, FOR REAL, BOTH WAYS')
# ==========================================================================
if not django_up:
    skip('the sign-ins', 'Django would not start')
else:
    for ident, label in ((NAME, 'the username'),
                         (MAIL, 'the email address'),
                         (MAIL.upper(), 'the address in capitals')):
        c = Client()
        r = c.post('/login/', {'username': ident, 'password': PASS},
                   follow=True)
        ok(r.redirect_chain and r.redirect_chain[-1][0] == '/',
           'signs in with %-24s' % label, r.redirect_chain)
        ok(bars(r.content.decode('utf-8', 'replace')) == [],
           '  and shows no message, as A1 settled')

    # THE DISABLED PATH RESOLVES TOO - the case that started all of this.
    who.refresh_from_db()
    who.is_active = False
    who.save()
    c = Client()
    r = c.post('/login/', {'username': MAIL, 'password': PASS}, follow=True)
    got = bars(r.content.decode('utf-8', 'replace'))
    ok(any('disabled' in t.lower() for _g, t in got),
       'a DISABLED account reached BY EMAIL with the right password says it '
       'is disabled - not "credentials are incorrect", which is the dead '
       'end this round exists to remove', got)
    who.is_active = True
    who.save()

# ==========================================================================
head('5. AND NO NEW WAY TO ASK WHETHER AN ACCOUNT EXISTS')
# ==========================================================================
if not django_up:
    skip('the enumeration check', 'Django would not start')
else:
    c = Client()
    r = c.post('/login/', {'username': 'nobody@nowhere.test',
                           'password': 'wrong'}, follow=True)
    by_mail = bars(r.content.decode('utf-8', 'replace'))
    r = c.post('/login/', {'username': 'no_such_user', 'password': 'wrong'},
               follow=True)
    by_name = bars(r.content.decode('utf-8', 'replace'))
    r = c.post('/login/', {'username': MAIL, 'password': 'wrong'},
               follow=True)
    real_mail = bars(r.content.decode('utf-8', 'replace'))
    ok(by_mail and by_mail == by_name == real_mail,
       'an unknown address, an unknown username and a REAL address with the '
       'wrong password all give the same sentence, character for character',
       '%r / %r / %r' % (by_mail, by_name, real_mail))

    src = read(AUTH)
    fn = next((n for n in ast.walk(ast.parse(src))
               if isinstance(n, ast.FunctionDef) and n.name == 'login_user'),
              None)
    body = ast.get_source_segment(src, fn) if fn else ''
    ok(body.count('messages.error') == 2,
       '  and login_user still has exactly the two messages A1 gave it',
       body.count('messages.error'))

# ==========================================================================
head('6. FORGOT PASSWORD TAKES EITHER, AND STILL SENDS ONLY TO THE ACCOUNT')
# ==========================================================================
if not django_up:
    skip('Forgot Password', 'Django would not start')
else:
    SENT = []
    real_send = email_utils.send_html_email

    def fake(subject, html, text, recipients):
        SENT.append(list(recipients.get('all') or []))
        return True

    email_utils.send_html_email = fake
    try:
        for ident, label in ((NAME, 'a username'), (MAIL, 'an address'),
                             (MAIL.upper(), 'an address in capitals')):
            SENT[:] = []
            r = Client().post('/forgot-password/', {'email': ident},
                              follow=True)
            said = bars(r.content.decode('utf-8', 'replace'))
            ok(SENT and MAIL in SENT[0],
               'given %-24s the link goes to the ACCOUNT\'S address'
               % label, SENT)
            ok(said and 'if that email address' in said[0][1].lower(),
               '  and the answer is the same vague sentence as always', said)
        # nothing matches: nothing sent, same sentence
        SENT[:] = []
        r = Client().post('/forgot-password/', {'email': 'ghost@nowhere.test'},
                          follow=True)
        unknown = bars(r.content.decode('utf-8', 'replace'))
        ok(not SENT, 'an identifier nobody has sends nothing')
        SENT[:] = []
        r = Client().post('/forgot-password/', {'email': MAIL}, follow=True)
        known = bars(r.content.decode('utf-8', 'replace'))
        ok(known and unknown and known[0][1] == unknown[0][1],
           '  and says exactly what a real one says - this page is still not '
           'an address checker', '%r vs %r' % (known, unknown))
    finally:
        email_utils.send_html_email = real_send

# ==========================================================================
head('7. THE GATE')
# ==========================================================================
src = read(AUTH)
fn = next((n for n in ast.walk(ast.parse(src))
           if isinstance(n, ast.FunctionDef) and n.name == 'account_for'),
          None)
ok(fn is not None, 'account_for is in views/auth.py')
if fn is not None:
    body = ast.get_source_segment(src, fn)
    i_user = body.find('filter(username=identifier)')
    i_at = body.find("'@' not in identifier")
    i_mail = body.find('email__iexact=identifier')
    ok(-1 < i_user < i_at < i_mail,
       '  and checks the username FIRST, then the @, then the address - an '
       'address that resolved first could shadow a username',
       (i_user, i_at, i_mail))
    ok('[:2]' in body and 'len(found) == 1' in body,
       '  and refuses an ambiguous address rather than taking the first row')

ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
for rel in ('pages/views/auth.py', 'pages/templates/login.html',
            'pages/templates/password_forgot.html'):
    p = (alv_tree.path_of(rel[len('pages/templates/'):])
         if rel.startswith('pages/templates/')
         else os.path.join(ROOT, rel.replace('/', os.sep)))
    ok(os.path.isfile(p + SUFFIX), '%-34s has its backup' % rel)

print('')
print('  WHAT MAKES THIS SAFE, and it was not safe a day ago: A1 made')
print('  email required on both Add User and Edit User and refuses a')
print('  duplicate case-insensitively, so an address identifies exactly')
print('  one account by construction. Show-UserEmails.py measured the')
print('  five existing accounts the same morning - every address unique.')
print('  Section 3 covers the case the data no longer allows anyway.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
