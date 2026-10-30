# -*- coding: utf-8 -*-
"""test_wellness_two.py - round WL-2, 30 Oct 2026.

RELEASE 44 - WELLNESS, PART TWO: JOURNAL AND BODY. From the proposal and
his decisions of 30 October:

    - A journal of four kinds (evening check-in, free write, gratitude,
      quick note) with optional mood, energy and tags, a prompt of the day,
      search, a 30-day mood line and On this day.
    - THE WORDS ARE ENCRYPTED (decision 5), with their own key,
      WELLNESS_JOURNAL_KEY, never derived from SECRET_KEY on Live.
    - Body: a quick weigh-in, the TREND weight as the headline (a smoothed
      average, never the day's scale), 7- and 30-day change, weekly rate,
      a goal with "on pace for", tape measures and waist-to-height.
    - Today gains the weigh-in card, the evening card and On this day.
    - Everyone sees only their own - every lookup filtered by the login.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_wellness2'
ME = 'test_wellness_two.py'
PATCHER = 'apply_wellness_two.py'
PS1 = 'Push-PendingChanges.ps1'

J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
NEW_FILES = ['crypto.py', 'body.py', 'journal.py',
             J('migrations', '0002_journal_and_body.py'),
             J('templates', 'wellness', 'journal_list.html'),
             J('templates', 'wellness', 'journal_form.html'),
             J('templates', 'wellness', 'journal_detail.html'),
             J('templates', 'wellness', 'body.html'),
             J('templates', 'wellness', 'body_weigh.html'),
             J('templates', 'wellness', 'body_measure.html'),
             J('templates', 'wellness', 'body_goal.html'),
             J('templates', 'wellness', 'includes', 'face.html')]
EDITED = [J(APP, 'models.py'), J(APP, 'views.py'), J(APP, 'urls.py'),
          J(APP, 'guide.py'), J(APP, 'assets', 'wellness.css'),
          J(APP, 'assets', 'wellness.js'), J(WT, 'base.html'),
          J(WT, 'today.html')]

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

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
missing = [f for f in NEW_FILES if not os.path.isfile(J(APP, f))]
ok(not missing, 'the journal and body files are all there (%d)'
   % len(NEW_FILES), ', '.join(missing))
mig = read(J(APP, 'migrations', '0002_journal_and_body.py'))
ok(all(re.search(r"""name=["']%s["']""" % n, mig)
       for n in ('JournalEntry', 'BodyMetric')),
   'migration 0002 makes the journal and body tables')
ok(all(f in mig for f in ('height_cm', 'weight_goal', 'goal_date')),
   '  and gives the profile a height and a goal')
cr = read(J(APP, 'crypto.py'))
ok("ENV = 'WELLNESS_JOURNAL_KEY'" in cr and 'MultiFernet' in cr,
   'the journal key is its own setting, and can be rotated')
base = read(J(WT, 'base.html'))
ok(all(u in base for u in ("wellness:journal_list", "wellness:body")),
   'the bottom bar has Journal and Body')
ok(base.count('class="w-tab{%') == 4, '  four tabs: Today, Habits, '
   'Journal, Body', base.count('class="w-tab{%'))
bad = [f for f in NEW_FILES if f.endswith('.html') and 'includes' not in f
       and '{% extends "wellness/base.html" %}' not in read(J(APP, f))]
ok(not bad, 'every new page is a Wellness page', bad)
# Confined when installed (Demetri, 30 Oct 08:52).
outs = [f for f in os.listdir(WT) if f.endswith('.html')
        and "{% url 'personal_page' %}" in read(J(WT, f))]
leaks = [f for f in outs if re.search(
    r'''<a class="(?![^"]*\bw-out\b)[^"]*" href="\{% url 'personal_page' %\}"''',
    read(J(WT, f)))]
ok(outs and not leaks, 'every link out to the main app is marked w-out (%d '
   'page(s))' % len(outs), leaks)
