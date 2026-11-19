# -*- coding: utf-8 -*-
"""test_ra05_budget.py - round RA05, 19 Nov 2026.

RELEASE RA05 - TRAVEL: THE DAILY SPENDING BUDGET, + SPENDING, AND SHARING
THE COSTS OR NOT.
Demetri, 19 Nov: "we only had the ability to set a budget for total
holiday spend (which would be a calculation based on average daily
spend). Then it keeps track of my actual daily spend vs. the budgeted one
and shows me if I am ahead or behind the schedule. Obviously these daily
spends get added to the trip costs"; "Let's have both options - Add Total
and calculate daily or vice versa"; "+Spending should default to Euros,
today's date, and optional note blank"; "shared travellers should be able
to see the budget and the costs, but should not be able to add spending" -
if the owner shares them. No test here calls an exchange-rate service,
Claude or Google.
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

SUFFIX = '.bak_ra05'
ME = 'test_ra05_budget.py'
PATCHER = 'apply_ra05_budget.py'
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
from decimal import Decimal as D                            # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import travel.fx as FX                                      # noqa: E402
FX.fetch = lambda day, cur: {'GBP': D('0.85')}.get(cur)     # never the web
import travel.places as PL                                  # noqa: E402
PL.start_details = lambda *a, **k: None                     # never Claude
from travel import budget as B                              # noqa: E402
TV = J(ROOT, 'travel')
TT = J(TV, 'templates', 'travel')

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
md = read(J(TV, 'models.py'))
ok("budget_by = models.CharField(max_length=5, default='day')" in md and
   'share_money = models.BooleanField(default=True)' in md and
   'class Spend(models.Model):' in md,
   'TRIP: a budget (a day\'s or the holiday\'s), Share costs and budget '
   '(on for trips already shared); SPEND')
ok('Hotel, Car' in md and 'BudgetLine' not in md,
   '  no per-category budgets - bookings are actuals (Demetri\'s redesign)')
ok(os.path.isfile(J(TV, 'migrations', '0012_budget.py')),
   'MIGRATION travel 0012')
ok("raise RuntimeError('A booking with its costs hidden is not saved.')"
   in md, 'A BOOKING WITH ITS COSTS BLANKED CAN NEVER BE SAVED')
vb = read(J(TV, 'views_budget.py'))
ok('def _owned' in vb and vb.count('= _owned(request') == 5,
   'ONLY THE OWNER sets the budget, adds or deletes spending (5 doors)')
ok("dt.date.today()" in vb and
   "{% if c == 'EUR' %} selected" in read(J(TT, 'm', 'spend.html')),
   '+ SPENDING: euros and today by default; the note blank')
try:
    ok('budget' not in was(J(TV, 'models.py')),
       'CONTROL: before this round no trip had a budget')
except IOError as _e:
    skip('control', str(_e))

# ==========================================================================
head('2. THE ARITHMETIC (no database)')
# ==========================================================================


class T(object):
    def __init__(self, budget, by='day'):
        self.budget, self.budget_by = budget, by


class S(object):
    def __init__(self, day, eur):
        self.day, self.amount_eur = day, eur


s0 = dt.date(2026, 12, 10)
e0 = s0 + dt.timedelta(days=11)                             # 12 days
ok(B.amounts(T(D('150')), 12) == (D('150'), D('1800')) and
   B.amounts(T(D('1800'), 'total'), 12) == (D('150.00'), D('1800')),
   'A DAY x 12 = THE HOLIDAY, and the holiday / 12 = a day')
sp = [S(s0, D('34')), S(s0 + dt.timedelta(1), D('186')),
      S(s0 + dt.timedelta(2), D('141')), S(s0 + dt.timedelta(3), D('239')),
      S(s0 + dt.timedelta(4), D('86'))]
x = B.summary(T(D('150')), sp, s0, e0, today=s0 + dt.timedelta(4))
ok(x['when'] == 'on' and x['elapsed'] == 5 and x['planned'] == D('750')
   and x['spent'] == D('686'),
   'DAY 5: planned by today 5 x 150 = 750; spent 686', x['planned'])
ok(x['ahead'] and x['gap_label'] == '€64' and x['to_go'] == 7 and
   x['keep_label'] == '€159',
   '  €64 AHEAD of plan; 7 days to go; €159 a day keeps you on budget')
ok([c['over'] for c in x['chart'][:5]] == [False, True, False, True, False]
   and len(x['chart']) == 12 and x['chart'][4]['today'],
   'EACH DAY: a bar for all 12, red where over €150; today marked')
y = B.summary(T(D('100')), sp, s0, e0, today=s0 + dt.timedelta(4))
ok(not y['ahead'] and y['gap_label'] == '€186',
   'BEHIND: €100 a day, 686 spent of 500 planned - €186 behind')
z = B.summary(T(D('150')), [], s0, e0, today=s0 - dt.timedelta(9))
ok(z['when'] == 'before' and z['total_label'] == '€1,800' and
   z['to_go'] == 12, 'BEFORE THE TRIP: the plan, €1,800 over 12 days')
w = B.summary(T(D('50')), sp, s0, e0, today=e0 + dt.timedelta(2))
ok(w['when'] == 'after' and w['over'] and w['left_label'] == '€86',
   'AFTER THE TRIP: €686 against €600 - €86 over budget')
ok(B.summary(T(None), sp, s0, e0, today=s0)['set'] is False,
   'NO BUDGET: nothing to be ahead or behind of')

# ==========================================================================
head('3. DRIVEN (database; no web)')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from pages.models import UserProfile
    from pages.workspace import ensure_workspace
    from travel.models import Booking, Spend, Trip
    connection.ensure_connection()
    Spend.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            me = User.objects.create_user('ra05a', 'ra05a@example.com', 'x')
            her = User.objects.create_user('ra05b', 'ra05b@example.com', 'x')
            for u in (me, her):
                u.user_permissions.add(perm)
                UserProfile.objects.update_or_create(
                    user=u, defaults={'workspace': ensure_workspace(me)})
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(me)
            H = Client(SERVER_NAME='localhost')
            H.force_login(her)
            d = timezone.localdate()
            t = Trip.objects.create(owner=me, name='RA05 trip')
            t.shared_with.add(her)
            bk = Booking(trip=t, added_by=me, kind='stay', title='Hotel RA05',
                         reference='R5', start_date=d - dt.timedelta(2),
                         end_date=d + dt.timedelta(3), amount=D('500'),
                         paid='due')
            FX.convert(bk)
            bk.save()
            r = A.post('/travel/%d/budget/' % t.pk,
                       {'by': 'total', 'budget_total': '600'})
            t.refresh_from_db()
            ok(r.status_code == 302 and t.budget == D('600') and
               t.budget_by == 'total',
               'SET THE HOLIDAY\'S BUDGET: €600 kept as the total')
            A.post('/travel/%d/spend/' % t.pk, {'amount': '40'})
            s1 = Spend.objects.get(trip=t)
            ok(s1.currency == 'EUR' and s1.day == d and s1.amount_eur ==
               D('40') and s1.what == '',
               '+ SPENDING with just the amount: euros, today, no note')
            A.post('/travel/%d/spend/' % t.pk, {'amount': '17', 'currency':
                                                'GBP', 'what': 'Taxi'})
            ok(Spend.objects.get(trip=t, what='Taxi').amount_eur == D('20.00'),
               '  another currency: in euros at the day\'s rate (stubbed)')
            c = A.get('/travel/%d/costs/' % t.pk).content.decode()
            ok('data-budget' in c and 'data-bud-pace=' in c and
               'data-budget-chart' in c and 'data-spend-form' in c,
               'COSTS TAB: the budget card, ahead/behind, the day bars, '
               '+ Spending')
            ok('Trip total' in c and '€560' in c and 'Daily spending' in c,
               '  the trip total is the bookings plus the spending (€560)')
            p = M.get('/travel/m/trip/%d/?tab=costs' % t.pk).content.decode()
            ok('data-budget' in p and 'data-spend-new' in p,
               'PHONE COSTS: the card and + Spending')
            td = M.get('/travel/m/').content.decode()
            ok('data-today-budget' in td,
               'PHONE TODAY: spent today against the day\'s budget')
            ok(M.get('/travel/m/%d/spend/new/' % t.pk).status_code == 200 and
               M.get('/travel/m/%d/budget/edit/' % t.pk).status_code == 200,
               '  the phone\'s + Spending and budget pages open')
            # Shared, costs shared: sees, cannot add.
            hc = H.get('/travel/%d/costs/' % t.pk)
            ok(hc.status_code == 200 and 'data-budget' in hc.content.decode()
               and 'data-spend-form' not in hc.content.decode(),
               'SHARED, COSTS SHARED: sees the budget and costs, no '
               '+ Spending')
            n0 = Spend.objects.filter(trip=t).count()
            r1 = H.post('/travel/%d/spend/' % t.pk, {'amount': '5'})
            r2 = H.post('/travel/%d/budget/' % t.pk, {'budget_day': '1'})
            r3 = H.post('/travel/spend/%d/delete/' % s1.pk)
            ok((r1.status_code, r2.status_code, r3.status_code) ==
               (404, 404, 404) and
               Spend.objects.filter(trip=t).count() == n0,
               '  and cannot add, set or delete - refused')
            # The owner unticks Share costs and budget.
            A.post('/travel/%d/share/' % t.pk, {'people': [her.pk]})
            t.refresh_from_db()
            ok(t.share_money is False, 'UNTICK Share costs and budget')
            ht = H.get('/travel/%d/' % t.pk).content.decode()
            ok('/costs/' not in ht and '€500' not in ht and
               'data-budget-side' not in ht,
               'NOT SHARED: no Costs tab, no amounts, no budget')
            ok(H.get('/travel/%d/costs/' % t.pk).status_code == 302,
               '  the Costs page sends them back to the trip')
            hb = H.get('/travel/booking/%d/' % bk.pk).content.decode()
            ok('data-booking-cost' not in hb and '€500' not in hb,
               '  a booking: no Cost section')
            hl = H.get('/travel/').content.decode()
            ok('€500' not in hl and '€560' not in hl,
               '  the trips list: no totals')
            hm = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            hm.force_login(her)
            ok('€500' not in hm.get('/travel/m/trip/%d/' % t.pk).content
               .decode(), '  the phone: no amounts')
            ef = H.get('/travel/booking/%d/edit/' % bk.pk).content.decode()
            ok('name="amount"' not in ef, '  editing a booking: no Cost '
               'section')
            H.post('/travel/booking/%d/edit/' % bk.pk, {
                'kind': 'stay', 'title': 'Hotel RA05 renamed',
                'start_date': str(bk.start_date),
                'end_date': str(bk.end_date)})
            bk.refresh_from_db()
            ok(bk.title == 'Hotel RA05 renamed' and bk.amount == D('500') and
               bk.paid == 'due',
               '  ...and saving it leaves the owner\'s amounts as they were')
            pdf_ctx = __import__('travel.report', fromlist=['context']) \
                .context(t, 'summary', her)
            ok(not pdf_ctx['money']['any'] and pdf_ctx['bud'] is None,
               '  the PDF: no costs, no budget')
            ok('€560' in A.get('/travel/%d/costs/' % t.pk).content.decode(),
               'THE OWNER still sees it all')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. HELP AND REGISTERED')
# ==========================================================================
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('data-help-budget' in adm and 'data-help-share-money' in adm and
   'ahead of plan' in adm,
   'HELP (computer): the daily spending budget; Share costs and budget')
ok('data-help-budget' in read(J(TT, 'm', 'help.html')),
   'HELP (phone): Budget and spending')
ph = read(J(TV, 'phone.py'))
ok("SW_VERSION = 'tv19-1'" in ph and '?v=tv19-1' in read(
    J(TT, 'm', 'base.html')), 'THE PHONE APP moves to tv19-1')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
