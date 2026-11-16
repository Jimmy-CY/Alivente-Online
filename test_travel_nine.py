# -*- coding: utf-8 -*-
"""test_travel_nine.py - round TR-9, 16 Nov 2026.

RELEASE 89 - TRAVEL: THE ORDER OF A DAY ON THE ITINERARY.
Demetri, 16 Nov: "On my itinerary, should i have the ability to drag and
drop items (within a day). Like the order on the 9th should be Checkout,
Dop off car, Fly on Ryan Air and then check in." Agreed: a smart order
(a check-in or pick-up waits for the flight that gets you there) and your
own order - dragged on the computer, up / down on the phone.
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

SUFFIX = '.bak_travel9'
ME = 'test_travel_nine.py'
PATCHER = 'apply_travel_nine.py'
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
ok('class DayOrder(models.Model):' in md and
   os.path.isfile(J(TA, 'migrations', '0008_day_order.py')),
   'MODEL: the order chosen for a day (0008)')
u = read(J(TA, 'urls.py'))
ok("name='day_order'" in u and "name='m_day_order'" in u,
   'routes: the day\'s order, computer and phone')
tp = read(J(TT, 'trip.html'))
ok('data-grip' in tp and 'data-order-form' in tp and
   "'X-Requested-With': 'fetch'" in tp and 'data-order-reset' in tp,
   'COMPUTER: a grip to drag by; the order saved on drop; Back to automatic')
mt = read(J(TT, 'm', 'trip.html'))
ok('data-order-change' in mt and 'data-order-up' in mt and
   'data-order-down' in mt and 'data-order-done' in mt,
   'PHONE: Change order -> up / down buttons -> Done')
ok('data-arrive' in read(J(TT, '_booking_row.html')) and
   'data-arrive' in read(J(TT, 'm', '_row.html')) and
   'r.arrive' in read(J(TT, 'trip_pdf.html')),
   'AFTER YOU LAND: on the computer, the phone and the PDFs')
ok('itinerary(t, bs, pl)' in read(J(TA, 'report.py')) and
   'saved = dayorder.saved_for(trip)' in read(J(TA, 'phone.py')),
   'the PDFs and the phone\'s Today follow the chosen order')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
mh = read(J(TT, 'm', 'help.html'))
ok('<strong>The order of a day.</strong>' in hp and
   'Back to automatic</strong>' in hp and
   '<b>Change order</b>' in mh,
   'HELP: smart order, dragging, Change order, Back to automatic')

# ==========================================================================
head('2. SMART ORDER (travel/dayorder.py)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from types import SimpleNamespace as NS                     # noqa: E402
from travel import dayorder as DO                           # noqa: E402
from travel.phone import on_day                             # noqa: E402

T = dt.time
D3, D5, D9, D10 = (dt.date(2026, 11, 3), dt.date(2026, 11, 5),
                   dt.date(2026, 11, 9), dt.date(2026, 11, 10))
_n = [0]


def bk(kind, title, sd, st=None, ed=None, et=None, frm='', to='',
       address=''):
    _n[0] += 1
    return NS(pk=_n[0], id=_n[0], kind=kind, title=title, provider='',
              start_date=sd, start_time=st, end_date=ed, end_time=et,
              from_place=frm, to_place=to, address=address, status='booked',
              amount=None, amount_eur=None, currency='EUR', paid='paid',
              reference='', traveller_names='', phone='', details='',
              travellers=NS(all=lambda: []))


athens1 = bk('stay', 'PAREA Athens', D3, T(15), D5, T(10, 30),
             address='8 Pittaki, Athens, 10554, Greece')
cy310 = bk('flight', 'Cyprus Airways CY310', D3, T(8, 25), D3, T(10, 20),
           'Larnaca (LCA)', 'Athens (ATH)')
fr4519 = bk('flight', 'Ryanair FR4519 Athens-Dublin', D5, T(15), D5,
            T(17, 25), 'Athens (ATH)', 'Dublin (DUB)')
car = bk('car', 'Enterprise car hire Dublin Airport', D5, T(16), D9,
         T(17, 30), address='Dublin Airport')
galway = bk('stay', 'Clybaun Hotel Galway', D5, T(16), D9, T(11, 30),
            address='Clybaun Road, Knocknacarra, Salthill, Galway, Ireland')
fr4518 = bk('flight', 'Ryanair FR4518 Dublin-Athens', D9, T(18, 20), D10,
            T(0, 35), 'Dublin (DUB)', 'Athens (ATH)')
athens2 = bk('stay', 'PAREA Athens', D9, T(15), dt.date(2026, 11, 11),
             T(11), address='8 Pittaki, Athens, 10554, Greece')
ALL = [athens1, cy310, fr4519, car, galway, fr4518, athens2]


def names(day):
    return ['%s %s' % (r.what, r.title) for r in on_day(ALL, day)]


got = names(D9)
ok(got == ['end Clybaun Hotel Galway',
           'end Enterprise car hire Dublin Airport',
           'start Ryanair FR4518 Dublin-Athens', 'start PAREA Athens'],
   'THE 9th (Demetri): check out, drop off the car, fly Ryanair, THEN '
   'check in', got)
r9 = on_day(ALL, D9)[-1]
ok(r9.arrive == T(0, 35) and r9.arrive_next and r9.after.title.startswith(
    'Ryanair FR4518'),
   '  the check-in says when you land - 00:35, after midnight')
got = names(D5)
ok(got == ['end PAREA Athens', 'start Ryanair FR4519 Athens-Dublin',
           'start Enterprise car hire Dublin Airport',
           'start Clybaun Hotel Galway'],
   'THE 5th: check out, fly to Dublin, pick up the car, then check in in '
   'Galway (no flight lands in Galway - the last one to land counts)', got)
got = names(D3)
ok(got == ['start Cyprus Airways CY310', 'start PAREA Athens'] and
   on_day(ALL, D3)[-1].arrive is None,
   'THE 3rd: CY310 lands 10:20, before the 15:00 check-in - nothing moves')
home = bk('stay', 'Hotel Lisbon', D3, T(9), D5, T(11),
          address='Rua Augusta, Lisbon')
out_ = bk('flight', 'TAP Lisbon-Porto', D3, T(12), D3, T(13),
          'Lisbon (LIS)', 'Porto (OPO)')
ok([r.title for r in on_day([home, out_], D3)] ==
   ['Hotel Lisbon', 'TAP Lisbon-Porto'] and
   on_day([home, out_], D3)[0].arrive is None,
   'A FLIGHT OUT OF THE HOTEL\'S OWN TOWN does not move the check-in')

rows = [NS(pk=1, is_place=False, what='start'),
        NS(pk=2, is_place=False, what='end'), NS(pk=3, is_place=True),
        NS(pk=4, is_place=False, what='start')]
auto = [DO.key(r) for r in rows]
out, custom = DO.ordered(rows, ['p3', 'b4-start', 'b1-start'])
ok([DO.key(r) for r in out] == ['p3', 'b2-end', 'b4-start', 'b1-start']
   and custom,
   'YOUR ORDER over the automatic one; a row not in it (b2) keeps its slot',
   [DO.key(r) for r in out])
out, custom = DO.ordered(rows, auto)
ok(not custom, '  the same as automatic -> not called "Your order"')
ok(DO.ordered(rows, [])[0] == rows and DO.ordered(rows, ['zz'])[0] == rows,
   '  nothing saved, or only strangers -> the automatic order')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, DayOrder, Place, Trip
    connection.ensure_connection()
    DayOrder.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('tv9a', 'tv9a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            t = Trip.objects.create(owner=u, name='TV9 Ireland')
            mk = dict(trip=t, added_by=u)
            Booking.objects.create(
                kind='stay', title='Clybaun Hotel Galway', start_date=D5,
                start_time=T(16), end_date=D9, end_time=T(11, 30),
                address='Clybaun Road, Galway, Ireland', **mk)
            Booking.objects.create(
                kind='car', title='Enterprise Dublin Airport', start_date=D5,
                start_time=T(16), end_date=D9, end_time=T(17, 30),
                address='Dublin Airport', **mk)
            Booking.objects.create(
                kind='flight', title='Ryanair FR4518', start_date=D9,
                start_time=T(18, 20), end_date=D10, end_time=T(0, 35),
                from_place='Dublin (DUB)', to_place='Athens (ATH)', **mk)
            parea = Booking.objects.create(
                kind='stay', title='PAREA Athens', start_date=D9,
                start_time=T(15), end_date=dt.date(2026, 11, 11),
                end_time=T(11), address='8 Pittaki, Athens, Greece', **mk)
            Place.objects.create(trip=t, name='Kylemore Abbey', day=D9)
            url = '/travel/%d/itinerary/' % t.pk

            def day9(h):
                return h.split('id="d20261109"', 1)[1].split(
                    '</section>', 1)[0]
            h = day9(A.get(url).content.decode())
            ok(h.index('Clybaun') < h.index('Enterprise') <
               h.index('FR4518') < h.index('PAREA') < h.index('Kylemore'),
               'THE 9th on the computer: check out, car, Ryanair, check in, '
               'then the place with no time')
            ok('After you land, about 00:35 (after midnight)' in h and
               'check-in from 15:00' in h, '  "After you land, about 00:35"')
            ok(h.count('data-grip') == 5 and 'data-custom-order' not in h,
               '  a grip on every row; not "Your order" yet')
            keys = [k.split('"')[0] for k in h.split('data-key="')[1:]]
            mine = [keys[3], keys[4]] + keys[:3] + ['b999-start', 'junk']
            r = A.post('/travel/%d/day-order/' % t.pk,
                       {'day': '2026-11-09', 'keys': ','.join(mine)},
                       HTTP_X_REQUESTED_WITH='fetch')
            o = DayOrder.objects.get(trip=t, day=D9)
            ok(r.status_code == 200 and r.json()['ok'] and
               o.keys.split(',') == mine[:5],
               'DRAG on the computer: the day\'s order saved; keys not of '
               'the day dropped')
            h = day9(A.get(url).content.decode())
            ok(h.index('PAREA') < h.index('Kylemore') < h.index('Clybaun')
               and 'data-custom-order' in h and 'data-order-reset' in h,
               '  the itinerary in that order, "Your order · Back to '
               'automatic"')
            hm = M.get('/travel/m/trip/%d/?tab=itinerary' % t.pk
                       ).content.decode()
            m9 = hm.split('id="d20261109"', 1)[1].split('</section>', 1)[0]
            ok(m9.index('PAREA') < m9.index('Clybaun') and
               'data-order-change' in hm and 'data-order-reset' in hm,
               'THE PHONE shows the same order, with Change order')
            hm = M.get('/travel/m/trip/%d/?tab=itinerary&order=2026-11-09'
                       % t.pk).content.decode()
            ok(hm.count('data-order-up') == 5 and 'data-order-done' in hm,
               '  Change order: up / down on each row of the day, Done')
            k_parea = 'b%d-start' % parea.pk
            r = M.post('/travel/m/trip/%d/day-order/' % t.pk,
                       {'day': '2026-11-09', 'move': k_parea, 'dir': 'down',
                        'next': '/travel/m/trip/%d/?tab=itinerary&order='
                                '2026-11-09' % t.pk})
            o.refresh_from_db()
            ok(r.status_code == 302 and o.keys.split(',')[1] == k_parea and
               'order=2026-11-09' in r['Location'],
               '  DOWN on the phone moves it one place, and stays on the day')
            r = A.post('/travel/%d/day-order/' % t.pk,
                       {'day': '2026-11-09', 'reset': '1', 'next': url})
            h = day9(A.get(url).content.decode())
            ok(not DayOrder.objects.filter(trip=t, day=D9).exists() and
               h.index('Clybaun') < h.index('PAREA') and
               'data-custom-order' not in h,
               'BACK TO AUTOMATIC: the order gone, time order again')
            other = User.objects.create_user('tv9b', 'tv9b@example.com', 'x')
            other.user_permissions.add(perm)
            B = Client(SERVER_NAME='localhost')
            B.force_login(other)
            ok(B.post('/travel/%d/day-order/' % t.pk,
                      {'day': '2026-11-09', 'reset': '1'}).status_code == 404
               and A.get('/travel/%d/day-order/' % t.pk).status_code == 405,
               'SOMEONE ELSE\'S trip cannot be reordered; POST only')
            t.shared_with.add(other)
            r = B.post('/travel/%d/day-order/' % t.pk,
                       {'day': '2026-11-09', 'keys': k_parea},
                       HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 200 and DayOrder.objects.get(
                trip=t, day=D9).keys.startswith(k_parea),
               'FAMILY on the trip can put it in order too (one order for all)')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('dayorder' not in was(J(TA, 'phone.py')),
       'before this round: a day in plain time order - check-in 15:00 '
       'before the 18:20 flight')
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
