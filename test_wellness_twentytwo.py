# -*- coding: utf-8 -*-
"""test_wellness_twentytwo.py - round WL-18, 12 Nov 2026.

RELEASE 67 - WELLNESS: THE GOAL DATE, DRAG TO ORDER, MOOD SEARCH.
Demetri, 11:18:
  - "I like the suggestion on goal date" - the date was saved and never
    used. Body now says the kilos a week needed and whether the trend
    gets there in time.
  - "re-ordering the exercises in a routine by dragging" - a grip on each
    exercise; the order is saved when you let go. The arrows stay.
  - "search the journal by mood" - it existed behind Search; now a mood
    searches as soon as it is tapped and says how many entries carry it.
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

SUFFIX = '.bak_wellness22'
ME = 'test_wellness_twentytwo.py'
PATCHER = 'apply_wellness_twentytwo.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

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
rf = read(J(WT, 'routine_form.html'))
ok('data-routine-list' in rf and 'data-drag' in rf and
   'data-pk="{{ it.pk }}"' in rf and 'name="order"' in rf,
   'ROUTINE: a grip on each exercise, inside one list that knows its order')
ok('value="up:{{ it.pk }}"' in rf and 'value="down:{{ it.pk }}"' in rf,
   '  and the arrows are still there')
vw = read(J(APP, 'views_workouts.py'))
ok('def _order(routine, text):' in vw and
   "elif action == 'order':" in vw and
   "if sorted(ids) != sorted(items):" in vw,
   '  the server applies an order only when it names exactly its exercises')
js = read(J(APP, 'assets', 'wellness.js'))
ok("querySelector('[data-routine-list]')" in js and
   "data.set('action', 'order'); data.set('order', now);" in js and
   "form.getAttribute('action') || location.pathname" in js and
   "document.addEventListener('pointermove', move)" in js and "toast('Order saved')" in js,
   '  dragging moves it live and saves the order when you let go')
ok("[data-search-now] input[type=radio]" in js and 'r.form.submit()' in js,
   'JOURNAL: a mood or tag searches as soon as it is tapped')
jl = read(J(WT, 'journal_list.html'))
ok(jl.count('data-search-now') == 2 and '{% for n, label, c in moods %}' in jl
   and '{% if c %} · {{ c }}{% endif %}' in jl,
   '  each mood shows how many entries carry it')
bd = read(J(WT, 'body.html'))
ok('data-goal-line' in bd and 'by {{ profile.goal_date|date:"j M Y" }}' in bd,
   'BODY: the goal shows its date and a line about getting there')
css = read(J(APP, 'assets', 'wellness.css'))
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins) and '.w-grip { touch-action: none;' in css,
   '  the grip does not scroll the page; still no min-height under 44px')
base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
# Loosened by WL-19: a later round bumps the version again.
ok(vv and len(set(vv)) == 1 and vv[0] not in ('wl19-1',) and
   ("SW_VERSION = '%s'" % vv[0]) in read(J(APP, 'views.py')),
   'the app files carry a new version, so phones fetch them again', vv)

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from wellness import body as B                              # noqa: E402
T = dt.date(2026, 11, 12)
JUNE = dt.date(2027, 6, 1)
c = B.goal_check(95.0, 85, -0.5, T, JUNE)
ok(c['state'] == 'on_track' and abs(c['need'] + 0.35) < 0.02,
   'ON TRACK: 10 kg to lose in 29 weeks needs 0.35 a week; losing 0.5',
   c)
w = B.goal_words(c, JUNE)
ok(w.startswith('To reach it by 1 June: lose 0.3 kg a week.') and
   'You are on track.' in w, '  "To reach it by 1 June: lose ... You are on '
   'track."', w)
c = B.goal_check(95.0, 85, -0.2, T, JUNE)
ok(c['state'] == 'behind' and c['pace'] > JUNE and
   'At your current pace you get there on' in B.goal_words(c, JUNE),
   'BEHIND: losing 0.2 a week gets there after the date, and says when')
c = B.goal_check(95.0, 85, 0.3, T, JUNE)
ok(c['state'] == 'behind' and c['pace'] is None and
   'not heading that way yet' in B.goal_words(c, JUNE),
   '  the trend going up: "not heading that way yet"')
c = B.goal_check(95.0, 85, None, T, JUNE)
ok(c['state'] == 'early' and 'after two weeks' in B.goal_words(c, JUNE),
   'EARLY: no pace yet - the need, and when on-track appears')
c = B.goal_check(95.0, 85, -0.5, T, dt.date(2026, 12, 10))
ok(c['fast'] and 'a later date is kinder' in B.goal_words(
    c, dt.date(2026, 12, 10)),
   'TOO FAST: 10 kg in four weeks says a later date is kinder')
ok(B.goal_check(95.0, 85, -0.5, T, dt.date(2026, 11, 1))['state'] ==
   'passed' and B.goal_check(85.02, 85, -0.5, T, JUNE)['state'] ==
   'reached', 'A PASSED date and a REACHED goal each say so')
c = B.goal_check(60.0, 64, 0.2, T, JUNE)
ok('gain' in B.goal_words(c, JUNE), '  and a goal above you says gain')
ok(B.goal_check(95.0, 85, -0.5, T, None) is None and
   B.goal_check(95.0, None, -0.5, T, JUNE) is None,
   'no goal, or no date: nothing is said')
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
steps = lambda n: ' '.join(HELP.for_url_name(n)['steps'])   # noqa: E731
ok('grip' in steps('routine_form') and 'on track' in steps('body') and
   'tap a mood' in steps('journal_list') and 'on track' in steps('body_goal'),
   'HELP: the grip, the goal date and the mood search on their screens')
qs = {h['q']: h for h in G.HOWTO}
ok('Set up: a goal weight with a date' in qs and
   qs['Set up: a goal weight with a date']['topic'] == 'body' and
   'How do I change the order of exercises in a routine?' in qs and
   'How do I find old journal entries by mood?' in qs,
   '  and the general questions answer all three, under the right topics')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import (WellnessProfile, Exercise, Routine,
                                 RoutineItem, BodyMetric, JournalEntry)
    connection.ensure_connection()
    RoutineItem.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

if have_db:
    import json
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
            a = User.objects.create_user('w22_a', 'w22a@example.com', 'x')
            b = User.objects.create_user('w22_b', 'w22b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
            prof = WellnessProfile.objects.create(user=a, onboarded=True)
            WellnessProfile.objects.create(user=b, onboarded=True)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            # ---- drag to order
            rt = Routine.objects.create(user=a, name='Order me')
            names = ['Push-up', 'Plank', 'Zumba']
            its = [RoutineItem.objects.create(
                routine=rt, exercise=Exercise.objects.get(user=None, name=n),
                position=k, sets=3, rep_min=10, rep_max=10, rest=60)
                for k, n in enumerate(names)]
            url = '/wellness/workouts/routines/%d/' % rt.pk
            page = ca.get(url).content.decode()
            ok(page.count('data-drag') == 3 and
               page.count('data-routine-item data-pk=') == 3,
               'THE ROUTINE draws a grip on each of its three exercises')
            want = [its[2].pk, its[0].pk, its[1].pk]
            r = ca.post(url, {'action': 'order', 'name': 'Order me',
                              'order': ','.join(str(x) for x in want),
                              'sets_%d' % its[0].pk: '4'},
                        HTTP_X_REQUESTED_WITH='fetch')
            got = list(rt.items.values_list('pk', flat=True))
            ok(r.status_code == 200 and json.loads(r.content)['ok'] and
               got == want,
               '  dragging Zumba to the top saves that order at once', got)
            ok(RoutineItem.objects.get(pk=its[0].pk).sets == 4,
               '  and keeps a number typed just before the drag')
            ca.post(url, {'action': 'order', 'name': 'Order me',
                          'order': '%d,%d' % (its[0].pk, its[1].pk)},
                    HTTP_X_REQUESTED_WITH='fetch')
            ok(list(rt.items.values_list('pk', flat=True)) == want,
               '  an order that leaves an exercise out changes nothing')
            ca.post(url, {'action': 'order', 'name': 'Order me',
                          'order': 'x,y'}, HTTP_X_REQUESTED_WITH='fetch')
            ok(list(rt.items.values_list('pk', flat=True)) == want,
               '  nor does nonsense')
            ok(cb.post(url, {'action': 'order', 'order': ','.join(
                str(x) for x in reversed(want))},
                HTTP_X_REQUESTED_WITH='fetch').status_code == 404 and
               list(rt.items.values_list('pk', flat=True)) == want,
               '  and nobody else can reorder your routine')
            r = ca.post(url, {'action': 'up:%d' % its[1].pk,
                              'name': 'Order me', 'order': ''})
            ok(r.status_code == 302 and
               list(rt.items.values_list('pk', flat=True)) ==
               [its[2].pk, its[1].pk, its[0].pk],
               '  the arrows still work')
            # ---- the goal date
            day = timezone.localdate()
            for k in range(21):
                BodyMetric.objects.create(
                    user=a, kind='weight', date=day - dt.timedelta(days=20 - k),
                    value='%.1f' % (96.0 - 0.08 * k))
            prof.weight_goal = 85
            prof.goal_date = day + dt.timedelta(days=7 * 40)
            prof.save()
            t = ca.get('/wellness/body/').content.decode()
            ok('data-goal-line' in t and 'To reach it by' in t and
               'kg a week' in t,
               'BODY shows what you need each week to reach 85 kg by the date')
            gd = prof.goal_date
            ok(('by %d %s' % (gd.day, gd.strftime('%b %Y'))) in t,
               '  and the goal says its date')
            prof.goal_date = None
            prof.save()
            ok('data-goal-line' not in ca.get('/wellness/body/').content
               .decode(), '  with no date, no line')
            # ---- mood search
            for mood, words in ((5, 'sea'), (5, 'hills'), (2, 'rain')):
                ca.post('/wellness/journal/new/', {
                    'kind': 'note', 'mood': str(mood), 'text': words,
                    'note': words, 'date': day.isoformat()})
            n5 = JournalEntry.objects.filter(user=a, mood=5).count()
            t = ca.get('/wellness/journal/').content.decode()
            ok(n5 == 2 and 'Great · 2' in t and 'A bit low · 1' in t,
               'JOURNAL: each mood shows how many entries carry it', n5)
            t = ca.get('/wellness/journal/?mood=2').content.decode()
            ok(t.count('class="w-entry-kind"') == 1 and
               'value="2" checked' in t,
               '  and tapping A bit low shows the one entry that has it')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL')
# ==========================================================================
try:
    ok('data-drag' not in was(J(WT, 'routine_form.html')) and
       'def goal_check(' not in was(J(APP, 'body.py')) and
       'data-search-now' not in was(J(WT, 'journal_list.html')),
       'before this round: no grip, no goal check, no instant mood search')
except IOError as _e:
    skip('section 4', str(_e))

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def goal_check('" in gate, '  with a sentinel on the goal date')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
