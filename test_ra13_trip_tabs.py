# -*- coding: utf-8 -*-
"""test_ra13_trip_tabs.py - round RA13, 22 Nov 2026.

RELEASE RA13 - THE TRIP TABS: ICONS; SHORT NAMES ON THE PHONE.
Demetri, 22 Nov: "I am not happy with how the way Bookings, Itinerary, etc
show on mobile" - "Lets go with Option B with full names on computer and
short ones on mobile." Five tabs wrapped onto two lines on the phone; now
an icon over a short name (Bookings, Plan, To do, Costs, Info), all on one
line, and the computer's tabs carry the same icons with their full names.
No network.
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

SUFFIX = '.bak_ra13'
ME = 'test_ra13_trip_tabs.py'
PATCHER = 'apply_ra13_trip_tabs.py'
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
import travel.places as PL                                  # noqa: E402
PL.start_details = lambda *a, **k: None                     # never Claude
from django.template.loader import render_to_string         # noqa: E402
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')

head('1. THE ICONS AND THE TABS')
seen = set()
for k in ('bookings', 'itinerary', 'wish', 'costs', 'info'):
    s = render_to_string('travel/_tab_icon.html', {'k': k})
    ok(s.count('<svg') == 1 and 'aria-hidden="true"' in s,
       'ICON: %s' % k)
    seen.add(s)
ok(len(seen) == 5, '  each one different')
mt = read(J(TT, 'm', 'trip.html'))
ok('<nav class="tv-tabs is-icons"' in mt and 'overflow-x: auto' not in
   mt.split('{% block tabs %}')[1].split('{% endblock %}')[0],
   'THE PHONE: icon tabs on one line - no sideways scroll')
for short, full in (('Plan', 'Itinerary'), ('To do', 'Things to do'),
                    ('Info', 'Good to know')):
    ok('aria-label="%s"' % full in mt and '<span>%s</span>' % short in mt,
       '  short name %s (read aloud as %s)' % (short, full))
c = read(J(TV, 'assets', 'travel.css'))
ok('.tv-tabs.is-icons .tv-tab { flex: 1 1 0;' in c and
   'white-space: nowrap' in c.split('.tv-tabs.is-icons .tv-tab {')[1]
   .split('}')[0], '  each tab an equal share of the line, no wrapping')
dt_ = read(J(TT, 'trip.html'))
ok(dt_.count("{% include 'travel/_tab_icon.html'") == 5 and
   '>Itinerary</a>' not in dt_ and "%}Itinerary</a>" in dt_ and
   "%}Good to know</a>" in dt_,
   'THE COMPUTER: the same icons, full names')

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
            me = User.objects.create_user('ra13a', 'ra13a@example.com', 'x')
            me.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=me, defaults={'workspace': ensure_workspace(me)})
            t = Trip.objects.create(owner=me, name='RA13 Istanbul')
            P = Client(SERVER_NAME='localhost')
            P.force_login(me)
            p = P.get('/travel/m/trip/%d/?tab=wish' % t.pk).content.decode()
            nav = p.split('<nav class="tv-tabs is-icons"')[1].split(
                '</nav>')[0]
            ok(nav.count('<svg') == nav.count('class="tv-tab') >= 4 and
               '<span>Plan</span>' in nav and '<span>Info</span>' in nav,
               'THE PHONE PAGE: an icon on every tab, short names')
            ok('data-tab="wish" aria-label="Things to do" aria-current="page"'
               in nav, '  the open tab is marked')
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
            h = A.get('/travel/%d/good-to-know/' % t.pk).content.decode()
            nav = h.split('aria-label="Trip">')[1].split('</nav>')[0]
            ok(nav.count('<svg') >= 4 and 'Things to do' in nav and
               'Good to know</a>' in nav,
               'THE COMPUTER PAGE: icons, full names')
            raise Rollback
    except Rollback:
        pass

head('3. HELP AND REGISTERED')
ok('short names (Bookings, Plan, To do, Costs, Info)' in
   read(J(ROOT, 'pages', 'help_content', 'administration.html')),
   'HELP (computer)')
ok('<b>Plan</b> (the itinerary)' in read(J(TT, 'm', 'help.html')),
   'HELP (phone)')
_v = re.search(r"SW_VERSION = 'tv(\d+)-\d+'", read(J(TV, 'phone.py')))
ok(_v and int(_v.group(1)) >= 26, 'THE PHONE APP moves to tv26-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
