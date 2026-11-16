# -*- coding: utf-8 -*-
"""test_travel_six.py - round TR-6, 16 Nov 2026.

RELEASE 87 - A STAY'S COST ONCE, ON THE ITINERARY.
Demetri, 16 Nov: "I don't think that we should have the cost (e.g. for
PAREA 270.28) showing three times for three nights. This is the total for
the 3 nights, and this looks deceiving."
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

SUFFIX = '.bak_travel6'
ME = 'test_travel_six.py'
PATCHER = 'apply_travel_six.py'
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
row = read(J(TT, '_booking_row.html'))
ok("{% if b.what == 'during' or b.what == 'end' %}{% elif b.amount is not None %}"
   in row and 'data-stay-total' in row,
   'THE ROW: no cost on the days after check-in; "for N nights" on it')
ok('b.night = (day - b.start_date).days + 1' in read(J(TA, 'phone.py')),
   '  which night of the stay a day is')
tr = read(J(TT, 'trip.html'))
ok('<i class="fas fa-plus"></i> Things to do</a>' in tr and
   'Add a place</a>' not in tr and
   '>+ Things to do</a>' in read(J(TT, 'm', 'trip.html')),
   'THE BUTTON is "+ Things to do" (Demetri, 16 Nov), on the computer and '
   'the phone')
ok('shown once, on the check-in day' in read(J(ROOT, 'pages', 'help_content',
                                                  'administration.html')),
   'HELP says so')

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
    from travel.models import Booking, Trip
    from travel import places as PL
    connection.ensure_connection()
    Booking.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

if have_db:
    import datetime as dt
    from decimal import Decimal
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
            u = User.objects.create_user('tv6a', 'tv6a@example.com', 'x')
            u.user_permissions.add(perm)
            ws = ensure_workspace(u)
            UserProfile.objects.update_or_create(user=u,
                                                 defaults={'workspace': ws})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            day = timezone.localdate() + dt.timedelta(days=20)
            t = Trip.objects.create(owner=u, name='TV6 Athens')
            Booking.objects.create(
                trip=t, kind='stay', title='TV6 PAREA', added_by=u,
                start_date=day, end_date=day + dt.timedelta(days=3),
                start_time=dt.time(15, 0), end_time=dt.time(11, 0),
                amount=Decimal('405.42'), amount_eur=Decimal('405.42'),
                currency='EUR', paid='paid', web_checked=timezone.now())
            h = A.get('/travel/%d/itinerary/' % t.pk).content.decode()

            def sec(n):
                return h.split('id="d%s"' % (day + dt.timedelta(days=n))
                               .strftime('%Y%m%d'), 1)[1] \
                    .split('</section>')[0]
            ok(h.count('405.42') == 1 and '405.42' in sec(0) and
               'for 3 nights' in sec(0),
               'THE COST ONCE: on the check-in day, "for 3 nights"',
               h.count('405.42'))
            ok('Night 2 of 3' in sec(1) and 'Night 3 of 3' in sec(2),
               '  the days between say which night')
            ok('Check out by 11:00' in sec(3) and '15:00' not in sec(3),
               '  check-out day: the check-out time, not the check-in one')
            h = A.get('/travel/%d/' % t.pk).content.decode()
            ok(h.count('405.42') == 3 and h.count('data-booking ') +
               h.count('data-booking>') == 1,
               '  the Bookings tab: the stay once, then Total and Paid',
               h.count('405.42'))
            raise Rollback
    except Rollback:
        pass
    finally:
        PL.call_details = real_details

# ==========================================================================
head('3. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('data-stay-total' not in was(J(TT, '_booking_row.html')),
       'before this round: the cost on every day of a stay')
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
