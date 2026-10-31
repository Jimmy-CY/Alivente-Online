# -*- coding: utf-8 -*-
"""test_wellness_eight.py - round WL-6, 31 Oct 2026.

RELEASE 51 - WELLNESS: HELP FOR EACH SCREEN. Demetri, 31 Oct 07:55:
"There needs to be customised help per screen... keep this [the generic
help] in a General section. Then add a section per screen which is only
visible on that screen." 07:57: a slide-up sheet. 08:05, on the
screenshots: "The Help screens look great !! Go ahead and build."

    - The ? slides a sheet up over the screen: THIS SCREEN first (what it is
      for, the few things done there, what its colours mean), GENERAL
      second (the guide's questions, the same everywhere).
    - EVERY Wellness screen has its own entry. A new screen without one
      fails here, so none can ship without help.
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

SUFFIX = '.bak_wellness8'
ME = 'test_wellness_eight.py'
PATCHER = 'apply_wellness_eight.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(WT, 'base.html'), J(APP, 'assets', 'wellness.css'),
          J(APP, 'assets', 'wellness.js'), J(APP, 'views.py')]

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
ok(os.path.isfile(J(APP, 'help.py')) and
   os.path.isfile(J(APP, 'templatetags', 'wellness_help.py')),
   'wellness/help.py and its template tag are there')
base = read(J(WT, 'base.html'))
ok('<dialog class="w-sheet" data-help-sheet' in base,
   'THE SHEET: a dialog that slides up over the screen')
ok('data-help-open' in base and "href=\"{% url 'wellness:guide' %}\"" in base,
   '  opened by the ? - which still opens the guide page without script')
ok(base.index('data-help-tab="screen"') < base.index('data-help-tab="general"'),
   '  This screen first, General second')
ok('{% if hp.screen %}' in base and 'hp.general' in base,
   '  This screen only when the screen has its own help')
js = read(J(APP, 'assets', 'wellness.js'))
ok('sheet.showModal()' in js and "typeof sheet.showModal === 'function'" in js,
   'the script opens it, and only where the browser can')
ok('outside = e.clientY < r.top' in js,
   '  a tap outside closes it; a tap inside does not')
css = read(J(APP, 'assets', 'wellness.css'))
ok('.w-sheet[open]' in css and '.w-sheet::backdrop' in css,
   'it is styled as a sheet, with the screen dimmed behind')
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
ok(v == ['wl8-1', 'wl8-1'] and "SW_VERSION = 'wl8-1'" in views,
   'the asset version moved together (wl8-1)', v)
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
ok('data-help-sheet' not in was(J(WT, 'base.html')),
   'CONTROL: before this round the ? only opened the guide page')

# ==========================================================================
head('2. EVERY SCREEN HAS ITS HELP')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import help as HELP                           # noqa: E402
from wellness import urls as WU                             # noqa: E402
names = [u.name for u in WU.urlpatterns if u.name]
missing = [n for n in names if n not in HELP.NOT_SCREENS and
           HELP.for_url_name(n) is None]
ok(not missing, 'every Wellness screen has its own help (%d screens)'
   % len([n for n in names if n not in HELP.NOT_SCREENS]), missing)
stale = sorted((set(HELP.SCREENS) | set(HELP.ALIASES) | HELP.NOT_SCREENS)
               - set(names) - set(HELP.ALIASES.values()))
ok(not stale, '  and no help is kept for a screen that is gone', stale)
bad = [k for k, e in HELP.SCREENS.items()
       if not e.get('title') or not e.get('purpose') or
       not isinstance(e.get('steps'), list) or
       any(len(s.split()) > 40 for s in e['steps'])]
ok(not bad, 'each has a title, one line on what it is for, and short steps',
   bad)
tokens = set(re.findall(r'(--w-[\w-]+):', css))
swatches = sorted({sw for e in HELP.SCREENS.values()
                   for sw, _w in e.get('signs', []) if sw})
ok(all(sw in tokens for sw in swatches),
   'every colour a sign shows is a real Wellness colour',
   [sw for sw in swatches if sw not in tokens])
words = ' '.join(s for e in HELP.SCREENS.values() for s in
                 [e['purpose']] + e['steps'] + [w for _s, w in e['signs']])
ok('!' not in words and 'failed' not in words.lower() and
   'you missed' not in words.lower(),
   'kind words: no exclamation marks, no "failed", no "you missed"')

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
            a = User.objects.create_user('w8_a', 'w8a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            h = Habit.objects.create(user=a, name='Walk',
                                     started_on=timezone.localdate())
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            pages = {'/wellness/': 'Today',
                     '/wellness/habits/': 'Habits',
                     '/wellness/habits/%d/' % h.pk: 'A habit',
                     '/wellness/journal/': 'Journal',
                     '/wellness/body/': 'Body',
                     '/wellness/workouts/': 'Workouts',
                     '/wellness/settings/': 'Settings'}
            for url, title in pages.items():
                t = ca.get(url).content.decode()
                ok('data-help-sheet' in t and
                   '<h3 class="w-sheet-title">%s</h3>' % title in t,
                   '%s: the sheet, with its own "%s" help' % (url, title))
            t = ca.get('/wellness/body/').content.decode()
            ok('How do streaks work here?' in t and
               'Show me the tips again' in t,
               'General is there too, the same on every screen')
            ok('Tap a habit when it is done.' not in t,
               "  and Today's own help is not on the Body screen")
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
ok("Text = 'def for_url_name('" in gate, '  with a sentinel on the help')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
