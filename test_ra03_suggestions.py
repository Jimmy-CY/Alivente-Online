# -*- coding: utf-8 -*-
"""test_ra03_suggestions.py - round RA03, 19 Nov 2026.

RELEASE RA03 - TRAVEL: RESTAURANTS AND CAFES, CHECKED ON GOOGLE, GREYED
OUT WHEN YOU CANNOT GO; SELECT AND DELETE SEVERAL THINGS TO DO.
Demetri, 19 Nov: "I need two new categories - 1. Cafes and 2. Restaurants
... from a list of top 10"; "closed or unavailable on a Tuesday should
display, but should be greyed out"; "how many km from the city centre
... must be greyed out ... All greyed out things to do should still be
selectable"; then: check on Google; from the city centre; day trips
never limited but greyed out past the km; greyed only when EVERY day is
closed; ten of each with rating and price; Show me more counts the grey
ones; "if I wanted to do a multi-select and delete of the things to do".
No test here ever calls Google or Claude.
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

SUFFIX = '.bak_ra03'
ME = 'test_ra03_suggestions.py'
PATCHER = 'apply_ra03_suggestions.py'
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
from types import SimpleNamespace as NS                     # noqa: E402
TA = J(ROOT, 'travel')
TT = J(TA, 'templates', 'travel')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from travel import gplaces as G, ideas as ID, places as PP   # noqa: E402
G.OFF = True

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
ok(('restaurants', 'Restaurants') == ID.INTERESTS[-2][:2] and
   ('cafes', 'Cafés') == ID.INTERESTS[-1][:2] and ID.PER_FOOD == 10,
   'TWO NEW CATEGORIES: Restaurants and Cafes, ten of each a city')
pl = read(J(TA, 'places.py'))
ok('FOOD_SYSTEM = ' in pl and 'No restaurants' in pl and
   "km=None, food=''" in pl,
   '  asked for on their own; the sights still never include a meal')
ok(os.path.isfile(J(TA, 'migrations', '0011_idea_google.py')),
   'MIGRATION 0011: each suggestion keeps what Google said')
gp = read(J(TA, 'gplaces.py'))
ok("KEY_ENV = 'GOOGLE_PLACES_KEY'" in gp and
   "startswith('test_')" in gp and 'print(' not in gp,
   'GOOGLE: the key from Railway; never from a test; never printed')
sys.argv[0] = 'test_x.py'
os.environ['GOOGLE_PLACES_KEY'] = 'not-a-real-key'
G.OFF = False
ok(not G.enabled(), '  a test_*.py script has no key, even with one set')
G.OFF = True
del os.environ['GOOGLE_PLACES_KEY']
ch = read(J(TT, '_ideas_choices.html'))
ok('name="km"' in ch and 'data-km=' in ch and
   'Restaurants are left out' not in ch,
   'THE KM BOX before searching, with quick picks')
cd = read(J(TT, '_ideas_card.html'))
ok("is-dim" in cd and 'data-idea-why' in cd and 'data-idea-meta' in cd and
   'name="idea"' in cd,
   'A GREYED CARD: why, rating, price, distance - and still tickable')

# ==========================================================================
head('2. THE RULES (no database, no Google)')
# ==========================================================================
ok(G.open_days({'periods': [{'open': {'day': 1, 'hour': 9}},
                            {'open': {'day': 3, 'hour': 9}}]}) == {1, 3}
   and G.open_days({'periods': [{'open': {'day': 0, 'hour': 0,
                                           'minute': 0}}]}) == set(range(7))
   and G.open_days({}) is None,
   "GOOGLE'S DAYS: the days it opens; round the clock is every day; "
   'unknown is None')
s = G.shape({'id': 'X', 'displayName': {'text': 'Karamanlidika'},
             'location': {'latitude': 37.98, 'longitude': 23.72},
             'businessStatus': 'OPERATIONAL', 'rating': 4.7,
             'userRatingCount': 2300, 'priceLevel': 'PRICE_LEVEL_MODERATE'})
ok(s['price'] == '€€' and s['rating'] == 4.7 and s['gid'] == 'X',
   '  price level as euro signs')
d = G.km((37.9755, 23.7348), (37.6502, 24.0249))
ok(40 < d < 50, '  Athens to Sounion as the crow flies: %.0f km' % d)
D = dt.date
TUE = D(2026, 11, 10)
ok(ID.closed_words([TUE], 'Athens') ==
   "Closed on Tuesdays - you're in Athens only on Tue 10 Nov",
   'THE WORDS: "Closed on Tuesdays - you\'re in Athens only on Tue 10 Nov"')
ok(ID.closed_words([TUE - dt.timedelta(days=1), TUE], 'Athens') ==
   "Closed on Mondays and Tuesdays - the only days you're in Athens",
   '  and for two days')

FOUND = {}


def fake_search(text, near=None, opener=None):
    return FOUND.get(text.split(',')[0])


G.search = fake_search
G.enabled = lambda: True
CENTRE = (37.9755, 23.7348)


def idea(name, interest='museums'):
    from travel.models import Idea as _I
    return _I(name=name, city='Athens', interest=interest)


def found(**kw):
    f = {'gid': 'g', 'lat': 37.97, 'lng': 23.73, 'status': 'OPERATIONAL',
         'rating': None, 'ratings': None, 'price': '', 'open_days': None}
    f.update(kw)
    return f


FOUND['Benaki'] = found(open_days={0, 3, 4, 5, 6})          # shut Mon, Tue
FOUND['Acropolis'] = found(open_days={1, 2, 3})
FOUND['Gone'] = found(status='CLOSED_PERMANENTLY')
FOUND['Shut'] = found(status='CLOSED_TEMPORARILY')
FOUND['Niarchos'] = found(lat=37.94, lng=23.69)
FOUND['Sounion'] = found(lat=37.6502, lng=24.0249)
FOUND['Karamanlidika'] = found(rating=4.7, ratings=2300, price='€€')
days = [TUE - dt.timedelta(days=1), TUE]
i = idea('Benaki')
ok(ID.check(i, CENTRE, days, 5) and i.flag == 'closed' and
   'Closed on Mondays and Tuesdays' in i.flag_text,
   'CLOSED ON EVERY DAY YOU ARE THERE: greyed out, with why')
i = idea('Acropolis')
ok(ID.check(i, CENTRE, days, 5) and i.flag == '' and i.checked,
   'OPEN ON ONE OF YOUR DAYS: not greyed out')
ok(not ID.check(idea('Gone'), CENTRE, days, 5),
   'CLOSED FOR GOOD: left out')
i = idea('Shut')
ok(ID.check(i, CENTRE, days, 5) and i.flag == 'temp',
   'TEMPORARILY CLOSED: greyed out')
i = idea('Niarchos')
ok(ID.check(i, CENTRE, days, 5) and i.flag == 'far' and
   'outside your 5 km' in i.flag_text and i.dist_km > 5,
   'FURTHER THAN YOUR KM: greyed out - "%s"' % i.flag_text)
i = idea('Niarchos')
ok(ID.check(i, CENTRE, days, None) and i.flag == '',
   '  no km asked for: not greyed out')
i = idea('Sounion', 'daytrips')
ok(ID.check(i, CENTRE, days, 5) and i.flag == 'far' and
   i.flag_text.startswith('Day trip - '),
   'A DAY TRIP past the km: shown, greyed out, with how far')
i = idea('Karamanlidika', 'restaurants')
ok(ID.check(i, CENTRE, days, 5) and i.rating == 4.7 and
   i.price_level == '€€' and i.dist_km is not None,
   'A RESTAURANT: rating, price level, distance')
i = idea('Nowhere')
ok(ID.check(i, CENTRE, days, 5) and not i.checked and i.flag == '',
   'NOT FOUND ON GOOGLE: shown as it came, unchecked')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from pages.models import UserProfile
    from travel.models import Booking, Idea, Place, Trip
    connection.ensure_connection()
    Idea.objects.filter(checked=True).exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')


class Fake(object):
    def __init__(self):
        self.messages = self
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        food = 'restaurants' if 'best restaurants' in kw['system'] else (
            'cafes' if 'best cafes' in kw['system'] else '')
        if food == 'restaurants':
            got = [dict(name='Karamanlidika', interest='restaurants',
                        kind='food', blurb='Meze.')]
        elif food == 'cafes':
            got = [dict(name='Little Tree', interest='cafes', kind='food',
                        blurb='Books and coffee.')]
        else:
            got = [dict(name='Benaki', interest='museums', blurb='Art.'),
                   dict(name='Acropolis', interest='musts', blurb='Rock.'),
                   dict(name='Gone', interest='musts', blurb='Shut.'),
                   dict(name='Niarchos', interest='musts', blurb='Far.'),
                   dict(name='Taverna X', interest='musts', kind='food',
                        blurb='A meal - never among the sights.')]
        return NS(content=[NS(type='tool_use', name='record_ideas',
                              input={'ideas': got})])


if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace
    fake = Fake()
    PP._client = lambda c: fake
    PP.SYNC = True
    ID.SYNC = True

    def _no(*a, **k):
        raise PP.LookupError_('not in tests')
    PP.call_details = _no
    PP.call = lambda place, client=None: {'found': False}
    FOUND['Athens'] = found(lat=CENTRE[0], lng=CENTRE[1])

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('ra03a', 'ra03a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            mon = timezone.localdate() + dt.timedelta(days=30)
            mon -= dt.timedelta(days=mon.weekday())
            t = Trip.objects.create(owner=u, name='RA03 Athens')
            Booking.objects.create(trip=t, added_by=u, kind='stay',
                                   title='Hotel Plaka', city='Athens',
                                   start_date=mon,
                                   end_date=mon + dt.timedelta(days=1))
            h = A.get('/travel/%d/ideas/new/' % t.pk).content.decode()
            ok('name="km"' in h and 'value="restaurants"' in h and
               'value="cafes"' in h,
               'THE QUESTIONS: Restaurants, Cafes and the km box')
            A.post('/travel/%d/ideas/new/' % t.pk, {
                'city': 'Athens', 'interest': ['musts', 'museums',
                                               'restaurants', 'cafes'],
                'style': 'mix', 'km': '5'})
            job = t.idea_runs.first()
            ok(job.answers.get('km') == 5 and job.answers.get('checked'),
               '  the km is kept with the run, and it was checked')
            sysm = [c['system'] for c in fake.calls]
            ok(len(fake.calls) == 3 and
               sum('best restaurants' in x for x in sysm) == 1 and
               sum('best cafes' in x for x in sysm) == 1 and
               'within about 5 km' in fake.calls[0]['messages'][0][
                   'content'],
               'THREE ASKS: the sights, the restaurants, the cafes - each '
               'told the km')
            names = dict((i.name, i) for i in t.ideas.all())
            ok('Gone' not in names and 'Taverna X' not in names,
               '  closed for good left out; no meal among the sights')
            ok(names['Benaki'].flag == 'closed' and
               names['Niarchos'].flag == 'far' and
               names['Acropolis'].flag == '' and
               names['Karamanlidika'].interest == 'restaurants' and
               names['Little Tree'].interest == 'cafes',
               '  marked: closed on your days, too far, fine; food in its '
               'own groups')
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok(h.count('data-idea-flag=') == 2 and
               'Closed on Mondays and Tuesdays' in h and
               'outside your 5 km' in h and
               'value="%d"' % names['Benaki'].pk in h,
               'THE PAGE: two greyed out, each saying why, still tickable')
            ok(h.index('data-idea="%d"' % names['Acropolis'].pk) <
               h.index('data-idea="%d"' % names['Niarchos'].pk),
               '  greyed ones last in their group')
            ok('Restaurants' in h and '&#9733; 4.7' in h and '€€' in h,
               '  restaurants with rating and price')
            h = M.get('/travel/m/trip/%d/ideas/' % t.pk).content.decode()
            ok('is-dim' in h and 'data-idea-why' in h,
               'THE PHONE: the same greyed out cards')
            # ---- Select and Delete
            A.post('/travel/%d/ideas/add/' % t.pk,
                   {'idea': [names['Acropolis'].pk, names['Benaki'].pk]})
            ps = list(t.places.order_by('pk'))
            other = Trip.objects.create(owner=u, name='RA03 other')
            keep = Place.objects.create(trip=other, name='Keep me')
            h = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok('data-select-start' in h and h.count(
                'name="p" value=') == len(ps) and
               'data-select-bar' in h,
               'SELECT: a tick beside each thing to do, and the bar')
            r = A.post('/travel/%d/places/delete/' % t.pk,
                       {'p': [ps[0].pk, keep.pk]})
            ok(r.status_code == 302 and not Place.objects.filter(
                pk=ps[0].pk).exists() and Place.objects.filter(
                pk=keep.pk).exists() and t.places.count() == len(ps) - 1,
               "DELETE: the ticked one goes; another trip's never")
            ok(not Idea.objects.filter(trip=t, name=ps[0].name).exists(),
               '  and it may be suggested again')
            h = M.get('/travel/m/trip/%d/?tab=wish' % t.pk).content.decode()
            ok('Select to delete' in h and 'm/%d/places/delete/' % t.pk
               in h, 'THE PHONE: Select to delete')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. HELP AND REGISTERED')
# ==========================================================================
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('<strong>Restaurants</strong> or <strong>Caf&eacute;s</strong>' in adm
   and 'How far from the centre?' in adm and '<em>greyed out</em>' in adm
   and 'Delete several things to do.' in adm,
   'HELP: the new categories, the km, greyed out, Select and Delete')
mh = read(J(TT, 'm', 'help.html'))
ok('greyed out' in mh and 'Select to delete' in mh, '  and on the phone')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
