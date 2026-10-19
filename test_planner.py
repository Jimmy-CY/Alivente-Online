# -*- coding: utf-8 -*-
"""test_planner.py - round MN-1, 18 Oct 2026.

RELEASE 3, PUSH 1. THE CALENDAR IS THE PLAN.

Meals belong to DATES. MealEntry replaces the chain
MealPlan -> MealPlanDay -> MealPlanRecipe, and the planner replaces
SEVEN screens - the plan list, Create, View, Edit, Duplicate, Delete
and the old calendar.

WHAT THIS SUITE ASSERTS

  1   THE MODEL. MealEntry exists, has no workspace field, and its
      recipe is nullable - because not every slot is a recipe.

  2   THE MIGRATION. 0100 depends on 0099, creates three tables, and
      carries NO data migration. Proved by APPLYING it to a disposable
      sqlite and then asking makemigrations --check whether the
      migration and the model agree.

  3   THE SOURCE - the planner, the five views, the routes.

  4   THE CONTROL. Every source claim re-asked of the pre-round
      backups, where every one must FAIL.

  5   THE BEHAVIOUR, driven for real. This is the register that
      matters: a model change is a claim about what the application
      DOES, and source text is a weak proof of it.

  6   THE FIXES THAT MOVE. Release 3 deletes the code release 1 fixed
      and retires the two suites that judged it. The fixes which
      OUTLIVE the shape are re-asserted here, by name, so that
      retiring a suite is not a way to drop a claim.

  7   THE RETIREMENT IS COMPLETE. Four templates and two suites gone,
      their backups on disk, and nothing in the tree still reverses a
      URL that no longer exists.

  8   Scope, registration and the gate.

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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import ast
import io
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_planner'
ME = 'test_planner.py'
PATCHER = 'apply_planner.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MN-1, 18 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
PLANNER = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
SHOP = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_shopping_list.html')
MIG = os.path.join(ROOT, 'pages', 'migrations', '0100_meal_entry.py')

GONE_TEMPLATES = ('meal_plans.html', 'create_meal_plan.html',
                  'view_meal_plan.html', 'meal_plan_calendar.html')
GONE_SUITES = ('test_meal_fixes.py', 'test_meal_display.py')

FILES = (MODELS, VIEW, URLS, SHOP)

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
    """Every source claim MN-1 makes, written once and asked twice.

    The absence claims read the comment-free text. MN-1's own prose
    names MealPlan, MealPlanDay and MealPlanRecipe a dozen times to
    explain what it replaced, and to a substring search a comment
    about a thing is the thing - which cost three wrong checks in
    MP-1, two in MD-1 and one wrong refusal in MD-1's own patcher."""
    c = {}
    mcode = T.python_code_only(text[MODELS])
    vcode = T.python_code_only(text[VIEW])
    ucode = T.python_code_only(text[URLS])

    # ---- 1. the model
    c['MealEntry exists'] = 'class MealEntry(models.Model):' in mcode
    c['  and a meal has a DATE'] = (
        'date = models.DateField(db_index=True)' in mcode)
    c['  with NO workspace field'] = (
        'class MealEntry' in mcode
        and 'workspace' not in mcode.split('class MealEntry')[1]
        .split('class Menu')[0])
    c['  its recipe is NULLABLE - not every slot is a recipe'] = (
        'Recipe, on_delete=models.CASCADE, null=True, blank=True,' in mcode)
    # SCOPED TO THE MealEntry BLOCK, like the workspace claim above.
    # `note = models.CharField(` is on other models in this file, so
    # asking the whole 180 KB was a claim about somebody else's table.
    c['  it carries a note, for the nights you do not cook'] = (
        'class MealEntry' in mcode
        and 'note = models.CharField(' in mcode.split('class MealEntry')[1]
        .split('class Menu')[0])
    c['  and leftover_of, which costs nothing on the list'] = (
        "leftover_of = models.ForeignKey(\n        'self'" in mcode)
    c['  counts_on_shopping_list answers notes and leftovers at once'] = (
        'def counts_on_shopping_list' in mcode
        and 'self.leftover_of_id is None' in mcode)
    c['Menu and MenuItem arrive with it'] = (
        'class Menu(models.Model):' in mcode
        and 'class MenuItem(models.Model):' in mcode)
    c['  and a MenuItem is on a day INDEX, not a date'] = (
        'day_index = models.IntegerField(' in mcode)

    # ---- 3. the views
    c['the aggregator walks entries, not a plan'] = (
        'def aggregate_meal_entries(entries):' in vcode)
    c['  and the plan-walking version is gone'] = (
        'def aggregate_meal_plan_ingredients' not in vcode)
    c['  a note buys nothing and leftovers were bought once'] = (
        'if entry.counts_on_shopping_list:' in vcode)
    c['the planner view exists'] = 'def meal_planner(request):' in vcode
    c['  and normalises the week to a Monday'] = (
        'week_start -= timedelta(days=week_start.weekday())' in vcode)
    c['  in ONE query for the week'] = (
        'MealEntry.objects.filter(date__gte=week_start, date__lte=week_end)'
        in vcode)
    c['add, remove and servings are three views'] = all(
        ('def %s(request):' % n) in vcode
        for n in ('add_meal_entry', 'remove_meal_entry', 'set_meal_servings'))
    c['  the servings view saves and answers JSON'] = (
        "entry.save(update_fields=['servings', 'updated_at'])" in vcode)
    c['  with a floor of one, so - cannot go negative'] = (
        'servings = max(1, min(99, servings))' in vcode)
    c['  and add falls back to the recipe yield, then the household'] = (
        'servings = recipe.servings or household_size(request.user)' in vcode)
    c['household size comes from the roster'] = (
        'def household_size(user):' in vcode
        and 'HouseholdMember.objects.for_user(user)' in vcode)
    c['the shopping list takes a date range'] = (
        'def meal_shopping_list(request):' in vcode)
    c['  with a ceiling, so one date cannot walk the whole table'] = (
        'if (end - start).days > 92:' in vcode)
    c['NOT ONE of the three old models survives in the module'] = not any(
        n in vcode for n in ('MealPlan.', 'MealPlanDay.', 'MealPlanRecipe.'))
    c['  nor is one imported'] = not any(
        ('    %s,' % n) in vcode
        for n in ('MealPlan', 'MealPlanDay', 'MealPlanRecipe'))

    # ---- the routes
    c['the planner has a route'] = (
        "views.meal_planner, name='meal_planner'" in ucode)
    c['  and meal_plans still resolves, so nothing in the tree 404s'] = (
        "views.meal_planner, name='meal_plans'" in ucode)
    c['  and so does meal_plan_calendar, for every old bookmark'] = (
        "views.meal_planner, name='meal_plan_calendar'" in ucode)
    c['the seven screens have no routes left'] = not any(
        ("name='%s'" % n) in ucode for n in
        ('create_meal_plan', 'view_meal_plan', 'edit_meal_plan',
         'duplicate_meal_plan', 'delete_meal_plan',
         'meal_plan_shopping_list', 'add_recipe_to_meal_plan_day',
         'remove_recipe_from_meal_plan'))

    # ---- the shopping list page
    scode = T.code_only_js(text[SHOP])
    # C18 IS A CHANGE CLAIM, NOT A CARRIED ONE. MP-1 made the email
    # count MEALS rather than days; the invariant survives but the
    # EXPRESSION had to be rewritten, because there is no
    # meal_plan_day__meal_plan to count through any more. A claim that
    # names the new expression cannot hold on the old tree, so it
    # belongs here and not in kept().
    c['C18 carries across: the email counts meals, and skips leftovers'] = (
        'recipe__isnull=False, leftover_of__isnull=True).count()' in vcode)
    c['the shopping list page reads the range, not a plan'] = (
        'meal_plan.' not in scode)
    c['  and sends the range when it emails'] = (
        "from: '{{ start|date:\"Y-m-d\" }}'" in scode)
    return c


