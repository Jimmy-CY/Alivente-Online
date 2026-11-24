# -*- coding: utf-8 -*-
"""test_ra20_travel_info_tab.py - round RA20, 24 Nov 2026.

RELEASE RA20 - GOOD TO KNOW SHOWS GOOD TO KNOW.
Demetri, 24 Nov: "Why does the Good to Know Button open the Costs?" The
trip page's tab chain ended in a bare {% else %} - the Costs branch - and
Good to know (RA12) sat after the chain, so on its tab the whole Costs
section was drawn above the city cards. That stray section also said "The
trip needs its dates first" and "Nothing yet": the view builds the days
and the spending only for the Costs tab. One cause, both symptoms; the
branch now names its tab.
And the Activity page says why a person can have pages but no sign-in
(Demetri: "Is that because the Wellness app keeps her logged in?").
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

SUFFIX = '.bak_ra20'
ME = 'test_ra20_travel_info_tab.py'
PATCHER = 'apply_ra20_travel_info_tab.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
TRIP = J(ROOT, 'travel', 'templates', 'travel', 'trip.html')
ACT = J(ROOT, 'pages', 'templates', 'user_activity.html')
HELP = J(ROOT, 'pages', 'help_content', 'administration.html')

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


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])


def chain(src):
    """The tab chain's branches, in order: what each {% if/elif/else %}
    at the start of a line says, from the bookings branch to its endif."""
    # The chain's own lines start at the left margin; the tab buttons
    # above it say {% if tab == ... %} too, inside an <a>.
    a = src.index("\n{% if tab == 'bookings' %}") + 1
    return re.findall(r"^\{% (?:if|elif) tab == '(\w+)' %\}|^(\{% else %\})",
                      src[a:], re.M)


def claims(trip, act, hlp):
    branches = chain(trip)
    names = [n for n, e in branches[:4]]
    return {
        'THE COSTS BRANCH NAMES ITS TAB - no bare else ends the chain':
            names[:4] == ['bookings', 'itinerary', 'wish', 'costs'] and
            not any(e for n, e in branches[:4]),
        '  and it says why, in the round\'s words':
            'Why does the Good to Know Button open the Costs?' in trip,
        'THE ACTIVITY PAGE SAYS WHY A PERSON CAN HAVE PAGES BUT NO SIGN-IN':
            'data-act-long' in act and '30 days' in act,
        '  and so does the Help':
            'keep someone signed in for 30 days' in hlp,
    }


head('1. THE SOURCE')
NOW = [read(p) for p in (TRIP, ACT, HELP)]
for m, got in claims(*NOW).items():
    ok(got, m)
ok(NOW[0].count("\n{% if tab == 'info' %}") == 1,
   'Good to know is still its own block after the chain, drawn once')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in (TRIP, ACT, HELP)):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in
                                     (TRIP, ACT, HELP)]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA20', held)
    was = chain(read(TRIP + SUFFIX))
    ok(any(e for n, e in was[:4]),
       'CONTROL: the chain did end in a bare else - the fault this round '
       'fixes', was[:4])
else:
    skip('the control', 'no .bak_ra20 beside the files')

head('3. DRIVEN - EACH TAB DRAWS ITS OWN SECTION (database; no network)')
import datetime as dt                                       # noqa: E402
from decimal import Decimal as D                            # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from travel.models import Trip, Spend
    connection.ensure_connection()
    Trip.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database - has migrate been run?)',
         str(_e).split('\n')[0][:70])

if have_db:
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            u = User.objects.create_user('ra20t', 'ra20t@example.com', 'pw')
            u.user_permissions.add(
                Permission.objects.get(codename='can_access_travel'))
            day = dt.date.today() + dt.timedelta(days=30)
            t = Trip.objects.create(owner=u, name='RA20 trip',
                                    start_date=day,
                                    end_date=day + dt.timedelta(days=3),
                                    budget=D('60'))
            Spend.objects.create(trip=t, day=day, what='RA20 taxi',
                                 currency='EUR', amount=D('50'),
                                 amount_eur=D('50'), added_by=u)
            c = Client()
            c.force_login(u)
            pages = {}
            for name, url in (('bookings', '/travel/%d/'),
                              ('costs', '/travel/%d/costs/'),
                              ('info', '/travel/%d/good-to-know/')):
                r = c.get(url % t.pk)
                pages[name] = (r.status_code,
                               r.content.decode('utf-8', 'replace'))
            ok(all(s == 200 for s, _ in pages.values()),
               'the three tabs open', [(k, s) for k, (s, _) in pages.items()])
            info = pages['info'][1]
            # The section markers, not the words: the Travel Help pop-up
            # on every trip page says "Daily spending budget" too.
            ok('data-spending' not in info and
               not re.search(r'data-budget(>|-none)', info),
               'GOOD TO KNOW draws no Costs section - no budget, no Daily '
               'spending')
            ok('data-spend-nodates' not in info and
               'needs its dates first' not in info,
               '  so no "The trip needs its dates first" either - that was '
               'the stray section, drawn without the days the view builds '
               'for Costs only')
            ok('data-city-none' in info or 'data-city' in info,
               '  and it still draws Good to know')
            cost = pages['costs'][1]
            ok('data-spending' in cost and
               re.search(r'data-budget(>|-none)', cost),
               'COSTS still draws the budget and the Daily spending')
            ok('data-spend-nodates' not in cost and 'RA20 taxi' in cost,
               '  with the trip\'s days and its spending')
            ok('data-spending' not in pages['bookings'][1],
               'BOOKINGS draws no Costs section')
            raise Rollback
    except Rollback:
        pass

    try:
        with transaction.atomic():
            su = User.objects.create_superuser('ra20s', 'ra20s@example.com',
                                               'pw')
            c = Client()
            c.force_login(su)
            r = c.get('/user-administration/activity/?tab=signins')
            t = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and 'data-act-long' in t,
               'SIGN-INS says a sign-in is a login, and that Wellness and '
               'Travel on a phone keep someone signed in for 30 days')
            raise Rollback
    except Rollback:
        pass

head('4. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
