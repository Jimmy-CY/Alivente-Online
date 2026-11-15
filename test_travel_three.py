# -*- coding: utf-8 -*-
"""test_travel_three.py - round TR-3, 15 Nov 2026.

RELEASE 84 - TRAVEL, STAGE 3: THE PHONE APP. Demetri, 15 Nov: a separate
installable Travel app "like Wellness" - 30 days signed in on the phone,
boarding passes that "work/show like Google Wallet" and without a signal,
and "Share -> Alivente Travel". Each passenger's pass is their own.
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

import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_travel3'
ME = 'test_travel_three.py'
PATCHER = 'apply_travel_three.py'
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
CODE = ('M1' + 'MANIAS/DIMITRIOS'.ljust(20) + 'E' + 'ABC123 ' + 'LCA' + 'ATH'
        + 'CY ' + '0326 ' + '186' + 'Y' + '012A' + '0045 ' + '1' + '00')
CODE2 = CODE.replace('MANIAS/DIMITRIOS', 'MANIA/ALEXANDRA ').replace(
    '012A', '012B')

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
u = read(J(TA, 'urls.py'))
ok("path('m/', phone.today, name='m_today')" in u and
   "path('m/passes/', phone.passes, name='m_passes')" in u and
   "path('m/share/', phone.share, name='m_share')" in u and
   "path('app/sw.js', phone.service_worker, name='service_worker')" in u,
   'routes: the phone app under m/, its shell under app/')
mw = read(J(ROOT, 'pages', 'middleware.py'))
ok("'travel/app/'," in mw and "'travel/m/'," not in mw,
   'the middleware lets the shell through - the pages keep their check')
se = read(J(ROOT, 'wellness', 'session.py'))
ok("LONG_APPS = ('/wellness/', '/travel/m/')" in se and
   'if path.startswith(LONG_APPS):' in se and
   "'/travel/m/', '/travel/app/', '/travel/inbound/')" in se,
   'the phone\'s 30 days: Wellness and now Travel')
ph = read(J(TA, 'phone.py'))
m = re.search(r"SW_VERSION = '([^']+)'", ph)
base = read(J(TT, 'm', 'base.html'))
ok(m and base.count('?v=%s"' % m.group(1)) == 2,
   'the worker\'s version and the page\'s ?v= agree (%s)'
   % (m.group(1) if m else '?'))
js = read(J(TA, 'assets', 'travel.js'))
ok("screen.orientation.lock('portrait-primary')" in js and
   "navigator.wakeLock.request('screen')" in js,
   'PASSES: the screen stays on and does not turn sideways')
ok("'share_target'" in ph and "'action': '/travel/m/share/'" in ph,
   'the manifest offers Share -> Travel')
for f in ('travel.css', 'travel.js', 'icon-192.png', 'icon-512.png',
          'icon-maskable-512.png', 'apple-touch-icon.png'):
    ok(os.path.isfile(J(TA, 'assets', f)), 'asset %s' % f)
for f in ('base', 'today', 'trips', 'trip', 'booking', 'passes', 'check',
          'help', '_row', '_icon', '_requests'):
    ok(os.path.isfile(J(TT, 'm', f + '.html')), 'template m/%s.html' % f)
for t in os.listdir(J(TT, 'm')):
    s = read(J(TT, 'm', t))
    ok('{#' not in s.split('\n', 1)[0] or s.split('\n', 1)[0].count('#}'),
       '  m/%s: no two-line {# #} comment' % t)
az = read(J(TA, 'barcodes', 'aztec.py'))
pd = read(J(TA, 'barcodes', 'pdf417', '__init__.py'))
ok('vendored' in az and 'MIT' in az and 'def main(' not in az and
   'Ivan Habunek' in pd and 'MIT' in pd,
   'the two vendored encoders keep their licences; no command lines')
ok(os.path.isfile(J(TA, 'migrations', '0003_boarding_passes.py')) and
   'def carry_over(' in read(J(TA, 'migrations',
                               '0003_boarding_passes.py')),
   'migration travel 0003 - a pass per passenger, stage 2\'s carried over')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('data-tab-slug="tr-phone"' in hp and 'Share &rarr; Travel' in hp,
   'HELP: a Phone app tab')

# ==========================================================================
head('2. THE BARCODES - no database')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import hashlib                                              # noqa: E402
import django                                               # noqa: E402
django.setup()
from travel import barcodes as BC                           # noqa: E402

info = BC.bcbp(CODE, 2030)
ok(info.get('name') == 'Dimitrios Manias' and info['pnr'] == 'ABC123' and
   info['from'] == 'LCA' and info['to'] == 'ATH' and
   info['carrier'] == 'CY' and info['flight'] == '326' and
   info['seat'] == '12A' and str(info['date']) == '2030-07-05',
   'BCBP read: passenger, reference, LCA-ATH, CY 326, seat 12A, 5 Jul',
   info)
ok(BC.bcbp('M1SHORT') == {} and BC.bcbp('hello ' * 20) == {},
   '  and nothing read from what is not a BCBP')
# The drawings, pinned: the round trip below was decoded with ZXing when
# they were written (15 Nov 2026), and identical text must draw identical
# codes on every machine - the encoders are pure Python.
PINS = {'aztec': '6c203b2ce3b97bd5', 'pdf417': '2495a8ea2fd1b61c',
        'qr': '6073716ec1277d0d'}
for f, want in PINS.items():
    s = BC.svg(CODE, f)
    got = hashlib.sha256(s.encode()).hexdigest()[:16]
    ok(s.startswith('<svg') and 'role="img"' in s and got == want,
       '%s: drawn, and exactly as when it was decoded' % f, got)
ok(BC.svg(CODE, 'code39') == '',
   '  an unknown symbology draws nothing (the PDF is shown instead)')
try:
    import re as _re
    import zxingcpp
    from PIL import Image

    def raster(s, sc):
        w, h = map(int, _re.search(r'viewBox="0 0 (\d+) (\d+)"',
                                   s).groups())
        img = Image.new('L', ((w + 4) * sc, (h + 4) * sc), 255)
        px = img.load()
        for x, y, ww, hh in _re.findall(r'M(\d+) (\d+)h(\d+)v(\d+)', s):
            x, y, ww, hh = map(int, (x, y, ww, hh))
            for yy in range((y + 2) * sc, (y + 2 + hh) * sc):
                for xx in range((x + 2) * sc, (x + 2 + ww) * sc):
                    px[xx, yy] = 0
        return img
    for f in PINS:
        r = zxingcpp.read_barcodes(raster(BC.svg(CODE, f),
                                          4 if f == 'pdf417' else 6))
        ok(r and r[0].text == CODE, 'DECODED: the %s drawing scans back to '
           'the boarding pass' % f)
except ImportError:
    skip('the scan round trip', 'ZXing is not installed here - the pins '
         'above stand for it')

# ==========================================================================
head('3. DRIVEN - the phone app')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.core.files.uploadedfile import SimpleUploadedFile
    from pages.models import UserProfile
    from travel.models import (BoardingPass, Booking, CheckItem,
                               InboundEmail, Trip)
    connection.ensure_connection()
    BoardingPass.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')
DESK = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0'

if have_db:
    import datetime as dt
    import tempfile
    from django.conf import settings as _dj
    from django.utils import timezone
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    _dj.MEDIA_ROOT = tempfile.mkdtemp(prefix='tv3-')
    from pages.workspace import ensure_workspace
    import travel.inbox as IB
    import travel.extract as EX

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            p, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            us = {}
            for n in ('tv3a', 'tv3b', 'tv3c'):
                usr = User.objects.create_user(n, n + '@example.com', 'x',
                                               first_name=n.upper())
                usr.user_permissions.add(p)
                us[n] = usr
            ws = ensure_workspace(us['tv3a'])
            for usr in us.values():
                UserProfile.objects.update_or_create(
                    user=usr, defaults={'workspace': ws})
            A = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            A.force_login(us['tv3a'])
            C = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            C.force_login(us['tv3c'])
            anon = Client(SERVER_NAME='localhost')

            r = anon.get('/travel/m/')
            ok(r.status_code == 302 and '/login/' in r['Location'],
               'SIGNED OUT: the app asks for the login')
            r = anon.get('/travel/app/manifest.webmanifest')
            mf = json.loads(r.content)
            ok(r.status_code == 200 and mf['scope'] == '/travel/m/' and
               mf['share_target']['action'] == '/travel/m/share/',
               'the manifest is served to a phone with no session')
            r = anon.get('/travel/app/sw.js')
            ok(r.status_code == 200 and r['Service-Worker-Allowed'] ==
               '/travel/m/' and "caches.delete(PAGES)" in r.content.decode(),
               '  the worker too - and it forgets the pages on sign-out')
            ok(anon.get('/travel/app/icon-192.png').status_code == 200 and
               anon.get('/travel/app/views.py').status_code == 404,
               '  the icons; nothing else from the app folder')

            day = timezone.localdate()
            t = Trip.objects.create(owner=us['tv3a'], name='TV3 Athens')
            t.shared_with.add(us['tv3b'])
            fl = Booking.objects.create(
                trip=t, kind='flight', title='Cyprus Airways CY 326',
                provider='Cyprus Airways', reference='ABC123',
                segment='CY 326', start_date=day + dt.timedelta(days=2),
                start_time=dt.time(6, 40), from_place='Larnaca (LCA)',
                to_place='Athens (ATH)', added_by=us['tv3a'])
            Booking.objects.create(
                trip=t, kind='stay', title='TV3 Parea',
                start_date=day + dt.timedelta(days=2),
                end_date=day + dt.timedelta(days=5), address='Athens 1',
                phone='+30 210 1', added_by=us['tv3a'])
            IB.keep_pass(fl, {'pass_code': CODE, 'pass_format': 'aztec',
                              'wallet_link': 'https://pay.google.com/gp/v/'
                                             'save/x'}, us['tv3a'])
            IB.keep_pass(fl, {'pass_code': CODE2, 'pass_format': 'pdf417'},
                         us['tv3b'])
            IB.keep_pass(fl, {'pass_code': CODE.replace('012A', '014C'),
                              'pass_format': 'aztec'}, us['tv3a'])
            ps = list(fl.passes.order_by('name'))
            ok([(x.name, x.seat) for x in ps] ==
               [('Alexandra Mania', '12B'), ('Dimitrios Manias', '14C')],
               'A PASS EACH: Alexandra\'s beside Demetri\'s; his again '
               'replaced his own (new seat)', [(x.name, x.seat) for x in ps])

            h = A.get('/travel/m/').content.decode()
            ok('TV3 Athens' in h and 'In 2 days' in h and 'data-next-trip'
               in h, 'TODAY before the trip: the countdown')
            r = A.get('/travel/m/')
            ok(r.status_code == 200 and A.session.get_expiry_age() >
               29 * 86400, '  and on the phone the sign-in lasts 30 days',
               A.session.get_expiry_age())
            D = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=DESK)
            D.force_login(us['tv3a'])
            D.get('/travel/m/')
            ok(D.session.get_expiry_age() < 29 * 86400,
               '  CONTROL: opened on a computer, the session is left alone')

            t.start_date = day
            t.end_date = day + dt.timedelta(days=5)
            t.save()
            fl.start_date = day + dt.timedelta(days=1)
            fl.save()
            h = A.get('/travel/m/').content.decode()
            ok('day 1 of 6' in h and 'data-tomorrow' in h and
               'Cyprus Airways CY 326' in h and 'data-passes-today' in h,
               'TODAY while away: day 1 of 6, tomorrow\'s flight, and the '
               'passes one tap away')

            h = A.get('/travel/m/passes/').content.decode()
            ok(h.count('data-pass ') == 2 and h.count('data-next') == 1 and
               h.count('<svg xmlns') >= 2 and
               'Dimitrios Manias' in h and 'Alexandra Mania' in h and
               'Add to Google Wallet' in h and 'data-barcode="pdf417"' in h,
               'PASSES: two cards, each with its barcode, Wallet link kept')
            ok('LCA' in h and 'ATH' in h and 'CY 326' in h and '12B' in h,
               '  read from the code: LCA to ATH, CY 326, seat 12B')
            # Demetri: once a flight has passed, the NEXT pass shows.
            import travel.phone as PHN
            later = Booking.objects.create(
                trip=t, kind='flight', title='TV3 back', reference='ABC123',
                segment='CY 327', start_date=day + dt.timedelta(days=4),
                start_time=dt.time(21, 0), added_by=us['tv3a'])
            IB.keep_pass(later, {'pass_code': CODE.replace('0326', '0327'),
                                 'pass_format': 'aztec'}, us['tv3a'])
            now = dt.datetime.combine(day, dt.time(12, 0))
            gone = Booking(start_date=day, start_time=dt.time(6, 40),
                           end_time=dt.time(8, 30))
            late = Booking(start_date=day, start_time=dt.time(23, 50),
                           end_time=dt.time(1, 10))
            ok(PHN.flown(gone, now) and not PHN.flown(late, now) and
               not PHN.flown(Booking(start_date=day, start_time=dt.time(
                   10, 0)), now) and PHN.flown(Booking(
                       start_date=day, start_time=dt.time(8, 0)), now),
               'FLOWN: landed (or 3 hours after leaving with no arrival) - '
               'a flight landing after midnight is not over yet')
            fl.start_date = day - dt.timedelta(days=1)
            fl.end_time = dt.time(8, 0)
            fl.save()
            h = A.get('/travel/m/passes/').content.decode()
            nx = h.split('data-next', 1)[1].split('</article>', 1)[0] \
                if 'data-next' in h else ''
            ok(h.count('data-pass ') == 3 and h.count('data-next') == 1 and
               'CY 327' in nx and 'CY 326' in h,
               'PASSES after a flight: nothing hidden, and it opens on the '
               'next flight\'s pass')
            later.delete()
            fl.start_date = day + dt.timedelta(days=1)
            fl.end_time = None
            fl.save()
            fl.status = 'cancelled'
            fl.save()
            ok(A.get('/travel/m/passes/').content.decode().count(
                'data-pass ') == 0, '  a cancelled flight\'s passes go')
            fl.status = 'ok'
            fl.save()

            h = A.get('/travel/m/trips/').content.decode()
            ok('TV3 Athens' in h and 'Shared' in h, 'TRIPS on the phone')
            h = A.get('/travel/m/trip/%d/' % t.pk).content.decode()
            ok(h.count('data-booking') >= 2, '  a trip, by day')
            hb = A.get('/travel/m/booking/%d/' % fl.pk).content.decode()
            ok('data-has-pass' in hb and 'ABC123' in hb,
               '  a booking, with its passes')
            st = Booking.objects.get(title='TV3 Parea')
            hs = A.get('/travel/m/booking/%d/' % st.pk).content.decode()
            ok('tel:+30 210 1' in hs and 'maps/search' in hs,
               '  Call and Map, one tap')
            ok(C.get('/travel/m/trip/%d/' % t.pk).status_code == 404 and
               C.get('/travel/m/booking/%d/' % fl.pk).status_code == 404 and
               'data-pass ' not in C.get('/travel/m/passes/').content
               .decode(), 'SOMEONE NOT ON THE TRIP sees none of it')
            dk = Client(SERVER_NAME='localhost')
            dk.force_login(us['tv3a'])
            hd = dk.get('/travel/booking/%d/' % fl.pk).content.decode()
            ok(hd.count('data-barcode=') == 2,
               'THE DESKTOP booking shows both passes too')
            ht = dk.get('/travel/').content.decode()
            ok('data-phone-app' in ht and 'Scan to open Travel' in ht,
               '  and the Travel page a code to open the app on the phone')

            # ---- To check on the phone, and Share -> Travel
            class Block(object):
                type = 'tool_use'

                def __init__(self, d):
                    self.input = d

            class Fake(object):
                def __init__(self):
                    self.messages = self

                def create(self, **kw):
                    class R(object):
                        content = [Block({'is_travel': True, 'bookings': [{
                            'kind': 'activity', 'title': 'TV3 Acropolis',
                            'reference': 'AC1', 'start_date':
                            (day + dt.timedelta(days=3)).isoformat(),
                            'city': 'Athens'}]})]
                    return R()
            real = EX.call
            EX.call = lambda info, client=None: real(info, client=Fake())
            IB.SYNC = True
            try:
                r = A.post('/travel/m/share/', {
                    'title': 'Acropolis tickets', 'text': 'see attached',
                    'files': SimpleUploadedFile(
                        'tickets.pdf', b'%PDF-1.4 tickets' * 50,
                        content_type='application/pdf')})
            finally:
                EX.call = real
                IB.SYNC = False
            e = InboundEmail.objects.get(subject='Acropolis tickets')
            it = CheckItem.objects.get(email=e)
            ok(r.status_code == 302 and r['Location'] == '/travel/m/check/'
               and e.user == us['tv3a'] and e.trusted and it.what == 'new'
               and it.trip == t,
               'SHARE -> TRAVEL: a PDF shared on the phone is read like a '
               'forwarded email, into To check, on the trip it falls in')
            h = A.get('/travel/m/check/').content.decode()
            ok('data-check-item' in h and 'TV3 Acropolis' in h and
               'data-trip-pick' in h, 'TO CHECK on the phone')
            r = A.post('/travel/m/check/%d/add/' % it.pk,
                       {'trip': t.pk, 'next': '/travel/m/check/'})
            ok(r.status_code == 302 and r['Location'] == '/travel/m/check/'
               and t.bookings.filter(title='TV3 Acropolis').exists() and
               t.bookings.get(title='TV3 Acropolis').files.filter(
                   name='tickets.pdf').exists(),
               '  Add puts it on the trip with its ticket, and stays on the '
               'phone')
            ok(A.post('/travel/m/check/%d/explode/' % it.pk).status_code ==
               404, '  an action that does not exist is refused')

            # ---- his first real run: confirmation and boarding pass for
            # one flight both waited as new; adding both made two.
            dd = {'kind': 'flight', 'title': 'TV3 CY 999', 'reference':
                  'DUP999', 'segment': 'CY 999', 'start_date':
                  (day + dt.timedelta(days=3)).isoformat(),
                  'start_time': '21:00'}
            i1 = CheckItem.objects.create(user=us['tv3a'], what='new',
                                          data=dict(dd))
            i2 = CheckItem.objects.create(user=us['tv3a'], what='new',
                                          data=dict(dd, segment='CY999',
                                                    pass_code=CODE,
                                                    pass_format='aztec'))
            h = A.get('/travel/m/check/').content.decode()
            ok(h.count('value="%d" selected' % t.pk) >= 2,
               'TO CHECK offers the trip the dates fall in, worked out '
               'afresh each time')
            A.post('/travel/m/check/%d/add/' % i1.pk, {'trip': t.pk})
            A.post('/travel/m/check/%d/add/' % i2.pk, {'trip': t.pk})
            b9 = t.bookings.filter(reference='DUP999')
            i2.refresh_from_db()
            ok(b9.count() == 1 and b9.get().passes.count() == 1 and
               i2.state == 'done' and i2.note.startswith('Went onto'),
               'THE SAME FLIGHT ADDED TWICE becomes one booking, the pass '
               'on it', (b9.count(), i2.note))

            # ---- stage 2's pass, carried over by the migration
            import importlib
            from django.apps import apps as _apps
            mig = importlib.import_module(
                'travel.migrations.0003_boarding_passes')
            old = Booking.objects.create(trip=t, kind='flight', title='Old',
                                         pass_code=CODE, pass_format='aztec')
            mig.carry_over(_apps, None)
            ok(old.passes.get().name == 'Dimitrios Manias',
               'MIGRATION: a pass stage 2 kept on a booking becomes its '
               'passenger\'s own row')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('LONG_APPS' not in was(J(ROOT, 'wellness', 'session.py')),
       'before this round: the 30 days were Wellness\'s alone')
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
