# -*- coding: utf-8 -*-
"""test_menu_range.py - round MN-2, 21 Oct 2026.

A MENU IS A NAMED SET OF MEALS. IT WAS A WEEK, AND ONLY THIS WEEK.

Demetri, 21 October, with the Saved Menus dialog open:

    "I am also not happy that a Menu has to be applied to a
     pre-specified week. Should I not be able to select to which week
     I want to apply the Saved Menu??? Also, when I save a Menu, it
     only allows me to select the current week. What if I want to save
     a previous week, or choose the just create a Xmas and New Years
     menu for days, and save that??"

THE TABLE ALREADY ALLOWED BOTH. MenuItem.day_index has carried the
help_text "0 is the first day of the menu, not a weekday" since MN-1
wrote it on 18 October. What tied a menu to seven days was the two
views either side of it - `(e.date - week).days` on the way in,
`if not 0 <= it.day_index <= 6` and `week + timedelta(...)` on the way
out - and a dialog with no field for either end.

SAME SHAPE AS CP-2 THREE ROUNDS AGO. copy_week_rows had copied by date
offset since MN-1; only the door was week-shaped. Section 1 asks the
model whether the premise still holds rather than quoting this
paragraph back.

WHERE YOU ARE AND WHAT YOU ARE ACTING ON ARE TWO THINGS. `week` keeps
its job: it is the page you came from and it decides where Back goes.
`from`, `to` and `onto` say what to keep and where to put it, and each
defaults to that week - so a caller that sends none of them gets
exactly what these views did before. Section 3 posts the old shape and
holds them to that.

THE CEILING IS 92 DAYS, a quarter, which covers Christmas and New Year
and stops a dragged date field saving a year.

THE COLUMN KEEPS ITS NAME. day_offset would be better English;
renaming a column on a live MySQL table buys nothing the help_text does
not already say. That was the choice, and section 1 holds the
docstrings to saying so.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The range is read and defaults to the week on
      screen; the offset is measured from the start of the range; the
      ceiling is named; the landing date is read.

  2   THE CONTROL. Re-asked of .bak_menurange, where a menu was seven
      days measured from a Monday.

  3   DRIVEN, WHICH IS THE ONLY FORM OF THIS CLAIM THAT MATTERS. Save
      ten days across a month boundary, read the offsets back, stamp
      them onto a Wednesday five weeks later and count the dates.
      Then every refusal, and the old post shape, unchanged.

  4   THE DIALOG. Two ends, a landing date, the three presets CP-2
      built - not a second copy of them - and a button armed by both
      halves of the instruction.

  5   MN-1 and MW-1's OWN SUITE, RUN. This round corrects four of its
      claims in the same patcher.

  6   Scope, registration and the gate.

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

import io
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_menurange'
ME = 'test_menu_range.py'
PATCHER = 'apply_menu_range.py'
PS1 = 'Push-PendingChanges.ps1'
WEEK = 'test_meal_week.py'
MARK = 'MN-2, 21 Oct 2026'
CEILING = 92

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEW, MODELS, TPL)

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


def fn(code, name, nxt):
    if ('def %s' % name) not in code or ('def %s' % nxt) not in code:
        return ''
    return code[code.index('def %s' % name):code.index('def %s' % nxt)]


def claims(d):
    v = T.python_code_only(d[VIEW], payloads=True)
    m = T.python_code_only(d[MODELS], payloads=True)
    t = d[TPL]
    sv = fn(v, 'save_menu', 'apply_menu')
    av = fn(v, 'apply_menu', 'delete_menu')
    return {
        'the ceiling is a named constant, where the rule that uses it is':
            'MENU_MAX_DAYS = 92' in v,
        'save_menu reads a RANGE':
            ("week_of(request.POST.get('from')" in sv
             and "week_of(request.POST.get('to')" in sv),
        '  and the offset is measured from the START of that range':
            'day_index=(e.date - start).days' in sv,
        '  over range_entries, not week_entries':
            'range_entries(start, end)' in sv,
        'apply_menu reads a LANDING DATE':
            "week_of(request.POST.get('onto')" in av,
        '  and lands the menu on it':
            'when = onto + timedelta(days=it.day_index)' in av,
        '  with the ceiling as the drop, not the week':
            'if not 0 <= it.day_index < MENU_MAX_DAYS:' in av,
        'the planner annotates each menu LENGTH for the dialog':
            "span_days=Coalesce(Max('items__day_index'), -1) + 1" in v,
        # THE DOCSTRING IS THE SUBJECT HERE, so the RAW file is read.
        # python_code_only strips docstrings, which is right for every
        # other claim in this dict and wrong for this one.
        'the Menu model stops calling itself a week':
            ('DAY OFFSETS and not dates' in d[MODELS]
             and 'DAY INDEXES, 0 to 6' not in d[MODELS]),
        # id=, NOT name=. The COPY dialog has carried name="onto"
        # since CP-2, so asking for the name alone would have held
        # before this round and failed the control for being correct.
        'the Saved Menus dialog has both ends and a landing date':
            ('id="mnFrom"' in t and 'id="mnTo"' in t
             and 'id="mnOnto"' in t),
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

V = T.python_code_only(NOW[VIEW], payloads=True)
SV = fn(V, 'save_menu', 'apply_menu')
AV = fn(V, 'apply_menu', 'delete_menu')

# THE DEFAULTS ARE THE WHOLE COMPATIBILITY STORY. Without them a caller
# that sends only `week` changes meaning silently, which is the one
# thing this round must not do.
ok("week_of(request.POST.get('from'), week)" in SV,
   'the range DEFAULTS to the week on screen, so a post that says '
   'nothing means what it always meant')
ok("timedelta(days=6))" in SV,
   '  and the far end defaults to that week Sunday')
ok("week_of(request.POST.get('onto'), week)" in AV,
   'and so does the landing date')

# NOTHING IS MEASURED FROM A MONDAY ANY MORE.
ok('(e.date - week).days' not in SV,
   'nothing in save_menu measures an offset from a Monday')
ok('week + timedelta(days=it.day_index)' not in AV,
   'and nothing in apply_menu lands on the week on screen')

# THE RULES THAT MUST NOT HAVE MOVED WITH THE WEEK. Guards, true
# before and after, so they are not in claims() - a guard in a delta
# dict fails the control for being correct.
ok('if e.leftover_of_id:' in SV,
   'GUARD: a leftover is STILL not saved into a menu - it is a '
   'consequence of a week, not a thing anybody plans')
ok('A menu needs a name.' in SV and 'name__iexact=name' in SV,
   'GUARD: a name is still required and still unique, case-blind')
ok('are still there' in T.python_code_only(NOW[VIEW], payloads=True),
   'GUARD: deleting a menu still leaves the meals it stamped')

# THE DECISION NOT TO RENAME THE COLUMN, WRITTEN DOWN.
M = NOW[MODELS]
ok('day_offset would be better English' in M,
   'the choice NOT to rename day_index is recorded where the column '
   'lives, so the next round inherits a decision and not a question')
ok('not a weekday' in M,
   '  and the help_text that was right all along is untouched')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

oldv = T.python_code_only(BEFORE[VIEW], payloads=True)
oldsv = fn(oldv, 'save_menu', 'apply_menu')
oldav = fn(oldv, 'apply_menu', 'delete_menu')
ok('day_index=(e.date - week).days' in oldsv,
   'CONTROL: a menu was measured from the Monday of the week on screen')
ok('if not 0 <= it.day_index <= 6:' in oldav,
   'CONTROL: and anything past day 6 was thrown away')
ok('week_entries(week)' in oldsv,
   'CONTROL: and what it saved was a week, by the helper it called')
ok('id="mnOnto"' not in BEFORE[TPL],
   'CONTROL: the Saved Menus dialog had no landing date to offer')
ok('DAY INDEXES, 0 to 6' in BEFORE[MODELS],
   'CONTROL: and the model said so about itself, which the table never '
   'agreed with')


# ==========================================================================
head('3. DRIVEN - A MENU THAT IS NOT A WEEK')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
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
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if django_up:
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Menu, MenuItem, Recipe

    editor = User.objects.create_user(username='mn2', password='x',
                                      email='mn2@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        editor.user_permissions.add(
            Permission.objects.get(codename=cn))
    cl = Client()
    cl.force_login(editor)

    SAVE = '/meal_plans/menus/save/'
    APPLY = '/meal_plans/menus/apply/'

    # TEN DAYS ACROSS A MONTH BOUNDARY, which a week cannot be. The
    # Christmas case he described is this one with different dates.
    START = dt.date(2026, 12, 23)        # a Wednesday
    END = dt.date(2027, 1, 1)            # ten days on, next YEAR
    HOME = dt.date(2026, 10, 19)         # the week you are standing on
    LAND = dt.date(2027, 3, 10)          # a Wednesday, months away

    soup = Recipe.objects.create(recipe_name='Soup for six', servings=6)
    stew = Recipe.objects.create(recipe_name="Yiayia's stew", servings=2)
    pie = Recipe.objects.create(recipe_name='Fish pie', servings=4)

    def entry(d, recipe=None, note='', servings=4, order=0, parent=None):
        return MealEntry.objects.create(
            date=d, recipe=recipe, note=note, servings=servings,
            sort_order=order, leftover_of=parent, created_by=editor)

    def on(d):
        return list(MealEntry.objects.filter(date=d)
                    .order_by('sort_order', 'meal_entry_id'))

    def clear():
        MealEntry.objects.all().delete()
        Menu.objects.all().delete()

    def iso(d):
        return d.strftime('%Y-%m-%d')

    # ---- 3a SAVING A RANGE -------------------------------------------
    clear()
    entry(START, soup, servings=6, order=1)                    # day 0
    entry(START + dt.timedelta(days=2), stew, servings=2, order=1)  # 2
    entry(START + dt.timedelta(days=9), pie, servings=4, order=1)   # 9
    entry(START + dt.timedelta(days=9), None, note='Fireworks',
          order=2)                                                  # 9
    # A DAY OUTSIDE THE RANGE IS NOT IN THE MENU.
    entry(START + dt.timedelta(days=12), soup, servings=6, order=1)

    r = cl.post(SAVE, {'week': iso(HOME), 'from': iso(START),
                       'to': iso(END), 'name': 'Xmas and New Year'})
    ok(r.status_code == 302, 'saving a RANGE redirects', r.status_code)
    menu = Menu.objects.filter(name='Xmas and New Year').first()
    if ok(menu is not None, 'the menu exists, under the name typed'):
        items = list(menu.items.all())
        ok(len(items) == 4,
           '  with the four rows inside the range and not the fifth',
           len(items))
        ok([i.day_index for i in items] == [0, 2, 9, 9],
           '  on day offsets 0, 2, 9 and 9 - and 9 is past the end of '
           'any week', [i.day_index for i in items])
        ok(items[3].recipe_id is None and items[3].note == 'Fireworks',
           '  a note is a row too - it is a planned night',
           (items[3].recipe_id, items[3].note))
        ok(not MealEntry.objects.filter(
            date=START + dt.timedelta(days=12)).exists() is False,
           '  and the meal twelve days out is still on its own day - '
           'saving is not moving')

    # ---- 3b A LEFTOVER IS STILL NOT SAVED ----------------------------
    clear()
    p = entry(START, soup, servings=6, order=1)
    entry(START + dt.timedelta(days=1), soup, servings=6, order=1,
          parent=p)
    cl.post(SAVE, {'week': iso(HOME), 'from': iso(START),
                   'to': iso(END), 'name': 'Just the roast'})
    m2 = Menu.objects.filter(name='Just the roast').first()
    if ok(m2 is not None, 'a range with a leftover in it still saves'):
        ok(m2.items.count() == 1,
           '  and the LEFTOVER is not in it', m2.items.count())

    # ---- 3c THE OLD SHAPE, UNCHANGED ---------------------------------
    # A POST THAT SENDS ONLY `week` MUST MEAN WHAT IT ALWAYS MEANT.
    # This is the compatibility claim, and it is driven rather than
    # argued.
    clear()
    entry(HOME, soup, servings=6, order=1)                     # Monday
    entry(HOME + dt.timedelta(days=6), pie, servings=4, order=1)  # Sun
    entry(HOME + dt.timedelta(days=8), stew, servings=2, order=1)  # out
    cl.post(SAVE, {'week': iso(HOME), 'name': 'Just this week'})
    m3 = Menu.objects.filter(name='Just this week').first()
    if ok(m3 is not None, 'a save that names no range still saves'):
        ok([i.day_index for i in m3.items.all()] == [0, 6],
           '  and it is THE WEEK ON SCREEN - day 0 and day 6, with the '
           'meal two days past Sunday left out',
           [i.day_index for i in m3.items.all()])

    # ---- 3d APPLYING ONTO A DATE OF YOUR CHOOSING --------------------
    clear()
    entry(START, soup, servings=6, order=1)
    entry(START + dt.timedelta(days=9), pie, servings=4, order=1)
    cl.post(SAVE, {'week': iso(HOME), 'from': iso(START),
                   'to': iso(END), 'name': 'Ten days'})
    # .filter().first(), NOT .get(). Against the reverted tree the
    # ranged save refuses and this menu never exists - .get() raised
    # DoesNotExist and the suite CRASHED rather than failing, which
    # blocks a push exactly as hard and says far less about why.
    # Fourth time today.
    menu = Menu.objects.filter(name='Ten days').first()
    if not ok(menu is not None,
              'a ten-day menu saved from a range exists to apply'):
        menu = Menu.objects.create(name='Ten days (stand-in)')
    MealEntry.objects.all().delete()

    r = cl.post(APPLY, {'week': iso(HOME), 'menu_id': menu.menu_id,
                        'onto': iso(LAND)})
    ok(r.status_code == 302, 'applying onto a chosen date redirects',
       r.status_code)
    ok(len(on(LAND)) == 1,
       'day 0 lands on the date that was CHOSEN - %s' % LAND,
       len(on(LAND)))
    ok(len(on(LAND + dt.timedelta(days=9))) == 1,
       '  and day 9 lands nine days later, which no week could hold',
       len(on(LAND + dt.timedelta(days=9))))
    ok(not MealEntry.objects.filter(date__lt=LAND).exists(),
       '  and nothing landed before it')
    ok(LAND.month != START.month and LAND.year != START.year,
       '  saved in %s %d, applied to %s %d - which is the whole point'
       % (START.strftime('%b'), START.year,
          LAND.strftime('%b'), LAND.year))
    ok(menu.items.count() == 2,
       '  and the MENU is unchanged - a stamp is not a move',
       menu.items.count())

    # ---- 3e APPLYING WITH NO LANDING DATE ----------------------------
    MealEntry.objects.all().delete()
    cl.post(APPLY, {'week': iso(HOME), 'menu_id': menu.menu_id})
    ok(len(on(HOME)) == 1,
       'an apply that names no landing date still lands on the week on '
       'screen', len(on(HOME)))

    # ---- 3f THE SAVES THAT MUST REFUSE -------------------------------
    print('')
    n = Menu.objects.count()
    for data, why in (
            ({'week': iso(HOME), 'from': iso(END), 'to': iso(START),
              'name': 'Backwards'}, 'a range the wrong way round'),
            ({'week': iso(HOME), 'from': iso(START),
              'to': iso(START + dt.timedelta(days=CEILING)),
              'name': 'A whole quarter and one'},
             'a range one day past the ceiling'),
            ({'week': iso(HOME), 'from': iso(dt.date(2030, 1, 1)),
              'to': iso(dt.date(2030, 1, 7)), 'name': 'Empty'},
             'a range with nothing on it'),
            ({'week': iso(HOME), 'from': iso(START), 'to': iso(END),
              'name': ''}, 'a menu with no name'),
            ({'week': iso(HOME), 'from': iso(START), 'to': iso(END),
              'name': 'Ten days'}, 'a name already taken')):
        r = cl.post(SAVE, data)
        ok(r.status_code == 302 and Menu.objects.count() == n,
           'REFUSED: %s' % why,
           'status %s, menus %d' % (r.status_code, Menu.objects.count()))

    # AND THE ONE THAT MUST NOT REFUSE: exactly the ceiling.
    clear()
    entry(START, soup, servings=6, order=1)
    r = cl.post(SAVE, {'week': iso(HOME), 'from': iso(START),
                       'to': iso(START + dt.timedelta(days=CEILING - 1)),
                       'name': 'Exactly a quarter'})
    ok(Menu.objects.filter(name='Exactly a quarter').exists(),
       'but exactly %d days is ALLOWED - the ceiling is a limit, not a '
       'fence one short of it' % CEILING)

    # ---- 3g THE DROP IS A DROP, NOT A WRAP ---------------------------
    menu = Menu.objects.filter(name='Exactly a quarter').first()
    if menu is None:
        menu = Menu.objects.create(name='Exactly a quarter (stand-in)')
    MealEntry.objects.all().delete()
    MenuItem.objects.create(menu=menu, day_index=CEILING, recipe=pie,
                            servings=4, sort_order=1)
    MenuItem.objects.create(menu=menu, day_index=-1, recipe=pie,
                            servings=4, sort_order=1)
    cl.post(APPLY, {'week': iso(HOME), 'menu_id': menu.menu_id,
                    'onto': iso(LAND)})
    ok(not MealEntry.objects.filter(
        date__gte=LAND + dt.timedelta(days=CEILING)).exists(),
       'a day offset ON the ceiling is dropped, not wrapped')
    ok(not MealEntry.objects.filter(date__lt=LAND).exists(),
       '  and a negative one is dropped too')


# ==========================================================================
head('4. THE DIALOG')
# ==========================================================================
t = NOW[TPL]
code = T.code_only(t)
for what, need in (('a From', 'id="mnFrom"'), ('a To', 'id="mnTo"'),
                   ('a Landing on', 'id="mnOnto"'),
                   ('and a line that says which days it will cover',
                    'id="mnSpan"')):
    ok(need in code, 'the Saved Menus dialog has %s' % what)
ok(code.count('mn-preset') >= 4,
   'and the three presets, which are CP-2 own - This day, This week, '
   'This month', code.count('mn-preset'))

# ONE ANSWER TO WHAT A MONTH IS. SL-7 settled it for the shopping list
# and CP-2 reused it; a second implementation here would be a second
# answer waiting to disagree.
# code_only_js, NOT the raw page: the comments in this round own
# script name the labels and selectors the checks below ask about, and
# a reader that sees comments answers "is it written down" rather than
# "is it there". CO-1's lesson, 17 October.
js = T.code_only_js(t)
ok(js.count('function span(') == 1,
   'and ONE span() in the page, shared by both preset rows - a second '
   'would be a second answer to what a month is',
   js.count('function span('))
ok("span(b.getAttribute('data-mn-span'))" in js,
   '  which the menu presets call rather than copy')

# THE BUTTON IS ARMED BY BOTH HALVES. A menu with no date, or a date
# with no menu, is half an instruction.
ok('function mnSaySpan(' in js,
   'the dialog works out which days a menu will cover, in the page')
ok('go.disabled = !ready' in js and 'sel && onto && onto.value' in js,
   '  and the Add button is armed only when a menu AND a date are '
   'chosen')
ok('data-menu-days=' in code,
   '  from the menu own length, which the planner annotates - so no '
   'query and no endpoint')

# THE WORDING FOLLOWED THE BEHAVIOUR.
ok('Add to This Week' not in T.code_only_js(t),
   'nothing still says "Add to This Week" - it stopped being true the '
   'moment a landing date arrived')
ok('Save this week<' not in T.code_only_js(t)
   and 'Save this week</strong>' not in T.code_only_js(t),
   '  and nothing still offers to save "this week" only, the empty '
   'state included')

# PHONE. Every control in this dialog is a 44px target, which is the
# house rule and the one most easily lost in a form.
style = t[t.index('<style'):t.index('</style>')] if '<style' in t else ''
ok('.cp-presets .btn { height: 44px; }' in style,
   'the preset buttons keep their 44px height on a phone')
ok('.cp-dates { flex-direction: column; gap: 0; }' in style,
   '  and the two date fields stack rather than squeeze')

ok(t.count('{%') == t.count('%}'),
   'the template tags balance - %d {%% against %d %%}'
   % (t.count('{%'), t.count('%}')))


# ==========================================================================
head("5. MN-1 and MW-1's OWN SUITE")
# ==========================================================================
# FOUR OF ITS CLAIMS MOVED IN THIS ROUND's PATCHER, and one of them is
# a BEHAVIOUR that changed rather than a pin: day 9 used to be thrown
# away and now lands. A claim moved is a claim that has to still fit.
w, wb = read(os.path.join(ROOT, WEEK)), was(os.path.join(ROOT, WEEK))
ok('day_index=(e.date - week).days' in wb,
   'CONTROL: it asked that the offset came from a Monday')
ok('day_index=(e.date - start).days' in w,
   '  corrected to the start of the range')
ok('if not 0 <= it.day_index <= 6:' in wb,
   'CONTROL: and that anything past day 6 was dropped')
ok('if not 0 <= it.day_index < MENU_MAX_DAYS:' in w,
   '  corrected to the ceiling, with the rule unchanged')
ok('day_index=9' in wb and 'a day index outside 0..6 is DROPPED' in wb,
   'CONTROL: and it drove day 9 being thrown away')
ok('while day 9 LANDS' in w,
   '  corrected to drive day 9 LANDING - the behaviour changed, so the '
   'check changed with it rather than being deleted')
ok(MARK in w, '  and it says which round changed it and why')

r = subprocess.run([sys.executable, WEEK], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode('utf-8', 'replace').strip().splitlines()
ok(r.returncode == 0, '%s is still green with its four claims corrected'
   % WEEK, '\n'.join(out[-6:]))
for line in out[-3:]:
    if 'passed,' in line:
        print('       %s' % line.strip())


# ==========================================================================
head('6. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# NO MIGRATION. The column was always an offset; only the views and the
# dialog were week-shaped. A round that touched models.py but added no
# migration is worth saying out loud rather than leaving to be noticed.
mig = os.path.join(ROOT, 'pages', 'migrations')
newmig = [f for f in os.listdir(mig)
          if os.path.isfile(os.path.join(mig, f) + SUFFIX)]
ok(not newmig,
   'NO MIGRATION. Only a docstring changed in models.py - the column '
   'was an offset from the day MN-1 wrote it', newmig)

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
ok(os.path.isfile(os.path.join(ROOT, WEEK) + SUFFIX),
   '  and %s, which this round corrects' % WEEK)
ok('MENU_MAX_DAYS' in gate and 'mn-preset' in gate,
   'both sentinels are on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_menu_range as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that 92 is the right ceiling. It covers Christmas and')
print('  New Year with room and stops a dragged date field saving a')
print('  year. It is a judgement, named in one place, and easy to')
print('  change if a real menu ever needs more.')
print('')
print('  Not that the Apply half says what is already on the landing')
print('  days. Copy does - that was the 19 October decision about')
print('  COPY - and Apply still only promises "alongside whatever is')
print('  already there". Asking the server would need the endpoint')
print('  CP-2 built, pointed at a span. It is a round, not an')
print('  oversight.')
print('')
print('  Not that the column should keep its name. day_offset is')
print('  better English. The choice was that a rename on a live')
print('  table buys nothing the help_text does not already say.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
