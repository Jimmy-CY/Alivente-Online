# -*- coding: utf-8 -*-
"""test_wellness_twenty.py - round WL-16, 12 Nov 2026.

RELEASE 64 - WELLNESS: CATCH UP, THE WHOLE DAY DONE, THE PHONE'S CLOCK.
Demetri, 07:29:
  1. "I want the ability to be able to tick off a habit that I forgot to
     tick off in the past ... some sort of calendar view and see unticked
     habits" - 07:32: "a catch up of 7 days is sufficient".
  2. "when all habits for the day are ticked off ... I also want there to
     be like a thing popping and confetti."
  3. "Thursday, 12 November and Good Morning, this needs to be driven by
     the phone time and date" - 07:32: "Everything should follow the
     phone's time zone."
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

SUFFIX = '.bak_wellness20'
ME = 'test_wellness_twenty.py'
PATCHER = 'apply_wellness_twenty.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(APP, 'views.py'), J(APP, 'urls.py'), J(APP, 'modules.py'),
          J(APP, 'reminders.py'), J(APP, 'daily_line.py'), J(APP, 'help.py'),
          J(APP, 'guide.py'), J(APP, 'assets', 'wellness.js'),
          J(APP, 'assets', 'wellness.css'), J(WT, 'base.html'),
          J(WT, 'today.html'), J(WT, 'habit_list.html')]

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
cu = read(J(WT, 'catch_up.html'))
ok('data-catch-day' in cu and 'data-tick' in cu and
   'name="date" value="{{ pick.iso }}"' in cu,
   'CATCH UP: seven days across the top; each day ticks the way Today does')
ok('Times a week - tick it if you did it' in cu and 'data-flex' in cu,
   '  times-a-week habits offered, never counted as "left"')
ok("'wellness:catch_up'" in read(J(WT, 'today.html')).replace('"', "'") and
   'data-catch-up-line' in read(J(WT, 'today.html')) and
   'data-catch-up-link' in read(J(WT, 'habit_list.html')),
   '  reached from Today (when something is left) and from Habits')
js = read(J(APP, 'assets', 'wellness.js'))
ok('function dayDone(ring)' in js and "'w-confetti'" in js and
   "'w-pop'" in js and 'All done for today' in js,
   'THE WHOLE DAY: the ring pops, confetti falls, "All done for today"')
ok("'w-day-done-'" in js and 'if (ring && all && got === all)' in js,
   '  once a day, and on Today only')
ok("document.cookie = 'w_tz=' + tz +" in js and
   "resolvedOptions().timeZone" in js and 'location.reload()' in js and
   "'w-tz-redrawn-'" in js,
   'THE PHONE\'S CLOCK: the phone says its time zone; a page drawn on '
   'another is drawn again, once')
base = read(J(WT, 'base.html'))
ok('data-tz="{{ W_TZ }}"' in base and "data-day=\"{% now 'Y-m-d' %}\"" in base,
   '  the page says which clock it was drawn on, and which day')
v = read(J(APP, 'views.py'))
ok('with timezone.override(z):' in v and 'def _phone_tz(request)' in v,
   '  every Wellness page runs on that clock')
ok('MOD.phone_now(now_all, prof.prefs)' in read(J(APP, 'reminders.py')) and
   'MOD.phone_now(now, p.prefs)' in read(J(APP, 'daily_line.py')),
   '  and reminders and the daily line follow it between visits')
css = read(J(APP, 'assets', 'wellness.css'))
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px')
vv = re.findall(r'\?v=([\w-]+)', base)
ok(len(set(vv)) == 1 and "SW_VERSION = '%s'" % vv[0] in v and
   vv[0] != 'wl17-1', 'the asset version moved together (%s)' % vv[0])
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('override' not in was(J(APP, 'views.py')),
   'CONTROL: before this round every page ran on the site\'s own clock')

# ==========================================================================
head('2. THE RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
from wellness import modules as MOD                         # noqa: E402
ok(MOD.tz_or_none('Europe/London') is not None and
   MOD.tz_or_none('Not/AZone') is None and MOD.tz_or_none('') is None and
   MOD.tz_or_none('x' * 80) is None,
   'A TIME ZONE is read only when it is a real one')
now = dt.datetime(2026, 11, 12, 23, 30, tzinfo=dt.timezone.utc)
ok(MOD.phone_now(now, {'tz': 'Asia/Nicosia'}).date() == dt.date(2026, 11, 13)
   and MOD.phone_now(now, {'tz': 'America/New_York'}).hour == 18 and
   MOD.phone_now(now, {}) == now,
   '  23:30 UTC is 13 Nov in Nicosia, 18:30 in New York; none kept: as is')
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok(HELP.for_url_name('catch_up') and
   'Catch up' in ' '.join(HELP.for_url_name('habit_list')['steps']) and
   'confetti' in ' '.join(HELP.for_url_name('today')['steps']) and
   "phone's own clock" in ' '.join(HELP.for_url_name('today')['steps']),
   'HELP: Catch up has its own, Habits and Today mention it, the confetti '
   'and the phone\'s clock')
qs = [h['q'] for h in G.HOWTO]
ok('Set up: catch up on days you forgot' in qs and
   'Does Wellness follow my time zone when I travel?' in qs,
   '  and the general questions answer both')

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
            a = User.objects.create_user('w20_a', 'w20a@example.com', 'x')
            a.user_permissions.add(perm)
            prof = WellnessProfile.objects.create(user=a, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            # ---- the phone's clock: Kiritimati is 14 hours ahead of UTC,
            # Pago Pago 11 behind - always two different dates.
            far = 'Pacific/Kiritimati'
            ca.cookies['w_tz'] = far
            t = ca.get('/wellness/').content.decode()
            here = timezone.now().astimezone(MOD.tz_or_none(far)).date()
            prof.refresh_from_db()
            ok(('data-day="%s"' % here.isoformat()) in t and
               'data-tz="%s"' % far in t and prof.prefs.get('tz') == far,
               'THE PHONE\'S CLOCK (driven): Today is drawn on Kiritimati\'s '
               'date, and the zone is kept')
            ca.cookies['w_tz'] = 'Pacific/Pago_Pago'
            t = ca.get('/wellness/').content.decode()
            back = timezone.now().astimezone(
                MOD.tz_or_none('Pacific/Pago_Pago')).date()
            ok(('data-day="%s"' % back.isoformat()) in t and back != here,
               '  and on Pago Pago\'s, a day apart')
            ca.cookies['w_tz'] = 'Europe%2FLondon'
            t = ca.get('/wellness/').content.decode()
            ok('data-tz="Europe/London"' in t,
               '  an encoded name (Europe%2FLondon) is read too')
            ca.cookies['w_tz'] = 'Pacific/Pago_Pago'
            ca.get('/wellness/')
            ca.cookies['w_tz'] = 'Nowhere/Real'
            t = ca.get('/wellness/').content.decode()
            ok('data-tz="Pacific/Pago_Pago"' in t,
               '  a nonsense zone is ignored: the last real one is used')
            hb = Habit.objects.create(user=a, name='Stretch', kind='yes_no',
                                      schedule='daily',
                                      started_on=back - dt.timedelta(days=5))
            r = ca.post('/wellness/habits/%d/check/' % hb.pk,
                        {'op': 'toggle'}, HTTP_X_REQUESTED_WITH='fetch')
            ok(HabitLog.objects.filter(habit=hb, date=back, done=True).exists(),
               '  a tick with no date counts for the phone\'s today')
            # ---- catch up
            t = ca.get('/wellness/').content.decode()
            ok('data-catch-up-line' in t and
               '5 habits left unticked this past week' in t,
               'CATCH UP (driven): Today says 5 left in the past days')
            y = back - dt.timedelta(days=1)
            t = ca.get('/wellness/habits/catch-up/').content.decode()
            ok(t.count('data-catch-day') == 7 and
               ('name="date" value="%s"' % y.isoformat()) in t and
               ('aria-current="date"' in t),
               '  the page: seven days, opened on yesterday')
            ca.post('/wellness/habits/%d/check/' % hb.pk,
                    {'op': 'toggle', 'date': y.isoformat()},
                    HTTP_X_REQUESTED_WITH='fetch')
            ok(HabitLog.objects.filter(habit=hb, date=y, done=True).exists(),
               '  ticking yesterday there records yesterday')
            t = ca.get('/wellness/').content.decode()
            ok('4 habits left unticked this past week' in t,
               '  and Today now says 4')
            old = back - dt.timedelta(days=7)
            t = ca.get('/wellness/habits/catch-up/?day=%s'
                       % old.isoformat()).content.decode()
            ok(('value="%s"' % old.isoformat()) not in t,
               '  eight days back is not offered (a week is the reach)')
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
ok("Text = 'def phone_now('" in gate, '  with a sentinel on the clock')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
