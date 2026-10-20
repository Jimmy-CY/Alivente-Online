# -*- coding: utf-8 -*-
"""test_pick_filter.py - round PF-2, 19 Oct 2026.

RELEASE 3, PUSH 3. THE PICKER ASKS THE SAME QUESTION THE LIBRARY DOES.

Demetri, testing the live planner: "I don't think that this picker is
any good at all. It only allows you to choose Course. We need to be
able to select Author, Favorites, Category and Protein (or
vegetarian)."

All four already existed. recipe_management has filtered by every one
of them since long before the planner did, with these exact GET
parameter names and the same `vegetarian` magic value. The picker was
ignoring a feature the application already had.

THE DECISION THIS ROUND TURNS ON. Four more data- attributes and a
JavaScript matcher was an hour's work. It would also have been a
SECOND description of what `Protein: Chicken` selects, in a second
language, free to drift from the first - and the whole purpose of the
suites in this project is to refuse that. Demetri chose the server.

So the burden of proof here is unusual: this round moved a filter that
a live screen depends on, and the thing that must be shown is that
NOTHING MOVED. Two independent proofs, because one would not be
enough for a change of this shape.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One shared module holds every clause; the library
      holds none of them; all five controls are in the markup; the
      endpoint and its route exist.

  2   THE REPLAY, which needs no database. The library's OLD filter
      block is lifted out of its own backup and EXECUTED against a
      recorder, beside the new shared function, over every
      combination of the five filters. The ORM calls must match
      exactly - 384 selections, no exceptions.

  3   THE SAME ANSWER ON REAL DATA. A library is built in sqlite with
      known courses, categories, proteins, authors and favourites.
      For each selection the library PAGE and the picker ENDPOINT are
      both asked, and must name the same recipes. The replay proves
      the calls match; this proves the rows do.

  4   RENDERED, at 1200 and at 390. Five controls, a menu that opens
      and closes, 44px targets on the phone, and the planner page
      shipping NO recipe cards where it used to ship every one in the
      library.

  5   WIDE. One description of a recipe filter in the whole tree.

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
import sys
import textwrap

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_pickfilter'
ME = 'test_pick_filter.py'
PATCHER = 'apply_pick_filter.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PF-2, 19 Oct 2026'

FILT = os.path.join(ROOT, 'pages', 'views', 'recipes', '_recipe_filter.py')
CRUD = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py')
MEAL = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

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

# DJANGO IS STARTED HERE, NOT IN SECTION 3. The replay imports the
# shared filter, which imports the models, so the app registry has to
# exist before section 2 runs. Section 3 then swaps the DATABASES
# setting for an in-memory sqlite and migrates it - a reconfiguration,
# not a second boot.
DJ_READY = False
try:
    # ITS OWN TEST KEY FIRST - the house convention, which
    # test_settings_env polices. settings.py reads SECRET_KEY from the
    # environment since E13, so on a checkout with no .env the setting
    # is empty and anything touching a session dies with
    # ImproperlyConfigured. A fixed throwaway, never the real one, and
    # setdefault so a machine that HAS a key keeps it.
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django                                           # noqa: E402
    django.setup()
    DJ_READY = True
except Exception as _e:                                   # pragma: no cover
    print('  !! Django would not start: %s' % str(_e)[:90])

FSRC = read(FILT)
CSRC = read(CRUD)
MSRC = read(MEAL)
TSRC = read(TPL)
CODEF = T.python_code_only(FSRC, payloads=True)
CODEC = T.python_code_only(CSRC, payloads=True)
CODEM = T.python_code_only(MSRC, payloads=True)
MARKUP = T.code_only(TSRC)
# ASKED OF THE SCRIPT, NOT OF THE FILE - narrowed by DC-1,
# 19 Oct 2026. code_only_js returns the markup too, so a Django
# `{% if recipe.is_vegetarian %}` that renders a TAG read as a copy of
# the matching in the browser. A template tag runs on the server; that
# it never reaches the browser is what this claim is about.
JS = T.code_only_js(''.join(
    re.findall(r'<script[^>]*>(.*?)</script>', TSRC, re.S)))

CLAUSES = (
    ('recipe_name__icontains', 'search by name'),
    ('recipe_ingredients__ingredient__name__icontains',
     'search by ingredient'),
    ('courses__recipe_course_id__in', 'course'),
    ('categories__recipe_category_id__in', 'category'),
    ('proteins__custom_protein_id__in', 'protein'),
    ('is_vegetarian=True', 'vegetarian'),
    ('author__in', 'author'),
    ('favourited_by__user', 'favourites'),
)


# ==========================================================================
head('1. THE SOURCE - ONE DESCRIPTION, AND THE LIBRARY GAVE ITS UP')
# ==========================================================================
for clause, what in CLAUSES:
    ok(clause in CODEF,
       'the shared filter carries the %s clause' % what)
ok('.distinct()' in CODEF,
   '  and the distinct() - four of the five join a many-to-many, and a '
   'recipe in two selected categories comes back twice without it')

for clause, what in CLAUSES:
    if clause == 'is_vegetarian=True':
        continue
    ok(clause not in CODEC,
       'recipe_crud no longer carries the %s clause' % what,
       'it would be a second description, free to drift')
ok('filter_recipes(recipes, _sel, request.user)' in CODEC,
   '  it calls the shared one instead')
ok('from pages.views.recipes._recipe_filter import' in CODEC,
   '  and imports it')

ok('def picker_recipes(' in CODEM, 'the picker endpoint exists')
ok('filter_recipes(' in CODEM and 'selected_from(' in CODEM,
   '  and answers with the SAME function, not a copy of it')
ok('all_recipes' not in CODEM,
   'all_recipes has left the planner view - it was every recipe in the '
   'library, prefetched and rendered on every page load')
ok('all_recipes' not in MARKUP,
   '  and the template no longer loops it')
ok("name='picker_recipes'" in read(URLS),
   'the route is registered')

# ALL FIVE CONTROLS, asked of the markup with comments blanked.
for nm, what in (('course', 'Courses'), ('category', 'Categories'),
                 ('protein', 'Proteins'), ('author', 'Authors')):
    ok('name="%s"' % nm in MARKUP,
       'the picker has a %s control' % what.lower()[:-1])
ok('value="vegetarian"' in MARKUP,
   '  and Vegetarian rides in the protein menu as a literal - it is a '
   'column and not a row, so it has no id, and recipe_management has '
   'done exactly this since before the planner existed')
ok('id="pickerFav"' in MARKUP, '  and Favourites is its own button')

# THE OLD COURSE STRIP IS GONE, by its declarations - not by its name
# as a substring, because `pickerCourse` is a substring of the id
# `pickerCourseBtn` that this round ADDS.
ok('var pickerCourse' not in JS and 'function pickCourse(' not in JS,
   "PK-1's course-only strip and its global are gone")
ok('onclick="pickCourse(' not in MARKUP,
   '  and nothing calls the handler that left')

# EVERY onclick NAMES A FUNCTION THIS PAGE DEFINES. PK-1's dialog
# could not open at all for a release because of a call that was never
# defined here.
dead = [fn for fn in sorted(set(re.findall(r'onclick="(\w+)\(', MARKUP)))
        if ('function %s(' % fn) not in JS]
ok(not dead,
   'every onclick on this page names a function it defines',
   'undefined: %s' % ', '.join(dead))


# ==========================================================================
head('2. THE REPLAY - THE OLD BLOCK AND THE NEW ONE, SIDE BY SIDE')
# ==========================================================================
# NO DATABASE NEEDED, AND THAT IS THE POINT. The library's own filter
# block is lifted out of recipe_crud's backup and EXECUTED against a
# recorder that logs every .filter() it is given, beside the new
# shared function, over every combination of the five filters.
#
# "It behaves the same" is a claim. This is a reading.
try:
    from django.db.models import Q
    OLD = re.search(
        r'    # Apply filters\n(.*?)\n    recipes = recipes\.distinct\(\)',
        was(CRUD), re.S)
    BLOCK = textwrap.dedent('    # Apply filters\n' + OLD.group(1) +
                            '\n    recipes = recipes.distinct()')
    from pages.views.recipes._recipe_filter import (filter_recipes,
                                                    selected_from)
    REPLAY = True
except Exception as e:
    REPLAY = False
    skip('the replay', str(e)[:90])

if REPLAY:
    class Rec(object):
        """Logs the ORM calls it is given instead of making them."""

        def __init__(self):
            self.log = []

        def filter(self, *a, **kw):
            self.log.append(('filter', tuple(str(x) for x in a),
                             tuple(sorted((k, str(v))
                                          for k, v in kw.items()))))
            return self

        def distinct(self):
            self.log.append(('distinct',))
            return self

    class _U(object):
        pass

    _user = _U()

    def run_old(sel):
        g = {'Q': Q, 'recipes': Rec(),
             'search_query': sel['search'],
             'search_type': sel['search_type'],
             'selected_courses': sel['courses'],
             'selected_categories': sel['categories'],
             'selected_proteins': sel['proteins'],
             'selected_authors': sel['authors'],
             'show_favourites': sel['favourites'],
             'request': type('R', (), {'user': _user})()}
        exec(compile(BLOCK, '<recipe_crud before PF-2>', 'exec'), g)
        return g['recipes'].log

    CASES = []
    for s in ('', 'salad'):
        for st in ('name', 'ingredient'):
            for co in ([], ['3'], ['3', '5']):
                for ca in ([], ['7']):
                    for pr in ([], ['2'], ['vegetarian'],
                               ['vegetarian', '2']):
                        for au in ([], ['Erene']):
                            for fa in (False, True):
                                CASES.append(dict(
                                    search=s, search_type=st, courses=co,
                                    categories=ca, proteins=pr,
                                    authors=au, favourites=fa))
    bad = []
    for c in CASES:
        if run_old(c) != filter_recipes(Rec(), c, _user).log:
            bad.append(c)
    ok(not bad,
       '%d selections replayed through BOTH implementations and every '
       'one made the identical ORM calls' % len(CASES),
       'first disagreement: %r\n  old: %r\n  new: %r'
       % (bad[0], run_old(bad[0]),
          filter_recipes(Rec(), bad[0], _user).log) if bad else '')

    # AND THE REPLAY CAN FAIL. A comparison that cannot tell two
    # things apart would pass over any change at all.
    mutant = dict(CASES[0]); mutant['courses'] = ['999']
    ok(run_old(CASES[0]) != run_old(mutant),
       '  CONTROL: the recorder distinguishes two different selections '
       '- a comparison that cannot fail is not a check')

# THE BACKUP HAD WHAT THIS ROUND MOVED.
ok('courses__recipe_course_id__in' in
   T.python_code_only(was(CRUD), payloads=True),
   'CONTROL: before this round recipe_crud held the only copy')
ok('def picker_recipes(' not in
   T.python_code_only(was(MEAL), payloads=True),
   'CONTROL: and there was no endpoint')
BT = T.code_only(was(TPL))
ok('all_recipes' in BT,
   'CONTROL: and the template rendered every recipe in the library')
ok('name="category"' not in BT and 'name="author"' not in BT,
   "CONTROL: with no category and no author control - Demetri's "
   'finding, in the markup')


# ==========================================================================
head('3. THE SAME ANSWER ON REAL DATA - THE PAGE AND THE ENDPOINT')
# ==========================================================================
django_up = False
try:
    if not DJ_READY:
        raise RuntimeError('Django did not start')
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

cl = None
if django_up:
    import json as _json
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import (CustomProtein, Recipe, RecipeCategory,
                              RecipeCourse, RecipeFavourite)

    u = User.objects.create_user(username='pf2', password='x',
                                 email='pf2@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)

    # A LIBRARY WHERE EVERY FILTER SEPARATES SOMETHING. Each recipe is
    # built so that at least one selection picks it out alone - a
    # fixture where two filters always agree cannot tell them apart.
    main = RecipeCourse.objects.create(name='Main', display_order=1)
    pud = RecipeCourse.objects.create(name='Dessert', display_order=2)
    pasta = RecipeCategory.objects.create(name='Pasta')
    greek = RecipeCategory.objects.create(name='Greek')
    lamb = CustomProtein.objects.create(name='Lamb')
    fish = CustomProtein.objects.create(name='Fish')

    def mk(name, course, cat, prot, author, veg=False, fav=False):
        r = Recipe.objects.create(recipe_name=name, servings=4,
                                  author=author, is_vegetarian=veg)
        if course:
            r.courses.add(course)
        if cat:
            r.categories.add(cat)
        if prot:
            r.proteins.add(prot)
        if fav:
            RecipeFavourite.objects.create(user=u, recipe=r)
        return r

    R = {}
    R['moussaka'] = mk('Moussaka', main, greek, lamb, 'Erene', fav=True)
    R['pastitsio'] = mk('Pastitsio', main, pasta, lamb, 'Erene')
    R['bream'] = mk('Sea Bream', main, greek, fish, 'Alexandra')
    R['briam'] = mk('Briam', main, greek, None, 'General', veg=True)
    R['baklava'] = mk('Baklava', pud, greek, None, 'Alexandra', veg=True,
                      fav=True)
    R['salad'] = mk('Greek Salad', None, greek, None, 'General', veg=True)

    SELECTIONS = [
        ('nothing selected', {}),
        ('course Main', {'course': [main.recipe_course_id]}),
        ('course Dessert', {'course': [pud.recipe_course_id]}),
        ('category Pasta', {'category': [pasta.recipe_category_id]}),
        ('protein Lamb', {'protein': [lamb.custom_protein_id]}),
        ('protein Fish', {'protein': [fish.custom_protein_id]}),
        ('vegetarian', {'protein': ['vegetarian']}),
        ('vegetarian OR Fish', {'protein': ['vegetarian',
                                            fish.custom_protein_id]}),
        ('author Erene', {'author': ['Erene']}),
        ('author Erene or Alexandra', {'author': ['Erene', 'Alexandra']}),
        ('favourites', {'favourites': '1'}),
        ('search bream', {'search': 'bream'}),
        ('course Main AND vegetarian', {'course': [main.recipe_course_id],
                                        'protein': ['vegetarian']}),
        ('favourites AND Dessert', {'favourites': '1',
                                    'course': [pud.recipe_course_id]}),
    ]

    def q(params):
        out = []
        for k, v in params.items():
            for one in (v if isinstance(v, list) else [v]):
                out.append('%s=%s' % (k, one))
        return '&'.join(out)

    def from_endpoint(params):
        r = cl.get('/meal_plans/picker_recipes/?' + q(params))
        if r.status_code != 200:
            return None, r.status_code
        d = _json.loads(r.content.decode('utf-8'))
        return sorted(row['id'] for row in d['rows']), 200

    # THE PRE-ROUND CODE, RUN AGAINST THE REAL DATABASE.
    #
    # The first cut of this compared the endpoint against the library
    # PAGE, scraped for data-recipe-id. That was the wrong instrument
    # twice over: the attribute only appears on two of the card's
    # buttons, and a page carries pagination, permissions and a letter
    # filter that have nothing to do with this round. It measured the
    # template, not the filter.
    #
    # So the comparison is against the filter block as recipe_crud
    # held it BEFORE this round - lifted from the backup in section 2
    # and executed here against a real queryset. That is the actual
    # thing that must not have moved, and no markup is involved.
    def from_before(params):
        sel = {
            'search': (params.get('search') or ''),
            'search_type': params.get('search_type', 'name'),
            'courses': [str(x) for x in params.get('course', [])],
            'categories': [str(x) for x in params.get('category', [])],
            'proteins': [str(x) for x in params.get('protein', [])],
            'authors': [str(x) for x in params.get('author', [])],
            'favourites': params.get('favourites') == '1',
        }
        g = {'Q': Q, 'recipes': Recipe.objects.all(),
             'search_query': sel['search'],
             'search_type': sel['search_type'],
             'selected_courses': sel['courses'],
             'selected_categories': sel['categories'],
             'selected_proteins': sel['proteins'],
             'selected_authors': sel['authors'],
             'show_favourites': sel['favourites'],
             'request': type('R', (), {'user': u})()}
        exec(compile(BLOCK, '<recipe_crud before PF-2>', 'exec'), g)
        return sorted(r.recipe_id for r in g['recipes']), 200

    first, code = from_endpoint({})
    ok(code == 200, 'the picker endpoint answers', code)
    ok(first is not None and len(first) == 6,
       '  with all six recipes when nothing is selected', first)

    agree = disagree = 0
    for label, params in SELECTIONS:
        got, c1 = from_endpoint(params)
        want, c2 = from_before(params)
        if got is None or want is None:
            skip('%s' % label, 'endpoint rc=%s before rc=%s' % (c1, c2))
            continue
        if got == want:
            agree += 1
        else:
            disagree += 1
            ok(False, '%s: the picker and the pre-round filter disagree'
               % label, 'picker=%r before=%r' % (got, want))
    ok(disagree == 0,
       'the picker and the PRE-ROUND filter code name the same recipes '
       'for all %d selections, run against a real database - the '
       'replay proved the calls match, this proves the rows do' % agree,
       '%d disagreed' % disagree)

    # AND THE FIXTURE CAN TELL THEM APART. If every selection returned
    # the same six recipes the comparison above would be worthless.
    veg, _ = from_endpoint({'protein': ['vegetarian']})
    lam, _ = from_endpoint({'protein': [lamb.custom_protein_id]})
    ok(veg is not None and sorted(veg) == sorted(
        [R['briam'].recipe_id, R['baklava'].recipe_id,
         R['salad'].recipe_id]),
       '  CONTROL: vegetarian selects exactly the three vegetarian '
       'recipes - not a filter that quietly selects everything', veg)
    ok(lam is not None and sorted(lam) == sorted(
        [R['moussaka'].recipe_id, R['pastitsio'].recipe_id]),
       '  CONTROL: and Lamb selects exactly two', lam)
    both, _ = from_endpoint({'protein': ['vegetarian',
                                         fish.custom_protein_id]})
    ok(both is not None and len(both) == 4,
       '  CONTROL: vegetarian OR Fish is a UNION and selects four - the '
       'three-way protein branch, which is the one piece of this '
       'filter that is not a plain AND', both)

    # THE PLANNER PAGE NO LONGER CARRIES THE LIBRARY.
    resp = cl.get('/meal_plans/planner/?week=2026-10-19')
    body = resp.content.decode('utf-8', 'replace')
    ok(resp.status_code == 200, 'the planner answers', resp.status_code)
    ok(body.count('class="recipe-option"') == 0,
       '  and ships ZERO recipe cards, where before this round it '
       'shipped one per recipe in the library',
       body.count('class="recipe-option"'))
    ok(body.count('<img') < 10,
       '  and fewer than ten images in the whole page',
       body.count('<img'))
    ok('name="protein"' in body and 'value="vegetarian"' in body,
       '  while the five controls ARE drawn - the options are a few '
       'dozen rows, not a few hundred recipes')


# ==========================================================================
head('4. RENDERED - THE DIALOG AT 1200 AND AT 390')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None

if not django_up:
    pass
elif sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the dialog is drawn', 'playwright or the Bootstrap fixture '
                                'is absent')
else:
    FIX = '<style>%s</style>' % read(FIXCSS)
    i = body.lower().find('</head>')
    DRESSED = body[:i] + FIX + body[i:] if i > 0 else FIX + body

    # The dialog is a Bootstrap modal and nothing has opened it, so it
    # is display:none. Show it the way PK-1's suite does - by hand,
    # because booting jQuery and Bootstrap in a fixture proves nothing
    # about this round.
    OPEN = """() => {
        const d = document.getElementById('pickerModal');
        d.style.display = 'block';
        d.classList.add('show');
        d.removeAttribute('aria-hidden');
    }"""

    with sync_playwright() as _pw:
        exe = os.environ.get('PLAYWRIGHT_CHROMIUM')
        br = _pw.chromium.launch(**({'executable_path': exe}
                                    if exe else {}))
        try:
            for w, h, label in ((1200, 900, 'DESKTOP 1200'),
                                (390, 844, 'PHONE 390')):
                ctx = br.new_context(viewport={'width': w, 'height': h})
                pg = ctx.new_page()
                pg.set_content(DRESSED, wait_until='domcontentloaded')
                pg.evaluate(OPEN)
                print('')
                print('   %s' % label)

                n = pg.evaluate(
                    "() => document.querySelectorAll('.picker-filter "
                    ".pf-btn').length")
                ok(n == 4,
                   '  four dropdown buttons are drawn', n)
                nf = pg.evaluate(
                    "() => document.querySelectorAll('#pickerFav').length")
                ok(nf == 1, '  and the Favourites button')

                # EVERY MENU IS CLOSED ON ARRIVAL. A dialog that opens
                # with four menus hanging out of it is unusable.
                openn = pg.evaluate(
                    "() => [...document.querySelectorAll('.pf-menu')]"
                    ".filter(m => getComputedStyle(m).display !== 'none')"
                    ".length")
                ok(openn == 0, '  and every menu starts closed', openn)

                # THE LIST IS EMPTY AND SAYS IT IS THINKING.
                cards = pg.evaluate(
                    "() => document.querySelectorAll('#pickerList "
                    ".recipe-option').length")
                ok(cards == 0,
                   '  the grid holds no cards before the fetch', cards)
                loading = pg.evaluate(
                    "() => { const l = "
                    "document.getElementById('pickerLoading');"
                    " return l ? !l.hidden : false; }")
                ok(loading,
                   '  and says it is finding recipes rather than '
                   'showing a blank grid')

                # THE CONTROLS FIT. PK-1's own suite caught this round's
                # predecessor leaving the phone list 2,572px tall.
                box = pg.evaluate(
                    "() => { const f = "
                    "document.querySelector('.picker-filter');"
                    " const r = f.getBoundingClientRect();"
                    " return {w: Math.round(r.width),"
                    " h: Math.round(r.height)}; }")
                dlg = pg.evaluate(
                    "() => Math.round(document.querySelector("
                    "'#pickerModal .modal-content')"
                    ".getBoundingClientRect().width)")
                ok(box['w'] <= dlg,
                   '  the filter strip is %dpx inside a %dpx dialog - '
                   'nothing hangs off the edge' % (box['w'], dlg))
                ok(box['h'] <= (170 if w < 768 else 110),
                   '  and %dpx tall, so the recipes are not pushed below '
                   'the fold' % box['h'], box['h'])

                if w < 768:
                    # 44px, THE HOUSE RULE. Every Add/Edit control in
                    # this application is thumb-sized at 390px.
                    small = pg.evaluate(
                        "() => [...document.querySelectorAll("
                        "'.picker-filter .pf-btn, .picker-filter "
                        ".pf-fav')].map(b => Math.round("
                        "b.getBoundingClientRect().height))"
                        ".filter(h => h < 44)")
                    ok(not small,
                       '  every filter control is at least 44px tall',
                       'shorter: %r' % small)
                    per = pg.evaluate(
                        "() => { const t = [...document.querySelectorAll("
                        "'.picker-filter .pf-drop')].map(d => Math.round("
                        "d.getBoundingClientRect().top));"
                        " return new Set(t).size; }")
                    ok(per >= 2,
                       '  and the four dropdowns wrap onto %d rows rather '
                       'than one unreadable line' % per, per)

                # A MENU OPENS AND CLOSES. The handler is real.
                pg.evaluate("() => pfToggle('course')")
                shown = pg.evaluate(
                    "() => getComputedStyle(document.getElementById("
                    "'pickerCourseMenu')).display !== 'none'")
                ok(shown, '  pfToggle opens the course menu')
                wide = pg.evaluate(
                    "() => { const r = document.getElementById("
                    "'pickerCourseMenu').getBoundingClientRect();"
                    " return Math.round(r.right) <= "
                    "Math.round(document.querySelector("
                    "'#pickerModal .modal-content')"
                    ".getBoundingClientRect().right) + 2; }")
                ok(wide, '  and it stays inside the dialog')
                pg.evaluate(
                    "() => document.body.dispatchEvent("
                    "new MouseEvent('click', {bubbles: true}))")
                still = pg.evaluate(
                    "() => getComputedStyle(document.getElementById("
                    "'pickerCourseMenu')).display !== 'none'")
                ok(not still,
                   '  and a click outside closes it - a menu that cannot '
                   'be dismissed is a trap')
                ctx.close()
        finally:
            br.close()


# ==========================================================================
head('5. WIDE, SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# ONE DESCRIPTION OF A RECIPE FILTER IN THE WHOLE TREE. The round's
# entire argument is that there must not be two.
owners = []
for dp, dn, fn in os.walk(os.path.join(ROOT, 'pages')):
    dn[:] = [d for d in dn if d not in ('__pycache__', 'migrations')]
    for f in fn:
        if not f.endswith('.py') or '.bak_' in f:
            continue
        p = os.path.join(dp, f)
        try:
            code = T.python_code_only(read(p), payloads=True)
        except Exception:
            continue
        hits = [c for c, _ in CLAUSES if c in code]
        # Three or more of the five clauses in one file is a filter,
        # not a coincidence - view_recipe legitimately touches one.
        if len(hits) >= 3:
            owners.append((os.path.relpath(p, ROOT), len(hits)))
ok(len(owners) == 1 and owners[0][0].endswith('_recipe_filter.py'),
   'exactly ONE file in pages/ describes what a recipe filter selects '
   '- %s' % ', '.join('%s(%d)' % o for o in owners),
   owners)

# AND THE JAVASCRIPT DOES NOT DESCRIBE ONE EITHER, which was the
# alternative Demetri turned down.
ok('is_vegetarian' not in JS and 'recipeCourses' not in JS,
   'and the browser holds no copy of the matching - the round turned '
   'on not writing one')

touched = sorted(
    os.path.relpath(os.path.join(dp, f), ROOT)[:-len(SUFFIX)]
    for dp, dn, fn in os.walk(ROOT)
    for f in fn if f.endswith(SUFFIX))
allowed = {'Push-PendingChanges.ps1', 'alv_tree.py', 'alv_rounds.py',
           'test_waiting_down.py',
           os.path.join('pages', 'urls.py'),
           os.path.join('pages', 'templates', 'meal_planner.html'),
           os.path.join('pages', 'views', 'recipes', 'recipe_crud.py'),
           os.path.join('pages', 'views', 'recipes', 'meal_planning.py'),
           # PK-1'S SUITE, carried by the round that superseded its
           # subject. Its course filter is what this round replaced,
           # so twenty of its claims stop being true the moment this
           # round lands - which is not PK-1 being wrong, it is PK-1
           # being superseded. Repaired here so a half-applied tree
           # stays green either way round.
           'test_picker_grid.py',
           # AND THE ONE TREE-WIDE RE-PIN. The picker's five controls
           # add five rules that set both a background and a colour,
           # so EXPECT_PAIRS goes 695 -> 700. Carried by the round
           # that caused it, like every other number this push moved.
           'test_pair_contrast.py'}
ok(len(touched) == 10,
   'TEN backups on disk, counted and not typed', '%r' % (touched,))
extra = set(touched) - allowed
ok(not extra, '  and every one is a file this round was allowed',
   'unexpected: %s' % ', '.join(sorted(extra)))
ok(os.path.isfile(FILT) and not os.path.isfile(FILT + SUFFIX),
   'the shared module is NEW and has no backup - this round writes 11 '
   'files and leaves 10 backups, by design')

# AND PK-1'S SUITE STILL JUDGES THE PICKER. A repair that quietly
# narrowed it would be this round marking its own homework.
PK = read(os.path.join(ROOT, 'test_picker_grid.py'))
# ASKED OF THE CODE, NOT THE PROSE. The one surviving mention of
# pickCourse in PK-1's suite is the comment saying what replaced it,
# and that comment is the record this repair exists to leave. To a
# substring search a comment about a thing is the thing - a trap this
# project has paid for five times in two days.
PKCODE = T.python_code_only(PK, payloads=True)
ok('function pfChanged(' in PKCODE and 'pickCourse' not in PKCODE,
   "PK-1's suite asks about the control that replaced its own")
ok('pickCourse' in PK,
   '  while its prose still says what that control used to be - a '
   'gate that forgets why a control exists is a gate that lets the '
   'next round remove it')
ok('pfDraw' in PK,
   '  and drives the real drawing code, not a copy of it')
ok(PK.count("c['") >= 20,
   '  and still makes %d source claims, not fewer'
   % PK.count("c['"), PK.count("c['"))

import alv_rounds                                          # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'alv_rounds knows the round')
ok(ME in T.CONVERTED, 'alv_tree knows this suite')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the gate runs this suite')
ok('def filter_recipes(' in gate and 'def picker_recipes(' in gate
   and 'id="pickerAuthor"' in gate,
   'all four sentinels are pinned in the gate')

# AND PK-1'S SENTINEL WENT WITH THE FUNCTION IT PINNED.
#
# PK-1 pinned `function pickCourse(`; this round is what replaced that
# function, and the first cut of it left the row behind. test_bar_order
# audits all 497 sentinel rows against the tree and refused the sweep
# at suite 32 - which is exactly what that audit is for.
#
# RETIRED, NOT DELETED. The row pins what PK-1's claim BECAME, because
# "it filters, composing with the search rather than replacing it" is
# still true and still worth defending; only the function's name moved.
ok('function pickCourse(' not in gate,
   "PK-1's sentinel for the function this round removed is gone")
ok('function pfChanged(' in gate,
   '  and its claim is re-pinned on the control that replaced it, '
   'rather than dropped - a gate that forgets why a control exists is '
   'a gate that lets the next round remove it')
ok('PK-1, widened by PF-2' in gate,
   '  and the row says who widened it and when')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE PICKER WAS IGNORING A FEATURE THE APPLICATION ALREADY HAD.')
print('  Author, Favourites, Category and Protein have been in')
print('  recipe_management since long before the planner existed, with')
print('  these exact parameter names. This round is a borrow.')
print('')
print('  AND IT IS BORROWED ONCE. The cheap way was four more data-')
print('  attributes and a matcher in JavaScript - a second description')
print('  of what Protein: Chicken selects, in a second language, free')
print('  to drift. Demetri chose the server.')
print('')
print('  SO NOTHING MOVED, PROVED TWICE. The library\'s old filter was')
print('  lifted out of its backup and replayed beside the new shared')
print('  one over every combination of the five; then both screens were')
print('  asked of a real library and had to name the same recipes.')
print('')
print('  AND 336 RECIPES CAME OFF THE PLANNER PAGE. It rendered every')
print('  recipe in the library, with its photo, on every load - opened')
print('  or not. It now ships none.')
print('=' * 74)
sys.exit(1 if failed else 0)
