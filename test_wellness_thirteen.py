# -*- coding: utf-8 -*-
"""test_wellness_thirteen.py - round CY-3, 31 Oct 2026.

RELEASE 56 - WELLNESS: DEEPER CYCLE TRACKING. Decided 31 Oct 15:46: more
to log (mood, energy, sleep, cravings, discharge, your own tags), a PMS
window on the calendar months ahead, a pill reminder and a nudge to log -
discreet, like every cycle reminder. No fertility signs; no sharing.
And Demetri, 18:23: the reminder's icon in the phone's top bar was a blank
white block - it is now the Wellness tick, white on clear. 20:06: a
challenge can have your own number of days.
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

SUFFIX = '.bak_wellness13'
ME = 'test_wellness_thirteen.py'
PATCHER = 'apply_wellness_thirteen.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(WT, 'base.html'), J(WT, 'cycle.html'), J(WT, 'cycle_log.html'),
          J(WT, 'settings.html'),
          J(WT, 'cycle_settings.html'), J(APP, 'cycle.py'),
          J(APP, 'views_cycle.py'), J(APP, 'views.py'),
          J(APP, 'reminders.py'), J(APP, 'assets', 'wellness.css'),
          J(APP, 'guide.py'), J(APP, 'help.py')]

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
st = read(J(WT, 'cycle_settings.html'))
ok('name="track"' in st and 'name="tags"' in st and 'name="pill_at"' in st
   and 'name="nudge"' in st,
   'CYCLE SETTINGS: more to log, your own tags, the pill time, the nudge')
ok('Reminders arrive with a later update' not in st,
   '  and no stale "arrive with a later update" line')
sett = read(J(WT, 'settings.html'))
ok(sett.count("url 'wellness:cycle'") == 1 and
   'Open the cycle tracker' in sett,
   'THE CYCLE TRACKER ONCE (Demetri, 21:06): only in Your sections')
ok('Switched on: {{ on_names }}' in sett,
   '  and the heading says the list is what is switched on (21:07)')
lg = read(J(WT, 'cycle_log.html'))
for k in ('mood', 'energy', 'sleep', 'discharge'):
    ok("{%% if '%s' in track %%}" % k in lg and 'name="%s"' % k in lg,
       'Log today asks about %s only when it is switched on' % k)
ok('name="tag"' in lg, '  and your own tags')
cy = read(J(WT, 'cycle.html'))
ok('<i class="pms"></i>PMS days' in cy and 'data-pms-line' in cy,
   'the calendar shows PMS days, and says so')
views = read(J(APP, 'views.py'))
ok("'badge-96.png': 'image/png'" in views and
   "badge: '/wellness/app/badge-96.png'" in views,
   "THE REMINDER'S TOP-BAR ICON is the Wellness badge")
ok(os.path.isfile(J(APP, 'assets', 'badge-96.png')), '  and it is on disk')
try:
    from PIL import Image
    im = Image.open(J(APP, 'assets', 'badge-96.png'))
    px = list(im.convert('RGBA').getdata())
    ok(im.size == (96, 96) and
       all(p[3] == 0 or (p[0] > 200 and p[1] > 200 and p[2] > 200)
           for p in px) and any(p[3] == 0 for p in px) and
       any(p[3] > 200 for p in px),
       '  white on clear, 96 by 96 - as Android draws it')
except ImportError:
    skip('the badge pixels', 'Pillow is not installed here')
rm = read(J(APP, 'reminders.py'))
ok("'key': 'pill'" in rm and "'key': 'cycle_log'" in rm and
   rm.count("'body': CYCLE_WORDS") >= 3,
   'the pill reminder and the nudge say only "A Wellness reminder"')
base = read(J(WT, 'base.html'))
v = re.findall(r'\?v=([\w-]+)', base)
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl13-1)', v)
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
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
ok('name="track"' not in was(J(WT, 'cycle_settings.html')),
   'CONTROL: before this round there was nothing more to log')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from wellness import cycle as C                             # noqa: E402
from django.http import QueryDict                           # noqa: E402
ok(C.clean_tags('coffee, Travel ,coffee,, late night') ==
   ['coffee', 'Travel', 'late night'], 'your own tags: tidy, no repeats')
ok(len(C.clean_tags(','.join('t%d' % i for i in range(30)))) == C.MAX_TAGS,
   '  at most %d' % C.MAX_TAGS)
q = QueryDict('', mutable=True)
q.update({'mood': 'low', 'energy': 'high', 'sleep': 'poor',
          'discharge': 'creamy'})
q.setlist('tag', ['coffee', 'stranger'])
e = C.clean_day(q, tags=['coffee'])
ok(e == {'mood': 'low', 'energy': 'high', 'sleep': 'poor',
         'discharge': 'creamy', 'tags': ['coffee']},
   'a day keeps mood, energy, sleep, discharge and only YOUR tags', e)
ok(C.clean_day(QueryDict('mood=furious')) == {},
   '  an answer that is not offered is dropped')
ok(C.has({'mood': 'very_low'}, 'low_mood') and
   C.has({'sleep': 'poor'}, 'poor_sleep') and
   C.has({'energy': 'low'}, 'low_energy') and
   C.has({'tags': ['coffee']}, 'tag:coffee') and not C.has({}, 'cramps'),
   'a low mood, poor sleep or low energy counts however it was logged')
D = dt.date
days = {}
starts = [D(2026, 7, 1), D(2026, 7, 29), D(2026, 8, 26), D(2026, 9, 23)]
for a in starts:
    for i in range(5):
        days[(a + dt.timedelta(days=i)).isoformat()] = {'flow': 'medium'}
for a in starts[1:]:
    for back in (1, 2, 3):
        days[(a - dt.timedelta(days=back)).isoformat()] = {
            'sym': ['bloating'], 'tags': ['coffee']}
cs = C.cycles(C.periods(days))
ok(C.pms(days, cs) == 3,
   'PMS DAYS: symptoms three days before most periods - 3', C.pms(days, cs))
rows, words = C.around(days, cs, tags=['coffee'])
ok(any(r[0] == 'coffee' for r in rows),
   'Patterns shows your own tags against the cycle')
s = C.summary(days, D(2026, 10, 5), dict(C.DEFAULT_SETTINGS))
wins = C.future_windows(s)
ok(len(wins) >= 6 and (wins[1][0] - wins[0][0]).days == s['avg_cycle'],
   'MONTHS AHEAD: a window each cycle, six months on')
grid = C.month_grid(2026, 10, days, s, D(2026, 10, 5), wins, 3)
kinds = [c['kind'] for w in grid for c in w if c['in']]
ok('pms' in kinds and 'expected' in kinds,
   '  the calendar marks the PMS days before the expected ones')
ok(C.pms(days, cs[:2]) is None, 'fewer than three periods: no PMS days')
from wellness import challenge as CH                        # noqa: E402
ok(CH.valid_days(45) and CH.valid_days(365) and not CH.valid_days(1) and
   not CH.valid_days(366),
   'OWN NUMBER OF DAYS (Demetri, 20:06): any from 2 to 365')
ok([len(r) for r in CH.rows(['todo'] * 45)] == [15, 15, 15] and
   CH.rows(['todo'] * 100) == [],
   '  45 days in rows of fifteen; past 90 a bar instead of squares')
from wellness import help as HELP                           # noqa: E402
ok('A Wellness reminder' in ' '.join(HELP.SCREENS['cycle_settings']['steps'])
   and any('PMS' in w for _s, w in HELP.SCREENS['cycle']['signs']),
   'the help explains the reminders, more to log and the PMS days')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile, PushDevice
    from wellness import reminders as RM
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
            a = User.objects.create_user('w13_a', 'w13a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            prefs = dict(C.DEFAULT_SETTINGS)
            prefs['on'] = True
            C.save(a, prefs, {})
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            ca.post('/wellness/cycle/settings/', {
                'mode': 'normal', 'track': ['mood', 'sleep', 'tags', 'x'],
                'tags': 'coffee, travel', 'pill_at': '21:30',
                'nudge': '1'})
            _r, p2, _d = C.load(a)
            ok(list(p2['track']) == ['mood', 'sleep', 'tags'] and
               list(p2['tags']) == ['coffee', 'travel'] and
               p2['pill_at'] == '21:30' and p2['nudge'],
               'SETTINGS SAVED: mood, sleep, tags; a 21:30 pill; the nudge')
            t = ca.get('/wellness/cycle/log/').content.decode()
            ok('name="mood"' in t and 'name="sleep"' in t and
               'name="energy"' not in t and 'value="coffee"' in t,
               'LOG TODAY asks only what was switched on')
            ca.post('/wellness/cycle/log/', {'mood': 'good', 'sleep': 'okay',
                                             'tag': ['travel']})
            _r, _p, d2 = C.load(a)
            today = timezone.localdate()
            ok(d2[today.isoformat()] == {'mood': 'good', 'sleep': 'okay',
                                         'tags': ['travel']},
               '  kept, locked like the rest', d2.get(today.isoformat()))
            now = timezone.make_aware(dt.datetime.combine(
                today, dt.time(21, 40)))
            items = [i for i in RM.items_for(a, now) if i['key'] == 'pill']
            ok(items and items[0]['body'] == 'A Wellness reminder',
               'THE PILL REMINDER at 21:30, saying only "A Wellness '
               'reminder"')
            ca.post('/wellness/settings/', {'form': 'sections',
                                            'module': ['habits']})
            ok(not [i for i in RM.items_for(a, now) if i['key'] == 'pill'],
               '  and none once the cycle tracker is switched off')
            from wellness.models import Habit
            ca.post('/wellness/settings/', {'form': 'sections', 'module': [
                'habits', 'journal', 'calm', 'workouts', 'body']})
            r = ca.post('/wellness/habits/new/', {
                'name': 'Walk', 'kind': 'yes_no', 'schedule': 'daily',
                'time_of_day': 'anytime', 'challenge': 'own',
                'challenge_own': '45'})
            hw = Habit.objects.get(user=a, name='Walk')
            ok(hw.challenge_days == 45 and
               'Day 1 of 45' in ca.get('/wellness/').content.decode(),
               'A 45-DAY CHALLENGE of your own: "Day 1 of 45"')
            t = ca.get('/wellness/habits/%d/edit/' % hw.pk).content.decode()
            ok('value="own" checked' in t and 'value="45"' in t,
               '  editing it shows Own, with 45')
            ca.post('/wellness/habits/new/', {
                'name': 'Swim', 'kind': 'yes_no', 'schedule': 'daily',
                'time_of_day': 'anytime', 'challenge': 'own',
                'challenge_own': '900'})
            ok(Habit.objects.get(user=a, name='Swim').challenge_days is None,
               '  900 days is not a challenge')
            r = ca.get('/wellness/app/badge-96.png')
            ok(r.status_code == 200 and r['Content-Type'] == 'image/png',
               'the badge is served')
            sw = ca.get('/wellness/app/sw.js').content.decode()
            ok("badge: '/wellness/app/badge-96.png'" in sw,
               '  and the app worker uses it for every reminder')
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
ok("Text = 'def _hm_ok('" in gate, '  with a sentinel on the settings')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
