# -*- coding: utf-8 -*-
"""test_ra08_google_quota.py - round RA08, 20 Nov 2026.

RELEASE RA08 - THE KEY WATCH STOPS USING UP GOOGLE'S DAILY LIMIT.
20 Nov: Google refused every search from 20:10 - "Quota exceeded for quota
metric 'SearchTextRequest' and limit 'SearchTextRequest per day'" (limit
100). RA04's watcher tried Google every 15 minutes in each web worker; even
a free search counts. Now Google is tried only while it fails, once an
hour; the workers share one watch; and Google's own reason is shown.
Demetri: "OK. Lt's make these changes." No test here calls Google or
Anthropic.
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

SUFFIX = '.bak_ra08'
ME = 'test_ra08_google_quota.py'
PATCHER = 'apply_ra08_google_quota.py'
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
import json                                                 # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from pages import key_health as KH                          # noqa: E402
PG = J(ROOT, 'pages')

head('1. GOOGLE\'S OWN REASON (no network)')
body = json.dumps({'error': {
    'code': 429, 'status': 'RESOURCE_EXHAUSTED',
    'message': "Quota exceeded for quota metric 'SearchTextRequest' and "
               "limit 'SearchTextRequest per day' of service "
               "'places.googleapis.com' for consumer 'project_number:1'.",
    'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo',
                 'metadata': {'quota_limit_value': '100',
                              'quota_limit':
                              'SearchTextRequestPerDayPerProject'}}]}})
p, d = KH.classify_google(429, body)
ok(p == 'limit' and 'SearchTextRequest per day (limit 100)' in d and
   len(d) <= 255, 'THE LIMIT BY NAME: SearchTextRequest per day (limit 100)',
   d)
p, d = KH.classify_google(403, json.dumps({'error': {
    'message': 'API key not valid AIzaSyFAKEFAKEFAKEFAKE123 please'}}))
ok(p == 'refused' and 'AIza' not in d and '[key]' in d,
   '  a message with something key-like: it is cut out', d)
ok(KH.classify_google(500, 'not json')[0] == 'down',
   '  no body worth reading: just "did not answer"')

head('2. THE WATCH (database; no network)')
have_db = False
try:
    from django.db import connection, transaction
    from django.utils import timezone
    from pages.models import KeyStatus
    connection.ensure_connection()
    KeyStatus.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])
if have_db:
    class Rollback(Exception):
        pass
    calls = []
    _pa, _pg, _me = KH.probe_anthropic, KH.probe_google, KH.maybe_email
    KH.probe_anthropic = lambda: (calls.append('a') or (True, '', ''))
    KH.probe_google = lambda: (calls.append('g') or (True, '', ''))
    KH.maybe_email = lambda now=None, send=None: False
    os.environ['GOOGLE_PLACES_KEY'] = 'fake'
    try:
        with transaction.atomic():
            KeyStatus.objects.all().delete()
            t0 = timezone.now()
            KH.save('google_places', True, now=t0)
            KH.check_all(t0)
            KH.check_all(t0 + dt.timedelta(minutes=1))
            ok(calls == ['a'],
               'TWO WORKERS AT ONCE: one check; Google not tried while it '
               'works', calls)
            del calls[:]
            KH.check_all(t0 + dt.timedelta(minutes=15))
            ok(calls == ['a'], '  15 minutes on: Anthropic again, still '
               'no Google', calls)
            del calls[:]
            KH.save('google_places', False, 'limit', 'x', now=t0)
            KH.check_all(t0 + dt.timedelta(minutes=30))
            ok(calls == ['a'], 'GOOGLE FAILING: not again within the hour',
               calls)
            del calls[:]
            KH.check_all(t0 + dt.timedelta(minutes=61))
            ok(calls == ['a', 'g'], '  an hour on: tried once', calls)
            del calls[:]
            KH.check_all(t0 + dt.timedelta(minutes=62), force=True)
            ok(calls == ['a', 'g'], 'BY HAND (check_keys): both, now',
               calls)
            KH.probe_google = lambda: (calls.append('g') or
                                       (False, 'limit', 'x'))
            KeyStatus.objects.filter(service=KH.WATCH).update(
                last_checked=None)
            n = 0
            for i in range(96):
                del calls[:]
                KH.check_all(t0 + dt.timedelta(minutes=80 + 15 * i))
                n += calls.count('g')
            ok(n <= 25, 'A WHOLE FAILING DAY: Google tried at most about 24 '
               'times (was 96 a worker)', n)
            ok(all(x['service'] != KH.WATCH for x in KH.lines()),
               '  the shared mark never shows in the email')
            raise Rollback
    except Rollback:
        pass
    KH.probe_anthropic, KH.probe_google, KH.maybe_email = _pa, _pg, _me

head('3. WIRED, HELP AND REGISTERED')
ok("_health(False, e.code, body)" in read(J(ROOT, 'travel', 'gplaces.py')),
   'A REAL SUGGESTION\'S REFUSAL carries Google\'s reason too')
ok('check_all(force=True)' in read(J(PG, 'management', 'commands',
                                     'check_keys.py')),
   'manage.py check_keys tries both keys, now')
adm = read(J(PG, 'help_content', 'administration.html'))
ok('Google is tried only while it is failing, once an hour' in adm and
   'Google&rsquo;s own reason' in adm, 'HELP: why, and Google\'s reason')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
