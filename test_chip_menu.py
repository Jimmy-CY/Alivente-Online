# -*- coding: utf-8 -*-
"""test_chip_menu.py - round RD-2, 19 Oct 2026.

RELEASE 4, PUSH 2. A MEAL IN THE CALENDAR HAS A MENU.

Demetri's Q2, in his own words: "maybe if I hover over a recipe name
in the calendar, it gives me the option to view the recipe ... or to
remove the recipe" - and then, on 19 Oct, that Move should be in it.

THE CLAIM THAT MATTERS, and the one a reader should check first:
clicking a chip opens the menu and DOES NOT ALSO OPEN THE PICKER.

The month cell carries onclick="openPicker(...)" - that is Demetri's
own Q2 answer, "I want it to go straight to the Picker, when I click a
day" - and the chip sits inside it. The obvious implementation, one
delegated listener on `document` calling stopPropagation, does not
work: a bubbling event reaches the CELL first, so by the time anything
on document hears about it the picker is already open. Stopping
propagation there stops nothing.

So the listener is registered with capture. Section 4 clicks a real
chip in a real browser and asks whether the picker opened - and then
RE-SERVES THE SAME PAGE with the capture flag flipped to false and
asks again, because a design decision nobody can see fail is
indistinguishable from superstition.

    the page as shipped          menu opens, picker does not
    the same page, bubble        picker opens too

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The chips are buttons; one menu serves all of them;
      the listener captures; base learned .icon-move as a NAME on the
      CHANGE colour rather than a colour of its own; and the Move form
      carries the view PB-2 made compulsory.

  2   THE CONTROL. Every claim re-asked of the pre-round files, where
      the chips are spans and there is no way to move anything.

  3   THE MOVE, on a real database. Leftovers travel keeping the gap;
      a leftover cannot overtake its parent, backwards or onto the
      same day; forwards is allowed; and a grandchild travels too.

  4   DRIVEN IN A BROWSER, with the bubble-phase control beside it.

  5   Scope, registration and the gate.

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

SUFFIX = '.bak_chipmenu'
ME = 'test_chip_menu.py'
PATCHER = 'apply_chip_menu.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RD-2, 19 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEW, URLS, TPL, BASE)

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
    """Every source claim RD-2 makes, written once and asked twice."""
    v = T.python_code_only(bundle[VIEW], payloads=True)
    u = T.python_code_only(bundle[URLS], payloads=True)
    t = T.code_only(bundle[TPL])
    b = T.code_only(bundle[BASE])
    c = {}

    # ---- THE ENDPOINT
    c['there is an endpoint that moves a meal'] = (
        'def move_meal_entry(' in v)
    c['it is edit-tier, like remove beside it'] = bool(re.search(
        r"@permission_required\('auth\.can_edit_recipes',[^)]*\)\s*"
        r"\ndef move_meal_entry\(", v))
    c['and it is routed beside remove'] = (
        "name='move_meal_entry'" in u)
    c['a leftover is compared with its parent, so it cannot overtake '
      'it'] = ('leftover_of.date' in v)
    c['the move is one transaction - a half-moved chain strands '
      'leftovers on a date nobody chose'] = (
        'transaction.atomic' in v.split('def move_meal_entry')[-1]
        if 'def move_meal_entry' in v else False)
    c['and it writes one column, not whole rows'] = (
        "update_fields=['date']" in v)

    # ---- THE CHIPS ARE CONTROLS
    #
    # ASKED AS A SPAN, not as an absence of `button`. A page HAVING
    # buttons and THE CHIP being one are different facts.
    c['the month chip is a button, not a span'] = (
        bool(t) and not re.search(r'<span class="month-chip', t))
    c['and so is the week chip'] = (
        bool(t) and not re.search(r'<span class="week-chip', t))
    c['each carries its entry, its name and its date'] = (
        'data-chip=' in t and 'data-chip-name=' in t and
        'data-chip-date=' in t)
    c['and announces that it opens a menu'] = (
        t.count('aria-haspopup="menu"') >= 2)

    # ---- ONE MENU
    c['one menu serves every chip - thirty-five cells times three '
      'meals is a hundred of them otherwise'] = (
        t.count('id="chipMenu"') == 1)

    # ---- AND IT CAPTURES
    c['the click listener is registered with capture, because the '
      'month cell opens the picker and the chip is inside it'] = (
        '}, true);' in t)

    # ---- THE DAY CARD KEEPS BUTTONS, AND GAINS ONE
    c['the Day card gains a Move button rather than the menu'] = (
        'data-move=' in t)
    c['on the house icon class'] = ('icon-action-btn icon-move' in t)

    # ---- BASE OWNS THE NAME
    c['base learned .icon-move'] = ('.icon-move' in b)
    c['as a NAME on the CHANGE colour, not a colour of its own - a '
      'class carries one picture, and .icon-leftover wears fa-redo'] = (
        '.icon-move' in b and
        'var(--alv-edit)' in b.split('.icon-move')[1][:200])

    # ---- AND PB-2'S RULE HOLDS FOR THE FORM ADDED AFTER IT
    move_form = t.split("action=\"{% url 'move_meal_entry' %}\"", 1)
    c['the Move form carries the view, which PB-2 made the rule'] = (
        len(move_form) > 1 and 'name="view"' in move_form[1][:600])

    # ---- NO LITERAL COLOUR
    #
    # ANCHORED TO ITS SUBJECT. An absence is trivially true of a file
    # that has no .chip-menu in it at all, so the pre-round control
    # reported this claim as "already held" - which is the control
    # working, on the suite rather than on the tree. THIRD TIME in this
    # push: RD-1 had three of these. A claim that something is not
    # there has to establish that the thing it is talking about IS.
    c['no literal hex colour in the markup this round added'] = (
        '.chip-menu {' in t and
        not re.search(r'\.chip-menu[^}]*#[0-9a-fA-F]{3}', t))

    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL - every claim re-asked of the pre-round files')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
WAS = claims(BEFORE)
held = [m for m, got in WAS.items() if got]
ok(not held,
   'not one of the %d claims held before this round ran' % len(WAS),
   'these held already: %r' % (held[:4],))

OLD_T = T.code_only(BEFORE[TPL])
ok(re.search(r'<span class="month-chip', OLD_T) is not None,
   'CONTROL: the month chip really was a span')
ok(re.search(r'<span class="week-chip', OLD_T) is not None,
   'CONTROL: and so was the week chip')
ok('openPicker(' in OLD_T,
   'CONTROL: and the cell around it already opened the picker, which '
   'is the whole reason the capture phase is needed')
ok('def move_meal_entry(' not in
   T.python_code_only(BEFORE[VIEW], payloads=True),
   'CONTROL: and nothing could move a meal at all')


# ==========================================================================
head('3. THE MOVE, ON A REAL DATABASE')
# ==========================================================================
django_up = False
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    from django.conf import settings as dj_settings
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + \
        ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    dj_settings.DEBUG = True
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

page_html = None
if django_up:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.urls import reverse
    from pages.models import MealEntry, Recipe

    u = User.objects.create_user(username='rd2', password='x',
                                 email='rd2@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)
    recipe = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    MON = dt.date(2026, 10, 19)

    def chain(*offsets):
        """A parent on Monday and a leftover at each offset given."""
        MealEntry.objects.all().delete()
        parent = MealEntry.objects.create(date=MON, recipe=recipe,
                                          servings=4, created_by=u)
        kids = [MealEntry.objects.create(
            date=MON + dt.timedelta(days=d), recipe=recipe, servings=2,
            leftover_of=parent, created_by=u) for d in offsets]
        return parent, kids

    def move(entry, when, view='week'):
        return cl.post(reverse('move_meal_entry'),
                       {'meal_entry_id': entry.meal_entry_id,
                        'date': when, 'view': view})

    # ---- RULE 1: LEFTOVERS TRAVEL, KEEPING THE GAP
    parent, kids = chain(1, 3)
    move(parent, '2026-10-21')
    parent.refresh_from_db()
    for k in kids:
        k.refresh_from_db()
    ok(parent.date == dt.date(2026, 10, 21),
       'the parent moved to the day it was sent to',
       'landed on %s' % parent.date)
    ok([(k.date - parent.date).days for k in kids] == [1, 3],
       'and its leftovers travelled with it, keeping the gap',
       'gaps are %r' % [(k.date - parent.date).days for k in kids])

    # ---- RULE 2: A LEFTOVER CANNOT OVERTAKE ITS PARENT
    parent, kids = chain(1)
    move(kids[0], '2026-10-18')
    kids[0].refresh_from_db()
    ok(kids[0].date == MON + dt.timedelta(days=1),
       'a leftover cannot be moved BEFORE the meal it comes from',
       'it moved to %s' % kids[0].date)

    parent, kids = chain(1)
    move(kids[0], MON.strftime('%Y-%m-%d'))
    kids[0].refresh_from_db()
    ok(kids[0].date == MON + dt.timedelta(days=1),
       'nor ONTO the same day - leftovers of a meal cooked that '
       'evening are not leftovers yet',
       'it moved to %s' % kids[0].date)

    parent, kids = chain(1)
    move(kids[0], '2026-10-23')
    kids[0].refresh_from_db()
    ok(kids[0].date == dt.date(2026, 10, 23),
       'CONTROL: but forwards is allowed, so the rule is a rule and '
       'not a freeze', 'it is on %s' % kids[0].date)

    # ---- RULE 3: THE WHOLE CHAIN
    MealEntry.objects.all().delete()
    p = MealEntry.objects.create(date=MON, recipe=recipe, servings=4,
                                 created_by=u)
    c1 = MealEntry.objects.create(date=MON + dt.timedelta(days=1),
                                  recipe=recipe, servings=2,
                                  leftover_of=p, created_by=u)
    c2 = MealEntry.objects.create(date=MON + dt.timedelta(days=2),
                                  recipe=recipe, servings=1,
                                  leftover_of=c1, created_by=u)
    move(p, '2026-10-26')
    for e in (p, c1, c2):
        e.refresh_from_db()
    ok((p.date, c1.date, c2.date) == (dt.date(2026, 10, 26),
                                      dt.date(2026, 10, 27),
                                      dt.date(2026, 10, 28)),
       'a leftover OF a leftover travels too - nothing builds one '
       'today, but leftover_of is a self-FK and the model allows it',
       'landed on %s, %s, %s' % (p.date, c1.date, c2.date))

    # ---- AND A DATE NOBODY CAN READ IS REFUSED, NOT GUESSED
    parent, kids = chain()
    move(parent, 'the day after tomorrow')
    parent.refresh_from_db()
    ok(parent.date == MON,
       'a date nobody can read moves nothing', 'it is on %s' % parent.date)

    # ---- AND THE VIEW COMES BACK, because PB-2 is the rule now
    parent, kids = chain()
    resp = move(parent, '2026-10-22', view='day')
    ok('view=day' in (resp.get('Location') or ''),
       'and the move returns you to the view you moved from',
       'Location %r' % resp.get('Location'))

    MealEntry.objects.all().delete()
    MealEntry.objects.create(date=dt.date(2026, 10, 21), recipe=recipe,
                             servings=4, created_by=u)
    page_html = cl.get('/meal_plans/',
                       {'view': 'month',
                        'date': '2026-10-19'}).content.decode('utf-8')


# ==========================================================================
head('4. DRIVEN IN A BROWSER - and the bubble-phase control beside it')
# ==========================================================================
if not django_up or not page_html:
    skip('the driven checks', 'no page to drive')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:50])

    if sync_playwright is not None:
        WATCH = """() => {
            window.__picker = false;
            const orig = window.openPicker;
            window.openPicker = function () {
                window.__picker = true;
                return orig ? orig.apply(this, arguments) : undefined;
            };
        }"""
        with sync_playwright() as pw:
            br = pw.chromium.launch()

            pg = br.new_page(viewport={'width': 1200, 'height': 950})
            pg.set_content(page_html, wait_until='load')
            pg.evaluate(WATCH)
            n_chips = pg.evaluate(
                "() => document.querySelectorAll('[data-chip]').length")
            ok(n_chips >= 1, 'the month renders a chip to click',
               'found %d' % n_chips)
            pg.click('[data-chip]')
            pg.wait_for_timeout(350)

            ok(pg.evaluate(
                "() => !document.getElementById('chipMenu').hidden"),
               'clicking a chip opens the menu')
            ok(not pg.evaluate("() => !!window.__picker"),
               'AND THE PICKER DOES NOT OPEN - which is the whole '
               'reason the listener captures')

            items = pg.evaluate(
                """() => Array.from(document.querySelectorAll(
                     '#chipMenu [data-act]')).filter(e => !e.hidden)
                     .map(e => e.getAttribute('data-act'))""")
            ok(items == ['view', 'move', 'remove'],
               'and it offers View, Move to and Remove, in that order - '
               'look, then change, then destroy',
               'offered %r' % (items,))

            label = pg.evaluate(
                """() => { const s = document.querySelector(
                     '#chipMenu [data-slot=\\"remove\\"]');
                   return s ? s.textContent.trim() : ''; }""")
            ok('Remove from' in label and 'Oct' in label,
               'and Remove names the day it would remove it from',
               'it says %r' % label)

            # THE CELL ITSELF STILL WORKS. A round that stopped the
            # chip's click by breaking the cell's would have passed
            # every check above.
            pg.evaluate("() => { window.__picker = false; }")
            pg.evaluate(
                """() => { const c = Array.from(document.querySelectorAll(
                     '.month-cell[role=\\"button\\"]')).find(
                       e => !e.querySelector('[data-chip]'));
                   if (c) { c.click(); } }""")
            pg.wait_for_timeout(300)
            ok(pg.evaluate("() => !!window.__picker"),
               'CONTROL: and a cell with no chip in it still opens the '
               'picker, so the chip stopped its own click and not the '
               "cell's")
            pg.close()

            # ---- THE CONTROL THAT MAKES THE DESIGN A DECISION
            #
            # The same page, with the capture flag flipped to false. If
            # this did not open the picker, the capture phase would be
            # decoration and this round's central claim would be a
            # story rather than a fact.
            bubbled = page_html.replace('}, true);', '}, false);')
            ok(bubbled != page_html,
               'the capture flag is where the suite thinks it is')
            pg2 = br.new_page(viewport={'width': 1200, 'height': 950})
            pg2.set_content(bubbled, wait_until='load')
            pg2.evaluate(WATCH)
            pg2.click('[data-chip]')
            pg2.wait_for_timeout(350)
            ok(pg2.evaluate("() => !!window.__picker"),
               'CONTROL: with the listener set to BUBBLE, the picker '
               'opens too - so the capture phase is load-bearing and '
               'not superstition')
            pg2.close()

            # ---- AND THE NARROW SCREEN, WHICH IS 768px AND NOT 390.
            #
            # This block used to open the menu at 390px and assert its
            # items were thumb targets. It passed for the wrong
            # reason: RD-2's chip reset carried `display: block`,
            # which outranked MV-2's rule hiding chips below 768px, so
            # the month drew 38 names in a 48px cell. test_month_view
            # caught that and the reset lost its display - and this
            # block then had nothing to click.
            #
            # WHICH IS THE RIGHT ANSWER. On a phone the month shows
            # MARKS, by Demetri's own Q4 decision, so there is no chip
            # to press and the menu is not the phone path at all - the
            # Day card's buttons are. The thumb-target claim belongs
            # at the narrowest width where the menu is actually used.
            pg3 = br.new_page(viewport={'width': 768, 'height': 900})
            pg3.set_content(page_html, wait_until='load')
            pg3.click('[data-chip]')
            pg3.wait_for_timeout(350)
            heights = pg3.evaluate(
                """() => Array.from(document.querySelectorAll(
                     '#chipMenu [data-act]')).filter(e => !e.hidden)
                     .map(e => Math.round(
                       e.getBoundingClientRect().height))""")
            ok(heights and min(heights) >= 44,
               'every menu item is at least 44px at 768px, the '
               'narrowest width that draws a chip to press',
               'heights %r' % (heights,))
            box = pg3.evaluate(
                """() => { const m = document.getElementById('chipMenu');
                   const r = m.getBoundingClientRect();
                   return {left: Math.round(r.left),
                           right: Math.round(r.right),
                           w: document.documentElement.clientWidth}; }""")
            ok(box['left'] >= 0 and box['right'] <= box['w'],
               'and the menu stays on the screen at 768px',
               'it spans %s..%s of %s' % (box['left'], box['right'],
                                          box['w']))
            pg3.close()

            # AND AT 390px THERE IS NO CHIP, which is MV-2's rule and
            # Demetri's Q4 answer - the month draws marks there. This
            # is asserted rather than assumed, because the block above
            # spent a day passing on the opposite.
            pg4 = br.new_page(viewport={'width': 390, 'height': 844})
            pg4.set_content(page_html, wait_until='load')
            pg4.wait_for_timeout(200)
            shown = pg4.evaluate(
                """() => Array.from(document.querySelectorAll(
                     '[data-chip]')).filter(
                       e => e.getBoundingClientRect().width > 0).length""")
            ok(shown == 0,
               'CONTROL: and at 390px no chip is drawn at all - the '
               'month shows marks there, so the menu is not the phone '
               "path; the Day card's buttons are",
               '%d chip(s) visible' % shown)
            pg4.close()
            br.close()


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
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
for _dep in ['.bak_viewback']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
ok(_i >= len(alv_rounds.ROUNDS) - 8,
   'and it is among the eight newest, where this push put it',
   'it is at %d of %d' % (_i, len(alv_rounds.ROUNDS)))
for frag in ('def move_meal_entry(', 'data-chip='):
    ok(frag in gate, 'the gate pins %r' % frag)

for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher,
   'the patcher has an already-applied path')
import apply_chip_menu as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
