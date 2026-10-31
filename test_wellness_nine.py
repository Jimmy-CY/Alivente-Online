# -*- coding: utf-8 -*-
"""test_wellness_nine.py - round WL-7, 31 Oct 2026.

RELEASE 52 - WELLNESS: CALM. Demetri, 31 Oct 14:26, on the spec: guided
practices SPOKEN, "use a female built in voice from the phone"; Calm a tab
of its own at the bottom if another tab can be fit; Calm minutes can tick
a habit. 14:41, on the screenshots: "Go ahead. I like it".

    - A Calm tab beside Journal (seven tabs with the cycle tracker fit at
      360px), and a "Take a breath" card on Today.
    - Breathe: a circle to breathe with - four patterns, 1 to 5 minutes.
    - Guided: eight short practices read aloud by the phone's own voice,
      a female English one chosen where the phone has one; the words show
      on screen too.
    - Sit: a quiet timer with bells.
    - It all runs on the phone. Only how long is kept (CalmSession), and a
      habit set to "When I spend time in Calm" is ticked by it.
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

SUFFIX = '.bak_wellness9'
ME = 'test_wellness_nine.py'
PATCHER = 'apply_wellness_nine.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(WT, 'base.html'), J(WT, 'today.html'), J(WT, 'habit_form.html'),
          J(APP, 'assets', 'wellness.css'), J(APP, 'assets', 'wellness.js'),
          J(APP, 'views.py'), J(APP, 'models.py'), J(APP, 'urls.py'),
          J(APP, 'badges.py'), J(APP, 'guide.py'), J(APP, 'help.py')]

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
for rel in ('calm.py', 'views_calm.py', J('migrations', '0008_calm.py'),
            J('templates', 'wellness', 'calm.html'),
            J('templates', 'wellness', 'calm_breathe.html'),
            J('templates', 'wellness', 'calm_sit.html'),
            J('templates', 'wellness', 'calm_guided.html'),
            J('templates', 'wellness', 'calm_practice.html'),
            J('templates', 'wellness', 'includes', 'calm_run.html'),
            J('templates', 'wellness', 'includes', 'calm_icons.html')):
    ok(os.path.isfile(J(APP, rel)), '%s is there' % rel)
base = read(J(WT, 'base.html'))
ok("{% url 'wellness:calm' %}" in base and
   base.index("wellness:journal_list") < base.index("wellness:calm' %}") <
   base.index("wellness:workouts"),
   'THE TAB: Calm sits at the bottom, beside Journal')
css = read(J(APP, 'assets', 'wellness.css'))
ok('.w-tabs .w-tab { flex: 1 1 0; min-width: 0;' in css,
   '  the tabs share the width, so seven fit at 360px')
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
ok('.w-still .w-breath-ring { display: block; }' in css,
   'REDUCED MOTION: the circle stays still and a ring fills instead')
v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
# Later rounds move the version on; the page and the service worker must
# always name the same one.
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl9-1): phones fetch the new script',
   v)
ok("wellness-calm-%(v)s" in views and '(breathe|sit|guided)' in views,
   'OFFLINE: the service worker keeps the Breathe, Sit and Guided pages')
js = read(J(APP, 'assets', 'wellness.js'))
ok('window.speechSynthesis' in js and 'SpeechSynthesisUtterance' in js,
   'SPOKEN by the phone\'s own voice (speech synthesis)')
ok('var FEMALE = /female' in js and "lang(v) === 'en-gb'" in js,
   '  a female English voice is chosen where the phone has one')
ok("load('voice', '')" in js and "keep('voice'" in js,
   '  and the person can pick another; it is kept on that phone')
ok("match(/[^.?!]+[.?!]*/g)" in js,
   '  each line is said sentence by sentence (Android cuts long ones off)')
ok('AudioContext' in js and 'function bell()' in js,
   'the bells are made on the phone - nothing to download')
ok("navigator.wakeLock.request('screen')" in js,
   'the screen stays on while a session runs')
ok("keep('queue'" in js and 'function flush(' in js,
   'a session finished offline is kept and sent later')
tmpl = ''.join(read(J(WT, f)) for f in ('calm.html', 'calm_breathe.html',
                                        'calm_sit.html', 'calm_guided.html',
                                        'calm_practice.html'))
tmpl += read(J(WT, 'includes', 'calm_run.html'))
ok('json_script:"calm-data"' in tmpl and 'data-calm-run' in tmpl,
   'one runner frame for Breathe, Sit and Guided')
ok('Words only' in tmpl and 'Pause' in tmpl and 'End' in tmpl,
   '  with Pause, End, and Words only for the guided ones')
form = read(J(WT, 'habit_form.html'))
ok('<option value="calm"' in form and 'When I spend time in Calm' in form,
   'a habit can be set to "When I spend time in Calm"')
today_t = read(J(WT, 'today.html'))
ok('data-calm-card' in today_t and 'Take a breath' in today_t,
   'Today has a "Take a breath" card')
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
ok("wellness:calm" not in was(J(WT, 'base.html')),
   'CONTROL: before this round there was no Calm tab')

# ==========================================================================
head('2. THE PRACTICES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from wellness import calm as C                              # noqa: E402
from wellness import help as HELP                           # noqa: E402
ok([p[0] for p in C.PATTERNS] == ['calm', 'box', 'sleep', 'even'],
   'four breaths: Calm, Box, Sleep, Even')
ok(C.pattern_words(C.PATTERNS[2][3]) == 'In 4, hold 7, out 8',
   '  Sleep is in 4, hold 7, out 8')
ok(C.BREATHE_MINUTES == [1, 2, 3, 5] and C.SIT_MINUTES == [5, 10, 15, 20],
   'Breathe 1 to 5 minutes; Sit 5 to 20')
keys = [g['key'] for g in C.GUIDED]
ok(len(keys) == 8 and len(set(keys)) == 8, 'eight guided practices', keys)
crowded, late, long_s = [], [], []
for g in C.GUIDED:
    end = g['minutes'] * 60
    L = g['lines']
    for i, (at, words) in enumerate(L):
        nxt = L[i + 1][0] if i + 1 < len(L) else end
        # About two words a second at the calm speed, and a breath after.
        if len(words.split()) / 2.0 + 1.5 > nxt - at:
            crowded.append('%s@%d' % (g['key'], at))
        if at >= end:
            late.append('%s@%d' % (g['key'], at))
        for s in re.findall(r'[^.?!]+[.?!]*', words):
            if len(s.split()) > 22:
                long_s.append(s[:40])
    ok(L[0][0] == 0 and [a for a, _w in L] == sorted(a for a, _w in L),
       '  %s: %d lines, in order' % (g['name'], len(L)))
ok(not crowded, 'no line is spoken over the one before it', crowded)
ok(not late, 'every line comes before the closing bell', late)
ok(not long_s, 'every sentence is short enough to be said in one go',
   long_s)
words = ' '.join(w for g in C.GUIDED for _a, w in g['lines']).lower()
ok('!' not in words and ' should ' not in words and 'failed' not in words
   and 'must ' not in words,
   'kind words: no exclamation marks, no "should", "must" or "failed"')
ok(C.clean('breathe', 'calm', 59) is None and
   C.clean('breathe', 'calm', 60) == ('breathe', 'calm', 60),
   'a session under a minute is not kept')
ok(C.clean('guided', 'nope', 300) is None and
   C.clean('sing', '', 300) is None and
   C.clean('sit', 'x', 99999)[2] == C.MAX_SECONDS,
   '  nor an unknown practice; a phone left running is capped')
D = dt.date(2026, 10, 31)
s = C.summary([(D, 'breathe', 'calm', 150), (D - dt.timedelta(days=1),
               'guided', 'body_scan', 600), (D - dt.timedelta(days=6),
               'sit', '', 600)], D)
ok(s['minutes'] == 12 and s['days'] == 2 and s['today_minutes'] == 2 and
   s['last'] == 'Breathe, calm, today',
   'the week starts on Monday; minutes and days add up', s)
from wellness.models import Habit                           # noqa: E402
hm = Habit(kind='duration', target=10)
ok(C.tick_value(hm, 6) == (False, 6) and C.tick_value(hm, 11) == (True, 11),
   'a minutes habit counts Calm minutes towards its target')
ok(C.tick_value(Habit(kind='yes_no'), 1) == (True, None),
   '  any other habit is ticked by a session')
for n in ('calm', 'calm_breathe', 'calm_sit', 'calm_guided',
          'calm_practice'):
    ok(HELP.for_url_name(n) is not None, 'help for %s' % n)

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import CalmSession, HabitLog, WellnessProfile
    connection.ensure_connection()
    CalmSession.objects.exists()
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
            a = User.objects.create_user('w9_a', 'w9a@example.com', 'x')
            b = User.objects.create_user('w9_b', 'w9b@example.com', 'x')
            n = User.objects.create_user('w9_n', 'w9n@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            day = timezone.localdate()
            med = Habit.objects.create(user=a, name='Meditate',
                                       kind='duration', target=10,
                                       auto_from='calm', started_on=day)
            yes = Habit.objects.create(user=a, name='Be still',
                                       auto_from='calm', started_on=day)
            walk = Habit.objects.create(user=a, name='Walk', started_on=day)
            bm = Habit.objects.create(user=b, name='Meditate',
                                      kind='duration', target=10,
                                      auto_from='calm', started_on=day)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            pages = {'/wellness/calm/': 'Calm',
                     '/wellness/calm/breathe/': 'Breathe',
                     '/wellness/calm/sit/': 'Sit',
                     '/wellness/calm/guided/': 'Guided',
                     '/wellness/calm/guided/body_scan/': 'A guided practice'}
            for url, title in pages.items():
                r = ca.get(url)
                t = r.content.decode()
                ok(r.status_code == 200 and
                   '<h3 class="w-sheet-title">%s</h3>' % title in t and
                   'class="w-tab is-on" href="/wellness/calm/"' in t,
                   '%s opens, on the Calm tab, with its own help' % url)
            t = ca.get('/wellness/calm/guided/body_scan/').content.decode()
            ok('id="calm-data"' in t and 'from head to toe' in t and
               'data-calm-mute' in t,
               '  the practice carries its words to the phone')
            ok(ca.get('/wellness/calm/guided/nope/').status_code == 404,
               'an unknown practice is not found')
            ok(ca.get('/wellness/calm/done/').status_code == 405,
               'a session is kept only by a POST')
            r = ca.post('/wellness/calm/done/', {'kind': 'breathe',
                                                 'practice': 'calm',
                                                 'seconds': '360'})
            j = r.json()
            ok(r.status_code == 200 and j['kept'] and
               j['minutes_week'] == 6 and j['ticked'] == 'Be still',
               'SIX MINUTES OF BREATHING: kept; the yes-or-no habit ticked',
               j)
            lm = HabitLog.objects.get(habit=med, date=day)
            ok(lm.value == 6 and not lm.done,
               '  Meditate (10 minutes) has 6, not done yet')
            ok(HabitLog.objects.filter(habit=yes, date=day,
                                       done=True).exists(),
               '  "Be still" is done for today')
            ok(not HabitLog.objects.filter(habit=walk).exists(),
               '  a habit ticked by hand is left alone')
            j = ca.post('/wellness/calm/done/', {
                'kind': 'guided', 'practice': 'reset',
                'seconds': '300'}).json()
            lm.refresh_from_db()
            ok(lm.value == 11 and lm.done and 'Meditate' in j['ticked'],
               'FIVE MORE, GUIDED: Meditate reaches 11 of 10 and is done', j)
            j = ca.post('/wellness/calm/done/', {'kind': 'sit',
                                                 'seconds': '40'}).json()
            ok(not j['kept'] and CalmSession.objects.filter(user=a).count()
               == 2, 'forty seconds is not kept')
            j = ca.post('/wellness/calm/done/', {
                'kind': 'sit', 'seconds': '300',
                'date': (day + dt.timedelta(days=1)).isoformat()}).json()
            ok(not j['kept'], 'a day still to come is refused')
            j = ca.post('/wellness/calm/done/', {
                'kind': 'sit', 'seconds': '300',
                'date': (day - dt.timedelta(days=2)).isoformat()}).json()
            ok(j['kept'] and CalmSession.objects.filter(
                user=a, date=day - dt.timedelta(days=2)).exists(),
               'a session finished offline two days ago is added to its day')
            ok(not HabitLog.objects.filter(habit=bm).exists(),
               "another member's Meditate is their own")
            t = ca.get('/wellness/calm/').content.decode()
            ok('Ticks your habit Meditate after 10 minutes in a day.' in t,
               'Calm says which habit it ticks')
            t = ca.get('/wellness/').content.decode()
            ok('data-calm-card' in t and 'Calm today: 11 minutes' in t,
               "Today's card shows today's Calm minutes")
            t = ca.get('/wellness/badges/').content.decode()
            ok('First breath' in t, 'a quiet badge: First breath')
            r = ca.post('/wellness/habits/%d/edit/' % walk.pk, {
                'name': 'Walk', 'kind': 'yes_no', 'schedule': 'daily',
                'time_of_day': 'anytime', 'auto_from': 'calm'})
            walk.refresh_from_db()
            ok(walk.auto_from == 'calm',
               'a habit can be set to be ticked by Calm', r.status_code)
            r = ca.post('/wellness/habits/%d/edit/' % walk.pk, {
                'name': 'Walk', 'kind': 'yes_no', 'schedule': 'daily',
                'time_of_day': 'anytime', 'auto_from': 'telepathy'})
            walk.refresh_from_db()
            ok(walk.auto_from == '', '  and nothing else is accepted')
            cn = Client(SERVER_NAME='localhost')
            cn.force_login(n)
            ok(cn.get('/wellness/calm/').status_code == 403 and
               cn.post('/wellness/calm/done/', {
                   'kind': 'sit', 'seconds': '300'}).status_code == 403,
               'someone without Wellness access cannot reach Calm')
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
ok("Text = 'def tick_value('" in gate, '  with a sentinel on Calm')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
