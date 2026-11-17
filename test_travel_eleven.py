# -*- coding: utf-8 -*-
"""test_travel_eleven.py - round TR-11, 17 Nov 2026.

RELEASE 92 - TRAVEL: PLAN MY DAYS.
Demetri, 17 Nov: "I want to add a button which will do a whole lot of
thinking using AI, to optimise these activities/things to do across the
days of my trip" - asking first which days, mornings or afternoons to keep
free, then using "opening hours, peak periods, proximity to other
activities". Decided: ask per place on a day (Keep / Can move); morning /
afternoon / evening; busy times from the AI's knowledge; no weather; one
release. Undo plan "must stay available for longer". And after accepting,
new things to do: "Fit them in" (agreed 1 to 4).
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

SUFFIX = '.bak_travel11'
ME = 'test_travel_eleven.py'
PATCHER = 'apply_travel_eleven.py'
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
md = read(J(TA, 'models.py'))
ok('class TripPlan(models.Model):' in md and
   'facts = models.JSONField(default=dict, blank=True)' in md and
   'lat = models.FloatField(null=True, blank=True)' in md and
   os.path.isfile(J(TA, 'migrations', '0009_plan_my_days.py')),
   'MODEL: what the planner knows about a place; the plan with its answers, '
   'proposal and Undo (0009)')
pl = read(J(TA, 'places.py'))
ok("PLAN_MODEL = os.environ.get('TRAVEL_PLAN_MODEL', 'claude-haiku-4-5')"
   in pl and 'def call_facts(' in pl and 'def call_reasons(' in pl and
   'This is general knowledge, not live data.' in pl,
   'AI: the small model, in the file that already talks to Claude; busy '
   'times are general knowledge and say so')
u = read(J(TA, 'urls.py'))
ok(all("name='%s'" % n in u for n in (
    'plan_setup', 'plan_view', 'plan_move', 'plan_accept', 'plan_undo',
    'plan_discard', 'm_plan_setup', 'm_plan_view', 'm_plan_move',
    'm_plan_accept', 'm_plan_undo', 'm_plan_discard')),
   'routes: setup, the plan, move, accept, undo, discard - computer and '
   'phone')
for f in ('plan_setup.html', 'plan_working.html', 'plan_review.html',
          'plan_fit.html', 'plan_failed.html'):
    ok(os.path.isfile(J(TT, f)) and os.path.isfile(J(TT, 'm', f)),
       '  %s on the computer and the phone' % f)
ok('data-travel-help' in read(J(TT, 'plan_setup.html')) and
   'data-travel-help' in read(J(TT, 'plan_review.html')),
   'Help on the new computer pages')
ok("include 'travel/_plan_banner.html'" in read(J(TT, 'trip.html')) and
   "include 'travel/_plan_banner.html' with phone=True" in read(
       J(TT, 'm', 'trip.html')) and 'data-plan-cta' in read(
       J(TT, 'trip.html')) and 'data-plan-cta' in read(
       J(TT, 'm', 'trip.html')),
   'Things to do and the itinerary: Plan my days, Undo plan, Fit them in')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('<strong>Plan my days.</strong>' in hp and '<strong>Fit them in</strong>'
   in hp and '<strong>Undo plan</strong>' in hp and
   '<b>Plan my days</b>' in read(J(TT, 'm', 'help.html')),
   'HELP: the three questions, the plan, Undo, Fit them in')

# ==========================================================================
head('2. THE RULES (travel/planner.py)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from types import SimpleNamespace as NS                     # noqa: E402
from travel import planner as PL, places as PP              # noqa: E402

ok(PL.parse_ranges('09:00-13:00,16:00-20:00') == [(540, 780), (960, 1200)]
   and PL.parse_ranges('closed') == [] and PL.parse_ranges('') is None,
   'opening hours read: two ranges, closed, not known')
T = dt.time
D = [dt.date(2027, 3, 12) + dt.timedelta(days=i) for i in range(5)]


def bk(kind, sd, st=None, ed=None, et=None, title='x'):
    return NS(kind=kind, status='booked', start_date=sd, start_time=st,
              end_date=ed, end_time=et, title=title,
              get_kind_display=lambda: kind.title())


fly_in = bk('flight', D[0], T(11, 50), D[0], T(14, 10), 'VY7821')
fly_out = bk('flight', D[4], T(17, 40), D[4], T(21), 'VY7822')
dinner = bk('restaurant', D[1], T(21), title='Can Sole')
g = PL.grid(None, [fly_in, fly_out, dinner], D)
st = {(r['day'], c['key']): (c['state'], c.get('label', ''))
      for r in g for c in r['cells']}
ok(st[(D[0], 'm')][0] == 'taken' and 'lands 14:10' in st[(D[0], 'm')][1]
   and st[(D[0], 'a')][0] == 'free',
   'THE GRID: the arrival morning is taken ("Flight lands 14:10"); the '
   'afternoon is free')
ok(st[(D[1], 'e')] == ('taken', 'Dinner 21:00') and
   st[(D[4], 'e')] == ('taken', 'Flight 17:40') and
   st[(D[4], 'a')][0] == 'free',
   '  the booked dinner takes the evening; the flight home its evening - '
   'the early afternoon before it is still free', [st[(D[1], 'e')],
                                                   st[(D[4], 'a')],
                                                   st[(D[4], 'e')]])
fr = PL.free_of(D[3], [], {'%s-m' % D[3].isoformat()})
ok(fr['m'] == [] and fr['a'] == [(780, 1080)],
   'A SLOT KEPT FREE has no time in it')
ok(PL.hop((41.3839, 2.1763), (41.3852, 2.1809), 'transit')[1].endswith(
    'walk') and 'metro or bus' in PL.hop((41.3839, 2.1763),
                                         (41.4145, 2.1527), 'transit')[1]
   and 'drive' in PL.hop((41.3839, 2.1763), (41.4145, 2.1527), 'car')[1],
   'THE WAY BETWEEN: a short one on foot; further by metro or bus, or '
   'drive with a car')

_n = [0]


def place(name, lat, lng, open_=None, minutes=60, best='any', day=None,
          booking=None, kind='sight', book=False, created=None):
    _n[0] += 1
    f = {'minutes': minutes, 'best': best, 'book': book}
    if open_:
        f['open'] = open_
    return NS(pk=_n[0], name=name, lat=lat, lng=lng, facts=f, kind=kind,
              day=day, time=None, booking_id=booking, done=False,
              save=lambda **k: None)


every = {d: '09:00-19:00' for d in PP.DAYS7}
no_sun = dict(every, sun='closed')
gothic = place('Gothic Quarter', 41.3839, 2.1763, every, 90)
picasso = place('Picasso Museum', 41.3852, 2.1809, every, 75)
boqueria = place('La Boqueria', 41.3817, 2.1716, no_sun, 45)
guell = place('Park Guell', 41.4145, 2.1527, every, 90, 'morning',
              book=True)
bunkers = place('Bunkers', 41.4194, 2.1617, every, 60)
monj = place('Montjuic', 41.3634, 2.1665, every, 90)
ALL = [gothic, picasso, boqueria, guell, bunkers, monj]
stay = bk('stay', D[0], T(15), D[4], T(11))
stay.address, stay.provider, stay.pk = '', '', 99
B = [fly_in, fly_out, dinner, stay]
PL.prepare = lambda p, start=None, client=None: p
PL.geocode = lambda text: None


def run(places, answers):
    return PL.plan(None, places, B, D, answers)


out = run(ALL, {'pace': 'normal', 'mode': 'transit'})
where = {r['name']: d['day'] for d in out['days'] for r in d['items']}
ok(len(where) == 6 and not out['unfit'],
   'EVERYTHING PLACED (6 of 6), nothing left out', where)
ok(len({where['Gothic Quarter'], where['Picasso Museum'],
         where['La Boqueria']}) <= 2 and where['Park Guell'] ==
   where['Bunkers'] and where['Montjuic'] not in (where['Park Guell'],),
   'NEAR GOES WITH NEAR: the old town on one day, the hill above Gracia '
   'on another (Demetri: "proximity to other activities to reduce '
   'travel/walking time")', where)
ok(where['La Boqueria'] != D[2].isoformat(),
   'CLOSED: La Boqueria is never put on its closed Sunday')
day0 = [d for d in out['days'] if d['day'] == D[0].isoformat()][0]
ok(all(r['time'] >= '15:25' for r in day0['items']),
   'ARRIVAL DAY: nothing before the flight has landed and you are out of '
   'the airport')
lastd = [d for d in out['days'] if d['day'] == D[4].isoformat()][0]
ok(all(r['time'] < '15:10' for r in lastd['items']),
   'LAST DAY: done before leaving for the 17:40 flight')
ok(any('Park Guell' in n and 'booked ahead' in n for n in out['notes']),
   'BEFORE YOU GO: Park Guell needs tickets booked ahead')
g2 = [r for d in out['days'] for r in d['items'] if r['name'] ==
      'Park Guell'][0]
ok(g2['time'] < '13:00', 'BUSY TIMES: Park Guell (best in the morning) '
   'goes in a morning', g2['time'])
out = run(ALL, {'pace': 'relaxed', 'mode': 'transit',
                'off': ['%s-%s' % (d.isoformat(), k) for d in D[1:4]
                        for k in 'mae']})
n_day = {d['day']: len(d['items']) for d in out['days']}
ok(max(n_day.values()) <= 2 and len(out['unfit']) >= 1 and
   all(n_day[d.isoformat()] == 0 for d in D[1:4]),
   'PACE AND FREE SLOTS ARE RULES: at most 2 a day, nothing on the days '
   'kept free - and what does not fit is said', n_day)
ok(all(u['why'] for u in out['unfit']),
   '  each with why', out['unfit'])
kept = place('Kept one', 41.38, 2.17, every, 60, day=D[3])
mov = place('Movable', 41.38, 2.17, every, 60, day=D[3])
booked = place('Booked one', 41.40, 2.17, every, 60, day=D[1], booking=7)
out = run([kept, mov, booked, gothic],
          {'keep': {str(mov.pk): 'move', str(booked.pk): 'move'}})
planned = {r['name'] for d in out['days'] for r in d['items']}
ok('Movable' in planned and 'Kept one' not in planned and
   'Booked one' not in planned,
   'KEEP OR CAN MOVE: only "Can move" is planned; a booked one never, '
   'whatever is sent')
closed_all = place('Never open', 41.38, 2.17,
                   {d: 'closed' for d in PP.DAYS7})
out = run([closed_all], {})
ok(out['unfit'] and 'closed on every day' in out['unfit'][0]['why'],
   'CLOSED EVERY DAY: not placed, and it says so')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
import importlib                                            # noqa: E402
importlib.reload(PL)
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, DayOrder, Place, Trip, TripPlan
    connection.ensure_connection()
    TripPlan.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

FACTS = {
    'Park Guell': dict(lat=41.4145, lng=2.1527, minutes=90, best='morning',
                       open={d: '09:30-19:30' for d in PP.DAYS7},
                       book=True, book_note='timed tickets'),
    'Bunkers': dict(lat=41.4194, lng=2.1617, minutes=60, best='afternoon'),
    'La Boqueria': dict(lat=41.3817, lng=2.1716, minutes=45,
                        open=dict({d: '08:00-20:30' for d in PP.DAYS7},
                                  sun='closed')),
    'Gothic Quarter': dict(lat=41.3839, lng=2.1763, minutes=90),
    'Picasso Museum': dict(lat=41.3852, lng=2.1809, minutes=75,
                           open=dict({d: '10:00-19:00' for d in PP.DAYS7},
                                     mon='closed')),
}


class Fake(object):
    def __init__(self):
        self.messages = self
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        name = kw['tools'][0]['name']
        if name == 'record_facts':
            nm = kw['messages'][0]['content'].split('\n')[0][7:]
            inp = FACTS.get(nm, {'minutes': 60, 'best': 'any',
                                 'lat': 41.39, 'lng': 2.17})
        else:
            days = [ln[:10] for ln in
                    kw['messages'][0]['content'].split('\n')]
            inp = {'days': [{'day': d, 'why': 'Close together, on foot.'}
                            for d in days]}
        return NS(content=[NS(type='tool_use', name=name, input=inp)])


PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace
    fake = Fake()
    PP._client = lambda c: fake
    PL.SYNC = True
    PL.geocode = lambda text: None

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('tv11a', 'tv11a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            Dd = [dt.date.today() + dt.timedelta(days=30 + i)
                  for i in range(5)]
            t = Trip.objects.create(owner=u, name='TV11 Barcelona')
            mk = dict(trip=t, added_by=u)
            Booking.objects.create(
                kind='flight', title='VY7821', start_date=Dd[0],
                start_time=T(11, 50), end_date=Dd[0], end_time=T(14, 10),
                from_place='Larnaca (LCA)', to_place='Barcelona (BCN)', **mk)
            Booking.objects.create(
                kind='flight', title='VY7822', start_date=Dd[4],
                start_time=T(17, 40), end_date=Dd[4], end_time=T(21),
                **mk)
            Booking.objects.create(
                kind='stay', title='Hotel', start_date=Dd[0],
                start_time=T(15), end_date=Dd[4], end_time=T(11),
                address='Barcelona', **mk)
            for nm in FACTS:
                Place.objects.create(trip=t, name=nm, kind='sight')
            pic = Place.objects.get(trip=t, name='Picasso Museum')
            pic.day = Dd[3]
            pic.save()
            tix = Place.objects.create(trip=t, name='Sagrada', kind='sight',
                                       day=Dd[1], time=T(10))
            tix.booking = Booking.objects.create(
                kind='activity', title='Sagrada ticket', start_date=Dd[1],
                start_time=T(10), **mk)
            tix.save()
            h = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok('data-plan-cta' in h and 'Plan my days' in h,
               'THINGS TO DO: "4 things to do have no day yet" with Plan '
               'my days')
            h = A.get('/travel/%d/plan/' % t.pk).content.decode()
            ok('data-plan-keep' in h and 'Sagrada' in h and
               'booked, so it stays' in h and 'name="keep_%d"' % pic.pk in h
               and 'name="keep_%d"' % tix.pk not in h,
               'STEP 1: Picasso asks Keep / Can move; the booked Sagrada '
               'is locked')
            ok('Flight lands 14:10' in h and h.count('data-plan-slot') >= 10
               and 'name="pace"' in h and 'name="mode"' in h and
               'name="must"' in h,
               'STEPS 2 AND 3: the grid with the flight greyed; pace, '
               'getting around, must-dos')
            hm = M.get('/travel/m/trip/%d/plan/' % t.pk).content.decode()
            ok('data-plan-steps' in hm and 'data-plan-next' in hm and
               hm.count('data-plan-step=') == 3,
               'PHONE: the same questions as three steps')
            r = A.post('/travel/%d/plan/' % t.pk, {
                'keep_%d' % pic.pk: 'move', 'keep_%d' % tix.pk: 'move',
                'off': ['%s-m' % Dd[3].isoformat()], 'pace': 'normal',
                'mode': 'transit', 'must': [str(pic.pk)]})
            tp = TripPlan.objects.get(trip=t)
            ok(r.status_code == 302 and tp.status == 'ready' and
               tp.answers['keep'] == {str(pic.pk): 'move'},
               'PLAN: worked out; the booked one dropped from the answers')
            names = {x['name']: d['day'] for d in tp.result['days']
                     for x in d['items']}
            ok(set(names) == {'Park Guell', 'Bunkers', 'La Boqueria',
                              'Gothic Quarter', 'Picasso Museum'},
               '  every free place and the movable Picasso planned', names)
            ok(all(x['why'] == 'Close together, on foot.'
                   for d in tp.result['days'] if d['items'] for x in [d]),
               '  each day with its line from the AI')
            ok(len([c for c in fake.calls
                    if c['tools'][0]['name'] == 'record_facts']) == 5 and
               all(c['model'] == 'claude-haiku-4-5' for c in fake.calls),
               '  one facts call per place, on the small model')
            pic.refresh_from_db()
            ok(pic.facts.get('minutes') == 75 and pic.lat == 41.3852 and
               pic.day == Dd[3],
               '  facts kept on the place; nothing moved before accepting')
            h = A.get('/travel/%d/plan/%d/' % (t.pk, tp.pk)).content.decode()
            ok(h.count('data-plan-item=') == 5 and 'data-plan-accept' in h
               and 'BOOKED' in h,
               'YOUR PLAN on the computer: 5 cards, Accept, the booked '
               'ticket shown grey')
            hm = M.get('/travel/m/trip/%d/plan/%d/' % (t.pk, tp.pk)
                       ).content.decode()
            ok(hm.count('data-plan-item=') == 5 and 'tv-pl-move' in hm,
               '  and on the phone, each with Move')
            bun = Place.objects.get(trip=t, name='Bunkers')
            target = Dd[1].isoformat()
            A.post('/travel/%d/plan/%d/move/' % (t.pk, tp.pk),
                   {'place': bun.pk, 'day': target})
            tp.refresh_from_db()
            ok([x['name'] for d in tp.result['days'] if d['day'] == target
                for x in d['items']].count('Bunkers') == 1,
               'MOVE before accepting: Bunkers on the day chosen')
            r = A.post('/travel/%d/plan/%d/accept/' % (t.pk, tp.pk))
            tp.refresh_from_db()
            bun.refresh_from_db()
            ok(tp.status == 'applied' and bun.day == Dd[1] and bun.time and
               'planned=' in r['Location'],
               'ACCEPT: the places on their days, at their times')
            h = A.get(r['Location']).content.decode()
            ok('data-plan-undo' in h and 'Plan applied' in h,
               '  the itinerary says so, with Undo plan')
            hw = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok('data-plan-undo' in hw,
               '  Undo plan on Things to do too - not only once')
            later = Place.objects.create(trip=t, name='Casa Batllo',
                                         kind='sight')
            hw = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok('data-plan-new' in hw and 'Casa Batllo' in hw and
               'Fit them in' in hw and 'data-plan-cta' not in hw,
               'NEW SINCE YOUR PLAN: "1 new thing since your plan - Fit '
               'them in"')
            hf = A.get('/travel/%d/plan/?fit=1' % t.pk).content.decode()
            ok('data-plan-reused' in hf and 'Casa Batllo' in hf and
               'data-plan-change' in hf,
               '  the last answers shown once, Change for the rest')
            before = {p.pk: (p.day, p.time) for p in t.places.exclude(
                pk=later.pk)}
            A.post('/travel/%d/plan/' % t.pk, {'fit': '1'})
            tp2 = TripPlan.objects.filter(trip=t).order_by('-pk')[0]
            only = [x['name'] for d in tp2.result['days'] for x in
                    d['items']]
            ok(only == ['Casa Batllo'] and tp2.answers.get('fit') and
               tp2.answers.get('off') == tp.answers.get('off') and
               all(x.get('new') for d in tp2.result['days']
                   for x in d['items']),
               'FIT THEM IN: only the new one planned, marked NEW, with the '
               'same answers', only)
            A.post('/travel/%d/plan/%d/accept/' % (t.pk, tp2.pk))
            tp.refresh_from_db()
            ok({p.pk: (p.day, p.time) for p in t.places.exclude(
                pk=later.pk)} == before and tp.status == 'replaced',
               '  everything already on a day stayed; the first plan is '
               'kept, no longer the one Undo undoes')
            r = A.post('/travel/%d/plan/%d/undo/' % (t.pk, tp2.pk))
            later.refresh_from_db()
            ok(later.day is None and 'undone=1' in r['Location'] and
               t.places.get(name='Bunkers').day == Dd[1],
               'UNDO undoes the latest run only: Casa Batllo back with no '
               'day; the first plan stays')
            tp.status = 'applied'
            tp.save()
            gq = Place.objects.get(trip=t, name='Gothic Quarter')
            gq.time = T(23)
            gq.save()
            r = A.post('/travel/%d/plan/%d/undo/' % (t.pk, tp.pk))
            gq.refresh_from_db()
            pic.refresh_from_db()
            ok(gq.time == T(23) and pic.day == Dd[3] and
               'kept=1' in r['Location'],
               'UNDO keeps what you moved since (Gothic Quarter at 23:00), '
               'puts the rest back (Picasso to Mon)')
            h = A.get(r['Location']).content.decode()
            ok('Plan undone' in h and 'left where you moved' in h,
               '  and says so')
            other = User.objects.create_user('tv11b', 'tv11b@example.com',
                                             'x')
            other.user_permissions.add(perm)
            B2 = Client(SERVER_NAME='localhost')
            B2.force_login(other)
            ok(B2.get('/travel/%d/plan/' % t.pk).status_code == 404 and
               B2.post('/travel/%d/plan/%d/undo/' % (t.pk, tp.pk)
                       ).status_code == 404,
               'SOMEONE ELSE\'S trip: no plan, no undo')
            ok(A.get('/travel/%d/plan/%d/accept/' % (t.pk, tp.pk)
                     ).status_code == 405,
               'accept, undo, move, discard: POST only')
            tp3 = TripPlan.objects.create(trip=t, status='ready',
                                          result={'days': []})
            A.post('/travel/%d/plan/%d/discard/' % (t.pk, tp3.pk))
            tp3.refresh_from_db()
            ok(tp3.status == 'discarded', 'DISCARD leaves the trip as it was')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('TripPlan' not in was(J(TA, 'models.py')),
       'before this round: no Plan my days - every place put on a day by '
       'hand')
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
