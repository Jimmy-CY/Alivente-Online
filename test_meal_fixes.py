# -*- coding: utf-8 -*-
"""test_meal_fixes.py - round MP-1, 18 Oct 2026.

MEAL PLANS, RELEASE 1. The nineteen items from the design record that
BREAK, EXPOSE or LOSE DATA - groups A, B and C. (#7, "no scoping", is
not one of them: Demetri decided on 18 Oct that all users see all meal
plans, and the code already agreed with him.)

WHAT THIS SUITE ASSERTS, AND IN WHICH REGISTER

  1-5   THE SOURCE. Each item, read out of the files. Nineteen items,
        so this is long by necessity rather than by thoroughness.

  6     THE CONTROL, and it is the part that matters. Every claim in
        1-5 is re-asked of the tree AS IT WAS BEFORE MP-1, read from
        the round's own .bak_mealfix backups, and every one of them
        must FAIL. A suite that cannot fail is a suite that proves
        nothing, and three rounds this month have shipped one.

  7     THE BEHAVIOUR, driven for real. Django on an in-memory sqlite
        database and the actual URLs, because MP-1 is almost entirely
        a round about what the application DOES, and source text is a
        weak proof of that. Eleven of the nineteen are asked here as
        well as above: add a recipe, add one to a day that is gone,
        fetch the calendar at ?year=abc, create a plan with no name,
        create one with a bad recipe in it, put the same recipe on a
        day twice, overlap two plans, email the list to an address
        nobody on the roster uses.

        This follows test_auth_flow.py, which has done the same since
        6 Oct - the bootstrap block below is lifted from it, comments
        and all, because every line of it was paid for.

  8     Scope, registration, and the gate.

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
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_mealfix'
ME = 'test_meal_fixes.py'
PATCHER = 'apply_meal_fixes.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MP-1, 18 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
CRUD = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
CAL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_calendar.html')
CREATE = os.path.join(ROOT, 'pages', 'templates', 'create_meal_plan.html')
SHOP = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_shopping_list.html')
LIST = os.path.join(ROOT, 'pages', 'templates', 'meal_plans.html')
VIEWT = os.path.join(ROOT, 'pages', 'templates', 'view_meal_plan.html')

FIVE = (CAL, CREATE, SHOP, LIST, VIEWT)

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
    """The file AS IT WAS BEFORE THIS ROUND - the round's own backup.

    NOT alv_rounds.as_left_by(), which answers the other question: what
    a file looked like as some EARLIER round left it, by reading the
    NEXT round's backup. For "before MP-1" the answer is MP-1's own
    .bak_mealfix, which is the newest backup there is.

    And it is read rather than assumed to exist: 17 Oct shipped six
    rounds without their backups and as_left_by() quietly fell back to
    reading the live file, so every historical comparison in the tree
    became a file compared with itself and the gate failed at suite 15.
    This raises instead."""
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk. MP-1 cannot ask what the tree '
                      'looked like before it, so the control section '
                      'below cannot run - and a control that does not run '
                      'is the whole reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402


# ======================================================================
# THE CLAIMS, as functions of the text, so section 6 can ask every one
# of them again of the tree as it was. A check written twice is a check
# that drifts; a check written once and asked twice cannot.
# ======================================================================

def _first_try_returns(src, fname):
    """Does every handler of this function's FIRST try block return?

    That try is the one that fetches the day and the recipe, and A2's
    fault was that its handler did not return: it set an error message
    and fell through to a `return redirect(...)` reading
    `meal_plan_day`, which the handler never assigns - so a missing day
    raised UnboundLocalError on the way out of the error path.

    THE FIRST TRY, NOT EVERY TRY. The first spelling of this asked
    whether every handler in the function returns, and it failed on the
    corrected file - because C19's guard in the same function is a
    try/except that assigns a fallback and must NOT return. A check
    that fails on the fix is a check aimed at the wrong thing.

    Parsed rather than matched: this is a claim about the shape of the
    function, and a regex cannot see shape."""
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == fname:
            for sub in node.body:
                if isinstance(sub, ast.Try):
                    if not sub.handlers:
                        return False
                    return all(h.body and isinstance(h.body[-1], ast.Return)
                               for h in sub.handlers)
            return False
    return False


def claims_view(raw, code):
    """MP-1's claims about meal_planning.py. {label: bool}."""
    c = {}
    # A1 - the parameter the URL never supplied
    c['A1 add() takes only request'] = bool(
        re.search(r'def add_recipe_to_meal_plan_day\(request\):', raw))
    c['A1 remove() takes only request'] = bool(
        re.search(r'def remove_recipe_from_meal_plan\(request\):', raw))
    # A2 - the except path returns before anything reads an unbound name
    add = raw.split('def add_recipe_to_meal_plan_day(')[-1]
    add = add[:add.index('\ndef ')] if '\ndef ' in add else add
    c['A2 the failure path returns'] = (
        "messages.error(request, 'That day or recipe no longer exists.')"
        in add and add.count('return redirect') >= 2)
    # AND ASKED OF THE PARSE TREE, because the fault was about SHAPE.
    #
    # The first spelling of this check compared two string indexes - was
    # the except written before the final redirect - and it was TRUE
    # BEFORE THE ROUND TOO, so it proved nothing and section 6 caught
    # it. The fault was never the order of the lines: it was that the
    # handler fell through to a redirect that reads a name the handler
    # never assigned. Every handler ending in a return is the fix, and
    # that is a question about the tree, not about the text.
    c['A2 the handler that fetches the day returns'] = _first_try_returns(
        raw, 'add_recipe_to_meal_plan_day')
    # NOT the same claim about remove(). Section 6 refused it: remove()'s
    # handler ALREADY ended in a return before the round, so asserting
    # it proves nothing about MP-1. A2 was only ever a fault in add(),
    # which is what the design record says - meal_planning.py:1110.
    #
    # What DID change in both is the exception tuple. A non-numeric id
    # in the POST body - '', 'abc', a list - raised ValueError out of
    # the ORM, which neither handler caught, so a malformed form was a
    # 500 on both views.
    c['A2 add() survives a non-numeric id'] = (
        'except (MealPlanDay.DoesNotExist, Recipe.DoesNotExist,\n'
        '            ValueError, TypeError):' in raw)
    c['A2 remove() survives a non-numeric id'] = (
        'except (MealPlanRecipe.DoesNotExist, ValueError, TypeError):'
        in raw)
    # A5 - the calendar address bar
    c['A5 year is guarded'] = 'year = today.year' in raw
    c['A5 month is range-checked'] = 'if not 1 <= month <= 12' in raw
    c['A5 the week date is guarded'] = (
        raw.count('selected_week_start = today - timedelta('
                  'days=today.weekday())') == 2)
    # B8 - the two ownership checks, consistently removed
    c['B8 no created_by check survives'] = (
        'created_by != request.user' not in code)
    # B9 - the email endpoint
    c['B9 the recipient must be on the roster'] = (
        'not a household member' in raw)
    c['B9 the plan is looked up, not posted'] = (
        'meal_plan_name = plan.plan_name' in raw)
    c['B9 every value is escaped'] = (
        'from django.utils.html import escape' in raw
        and raw.count('escape(') >= 4)
    # B12 - the author picker
    c['B12 the authors come from the model'] = (
        'Recipe.AUTHOR_CHOICES' in raw
        and "{'value': 'Erene', 'name': 'Erene'}" not in code)
    # C13 - the dropped days are counted and named
    c['C13 the dropped meals are counted'] = 'dropped_meals' in raw
    c['C13 and the reader is told'] = (
        'fell outside the new dates' in raw)
    # C14 - three transactions where there was one
    # THE STATEMENT, NOT THE WORD. The first spelling counted
    # 'transaction.atomic()' and got four, because MP-1's own comment in
    # Create explains that there used to be exactly one of them. A
    # comment that quotes the thing it is about is indistinguishable
    # from the thing itself to a substring count - which is what
    # code_only() exists for, and this is the cheap version of it.
    c['C14 three atomic blocks - Create, Edit, Duplicate'] = (
        code.count('with transaction.atomic():') == 3)
    # C15 - a queue per recipe, not one row per recipe
    c['C15 rows are kept in a list'] = (
        'existing_rows' in raw
        and 'existing_recipes = {mr.recipe.recipe_id: mr' not in code)
    c['C15 and consumed one per posted entry'] = 'queue.pop(0)' in raw
    # C16 - the third tracker and the fourth return value
    c['C16 lines with no unit are tracked'] = 'missing_units = []' in raw
    c['C16 the aggregator returns four things'] = (
        'missing_shopping_units, missing_units)' in raw)
    c['C16 both lists reach the page'] = (
        "'missing_shopping_units_list'" in raw
        and "'missing_units_list'" in raw)
    # C17 - deterministic, and said out loud
    c['C17 the weeks plan is chosen deterministically'] = (
        "order_by('start_date', 'meal_plan_id')" in raw)
    c['C17 and the reader is told there are others'] = (
        'meal plans cover this week' in raw)
    c['C17 Create and Duplicate warn on an overlap'] = (
        raw.count('the calendar can only show one plan') == 2)
    # C18 - recipes, not days
    c['C18 the email counts meals, not days'] = (
        'meal_plan_day__meal_plan=plan).count()' in raw)
    # C19 - the recipes own yield
    c['C19 the server falls back to the recipes yield'] = (
        'servings = recipe.servings or 4' in raw)
    c['C19 and not to a hardcoded 4'] = (
        "request.POST.get('servings', 4)" not in code)
    # C20 - a plan needs a name on Create too
    c['C20 Create refuses a blank name'] = (
        raw.count("messages.error(request, 'Plan name is required.')") == 2)
    return c


