# -*- coding: utf-8 -*-
"""test_wellness_seven.py - round WL-5, 31 Oct 2026.

RELEASE 50 - WELLNESS: THE COG. Demetri, 31 Oct 06:18: "these three
sections should not be under the question mark list. We should create
another little icon, the cog (for settings) and then put these three
sections in there."

    - A cog beside the ?, top right on every Wellness page, opens Settings.
    - Settings lists Your badges and the Cycle tracker, above reminders,
      the daily quote and the Monday email. The ? guide is help only.
    - And from the first morning of W-4c: the reminder job now says
      plainly when a key is missing on its service, and a recent login
      counts as using Wellness.
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

SUFFIX = '.bak_wellness7'
ME = 'test_wellness_seven.py'
PATCHER = 'apply_wellness_seven.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
CMD = J(APP, 'management', 'commands', 'wellness_reminders.py')
EDITED = [J(WT, 'base.html'), J(WT, 'guide.html'), J(WT, 'settings.html'),
          J(APP, 'assets', 'wellness.css'), J(APP, 'views.py'),
          J(APP, 'guide.py'), J(APP, 'daily_line.py'), CMD]

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
base = read(J(WT, 'base.html'))
top = base[base.index('<div class="w-top">'):base.index('{% block content %}')]
ok('<span class="w-top-icons">' in top and
   top.index("url 'wellness:settings'") < top.index("url 'wellness:guide'"),
   'THE COG: settings and then the ?, together in the top bar')
# WL-6 (Release 51) renamed the ? for what it now opens.
ok('aria-label="Settings"' in top and ('aria-label="Guide and help"' in top
                                       or 'aria-label="Help for this screen"'
                                       in top),
   '  each named for a screen reader')
ok('{% block top_left %}' in top and top.index('{% endblock %}') <
   top.index('w-top-icons'), '  outside the back-link block, so every page '
   'has them')
css = read(J(APP, 'assets', 'wellness.css'))
ok('.w-top-icons { margin-left: auto;' in css,
   '  pinned top right, with or without the back link')
guide = read(J(WT, 'guide.html'))
ok("wellness:badges" not in guide and "wellness:settings" not in guide and
   "url 'wellness:cycle'" not in guide,
   'THE ? IS HELP ONLY: badges, settings and the cycle tracker are gone '
   'from it')
ok('Show me the tips again' in guide and 'Back to Alivente' in guide,
   '  and it keeps the tips and the way back')
st = read(J(WT, 'settings.html'))
ok("url 'wellness:badges'" in st and "url 'wellness:cycle'" in st and
   st.index("wellness:badges") < st.index('data-push'),
   'SETTINGS lists Your badges and the Cycle tracker first')
ok("url 'wellness:today'" in st.split('{% endblock %}')[1] or
   "url 'wellness:today' %}\"><svg" in st,
   '  and its back link goes to Today, not the guide')
v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
# Later rounds move the version on (WL-6: wl8-1); the page and the
# service worker must always name the same one.
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl7-1)', v)
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
         and m != '0']
ok(not small, 'every control is still at least 44px', small)
dl = read(J(APP, 'daily_line.py'))
ok('ANTHROPIC_API_KEY is not set on this' in dl and 'def key_present' in dl,
   'THE FIRST MORNING: a missing Anthropic key is said plainly, and no '
   'try is spent')
ok('recent_login' in dl, '  a recent login counts as using Wellness')
cmd = read(CMD)
ok('WELLNESS_VAPID_PUBLIC and' in cmd,
   '  and a missing push key is named in the log')
# A {# #} comment only hides itself on ONE line. Two of this round's notes
# ran over two and showed on every page (found in the help-sheet
# screenshots, 31 Oct 07:58). Every Wellness template, then.
import glob as _g                                            # noqa: E402
multi = []
for _f in sorted(_g.glob(J(WT, '**', '*.html'), recursive=True)):
    for _n, _line in enumerate(read(_f).split('\n'), 1):
        if '{#' in _line and '#}' not in _line.split('{#', 1)[1]:
            multi.append('%s:%d' % (os.path.relpath(_f, ROOT), _n))
ok(not multi, 'NO NOTE SHOWS ON SCREEN: no {# comment runs over two lines '
   'in any Wellness template', multi)
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('w-top-icons' not in was(J(WT, 'base.html')),
   'CONTROL: before this round there was no cog')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
have_db = False
try:
    import django
    django.setup()
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile
    from wellness import daily_line as DL
    connection.ensure_connection()
    WellnessProfile.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2', 'no database, or migrate not run yet: %s'
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
            a = User.objects.create_user('w7_a', 'w7a@example.com', 'x')
            a.user_permissions.add(perm)
            WellnessProfile.objects.create(user=a, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            for page in ('/wellness/', '/wellness/habits/',
                         '/wellness/journal/', '/wellness/guide/'):
                t = ca.get(page).content.decode()
                ok('href="/wellness/settings/"' in t and
                   'href="/wellness/guide/"' in t,
                   'the cog and the ? on %s' % page)
            t = ca.get('/wellness/settings/').content.decode()
            ok('WL-5' not in t and '{#' not in t and
               'WL-5' not in ca.get('/wellness/').content.decode(),
               'and no note of ours is printed on a page')
            ok('href="/wellness/badges/"' in t and
               'href="/wellness/cycle/"' in t,
               'Settings opens with Your badges and the Cycle tracker')
            t = ca.get('/wellness/guide/').content.decode()
            ok('href="/wellness/badges/"' not in t, 'the guide does not')
            ok(a in [p.user for p in DL.due_people(timezone.localtime())],
               'someone who just logged in gets a line tonight, before '
               'opening Today')
            said = []
            _old = _dj.ANTHROPIC_API_KEY
            _dj.ANTHROPIC_API_KEY = None
            try:
                ok(DL.run(timezone.localtime(), write=said.append) == 0 and
                   said and 'ANTHROPIC_API_KEY is not set' in said[0],
                   'without the key the job says so')
                pa = WellnessProfile.objects.get(user=a)
                ok(not (pa.prefs or {}).get('daily_line_try'),
                   '  and spends none of the day\'s tries')
            finally:
                _dj.ANTHROPIC_API_KEY = _old
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'w-top-icons'" in gate, '  with a sentinel on the cog')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
