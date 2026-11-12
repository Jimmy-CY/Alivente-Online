# -*- coding: utf-8 -*-
"""test_wellness_twentyone.py - round WL-17, 12 Nov 2026.

RELEASE 65 - WELLNESS: WORKOUTS - SPORTS AND DANCE, STARTING NUMBERS, YOUR
OWN EXERCISES EDITED, DELETED OR HIDDEN. Bundled with Release 64.

Demetri, 07:54: "Can we add a section like Sports ... Padel, Netball,
Tennis, Squash and Soccer ... under Cardio ... Dance ... once I have create
my own exercise, then I should have the ability to Edit it and to Delete it
(with the appropriate checks)". 08:01: "Why do we have Reps from and to?
... x number of sets of y number of Reps, with a rest of z ... starting
weight ... For Zumba or other dances, would we would not measure in
seconds?? Maybe 3 sets of 15 minutes with 5 minute rest". 08:05: "when I
add an exercise, it will prompt me for sets, reps, rest and weight (or other
appropriate information based on exercise type). Then based on performance,
it will suggest more weight". 08:13: "Go ahead and develop, Test and
Bundle."
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

SUFFIX = '.bak_wellness21'
ME = 'test_wellness_twentyone.py'
PATCHER = 'apply_wellness_twentyone.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(APP, 'models.py'), J(APP, 'training.py'),
          J(APP, 'views_workouts.py'), J(APP, 'urls.py'), J(APP, 'help.py'),
          J(APP, 'guide.py'), J(APP, 'views.py'),
          J(APP, 'templatetags', 'wellness_modules.py'),
          J(APP, 'assets', 'wellness.css'), J(WT, 'base.html'),
          J(WT, 'routine_form.html'), J(WT, 'session_live.html'),
          J(WT, 'exercise_form.html'), J(WT, 'workouts.html'),
          J(WT, 'session_detail.html'), J(WT, 'exercise_detail.html')]

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
mig = read(J(APP, 'migrations', '0013_workouts_sports.py'))
ok('"0012_habit_pauses"' in mig and "('Padel', 'time', 'sport', 'ball')" in mig
   and "('Zumba', 'time', 'cardio', 'none')" in mig and
   "('Dance', 'time', 'cardio', 'none')" in mig and 'RemoveField' not in mig,
   'MIGRATION 0013: Sports, Racket or ball, hidden_at, a starting weight - '
   'and the new library exercises')
for n in ('Netball', 'Tennis', 'Squash', 'Soccer'):
    ok("('%s', 'time', 'sport', 'ball')" % n in mig, '  %s, under Sports' % n)
rf = read(J(WT, 'routine_form.html'))
ok('name="reps_{{ it.pk }}"' in rf and 'name="weight_{{ it.pk }}"' in rf and
   'name="minutes_{{ it.pk }}"' in rf and 'name="rest_min_{{ it.pk }}"' in rf
   and 'Aim for a range instead' in rf,
   'THE ROUTINE: one Reps number, a Weight, minutes for cardio - a range '
   'only if asked for')
ok('Set your starting numbers' in rf and 'is-new' in rf and 'autofocus' in rf,
   '  a new exercise opens asking for its starting numbers')
ef = read(J(WT, 'exercise_form.html'))
ok('Edit your exercise' in ef and 'data-kind-fixed' in ef and
   'Hide it' in ef and 'Yes, take it out of' in ef,
   'YOUR OWN EXERCISE: edit; counted fixed once logged; delete or hide')
ok(os.path.isfile(J(WT, 'my_exercises.html')) and
   'data-my-exercises-link' in read(J(WT, 'workouts.html')),
   'MY EXERCISES: a list of your own, linked from Workouts')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok("('sport', 'Sports')" not in was(J(APP, 'models.py')),
   'CONTROL: before this round there was no Sports')
ok('Reps from' in was(J(WT, 'routine_form.html')),
   'CONTROL: before this round a routine asked for a range')
css = read(J(APP, 'assets', 'wellness.css'))
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import training as TR                         # noqa: E402
from wellness.models import Exercise, RoutineItem          # noqa: E402
kit = {'dumbbells': [18, 20, 22.5, 25]}
s = TR.suggest(10, 10, [(20, 10), (20, 10), (20, 10)], 'dumbbell', kit)
ok(s['why'] == 'up' and s['weight'] == 22.5,
   'ONE NUMBER: 3 x 10 at 20 kg, every rep -> the next weight owned (22.5)',
   s)
s = TR.suggest(10, 10, [(20, 10), (20, 9), (20, 8)], 'dumbbell', kit)
ok(s['why'] == 'reps' and s['weight'] == 20,
   '  missed reps -> the same weight', s)
s = TR.suggest(12, 12, [(None, 12), (None, 12), (None, 12)], 'bodyweight', {})
ok(s['why'] == 'more_reps' and s['reps'] == 13,
   'REPS ONLY: every rep -> one more (13)', s)
ok(TR.suggest_hold(45, [45, 45, 50]) == (55, 'longer') and
   TR.suggest_hold(45, [45, 40]) == (45, ''),
   'A HOLD: held in full -> a little longer; not -> the same')
z = Exercise(name='Zumba', kind='time', muscle='cardio', equipment='none')
pl = Exercise(name='Plank', kind='time', muscle='core', equipment='none')
pd = Exercise(name='Padel', kind='time', muscle='sport', equipment='ball')
ok(TR.in_minutes(z) and TR.in_minutes(pd) and not TR.in_minutes(pl),
   'MINUTES for cardio, dance and sports; seconds for a hold')
ok(TR.item_words(RoutineItem(exercise=z, sets=3, seconds=900)) ==
   '3 × 15 min' and
   TR.item_words(RoutineItem(exercise=pl, sets=3, seconds=45)) == '3 × 45 s'
   and TR.item_words(RoutineItem(exercise=Exercise(kind='weight',
                                                   muscle='chest'),
                                 sets=3, rep_min=10, rep_max=10)) ==
   '3 × 10', '  "3 × 15 min", "3 × 45 s", "3 × 10"')
ok(TR.rest_words(300, True) == '5 min' and TR.rest_words(90) == '90 s',
   '  rest: "5 min" for cardio, "90 s" for a lift')
from wellness.templatetags import wellness_modules as WM   # noqa: E402
ok(WM.nice_secs(2700) == '45 min' and WM.nice_secs(45) == '45 s',
   'PAST WORKOUTS read 45 min, not 2700 s')
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok(HELP.for_url_name('my_exercises') and HELP.for_url_name('exercise_edit')
   and 'starting weight' in ' '.join(HELP.for_url_name('routine_form')['steps']),
   'HELP: My exercises, editing, and the starting numbers')
qs = [h['q'] for h in G.HOWTO]
ok('Set up: a routine with your starting numbers' in qs and
   'Set up: edit or delete an exercise you made' in qs and
   'Where do sports and dance go?' in qs,
   '  and the general questions answer all three')
ok('Reps from - to' not in ' '.join(' '.join(h.get('steps', []))
                                    for h in G.HOWTO),
   '  no answer still says "Reps from - to"')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import (WellnessProfile, Routine, WorkoutSession,
                                 WorkoutSet)
    connection.ensure_connection()
    Exercise.objects.filter(hidden_at__isnull=True).exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

if have_db:
    from decimal import Decimal
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
            a = User.objects.create_user('w21_a', 'w21a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            b = User.objects.create_user('w21_b', 'w21b@example.com', 'x')
            b.user_permissions.add(perm)
            WellnessProfile.objects.create(user=b, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            lib = set(Exercise.objects.filter(user__isnull=True)
                      .values_list('name', flat=True))
            ok({'Padel', 'Netball', 'Tennis', 'Squash', 'Soccer', 'Dance',
                'Zumba'} <= lib, 'THE LIBRARY has the sports and dances')
            rt = Routine.objects.create(user=a, name='Mix')
            bench = Exercise.objects.get(user=None,
                                         name='Barbell bench press')
            r = ca.post('/wellness/workouts/routines/%d/' % rt.pk,
                        {'action': 'add', 'exercise': bench.pk,
                         'name': 'Mix'})
            it = rt.items.get(exercise=bench)
            ok(r.status_code == 302 and ('?new=%d' % it.pk) in r['Location']
               and it.sets == 3 and it.rep_min == it.rep_max == 10 and
               it.rest == 90,
               'ADDED: opens asking for its numbers, starting at 3 x 10, '
               'rest 90 s')
            t = ca.get(r['Location']).content.decode()
            ok('Set your starting numbers' in t and
               ('name="weight_%d"' % it.pk) in t,
               '  the page asks, with a Weight box')
            ca.post('/wellness/workouts/routines/%d/' % rt.pk, {
                'action': 'save', 'name': 'Mix', 'sets_%d' % it.pk: '3',
                'reps_%d' % it.pk: '8', 'weight_%d' % it.pk: '20',
                'rest_%d' % it.pk: '120'})
            it.refresh_from_db()
            ok(it.rep_min == it.rep_max == 8 and it.weight == Decimal('20')
               and it.rest == 120,
               'SAVED: 3 x 8 at 20 kg, rest 120 s')
            zumba = Exercise.objects.get(user=None, name='Zumba')
            ca.post('/wellness/workouts/routines/%d/' % rt.pk,
                    {'action': 'add', 'exercise': zumba.pk, 'name': 'Mix'})
            iz = rt.items.get(exercise=zumba)
            ok(iz.sets == 1 and iz.seconds == 1800 and iz.rest == 0,
               'ZUMBA starts at 1 x 30 min')
            ca.post('/wellness/workouts/routines/%d/' % rt.pk, {
                'action': 'save', 'name': 'Mix', 'sets_%d' % iz.pk: '3',
                'minutes_%d' % iz.pk: '15', 'rest_min_%d' % iz.pk: '5'})
            iz.refresh_from_db()
            ok(iz.sets == 3 and iz.seconds == 900 and iz.rest == 300,
               '  3 x 15 min, rest 5 min - stored, and read back in minutes')
            r = ca.post('/wellness/workouts/start/', {'routine': rt.pk})
            s = WorkoutSession.objects.get(user=a, finished_at__isnull=True)
            first = WorkoutSet.objects.filter(session=s, exercise=bench)
            ok(first.count() == 3 and
               all(x.weight == Decimal('20') and x.reps == 8 for x in first),
               'THE FIRST WORKOUT starts from the starting weight: 20 kg x 8')
            t = ca.get('/wellness/workouts/%d/live/' % s.pk).content.decode()
            ok('3 × 15 min' in t and 'rest 5 min' in t and
               'name="minutes"' in t,
               '  and shows Zumba as "3 × 15 min · rest 5 min", in minutes')
            # ---- your own exercise
            ca.post('/wellness/workouts/exercises/new/', {
                'name': 'My Zumba', 'kind': 'weight', 'muscle': 'full',
                'equipment': 'none'})
            mine = Exercise.objects.get(user=a, name='My Zumba')
            r = ca.post('/wellness/workouts/exercises/%d/edit/' % mine.pk, {
                'name': 'Zumba night', 'kind': 'time', 'muscle': 'cardio',
                'equipment': 'none'})
            mine.refresh_from_db()
            ok(mine.name == 'Zumba night' and mine.kind == 'time' and
               mine.muscle == 'cardio',
               'EDIT: renamed, moved to Cardio, counted by time (not logged '
               'yet)')
            cb = Client(SERVER_NAME='localhost')
            cb.force_login(b)
            ok(cb.get('/wellness/workouts/exercises/%d/edit/' % mine.pk)
               .status_code == 404 and
               cb.post('/wellness/workouts/exercises/%d/delete/' % mine.pk)
               .status_code == 404,
               '  nobody else can edit or delete it')
            ok(ca.get('/wellness/workouts/exercises/%d/edit/' % bench.pk)
               .status_code == 404, '  nor a built-in one be edited')
            t = ca.get('/wellness/workouts/exercises/%d/edit/'
                       % mine.pk).content.decode()
            ok('not in any routine or workout' in t,
               'DELETE, never used: says so')
            rt.items.create(exercise=mine, position=9)
            t = ca.get('/wellness/workouts/exercises/%d/edit/'
                       % mine.pk).content.decode()
            ok('It is in 1 routine: Mix' in t,
               'DELETE, in a routine: names it')
            r = ca.post('/wellness/workouts/exercises/%d/delete/' % mine.pk)
            ok(r.status_code == 400 and Exercise.objects.filter(
                pk=mine.pk).exists(), '  and will not without the tick')
            WorkoutSet.objects.create(session=s, exercise=mine, set_no=1,
                                      seconds=600, done=True)
            r = ca.post('/wellness/workouts/exercises/%d/edit/' % mine.pk, {
                'name': 'Zumba night', 'kind': 'weight', 'muscle': 'cardio',
                'equipment': 'none'})
            mine.refresh_from_db()
            ok(mine.kind == 'time' and b'stays as it is' in r.content,
               'LOGGED: how it is counted can no longer change')
            r = ca.post('/wellness/workouts/exercises/%d/delete/' % mine.pk,
                        {'confirm': 'yes'})
            ok(r.status_code == 400 and Exercise.objects.filter(
                pk=mine.pk).exists(),
               '  and it cannot be deleted - the workout keeps it')
            ca.post('/wellness/workouts/exercises/%d/hide/' % mine.pk)
            mine.refresh_from_db()
            ok(mine.hidden_at is not None and
               not rt.items.filter(exercise=mine).exists() and
               WorkoutSet.objects.filter(exercise=mine).exists(),
               'HIDE: off the routine, still in the workout')
            t = ca.get('/wellness/workouts/routines/%d/' % rt.pk) \
                .content.decode()
            ok('Zumba night' not in t, '  and off the exercise list')
            t = ca.get('/wellness/workouts/exercises/mine/').content.decode()
            ok('Zumba night' in t and 'hidden' in t and 'Bring back' in t,
               '  My exercises shows it hidden, with Bring back')
            ca.post('/wellness/workouts/exercises/%d/hide/' % mine.pk,
                    {'back': '1'})
            mine.refresh_from_db()
            ok(mine.hidden_at is None, '  Bring back puts it back')
            spare = Exercise.objects.create(user=a, name='Spare', kind='reps',
                                            muscle='core',
                                            equipment='bodyweight')
            ca.post('/wellness/workouts/exercises/%d/delete/' % spare.pk)
            ok(not Exercise.objects.filter(pk=spare.pk).exists(),
               'DELETE, never used: gone')
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
ok("Text = 'def in_minutes('" in gate, '  with a sentinel on the rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
