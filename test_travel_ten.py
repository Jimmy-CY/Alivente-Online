# -*- coding: utf-8 -*-
"""test_travel_ten.py - round TR-10, 16 Nov 2026.

RELEASE 90 - TRAVEL: DRAG A DAY INTO ORDER, ON THE PHONE TOO.
Demetri, 16 Nov 17:40: "I am not happy how the sorting happens on the
mobile. It is cumbersome and not user intuitive." Agreed: a grip on every
row, drag it (the others slide aside, the page scrolls at the edge), saved
on release with "Order saved - Undo"; no separate mode, no up / down
buttons; the computer the same, without the reload.
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

SUFFIX = '.bak_travel10'
ME = 'test_travel_ten.py'
PATCHER = 'apply_travel_ten.py'
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
ro = read(J(TT, '_reorder.html'))
ok("addEventListener('pointerdown'" in ro and 'setPointerCapture' in ro and
   "e.target.closest('[data-grip]')" in ro,
   'ONE SCRIPT for phone and computer: pointer events, started only from '
   'the grip')
ok('translateY(' in ro and 'requestAnimationFrame(edge)' in ro and
   'window.scrollBy(0, v)' in ro,
   '  the row follows the finger, the others slide aside, the page scrolls '
   'at the top and bottom edge')
ok("say('Order saved'" in ro and 'data-order-undo' in ro and
   "post(box, {reset: '1'})" in ro,
   '  saved on release; "Order saved - Undo" (back to automatic if it was)')
ok("'ArrowUp'" in ro and "'ArrowDown'" in ro,
   '  arrow keys on a focused grip (keyboard)')
css = read(J(TA, 'assets', 'travel.css')) + read(J(TT, '_style.html'))
ok(css.count('touch-action: none') >= 2 and '.tv-toast' in css and
   '.tv-drag.is-lifted' in css,
   'CSS: the grip takes the touch (the row still scrolls); the lifted row; '
   'the Undo bar')
mt = read(J(TT, 'm', 'trip.html'))
ok('data-reorder' in mt and 'data-grip' in mt and
   "include 'travel/_reorder.html'" in mt and 'data-order-up' not in mt and
   'data-order-change' not in mt and 'order_day' not in mt,
   'PHONE: grips on the rows; "Change order" and the up / down buttons gone')
tp = read(J(TT, 'trip.html'))
ok('data-reorder' in tp and "include 'travel/_reorder.html'" in tp and
   'window.location.reload()' not in tp,
   'COMPUTER: the same script - no reload after a drop')
ok("'custom': bool(rows.custom)" in read(J(TA, 'views_places.py')),
   'the server says whether the day still differs from automatic')
ph = read(J(TA, 'phone.py'))
# TR-11 (17 Nov) moved the version on again: tv10-1 or later, worker and
# page agreeing.
import re                                                   # noqa: E402
_v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
ok(_v and int(_v.group(1)) >= 10 and
   '?v=tv%s-%s' % _v.groups() in read(J(TT, 'm', 'base.html')),
   'the phone fetches the new script and style (tv10-1 or later)')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
mh = read(J(TT, 'm', 'help.html'))
ok('Order saved &middot; Undo' in hp and 'hold the grip' in mh and
   'Change order' not in mh and '<strong>Change order</strong>' not in hp,
   'HELP: drag the grip; Undo; no "Change order"')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, DayOrder, Trip
    connection.ensure_connection()
    DayOrder.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')
T = dt.time
D9, D10 = dt.date(2026, 11, 9), dt.date(2026, 11, 10)

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
            u = User.objects.create_user('tv10a', 'tv10a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            t = Trip.objects.create(owner=u, name='TV10')
            mk = dict(trip=t, added_by=u)
            out = Booking.objects.create(
                kind='stay', title='Clybaun Galway', start_date=D9 -
                dt.timedelta(days=2), start_time=T(16), end_date=D9,
                end_time=T(11, 30), address='Galway, Ireland', **mk)
            fly = Booking.objects.create(
                kind='flight', title='Ryanair FR4518', start_date=D9,
                start_time=T(18, 20), end_date=D10, end_time=T(0, 35),
                from_place='Dublin (DUB)', to_place='Athens (ATH)', **mk)
            inn = Booking.objects.create(
                kind='stay', title='PAREA Athens', start_date=D9,
                start_time=T(15), end_date=D10 + dt.timedelta(days=1),
                end_time=T(11), address='Athens, Greece', **mk)
            ka, kb, kc = ('b%d-end' % out.pk, 'b%d-start' % fly.pk,
                          'b%d-start' % inn.pk)
            hm = M.get('/travel/m/trip/%d/?tab=itinerary' % t.pk
                       ).content.decode()
            m9 = hm.split('id="d20261109"', 1)[1].split('</section>', 1)[0]
            ok(m9.count('data-grip') == 3 and 'data-reorder' in m9 and
               'data-day="2026-11-09"' in m9 and
               'data-order-status="2026-11-09" hidden' in m9 and
               'csrfmiddlewaretoken' in m9,
               'PHONE: a grip on each of the 3 rows; "Your order" hidden '
               'until there is one')
            ok(m9.index('Clybaun') < m9.index('FR4518') <
               m9.index('PAREA'), '  automatic order to start with')
            m10 = hm.split('id="d20261110"', 1)[1].split('</section>', 1)[0]
            ok('data-grip' not in m10 and 'data-reorder' not in m10,
               '  a day with one row has nothing to drag')
            u9 = '/travel/m/trip/%d/day-order/' % t.pk
            r = M.post(u9, {'day': '2026-11-09', 'keys': ','.join(
                [kc, ka, kb])}, HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 200 and r.json()['custom'] is True and
               r.json()['keys'] == [kc, ka, kb],
               'DRAGGED (phone): saved, and "custom" - show "Your order"')
            m9 = M.get('/travel/m/trip/%d/?tab=itinerary' % t.pk
                       ).content.decode().split('id="d20261109"', 1)[1]
            m9 = m9.split('</section>', 1)[0]
            ok(m9.index('PAREA') < m9.index('Clybaun') and
               'data-order-status="2026-11-09" hidden' not in m9 and
               'data-custom="1"' in m9,
               '  the next visit shows it, with "Your order · Back to '
               'automatic"')
            r = M.post(u9, {'day': '2026-11-09', 'keys': ','.join(
                [ka, kb, kc])}, HTTP_X_REQUESTED_WITH='fetch')
            ok(r.json()['custom'] is False,
               'DRAGGED BACK into time order: "custom" false - "Your order" '
               'hides by itself')
            r = M.post(u9, {'day': '2026-11-09', 'reset': '1'},
                       HTTP_X_REQUESTED_WITH='fetch')
            ok(r.json()['ok'] and r.json()['custom'] is False and
               not DayOrder.objects.filter(trip=t, day=D9).exists(),
               'UNDO to automatic: the saved order removed')
            h = A.get('/travel/%d/itinerary/' % t.pk).content.decode()
            d9 = h.split('id="d20261109"', 1)[1].split('</section>', 1)[0]
            ok(d9.count('data-grip') == 3 and 'data-reorder' in d9 and
               '__tvReorder' in h,
               'COMPUTER: the same grips and the same script')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('data-order-up' in was(J(TT, 'm', 'trip.html')),
       'before this round: "Change order" and up / down buttons on the phone')
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
