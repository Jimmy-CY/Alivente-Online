# -*- coding: utf-8 -*-
"""test_wellness_nineteen.py - round WL-15, 2 Nov 2026.

RELEASE 62 - WELLNESS: A LITTLE JOY - SOUNDS, MOVEMENT, SAVED.
Demetri, 19:36: "When someone ticks off a Habit on the today page, it
should do some sort of sound and something visual and/or a vibration?...
when somebody achieves a badge, it needs to make a sound and short
something more graphic or animated... when somebody hits Add or Save, it
needs to let them know that they have pressed the button." 19:39: all
three as suggested; sounds on by default.

    - A tick: the tick draws in, the circle pulses, a soft two-note ding
      and a 12 ms tap. The last habit of the day: three rising notes and
      the ring glows. Unticking is silent.
    - A badge: a medallion rises into the middle with a short burst of
      sage and sand behind it and a warm chime - straight after the tick
      that earned it, or once when Today next opens. Nice closes it.
    - Add and Save: the button presses in, shows "Saving..." with a
      spinner and cannot be tapped twice; the next screen says "Saved"
      for two seconds - only if the form really went through.
    - Settings > Sounds and vibration, on by default. Reduce motion: a
      simple fade. Sounds are made on the phone, like the Calm bells.
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

SUFFIX = '.bak_wellness19'
ME = 'test_wellness_nineteen.py'
PATCHER = 'apply_wellness_nineteen.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')
EDITED = [J(APP, 'views.py'), J(APP, 'help.py'), J(APP, 'guide.py'),
          J(APP, 'templatetags', 'wellness_modules.py'),
          J(APP, 'assets', 'wellness.js'), J(APP, 'assets', 'wellness.css'),
          J(WT, 'base.html'), J(WT, 'today.html'), J(WT, 'settings.html')]

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
js = read(J(APP, 'assets', 'wellness.js'))
ok('var FX = (function ()' in js and 'tick: function ()' in js and
   'allDone: function ()' in js and 'badge: function ()' in js,
   'THE SOUNDS: a tick, the whole day, a badge - made on the phone')
ok("getAttribute('data-fx') !== 'off'" in js and 'navigator.vibrate' in js,
   '  they follow Settings, and vibrate where the phone can')
ok("prefers-reduced-motion: reduce" in js and "'w-celebrate' + (FX.still()"
   in js, '  and reduce motion keeps it still')
i_tick = js.index('if (!was) {\n      var all')
ok('FX.allDone()' in js[i_tick:i_tick + 600] and
   'FX.tick()' in js[i_tick:i_tick + 600],
   'A TICK: the ding - or, the last of the day, the chime and the glow')
ok('if (res.badge)' in js and 'celebrate(res.badge' in js,
   'A BADGE earned by a tick is celebrated on the spot')
ok("querySelector('[data-new-badge]')" in js and 'w-badge-shown-' in js,
   '  and one earned since last time, once, when Today opens')
ok(js.rindex("document.addEventListener('submit'") >
   js.index("form.matches('[data-tick]')"),
   'SAVING...: the busy-button listener is registered last')
ok('e.defaultPrevented' in js and "'Saving...'" in js and
   "getAttribute('data-busy') === '1'" in js,
   '  leaves forms the script handles alone; one tap only')
ok('redirectCount' in js and "'w-saved'" in js,
   'SAVED on the next screen - only after a real redirect')
css = read(J(APP, 'assets', 'wellness.css'))
ok('.w-toast' in css and '.w-celebrate' in css and '.w-btn.is-busy' in css
   and '.w-btn:active' in css and '@keyframes w-draw' in css,
   'THE STYLES: toast, celebration, busy and pressed buttons, the tick')
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px')
base = read(J(WT, 'base.html'))
ok('data-fx="{% fx_state %}"' in base, 'THE PAGE says whether sounds are on')
v = re.findall(r'\?v=([\w-]+)', base)
ok(len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in read(J(APP, 'views.py'))
   and v[0] != 'wl16-1', 'the asset version moved together (%s)' % v[0])
st = read(J(WT, 'settings.html'))
ok('name="sounds"' in st and 'Sounds and vibration' in st,
   'SETTINGS: Sounds and vibration')
ok('data-badge-key="{{ new_badge.key }}"' in read(J(WT, 'today.html')),
   'TODAY: the new badge card carries what the celebration shows')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), 'CONTROL: %s has its backup'
       % os.path.relpath(p, ROOT))
ok('var FX' not in was(J(APP, 'assets', 'wellness.js')),
   'CONTROL: before this round a tick made no sound')

# ==========================================================================
head('2. THE WORDS')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok('soft ding' in ' '.join(HELP.for_url_name('today')['steps']) and
   'Sounds and vibration' in ' '.join(HELP.for_url_name('settings')['steps']),
   'HELP: Today and Settings explain the sounds')
q = [h for h in G.HOWTO if h['q'] == 'Can I turn the sounds off?']
ok(q and q[0]['topic'] == 'setup', '  and "Can I turn the sounds off?" '
   'sits under Getting set up')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile, Habit
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
            a = User.objects.create_user('w19_a', 'w19a@example.com', 'x')
            a.user_permissions.add(perm)
            prof = WellnessProfile.objects.create(user=a, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            t = ca.get('/wellness/').content.decode()
            ok('data-fx="on"' in t, 'SOUNDS ON BY DEFAULT')
            hb = Habit.objects.create(user=a, name='Water', kind='yes_no',
                                      schedule='daily',
                                      started_on=timezone.localdate())
            r = ca.post('/wellness/habits/%d/check/' % hb.pk,
                        {'op': 'toggle'}, HTTP_X_REQUESTED_WITH='fetch')
            res = json.loads(r.content)
            ok(res['done'] and res['badge'] and res['badge']['name'] and
               res['badges_seen'] == '/wellness/badges/seen/',
               'A FIRST TICK earns a badge - and the answer carries it: %s'
               % (res.get('badge') or {}).get('name'))
            ca.post(res['badges_seen'])
            r = ca.post('/wellness/habits/%d/check/' % hb.pk,
                        {'op': 'toggle'}, HTTP_X_REQUESTED_WITH='fetch')
            ok(json.loads(r.content)['badge'] is None,
               '  an untick celebrates nothing')
            ca.post('/wellness/settings/', {'claude_line': '1'})
            prof.refresh_from_db()
            t = ca.get('/wellness/').content.decode()
            ok(prof.prefs.get('sounds_off') is True and 'data-fx="off"' in t,
               'SETTINGS: unticked and saved - sounds off on every page')
            ca.post('/wellness/settings/', {'claude_line': '1', 'sounds': '1'})
            ok('data-fx="on"' in ca.get('/wellness/').content.decode(),
               '  ticked - back on')
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
ok("Text = 'def fx_state('" in gate, '  with a sentinel on the switch')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
