# -*- coding: utf-8 -*-
"""test_wellness_three.py - round WL-3, 30 Oct 2026.

RELEASE 45 - WELLNESS, PART THREE: WORKOUTS. From the proposal:

    - An exercise library (68 to start) plus your own exercises, and your
      equipment, so suggestions only offer weights you own.
    - Routines: saved workouts with sets, a rep range and rest, shown on
      Today on the days you choose.
    - The live logger: last time's numbers beside every set, a rest timer
      when a set is ticked, a record celebrated the moment it happens, the
      screen kept awake.
    - Double progression: top the rep range on every set and the next
      workout suggests the next weight up that you own.
    - Records, history and a chart per exercise; a habit can tick itself
      when a workout is finished.
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

import datetime as dt
import os
import re
import sys
from decimal import Decimal

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_wellness3'
ME = 'test_wellness_three.py'
PATCHER = 'apply_wellness_three.py'
PS1 = 'Push-PendingChanges.ps1'

J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
NEW_FILES = ['training.py', 'views_workouts.py',
             J('migrations', '0003_workouts.py'),
             J('migrations', '0004_exercise_library.py')] + [
    J('templates', 'wellness', f) for f in (
        'workouts.html', 'routine_form.html', 'session_live.html',
        'session_detail.html', 'exercise_detail.html', 'exercise_form.html',
        'kit.html')]
EDITED = [J(APP, 'models.py'), J(APP, 'views.py'), J(APP, 'urls.py'),
          J(APP, 'guide.py'), J(APP, 'assets', 'wellness.css'),
          J(APP, 'assets', 'wellness.js'), J(WT, 'base.html'),
          J(WT, 'today.html'), J(WT, 'habit_form.html')]

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

import alv_tree as T                                        # noqa: E402

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
missing = [f for f in NEW_FILES if not os.path.isfile(J(APP, f))]
ok(not missing, 'the workout files are all there (%d)' % len(NEW_FILES),
   ', '.join(missing))
mig = read(J(APP, 'migrations', '0003_workouts.py'))
ok(all(re.search(r"""name=["']%s["']""" % n, mig) for n in (
    'Exercise', 'Routine', 'RoutineItem', 'WorkoutSession', 'WorkoutSet')),
   'migration 0003 makes the five workout tables')
seed = read(J(APP, 'migrations', '0004_exercise_library.py'))
lib = re.findall(r"^    \('([^']+)', '(\w+)', '(\w+)', '(\w+)'\),$", seed, re.M)
ok(len(lib) >= 60, 'migration 0004 seeds a library of %d exercises'
   % len(lib))
ok(len({n for n, _, _, _ in lib}) == len(lib), '  every name once')
ok('from wellness' not in seed and 'import wellness' not in seed,
   '  the list lives in the migration, so it means the same whenever it '
   'runs')
ok('def unseed' in seed and "exclude(id__in=used)" in seed,
   '  and reversing it never removes an exercise somebody used')
base = read(J(WT, 'base.html'))
# CY-1 (Release 46) adds a sixth tab, Cycle, shown only to a person who
# turned the tracker on - so at least five.
ok("wellness:workouts" in base and base.count('class="w-tab{%') >= 5,
   'the bottom bar has Workouts: five tabs', base.count('class="w-tab{%'))
v = read(J(APP, 'views_workouts.py'))
gets = [m.group(0) for m in re.finditer(
    r'get_object_or_404\((?:Routine|WorkoutSession|WorkoutSet)[^)]*\)', v)]
ok(len(gets) >= 9 and all('user=request.user' in g or
                          'session__user=request.user' in g for g in gets),
   'every routine, workout and set lookup is filtered by the login (%d)'
   % len(gets), [g for g in gets if 'user=request.user' not in g])
ok('Q(user__isnull=True) | Q(user=user)' in v,
   'exercises: the shared library, plus your own - never anybody else\'s')
