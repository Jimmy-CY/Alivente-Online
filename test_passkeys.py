# -*- coding: utf-8 -*-
"""test_passkeys.py - round PK-1, 30 Oct 2026.

RELEASE 43 - SIGN IN WITH A FINGERPRINT (PASSKEYS). His decision of 30
October: "Let's go with the passkeys. Let's keep the one hour login for
the main app as it is."

    - A "Sign in with fingerprint" button on the login page, shown only
      where the browser can do it. The password form is untouched.
    - My Profile lists your passkeys, adds one on the device you are on,
      and removes one.
    - The server keeps only the public half of each key. A disabled
      account cannot sign in with one. A challenge is used once and dies
      after five minutes.
    - webauthn 2.4.0 with pyOpenSSL 24.3.0 and cbor2 5.6.5: the versions
      that sit with cryptography 44.0.0, which pyHanko keeps.

THE AUTHENTICATOR IN SECTION 4 IS A REAL ONE, IN SOFTWARE. It makes a P-256
key pair, builds the attestation and the signed assertion byte for byte
as a phone does, and the server verifies them with the same library it
uses for a real fingerprint. Nothing is mocked on the server side.
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

import base64
import hashlib
import json
import os
import re
import struct
import sys
import time

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_passkeys'
ME = 'test_passkeys.py'
PATCHER = 'apply_passkeys.py'
PS1 = 'Push-PendingChanges.ps1'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
LOGIN = J(TPL, 'login.html')
PROFILE = J(TPL, 'my_profile.html')
REQS = J(ROOT, 'mysite', 'cron-requirements.txt')
EDITED = [J(ROOT, 'mysite', 'settings.py'), J(ROOT, 'mysite', 'urls.py'),
          REQS, LOGIN, PROFILE, J(ROOT, 'pages', 'views', 'administration.py')]
APP = ['__init__.py', 'apps.py', 'models.py', 'views.py', 'urls.py',
       J('migrations', '__init__.py'), J('migrations', '0001_initial.py'),
       J('migrations', '0002_credential_id_255.py')]

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
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402
code_only = T.code_only

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
missing = [f for f in APP if not os.path.isfile(J(ROOT, 'passkeys', f))]
ok(not missing, 'the passkeys app is all there', ', '.join(missing))
ok(not os.path.isdir(J(ROOT, 'passkeys', 'templates')),
   '  with no templates of its own - the tree does not grow')
s = read(J(ROOT, 'mysite', 'settings.py'))
ok(re.search(r'INSTALLED_APPS\s*=\s*\[[^\]]*"passkeys"', s, re.S),
   'it is an installed app')
ok("path('', include('passkeys.urls'))" in read(J(ROOT, 'mysite',
                                                  'urls.py')),
   '  and its urls are mounted')
u = read(J(ROOT, 'passkeys', 'urls.py'))
ok(all(p in u for p in ("'login/passkey/begin/'", "'login/passkey/finish/'",
                        "'my-profile/passkeys/add/begin/'",
                        "'my-profile/passkeys/add/finish/'",
                        "'my-profile/passkeys/<int:pk>/remove/'")),
   'sign-in under login/ (public, like the password), the rest under '
   'my-profile/ (login only) - the middleware needs no new rule')
r = read(REQS)
for pin in ('webauthn==2.4.0', 'pyOpenSSL==24.3.0', 'cbor2==5.6.5'):
    ok(re.search(r'^%s$' % re.escape(pin), r, re.M), 'Railway installs %s'
       % pin)
ok(re.search(r'^cryptography==44\.0\.0$', r, re.M)
   and re.search(r'^pyHanko==0\.30\.0$', r, re.M),
   "  and pyHanko's cryptography pin is where it was")
lg = code_only(read(LOGIN))
ok('id="passkeyLogin" hidden' in lg and 'Sign in with fingerprint' in lg,
   'the login page has the fingerprint button, hidden until the browser '
   'can do it')
ok('window.PublicKeyCredential' in lg and 'btn.hidden = false' in lg,
   '  and the script that shows it only then')
ok('name="password"' in lg and 'class="btn action-primary">Login</button>'
   in lg, '  the password form is untouched')
ok('class="btn action-secondary" id="passkeyLogin"' in lg,
   '  a house secondary button, in house order')
pf = code_only(read(PROFILE))
ok('id="passkeys"' in pf and "{% url 'passkey_remove' k.pk %}" in pf,
   'My Profile lists the passkeys, each with Remove')
ok(pf.index('id="passkeys"') > pf.index('</form>'),
   '  outside the profile form - a form cannot sit inside another')
ok('id="passkeyAdd" hidden' in pf, '  and adds one on this device')
ok(not re.search(r'#[0-9a-fA-F]{3,8}\b', re.sub(r'href="#[^"]*"', '',
                                                pf[pf.index('.passkey-row'):
                                                   pf.index('.passkey-row')
                                                   + 400])),
   'its rows use house colours, no new literal')
ok('passkeys' not in was(PROFILE), 'CONTROL: before this round My Profile '
   'had no passkeys')

# ==========================================================================
head('2. THE RULES (no database)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from passkeys import views as V                             # noqa: E402
ok(V.CHALLENGE_TTL == 300, 'a challenge lives five minutes')
from passkeys.models import Passkey as _P                   # noqa: E402
ok(_P._meta.get_field('credential_id').max_length == 255,
   'the id column is 255 - the longest unique column MySQL promises to '
   'index (mysql.W003, seen on his migrate of 30 Oct)')
ok('max_length=255' in read(J(ROOT, 'passkeys', 'migrations',
                              '0002_credential_id_255.py')),
   '  changed by a second migration, so a database that already ran 0001 '
   'follows')
ok('if len(cid) > 255:' in read(J(ROOT, 'passkeys', 'views.py')), '  and an id too long to keep is refused '
   'kindly, not with a database error')
ok(V.user_handle(type('U', (), {'pk': 7})()) == b'alv-7',
   'the handle the phone keeps names the account by number, not name')
src = read(J(ROOT, 'passkeys', 'views.py'))
ok(src.count('require_user_verification=True') == 2,
   'both sign-in and adding demand the fingerprint, not a mere tap')
ok("request.session.pop(key, None)" in src,
   'the challenge is taken out on first use, whatever happens next')
ok('if not pk.user.is_active' in src, 'a disabled account is refused')
ok('login(request, pk.user, backend=BACKEND)' in src,
   "it logs in through django's login(), so everything listening for a "
   'login hears it')

# ==========================================================================
head('3. A SOFTWARE AUTHENTICATOR')
# ==========================================================================
from cryptography.hazmat.primitives import hashes, serialization  # noqa
from cryptography.hazmat.primitives.asymmetric import ec          # noqa
import cbor2                                                      # noqa


def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')


def unb64u(s):
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


class Phone(object):
    """What a phone's passkey store does, in eighty lines."""

    def __init__(self, rp='localhost', origin='http://localhost'):
        self.rp, self.origin = rp, origin
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.cid = os.urandom(32)
        self.count = 0
        self.handle = None

    def cose(self):
        n = self.key.public_key().public_numbers()
        return cbor2.dumps({1: 2, 3: -7, -1: 1,
                            -2: n.x.to_bytes(32, 'big'),
                            -3: n.y.to_bytes(32, 'big')})

    def client_data(self, kind, challenge):
        return json.dumps({'type': kind, 'challenge': challenge,
                           'origin': self.origin,
                           'crossOrigin': False}).encode()

    def create(self, opts):
        self.handle = unb64u(opts['user']['id'])
        cd = self.client_data('webauthn.create', opts['challenge'])
        auth = (hashlib.sha256(self.rp.encode()).digest()
                + bytes([0x45])                     # UP | UV | AT
                + struct.pack('>I', self.count)
                + b'\x00' * 16                      # aaguid
                + struct.pack('>H', len(self.cid)) + self.cid
                + self.cose())
        att = cbor2.dumps({'fmt': 'none', 'attStmt': {}, 'authData': auth})
        return {'id': b64u(self.cid), 'rawId': b64u(self.cid),
                'type': 'public-key',
                'response': {'clientDataJSON': b64u(cd),
                             'attestationObject': b64u(att),
                             'transports': ['internal']},
                'clientExtensionResults': {}}

    def get(self, opts, flags=0x05):
        self.count += 1
        cd = self.client_data('webauthn.get', opts['challenge'])
        auth = (hashlib.sha256(self.rp.encode()).digest() + bytes([flags])
                + struct.pack('>I', self.count))
        sig = self.key.sign(auth + hashlib.sha256(cd).digest(),
                            ec.ECDSA(hashes.SHA256()))
        return {'id': b64u(self.cid), 'rawId': b64u(self.cid),
                'type': 'public-key',
                'response': {'clientDataJSON': b64u(cd),
                             'authenticatorData': b64u(auth),
                             'signature': b64u(sig),
                             'userHandle': b64u(self.handle)},
                'clientExtensionResults': {}}