def kept(text):
    """CLAIMS THAT MUST HOLD IN BOTH TREES - the other register.

    MD-1 and MH-1 learned this the same way: a claim that the round
    did NOT LOSE something cannot fail on the tree as it was, so
    mixing it in with the change claims makes the control unusable.

    Both of these are release-1 work that release 3 had to carry
    across rather than inherit. A5 guarded the calendar's address bar;
    the planner is a different view and has to guard its own. MD-1 put
    a Decimal, guarded multiplier on MealPlanRecipe; MealEntry needed
    its own copy of the same expression, and getting it wrong would
    have put back the ZeroDivisionError MD-1 took out.
    """
    c = {}
    mcode = T.python_code_only(text[MODELS])
    vcode = T.python_code_only(text[VIEW])
    c['A5 survives: the month is range-checked'] = (
        'if not 1 <= month <= 12:' in vcode)
    c['A5 survives: a bad week falls back'] = (
        'except (TypeError, ValueError):' in vcode)
    c['E33 survives: a servings multiplier is Decimal and guarded'] = (
        'Decimal(self.servings) / Decimal(self.recipe.servings or 1)'
        in mcode)
    c['B9 survives: the email recipient must be on the roster'] = (
        'not a household member' in vcode)
    c['C16 survives: the aggregator still tracks the three drops'] = (
        'missing_units.append' in vcode
        and 'missing_shopping_units.append' in vcode)
    c['E32 survives: the module logs rather than printing'] = (
        'logger.exception(' in vcode and 'traceback.print_exc' not in vcode)
    return c