live = read(J(WT, 'session_live.html'))
ok('data-rest-bar' in live and 'data-record' in live and 'data-elapsed'
   in live, 'the live logger has the rest timer, the record moment and the '
   'clock')
js = read(J(APP, 'assets', 'wellness.js'))
ok("navigator.wakeLock.request('screen')" in js,
   '  and keeps the screen awake where the phone allows')
ok('navigator.vibrate' in js, '  and buzzes when the rest is over')
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('class Routine' not in was(J(APP, 'models.py')),
   'CONTROL: before this round there were no workouts')

# ==========================================================================
head('2. THE RULES (no database)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import training as TR                         # noqa: E402
ok(abs(TR.e1rm(100, 5) - 116.6667) < 1e-3,
   "Epley: 100 kg for 5 is about 116.7 kg for one")
ok(TR.e1rm(100, 1) == 100 and TR.e1rm(20, 15) is None,
   '  a single is itself; past 12 reps no estimate is offered')
kit = {'dumbbells': [1, 2, 3, 4, 5, 6, 7, 8], 'barbell_max': 30,
       'plate_step': 2.5}
ok(TR.next_weight(6, 'dumbbell', kit) == 7,
   'his dumbbells: after 6 kg comes 7 kg, the next one he owns')
ok(TR.next_weight(8, 'dumbbell', kit) is None,
   '  and after 8 kg there is none')
ok(TR.next_weight(27.5, 'barbell', kit) == 30
   and TR.next_weight(30, 'barbell', kit) is None,
   'his barbell: 27.5 -> 30, and 30 is the top')
s = TR.suggest(8, 10, [(6, 10), (6, 10), (6, 10)], 'dumbbell', kit)
ok(s['weight'] == 7 and s['reps'] == 8 and s['why'] == 'up',
   'double progression: 10, 10, 10 at the top of 8-10 -> 7 kg for 8', s)
s = TR.suggest(8, 10, [(6, 10), (6, 9), (6, 8)], 'dumbbell', kit)
ok(s['weight'] == 6 and s['reps'] == 10 and s['why'] == 'reps',
   '  10, 9, 8 -> same weight, aim for 10', s)
s = TR.suggest(8, 10, [(8, 10)] * 3, 'dumbbell', kit)
ok(s['why'] == 'top' and s['weight'] == 8,
   '  at the heaviest dumbbell he owns it never suggests one he lacks', s)
ok(TR.suggest(8, 12, [], 'dumbbell', kit)['why'] == 'first',
   '  and a first workout suggests nothing to beat')
best = TR.records([(6, 10, None, None), (6, 9, None, None)])
ok(TR.is_record((7, 8, None, None), best).startswith('Heaviest yet'),
   'records: more weight is a record')
ok(TR.is_record((6, 11, None, None), best).startswith('Most reps at 6'),
   '  more reps at the same weight is a record')
ok(TR.is_record((6, 10, None, None), best) == '',
   '  matching it is not')
ok(TR.is_record((5, 15, None, None), best) == '',
   'CONTROL: a lighter set with more reps but a lower estimate is not')
ok(TR.is_record((6, 10, None, None), TR.records([])) == '',
   'CONTROL: the very first set is not a record - there is nothing to beat')
ok(TR.is_record((None, None, 70, None),
                TR.records([(None, None, 60, None)])).startswith('Longest'),
   '  a longer plank is a record')
ok(TR.volume([(6, 10), (7, 8), (None, 12)]) == 116,
   'volume counts weighted sets: 60 + 56')
ok(TR.duration(754) == '12:34' and TR.duration(3725) == '1:02:05',
   'durations read as a clock')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import (Exercise, Habit, HabitLog, Routine,
                                 RoutineItem, WellnessProfile,
                                 WorkoutSession, WorkoutSet)
    connection.ensure_connection()
    Routine.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

# NO PERIODIC CLEANUP WHILE THIS SUITE DRIVES THE APP. The site's
# DatabaseConnectionMiddleware closes every connection each
# DB_FORCE_CLEANUP_INTERVAL requests (25). This suite makes more than that
# inside one rolled-back transaction, and a close in the middle of it ends
# the transaction under the suite's feet. Set before the first request,
# because the middleware reads it once, when it is built.
from django.conf import settings as _dj                     # noqa: E402
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


def post(c, url, data=None, fetch=False):
    kw = {'HTTP_X_REQUESTED_WITH': 'fetch'} if fetch else {}
    return c.post(url, data or {}, **kw)


if have_db:
    try:
        with transaction.atomic():
            ok(Exercise.objects.filter(user__isnull=True).count() >= 60,
               'the library is in the database')
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            a = User.objects.create_user('wl3_a', 'a@example.com', 'x')
            b = User.objects.create_user('wl3_b', 'b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            day = timezone.localdate()

            r = post(ca, '/wellness/workouts/kit/', {
                'dumbbells': '1 2 3 4 5 6 7 8', 'barbell_max': '30',
                'plate_step': '2.5'})
            ok(WellnessProfile.objects.get(user=a).equipment.get(
                'dumbbells') == [1, 2, 3, 4, 5, 6, 7, 8],
               'his kit is saved: dumbbells 1 to 8 kg')
            press = Exercise.objects.get(user=None,
                                         name='Dumbbell shoulder press')
            plank = Exercise.objects.get(user=None, name='Plank')
            r = post(ca, '/wellness/workouts/routines/new/', {
                'name': 'Upper body', 'weekdays': [str(day.weekday())],
                'action': 'add-first'})
            rt = Routine.objects.get(user=a)
            ok(rt.weekdays == str(day.weekday()),
               'a routine is made, on today\'s weekday')
            for ex in (press, plank):
                post(ca, '/wellness/workouts/routines/%d/' % rt.pk,
                     {'action': 'add', 'exercise': ex.pk,
                      'name': 'Upper body',
                      'weekdays': [str(day.weekday())]})
            items = list(rt.items.order_by('position'))
            ok([i.exercise_id for i in items] == [press.pk, plank.pk],
               '  with two exercises, in order')
            post(ca, '/wellness/workouts/routines/%d/' % rt.pk, {
                'action': 'save', 'name': 'Upper body',
                'weekdays': [str(day.weekday())],
                'rep_min_%d' % items[0].pk: '8',
                'rep_max_%d' % items[0].pk: '10',
                'sets_%d' % items[0].pk: '3'})
            ok(RoutineItem.objects.get(pk=items[0].pk).rep_max == 10,
               '  and its rep range is set')
            ok('Upper body' in ca.get('/wellness/').content.decode(),
               'Today shows the planned routine')
            ok(cb.get('/wellness/workouts/routines/%d/' % rt.pk).status_code
               == 404, "another member cannot open it")

            # A past workout: 6 kg x 10, 10, 10.
            past = WorkoutSession.objects.create(
                user=a, routine=rt, name='Upper body',
                date=day - dt.timedelta(days=2),
                started_at=timezone.now() - dt.timedelta(days=2),
                finished_at=timezone.now() - dt.timedelta(days=2))
            for n in (1, 2, 3):
                WorkoutSet.objects.create(session=past, exercise=press,
                                          set_no=n, weight=6, reps=10,
                                          done=True)
            r = post(ca, '/wellness/workouts/start/', {'routine': rt.pk})
            s = WorkoutSession.objects.filter(
                user=a, finished_at__isnull=True).first()
            ok(r.status_code == 302 and s is not None,
               'starting the routine opens a live workout')
            sets = list(s.sets.filter(exercise=press).order_by('set_no'))
            ok(len(sets) == 3 and all(x.weight == Decimal('7')
                                      and x.reps == 8 for x in sets),
               '  its sets are filled with the suggestion: 7 kg for 8')
            t = ca.get('/wellness/workouts/%d/live/' % s.pk).content.decode()
            ok('6 × 10' in t, '  last time\'s numbers sit beside each set')
            ok('7 kg today' in t, '  and it says why the weight went up')
            res = post(ca, '/wellness/workouts/sets/%d/' % sets[0].pk,
                       {'weight': '7', 'reps': '8', 'done': '1'},
                       fetch=True).json()
            ok(res['done'] and res['record'] == 'Heaviest yet: 7 kg',
               'ticking 7 kg x 8 is a record, celebrated at once', res)
            ok(res['rest'] == RoutineItem.objects.get(pk=items[0].pk).rest,
               '  and starts the routine\'s rest')
            res = post(ca, '/wellness/workouts/sets/%d/' % sets[1].pk,
                       {'weight': '7', 'reps': '8', 'done': '1'},
                       fetch=True).json()
            ok(res['record'] == '',
               'CONTROL: matching it in the next set is not another record')
            r = post(ca, '/wellness/workouts/sets/%d/' % sets[2].pk,
                     {'weight': 'heavy', 'reps': '8'}, fetch=True)
            ok(r.status_code == 400, 'a weight that is not a number is '
               'refused')
            ok(post(cb, '/wellness/workouts/sets/%d/' % sets[2].pk,
                    {'weight': '7', 'reps': '8'}).status_code == 404,
               'nobody can touch somebody else\'s set')
            h = Habit.objects.create(user=a, name='Train', kind='yes_no',
                                     schedule='per_week', per_week=5,
                                     started_on=day, auto_from='workout')
            r = post(ca, '/wellness/workouts/%d/finish/' % s.pk,
                     {'effort': '7', 'note': 'felt strong'})
            s.refresh_from_db()
            ok(s.finished_at and s.effort == 7,
               'finishing saves the time and the effort')
            ok(s.sets.count() == 2,
               '  the set left unticked is not kept (two of three, plus no '
               'plank)')
            ok(HabitLog.objects.filter(habit=h, date=day, done=True).exists(),
               'a habit set to tick itself from a workout is ticked')
            t = ca.get('/wellness/workouts/%d/' % s.pk).content.decode()
            ok('Nice work' in t and '1' in t and '112' in t,
               'the summary shows the time, 112 kg lifted and the record')
            t = ca.get('/wellness/workouts/exercises/%d/' % press.pk) \
                .content.decode()
            ok('Heaviest' in t and '7 kg' in t,
               'the exercise page shows the best')
            ok('6 × 10' not in cb.get('/wellness/workouts/exercises/%d/'
                                     % press.pk).content.decode()
               and 'Heaviest' not in cb.get(
                   '/wellness/workouts/exercises/%d/' % press.pk)
               .content.decode(),
               "  another member sees the exercise but none of his numbers")
            r = post(ca, '/wellness/workouts/exercises/new/', {
                'name': 'Sandbag carry', 'kind': 'distance',
                'muscle': 'full', 'equipment': 'none'})
            mine = Exercise.objects.get(name='Sandbag carry')
            ok(mine.user_id == a.pk, 'his own exercise is his')
            ok(cb.get('/wellness/workouts/exercises/%d/'
                      % mine.pk).status_code == 404,
               '  and invisible to anybody else')
            r = post(ca, '/wellness/workouts/start/')
            e2 = WorkoutSession.objects.filter(
                user=a, finished_at__isnull=True).first()
            ok(e2 and e2.name == 'Workout', 'an empty workout can be started')
            post(ca, '/wellness/workouts/%d/finish/' % e2.pk,
                 {'discard': 'yes'})
            ok(not WorkoutSession.objects.filter(pk=e2.pk).exists(),
               '  and discarded, leaving nothing behind')
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
ok("Text = 'def suggest('" in gate, '  with a sentinel on the progression')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
