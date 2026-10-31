# -*- coding: utf-8 -*-
"""test_wellness_twelve.py - round CY-2, 31 Oct 2026.

RELEASE 55 - WELLNESS: CYCLE PHASES. Demetri, 31 Oct 15:41, sharing the
Lively app: a phase card, "My period ended", a board of things to do, move
and eat. 15:46: "Do, Move and Eat"; no fertility signs.

    - The phase card: the day of the cycle and its phase on a soft wave,
      Today or Tomorrow. Day only for very irregular cycles, pregnancy or
      hormonal contraception.
    - One tap: "My period started", "My period ended" (or yesterday) -
      the days between filled in.
    - Do - Move - Eat: ideas with why and how, each can be hidden. Ideas,
      not rules: nothing medical, no targets.
    - Long-press shortcuts on the app icon (no widgets on Android), with
      nothing about the cycle in them.
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

SUFFIX = '.bak_wellness12'
ME = 'test_wellness_twelve.py'
PATCHER = 'apply_wellness_twelve.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(WT, 'base.html'), J(WT, 'cycle.html'), J(APP, 'cycle.py'),
          J(APP, 'views_cycle.py'), J(APP, 'views.py'), J(APP, 'urls.py'),
          J(APP, 'assets', 'wellness.css'), J(APP, 'guide.py'),
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
ok(os.path.isfile(J(APP, 'phases.py')), 'wellness/phases.py is there')
cy = read(J(WT, 'cycle.html'))
ok('data-phase-card' in cy and 'class="w-wave"' in cy and
   '?when=tomorrow' in cy, 'the phase card, its wave, Today and Tomorrow')
ok('My period started' in cy and 'My period ended' in cy and
   'It ended yesterday' in cy, 'one tap: started, ended, ended yesterday')
ok('data-board' in cy and 'Hide this idea' in cy and 'Ideas, not rules' in cy,
   'the Do - Move - Eat board, each idea can be hidden')
views = read(J(APP, 'views.py'))
ok("'shortcuts': [" in views, 'long-press shortcuts on the app icon')
base = read(J(WT, 'base.html'))
v = re.findall(r'\?v=([\w-]+)', base)
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl12-1)', v)
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
ok('data-phase-card' not in was(J(WT, 'cycle.html')),
   'CONTROL: before this round there was no phase card')

# ==========================================================================
head('2. THE PHASES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
import json                                                 # noqa: E402
from wellness import phases as PH                           # noqa: E402
got = [PH.phase_on(n, 28, 5) for n in range(1, 29)]
ok(got[:5] == ['menstrual'] * 5 and got[5:12] == ['follicular'] * 7 and
   got[12:15] == ['ovulation'] * 3 and got[15:] == ['luteal'] * 13,
   'A 28-DAY CYCLE: menstrual 1-5, follicular 6-12, ovulation 13-15, '
   'luteal 16-28 (ovulation about 14 days before the next)')
ok(PH.phase_on(19, 35, 5) == 'follicular' and
   PH.phase_on(21, 35, 5) == 'ovulation',
   '  a 35-day cycle ovulates later')
base_s = {'cycle_day': 12, 'avg_cycle': 28, 'avg_period': 5,
          'range': (27, 29), 'state': 'predicted'}
c = PH.place(base_s, 'today')
ok(c['day'] == 12 and c['phase'] == 'follicular' and c['title'] and
   c['line'] and 0 < c['frac'] < 1, 'day 12: follicular, with a line')
ok(PH.place(base_s, 'tomorrow')['day'] == 13 and
   PH.place(base_s, 'tomorrow')['phase'] == 'ovulation',
   'TOMORROW: day 13, ovulation')
irr = dict(base_s, range=(24, 38))
ok(PH.place(irr, 'today')['phase'] is None and
   'vary' in PH.place(irr, 'today')['why_none'],
   'VERY IRREGULAR: the day only, and why')
for mode in ('pregnant', 'hormonal'):
    ok(PH.place(dict(base_s, state=mode), 'today')['phase'] is None,
       '%s: no phase' % mode)
ok(PH.place(dict(base_s, avg_cycle=None, cycle_day=3), 'today')['estimated'],
   'before a cycle is complete: an estimate, and it says so')
ok(PH.place(dict(base_s, cycle_day=31), 'today')['late'],
   'past the usual length: "may be on its way"')
ok(PH.place({'cycle_day': None}, 'today') is None, 'no log: no card')
counts = {p: {g: len(PH.BOARD[p][g]) for g in ('do', 'move', 'eat')}
          for p in PH.BOARD}
ok(all(n >= 3 for p in counts.values() for n in p.values()),
   'DO, MOVE, EAT: at least three ideas each, every phase', counts)
words = ' '.join(' '.join(i[1:4]) for p in PH.BOARD.values()
                 for g in p.values() for i in g).lower()
words += ' '.join(t + ' ' + l for v in PH.LINES.values()
                  for t, l in v).lower()
bad = [w for w in ('calorie', 'kcal', 'grams', 'diet', 'lose weight',
                   'must', 'should', 'cure', 'treat', 'medication', '!')
       if w in words]
ok(not bad, 'IDEAS, NOT RULES: no calories, diets, musts or cures', bad)
ok(len(PH.ALL_KEYS) == sum(len(g) for p in PH.BOARD.values()
                           for g in p.values()), 'every idea has its own key')
prefs, days = {}, {}
T = dt.date(2026, 10, 31)
PH.start(prefs, days, T - dt.timedelta(days=3))
ok(prefs['open_period'] == '2026-10-28' and
   days['2026-10-28']['flow'] == 'medium',
   'MY PERIOD STARTED: day one logged, and it stays open')
days['2026-10-29'] = {'flow': 'heavy', 'sym': ['cramps']}
PH.end(prefs, days, T)
ok('open_period' not in prefs and
   [days[(T - dt.timedelta(days=k)).isoformat()]['flow']
    for k in (3, 2, 1, 0)] == ['medium', 'heavy', 'medium', 'medium'] and
   days['2026-10-29']['sym'] == ['cramps'],
   'MY PERIOD ENDED: the days between filled in, what was logged kept')
p2, d2 = {}, {}
PH.start(p2, d2, T - dt.timedelta(days=9))
ok(PH.tidy(p2, d2, T, 5) and 'open_period' not in p2 and
   len(d2) == 5, 'left open: it closes itself at its usual length')
from wellness import help as HELP                           # noqa: E402
ok('My period started' in ' '.join(HELP.SCREENS['cycle']['steps']),
   "the cycle page's help explains the card, the buttons and the ideas")

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile
    from wellness import cycle as C
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
            a = User.objects.create_user('w12_a', 'w12a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            today = timezone.localdate()
            prefs = dict(C.DEFAULT_SETTINGS)
            prefs['on'] = True
            days = {}
            for back in (95, 67, 39, 11):
                st = today - dt.timedelta(days=back)
                for i in range(5):
                    days[(st + dt.timedelta(days=i)).isoformat()] = {
                        'flow': 'medium'}
            C.save(a, prefs, days)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            t = ca.get('/wellness/cycle/').content.decode()
            ok('data-phase-card' in t and 'Day 12 of your cycle' in t and
               'Follicular phase' in t,
               'THE CARD: "Day 12 of your cycle - Follicular phase"')
            ok('My period started' in t and 'data-board' in t and
               'Plan the month' in t, '  the start button and the ideas')
            t2 = ca.get('/wellness/cycle/?when=tomorrow').content.decode()
            ok('Tomorrow is day 13' in t2 and 'Ovulation phase' in t2,
               'TOMORROW: day 13, ovulation')
            ca.post('/wellness/cycle/quick/', {'do': 'hide',
                                               'tip': 'f_plan'})
            t = ca.get('/wellness/cycle/').content.decode()
            ok('Plan the month' not in t and 'Show the 1 idea you hid' in t,
               'HIDE AN IDEA: gone, with a way to bring it back')
            ca.post('/wellness/cycle/quick/', {'do': 'unhide'})
            ok('Plan the month' in ca.get('/wellness/cycle/').content
               .decode(), '  and back')
            ca.post('/wellness/cycle/quick/', {'do': 'start'})
            t = ca.get('/wellness/cycle/').content.decode()
            ok('Day 1 of your cycle' in t and 'Menstrual phase' in t and
               'My period ended' in t,
               'ONE TAP, STARTED: day 1, menstrual, "My period ended"')
            ca.post('/wellness/cycle/quick/', {'do': 'end'})
            _r, p3, d3 = C.load(a)
            ok(not p3.get('open_period') and
               d3[today.isoformat()]['flow'] == 'medium',
               'ONE TAP, ENDED: nothing left open')
            t = ca.get('/wellness/').content.decode()
            ok('phase' not in t.lower().split('data-cycle-card')[-1]
               [:400], "Today's cycle line stays as discreet as before")
            m = json.loads(ca.get('/wellness/app/manifest.webmanifest')
                           .content.decode())
            names = ' '.join(s['name'] + s['url'] for s in
                             m.get('shortcuts', [])).lower()
            ok('breathe' in names and 'cycle' not in names and
               'period' not in names,
               'SHORTCUTS: Breathe, check-in, weigh-in - nothing about the '
               'cycle')
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
ok("Text = 'def place('" in gate, '  with a sentinel on the phases')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
