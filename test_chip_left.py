# -*- coding: utf-8 -*-
"""test_chip_left.py - round LO-1, 20 Oct 2026.

LEFTOVERS, FROM MONTH AND WEEK.

Demetri: "How can I add a Note or Leftovers from the month view or the
week view??" He could not: openLeftover was reachable only from the
Day card, and the chip menu offered View, Move to... and Remove.

THE CLAIM THAT NEEDS A BROWSER IS THE ONE ABOUT A NOTE.

add_leftover refuses a note in as many words - "A note has no
leftovers - there was nothing cooked" - so the item must not be
offered on a note chip. Whether it IS offered depends on a `hidden`
property set at open time, which no reading of the file can settle.
So section 3 opens the menu on a recipe chip and on a note chip and
asks each one what it is showing.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One item, inside the same permission as Move and
      Remove, calling the dialog MO-1 already built.

  2   THE CONTROL. Re-asked of the pre-round file, where the menu
      offered three things.

  3   DRIVEN: the menu on a recipe, and the menu on a note.

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

SUFFIX = '.bak_chipleft'
ME = 'test_chip_left.py'
PATCHER = 'apply_chip_left.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'LO-1, 20 Oct 2026'

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


def claims(bundle):
    code = T.code_only(bundle[TPL])
    js = T.code_only_js(bundle[TPL])
    c = {}
    # COUNTED AS AN ELEMENT. The patcher's own first gate counted two
    # here, the second being the JavaScript selector that finds it.
    c['LEFTOVERS IS ON THE CHIP MENU - the finding, in one line'] = (
        len(re.findall(r'<button[^>]*data-act="leftovers"', code)) == 1)
    c['and it calls the dialog MO-1 already built'] = (
        'openLeftover(chip.getAttribute' in js)
    c['with the day it was cooked on'] = (
        "openLeftover(chip.getAttribute('data-chip')" in js
        and "data-chip-date" in js)
    c['something hides it for a note'] = (
        'data-act="leftovers"' in js and 'hidden = !url' in js)
    # THE OTHER THREE ARE UNTOUCHED. A round that added an item and
    # lost one would pass everything above.
    c['View, Move and Remove are all still there'] = all(
        'data-act="%s"' % a in code for a in ('view', 'move', 'remove'))
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# IT SITS INSIDE THE SAME PERMISSION AS THE REST. View is offered to
# everybody; Move, Remove and this are not.
CODE = T.code_only(NOW[TPL])
menu = CODE[CODE.index('id="chipMenu"'):]
menu = menu[:menu.index('</div>')]
ok(menu.index('data-act="leftovers"') > menu.index('data-act="move"'),
   'and it sits after Move to..., inside the same permission guard')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
held = [m for m, got in claims(BEFORE).items() if got]
ok('LEFTOVERS IS ON THE CHIP MENU - the finding, in one line'
   not in held,
   'CONTROL: before this round the menu offered three things',
   'what held: %r' % (held,))
OLD = T.code_only(BEFORE[TPL])
old_menu = OLD[OLD.index('id="chipMenu"'):]
old_menu = old_menu[:old_menu.index('</div>')]
ok(len(re.findall(r'<button[^>]*data-act=', old_menu)) == 3,
   'CONTROL: exactly three, and now there are four',
   len(re.findall(r'<button[^>]*data-act=', old_menu)))
ok('function openLeftover(' in T.code_only_js(BEFORE[TPL]),
   'CONTROL: and openLeftover already existed - it was never '
   'missing, only unreachable from here')


# ==========================================================================
head('3. DRIVEN - A RECIPE CHIP, AND A NOTE CHIP')
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
    u = User.objects.create_user(username='lo1', password='x',
                                 email='lo1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    MealEntry.objects.create(date=dt.date(2026, 10, 20), recipe=r,
                             servings=4, created_by=u)
    # A NOTE, which is the chip this round must NOT offer leftovers on.
    MealEntry.objects.create(date=dt.date(2026, 10, 21),
                             note='Eating out', servings=2,
                             created_by=u)
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
    skip('the menu', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        SHOWN = """() => [...document.querySelectorAll(
            '#chipMenu .chip-menu-item')].filter(e => !e.hidden)
            .map(e => (e.getAttribute('data-act')))"""
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1400, 'height': 1000})
            pg.set_content(page, wait_until='load')
            seen = {}
            for kind, sel in (
                    ('a recipe', '[data-chip][data-chip-view]'),
                    ('a note', '[data-chip]:not([data-chip-view])')):
                n = pg.evaluate(
                    "(s) => document.querySelectorAll(s).length", sel)
                if not n:
                    seen[kind] = None
                    continue
                pg.evaluate("(s) => document.querySelector(s).click()",
                            sel)
                pg.wait_for_timeout(200)
                seen[kind] = pg.evaluate(SHOWN)
                pg.keyboard.press('Escape')
                pg.wait_for_timeout(100)
            br.close()

        print('')
        for kind in ('a recipe', 'a note'):
            print('  on %-9s %s' % (kind, seen.get(kind)))
        print('')

        if seen.get('a recipe') is None:
            skip('the recipe chip', 'none on the page')
        else:
            ok('leftovers' in seen['a recipe'],
               'THE FINDING: a recipe chip offers Leftovers',
               seen['a recipe'])
            ok(seen['a recipe'].count('leftovers') == 1,
               '  once', seen['a recipe'])
            for act in ('view', 'move', 'remove'):
                ok(act in seen['a recipe'],
                   '  and still offers %s' % act, seen['a recipe'])
        if seen.get('a note') is None:
            skip('the note chip', 'none on the page')
        else:
            ok('leftovers' not in seen['a note'],
               'AND A NOTE DOES NOT - add_leftover refuses one, so it '
               'is not offered rather than offered and refused',
               seen['a note'])
            ok('view' not in seen['a note'],
               '  nor View, which RD-2 already hid for the same reason',
               seen['a note'])
            ok('remove' in seen['a note'],
               '  but it can still be removed', seen['a note'])


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
for _dep in ['.bak_chipmenu']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose menu it adds to - so revert takes '
       'them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_chip_left as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
