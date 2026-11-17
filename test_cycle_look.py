# -*- coding: utf-8 -*-
"""test_cycle_look.py - round CY-5, 17 Nov 2026.

RELEASE 98 - WELLNESS: THE CYCLE TRACKER REDESIGN.
Demetri, 17 Nov: "I am happy with the Cycle Tracking changes, including
sex tracking (as suggested) and Ovulation Days (as suggested). The rest of
the Wellness app would keep our original colours." The approved canvas:
softer pinks on the cycle pages only, the cycle as a ring of days, the
calendar in shades of red by flow (a fifth, very heavy), icon tiles to
log a day, Cycle history as bars, the likely ovulation day and sex as
opt-ins.
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

SUFFIX = '.bak_cyclelook'
ME = 'test_cycle_look.py'
PATCHER = 'apply_cycle_look.py'
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
import datetime as dt                                       # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import cycle as C, cycle_icons as IC          # noqa: E402
D = dt.date
CYCLE_PAGES = ('cycle.html', 'cycle_intro.html', 'cycle_log.html',
               'cycle_patterns.html', 'cycle_settings.html')

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
css = read(J(APP, 'assets', 'wellness.css'))
for name, hexv in (('blush', '#FFF6F7'), ('rose', '#C2185B'),
                   ('spotting', '#F6C9D0'), ('light', '#F08A9B'),
                   ('medium', '#E04F68'), ('heavy', '#B4233D'),
                   ('very heavy', '#7E1328'), ('fertile', '#5AA9C8'),
                   ('ovulation', '#1F5F8B'), ('PMS', '#B9A3D9'),
                   ('expected', '#F3B6C2')):
    ok(hexv in css, 'THE PALETTE: %s %s' % (name, hexv))
ok('body:has(.cy-page) {' in css and '--w-sage-deep: var(--cy-rose);' in css,
   'THE PINKS ARE ONLY WHERE A PAGE ASKS: body:has(.cy-page)')
_root = css[:css.index('}')]
ok('--w-sage-deep: #4F7A5E;' in _root and '--w-bg: #F7F5F0;' in _root,
   '  the rest of Wellness keeps its sage and off-white (Demetri, 17 Nov)')
for t in CYCLE_PAGES:
    ok('<span class="cy-page" hidden></span>' in read(J(WT, t)),
       '  %s turns the pinks on' % t)
others = [f for f in os.listdir(WT) if f.endswith('.html') and
          f not in CYCLE_PAGES and 'cy-page' in read(J(WT, f))]
ok(not others, '  and no other Wellness page does', others)
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css)
         if int(m) < 44 and m != '0']
ok(not small, 'every control still at least 44px', small)
base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
ok(vv and len(set(vv)) == 1 and vv[0] != 'wl25-1' and
   ("SW_VERSION = '%s'" % vv[0]) in read(J(APP, 'views.py')),
   'THE PHONE APP FETCHES THE NEW LOOK: the version moved', vv)
names = [k for k, _n in C.SYMPTOMS + C.PERI_SYMPTOMS + C.MOODS + C.SEX +
         C.DISCHARGE]
plain = [k for k in names if k not in IC.ICONS]
ok(not plain, 'EVERY TILE HAS ITS OWN DRAWING (%d)' % len(names), plain)
ok(all(IC.icon(k, f) != IC.ICONS['dot'] for f, opts in
       (('energy', C.ENERGY), ('sleep', C.SLEEP)) for k, _n in opts),
   '  energy and sleep too')
ok(all('clipPath' in IC.drop(k) for k, _n in C.FLOWS),
   '  and the period tiles are drops, fuller for heavier')
lg = read(J(WT, 'cycle_log.html'))
ok("{% if 'sex' in track %}" in lg and 'name="sex"' in lg,
   'SEX: a group in Log a day, only when switched on')
ok('<i class="pms"></i>PMS days' in read(J(WT, 'cycle.html')),
   'the calendar still names the PMS days')
try:
    ok("'very_heavy'" not in was(J(APP, 'cycle.py')) and
       "'sex'" not in was(J(APP, 'cycle.py')),
       'CONTROL: before this round there was no very heavy and no sex')
except IOError as _e:
    skip('control', str(_e))

# ==========================================================================
head('2. THE RULES (no database)')
# ==========================================================================
ok(C.FLOWS[-1] == ('very_heavy', 'Very heavy') and 'very_heavy' in C.BLEED
   and C.FLOW_RANK['very_heavy'] == 4,
   'VERY HEAVY: a fifth flow, a bleeding day, the heaviest')
ok(('sex', 'Sex') in C.TRACK and C.DEFAULT_SETTINGS['ovulation'] is False,
   'sex is one of More to log; the ovulation day is off by default')


class Post(dict):
    def getlist(self, k):
        v = self.get(k, [])
        return v if isinstance(v, list) else [v]


e = C.clean_day(Post({'flow': 'very_heavy', 'sex': ['protected', 'bogus',
                                                    'high_drive']}))
ok(e == {'flow': 'very_heavy', 'sex': ['protected', 'high_drive']},
   'a day keeps very heavy and the sex ticks, and drops a made-up one', e)
ok(C.day_words({'flow': 'heavy', 'sym': ['cramps'], 'sleep': 'poor',
                'sex': ['protected']}) == 'Heavy flow · Cramps · Slept poorly',
   "A DAY'S SUMMARY never mentions sex")
days = {}
for a in (D(2026, 8, 1), D(2026, 8, 29), D(2026, 9, 26), D(2026, 10, 24)):
    for i, f in enumerate(['heavy', 'very_heavy', 'medium', 'light']):
        days[(a + dt.timedelta(days=i)).isoformat()] = {'flow': f}
days['2026-10-30'] = {'sym': ['headache']}
T = D(2026, 11, 2)
s0 = C.summary(days, T, dict(C.DEFAULT_SETTINGS, fertile=True))
s1 = C.summary(days, T, dict(C.DEFAULT_SETTINGS, fertile=True,
                             ovulation=True))
s2 = C.summary(days, T, dict(C.DEFAULT_SETTINGS, ovulation=True))
ok(s0['ovulation'] is None and s2['ovulation'] is None and
   s1['ovulation'] == D(2026, 11, 7),
   'OVULATION DAY: only with the fertile estimate AND its own switch - '
   '14 days before the next expected start', s1['ovulation'])
ok(s1['fertile'][0] < s1['ovulation'] < s1['fertile'][1],
   '  inside the fertile estimate')
w = C.wheel(s1, days, T)
cls = [b['cls'] for b in w['beads']]
ok(len(cls) == 28 and cls[:4] == ['f-heavy', 'f-very_heavy', 'f-medium',
                                  'f-light'],
   'THE RING: one bead a day, the period in its logged shades')
ok(cls[14] == 'ov' and cls.count('fert') == 6 and 'pred' in cls,
   '  the fertile days, the ovulation day and the expected period')
ok(w['big'] == '18 days' and w['small'] == 'until your next period' and
   w['line'] == 'Ovulation likely in 5 days',
   '  and in the middle: "18 days until your next period", "Ovulation '
   'likely in 5 days"', (w['big'], w['line']))
ok(len(w['marks']) == 5 and w['when'] == 'Today, Mon 2 Nov',
   '  a dot for each logged day; today written out')
ok(C.wheel(C.summary({}, T, C.DEFAULT_SETTINGS), {}, T) is None,
   '  no ring before anything is logged')
grid = C.month_grid(2026, 10, days, s1, T)
cell = {c['date']: c for wk in grid for c in wk}
ok(cell[D(2026, 10, 25)]['flow'] == 'very_heavy' and
   cell[D(2026, 10, 30)]['dots'] == ['body'],
   "THE CALENDAR: each day's flow, and a dot for what was logged")
grid = C.month_grid(2026, 11, days, s1, T)
ok([c['date'] for wk in grid for c in wk if c['ov']] == [D(2026, 11, 7)],
   '  the likely ovulation day marked')
hist = C.history(days, s1['cycles'], s1, fertile=True)
ok(len(hist) == 4 and hist[0]['label'].startswith('Now') and
   hist[1]['side'] == '28 days' and hist[1]['cells'][:2] ==
   ['f-heavy', 'f-very_heavy'] and 'ov' in hist[1]['cells'],
   'CYCLE HISTORY: newest first, every cycle a bar of its days')
st = C.stats(s1['cycles'])
ok(st['cycle'] == 28 and st['vary'] == 0 and st['vary_word'] == 'regular',
   '  three tiles: cycle, period, how much they vary', st)
rep = C.report(days, s1['cycles'], 6)
ok(rep['rows'][0]['heavy'] == 2 and
   rep['rows'][0]['heaviest_name'] == 'Very heavy',
   'THE DOCTOR REPORT counts very heavy days as heavy, by name')

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
    connection.ensure_connection()
    WellnessProfile.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

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
            u = User.objects.create_user('cy5a', 'cy5a@example.com', 'x')
            u.user_permissions.add(perm)
            WellnessProfile.objects.create(user=u, onboarded=True)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            c.post('/wellness/cycle/settings/', {'turn': 'on'})
            today = timezone.localdate()
            for back in (60, 31, 2):
                for i in range(4):
                    d = today - dt.timedelta(days=back - i)
                    if d <= today:
                        c.post('/wellness/cycle/log/', {
                            'date': d.isoformat(),
                            'flow': 'very_heavy' if i == 0 else 'medium',
                            'sym': ['cramps']})
            lg = c.get('/wellness/cycle/log/').content.decode()
            ok('value="very_heavy"' in lg and 'cy-tile' in lg and
               'name="sex"' not in lg,
               'LOG A DAY: icon tiles, very heavy, and no Sex until it is on')
            c.post('/wellness/cycle/settings/', {
                'mode': 'normal', 'ovulation': '1', 'track': ['sex']})
            _r, prefs, _d = C.load(u)
            ok(prefs['ovulation'] is False,
               '  the ovulation day cannot be on without the fertile estimate')
            c.post('/wellness/cycle/settings/', {
                'mode': 'normal', 'fertile': '1', 'ovulation': '1',
                'track': ['sex']})
            _r, prefs, _d = C.load(u)
            ok(prefs['ovulation'] is True and 'sex' in prefs['track'],
               '  with it, it is')
            lg = c.get('/wellness/cycle/log/').content.decode()
            ok('name="sex"' in lg and 'Only you' in lg,
               '  and once Sex is on, its tiles appear')
            d0 = today - dt.timedelta(days=60)
            c.post('/wellness/cycle/log/', {
                'date': d0.isoformat(), 'flow': 'very_heavy',
                'sym': ['cramps'], 'sex': ['unprotected']})
            _r, _p, dd = C.load(u)
            ok(dd[d0.isoformat()].get('sex') == ['unprotected'],
               '  what is ticked is kept, locked with the rest')
            h = c.get('/wellness/cycle/').content.decode()
            ok('data-cycle-ring' in h and 'class="cy-b f-very_heavy"' in h
               and '+ Log today' in h or 'Change today' in h,
               'THE OVERVIEW: the ring, in the period\'s shades')
            ok('f-very_heavy' in h.split('id="calendar"')[1],
               '  the calendar in shades of red')
            h = c.get('/wellness/cycle/?m=%s&d=%s' % (
                d0.strftime('%Y-%m'), d0.isoformat())).content.decode()
            box = h.split('data-day-summary')[1].split('</div>')[0] \
                if 'data-day-summary' in h else ''
            ok('Very heavy flow' in box and 'rotected' not in box,
               'A TAPPED DAY: its summary - and never the sex')
            h = c.get('/wellness/cycle/patterns/').content.decode()
            ok('data-cycle-history' in h and 'Cycle history' in h,
               'CYCLE HISTORY on the patterns page')
            h = c.get('/wellness/cycle/report/?n=6').content.decode()
            rows = h.split('<tbody')[1].split('</tbody>')[0] \
                if '<tbody' in h else h
            ok('Very heavy' in rows and 'rotected' not in rows,
               'THE DOCTOR REPORT: very heavy by name, never the sex')
            h = c.get('/wellness/').content.decode()
            ok('cy-page' not in h,
               'TODAY keeps the original colours')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. HELP AND REGISTERED')
# ==========================================================================
from wellness import help as HELP, guide as G               # noqa: E402
signs = ' '.join(w for _c, w in HELP.SCREENS['cycle']['signs'])
ok('very heavy' in signs and 'ovulation' in signs and 'PMS' in signs,
   'HELP: the colours, from spotting to very heavy, and ovulation')
ok(all(cv in css for cv, _w in HELP.SCREENS['cycle']['signs'] if cv),
   '  every swatch the help shows exists')
ok('Sex is only ever seen here' in ' '.join(
    HELP.SCREENS['cycle_log']['steps']) and
   'Cycle history' in ' '.join(HELP.SCREENS['cycle_patterns']['steps']),
   '  Log a day and Cycle history explained')
qs = ' '.join(h['q'] for h in G.HOWTO)
ok('What do the colours on the cycle pages mean?' in qs and
   'Can I see the likely ovulation day?' in qs and
   'Can I track sex, and who sees it?' in qs,
   'GUIDE: colours, the ovulation day, and sex')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