# ==========================================================================
head('1-3. THE MODEL, THE VIEWS AND THE ROUTES')
# ==========================================================================
LIVE = claims(NOW)
for label in sorted(LIVE):
    ok(LIVE[label], label)

KEPT = kept(NOW)
print('')
print('  -- and %d release-1 fixes the round had to CARRY ACROSS --'
      % len(KEPT))
for label in sorted(KEPT):
    ok(KEPT[label], label)

# ==========================================================================
head('4. THE CONTROL - every claim above, asked of the tree BEFORE MN-1')
# ==========================================================================
try:
    BEFORE = dict((p, was(p)) for p in FILES)
except IOError as e:
    BEFORE = None
    ok(False, 'the round backups are on disk', str(e))

if BEFORE is not None:
    OLD = claims(BEFORE)
    ok(sorted(OLD) == sorted(LIVE),
       'the same %d claims are asked of both trees' % len(LIVE),
       'live %d, old %d' % (len(LIVE), len(OLD)))
    held = sorted(k for k in OLD if OLD.get(k))
    ok(not held,
       'ALL %d claims FAIL on the tree as it was - the suite can fail'
       % len(OLD),
       '%d held before the round:\n%s'
       % (len(held), '\n'.join(held[:14])))

    # AND THE OTHER REGISTER, THE OTHER WAY ROUND. These are fixes
    # release 1 made that release 3 had to write again somewhere else,
    # so they hold in both trees - in DIFFERENT FILES, which is the
    # whole point of asking.
    OLDKEPT = kept(BEFORE)
    lost = sorted(k for k in OLDKEPT if not OLDKEPT.get(k))
    ok(not lost,
       'and all %d carried-across fixes held BEFORE the round too'
       % len(OLDKEPT),
       '%d did not:\n%s' % (len(lost), '\n'.join(lost)))

# ==========================================================================
head('5. THE PLANNER PAGE')
# ==========================================================================
P = read(PLANNER)
PC = T.code_only_js(P)
ok("{% extends 'base.html' %}" in PC,
   'the planner extends base, so it inherits every token')
ok('{% load help_modal_tags %}' in PC and 'meal_plansHelpModal' in PC,
   '  and carries the Meal Plans guide, like every meal-plan screen')
ok(PC.count('class="page-action-buttons"') == 1,
   'ONE action bar', PC.count('class="page-action-buttons"'))
# BACK IS LAST, asked of the order in the bar and not of its presence.
_bar = PC.split('class="page-action-buttons"')[1].split('</div>')[0] \
    if 'class="page-action-buttons"' in PC else ''
