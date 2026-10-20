# -*- coding: utf-8 -*-
"""test_week_click.py - round WC-1, 19 Oct 2026.

RELEASE 4, PUSH 2. A DAY IS A DAY IN EVERY VIEW.

Demetri: "In the week view ... I am forced to click on the '+' button
to add a recipe. Why does this change from the month view?"

THE CLAIM THAT MATTERS, and the reason this suite exists at all:
clicking a day opens the picker in BOTH views, and clicking a meal
opens the picker in NEITHER.

That comparison is the whole round. MV-2 gave the month cell the
click; MV-3 gave the week column a button an hour later; both suites
passed, because each judged its own view. **No suite was asking
whether the same action behaves the same way in two places** - and
nothing in the gate does, because the gate judges rounds, not pairs
of them.

So section 3 is a 2x2, driven in a browser:

                  click the day        click a meal
    Month         picker opens         picker does NOT
    Week          picker opens         picker does NOT

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Both views open the picker from the day itself,
      with the same call; the week column asks the same permission
      the month cell does; and the + survives.

  2   THE CONTROL. Re-asked of the pre-round file, where the week
      column is not a target.

  3   THE 2x2, driven.

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

SUFFIX = '.bak_weekclick'
ME = 'test_week_click.py'
PATCHER = 'apply_week_click.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'WC-1, 19 Oct 2026'

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
    t = T.code_only(bundle[TPL])
    c = {}
    month = re.search(
        r'class="month-cell[^>]*?onclick="(openPicker\([^"]*\))', t, re.S)
    week = re.search(
        r'class="week-col-body"[^>]*?onclick="(openPicker\([^"]*\))',
        t, re.S)
    c['the month cell opens the picker'] = bool(month)
    c['AND SO DOES THE WEEK COLUMN - the finding, in one line'] = (
        bool(week))
    # THE SAME ERRAND, not merely the same gesture. Two views calling
    # different functions that both happen to show a dialog would look
    # identical and drift apart on the next round.
    c['and both call the same function'] = (
        bool(month) and bool(week)
        and month.group(1).split('(')[0] == week.group(1).split('(')[0])
    # ANCHORED: asked of the week body's own attributes, not of the
    # file. A page having perms and THIS element asking them are
    # different facts.
    _body = t.split('class="week-col-body"', 1)
    c['the week column asks the same permission the month cell does'] = (
        len(_body) > 1
        and 'perms.auth.can_edit_recipes' in _body[1][:400])
    c['it is reachable by a keyboard'] = (
        len(_body) > 1 and 'tabindex="0"' in _body[1][:400])
    c['and says what it will do'] = (
        len(_body) > 1 and 'aria-label=' in _body[1][:400])
    # THE + SURVIVES - kept on purpose; without hover it is the only
    # affordance on a touch screen.
    c['the + is still there'] = ('week-col-add' in t)
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
ok(held == ['the month cell opens the picker', 'the + is still there'],
   'before this round, the month cell opened the picker and the week '
   'column did not - which is exactly the finding',
   'what held: %r' % (held,))

OLD = T.code_only(BEFORE[TPL])
ok(re.search(r'class="week-col-body"[^>]*onclick=', OLD) is None,
   'CONTROL: the week column really was not a target')
ok('week-col-add' in OLD,
   'CONTROL: and the + was the only way in')


# ==========================================================================
head('3. THE 2x2, DRIVEN')
# ==========================================================================
page = {}
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
    u = User.objects.create_user(username='wc1', password='x',
                                 email='wc1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    MealEntry.objects.create(date=dt.date(2026, 10, 21), recipe=r,
                             servings=4, created_by=u)
    cl = Client()
    cl.force_login(u)
    for view in ('month', 'week'):
        resp = cl.get('/meal_plans/', {'view': view,
                                       'date': '2026-10-19'})
        if resp.status_code == 200:
            page[view] = resp.content.decode('utf-8')
except Exception as e:
    skip('the driven checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not page:
    skip('the 2x2', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        WATCH = """() => { window.__picker = false;
            const o = window.openPicker;
            window.openPicker = function () { window.__picker = true;
                return o ? o.apply(this, arguments) : undefined; }; }"""
        DAY_SEL = {'month': '.month-cell[role="button"]',
                   'week': '.week-col-body[role="button"]'}
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            grid = {}
            for view, html in page.items():
                # ---- clicking the DAY
                pg = br.new_page(viewport={'width': 1200, 'height': 950})
                pg.set_content(html, wait_until='load')
                pg.evaluate(WATCH)
                n = pg.evaluate("(s) => document.querySelectorAll(s).length",
                                DAY_SEL[view])
                ok(n > 0, '%s: there are %d day targets' % (view, n))
                if n:
                    # A DAY WITH NO MEAL IN IT, so the click cannot land
                    # on a chip and answer the other question by
                    # accident.
                    pg.evaluate(
                        """(s) => { const e = Array.from(
                             document.querySelectorAll(s)).find(
                               x => !x.querySelector('[data-chip]'));
                           if (e) { e.click(); } }""", DAY_SEL[view])
                    pg.wait_for_timeout(300)
                grid[(view, 'day')] = pg.evaluate(
                    "() => !!window.__picker")
                pg.close()

                # ---- clicking a MEAL
                pg = br.new_page(viewport={'width': 1200, 'height': 950})
                pg.set_content(html, wait_until='load')
                pg.evaluate(WATCH)
                has_chip = pg.evaluate(
                    "() => document.querySelectorAll('[data-chip]').length")
                if has_chip:
                    pg.click('[data-chip]')
                    pg.wait_for_timeout(300)
                grid[(view, 'meal')] = pg.evaluate(
                    "() => !!window.__picker")
                pg.close()
            br.close()

        print('')
        print('  %-8s %-18s %s' % ('', 'click the day', 'click a meal'))
        for view in page:
            print('  %-8s %-18s %s'
                  % (view,
                     'picker opens' if grid[(view, 'day')] else 'NOTHING',
                     'picker opens' if grid[(view, 'meal')]
                     else 'picker does not'))
        print('')

        for view in page:
            ok(grid[(view, 'day')],
               '%s: clicking a day opens the picker' % view)
            ok(not grid[(view, 'meal')],
               '%s: and clicking a meal does not' % view)
        ok(grid.get(('month', 'day')) == grid.get(('week', 'day')),
           'THE FINDING: Month and Week now answer the same way',
           'month=%r week=%r' % (grid.get(('month', 'day')),
                                 grid.get(('week', 'day'))))


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
# AFTER WHAT IT BUILDS ON, not "newest".
#
# This asserted ROUNDS[-1] == SUFFIX, which is true of a round
# delivered on its own and FALSE for seven of the eight in this push -
# only one of them can be last. Eight suites carried the same wrong
# claim, because each was written as though it would ship alone.
#
# The claim was reaching for something real: revert runs NEWEST FIRST,
# so a round must sit AFTER anything whose work it edits, or reverting
# the two in order restores the older round's text over the newer
# one. That is the 18 Oct bug and it cost a hand repair.
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_chipmenu']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
# RETIRED - DB-1, 20 Oct 2026. This asked whether the round sat in
# the last eight entries of the register, which was true while push 2
# was the newest thing in it and false as soon as anything shipped
# after it. It is the same mistake as the `ROUNDS[-1] == SUFFIX` it
# replaced: a claim about a POSITION in a growing list expires
# whatever number is in it, so re-pinning would only move the date.
# The dependency claim above is the real one and does not expire.
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once',
   alv_rounds.ROUNDS.count(SUFFIX))
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_week_click as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
