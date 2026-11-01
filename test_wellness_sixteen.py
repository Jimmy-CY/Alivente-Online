# -*- coding: utf-8 -*-
"""test_wellness_sixteen.py - round WL-12, 1 Nov 2026.

RELEASE 59 - WELLNESS: WEEKLY CHALLENGES, THREE MARKS, EARLIER AMOUNTS.
Demetri, 12:13:
  1. "What is the meaning of Done, Comeback, Forgiven and Rest" - 12:24:
     "I would prefer to just have 3: Done, Missed and Rest". 12:26: the
     help says the first two missed days a month are forgiven and never
     spoil a streak.
  2. "Why am I only able to enter the minutes for Today, but not for a
     previous day?" - tap any of the last seven days (12:20: keep the 7).
  3. "Run 4 times a week for 30 minutes... make this a challenge... an 8
     week challenge" - weekly challenges for times a week and chosen days;
     4, 6, 8, 12 weeks or your own (12:20: "Correct. Go ahead." "Perfect").
     And choosing a challenge no longer turns a habit into an every-day one.
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

SUFFIX = '.bak_wellness16'
ME = 'test_wellness_sixteen.py'
PATCHER = 'apply_wellness_sixteen.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(APP, 'models.py'), J(APP, 'challenge.py'), J(APP, 'views.py'),
          J(APP, 'badges.py'), J(APP, 'help.py'), J(APP, 'guide.py'),
          J(APP, 'assets', 'wellness.css'), J(APP, 'assets', 'wellness.js'),
          J(WT, 'habit_detail.html'), J(WT, 'habit_form.html'),
          J(WT, 'today.html'), J(WT, 'base.html')]

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
ok(os.path.isfile(J(APP, 'migrations', '0011_weekly_challenges.py')),
   'MIGRATION 0011_weekly_challenges is on disk')
mig = read(J(APP, 'migrations', '0011_weekly_challenges.py'))
ok('"0010_workout_calories"' in mig and 'default="day"' in mig and
   'RemoveField' not in mig, '  one column, after 0010, every habit "day"')
det = read(J(WT, 'habit_detail.html'))
ok('Comeback' not in det and 'Forgiven' not in det and
   '<i class="miss"></i>Missed' in det,
   'THREE MARKS: the key shows Done, Missed and Rest - no Comeback, '
   'no Forgiven')
ok('first two missed days each month are forgiven' in det,
   '  and says the first two missed days a month are forgiven')
ok('data-day-pick' in det and 'name="date" value="{{ entry.iso }}"' in det,
   'EARLIER AMOUNTS: a day of the seven is picked, the box saves for it')
form = read(J(WT, 'habit_form.html'))
ok('name="challenge_w"' in form and
   'data-when-schedule="per_week weekdays"' in form,
   'THE FORM: week choices for times a week and chosen days')
js = read(J(APP, 'assets', 'wellness.js'))
ok("[name=schedule][value=daily]" not in js,
   'CHOOSING A CHALLENGE no longer flips the schedule to every day')
v = read(J(APP, 'views.py'))
ok('a challenge is every day.\n    if _challenge_choice' not in v and
   'schedule = Habit.SCHEDULE_DAILY\n    weekdays' not in v,
   '  nor does the server')
css = read(J(APP, 'assets', 'wellness.css'))
ok('--w-miss:' in css and '.w-cell.miss' in css and '.w-wstrip' in css,
   'THE STYLES: Missed is a grey outline; the weekly strip fills')
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px',
   [m for m in mins if int(m) < 44])
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('Comeback' in was(J(WT, 'habit_detail.html')),
   'CONTROL: before this round the key showed Comeback')
ok("value=daily]" in was(J(APP, 'assets', 'wellness.js')),
   'CONTROL: before this round a challenge flipped the schedule')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from wellness import challenge as CH                        # noqa: E402
from wellness.models import Habit                           # noqa: E402
D = dt.date
ok(CH.WEEKS == [4, 6, 8, 12] and CH.valid_weeks(10) and
   not CH.valid_weeks(1) and not CH.valid_weeks(53),
   'LENGTHS: 4, 6, 8, 12 weeks, or your own 2 to 52')


def run(start, n=8):
    h = Habit(name='Run', kind='duration', target=30, schedule='per_week',
              per_week=4, started_on=D(2026, 10, 1))
    CH.begin(h, n, start, CH.unit_for(h))
    return h


h = run(D(2026, 11, 2))           # a Monday
ok(h.challenge_unit == 'week', 'TIMES A WEEK: the challenge counts weeks')
s = CH.state(h, {D(2026, 11, 2), D(2026, 11, 4)}, D(2026, 11, 5))
ok(s['words'] == 'Week 1 of 8' and s['this_words'] == '2 of 4 this week',
   '  "Week 1 of 8 - 2 of 4 this week"', (s['words'], s['this_words']))
ok(s['strip'][0] == {'cls': 'now', 'pct': 50} and len(s['strip']) == 8,
   '  one square per week, half full', s['strip'][:2])
four = {D(2026, 11, 2), D(2026, 11, 3), D(2026, 11, 5), D(2026, 11, 7)}
s = CH.state(h, four, D(2026, 11, 10))
ok(s['words'] == 'Week 2 of 8' and s['strip'][0]['cls'] == 'done' and
   not s['ask'], '  four runs: the week counts, on to week 2')
s = CH.state(h, {D(2026, 11, 2)}, D(2026, 11, 10))
ok(s['ask'] == D(2026, 11, 2) and 'fell short' in s['ask_words'] and
   s['misses'] == 1 and 'failed' not in s['ask_words'].lower(),
   'A SHORT WEEK asks, kindly: "Last week fell short. That happens."',
   s['ask_words'])
f1 = s['finish']
CH.carry_on(h, D(2026, 11, 10))
s = CH.state(h, {D(2026, 11, 2)}, D(2026, 11, 10))
ok(s['ask'] is None and s['finish'] == f1 and f1.weekday() == 6,
   '  carry on: asked once, the finish is a Sunday a week further out')
CH.start_again(h, D(2026, 11, 10))
s = CH.state(h, {D(2026, 11, 2)}, D(2026, 11, 10))
ok(s['words'] == 'Week 1 of 8' and s['misses'] == 0,
   '  start again: week 1 is this week')
t = run(D(2026, 10, 29))          # a Thursday
ok(CH.week_target(t, D(2026, 10, 26), D(2026, 10, 29)) == 2,
   'A THURSDAY START: the first week asks for its share - 2 of 4')
s = CH.state(t, {D(2026, 10, 30), D(2026, 11, 1)}, D(2026, 11, 1))
ok(s['strip'][0]['cls'] == 'done' and s['this_words'] == '2 of 2 this week',
   '  two runs by Sunday and it counts', (s['words'], s['this_words']))
g = Habit(name='Gym', kind='yes_no', schedule='weekdays', weekdays='024',
          started_on=D(2026, 10, 1))
CH.begin(g, 4, D(2026, 11, 2), CH.unit_for(g))
s = CH.state(g, {D(2026, 11, 2)}, D(2026, 11, 3))
ok(g.challenge_unit == 'week' and s['this_words'] == '1 of 3 days this week',
   'CHOSEN DAYS (Mon, Wed, Fri): weeks too - "1 of 3 days this week"')
s = CH.state(g, {D(2026, 11, 2), D(2026, 11, 6)}, D(2026, 11, 9))
ok(s['strip'][0]['cls'] == 'done',
   '  a missed Wednesday is forgiven (first two a month): the week counts')
two = Habit(name='R', kind='yes_no', schedule='per_week', per_week=2,
            started_on=D(2026, 10, 1))
CH.begin(two, 2, D(2026, 11, 2), 'week')
s = CH.state(two, {D(2026, 11, 2), D(2026, 11, 3), D(2026, 11, 9),
                   D(2026, 11, 11)}, D(2026, 11, 12))
ok(s['finished'] == D(2026, 11, 11) and s['words'] == 'Finished: 2 weeks.',
   'FINISHED on the day the last week was met')
dly = Habit(name='W', kind='yes_no', schedule='daily',
            started_on=D(2026, 10, 1))
CH.begin(dly, 30, D(2026, 11, 1), CH.unit_for(dly))
s = CH.state(dly, {D(2026, 11, 1)}, D(2026, 11, 1))
ok(s['unit'] == 'day' and s['words'] == 'Day 1 of 30',
   'EVERY DAY: as before - "Day 1 of 30"')
from wellness import views as V                             # noqa: E402
ok(V.SHOWN == {'grace': 'miss'}, 'A FORGIVEN DAY SHOWS AS MISSED')
from wellness import habits as HB                           # noqa: E402
ok(HB.GRACE_PER_MONTH == 2, '  and is still forgiven behind the scenes')
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
hd = HELP.for_url_name('habit_detail')
words = ' '.join(hd['steps']) + ' '.join(w for _c, w in hd['signs'])
ok('Done, Missed or Rest' in words and 'never spoil your streak' in words
   and 'comeback' not in words.lower(),
   'HELP (habit): three marks, the forgiven two, no comebacks')
ok('Week 3 of 12' in words and 'carry on (the finish moves out a week)'
   in words, '  and the weekly challenge')
hf = ' '.join(HELP.for_url_name('habit_form')['steps'])
ok('4 times a' in hf and '12 weeks' in hf and '2 to 52' in hf,
   'HELP (form): "Run, 30 minutes, 4 times a week, 12 weeks"')
qs = ' '.join(h['q'] for h in G.HOWTO)
ok('What do Done, Missed and Rest mean?' in qs and
   'Will a missed day spoil my streak?' in qs and
   'How does a weekly challenge work?' in qs and 'comeback' not in qs,
   'THE GENERAL QUESTIONS answer all three')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile, HabitLog
    connection.ensure_connection()
    Habit.objects.filter(challenge_unit='week').exists()
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
            a = User.objects.create_user('w16_a', 'w16a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            r = ca.post('/wellness/habits/new/', {
                'name': 'Run', 'kind': 'duration', 'target': '30',
                'schedule': 'per_week', 'per_week': '4',
                'challenge': '30', 'challenge_w': '8',
                'time_of_day': 'anytime'})
            hb = Habit.objects.get(user=a, name='Run')
            ok(r.status_code == 302 and hb.schedule == 'per_week' and
               hb.per_week == 4 and hb.challenge_days == 8 and
               hb.challenge_unit == 'week',
               'NEW: Run, 4 times a week, 8 weeks - stays 4 times a week',
               (hb.schedule, hb.challenge_days, hb.challenge_unit))
            url = '/wellness/habits/%d/' % hb.pk
            t = ca.get(url).content.decode()
            ok('8-week challenge' in t and 'Week 1 of 8' in t and
               'data-this-week' in t and 'w-wstrip' in t,
               '  its page: "8-week challenge", "Week 1 of 8", the weeks')
            ok('Comeback' not in t and 'Forgiven' not in t and
               '>Done</span>' in t and '>Missed</span>' not in t,
               '  the key: Done and Rest - times a week has no missed days')
            today = timezone.localdate()
            y = today - dt.timedelta(days=2)
            t = ca.get(url + '?day=%s' % y.isoformat()).content.decode()
            ok(('value="%s"' % y.isoformat()) in t and 'aria-current="date"'
               in t and (y.strftime('%A ') + str(y.day)) in t,
               'EARLIER AMOUNTS: tap %s - the box is for that day' %
               y.strftime('%a'))
            r = ca.post('/wellness/habits/%d/check/' % hb.pk, {
                'op': 'set', 'date': y.isoformat(), 'value': '25',
                'next': url + '?day=' + y.isoformat()})
            lg = HabitLog.objects.filter(habit=hb, date=y).first()
            ok(lg and lg.value == 25 and not lg.done,
               '  25 of 30 minutes kept for that day, not yet done')
            r = ca.post('/wellness/habits/%d/check/' % hb.pk, {
                'op': 'set', 'date': y.isoformat(), 'value': '0'})
            ok(not HabitLog.objects.filter(habit=hb, date=y).exists(),
               '  0 clears it')
            old = today - dt.timedelta(days=9)
            r = ca.post('/wellness/habits/%d/check/' % hb.pk, {
                'op': 'set', 'date': old.isoformat(), 'value': '30'})
            ok(not HabitLog.objects.filter(habit=hb, date=old).exists(),
               '  still only the last seven days')
            r = ca.post('/wellness/habits/%d/edit/' % hb.pk, {
                'name': 'Run', 'kind': 'duration', 'target': '30',
                'schedule': 'daily', 'challenge': '30',
                'time_of_day': 'anytime'})
            hb.refresh_from_db()
            ok(hb.challenge_unit == 'day' and hb.challenge_days == 30,
               'EDIT to every day, 30 days: the challenge counts days')
            t = ca.get(url).content.decode()
            ok('>Missed</span>' in t and 'never spoil' not in t or
               'forgiven - they never spoil your streak' in t,
               '  every day: the key adds Missed, and the forgiven two')
            t = ca.get('/wellness/habits/%d/edit/' % hb.pk).content.decode()
            ok('name="challenge_w"' in t and
               'value="30" checked' in t, '  and the form shows 30 days')
            t = ca.get('/wellness/').content.decode()
            ok('Day 1 of 30' in t or 'data-challenge-day' in t,
               'TODAY still shows the challenge')
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
ok("Text = 'def week_state('" in gate, '  with a sentinel on the rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