_bar = PC[PC.index('class="page-action-buttons"'):][:1800]
ok(_bar.index('action-back') > _bar.index('action-secondary'),
   '  and Back is after the Help secondary - Back is last in every bar')
ok('action-back-label' in PC,
   '  with base hiding its label on a phone, not a copy of the rule')
ok(re.search(r'<h2[^>]*>\s*MEAL PLANNER\s*</h2>', PC) is not None,
   'an h2 page title in CAPITALS - the heading standard, for a label')

# NO HEX LITERALS. The 76 template-walking suites judge a new page on
# day one, and this is the one they refuse most often.
_style = re.search(r'<style>(.*?)</style>', PC, re.S)
_css = _style.group(1) if _style else ''
_hex = re.findall(r'#[0-9a-fA-F]{3,6}\b', _css)
ok(not _hex, 'not one hex literal in the planner stylesheet', _hex[:6])
ok('var(--alv-' in _css, '  and it does use the house tokens')

ok('loading="lazy" decoding="async"' in PC,
   'the recipe images are lazy and async')
ok('escapejs' in P,
   'every model string in a JS literal goes through escapejs')
ok(PC.count('|escapejs') >= 6,
   '  at %d sites' % PC.count('|escapejs'), PC.count('|escapejs'))
ok('alert(' not in PC,
   'no alert() - SL-4, and the page has a place to say things')
ok('id="plannerStatus"' in PC, '  which is plannerStatus, and it is a role=status')
ok("$('#pickerModal').modal(" in PC,
   'the picker uses the Bootstrap 4 jQuery API that base actually loads')
ok('new bootstrap.Modal' not in PC,
   '  and not the Bootstrap 5 constructor that A4 spent a release on')
ok('code.jquery.com' not in PC,
   'no second copy of jQuery - E31, and base already loads it')
ok('console.log(' not in PC,
   'no debug tracing left on the page - E32')
ok('class="row-actions"' in PC,
   'the row controls are in a .row-actions wrapper')
_ra = PC[PC.index('class="row-actions"'):][:900]
ok(_ra.index('icon-view') < _ra.index('icon-delete'),
   '  in house order: LOOK before DESTROY')
ok('<label for="pickerSearch"><strong>' in PC,
   'field labels are bold through <strong>, which base pins')
ok('perms.auth.can_edit_recipes' in PC
   and 'can_edit_personal' not in PC,
   'it gates on the tier the views actually check - B11 survives')
ok('min-width: 44px' in _css and 'height: 44px' in _css,
   'the week controls are 44px, which test_tap_target calls the floor')

# ==========================================================================
head('6. THE RETIREMENT - four screens and two suites, deliberately')
# ==========================================================================
# RELEASE 3 DELETES THE CODE RELEASE 1 FIXED, and that is the point
# rather than waste. Nineteen of release 1's items were guards against
# a shape that no longer exists: there is no overlapping plan to warn
# about, no plan dates to drop meals, no day outside a plan, no plan to
# name. What outlives the shape is asserted in section 1-3 and in
# kept() above, by name.
for t in GONE_TEMPLATES:
    p = os.path.join(ROOT, 'pages', 'templates', t)
    ok(not os.path.exists(p), '%s is gone' % t)
    ok(os.path.isfile(p + SUFFIX),
       '  and its backup is on disk, so it can still be compared against')
for s in GONE_SUITES:
    p = os.path.join(ROOT, s)
    ok(not os.path.exists(p), '%s is retired' % s)
    ok(os.path.isfile(p + SUFFIX), '  with its backup beside it')

tr = T.python_code_only(read(os.path.join(ROOT, 'alv_tree.py')))

