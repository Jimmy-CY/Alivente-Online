# -*- coding: utf-8 -*-
"""test_ra04_key_email.py - round RA04, 19 Nov 2026.

RELEASE RA04 - AN EMAIL WHEN A KEY STOPS WORKING.
Demetri, 19 Nov: "If there is a problem with the key in the future, also
with the Anthropic key, can the system send me an email letting me
know.... instead of just to stop working?" - "The email should go to me
only. Leave the working again email. Let's increase the time to 60
minutes of failing. Just one email daily, covering all keys - and
showing the status of all keys" - "The email, ONLY if their is a problem
on one key". No test here calls Anthropic, Google or a mail server.
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

SUFFIX = '.bak_ra04'
ME = 'test_ra04_key_email.py'
PATCHER = 'apply_ra04_key_email.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

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
import datetime as dt                                       # noqa: E402
import urllib.error                                         # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from pages import key_health as KH                          # noqa: E402
PG = J(ROOT, 'pages')

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
kh = read(J(PG, 'key_health.py'))
ok('FAIL_FOR = dt.timedelta(minutes=60)' in kh and 'EVERY = 15 * 60' in kh,
   'AN HOUR OF FAILING before an email; checked every 15 minutes')
ok("'places.id'" in kh and 'models.list(limit=1)' in kh,
   '  the checks cost nothing: IDs-only Google search, the list of models')
ok('print(' not in kh and 'api_key=key' in kh and
   "os.environ.get('KEY_ALERT_EMAIL')" in kh,
   'NEVER THE KEY: not printed, not emailed; to KEY_ALERT_EMAIL, else the '
   'first superuser')
ap = read(J(PG, 'apps.py'))
ok('key_health.wrap_anthropic()' in ap and 'key_health.start_watcher()' in
   ap and b'\r\n' in open(J(PG, 'apps.py'), 'rb').read(),
   'AT START-UP: every Anthropic call watched; the watcher on Railway '
   '(apps.py keeps its CRLF)')
ok(os.path.isfile(J(PG, 'migrations', '0120_key_status.py')) and
   os.path.isfile(J(PG, 'management', 'commands', 'check_keys.py')),
   'MIGRATION 0120 (the key_status table) and manage.py check_keys')
ok("_health(False, e.code)" in read(J(ROOT, 'travel', 'gplaces.py')),
   'GOOGLE PLACES reports how each call went')
try:
    ok('key_health' not in was(J(PG, 'apps.py')),
       'CONTROL: before this round nothing watched the keys')
except IOError as _e:
    skip('control', str(_e))

# ==========================================================================
head('2. WHAT COUNTS AS A KEY PROBLEM (no network)')
# ==========================================================================


def err(name, status=None, text='x'):
    return type(name, (Exception,), {'status_code': status})(text)


ok(KH.classify_anthropic(err('AuthenticationError', 401))[0] == 'refused',
   'ANTHROPIC 401: the key was refused')
ok(KH.classify_anthropic(err('BadRequestError', 400,
                             'Your credit balance is too low'))[0] ==
   'credit', '  400 "credit balance is too low": out of credit')
ok(KH.classify_anthropic(err('BadRequestError', 400, 'bad tool')) is None,
   '  any other 400 is our mistake, not the key\'s - no email')
ok(KH.classify_anthropic(err('RateLimitError', 429))[0] == 'limit' and
   KH.classify_anthropic(err('InternalServerError', 529))[0] == 'down' and
   KH.classify_anthropic(err('APIConnectionError'))[0] == 'down',
   '  429 over a limit; 529 / no connection: not answering')
ok(KH.classify_google(403)[0] == 'refused' and
   KH.classify_google(429)[0] == 'limit' and
   KH.classify_google(None)[0] == 'down', 'GOOGLE: 403, 429, down')
ok(not KH.start_watcher(), 'NO WATCHER in a test (or off Railway)')
os.environ.pop('GOOGLE_PLACES_KEY', None)
ok(KH.probe_google()[:2] == (False, 'missing'),
   'A KEY NOT SET ON RAILWAY is a problem too')
os.environ['GOOGLE_PLACES_KEY'] = 'fake-key-xyz'


def deny(req, timeout=None):
    raise urllib.error.HTTPError(req.full_url, 403, 'no', {}, None)


class Fine(object):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return b'{}'


ok(KH.probe_google(opener=deny)[:2] == (False, 'refused') and
   KH.probe_google(opener=lambda r, timeout=None: Fine())[0],
   '  a refused Google key, and a working one (no real call)')
seen = []
_rec = KH.record
KH.record = lambda *a, **k: seen.append(a)
from anthropic.resources.messages import Messages           # noqa: E402
_orig = Messages.create


def boom(self, *a, **k):
    raise err('AuthenticationError', 401)


Messages.create = boom
KH.wrap_anthropic()
try:
    Messages.create(None)
except Exception:                                           # noqa: BLE001
    pass
ok(seen and seen[0][:3] == ('anthropic', False, 'refused'),
   'EVERY ANTHROPIC CALL reports: a refused key is noted', seen)
ok(KH.wrap_anthropic() and getattr(Messages.create, '_alv_watched', False),
   '  wrapped once only')
Messages.create = _orig
KH.record = _rec

# ==========================================================================
head('3. THE EMAIL (database; no mail server)')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.utils import timezone
    from pages.models import KeyStatus
    connection.ensure_connection()
    KeyStatus.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

if have_db:
    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            KeyStatus.objects.all().delete()
            os.environ['KEY_ALERT_EMAIL'] = 'demetri@example.com'
            sent = []
            t0 = timezone.now().replace(hour=8, minute=0)
            KH.save('anthropic', True, now=t0)
            KH.save('google_places', False, 'refused', 'Refused.', now=t0)
            ok(not KH.maybe_email(t0 + dt.timedelta(minutes=59),
                                  send=sent.append) and not sent,
               'FAILING 59 MINUTES: no email yet')
            KH.save('google_places', False, 'refused', 'Refused.',
                    now=t0 + dt.timedelta(minutes=30))
            ok(KeyStatus.objects.get(service='google_places')
               .failing_since == t0,
               '  failing since the first failure, not the latest')
            ok(KH.maybe_email(t0 + dt.timedelta(minutes=61),
                              send=sent.append) and len(sent) == 1,
               'FAILING AN HOUR: one email')
            m = sent[0]
            ok(m.to == ['demetri@example.com'] and
               'Google Places' in m.subject and
               'Anthropic (the AI): Working' in m.body and
               'Google Places: NOT WORKING since' in m.body and
               'Not working because of it' in m.body and
               'fake-key-xyz' not in m.body,
               '  to Demetri only; every key and how it is; never the key')
            ok(not KH.maybe_email(t0 + dt.timedelta(hours=5),
                                  send=sent.append) and len(sent) == 1,
               'ONE A DAY: not again the same day')
            KH.save('google_places', True, now=t0 + dt.timedelta(hours=6))
            KeyStatus.objects.update(emailed_on=None)
            ok(not KH.maybe_email(t0 + dt.timedelta(hours=7),
                                  send=sent.append) and len(sent) == 1,
               'ALL WORKING: no email, and no "working again" email')
            raise Rollback
    except Rollback:
        pass
    os.environ.pop('KEY_ALERT_EMAIL', None)

# ==========================================================================
head('4. HELP AND REGISTERED')
# ==========================================================================
adm = read(J(PG, 'help_content', 'administration.html'))
ok('data-key-email-help' in adm and 'failing for an hour' in adm and
   'python manage.py check_keys' in adm,
   'HELP (Administration, System): the email, when, to whom, check_keys')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
