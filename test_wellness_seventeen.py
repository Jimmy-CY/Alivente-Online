# -*- coding: utf-8 -*-
"""test_wellness_seventeen.py - round WL-13, 1 Nov 2026.

RELEASE 60 - WELLNESS: DEEPER HELP.
Demetri, 17:26: "Make sure that all the Help is relevant and updated. Can
we improve the Help by giving even more how-to's tips and help to set up
tricky items?"

    - Step-by-step set-ups for the tricky things, with the real button
      names: the Samsung install, fingerprint sign-in, reminders (and the
      Samsung battery setting), shortcuts, a weekly challenge, a habit that
      ticks itself, a routine with equipment, logging with calories, the
      cycle tracker.
    - "When something is not working": reminders, an out-of-date look,
      the voice, signing in again, a wrong tick.
    - The questions in topics, set-ups first; "Good to know" tips on the
      trickier screens; stale lines brought up to date.
    - A line-by-line check of the help against the code (a separate
      reviewer) found the app breaking two promises its own screens make.
      17:40, "Fix the app": PAUSED DAYS ARE REST, and an ESTABLISHED habit
      leaves Today and stops reminding. Migration 0012_habit_pauses.
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

SUFFIX = '.bak_wellness17'
ME = 'test_wellness_seventeen.py'
PATCHER = 'apply_wellness_seventeen.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(APP, 'models.py'), J(APP, 'habits.py'), J(APP, 'challenge.py'),
          J(APP, 'guide.py'), J(APP, 'help.py'), J(APP, 'views.py'),
          J(APP, 'templatetags', 'wellness_help.py'),
          J(APP, 'assets', 'wellness.css'), J(WT, 'base.html'),
          J(WT, 'guide.html')]

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
base = read(J(WT, 'base.html'))
ok('{% for name, qs in hp.groups %}' in base and 'h.steps' in base and
   'data-help-tips' in base,
   'THE HELP SHEET: questions in topics, numbered steps, Good to know')
gp = read(J(WT, 'guide.html'))
ok('data-guide-topic' in gp and 'h.steps' in gp,
   'THE GUIDE PAGE: the same topics and steps')
ok('data-no-missed' in read(J(WT, 'habit_detail.html')),
   'A TIMES-A-WEEK CALENDAR says why it has no Missed (17:45)')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('Set up:' not in was(J(APP, 'guide.py')),
   'CONTROL: before this round there were no step-by-step set-ups')
v = re.findall(r'\?v=([\w-]+)', base)
ok(len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in read(J(APP, 'views.py')),
   'the asset version moved together (%s)' % (v[0] if v else '?'))

# ==========================================================================
head('2. THE WORDS')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import guide as G                             # noqa: E402
from wellness import help as HELP                           # noqa: E402
qs = {h['q']: h for h in G.HOWTO}
setups = [q for q in qs if q.startswith('Set up:')]
ok(len(setups) >= 9, 'SET-UPS: %d step-by-step guides' % len(setups),
   setups)
want = ['Samsung phone', 'fingerprint', 'reminders on a Samsung',
        'shortcuts', 'weekly challenge', 'ticks itself', 'heavier',
        'calories', 'cycle tracker']
miss = [w for w in want if not any(w in q for q in setups)]
ok(not miss, '  install, fingerprint, reminders, shortcuts, weekly '
   'challenge, self-ticking habit, routine, calories, cycle', miss)
ok(all(2 <= len(qs[q].get('steps', [])) <= 6 for q in setups),
   '  each in two to six numbered steps')
allsteps = ' '.join(' '.join(h.get('steps', [])) for h in G.HOWTO)
ok('Battery: choose Unrestricted' in allsteps and
   'Add a passkey on this device' in allsteps and
   '"Send me a test"' in allsteps,
   '  with the real button names - and the Samsung battery setting')
fixes = [h['q'] for h in G.HOWTO if h['topic'] == 'fix']
ok(len(fixes) >= 5 and 'Reminders do not arrive' in fixes and
   'Wellness looks out of date after an update' in fixes,
   'WHEN SOMETHING IS NOT WORKING: %d answers' % len(fixes))
names = [n for n, _q in G.grouped()]
ok(names[0] == 'Getting set up' and names[-1] ==
   'When something is not working' and len(names) >= 8,
   'TOPICS: set-up first, fixes last', names)
ok(sum(len(q) for _n, q in G.grouped()) == len(G.HOWTO),
   '  every question in exactly one topic')
ok(all(G.grouped()[0][1][i]['q'].startswith('Set up:') for i in range(4)),
   '  set-ups lead their topic')
tipped = [k for k, e in HELP.SCREENS.items() if e.get('tips')]
ok(len(tipped) >= 15, 'GOOD TO KNOW on %d screens' % len(tipped))
long = [t for e in HELP.SCREENS.values() for t in e.get('tips', [])
        if len(t.split()) > 30]
ok(not long, '  each tip short', long)
ok('workout calories' in ' '.join(HELP.for_url_name('insights')['steps'])
   and 'My equipment' in ' '.join(HELP.for_url_name('workouts')['steps'])
   and 'stays awake' in ' '.join(HELP.for_url_name('session_live')['steps']),
   'STALE LINES UPDATED: Insights calories, My equipment, screen awake')
ok('My kit' not in ' '.join(' '.join(e['steps']) + e['title'] for e in
                            HELP.SCREENS.values()),
   '  no screen calls it "My kit" any more - the page says My equipment')
everything = ' '.join(h['q'] + ' ' + h['a'] + ' ' +
                      ' '.join(h.get('steps', [])) for h in G.HOWTO)
everything += ' '.join(' '.join(e['steps'] + e.get('tips', []))
                       for e in HELP.SCREENS.values())
ok(not any(w in everything.lower() for w in ('comeback', 'forgiven ('
                                              'outline', 'sand square',
                                              'grace day')),
   'NOTHING STALE: no comebacks, sand squares or grace days')
ok('!' not in everything and ' failed' not in everything.lower(),
   '  and still no exclamation marks or "failed"')

# ---- the two broken promises, fixed
import datetime as dt                                       # noqa: E402
from wellness import habits as HB                           # noqa: E402
from wellness import challenge as CHL                       # noqa: E402
from wellness.models import Habit                           # noqa: E402
D = dt.date
h = Habit(name='W', kind='yes_no', schedule='daily', started_on=D(2026, 10, 1))
dn = {D(2026, 10, 1) + dt.timedelta(days=i) for i in range(10)}
HB.start_pause(h, D(2026, 10, 11))
HB.end_pause(h, D(2026, 10, 25))
st = HB.day_states(h, dn, D(2026, 10, 27))
ok(h.pauses == [['2026-10-11', '2026-10-24']] and
   st[D(2026, 10, 11)] == 'rest' and st[D(2026, 10, 24)] == 'rest' and
   st[D(2026, 10, 25)] != 'rest',
   'PAUSE: paused days are Rest; the resume day counts again')
ok(HB.consistency(h, dn | {D(2026, 10, 25), D(2026, 10, 26)},
                  D(2026, 10, 26)) == 1.0,
   '  and never touch the 30-day percentage')
ok(HB.week_streak(h, dn | {D(2026, 10, 25), D(2026, 10, 26)},
                  D(2026, 10, 27)) >= 2,
   '  nor break the streak')
h2 = Habit(name='W', kind='yes_no', schedule='daily', started_on=D(2026, 10, 1))
HB.start_pause(h2, D(2026, 10, 5))
HB.end_pause(h2, D(2026, 10, 5))
ok(h2.pauses == [], '  paused and resumed the same day: nothing left behind')
c = Habit(name='C', kind='yes_no', schedule='daily', started_on=D(2026, 10, 1))
CHL.begin(c, 30, D(2026, 10, 1))
c.pauses = [['2026-10-03', '2026-10-06']]
ok(CHL.state(c, {D(2026, 10, 1), D(2026, 10, 2), D(2026, 10, 7)},
             D(2026, 10, 8))['misses'] == 0,
   '  a challenge counts no misses while paused')
w = Habit(name='R', kind='yes_no', schedule='per_week', per_week=3,
          started_on=D(2026, 10, 1))
w.pauses = [['2026-10-05', '2026-10-11']]
ok(HB.weekly_target(w, D(2026, 10, 5)) == 0,
   '  a times-a-week habit paused all week owes nothing that week')
r = Habit(name='Run', kind='duration', target=30, schedule='per_week',
          per_week=4, started_on=D(2026, 11, 1))
CHL.begin(r, 8, D(2026, 11, 1), 'week')
s = CHL.state(r, {D(2026, 11, 1)}, D(2026, 11, 1))
ok(s['words'] == 'Week 1 of 8 done' and
   'week 2 starts on Monday' in s['this_words'] and
   'a short first week: you began on a Sunday' in s['this_words'],
   'A MET WEEK says so: "Week 1 of 8 done - week 2 starts on Monday"',
   (s['words'], s['this_words']))
e = Habit(name='E', kind='yes_no', schedule='daily', started_on=D(2026, 1, 1),
          established_at=D(2026, 10, 1))
ok(not HB.due_today(e, set(), D(2026, 11, 1)),
   'ESTABLISHED: off Today (and so no reminder)')
ok('established_at__isnull=True' in read(J(APP, 'views.py')),
   '  Today leaves established habits out')
ok('paused' in was(J(APP, 'habits.py')) and
   'def is_paused_on' not in was(J(APP, 'habits.py')),
   'CONTROL: before this round a paused day could be Missed')
ok(os.path.isfile(J(APP, 'migrations', '0012_habit_pauses.py')),
   'MIGRATION 0012_habit_pauses is on disk')
# ---- the review's wording fixes
hp = ' '.join(HELP.for_url_name('habit_detail')['steps'] +
              HELP.for_url_name('habit_detail').get('tips', []))
ok('66 days at 80%' in hp and 'type 0, Save' in hp,
   'WORDING: established is 66 days at 80%; minutes untick is 0 and Save')
ok('six days before it' in qs['How do I fill in a day I forgot?']['a'],
   '  "today and the six days before it", not seven back')
ok('first guess' in qs['How does Wellness predict my next period?']['a'],
   '  a first period guess after one cycle')
ok(HELP.SCREENS['kit']['title'] == 'My equipment' and
   'never mentions your journal' in qs['Who can read my journal?']['a'],
   '  My equipment; the Monday email never mentions the journal')
ok('at least one ticked set' in
   qs['Can a habit tick itself when I train?']['a'],
   '  a workout ticks a habit only with a ticked set')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from wellness.models import WellnessProfile
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
            a = User.objects.create_user('w17_a', 'w17a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            t = ca.get('/wellness/guide/').content.decode()
            ok('Getting set up' in t and 'When something is not working' in t
               and 'Set up: reminders on a Samsung' in t and
               'Unrestricted' in t,
               'THE GUIDE PAGE shows topics and the Samsung set-up steps')
            t = ca.get('/wellness/settings/').content.decode()
            ok('Good to know' in t and 'Send me a test' in t and
               'w-sheet-topic' in t,
               'SETTINGS: its help has Good to know, and the topics')
            t = ca.get('/wellness/').content.decode()
            ok('Your sections switches whole' in t,
               'TODAY: its help has Good to know too')
            from django.utils import timezone
            today = timezone.localdate()
            hb = Habit.objects.create(user=a, name='Steady walk',
                                      kind='yes_no', schedule='daily',
                                      started_on=today - dt.timedelta(days=3))
            ca.post('/wellness/habits/%d/pause/' % hb.pk)
            hb.refresh_from_db()
            ok(hb.paused and hb.pauses == [[today.isoformat(), None]],
               'PAUSE (driven): the pause is kept from today')
            ca.post('/wellness/habits/%d/resume/' % hb.pk)
            hb.refresh_from_db()
            ok(not hb.paused and hb.pauses == [],
               '  resumed the same day: nothing left behind')
            ca.post('/wellness/habits/%d/establish/' % hb.pk)
            t = ca.get('/wellness/').content.decode()
            ok('Steady walk' not in t,
               'ESTABLISHED (driven): it leaves Today')
            ca.post('/wellness/habits/%d/unestablish/' % hb.pk)
            ok('Steady walk' in ca.get('/wellness/').content.decode(),
               '  "Bring back to Today" brings it back')
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
ok("Text = 'def grouped('" in gate, '  with a sentinel on the topics')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
