# -*- coding: utf-8 -*-
"""test_travel_five.py - round TR-5, 16 Nov 2026.

RELEASE 86 - TRAVEL: RESTAURANTS, AND DEMETRI'S REVIEW OF STAGE 4.
"Let's do a Restaurant type. Matching to the Wish List is necessary";
one PDF button with Summary or Detailed; "Don't keep home countries in";
one traveller, not two, when a boarding pass writes the name backwards;
"more details for like hotels (address, phone number, check in and check
out time, etc.) The same for restaurants"; "hover over for those
buttons"; the place search "too rigid"; "if it finds two or three
options ... given these options to choose from"; "To Move, you should at
least need as a minimum to have a date".
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

SUFFIX = '.bak_travel5'
ME = 'test_travel_five.py'
PATCHER = 'apply_travel_five.py'
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
ok("('restaurant', 'Restaurant')," in md and
   "booking = models.ForeignKey(Booking, on_delete=models.SET_NULL," in md
   and "('choose', 'Which one?')" in md and
   'web_checked = models.DateTimeField(null=True, blank=True)' in md,
   'MODELS: a Restaurant kind; a place knows its booking; options to '
   'choose from; when the web was asked')
ok(os.path.isfile(J(TA, 'migrations', '0005_restaurants.py')),
   'migration travel 0005')
ex = read(J(TA, 'extract.py'))
ok("'restaurant', 'other']" in ex and 'is kind "restaurant"' in ex,
   'EMAILS: a table booking is read as a Restaurant')
ok("'restaurant': 'fa-utensils'" in read(J(TA, 'views.py')) and
   "kind == 'restaurant'" in read(J(TT, 'm', '_icon.html')),
   '  with its own icon, on the computer and the phone')
pl = read(J(TA, 'places.py'))
ok('Never reject a well-known place because it is somewhere else.' in pl
   and 'or near the trip' not in pl and "'options': {'type': 'array'" in pl,
   'THE LOOKUP: generous with names; the destination only breaks ties; '
   'two or three options when unsure')
tr = read(J(TT, 'trip.html'))
# RA02, 19 Nov 2026 - the phone's More menu repeats PDF - summary and PDF -
# detailed; the one PDF BUTTON is counted outside it.
_desk = tr.split('<div class="action-more-wrapper"')[0] + \
    tr.split('<div class="action-more-wrapper"')[-1].split('</div>', 2)[-1]
ok(tr.count('data-trip-pdf=') == 2 and 'data-pdf-menu' in tr and
   _desk.count('fa-file-pdf') == 1 and '> PDF summary<' not in tr,
   'ONE PDF BUTTON on the trip, with Summary and Detailed under it')
ok('Itinerary{% if planned %}' not in tr and 'Itinerary</a>' in tr,
   '  the Itinerary tab carries no misleading count')
ok('name="need_day"' in tr and 'Choose a day&hellip;</option>' in tr and
   'required><option value="" selected>' in tr,
   'MOVE NEEDS A DAY: none chosen for you, and required')
pr = read(J(TT, '_place_row.html'))
ok(pr.count('title="') >= 4 and 'title="Map - open it in Google Maps"' in pr
   and 'data-to-wish' in pr and "url 'travel:place' p.pk" in pr,
   'HOVER: Edit, Map, Back to the wish list and Done each say what they do')
mt = read(J(TT, 'm', 'trip.html'))
ok('data-trip-pdf-phone' in mt and '<summary' in mt and
   'name="need_day"' in mt,
   '  the phone: one PDF button; Move needs a day')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('Restaurant</strong> is a kind of its own' in hp and
   'home country (Cyprus) is left out' in hp and
   'Which one did you mean?' in hp and
   'Missing details are looked up.' in hp and
   'choose <strong>Summary</strong> or <strong>Detailed</strong>' in hp and
   'Coming next: an itinerary' not in hp,
   'HELP: restaurants, countries, choosing a place, details looked up, '
   'the one PDF button')
ok('Places and the PDF' in read(J(TT, 'm', 'help.html')),
   '  and the phone\'s help')
ok("'travel/places.py'" in read(J(ROOT, 'test_ai_models.py')),
   'the Anthropic census already counts travel/places.py')

# ==========================================================================
head('2. NO DATABASE - countries, names, matching, the answer')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from travel import places as PL                             # noqa: E402
from travel import where as W                               # noqa: E402
from travel.views import same_people                        # noqa: E402


class _B(object):
    def __init__(self, **kw):
        self.kind, self.title, self.provider = 'other', '', ''
        self.address = self.city = self.country = ''
        self.from_place = self.to_place = self.phone = self.link = ''
        self.start_time = self.end_time = None
        self.status, self.web_checked, self.pk = 'ok', None, 1
        for k, v in kw.items():
            setattr(self, k, v)


ok(W.country_of(_B(kind='flight', from_place='Athens (ATH)',
                   to_place='Dublin (DUB)')) == 'Ireland' and
   W.country_of(_B(kind='stay', title='Clybaun Hotel Galway',
                   address='Clybaun Road, Galway, H91 TFX9, Ireland'))
   == 'Ireland' and
   W.country_of(_B(kind='car', title='Enterprise car hire Dublin Airport',
                   from_place='Dublin Airport')) == 'Ireland' and
   W.country_of(_B(kind='stay', title='PAREA Athens')) == 'Greece' and
   W.country_of(_B(kind='flight', from_place='Athens (ATH)',
                   to_place='Larnaca (LCA)')) == 'Cyprus',
   'COUNTRIES from what a booking says: its airport, its address, its town '
   '- Demetri\'s Ryanair, Galway hotel, Enterprise car and PAREA Athens')
ok(W.is_home('Cyprus') and not W.is_home('Ireland'),
   '  Cyprus is home')
ok(same_people(['Dimitrios Manias', 'Manias Dimitrios', 'Demetrios Manias'])
   == ['Dimitrios Manias', 'Demetrios Manias'],
   'ONE TRAVELLER: "Manias Dimitrios" from the boarding pass is the '
   'Dimitrios Manias already there; another spelling stays')


class _P(object):
    pk = None
    name = 'cafe central'
    kind = 'sight'
    address = hours = price = website = about = maps_link = ''
    query = 'cafe central'
    lookup = 'waiting'
    lookup_note = ''
    options = []


p = PL.fill(_P(), {'found': True, 'sure': False, 'options': [
    {'name': 'Cafe Central', 'city': 'Vienna', 'country': 'Austria',
     'address': 'Herrengasse 14, 1010 Wien', 'about': 'Historic coffee house'},
    {'name': 'Cafe Central', 'city': 'Madrid', 'country': 'Spain',
     'address': 'Plaza del Angel 10'},
    {'name': '', 'city': 'nowhere'}]})
ok(p.lookup == 'choose' and len(p.options) == 2 and
   p.options[0]['city'] == 'Vienna' and p.name == 'cafe central',
   'TWO OR THREE COULD BE MEANT: kept as options to choose from, nothing '
   'filled in')
q = _P()
q.maps_link = 'https://maps.app.goo.gl/x'
p = PL.fill(q, {'found': True, 'sure': False, 'name': 'Cafe Central',
                'options': [{'name': 'A'}, {'name': 'B'}]})
ok(p.lookup == 'found', '  a Google Maps link is one place - no choosing')
p = PL.fill(_P(), {'found': True, 'name': 'Basilica de la Sagrada Familia',
                   'kind': 'sight'})
ok(p.lookup == 'found' and p.name == 'Basilica de la Sagrada Familia',
   'ONE PLACE: its proper name over the words typed to find it')


class _Pl(object):
    def __init__(self, name, kind='food', address='', maps_link=''):
        self.name, self.kind, self.address = name, kind, address
        self.maps_link = maps_link


R = _B(kind='restaurant', title='Taverna Psaras')
ok(PL.same_place(_Pl('Psaras'), R) and
   PL.same_place(_Pl('Psaras Taverna'), R) and
   PL.same_place(_Pl('Taverna Psarás'), R) and
   not PL.same_place(_Pl('Dionysos Zonars'), R),
   'MATCHING: the restaurant booked is the one on the wish list (any '
   'order, accents, "taverna" or not) - and not another')
ok(PL.same_place(_Pl('Acropolis Museum', 'museum'),
                 _B(kind='activity', title='Acropolis Museum tickets')) and
   not PL.same_place(_Pl('Acropolis', 'sight'),
                     _B(kind='activity', title='Acropolis Museum tickets')),
   '  museum tickets for the museum - not for the hill next to it')
H = _B(kind='stay', title='Clybaun Hotel', phone='+353 91 000000')
ok(PL.gaps(H) == ['address', 'check_in', 'check_out'] and
   PL.add_details(H, {'found': True, 'address': 'Clybaun Rd, Galway',
                      'phone': '+353 1 111', 'check_in': '15:00',
                      'check_out': '11:00'}) and
   H.address == 'Clybaun Rd, Galway' and H.phone == '+353 91 000000' and
   H.end_time.hour == 11,
   'MISSING DETAILS: only the blanks are filled - the phone from the email '
   'stays')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, BookingChange, Place, Trip
    connection.ensure_connection()
    Place.objects.filter(booking__isnull=False).exists()
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
    def __init__(self, tool, data=None):
        self.tool, self.data, self.sent = tool, data, []
        self.messages = self

    def create(self, **kw):
        self.sent.append(kw)

        class Rr(object):
            pass
        r = Rr()
        r.content = [Block('server_tool_use', 'web_search', {'query': 'x'}),
                     Block('tool_use', self.tool, self.data)]
        return r


if have_db:
    import datetime as dt
    from django.conf import settings as _dj
    from django.utils import timezone
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    real_call, real_details = PL.call, PL.call_details
    asked = []

    def no_web(b, client=None):
        asked.append(b.title)
        raise PL.LookupError_('not from the test suite')
    PL.call_details = no_web
    PL.SYNC = True
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            us = {}
            for n in ('tv5a', 'tv5c'):
                usr = User.objects.create_user(n, n + '@example.com', 'x')
                usr.user_permissions.add(perm)
                us[n] = usr
            ws = ensure_workspace(us['tv5a'])
            for usr in us.values():
                UserProfile.objects.update_or_create(
                    user=usr, defaults={'workspace': ws})
            A = Client(SERVER_NAME='localhost')
            A.force_login(us['tv5a'])
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(us['tv5a'])
            day = timezone.localdate() + dt.timedelta(days=20)
            t = Trip.objects.create(owner=us['tv5a'], name='TV5 Greece',
                                    countries='')
            mk = lambda **kw: Booking.objects.create(            # noqa: E731
                trip=t, added_by=us['tv5a'], **kw)
            mk(kind='flight', title='TV5 CY310', from_place='Larnaca (LCA)',
               to_place='Athens (ATH)', start_date=day,
               traveller_names='Dimitrios Manias, Manias Dimitrios')
            mk(kind='stay', title='TV5 Clybaun Hotel', start_date=day +
               dt.timedelta(days=2), end_date=day + dt.timedelta(days=4),
               address='Clybaun Road, Galway, Ireland',
               phone='+353 91 588 588', start_time=dt.time(15, 0),
               end_time=dt.time(11, 0))
            mk(kind='flight', title='TV5 home', from_place='Dublin (DUB)',
               to_place='Larnaca (LCA)', start_date=day +
               dt.timedelta(days=4))
            h = A.get('/travel/%d/' % t.pk).content.decode()
            from travel.views import span
            span(t, list(t.bookings.all()))
            ok(t.where == 'Greece, Ireland' and 'Greece, Ireland' in h,
               'COUNTRIES: Greece and Ireland from the bookings - no Cyprus',
               t.where)
            ok('Dimitrios Manias, Manias Dimitrios' not in h and
               'Dimitrios Manias' in h,
               'ONE TRAVELLER on CY310, not two')
            home = Trip.objects.create(owner=us['tv5a'], name='TV5 Paphos')
            Booking.objects.create(trip=home, kind='stay', title='TV5 Annabelle',
                                   address='Poseidonos Ave, Paphos, Cyprus',
                                   added_by=us['tv5a'])
            span(home, list(home.bookings.all()))
            ok(home.where == 'Cyprus', '  a trip at home still says Cyprus')

            # ---- the wish list and a restaurant booking
            PL.call = lambda place, client=None: real_call(place, client=Fake(
                'record_place', {'found': True, 'sure': True,
                                 'name': 'Psaras', 'kind': 'food',
                                 'address': 'Erechtheos 16, Athens',
                                 'hours': '12:00-24:00'}))
            A.post('/travel/%d/place/new/' % t.pk, {'q': 'psaras taverna',
                                                    'lookup': '1'})
            ps = Place.objects.get(trip=t, name='Psaras')
            ok(ps.day is None and ps.lookup == 'found',
               'ON THE WISH LIST: Psaras, looked up')
            r = A.post('/travel/place/%d/move/' % ps.pk, {
                'need_day': '1', 'day': '', 'time': '20:00',
                'next': '/travel/%d/wish-list/' % t.pk})
            ps.refresh_from_db()
            ok(ps.day is None and r.status_code == 302 and
               'Choose a day first' in A.get(r['Location']).content.decode(),
               'MOVE WITH NO DAY: refused, "Choose a day first" - not put on '
               'the first day')
            r = A.post('/travel/%d/booking/new/' % t.pk, {
                           'kind': 'restaurant', 'title': 'Taverna Psaras',
                           'start_date': (day + dt.timedelta(days=1))
                           .isoformat(), 'start_time': '20:30',
                           'currency': 'EUR', 'paid': 'due',
                           'phone': '+30 210 3218733'})
            rb = Booking.objects.get(trip=t, title='Taverna Psaras')
            ps.refresh_from_db()
            ok(r.status_code == 302 and ps.booking_id == rb.pk and
               ps.day == rb.start_date and ps.time == dt.time(20, 30),
               'A TABLE BOOKED AT PSARAS: the wish-list place takes the '
               'booking\'s day and time', (r.status_code, ps.booking_id))
            h = A.get('/travel/%d/itinerary/' % t.pk).content.decode()
            ok(h.count('Psaras') == 1 and 'fa-utensils' in h,
               '  on the itinerary once - as the booking, with the '
               'restaurant icon')
            ok('from Things to do' in A.get('/travel/booking/%d/' % rb.pk)
               .content.decode() and 'data-booked' in A.get(
                   '/travel/place/%d/' % ps.pk).content.decode(),
               '  the booking and the place each point to the other')
            A.post('/travel/booking/%d/edit/' % rb.pk, {
                'kind': 'restaurant', 'title': 'Taverna Psaras',
                'start_date': (day + dt.timedelta(days=1)).isoformat(),
                'start_time': '20:30', 'currency': 'EUR', 'paid': 'due',
                'cancelled': '1'})
            ps.refresh_from_db()
            ok(ps.booking_id is None and ps.day is None,
               'CANCELLED: the place goes back to the wish list')
            A.post('/travel/booking/%d/edit/' % rb.pk, {
                'kind': 'restaurant', 'title': 'Taverna Psaras',
                'start_date': (day + dt.timedelta(days=2)).isoformat(),
                'start_time': '21:00', 'currency': 'EUR', 'paid': 'due'})
            ps.refresh_from_db()
            ok(ps.booking_id == rb.pk and ps.time == dt.time(21, 0),
               '  booked again: back on the booking\'s day')
            A.post('/travel/booking/%d/delete/' % rb.pk)
            ps.refresh_from_db()
            ok(ps.booking_id is None and ps.day is None,
               'DELETED: back to the wish list')

            # ---- from an email, the table booked first
            from travel import inbox as IB
            eb = IB.create(t, {'kind': 'restaurant', 'title': 'Funky Gourmet',
                               'start_date': (day + dt.timedelta(days=3))
                               .isoformat(), 'start_time': '19:30',
                               'status': 'confirmed'}, us['tv5a'])
            PL.call = lambda place, client=None: real_call(place, client=Fake(
                'record_place', {'found': True, 'name': 'Funky Gourmet',
                                 'kind': 'food'}))
            A.post('/travel/%d/place/new/' % t.pk, {'q': 'funky gourmet',
                                                    'lookup': '1'})
            fg = Place.objects.get(trip=t, name='Funky Gourmet')
            ok(fg.booking_id == eb.pk and fg.time == dt.time(19, 30),
               'BOOKED FIRST, ADDED LATER: the place finds its booking')

            # ---- choosing
            PL.call = lambda place, client=None: real_call(place, client=Fake(
                'record_place', {'found': True, 'sure': False, 'options': [
                    {'name': 'Cafe Central', 'city': 'Vienna',
                     'country': 'Austria', 'address': 'Herrengasse 14'},
                    {'name': 'Cafe Central', 'city': 'Madrid',
                     'country': 'Spain', 'address': 'Plaza del Angel 10'}]}))
            A.post('/travel/%d/place/new/' % t.pk, {'q': 'cafe central',
                                                    'lookup': '1'})
            cc = Place.objects.get(trip=t, name='cafe central')
            h = A.get('/travel/place/%d/' % cc.pk).content.decode()
            ok(cc.lookup == 'choose' and h.count('data-option') == 2 and
               'Which one did you mean?' in h and 'Herrengasse 14' in h and
               'data-none' in h,
               'WHICH ONE: two Cafe Centrals to choose from, and None of these')
            ok(M.get('/travel/m/place/%d/' % cc.pk).content.decode()
               .count('data-option') == 2, '  on the phone too')
            seen = {}

            def vienna(place, client=None):
                f = Fake('record_place', {'found': True, 'sure': True,
                                          'name': 'Cafe Central',
                                          'hours': '08:00-21:00'})
                out = real_call(place, client=f)
                seen['ask'] = f.sent[0]['messages'][0]['content']
                return out
            PL.call = vienna
            A.post('/travel/place/%d/pick/' % cc.pk, {'pick': '0'})
            cc.refresh_from_db()
            ok(cc.lookup == 'found' and cc.address == 'Herrengasse 14' and
               cc.hours == '08:00-21:00' and 'Vienna' in seen.get('ask', ''),
               '  the Vienna one picked: that one is looked up')

            # ---- Try again with the name changed in the box
            PL.call = lambda place, client=None: real_call(place, client=Fake(
                'record_place', {'found': False}))
            A.post('/travel/%d/place/new/' % t.pk, {'q': 'sagrada familia',
                                                    'lookup': '1'})
            sf = Place.objects.get(trip=t, name='sagrada familia')
            ok(sf.lookup == 'failed' and 'add the town' in sf.lookup_note,
               'NOT FOUND: says to add the town and try again')
            PL.call = vienna
            A.post('/travel/place/%d/again/' % sf.pk, {
                'name': 'Sagrada Familia Barcelona', 'kind': 'sight',
                'address': '', 'hours': '', 'price': '', 'website': '',
                'notes': '', 'day': '', 'time': ''})
            ok('Sagrada Familia Barcelona' in seen.get('ask', ''),
               '  TRY AGAIN looks up what is in the Name box now')

            # ---- one PDF button; the detailed one has the hotel's details
            h = A.get('/travel/%d/' % t.pk).content.decode()
            ok('data-pdf-menu' in h and h.count('data-trip-pdf=') == 2,
               'ONE PDF BUTTON, Summary and Detailed under it')
            from travel.report import context
            from django.template.loader import get_template
            html = get_template('travel/trip_pdf.html').render(
                context(t, 'detailed'))
            ok('Tel +353 91 588 588' in html and
               'Clybaun Road, Galway, Ireland' in html and
               'Check in from 15:00' in html and 'by 11:00' in html,
               'DETAILED: the hotel\'s address, phone, check-in and '
               'check-out on its day')
            html = get_template('travel/trip_pdf.html').render(
                context(t, 'summary'))
            ok('Tel +353' not in html, '  the summary stays short')

            # ---- missing details, looked up once
            gap = Booking.objects.create(
                trip=t, kind='stay', title='TV5 PAREA Athens',
                start_date=day, end_date=day + dt.timedelta(days=2),
                added_by=us['tv5a'])
            PL.call_details = lambda b, client=None: real_details(
                b, client=Fake('record_details', {
                    'found': True, 'address': 'Kriezotou 6, Athens',
                    'phone': '+30 210 000 0000', 'check_in': '15:00',
                    'check_out': '12:00'}))
            A.get('/travel/%d/itinerary/' % t.pk)
            gap.refresh_from_db()
            ch = BookingChange.objects.filter(booking=gap, source='web')
            ok(gap.address == 'Kriezotou 6, Athens' and
               gap.start_time == dt.time(15, 0) and
               gap.web_checked is not None and ch.count() == 1,
               'A HOTEL\'S MISSING ADDRESS, PHONE AND TIMES: looked up when '
               'the trip is opened, and in its Changes')
            PL.call_details = no_web
            n = len(asked)
            gap.address = ''
            gap.save()
            A.get('/travel/%d/itinerary/' % t.pk)
            ok(len(asked) == n, '  once only - not again on the next visit')

            # ---- hover labels, and back to the wish list
            Place.objects.filter(pk=sf.pk).update(day=day, lookup='found')
            h = A.get('/travel/%d/itinerary/' % t.pk).content.decode()
            ok('title="Edit - change it, look it up again or remove it"' in h
               and 'data-to-wish' in h,
               'HOVER LABELS on the itinerary\'s place buttons')
            A.post('/travel/place/%d/move/' % sf.pk, {'to_wish': '1'})
            sf.refresh_from_db()
            ok(sf.day is None, '  Back to the wish list')

            # ---- Demetri, 16 Nov: "Things to do", and at the bottom of
            # the itinerary those with no day yet.
            h = A.get('/travel/%d/itinerary/' % t.pk).content.decode()
            todo = h.split('data-itinerary-todo', 1)[-1]
            ok('Things to do &mdash; no day yet' in h and
               'Sagrada' in todo and 'href="#todo"' in h and
               h.index('data-itinerary-todo') > h.rindex('data-itinerary-day'),
               'THINGS TO DO with no day yet: at the bottom of the itinerary')
            ok('Things to do &mdash; no day yet' in M.get(
                '/travel/m/trip/%d/?tab=itinerary' % t.pk).content.decode(),
               '  on the phone too')
            html = get_template('travel/trip_pdf.html').render(
                context(t, 'summary'))
            ok('Things to do - no day yet' in html and 'Wish list' not in html,
               '  and in the PDF')
            h = A.get('/travel/%d/' % t.pk).content.decode()
            ok('>Things to do' in h and '>Wish list' not in h and
               'Things to do</a>' in M.get('/travel/m/trip/%d/' % t.pk)
               .content.decode(),
               'THE TAB IS "Things to do", on the computer and the phone')
            raise Rollback
    except Rollback:
        pass
    finally:
        PL.call, PL.call_details = real_call, real_details
        PL.SYNC = False

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok("'restaurant'" not in was(J(TA, 'models.py')),
       'before this round: no Restaurant kind')
except IOError as _e:
    skip('control', str(_e))
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
