# -*- coding: utf-8 -*-
"""test_ra12_city_info_receipts.py - round RA12, 22 Nov 2026.

RELEASE RA12 - GOOD TO KNOW; + SPENDING FROM A RECEIPT PHOTO.
Demetri, 22 Nov: "I like 11 - Receipt photo to spending. The user should
have the option to manually capture or to take a photo." "Let's not keep
the receipt photo." "I like 12 - City Info card" - "Add which side they
drive on, typical shopping hours ... the latest conversion rate to Euro
(... just a once-off indication) ... the phrases, I must be able to click
on them and it plays them out loud."
No test here calls Claude, Google or an exchange-rate service: the
readers and the rate are replaced.
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

SUFFIX = '.bak_ra12'
ME = 'test_ra12_city_info_receipts.py'
PATCHER = 'apply_ra12_city_info_receipts.py'
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
import io                                                   # noqa: E402
from decimal import Decimal                                 # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import travel.places as PL                                  # noqa: E402
PL.start_details = lambda *a, **k: None                     # never Claude
from travel import cityinfo as CI                           # noqa: E402
from travel import fx                                       # noqa: E402
from travel import receipt as RC                            # noqa: E402
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')


class _Block:
    def __init__(self, data):
        self.type, self.name, self.input = 'tool_use', 'x', data


class _Msg:
    def __init__(self, data):
        self.content = [_Block(data)]


class Fake:
    """Stands in for Claude: records what it was asked."""
    def __init__(self, data):
        self.data, self.asked = data, []
        self.messages = self

    def create(self, **kw):
        self.asked.append(kw)
        return _Msg(self.data)


ISTANBUL = {
    'country': 'Turkey', 'timezone': 'Europe/Istanbul', 'emergency': '112',
    'emergency_note': 'Police, ambulance, fire', 'plugs': 'C/F',
    'voltage': '230 V', 'drives': 'right', 'currency_code': 'TRY',
    'currency_name': 'Turkish lira', 'money_note': 'Cards widely taken',
    'tipping': 'About 10% in restaurants', 'tipping_note': 'Round up taxis',
    'shops': '10:00-22:00 daily', 'shops_note': 'Bazaars closed Sunday',
    'water': 'bottled', 'water_note': 'Fine for brushing teeth',
    'language': 'Turkish', 'language_note': 'English in tourist areas',
    'lang': 'tr-TR', 'phrases': [
        {'text': 'Merhaba', 'means': 'Hello'},
        {'text': 'Hesap, lütfen', 'means': 'The bill, please'}]}


def photo(fmt='PNG'):
    from PIL import Image
    b = io.BytesIO()
    Image.new('RGB', (40, 60), (250, 250, 250)).save(b, fmt)
    b.seek(0)
    b.name = 'receipt.' + fmt.lower()
    return b


head('1. THE SOURCE')
md = read(J(TV, 'models.py'))
ok('class CityInfo(models.Model):' in md and
   os.path.isfile(J(TV, 'migrations', '0015_city_info.py')),
   'GOOD TO KNOW: CityInfo, a card a city; MIGRATION travel 0015')
rc = read(J(TV, 'receipt.py'))
ok('.save(' not in rc.replace("im.save(out, 'JPEG'", '') and
   'FileField' not in md.split('class CityInfo')[1] and
   'storage' not in rc, 'THE RECEIPT PHOTO IS NEVER KEPT (read in memory)')
ci = read(J(TT, '_city_info.html'))
ok('speechSynthesis' in ci and 'SpeechSynthesisUtterance' in ci and
   'data-lang="{{ d.lang }}"' in ci and 'onclick="tvSay(this)"' in ci,
   'PHRASES PLAY OUT LOUD: the device\'s own voice, in the city\'s '
   'language')
for w in ('Driving', 'Shops', 'ECB rate on', 'bring an adapter',
          'Tap water', 'Emergency', 'Tipping', 'Language'):
    ok(w in ci, '  the card shows: %s' % w)
ok('capture="environment"' in read(J(TT, 'm', 'spend.html')) and
   'Or type it in' in read(J(TT, 'm', 'spend.html')),
   'THE PHONE: take a photo, choose one, or type it in')
ok('data-receipt-form' in read(J(TT, '_budget.html')),
   'THE COMPUTER: From a receipt photo under Daily spending')
ok(CI.off() and RC.off(), 'NEVER CLAUDE FROM A TEST')
try:
    RC._client(None)
    ok(False, '  receipt refuses without a client')
except RC.LookupError_:
    ok(True, '  receipt refuses without a client')
try:
    CI._client(None)
    ok(False, '  city card refuses without a client')
except CI.LookupError_:
    ok(True, '  city card refuses without a client')

head('2. THE PIECES')
ok(RC.money('53.50') == Decimal('53.50') and
   RC.money('1.234,50') == Decimal('1234.50') and
   RC.money('1,234.50') == Decimal('1234.50') and
   RC.money('12,90') == Decimal('12.90') and RC.money('') is None and
   RC.money('0') is None, 'AMOUNTS READ: 53.50, 1.234,50, 1,234.50, 12,90')
f = Fake({'total': '53,50', 'currency': 'try', 'date': '2027-05-02',
          'merchant': 'Taverna Psaras'})
got = RC.read(photo().getvalue(), 'image/png', client=f)
ok(got == {'amount': Decimal('53.50'), 'currency': 'TRY',
           'date': '2027-05-02', 'merchant': 'Taverna Psaras'},
   'A RECEIPT READ: total, currency, day, shop', got)
img = f.asked[0]['messages'][0]['content'][0]
ok(img['type'] == 'image' and img['source']['media_type'] == 'image/jpeg',
   '  sent as a small JPEG')
ok(RC.read(photo().getvalue(), '', client=Fake(
    {'total': '9', 'currency': 'EUR', 'date': 'yesterday',
     'merchant': ''}))['date'] == '', '  a date it cannot read is left out')
try:
    RC.prepare(b'not a photo', 'text/plain')
    ok(False, '  not a photo: refused')
except RC.LookupError_:
    ok(True, '  not a photo: refused')
ok(CI.time_vs_home('Europe/Istanbul', dt.date(2027, 1, 10)) ==
   '1 hour ahead of Cyprus' and
   CI.time_vs_home('Europe/Istanbul', dt.date(2027, 7, 10)) ==
   'Same time as Cyprus' and
   CI.time_vs_home('Europe/London', dt.date(2027, 1, 10)) ==
   '2 hours behind Cyprus',
   'TIME FROM CYPRUS on the trip\'s dates (Istanbul winter, summer; '
   'London)')
ok(CI.clean(ISTANBUL)['drives'] == 'right' and
   CI.clean(dict(ISTANBUL, drives='LEFT'))['drives'] == 'left' and
   CI.clean(dict(ISTANBUL, water='?'))['water'] == 'bottled',
   'THE CARD TIDIED: driving side, water')

head('3. DRIVEN (database; no network)')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from pages.models import UserProfile
    from pages.workspace import ensure_workspace
    from travel.models import Booking, CityInfo, Spend, Trip
    connection.ensure_connection()
    CityInfo.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])
if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    _call, _fetch, _rcall = CI.call, fx.fetch, RC.call
    calls = []

    def fake_city(city, country='', client=None):
        calls.append(city)
        if city == 'Nowhere':
            raise CI.LookupError_('Claude could not be reached (Timeout).')
        return dict(ISTANBUL)
    CI.call, CI.SYNC = fake_city, True
    fx.fetch = lambda day, cur: Decimal('41.20')
    try:
        with transaction.atomic():
            CityInfo.objects.all().delete()
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            me = User.objects.create_user('ra12a', 'ra12a@example.com', 'x')
            her = User.objects.create_user('ra12b', 'ra12b@example.com', 'x')
            for x in (me, her):
                x.user_permissions.add(perm)
                UserProfile.objects.update_or_create(
                    user=x, defaults={'workspace': ensure_workspace(me)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
            day = timezone.localdate()
            t = Trip.objects.create(owner=me, name='RA12 Istanbul')
            t.shared_with.add(her)
            Booking.objects.create(trip=t, added_by=me, kind='stay',
                                   title='Hotel Pera', city='Istanbul',
                                   country='Turkey', start_date=day,
                                   end_date=day + dt.timedelta(days=3))
            p = A.get('/travel/%d/good-to-know/' % t.pk).content.decode()
            row = CityInfo.objects.get(key=CI.key_for('Istanbul', 'Turkey'))
            ok(row.state == 'ready' and row.rate == Decimal('41.20') and
               row.rate_day == dt.date.today() and calls == ['Istanbul'],
               'GOOD TO KNOW: written once by Claude, the ECB rate kept '
               'with it', (row.state, row.rate, calls))
            ok('data-tab-info' in p and 'data-city-info="Istanbul"' in p and
               'Cyprus is Type G: bring an adapter' in p and
               'On the right' in p and 'Cyprus drives on the left' in p,
               'THE TAB: the card - plugs and adapter, driving side')
            ok('&euro;1 = 41.20 TRY' in p and
               '100 TRY &asymp; &euro;2.43' in p and 'ECB rate on' in p,
               '  the one-off euro rate (41.20; 100 TRY = EUR 2.43)')
            ok('10:00-22:00 daily' in p and 'Bazaars closed Sunday' in p,
               '  typical shop hours')
            ok('data-say="Merhaba"' in p and 'data-lang="tr-TR"' in p and
               'Tap to hear it' in p,
               '  the phrases, to tap and hear in Turkish')
            A.get('/travel/%d/good-to-know/' % t.pk)
            ok(calls == ['Istanbul'], 'KEPT: not written again', calls)
            fx.fetch = lambda day, cur: Decimal('50')
            A.post('/travel/%d/good-to-know/%d/refresh/' % (t.pk, row.pk))
            row.refresh_from_db()
            ok(calls == ['Istanbul', 'Istanbul'] and row.state == 'ready',
               'REFRESH writes it again', calls)
            t2 = Trip.objects.create(owner=me, name='RA12 Nowhere')
            Booking.objects.create(trip=t2, added_by=me, kind='stay',
                                   title='Inn', city='Nowhere',
                                   start_date=day + dt.timedelta(days=40),
                                   end_date=day + dt.timedelta(days=41))
            p = A.get('/travel/%d/good-to-know/' % t2.pk).content.decode()
            ok('data-city-failed' in p and 'Try again' in p,
               'CLAUDE NOT REACHED: says so, with Try again')
            P = Client(SERVER_NAME='localhost')
            P.force_login(me)
            p = P.get('/travel/m/trip/%d/?tab=info' % t.pk).content.decode()
            ok('data-city-info="Istanbul"' in p and 'data-say="Merhaba"' in p,
               'THE PHONE: the Good to know tab')
            p = P.get('/travel/m/').content.decode()
            ok('data-city-info="Istanbul"' in p,
               'THE PHONE\'S TODAY: the card for the city you are in')
            # ---- receipts ----
            RC.call = lambda media, b64, client=None: {
                'total': '53.50', 'currency': 'TRY',
                'date': day.isoformat(), 'merchant': 'Taverna Psaras'}
            n0 = Spend.objects.count()
            p = A.post('/travel/%d/spend/receipt/' % t.pk,
                       {'photo': photo()}).content.decode()
            ok('data-receipt-read' in p and 'value="53.50"' in p and
               '<option value="TRY" selected>' in p and
               'value="Taverna Psaras"' in p and
               'value="%s"' % day.isoformat() in p,
               'FROM A RECEIPT PHOTO (computer): the form filled in to check')
            ok(Spend.objects.count() == n0,
               '  nothing added until you add it')
            p = P.post('/travel/m/%d/spend/receipt/' % t.pk,
                       {'photo': photo('JPEG')}).content.decode()
            ok('data-receipt-read' in p and 'value="53.50"' in p and
               'value="Taverna Psaras"' in p and 'data-receipt-form' not in p,
               'THE PHONE: the same, filled in on + Spending')
            RC.call = lambda media, b64, client=None: {
                'total': '', 'currency': 'XYZ', 'date': '2001-01-01',
                'merchant': ''}
            p = A.post('/travel/%d/spend/receipt/' % t.pk,
                       {'photo': photo()}).content.decode()
            ok('outside the trip' in p and 'XYZ cannot be converted' in p and
               'The total could not be read' in p and
               '<option value="EUR" selected>' in p,
               '  what it cannot use it says, and leaves to you')

            def boom(media, b64, client=None):
                raise RC.LookupError_('Claude could not be reached (Timeout).')
            RC.call = boom
            r = P.post('/travel/m/%d/spend/receipt/' % t.pk,
                       {'photo': photo()})
            ok(r.status_code == 302 and '/spend/new/' in r['Location'],
               '  not read: back to type it in')
            H = Client(SERVER_NAME='localhost')
            H.force_login(her)
            ok(H.post('/travel/%d/spend/receipt/' % t.pk,
                      {'photo': photo()}).status_code == 404,
               'ONLY THE OWNER adds spending, from a photo too')
            p = P.get('/travel/m/%d/spend/new/' % t.pk).content.decode()
            ok('data-receipt-camera' in p and 'data-receipt-choose' in p and
               'name="amount"' in p,
               '+ SPENDING (phone): take a photo, choose one, or type it')
            raise Rollback
    except Rollback:
        pass
    CI.call, CI.SYNC, fx.fetch, RC.call = _call, False, _fetch, _rcall

head('4. HELP AND REGISTERED')
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('From a receipt photo' in adm and 'Good to know' in adm and
   'tap to hear spoken' in adm, 'HELP (computer): receipts; Good to know')
mh = read(J(TT, 'm', 'help.html'))
ok('Take a photo of the receipt' in mh and 'data-help-goodtoknow' in mh,
   'HELP (phone)')
_v = re.search(r"SW_VERSION = 'tv(\d+)-\d+'", read(J(TV, 'phone.py')))
ok(_v and int(_v.group(1)) >= 25, 'THE PHONE APP moves to tv25-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