# THE GATE'S CODE, NOT ITS COMMENTS. MN-1's own note in the suite list
# names both retired suites to explain why they are not there - and to
# a substring search a comment about a thing is the thing. That is the
# FOURTH time today: A4, C14 and the Workspace docstring were the
# others, and each time the answer was to ask an instrument that can
# tell code from prose.
#
# There is no code_only for PowerShell in alv_tree, because nothing
# until now has needed one. A # line comment is the whole of what has
# to go here, and blanking it line for line keeps every line number
# the gate reports meaning what it says.
_ps_raw = read(os.path.join(ROOT, PS1))
ps = re.sub(r'(?m)^([ \t]*)#.*$',
            lambda m: m.group(1) + ' ' * (len(m.group(0)) - len(m.group(1))),
            _ps_raw)
ok('MN-1, 18 Oct 2026 - test_meal_fixes.py' in _ps_raw,
   'CONTROL: the gate really does explain the retirement in a comment')
ok('MN-1, 18 Oct 2026 - test_meal_fixes.py' not in ps,
   'CONTROL: and the comment stripper really strips it')
for s in GONE_SUITES:
    ok(s not in tr, '  %s is out of alv_tree.CONVERTED' % s)
    ok(s not in ps, '  and off the gate, in its code' % ())
    ok(s not in T.CONVERTED, '  and alv_tree agrees when imported')

# THE REGISTER KEEPS ITS HISTORY. The suffixes stay: a retired SUITE
# is not a retired ROUND, and as_left_by() reads those backups to
# answer what a file looked like at each step.
rd = read(os.path.join(ROOT, 'alv_rounds.py'))
for suf in ('.bak_mealfix', '.bak_mealdisplay', '.bak_mealhelp'):
    ok("'%s'" % suf in rd,
       '  %s stays in alv_rounds - history is what it is for' % suf)

# NOTHING IN THE TREE REVERSES A URL THAT NO LONGER EXISTS. This is
# the check that would have caught the whole retirement going wrong:
# recipe_management.html links to `meal_plans` twice, and if that name
# had gone with its view the Recipes page would raise
# NoReverseMatch on every load.
DEAD_URLS = ('create_meal_plan', 'view_meal_plan', 'edit_meal_plan',
             'duplicate_meal_plan', 'delete_meal_plan',
             'meal_plan_shopping_list', 'add_recipe_to_meal_plan_day',
             'remove_recipe_from_meal_plan')
offenders = []
for q in T.templates():
    body = read(q)
    for name in DEAD_URLS:
        # THE PATTERN IS BUILT, NOT FORMATTED. `\{%` in a %-format
        # string is "unsupported format character" - the template
        # syntax this is looking for collides with the operator doing
        # the looking.
        pat = '\\{%\\s*url\\s*[\'"]' + re.escape(name) + '[\'"]'
        if re.search(pat, body):
            offenders.append('%s -> %s' % (T.rel(q), name))
ok(not offenders,
   'no template reverses a URL this round removed', offenders[:8])
ok(re.search('\\{%\\s*url\\s*[\'"]meal_plans[\'"]',
             read(T.path_of('recipe_management.html'))) is not None,
   '  and recipe_management still reverses meal_plans, which still resolves')

# ==========================================================================
head('7. THE MIGRATION - applied, and it agrees with the model')
# ==========================================================================
M = read(MIG)
ok(os.path.isfile(MIG), '0100_meal_entry.py is on disk')
ok("('pages', '0099_recipe_image_display')" in M,
   '  and depends on 0099, which was head before this round')
for name in ('MealEntry', 'Menu', 'MenuItem'):
    ok("name='%s'" % name in M, '  it creates %s' % name)
ok('RunPython' not in M,
   '  and carries NO data migration - the four test plans are cleared '
   'by decision, not converted')
ok(M.count('migrations.CreateModel') == 3,
   '  three tables, and only three', M.count('migrations.CreateModel'))
# THE CODE, NOT THE DOCSTRING. 0100's own docstring says "until 0101
# drops them in push 3" - so asking the raw file whether it mentions
# 0101 refuses the correct migration. FIFTH time today, and the same
# answer each time: ask an instrument that can tell code from prose.
_mcode = T.python_code_only(M)
ok('0101' not in _mcode,
   '  it does not drop the old tables - that is push 3, and it is the '
   'only irreversible step in the release')
