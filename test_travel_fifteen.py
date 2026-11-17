# -*- coding: utf-8 -*-
"""test_travel_fifteen.py - round TR-15, 17 Nov 2026.

RELEASE 96 - TRAVEL: THE PHONE APP FETCHES THE NEW LOOK.
Demetri, 17 Nov, after R95: "It looks perfect on the Desktop. However, it
is wrong on the mobile app" - the calendar unstyled. R95 changed
travel.css but not the phone's version, so the app kept its old copy. The
version moves now, and this suite fails the gate whenever travel.css or
travel.js change and the version does not.
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

SUFFIX = '.bak_travel15'
ME = 'test_travel_fifteen.py'
PATCHER = 'apply_travel_fifteen.py'
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
import hashlib                                              # noqa: E402
import re                                                   # noqa: E402
TA = J(ROOT, 'travel')
TT = J(TA, 'templates', 'travel')
# ==========================================================================
head('1. THE VERSION')
# ==========================================================================
ph = read(J(TA, 'phone.py'))
v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
fp = re.search(r"SW_ASSETS = '([0-9a-f]{12})'", ph)
base = read(J(TT, 'm', 'base.html'))
ok(v and int(v.group(1)) >= 15 and
   base.count('?v=tv%s-%s' % v.groups()) == 2,
   'THE PHONE: tv15-1 or later, on its style and its script')
with open(J(TA, 'assets', 'travel.css'), 'rb') as f1, \
        open(J(TA, 'assets', 'travel.js'), 'rb') as f2:
    now = hashlib.sha1(f1.read() + f2.read()).hexdigest()[:12]
ok(fp and fp.group(1) == now,
   'THE GUARD: travel.css and travel.js are the ones this version was '
   'moved for - change either, move SW_VERSION and set SW_ASSETS to %s'
   % now, fp.group(1) if fp else None)
ok('fetches its new look by itself' in read(
    J(ROOT, 'pages', 'help_content', 'administration.html')),
   'HELP: the phone app picks up a new look by itself')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Trip
    from travel import phone as PH
    connection.ensure_connection()
    Trip.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('tv15a', 'tv15a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            h = M.get('/travel/m/trips/?view=calendar').content.decode()
            ok('travel.css?v=%s' % PH.SW_VERSION in h and
               'data-calendar' in h,
               'THE CALENDAR on the phone asks for the new style')
            sw = M.get('/travel/app/sw.js').content.decode()
            ok('travel.css?v=%s' % PH.SW_VERSION in sw and
               "travel-shell-%s" % PH.SW_VERSION in sw,
               'THE WORKER keeps the new copy, and drops the old one')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok("SW_VERSION = 'tv12-1'" in was(J(TA, 'phone.py')),
       'before this round: R95 changed the style and the phone kept tv12-1')
except IOError as _e:
    skip('control', str(_e))
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
