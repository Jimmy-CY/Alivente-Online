# -*- coding: utf-8 -*-
"""test_wellness_four.py - round WL-4a, 30 Oct 2026.

RELEASE 47 - WELLNESS W-4a: BADGES AND THE MONDAY SUMMARY. From the
proposal, the approved Badges screen and Demetri's notes of 30 Oct:

    - Badges mark what was done, never what was missed, and are KEPT for
      good once earned. The cycle tracker has none.
    - A badge just earned shows on Today, one at a time, until seen.
    - The Monday summary email is OFF unless the person turns it on, goes
      only to their own address, at most once a week, and NEVER carries
      the journal or the cycle log.
    - The Recent weigh-ins list shows 30, so a wrong one can be found and
      deleted (Demetri, 30 Oct 12:47).
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

SUFFIX = '.bak_wellness4'
ME = 'test_wellness_four.py'
PATCHER = 'apply_wellness_four.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
DAILY = J(ROOT, 'pages', 'management', 'commands',
          'check_lease_renewal_and_invoices.py')
NEW_FILES = ['badges.py', 'weekly.py', J('migrations', '0006_profile_prefs.py'),
             J('management', '__init__.py'),
             J('management', 'commands', '__init__.py'),
             J('management', 'commands', 'wellness_weekly.py'),
             J('templates', 'wellness', 'badges.html'),
             J('templates', 'wellness', 'settings.html')]
EDITED = [J(APP, 'models.py'), J(APP, 'views.py'), J(APP, 'urls.py'),
          J(APP, 'guide.py'), J(APP, 'assets', 'wellness.css'),
          J(WT, 'base.html'), J(WT, 'today.html'), J(WT, 'guide.html'),
          DAILY]

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
import ast                                                  # noqa: E402


def py_words(src):
    """Every name, attribute, import and string a Python file USES -
    docstrings and comments left out, so a file may explain what it never
    touches."""
    tree = ast.parse(src)
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and \
                n.body and isinstance(n.body[0], ast.Expr) and \
                isinstance(getattr(n.body[0], 'value', None), ast.Constant):
            docs.add(id(n.body[0].value))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.append(n.id)
        elif isinstance(n, ast.Attribute):
            out.append(n.attr)
        elif isinstance(n, ast.alias):
            out.append(n.name)
        elif isinstance(n, ast.ImportFrom):
            out.append(n.module or '')
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and \
                id(n) not in docs:
            out.append(n.value)
    return ' '.join(out).lower()

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
missing = [f for f in NEW_FILES if not os.path.isfile(J(APP, f))]
ok(not missing, 'the W-4a files are all there (%d)' % len(NEW_FILES),
   ', '.join(missing))
mig = read(J(APP, 'migrations', '0006_profile_prefs.py'))
ok('0005_cycle' in mig and 'name="prefs"' in mig,
   'migration 0006 adds the profile prefs, after the cycle tracker')
bg = read(J(APP, 'badges.py'))
ok('cycle' not in py_words(bg),
   'NO CYCLE BADGES: the badge rules never read the cycle tracker')
ok("kept[k] = today.isoformat()" in bg and 'del kept' not in bg and
   '.pop(' not in bg, 'a badge once earned is kept, with its day - never '
   'taken away')
wk = read(J(APP, 'weekly.py'))
ok('journal' not in py_words(wk) and 'cycle' not in py_words(wk),
   'THE EMAIL NEVER CARRIES the journal or the cycle log')
ok("get('weekly_email')" in wk and "p.user.email" in wk,
   '  it goes only to people who turned it on, at their own address')
cmd = read(J(APP, 'management', 'commands', 'wellness_weekly.py'))
ok("weekday() != 0" in cmd and "'weekly_sent'" in cmd,
   'the command acts only on a Monday, and once a week per person')
daily = read(DAILY)
blk = daily[daily.index("call_command('wellness_weekly'") - 200:
            daily.index("call_command('wellness_weekly'") + 300]
ok("try:" in blk and "except Exception as e:" in blk,
   'the daily job calls it, guarded - a failure never stops the property '
   'reports')
views = read(J(APP, 'views.py'))
ok("kind='weight')[:30])" in views,
   'Recent weigh-ins lists 30, so a wrong one can be found and deleted')
ok("def badges_page" in views and "def settings_page" in views,
   'the badges page and the settings page')
base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
# Later rounds move the version on (WL-4b: wl5-1); what must hold is that
# the page and the service worker always name the same one.
ok(len(_v) == 2 and len(set(_v)) == 1 and "SW_VERSION = '%s'" % _v[0]
   in views, 'the asset version moved together (wl4-1)', _v)
today = read(J(WT, 'today.html'))
ok('{% if new_badge %}' in today and 'data-new-badge' in today,
   'Today shows a new badge only when there is one')
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
ok("url 'wellness:settings'" in read(J(WT, 'guide.html')) and
   "url 'wellness:badges'" in read(J(WT, 'guide.html')),
   'the guide leads to badges and settings')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('prefs = models.JSONField' not in was(J(APP, 'models.py')),
   'CONTROL: before this round the profile had no prefs')

# ==========================================================================
head('2. THE RULES (no database)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import badges as BG                           # noqa: E402
from wellness import weekly as WK                           # noqa: E402
f = dict(BG.EMPTY)
ok(BG.earned(f) == [], 'nothing done, no badges')
f.update(ticks=1, streak=4, entries=12, sessions=1, records=1)
e = BG.earned(f)
ok(e == ['first_step', 'week_1', 'weeks_4', 'entry_1', 'entries_10',
         'session_1', 'record_1'], 'facts become badges, in order', e)
nx = BG.up_next(f, set(e))
ok(nx and nx[0]['name'] in ('10 workouts', '50 entries', 'Twelve good weeks',
                            '100 ticks') and all('to go' in n['need']
                                                 for n in nx),
   'up next: the closest few, each with what is left', nx)
f2 = dict(BG.EMPTY, habit_days=80)
ok(all(n['key'] != 'established' for n in BG.up_next(f2, set())),
   '  a habit past 66 days waits for the person - no "0 days to go"')
f3 = dict(BG.EMPTY, progress=0.6, kg_total=6.0, kg_half=3.0, kg_done=3.6)
ok('halfway' in BG.earned(f3) and 'goal' not in BG.earned(f3),
   'halfway to the goal weight, not yet the goal')
ok([n['need'] for n in BG.up_next(f3, set(BG.earned(f3)))
    if n['key'] == 'goal'] == ['2.4 kg to go'], '  and "2.4 kg to go"')
ok(len(BG.KEYS) == len(set(BG.KEYS)) == 22, 'twenty-two badges, no repeats')
ok(WK.week_before(dt.date(2026, 11, 2)) == (dt.date(2026, 10, 26),
                                             dt.date(2026, 11, 1)),
   'on Monday 2 November the summary is about 26 October - 1 November')
s = {'monday': dt.date(2026, 10, 26), 'sunday': dt.date(2026, 11, 1),
     'habits': [{'name': 'Walk', 'got': 4, 'target': 5, 'met': False}],
     'met': 0, 'sessions': [], 'minutes': 0, 'records': 0,
     'weight': {'trend': '84.7', 'change': '-0.3', 'weighins': 4},
     'badges': ['First step']}
subj, text, html = WK.render(s, 'Demetri')
ok(subj == 'Your Wellness week, 26 Oct – 1 Nov' and 'Walk - 4 of 5' in text
   and '-0.3 kg over the week' in text and 'First step' in text,
   'the email: habits, the trend and new badges, in kind words')
ok('<script' not in html and 'Demetri' in html,
   '  and its HTML is plain and escaped')
ok(WK.is_empty(dict(s, habits=[], weight=None, badges=[])),
   'a quiet week sends nothing')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.core.management import call_command
    from django.utils import timezone
    from wellness.models import Habit, HabitLog, WellnessProfile
    connection.ensure_connection()
    WellnessProfile.objects.filter(prefs__isnull=False).exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

# NO PERIODIC CLEANUP WHILE THIS SUITE DRIVES THE APP. The site's
# DatabaseConnectionMiddleware closes every connection each
# DB_FORCE_CLEANUP_INTERVAL requests (25). Set before the first request,
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
            a = User.objects.create_user('w4_a', 'w4a@example.com', 'x')
            b = User.objects.create_user('w4_b', 'w4b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            today = timezone.localdate()
            h = Habit.objects.create(user=a, name='Walk',
                                     started_on=today - dt.timedelta(days=21))
            t = ca.get('/wellness/').content.decode()
            ok('data-new-badge' not in t, 'no tick yet: no badge card')
            HabitLog.objects.create(habit=h, date=today, done=True)
            t = ca.get('/wellness/').content.decode()
            ok('data-new-badge' in t and 'First step' in t,
               'the first tick: "First step" on Today')
            pa = WellnessProfile.objects.get(user=a)
            ok((pa.prefs.get('badges') or {}).get('first_step')
               == today.isoformat(), '  kept with the day it was earned')
            ca.post('/wellness/badges/seen/', {'next': '/wellness/'})
            ok('data-new-badge' not in ca.get('/wellness/').content.decode(),
               '  "Nice" puts it away')
            HabitLog.objects.filter(habit=h).delete()
            t = ca.get('/wellness/badges/').content.decode()
            ok('First step' in t and '1 of 22' in t,
               'NEVER TAKEN AWAY: the tick undone, the badge stays')
            ok('First step' not in cb.get('/wellness/badges/').content
               .decode(), "another member's badges are their own")
            t = ca.get('/wellness/settings/').content.decode()
            ok('name="weekly_email"' in t and ' checked' not in
               t.split('name="weekly_email"')[1].split('>')[0],
               'the Monday summary is OFF by default')
            ca.post('/wellness/settings/', {'weekly_email': '1'})
            pa.refresh_from_db()
            ok(pa.prefs.get('weekly_email') is True and
               pa.prefs.get('badges'), 'turned on - and the badges kept')
            ok([p.user_id for p in WK.recipients()
                if p.user_id in (a.pk, b.pk)] == [a.pk],
               '  only the person who turned it on gets one')
            HabitLog.objects.create(habit=h, date=today - dt.timedelta(
                days=today.weekday() + 3), done=True)
            mon, sun = WK.week_before(today)
            ok(not WK.is_empty(WK.summary(a, mon)),
               "last week's tick makes a summary")
            sent = []
            _real = WK.send
            WK.send = lambda *a_, **k_: sent.append(a_) or True
            try:
                from io import StringIO
                out = StringIO()
                call_command('wellness_weekly', force=True, user='w4_a',
                             stdout=out)
                call_command('wellness_weekly', force=True, user='w4_a',
                             stdout=out)
            finally:
                WK.send = _real
            ok(len(sent) == 1 and sent[0][0] == 'w4a@example.com',
               'sent once, to her own address - a second run that week '
               'sends nothing', [x[0] for x in sent])
            ok('Walk' in sent[0][2] and 'journal' not in sent[0][2].lower()
               and 'First step' not in sent[0][2],
               '  about her habits, nothing from the journal - and a badge '
               'earned this week waits for next week\'s email')
            out = StringIO()
            call_command('wellness_weekly', stdout=out)
            if today.weekday() != 0:
                ok('not Monday' in out.getvalue(),
                   'on any other day the daily call does nothing')
            else:
                skip('the not-Monday check', 'today is a Monday')
            t = ca.get('/wellness/body/')
            ok(t.status_code == 200, 'the Body page still opens')
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
ok("Text = 'def earned('" in gate, '  with a sentinel on the badge rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
