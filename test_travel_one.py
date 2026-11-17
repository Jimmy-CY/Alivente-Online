# -*- coding: utf-8 -*-
"""test_travel_one.py - round TR-1, 15 Nov 2026.

RELEASE 82 - TRAVEL, STAGE 1. Demetri, 15 Nov: trips of his own, shared
like meal plans ("Non-shared trips will be unique to that one user");
bookings with every detail - reference, dates, addresses, phone, paid or
unpaid; costs in the original currency "but also a conversion to Euros";
the tickets attached. Under Personal on the desktop; its own app, as
Wellness is.
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

SUFFIX = '.bak_travel1'
ME = 'test_travel_one.py'
PATCHER = 'apply_travel_one.py'
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
st = read(J(ROOT, 'mysite', 'settings.py'))
ok('    "travel",\n' in st, 'travel is an installed app')
ok('path("travel/", include("travel.urls"))' in read(J(ROOT, 'mysite',
                                                         'urls.py')),
   'mounted at /travel/')
ok("'codename': 'can_access_travel'" in read(J(ROOT, 'pages',
                                              'permissions.py')),
   'its own permission, can_access_travel')
ok("('travel', 'auth.can_access_travel')" in read(J(ROOT, 'pages',
                                                   'middleware.py')),
   'the middleware guards it')
pe = read(J(ROOT, 'pages', 'templates', 'personal.html'))
ok("{% url 'travel:trips' %}" in pe and '{% if perms_map.travel %}' in pe,
   'PERSONAL: a Travel tile, for those who have it')
ok(pe.index('perms_map.passports') < pe.index('perms_map.travel') <
   pe.index('perms_map.recipes') and
   'admin-btn btn-personal admin-btn-wide' in pe and
   '.admin-grid .admin-btn-wide { grid-column: 1 / -1; }' in pe,
   '  beside Passports; Wellness across the bottom')
ok(read(J(ROOT, 'pages', 'templates', 'base.html')).count(
    'or perms.auth.can_access_travel or perms.auth.can_access_wellness %}')
   == 2, 'both menus show Personal for it')
v = read(J(TA, 'views.py'))
ok('return get_object_or_404(trips_for(request.user), pk=trip_id)' in v,
   'every trip is looked up through trips_for - the one door')
ok("'travel/%s/%s' % (uuid.uuid4().hex, base)" in read(J(TA, 'models.py')),
   'files under a random folder, served through a checked view')
for name in ('trips', 'trip', 'booking', 'booking_form', 'trip_form',
             'share'):
    ok(os.path.isfile(J(TT, name + '.html')), 'template %s.html' % name)

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from decimal import Decimal                                 # noqa: E402
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.core.files.uploadedfile import SimpleUploadedFile
    from pages.models import UserProfile
    from travel.models import Booking, BookingFile, Trip
    connection.ensure_connection()
    Trip.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
    import tempfile
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    _dj.MEDIA_ROOT = tempfile.mkdtemp(prefix='tv1-')
    from pages.workspace import ensure_workspace
    import travel.fx as FX
    FX.fetch = lambda day, cur: {'GBP': Decimal('0.85')}.get(cur)

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            p, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            us = {}
            for n in ('tva', 'tvb', 'tvc', 'tvd'):
                u = User.objects.create_user(n, n + '@example.com', 'x',
                                             first_name=n.upper())
                if n != 'tvd':
                    u.user_permissions.add(p)
                us[n] = u
            ws = ensure_workspace(us['tva'])
            cl = {}
            for n, u in us.items():
                UserProfile.objects.update_or_create(
                    user=u, defaults={'workspace': ws})
                c = Client(SERVER_NAME='localhost')
                c.force_login(u)
                cl[n] = c
            A, B, C, D = cl['tva'], cl['tvb'], cl['tvc'], cl['tvd']

            r = D.get('/travel/')
            ok(r.status_code in (302, 403), 'WITHOUT Travel: no way in',
               r.status_code)
            r = A.get('/travel/')
            ok(r.status_code == 200 and 'No trips yet' in r.content.decode(),
               'TRIPS: an empty list to start')
            r = A.post('/travel/new/', {'name': 'TV Lisbon',
                                        'start_date': '2030-05-08',
                                        'end_date': '2030-05-15',
                                        'countries': 'Portugal'})
            t = Trip.objects.get(name='TV Lisbon')
            ok(r.status_code == 302 and t.owner == us['tva'],
               'NEW TRIP: made, and it is A\'s')
            u = '/travel/%d/' % t.pk
            ok(B.get(u).status_code == 404 and C.get(u).status_code == 404,
               '  nobody else can open it - not shared')

            r = A.post(u + 'booking/new/', {
                'kind': 'stay', 'title': 'TV Casa', 'provider': 'Booking.com',
                'reference': 'R-1', 'start_date': '2030-05-08',
                'start_time': '15:00', 'end_date': '2030-05-11',
                'address': 'Largo 12', 'phone': '+351 1', 'amount': '400',
                'currency': 'GBP', 'paid': 'part', 'paid_amount': '100',
                'cancel_until': '2030-05-06', 'link': 'example.com/x',
                'files': SimpleUploadedFile('conf.pdf', b'%PDF-1.4 test',
                                            content_type='application/pdf')})
            b = Booking.objects.get(title='TV Casa')
            ok(r.status_code == 302 and b.amount_eur == Decimal('470.59') and
               b.fx_rate == Decimal('0.85') and b.currency == 'GBP',
               'BOOKING: £400 kept, and €470.59 at the day\'s rate',
               (b.amount_eur, b.fx_rate))
            ok(b.paid_eur == Decimal('117.65') and
               b.due_eur == Decimal('352.94') and
               b.link == 'https://example.com/x',
               '  part paid: £100 is €117.65, €352.94 still to pay')
            f = b.files.get()
            ok(f.file.name.startswith('travel/') and f.name == 'conf.pdf',
               '  the PDF is attached')
            ok(A.get('/travel/file/%d/' % f.pk).status_code == 200 and
               C.get('/travel/file/%d/' % f.pk).status_code == 404,
               '  and only the trip\'s people can open it')

            A.post(u + 'booking/new/', {
                'kind': 'flight', 'title': 'TV TP 1307', 'from_place': 'LCA',
                'to_place': 'LIS', 'start_date': '2030-05-08',
                'start_time': '06:40', 'amount': '612', 'currency': 'EUR',
                'paid': 'paid'})
            h = A.get(u).content.decode()
            ok(h.count('data-booking') >= 2 and 'TV TP 1307' in h and
               '€1,082.59' in h and '€729.65' in h,
               'TRIP PAGE: both on Sat 8 May, total €1,082.59, €729.65 '
               'paid')
            ok('Free cancellation ends' in h, '  the cancellation deadline '
               'is coming up')
            h = A.get(u + 'costs/').content.decode()
            ok('data-costs' in h and '£' not in h and '400.00 GBP' in h,
               'COSTS: each in euros, the original underneath')

            A.post('/travel/booking/%d/edit/' % b.pk, {
                'kind': 'stay', 'title': 'TV Casa', 'amount': '400',
                'reference': 'R-1', 'start_date': '2030-05-08',
                'start_time': '16:00', 'currency': 'GBP',
                'amount_eur': '466.10', 'paid': 'paid'})
            b.refresh_from_db()
            ok(b.amount_eur == Decimal('466.10') and b.eur_typed,
               'CARD AMOUNT typed in euros wins over the rate')
            ch = b.changes.get()
            got = {x['label']: (x['old'], x['new']) for x in ch.changes}
            ok(got.get('Start time') == ('15:00', '16:00') and
               got.get('Paid?') == ('Part paid', 'Paid') and
               got.get('In euros') == ('470.59', '466.10') and ch.by == us['tva'],
               'CHANGES: the edit is kept as a trail - old and new', got)
            h = A.get('/travel/booking/%d/' % b.pk).content.decode()
            ok('data-booking-changes' in h and 'Changes (1)' in h and
               '15:00' in h and '16:00' in h,
               '  and the booking shows it under Changes')
            r = A.post(u + 'booking/new/', {'kind': 'stay',
                                             'title': 'TV Casa again',
                                             'reference': 'r-1',
                                             'currency': 'EUR'})
            h = r.content.decode()
            ok(r.status_code == 200 and 'already on this trip' in h and
               not Booking.objects.filter(title='TV Casa again').exists(),
               'DUPLICATE: the same reference again is stopped, with the '
               'one it matches')
            r = A.post(u + 'booking/new/', {'kind': 'stay',
                                             'title': 'TV Casa again',
                                             'reference': 'r-1',
                                             'currency': 'EUR',
                                             'dupe_ok': '1'})
            ok(Booking.objects.filter(title='TV Casa again').exists(),
               '  and saved only when the person says so')
            Booking.objects.filter(title='TV Casa again').delete()

            r = B.get(u + 'share/')
            ok(r.status_code == 404, 'only the owner shares')
            r = A.get(u + 'share/').content.decode()
            ok('TVB' in r and 'TVC' in r and 'TVD' not in r,
               'SHARE: with people who have Travel')
            A.post(u + 'share/', {'people': [us['tvb'].pk]})
            ok(B.get(u).status_code == 200 and C.get(u).status_code == 404,
               '  shared with B: B opens it, C still cannot')
            h = B.get('/travel/').content.decode()
            ok('TV Lisbon' in h and 'Shared' in h,
               '  and it is in B\'s list, marked shared')
            r = B.post(u + 'booking/new/', {'kind': 'car', 'title': 'TV Car',
                                             'amount': '196',
                                             'currency': 'EUR',
                                             'paid': 'paid'})
            ok(Booking.objects.filter(title='TV Car', trip=t,
                                      added_by=us['tvb']).exists(),
               '  B adds a booking to it')
            ok(B.post(u + 'delete/').status_code == 404 and
               Trip.objects.filter(pk=t.pk).exists(),
               '  but cannot delete the trip')
            A.post(u + 'delete/')
            ok(not Trip.objects.filter(pk=t.pk).exists() and
               not BookingFile.objects.filter(pk=f.pk).exists(),
               'DELETE: the owner deletes it, bookings and files with it')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('"travel"' not in was(J(ROOT, 'mysite', 'settings.py')),
       'before this round: no Travel')
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
