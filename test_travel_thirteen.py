# -*- coding: utf-8 -*-
"""test_travel_thirteen.py - round TR-13, 17 Nov 2026.

RELEASE 94 - TRAVEL: TRIPS LISTED LATEST FIRST; PLAN MY DAYS KNOWS WHERE
YOU ARE.
Demetri, 17 Nov: "When trips are listed, they should be sorted from the
latest one, to the oldest one." Every list - Upcoming, Past, a year, a
country, All - on the computer and the phone.
And: "It put the Parthenon on Monday 9th, but the flight from Dublin to
Athens is at night and I would land on midnight on Monday" - a place goes
on a day only while you are in its country.
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

SUFFIX = '.bak_travel13'
ME = 'test_travel_thirteen.py'
PATCHER = 'apply_travel_thirteen.py'
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
TA = J(ROOT, 'travel')
TT = J(TA, 'templates', 'travel')
# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
v = read(J(TA, 'views.py'))
ok('sel.sort(key=lambda t: (t.start or far), reverse=True)' in v and
   "reverse=(show == 'past' or auto_past)" not in v,
   'COMPUTER: every list sorted latest first')
ph = read(J(TA, 'phone.py'))
ok(ph.count('key=lambda t: t.start or far, reverse=True)') == 3,
   'PHONE: Upcoming too, as Past already was')
pl = read(J(TA, 'planner.py'))
ok('def whereabouts(' in pl and 'def there(' in pl and
   'there(points, it.country, d, t,' in pl,
   'PLAN MY DAYS: where you are, from the flights - checked for every '
   'slot')
ok('It also knows where you are' in read(J(ROOT, 'pages', 'help_content',
                                         'administration.html')) and
   'only on a day you are in that country' in read(J(TT, 'm', 'help.html')),
   'HELP: Plan my days says it knows where you are')
ok('latest trip at the top' in read(J(ROOT, 'pages', 'help_content',
                                    'administration.html')) and
   'listed latest first' in read(J(TT, 'm', 'help.html')),
   'HELP: says so on the computer and the phone')

# ==========================================================================
head('2. WHERE YOU ARE (travel/planner.py)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from types import SimpleNamespace as NS                     # noqa: E402
from travel import planner as PL, places as PP              # noqa: E402

T = dt.time
D = [dt.date(2026, 11, 3) + dt.timedelta(days=i) for i in range(9)]


def bk(kind, sd, st=None, ed=None, et=None, frm='', to='', title='x',
       city='', address=''):
    return NS(kind=kind, status='booked', start_date=sd, start_time=st,
              end_date=ed, end_time=et, from_place=frm, to_place=to,
              title=title, city=city, address=address, country='',
              provider='', pk=id(title) % 10000,
              get_kind_display=lambda: kind.title())


# Demetri's own trip, Athens Nov 2026.
TRIP = [
    bk('flight', D[0], T(8, 30), D[0], T(10, 20), 'Larnaca (LCA)',
       'Athens (ATH)', 'Cyprus Airways CY310'),
    bk('flight', D[2], T(15), D[2], T(17, 5), 'Athens (ATH)',
       'Dublin (DUB)', 'Ryanair FR4519'),
    bk('car', D[2], T(17, 30), D[6], T(16), title='Enterprise car hire',
       address='Dublin Airport, Ireland'),
    bk('flight', D[6], T(18, 20), D[7], T(0, 25), 'Dublin (DUB)',
       'Athens (ATH)', 'Ryanair FR4518'),
    bk('flight', D[8], T(21), D[8], T(22, 40), 'Athens (ATH)',
       'Larnaca (LCA)', 'Cyprus Airways CY313'),
]
pts = PL.whereabouts(TRIP)
ok(PL.where_at(pts, D[0], 12 * 60) == 'Greece' and
   PL.where_at(pts, D[3], 10 * 60) == 'Ireland' and
   PL.where_at(pts, D[6], 10 * 60) == 'Ireland' and
   PL.where_at(pts, D[6], 19 * 60) is None and
   PL.where_at(pts, D[7], 10 * 60) == 'Greece',
   'WHERE YOU ARE: Athens from Tue 3 10:20, Ireland from Thu 5, in the air '
   'Mon 9 evening, Athens again from Tue 10 00:25',
   [(d, PL.where_at(pts, d, 10 * 60)) for d in D])
PL.prepare = lambda p, start=None, client=None: p
PL.geocode = lambda text: None
every = {d: '08:00-20:00' for d in PP.DAYS7}


def place(pk, name, address, lat, lng):
    return NS(pk=pk, name=name, address=address, lat=lat, lng=lng,
              facts={'minutes': 120, 'best': 'morning', 'open': every},
              kind='sight', day=None, time=None, booking_id=None,
              done=False, save=lambda **k: None)


par = place(1, 'Parthenon (Acropolis of Athens)',
            'Dionysiou Areopagitou, Athens 105 58, Greece', 37.9715, 23.7257)
cliffs = place(2, 'Cliffs of Moher', 'Liscannor, Co. Clare, Ireland',
               52.9715, -9.4309)
out = PL.plan(None, [par, cliffs], TRIP, D, {'pace': 'relaxed'})
on = {r['name']: dt.date.fromisoformat(d['day']) for d in out['days']
      for r in d['items']}
ok(on.get(par.name) in (D[0], D[1], D[2], D[7], D[8]) and
   on.get(par.name) != D[6],
   'THE PARTHENON: only on a day you are in Athens - never Mon 9, when you '
   'are still in Ireland until the evening flight', on)
ok(on.get(cliffs.name) in (D[3], D[4], D[5], D[6]),
   'THE CLIFFS OF MOHER: only while you are in Ireland', on)
par.facts = dict(par.facts, open={d: 'closed' for d in PP.DAYS7})
par.facts['open']['mon'] = '08:00-20:00'
out = PL.plan(None, [par], TRIP, D, {})
ok(not out['days'] or all(not d['items'] for d in out['days']),
   'OPEN ONLY ON MONDAY - the Monday you are in Ireland: not placed', out)
cliffs.facts = dict(cliffs.facts)
far = place(3, 'Somewhere in Peru', 'Cusco, Peru', -13.5, -71.9)
out = PL.plan(None, [far], TRIP, D, {})
ok(out['unfit'] and 'not in Peru' in out['unfit'][0]['why'],
   'NOT THERE AT ALL: not placed, and it says why', out['unfit'])
plain = place(4, 'No address', '', None, None)
out = PL.plan(None, [plain], TRIP, D, {})
ok(any(d['items'] for d in out['days']),
   'A PLACE WITH NO COUNTRY KNOWN is still planned')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Trip
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
            u = User.objects.create_user('tv13a', 'tv13a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            today = dt.date.today()

            def trip(name, days, length=5):
                s = today + dt.timedelta(days=days)
                return Trip.objects.create(
                    owner=u, name=name, start_date=s,
                    end_date=s + dt.timedelta(days=length))
            trip('TV13 Old', -400)
            trip('TV13 Last', -60)
            trip('TV13 Next', 30)
            trip('TV13 Later', 90)

            def order(h, names):
                at = [h.find(n) for n in names]
                return all(x >= 0 for x in at) and at == sorted(at)
            h = A.get('/travel/?show=all').content.decode()
            ok(order(h, ['TV13 Later', 'TV13 Next', 'TV13 Last',
                         'TV13 Old']),
               'ALL: Later, Next, Last, Old - the latest first')
            h = A.get('/travel/').content.decode()
            ok(order(h, ['TV13 Later', 'TV13 Next']) and 'TV13 Last' not in h,
               'UPCOMING: the latest first')
            h = A.get('/travel/?show=past').content.decode()
            ok(order(h, ['TV13 Last', 'TV13 Old']),
               'PAST: the latest first, as before')
            h = M.get('/travel/m/trips/').content.decode()
            ok(order(h, ['TV13 Later', 'TV13 Next']),
               'PHONE, Trips: the latest first')
            h = M.get('/travel/m/trips/?show=past').content.decode()
            ok(order(h, ['TV13 Last', 'TV13 Old']),
               '  and its past ones')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok("reverse=(show == 'past' or auto_past)" in was(J(TA, 'views.py')),
       'before this round: Upcoming and All listed oldest first')
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