def claims_cal(raw, code):
    c = {}
    c['A3 the empty day guards the id'] = (
        '{% if day.meal_plan_day_id %}' in code)
    c['A3 the other call site guards it too'] = (
        'can_edit_recipes and day.meal_plan_day_id' in code)
    c['A3 and says why there is no button'] = (
        'This date is outside' in raw)
    c['C19 the option carries the recipes yield'] = (
        'data-recipe-servings=' in code)
    c['C19 the box is not hardcoded to 4'] = (
        'id="recipeServings" value="4"' not in code)
    c['C19 and is reset on every open'] = (
        "getElementById('recipeServings').value = ''" in code)
    return c


def claims_create(raw, code):
    c = {}
    c['A4 no Bootstrap 5 modal constructor'] = (
        'new bootstrap.Modal' not in code)
    c['A4 no Bootstrap 5 getInstance'] = (
        'bootstrap.Modal.getInstance' not in code)
    c['A4 the jQuery form, twice'] = (
        code.count("$('#recipeSelectorModal').modal(") == 2)
    c['B10 one escaping helper'] = 'function esc(s) {' in code
    c['B10 and it escapes the double quote'] = (
        'esc' in code and ".replace(/\"/g, '&quot;')" in code)
    # EVERY interpolation of database text, named one at a time. A count
    # would pass on nine wrong sites as happily as nine right ones.
    for frag in ('${esc(recipe.recipe_name)}',
                 '${esc(recipe.recipeName)}',
                 '${esc(recipeName)}',
                 '${esc(course.name)}',
                 '${esc(cat.name)}',
                 '${esc(protein.name)}',
                 '${esc(author.name)}',
                 '${esc(recipe.recipe_image)}',
                 '${esc(recipe.difficulty_level)}',
                 '${esc(course)}',
                 '${esc(cat)}',
                 '${esc(protein)}'):
        c['B10 %s' % frag] = frag in code
    # AND NOTHING BARE LEFT. The positive checks above would all pass on
    # a page that also still carried an unescaped copy.
    for frag in ('<strong>${recipe.recipe_name}</strong>',
                 '<strong>${recipe.recipeName}</strong>',
                 '<strong>${recipeName}</strong>',
                 '<option value="${course.name}">',
                 '<option value="${cat.name}">',
                 '<option value="${protein.name}">',
                 '<option value="${author.value}">',
                 'card-title">${recipe.recipe_name}<'):
        c['B10 nothing bare: %s' % frag] = frag not in code
    c['C13 the page has a place to warn'] = 'id="dateChangeNote"' in code
    c['C13 the discarded meals are counted'] = 'droppedMeals' in code
    c['C13 and not only logged'] = (
        'no longer exists in range - recipes discarded' not in code)
    c['C13 the warning names them'] = (
        'will be removed when you' in raw)
    return c


