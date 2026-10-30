# -*- coding: utf-8 -*-
"""test_wellness_cycle.py - round CY-1, 30 Oct 2026.

RELEASE 46 - WELLNESS: THE CYCLE TRACKER. Demetri's decisions of 30 Oct:

    1. Opt-in per person, OFF by default - no tab, no Today card, until
       the person turns it on.
    2. The fertile-window estimate is offered but OFF by default, and is
       always labelled "an estimate, not contraception".
    3. The WHOLE record is encrypted: every day and every setting, with no
       plain date column.
    4. After Workouts, before W-4.

From the approved screens: an overview with the cycle-day ring, the next
period as a window, a month calendar and Log today; a day log of flow,
symptoms, pain and a private note; patterns around the period after
three cycles; a printable doctor report; gentle doctor flags; pregnancy
and hormonal-contraception modes; one-step download and delete.
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
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_cycle1'
ME = 'test_wellness_cycle.py'
PATCHER = 'apply_wellness_cycle.py'
PS1 = 'Push-PendingChanges.ps1'

J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
NEW_FILES = ['cycle.py', 'views_cycle.py', J('migrations', '0005_cycle.py'),
             J('templatetags', '__init__.py'),
             J('templatetags', 'wellness_cycle.py')] + [
    J('templates', 'wellness', f) for f in (
        'cycle_intro.html', 'cycle.html', 'cycle_log.html',
        'cycle_settings.html', 'cycle_patterns.html', 'cycle_report.html')]
EDITED = [J(APP, 'models.py'), J(APP, 'views.py'), J(APP, 'urls.py'),
          J(APP, 'guide.py'), J(APP, 'assets', 'wellness.css'),
          J(APP, 'assets', 'wellness.js'), J(WT, 'base.html'),
          J(WT, 'today.html'), J(WT, 'guide.html')]

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
ok(not missing, 'the cycle files are all there (%d)' % len(NEW_FILES),
   ', '.join(missing))
models = T.code_only(read(J(APP, 'models.py')))
cls = models[models.index('class CycleRecord'):]
ok(re.search(r'prefs = models\.TextField', cls) and
   re.search(r'days = models\.TextField', cls),
   'the record is two locked text fields, settings and days')
ok('DateField' not in cls,
   '  with no date column - a plain list of dates would give a period away')
ok('OneToOneField' in cls, '  one record per person')
mig = read(J(APP, 'migrations', '0005_cycle.py'))
ok('0004_exercise_library' in mig and 'CycleRecord' in mig,
   'migration 0005 makes it, after the exercise library')
cy = T.code_only(read(J(APP, 'cycle.py')))
ok(cy.count('crypto.seal(') == 2 and cy.count('crypto.open_(') == 3,
   'only cycle.py locks and opens it: both fields sealed on save')
ok("'on': False" in cy and "'fertile': False" in cy,
   'off by default, and the fertile estimate off by default')
views = T.code_only(read(J(APP, 'views_cycle.py')))
ok('<int:pk>' not in read(J(APP, 'urls.py')).split("'cycle/")[1]
   .split('guide/')[0], 'no cycle address carries an id - nothing to guess')
ok(views.count('C.load(request.user)') >= 6,
   "every page reads the signed-in person's own record (%d)"
   % views.count('C.load(request.user)'))
ok('FERTILE_LABEL' in read(J(WT, 'cycle.html')) or
   'fertile_label' in read(J(WT, 'cycle.html')),
   'the calendar labels the fertile estimate wherever it shows')
ok('not contraception' in read(J(APP, 'cycle.py')),
   '  and the label says "not contraception"')
base = read(J(WT, 'base.html'))
ok('{% cycle_on as cy_on %}{% if cy_on %}' in base,
   'the bottom bar shows Cycle only when it is on')
ok('?v=cy1-1' in base and base.count('?v=cy1-1') == 2 and
   "SW_VERSION = 'cy1-1'" in read(J(APP, 'views.py')),
   'the asset version moved together (cy1-1): phones fetch the new css')
today = read(J(WT, 'today.html'))
ok('{% if cycle %}' in today and 'data-cycle-card' in today,
   'Today has a cycle card, only when there is one')
ok('period' not in T.code_only(read(J(APP, 'views_cycle.py'))
                                .split('def today_card')[1]).lower()
   .replace("never says 'period'", ''),
   '  and its line never says "period" - Today is seen over a shoulder')
css = read(J(APP, 'assets', 'wellness.css'))
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
ok('#E9D3CF' in css and '.w-month' in css,
   'soft rose for period days, in its own month grid (not the habit one)')
ok(not re.search(r'#(?:F00|FF0000|D9534F|DC3545)\b', css, re.I),
   '  and still no red')
guide = read(J(APP, 'guide.py'))
ok('Who can see my cycle log?' in guide and
   'What is the fertile estimate?' in guide,
   'the guide answers who can see it and what the estimate is')
ok("url 'wellness:cycle'" in read(J(WT, 'guide.html')),
   '  and the guide is where it is turned on')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('class CycleRecord' not in was(J(APP, 'models.py')),
   'CONTROL: before this round there was no cycle tracker')

# ==========================================================================
head('2. THE RULES (no database)')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import cycle as C                             # noqa: E402
D = dt.date


def run(start, n, flows=('medium', 'heavy', 'medium', 'light', 'light')):
    return {(start + dt.timedelta(days=i)).isoformat(): {'flow': f}
            for i, f in enumerate(flows[:n])}


days = {}
for a in (D(2026, 7, 1), D(2026, 7, 29), D(2026, 8, 28), D(2026, 9, 26)):
    days.update(run(a, 5))
ps = C.periods(days)
ok([p[0] for p in ps] == [D(2026, 7, 1), D(2026, 7, 29), D(2026, 8, 28),
                          D(2026, 9, 26)], 'four periods found', ps)
gap = dict(run(D(2026, 1, 1), 3))
gap[D(2026, 1, 5).isoformat()] = {'flow': 'light'}
ok(len(C.periods(gap)) == 1, '  one dry day inside a period does not end it')
ok(not C.periods({'2026-01-01': {'flow': 'spotting'}}),
   '  and spotting alone does not start one')
cs = C.cycles(ps)
ok([c['length'] for c in cs] == [28, 30, 29, None],
   'cycle lengths 28, 30, 29 and the current one', [c['length'] for c in cs])
s = C.summary(days, D(2026, 10, 10), {'mode': 'normal', 'fertile': False})
ok(s['state'] == 'predicted' and s['window'] == (D(2026, 10, 24),
                                                 D(2026, 10, 26)),
   'the next period is a WINDOW: median 29, widened by the spread',
   (s['state'], s['window']))
ok(s['cycle_day'] == 15 and s['avg_cycle'] == 29 and s['avg_period'] == 5,
   '  cycle day 15, typical cycle 29, typical period 5')
ok(s['fertile'] is None, 'the fertile estimate is off unless asked for')
s2 = C.summary(days, D(2026, 10, 10), {'mode': 'normal', 'fertile': True})
ok(s2['fertile'] == (D(2026, 10, 6), D(2026, 10, 12)),
   '  and when asked for, it is a window counted back from the next period',
   s2['fertile'])
one = run(D(2026, 9, 1), 5)
ok(C.summary(one, D(2026, 9, 10), C.DEFAULT_SETTINGS)['state'] == 'learning',
   'one period: still learning, no guess')
two = dict(one)
two.update(run(D(2026, 9, 29), 5))
ok(C.summary(two, D(2026, 10, 5), C.DEFAULT_SETTINGS)['state']
   == 'first_guess', 'two periods: a first guess, said to be one')
ok(C.summary(days, D(2026, 11, 10), C.DEFAULT_SETTINGS)['state'] == 'late',
   'past the window: "a few days later than usual", kindly')
for m in ('pregnant', 'hormonal'):
    sm = C.summary(days, D(2026, 10, 10), {'mode': m})
    ok(sm['state'] == m and sm['window'] is None and not sm['flags'],
       '%s mode: no prediction and no flags' % m)
odd = {}
for a, n in ((D(2026, 1, 1), 5), (D(2026, 1, 19), 5), (D(2026, 2, 6), 9),
             (D(2026, 2, 24), 5)):
    odd.update(run(a, n, ('heavy',) * 9))
fl = C.flags(C.cycles(C.periods(odd)), D(2026, 3, 1))
ok(any('shorter than 21' in f for f in fl) and
   any('more than 7 days' in f for f in fl),
   'gentle flags: short cycles, and a period over 7 days', fl)
ok(any('three months' in f for f in C.flags(cs, D(2027, 1, 10))),
   '  and three months without one')
ok(not C.flags(cs, D(2026, 10, 10)), '  nothing to flag for a steady cycle')
ok(C.headline(s)[0] == 'Next period around 24 – 26 October' and
   'Usually 28–30 days' in C.headline(s)[1],
   'the headline: "Next period around 24 – 26 October"', C.headline(s))
ok(C.span_words(29, 29) == '29' and C.span_words(28, 31) == '28 to 31',
   '  "29", never "29 to 29"')
ok(C.today_line(s, D(2026, 10, 10)) == 'Cycle day 15' and
   C.today_line(s, D(2026, 10, 22)) == 'Expected in about 2 days',
   'the Today line is discreet: "Cycle day 15", "Expected in about 2 days"')
syms = dict(days)
for a in (D(2026, 7, 1), D(2026, 7, 29), D(2026, 8, 28), D(2026, 9, 26)):
    k = (a - dt.timedelta(days=2)).isoformat()
    syms[k] = {'sym': ['headache']}
    syms[a.isoformat()] = dict(syms[a.isoformat()], sym=['cramps'])
rows, words = C.around(syms, C.cycles(C.periods(syms)))
ok([r[0] for r in rows][:2] in (['Cramps', 'Headache'],
                                ['Headache', 'Cramps']),
   'patterns: cramps and headaches around day 1', rows)
ok('Headaches often start 2 days before your period.' in words and
   'Cramps are most common on day 1.' in words,
   '  "Headaches often start 2 days before your period."', words)
ok(C.around(run(D(2026, 1, 1), 5), C.cycles(C.periods(
    run(D(2026, 1, 1), 5))))[0] == [],
   '  and nothing is claimed from fewer than three periods')
rep = C.report(syms, C.cycles(C.periods(syms)), 6)
ok(len(rep['rows']) == 4 and rep['rows'][0]['start'] == D(2026, 9, 26) and
   rep['rows'][1]['heaviest'] == 'heavy' and rep['rows'][1]['heavy'] == 1,
   'the doctor report: one row per cycle, newest first, heavy days counted')
ok(rep['notes'] == [], '  notes only when asked for')


class _Q(dict):
    def getlist(self, k):
        v = self.get(k, [])
        return v if isinstance(v, list) else [v]


ok(C.clean_day(_Q(flow='heavy', sym=['cramps', 'nonsense'], pain='4',
                  note=' sore ')) ==
   {'flow': 'heavy', 'sym': ['cramps'], 'pain': 4, 'note': 'sore'},
   'a day is cleaned: unknown symptoms dropped, pain kept 0-10')
ok(C.clean_day(_Q(flow='', pain='0')) == {},
   '  and an empty day is nothing - saving it removes the day')
g = C.month_grid(2026, 10, days, s, D(2026, 10, 10))
flat = [c for w in g for c in w]
ok(len(g[0]) == 7 and flat[0]['date'].weekday() == 0,
   'the calendar runs Monday first, in weeks of seven')
ok([c['kind'] for c in flat if c['date'] == D(2026, 10, 25)] == ['expected']
   and [c['kind'] for c in flat if c['date'] == D(2026, 9, 28)]
   == ['period'], '  period days and expected days marked')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import CycleRecord, WellnessProfile
    connection.ensure_connection()
    CycleRecord.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database, or migrate not run yet: %s'
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
            a = User.objects.create_user('cy1_a', 'a@example.com', 'x')
            b = User.objects.create_user('cy1_b', 'b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            t = ca.get('/wellness/').content.decode()
            ok('/wellness/cycle/' not in t.split('w-tabs')[1] and
               'data-cycle-card' not in t,
               'OFF BY DEFAULT: no Cycle tab and no Today card')
            r = ca.get('/wellness/cycle/')
            ok(r.status_code == 200 and
               'Turn on the cycle tracker' in r.content.decode(),
               '  its address shows the introduction and the switch')
            ok(ca.get('/wellness/cycle/log/').status_code == 302 and
               ca.get('/wellness/cycle/patterns/').status_code == 302,
               '  and every other page goes back to it while off')
            ok(not CycleRecord.objects.filter(user=a).exists(),
               '  looking creates nothing')
            ca.post('/wellness/cycle/settings/', {'turn': 'on'})
            t = ca.get('/wellness/cycle/').content.decode()
            ok('Log today' in t and 'Log your next period' in t,
               'turned on: the overview, waiting for the first period')
            ok('href="/wellness/cycle/"' in t.split('w-tabs')[1],
               '  and the bottom bar gains Cycle')
            today = timezone.localdate()
            starts = [today - dt.timedelta(days=x) for x in (95, 66, 37, 8)]
            for st in starts:
                for i, f in enumerate(['medium', 'heavy', 'medium', 'light',
                                       'light']):
                    data = {'date': (st + dt.timedelta(days=i)).isoformat(),
                            'flow': f}
                    if i == 0:
                        data['sym'] = ['cramps']
                        data['pain'] = '6'
                    ca.post('/wellness/cycle/log/', data)
            rec = CycleRecord.objects.get(user=a)
            raw = rec.prefs + rec.days
            ok(starts[-1].isoformat() not in raw and 'heavy' not in raw and
               'cramps' not in raw and '"on"' not in raw,
               'THE WHOLE RECORD IS LOCKED: no date, flow, symptom or '
               'setting readable in the database')
            t = ca.get('/wellness/cycle/').content.decode()
            ok('Next period around' in t and 'Usually 29 days' in t,
               'after four periods: "Next period around ..., usually 29 '
               'days"')
            ok('Fertile estimate' not in t,
               '  no fertile estimate unless turned on')
            ca.post('/wellness/cycle/settings/', {'mode': 'normal',
                                                  'fertile': '1'})
            t = ca.get('/wellness/cycle/').content.decode()
            ok('Fertile estimate' in t and 'not contraception' in t,
               '  turned on, it shows - labelled "not contraception"')
            t = ca.get('/wellness/').content.decode()
            ok('data-cycle-card' in t and 'Cycle day 9' in t,
               'Today: one discreet line, "Cycle day 9"')
            t = ca.get('/wellness/cycle/log/?date=%s'
                       % starts[-1].isoformat()).content.decode()
            ok('Started this day' in t and 'value="heavy"' in t,
               'a past day opens with what was logged')
            ok(ca.get('/wellness/cycle/log/?date=%s' % (
                today + dt.timedelta(days=3)).isoformat()
            ).content.decode().count('How is today?') == 1,
               '  and a future day is not loggable - it opens today')
            t = ca.get('/wellness/cycle/patterns/').content.decode()
            ok('Your cycles run 29 days' in t and 'Cramps' in t,
               'patterns: the bars and what comes around day 1')
            t = ca.get('/wellness/cycle/report/?n=6').content.decode()
            ok(t.count('<tr><td>') == 4 and 'Print or save as PDF' in t,
               'the doctor report: four cycles, printable')
            r = ca.get('/wellness/cycle/export/')
            body = json.loads(r.content.decode())
            ok('attachment' in r['Content-Disposition'] and
               len(body['days']) == 20 and body['settings']['fertile'],
               'download: every day and setting, opened, as a file')
            t = cb.get('/wellness/cycle/').content.decode()
            ok('Turn on the cycle tracker' in t and 'Cycle day' not in t,
               "EVERYONE SEES ONLY THEIR OWN: another member sees none of it")
            ok('data-cycle-card' not in cb.get('/wellness/').content
               .decode(), '  not even a Today card')
            ca.post('/wellness/cycle/settings/', {'mode': 'hormonal'})
            ok('Hormonal contraception' in ca.get('/wellness/cycle/')
               .content.decode(), 'hormonal mode pauses predictions')
            ca.post('/wellness/cycle/settings/', {'turn': 'off'})
            t = ca.get('/wellness/').content.decode()
            ok('data-cycle-card' not in t and
               '/wellness/cycle/' not in t.split('w-tabs')[1],
               'turned off: the tab and the card go')
            ok('still here, locked' in ca.get('/wellness/cycle/')
               .content.decode(), '  and the log is kept, locked')
            ca.post('/wellness/cycle/delete/', {})
            ok(CycleRecord.objects.filter(user=a).exists(),
               'delete without the confirm does nothing')
            ca.post('/wellness/cycle/delete/', {'confirm': 'delete'})
            ok(not CycleRecord.objects.filter(user=a).exists(),
               '  with it, every day and setting is gone in one step')
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
ok("Text = 'def summary('" in gate, '  with a sentinel on the predictions')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
