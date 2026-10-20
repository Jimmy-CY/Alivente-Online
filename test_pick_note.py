# -*- coding: utf-8 -*-
"""test_pick_note.py - round NT-1, 20 Oct 2026.

A NOTE, FROM MONTH AND WEEK.

Demetri: "How can I add a Note or Leftovers from the month view or the
week view??" LO-1 answered the leftovers half. A note belongs to a DAY
rather than to a meal, so it goes in the picker - the dialog that adds
things to a day.

WHY SECTION 3 STUBS jQUERY RATHER THAN LOADING IT.

The hand-off is three steps and only the middle one is interesting:

    clear the dirty flag  so PS-1's reload does not arrive mid-way
    wait for hidden       so two modals are never open at once
    open the note         on the day the picker was holding

Loading real Bootstrap would prove the dialog animates. What needs
proving is the ORDER and the ARGUMENTS, so jQuery is replaced by a
recorder: it remembers which event was subscribed to and lets this
suite fire it by hand. The sequence is then observed rather than
assumed, and nothing depends on a CDN this sandbox cannot reach.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One button, a delegated handler, the flag carried
      and spent, and the wait before opening.

  2   THE CONTROL. Re-asked of the pre-round file.

  3   DRIVEN: press it, and watch what happens in what order.

  4   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_picknote'
ME = 'test_pick_note.py'
PATCHER = 'apply_pick_note.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'NT-1, 20 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

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
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def handoff(js):
    i = js.find("closest('#pickerNote')")
    return js[max(0, i - 400):i + 1800] if i >= 0 else ''


def claims(bundle):
    code = T.code_only(bundle[TPL])
    js = T.code_only_js(bundle[TPL])
    hand = handoff(js)
    c = {}
    # COUNTED AS AN ELEMENT, which is the lesson LO-1 paid an hour
    # earlier when a selector counted as a second button.
    c['THE PICKER OFFERS A NOTE - the finding, in one line'] = (
        len(re.findall(r'<button[^>]*id="pickerNote"', code)) == 1)
    # find(), NOT index(). The control section asks these of the
    # PRE-ROUND file, where the button does not exist - and index()
    # raises there, which turns a failure into a crash. A suite that
    # crashes blocks a push exactly as hard and says far less.
    _n, _p = code.find('id="pickerNote"'), code.find('id="pickerModal"')
    c['and it is in the picker, not somewhere else'] = (
        _n > 0 and _p > 0 and _n > _p)
    c['the hand-off waits for the picker to close'] = (
        "one('hidden.bs.modal'" in hand)
    c['it clears the flag that would reload mid-way'] = (
        'pickerDirty = false' in hand)
    c['AND SPENDS IT AFTERWARDS rather than dropping it'] = (
        'location.reload' in hand)
    c['it opens the note on the day the picker was holding'] = (
        'openNote(dateStr, dayName)' in hand)
    c['and asks for jQuery rather than assuming it'] = (
        'window.jQuery' in hand)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
held = [m for m, got in claims(BEFORE).items() if got]
ok('THE PICKER OFFERS A NOTE - the finding, in one line' not in held,
   'CONTROL: before this round the picker offered no note',
   'what held: %r' % (held,))
OLDJS = T.code_only_js(BEFORE[TPL])
ok('function openNote(' in OLDJS,
   'CONTROL: openNote already existed - it was never missing, only '
   'unreachable from here')
ok('pickerDirty' in OLDJS,
   'CONTROL: and PS-1\'s dirty flag was already there, which is what '
   'had to be carried across')


# ==========================================================================
head('3. DRIVEN - PRESS IT, AND WATCH THE ORDER')
# ==========================================================================
page = None
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    from django.conf import settings as dj
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='nt1', password='x',
                                 email='nt1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    MealEntry.objects.create(date=dt.date(2026, 10, 20), recipe=r,
                             servings=4, created_by=u)
    cl = Client()
    cl.force_login(u)
    resp = cl.get('/meal_plans/', {'view': 'week',
                                   'date': '2026-10-20'})
    if resp.status_code == 200:
        page = resp.content.decode('utf-8')
except Exception as e:
    skip('the driven checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if page is None:
    skip('the hand-off', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        # A RECORDER, NOT A LIBRARY. jQuery is a CDN this sandbox
        # cannot reach, and what matters is the order and the
        # arguments rather than the animation.
        STUB = """() => {
            window.__log = [];
            window.__fire = {};
            window.jQuery = function (sel) {
                var name = (sel && sel.id) ? ('#' + sel.id) : String(sel);
                return {
                    one: function (ev, fn) {
                        window.__log.push('one ' + name + ' ' + ev);
                        window.__fire[name + ' ' + ev] = fn;
                        return this;
                    },
                    modal: function (what) {
                        window.__log.push('modal ' + name + ' ' + what);
                        return this;
                    }
                };
            };
            window.openNote = function (d, n) {
                window.__log.push('openNote ' + d + ' | ' + n);
            };
            window.pickerDirty = true;   /* as if meals were added */
        }"""
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1400, 'height': 1000})
            pg.set_content(page, wait_until='load')
            pg.evaluate(STUB)
            pg.evaluate("""() => {
                document.getElementById('pickerDate').value = '2026-10-23';
                document.getElementById('pickerDayName').textContent =
                    'Friday 23';
                document.getElementById('pickerNote').click();
            }""")
            pg.wait_for_timeout(150)
            mid = pg.evaluate(
                "() => ({log: window.__log.slice(), "
                "dirty: window.pickerDirty})")
            # NOW LET THE PICKER FINISH CLOSING, which is what
            # Bootstrap would have done.
            after = pg.evaluate("""() => {
                const fn = window.__fire['#pickerModal hidden.bs.modal'];
                if (fn) { fn(); }
                return window.__log.slice();
            }""")
            br.close()

        print('')
        print('  on pressing the button:')
        for line in mid['log']:
            print('      %s' % line)
        print('  pickerDirty is now %s' % mid['dirty'])
        print('  once the picker has finished closing:')
        for line in after[len(mid['log']):]:
            print('      %s' % line)
        print('')

        ok(any('one #pickerModal hidden.bs.modal' in x
               for x in mid['log']),
           'it subscribes to the picker closing before hiding it',
           mid['log'])
        ok(any('modal #pickerModal hide' in x for x in mid['log']),
           '  and then hides it', mid['log'])
        ok(mid['dirty'] is False,
           'THE FLAG IS CLEARED FIRST, so PS-1 does not reload the '
           'page in the middle of the hand-off', mid['dirty'])
        ok(not any('openNote' in x for x in mid['log']),
           '  and the note is NOT opened yet - two modals at once is '
           'what the wait exists to prevent', mid['log'])
        opened = [x for x in after if x.startswith('openNote')]
        ok(bool(opened),
           'once it has closed, the note dialog opens', after)
        ok(opened and opened[0] == 'openNote 2026-10-23 | Friday 23',
           '  on the day the picker was holding, by name', opened)
        ok(any('#noteModal hidden.bs.modal' in x for x in after),
           'AND THE CARRIED FLAG IS SPENT - dismissing the note '
           'reloads, because meals were added before it', after)


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_pickerstays', '.bak_chipleft']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it builds on - so revert '
       'takes them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_pick_note as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
