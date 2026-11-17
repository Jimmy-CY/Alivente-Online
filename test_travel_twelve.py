# -*- coding: utf-8 -*-
"""test_travel_twelve.py - round TR-12, 17 Nov 2026.

RELEASE 93 - TRAVEL: SUGGEST THINGS TO DO.
Demetri, 17 Nov: "Can we add another button to Things to Do. Basically,
based on the city where you are going to be (if multiple cities the user
can decide if all or selected city/cities). Then the system must do a
search and identify the top Things to Do for that destination ... the
user should be given the opportunity to select what they like ... The
user must then read up on these (short blurb) and then tick which ones
they want to add to their Things to Do." And: "It must also not repeat
suggestions, if these are already in the Things to Do." Decided: the AI's
own knowledge; no restaurants; 10 to 12 a city with Show more; saved on
the trip; no photos for now.
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

SUFFIX = '.bak_travel12'
ME = 'test_travel_twelve.py'
PATCHER = 'apply_travel_twelve.py'
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
ok('class IdeaRun(models.Model):' in md and 'class Idea(models.Model):' in md
   and os.path.isfile(J(TA, 'migrations', '0010_suggestions.py')),
   'MODEL: a run of suggestions and each suggestion kept on the trip (0010)')
pl = read(J(TA, 'places.py'))
k = pl.find('def call_ideas(')
ok("SUGGEST_MODEL = os.environ.get('TRAVEL_SUGGEST_MODEL', MODEL)" in pl
   and k > 0 and 'web_search' not in pl[k:pl.find('def start_many(')],
   'AI: in the file that already talks to Claude; its own knowledge, no '
   'web search (agreed 17 Nov)')
ok('No restaurants' in pl and 'Never suggest anything in the list of what '
   'to leave out' in pl,
   '  told: no restaurants, and never what is on the list')
u = read(J(TA, 'urls.py'))
ok(all("name='%s'" % n in u for n in (
    'ideas_setup', 'ideas', 'ideas_add', 'ideas_hide', 'ideas_more',
    'm_ideas_setup', 'm_ideas', 'm_ideas_add', 'm_ideas_hide',
    'm_ideas_more')),
   'routes: setup, the suggestions, add, hide, more - computer and phone')
for f in ('ideas_setup.html', 'ideas_working.html', 'ideas.html'):
    ok(os.path.isfile(J(TT, f)) and os.path.isfile(J(TT, 'm', f)),
       '  %s on the computer and the phone' % f)
ok('data-travel-help' in read(J(TT, 'ideas_setup.html')) and
   'data-travel-help' in read(J(TT, 'ideas.html')),
   'Help on the new computer pages')
ok('data-idea-suggest' in read(J(TT, 'trip.html')) and 'data-idea-suggest'
   in read(J(TT, 'm', 'trip.html')),
   'THINGS TO DO: Suggest things to do beside + Things to do')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('<strong>Suggest things to do.</strong>' in hp and
   '<strong>Not interested</strong>' in hp and
   '<b>Suggest things to do</b>' in read(J(TT, 'm', 'help.html')),
   'HELP: on the computer and the phone')
ph = read(J(TA, 'phone.py'))
ok("SW_VERSION = 'tv12-1'" in ph and '?v=tv12-1' in read(
    J(TT, 'm', 'base.html')),
   'the phone fetches the new style (tv12-1)')

# ==========================================================================
head('2. THE RULES (travel/ideas.py)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from types import SimpleNamespace as NS                     # noqa: E402
from travel import ideas as ID, places as PP                # noqa: E402

for a, b in (('Gulbenkian Museum', 'Museu Calouste Gulbenkian'),
             ('Jeronimos Monastery', 'Mosteiro dos Jeronimos'),
             ('Time Out Market', 'Time Out Market Lisboa'),
             ('Sagrada Familia', 'Basilica de la Sagrada Familia'),
             ('Belem Tower', 'Torre de Belem')):
    ok(ID.same(a, b, PP.name_words('Lisbon')),
       'THE SAME PLACE: "%s" and "%s"' % (a, b))
for a, b in (('Belem Tower', 'Belem Cultural Centre'),
             ('Park Guell', 'Palau Guell'),
             ('Alfama', 'Bairro Alto')):
    ok(not ID.same(a, b), 'NOT THE SAME: "%s" and "%s"' % (a, b))
D0 = dt.date(2027, 6, 11)


def bk(kind, sd, ed, city='', title='Hotel', address='', to_place='',
       status='booked'):
    return NS(kind=kind, start_date=sd, end_date=ed, city=city,
              title=title, address=address, to_place=to_place,
              from_place='', status=status, country='')


cs = ID.cities_of(NS(), [
    bk('stay', D0 + dt.timedelta(days=4), D0 + dt.timedelta(days=6),
       title='Porto Hotel', address='Rua X 1, 4050 Porto, Portugal'),
    bk('stay', D0, D0 + dt.timedelta(days=2), city='Lisbon'),
    bk('stay', D0 + dt.timedelta(days=2), D0 + dt.timedelta(days=4),
       city='Lisbon', title='Second hotel'),
    bk('stay', D0, D0 + dt.timedelta(days=9), city='Madrid',
       status='cancelled')])
ok([c['name'] for c in cs] == ['Lisbon', 'Porto'] and cs[0]['nights'] == 4
   and cs[1]['nights'] == 2,
   'THE CITIES: from the hotel stays, first night first, nights added up; '
   'a city from the address; a cancelled stay is not one',
   [(c['name'], c['nights']) for c in cs])
cs = ID.cities_of(NS(), [bk('flight', D0, D0, to_place='Lisbon (LIS)'),
                         bk('flight', D0 + dt.timedelta(days=5), None,
                            to_place='Larnaca (LCA)')])
ok([c['name'] for c in cs] == ['Lisbon'],
   'NO HOTEL YET: where the flights go - not home', cs)

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, Idea, IdeaRun, Place, Trip
    connection.ensure_connection()
    IdeaRun.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

ANSWERS = {
    'Lisbon': [
        dict(name='Belem Tower', interest='musts', kind='sight',
             area='Belem', blurb='A 16th-century fort on the river.',
             visit='45 min', price='about EUR 8', book=True),
        dict(name='Mosteiro dos Jeronimos', interest='history',
             blurb='Already on the list, under another name.'),
        dict(name='Time Out Market Lisboa', interest='markets',
             kind='food', blurb='Already on the list.'),
        dict(name='Cervejaria Ramiro', interest='musts', kind='food',
             blurb='A restaurant - never.'),
        dict(name='Alfama', interest='streets', area='Old town',
             blurb='The oldest quarter.', note='Santo Antonio parties'),
        dict(name='Calouste Gulbenkian Museum', interest='museums',
             kind='museum', blurb='A private collection.',
             note='Closed Tue'),
        dict(name='Miradouro da Senhora do Monte', interest='views',
             blurb='The highest viewpoint.')],
    'Porto': [
        dict(name='Livraria Lello', interest='musts', blurb='The bookshop.',
             book=True),
        dict(name='Ribeira', interest='streets', blurb='The riverfront.')],
}
MORE = [dict(name='Torre de Belem', interest='musts', blurb='Again.'),
        dict(name='National Tile Museum', interest='museums',
             blurb='Azulejos.'),
        dict(name='LX Factory', interest='streets', blurb='A mill.')]


class Fake(object):
    def __init__(self):
        self.messages = self
        self.calls = []
        self.more = False

    def create(self, **kw):
        self.calls.append(kw)
        text = kw['messages'][0]['content']
        city = text.split('\n')[0][6:].split(',')[0]
        got = MORE if self.more else ANSWERS.get(city, [])
        return NS(content=[NS(type='tool_use', name='record_ideas',
                              input={'ideas': got})])


PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace
    fake = Fake()
    PP._client = lambda c: fake
    PP.call = lambda place, client=None: {
        'found': True, 'sure': True, 'name': place.name,
        'address': 'Somewhere 1, Lisboa'}
    PP.SYNC = True
    ID.SYNC = True

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('tv12a', 'tv12a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            Dd = [dt.date.today() + dt.timedelta(days=30 + i)
                  for i in range(7)]
            t = Trip.objects.create(owner=u, name='TV12 Lisbon and Porto')
            mk = dict(trip=t, added_by=u)
            Booking.objects.create(kind='stay', title='Hotel Chiado',
                                   city='Lisbon', start_date=Dd[0],
                                   end_date=Dd[4], **mk)
            Booking.objects.create(kind='stay', title='Hotel Ribeira',
                                   city='Porto', start_date=Dd[4],
                                   end_date=Dd[6], **mk)
            Place.objects.create(trip=t, name='Jeronimos Monastery',
                                 kind='museum')
            Place.objects.create(trip=t, name='Time Out Market',
                                 kind='food', day=Dd[1])
            h = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok('data-idea-suggest' in h and 'Suggest things to do' in h,
               'THINGS TO DO: the Suggest things to do button')
            h = M.get('/travel/m/trip/%d/?tab=wish' % t.pk).content.decode()
            ok('data-idea-suggest' in h and 'data-add-place' in h,
               '  and on the phone, under + Things to do')
            r = A.get('/travel/%d/ideas/' % t.pk)
            ok(r.status_code == 302 and r['Location'].endswith(
                '/travel/%d/ideas/new/' % t.pk),
               'NO SUGGESTIONS YET: straight to the questions')
            h = A.get('/travel/%d/ideas/new/' % t.pk).content.decode()
            ok(h.count('data-idea-city') == 2 and 'Lisbon' in h and
               '4 nights' in h and 'Porto' in h and '2 nights' in h and
               'name="other"' in h,
               'STEP 1: Lisbon (4 nights) and Porto (2 nights) from the '
               'hotels, + Another city')
            ok(h.count('data-idea-interest') == 9 and 'name="style"' in h
               and 'name="extra"' in h and 'Restaurants are left out' in h,
               'STEP 2: nine interests, famous or local, anything else; '
               'restaurants left out')
            hm = M.get('/travel/m/trip/%d/ideas/new/' % t.pk
                       ).content.decode()
            ok('data-idea-steps' in hm and hm.count('data-idea-step=') == 2,
               '  on the phone: two steps')
            r = A.post('/travel/%d/ideas/new/' % t.pk, {
                'city': ['Lisbon', 'Porto'], 'other': 'Sintra',
                'interest': ['musts', 'museums', 'streets', 'views',
                             'markets', 'history'],
                'style': 'mix', 'extra': 'not long queues'})
            ok(r.status_code == 302 and r['Location'].endswith(
                '/travel/%d/ideas/' % t.pk), 'ASKED: on to the suggestions')
            job = IdeaRun.objects.get(trip=t)
            ok(job.status == 'ready' and set(job.progress) == {
                'Lisbon', 'Porto', 'Sintra'} and len(fake.calls) == 3,
               '  one question per city - Sintra too', job.progress)
            c0 = fake.calls[0]
            ask = c0['messages'][0]['content']
            ok('Jeronimos Monastery' in ask and 'Time Out Market' in ask and
               'web_search' not in str(c0['tools']) and
               c0['model'] == PP.SUGGEST_MODEL and 'not long queues' in ask
               and '4 nights' in ask,
               'THE QUESTION: what is on the list to leave out, the dates '
               'and nights, their own line; no web search', ask)
            names = list(t.ideas.values_list('name', flat=True))
            ok('Belem Tower' in names and 'Alfama' in names and
               'Mosteiro dos Jeronimos' not in names and
               'Time Out Market Lisboa' not in names,
               'NEVER WHAT IS ON THE LIST, even if the AI forgets: '
               'Mosteiro dos Jeronimos and Time Out Market Lisboa dropped',
               names)
            ok('Cervejaria Ramiro' not in names,
               'NO RESTAURANTS: one the AI sent anyway is dropped')
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            bt = Idea.objects.get(trip=t, name='Belem Tower')
            ok(h.count('name="idea"') == 6 and 'A 16th-century fort' in h
               and 'Book ahead' in h and '45 min' in h and
               'Closed Tue' in h and 'View on Google Maps' in h and
               'google.com/maps/search' in h,
               'THE SUGGESTIONS: 6 to tick, each with its blurb, time, '
               'price, Book ahead, a note and Google Maps')
            ok('Show me more for Lisbon' in h and 'Show me more for Porto'
               in h and 'data-idea-hide' in h and 'data-idea-add' in h,
               '  Not interested, Show me more per city, Add')
            ok(h.find('>Lisbon<') < h.find('>Porto<') and
               h.find('Must-sees') < h.find('Museums &amp; galleries'),
               '  by city, then by what you like')
            ok('No ideas for Sintra' in h,
               '  a city with nothing back says so, with Try again')
            hm = M.get('/travel/m/trip/%d/ideas/' % t.pk).content.decode()
            ok(hm.count('name="idea"') == 6 and 'data-idea-add' in hm,
               '  the same on the phone')
            al = Idea.objects.get(trip=t, name='Alfama')
            r = A.post('/travel/%d/ideas/hide/' % t.pk, {
                'hide': str(bt.pk), 'idea': [str(al.pk)]})
            bt.refresh_from_db()
            ok(bt.state == 'hidden' and 't=%d' % al.pk in r['Location'],
               'NOT INTERESTED: hidden - and what was ticked stays ticked')
            h = A.get(r['Location']).content.decode()
            ok('Belem Tower' not in h and 'hidden as Not interested' in h
               and 'value="%d" checked' % al.pk in h,
               '  gone from the list, "1 hidden - Show them"')
            h = A.get('/travel/%d/ideas/?hidden=1' % t.pk).content.decode()
            ok('Belem Tower' in h and 'data-idea-unhide' in h,
               'SHOW THEM: hidden ones, with Bring it back')
            fake.more = True
            n0 = len(fake.calls)
            A.post('/travel/%d/ideas/more/' % t.pk, {'more': 'Lisbon'})
            ask = fake.calls[n0]['messages'][0]['content']
            names = list(t.ideas.values_list('name', flat=True))
            ok(len(fake.calls) == n0 + 1 and 'Belem Tower' in ask and
               'Alfama' in ask and 'National Tile Museum' in names and
               'Torre de Belem' not in names and 'Alfama' in names,
               'SHOW ME MORE: one city; shown and hidden ones named to '
               'leave out; Torre de Belem (= the hidden Belem Tower) never '
               'shown; the rest kept', names)
            fake.more = False
            gb = Idea.objects.get(trip=t, name='Calouste Gulbenkian Museum')
            r = A.post('/travel/%d/ideas/add/' % t.pk,
                       {'idea': [str(al.pk), str(gb.pk)]})
            ok(r.status_code == 302 and 'added=2' in r['Location'],
               'ADD: two ticked, back to Things to do')
            p1 = Place.objects.get(trip=t, name='Alfama')
            ok(p1.lookup == 'found' and p1.address == 'Somewhere 1, Lisboa'
               and p1.about == 'The oldest quarter.' and p1.day is None and
               p1.query == 'Alfama, Lisbon',
               '  each a place in Things to do, looked up on the web like '
               'one typed in (name and city), its blurb kept')
            al.refresh_from_db()
            ok(al.state == 'added' and al.place_id == p1.pk,
               '  the suggestion knows it was added')
            h = A.get(r['Location']).content.decode()
            ok('data-idea-added' in h and '2 added to Things to do' in h and
               'Back to suggestions' in h and 'left to look at' in h,
               '  "2 added to Things to do" - and Your suggestions, N left')
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok('name="idea" value="%d"' % al.pk not in h and '2 added' in h,
               '  no longer to tick')
            r = M.post('/travel/m/trip/%d/ideas/add/' % t.pk, {})
            ok(r.status_code == 302 and '/m/' in r['Location'],
               'NOTHING TICKED: back, with a word - on the phone too')
            lt = Idea.objects.get(trip=t, name='Livraria Lello')
            n0 = len(fake.calls)
            A.post('/travel/%d/ideas/new/' % t.pk, {
                'city': ['Lisbon'], 'interest': ['musts'], 'style': 'local'})
            names = set(t.ideas.values_list('name', flat=True))
            ask = fake.calls[n0]['messages'][0]['content']
            ok(not Idea.objects.filter(pk=lt.pk).exists() and 'Belem Tower'
               in names and 'Alfama' in names and 'local' in ask,
               'CHANGE WHAT YOU LIKE: the untouched ones make way; hidden '
               'and added are kept (and never suggested again)')
            ok(t.idea_runs.first().answers['style'] == 'local' and
               'value="local" checked' in A.get(
                   '/travel/%d/ideas/new/' % t.pk).content.decode(),
               '  and the answers are remembered for next time')
            other = User.objects.create_user('tv12b', 'tv12b@example.com',
                                             'x')
            other.user_permissions.add(perm)
            B2 = Client(SERVER_NAME='localhost')
            B2.force_login(other)
            ok(B2.get('/travel/%d/ideas/' % t.pk).status_code == 404 and
               B2.post('/travel/%d/ideas/add/' % t.pk,
                       {'idea': [str(bt.pk)]}).status_code == 404,
               'SOMEONE ELSE\'S trip: no suggestions, nothing added')
            ok(A.get('/travel/%d/ideas/add/' % t.pk).status_code == 405 and
               A.get('/travel/%d/ideas/hide/' % t.pk).status_code == 405 and
               A.get('/travel/%d/ideas/more/' % t.pk).status_code == 405,
               'add, hide, more: POST only')
            job = IdeaRun.objects.create(trip=t, status='working',
                                         progress={'Lisbon': 'working'})
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            ok('data-idea-working' in h and 'Thinking about what you like'
               in h and 'location.reload' in h,
               'WHILE IT WORKS: city by city; the page asks again')
            IdeaRun.objects.filter(pk=job.pk).update(
                updated_at=job.updated_at - dt.timedelta(minutes=10))
            h = A.get('/travel/%d/ideas/' % t.pk).content.decode()
            job.refresh_from_db()
            ok(job.status == 'failed' and 'data-idea-working' not in h,
               '  one stuck for ten minutes (a restart) is given up')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('class Idea(' not in was(J(TA, 'models.py')),
       'before this round: no suggestions - every thing to do typed in')
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