_css = read(J(APP, 'assets', 'wellness.css'))
ok('.in-app .w-out { display: none !important; }' in _css
   and '@media (display-mode: standalone) { .w-out' in _css,
   '  and the installed app hides them - Today is as far back as it goes')
ok("matchMedia('(display-mode: standalone)')" in base
   and 'navigator.standalone' in base,
   '  the app is recognised on Android and iPhone alike')
ok(all(os.sep + 'wellness' + os.sep not in p for p in T.templates()),
   'and still outside the house tree')
v = read(J(APP, 'views.py'))
gets = [m.group(0) for m in re.finditer(
    r'get_object_or_404\((?:JournalEntry|BodyMetric)[^)]*\)', v)]
ok(len(gets) >= 4 and all('user=request.user' in g for g in gets),
   'every journal and body lookup is filtered by the login (%d)'
   % len(gets), gets)
ok(v.count('crypto.seal(') == 1 and 'e.body = crypto.seal(data)' in v,
   'the words are sealed in exactly one place')
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44]
ok(not small, 'every control is still at least 44px', small)
ok('Today' in read(J(WT, 'today.html')) and "wellness:body_weigh" in
   read(J(WT, 'today.html')), 'Today has the weigh-in card')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('JournalEntry' not in was(J(APP, 'models.py')),
   'CONTROL: before this round there was no journal')

