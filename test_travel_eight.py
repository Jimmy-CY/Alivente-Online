# -*- coding: utf-8 -*-
"""test_travel_eight.py - round TR-8, 16 Nov 2026.

RELEASE 88 - TRAVEL: BOARDING PASSES - NEXT, COMING UP, USED.
Demetri, 16 Nov: "Selection is hidden at the bottom"; "Your Boarding Pass
must always come first"; "Always you pass first. Keep forever, but stamp
them USED in red diagonally across (also grey out the QR Code)"; "What
happens if a flight is drastically delayed"; "if I fly to Greece (1hr40min)
and then I connect within 2 hours to Dublin. The 8 hours will be an
issue"; Add to Google Wallet after the flight - "give a nice message ...
Not have the system error out".
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

SUFFIX = '.bak_travel8'
ME = 'test_travel_eight.py'
PATCHER = 'apply_travel_eight.py'
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
ok("marked = models.CharField(max_length=8, blank=True, default='')" in md
   and 'marked_at = models.DateTimeField(null=True, blank=True)' in md and
   os.path.isfile(J(TA, 'migrations', '0007_pass_marks.py')),
   'MODEL: a pass put right by hand - Done with this pass / Not flown yet '
   '(0007)')
u = read(J(TA, 'urls.py'))
ok(all("name='%s'" % n in u for n in ('pass_wallet', 'pass_mark',
                                      'm_pass_wallet', 'm_pass_mark')),
   'routes: the Wallet page and the two buttons, computer and phone')
mp = read(J(TT, 'm', 'passes.html'))
ok(0 <= mp.find('data-pass-tabs') < mp.find('{% block content %}'),
   'PHONE: the tabs are AT THE TOP, above the passes ("Selection is hidden '
   'at the bottom")')
dp = read(J(TT, 'passes.html'))
ok(0 <= dp.find('data-pass-tabs') < dp.find('data-tab-panel="next"'),
   'COMPUTER: the same three tabs at the top')
css = read(J(TA, 'assets', 'travel.css')) + read(J(TT, '_style.html'))
ok('rotate(-28deg)' in css and '#C62828' in css and
   '.is-used .tv-code-box { opacity: .22; filter: grayscale(1); }' in css,
   'USED: stamped in red, diagonally; the barcode greyed')
ok(all('travel:pass_wallet' in read(J(TT, x)) or
       'travel:m_pass_wallet' in read(J(TT, x))
       for x in ('booking.html', '_pass_desk.html', J('m', '_pass.html'))) and
   'p.wallet_link }}"' not in read(J(TT, '_pass_desk.html')) + read(
       J(TT, 'm', '_pass.html')) + read(J(TT, 'booking.html')),
   'GOOGLE WALLET: every button goes through Alivente first, never '
   'straight to the airline\'s link')
ph = read(J(TA, 'phone.py'))
ok("SW_VERSION = 'tv8-1'" in ph and 'travel.js\' %}?v=tv8-1' in read(
    J(TT, 'm', 'base.html')),
   'the phone fetches the new script (worker and page agree on tv8-1)')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
mh = read(J(TT, 'm', 'help.html'))
ok('<strong>Done with this pass</strong>' in hp and
   '<strong>Earlier today</strong>' in hp and
   'airlines stop offering passes to Google Wallet' in hp and
   '<b>Not flown yet</b>' in mh and 'three tabs' in hp.lower(),
   'HELP: the tabs, USED, connections, the two buttons, Google Wallet')

# ==========================================================================
head('2. THE RULES (travel/boarding.py)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from types import SimpleNamespace as NS                     # noqa: E402
from travel import boarding as BD                           # noqa: E402

DAY = dt.date(2026, 12, 18)
me = NS(first_name='Demetri', last_name='Manias', username='dm',
        get_full_name=lambda: 'Demetri Manias')
ok(BD.is_me('Dimitrios Manias', me) and BD.is_me('MANIAS DIMITRIOS', me)
   and not BD.is_me('Alexandra Mania', me) and
   not BD.is_me('Erene Mania', me),
   'YOUR PASS: Demetri Manias is the pass\'s Dimitrios Manias; Alexandra '
   'and Erene are not')
_n = [0]


def card(name, flight, day, leaves, lands=None, marked='', marked_at=None,
         lands_day=None):
    _n[0] += 1
    b = NS(pk=_n[0], start_date=day, start_time=leaves, end_time=lands,
           end_date=lands_day)
    return NS(pk=_n[0], name=name, flight=flight, booking=b, marked=marked,
              marked_at=marked_at)


def at(h, m=0, day=DAY):
    return dt.datetime.combine(day, dt.time(h, m))


def run(cards, now):
    return BD.settle(cards, now, me)


fam = [card('Alexandra Mania', 'CY 326', DAY, dt.time(10), dt.time(11, 40)),
       card('Dimitrios Manias', 'CY 326', DAY, dt.time(10), dt.time(11, 40)),
       card('Erene Mania', 'CY 326', DAY, dt.time(10), dt.time(11, 40))]
n, c, us, e, t = run(fam, at(7))
ok([p.name for p in n] == ['Dimitrios Manias', 'Alexandra Mania',
                           'Erene Mania'],
   'ALWAYS YOUR PASS FIRST, then the family on the same flight',
   [p.name for p in n])

# Demetri's connection: LCA-ATH 10:00-11:40, ATH-DUB 13:40-16:30.
def conn():
    return [card('Dimitrios Manias', 'CY 326', DAY, dt.time(10),
                 dt.time(11, 40)),
            card('Dimitrios Manias', 'A3 610', DAY, dt.time(13, 40),
                 dt.time(16, 30))]


x = conn()
n, c, us, e, t = run(x, at(9))
ok([p.flight for p in n] == ['CY 326'] and t is x[1] and
   [p.flight for p in c] == ['A3 610'],
   'CONNECTION, before boarding: Athens is Next, and "Then: ATH -> DUB" is '
   'one tap away under it')
x = conn()
n, c, us, e, t = run(x, at(11, 41))
ok([p.flight for p in n] == ['A3 610'] and e is x[0] and
   not x[0].stamped,
   'CONNECTION, at Athens\' landing time: Dublin is Next, Athens one tap '
   'away as "Earlier today", not stamped (Demetri: "The 8 hours will be an '
   'issue")')
x = conn()
n, c, us, e, t = run(x, at(17, 41))
ok(x[0].stamped and not x[1].stamped and [p.flight for p in n] ==
   ['A3 610'],
   '  Athens stamped USED six hours after it was due to land')
x = conn()
n, c, us, e, t = run(x, at(22, 0))
ok([p.flight for p in n] == ['A3 610'] and not x[1].handed,
   'LAST FLIGHT DELAYED: Dublin (due 16:30) is still Next at 22:00')
x = conn()
n, c, us, e, t = run(x, at(22, 31))
ok(not n and x[1].stamped and us[0] is x[1],
   '  and USED at 22:31 - six hours after it was due - newest first')
ok(x[1].over and x[0].over, '  Google Wallet then explains instead of '
   'sending you to the airline')
y = [card('Dimitrios Manias', 'CY 999', DAY, dt.time(10))]
ok(run(y, at(17, 59))[0] and not run(y, at(18, 1))[0],
   'NO LANDING TIME: used eight hours after it left')
y = [card('Dimitrios Manias', 'CY 998', DAY, dt.time(23, 50),
          dt.time(1, 10))]
ok(run(y, at(6, 0, DAY + dt.timedelta(days=1)))[0] and
   not run(y, at(7, 11, DAY + dt.timedelta(days=1)))[0],
   'LANDS AFTER MIDNIGHT: counted from the next morning\'s landing')
now = at(9)
x = conn()
x[0].marked, x[0].marked_at = 'used', now
n, c, us, e, t = run(x, now)
ok([p.flight for p in n] == ['A3 610'] and x[0].stamped,
   'DONE WITH THIS PASS: moves on at once')
x = conn()
x[1].marked, x[1].marked_at = 'open', at(22, 40)
n, c, us, e, t = run(x, at(23, 0))
ok([p.flight for p in n] == ['A3 610'] and not x[1].stamped,
   'NOT FLOWN YET: a used pass back to Next (a big delay)')
n, c, us, e, t = run(x, at(22, 41, DAY + dt.timedelta(days=1)))
ok(not n and x[1].stamped, '  for a day, then the clock again')
z = [card('Dimitrios Manias', 'CY 326', DAY - dt.timedelta(days=5),
          dt.time(10), dt.time(11, 40))]
n, c, us, e, t = run(z, at(9))
ok(not n and us and us[0].stamped,
   'NOTHING AHEAD: no old pass passed off as Next (CY 313 of 11 Nov on '
   '16 Nov)')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import Booking, BoardingPass, Trip
    connection.ensure_connection()
    BoardingPass.objects.filter(marked='').exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')


def code(name, frm, to, car, num, seat):
    return ('M1' + name.ljust(20) + 'E' + 'ABC123 ' + frm + to +
            car.ljust(3) + num.rjust(4, '0') + ' ' + '186' + 'Y' +
            seat.rjust(4, '0') + '0045 ' + '1' + '00')


if have_db:
    from django.conf import settings as _dj
    from django.utils import timezone
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('tv8a', 'tv8a@example.com', 'x',
                                         first_name='Demetri',
                                         last_name='Manias')
            u.user_permissions.add(perm)
            ws = ensure_workspace(u)
            UserProfile.objects.update_or_create(user=u,
                                                 defaults={'workspace': ws})
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            today = timezone.localdate()
            tr = Trip.objects.create(owner=u, name='TV8 Ireland')
            old = Booking.objects.create(
                trip=tr, kind='flight', title='Cyprus Airways CY 313',
                provider='Cyprus Airways', start_date=today - dt.timedelta(
                    days=5), start_time=dt.time(10), end_time=dt.time(12),
                added_by=u)
            gone = BoardingPass.objects.create(
                booking=old, name='Dimitrios Manias',
                code=code('MANIAS/DIMITRIOS', 'LCA', 'DUB', 'CY', '313',
                          '12A'), format='aztec',
                wallet_link='https://pay.google.com/gp/v/save/old')
            h = M.get('/travel/m/passes/').content.decode()
            ok('data-no-next' in h and 'Your last pass was' in h and
               'data-next' not in h.replace('data-no-next', ''),
               'NOTHING AHEAD on the phone: "No flight coming up · your '
               'last pass was ..." - never an old pass as Next')
            ok('data-used-stamp' in h and 'data-show-anyway' in h and
               'Used · 1' in h and 'data-pass-notyet' not in h,
               'USED tab: the pass kept, stamped, "Show the barcode '
               'anyway" - and five days on, no "Not flown yet"')
            r = M.get('/travel/m/pass/%d/wallet/' % gone.pk)
            hw = r.content.decode()
            ok(r.status_code == 200 and 'data-wallet-over' in hw and
               'already flown' in hw and 'pay.google.com' not in hw,
               'GOOGLE WALLET after the flight: a friendly page, not the '
               'airline\'s error (Demetri, 16 Nov)')
            r = A.get('/travel/pass/%d/wallet/' % gone.pk)
            ok(r.status_code == 200 and 'already flown' in r.content.decode()
               and 'data-travel-help' in r.content.decode(),
               '  and on the computer, with Help')

            nxt = Booking.objects.create(
                trip=tr, kind='flight', title='Cyprus Airways CY 326',
                provider='Cyprus Airways', start_date=today + dt.timedelta(
                    days=2), start_time=dt.time(10), end_time=dt.time(11, 40),
                added_by=u)
            con = Booking.objects.create(
                trip=tr, kind='flight', title='Aegean A3 610',
                provider='Aegean', start_date=today + dt.timedelta(days=2),
                start_time=dt.time(13, 40), end_time=dt.time(16, 30),
                added_by=u)
            her = BoardingPass.objects.create(
                booking=nxt, name='Alexandra Mania',
                code=code('MANIA/ALEXANDRA', 'LCA', 'ATH', 'CY', '326',
                          '12B'), format='aztec')
            mine = BoardingPass.objects.create(
                booking=nxt, name='Dimitrios Manias',
                code=code('MANIAS/DIMITRIOS', 'LCA', 'ATH', 'CY', '326',
                          '12A'), format='aztec',
                wallet_link='https://pay.google.com/gp/v/save/new')
            BoardingPass.objects.create(
                booking=con, name='Dimitrios Manias',
                code=code('MANIAS/DIMITRIOS', 'ATH', 'DUB', 'A3', '610',
                          '03C'), format='aztec')
            h = M.get('/travel/m/passes/').content.decode()
            panel = h.split('data-tab-panel="next"', 1)[1].split(
                'data-tab-panel="coming"', 1)[0]
            ok(panel.count('data-pass ') == 2 and h.count('data-next') == 1
               and panel.find('Dimitrios Manias') < panel.find(
                   'Alexandra Mania'),
               'NEXT: both passes of the flight to swipe between, yours '
               'first')
            ok('data-then' in panel and 'ATH &rarr; DUB' in panel,
               '  "Then: ATH -> DUB" under it (the connection)')
            ok('Coming up · 1' in h and 'Used · 1' in h,
               '  Coming up 1, Used 1')
            r = M.get('/travel/m/pass/%d/wallet/' % mine.pk)
            ok(r.status_code == 302 and r['Location'] ==
               'https://pay.google.com/gp/v/save/new',
               'GOOGLE WALLET before the flight: straight on to the airline')
            r = M.post('/travel/m/pass/%d/used/' % mine.pk)
            mine.refresh_from_db()
            h = M.get('/travel/m/passes/').content.decode()
            panel = h.split('data-tab-panel="next"', 1)[1].split(
                'data-tab-panel="coming"', 1)[0]
            ok(r.status_code == 302 and mine.marked == 'used' and
               'Alexandra Mania' in panel and panel.count('data-pass ') == 1
               and 'Dimitrios Manias' not in panel.split('data-then')[0],
               'DONE WITH THIS PASS: yours moves to Used; Alexandra\'s, on '
               'the same flight, stays')
            ok('data-pass-notyet' in h, '  and a just-used pass offers '
               '"Not flown yet"')
            r = M.post('/travel/m/pass/%d/open/' % mine.pk)
            mine.refresh_from_db()
            ok(mine.marked == 'open', 'NOT FLOWN YET puts it back')
            ok(M.get('/travel/m/pass/%d/elsewhere/' % mine.pk).status_code
               == 405 and M.post('/travel/m/pass/%d/elsewhere/'
                                 % mine.pk).status_code == 404,
               '  only the two marks, and only by POST')
            h = A.get('/travel/passes/').content.decode()
            ok('data-pass-tabs' in h and h.count('data-next') == 1 and
               'Next' in h and 'Coming up' in h and 'Used' in h,
               'COMPUTER: the same tabs and the same Next')
            h = A.get('/travel/passes/?tab=used').content.decode()
            ok('data-tab-panel="used">' in h,
               '  ?tab=used opens on Used')
            other = User.objects.create_user('tv8b', 'tv8b@example.com', 'x')
            other.user_permissions.add(perm)
            B = Client(SERVER_NAME='localhost')
            B.force_login(other)
            ok(B.post('/travel/pass/%d/used/' % mine.pk).status_code == 404
               and B.get('/travel/pass/%d/wallet/' % mine.pk).status_code
               == 404, 'SOMEONE ELSE\'S pass cannot be marked or opened')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok("'used'" not in was(J(TA, 'phone.py')),
       'before this round: no Used, the old flight came back as Next')
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
