# -*- coding: utf-8 -*-
"""test_travel_four.py - round TR-4, 15 Nov 2026.

RELEASE 85 - TRAVEL, STAGE 4: THE ITINERARY, THE WISH LIST, PLACES.
Demetri, 15 Nov: places with no booking (a museum, a garden) - typed,
pasted, or shared from Google Maps - looked up by "Claude searches the
web"; and "Should the Trip Name and the From and To Dates be based on
uploaded reservations?" (yes: the dates and countries follow the
bookings); New trip and the phone code only when asked for.
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

SUFFIX = '.bak_travel4'
ME = 'test_travel_four.py'
PATCHER = 'apply_travel_four.py'
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
u = read(J(TA, 'urls.py'))
ok("name='trip_itinerary'" in u and "name='trip_wishlist'" in u and
   "name='place_new'" in u and "name='m_place_new'" in u and
   "name='m_place_move'" in u,
   'routes: the itinerary, the wish list, places - on the phone under m/')
ok(os.path.isfile(J(TA, 'migrations', '0004_places.py')),
   'migration travel 0004: places, and where each booking is')
pl = read(J(TA, 'places.py'))
ok("MODEL = os.environ.get('TRAVEL_AI_MODEL', 'claude-sonnet-4-6')" in pl and
   "'type': 'web_search_20250305'" in pl and "'max_uses': SEARCHES" in pl,
   'Claude looks places up with web search - one model constant')
ok("'travel/places.py'" in read(J(ROOT, 'test_ai_models.py')),
   '  and the Anthropic census knows the call site')
vw = read(J(TA, 'views.py'))
ok('trip.by_bookings = bool(days)' in vw and
   'if days:\n        start, end = min(days), max(days)' in vw,
   'DATES FROM BOOKINGS: the bookings win once there are any')
tp = read(J(TT, 'trips.html'))
ok('{% if new_open %}' in tp and '{% if phone_qr %}' in tp and
   'data-phone-button' in tp,
   'the Travel page: New trip and the phone code only when asked for')
ph = read(J(TA, 'phone.py'))
ok("'orientation': 'portrait'," in ph and "SW_VERSION = 'tv" in ph and
   'tv-turn-90' in read(J(TA, 'assets', 'travel.js')) and
   'class="tv-holding"' in read(J(TT, 'm', 'passes.html')),
   'THE PASS DOES NOT FLIP: the installed app stays upright; elsewhere '
   'Passes is turned back')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('data-tab-slug="tr-plan"' in hp and 'The bookings set the dates' in hp
   and 'press <strong>Phone app</strong>' in hp,
   'HELP: Itinerary & Places; dates from bookings; the Phone app button')

# ==========================================================================
head('2. WHAT WAS TYPED OR SHARED - no database')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from travel import places as PL                             # noqa: E402

ok(PL.parse_query('Calouste Gulbenkian Museum\nAv. de Berna 45A, Lisboa\n'
                  'https://maps.app.goo.gl/AbC123') ==
   ('Calouste Gulbenkian Museum', 'Av. de Berna 45A, Lisboa',
    'https://maps.app.goo.gl/AbC123'),
   'GOOGLE MAPS on a phone shares name, address, link - all three kept')
ok(PL.parse_query('https://www.google.com/maps/place/Jardim+da+Estrela/'
                  '@38.71,-9.16,17z')[0] == 'Jardim da Estrela',
   '  a desktop Maps link gives its name')
ok(PL.parse_query('Gulbenkian museum') == ('Gulbenkian museum', '', '') and
   PL.parse_query('https://gulbenkian.pt/museu')[2] ==
   'https://gulbenkian.pt/museu',
   '  a name is a name; a website link is kept as the link')
ok(PL.is_maps('look https://maps.app.goo.gl/x') and
   not PL.is_maps('https://booking.com/x'),
   '  Maps links told apart from any other')


class _P(object):
    name = 'gulbenkian'
    kind = 'sight'
    address = 'Typed address 1'
    hours = price = website = about = ''
    lookup = 'waiting'
    lookup_note = ''


p = PL.fill(_P(), {'found': True, 'name': 'Calouste Gulbenkian Museum',
                   'kind': 'museum', 'address': 'Av. de Berna 45A',
                   'hours': '10:00-18:00, closed Tuesdays',
                   'price': 'about EUR 14', 'website': 'http://insecure',
                   'about': 'Book the garden cafe.'})
ok(p.name == 'Calouste Gulbenkian Museum' and p.kind == 'museum' and
   p.address == 'Typed address 1' and p.hours.startswith('10:00') and
   p.website == '' and p.lookup == 'found',
   'FOUND: filled in - never over what was typed; only an https site kept')
p = PL.fill(_P(), {'found': False})
ok(p.lookup == 'failed' and 'Could not tell' in p.lookup_note,
   '  not found: said so, and left as typed')

# ==========================================================================
head('3. DRIVEN - dates, places, the itinerary')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, Place, Trip
    connection.ensure_connection()
    Place.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')


class Block(object):
    def __init__(self, kind, name='', data=None):
        self.type = kind
        self.name = name
        self.input = data


class Fake(object):
    """Answers as Claude would after its web searches."""
    def __init__(self, data=None, error=None):
        self.data, self.error, self.sent = data, error, []
        self.messages = self

    def create(self, **kw):
        self.sent.append(kw)
        if self.error:
            raise self.error

        class R(object):
            pass
        r = R()
        r.content = [Block('server_tool_use', 'web_search', {'query': 'x'}),
                     Block('tool_use', 'record_place', self.data)]
        return r


if have_db:
    import datetime as dt
    from decimal import Decimal
    from django.conf import settings as _dj
    from django.utils import timezone
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    real_call = PL.call
    # TR-5 (Release 86) looks up a stay's missing address and times when
    # its trip is opened - never on the web from this suite.
    real_details = getattr(PL, 'call_details', None)

    def _no_web(b, client=None):
        raise PL.LookupError_('not from the test suite')
    if real_details is not None:
        PL.call_details = _no_web
    PL.SYNC = True
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            us = {}
            for n in ('tv4a', 'tv4b', 'tv4c'):
                usr = User.objects.create_user(n, n + '@example.com', 'x')
                usr.user_permissions.add(perm)
                us[n] = usr
            ws = ensure_workspace(us['tv4a'])
            for usr in us.values():
                UserProfile.objects.update_or_create(
                    user=usr, defaults={'workspace': ws})
            A = Client(SERVER_NAME='localhost')
            A.force_login(us['tv4a'])
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(us['tv4a'])
            C = Client(SERVER_NAME='localhost')
            C.force_login(us['tv4c'])

            h = A.get('/travel/').content.decode()
            ok('id="new-trip"' in h, 'NO TRIPS YET: the New trip form shows')
            day = timezone.localdate()
            t = Trip.objects.create(
                owner=us['tv4a'], name='TV4 Lisbon', countries='Paphos',
                start_date=day + dt.timedelta(days=30),
                end_date=day + dt.timedelta(days=32))
            t.shared_with.add(us['tv4b'])
            h = A.get('/travel/').content.decode()
            ok('id="new-trip"' not in h and 'data-phone-app' not in h and
               'data-phone-button' in h,
               'WITH TRIPS: no New trip form and no phone code until asked')
            ok('id="new-trip"' in A.get('/travel/?new=1').content.decode()
               and 'data-phone-app' in A.get('/travel/?phone=1').content
               .decode(), '  + New trip and Phone app open them')
            h = A.get('/travel/%d/' % t.pk).content.decode()
            d30 = (day + dt.timedelta(days=30))
            ok('%d %s' % (d30.day, d30.strftime('%b')) in h,
               'NO BOOKINGS: the typed dates stand (planning)')
            fl = Booking.objects.create(
                trip=t, kind='flight', title='TV4 TP 1307',
                start_date=day + dt.timedelta(days=10),
                start_time=dt.time(6, 40), added_by=us['tv4a'],
                country='Portugal', city='Lisbon')
            st = Booking.objects.create(
                trip=t, kind='stay', title='TV4 Casa',
                start_date=day + dt.timedelta(days=10),
                start_time=dt.time(15, 0),
                end_date=day + dt.timedelta(days=13), added_by=us['tv4a'],
                country='Portugal')
            Booking.objects.create(
                trip=t, kind='car', title='TV4 cancelled car',
                start_date=day + dt.timedelta(days=40), status='cancelled',
                added_by=us['tv4a'], country='Spain')
            from travel.views import span
            s, e = span(t, list(t.bookings.all()))
            ok(s == day + dt.timedelta(days=10) and
               e == day + dt.timedelta(days=13) and t.by_bookings and
               t.where == 'Portugal, Paphos',
               'BOOKINGS SET THE DATES: first start to last end, typed ones '
               'ignored, a cancelled one left out; countries from the '
               'bookings with the typed ones', (s, e, t.where))
            h = A.get('/travel/%d/edit/' % t.pk).content.decode()
            ok('data-dates-by-bookings' in h and 'set by its bookings' in h,
               '  the edit form says so instead of offering the dates')

            # ---- Add a place: Claude looks it up
            PL.call = lambda place, client=None: real_call(place, client=Fake({
                'found': True, 'name': 'Calouste Gulbenkian Museum',
                'kind': 'museum', 'address': 'Av. de Berna 45A, Lisboa',
                'hours': '10:00-18:00, closed Tuesdays',
                'price': 'about EUR 14 each',
                'website': 'https://gulbenkian.pt', 'about': 'Allow 2 hours.'}))
            r = A.post('/travel/%d/place/new/' % t.pk, {
                'q': 'Gulbenkian museum', 'lookup': '1',
                'day': (day + dt.timedelta(days=11)).isoformat(),
                'time': '10:30', 'notes': 'garden cafe'})
            g = Place.objects.get(trip=t)
            ok(r.status_code == 302 and g.lookup == 'found' and
               g.name == 'Calouste Gulbenkian Museum' and
               g.hours.startswith('10:00') and g.notes == 'garden cafe' and
               g.time == dt.time(10, 30) and g.added_by == us['tv4a'],
               'ADD A PLACE: looked up on the web, on its day at 10:30',
               (g.lookup, g.name))
            ok('gulbenkian.pt' in A.get('/travel/place/%d/' % g.pk).content
               .decode(), '  its page, with the website')
            PL.call = lambda place, client=None: real_call(
                place, client=Fake(error=RuntimeError(
                    'web_search tool is not enabled')))
            A.post('/travel/%d/place/new/' % t.pk, {'q': 'Jardim da Estrela',
                                                    'lookup': '1'})
            j = Place.objects.get(trip=t, name='Jardim da Estrela')
            ok(j.lookup == 'failed' and j.day is None and
               'Web search is not switched on' in j.lookup_note,
               'NOT FOUND: kept as typed, on the wish list, and why')
            ok(j.map_url.startswith('https://www.google.com/maps/search/') and
               'Jardim' in j.map_url, '  a Map button that searches for it')

            # ---- the itinerary
            h = A.get('/travel/%d/itinerary/' % t.pk).content.decode()
            ok(h.count('data-itinerary-day') == 4,
               'ITINERARY: every day of the trip, empty ones too')
            d11 = h.split('id="d%s"' % (day + dt.timedelta(days=11))
                          .strftime('%Y%m%d'), 1)[1].split('</section>')[0]
            ok('Staying at' in d11 and 'Calouste Gulbenkian Museum' in d11 and
               d11.index('Staying at') < d11.index('Gulbenkian'),
               '  a day: the stay you wake up in, then the museum at 10:30')
            d10 = h.split('id="d%s"' % (day + dt.timedelta(days=10))
                          .strftime('%Y%m%d'), 1)[1].split('</section>')[0]
            d13 = h.split('id="d%s"' % (day + dt.timedelta(days=13))
                          .strftime('%Y%m%d'), 1)[1].split('</section>')[0]
            ok('Check in' in d10 and 'Check out' in d13 and
               'TV4 TP 1307' in d10,
               '  the same stay says Check in, Staying at, Check out on its '
               'own days')
            h = A.get('/travel/%d/wish-list/' % t.pk).content.decode()
            ok(h.count('data-wish-item') == 1 and 'Jardim da Estrela' in h,
               'WISH LIST: the place with no day')
            A.post('/travel/place/%d/move/' % j.pk, {
                'day': (day + dt.timedelta(days=12)).isoformat()})
            j.refresh_from_db()
            ok(j.day == day + dt.timedelta(days=12) and j.time is None,
               '  Put on a day')
            A.post('/travel/place/%d/done/' % j.pk)
            j.refresh_from_db()
            ok(j.done, 'DONE when you have been')
            ok(C.get('/travel/place/%d/' % g.pk).status_code == 404 and
               C.post('/travel/place/%d/delete/' % g.pk).status_code == 404,
               'SOMEONE NOT ON THE TRIP cannot see or remove its places')
            B = Client(SERVER_NAME='localhost')
            B.force_login(us['tv4b'])
            ok(B.get('/travel/place/%d/' % g.pk).status_code == 200,
               '  someone it is shared with can')

            # ---- Demetri, 15 Nov: delete from the booking itself, and
            # boarding passes on the computer too.
            gone = Booking.objects.create(trip=t, kind='other',
                                          title='TV4 to delete',
                                          added_by=us['tv4a'])
            h = A.get('/travel/booking/%d/' % gone.pk).content.decode()
            ok('data-delete-booking' in h and
               'form="del-booking-view"' in h,
               'DELETE on the booking page, no Edit first')
            A.post('/travel/booking/%d/delete/' % gone.pk)
            ok(not Booking.objects.filter(pk=gone.pk).exists(),
               '  and it is deleted')
            from travel.inbox import keep_pass
            CODE = ('M1' + 'MANIAS/DIMITRIOS'.ljust(20) + 'E' + 'ABC123 ' +
                    'LCA' + 'LIS' + 'TP ' + '1307 ' + '186' + 'Y' + '012A' +
                    '0045 ' + '1' + '00')
            keep_pass(fl, {'pass_code': CODE, 'pass_format': 'aztec'},
                      us['tv4a'])
            h = A.get('/travel/passes/').content.decode()
            ok(h.count('data-pass ') == 1 and 'data-next' in h and
               'Dimitrios Manias' in h and '<svg xmlns' in h and
               'data-passes-button' in A.get('/travel/').content.decode(),
               'BOARDING PASSES ON THE COMPUTER: Travel -> Boarding passes, '
               'the next one marked')

            # ---- Demetri, 15 Nov: the return flight's price is on the
            # first flight - the second says so instead of nothing.
            o1 = Booking.objects.create(
                trip=t, kind='flight', title='TV4 out', reference='RET1',
                segment='FR 4519', start_date=day + dt.timedelta(days=10),
                amount=Decimal('289.97'), amount_eur=Decimal('289.97'),
                paid='paid', added_by=us['tv4a'])
            o2 = Booking.objects.create(
                trip=t, kind='flight', title='TV4 back', reference='ret 1',
                segment='FR 4518', start_date=day + dt.timedelta(days=13),
                added_by=us['tv4a'])
            h = A.get('/travel/%d/costs/' % t.pk).content.decode()
            row = h.split('TV4 back', 1)[1].split('data-booking', 1)[0]
            ok('Included in FR 4519' in row,
               'INCLUDED: the return flight says "Included in FR 4519"')
            ok('Included in the price of' in A.get(
                '/travel/booking/%d/' % o2.pk).content.decode() and
               'data-included' not in A.get('/travel/booking/%d/' % o1.pk)
               .content.decode(), '  on its own page too - not on the one '
               'that carries the price')
            ok('Included in FR 4519' in M.get(
                '/travel/m/trip/%d/?tab=costs' % t.pk).content.decode(),
               '  and on the phone')
            o1.delete()
            o2.delete()

            # ---- Demetri, 15 Nov: the trip as a PDF, summary or detailed,
            # to share by email, WhatsApp... through the house PDF viewer.
            for kind in ('summary', 'detailed'):
                r = A.get('/travel/%d/pdf/?kind=%s' % (t.pk, kind))
                ok(r.status_code == 200 and
                   r['Content-Type'] == 'application/pdf' and
                   r.content[:5] == b'%PDF-' and
                   ('_%s.pdf' % kind) in r['Content-Disposition'],
                   'TRIP PDF, %s: made' % kind)
            ok(len(A.get('/travel/%d/pdf/?kind=detailed' % t.pk).content) >
               len(A.get('/travel/%d/pdf/?kind=summary' % t.pk).content),
               '  the detailed one carries more')
            h = A.get('/travel/%d/' % t.pk).content.decode()
            ok('data-trip-pdf="summary"' in h and
               'data-trip-pdf="detailed"' in h and 'openPdfViewer(' in h,
               '  the trip page opens either in the PDF viewer (Download, '
               'Share)')
            ok(C.get('/travel/%d/pdf/' % t.pk).status_code == 404,
               '  nobody off the trip can have it')
            ok(M.get('/travel/m/trip/%d/pdf/?kind=summary' % t.pk)
               .status_code == 200 and 'data-share-pdf' in M.get(
                   '/travel/m/trip/%d/' % t.pk).content.decode(),
               '  and on the phone, to the share sheet')

            # ---- the phone
            h = M.get('/travel/m/trip/%d/?tab=itinerary' % t.pk).content \
                .decode()
            ok(h.count('data-itinerary-day') == 4 and 'data-place' in h and
               'Gulbenkian' in h, 'PHONE: the itinerary')
            h = M.get('/travel/m/trip/%d/?tab=wish' % t.pk).content.decode()
            ok('data-add-place' in h, '  the wish list, with Add a place')
            share = ('Jeronimos Monastery\nPraca do Imperio, Lisboa\n'
                     'https://maps.app.goo.gl/XyZ')
            r = M.post('/travel/m/share/', {'title': 'Jeronimos Monastery',
                                            'text': share})
            ok(r.status_code == 302 and
               ('/travel/m/trip/%d/place/new/?q=' % t.pk) in r['Location'],
               'SHARE FROM GOOGLE MAPS opens Add a place on the coming trip',
               r.get('Location'))
            h = M.get(r['Location']).content.decode()
            ok('Jeronimos Monastery' in h and 'maps.app.goo.gl' in h,
               '  with what Maps shared filled in')
            PL.call = lambda place, client=None: real_call(place, client=Fake(
                {'found': True, 'name': 'Jeronimos Monastery'}))
            r = M.post('/travel/m/trip/%d/place/new/' % t.pk,
                       {'q': share, 'lookup': '1', 'day': ''})
            jm = Place.objects.get(trip=t, name='Jeronimos Monastery')
            ok(r['Location'] == '/travel/m/place/%d/' % jm.pk and
               jm.maps_link == 'https://maps.app.goo.gl/XyZ' and
               jm.address == 'Praca do Imperio, Lisboa',
               '  added: Maps\' own link and address kept')
            r = M.post('/travel/m/place/%d/move/' % jm.pk, {
                'day': (day + dt.timedelta(days=10)).isoformat(),
                'time': '18:00', 'next': '/travel/m/place/%d/' % jm.pk})
            jm.refresh_from_db()
            ok(r['Location'] == '/travel/m/place/%d/' % jm.pk and
               jm.time == dt.time(18, 0),
               '  moved on the phone, staying on the phone')
            raise Rollback
    except Rollback:
        pass
    finally:
        PL.call = real_call
        if real_details is not None:
            PL.call_details = real_details
        PL.SYNC = False

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('trip.by_bookings' not in was(J(TA, 'views.py')),
       'before this round: typed dates won over the bookings')
except IOError as _e:
    skip('control', str(_e))
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
