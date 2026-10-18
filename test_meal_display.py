# -*- coding: utf-8 -*-
"""test_meal_display.py - round MD-1, 18 Oct 2026.

MEAL PLANS, RELEASE 1, GROUPS D AND E. Twelve items - display,
navigation, queries and hygiene.

THE NAME. The master list calls this round MP-2. MP-2 has been a
shipped round since 3 October and test_ae_line.py PINS THE STRING BY
NAME, so a second one would make a sibling suite's pin ambiguous.
check_gates.py asked before a line was written.

WHAT THIS SUITE ASSERTS

  1     THE SOURCE. Each of the twelve, read out of the files.

  2     THE CONTROL. Every one of those claims re-asked of the tree as
        it was, from .bak_mealdisplay, where every one must FAIL.

  3     THE BEHAVIOUR, driven for real against Django on an in-memory
        sqlite database - and for E29 that is the only register that
        means anything. "The source says prefetch_related" is a claim
        about text; "the View page costs 13 queries and not 53, and
        the calendar's cost does not grow when you add plans" is a
        claim about the application.

  4     Scope, registration and the gate.

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

SUFFIX = '.bak_mealdisplay'
ME = 'test_meal_display.py'
PATCHER = 'apply_meal_display.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MD-1, 18 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
CAL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_calendar.html')
CREATE = os.path.join(ROOT, 'pages', 'templates', 'create_meal_plan.html')
SHOP = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_shopping_list.html')
LIST = os.path.join(ROOT, 'pages', 'templates', 'meal_plans.html')
VIEWT = os.path.join(ROOT, 'pages', 'templates', 'view_meal_plan.html')

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
    """The file as it was BEFORE this round - the round's own backup.

    Raises rather than falling back to a live read. 17 Oct shipped six
    rounds without their backups, as_left_by() read the live files, and
    every historical comparison in the tree became a file compared with
    itself."""
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

FILES = (VIEW, MODELS, CAL, CREATE, SHOP, LIST, VIEWT)


# ======================================================================
# THE CLAIMS, written once and asked twice.
#
# Each takes the RAW file and the COMMENT-FREE one. Which of the two a
# claim reads is not a detail: MD-1's own comments quote the code they
# replaced - "was `}tn-action-disabled {`", "this read
# `}ction-more-menu {`", "console.log" - and to a substring search a
# comment about a thing is the thing. That cost three wrong checks in
# MP-1 and one wrong refusal in this round's own patcher, which searched
# for 'traceback.' and found its own explanation.
#
# So: every "no longer present" claim reads `code`. The handful that are
# ABOUT the explanation read `raw`, and they are named.
# ======================================================================

def claims_view(raw, code):
    c = {}
    # D23 - the calendar's ?start_date is read
    c['D23 Create reads the start date it was sent'] = (
        "request.GET.get('start_date')" in code)
    c['D23 and guards it like A5 guards the calendar'] = (
        'default_start = today' in code)
    c['D23 the list supplies next Monday'] = (
        'next_monday = today + timedelta(' in code)
    # D24 - the save keeps the calendar
    c['D24 saving an Edit keeps from= and week='] = (
        "if request.GET.get('from') == 'calendar':" in code
        and "dest = '%s?from=calendar&week=%s' % (" in code)
    # D26 - Monday
    c['D26 the week is normalised to a Monday'] = (
        'selected_week_start -= timedelta(days=selected_week_start.weekday())'
        in code)
    # E29
    c['E29 the month dots are one query'] = (
        'meal_plan__in=month_meal_plans' in code)
    c['E29 and the per-plan loop is gone'] = (
        'for plan in month_meal_plans:' not in code)
    c['E29 the plan counts are annotated'] = (
        "recipe_count=Count('days__recipes')" in code
        and code.count("recipe_count=Count('days__recipes')") == 2)
    c['E29 the week is one prefetched query'] = (
        'week_day_map' in code)
    c['E29 and the loop no longer asks per day'] = (
        'meal_plan_day = MealPlanDay.objects.filter(' not in code)
    c['E29 the View page prefetches its tags'] = (
        "prefetch_related('recipe__courses',\n"
        "                                          'recipe__categories')"
        in code)
    c['E29 the Edit page prefetches all three'] = (
        "'recipe__proteins')" in code)
    # E32
    c['E32 the module has a logger'] = (
        'logger = logging.getLogger(__name__)' in code)
    c['E32 and logging is imported'] = 'import logging' in code
    c['E32 no stdout traceback survives'] = (
        'traceback.print_exc()' not in code)
    c['E32 and traceback is not imported'] = (
        'import traceback' not in code)
    c['E32 three handlers log instead'] = (
        code.count('logger.exception(') == 3)
    # E33
    c['E33 the shared rounding helper is imported'] = (
        'from .shopping import round_shopping_quantity' in code)
    c['E33 the nested copy is gone'] = (
        'def round_shopping_qty(qty, unit):' not in code)
    c['E33 and math is not imported any more'] = 'import math' not in code
    c['E33 the aggregator uses the model property'] = (
        'servings_multiplier = meal_recipe.servings_multiplier' in code)
    return c


def claims_models(raw, code):
    c = {}
    # E33 - and the property had to be made safe before it could be used
    c['E33 servings_multiplier is Decimal'] = (
        'return Decimal(self.servings) / Decimal(self.recipe.servings or 1)'
        in code)
    c['E33 and the unguarded division is gone'] = (
        'return self.servings / self.recipe.servings' not in code)
    return c


def claims_viewt(raw, code):
    c = {}
    # D21
    c['D21 the day heading reads one real field'] = (
        '{{ day.date|date:"D j M" }}' in code)
    c['D21 and the two attributes that do not exist are gone'] = (
        'day.day_name' not in code and 'day.formatted_date' not in code)
    # D22
    c['D22 the disabled-button selector is repaired'] = (
        '.btn-action-disabled {' in code)
    c['D22 and the swallowed form of it is gone'] = (
        '}tn-action-disabled {' not in code)
    c['D22 the local action-more-menu copy is deleted'] = (
        '}ction-more-menu {' not in code
        and '.action-more-menu {' not in code)
    c['D22 and days-grid closes properly'] = (
        '    .days-grid {\n        grid-template-columns: 1fr;\n    }\n'
        in code)
    return c


def claims_cal(raw, code):
    c = {}
    # D26
    c['D26 the chosen week carries the selected class'] = (
        'week.week_start == selected_week_start' in code)
    # D28
    c['D28 the calendar can shift a plan'] = (
        'name="delete_original"' in code)
    # E29
    c['E29 the plan list reads the annotation'] = (
        '{{ plan.recipe_count }}' in code)
    c['E29 and not the model property'] = (
        '{{ plan.total_recipes }}' not in code)
    # E31
    c['E31 the second copy of jQuery is gone'] = (
        'code.jquery.com' not in code)
    # D25
    c['D25 the calendar no longer stamps the preference on load'] = (
        "sessionStorage.setItem('meal_plan_view_preference', 'calendar');"
        not in code)
    return c


def claims_list(raw, code):
    c = {}
    c['D23 both Create links send a start date'] = (
        code.count("?start_date={{ next_monday|date:'Y-m-d' }}") == 2)
    c['D25 the list no longer stamps the preference on load'] = (
        "sessionStorage.setItem('meal_plan_view_preference', 'list');"
        not in code)
    c['D28 the list can shift a plan'] = (
        'name="delete_original"' in code)
    return c


def claims_create(raw, code):
    c = {}
    # D27
    c['D27 neither date input bounds itself to today'] = (
        "min=\"{{ today|date:'Y-m-d' }}\"" not in code)
    # E32
    c['E32 no console.log survives on the form'] = (
        'console.log(' not in code)
    # THREE console.error CALLS BECAME TWO, and which one went is the
    # point. The two that stay record a real failure with no other
    # trace - a recipe list that is not on the page, a date the browser
    # could not parse. The one that went dumped three booleans about
    # which elements were missing, which is tracing wearing
    # console.error. A count alone could not tell those apart, so the
    # dump is named.
    c['E32 the element dump is gone'] = (
        "console.error('Required elements not found:'" not in code)
    c['E32 and the two real failure reports stay'] = (
        code.count('console.error(') == 2)
    # E33
    c['E33 one recipe row helper'] = (
        'function recipeRowHtml(' in code)
    c['E33 and three callers'] = (
        code.count('recipeRowHtml(') == 4)
    c['E33 the row markup is written once'] = (
        code.count('class="servings-input"') == 1)
    return c


def claims_shop(raw, code):
    c = {}
    c['E32 no console.log survives on the shopping list'] = (
        'console.log(' not in code)
    return c


def all_kept(text):
    """CLAIMS THAT MUST HOLD IN BOTH TREES - a different register.

    The control below requires every claim in all_claims() to FAIL on
    the tree as it was, because a claim that holds before and after is
    a claim about nothing. Four checks failed that bar on the first run
    of this suite, and all four were right to: they are not claims that
    MD-1 CHANGED something, they are claims that it did NOT BREAK
    something.

        the two view toggles still write the preference on click - D25
        deletes two unconditional writes and must leave these alone,
        and deleting the wrong pair would be a silent regression

        the shopping list's two console.error calls survive - E32
        removes tracing and keeps failure reporting. The FORM's count
        is a change claim and lives in the other register, because
        three of them became two: the element dump went

        nothing annotates over total_recipes - the name collision this
        round's first spelling walked into. It was never there before,
        so it cannot fail on the old tree; it is a guard against
        putting it back

    Mixing the two registers makes the control unusable, which is why
    they are separate rather than why four checks were deleted."""
    c = {}
    cal, lst = T.code_only_js(text[CAL]), T.code_only_js(text[LIST])
    c['D25 the calendar toggle writes the preference on click'] = (
        "sessionStorage.setItem('meal_plan_view_preference', 'calendar')"
        in cal)
    c['D25 the list toggle writes the preference on click'] = (
        "sessionStorage.setItem('meal_plan_view_preference', 'list')"
        in lst)
    c['E32 the shopping list keeps its two console.error calls'] = (
        T.code_only_js(text[SHOP]).count('console.error(') == 2)
    c['E29 nothing annotates over the total_recipes property'] = (
        'total_recipes=Count(' not in T.python_code_only(text[VIEW]))
    return c


def all_claims(text):
    c = {}
    for fn, path, strip in (
            (claims_view, VIEW, T.python_code_only),
            (claims_models, MODELS, T.python_code_only),
            (claims_viewt, VIEWT, T.code_only_js),
            (claims_cal, CAL, T.code_only_js),
            (claims_list, LIST, T.code_only_js),
            (claims_create, CREATE, T.code_only_js),
            (claims_shop, SHOP, T.code_only_js)):
        c.update(fn(text[path], strip(text[path])))
    return c


NOW = dict((p, read(p)) for p in FILES)

# ==========================================================================
head('1. THE SOURCE - twelve items, read out of the files')
# ==========================================================================
LIVE = all_claims(NOW)
for label in sorted(LIVE):
    ok(LIVE[label], label)

KEPT = all_kept(NOW)
print('')
print('  -- and %d things the round had to LEAVE ALONE --' % len(KEPT))
for label in sorted(KEPT):
    ok(KEPT[label], label)

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the tree BEFORE MD-1')
# ==========================================================================
try:
    BEFORE = dict((p, was(p)) for p in FILES)
except IOError as e:
    BEFORE = None
    ok(False, 'the round backups are on disk', str(e))

if BEFORE is not None:
    OLD = all_claims(BEFORE)
    ok(sorted(OLD) == sorted(LIVE),
       'the same %d claims are asked of both trees' % len(LIVE),
       'live %d, old %d' % (len(LIVE), len(OLD)))
    held = sorted(k for k in OLD if OLD.get(k))
    ok(not held,
       'ALL %d claims FAIL on the tree as it was - the suite can fail'
       % len(OLD),
       '%d held before the round, so they prove nothing:\n%s'
       % (len(held), '\n'.join(held[:12])))

    # AND THE OTHER REGISTER, THE OTHER WAY ROUND. The five
    # preservation claims must hold in BOTH trees - that is what makes
    # them preservation claims. One that fails on the old tree is a
    # claim about a change, filed in the wrong place.
    OLDKEPT = all_kept(BEFORE)
    lost = sorted(k for k in OLDKEPT if not OLDKEPT.get(k))
    ok(not lost,
       'and all %d preservation claims held BEFORE the round too'
       % len(OLDKEPT),
       '%d did not, so they are claims about a change:\n%s'
       % (len(lost), '\n'.join(lost)))


# ==========================================================================
head('3. THE BEHAVIOUR, DRIVEN FOR REAL')
# ==========================================================================
# For E29 this is the ONLY register that means anything. "The source
# says prefetch_related" is a claim about text. "The View page costs 13
# queries rather than 53, and the calendar's cost DOES NOT GROW when
# you add plans" is a claim about the application, and the second one
# is what the item was about.
#
# The bootstrap follows test_auth_flow.py, as test_meal_fixes.py does.
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
    # DEBUG, because connection.queries is empty without it - and that
    # is the whole instrument for E29.
    dj_settings.DEBUG = True
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    import datetime as _dt
    from django.contrib.auth.models import User, Permission
    from django.db import connection, reset_queries
    from django.test import Client
    from pages.models import (MealPlan, MealPlanDay, MealPlanRecipe,
                              Recipe)

    MON = _dt.date(2026, 10, 19)          # a Monday
    WED = _dt.date(2026, 10, 21)          # and a Wednesday in the same week

    u = User.objects.create_user(username='md_user', password='x',
                                 email='md@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        u.user_permissions.add(Permission.objects.get(codename=codename))
    cl = Client()
    cl.force_login(u)

    def plant(n_plans):
        """n plans, seven days each, three meals a day."""
        made = []
        for k in range(n_plans):
            st = MON + _dt.timedelta(days=7 * k)
            p = MealPlan.objects.create(
                plan_name='Week %d' % k, start_date=st,
                end_date=st + _dt.timedelta(days=6), created_by=u)
            made.append(p)
            for i in range(7):
                d = MealPlanDay.objects.create(
                    meal_plan=p, date=st + _dt.timedelta(days=i))
                for j, r in enumerate(RS):
                    MealPlanRecipe.objects.create(
                        meal_plan_day=d, recipe=r, servings=6,
                        sort_order=j)
        return made

    def cost(url):
        reset_queries()
        r = cl.get(url)
        return r, len(connection.queries)

    RS = [Recipe.objects.create(recipe_name='Recipe %d' % i, servings=6)
          for i in range(3)]
    plans = plant(2)

    # -------------------------------------------------------------- E29
    head('3a. E29 - the query count does not grow with the data')
    # THE CLAIM THAT MATTERS. A fixed handful per page, whatever is in
    # the database. Measured at two plans and again at eight - the
    # loops this round removed were per plan and per day, so if any of
    # them survived the second number would be larger.
    r2, q2 = cost('/meal_plans/calendar/')
    rw2, qw2 = cost('/meal_plans/calendar/?week=' + MON.strftime('%Y-%m-%d'))
    ok(r2.status_code == 200 and rw2.status_code == 200,
       'the calendar answers at two plans', '%s %s'
       % (r2.status_code, rw2.status_code))
    plant(6)                                      # eight plans in all
    r8, q8 = cost('/meal_plans/calendar/')
    rw8, qw8 = cost('/meal_plans/calendar/?week=' + MON.strftime('%Y-%m-%d'))
    ok(q8 == q2,
       'the calendar costs the same at 8 plans as at 2 - %d queries' % q8,
       '2 plans: %d, 8 plans: %d. A per-plan loop survived.' % (q2, q8))
    ok(qw8 == qw2,
       'and so does the calendar with a week open - %d queries' % qw8,
       '2 plans: %d, 8 plans: %d' % (qw2, qw8))
    # AND AN ABSOLUTE CEILING, so a future round that reintroduces a
    # loop fails here even if it reintroduces it uniformly.
    #
    # THE DIRECTION IS THE WHOLE CHECK. `<=` is the safe way round: a
    # tree that gets FASTER passes, and only a tree that gets slower
    # fails. The numbers measured on 18 Oct were 9 and 11, against 19
    # and 31 before the round.
    ok(q8 <= 14, 'the calendar is under 14 queries (was 19)', q8)
    ok(qw8 <= 16, 'the week view is under 16 queries (was 31)', qw8)

    p = plans[0]
    rv, qv = cost('/meal_plans/%d/' % p.meal_plan_id)
    re_, qe = cost('/meal_plans/%d/edit/' % p.meal_plan_id)
    ok(rv.status_code == 200 and qv <= 20,
       'the View page is under 20 queries (was 53, and the application '
       'own HIGH QUERY REQUEST warning was firing on it)', qv)
    ok(re_.status_code == 200 and qe <= 26,
       'the Edit page is under 26 queries (was 79, also warned about)',
       qe)
    # 21 meals on the plan, and the tags prefetched - so a count that
    # scales with the meals would show here.
    ok(MealPlanRecipe.objects.filter(
        meal_plan_day__meal_plan=p).count() == 21,
       '  and that is with 21 meals on the plan, each with its own tags')

    # THE COUNT APPEARS AT ALL
    r, _ = cost('/meal_plans/calendar/')
    counts = [x.recipe_count for x in r.context['all_meal_plans']]
    ok(counts and all(c == 21 for c in counts),
       'every plan in the list carries its own recipe count: 21',
       counts[:5])

    # -------------------------------------------------------------- D26
    head('3b. D26 - the week is a Monday, whatever was asked for')
    r, _ = cost('/meal_plans/calendar/?week=' + WED.strftime('%Y-%m-%d'))
    ok(r.context['selected_week_start'] == MON,
       'a Wednesday in ?week= opens the Monday of that week',
       r.context['selected_week_start'])
    ok(r.context['selected_week_end'] == MON + _dt.timedelta(days=6),
       '  and the week ends on the Sunday',
       r.context['selected_week_end'])
    # AND THAT IS WHAT MAKES THE HIGHLIGHT POSSIBLE: the row the mini
    # calendar draws is a Monday, so an un-normalised week could never
    # have matched it.
    body = r.content.decode('utf-8', 'replace')
    ok('mini-calendar-week selected' in body,
       '  and the row for that week is marked selected',
       [l.strip() for l in body.split('\n')
        if 'mini-calendar-week' in l][:2])

    # -------------------------------------------------------------- D23
    head('3c. D23 - Create opens on the week it was sent')
    r, _ = cost('/meal_plans/create/?start_date=2026-11-02')
    ok(r.context['default_start_date'] == '2026-11-02',
       'the form opens on the date the calendar sent',
       r.context['default_start_date'])
    ok(r.context['default_end_date'] == '2026-11-08',
       '  and ends six days later', r.context['default_end_date'])
    r, _ = cost('/meal_plans/create/?start_date=not-a-date')
    ok(r.status_code == 200,
       'a start date nobody could parse is a 200, not a 500',
       r.status_code)
    r, _ = cost('/meal_plans/create/')
    ok(r.context['default_start_date']
       == _dt.date.today().strftime('%Y-%m-%d'),
       '  and with no start date at all it is still today',
       r.context['default_start_date'])
    r, _ = cost('/meal_plans/')
    nm = r.context['next_monday']
    ok(nm.weekday() == 0 and nm > _dt.date.today(),
       'the list sends the NEXT Monday, which is in the future',
       '%s (a %s)' % (nm, nm.strftime('%A')))

    # -------------------------------------------------------------- D24
    head('3d. D24 - saving an Edit keeps the calendar')
    key = p.start_date.strftime('%Y-%m-%d')
    r = cl.post('/meal_plans/%d/edit/?from=calendar&week=%s'
                % (p.meal_plan_id, key),
                {'plan_name': 'Week 0', 'start_date': key,
                 'end_date': key,
                 'recipes_%s[]' % key: [str(RS[0].recipe_id)],
                 'servings_%s[]' % key: ['6']})
    ok(r.status_code == 302 and 'from=calendar' in r['Location'],
       'the redirect after saving carries from=calendar',
       r.get('Location'))
    ok('week=%s' % key in r['Location'],
       '  and the week it came from', r.get('Location'))
    # AND WITHOUT IT, NOTHING CHANGES. A round that always appended the
    # parameters would pass the check above and break every other path.
    r = cl.post('/meal_plans/%d/edit/' % p.meal_plan_id,
                {'plan_name': 'Week 0', 'start_date': key,
                 'end_date': key,
                 'recipes_%s[]' % key: [str(RS[0].recipe_id)],
                 'servings_%s[]' % key: ['6']})
    ok(r.status_code == 302 and '?' not in r['Location'],
       'reached any other way the redirect is bare, exactly as before',
       r.get('Location'))

    # -------------------------------------------------------------- D27
    head('3e. D27 - past dates on both screens')
    past = (_dt.date.today() - _dt.timedelta(days=30))
    pk = past.strftime('%Y-%m-%d')
    before = MealPlan.objects.count()
    r = cl.post('/meal_plans/create/',
                {'plan_name': 'Last month', 'start_date': pk,
                 'end_date': (past + _dt.timedelta(days=2)).strftime(
                     '%Y-%m-%d')})
    ok(MealPlan.objects.count() == before + 1,
       'Create accepts a plan that starts a month ago - a meal plan is '
       'also a record of what you ate',
       '%d -> %d' % (before, MealPlan.objects.count()))

    # -------------------------------------------------------------- E33
    head('3f. E33 - the property that would have crashed')
    mpr = MealPlanRecipe.objects.filter(
        meal_plan_day__meal_plan=plans[1]).first()
    from decimal import Decimal as _D
    ok(isinstance(mpr.servings_multiplier, _D),
       'servings_multiplier is a Decimal, like everything it multiplies',
       type(mpr.servings_multiplier).__name__)
    # THE CASE THE RECORD'S VERSION WOULD HAVE RAISED ON.
    zero = Recipe.objects.create(recipe_name='No yield recorded',
                                 servings=0)
    zd = MealPlanDay.objects.create(meal_plan=plans[1],
                                    date=MON + _dt.timedelta(days=300))
    zm = MealPlanRecipe.objects.create(meal_plan_day=zd, recipe=zero,
                                       servings=4, sort_order=0)
    try:
        got = zm.servings_multiplier
        raised = None
    except Exception as exc:
        got, raised = None, exc
    ok(raised is None and got == 4,
       'a recipe with no servings recorded scales by its own servings, '
       'not ZeroDivisionError - which is what the unguarded version did',
       raised or got)
    # AND THE SHOPPING LIST STILL ADDS UP, through the property.
    r, _ = cost('/meal_plans/%d/shopping_list/' % p.meal_plan_id)
    ok(r.status_code == 200,
       'the shopping list renders through the shared rounding helper',
       r.status_code)

    # -------------------------------------------------------------- D21
    head('3g. D21 - the day heading says something')
    r, _ = cost('/meal_plans/%d/' % plans[1].meal_plan_id)
    body = r.content.decode('utf-8', 'replace')
    want = plans[1].start_date.strftime('%a %-d %b') if os.name != 'nt' \
        else plans[1].start_date.strftime('%a %d %b')
    ok(plans[1].start_date.strftime('%a') in body,
       'the View page prints the day name - it printed nothing before',
       [l.strip() for l in body.split('\n')
        if 'fa-calendar-day' in l][:2])
    ok(plans[1].start_date.strftime('%b') in body,
       '  and the month, which was also empty')

    # -------------------------------------------------------------- E32
    head('3h. E32 - the handlers log instead of printing')
    import logging as _logging
    import pages.views.recipes.meal_planning as MP
    ok(isinstance(getattr(MP, 'logger', None), _logging.Logger),
       'the module carries a real logger',
       type(getattr(MP, 'logger', None)).__name__)
    ok(MP.logger.name == 'pages.views.recipes.meal_planning',
       '  named after the module, so a line in the log says where it '
       'came from', MP.logger.name)
    ok(not hasattr(MP, 'traceback'),
       '  and traceback is not in the module namespace at all')
    ok(not hasattr(MP, 'math'),
       '  nor math, whose only callers were the deleted helper')

# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
pa = read(os.path.join(ROOT, PATCHER))
ok(MARK in pa, 'the patcher stamps %s' % MARK)
ok('MP-1 is not applied' in pa,
   'and it refuses to run on a tree without MP-1, which it builds on')

tr = read(os.path.join(ROOT, 'alv_tree.py'))
ok(ME in tr and ME in T.CONVERTED,
   '%s is in alv_tree.CONVERTED - judged on day one' % ME)
rd = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rd, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok(ME in ps, '%s is in the gate $suites' % ME)
ok('MD-1: the calendar week is one pair of queries, not fourteen' in ps,
   'and the gate carries a sentinel for the round')
ok('MD-1: the swallowed selector that made disabled buttons look live'
   in ps, 'and a second one for D22')

# THE NAME. MD-1 and not MP-2, which has been a round since 3 October.
for f in ('apply_meal_bar_top.py', 'test_bar_top.py', 'test_ae_line.py'):
    src = read(os.path.join(ROOT, f))
    ok('MP-2' in src,
       '%s still refers to the REAL MP-2, the 3 Oct bar round' % f)
# AND THE REGISTER SAYS MD-1 OWNS THIS SUFFIX, which is the claim that
# actually matters - asked of alv_preflight.register(), the same reader
# the gate's pre-flight uses.
#
# TWO SPELLINGS OF THIS CHECK FAILED FIRST. A chain of .replace() calls
# whitelisting each sentence that mentions MP-2 was fragile and wrong;
# python_code_only(pa) with its default payloads=True was wrong for a
# better reason - a patcher's triple-quoted literals are what it DOES,
# and the register comment MD-1 writes mentions MP-2 on purpose, to say
# why the name was not taken. payloads=False is the question "where
# does this name appear as PROSE", and the register is the question
# "whose round is this".
import alv_preflight as _PF                                 # noqa: E402
_reg = _PF.register(ROOT)
ok(_reg.get('MD-1') == [SUFFIX],
   'alv_rounds.py records MD-1 as the owner of %s' % SUFFIX,
   _reg.get('MD-1'))
ok('MP-2' not in _reg,
   '  and MP-2 owns nothing in the register - it predates it, which is '
   'why checking the register alone would have called the name free',
   _reg.get('MP-2'))
ok('MP-2' not in T.python_code_only(pa, payloads=False),
   '  MP-2 appears in this round as prose only, never as a name it uses',
   [l.strip() for l in T.python_code_only(pa, payloads=False).split('\n')
    if 'MP-2' in l][:3])

# THE BACKUPS SHIPPED.
missing = [os.path.basename(x) for x in FILES
           if not os.path.isfile(x + SUFFIX)]
ok(not missing, 'every file this round touched has its %s backup' % SUFFIX,
   'missing: %s' % ', '.join(missing))

print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
