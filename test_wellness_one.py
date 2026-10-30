# -*- coding: utf-8 -*-
"""test_wellness_one.py - round WL-1, 30 Oct 2026.

RELEASE 42 - WELLNESS, PART ONE: TODAY AND HABITS. His decisions of 29
and 30 October:

    - A fourth tile on Personal, "Wellness", behind its own permission.
    - Its own Django app, OUTSIDE the house standard: calm, minimal, phone
      first. The house suites do not walk it; this suite is what holds it.
    - Everyone sees only their own data - no exceptions, superusers too.
      Every member logs in themselves.
    - An installable app (manifest + service worker) from day one.
    - Habits that forgive: weeks not days, two grace days a month,
      comebacks marked, "established" at 66 days and 80%.
    - Help inside the screens: welcome cards and a starter set, a guided
      four-step habit setup, one-time tips, and the ? guide.
    - The quote of the day from a curated library of real, sourced quotes.
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
import types

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_wellness1'
ME = 'test_wellness_one.py'
PATCHER = 'apply_wellness_one.py'
PS1 = 'Push-PendingChanges.ps1'

J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
TPL = J(ROOT, 'pages', 'templates')
EDITED = [J(ROOT, 'mysite', 'settings.py'), J(ROOT, 'mysite', 'urls.py'),
          J(ROOT, 'pages', 'permissions.py'), J(ROOT, 'pages', 'middleware.py'),
          J(ROOT, 'pages', 'views', 'administration.py'),
          J(ROOT, 'pages', 'views', 'home.py'), J(TPL, 'base.html'),
          J(TPL, 'personal.html')]
APP_FILES = ['__init__.py', 'apps.py', 'models.py', 'habits.py', 'quotes.py',
             'guide.py', 'views.py', 'urls.py', 'session.py',
             J('migrations', '__init__.py'), J('migrations', '0001_initial.py'),
             J('assets', 'wellness.css'), J('assets', 'wellness.js'),
             J('assets', 'icon-192.png'), J('assets', 'icon-512.png'),
             J('assets', 'icon-maskable-512.png'),
             J('assets', 'apple-touch-icon.png')]
TEMPLATES = ['base.html', 'today.html', 'welcome.html', 'habit_list.html',
             'habit_detail.html', 'habit_form.html', 'guide.html']

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
code_only = T.code_only

# ==========================================================================
head('1. ITS OWN APP, OUTSIDE THE HOUSE')
# ==========================================================================
missing = [f for f in APP_FILES if not os.path.isfile(J(APP, f))]
ok(not missing, 'the wellness app is all there (%d files)' % len(APP_FILES),
   ', '.join(missing))
missing = [f for f in TEMPLATES if not os.path.isfile(J(WT, f))]
ok(not missing, '  and its %d templates' % len(TEMPLATES), ', '.join(missing))
settings = read(J(ROOT, 'mysite', 'settings.py'))
ok(re.search(r'INSTALLED_APPS\s*=\s*\[[^\]]*"wellness"', settings, re.S),
   'wellness is an installed app')
ok('path("wellness/", include("wellness.urls"))'
   in read(J(ROOT, 'mysite', 'urls.py')), '  mounted at /wellness/')
ok(all(parts != ('wellness', 'templates') for parts, _ in T.TEMPLATE_ROOTS),
   'its templates are NOT a house template root - by decision, the house '
   'suites never walk it')
ok(not any(os.sep + 'wellness' + os.sep in p for p in T.templates()),
   '  and alv_tree.templates() does not list one of them')
base = read(J(WT, 'base.html'))
ok('{% extends' not in code_only(base), 'its base page stands alone - it '
   'does not extend the house base.html')
bad = [f for f in TEMPLATES[1:]
       if '{% extends "wellness/base.html" %}' not in read(J(WT, f))]
ok(not bad, '  and every other page extends it', ', '.join(bad))
ok('width=device-width' in base and 'viewport-fit=cover' in base,
   'phone first: the viewport fits the screen, notch included')
ok('wellness:manifest' in base and 'apple-touch-icon' in base,
   'the installable app: a manifest link and a home-screen icon')
css = read(J(APP, 'assets', 'wellness.css'))
ok('prefers-color-scheme: dark' in css,
   'dark mode follows the phone (for the evening)')
ok('prefers-reduced-motion' in css, 'motion is off for anyone who asked '
   'their phone for less')
reds = re.findall(r'#(?:dc3545|ff0000|e74c3c|d9534f|c0392b)\b', css, re.I)
ok(not reds, 'no red anywhere - a miss is simply empty', reds)
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css)
         if int(m) < 44]
ok(not small, 'every control is at least 44px tall', small)
js = read(J(APP, 'assets', 'wellness.js'))
ok("register('/wellness/app/sw.js', {scope: '/wellness/'})" in js,
   'the service worker is registered for the whole of /wellness/')

# ==========================================================================
head('2. WIRED IN')
# ==========================================================================
import importlib                                            # noqa: E402
perms_src = read(J(ROOT, 'pages', 'permissions.py'))
ok("'codename': 'can_access_wellness',       'edit_codename': None" in
   perms_src, 'can_access_wellness is a module permission, with no edit '
   'tier - your own data is yours to change')
mw = read(J(ROOT, 'pages', 'middleware.py'))
ok("('wellness', 'auth.can_access_wellness')" in mw,
   'the middleware asks for it on every /wellness/ page')
ok('"wellness.session.WellnessSessionMiddleware"' in settings
   and settings.index('wellness.session.WellnessSessionMiddleware')
   < settings.index('pages.middleware.ModuleAccessMiddleware')
   and settings.index('AuthenticationMiddleware')
   < settings.index('wellness.session.WellnessSessionMiddleware'),
   'the session rule sits after login and before the permission check')
ok("'wellness/app/'," in mw, '  except the app shell, which a phone '
   'fetches with no session')
ok("('wellness/', 'auth.can_access_wellness')" not in mw,
   'CONTROL: not with a trailing slash, which never matches - the path '
   'is compared with its slash stripped')
per = code_only(read(J(TPL, 'personal.html')))
ok("{% if perms_map.wellness %}" in per
   and "{% url 'wellness:today' %}" in per,
   'Personal has the fourth tile, behind the permission')
ok(per.count('class="admin-btn btn-personal"') == 5,
   '  four tiles on the Personal tab, CRS on Compliance', per.count(
       'class="admin-btn btn-personal"'))
ok("'wellness':     request.user.has_perm('auth.can_access_wellness')" in
   read(J(ROOT, 'pages', 'views', 'administration.py')),
   '  and the view tells it')
home = read(J(ROOT, 'pages', 'views', 'home.py'))
ok("or request.user.has_perm('auth.can_access_wellness')" in home,
   'a login with only Wellness still gets the way to Personal on Home')
bh = read(J(TPL, 'base.html'))
ok(bh.count('or perms.auth.can_access_wellness %}') == 2,
   '  and in both navigation menus', bh.count(
       'or perms.auth.can_access_wellness %}'))
mig = read(J(APP, 'migrations', '0001_initial.py'))
ok(all(re.search(r'''name=["']%s["']''' % n, mig)
        for n in ('Habit', 'HabitLog', 'WellnessProfile')),
   'migration 0001 makes the three tables')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('wellness' not in was(J(TPL, 'personal.html')),
   'CONTROL: before this round Personal had no Wellness tile')

# ==========================================================================
head('3. THE RULES OF A KIND TRACKER (no database)')
# ==========================================================================
from wellness import habits as H                            # noqa: E402


def fake(schedule='daily', start=dt.date(2026, 9, 1), weekdays='',
         per_week=None, paused=False, **kw):
    h = types.SimpleNamespace(schedule=schedule, started_on=start,
                              weekdays=weekdays, per_week=per_week,
                              paused=paused, archived_at=None,
                              established_at=None, kind='yes_no',
                              target=None, unit='', **kw)
    h.weekday_set = lambda: {int(c) for c in h.weekdays}
    return h


D = dt.date
h = fake()
today = D(2026, 9, 30)
allsept = {D(2026, 9, d) for d in range(1, 31)}
miss3 = allsept - {D(2026, 9, 10), D(2026, 9, 11), D(2026, 9, 12)}
st = H.day_states(h, miss3, today)
ok(st[D(2026, 9, 10)] == 'grace' and st[D(2026, 9, 11)] == 'grace',
   'the first two misses in a month are forgiven')
ok(st[D(2026, 9, 12)] == 'miss', '  the third is a miss - and only a miss')
ok(H.day_states(h, set(), today)[today] == 'open',
   'today is never a miss: it is open until it is over')
miss4 = miss3 - {D(2026, 9, 13)}
ok(D(2026, 9, 14) in H.comebacks(h, miss4, today),
   'a done day after a real break (two unforgiven misses) is a comeback')
ok(D(2026, 9, 13) not in H.comebacks(h, miss3, today),
   'CONTROL: after two forgiven days and one miss, it is not')
one_miss = allsept - {D(2026, 9, 10), D(2026, 9, 11), D(2026, 9, 12),
                      D(2026, 9, 20)}
ok(D(2026, 9, 21) not in H.comebacks(h, one_miss, today),
   'CONTROL: one unforgiven miss is not a break, so no comeback')
ok(H.consistency(h, allsept - {today}, today) == 1.0,
   'a full month with today still open is 100%, not 29/30')
c = H.consistency(h, miss3, today)
ok(c is not None and abs(c - 29 / 30.0) < 1e-9,
   'two forgiven and one missed is 29 of 30', c)
# Weeks: 7-13 Sep has the miss on the 12th; everything else whole.
ok(H.week_met(h, miss3, D(2026, 9, 7), today) is False,
   'a week with a miss is not met')
ok(H.week_met(h, miss3, D(2026, 9, 14), today) is True,
   '  the next one is')
ok(H.week_streak(h, miss3, today) == 2,
   'the streak counts weeks: 14-20 and 21-27 Sep, then the miss stops it',
   H.week_streak(h, miss3, today))
ok(H.week_streak(h, allsept - {today}, today) == 4,
   'this week, not yet met, does not break a streak',
   H.week_streak(h, allsept - {today}, today))
f = fake(schedule='per_week', per_week=3)
wk = {D(2026, 9, 21), D(2026, 9, 23), D(2026, 9, 25)}
ok(H.week_met(f, wk, D(2026, 9, 21), today) is True,
   'times a week: three in the week meets three a week')
ok(H.week_met(f, wk - {D(2026, 9, 25)}, D(2026, 9, 21), today) is False,
   '  two does not')
ok(all(s != 'miss' for s in H.day_states(f, wk, today).values()),
   '  and a times-a-week habit never has a missed DAY')
ok(H.this_week(f, {D(2026, 9, 28)}, today) == (1, 3), "'1 of 3 this week'")
ok(H.due_today(f, {D(2026, 9, 28), D(2026, 9, 29), D(2026, 9, 30)},
               today),
   'Today still lists a times-a-week habit already ticked today')
done3 = {D(2026, 9, 28), D(2026, 9, 29)}
f3 = fake(schedule='per_week', per_week=2)
ok(not H.due_today(f3, done3, today),
   'a times-a-week habit whose week is met leaves Today until next week')
wd = fake(schedule='weekdays', weekdays='024')
ok(H.scheduled(wd, D(2026, 9, 28)) and not H.scheduled(wd, D(2026, 9, 29)),
   'chosen days: Monday yes, Tuesday no')
ok(H.day_states(wd, set(), today)[D(2026, 9, 29)] == 'rest',
   '  and a day off is rest, not a miss')
paused = fake(paused=True)
ok(not H.due_today(paused, set(), today), 'a paused habit is off Today')
old = fake(start=D(2026, 7, 1))
long_done = {D(2026, 7, 1) + dt.timedelta(d) for d in range(92)}
ok(H.can_establish(old, long_done, today),
   '66 days at 80% or better: offered "established"')
ok(not H.can_establish(fake(start=D(2026, 8, 1)),
                       {D(2026, 8, 1) + dt.timedelta(d) for d in range(61)},
                       today),
   'CONTROL: not before day 66, however good the record')
thin = {d for d in long_done if d.day % 3}
ok(not H.can_establish(old, thin, today),
   'CONTROL: not below 80%')
cal = H.calendar(h, miss3, today)
ok(len(cal) == 12 and all(len(c) == 7 for c in cal),
   'the calendar is 12 weeks of 7 days')
ok(cal[-1][2]['date'] == today and cal[-1][3]['state'] == 'future',
   '  ending this week, the days after today marked future')

# ==========================================================================
head('4. THE QUOTES ARE REAL')
# ==========================================================================
from wellness import quotes as Q                            # noqa: E402
ok(len(Q.QUOTES) >= 25, 'a library of %d quotes' % len(Q.QUOTES))
ok(all(q['text'] and q['author'] for q in Q.QUOTES),
   'every one says whose it is')
texts = ' '.join(q['text'] for q in Q.QUOTES).lower()
ok('best time to plant a tree' not in texts
   and 'be the change' not in texts,
   'the famous misattributions are left out, not "fixed"')
dur = [q for q in Q.QUOTES if 'repeatedly do' in q['text']]
ok(dur and dur[0]['author'] == 'Will Durant',
   '"We are what we repeatedly do" is Will Durant, not Aristotle')
q1 = Q.for_day(1, D(2026, 10, 30))
ok(q1 == Q.for_day(1, D(2026, 10, 30)), "today's quote holds all day")
ok(len({Q.for_day(1, D(2026, 10, d))['text'] for d in range(1, 31)}) > 10,
   '  and changes from day to day')

# ==========================================================================
head('5. DRIVEN')
# ==========================================================================
have_db = False
try:
    import django
    django.setup()
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import Habit, HabitLog, WellnessProfile
    connection.ensure_connection()
    Habit.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 5', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])


class Rollback(Exception):
    pass


if have_db:
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            a = User.objects.create_user('wl1_a', 'a@example.com', 'x',
                                         first_name='Demetri')
            b = User.objects.create_user('wl1_b', 'b@example.com', 'x')
            su = User.objects.create_superuser('wl1_su', 's@example.com', 'x')
            n = User.objects.create_user('wl1_n', 'n@example.com', 'x')
            a.user_permissions.add(perm)
            b.user_permissions.add(perm)
            ca, cb, cs, cn, anon = (Client(SERVER_NAME='localhost')
                                    for _ in range(5))
            ca.force_login(a)
            cb.force_login(b)
            cs.force_login(su)
            cn.force_login(n)
            day = timezone.localdate()

            r = ca.get('/wellness/')
            ok(r.status_code == 200 and b'Pick two or three' in r.content,
               'the first visit opens on the welcome cards and starter set')
            r = ca.post('/wellness/welcome/',
                        {'starter': ['walk', 'water', 'read']})
            ok(r.status_code == 302
               and Habit.objects.filter(user=a).count() == 3,
               '  three starters tapped, three habits made')
            r = ca.get('/wellness/')
            t = r.content.decode()
            ok(t.count('data-habit-row') == 3 and 'Good ' in t,
               'Today greets them and lists the three')
            ok('Tap a habit when you have done it' in t,
               '  with the first tip')
            water = Habit.objects.get(user=a, name='Glass of water')
            r = ca.post('/wellness/habits/%d/check/' % water.pk,
                        {'date': day.isoformat(), 'op': 'toggle'},
                        HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 200 and r.json()['done'] is True,
               'one tap ticks it')
            r = ca.post('/wellness/habits/%d/check/' % water.pk,
                        {'date': day.isoformat(), 'op': 'toggle'},
                        HTTP_X_REQUESTED_WITH='fetch')
            ok(r.json()['done'] is False
               and not HabitLog.objects.filter(habit=water).exists(),
               '  and a second tap undoes it, leaving no row')
            water.started_on = day - dt.timedelta(days=30)
            water.save()
            r = ca.post('/wellness/habits/%d/check/' % water.pk,
                        {'date': (day - dt.timedelta(6)).isoformat()},
                        HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 200, 'a day six days ago can be filled in')
            r = ca.post('/wellness/habits/%d/check/' % water.pk,
                        {'date': (day - dt.timedelta(7)).isoformat()},
                        HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 400, '  seven days ago cannot')
            r = ca.post('/wellness/habits/%d/check/' % water.pk,
                        {'date': (day + dt.timedelta(1)).isoformat()},
                        HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 400, '  nor tomorrow')
            read_h = Habit.objects.get(user=a, name='Read')
            r = ca.post('/wellness/habits/%d/check/' % read_h.pk,
                        {'date': day.isoformat(), 'op': 'set',
                         'value': '6'}, HTTP_X_REQUESTED_WITH='fetch')
            ok(r.json() == dict(r.json(), done=False, value=6),
               '6 of 10 pages is logged, and not done yet')
            r = ca.post('/wellness/habits/%d/edit/' % read_h.pk,
                        {'name': 'Read', 'kind': 'count', 'target': '5',
                         'unit': 'pages', 'schedule': 'daily',
                         'time_of_day': 'evening'})
            ok(HabitLog.objects.get(habit=read_h, date=day).done,
               '  lowering the aim to 5 re-judges it: done')

            for who, cl, code in (('another member', cb, 404),
                                  ('a superuser', cs, 404)):
                r = cl.get('/wellness/habits/%d/' % water.pk)
                ok(r.status_code == code,
                   "%s cannot open Demetri's habit (%d)" % (who, code),
                   r.status_code)
            r = cb.post('/wellness/habits/%d/check/' % water.pk,
                        {'op': 'toggle'})
            ok(r.status_code == 404, '  nor tick it')
            r = cb.get('/wellness/habits/')
            ok(b'Glass of water' not in r.content,
               "  and their list does not show it")
            r = cn.get('/wellness/')
            ok(r.status_code == 403, 'without the permission: refused',
               r.status_code)
            r = anon.get('/wellness/')
            ok(r.status_code == 302 and '/login/' in r['Location'],
               'with no login: to the login page')
            for u, ctype in (('manifest.webmanifest', 'application/manifest'),
                             ('sw.js', 'application/javascript'),
                             ('wellness.css', 'text/css'),
                             ('icon-192.png', 'image/png')):
                r = anon.get('/wellness/app/' + u)
                ok(r.status_code == 200 and r['Content-Type'].startswith(
                    ctype), 'the app shell answers with no login: %s' % u,
                   r.status_code)
            r = anon.get('/wellness/app/sw.js')
            ok(r.get('Service-Worker-Allowed') == '/wellness/',
               '  the worker may look after all of /wellness/')
            r = anon.get('/wellness/app/views.py')
            ok(r.status_code == 404, 'CONTROL: and nothing else is served '
               'from there')

            r = ca.post('/wellness/tips/', {'key': 'today_tap'},
                        HTTP_X_REQUESTED_WITH='fetch')
            t = ca.get('/wellness/').content.decode()
            ok('Tap a habit when you have done it' not in t
               and 'The ring fills' in t,
               'a tip, once tapped, is gone - and the next one waits')
            ok(t.count('class="w-tip"') == 1, '  one tip at a time')
            ca.post('/wellness/tips/', {'reset': 'all'})
            ok(WellnessProfile.objects.get(user=a).tips_seen == [],
               '"Show me the tips again" brings them back')

            r = ca.get('/wellness/habits/new/')
            t = r.content.decode()
            ok(t.count('class="w-step"') == 4,
               'a new habit is four short questions')
            ok('data-fill="f-name"' in t and 'data-fill="f-cue"' in t,
               '  with examples to tap')
            r = ca.post('/wellness/habits/new/', {'name': '', 'kind':
                                                  'count'})
            ok(b'Give it a short name' in r.content,
               '  a missing name is asked for, kindly')
            r = ca.post('/wellness/habits/new/',
                        {'name': 'Strength', 'kind': 'duration',
                         'target': '15', 'schedule': 'per_week',
                         'per_week': '3', 'time_of_day': 'morning',
                         'tiny_version': 'one set'})
            g = Habit.objects.get(user=a, name='Strength')
            ok(r.status_code == 302 and g.per_week == 3
               and g.started_on == day, '  and a good one starts today')
            ok(ca.get('/wellness/habits/%d/' % g.pk).status_code == 200,
               'its page opens')
            ca.post('/wellness/habits/%d/pause/' % g.pk)
            ok(Habit.objects.get(pk=g.pk).paused, 'Pause')
            ca.post('/wellness/habits/%d/archive/' % g.pk)
            ok(Habit.objects.get(pk=g.pk).archived_at, 'Archive')
            r = ca.post('/wellness/habits/%d/delete/' % g.pk)
            ok(r.status_code == 400 and Habit.objects.filter(pk=g.pk)
               .exists(), 'Delete without the tick box does nothing')
            ca.post('/wellness/habits/%d/delete/' % g.pk, {'confirm': 'yes'})
            ok(not Habit.objects.filter(pk=g.pk).exists(),
               '  with it, the habit and its history go')
            ok(ca.get('/wellness/guide/').status_code == 200,
               'the ? guide opens')
            t = ca.get('/personal/').content.decode()
            ok("Wellness</h6>" in t, 'Personal shows the tile to a member '
               'who has Wellness')
            t = cn.get('/personal/').content.decode()
            ok("Wellness</h6>" not in t, '  and not to one who has not')

            # ---- 30 days on the phone, the main app's hour kept.
            from wellness import session as WS
            PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) '
                     'AppleWebKit/537.36 Chrome/131.0 Mobile Safari/537.36')
            DESK = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0'
            cp = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            cd = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=DESK)
            for cl in (cp, cd):
                cl.post('/login/', {'username': 'wl1_a', 'password': 'x'})
            cd.get('/wellness/')
            ok(not cd.session.get(WS.LONG),
               'Wellness on a computer: the session is left alone')
            cp.get('/wellness/')
            sp = cp.session
            ok(sp.get(WS.LONG) and sp.get_expiry_age() > 29 * 86400,
               'Wellness on a phone: the session lasts 30 days',
               sp.get_expiry_age())
            ok(sp.get(WS.MAIN_UNTIL),
               '  and the main app keeps its own hour, stamped at login')
            ok(cp.get('/personal/').status_code == 200,
               '  within the hour, the main app opens as usual')
            sp[WS.MAIN_UNTIL] = 1
            sp.save()
            r = cp.get('/personal/')
            ok(r.status_code == 302
               and r['Location'].startswith('/login/?next=/personal/'),
               'after the hour, a main-app page asks for the login again')
            ok(cp.get('/wellness/').status_code == 200,
               '  while Wellness carries on - the session was kept')
            cp.post('/login/', {'username': 'wl1_a', 'password': 'x'})
            ok(cp.get('/personal/').status_code == 200,
               '  and logging in gives the main app a fresh hour')
            sd = cd.session
            sd[WS.MAIN_UNTIL] = 1
            sd.save()
            ok(cd.get('/personal/').status_code == 200,
               'CONTROL: a session that never opened Wellness on a phone is '
               'governed by Django alone, exactly as before')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def can_establish('" in gate, '  with a sentinel on the rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