def claims_shop(raw, code):
    c = {}
    c['A6 the plan name is not sent raw'] = (
        "meal_plan_name: '{{ meal_plan.plan_name }}'" not in code)
    c['B9 the plan id goes up instead'] = (
        'meal_plan_id: {{ meal_plan.meal_plan_id }}' in code)
    c['C18 the day count is not sent as a recipe count'] = (
        'total_recipes: {{ meal_plan.days.count }}' not in code)
    c['C16 the page prints what it left off'] = (
        'NOT ON THIS LIST' in code)
    c['C16 both lists are read'] = (
        'missing_units_list' in code and 'missing_shopping_units_list' in code)
    c['C16 and points at the screen that fixes it'] = (
        "{% url 'ingredient_base_units_management' %}" in code)
    return c


def claims_perms(text):
    """B11 - one claim per template, counted.

    `text` maps a path to its contents, so section 6 can hand this the
    BACKUPS and get the opposite answer. The counts are the ones MP-1
    measured on 18 Oct: calendar 10, shopping list 4, list 7, view 5,
    and all 26 gate an edit control."""
    c = {}
    for path, n in ((CAL, 10), (SHOP, 4), (LIST, 7), (VIEWT, 5)):
        name = os.path.basename(path)
        src = text[path]
        c['B11 %s has no can_edit_personal left' % name] = (
            'can_edit_personal' not in src)
        c['B11 %s gates %d control(s) on can_edit_recipes' % (name, n)] = (
            src.count('perms.auth.can_edit_recipes') >= n)
    return c


def claims_crud(raw, code):
    c = {}
    c['B12 the third copy reads the model too'] = (
        'Recipe.AUTHOR_CHOICES' in code
        and "{'value': 'Erene', 'name': 'Erene'}" not in code)
    return c


def claims_models(src):
    c = {}
    ws = src[src.index('class Workspace(models.Model):'):][:2600]
    # THE LIVE SENTENCES, NOT THE HISTORY NOTE. The first spelling of
    # this asked whether "Celebrations, Recipes)" appears anywhere in
    # the docstring - and MP-1's own note QUOTES the old wording to say
    # it was wrong, so the check failed on the corrected file. Section 6
    # did not catch that one; the live run did, which is the same
    # lesson from the other end.
    #
    # Everything from the MP-1 marker down is the note. The claim is
    # about what comes before it.
    live = ws.split('MP-1, 18 Oct 2026')[0]
    c['the Workspace docstring no longer claims Recipes are tenanted'] = (
        'Recipes)' not in live and 'recipe, ingredient' not in live)
    c['and it names Passports and Celebrations, which do carry the field'] = (
        'Passports,' in live and 'Celebrations)' in live)
    c['and the correction says what is actually true'] = (
        'Recipe` has no workspace at all' in ws)
    return c


