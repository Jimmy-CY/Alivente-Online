# -*- coding: utf-8 -*-
"""test_travel_fourteen.py - round TR-14, 17 Nov 2026.

RELEASE 95 - TRAVEL: SHOW ME MORE KEEPS THE TICKS, MARKS THE NEW.
Demetri, 17 Nov: "If I tick a few suggested things to do and then select
'Show me more for Athens', the ones I ticked must remain ticked, even
though new ones are added. Also, it is not clear which ones are new?
Maybe we should always mark the new ones added with a new label each
time?"
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

SUFFIX = '.bak_travel14'
ME = 'test_travel_fourteen.py'
PATCHER = 'apply_travel_fourteen.py'
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
v = read(J(TA, 'views_ideas.py'))
ok("return _back(request, t, anchor='new')" in v,
   'SHOW ME MORE: back with what was ticked, at the first new one')
ok('data-idea-new' in read(J(TT, '_ideas_card.html')) and
   'data-idea-newline' in read(J(TT, '_ideas_top.html')) and
   '.tv-id-new' in read(J(TA, 'assets', 'travel.css')) and
   '.tv-id-new' in read(J(TT, '_style.html')),
   'NEW: a label on each card, a line at the top - computer and phone')
rf = read(J(TT, '_lookup_refresh.html'))
ok('{% if looking %}' in rf and 'location.reload' in rf and
   "include 'travel/_lookup_refresh.html'" in read(J(TT, 'trip.html')) and
   "include 'travel/_lookup_refresh.html'" in read(J(TT, 'm', 'trip.html')),
   'LOOKING IT UP: the trip page asks again by itself while a place is '
   'being looked up - computer and phone')
ok('INPUT|SELECT|TEXTAREA' in rf and 'is-sorting' in rf,
   '  never while you are choosing a day, typing or dragging')
ok('looked up by itself' in read(J(ROOT, 'pages', 'help_content',
                                  'administration.html')),
   '  and Help says so')
ok(os.path.isfile(J(TA, 'calendar_view.py')) and
   os.path.isfile(J(TT, '_calendar.html')) and
   "include 'travel/_calendar.html'" in read(J(TT, 'trips.html')) and
   "include 'travel/_calendar.html' with phone=True" in read(
       J(TT, 'm', 'trips.html')) and 'data-view-switch' in read(
       J(TT, 'trips.html')),
   'CALENDAR: List | Calendar on Travel and on the phone\'s Trips')
ok('<strong>Calendar.</strong>' in read(J(ROOT, 'pages', 'help_content',
                                         'administration.html')) and
   '<p class="tv-h2">Calendar</p>' in read(J(TT, 'm', 'help.html')),
   '  and Help says how it works')
ok('marked <strong>New</strong>' in read(J(ROOT, 'pages', 'help_content',
                                          'administration.html')) and
   'marked <b>New</b>' in read(J(TT, 'm', 'help.html')),
   'HELP: says so')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from types import SimpleNamespace as NS                     # noqa: E402
from travel import ideas as ID, places as PP                # noqa: E402
from travel import planner as PL                            # noqa: E402


def dd(day, minutes):
    return {'day': day, 'minutes': minutes, 'items': []}


notes = PL.notes_of({'days': [dd('2026-11-09', 330), dd('2026-11-10', 120),
                              dd('2026-11-11', 420)]}, [])
full = [n for n in notes if 'full' in n]
ok(len(full) == 1 and full[0].count('fullest') == 1 and
   full[0].startswith('Wednesday 11 is the fullest day - about 7 hours') and
   'Monday 9 is also very full (about 6 hours)' in full[0],
   'PLAN MY DAYS: one fullest day (Wednesday); Monday "also very full"',
   full)
notes = PL.notes_of({'days': [dd('2026-11-09', 330)]}, [])
ok(notes == ['Monday 9 is the fullest day - about 6 hours of visits.'],
   '  one long day: just the fullest', notes)
ok(not PL.notes_of({'days': [dd('2026-11-09', 200)]}, []),
   '  no long day: nothing said')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, Idea, IdeaRun, Trip
    connection.ensure_connection()
    IdeaRun.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

FIRST = [dict(name='Temple of Olympian Zeus', interest='musts', blurb='a'),
         dict(name='Panathenaic Stadium', interest='musts', blurb='b'),
         dict(name='Ancient Agora of Athens', interest='musts', blurb='c')]
MORE = [dict(name='Benaki Museum', interest='museums', blurb='d'),
        dict(name='Museum of Cycladic Art', interest='museums', blurb='e')]


class Fake(object):
    def __init__(self):
        self.messages = self
        self.more = False

    def create(self, **kw):
        return NS(content=[NS(type='tool_use', name='record_ideas',
                              input={'ideas': MORE if self.more
                                     else FIRST})])


PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace
    fake = Fake()
    PP._client = lambda c: fake
    ID.SYNC = True
    # TR-14 (17 Nov): a hotel on the trip has its missing details looked
    # up on the web when the trip opens - a real, slow, paid call on a
    # machine with the Anthropic key (31.7s in the gate's pool, and the
    # connection guard closed the test's transaction). Never from a test.
    def _no_details(b, client=None):
        raise PP.LookupError_('not in tests')
    PP.call_details = _no_details

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('tv14a', 'tv14a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            d0 = dt.date.today() + dt.timedelta(days=30)
            t = Trip.objects.create(owner=u, name='TV14 Athens')
            Booking.objects.create(trip=t, added_by=u, kind='stay',
                                   title='Hotel', city='Athens',
                                   start_date=d0,
                                   end_date=d0 + dt.timedelta(days=3))
            A.post('/travel/%d/ideas/new/' % t.pk,
                   {'city': ['Athens'], 'interest': ['musts', 'museums']})
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok('data-idea-new' not in h and 'data-idea-newline' not in h,
               'THE FIRST SUGGESTIONS: nothing marked New - all of them are')
            zeus = Idea.objects.get(trip=t, name='Temple of Olympian Zeus')
            agora = Idea.objects.get(trip=t, name='Ancient Agora of Athens')
            fake.more = True
            r = A.post('/travel/%d/ideas/more/' % t.pk, {
                'more': 'Athens', 'idea': [str(zeus.pk), str(agora.pk)]})
            loc = r['Location']
            ok('t=%d,%d' % (zeus.pk, agora.pk) in loc and loc.endswith(
                '#new'),
               'SHOW ME MORE: back with the two ticked, at the first new one',
               loc)
            h = A.get(loc.split('#')[0]).content.decode()
            ok('value="%d" checked' % zeus.pk in h and
               'value="%d" checked' % agora.pk in h,
               '  Temple of Olympian Zeus and the Agora still ticked')
            bm = Idea.objects.get(trip=t, name='Benaki Museum')
            ok(h.count('data-idea-new>') == 2 and 'id="new"' in h and
               h.find('id="new"') < h.find('Benaki Museum') + 400 and
               'data-idea-newline' in h and '2 more ideas for Athens' in h
               and 'value="%d" checked' % bm.pk not in h,
               'NEW: the two it brought are marked New, with a line at the '
               'top and the first one to go to')
            ok(h.split('Temple of Olympian Zeus')[1][:120].count(
                'data-idea-new') == 0,
               '  the ones from before are not')
            hm = M.get('/travel/m/trip/%d/ideas/' % t.pk).content.decode()
            ok(hm.count('data-idea-new>') == 2,
               '  the same on the phone')
            fake.more = False
            MORE[:] = [dict(name='Lycabettus Hill', interest='musts',
                            blurb='f')]
            fake.more = True
            A.post('/travel/%d/ideas/more/' % t.pk, {'more': 'Athens'})
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok(h.count('data-idea-new>') == 1 and
               h.split('Benaki Museum')[1][:120].count('data-idea-new') == 0,
               'EACH TIME: the next Show me more moves New to what it '
               'brought')
            from travel.models import Place
            p = Place.objects.create(trip=t, name='Hagia Sophia',
                                     lookup='waiting')
            h = A.get('/travel/%d/wish-list/?added=1' % t.pk
                      ).content.decode()
            ok('data-lookup-refresh' in h and 'updates by itself' in h,
               'LOOKING IT UP: the page asks again, and says it will')
            hm = M.get('/travel/m/trip/%d/?tab=wish' % t.pk).content.decode()
            ok('data-lookup-refresh' in hm, '  on the phone too')
            p.lookup = 'found'
            p.save()
            h = A.get('/travel/%d/wish-list/?added=1' % t.pk
                      ).content.decode()
            ok('data-lookup-refresh' not in h and 'all looked up' in h,
               '  and stops when it is done: "all looked up"')
            p.lookup = 'waiting'
            p.save()
            Place.objects.filter(pk=p.pk).update(
                updated_at=p.updated_at - dt.timedelta(minutes=30))
            h = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok('data-lookup-refresh' not in h,
               '  one stuck for half an hour does not keep it asking')
            # ---- the calendar
            from travel import calendar_view as CV
            today = dt.date.today()
            first = today.replace(day=1)
            mid = first + dt.timedelta(days=9)
            cal_t = Trip.objects.create(owner=u, name='TV14 Calendar trip')
            Booking.objects.create(trip=cal_t, added_by=u, kind='flight',
                                   title='CY1', start_date=mid,
                                   start_time=dt.time(8),
                                   end_date=mid, end_time=dt.time(10))
            Booking.objects.create(trip=cal_t, added_by=u, kind='stay',
                                   title='Hotel', city='Athens',
                                   start_date=mid,
                                   end_date=mid + dt.timedelta(days=4))
            Trip.objects.create(owner=u, name='TV14 No dates')
            h = A.get('/travel/').content.decode()
            ok('data-view-switch' in h and 'data-calendar' not in h,
               'CALENDAR: List | Calendar on Travel; the list first')
            r = A.get('/travel/?view=calendar')
            h = r.content.decode()
            ok('data-calendar' in h and today.strftime('%B %Y') in h and
               'aria-current="date"' in h and r.cookies.get(
                   'tv_view').value == 'calendar',
               '  Calendar: this month, today marked - and remembered')
            ok('data-cal-bar="%d"' % cal_t.pk in h and
               '/travel/%d/itinerary/' % cal_t.pk in h and
               'data-cal-plane' in h,
               '  the trip as a bar that opens its itinerary; a plane on '
               'the day it flies')
            ok('TV14 No dates' in h and 'no dates' in h,
               '  a trip with no dates is named under it')
            h = A.get('/travel/').content.decode()
            ok('data-calendar' in h,
               '  next time Travel opens on the calendar')
            nxt = (first + dt.timedelta(days=32)).replace(day=1)
            h = A.get('/travel/?month=%s' % nxt.strftime('%Y-%m')
                      ).content.decode()
            ok(nxt.strftime('%B %Y') in h and 'data-cal-today' in h,
               '  another month, with Today to come back')
            h = A.get('/travel/?month=1999-99').content.decode()
            ok(today.strftime('%B %Y') in h,
               '  a month that makes no sense: this month')
            hm = M.get('/travel/m/trips/?view=calendar').content.decode()
            ok('data-calendar' in hm and 'data-cal-list' in hm and
               '/travel/m/trip/%d/?tab=itinerary' % cal_t.pk in hm,
               '  the phone: the month, the trips listed under it, a tap '
               'opens the itinerary')
            A.get('/travel/?view=list')
            ok('data-calendar' not in A.get('/travel/').content.decode(),
               '  List goes back, and that is remembered too')
            NT = lambda pk, s, e: NS(pk=pk, name='t%d' % pk, start=s,  # noqa
                                     end=e, bookings=NS(all=lambda: []))
            d1 = dt.date(2027, 3, 1)
            got = CV.build([NT(1, dt.date(2027, 3, 3), dt.date(2027, 3, 10)),
                            NT(2, dt.date(2027, 3, 5), dt.date(2027, 3, 6)),
                            NT(3, dt.date(2027, 3, 12), dt.date(2027, 3, 13))],
                           d1, dt.date(2027, 3, 4))
            w = got['weeks'][0]
            lanes = {b['trip'].pk: b['lane'] for b in w['bars']}
            ok(lanes[1] != lanes[2] and w['rows'] == 2 and
               [b for b in got['weeks'][1]['bars'] if b['trip'].pk == 1][0][
                   'more_left'],
               '  trips that overlap stack; one that runs on says so')
            ok([b['past'] for b in w['bars'] if b['trip'].pk == 2] ==
               [False] and got['prev'] == '2027-02' and
               got['next'] == '2027-04',
               '  past and next months worked out')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok("anchor='new'" not in was(J(TA, 'views_ideas.py')),
       'before this round: Show me more lost the ticks and marked nothing')
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