# ==========================================================================
head('2. THE TREND (no database)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import body as B                              # noqa: E402
D = dt.date
f = B.daily({D(2026, 10, 1): 80, D(2026, 10, 5): 84})
ok(len(f) == 5 and abs(f[D(2026, 10, 3)] - 82) < 1e-9,
   'days between two weigh-ins are filled in a straight line')
flat = {D(2026, 9, 1) + dt.timedelta(i): 80.0 for i in range(30)}
spike = dict(flat)
spike[D(2026, 9, 30)] = 83.0
tr = B.trend(spike)
ok(abs(tr[D(2026, 9, 30)] - 80.3) < 1e-9,
   'one heavy morning (+3 kg) moves the trend a tenth as much (+0.3)')
ok(max(tr) == D(2026, 9, 30), 'the trend stops at the last weigh-in')
lin = {D(2026, 9, 1) + dt.timedelta(i): 90 - 0.1 * i for i in range(60)}
tl = B.trend(lin)
r = B.weekly_rate(tl)
ok(r is not None and abs(r + 0.7) < 0.05,
   'a steady 0.1 kg a day down reads as about -0.7 kg a week', r)
ok(B.change(tl, 7) < 0 and B.change(tl, 400) is None,
   'the 7-day change is there; a change with no history is None')
ok(B.weekly_rate(B.trend({D(2026, 9, 1): 80, D(2026, 9, 3): 80})) is None,
   'no weekly rate from fewer than seven days')
p = B.pace(84.0, 80, -0.5, D(2026, 10, 30))
ok(p == D(2026, 10, 30) + dt.timedelta(days=56),
   'four kilos at half a kilo a week is eight weeks away', p)
ok(B.pace(84.0, 80, 0.3, D(2026, 10, 30)) is None,
   'CONTROL: no "on pace" when the trend goes the other way')
ok(abs(B.progress(86.0, 84.0, 80) - 1 / 3.0) < 1e-9,
   'two of six kilos is a third of the way')
ch = B.chart(lin, tl, 30)
ok(ch and ch['line'].startswith('M') and ch['dots'],
   'the chart has a trend line and the raw dots')
ok(B.chart({}, {}, 30) is None, '  and nothing at all without weigh-ins')

# ==========================================================================
head('3. THE JOURNAL (no database)')
# ==========================================================================
from wellness import journal as JN                          # noqa: E402
ok(JN.clean_tags('#Work, family  work Sleep') == ['work', 'family', 'sleep'],
   'tags are cleaned: no hashes, lower case, no repeats')
ok(JN.prompt_for(1, D(2026, 10, 30)) == JN.prompt_for(1, D(2026, 10, 30)),
   "today's prompt holds all day")
ok(len({JN.prompt_for(1, D(2026, 10, 30), i) for i in range(8)}) > 2,
   '  and "Another prompt" gives another')
ok(JN._months_back(D(2026, 3, 31), 1) == D(2026, 2, 28),
   'On this day: a month before 31 March is 28 February, not an error')
ok(JN._months_back(D(2026, 1, 15), 12) == D(2025, 1, 15), '  a year back')

# ==========================================================================
head('4. THE LOCK')
# ==========================================================================
from wellness import crypto                                 # noqa: E402
from cryptography.fernet import Fernet                      # noqa: E402
secret = 'I walked by the sea and felt better'
tok = crypto.seal({'text': secret})
ok('sea' not in tok and 'walked' not in tok,
   'a sealed entry carries none of its words')
ok(crypto.open_(tok) == {'text': secret}, '  and opens back exactly')
old_env = os.environ.get(crypto.ENV)
k1, k2 = Fernet.generate_key().decode(), Fernet.generate_key().decode()
os.environ[crypto.ENV] = k1
t1 = crypto.seal({'text': secret})
os.environ[crypto.ENV] = k2
ok(crypto.open_(t1) == {'locked': True},
   'with the wrong key an entry says it is locked, rather than crashing')
os.environ[crypto.ENV] = k2 + ',' + k1
ok(crypto.open_(t1) == {'text': secret},
   'with the new key first and the old one after, old entries still open '
   '- a key can be rotated')
ok(crypto.configured(), '  and the setting counts as configured')
if old_env is None:
    del os.environ[crypto.ENV]
else:
    os.environ[crypto.ENV] = old_env

# ==========================================================================
head('5. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import JournalEntry, BodyMetric, WellnessProfile
    connection.ensure_connection()
    JournalEntry.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 5', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

# NO PERIODIC CLEANUP WHILE THIS SUITE DRIVES THE APP. The site's
# DatabaseConnectionMiddleware closes every connection each
# DB_FORCE_CLEANUP_INTERVAL requests (25). This suite makes more than that
# inside one rolled-back transaction, and a close in the middle of it ends
# the transaction under the suite's feet. Set before the first request,
# because the middleware reads it once, when it is built.
from django.conf import settings as _dj                     # noqa: E402
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


if have_db:
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_wellness',
                content_type__app_label='auth',
                defaults={'name': 'Can access Wellness'})
            a = User.objects.create_user('wl2_a', 'a@example.com', 'x',
                                         first_name='Demetri')
            b = User.objects.create_user('wl2_b', 'b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            day = timezone.localdate()

            r = ca.post('/wellness/journal/new/', {
                'kind': 'checkin', 'mood': '4', 'energy': '3',
                'best': 'Walked by the sea after lunch',
                'let_go': 'the late invoice', 'intention': 'gym at seven',
                'tags': 'Family #sleep', 'date': day.isoformat()})
            e = JournalEntry.objects.filter(user=a).first()
            ok(r.status_code == 302 and e and e.kind == 'checkin'
               and e.mood == 4 and e.energy == 3,
               'an evening check-in is saved with its mood and energy')
            ok(e.tags == ['family', 'sleep'], '  and its tags, cleaned')
            ok('sea' not in e.body and 'invoice' not in e.body,
               'IN THE DATABASE, the words are not there - only a token')
            t = ca.get('/wellness/journal/%d/' % e.pk).content.decode()
            ok('Walked by the sea after lunch' in t and 'gym at seven' in t,
               '  while the writer reads them back')
            ok(cb.get('/wellness/journal/%d/' % e.pk).status_code == 404,
               'another member gets "not found"')
            su = User.objects.create_superuser('wl2_su', 's@x.com', 'x')
            cs = Client(SERVER_NAME='localhost')
            cs.force_login(su)
            ok(cs.get('/wellness/journal/%d/' % e.pk).status_code == 404,
               '  and so does a superuser')
            ok(b'Walked by the sea' not in cb.get(
                '/wellness/journal/?q=sea').content,
               "  and their search cannot reach it")
            for kind, data in (('free', {'text': 'A long walk today'}),
                               ('gratitude', {'line1': 'Coffee',
                                              'line2': 'Sun', 'line3': ''}),
                               ('note', {'text': 'Call the plumber'})):
                d = dict(data, kind=kind, date=day.isoformat())
                ca.post('/wellness/journal/new/', d)
            ok(JournalEntry.objects.filter(user=a).count() == 4,
               'free write, gratitude and a quick note are saved too')
            r = ca.post('/wellness/journal/new/', {'kind': 'free', 'text':
                                                   '   '})
            ok(r.status_code == 200 and b'Write a word or two' in r.content,
               'an empty entry is asked for a word, kindly')
            r = ca.post('/wellness/journal/new/', {
                'kind': 'note', 'text': 'tomorrow',
                'date': (day + dt.timedelta(5)).isoformat()})
            ok(JournalEntry.objects.filter(user=a).order_by(
                '-created_at').first().date == day,
               'a date in the future is brought back to today')
            t = ca.get('/wellness/journal/?q=plumber').content.decode()
            ok('Call the plumber' in t and 'Walked by the sea' not in t,
               'search finds by a word inside the locked text')
            t = ca.get('/wellness/journal/?tag=family').content.decode()
            ok('Walked by the sea' in t and 'plumber' not in t,
               '  and filters by tag')
            t = ca.get('/wellness/journal/?mood=4').content.decode()
            ok('Walked by the sea' in t and 'plumber' not in t,
               '  and by mood')
            r = ca.post('/wellness/journal/%d/delete/' % e.pk)
            ok(r.status_code == 400 and JournalEntry.objects.filter(
                pk=e.pk).exists(), 'delete without the tick box does nothing')
            t = ca.get('/wellness/').content.decode()
            ok('Today is written' in t,
               "Today knows the evening check-in is done")
            ok('Weigh in' in t, '  and offers the weigh-in')

            for i, w in enumerate((86.0, 85.6, 85.9, 85.2, 85.0, 84.8,
                                   84.9, 84.4)):
                BodyMetric.objects.create(
                    user=a, kind='weight', value=w,
                    date=day - dt.timedelta(days=14 - 2 * i))
            r = ca.post('/wellness/body/weigh/', {'value': '84,3',
                                                  'date': day.isoformat()})
            from decimal import Decimal
            ok(r.status_code == 302 and BodyMetric.objects.get(
                user=a, kind='weight', date=day).value == Decimal('84.3'),
               'a weigh-in is saved - a comma for the decimal is fine')
            ca.post('/wellness/body/weigh/', {'value': '84.1'})
            ok(BodyMetric.objects.filter(user=a, kind='weight',
                                         date=day).count() == 1,
               '  a second one the same day replaces the first')
            r = ca.post('/wellness/body/weigh/', {'value': '8.41'})
            ok(r.status_code == 200 and b'does not look like' in r.content,
               'an impossible weight is questioned, not saved')
            ca.post('/wellness/body/goal/', {'weight_goal': '80',
                                             'height_cm': '180'})
            pr = WellnessProfile.objects.get(user=a)
            ok(pr.weight_goal == 80 and pr.height_cm == 180,
               'goal and height are saved')
            ca.post('/wellness/body/measure/', {'waist': '94', 'arm': '34',
                                                'chest': ''})
            ok(BodyMetric.objects.filter(user=a).exclude(
                kind='weight').count() == 2,
               'measurements: only the ones filled in are saved')
            t = ca.get('/wellness/body/').content.decode()
            ok('Trend weight' in t and 'kg this week' in t,
               'Body shows the trend and its weekly change')
            ok('0.52' in t, '  and waist to height (94 / 180)')
            ok('Goal 80' in t, '  and the goal')
            m = BodyMetric.objects.filter(user=a).first()
            ok(cb.post('/wellness/body/%d/delete/' % m.pk).status_code
               == 404, "nobody can delete somebody else's weigh-in")
            ok(b'Trend weight' not in cb.get('/wellness/body/').content,
               "  or see their trend")
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
ok("Text = 'def trend('" in gate, '  with a sentinel on the trend')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
