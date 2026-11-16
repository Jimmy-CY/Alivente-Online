# -*- coding: utf-8 -*-
"""test_travel_seven.py - round TR-7, 16 Nov 2026.

RELEASE 88 - TRAVEL: SETTLING UP, COMPARING TRIPS, NEVER A BLANK PAGE.
Demetri, 16 Nov: "Once all the trip days have passed ... set all
Reservations as paid (maybe to ask first)"; "compare flight costs,
accommodation costs (per night), car rental (per day), trains ... multi
select trips"; Travel "blank until I press Past" and Today on the phone
blank - show the past trips, newest first, marked Past.
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

SUFFIX = '.bak_travel7'
ME = 'test_travel_seven.py'
PATCHER = 'apply_travel_seven.py'
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
ok('settle_off = models.BooleanField(default=False)' in md and
   'settle_after = models.DateField(null=True, blank=True)' in md and
   os.path.isfile(J(TA, 'migrations', '0006_settle_up.py')),
   'MODEL: a trip remembers Leave as it is / Ask again in a week (0006)')
u = read(J(TA, 'urls.py'))
ok("name='trip_settle'" in u and "name='compare'" in u and
   "name='m_compare'" in u, 'routes: settle up, compare (and on the phone)')
cp = read(J(TA, 'compare.py'))
ok('anthropic' not in cp.lower() and "'hotel_night'" in cp and
   "'flight_seat'" in cp and "'car_day'" in cp,
   'COMPARE works the figures out itself - no model asked')
import glob as _g                                           # noqa: E402
pages = [x for x in sorted(_g.glob(J(TT, '*.html')))
         if "{% extends 'base.html' %}" in read(x)]
nohelp = [os.path.basename(x) for x in pages
          if 'data-target="#travelHelpModal"' not in read(x) or
          '{% render_help_modal "travel" %}' not in read(x)]
ok(len(pages) >= 12 and not nohelp,
   'HELP ON EVERY TRAVEL PAGE (Demetri, 16 Nov: "I don\'t see any Help?? We '
   'need to create Help sections throughout the module") - %d pages'
   % len(pages), nohelp)
ok(read(J(TT, 'trip.html')).count("this.closest('details').open = false")
   == 2 and read(J(TT, 'm', 'trip.html')).count(
       "this.closest('details').open = false") == 2,
   'PDF: the Summary / Detailed choice closes once one is picked (Demetri, '
   '16 Nov)')
ok(all('{% if p.wallet_link and not p.over %}' in read(J(TT, *x))
        for x in (('passes.html',), ('m', 'passes.html'), ('booking.html',)))
   and 'p.over = flown(b,' in read(J(TA, 'phone.py')),
   'GOOGLE WALLET: the airline\'s link only before the flight - after it, '
   'the airline answers with an error (Demetri, 16 Nov)')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('<strong>Compare trips.</strong>' in hp and
   '<strong>After a trip.</strong>' in hp and
   'with nothing coming up it shows your <strong>Past</strong>' in hp and
   'Between trips' in read(J(TT, 'm', 'help.html')),
   'HELP: comparing, settling up, past trips when nothing is ahead')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, BookingChange, Trip
    from travel import places as PL
    connection.ensure_connection()
    Trip.objects.filter(settle_off=False).exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    import datetime as dt
    from decimal import Decimal as D
    from django.conf import settings as _dj
    from django.utils import timezone
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    real_details = PL.call_details

    def no_web(b, client=None):
        raise PL.LookupError_('not from the test suite')
    PL.call_details = no_web
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('tv7a', 'tv7a@example.com', 'x',
                                         first_name='Tv', last_name='Seven')
            u.user_permissions.add(perm)
            ws = ensure_workspace(u)
            UserProfile.objects.update_or_create(user=u,
                                                 defaults={'workspace': ws})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            today = timezone.localdate()

            def trip(name, start, nights, stay, flights, car=None,
                     paid='paid'):
                t = Trip.objects.create(owner=u, name=name)
                s = today + dt.timedelta(days=start)
                Booking.objects.create(
                    trip=t, kind='stay', title=name + ' hotel', added_by=u,
                    start_date=s, end_date=s + dt.timedelta(days=nights),
                    amount=D(stay), amount_eur=D(stay), paid=paid,
                    web_checked=timezone.now())
                Booking.objects.create(
                    trip=t, kind='flight', title=name + ' out', added_by=u,
                    reference=name[:5].upper(), start_date=s,
                    amount=D(flights), amount_eur=D(flights), paid='paid',
                    traveller_names='A One, B Two')
                Booking.objects.create(
                    trip=t, kind='flight', title=name + ' back', added_by=u,
                    reference=name[:5].upper(),
                    start_date=s + dt.timedelta(days=nights),
                    traveller_names='A One, B Two')
                if car:
                    Booking.objects.create(
                        trip=t, kind='car', title=name + ' car', added_by=u,
                        start_date=s, end_date=s + dt.timedelta(days=4),
                        amount=D(car), amount_eur=D(car), paid='paid')
                return t
            g = trip('TV7 Greece', -14, 8, '1064.88', '440.96', '77.90',
                     paid='due')
            sw = trip('TV7 Swiss', -60, 5, '1325.00', '384.00')

            # ---- nothing coming up: the past trips, newest first
            h = A.get('/travel/').content.decode()
            ok('data-auto-past' in h and h.index('TV7 Greece') <
               h.index('TV7 Swiss') and h.count('data-past') == 2,
               'NOTHING COMING UP: Travel shows the past trips, newest first, '
               'each marked Past')
            ok('Upcoming <span class="tv-sub">0</span>' in h and
               'Past <span class="tv-sub">2</span>' in h,
               '  the chips say how many')
            ok('data-owing' in h.split('TV7 Swiss')[0],
               '  a finished trip still owing says so')
            h = A.get('/travel/?phone=1').content.decode()
            ok('data-phone-steps' in h and 'three dots' in h and
               'Create shortcut' in h and 'data-trips' not in h,
               'PHONE APP: the code and the steps, on their own - no trip '
               'list under them')
            h = M.get('/travel/m/').content.decode()
            ok('data-last-trip' in h and 'TV7 Greece' in h and
               'data-earlier' in h and 'TV7 Swiss' in h and
               'data-owing' in h,
               'PHONE TODAY: the last trip (still owing), then the earlier ones')
            h = M.get('/travel/m/trips/').content.decode()
            ok('data-auto-past' in h and 'data-compare-link' in h,
               '  phone Trips: the past ones, and Compare')

            # ---- settling up
            h = A.get('/travel/%d/' % g.pk).content.decode()
            ok('data-settle' in h and 'TV7 Greece hotel' in h.split(
                'data-settle')[1].split('</section>')[0],
               'AFTER THE TRIP: asked whether everything is paid - the hotel '
               'listed')
            ok('data-settle' not in A.get('/travel/%d/' % sw.pk).content
               .decode(), '  not on a trip that is all paid')
            hotel = g.bookings.get(kind='stay')
            A.post('/travel/%d/settle/' % g.pk, {
                'what': 'later', 'b': [hotel.pk]})
            g.refresh_from_db()
            hotel.refresh_from_db()
            ok(g.settle_after == today + dt.timedelta(days=7) and
               hotel.paid == 'due' and
               'data-settle' not in A.get('/travel/%d/' % g.pk).content
               .decode(), 'ASK AGAIN IN A WEEK: nothing changed, not asked '
               'for seven days')
            g.settle_after = None
            g.save()
            A.post('/travel/%d/settle/' % g.pk, {
                'what': 'paid', 'b': [hotel.pk],
                'eur_%d' % hotel.pk: '1050.00'})
            hotel.refresh_from_db()
            ok(hotel.paid == 'paid' and hotel.amount_eur == D('1050.00') and
               BookingChange.objects.filter(
                   booking=hotel, note='Settled after the trip').exists(),
               'MARK TICKED ONES PAID: paid, at the amount typed, in its '
               'Changes')
            ok('data-settle' not in A.get('/travel/%d/' % g.pk).content
               .decode(), '  and not asked again')
            Booking.objects.filter(pk=hotel.pk).update(paid='due')
            A.post('/travel/%d/settle/' % g.pk, {'what': 'leave'})
            g.refresh_from_db()
            ok(g.settle_off and 'data-settle' not in A.get(
                '/travel/%d/' % g.pk).content.decode(),
               'LEAVE AS IT IS: not asked again')
            up = trip('TV7 Ahead', 20, 3, '300', '100', paid='due')
            ok('data-settle' not in A.get('/travel/%d/' % up.pk).content
               .decode(), '  never before a trip is over')
            h = A.get('/travel/').content.decode()
            ok('data-auto-past' not in h and 'TV7 Ahead' in h,
               '  with a trip ahead, Upcoming shows as before')

            # ---- comparing
            r = A.get('/travel/compare/?t=%d&t=%d' % (g.pk, sw.pk))
            h = r.content.decode()
            ok(r.status_code == 200 and 'data-compare-table' in h and
               'TV7 Greece' in h and 'TV7 Swiss' in h,
               'COMPARE two trips: the like-for-like table')
            from travel.compare import figures
            fg, fs = figures(g), figures(sw)
            ok(fg['hotel_night'] == D('131.25') and
               fs['hotel_night'] == D('265.00'),
               'HOTEL PER NIGHT: the stay’s cost over its nights '
               '(1050 / 8, 1325 / 5)', (fg['hotel_night'], fs['hotel_night']))
            ok(fg['flight_seat'] == D('110.24') and
               fs['flight_seat'] == D('96.00'),
               'FLIGHTS PER PERSON PER FLIGHT: a return’s one price over '
               'both flights and both people', (fg['flight_seat'],
                                                fs['flight_seat']))
            ok(fg['car_day'] == D('19.48') and fs['car_day'] is None,
               'CAR PER DAY: 77.90 over 4 days; none for the trip without')
            ok(fg['per_day'] == D('196.11') and fg['people'] == 2,
               'PER DAY: the trip’s total over its nights; two people',
               (fg['per_day'], fg['people']))
            ok('lowest' in h and '’s hotels cost' in h and
               'data-compare-hotels' in h,
               '  the cheapest marked, what stands out, every hotel per night')
            ok('Tick two or more' in A.get('/travel/compare/?t=%d' % g.pk)
               .content.decode(), 'ONE TRIP: asks for two or more')
            other = User.objects.create_user('tv7b', 'tv7b@example.com', 'x')
            other.user_permissions.add(perm)
            B = Client(SERVER_NAME='localhost')
            B.force_login(other)
            hb = B.get('/travel/compare/?t=%d&t=%d' % (g.pk, sw.pk)) \
                .content.decode()
            ok('TV7 Greece' not in hb,
               'SOMEONE NOT ON THE TRIPS cannot compare them')
            ok(B.post('/travel/%d/settle/' % g.pk, {'what': 'leave'})
               .status_code == 404, '  nor settle them')
            h = M.get('/travel/m/compare/?t=%d&t=%d' % (g.pk, sw.pk)) \
                .content.decode()
            ok(h.count('data-compare-row') == 7, 'PHONE: the figures, row by row')
            h = A.get('/travel/?show=all').content.decode()
            ok('data-compare-form' in h and h.count('name="t"') == 3,
               'TRAVEL: a Compare tick under every trip')
            raise Rollback
    except Rollback:
        pass
    finally:
        PL.call_details = real_details

# ==========================================================================
head('3. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('auto_past' not in was(J(TA, 'views.py')),
       'before this round: Travel stayed on an empty Upcoming')
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
