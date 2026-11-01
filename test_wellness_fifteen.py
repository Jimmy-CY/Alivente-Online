# -*- coding: utf-8 -*-
"""test_wellness_fifteen.py - round WL-11, 1 Nov 2026.

RELEASE 58 - WELLNESS: CALORIES ON A WORKOUT.
Demetri, 11:27: "When I do a workout I want to be able to optionally
capture the Calories that I burnt during that workout. How could we do
that? Where would we include it?" 11:28: "Perfect. Go for it."

    - Typed in from the watch: a web app cannot read the watch, and an
      estimate from weight and time is far rougher than the watch's
      heart-rate figure - so Wellness never estimates.
    - A fourth figure on the finished workout: "+ Add calories", then
      "285 kcal". Optional; blank clears it; can be added or changed later.
    - Adds up on the Workouts page (this week), in Recent workouts, the
      Monday email and Insights (once there are any).
    - Migration 0010_workout_calories: one nullable column.
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

SUFFIX = '.bak_wellness15'
ME = 'test_wellness_fifteen.py'
PATCHER = 'apply_wellness_fifteen.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(APP, 'models.py'), J(APP, 'views_workouts.py'),
          J(APP, 'urls.py'), J(APP, 'weekly.py'), J(APP, 'insights.py'),
          J(APP, 'help.py'), J(APP, 'guide.py'),
          J(WT, 'session_detail.html'), J(WT, 'workouts.html'),
          J(WT, 'insights.html')]

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
ok(os.path.isfile(J(APP, 'migrations', '0010_workout_calories.py')),
   'MIGRATION 0010_workout_calories is on disk')
mig = read(J(APP, 'migrations', '0010_workout_calories.py'))
ok('"0009_challenges"' in mig and 'null=True' in mig and
   'RemoveField' not in mig and 'AlterField' not in mig,
   '  it only adds one nullable column after 0009')
models_src = read(J(APP, 'models.py'))
ok(models_src.index('calories = models.PositiveSmallIntegerField') <
   models_src.index('class CycleRecord'),
   '  the field sits on WorkoutSession, before CycleRecord')
det = read(J(WT, 'session_detail.html'))
ok('+ Add' in det and 'data-cal-tile' in det and 'id="w-cal"' in det and
   'cal_open %}' in det,
   'THE FINISHED WORKOUT has a fourth figure and a place to type')
ok('inputmode="numeric"' in det and 'autofocus' in det,
   '  a number pad opens, ready to type')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('calories' not in was(J(APP, 'models.py')),
   'CONTROL: before this round a workout had no calories')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import views_workouts as VW                   # noqa: E402
ok(VW.clean_calories('285') == 285 and VW.clean_calories(' 1,250 ') == 1250
   and VW.clean_calories('300 kcal') == 300,
   'CLEAN: "285", "1,250" and "300 kcal" are read')
ok(VW.clean_calories('') is None and VW.clean_calories(None) is None,
   '  blank clears it')
bad = []
for raw in ('0', '-5', '12.5', 'abc', str(VW.CAL_MAX + 1)):
    try:
        VW.clean_calories(raw)
        bad.append(raw)
    except ValueError:
        pass
ok(not bad, '  0, negative, decimals, words and over %d are refused'
   % VW.CAL_MAX, bad)
import datetime as dt                                       # noqa: E402
from wellness import insights as INS                        # noqa: E402
T = dt.date(2026, 11, 1)
rows = INS.weekly(T, {}, {}, {}, {T}, {T: 300})
ok(rows[-1]['kcal'] == 300 and rows[0]['kcal'] == 0,
   'INSIGHTS adds up the week\'s calories')
ok(INS.weekly(T, {}, {}, {}, {T})[-1]['kcal'] == 0,
   '  and still works when none were typed')
from wellness import weekly as WK                           # noqa: E402
s = {'monday': T - dt.timedelta(days=6), 'sunday': T, 'habits': [],
     'met': 0, 'sessions': [{'name': 'Push', 'date': T}], 'minutes': 40,
     'records': 0, 'weight': None, 'badges': [], 'calories': 285}
txt = WK.render(s, 'Demetri')
txt = txt if isinstance(txt, str) else ' '.join(
    x for x in txt if isinstance(x, str))
ok('Workouts: 1, 40 minutes, 285 kcal' in txt,
   'THE MONDAY EMAIL: "Workouts: 1, 40 minutes, 285 kcal"')
s['calories'] = 0
txt = WK.render(s, 'Demetri')
txt = txt if isinstance(txt, str) else ' '.join(
    x for x in txt if isinstance(x, str))
ok('kcal' not in txt, '  and says nothing when none were typed')
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
hd = HELP.for_url_name('session_detail')
ok(hd and 'calories' in ' '.join(hd['steps']).lower(),
   'HELP: the finished-workout screen explains calories')
ok(any('calories' in h['q'].lower() for h in G.HOWTO),
   '  and the general questions answer it')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile, WorkoutSession
    connection.ensure_connection()
    WorkoutSession.objects.filter(calories__isnull=False).exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            a = User.objects.create_user('w15_a', 'w15a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            b = User.objects.create_user('w15_b', 'w15b@example.com', 'x')
            b.user_permissions.add(perm)
            WellnessProfile.objects.create(user=b, onboarded=True)
            now = timezone.now()
            ws = WorkoutSession.objects.create(
                user=a, name='Push', date=timezone.localdate(),
                started_at=now - dt.timedelta(minutes=43), finished_at=now)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            url = '/wellness/workouts/%d/' % ws.pk
            t = ca.get(url).content.decode()
            ok('+ Add' in t and 'calories' in t and 'id="w-cal"' not in t,
               'THE FINISHED WORKOUT: "+ Add calories", no form until tapped')
            t = ca.get(url + '?calories=1').content.decode()
            ok('id="w-cal" open' in t and 'autofocus' in t,
               '  tapping it opens the form, ready to type')
            r = ca.post(url + 'calories/', {'calories': '285'})
            ws.refresh_from_db()
            ok(r.status_code == 302 and ws.calories == 285,
               'SAVED: 285 kcal')
            t = ca.get(url).content.decode()
            ok('285</div><div class="w-small w-quiet">kcal' in t,
               '  and shown as the fourth figure')
            r = ca.post(url + 'calories/', {'calories': 'lots'})
            ws.refresh_from_db()
            ok(ws.calories == 285 and 'cal_error=1' in r['Location'],
               'A WRONG VALUE is refused and the old one kept')
            t = ca.get(r['Location']).content.decode()
            ok('Please type a whole number' in t, '  with a line saying why')
            t = ca.get('/wellness/workouts/').content.decode()
            ok('285 kcal' in t, 'THE WORKOUTS PAGE: this week and Recent')
            ins = ca.get('/wellness/insights/').content.decode()
            ok('data-ins-kcal' in ins and 'Workout calories' in ins,
               'INSIGHTS: a calories chart once there are any')
            cb = Client(SERVER_NAME='localhost')
            cb.force_login(b)
            r = cb.post(url + 'calories/', {'calories': '1'})
            ws.refresh_from_db()
            ok(r.status_code == 404 and ws.calories == 285,
               'SOMEONE ELSE cannot change your calories')
            ok(cb.get(url + 'calories/').status_code == 405,
               '  and the address only takes a POST')
            r = ca.post(url + 'calories/', {'calories': ''})
            ws.refresh_from_db()
            ok(ws.calories is None, 'BLANK clears it')
            ins = ca.get('/wellness/insights/').content.decode()
            ok('data-ins-kcal' not in ins,
               '  and Insights shows no calories chart with none typed')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def clean_calories('" in gate, '  with a sentinel on the rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
