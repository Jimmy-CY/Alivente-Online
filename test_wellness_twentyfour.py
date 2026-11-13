# -*- coding: utf-8 -*-
"""test_wellness_twentyfour.py - round PT-1, 12 Nov 2026.

RELEASE 70 - PERSONAL TODAY INSIDE WELLNESS, AND LOG A PAST WORKOUT.
Demetri, 14:32-14:38: celebrations, meals and documents "in an app format
like the Wellness app", reached from Wellness without making it clumsy -
a small "At home today" card on Today, See all for the page. Celebrations:
only his own. Meals: his plan and plans shared with him. Documents: only
his own here (the Documents section still shows everybody's). No CRS.
17:33: "Log a past workout (pick the day and duration)".
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

SUFFIX = '.bak_wellness24'
ME = 'test_wellness_twentyfour.py'
PATCHER = 'apply_wellness_twentyfour.py'
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

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
hm = read(J(APP, 'home.py'))
ok("CEL_PERM = 'auth.can_access_celebrations'" in hm and
   "MEAL_PERM = 'auth.can_access_recipes'" in hm and
   "DOC_PERM = 'auth.can_access_passports'" in hm and 'crs' not in
   hm.lower().replace('across', ''),
   'HOME: each part only for someone who can open it; no CRS')
ok('relevant_to__in=members' in hm and 'holder__in=members' in hm and
   'MC.accessible(user)' in hm,
   '  only their celebrations, only their documents, their meal plans')
td = read(J(WT, 'today.html'))
# PT-2, 12 Nov 2026 - the card is the whole of At home today now, and the
# page behind See all is gone (Demetri, 21:48). test_wellness_twentyfive
# holds the card; this keeps only what PT-1 still owns: a card, only when
# there is something to say.
ok('{% if home %}' in td and 'data-home-card' in td,
   'TODAY: a card only when there is something to say')
v = read(J(APP, 'views.py'))
ok("if (profile.prefs or {}).get('home_off'):" in v and
   # PT-3, 13 Nov 2026 - the switch moved into Your sections.
   "hp['home_off'] = not request.POST.get('home')" in v and
   'except Exception:  # noqa: BLE001 - Today must always open' in v,
   '  it can be turned off in Settings, and a fault there never stops Today')
vw = read(J(APP, 'views_workouts.py'))
ok('def session_past(request):' in vw and
   'def _new_session(user, routine, day, start):' in vw and
   's.started_at + dt.timedelta(minutes=s.minutes)' in vw,
   'PAST WORKOUT: its own page; it ends when it really ended')
ok("{% url 'wellness:session_past' %}" in read(J(WT, 'workouts.html')) and
   'data-past' in read(J(WT, 'session_live.html')) and
   'if (clock) setInterval(' in read(J(APP, 'assets', 'wellness.js')),
   '  reached from Workouts; the live page shows its length, not a clock')
css = read(J(APP, 'assets', 'wellness.css'))
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px')
base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
ok(vv and len(set(vv)) == 1 and vv[0] not in ('wl22-1',) and
   ("SW_VERSION = '%s'" % vv[0]) in v, 'the app files carry a new version',
   vv)

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
# PT-2 - the At home page is gone; its help went with it.
ok(HELP.for_url_name('session_past') and
   'Log a past workout' in ' '.join(HELP.for_url_name('workouts')['steps'])
   and 'At home today' in ' '.join(HELP.for_url_name('settings')['steps']),
   'HELP: both new screens; Workouts and Settings mention them')
qs = {h['q']: h for h in G.HOWTO}
ok(qs.get('What is At home today?', {}).get('topic') == 'setup' and
   qs.get('Set up: log a workout you already did', {}).get('topic') ==
   'workouts', '  and the general questions, under the right topics')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import (WellnessProfile, WorkoutSession, Exercise,
                                 WorkoutSet)
    from pages.models import (HouseholdMember, Contact, CelebrationEvent,
                              Passport, MealEntry, MealCalendar)
    connection.ensure_connection()
    WorkoutSession.objects.filter(minutes__isnull=False).exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            def perm(code):
                p, _ = Permission.objects.get_or_create(
                    codename=code, content_type__app_label='auth',
                    defaults={'name': code})
                return p
            a = User.objects.create_user('w24_a', 'w24a@example.com', 'x',
                                         first_name='Al')
            b = User.objects.create_user('w24_b', 'w24b@example.com', 'x',
                                         first_name='Bo')
            for u in (a, b):
                u.user_permissions.add(perm('can_access_wellness'))
                WellnessProfile.objects.create(user=u, onboarded=True)
            a.user_permissions.add(perm('can_access_celebrations'),
                                   perm('can_access_recipes'),
                                   perm('can_access_passports'))
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            day = timezone.localdate()
            ws = ensure_workspace(a)
            ma = HouseholdMember.objects.create(workspace=ws, name='Al',
                                                user=a)
            mb = HouseholdMember.objects.create(workspace=ws, name='Bo',
                                                user=b)
            kid = Contact.objects.create(name='Kiddo', relationship='other',
                                         workspace=ws, created_by=a)
            other = Contact.objects.create(name='Nobody', relationship='other',
                                           workspace=ws, created_by=a)
            soon = day + dt.timedelta(days=3)
            e1 = CelebrationEvent.objects.create(
                contact=kid, event_type='birthday', created_by=a,
                event_date=soon.replace(year=soon.year - 21))
            e1.relevant_to.add(ma)
            e2 = CelebrationEvent.objects.create(
                contact=other, event_type='birthday', created_by=a,
                event_date=soon.replace(year=1900))
            e2.relevant_to.add(mb)
            Passport.objects.create(workspace=ws, holder_name='Al',
                                    holder=ma, document_type='passport',
                                    document_number='X1',
                                    country_of_issue='Greece',
                                    expiry_date=day + dt.timedelta(days=40))
            Passport.objects.create(workspace=ws, holder_name='Bo',
                                    holder=mb, document_type='passport',
                                    document_number='X2',
                                    country_of_issue='Cyprus',
                                    expiry_date=day + dt.timedelta(days=10))
            cal = MealCalendar.objects.create(owner=a)
            MealEntry.objects.create(date=day, note='Souvlaki night',
                                     calendar=cal)
            calb = MealCalendar.objects.create(owner=b)
            MealEntry.objects.create(date=day, note='Bo private meal',
                                     calendar=calb)

            # PT-2, 12 Nov 2026 - the card shows today's celebrations
            # only, and the page behind it is gone, so Kiddo's birthday in
            # three days is no longer on it. What PT-1 promised still
            # holds and is checked here: his meal, his own document, and
            # nothing of Bo's. test_wellness_twentyfive drives the rest.
            t = ca.get('/wellness/').content.decode()
            ok('data-home-card' in t and 'Souvlaki night' in t and
               'Greek passport' in t,
               'TODAY: Al sees his card - Souvlaki night, his passport')
            ok('Nobody' not in t and 'Bo private meal' not in t and
               'Cyprus passport' not in t,
               '  and not Bo\'s celebration, Bo\'s meal plan or Bo\'s '
               'passport')
            calb.shared_with.add(a)
            t = ca.get('/wellness/').content.decode()
            ok('Bo private meal' in t and 'Bo&#x27;s meal plan' in t,
               '  a plan shared with him joins, saying whose it is')
            ok('data-home-card' not in cb.get('/wellness/').content
               .decode(),
               'Bo, who cannot open those parts of Alivente, gets no card')
            p = WellnessProfile.objects.get(user=a)
            p.prefs = dict(p.prefs or {}, home_off=True)
            p.save()
            ok('data-home-card' not in ca.get('/wellness/').content.decode(),
               'turned off in Settings, the card is gone')
            # ---- log a past workout
            yday = day - dt.timedelta(days=1)
            r = ca.post('/wellness/workouts/past/', {
                'date': yday.isoformat(), 'time': '07:15', 'minutes': '40'})
            s = WorkoutSession.objects.filter(user=a).first()
            ok(r.status_code == 302 and s and s.date == yday and
               s.minutes == 40 and s.finished_at is None,
               'PAST: yesterday 07:15, 40 minutes - opened to tick sets')
            t = ca.get('/wellness/workouts/%d/live/' % s.pk).content.decode()
            ok('data-past-note' in t and '40 min' in t and
               'data-elapsed' not in t,
               '  the page says which day, and shows 40 min, not a clock')
            run = Exercise.objects.get(user=None, name='Run')
            WorkoutSet.objects.create(session=s, exercise=run, set_no=1,
                                      distance_m=6000, seconds=2400,
                                      done=True)
            ca.post('/wellness/workouts/%d/finish/' % s.pk, {'effort': '6'})
            s.refresh_from_db()
            ok(s.finished_at and int((s.finished_at - s.started_at)
                                     .total_seconds()) == 2400,
               '  finished, it lasted the 40 minutes typed - not the '
               'minute it took to log')
            r = ca.post('/wellness/workouts/past/', {
                'date': (day + dt.timedelta(days=1)).isoformat(),
                'time': '07:00', 'minutes': '30'})
            ok(r.status_code == 200 and 'Pick a day in the last year' in
               r.content.decode(), '  tomorrow is refused, in words')
            r = ca.post('/wellness/workouts/past/', {
                'date': day.isoformat(), 'time': '07:00', 'minutes': '0'})
            ok(r.status_code == 200 and 'How long did it take' in
               r.content.decode(), '  and no length is asked for')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok('home_lines' not in was(J(APP, 'views.py')) and
       'session_past' not in was(J(APP, 'urls.py')),
       'before this round: no At home today and no past workouts')
except IOError as _e:
    skip('section 3', str(_e))

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# PT-2 - card_lines went with the page; the sentinel moved to card().
ok("Text = 'def card(user, day):'" in gate, '  with a sentinel on the card')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