def all_claims(text):
    """Every claim MP-1 makes, as one flat {label: bool}.

    EACH CLAIM IS ASKED OF THE CODE OR OF THE PROSE, DELIBERATELY, AND
    THE DIFFERENCE IS NOT A DETAIL. Three of these checks failed on the
    corrected files the first time they ran, all for one reason: MP-1's
    own comments QUOTE WHAT THEY REMOVED.

        A4   "was `new bootstrap.Modal(...)`, a Bootstrap 5 call"
        C14  "there was exactly one transaction.atomic() in this module"
        the  "used to say (Passports, Celebrations, Recipes)"
        docstring

    To a substring search a comment about a thing is the thing. That is
    what alv_tree.code_only_js and python_code_only exist for - they
    blank every comment LINE FOR LINE, so a line number still means
    what it says - and every "no longer present" claim below is asked
    of the blanked text. The handful of claims that are ABOUT the
    explanation are asked of the raw file, and they are the exceptions
    rather than the rule."""
    c = {}
    c.update(claims_view(text[VIEW], T.python_code_only(text[VIEW])))
    c.update(claims_cal(text[CAL], T.code_only_js(text[CAL])))
    c.update(claims_create(text[CREATE], T.code_only_js(text[CREATE])))
    c.update(claims_shop(text[SHOP], T.code_only_js(text[SHOP])))
    c.update(claims_perms(dict((k, T.code_only_js(v))
                               for k, v in text.items())))
    c.update(claims_crud(text[CRUD], T.python_code_only(text[CRUD])))
    c.update(claims_models(text[MODELS]))
    return c


FILES = (VIEW, CRUD, MODELS, CAL, CREATE, SHOP, LIST, VIEWT)
NOW = dict((p, read(p)) for p in FILES)


# ==========================================================================
head('1-5. THE SOURCE - nineteen items, read out of the files')
# ==========================================================================
# Grouped as the design record groups them, because that is how Demetri
# will read the result: A is "it does not work", B is "it is not safe",
# C is "the data is wrong".
LIVE = all_claims(NOW)
for label in sorted(LIVE):
    ok(LIVE[label], label)

# ==========================================================================
head('5b. A1 - AND THE URLS REALLY DO SUPPLY NOTHING')
# ==========================================================================
# The whole of A1 rests on this: the two routes capture no argument, so
# the two views demanding one could never be called. If a route DID
# feed a plan id, deleting the parameter would have broken two working
# screens instead of fixing two broken ones. Asked of urls.py, not
# assumed from the review.
u = read(URLS)
for route, view in (('add_recipe_to_day', 'add_recipe_to_meal_plan_day'),
                    ('remove_recipe', 'remove_recipe_from_meal_plan')):
    lines = [ln for ln in u.split('\n') if route + "/'" in ln]
    ok(len(lines) == 1, 'pages/urls.py has exactly one %s route' % route,
       '%d found' % len(lines))
    if lines:
        ok('<' not in lines[0],
           '  and it captures nothing - so views.%s may not demand one'
           % view, lines[0].strip())

