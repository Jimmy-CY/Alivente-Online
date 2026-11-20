# -*- coding: utf-8 -*-
"""test_ra07_trip_days.py - round RA07, 19 Nov 2026.

RELEASE RA07 - WEATHER BEFORE ANYTHING IS BOOKED; SPENDING ONLY ON THE
TRIP'S DAYS, AND CHANGED WHEN NEEDED; A STEADIER WELLNESS TEST.
Demetri, 19 Nov, on a trip with no bookings: "Why can't i see any
weather??"; "Should I be able to add Spending to days outside of my trip
dates? I don't think so..."; "Create a plan to do this ... Group all of
these changes together." No test here calls the weather or rate services.
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

SUFFIX = '.bak_ra07'
ME = 'test_ra07_trip_days.py'
PATCHER = 'apply_ra07_trip_days.py'
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
from decimal import Decimal as D                            # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import travel.fx as FX                                      # noqa: E402
FX.fetch = lambda day, cur: {'GBP': D('0.85')}.get(cur)     # never the web
import travel.places as PL                                  # noqa: E402
PL.start_details = lambda *a, **k: None                     # never Claude
from travel import budget as BU                             # noqa: E402
from travel import weather as WX                            # noqa: E402
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')

head('1. WEATHER BEFORE ANYTHING IS BOOKED (no network)')


class P(object):
    def __init__(self, name, lat, lng, day=None, address=''):
        self.name, self.lat, self.lng, self.day = name, lat, lng, day
        self.address = address


d0 = dt.date(2026, 11, 28)
ist = [P('Hagia Sophia', 41.0086, 28.9802, address='Sultan Ahmet, '
         'Fatih, Istanbul, Turkey'),
       P('Topkapi', 41.0115, 28.9834, address='Istanbul'),
       P('Ephesus', 37.9396, 27.3417, day=d0 + dt.timedelta(1),
         address='Selcuk, Izmir')]
sp = WX.spot_for(ist, d0)
ok(sp and round(sp[0]) == 41 and sp[2] == 'Istanbul',
   'NO BOOKINGS: where most of the Things to do are (Istanbul)', sp)
sp2 = WX.spot_for(ist, d0 + dt.timedelta(1))
ok(sp2 and round(sp2[0]) == 38,
   '  a day with something planned: that place first (Ephesus)', sp2)
ok(WX.spot_for([P('Nowhere', None, None)], d0) is None,
   '  no places with a position: no weather')
ok(WX.place_name(P('Hagia Sophia', 1, 2)) == 'near Hagia Sophia',
   '  no city in the address: "near" the place')
_off, _fetch = WX.off, WX.fetch
WX.off = lambda: False
calls = []
day = {'time': [str(d0)], 'weather_code': [2],
       'temperature_2m_max': [14.2], 'temperature_2m_min': [8.1],
       'precipitation_probability_max': [20], 'precipitation_sum': [0],
       'wind_speed_10m_max': [12]}


def fake(url):
    calls.append(url)
    if 'geocoding' in url:
        return {'results': [{'latitude': 1, 'longitude': 2,
                             'country': 'Greece'}]}
    return {'daily': day}


WX.fetch = fake
from django.core.cache import cache                         # noqa: E402
cache.clear()
w = WX.for_day([], d0, today=d0 - dt.timedelta(9), places=ist)
ok(w and w['city'] == 'Istanbul' and w['hi'] == 14 and
   not any('geocoding' in u for u in calls),
   'THE FORECAST from the place\'s own position - no place search')


class Bk(object):
    def __init__(self, kind, start, end=None, city=''):
        self.kind, self.start_date, self.end_date = kind, start, end
        self.city, self.status = city, 'ok'
        self.to_place = self.address = self.title = self.country = ''
        self.from_place = ''


cache.clear()
w2 = WX.for_day([Bk('stay', d0, d0 + dt.timedelta(3), city='Athens')], d0,
                today=d0, places=ist)
ok(w2 and w2['city'] == 'Athens', 'A BOOKING STILL WINS', w2)
WX.off, WX.fetch = _off, _fetch
ok("with_weather(itinerary(t, bs, pl), bs, pl)" in read(J(TV, 'views.py'))
   and "weather.for_day(shaped, day, day, pl)" in read(J(TV, 'phone.py')),
   '  the itinerary and Today pass the Things to do')

head('2. SPENDING ONLY ON THE TRIP\'S DAYS (no database)')
s0, e0 = dt.date(2026, 11, 28), dt.date(2026, 12, 1)
ok(BU.default_day(s0, e0, today=dt.date(2026, 11, 19)) == s0 and
   BU.default_day(s0, e0, today=dt.date(2026, 11, 30)) ==
   dt.date(2026, 11, 30) and
   BU.default_day(s0, e0, today=dt.date(2026, 12, 9)) == e0 and
   BU.default_day(None, None) is None,
   'THE DAY: the first before the trip, today during it, the last after')


class T(object):
    budget, budget_by = D('60'), 'day'


class SP(object):
    def __init__(self, day, eur):
        self.day, self.amount_eur = day, eur


x = BU.summary(T, [SP(dt.date(2026, 11, 19), D('50')), SP(s0, D('40'))],
               s0, e0, today=s0)
ok(x['outside'] == 1 and x['outside_label'] == '€50' and
   x['spent'] == D('40') and all(c['day'] >= s0 for c in x['chart']),
   'OUTSIDE: the €50 on 19 Nov is apart, not in the plan or the bars')

head('3. DRIVEN (database; no web)')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from pages.models import UserProfile
    from pages.workspace import ensure_workspace
    from travel.models import Booking, Spend, Trip
    connection.ensure_connection()
    Spend.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])
PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')
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
            me = User.objects.create_user('ra07a', 'ra07a@example.com', 'x')
            her = User.objects.create_user('ra07b', 'ra07b@example.com', 'x')
            for u in (me, her):
                u.user_permissions.add(perm)
                UserProfile.objects.update_or_create(
                    user=u, defaults={'workspace': ensure_workspace(me)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(me)
            H = Client(SERVER_NAME='localhost')
            H.force_login(her)
            d = timezone.localdate()
            t = Trip.objects.create(owner=me, name='RA07 trip',
                                    start_date=d + dt.timedelta(9),
                                    end_date=d + dt.timedelta(12))
            t.shared_with.add(her)
            A.post('/travel/%d/spend/' % t.pk, {'amount': '30'})
            s1 = Spend.objects.filter(trip=t).first()
            ok(s1 and s1.day == t.start_date,
               '+ SPENDING before the trip: lands on its first day')
            n = Spend.objects.filter(trip=t).count()
            A.post('/travel/%d/spend/' % t.pk, {'amount': '5',
                                                'day': str(d)})
            ok(Spend.objects.filter(trip=t).count() == n,
               '  a day outside the trip is refused')
            old = Spend.objects.create(trip=t, day=d, amount=D('50'),
                                       amount_eur=D('50'), added_by=me)
            c = A.get('/travel/%d/costs/' % t.pk).content.decode()
            ok('data-spend-outside' in c and 'data-bud-outside' not in c
               or 'data-spend-outside' in c,
               'COSTS: an old one outside the dates is listed apart')
            ok('min="%s"' % t.start_date.isoformat() in c and
               'max="%s"' % t.end_date.isoformat() in c,
               '  the day picker offers only the trip\'s days')
            ok('Trip total' in c and '€80' in c,
               '  ...and it still counts in the trip\'s costs (€80)')
            A.post('/travel/spend/%d/edit/' % old.pk, {
                'amount': '17', 'currency': 'GBP',
                'day': str(t.start_date + dt.timedelta(1)), 'what': 'Taxi'})
            old.refresh_from_db()
            ok(old.day == t.start_date + dt.timedelta(1) and
               old.currency == 'GBP' and old.amount_eur == D('20.00') and
               old.what == 'Taxi',
               'CHANGE A SPENDING: moved onto the trip, in GBP, re-converted')
            A.post('/travel/spend/%d/edit/' % old.pk, {
                'amount': '17', 'day': str(d)})
            old.refresh_from_db()
            ok(old.day == t.start_date + dt.timedelta(1),
               '  and never off the trip again')
            r = H.post('/travel/spend/%d/edit/' % old.pk, {'amount': '1'})
            ok(r.status_code == 404, '  a shared traveller cannot change it')
            ok(M.get('/travel/m/%d/spend/%d/' % (t.pk, old.pk))
               .status_code == 200,
               'THE PHONE: tap one to change it')
            nd = Trip.objects.create(owner=me, name='No dates')
            r = A.post('/travel/%d/spend/' % nd.pk, {'amount': '9'})
            ok(not Spend.objects.filter(trip=nd).exists(),
               'A TRIP WITH NO DATES: nothing added until it has dates')
            raise Rollback
    except Rollback:
        pass

head('4. WELLNESS AND HELP')
ok("_esc(Q.for_day(a.pk, today)['text']) in t" in read(
    J(ROOT, 'test_wellness_six.py')),
   'test_wellness_six compares the quote as the page shows it (escaped)')
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('the weather follows your <strong>Things to do</strong>' in adm and
   'Outside the trip&rsquo;s dates' in adm and 'Click a spending' in adm,
   'HELP (computer): weather from Things to do; trip days; changing')
mh = read(J(TT, 'm', 'help.html'))
ok('follows your Things to do' in mh and 'tap a spending' in mh,
   'HELP (phone)')
import re as _re                                            # noqa: E402
_v = _re.search(r"SW_VERSION = 'tv(\d+)-\d+'", read(J(TV, 'phone.py')))
ok(_v and int(_v.group(1)) >= 21, 'THE PHONE APP moves to tv21-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