ok('DeleteModel' not in _mcode and 'RemoveField' not in _mcode,
   '  and it removes nothing at all')
ok('0101' in M,
   '  CONTROL: it does SAY so, which is why the check reads the code')

# ==========================================================================
head('8. THE BEHAVIOUR, DRIVEN FOR REAL')
# ==========================================================================
# THIS IS THE REGISTER THAT MATTERS FOR A MODEL CHANGE. "The source
# says MealEntry" is a claim about text; "a date in March 2027 takes a
# meal, and the planner costs the same whatever is on it" is a claim
# about the application.
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
    from django.core.management import call_command
    _buf = io.StringIO()
    call_command('migrate', run_syncdb=True, verbosity=0, stdout=_buf)
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    import datetime as _dt
    from decimal import Decimal as _D
    from django.contrib.auth.models import User, Permission
    from django.core.management import call_command
    from django.db import connection, reset_queries
    from django.test import Client
    from pages.models import MealEntry, Menu, MenuItem, Recipe

    # 0100 APPLIED. And the strongest thing that can be asked of a
    # hand-written migration: does it AGREE with the model? 0097 once
    # shipped asserting it was the latest, and this is the check that
    # catches the other half of that.
    ok(True, 'every migration applied to a fresh database, 0100 included')
    _m = io.StringIO()
    try:
        call_command('makemigrations', '--check', '--dry-run',
                     verbosity=1, stdout=_m)
        agreed = True
    except SystemExit:
        agreed = False
    ok(agreed,
       '  and makemigrations --check reports NO CHANGES - the hand-written '
       '0100 matches the three models exactly', _m.getvalue()[-300:])

    u = User.objects.create_user(username='mn_user', password='x',
                                 email='mn@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        u.user_permissions.add(Permission.objects.get(codename=codename))
    cl = Client()
    cl.force_login(u)

    MON = _dt.date(2026, 10, 19)
    WED = _dt.date(2026, 10, 21)
    soup = Recipe.objects.create(recipe_name='Soup for six', servings=6)
    stew = Recipe.objects.create(recipe_name="Yiayia's stew", servings=2)

    def cost(url):
        reset_queries()
        r = cl.get(url)
        return r, len(connection.queries)

    head('8a. the planner answers, and a bad address does not break it')
    for q in ('', '?week=2026-10-21', '?year=abc&month=99&week=nope',
              '?year=99999', '?month=0', '?week=2026-13-45'):
        r, n = cost('/meal_plans/planner/' + q)
        ok(r.status_code == 200, 'GET /meal_plans/planner/%s is 200' % q,
           r.status_code)
    # AND THE OLD NAMES STILL LAND SOMEWHERE. Every bookmark, and every
    # Back control written before today.
    for url in ('/meal_plans/', '/meal_plans/calendar/'):
        r, _ = cost(url)
        ok(r.status_code == 200, '%s still answers' % url, r.status_code)

    head('8b. the week is a Monday, and the row is marked')
    r, _ = cost('/meal_plans/planner/?week=' + WED.strftime('%Y-%m-%d'))
    ok(r.context['week_start'] == MON,
       'a Wednesday opens the Monday of that week',
       r.context['week_start'])
    ok(r.context['week_end'] == MON + _dt.timedelta(days=6),
       '  and ends on the Sunday', r.context['week_end'])
    ok('mini-calendar-week selected' in r.content.decode('utf-8', 'replace'),
       '  and that row is marked selected')

    head('8c. ANY date takes a meal - A3 dissolved, not guarded')
    r = cl.post('/meal_plans/add/',
                {'date': WED.strftime('%Y-%m-%d'),
                 'recipe_id': soup.recipe_id}, follow=True)
    e = MealEntry.objects.filter(recipe=soup).first()
    ok(e is not None and e.date == WED,
       'a recipe lands on the date it was sent', e)
    ok(e is not None and e.servings == 6,
       '  with the recipe own yield, not a 4 - C19 carried across',
       e.servings if e else None)
    # THE DATE THAT MAKES THE POINT. No plan ever covered March 2027,
    # and under the old model a meal could not exist there without one.
    far = _dt.date(2027, 3, 2)
    cl.post('/meal_plans/add/', {'date': far.strftime('%Y-%m-%d'),
                                 'recipe_id': stew.recipe_id,
                                 'servings': 2})
    ok(MealEntry.objects.filter(date=far).exists(),
       'a date no plan ever covered takes a meal - which is the whole '
       'model change in one assertion')

    head('8d. servings save on press, with no Save button')
    r = cl.post('/meal_plans/servings/',
                {'meal_entry_id': e.meal_entry_id, 'servings': 9})
    d = r.json()
    ok(r.status_code == 200 and d.get('servings') == 9,
       'the stepper saves and answers JSON', d)
    ok(abs(float(d.get('scales') or 0) - 1.5) < 0.001,
       '  and says how far the shopping list scales: 9 of 6 is 1.5',
       d.get('scales'))
    r = cl.post('/meal_plans/servings/',
                {'meal_entry_id': e.meal_entry_id, 'servings': 0})
    e.refresh_from_db()
    ok(e.servings == 1,
       '  with a floor of one - minus cannot walk a meal negative',
       e.servings)
    r = cl.post('/meal_plans/servings/',
                {'meal_entry_id': e.meal_entry_id, 'servings': 'abc'})
    ok(r.status_code == 400,
       '  and a non-number is a 400, not a 500', r.status_code)
    r = cl.post('/meal_plans/servings/',
                {'meal_entry_id': 999999, 'servings': 4})
    ok(r.status_code == 404,
       '  and a meal that is gone is a 404', r.status_code)

    head('8e. the query count does not grow with the data')
    # THE CLAIM E29 WAS ABOUT, built in from the start this time rather
    # than retro-fitted. Measured at one week of meals and again at
    # twelve weeks: a per-day or per-meal query would show here.
    _, q_small = cost('/meal_plans/planner/?week=' + MON.strftime('%Y-%m-%d'))
    for k in range(12):
        for i in range(7):
            MealEntry.objects.create(
                date=MON + _dt.timedelta(days=7 * k + i),
                recipe=soup, servings=6, sort_order=i, created_by=u)
    _, q_big = cost('/meal_plans/planner/?week=' + MON.strftime('%Y-%m-%d'))
    ok(q_big == q_small,
       'the planner costs the same with 84 meals as with one - %d queries'
       % q_big, 'one meal: %d, 84 meals: %d' % (q_small, q_big))
    ok(q_big <= 12, '  and that number is under 12', q_big)

    head('8f. the shopping list shops a range')
    r, q = cost('/meal_plans/shopping_list/?from=2026-10-19&to=2026-10-25')
    ok(r.status_code == 200, 'a date range renders a list', r.status_code)
    ok(r.context['start'] == MON and r.context['end'] == MON + _dt.timedelta(days=6),
       '  over the dates it was given',
       (r.context['start'], r.context['end']))
    r, _ = cost('/meal_plans/shopping_list/')
    ok(r.status_code == 200 and r.context['start'].weekday() == 0,
       '  and with no dates at all it opens on this week, from its Monday',
       r.context['start'])
    r, _ = cost('/meal_plans/shopping_list/?from=nope&to=also-nope')
    ok(r.status_code == 200,
       '  a pair of dates nobody could parse is a 200, not a 500',
       r.status_code)
    r, _ = cost('/meal_plans/shopping_list/?from=2026-10-25&to=2026-10-19')
    ok(r.status_code == 200 and r.context['start'] <= r.context['end'],
       '  and a range given backwards is turned round',
       (r.context['start'], r.context['end']))
    r, _ = cost('/meal_plans/shopping_list/?from=1900-01-01&to=2099-01-01')
    ok(r.status_code == 200
       and (r.context['end'] - r.context['start']).days <= 92,
       '  and a range of two centuries is capped at 13 weeks',
       (r.context['end'] - r.context['start']).days)

    head('8g. a note and a leftover cost nothing on the list')
    # PUSH 2 WRITES THESE. The model answers for them now, so that the
    # shopping list is right the day the planner starts writing them
    # rather than the day somebody notices.
    note = MealEntry.objects.create(date=MON, note='Eat out', servings=0)
    ok(not note.counts_on_shopping_list,
       'a note buys nothing')
    ok(note.servings_multiplier == _D('0'),
       '  and scales nothing', note.servings_multiplier)
    orig = MealEntry.objects.create(date=MON, recipe=soup, servings=8)
    left = MealEntry.objects.create(date=MON + _dt.timedelta(days=3),
                                    recipe=soup, servings=4,
                                    leftover_of=orig)
    ok(orig.counts_on_shopping_list,
       'the meal you cook extra of is bought')
    ok(not left.counts_on_shopping_list,
       '  and the night you eat it again is not')
    # AND THE PAGE SURVIVES ONE. The first form of this round assumed
    # every entry had a recipe, so the planner 500d the moment a note
    # existed - found here, before it shipped, which is the whole
    # reason a model change is driven and not read.
    r, _ = cost('/meal_plans/planner/?week=' + MON.strftime('%Y-%m-%d'))
    ok(r.status_code == 200,
       'and the planner renders a week that contains a note',
       r.status_code)
    _b = r.content.decode('utf-8', 'replace')
    ok('Eat out' in _b, '  showing what the note says', 'Eat out' in _b)
    ok('note-item' in _b, '  in a row of its own, quieter than a meal')

    head('8h. remove, and the module has no plan left to break')
    n_was = MealEntry.objects.count()
    cl.post('/meal_plans/remove/', {'meal_entry_id': e.meal_entry_id},
            follow=True)
    ok(MealEntry.objects.count() == n_was - 1,
       'remove takes one meal off', MealEntry.objects.count())
    r = cl.post('/meal_plans/remove/', {'meal_entry_id': 'not-a-number'},
                follow=True)
    ok(r.status_code == 200,
       '  and a meal id nobody could read is a message, not a 500',
       r.status_code)
    import pages.views.recipes.meal_planning as MP
    for dead in ('meal_plans', 'create_meal_plan', 'view_meal_plan',
                 'edit_meal_plan', 'duplicate_meal_plan',
                 'delete_meal_plan', 'meal_plan_calendar',
                 'meal_plan_shopping_list', 'add_recipe_to_meal_plan_day',
                 'remove_recipe_from_meal_plan'):
        ok(not hasattr(MP, dead),
           '  views.%s is gone from the module' % dead)

# ==========================================================================
head('9. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
pa = read(os.path.join(ROOT, PATCHER))
ok(MARK in pa, 'the patcher stamps %s' % MARK)
ok('MP-1 is not applied' in pa or 'is not applied. MN-1 replaces' in pa,
   'and it refuses to run on a tree without the rounds it replaces')
ok('the latest migration is' in pa,
   'and it refuses if the tree has grown a 0100 since it was measured')
ok('Release 3 replaces the plan with the' in pa,
   'and it asks the PARSE TREE whether any of the three old models '
   'survives in the module, because its own comments name all three')

ok(ME in tr and ME in T.CONVERTED,
   '%s is in alv_tree.CONVERTED - judged on day one' % ME)
ok("'%s'" % SUFFIX in rd, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in ps, '%s is in the gate $suites' % ME)
ok('MN-1: the aggregator walks dated entries, not a plan' in ps,
   'and the gate carries a sentinel for the model change')
ok('MN-1: servings save on press, with no Save button' in ps,
   'and a second one for the planner')

# THE COUNTER GOES DOWN, for the first time in this register: one
# suite arrives and two retire with the screens they judged.
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
ok('MN-1, 18 Oct 2026 - one suite in, two retired' in wd,
   'CONVERTED_N records that the count FELL, and why')

missing = [os.path.basename(x) for x in FILES
           if not os.path.isfile(x + SUFFIX)]
ok(not missing, 'every file this round changed has its %s backup' % SUFFIX,
   'missing: %s' % ', '.join(missing))

print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