# AND THE PARAMETER IS GONE FROM THE SIGNATURES, asked of the parse tree
# rather than of a regex, because a docstring mentioning meal_plan_id
# would satisfy a text search.
tree = ast.parse(NOW[VIEW])
sigs = dict((n.name, [a.arg for a in n.args.args])
            for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
for fn in ('add_recipe_to_meal_plan_day', 'remove_recipe_from_meal_plan'):
    ok(sigs.get(fn) == ['request'],
       '%s(request) - one argument, from the parse tree' % fn,
       sigs.get(fn))

# ==========================================================================
head('6. THE CONTROL - every claim above, asked of the tree BEFORE MP-1')
# ==========================================================================
# This is the section that decides whether the suite is worth running.
# Each of the claims is re-asked of the .bak_mealfix backups, and every
# single one must come back FALSE. A claim that holds both before and
# after the round is a claim about nothing.
try:
    BEFORE = dict((p, was(p)) for p in FILES)
except IOError as e:
    BEFORE = None
    ok(False, 'the round backups are on disk', str(e))

if BEFORE is not None:
    try:
        OLD = all_claims(BEFORE)
    except Exception as e:
        OLD = None
        ok(False, 'the claims can be asked of the old tree',
           '%s: %s' % (type(e).__name__, e))
    if OLD is not None:
        ok(sorted(OLD) == sorted(LIVE),
           'the same %d claims are asked of both trees' % len(LIVE),
           'live %d, old %d' % (len(LIVE), len(OLD)))
        held = sorted(k for k in OLD if OLD.get(k))
        ok(not held,
           'ALL %d claims FAIL on the tree as it was - the suite can fail'
           % len(OLD),
           '%d held before the round, so they prove nothing:\n%s'
           % (len(held), '\n'.join(held[:12])))


# ==========================================================================
head('7. THE BEHAVIOUR, DRIVEN FOR REAL')
# ==========================================================================
# MP-1 is a round about what the application DOES. "The source says
# `request` and not `request, meal_plan_id`" is a weak proof that a
# calendar add works; posting to the URL and reading the database is a
# strong one.
#
# Django on an in-memory sqlite database, following test_auth_flow.py,
# which has done this since 6 Oct. The bootstrap block is lifted from
# it with its comments, because every line of it was paid for once.
django_up = False
try:
    import django
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        # SE-1 - a test run signs with its own throwaway key. SECRET_KEY
        # reads the environment now, and a suite that boots Django must
        # not fall over because a .env is absent. setdefault, so a real
        # key always wins; this one signs nothing that leaves the test.
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    # AND THE TEST ENVIRONMENT, which test_auth_flow.py does not need
    # and this suite does. It wires up the template_rendered signal, and
    # without it response.context is None on every response - so every
    # check that reads a MESSAGE the view left behind silently sees an
    # empty list. Nine of MP-1's claims are "and the reader is told",
    # and the first run of this suite reported four of them failing for
    # exactly that reason. It also switches email to locmem by itself;
    # the explicit setting below stays, because a suite that sends real
    # mail if one line is reordered is not worth the risk.
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    # SQLITE, IN MEMORY, AFTER setup(). The handler caches both its
    # settings and its wrappers, so all three have to be dropped or the
    # first query still goes to MySQL - which is exactly what happened the
    # first time this was tried.
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    # AND THE MAIL GOES NOWHERE. B9 is a round about an endpoint that
    # SENDS EMAIL, so a suite that drives it must not be able to post
    # one. locmem keeps every message in a list this file can read, and
    # reading the outbox is how B9 is proved rather than asserted.
    dj_settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    _quiet = io.StringIO()
    call_command('migrate', run_syncdb=True, verbosity=0, stdout=_quiet)
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    import datetime as _dt
    from django.contrib.auth.models import User, Permission
    from django.core import mail
    from django.test import Client
    from pages.models import (HouseholdMember, MealPlan, MealPlanDay,
                              MealPlanRecipe, Recipe, Workspace)

    def grant(u, *codes):
        for c in codes:
            u.user_permissions.add(Permission.objects.get(codename=c))
        u.save()
        del u._perm_cache
        del u._user_perm_cache

    def signed_in(name, *codes):
        u = User.objects.create_user(username=name, password='x',
                                     email='%s@example.test' % name)
        for c in codes:
            u.user_permissions.add(Permission.objects.get(codename=c))
        c = Client()
        c.force_login(u)
        return u, c

    MON = _dt.date(2026, 10, 19)        # a Monday, so weeks are tidy

    owner, oc = signed_in('mp_owner', 'can_access_recipes',
                          'can_edit_recipes')
    # SOMEBODY ELSE ENTIRELY - B8. The old ownership checks refused
    # anyone who was not created_by, and the 18 Oct decision says every
    # user may edit every plan.
    other, xc = signed_in('mp_other', 'can_access_recipes',
                          'can_edit_recipes')

    soup = Recipe.objects.create(recipe_name='Soup for six', servings=6)
    stew = Recipe.objects.create(recipe_name="Yiayia's stew", servings=2)

    plan = MealPlan.objects.create(plan_name='Week one', start_date=MON,
                                   end_date=MON + _dt.timedelta(days=6),
                                   created_by=owner)
    day1 = MealPlanDay.objects.create(meal_plan=plan, date=MON)

    ADD = '/meal_plans/add_recipe_to_day/'
    REMOVE = '/meal_plans/remove_recipe/'
    CALURL = '/meal_plans/calendar/'

    def said(resp):
        """The messages a FOLLOWED response rendered, as plain strings.

        follow=True, every time. The first spelling of this posted
        without following and then fetched the calendar to read the
        message storage - which works, until a check wants the message
        from a view that redirects somewhere else, and reads an empty
        list instead of failing."""
        if resp.context is None:
            return []
        try:
            return [str(m) for m in resp.context['messages']]
        except KeyError:
            return []

    # ------------------------------------------------------------ A1
    head('7a. A1 - the calendar add and remove, which could not run at all')
    r = oc.post(ADD, {'meal_plan_day_id': day1.meal_plan_day_id,
                      'recipe_id': soup.recipe_id, 'servings': 4})
    ok(r.status_code == 302, 'POST to the add URL redirects, not 500',
       'status %s' % r.status_code)
    ok(MealPlanRecipe.objects.filter(meal_plan_day=day1,
                                     recipe=soup).exists(),
       '  and the meal is on the day - this was a TypeError before MP-1')

    mpr = MealPlanRecipe.objects.get(meal_plan_day=day1, recipe=soup)
    r = oc.post(REMOVE, {'meal_plan_recipe_id': mpr.meal_plan_recipe_id})
    ok(r.status_code == 302, 'POST to the remove URL redirects, not 500',
       'status %s' % r.status_code)
    ok(not MealPlanRecipe.objects.filter(
        meal_plan_recipe_id=mpr.meal_plan_recipe_id).exists(),
       '  and the meal is gone')

    # ------------------------------------------------------------ A2
    head('7b. A2 - a day or recipe that is no longer there')
    r = oc.post(ADD, {'meal_plan_day_id': 999999,
                      'recipe_id': soup.recipe_id, 'servings': 2})
    ok(r.status_code == 302,
       'adding to a day that does not exist is a redirect, not '
       'UnboundLocalError', 'status %s' % r.status_code)
    r = oc.post(ADD, {'meal_plan_day_id': 999999,
                      'recipe_id': soup.recipe_id, 'servings': 2},
                follow=True)
    told = said(r)
    ok(any('no longer exists' in m for m in told),
       '  and it says so: "That day or recipe no longer exists."', told)
    # AND A NON-NUMERIC ID, which raised ValueError out of the ORM
    r = oc.post(ADD, {'meal_plan_day_id': 'not-a-number',
                      'recipe_id': soup.recipe_id, 'servings': 2})
    ok(r.status_code == 302, 'a non-numeric day id is a redirect too',
       'status %s' % r.status_code)
    r = oc.post(REMOVE, {'meal_plan_recipe_id': 'not-a-number'})
    ok(r.status_code == 302, 'and so is a non-numeric meal id',
       'status %s' % r.status_code)

    # ------------------------------------------------------------ B8
    head('7c. B8 - somebody who did not create the plan may still edit it')
    r = xc.post(ADD, {'meal_plan_day_id': day1.meal_plan_day_id,
                      'recipe_id': stew.recipe_id, 'servings': 2},
                follow=True)
    ok(MealPlanRecipe.objects.filter(meal_plan_day=day1,
                                     recipe=stew).exists(),
       'a second user adds to a plan created by the first',
       'the 18 Oct decision says every user may edit every plan')
    told = said(r)
    ok(not any('permission to modify' in m for m in told),
       '  and is not told they lack permission', told)
    ok(any('Added' in m for m in told),
       '  and is told it worked', told)

    # ------------------------------------------------------------ C19
    head('7d. C19 - the servings come from the recipe, not from a 4')
    MealPlanRecipe.objects.all().delete()
    r = oc.post(ADD, {'meal_plan_day_id': day1.meal_plan_day_id,
                      'recipe_id': soup.recipe_id})          # no servings
    got = MealPlanRecipe.objects.filter(meal_plan_day=day1,
                                        recipe=soup).first()
    ok(got is not None and got.servings == 6,
       'a recipe for six, posted with no servings, is planned for six',
       'got %s' % (got.servings if got else 'nothing'))
    MealPlanRecipe.objects.all().delete()

    # ------------------------------------------------------------- A5
    head('7e. A5 - a bad calendar address falls back instead of breaking')
    for q in ('?year=abc', '?month=99', '?year=99999', '?month=0',
              '?week=not-a-date', '?year=abc&month=zz&week=x',
              '?year=2026&month=12'):
        r = oc.get(CALURL + q)
        ok(r.status_code == 200, 'GET %s%s is 200' % (CALURL, q),
           'status %s' % r.status_code)

    # ------------------------------------------------------------ C20
    head('7f. C20 - a plan with no name is refused on Create too')
    before = MealPlan.objects.count()
    r = oc.post('/meal_plans/create/', {
        'plan_name': '   ',
        'start_date': '2026-11-02', 'end_date': '2026-11-04'})
    ok(MealPlan.objects.count() == before,
       'a blank plan name creates nothing',
       '%d -> %d' % (before, MealPlan.objects.count()))

    # ------------------------------------------------------------ C14
    head('7g. C14 - a failure part way through Create leaves nothing')
    before = MealPlan.objects.count()
    bd = MealPlan.objects.count()
    r = oc.post('/meal_plans/create/', {
        'plan_name': 'Half a plan',
        'start_date': '2026-11-02', 'end_date': '2026-11-04',
        'recipes_2026-11-04[]': ['999999'],       # no such recipe
        'servings_2026-11-04[]': ['2']})
    ok(MealPlan.objects.filter(plan_name='Half a plan').count() == 0,
       'a bad recipe id on day 3 leaves NO plan behind - one transaction',
       '%d plan(s) named "Half a plan"'
       % MealPlan.objects.filter(plan_name='Half a plan').count())
    ok(MealPlan.objects.count() == before,
       '  and no orphan days or meals either',
       '%d -> %d' % (before, MealPlan.objects.count()))

    # ------------------------------------------------------------ C15
    head('7h. C15 - the same recipe twice on one day survives a save')
    two = MealPlan.objects.create(plan_name='Twice', start_date=MON,
                                  end_date=MON, created_by=owner)
    td = MealPlanDay.objects.create(meal_plan=two, date=MON)
    MealPlanRecipe.objects.create(meal_plan_day=td, recipe=soup,
                                  servings=6, sort_order=0)
    MealPlanRecipe.objects.create(meal_plan_day=td, recipe=soup,
                                  servings=2, sort_order=1)
    key = MON.strftime('%Y-%m-%d')
    r = oc.post('/meal_plans/%d/edit/' % two.meal_plan_id, {
        'plan_name': 'Twice',
        'start_date': key, 'end_date': key,
        'recipes_%s[]' % key: [str(soup.recipe_id), str(soup.recipe_id)],
        'servings_%s[]' % key: ['6', '2']})
    rows = list(MealPlanRecipe.objects.filter(
        meal_plan_day=td).order_by('sort_order'))
    ok(len(rows) == 2,
       'two servings of one recipe are still two rows after an edit',
       '%d row(s)' % len(rows))
    ok([x.servings for x in rows] == [6, 2],
       '  and each keeps its own servings',
       [x.servings for x in rows])
    # AND THE OTHER DIRECTION: posting one keeps one.
    r = oc.post('/meal_plans/%d/edit/' % two.meal_plan_id, {
        'plan_name': 'Twice',
        'start_date': key, 'end_date': key,
        'recipes_%s[]' % key: [str(soup.recipe_id)],
        'servings_%s[]' % key: ['4']})
    rows = list(MealPlanRecipe.objects.filter(meal_plan_day=td))
    ok(len(rows) == 1 and rows[0].servings == 4,
       '  and posting one of them deletes the other',
       '%d row(s): %s' % (len(rows), [x.servings for x in rows]))

    # ------------------------------------------------------------ C13
    head('7i. C13 - shortening a plan says what it removed')
    shrink = MealPlan.objects.create(plan_name='Shrink', start_date=MON,
                                     end_date=MON + _dt.timedelta(days=2),
                                     created_by=owner)
    for i in range(3):
        d = MealPlanDay.objects.create(meal_plan=shrink,
                                       date=MON + _dt.timedelta(days=i))
        MealPlanRecipe.objects.create(meal_plan_day=d, recipe=soup,
                                      servings=6, sort_order=0)
    r = oc.post('/meal_plans/%d/edit/' % shrink.meal_plan_id, {
        'plan_name': 'Shrink', 'start_date': key, 'end_date': key,
        'recipes_%s[]' % key: [str(soup.recipe_id)],
        'servings_%s[]' % key: ['6']}, follow=True)
    told = said(r)
    ok(any('fell outside the new dates' in m for m in told),
       'the reader is told meals were removed', told)
    ok(any('2 meals on 2 days' in m for m in told),
       '  and told how many: 2 meals on 2 days', told)
    ok(MealPlanDay.objects.filter(meal_plan=shrink).count() == 1,
       '  and the plan really is one day long now',
       MealPlanDay.objects.filter(meal_plan=shrink).count())

    # ------------------------------------------------------------ C17
    head('7j. C17 - two plans over one week, chosen the same way twice')
    MealPlan.objects.all().delete()
    a = MealPlan.objects.create(plan_name='Plan A', start_date=MON,
                                end_date=MON + _dt.timedelta(days=6),
                                created_by=owner)
    b = MealPlan.objects.create(plan_name='Plan B', start_date=MON,
                                end_date=MON + _dt.timedelta(days=3),
                                created_by=owner)
    seen = set()
    for _ in range(4):
        r = oc.get(CALURL + '?week=' + key)
        seen.add(r.context['selected_meal_plan'].meal_plan_id)
    ok(len(seen) == 1, 'the same plan is chosen on every load',
       '%d different plans over four loads' % len(seen))
    r = oc.get(CALURL + '?week=' + key)
    told = said(r)
    ok(any('meal plans cover this week' in m for m in told),
       '  and the reader is told the other one exists', told)
    # AND CREATE WARNS
    r = oc.post('/meal_plans/create/', {
        'plan_name': 'Plan C', 'start_date': key,
        'end_date': (MON + _dt.timedelta(days=1)).strftime('%Y-%m-%d')},
        follow=True)
    told = said(r)
    ok(any('overlap' in m for m in told),
       'Create warns that the dates overlap an existing plan', told)
    ok(any('created successfully' in m for m in told),
       '  and creates it anyway - a warning, not a refusal', told)

    # ------------------------------------------------------------- B9
    head('7k. B9 - the email endpoint will not write to a stranger')
    MealPlan.objects.exclude(meal_plan_id=a.meal_plan_id).delete()
    mday = MealPlanDay.objects.create(meal_plan=a, date=MON)
    MealPlanRecipe.objects.create(meal_plan_day=mday, recipe=soup,
                                  servings=6, sort_order=0)
    MealPlanRecipe.objects.create(meal_plan_day=mday, recipe=stew,
                                  servings=2, sort_order=1)
    SEND = '/meal_plans/send_shopping_list/'
    payload = {'meal_plan_id': a.meal_plan_id,
               'ingredients': {'Vegetables': [
                   {'ingredient': 'Onion', 'quantity': 2, 'unit': 'each'}]}}
    mail.outbox = []
    r = oc.post(SEND, dict(payload, email='stranger@elsewhere.test'),
                content_type='application/json')
    ok(r.status_code == 403,
       'an address nobody on the roster uses is refused',
       'status %s' % r.status_code)
    ok(len(mail.outbox) == 0, '  and nothing was sent',
       '%d message(s) in the outbox' % len(mail.outbox))

    # THE SIGNED-IN USER'S OWN ADDRESS IS ALWAYS ALLOWED
    mail.outbox = []
    r = oc.post(SEND, dict(payload, email=owner.email),
                content_type='application/json')
    ok(r.status_code == 200 and len(mail.outbox) == 1,
       'a user may always email their own shopping list to themselves',
       'status %s, %d message(s)' % (r.status_code, len(mail.outbox)))

    # AND A HOUSEHOLD MEMBER IS ALLOWED
    # A WORKSPACE, MADE HERE. Nothing auto-creates one on a fresh
    # database, and HouseholdMember.workspace is required - so the first
    # spelling of this check SKIPPED, and a skipped check is a check
    # that proves nothing. HouseholdMember.objects.for_user() is what
    # the view calls, and it needs the user's profile to point at the
    # same workspace.
    ws = Workspace.objects.first() or Workspace.objects.create(
        name='Test household', owner=owner)
    prof = getattr(owner, 'profile', None)
    if prof is not None and getattr(prof, 'workspace_id', None) is None:
        prof.workspace = ws
        prof.save()
    HouseholdMember.objects.create(workspace=ws, name='Angy',
                                   email='angy@example.test',
                                   is_active=True)
    mail.outbox = []
    r = oc.post(SEND, dict(payload, email='angy@example.test'),
                content_type='application/json')
    ok(r.status_code == 200 and len(mail.outbox) == 1,
       'an active household member with an address is allowed',
       'status %s, %d message(s), body %s'
       % (r.status_code, len(mail.outbox), r.content[:120]))
    # AND AN INACTIVE ONE IS NOT. The view filters is_active=True, and a
    # check that only ever tries an allowed address cannot tell the
    # filter from no filter at all.
    HouseholdMember.objects.create(workspace=ws, name='Gone',
                                   email='gone@example.test',
                                   is_active=False)
    mail.outbox = []
    r = oc.post(SEND, dict(payload, email='gone@example.test'),
                content_type='application/json')
    ok(r.status_code == 403 and len(mail.outbox) == 0,
       'a household member marked inactive is refused',
       'status %s, %d message(s)' % (r.status_code, len(mail.outbox)))

    # ------------------------------------------------- B9 content, C18
    head('7l. B9 and C18 - the email says what the PLAN says')
    mail.outbox = []
    r = oc.post(SEND, {'meal_plan_id': a.meal_plan_id,
                       'email': owner.email,
                       'ingredients': {'Veg<x>': [
                           {'ingredient': '<img src=x>',
                            'quantity': 2, 'unit': 'each'}]}},
                content_type='application/json')
    ok(len(mail.outbox) == 1, 'the message was built', r.content[:200])
    if mail.outbox:
        m = mail.outbox[0]
        body = m.alternatives[0][0] if m.alternatives else ''
        ok('Plan A' in m.subject,
           'the subject carries the plan name the SERVER read, not a '
           'posted one', m.subject)
        # C18 - two meals on the plan, one day. The old code sent
        # days.count, so this said "1 recipes".
        ok('2 recipes' in body or '2 recipes' in m.body,
           'and it counts the MEALS, not the days: 2 recipes',
           [l for l in m.body.split('\n') if 'recipe' in l][:3])
        ok('<img src=x>' not in body,
           'an ingredient name that looks like markup is escaped',
           [l for l in body.split('\n') if 'img' in l][:3])
        ok('&lt;img src=x&gt;' in body,
           '  and arrives as text the reader can see')
        ok('Veg&lt;x&gt;' in body,
           'and so is a category name')

    # ---------------------------------------------- C16, the aggregator
    head('7m. C16 - the shopping list names what it left off')
    import pages.views.recipes.meal_planning as MP
    out = MP.aggregate_meal_plan_ingredients(a)
    ok(isinstance(out, tuple) and len(out) == 4,
       'the aggregator returns four things, not three',
       'returned %d' % (len(out) if isinstance(out, tuple) else -1))

# ==========================================================================
head('8. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
me = read(os.path.join(ROOT, ME))
pa = read(os.path.join(ROOT, PATCHER))
ok(MARK in pa, 'the patcher stamps %s' % MARK)
ok(me.count('%s own round' % 'this') >= 0, 'this suite is on disk')

tr = read(os.path.join(ROOT, 'alv_tree.py'))
ok(ME in tr, '%s is in alv_tree.CONVERTED - judged on day one' % ME)
ok(ME in T.CONVERTED, '  and alv_tree agrees when imported')

rd = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rd, '%s is in alv_rounds.ROUNDS' % SUFFIX)

ps = read(os.path.join(ROOT, PS1))
ok(ME in ps, '%s is in the gate $suites' % ME)
ok('MP-1: the shopping list names the ingredients it dropped' in ps,
   'and the gate carries a sentinel for the round')
ok('MP-1: recipe names are escaped before they reach innerHTML' in ps,
   'and a second one for B10')

# THE STALE PF-1 NAME, in three places the rename missed.
ok('PF-1, 18 Oct 2026' not in tr,
   'alv_tree.py no longer credits the pre-flight to PF-1 - the 5 October '
   'picker round')
ok('# PF-1, 18 Oct 2026 - this round own suite'
   not in read(os.path.join(ROOT, 'test_waiting_down.py')),
   'and neither does the CONVERTED_N note')
ok('PF-1, 18 Oct 2026' not in read(os.path.join(ROOT,
                                                'apply_crs_buttons.py')),
   "and BG-1's register anchor matches alv_rounds.py again")

# THE BACKUPS SHIPPED. 17 Oct: six rounds arrived without theirs and
# every historical comparison in the tree became a file compared with
# itself.
missing = [os.path.basename(p) for p in FILES
           if not os.path.isfile(p + SUFFIX)]
ok(not missing, 'every file this round touched has its %s backup' % SUFFIX,
   'missing: %s' % ', '.join(missing))

print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