ok(len(Phone().cose()) > 70, 'the phone makes a P-256 public key')

# ==========================================================================
head('4. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User
    from passkeys.models import Passkey
    connection.ensure_connection()
    Passkey.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 4', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])


# NO PERIODIC CLEANUP WHILE THIS SUITE DRIVES THE APP. The site's
# DatabaseConnectionMiddleware closes every connection each
# DB_FORCE_CLEANUP_INTERVAL requests (25). This suite makes more than that
# inside one rolled-back transaction, and a close in the middle of it ends
# the transaction under the suite's feet. Set before the first request,
# because the middleware reads it once, when it is built.
from django.conf import settings as _dj                     # noqa: E402
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


def post(c, url, **data):
    r = c.post(url, data)
    try:
        return r.status_code, json.loads(r.content.decode() or '{}')
    except ValueError:
        return r.status_code, {}


if have_db:
    try:
        with transaction.atomic():
            a = User.objects.create_user('pk1_a', 'a@example.com', 'x',
                                         first_name='Demetri')
            b = User.objects.create_user('pk1_b', 'b@example.com', 'x')
            PH = 'Mozilla/5.0 (Linux; Android 15; SM-S936B) Mobile'
            ca = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PH)
            ca.force_login(a)
            phone = Phone()

            code, opts = post(ca, '/my-profile/passkeys/add/begin/')
            ok(code == 200 and opts.get('rp', {}).get('id') == 'localhost',
               'adding a passkey: the server asks for one for this site')
            ok(opts.get('authenticatorSelection', {}).get('residentKey')
               == 'required',
               '  one the phone keeps, so sign-in needs no username')
            code, res = post(ca, '/my-profile/passkeys/add/finish/',
                             credential=json.dumps(phone.create(opts)))
            ok(code == 200 and res.get('ok'), '  and the phone\'s answer is '
               'verified and saved', res)
            k = Passkey.objects.filter(user=a).first()
            ok(k and k.name == 'Android phone',
               '  named for where it was made', k and k.name)
            code, res = post(ca, '/my-profile/passkeys/add/finish/',
                             credential=json.dumps(phone.create(opts)))
            ok(code == 400, 'CONTROL: the same challenge cannot be used '
               'twice', code)
            t = ca.get('/my-profile/').content.decode()
            ok('Android phone' in t and 'passkey_remove' not in t
               and '/my-profile/passkeys/%d/remove/' % k.pk in t,
               'My Profile lists it with its Remove button')

            anon = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PH)
            code, o = post(anon, '/login/passkey/begin/')
            ok(code == 200 and o.get('userVerification') == 'required',
               'signing in: anyone may ask for a challenge (the login page '
               'is public)')
            code, res = post(anon, '/login/passkey/finish/',
                             credential=json.dumps(phone.get(o)),
                             next='/wellness/')
            ok(code == 200 and res.get('redirect') == '/wellness/',
               '  the fingerprint\'s signature logs them in, and ?next= is '
               'kept', res)
            ok(anon.get('/my-profile/').status_code == 200,
               '  and they really are logged in')
            ok('wl_main_until' in anon.session,
               '  through login(): the Wellness hour was stamped too')
            k.refresh_from_db()
            ok(k.sign_count == 1 and k.last_used_at,
               '  the key\'s counter and "last used" move')

            evil = Client(SERVER_NAME='localhost')
            code, o = post(evil, '/login/passkey/begin/')
            bad = phone.get(o)
            bad['response']['signature'] = b64u(b'\x30\x06\x02\x01\x01'
                                                b'\x02\x01\x01')
            code, res = post(evil, '/login/passkey/finish/',
                             credential=json.dumps(bad))
            ok(code == 400 and '_auth_user_id' not in evil.session,
               'CONTROL: a forged signature does not log anybody in')
            code, o = post(evil, '/login/passkey/begin/')
            stranger = Phone()
            stranger.handle = b'alv-%d' % a.pk
            code, res = post(evil, '/login/passkey/finish/',
                             credential=json.dumps(stranger.get(o)))
            ok(code == 400, 'CONTROL: nor does a key the server never saw')
            code, o = post(evil, '/login/passkey/begin/')
            code, res = post(evil, '/login/passkey/finish/',
                             credential=json.dumps(phone.get(o, flags=0x01)))
            ok(code == 400, 'CONTROL: nor a tap without the fingerprint '
               '(user not verified)')
            code, o = post(evil, '/login/passkey/begin/')
            s2 = evil.session
            s2[V.AUTH]['t'] = int(time.time()) - 301
            s2.save()
            code, res = post(evil, '/login/passkey/finish/',
                             credential=json.dumps(phone.get(o)))
            ok(code == 400, 'CONTROL: nor a challenge older than five '
               'minutes')
            a.is_active = False
            a.save()
            code, o = post(evil, '/login/passkey/begin/')
            code, res = post(evil, '/login/passkey/finish/',
                             credential=json.dumps(phone.get(o)))
            ok(code == 403 and '_auth_user_id' not in evil.session,
               'a disabled account cannot sign in with a passkey either')
            a.is_active = True
            a.save()

            cb = Client(SERVER_NAME='localhost')
            cb.force_login(b)
            r = cb.post('/my-profile/passkeys/%d/remove/' % k.pk)
            ok(r.status_code == 404 and Passkey.objects.filter(pk=k.pk)
               .exists(), "nobody can remove somebody else's passkey")
            ok('Android phone' not in cb.get('/my-profile/').content
               .decode(), '  or see it on their own profile')
            r = ca.post('/my-profile/passkeys/%d/remove/' % k.pk)
            ok(r.status_code == 302 and not Passkey.objects.filter(
                pk=k.pk).exists(), 'Remove takes your own one away')
            code, o = post(evil, '/login/passkey/begin/')
            code, res = post(evil, '/login/passkey/finish/',
                             credential=json.dumps(phone.get(o)))
            ok(code == 400, '  after which it cannot sign in')
            r = anon.get('/login/passkey/begin/')
            ok(r.status_code == 405, 'every endpoint is POST only')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'id=\"passkeyLogin\"'" in gate, '  with a sentinel on the button')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, 'every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
