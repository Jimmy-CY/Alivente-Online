# -*- coding: utf-8 -*-
"""test_meal_day.py - round MO-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE DAY SPEAKS.

Demetri, 19 Oct, asked for two things a day should be able to say
besides "here is a recipe": "A note row, and Leftovers marked on a
meal."

BOTH COLUMNS HAVE BEEN IN THE MODEL SINCE MN-1 AND NOTHING COULD FILL
EITHER. MealEntry.recipe has been nullable and MealEntry.leftover_of
has existed since 18 October; the planner has DRAWN both row shapes
since the same afternoon, and MW-1 took care to copy leftovers
correctly a few hours ago. There was no control anywhere in the
application that could make one. A column nobody can fill is a column
nobody can check, which is the sentence RT-1 wrote about exemptions.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Two views, two routes, two dialogs, the leftover row
      and the second Add control.

  2   THE CONTROL. Every claim re-asked of the .bak_mealday backups,
      where every one must FAIL.

  3   THE BEHAVIOUR, DRIVEN FOR REAL. A note buys nothing. A leftover
      buys nothing. A leftover of a leftover points at the ORIGINAL. A
      leftover cannot be dated before the meal it came from. And the
      planner still costs one query for the week with leftovers on it,
      which is the claim select_related('leftover_of') makes.

  4   THE ROW SHAPES, rendered. A leftover has no servings stepper,
      because a number that changes nothing on the shopping list is a
      control that lies.

  5   WIDE FROM BIRTH, and the house vocabulary: Leftovers is COPY,
      not a new verb.

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

import ast
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_mealday'
ME = 'test_meal_day.py'
PATCHER = 'apply_meal_day.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MO-1, 19 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')

BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

FILES = (VIEW, URLS, TPL, BASE)
VIEWS_ADDED = ('add_meal_note', 'add_leftover')
DIALOGS = ('noteModal', 'leftoverModal')

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


def claims(text):
    """Every source claim MO-1 makes, written once and asked twice.

    ASKED OF THE CODE. This round's prose names the stepper it leaves
    out, the chain it refuses and C13 by name; to a substring search a
    comment about a thing is the thing, and MW-1's own patcher refused
    its own round over one sentence a few hours ago.
    """
    c = {}
    vcode = T.python_code_only(text[VIEW])
    ucode = T.python_code_only(text[URLS])
    tcode = T.code_only_js(text[TPL])
    ccss = T.code_only(text[TPL])

    # THE TWO ROW ARMS, SLICED BETWEEN THE BRANCH TAGS. Both of these
    # were got wrong first: 'leftover-item' occurs in the STYLESHEET
    # before it occurs in the markup, so splitting on the class name
    # handed back a slice of CSS; and the recipe arm carries its own
    # photo_url and permission branches, so splitting on the next
    # {% else %} stopped 344 characters in, before the row actions.
    # Both checks failed rather than passing on an empty slice, which
    # is the only reason this is a note and not a defect.
    lrow = (tcode.split('{% if entry.recipe and entry.leftover_of %}')[1]
            .split('{% elif entry.recipe %}')[0]
            if '{% if entry.recipe and entry.leftover_of %}' in tcode
            else '')
    arm = (tcode.split('{% elif entry.recipe %}')[1].split('{% empty %}')[0]
           if '{% elif entry.recipe %}' in tcode else '')

    # ---- 1. the two views, their tier and their method
    def tier(fn):
        i = vcode.find('def %s(request):' % fn)
        return vcode[max(0, i - 260):i] if i >= 0 else ''

    for fn in VIEWS_ADDED:
        c['%s is a view' % fn] = 'def %s(request):' % fn in vcode
        c['  and %s is EDIT-tier' % fn] = (
            'def %s(request):' % fn in vcode
            and 'can_edit_recipes' in tier(fn))
        c['  and %s is POST-only' % fn] = (
            'def %s(request):' % fn in vcode
            and 'require_POST' in tier(fn))
        c['  the route %s is registered' % fn] = (
            "views.%s, name='%s'" % (fn, fn)) in ucode

    # ---- 2. what makes a note a note
    note = vcode.split('def add_meal_note')[-1].split('def ')[0]
    c['a note has NO recipe'] = 'recipe=None' in note
    c['  it is trimmed and capped at the field width'] = (
        ".strip()[:200]" in note)
    c['  and a note of nothing is refused'] = (
        'A note needs some words.' in note)
    c['  it lands after whatever the day holds'] = (
        "Max('sort_order')" in note)

    # ---- 3. what makes a leftover a leftover
    left = vcode.split('def add_leftover')[-1].split('def ')[0]
    c['a leftover points at the meal it came from'] = (
        'leftover_of=root' in left)
    c['  and a leftover OF A LEFTOVER points at the ORIGINAL'] = (
        'root = src.leftover_of or src' in left)
    c['  it carries the recipe, so you know what it is'] = (
        'recipe=root.recipe' in left)
    c['  a note has no leftovers - nothing was cooked'] = (
        'if root.recipe_id is None:' in left)
    c['  and it cannot be dated before the meal it came from'] = (
        'if when < root.date:' in left)
    c['  refused with a sentence, not quietly moved  [C13]'] = (
        'cannot be eaten before the ' in left)
    c['  and the message says it costs nothing'] = (
        'nothing on the shopping list.' in left)

    # ---- 4. ONE QUERY, not one per leftover row
    c['leftover_of joins the week query'] = (
        "select_related('recipe', 'leftover_of')" in vcode)

    # ---- 5. the leftover row is a different row
    c['the leftover row is its own row'] = 'leftover-item' in tcode
    c['  tested BEFORE the recipe arm, because it has a recipe'] = (
        '{% if entry.recipe and entry.leftover_of %}' in tcode)
    c['  and the recipe arm became an elif'] = (
        '{% elif entry.recipe %}' in tcode)
    # THE CLAIM THAT MATTERS MOST ON THIS ROW. A stepper here would be
    # a number that changes nothing: counts_on_shopping_list is False
    # for a leftover, which is the whole feature.
    c['  it has NO servings stepper'] = (
        bool(lrow) and 'stepServings' not in lrow
        and 'servings-step' not in lrow)
    c['  while the recipe row still has one'] = (
        bool(arm) and 'stepServings' in arm)
    c['  it names the day it was cooked on instead'] = (
        'Cooked on {{ entry.leftover_of.date|date:"D j M" }}' in tcode)
    # PAIRED, because the NOTE row has said "Nothing to cook, nothing
    # to buy" since MN-1 - so the bare phrase was true before this
    # round and the control section said so.
    c['  and says there is nothing to buy'] = (
        'leftover-item' in tcode
        and 'nothing to buy</span>' in tcode)
    c['  wearing a pill that says Leftovers'] = (
        'alv-pill alv-pill-info">Leftovers<' in tcode)

    # ---- 6. the two Add controls, and the two dialogs
    c['a day has a second Add control'] = 'Add Note' in tcode
    c['  side by side, and stacked on a phone'] = (
        '.day-add-row {' in ccss and 'flex-direction: column;' in ccss)
    for mid in DIALOGS:
        c['%s is on the planner' % mid] = tcode.count('id="%s"' % mid) == 1
    c['the note dialog suggests three nights'] = (
        tcode.count('onclick="setNote(') == 3)
    c['the leftover dialog stops the browser dating it too early'] = (
        'box.min = cookedOn;' in tcode)
    c['  and says so in words as well'] = (
        'Leftovers cannot come first.' in tcode)
    c['both dialogs are emptied as they open  [C19]'] = (
        "document.getElementById('noteText').value = '';" in tcode
        and "box.value = '';" in tcode)
    c['nothing is said through an alert  [SL-4]'] = (
        'function openNote(' in tcode and 'alert(' not in tcode)

    # ---- 7. the house vocabulary, not a new verb
    # ITS OWN NAME ON COPY'S COLOUR. The first cut of this round wrote
    # `icon-action-btn icon-duplicate` with a fa-redo glyph, on the
    # reasoning that a leftover is COPY - right about the family, wrong
    # about the class. test_icon_names refused it inside a minute:
    # ".icon-duplicate fa-copy(11) fa-redo(1)". A CLASS CARRIES ONE
    # PICTURE, and base.html says so beside .icon-manage in words this
    # round should have read first: ALIAS THE COLOUR, NEVER THE NAME.
    c['Leftovers has its OWN class - a class carries one picture'] = (
        'icon-action-btn icon-leftover' in tcode
        and 'icon-duplicate' not in tcode)
    c['  on COPY\'s existing colour, aliased not invented'] = (
        '.icon-leftover       { color: var(--alv-edit);' in T.code_only(
            text[BASE]))
    c['  and the page SAYS why, so the next round does not repeat it'] = (
        'icon-duplicate' in text[TPL])
    # PAIRED FOR THE SAME REASON. fa-redo has been on the note row
    # since MN-1, which drew it for a leftover nothing could make.
    c['  wearing fa-redo, its one picture'] = (
        'icon-leftover' in tcode and 'fa-redo"></i></button>' in tcode)
    c['  and the row keeps LOOK, COPY, DESTROY in that order'] = (
        0 <= arm.find('icon-view') < arm.find('icon-leftover')
        < arm.find('icon-delete'))
    # AND THE LEFTOVER ROW KEEPS LOOK then DESTROY, with no COPY -
    # leftovers of leftovers are flattened by the view, so a control
    # that offered them would be a control that lies about what it
    # makes.
    c['  and the leftover row has no Leftovers control of its own'] = (
        bool(lrow) and 'icon-leftover' not in lrow
        and 0 <= lrow.find('icon-view') < lrow.find('icon-delete'))
    c['no colour literal enters the new CSS'] = (
        not re.search(r'(?m)^\s*(background|border-color|color)\s*:'
                      r'[^;]*#[0-9a-fA-F]{3,6}',
                      ccss.split('.recipe-item.leftover-item {')[1]
                      .split('/* Empty Day */')[0])
        if '.recipe-item.leftover-item {' in ccss else False)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for k in NOW_CLAIMS:
    ok(NOW_CLAIMS[k], k)

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the pre-round tree')
# ==========================================================================
WASC = claims(dict((p, was(p)) for p in FILES))
leaked = sorted(k for k in NOW_CLAIMS if WASC.get(k))
ok(not leaked,
   'not one of the %d claims above was already true before MO-1'
   % len(NOW_CLAIMS), '\n'.join(leaked))


# ==========================================================================
head('3. THE BEHAVIOUR, DRIVEN FOR REAL')
# ==========================================================================
# "THE SOURCE SAYS leftover_of=root" IS A CLAIM ABOUT TEXT. "A pot of
# soup cooked on Monday and eaten again on Wednesday and Friday is
# bought once" is a claim about the application, and it is the one that
# decides whether the feature is worth having.
django_up = False
try:
    import django
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    dj_settings.EMAIL_BACKEND = \
        'django.core.mail.backends.locmem.EmailBackend'
    dj_settings.DEBUG = True           # connection.queries needs it
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    # The 400s in section 3 are checks passing, not a problem - see
    # test_meal_week.py, where the same five junk dates are asked.
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    _buf = io.StringIO()
    call_command('migrate', run_syncdb=True, verbosity=0, stdout=_buf)
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    import datetime as _dt
    from django.contrib.auth.models import User, Permission
    from django.db import connection, reset_queries
    from django.test import Client
    from pages.models import MealEntry, Recipe

    editor = User.objects.create_user(username='mo_edit', password='x',
                                      email='mo1@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        editor.user_permissions.add(
            Permission.objects.get(codename=codename))
    reader = User.objects.create_user(username='mo_read', password='x',
                                      email='mo2@example.test')
    reader.user_permissions.add(
        Permission.objects.get(codename='can_access_recipes'))
    cl, ro = Client(), Client()
    cl.force_login(editor)
    ro.force_login(reader)

    MON = _dt.date(2026, 10, 19)
    WED = MON + _dt.timedelta(days=2)
    FRI = MON + _dt.timedelta(days=4)
    SUN_BEFORE = MON - _dt.timedelta(days=1)

    soup = Recipe.objects.create(recipe_name='Soup for six', servings=6)
    NOTE = '/meal_plans/note/'
    LEFT = '/meal_plans/leftover/'
    PLANNER = '/meal_plans/planner/?week=' + MON.strftime('%Y-%m-%d')

    def on(d):
        return list(MealEntry.objects.filter(date=d)
                    .order_by('sort_order', 'meal_entry_id'))

    def clear():
        MealEntry.objects.all().delete()

    # ----------------------------------------------------------------
    head('3a. a note is a planned night, and it buys nothing')
    # ----------------------------------------------------------------
    clear()
    r = cl.post(NOTE, {'date': WED.strftime('%Y-%m-%d'), 'note': 'Eat out'})
    ok(r.status_code == 302, 'adding a note redirects', r.status_code)
    ok(MON.strftime('%Y-%m-%d') in r['Location'],
       '  to the WEEK the day belongs to, not the day', r['Location'])
    rows = on(WED)
    ok(len(rows) == 1, 'the note is on the day', len(rows))
    e = rows[0]
    ok(e.recipe_id is None, '  with no recipe', e.recipe_id)
    ok(e.note == 'Eat out', '  and the words that were typed', e.note)
    ok(e.counts_on_shopping_list is False,
       '  AND IT BUYS NOTHING - counts_on_shopping_list is False')
    ok(e.servings_multiplier == 0,
       '  and scales nothing either', e.servings_multiplier)

    # IT LANDS BEHIND WHAT THE DAY ALREADY HOLDS.
    MealEntry.objects.create(date=FRI, recipe=soup, servings=6,
                             sort_order=1, created_by=editor)
    cl.post(NOTE, {'date': FRI.strftime('%Y-%m-%d'), 'note': 'Takeaway'})
    rows = on(FRI)
    ok(len(rows) == 2 and rows[1].note == 'Takeaway',
       'a note lands behind the meal already on that day',
       [str(x) for x in rows])

    # TRIMMED, CAPPED, AND A NOTE OF NOTHING IS REFUSED.
    n = MealEntry.objects.count()
    cl.post(NOTE, {'date': WED.strftime('%Y-%m-%d'), 'note': '  At Helen  '})
    ok(MealEntry.objects.filter(note='At Helen').exists(),
       'a note is trimmed before it is stored')
    cl.post(NOTE, {'date': WED.strftime('%Y-%m-%d'), 'note': 'x' * 300})
    long_one = MealEntry.objects.filter(note__startswith='xxx').first()
    ok(long_one is not None and len(long_one.note) == 200,
       '  and capped at the field width, rather than raising on save',
       len(long_one.note) if long_one else None)
    n = MealEntry.objects.count()
    for data, why in (({'date': WED.strftime('%Y-%m-%d'), 'note': ''},
                       'a note with no words'),
                      ({'date': WED.strftime('%Y-%m-%d'), 'note': '   '},
                       'a note of spaces'),
                      ({'date': WED.strftime('%Y-%m-%d')}, 'no note at all'),
                      ({'note': 'No day'}, 'no date'),
                      ({'date': 'nope', 'note': 'Bad date'}, 'a junk date')):
        r = cl.post(NOTE, data)
        ok(r.status_code == 302 and MealEntry.objects.count() == n,
           '%s is refused' % why, MealEntry.objects.count())
    ok(cl.get(NOTE).status_code == 405, 'the note route refuses a GET',
       cl.get(NOTE).status_code)

    # ----------------------------------------------------------------
    head('3b. ONE POT, BOUGHT ONCE - leftovers')
    # ----------------------------------------------------------------
    clear()
    pot = MealEntry.objects.create(date=MON, recipe=soup, servings=6,
                                   sort_order=1, created_by=editor)
    r = cl.post(LEFT, {'meal_entry_id': pot.meal_entry_id,
                       'date': WED.strftime('%Y-%m-%d')})
    ok(r.status_code == 302, 'adding leftovers redirects', r.status_code)
    lo = on(WED)[0]
    ok(lo.leftover_of_id == pot.meal_entry_id,
       'the leftover points at the meal it came from', lo.leftover_of_id)
    ok(lo.recipe_id == soup.recipe_id,
       '  and carries the recipe, so you can see what it is', lo.recipe)
    ok(lo.servings == 6, '  and the servings it was cooked for',
       lo.servings)
    ok(lo.counts_on_shopping_list is False,
       '  AND IT BUYS NOTHING - that is the whole feature')
    ok(pot.counts_on_shopping_list is True,
       '  while the night it was cooked on still does')

    # A LEFTOVER OF A LEFTOVER POINTS AT THE ORIGINAL.
    r = cl.post(LEFT, {'meal_entry_id': lo.meal_entry_id,
                       'date': FRI.strftime('%Y-%m-%d')})
    lo2 = on(FRI)[0]
    ok(lo2.leftover_of_id == pot.meal_entry_id,
       'leftovers OF leftovers point at the ORIGINAL meal',
       lo2.leftover_of_id)
    ok(lo2.leftover_of_id != lo.meal_entry_id,
       '  and not at the leftover they were made from')
    chain = MealEntry.objects.filter(leftover_of__isnull=False)
    ok(chain.count() == 2
       and set(x.leftover_of_id for x in chain) == {pot.meal_entry_id},
       '  so the pot has exactly one parent and two children, not a chain',
       sorted(set(x.leftover_of_id for x in chain)))
    paid = [x for x in MealEntry.objects.all() if x.counts_on_shopping_list]
    ok(len(paid) == 1 and paid[0].meal_entry_id == pot.meal_entry_id,
       'THREE NIGHTS OF SOUP, AND THE SHOPPING LIST BUYS IT ONCE',
       [str(x) for x in paid])

    # EATEN AGAIN ON THE SAME DAY IS ALLOWED - lunch and dinner.
    n = MealEntry.objects.count()
    cl.post(LEFT, {'meal_entry_id': pot.meal_entry_id,
                   'date': MON.strftime('%Y-%m-%d')})
    ok(MealEntry.objects.count() == n + 1,
       'leftovers on the SAME day are allowed - lunch and dinner',
       MealEntry.objects.count())

    # ----------------------------------------------------------------
    head('3c. the leftovers that must REFUSE')
    # ----------------------------------------------------------------
    n = MealEntry.objects.count()
    r = cl.post(LEFT, {'meal_entry_id': pot.meal_entry_id,
                       'date': SUN_BEFORE.strftime('%Y-%m-%d')})
    ok(MealEntry.objects.count() == n,
       'leftovers cannot be dated BEFORE the meal they came from',
       MealEntry.objects.count())
    ok(not MealEntry.objects.filter(date=SUN_BEFORE).exists(),
       '  and nothing was quietly moved to a date that works  [C13]')

    note_row = MealEntry.objects.create(
        date=FRI, recipe=None, note='Eat out', servings=0, sort_order=9,
        created_by=editor)
    n = MealEntry.objects.count()
    r = cl.post(LEFT, {'meal_entry_id': note_row.meal_entry_id,
                       'date': FRI.strftime('%Y-%m-%d')})
    ok(MealEntry.objects.count() == n,
       'a NOTE has no leftovers - there was nothing cooked',
       MealEntry.objects.count())

    for data, why in (({'meal_entry_id': 999999,
                        'date': WED.strftime('%Y-%m-%d')},
                       'a meal that does not exist'),
                      ({'meal_entry_id': 'nope',
                        'date': WED.strftime('%Y-%m-%d')},
                       'an id that is not a number'),
                      ({'meal_entry_id': pot.meal_entry_id,
                        'date': 'nope'}, 'a junk date'),
                      ({}, 'nothing at all')):
        r = cl.post(LEFT, data)
        ok(r.status_code == 302,
           'leftovers with %s redirects, it does not 500' % why,
           r.status_code)
    ok(MealEntry.objects.count() == n,
       '  and not one of them wrote a row', MealEntry.objects.count())
    ok(cl.get(LEFT).status_code == 405, 'the leftover route refuses a GET',
       cl.get(LEFT).status_code)

    # ----------------------------------------------------------------
    head('3d. a reader may read, and may change NOTHING')
    # ----------------------------------------------------------------
    n = MealEntry.objects.count()
    for url, data, what in (
            (NOTE, {'date': WED.strftime('%Y-%m-%d'),
                    'note': 'Reader wrote this'}, 'add a note'),
            (LEFT, {'meal_entry_id': pot.meal_entry_id,
                    'date': WED.strftime('%Y-%m-%d')}, 'add leftovers')):
        r = ro.post(url, data)
        ok(r.status_code in (302, 403),
           'a read-tier user cannot %s' % what, r.status_code)
    ok(MealEntry.objects.count() == n,
       '  and not one row was written', MealEntry.objects.count())
    ok(not MealEntry.objects.filter(note='Reader wrote this').exists(),
       '  the note a reader tried to write is not there')

    # ----------------------------------------------------------------
    head('3e. the planner still costs ONE query for the week')
    # ----------------------------------------------------------------
    # select_related('leftover_of') IS THE CLAIM. The leftover row
    # prints the date of the meal it came from, which is a query per
    # row without it - and E29 spent a round taking exactly this fault
    # off four screens.
    clear()
    base_pot = MealEntry.objects.create(date=MON, recipe=soup, servings=6,
                                        sort_order=1, created_by=editor)

    def cost(u):
        reset_queries()
        resp = cl.get(u)
        return resp, len(connection.queries)

    r, one = cost(PLANNER)
    ok(r.status_code == 200, 'the planner answers with one meal on it',
       r.status_code)
    for i in range(1, 7):
        MealEntry.objects.create(
            date=MON + _dt.timedelta(days=i), recipe=soup, servings=6,
            sort_order=1, leftover_of=base_pot, created_by=editor)
        MealEntry.objects.create(
            date=MON + _dt.timedelta(days=i), recipe=None,
            note='Eat out', servings=0, sort_order=2, created_by=editor)
    r, many = cost(PLANNER)
    ok(r.status_code == 200,
       '  and with six leftovers and six notes beside it', r.status_code)
    ok(many <= one, '  for %d queries against %d - no growth at all'
                    % (many, one), (one, many))

    # ----------------------------------------------------------------
    head('3f. the two rows, rendered')
    # ----------------------------------------------------------------
    body = r.content.decode('utf-8', 'replace')
    ok(body.count('leftover-item') >= 6,
       'six leftover rows are drawn as leftover rows',
       body.count('leftover-item'))
    ok(body.count('note-item') >= 6, '  and six note rows as note rows',
       body.count('note-item'))
    ok('Leftovers</span>' in body, '  the leftover row wears its pill')
    ok('Cooked on Mon 19 Oct' in body,
       '  and names the day the pot was cooked on')
    # THE STEPPER IS ON THE MEAL AND NOWHERE ELSE. One real meal on
    # this week, so one stepper - six leftovers and six notes add none.
    ok(body.count('class="servings-step"') == 1,
       'exactly ONE servings stepper on a week of thirteen rows - the '
       'one meal that was actually cooked',
       body.count('class="servings-step"'))
    ok(body.count('icon-action-btn icon-leftover') == 1,
       '  and ONE Leftovers control, on that same meal',
       body.count('icon-action-btn icon-leftover'))
    # COUNTED ON THE CONTROL, NOT ON THE WORDS. The first cut counted
    # the string 'Add Note' and expected seven, then eight - seven day
    # cards and the dialog's submit - and got NINE: MH-3 put an Add
    # Note paragraph in the Meal Plans guide, and the guide is rendered
    # INTO this page by render_help_modal. Three different things say
    # the same two words, so the day controls are counted by the
    # function only they call.
    ok(body.count('onclick="openNote(') == 7,
       '  an Add Note control under each of the seven days',
       body.count('onclick="openNote('))
    ok(body.count('Add Note') == 9,
       '  and the words appear nine times - seven days, the dialog '
       'button, and the guide this page carries',
       body.count('Add Note'))
    # AND A READER GETS NEITHER CONTROL.
    rb = ro.get(PLANNER).content.decode('utf-8', 'replace')
    # THE CONTROL, NOT THE CLASS NAME. base.html defines
    # .icon-duplicate in its own stylesheet, so the bare class is on
    # every rendered page in the application and the first cut of this
    # check failed against base's CSS. The control is the pair.
    ok('icon-action-btn icon-leftover' not in rb,
       'a read-tier user is given no Leftovers control')
    ok('.icon-leftover' in rb,
       '  though base still defines the class, which is why that is '
       'asked of the control and not of the name')
    ok('id="noteModal"' not in rb, '  and no note dialog at all')
    ok('add-recipe-btn-disabled' in rb,
       '  but still sees both Add controls, disabled and saying why')


# ==========================================================================
head('4. WIDE FROM BIRTH, AND THE HOUSE VOCABULARY')
# ==========================================================================
# THE TWO DIALOGS BELONG TO ONE SCREEN, and base owns the id of a More
# menu. A second page with a copy of either is two elements answering to
# one id, which is the fault H8 spent a round removing from 31 pages.
pages_all = T.templates(include_base=False)
ok(len(pages_all) > 100, 'the census reads %d pages in both roots'
   % len(pages_all), len(pages_all))
for mid in DIALOGS:
    holders = [T.rel(p) for p in pages_all
               if 'id="%s"' % mid in T.code_only(read(p))]
    ok(holders == ['meal_planner.html'],
       'only the planner carries %s' % mid, holders)
for fn in ('function openNote(', 'function openLeftover(',
           'function setNote('):
    holders = [T.rel(p) for p in pages_all
               if fn in T.code_only_js(read(p))]
    ok(holders == ['meal_planner.html'],
       'only the planner defines %s' % fn.rstrip('('), holders)

# LEFTOVERS IS COPY. NOT A NEW VERB.
# NV-1c added Notify to the vocabulary and that was right - emailing
# everyone is a thing the record DOES and none of the five families
# covered it. Leftovers is not that: it is the same meal again on
# another day, which is COPY, and alv_rowactions already says what
# colour COPY wears and where it sits. The register's own note settles
# the glyph question: "COPY shares CHANGE's token because base's own
# .icon-duplicate does - the two are told apart by their glyph, not
# their colour."
# LEFTOVERS IS COPY, UNDER ITS OWN NAME, AND THE REGISTER KNOWS IT.
#
# Two mistakes in one control, and the instruments found both.
#
#   THE CLASS. It was written as icon-duplicate, because a leftover is
#   the same meal again on another day and that is COPY - right about
#   the FAMILY, wrong about the class. test_icon_names refused it in
#   under a minute: ".icon-duplicate fa-copy(11) fa-redo(1)". A class
#   carries ONE picture, which base.html states beside .icon-manage in
#   words this round should have read first: alias the colour, never
#   the name.
#
#   THE VERB. With icon-leftover a NEW name, the register did not know
#   it - and verbs_of keeps only the classes it recognises, so the
#   control went SILENTLY MISSING from the whole row-action register.
#   Every row-action suite passed, because as far as any of them could
#   tell the button was not there. That is the worse of the two.
import alv_rowactions                                        # noqa: E402
ok('leftover' in alv_rowactions.FAMILY,
   'leftover is a registered verb - without it verbs_of drops the '
   'control and no row-action check can see it')
ok(alv_rowactions.FAMILY.get('leftover') == alv_rowactions.COPY,
   '  filed under COPY, beside duplicate',
   alv_rowactions.FAMILY.get('leftover'))
ok(alv_rowactions.tone_of('leftover') == '--alv-edit',
   '  on duplicate\'s own token, aliased not invented',
   alv_rowactions.tone_of('leftover'))
ok(alv_rowactions.FAMILY['view'] < alv_rowactions.FAMILY['leftover']
   < alv_rowactions.FAMILY['delete'],
   '  and the order this round writes the three controls in is the '
   'register\'s own')
# AND THE REGISTER READS THE ROW. The claim that matters: not that the
# verb is in a dict, but that the instrument looking at the real markup
# comes back with all three controls in house order.
_tc = T.code_only_js(NOW[TPL])
_arm = _tc.split('{% elif entry.recipe %}')[-1].split('{% empty %}')[0]
_seen = []
for _g, _blk in alv_rowactions.blocks(
        _arm[_arm.find('<div class="row-actions">'):]):
    _seen.extend(alv_rowactions.verbs_of(_blk))
ok(_seen[:3] == ['view', 'leftover', 'delete'],
   'alv_rowactions reads the recipe row as view, leftover, delete',
   _seen[:3])
ok(alv_rowactions.in_order(_seen),
   '  and says it is in house order', _seen)
# THE CONTROL ON THAT CLAIM: the verb really was unknown before.
_before = T.python_code_only(was(os.path.join(ROOT, 'alv_rowactions.py'))) \
    if os.path.isfile(os.path.join(ROOT, 'alv_rowactions.py') + SUFFIX) \
    else None
ok(_before is not None and "'leftover': COPY" not in _before,
   '  CONTROL: and leftover was NOT a verb before this round, which is '
   'why the control would have been invisible')
# NO SEVENTH COLOUR. test_verb_colours counts base's --alv- tokens and
# asserts there are as many as before; an alias that invented one would
# move that number, and this round aliases.
_bnow = set(re.findall(r'--alv-[a-z0-9-]+', NOW[BASE]))
_bwas = set(re.findall(r'--alv-[a-z0-9-]+', was(BASE)))
ok(not (_bnow - _bwas),
   'base gains no new --alv- token - the colour is aliased, not '
   'invented', sorted(_bnow - _bwas))
ok('.icon-leftover' in T.code_only(NOW[BASE]),
   '  and .icon-leftover is a real rule in base, so the control has a '
   'colour at all')
# AND THE PLANNER IS NOT IN THE EXEMPTION REGISTERS. A page that needed
# one would be a page whose action column this round got wrong.
ok('meal_planner.html' not in alv_rowactions.NAMED,
   'the planner needs no loose-button exemption')
ok('meal_planner.html' not in alv_rowactions.VERNACULAR,
   '  and no private action vocabulary - it wears the house classes')

# ==========================================================================
head('5. NO MIGRATION, AND BOTH COLUMNS WERE ALREADY THERE')
# ==========================================================================
migs = os.path.join(ROOT, 'pages', 'migrations')
ours = sorted(n for n in os.listdir(migs)
              if n.endswith('.py') and n[:4].isdigit() and int(n[:4]) > 100)
ok(not ours, 'this round adds NO migration', ours)
mcode = T.python_code_only(read(MODELS))
block = mcode.split('class MealEntry')[1].split('class Menu')[0]
ok('leftover_of = models.ForeignKey(' in block,
   'MealEntry.leftover_of was already there - 0100, push 1')
ok("'self'" in block, '  pointing at MealEntry itself')
ok('null=True, blank=True' in block.split('leftover_of')[1][:200],
   '  and nullable, because most meals are not leftovers')
ok('def counts_on_shopping_list' in mcode,
   'and counts_on_shopping_list was already there too')
ok('return bool(self.recipe) and self.leftover_of_id is None' in mcode,
   '  saying exactly what this round relies on: a note buys nothing '
   'and a leftover was bought once already')

# ==========================================================================
head('6. CONTROLS, REGISTRATION AND THE GATE')
# ==========================================================================
from alv_rounds import ROUNDS                                 # noqa: E402

ok('def add_leftover(' not in T.python_code_only(was(VIEW)),
   'reverting the view takes both views out, so section 1 would FAIL')
ok("name='add_leftover'" not in T.python_code_only(was(URLS)),
   '  and the routes with them')
ok('id="leftoverModal"' not in T.code_only(was(TPL)),
   '  and reverting the planner takes both dialogs')
ok('leftover-item' not in T.code_only(was(TPL)),
   '  leaving a leftover to be drawn as an ordinary meal, with a '
   'stepper that buys nothing')
ok("select_related('recipe', 'leftover_of')"
   not in T.python_code_only(was(VIEW)),
   '  and the week back to one query that cannot print a cooked-on date')

# THE INSTRUMENTS, asked the questions they are trusted with in
# section 1 - all four caught this suite's own author today.
ok('fa-redo' not in T.code_only('{# fa-redo #}'),
   'the markup reader does not see a glyph named in a Django comment')
ok('leftover-item' not in T.code_only(
    '<style>/* .leftover-item */ a{x:1}</style>'),
   '  or a class named in a CSS comment')
ok('stepServings' not in T.code_only_js('<script>// stepServings\n</script>'),
   '  and code_only_js does not see a call named in a // comment')
ok('%-d' not in T.python_code_only('def f():\n    """no %-d"""\n'),
   '  and python_code_only blanks a docstring')

vcode = T.python_code_only(NOW[VIEW])
for bad in ('%-d', '%#d', '%-m', '%#m'):
    ok(bad not in vcode, 'the view uses no %s' % bad)

tpl = NOW[TPL]
ok(tpl.count('/*') == tpl.count('*/'),
   'the planner\'s CSS comments balance - %d /* and %d */'
   % (tpl.count('/*'), tpl.count('*/')))
for o, c in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
    ok(tpl.count(o) == tpl.count(c),
       '  and its %s tags close - %d and %d'
       % (o, tpl.count(o), tpl.count(c)))
ok(tpl.count('{% if ') == tpl.count('{% endif %}'),
   '  and every {%% if %%} has an {%% endif %%} - %d and %d'
   % (tpl.count('{% if '), tpl.count('{% endif %}')))
depth, worst = 0, 0
for m in re.finditer(r'<form\b|</form>', tpl):
    depth += 1 if m.group(0) == '<form' else -1
    worst = max(worst, depth)
ok(worst == 1 and depth == 0,
   '  and no form is nested in another - %d deep, closing at %d'
   % (worst, depth))
tcode = T.code_only_js(tpl)
ok('new bootstrap.Modal' not in tcode,
   '  and no Bootstrap 5 modal call - base loads 4.1.3  [A4]')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:])
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealweek'),
   '  and after .bak_mealweek, the round it reads the planner from  '
   '[lesson 54]', ROUNDS[-4:])
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is on the push gate' % ME)
for text in ('id="noteModal"', 'id="leftoverModal"', 'leftover-item',
             'def add_leftover(',
             "select_related('recipe', 'leftover_of')"):
    ok(text in ps1, '  the pre-flight can see %r' % text)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m is not None, 'test_waiting_down declares a CONVERTED_N')
ok(m and int(m.group(1)) == len(T.CONVERTED),
   '  and it agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))

# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE DAY SPEAKS. A night that is planned and is not cooking,')
print('  and a pot that feeds you three times and is bought once.')
print('')
print('  BOTH COLUMNS WERE ALREADY IN THE MODEL. MealEntry.recipe has')
print('  been nullable and leftover_of has existed since MN-1 on 18')
print('  October; the planner has DRAWN both rows since the same')
print('  afternoon, and MW-1 took care this morning to copy leftovers')
print('  onto a new week correctly. Nothing in the application could')
print('  make either one. A column nobody can fill is a column nobody')
print('  can check.')
print('=' * 74)
sys.exit(1 if failed else 0)
