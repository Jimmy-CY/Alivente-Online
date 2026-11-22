# -*- coding: utf-8 -*-
"""test_ra14_trip_tabs_tap.py - round RA14, 22 Nov 2026.

RELEASE RA14 - THE PHONE'S TRIP TABS OPEN AGAIN.
Demetri, 22 Nov: "Buttons look good on mobile. But don't work when you
press them". RA13 marked the trip tabs data-tab="..."; travel.js takes
every [data-tab] on a page for its own in-page tabs (the boarding passes),
cancelled the tap and looked for a panel the trip page has not got. The
trip tabs are marked data-trip-tab now: plain links again. No network.
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

SUFFIX = '.bak_ra14'
ME = 'test_ra14_trip_tabs_tap.py'
PATCHER = 'apply_ra14_trip_tabs_tap.py'
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
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')

head('1. THE SOURCE')
js = read(J(TV, 'assets', 'travel.js'))
ok("querySelectorAll('[data-tab]')" in js and 'e.preventDefault()' in js,
   'travel.js takes every [data-tab] for its own tabs (why RA13 broke)')
mt = read(J(TT, 'm', 'trip.html'))
nav = mt.split('{% block tabs %}')[1].split('{% endblock %}')[0]
ok(' data-tab=' not in nav and nav.count(' data-trip-tab="') == 5,
   'THE TRIP TABS are data-trip-tab - travel.js leaves them alone')
ok(' data-tab=' not in mt, '  and nothing else on the trip page uses it')
ok(nav.count(' href="') == 5, '  each one a real link')

head('2. DRIVEN (database; no network)')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from pages.workspace import ensure_workspace
    from travel.models import Trip
    connection.ensure_connection()
    Trip.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])
if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            me = User.objects.create_user('ra14a', 'ra14a@example.com', 'x')
            me.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=me, defaults={'workspace': ensure_workspace(me)})
            t = Trip.objects.create(owner=me, name='RA14 Istanbul')
            P = Client(SERVER_NAME='localhost')
            P.force_login(me)
            for tab in ('', 'itinerary', 'wish', 'costs', 'info'):
                url = '/travel/m/trip/%d/%s' % (t.pk,
                                               '?tab=' + tab if tab else '')
                p = P.get(url).content.decode()
                ok(' data-tab=' not in p,
                   'THE PHONE PAGE (%s): no [data-tab] for travel.js to '
                   'catch' % (tab or 'bookings'))
            raise Rollback
    except Rollback:
        pass

head('3. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
