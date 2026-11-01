# -*- coding: utf-8 -*-
"""test_wellness_fourteen.py - round CY-4, 1 Nov 2026.

RELEASE 57 - WELLNESS: HONEST WORDING, PERIMENOPAUSE MODE, INSIGHTS.
Demetri, 05:21:
"Are these ideas scientifically or generally solid suggestions?" Mostly
general good habits; the phase-matching went beyond the research (McNulty
et al. 2020: trivial performance differences across the cycle; people vary
a lot). 05:26: "Let's do this for Release 57."

    - Well supported, kept plainly: heat and gentle exercise for period
      pain, iron while bleeding, rest.
    - Everything else said as a general habit or "some people find" -
      never as what the phase does to the body.
    - The board says so under its heading.

05:43: "Can we add a Perimenopause mode. At the same time, can we add an
Insights section/area" - both in this release. 05:48: "let's add more
symptoms to ours as well" - 22 for everyone, 6 more in perimenopause.
    - Perimenopause: a rough, wider window, never "late", no fertile
      estimate, no phases (ideas for these years instead), its symptoms
      in Log today and Patterns.
    - Insights: eight weeks side by side, and carefully what goes with
      what. Patterns, not proof.
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

SUFFIX = '.bak_wellness14'
ME = 'test_wellness_fourteen.py'
PATCHER = 'apply_wellness_fourteen.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(WT, 'cycle.html'), J(WT, 'cycle_settings.html'),
          J(WT, 'today.html'), J(WT, 'settings.html'), J(APP, 'phases.py'),
          J(APP, 'cycle.py'), J(APP, 'views_cycle.py'), J(APP, 'views.py'),
          J(APP, 'urls.py'), J(APP, 'assets', 'wellness.css'),
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
cy = read(J(WT, 'cycle.html'))
ok('{{ board_note }}' in cy and 'Ideas, not rules' in cy,
   'the board says what its ideas are, under its heading')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('at their best' in was(J(APP, 'phases.py')),
   'CONTROL: before this round an idea said strength was "at its best"')

# ==========================================================================
head('2. THE WORDS')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import phases as PH                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok('people vary a lot' in PH.DISCLAIMER and 'how you feel' in PH.DISCLAIMER,
   'THE NOTE: "Research shows people vary a lot - go by how you feel."')
words = ' '.join(' '.join(i[1:4]) for p in PH.BOARD.values()
                 for g in p.values() for i in g)
words += ' ' + ' '.join(t + ' ' + l for v in PH.LINES.values()
                        for t, l in v)
words += ' ' + ' '.join(w for _k, _n, w in PH.PHASES)
low = words.lower()
claims = [c for c in ('at their best', 'at its best', 'energy rises',
                      'energy often rises', 'energy often starts to rise',
                      'most energetic', 'confidence often peaks',
                      'calms the body before', 'suit lower-energy',
                      'many feel more sociable') if c in low]
ok(not claims, 'NO PHASE CLAIMS the research does not back', claims)
ok('best-studied' in low and 'reduce period pain' in low and
   'low iron is common' in low,
   'THE WELL-SUPPORTED ONES STAY PLAIN: heat, exercise for pain, iron')
ok('evidence is mixed' in low and 'some evidence' in low,
   '  and the weaker ones say how strong the evidence is')
ok('little difference across the cycle' in low,
   '  the harder-workout idea says what the research found')
bad = [w for w in ('calorie', 'kcal', 'diet', 'must', 'should', 'cure',
                   'treat', '!') if w in low]
ok(not bad, 'still no diets, musts, cures or exclamation marks', bad)
ok(sorted(PH.ALL_KEYS) == sorted({i[0] for p in PH.BOARD.values()
                                  for g in p.values() for i in g}) and
   len(PH.ALL_KEYS) == 50, 'every idea kept its key (40), plus 10 for '
   'perimenopause',
   len(PH.ALL_KEYS))
ga = ' '.join(h['a'] for h in G.HOWTO if 'cycle' in h['q'].lower())
ok('energy often rises' not in ga and 'vary a lot' in ga,
   'the guide answers say the same')

import datetime as dt                                       # noqa: E402
from wellness import cycle as CYC                           # noqa: E402
ok(len(CYC.SYMPTOMS) == 22 and len(CYC.PERI_SYMPTOMS) == 6 and
   len({k for k, _n in CYC.SYMPTOMS + CYC.PERI_SYMPTOMS}) == 28 and
   'mood_swings' in CYC.SYMPTOM_NAMES and 'pelvic_pain' in CYC.SYMPTOM_NAMES,
   'MORE SYMPTOMS (05:48): 22 for everyone, 6 more in perimenopause')
ok(all(CYC._noun(n)[1] in ('is', 'are') for _k, n in
       CYC.SYMPTOMS + CYC.PERI_SYMPTOMS) and
   CYC._noun('Mood swings') == ('Mood swings', 'are'),
   '  and each reads well in a Patterns sentence')
ok(('perimenopause', 'In perimenopause') in CYC.MODES and
   'hot_flush' in CYC.SYMPTOM_NAMES,
   'PERIMENOPAUSE: a mode of its own, with its symptoms')
Dd = dt.date
pdays = {}
for st in (Dd(2026, 6, 1), Dd(2026, 7, 10), Dd(2026, 8, 2),
           Dd(2026, 9, 15)):
    for k in range(4):
        pdays[(st + dt.timedelta(days=k)).isoformat()] = {'flow': 'medium'}
ps_ = dict(CYC.DEFAULT_SETTINGS, mode='perimenopause')
sp = CYC.summary(pdays, Dd(2026, 11, 20), ps_)
sn = CYC.summary(pdays, Dd(2026, 11, 20), dict(CYC.DEFAULT_SETTINGS))
ok(sp['soft'] and sp['state'] != 'late' and sn['state'] == 'late',
   '  NEVER "LATE" in perimenopause (it would be in the usual mode)')
ok((sp['window'][1] - sp['window'][0]).days >= 2 * CYC.PERI_SPREAD,
   '  the expected window is wider', sp['window'])
ok(CYC.summary(pdays, Dd(2026, 10, 1), dict(ps_, fertile=True))['fertile']
   is None, '  and no fertile estimate')
ok(CYC.headline(sp)[0].startswith('Perhaps around') and
   'rough guide' in CYC.headline(sp)[1], '  "Perhaps around ... a rough guide"')
pc = PH.place(sp, 'today')
ok(pc['phase'] is None and pc.get('peri') and pc['title'] and
   'perimenopause' in pc['why_none'],
   '  no phases - its own lines instead')
ok([g for g, _n, _i in PH.board('peri')] == ['do', 'move', 'eat'] and
   any(i['key'] == 'p_strength' for _g, _n, items in PH.board('peri')
       for i in items), '  and ideas for these years: strength, bones, cool')
from wellness import insights as INS                        # noqa: E402
T = Dd(2026, 11, 1)
mood = {T - dt.timedelta(days=i): (4 if i % 2 else 3) for i in range(20)}
calm = {T - dt.timedelta(days=i) for i in range(20) if i % 2}
f = INS.compare(mood, calm, 'you did Calm')
ok(f and f['with'] == 4.0 and f['without'] == 3.0 and
   'On days you did Calm, your mood averaged 4.0, against 3.0' in f['words'],
   'INSIGHTS: mood on Calm days against other days')
ok(INS.compare({T: 4, T - dt.timedelta(days=1): 3}, {T}, 'x') is None,
   '  nothing said without enough days on each side')
ok(INS.compare({T - dt.timedelta(days=i): 3 for i in range(10)},
               {T - dt.timedelta(days=i) for i in range(5)}, 'x') is None,
   '  nor when there is no real difference')
rows = INS.weekly(T, mood, {T: (2, 4)}, {T: 600}, {T})
ok(len(rows) == 8 and rows[-1]['habits_pct'] == 50 and
   rows[-1]['calm_min'] == 10 and rows[-1]['workouts'] == 1,
   '  eight weeks, oldest first, with habits, Calm, workouts and mood')
ok([n for n, _m, _c in INS.mood_by_phase(
    {Dd(2026, 10, 1) + dt.timedelta(days=i): 3 for i in range(28)},
    [Dd(2026, 10, 1)], 28, 5)] == ['Menstrual phase', 'Follicular phase',
                                   'Ovulation phase', 'Luteal phase'],
   '  mood by cycle phase, with enough days in each')
from wellness import help as HELP2                          # noqa: E402
ok(HELP2.for_url_name('insights') is not None, '  Insights has its help')

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
            a = User.objects.create_user('w14_a', 'w14a@example.com', 'x')
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
            ok('Research shows people vary a lot' in t and
               'data-board-note' in t,
               'THE CYCLE PAGE shows the note above the ideas')
            ins = ca.get('/wellness/insights/').content.decode()
            ok('Your last eight weeks' in ins and 'w-ins-bars' in ins and
               '<h3 class="w-sheet-title">Insights</h3>' in ins,
               'INSIGHTS opens, with its charts and its help')
            ok('href="/wellness/insights/"' in ca.get('/wellness/').content
               .decode(), '  reached from Today')
            t = ca.get('/wellness/cycle/?when=tomorrow').content.decode()
            ok('if you feel strong' in t.lower() and
               'at their best' not in t,
               'tomorrow (ovulation): "a harder workout, if you feel strong"')
            ca.post('/wellness/cycle/settings/', {'mode': 'perimenopause'})
            t = ca.get('/wellness/cycle/').content.decode()
            ok('In perimenopause cycles change a lot' in t and
               'Strength training' in t and 'Follicular phase' not in t,
               'PERIMENOPAUSE on the cycle page: no phase, its own ideas')
            t = ca.get('/wellness/cycle/log/').content.decode()
            ok('Hot flushes' in t and 'Night sweats' in t,
               '  and its symptoms in Log today')
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
ok("Text = 'DISCLAIMER = ('" in gate, '  with a sentinel on the wording')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
