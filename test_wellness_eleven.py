# -*- coding: utf-8 -*-
"""test_wellness_eleven.py - round WL-9, 31 Oct 2026.

RELEASE 54 - WELLNESS: YOUR SECTIONS. Demetri, 31 Oct 17:05: "On the
Settings page, every user must be able to expand a modules section and
must then be allowed to activate/deactivate any of the six modules.
Habits, Journal, Workouts, Body, Cycle tracker and Calm. They should then
only have the relevant section show on the Today page and in the bottom
module-selector bar."

    - Settings > Your sections: six switches. Today always stays.
    - Off: gone from Today and the bottom bar, its reminders stop, Claude's
      line and the Monday email leave it out, and its pages send the
      person to Settings. NOTHING IS DELETED.
    - The cycle tracker keeps its own switch and its welcome page.
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

SUFFIX = '.bak_wellness11'
ME = 'test_wellness_eleven.py'
PATCHER = 'apply_wellness_eleven.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(WT, 'base.html'), J(WT, 'today.html'), J(WT, 'settings.html'),
          J(APP, 'views.py'), J(APP, 'reminders.py'), J(APP, 'daily_line.py'),
          J(APP, 'weekly.py'), J(APP, 'guide.py'), J(APP, 'help.py')]

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
ok(os.path.isfile(J(APP, 'modules.py')) and
   os.path.isfile(J(APP, 'templatetags', 'wellness_modules.py')),
   'wellness/modules.py and its template tag are there')
st = read(J(WT, 'settings.html'))
ok('<details class="w-card" id="sections"' in st and 'name="module"' in st
   and 'Your sections' in st,
   'SETTINGS: "Your sections" opens out to the switches')
ok('Nothing is deleted' in st, '  and says that nothing is deleted')
base = read(J(WT, 'base.html'))
for k in ('habits', 'journal', 'calm', 'workouts', 'body', 'cycle'):
    ok("{%% if '%s' in mods %%}" % k in base,
       'the bottom bar shows %s only when it is on' % k)
ok(base.index("{% modules_on as mods %}") < base.index("wellness:today' %}\"")
   or "{% modules_on as mods %}" in base, '  (one look per page)')
today_t = read(J(WT, 'today.html'))
for k in ('habits', 'journal', 'calm', 'workouts', 'body'):
    ok("{%% if '%s' in mods %%}" % k in today_t,
       'Today shows %s only when it is on' % k)
ok('data-no-sections' in today_t,
   '  and, with everything off, a gentle way back to Your sections')
views = read(J(APP, 'views.py'))
ok('MOD.section_of(request.path)' in views and 'def wellness_view(fn):'
   in views, "a switched-off section's pages go to Settings")
for f in ('reminders.py', 'daily_line.py', 'weekly.py'):
    ok("'habits' not in mods" in read(J(APP, f)),
       '%s leaves out a switched-off section' % f)
v = re.findall(r'\?v=([\w-]+)', base)
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl11-1)', v)
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
ok('name="module"' not in was(J(WT, 'settings.html')),
   'CONTROL: before this round there were no section switches')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import modules as MOD                         # noqa: E402
ok([m[0] for m in MOD.MODULES] == ['habits', 'journal', 'calm', 'workouts',
                                   'body', 'cycle'],
   'six sections, in the bottom bar\'s order')
ok(MOD.section_of('/wellness/habits/3/') == 'habits' and
   MOD.section_of('/wellness/calm/guided/reset/') == 'calm' and
   MOD.section_of('/wellness/') is None and
   MOD.section_of('/wellness/settings/') is None and
   MOD.section_of('/wellness/cycle/') is None,
   'each address knows its section; Today, Settings and Cycle stay open')
ok(MOD.off_from_prefs({'modules_off': ['body', 'cycle', 'x']}) == {'body'},
   'only the five switchable here are kept off (cycle has its own)')
ok(MOD.off_from_prefs({}) == set(), 'everything on to begin with')
from wellness import help as HELP                           # noqa: E402
ok('Your sections' in ' '.join(HELP.SCREENS['settings']['steps']),
   "Settings' help explains Your sections")

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import Habit, WellnessProfile
    from wellness import cycle as CY
    from wellness import reminders as RM
    import datetime as dt
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
            a = User.objects.create_user('w11_a', 'w11a@example.com', 'x')
            b = User.objects.create_user('w11_b', 'w11b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            day = timezone.localdate()
            h = Habit.objects.create(user=a, name='Walk the dog',
                                     started_on=day,
                                     remind_at=dt.time(9, 0))
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            t = ca.get('/wellness/').content.decode()
            ok('Walk the dog' in t and 'href="/wellness/habits/"' in t and
               'data-calm-card' in t and 'href="/wellness/body/"' in t,
               'TO BEGIN WITH everything is on, as before')
            t = ca.get('/wellness/settings/').content.decode()
            ok('id="sections"' in t and t.count('name="module"') == 6,
               'Settings has the six switches')
            r = ca.post('/wellness/settings/', {
                'form': 'sections',
                'module': ['journal', 'workouts', 'calm']})
            ok(r.status_code == 302 and 's=1' in r['Location'],
               'saved')
            pa = WellnessProfile.objects.get(user=a)
            ok(sorted(pa.prefs.get('modules_off')) == ['body', 'habits'],
               '  Habits and Body are off')
            t = ca.get('/wellness/').content.decode()
            ok('Walk the dog' not in t and
               'href="/wellness/habits/"' not in t,
               'HABITS OFF: gone from Today and from the bottom bar')
            ok('href="/wellness/body/"' not in t and
               'href="/wellness/body/weigh/"' not in t,
               'BODY OFF: no weigh-in card, no Body tab')
            ok('data-calm-card' in t and 'href="/wellness/journal/"' in t,
               '  Calm and Journal still there')
            r = ca.get('/wellness/habits/%d/' % h.pk)
            ok(r.status_code == 302 and 'off=habits' in r['Location'],
               "a switched-off section's page goes to Settings")
            t = ca.get(r['Location']).content.decode()
            ok('Habits is switched off' in t and 'data-sections open' in t,
               '  which says so, with Your sections open')
            ok(Habit.objects.filter(pk=h.pk).exists(),
               'NOTHING DELETED: the habit is kept')
            now = timezone.make_aware(dt.datetime.combine(
                day, dt.time(9, 30)))
            ok(not [i for i in RM.items_for(a, now)
                    if i['key'].startswith('habit:')],
               'and its reminder is not sent')
            ca.post('/wellness/settings/', {
                'form': 'sections',
                'module': ['habits', 'journal', 'workouts', 'calm',
                           'body']})
            ok([i for i in RM.items_for(a, now)
                if i['key'].startswith('habit:')] and
               'Walk the dog' in ca.get('/wellness/').content.decode(),
               'BACK ON: the habit and its reminder return')
            r = ca.post('/wellness/settings/', {
                'form': 'sections',
                'module': ['habits', 'journal', 'workouts', 'calm', 'body',
                           'cycle']})
            ok(r['Location'].endswith('/wellness/cycle/') and
               not CY.is_on(a),
               'CYCLE ON goes to its welcome page first - not on yet')
            ca.post('/wellness/cycle/settings/', {'turn': 'on'})
            t = ca.get('/wellness/').content.decode()
            ok(CY.is_on(a) and 'href="/wellness/cycle/"' in t,
               '  turned on there: in the bottom bar')
            ca.post('/wellness/settings/', {
                'form': 'sections',
                'module': ['habits', 'journal', 'workouts', 'calm',
                           'body']})
            ok(not CY.is_on(a) and 'href="/wellness/cycle/"' not in
               ca.get('/wellness/').content.decode(),
               'CYCLE OFF from Settings: off, and out of the bar')
            ca.post('/wellness/settings/', {'form': 'sections'})
            t = ca.get('/wellness/').content.decode()
            ok('data-no-sections' in t and 'Good ' in t,
               'EVERYTHING OFF: Today still opens, with a way back')
            cb = Client(SERVER_NAME='localhost')
            cb.force_login(b)
            ok('href="/wellness/habits/"' in cb.get('/wellness/').content
               .decode(), "another member's sections are their own")
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
ok("Text = 'def section_of('" in gate, '  with a sentinel on the switches')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
