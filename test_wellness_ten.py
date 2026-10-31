# -*- coding: utf-8 -*-
"""test_wellness_ten.py - round WL-8, 31 Oct 2026.

RELEASE 53 - WELLNESS: CHALLENGES. A habit with a finish line: 7, 14, 21
or 30 days, every day. Demetri, 31 Oct 14:26: when a day is missed, "give
the option of continueing, but extending by a day, or restarting". 15:46:
Challenges first, before the cycle-tracker work.

    - "Day 12 of 30" on Today; a square for each day on the habit.
    - A missed day is asked about ONCE: Carry on (the finish moves out a
      day) or Start again today; after three in a row, Pause it too.
      Never "failed", never "lost".
    - The finish: keep it as a habit, go again, or let it go; a
      "Challenge finished" badge.
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

SUFFIX = '.bak_wellness10'
ME = 'test_wellness_ten.py'
PATCHER = 'apply_wellness_ten.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(WT, 'base.html'), J(WT, 'today.html'), J(WT, 'habit_form.html'),
          J(WT, 'habit_detail.html'), J(APP, 'assets', 'wellness.css'),
          J(APP, 'assets', 'wellness.js'), J(APP, 'views.py'),
          J(APP, 'models.py'), J(APP, 'badges.py'), J(APP, 'guide.py'),
          J(APP, 'help.py')]

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
ok(os.path.isfile(J(APP, 'challenge.py')) and
   os.path.isfile(J(APP, 'migrations', '0009_challenges.py')),
   'wellness/challenge.py and migration 0009 are there')
form = read(J(WT, 'habit_form.html'))
ok('name="challenge"' in form and 'Make it a challenge' in form and
   'Or try a challenge' in form,
   'the habit form: "Make it a challenge", and challenges to try')
today_t = read(J(WT, 'today.html'))
ok('data-challenge-day' in today_t and 'data-challenge-finish' in today_t
   and 'data-challenge-ask' in today_t,
   'Today: "Day N of D", the finish card, and the missed-day question')
ok('Carry on' in today_t and 'Start again today' in today_t,
   '  the question offers Carry on and Start again')
det = read(J(WT, 'habit_detail.html'))
ok('class="w-strip"' in det and 'data-challenge-card' in det,
   'the habit page: a square for each day to do')
css = read(J(APP, 'assets', 'wellness.css'))
ok('.w-strip i.done' in css, '  styled')
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
js = read(J(APP, 'assets', 'wellness.js'))
ok("set('challenge', p.challenge || '')" in js and
   "[name=schedule][value=daily]" in js,
   'a challenge to try fills the form; a challenge is every day')
base = read(J(WT, 'base.html'))
v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
# Later rounds move the version on; the page and the service worker must
# always name the same one.
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl10-1)', v)
words = ' '.join([today_t, det, form]).lower()
ok('failed' not in words and ' lost' not in words and 'broke' not in words,
   'NEVER "failed", "lost" or "broken"')
import glob as _g                                            # noqa: E402
multi = []
for _f in sorted(_g.glob(J(WT, '**', '*.html'), recursive=True)):
    for _n, _line in enumerate(read(_f).split('\n'), 1):
        if '{#' in _line and '#}' not in _line.split('{#', 1)[1]:
            multi.append('%s:%d' % (os.path.relpath(_f, ROOT), _n))
ok(not multi, 'no note runs over two lines (it would show on screen)', multi)
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('name="challenge"' not in was(J(WT, 'habit_form.html')),
   'CONTROL: before this round a habit could not be a challenge')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
import types                                                # noqa: E402
from wellness import challenge as CH                        # noqa: E402
D = dt.date


def hab(days=7, start=D(2026, 10, 25), seen=None, fin=None):
    return types.SimpleNamespace(challenge_days=days, challenge_from=start,
                                 challenge_seen=seen, challenge_done_on=fin)


ok(CH.DAYS == [7, 14, 21, 30], '7, 14, 21 or 30 days')
h = hab()
done = {D(2026, 10, 25), D(2026, 10, 26), D(2026, 10, 28), D(2026, 10, 29)}
s = CH.state(h, done, D(2026, 10, 31))
ok(s['got'] == 4 and s['day'] == 5 and s['words'] == 'Day 5 of 7',
   'ONLY DONE DAYS COUNT: four done, so today is "Day 5 of 7"', s['words'])
ok(s['misses'] == 2 and s['finish'] == D(2026, 11, 2),
   '  two misses: it finishes on 2 Nov, not 31 Oct (carry on = a day '
   'added for each)', s['finish'])
ok(s['ask'] == D(2026, 10, 30) and s['ask_words'].startswith('Yesterday'),
   'yesterday was missed: it asks, once', s['ask_words'])
ok(not s['can_pause'], '  one miss: no "pause" offered yet')
ok(s['strip'] == ['done'] * 4 + ['today', 'todo', 'todo'],
   'the strip: four done, today next, two to do')
CH.carry_on(h, D(2026, 10, 31))
ok(CH.state(h, done, D(2026, 10, 31))['ask'] is None,
   'CARRY ON: asked and answered - it does not ask again')
CH.start_again(h, D(2026, 10, 31))
s2 = CH.state(h, done, D(2026, 10, 31))
ok(s2['got'] == 0 and s2['day'] == 1 and s2['finish'] == D(2026, 11, 6),
   'START AGAIN: day 1 is today, finishing in seven days', s2['finish'])
h3 = hab(start=D(2026, 10, 20))
s3 = CH.state(h3, {D(2026, 10, 20), D(2026, 10, 21)}, D(2026, 10, 31))
ok(s3['in_a_row'] == 9 and s3['can_pause'] and
   s3['ask_words'].startswith('A few days'),
   'many days in a row: kind words, and "pause it" is offered')
h4 = hab()
all7 = {D(2026, 10, 25) + dt.timedelta(days=i) for i in range(8)}
s4 = CH.state(h4, all7, D(2026, 11, 1))
ok(s4['finished'] == D(2026, 10, 31) and s4['words'] == 'Finished: 7 days.'
   and s4['ask'] is None,
   'THE FINISH: the seventh done day, and nothing more is asked')
ok(CH.rows(['todo'] * 30) == [['todo'] * 15] * 2 and
   len(CH.rows(['todo'] * 7)) == 1, 'thirty squares in two rows of fifteen')
ok([a for a, _w in CH.FINISH_ACTIONS] == ['challenge_keep', 'challenge_again',
                                          'challenge_letgo'],
   'the finish offers keep, go again, let it go')
ok(all(p['challenge'] in CH.DAYS and p['schedule'] == 'daily'
       for _l, p in CH.STARTERS), 'every challenge to try is every day')
from wellness import help as HELP                           # noqa: E402
ok('challenge' in ' '.join(HELP.SCREENS['habit_detail']['steps']).lower(),
   "the habit page's help explains the squares")

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import Habit, HabitLog, WellnessProfile
    connection.ensure_connection()
    Habit.objects.filter(challenge_days__isnull=False).exists()
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
            a = User.objects.create_user('w10_a', 'w10a@example.com', 'x')
            b = User.objects.create_user('w10_b', 'w10b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            day = timezone.localdate()
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            t = ca.get('/wellness/habits/new/').content.decode()
            ok('30 days of no sugar' in t and '&quot;challenge&quot;: 30' in t,
               'the new-habit screen offers challenges to try')
            r = ca.post('/wellness/habits/new/', {
                'name': 'No sugar', 'kind': 'avoid', 'schedule': 'per_week',
                'per_week': '3', 'time_of_day': 'anytime',
                'challenge': '7'})
            h = Habit.objects.get(user=a, name='No sugar')
            ok(r.status_code == 302 and h.challenge_days == 7 and
               h.challenge_from == day and h.schedule == 'daily',
               'A 7-DAY CHALLENGE begins today - and a challenge is every '
               'day, whatever was picked', (h.challenge_days, h.schedule))
            t = ca.get('/wellness/').content.decode()
            ok('data-challenge-day>Day 1 of 7<' in t,
               'Today: "Day 1 of 7"')
            t = ca.get('/wellness/habits/%d/' % h.pk).content.decode()
            ok('data-challenge-card' in t and t.count('<i class="today">')
               == 1 and t.count('<i class="todo">') == 6,
               'the habit page: seven squares, today first')
            # Back-date it: started four days ago, two days done.
            h.challenge_from = h.started_on = day - dt.timedelta(days=4)
            h.save()
            for k in (4, 3):
                HabitLog.objects.create(habit=h, date=day -
                                        dt.timedelta(days=k), done=True)
            t = ca.get('/wellness/').content.decode()
            ok('data-challenge-ask' in t and 'A few days slipped by' in t and
               'Day 3 of 7' in t,
               'MISSED DAYS: asked on Today, kindly ("Day 3 of 7")')
            ok('pause it for now' in t,
               '  three in a row: "pause it for now" is offered too')
            ca.post('/wellness/habits/%d/challenge_carry/' % h.pk,
                    {'next': '/wellness/'})
            h.refresh_from_db()
            t = ca.get('/wellness/').content.decode()
            ok(h.challenge_seen == day - dt.timedelta(days=1) and
               'data-challenge-ask' not in t and 'Day 3 of 7' in t,
               'CARRY ON: no more asking; still day 3 of 7')
            ca.post('/wellness/habits/%d/challenge_restart/' % h.pk)
            h.refresh_from_db()
            ok(h.challenge_from == day and 'Day 1 of 7' in
               ca.get('/wellness/').content.decode(),
               'START AGAIN: day 1 is today')
            # Finish it: seven days done, the last today.
            h.challenge_from = day - dt.timedelta(days=6)
            h.save()
            HabitLog.objects.filter(habit=h).delete()
            for k in range(7):
                HabitLog.objects.create(habit=h, date=day -
                                        dt.timedelta(days=k), done=True)
            t = ca.get('/wellness/').content.decode()
            h.refresh_from_db()
            ok('data-challenge-finish' in t and
               'You finished 7 days of No sugar' in t and
               h.challenge_done_on == day,
               'THE FINISH CARD on Today, and the day kept')
            ok('Challenge finished' in ca.get('/wellness/badges/')
               .content.decode(), '  with the "Challenge finished" badge')
            ca.get('/wellness/')
            pa = WellnessProfile.objects.get(user=a)
            ok(len(pa.prefs.get('challenges') or []) == 1,
               '  noted once, however often Today is opened')
            ca.post('/wellness/habits/%d/challenge_keep/' % h.pk,
                    {'next': '/wellness/'})
            h.refresh_from_db()
            t = ca.get('/wellness/').content.decode()
            ok(h.challenge_days is None and not h.archived_at and
               'data-challenge-finish' not in t,
               'KEEP IT AS A HABIT: an ordinary habit again, history kept')
            ca.post('/wellness/habits/%d/edit/' % h.pk, {
                'name': 'No sugar', 'kind': 'avoid', 'schedule': 'daily',
                'time_of_day': 'anytime', 'challenge': '14'})
            h.refresh_from_db()
            ok(h.challenge_days == 14 and h.challenge_from == day,
               'a habit can become a challenge when edited')
            ca.post('/wellness/habits/%d/edit/' % h.pk, {
                'name': 'No sugar!', 'kind': 'avoid', 'schedule': 'daily',
                'time_of_day': 'anytime', 'challenge': '14'})
            h.refresh_from_db()
            ok(h.challenge_from == day and h.challenge_days == 14,
               '  editing something else leaves it running')
            ca.post('/wellness/habits/%d/challenge_letgo/' % h.pk)
            h.refresh_from_db()
            ok(h.archived_at and h.logs.count() == 7,
               'LET IT GO: archived, its history kept')
            cb = Client(SERVER_NAME='localhost')
            cb.force_login(b)
            ok(cb.post('/wellness/habits/%d/challenge_restart/' % h.pk)
               .status_code == 404, "another member cannot touch it")
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
ok("Text = 'def carry_on('" in gate, '  with a sentinel on the challenges')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
