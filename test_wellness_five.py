# -*- coding: utf-8 -*-
"""test_wellness_five.py - round WL-4b, 30 Oct 2026.

RELEASE 48 - WELLNESS W-4b: PHONE REMINDERS (web push), and the ? kept top
right. From decision 3 of 30 Oct and Demetri's notes:

    - A phone gets reminders only after the person turns them on there and
      the phone asks and they allow it.
    - A habit can have a reminder time; the evening check-in and the
      weigh-in can too. Nothing is sent once the thing is done, and each
      reminder goes at most once a day, within two hours of its time.
    - The cycle tracker's reminder says only "A Wellness reminder".
    - The two push keys are Railway variables he generates; without them
      nothing is sent and nothing breaks.
    - The ? stays top right in the installed app (14:06).
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
import datetime as dt
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_wellness5'
ME = 'test_wellness_five.py'
PATCHER = 'apply_wellness_five.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
REQ = J(ROOT, 'mysite', 'cron-requirements.txt')
NEW_FILES = ['push.py', 'reminders.py', J('migrations', '0007_reminders.py'),
             J('management', 'commands', 'wellness_reminders.py')]
EDITED = [J(APP, 'models.py'), J(APP, 'views.py'), J(APP, 'urls.py'),
          J(APP, 'guide.py'), J(APP, 'assets', 'wellness.css'),
          J(APP, 'assets', 'wellness.js'), J(WT, 'base.html'),
          J(WT, 'settings.html'), J(WT, 'habit_form.html'), REQ]

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
import ast                                                  # noqa: E402


def py_words(src):
    """Every name, attribute, import and string a Python file USES -
    docstrings and comments left out, so a file may explain what it never
    touches."""
    tree = ast.parse(src)
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and \
                n.body and isinstance(n.body[0], ast.Expr) and \
                isinstance(getattr(n.body[0], 'value', None), ast.Constant):
            docs.add(id(n.body[0].value))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.append(n.id)
        elif isinstance(n, ast.Attribute):
            out.append(n.attr)
        elif isinstance(n, ast.alias):
            out.append(n.name)
        elif isinstance(n, ast.ImportFrom):
            out.append(n.module or '')
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and \
                id(n) not in docs:
            out.append(n.value)
    return ' '.join(out).lower()

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
missing = [f for f in NEW_FILES if not os.path.isfile(J(APP, f))]
ok(not missing, 'the reminder files are all there (%d)' % len(NEW_FILES),
   ', '.join(missing))
req = read(REQ)
ok('pywebpush==2.3.0' in req and 'py-vapid==1.9.2' in req and
   'aiohttp==3.12.15' in req, 'Railway installs pywebpush and its family')
ok('cryptography==44.0.0' in req, "  and pyHanko's cryptography pin is "
   'where it was')
models = read(J(APP, 'models.py'))
cls = models[models.index('class PushDevice'):]
ok('endpoint_hash = models.CharField(max_length=64, unique=True)' in cls
   and 'endpoint = models.TextField()' in cls,
   'a phone is unique by the hash of its address - MySQL indexes 255 at '
   'most')
ok('remind_at = models.TimeField(null=True, blank=True)' in models,
   'a habit may have a reminder time, empty by default')
mig = read(J(APP, 'migrations', '0007_reminders.py'))
ok('0006_profile_prefs' in mig and 'PushDevice' in mig and
   'remind_at' in mig, 'migration 0007, after the badges')
push = read(J(APP, 'push.py'))
ok("'WELLNESS_VAPID_PUBLIC'" in push and "'WELLNESS_VAPID_PRIVATE'" in push
   and 'BEGIN' not in push, 'the keys come from two Railway variables, '
   'none written here')
ok('Vapid02' in push, '  signed the standard way (RFC 8292), which Apple '
   'requires')
ok('GONE = (404, 410)' in push and 'device.delete()' in push,
   'a phone that is gone is forgotten the first time it says so')
rm = read(J(APP, 'reminders.py'))
ok("CYCLE_WORDS = 'A Wellness reminder'" in rm and
   'period' not in py_words(rm),
   'the cycle reminder says only "A Wellness reminder" - never period')
ok("LATE = dt.timedelta(hours=2)" in rm and 'sent_today' in rm,
   'at most once a day, never more than two hours late')
ok('journal' not in py_words(rm).replace('journalentry', '')
   .replace('/wellness/journal/new/', ''),
   '  and no reminder carries a word of the journal')
views = read(J(APP, 'views.py'))
sw = views[views.index('def service_worker'):views.index('def asset(')]
ok("addEventListener('push'" in sw and
   "addEventListener('notificationclick'" in sw,
   'the app worker shows a reminder and opens Wellness when it is tapped')
ok("d.url.indexOf('/wellness/') === 0" in sw,
   '  only ever a Wellness page')
ok('def push_subscribe' in views and views.count('@require_POST\ndef push_')
   == 3, 'subscribe, stop and test are POST only')
js = read(J(APP, 'assets', 'wellness.js'))
ok('Notification.requestPermission()' in js and
   'applicationServerKey' in js, 'the phone asks the person before '
   'anything is sent')
css = read(J(APP, 'assets', 'wellness.css'))
ok('.w-top > .w-icon-btn:last-child { margin-left: auto; }' in css,
   'THE ? STAYS TOP RIGHT in the installed app (Demetri, 14:06)')
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
# Later rounds move the version on (WL-4c: wl6-1); what must hold is that
# the page and the service worker always name the same one.
ok(len(_v) == 2 and len(set(_v)) == 1 and "SW_VERSION = '%s'" % _v[0]
   in views, 'the asset version moved together (wl5-1): phones fetch the '
   'new worker', _v)
ok('name="remind_at"' in read(J(WT, 'habit_form.html')),
   'the habit form has a reminder time')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('class PushDevice' not in was(J(APP, 'models.py')),
   'CONTROL: before this round no phone could be reminded')
ok('.w-icon-btn:last-child' not in was(J(APP, 'assets', 'wellness.css')),
   'CONTROL: and the ? was free to slide left')

# ==========================================================================
head('2. THE RULES (no database)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.utils import timezone                           # noqa: E402
from wellness import push as P                              # noqa: E402
from wellness import reminders as R                         # noqa: E402
tz = timezone.get_current_timezone()
now = dt.datetime(2026, 11, 2, 7, 40, tzinfo=tz)
items = [{'key': 'habit:1', 'at': dt.time(7, 30)},
         {'key': 'habit:2', 'at': dt.time(8, 0)},
         {'key': 'weigh', 'at': dt.time(5, 0)},
         {'key': 'checkin', 'at': dt.time(7, 0)}]
ok([i['key'] for i in R.due(now, items, set())] == ['habit:1', 'checkin'],
   'due now: 07:30 and 07:00 at 07:40; not 08:00 yet; not 05:00 (too late)')
ok([i['key'] for i in R.due(now, items, {'habit:1'})] == ['checkin'],
   '  and nothing twice in a day')
ok(R._hm('21:30') == dt.time(21, 30) and R._hm('') is None and
   R._hm('xx') is None, 'times read kindly; a bad one is none')
_save = dict(os.environ)
for k in (P.PUBLIC, P.PRIVATE):
    os.environ.pop(k, None)
ok(not P.configured(), 'without the two keys reminders are off')
from cryptography.hazmat.primitives.asymmetric import ec   # noqa: E402
from cryptography.hazmat.primitives import serialization as SER  # noqa
_b = lambda x: base64.urlsafe_b64encode(x).rstrip(b'=').decode()  # noqa
_k = ec.generate_private_key(ec.SECP256R1())
os.environ[P.PRIVATE] = _b(_k.private_numbers().private_value
                           .to_bytes(32, 'big'))
os.environ[P.PUBLIC] = _b(_k.public_key().public_bytes(
    SER.Encoding.X962, SER.PublicFormat.UncompressedPoint))
ok(P.configured() and P.looks_like_key(P.public_key()),
   'with them, on - and the public key is a real P-256 point')
ok(P._vapid() is not None, '  and the private key signs')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from wellness.models import (Habit, PushDevice, WellnessProfile,
                                 HabitLog)
    connection.ensure_connection()
    PushDevice.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

from django.conf import settings as _dj                     # noqa: E402
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


class _Resp(object):
    def __init__(self, code):
        self.status_code = code
        self.text = ''
        self.reason = 'x'
        self.headers = {}


if have_db:
    import http_ece
    import pywebpush
    sent = []
    _real_post = pywebpush.requests.post

    def _ok(url, data=None, headers=None, timeout=None, **kw):
        sent.append((url, data, headers))
        return _Resp(201)
    try:
        pywebpush.requests.post = _ok
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            a = User.objects.create_user('w5_a', 'w5a@example.com', 'x')
            b = User.objects.create_user('w5_b', 'w5b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            t = ca.get('/wellness/settings/').content.decode()
            ok('Turn on reminders here' in t and 'data-key="%s"'
               % P.raw_key_words(P.public_key()) in t,
               'settings offers reminders, with the public key for the '
               'phone')
            ck = ec.generate_private_key(ec.SECP256R1())
            auth = os.urandom(16)
            sub = {'endpoint': 'https://fcm.googleapis.com/fcm/send/w5test',
                   'keys': {'p256dh': _b(ck.public_key().public_bytes(
                       SER.Encoding.X962, SER.PublicFormat.UncompressedPoint)),
                       'auth': _b(auth)}}
            r = ca.post('/wellness/push/subscribe/',
                        json.dumps({'subscription': sub}),
                        content_type='application/json',
                        HTTP_USER_AGENT='Mozilla (iPhone)')
            dev = PushDevice.objects.filter(user=a).first()
            ok(r.status_code == 200 and dev and dev.label == 'iPhone',
               'a phone that allowed it is kept, named for what it is')
            ok(ca.post('/wellness/push/subscribe/', '{"endpoint": '
                       '"http://evil"}', content_type='application/json')
               .status_code == 400, '  and something that is not a phone '
               'subscription is refused')
            r = ca.post('/wellness/push/test/')
            url, data, headers = sent[-1]
            plain = json.loads(http_ece.decrypt(
                data, private_key=ck, auth_secret=auth,
                version='aes128gcm'))
            ok(url == sub['endpoint'] and headers.get('Content-Encoding')
               == 'aes128gcm' and headers.get('Authorization', '')
               .startswith('vapid t='),
               'a test goes to that phone, encrypted and signed')
            ok(plain['title'] == 'Wellness' and 'Reminders are on' in
               plain['body'], '  and only the phone can read it: "%s"'
               % plain['body'])
            today = timezone.localdate()
            now = timezone.localtime().replace(second=0, microsecond=0)
            h = Habit.objects.create(
                user=a, name='Stretch', started_on=today -
                dt.timedelta(days=10),
                remind_at=(now - dt.timedelta(minutes=10)).time())
            n0 = len(sent)
            ok(R.run(now) == (1, 1) and len(sent) == n0 + 1,
               'a habit due and not done: one reminder at its time')
            body = json.loads(http_ece.decrypt(
                sent[-1][1], private_key=ck, auth_secret=auth,
                version='aes128gcm'))['body']
            ok(body == 'Stretch - whenever you are ready.',
               '  in kind words: "%s"' % body)
            ok(R.run(now) == (0, 1), '  and never twice in a day')
            h2 = Habit.objects.create(
                user=a, name='Walk', started_on=today -
                dt.timedelta(days=10),
                remind_at=(now - dt.timedelta(minutes=5)).time())
            HabitLog.objects.create(habit=h2, date=today, done=True)
            ok(R.run(now)[0] == 0, 'a habit already done today is not '
               'mentioned')
            ok(not PushDevice.objects.filter(user=b).exists() and
               R.items_for(b, now) == [],
               "another member's phone and habits are untouched")
            t = ca.get('/wellness/habits/%d/edit/' % h.pk).content.decode()
            ok('name="remind_at"' in t and 'value="%s"'
               % h.remind_at.strftime('%H:%M') in t,
               'the habit form shows its reminder time')
            ca.post('/wellness/settings/', {'remind_checkin': '21:30',
                                            'remind_weigh': 'nonsense'})
            pa = WellnessProfile.objects.get(user=a)
            ok(pa.prefs.get('remind_checkin') == '21:30' and
               pa.prefs.get('remind_weigh') == '',
               'settings keeps a good time and drops a bad one')

            def _gone(url, data=None, headers=None, timeout=None, **kw):
                return _Resp(410)
            pywebpush.requests.post = _gone
            ok(P.send_to_user(a, 'x', 'y') == 0 and
               not PushDevice.objects.filter(user=a).exists(),
               'a phone the push service says is gone is forgotten')
            raise Rollback
    except Rollback:
        pass
    finally:
        pywebpush.requests.post = _real_post
os.environ.clear()
os.environ.update(_save)

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def due('" in gate, '  with a sentinel on the reminder rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
