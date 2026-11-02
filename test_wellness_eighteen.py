# -*- coding: utf-8 -*-
"""test_wellness_eighteen.py - round WL-14, 2 Nov 2026.

RELEASE 61 - WELLNESS: INSIGHTS WITHOUT EMPTY CHARTS.
Demetri, 05:18: "For the Insights, if a graph has NO data, should that graph
not be hidden (like mood in this case)? What do you think?" 05:19: "Build
it".
    - The charts start at the first week with anything in it.
    - A chart with nothing in it is one line saying how to fill it (Mood
      above all - the findings need moods).
    - No "0" over an empty week.
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

SUFFIX = '.bak_wellness18'
ME = 'test_wellness_eighteen.py'
PATCHER = 'apply_wellness_eighteen.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(APP, 'insights.py'), J(APP, 'views.py'), J(APP, 'help.py'),
          J(APP, 'guide.py'), J(WT, 'insights.html')]

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
t = read(J(WT, 'insights.html'))
ok(t.count('data-ins-empty') == 4,
   'FOUR CHARTS can say they are empty: habits, mood, Calm, workouts')
ok('No moods yet. Add one in the evening check-in' in t,
   '  Mood says how to fill it')
ok('<b>{% if b.v %}{{ b.v }}{% endif %}</b>' in t and
   t.count('style="{{ cols }}"') == 5,
   'NO "0" over an empty week; as many columns as weeks shown')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('data-ins-empty' not in was(J(WT, 'insights.html')),
   'CONTROL: before this round an empty chart was drawn anyway')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from wellness import insights as INS                        # noqa: E402
T = dt.date(2026, 11, 2)
rows = INS.weekly(T, {}, {T - dt.timedelta(days=7): (1, 1), T: (1, 1)},
                  {}, set())
tr = INS.trim(rows)
ok(len(rows) == 8 and len(tr) == 2 and tr[0]['label'] == '26 Oct',
   'TRIM: from the first week with anything in it - two weeks, not eight',
   [r['label'] for r in tr])
ok(len(INS.trim(INS.weekly(T, {}, {}, {}, set()))) == 1,
   '  nothing at all: just this week')
e = INS.empty(tr)
ok(e == {'habits': False, 'mood': True, 'calm': True, 'workouts': True},
   'EMPTY: mood, Calm and workouts empty; habits not', e)
z = INS.weekly(T, {}, {T: (0, 2)}, {}, set())
ok(not INS.empty(INS.trim(z))['habits'],
   '  habits at 0% is something to see, not empty')
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok('says how to fill it' in ' '.join(HELP.for_url_name('insights')['steps']),
   'HELP: Insights explains the empty-chart line')
ok('growing to eight' in [h for h in G.HOWTO
                          if h['q'] == 'What is Insights?'][0]['a'],
   '  and the general question says up to eight weeks')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile, Habit, HabitLog
    connection.ensure_connection()
    WellnessProfile.objects.exists()
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
            a = User.objects.create_user('w18_a', 'w18a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            today = timezone.localdate()
            hb = Habit.objects.create(user=a, name='Walk', kind='yes_no',
                                      schedule='daily',
                                      started_on=today - dt.timedelta(days=8))
            for k in range(9):
                HabitLog.objects.create(habit=hb, done=True,
                                        date=today - dt.timedelta(days=k))
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            t = ca.get('/wellness/insights/').content.decode()
            ok('Week by week since you started' in t and
               ('repeat(2,minmax(0,1fr))' in t or
                'repeat(3,minmax(0,1fr))' in t),
               'DRIVEN: a habit begun eight days ago - two or three weeks '
               'shown, not eight')
            ok('No moods yet' in t and 'No Calm minutes yet' in t and
               'No workouts yet' in t and t.count('w-ins-bars') == 1,
               '  mood, Calm and workouts are one line each; habits drawn')
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
ok("Text = 'def trim('" in gate, '  with a sentinel on the trim')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
