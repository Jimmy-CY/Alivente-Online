# -*- coding: utf-8 -*-
"""apply_pick_filter.py - round PF-2, 19 Oct 2026.

RELEASE 3, PUSH 3. THE PICKER ASKS THE SAME QUESTION THE LIBRARY DOES.

Demetri, 19 Oct, testing the live planner: "I don't think that this
picker is any good at all. It only allows you to choose Course. We
need to be able to select Author, Favorites, Category and Protein (or
vegetarian)."

THE FINDING BEHIND THE FINDING. All four already exist, and
recipe_management has filtered by all four since long before the
planner did - same GET parameter names, same `vegetarian` magic value
in the protein list, same `favourites=1`. The picker was not missing a
feature. It was ignoring one the application already had.

So this round is a BORROW, and the shape of the borrow is the whole
decision. There were two ways:

  in JavaScript   Render four more data- attributes per card and match
                  them in the browser. An hour's work, no round trip -
                  and a second implementation of "what does Protein:
                  Chicken select", in a second language, that will
                  drift from the first. That is the exact class of
                  fault the suites exist to refuse.

  on the server   One function. recipe_management calls it, the picker
                  calls it, and a suite proves both callers get the
                  same answer for the same input.

Demetri chose the server.

AND IT CLOSES SOMETHING ELSE. The picker renders ALL 336 recipes into
the planner page - 336 cards and 336 <img> tags - on every single
load, whether the dialog is opened or not. PK-1 made that grid
beautiful; it did not make it cheap. Asking the server means the
planner page ships none of them and the dialog fetches what it needs
when it is opened.

WHAT THIS ROUND DOES

    _recipe_filter.py  NEW. selected_from() reads the five filters out
                       of a QueryDict; filter_recipes() applies them.
                       One place that decides what a filter selects.
    recipe_crud.py     recipe_management stops having its own copy and
                       calls the shared one. Its behaviour must not
                       move by a single recipe - section 2 proves it
                       by replaying both implementations.
    meal_planning.py   picker_recipes(), a read-tier JSON endpoint,
                       and all_recipes LEAVES the planner context.
    meal_planner.html  five dropdowns, an empty list, and a fetch.

THE SEARCH GAINS INGREDIENT MODE, which Demetri did not ask for and
is told about: the library's search offers name-or-ingredient and the
shared function carries it, so leaving it out of the picker would
have meant writing a narrower copy of the thing this round exists to
stop copying.

Idempotent. Every file backed up to .bak_pickfilter.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_pickfilter'
FILT = os.path.join('pages', 'views', 'recipes', '_recipe_filter.py')
CRUD = os.path.join('pages', 'views', 'recipes', 'recipe_crud.py')
MEAL = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_pick_filter.py'
PATCHER = 'apply_pick_filter.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PF-2, 19 Oct 2026'
CHECK = False


# ======================================================== THE NEW MODULE
MODULE = '''# -*- coding: utf-8 -*-
"""_recipe_filter.py - ONE place that decides what a filter selects.

PF-2, 19 Oct 2026. Demetri, testing the planner: "It only allows you
to choose Course. We need to be able to select Author, Favorites,
Category and Protein (or vegetarian)."

All four already existed in recipe_management, with these exact GET
parameter names, and the picker was ignoring them. The cheap fix was
to re-implement the matching in JavaScript against data- attributes.
The honest one is this: both screens ask the same function, and a
suite replays them side by side to prove they agree.

THE THREE PIECES, kept apart on purpose:

    vocabulary(user)   what the controls are allowed to offer
    selected_from(q)   what the person chose, read out of a QueryDict
    filter_recipes()   what that selects

A caller that only draws the controls needs the first. A caller that
only answers a fetch needs the last two. Nothing needs all three to
do one job, and splitting them is what lets the planner page stop
carrying 336 recipes it may never show.

THE `vegetarian` MAGIC VALUE IS LOAD-BEARING AND IT IS NOT NEW.
`is_vegetarian` is a boolean column, not a CustomProtein row, so it
cannot have an id - and a separate checkbox for it would read as a
fifth filter rather than one more answer to "what protein?".
recipe_management solved that on its own by putting the literal
string 'vegetarian' in the protein list. That decision is kept here
exactly, because changing it would silently break every saved link
anyone has to a filtered library.
"""
from django.db.models import Q

from pages.models import (
    CustomProtein,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
)

# THE PARAMETER NAMES, IN ONE PLACE. Both callers read these and the
# suite checks the library's own template still writes them, so a
# rename cannot quietly orphan the controls.
PARAMS = ('search', 'search_type', 'course', 'category', 'protein',
          'author', 'favourites')

VEGETARIAN = 'vegetarian'


def vocabulary():
    """What the five controls may offer.

    RecipeCourse orders itself by display_order then name, which is
    why the course list reads Starter, Main, Dessert rather than
    alphabetically; the others are alphabetical because nothing
    better is defined for them.
    """
    return {
        'courses': RecipeCourse.objects.all().order_by('name'),
        'categories': RecipeCategory.objects.all().order_by('name'),
        'proteins': CustomProtein.objects.all().order_by('name'),
        'authors': [{'value': v, 'name': n}
                    for v, n in Recipe.AUTHOR_CHOICES],
    }


def selected_from(params):
    """Read the five filters out of a GET QueryDict. One reading.

    Returns plain Python, so a caller can log it, compare it or put
    it in a template context without going near the database.
    """
    return {
        'search': params.get('search', ''),
        'search_type': params.get('search_type', 'name'),
        'courses': params.getlist('course'),
        'categories': params.getlist('category'),
        'proteins': params.getlist('protein'),
        'authors': params.getlist('author'),
        'favourites': params.get('favourites') == '1',
    }


def filter_recipes(recipes, sel, user):
    """Apply the five filters. THE ONE PLACE.

    Lifted from recipe_management unchanged - every clause, in the
    same order, including the three-way protein branch. It is not an
    improvement on that code and must not become one without the
    suite being told, because the suite's whole job is to prove the
    library still selects exactly what it selected before.
    """
    search_query = sel.get('search') or ''
    if search_query:
        if sel.get('search_type') == 'ingredient':
            recipes = recipes.filter(
                recipe_ingredients__ingredient__name__icontains=search_query
            )
        else:
            recipes = recipes.filter(recipe_name__icontains=search_query)

    if sel.get('courses'):
        recipes = recipes.filter(
            courses__recipe_course_id__in=sel['courses'])

    if sel.get('categories'):
        recipes = recipes.filter(
            categories__recipe_category_id__in=sel['categories'])

    if sel.get('proteins'):
        selected_proteins = sel['proteins']
        if VEGETARIAN in selected_proteins:
            protein_ids = [p for p in selected_proteins if p != VEGETARIAN]
            if protein_ids:
                recipes = recipes.filter(
                    Q(is_vegetarian=True) |
                    Q(proteins__custom_protein_id__in=protein_ids)
                )
            else:
                recipes = recipes.filter(is_vegetarian=True)
        else:
            recipes = recipes.filter(
                proteins__custom_protein_id__in=selected_proteins)

    if sel.get('authors'):
        recipes = recipes.filter(author__in=sel['authors'])

    if sel.get('favourites'):
        recipes = recipes.filter(favourited_by__user=user)

    # DISTINCT, ALWAYS. Four of the five filters join a many-to-many,
    # and a recipe in two selected categories comes back twice
    # without it. recipe_management has called this since before the
    # planner existed.
    return recipes.distinct()


def favourite_ids(user):
    """The user's favourites, as a set, for a fast `in` on a card."""
    return set(RecipeFavourite.objects.filter(user=user)
               .values_list('recipe_id', flat=True))
'''


# ============================================== THE LIBRARY STOPS COPYING
CRUD_WAS = """    selected_courses = request.GET.getlist('course')
    selected_categories = request.GET.getlist('category')
    selected_proteins = request.GET.getlist('protein')
    selected_authors = request.GET.getlist('author')
    selected_letter = request.GET.get('letter', '')"""
CRUD_NOW = """    # PF-2, 19 Oct 2026 - ONE READING, SHARED WITH THE PICKER.
    # These five lines and the filter block below were the only
    # description in the application of what a recipe filter selects,
    # and the picker needed the same answer. Rather than a second copy
    # in JavaScript, both screens now ask _recipe_filter.
    #
    # The names are unchanged on purpose: `course`, `category`,
    # `protein` with its `vegetarian` magic value, `author`,
    # `favourites=1`. Every saved link to a filtered library still
    # works, and the template below still writes exactly these.
    _sel = selected_from(request.GET)
    selected_courses = _sel['courses']
    selected_categories = _sel['categories']
    selected_proteins = _sel['proteins']
    selected_authors = _sel['authors']
    selected_letter = request.GET.get('letter', '')"""

CRUD_BLOCK_WAS = """    # Apply filters
    if search_query:
        if search_type == 'ingredient':
            recipes = recipes.filter(
                recipe_ingredients__ingredient__name__icontains=search_query
            )
        else:
            recipes = recipes.filter(recipe_name__icontains=search_query)

    if selected_courses:
        recipes = recipes.filter(courses__recipe_course_id__in=selected_courses)

    if selected_categories:
        recipes = recipes.filter(categories__recipe_category_id__in=selected_categories)

    if selected_proteins:
        if 'vegetarian' in selected_proteins:
            protein_ids = [p for p in selected_proteins if p != 'vegetarian']
            if protein_ids:
                recipes = recipes.filter(
                    Q(is_vegetarian=True) |
                    Q(proteins__custom_protein_id__in=protein_ids)
                )
            else:
                recipes = recipes.filter(is_vegetarian=True)
        else:
            recipes = recipes.filter(proteins__custom_protein_id__in=selected_proteins)

    if selected_authors:
        recipes = recipes.filter(author__in=selected_authors)

    if show_favourites:
        recipes = recipes.filter(favourited_by__user=request.user)

    recipes = recipes.distinct()"""
CRUD_BLOCK_NOW = """    # Apply filters - PF-2, 19 Oct 2026. THE BODY MOVED, THE
    # BEHAVIOUR DID NOT. Every clause that was here is in
    # _recipe_filter.filter_recipes in the same order, including the
    # three-way protein branch and the distinct() at the end, and
    # test_pick_filter replays both implementations against the same
    # selections to prove this screen still selects what it selected.
    recipes = filter_recipes(recipes, _sel, request.user)"""

CRUD_IMP_WAS = """from pages.models import ("""
CRUD_IMP_NOW = """# PF-2, 19 Oct 2026 - the shared filter. One description of what a
# recipe filter selects, asked by this screen and by the picker.
from pages.views.recipes._recipe_filter import (
    filter_recipes,
    selected_from,
)
from pages.models import ("""


# ====================================================== THE NEW ENDPOINT
ENDPOINT = '''

# ==========================================================================
# PF-2, 19 Oct 2026 - THE PICKER ASKS THE SERVER
# ==========================================================================
@login_required
def picker_recipes(request):
    """The recipe picker's rows, filtered by the SAME function the
    library uses.

    Demetri, testing the planner: "It only allows you to choose
    Course. We need to be able to select Author, Favorites, Category
    and Protein (or vegetarian)."

    WHY THIS IS AN ENDPOINT AND NOT FOUR MORE data- ATTRIBUTES.
    Matching five filters in the browser means writing, in JavaScript,
    a second description of what `Protein: Chicken` selects. There
    would then be two, in two languages, and they would drift - which
    is the fault the suites in this project exist to refuse.

    AND IT TAKES 336 RECIPES OFF THE PLANNER PAGE. The picker used to
    render every recipe in the library into the page, with its photo,
    on every load of the planner whether the dialog was opened or not.
    Now the page ships none and the dialog asks for what it needs.

    READ TIER. It selects and never writes, so it answers GET and
    says so - a view that mutates nothing should not require a POST,
    and a filter you can link to is worth more than one you cannot.
    """
    sel = selected_from(request.GET)
    recipes = filter_recipes(
        Recipe.objects.all().prefetch_related('courses'),
        sel, request.user).order_by('recipe_name')

    # THE CEILING IS A REFUSAL TO BE SLOW, not a page. 336 rows of
    # four fields is small; a library of 20,000 would not be, and a
    # dialog that hangs is worse than one that says there is too much
    # to show. MD-1 put the same ceiling on the shopping list.
    total = recipes.count()
    rows = []
    for r in recipes[:500]:
        rows.append({
            'id': r.recipe_id,
            'name': r.recipe_name,
            'servings': r.servings or '',
            'minutes': (r.prep_time or 0) + (r.cook_time or 0),
            'photo': r.photo_url or '',
        })
    return JsonResponse({
        'success': True,
        'rows': rows,
        'total': total,
        'shown': len(rows),
        'capped': total > len(rows),
    })
'''

MEAL_CTX_WAS = """        # PK-1, 19 Oct 2026 - prefetch_related('courses'), because
        # every card in the picker prints the course ids it belongs to
        # so the filter can work in the browser. Without it that is a
        # query per recipe, which on this tree is two hundred of them
        # to open a dialog. [E29]
        'all_recipes': (Recipe.objects.all()
                        .prefetch_related('courses')
                        .order_by('recipe_name')),
        # The filter's own buttons. RecipeCourse orders itself by
        # display_order then name, so the strip reads Starter, Main,
        # Dessert rather than alphabetically.
        'all_courses': RecipeCourse.objects.all(),"""
MEAL_CTX_NOW = """        # PF-2, 19 Oct 2026 - all_recipes IS GONE FROM THIS PAGE.
        #
        # It was every recipe in the library, with a prefetch, rendered
        # into the markup as 336 cards and 336 <img> tags on every load
        # of the planner - whether the dialog was opened or not. PK-1
        # added the prefetch to stop it being 200 queries as well, which
        # was right and did not make it cheap.
        #
        # The picker now fetches what it needs from picker_recipes()
        # when it opens, so the page ships none of them.
        #
        # The five controls still need their OPTIONS, which is a few
        # dozen rows and not a few hundred recipes. vocabulary() is the
        # same list recipe_management draws its panel from.
        **_filter_vocabulary(),"""

MEAL_IMP_WAS = """from .conversions import convert_quantity, get_conversion_cache"""
MEAL_IMP_NOW = """# PF-2, 19 Oct 2026 - the shared filter, asked by the picker exactly
# as recipe_management asks it.
from pages.views.recipes._recipe_filter import (
    filter_recipes,
    selected_from,
    vocabulary as _filter_vocabulary,
)

from .conversions import convert_quantity, get_conversion_cache"""


# ============================================================== THE ROUTE
URL_WAS = """    path('meal_plans/servings/', views.set_meal_servings, name='set_meal_servings'),"""
URL_NOW = """    path('meal_plans/servings/', views.set_meal_servings, name='set_meal_servings'),
    # PF-2, 19 Oct 2026 - the picker's rows. GET, because it selects
    # and never writes, and because a filter you can link to is worth
    # more than one you cannot.
    path('meal_plans/picker_recipes/', views.picker_recipes, name='picker_recipes'),"""


# ====================================================== THE SENTINEL ROWS
# PK-1'S SENTINEL GOES WITH THE FUNCTION IT PINNED.
#
# PK-1 pinned `function pickCourse(` in the gate, and this round is
# what replaces that function. test_bar_order audits all 497 sentinel
# rows against the tree and caught it - which is the whole reason that
# audit exists, and it caught it on the first sweep after this round
# was written.
#
# RETIRED, NOT DELETED. The row is rewritten to pin what PK-1's claim
# BECAME rather than removed, because PK-1's finding - "There is no
# search or filtering" - is still a true thing about this dialog's
# history, and a gate that forgets why a control exists is a gate that
# lets the next round remove it.
PK1_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'function pickCourse('; What = 'PK-1: and it filters by course, composing with the search rather than replacing it' },"""
PK1_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'function pfChanged('; What = 'PK-1, widened by PF-2 19 Oct 2026: it filters, composing with the search rather than replacing it - by course and by four more things since Demetri asked for them' },"""

SENT_WAS = """    @{ File = 'pages/migrations/0101_drop_meal_plan.py'; Text = 'dropping %s - %d row(s)'; What = 'MX-1: and the count is taken BEFORE the drop and printed, because a DeleteModel reverses into an empty table' },"""
SENT_NOW = """    @{ File = 'pages/migrations/0101_drop_meal_plan.py'; Text = 'dropping %s - %d row(s)'; What = 'MX-1: and the count is taken BEFORE the drop and printed, because a DeleteModel reverses into an empty table' },
    # ------------------------------------------------- PF-2, 19 Oct 2026
    @{ File = 'pages/views/recipes/_recipe_filter.py'; Text = 'def filter_recipes('; What = 'PF-2: ONE place decides what a recipe filter selects, asked by the library and by the picker' },
    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'recipes = filter_recipes(recipes, _sel, request.user)'; What = 'PF-2: and the library stopped keeping its own copy of it' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def picker_recipes('; What = 'PF-2: the picker asks the server for its rows, after Demetri said it only allows you to choose Course' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerAuthor"'; What = 'PF-2: and all five filters are there - course, category, protein with vegetarian, author and favourites' },"""

SUITE_WAS = """    'test_meal_drop.py'
)"""
SUITE_NOW = """    'test_meal_drop.py',
    # PF-2, 19 Oct 2026 - the five filters on one shared function.
    # Section 2 REPLAYS the library's old filter block and the new
    # shared one against the same selections and compares the ORM
    # calls, because "it behaves the same" is a claim and a
    # recording is a reading.
    'test_pick_filter.py'
)"""

TREE_WAS = """    'test_meal_drop.py',
]"""
TREE_NOW = """    'test_meal_drop.py',
    # PF-2, 19 Oct 2026 - Demetri's finding. The picker filters by
    # five things because the library already did, and they share one
    # function rather than two implementations in two languages.
    'test_pick_filter.py',
]"""

RD_WAS = """    '.bak_mealdrop',
]"""
RD_NOW = """    '.bak_mealdrop',
    # PF-2, 19 Oct 2026 - "I don't think that this picker is any good
    # at all. It only allows you to choose Course." All four of the
    # filters he asked for already existed in recipe_management with
    # these exact parameter names; the picker was ignoring a feature
    # the application already had. One shared function now, and 336
    # recipes come off the planner page with it.
    '.bak_pickfilter',
]"""

WD_WAS = """CONVERTED_N = 114   # MX-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 115   # PF-2, 19 Oct 2026 - this round own suite   # (was 114)   # MX-1, 19 Oct 2026 - this round own suite"""


# ============================================================== HELPERS
def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('PF-2 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


# =========================================================== THE MARKUP
# FIVE DROPDOWNS, Demetri's choice from the three offered.
#
# Chips were what PK-1 built for course alone and they were right for
# one filter: fourteen courses already wrap to two rows in a dialog
# 766px wide. Five dimensions of chips would be six rows and the
# recipes would be below the fold.
#
# The shape is recipe_management's own filter panel - a button that
# names the selection, a menu of checkboxes - so the two screens look
# and behave alike. base owns no multiselect, so the rules live here.
FILTER_WAS = """                        <label for="pickerList"><strong>Choose one</strong></label>
                        {# THE FILTER - PK-1, 19 Oct 2026. Demetri, on the #}
                        {# live picker: "There is no search or filtering". #}
                        {# base owns .alv-seg, its pressed state and its   #}
                        {# focus ring, so this page writes no component -  #}
                        {# only the wrap rule a five-course strip needs.   #}
                        <div class="picker-filter">
                            <div class="alv-seg" role="group" aria-label="Filter by course">
                                <button type="button" data-course="" aria-pressed="true"
                                        onclick="pickCourse(this)">All</button>
                                {% for course in all_courses %}
                                <button type="button" data-course="{{ course.recipe_course_id }}"
                                        aria-pressed="false" onclick="pickCourse(this)">{{ course.name }}</button>
                                {% endfor %}
                            </div>
                            <span class="picker-count" id="pickerCount" aria-live="polite"></span>
                        </div>"""
FILTER_NOW = """                        {# THE LABEL MOVED - PF-2, 19 Oct 2026. PK-1 put  #}
                        {# "Choose one" above the filter strip, where it  #}
                        {# labelled the one course bar as well as the     #}
                        {# list. With five controls between it and the    #}
                        {# recipes it reads as an instruction about the   #}
                        {# filters, which is not what it means.           #}
                        <label class="picker-lbl"><strong>Filter</strong></label>
                        {# THE FIVE FILTERS - PF-2, 19 Oct 2026. Demetri:  #}
                        {# "It only allows you to choose Course. We need to #}
                        {# be able to select Author, Favorites, Category    #}
                        {# and Protein (or vegetarian)."                    #}
                        {#                                                  #}
                        {# DROPDOWNS, NOT CHIPS, by his choice. PK-1's      #}
                        {# course chips already wrapped to two rows in this #}
                        {# dialog; five dimensions of chips would be six,   #}
                        {# and the recipes would start below the fold.      #}
                        {#                                                  #}
                        {# The names are recipe_management's own - course,  #}
                        {# category, protein, author - because the server   #}
                        {# answers both screens with one function now.      #}
                        <div class="picker-filter">
                            <div class="pf-drop">
                                <button type="button" class="pf-btn" id="pickerCourseBtn"
                                        aria-expanded="false" aria-haspopup="true"
                                        onclick="pfToggle('course')">
                                    <span id="pickerCourseLabel">All Courses</span>
                                    <i class="fas fa-chevron-down" aria-hidden="true"></i>
                                </button>
                                <div class="pf-menu" id="pickerCourseMenu" role="group"
                                     aria-label="Filter by course">
                                    {% for course in courses %}
                                    <label><input type="checkbox" name="course"
                                           value="{{ course.recipe_course_id }}"
                                           onchange="pfChanged()"> {{ course.name }}</label>
                                    {% endfor %}
                                </div>
                            </div>
                            <div class="pf-drop">
                                <button type="button" class="pf-btn" id="pickerCategoryBtn"
                                        aria-expanded="false" aria-haspopup="true"
                                        onclick="pfToggle('category')">
                                    <span id="pickerCategoryLabel">All Categories</span>
                                    <i class="fas fa-chevron-down" aria-hidden="true"></i>
                                </button>
                                <div class="pf-menu" id="pickerCategoryMenu" role="group"
                                     aria-label="Filter by category">
                                    {% for cat in categories %}
                                    <label><input type="checkbox" name="category"
                                           value="{{ cat.recipe_category_id }}"
                                           onchange="pfChanged()"> {{ cat.name }}</label>
                                    {% endfor %}
                                </div>
                            </div>
                            <div class="pf-drop">
                                <button type="button" class="pf-btn" id="pickerProteinBtn"
                                        aria-expanded="false" aria-haspopup="true"
                                        onclick="pfToggle('protein')">
                                    <span id="pickerProteinLabel">All Proteins</span>
                                    <i class="fas fa-chevron-down" aria-hidden="true"></i>
                                </button>
                                <div class="pf-menu" id="pickerProteinMenu" role="group"
                                     aria-label="Filter by protein">
                                    {% for protein in proteins %}
                                    <label><input type="checkbox" name="protein"
                                           value="{{ protein.custom_protein_id }}"
                                           onchange="pfChanged()"> {{ protein.name }}</label>
                                    {% endfor %}
                                    {# VEGETARIAN IS A COLUMN, NOT A ROW, so #}
                                    {# it has no id and travels as a literal.#}
                                    {# recipe_management has done exactly    #}
                                    {# this since long before the planner.   #}
                                    <label><input type="checkbox" name="protein"
                                           value="vegetarian"
                                           onchange="pfChanged()"> Vegetarian</label>
                                </div>
                            </div>
                            <div class="pf-drop">
                                <button type="button" class="pf-btn" id="pickerAuthorBtn"
                                        aria-expanded="false" aria-haspopup="true"
                                        onclick="pfToggle('author')">
                                    <span id="pickerAuthorLabel">All Authors</span>
                                    <i class="fas fa-chevron-down" aria-hidden="true"></i>
                                </button>
                                <div class="pf-menu" id="pickerAuthor" role="group"
                                     aria-label="Filter by author">
                                    {% for author in authors %}
                                    <label><input type="checkbox" name="author"
                                           value="{{ author.value }}"
                                           onchange="pfChanged()"> {{ author.name }}</label>
                                    {% endfor %}
                                </div>
                            </div>
                            {# FAVOURITES IS ONE ANSWER, so it is one button #}
                            {# and not a menu of one checkbox.               #}
                            <button type="button" class="pf-fav" id="pickerFav"
                                    aria-pressed="false" onclick="pfFav(this)">
                                <i class="fas fa-heart" aria-hidden="true"></i> Favourites
                            </button>
                            <button type="button" class="pf-clear" id="pickerClear"
                                    onclick="pfClear()" hidden>Clear filters</button>
                            <span class="picker-count" id="pickerCount" aria-live="polite"></span>
                        </div>"""

LIST_WAS = """                        <div id="pickerList">
                            {% for recipe in all_recipes %}
                            <div class="recipe-option"
                                 data-recipe-id="{{ recipe.recipe_id }}"
                                 data-recipe-servings="{{ recipe.servings|default:4 }}"
                                 data-recipe-name="{{ recipe.recipe_name|lower }}"
                                 {# PK-1, 19 Oct 2026 - the ids, not the   #}
                                 {# names: a course that is renamed should #}
                                 {# not silently stop matching. Read from  #}
                                 {# a prefetch, so this is not a query per #}
                                 {# card.                                  #}
                                 data-recipe-courses="{% for c in recipe.courses.all %}{{ c.recipe_course_id }} {% endfor %}"
                                 onclick="pickRecipe(this)">
                                {% if recipe.photo_url %}
                                <img loading="lazy" decoding="async" src="{{ recipe.photo_url }}"
                                     alt="" class="recipe-thumbnail">
                                {% else %}
                                <div class="recipe-thumbnail-placeholder"><i class="fas fa-utensils"></i></div>
                                {% endif %}
                                <div>
                                    <strong>{{ recipe.recipe_name }}</strong><br>
                                    <small class="text-muted">
                                        {{ recipe.prep_time|default:0|add:recipe.cook_time|default:0 }} min
                                        &bull; makes {{ recipe.servings|default:"?" }}
                                    </small>
                                </div>
                            </div>
                            {% endfor %}
                            {# A FILTER THAT HIDES EVERYTHING SAYS SO -  #}
                            {# PK-1. Otherwise an empty dialog reads as  #}
                            {# a broken one, which is the same class of  #}
                            {# fault as a selected state nothing drew.   #}
                            <div class="picker-empty" id="pickerEmpty" hidden>
                                <i class="fas fa-search"></i>
                                <p>No recipe matches that.</p>
                            </div>
                        </div>"""
LIST_NOW = """                        <label for="pickerList"><strong>Choose one</strong></label>
                        {# EMPTY ON ARRIVAL - PF-2, 19 Oct 2026.          #}
                        {#                                                #}
                        {# This held every recipe in the library: 336     #}
                        {# cards and 336 <img> tags rendered into the     #}
                        {# planner on every load, opened or not. PK-1     #}
                        {# gave them a grid and a prefetch, which was     #}
                        {# right and did not make them cheap.             #}
                        {#                                                #}
                        {# openPicker() fetches what it needs now. The    #}
                        {# page ships none of them.                       #}
                        <div id="pickerList" aria-busy="false">
                            {# A FILTER THAT HIDES EVERYTHING SAYS SO -  #}
                            {# PK-1. Otherwise an empty dialog reads as  #}
                            {# a broken one, which is the same class of  #}
                            {# fault as a selected state nothing drew.   #}
                            <div class="picker-empty" id="pickerEmpty" hidden>
                                <i class="fas fa-search"></i>
                                <p>No recipe matches that.</p>
                            </div>
                            {# AND A DIALOG THAT IS THINKING SAYS THAT   #}
                            {# TOO. The fetch is fast on a library of    #}
                            {# 336, and a blank grid with no explanation #}
                            {# is indistinguishable from a broken one on #}
                            {# the one connection where it is not.       #}
                            <div class="picker-empty" id="pickerLoading">
                                <i class="fas fa-circle-notch fa-spin"></i>
                                <p>Finding recipes...</p>
                            </div>
                        </div>"""


# ============================================================== THE CSS
CSS_WAS = """/* THE FILTER STRIP. base owns .alv-seg - its CSS, its pressed state
   and its focus ring - so this round writes none of that. All it does
   is let the strip wrap on a narrow dialog, which a bar of five
   courses needs and a segmented view bar of two never did. */
.picker-filter {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.picker-filter .alv-seg {
    flex-wrap: wrap;
}"""
CSS_NOW = """/* THE FILTER STRIP. PK-1 built it for one course bar; PF-2 put five
   dropdowns in it, by Demetri's choice, because fourteen courses
   already wrapped to two rows and five dimensions of chips would have
   been six rows with the recipes below the fold.

   base owns no multiselect - recipe_management rolled its own - so
   the rules are here, and they are the same shape so the two screens
   read alike. */
.picker-filter {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.picker-filter .alv-seg {
    flex-wrap: wrap;
}

/* PF-2, 19 Oct 2026 - the five controls. */
.picker-lbl {
    display: block;
    margin-bottom: 4px;
}

.pf-drop {
    position: relative;
}

.pf-btn,
.pf-fav,
.pf-clear {
    font-size: 13px;
    line-height: 1.4;
    padding: 6px 10px;
    border: 1px solid var(--alv-line);
    border-radius: 6px;
    background: var(--alv-paper);
    color: var(--alv-ink-soft);
    display: inline-flex;
    align-items: center;
    gap: 10px;
    /* 44px ON A PHONE. Every Add/Edit control in this application is
       thumb-sized at 390px and a filter is no different - PK-1 paid
       for that lesson on this same dialog. */
    min-height: 34px;
}

/* --alv-ink-soft AND NOT --alv-ink-faint. The faint token reads
   3.0:1 on paper, which is below AA, and test_verb_colours counts
   every rule that takes its ground from an ancestor and lands there.
   It caught this one the first time the sweep ran after this round -
   the chevron is decorative and aria-hidden, and the rule is the rule.
   ink-soft reads 5.3:1 on the same ground. */
.pf-btn .fa-chevron-down {
    font-size: 10px;
    color: var(--alv-ink-soft);
}

/* A CONTROL THAT IS DOING SOMETHING LOOKS LIKE IT. The accent tint is
   the same one base gives a selected chip, so a narrowed filter is
   visible without reading the label. */
.pf-btn.is-on {
    border-color: var(--alv-accent-line);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    font-weight: 600;
}

.pf-fav.is-on {
    border-color: var(--alv-bad-line);
    background: var(--alv-bad-soft);
    color: var(--alv-bad-ink);
    font-weight: 600;
}

.pf-clear {
    color: var(--alv-accent);
    border-color: transparent;
    background: none;
}

.pf-menu {
    display: none;
    position: absolute;
    z-index: 5;
    top: calc(100% + 4px);
    left: 0;
    min-width: 190px;
    max-height: 240px;
    overflow-y: auto;
    padding: 6px;
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: 6px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
}

.pf-menu.is-open {
    display: block;
}

.pf-menu label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    padding: 6px 8px;
    font-size: 13px;
    font-weight: 400;
    border-radius: 4px;
    cursor: pointer;
}

.pf-menu label:hover {
    background: var(--alv-surface);
}

.pf-menu input {
    margin: 0;
}"""

CSS_PHONE_WAS = """    #pickerList {
        max-height: 50vh;
    }"""
CSS_PHONE_NOW = """    /* PF-2, 19 Oct 2026 - the five controls at 390px. Two per row,
       and the menus go full width rather than hanging off the edge
       of a dialog that is only 340px wide. */
    .pf-drop {
        flex: 1 1 46%;
    }

    .pf-btn {
        width: 100%;
        min-height: 44px;
        justify-content: space-between;
    }

    .pf-fav,
    .pf-clear {
        min-height: 44px;
    }

    .pf-menu {
        left: 0;
        right: 0;
        min-width: 0;
    }

    .pf-menu label {
        min-height: 44px;
    }

    /* THE LIST GIVES UP WHAT THE FILTERS TOOK - PF-2, 19 Oct 2026.

       PK-1 capped this at 50vh after finding MW-1's
       `max-height: none !important` had left the phone list 2,572px
       tall with Add Meal below the fold. Its rule stands: the
       controls under the list must stay on the screen.

       Five filters are 71px taller than one course strip, and that
       pushed Add Meal to 967px on an 844px phone - the same fault
       PK-1 fixed, caused by this round. The list is what gives way,
       because an Add Meal button you cannot reach is a broken dialog
       and three visible cards instead of four is not.

       test_picker_grid measures both and would refuse either. */
    #pickerList {
        max-height: 38vh;
    }"""


# =============================================================== THE JS
JS_WAS = """function openPicker(dateStr, dayName) {
    document.getElementById('pickerDate').value = dateStr;
    document.getElementById('pickerDayName').textContent = dayName;
    document.getElementById('pickerRecipeId').value = '';
    // C19: the box is EMPTIED on every open. It used to arrive holding
    // whatever the last recipe was set to.
    document.getElementById('pickerServings').value = '';
    document.getElementById('pickerSearch').value = '';
    // C19 AGAIN, now that there is a second thing to forget. A dialog
    // that opens still filtered to Dessert, three days after you last
    // used it, is a dialog with no recipes in it.
    pickerCourse = '';
    document.querySelectorAll('.picker-filter .alv-seg button').forEach(
        function (b) {
            b.setAttribute('aria-pressed',
                           b.dataset.course ? 'false' : 'true');
        });
    document.getElementById('pickerAdd').disabled = true;
    document.querySelectorAll('.recipe-option').forEach(function (o) {
        o.classList.remove('selected');
    });
    filterPicker();
    $('#pickerModal').modal('show');
}

// PK-1, 19 Oct 2026 - the search and the course filter COMPOSE.
// Either alone narrows; both together narrow further. The first cut of
// a filter that replaced the search instead of joining it is the kind
// of thing that makes a dialog feel broken when it is only opinionated.
var pickerCourse = '';

function pickCourse(btn) {
    var strip = btn.parentNode;
    strip.querySelectorAll('button').forEach(function (b) {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
    });
    pickerCourse = btn.dataset.course || '';
    filterPicker();
}

function filterPicker() {
    var q = document.getElementById('pickerSearch').value.toLowerCase();
    var shown = 0, total = 0;
    document.querySelectorAll('.recipe-option').forEach(function (o) {
        total += 1;
        var byName = o.dataset.recipeName.indexOf(q) >= 0;
        // SPACE-DELIMITED, AND PADDED AT BOTH ENDS, so course 1 does
        // not match course 11. The template writes a trailing space
        // after every id for the same reason.
        var byCourse = !pickerCourse ||
            (' ' + (o.dataset.recipeCourses || '') + ' ')
                .indexOf(' ' + pickerCourse + ' ') >= 0;
        var on = byName && byCourse;
        o.style.display = on ? '' : 'none';
        if (on) { shown += 1; }
    });
    // HOW MANY OF HOW MANY. The number is the thing that tells you the
    // filter did something rather than the dialog breaking.
    var count = document.getElementById('pickerCount');
    if (count) {
        count.textContent = shown === total
            ? total + ' recipe' + (total === 1 ? '' : 's')
            : shown + ' of ' + total;
    }
    var empty = document.getElementById('pickerEmpty');
    if (empty) { empty.hidden = shown !== 0; }
}"""

JS_NOW = """function openPicker(dateStr, dayName) {
    document.getElementById('pickerDate').value = dateStr;
    document.getElementById('pickerDayName').textContent = dayName;
    document.getElementById('pickerRecipeId').value = '';
    // C19: the box is EMPTIED on every open. It used to arrive holding
    // whatever the last recipe was set to.
    document.getElementById('pickerServings').value = '';
    document.getElementById('pickerSearch').value = '';
    // C19 AGAIN, now with five things to forget rather than one. A
    // dialog that opens still filtered to Dessert, three days after
    // you last used it, is a dialog with no recipes in it.
    pfClear(true);
    document.getElementById('pickerAdd').disabled = true;
    filterPicker();
    $('#pickerModal').modal('show');
}

// PF-2, 19 Oct 2026 - THE FILTERS COMPOSE, AND THE SERVER DECIDES.
//
// PK-1's note is still true and now applies to five things rather
// than two: search and every filter narrow together, never replace
// each other. What changed is WHO answers. Matching five dimensions
// in the browser would mean a second description of what
// `Protein: Chicken` selects, in a second language, drifting from
// recipe_management's.
function pfToggle(which) {
    var menu = document.getElementById('picker' + pfCap(which) + 'Menu')
        || document.getElementById('picker' + pfCap(which));
    var btn = document.getElementById('picker' + pfCap(which) + 'Btn');
    var open = menu.classList.contains('is-open');
    pfCloseAll();
    if (!open) {
        menu.classList.add('is-open');
        if (btn) { btn.setAttribute('aria-expanded', 'true'); }
    }
}

function pfCap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function pfCloseAll() {
    document.querySelectorAll('.pf-menu.is-open').forEach(function (m) {
        m.classList.remove('is-open');
    });
    document.querySelectorAll('.pf-btn[aria-expanded="true"]').forEach(
        function (b) { b.setAttribute('aria-expanded', 'false'); });
}

// A MENU THAT CANNOT BE DISMISSED IS A TRAP. Click anywhere that is
// not inside a dropdown and all of them close.
document.addEventListener('click', function (e) {
    if (!e.target.closest('.pf-drop')) { pfCloseAll(); }
});

function pfChecked(name) {
    var out = [];
    document.querySelectorAll(
        '.picker-filter input[name="' + name + '"]:checked'
    ).forEach(function (i) { out.push(i.value); });
    return out;
}

// THE BUTTON SAYS WHAT IT IS DOING. "All Courses", "Salad", or
// "3 Courses" - a control whose label never changes cannot tell you
// the dialog is narrowed, and an empty grid then reads as broken.
function pfLabel(which, plural) {
    var on = pfChecked(which);
    var span = document.getElementById('picker' + pfCap(which) + 'Label');
    var btn = document.getElementById('picker' + pfCap(which) + 'Btn');
    if (!span) { return; }
    if (!on.length) {
        span.textContent = 'All ' + plural;
    } else if (on.length === 1) {
        var box = document.querySelector(
            '.picker-filter input[name="' + which + '"]:checked');
        span.textContent = (box && box.parentNode.textContent.trim())
            || on[0];
    } else {
        span.textContent = on.length + ' ' + plural;
    }
    if (btn) { btn.classList.toggle('is-on', on.length > 0); }
}

function pfChanged() {
    pfLabel('course', 'Courses');
    pfLabel('category', 'Categories');
    pfLabel('protein', 'Proteins');
    pfLabel('author', 'Authors');
    var any = pfChecked('course').length + pfChecked('category').length +
        pfChecked('protein').length + pfChecked('author').length +
        (pickerFav ? 1 : 0);
    var clear = document.getElementById('pickerClear');
    if (clear) { clear.hidden = any === 0; }
    filterPicker();
}

var pickerFav = false;

function pfFav(btn) {
    pickerFav = !pickerFav;
    btn.setAttribute('aria-pressed', pickerFav ? 'true' : 'false');
    btn.classList.toggle('is-on', pickerFav);
    pfChanged();
}

function pfClear(quiet) {
    document.querySelectorAll('.picker-filter input[type="checkbox"]')
        .forEach(function (i) { i.checked = false; });
    pickerFav = false;
    var fav = document.getElementById('pickerFav');
    if (fav) {
        fav.setAttribute('aria-pressed', 'false');
        fav.classList.remove('is-on');
    }
    pfCloseAll();
    pfLabel('course', 'Courses');
    pfLabel('category', 'Categories');
    pfLabel('protein', 'Proteins');
    pfLabel('author', 'Authors');
    var clear = document.getElementById('pickerClear');
    if (clear) { clear.hidden = true; }
    if (!quiet) { filterPicker(); }
}

// ONE FETCH IN FLIGHT AT A TIME. Typing in the search box fires on
// every keystroke; without this the answer to "sal" can arrive after
// the answer to "salad" and overwrite it. The token is checked when
// the reply lands, which is cheaper than aborting and does not depend
// on AbortController.
var pfSeq = 0;
var pfTimer = null;

function filterPicker() {
    // DEBOUNCED, because the server answers now. 180ms is below the
    // threshold at which a list feels like it is lagging the keyboard
    // and above the one at which every letter is a request.
    if (pfTimer) { clearTimeout(pfTimer); }
    pfTimer = setTimeout(pfFetch, 180);
}

function pfFetch() {
    var mine = ++pfSeq;
    var p = new URLSearchParams();
    var q = document.getElementById('pickerSearch').value.trim();
    if (q) { p.append('search', q); }
    pfChecked('course').forEach(function (v) { p.append('course', v); });
    pfChecked('category').forEach(function (v) { p.append('category', v); });
    pfChecked('protein').forEach(function (v) { p.append('protein', v); });
    pfChecked('author').forEach(function (v) { p.append('author', v); });
    if (pickerFav) { p.append('favourites', '1'); }

    var list = document.getElementById('pickerList');
    var load = document.getElementById('pickerLoading');
    if (load) { load.hidden = false; }
    if (list) { list.setAttribute('aria-busy', 'true'); }

    fetch('{% url "picker_recipes" %}?' + p.toString(), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            if (mine !== pfSeq) { return; }
            pfDraw(d);
        })
        .catch(function () {
            if (mine !== pfSeq) { return; }
            // A DIALOG THAT CANNOT REACH THE SERVER SAYS SO. It used
            // to be impossible for this list to fail, because it was
            // already in the page; now it is possible and silence
            // would read as "no recipes".
            pfDraw({ rows: [], total: 0, shown: 0, error: true });
        });
}

function pfDraw(d) {
    var list = document.getElementById('pickerList');
    var load = document.getElementById('pickerLoading');
    var empty = document.getElementById('pickerEmpty');
    if (load) { load.hidden = true; }
    if (list) { list.setAttribute('aria-busy', 'false'); }

    list.querySelectorAll('.recipe-option').forEach(function (o) {
        o.remove();
    });

    (d.rows || []).forEach(function (r) {
        var card = document.createElement('div');
        card.className = 'recipe-option';
        card.dataset.recipeId = r.id;
        card.dataset.recipeServings = r.servings;
        card.onclick = function () { pickRecipe(card); };

        if (r.photo) {
            var img = document.createElement('img');
            img.loading = 'lazy';
            img.decoding = 'async';
            img.src = r.photo;
            img.alt = '';
            img.className = 'recipe-thumbnail';
            card.appendChild(img);
        } else {
            var ph = document.createElement('div');
            ph.className = 'recipe-thumbnail-placeholder';
            ph.innerHTML = '<i class="fas fa-utensils"></i>';
            card.appendChild(ph);
        }

        // BUILT, NOT INTERPOLATED. A recipe called Ben & Jerry's goes
        // into textContent intact and into innerHTML as a hole; the
        // names come from the server but they came from a person
        // first. SL-4 is the same lesson about alert().
        var box = document.createElement('div');
        var name = document.createElement('strong');
        name.textContent = r.name;
        var small = document.createElement('small');
        small.className = 'text-muted';
        small.textContent = r.minutes + ' min \\u2022 makes ' +
            (r.servings || '?');
        box.appendChild(name);
        box.appendChild(document.createElement('br'));
        box.appendChild(small);
        card.appendChild(box);
        list.insertBefore(card, empty);
    });

    // HOW MANY OF HOW MANY. PK-1's rule, and now it can also say that
    // the answer was cut short, which it could not before.
    var count = document.getElementById('pickerCount');
    if (count) {
        if (d.error) {
            count.textContent = 'could not reach the server';
        } else if (d.capped) {
            count.textContent = 'first ' + d.shown + ' of ' + d.total;
        } else {
            count.textContent = d.total + ' recipe' +
                (d.total === 1 ? '' : 's');
        }
    }
    if (empty) {
        empty.hidden = (d.rows || []).length !== 0;
        var p = empty.querySelector('p');
        if (p) {
            p.textContent = d.error
                ? 'Could not reach the server. Try again.'
                : 'No recipe matches that.';
        }
    }
}"""




# ================================ PK-1'S SUITE, WIDENED BY THIS ROUND
# PK-1 BUILT THE PICKER'S GRID AND ITS COURSE FILTER. This round keeps
# the grid untouched and REPLACES the filter, so twenty of its claims
# stop being true the moment this round lands - which is not PK-1
# being wrong, it is PK-1 being superseded.
#
# REWRITTEN, NOT RETIRED, AND NOT RE-PINNED. What PK-1 was defending -
# a filter that composes with the search rather than replacing it, a
# count, an empty state, and a dialog that forgets last time - is all
# still worth defending. Only the card's course ids go, because they
# existed so the BROWSER could match and this round is the one that
# stopped it matching.
#
# AND THE DRIVEN FILTER CHECKS MOVE TO test_pick_filter. They pressed
# a course button and counted cards; the filter is a GET now, and
# test_pick_filter drives it against a real database over fourteen
# selections, which is more than this section could ever have asked.
# What stays here is what is still PK-1's: the card, its selected
# state, the Add Meal button it arms, the empty state and the grid.
PKS = 'test_picker_grid.py'

PKC_WAS = '''def claims(text):
    """Every source claim PK-1 makes, written once and asked twice."""
    c = {}
    code = T.code_only(text[TPL])
    js = T.code_only_js(text[TPL])
    v = T.python_code_only(text[VIEW])
    body = re.split(r'\\n(?=function )',
                    js.split('function filterPicker()')[-1])[0]'''
PKC_NOW = '''def claims(text):
    """Every source claim PK-1 makes, written once and asked twice.

    WIDENED BY PF-2, 19 Oct 2026. Demetri: "It only allows you to
    choose Course. We need to be able to select Author, Favorites,
    Category and Protein (or vegetarian)."

    Sections 2 to 6 were about a course strip that matched in the
    browser. The picker now offers five filters and the SERVER
    decides, so those claims are rewritten to the controls that
    replaced them rather than deleted - what PK-1 was defending is
    still worth defending, and only the thing doing it changed.

    Section 5 is the exception and is retired outright: the card's
    course ids existed so the browser could match, and this round is
    the one that stopped it matching. In their place, the claim that
    MATTERS now - the page carries no recipe cards at all.
    """
    c = {}
    code = T.code_only(text[TPL])
    js = T.code_only_js(text[TPL])
    v = T.python_code_only(text[VIEW])
    # THE DRAWING MOVED. filterPicker did the matching and the
    # counting; since PF-2 it debounces, and pfDraw does both.
    body = re.split(r'\\n(?=function )',
                    js.split('function pfDraw(')[-1])[0]'''

PKF_WAS = """    # ---- 2. the filter, and it is BASE'S component
    c['there is a course filter'] = 'picker-filter' in code
    c['  built from base\\'s .alv-seg'] = (
        'class="alv-seg" role="group"' in code)
    # PAIRED WITH THE STRIP. A page that has no filter at all writes no
    # .alv-seg rule either, so the absence on its own was true before
    # this round and the control section said so.
    c['  and the page writes no .alv-seg rule of its own'] = (
        'class="alv-seg" role="group"' in code
        and not re.search(r'(?m)^\\s*\\.alv-seg\\s*\\{', code))
    c['  one button per course, out of the context'] = (
        '{% for course in all_courses %}' in code)
    c['  and an All button that is pressed to begin with'] = (
        'data-course="" aria-pressed="true"' in code)

    # ---- 3. the two narrowings COMPOSE
    c['the filter and the search compose'] = (
        'byName && byCourse' in body)
    c['  the typed text still narrows'] = 'byName' in body
    c['  the chosen course narrows too'] = 'byCourse' in body
    c['  matched on ids, padded on BOTH sides'] = (
        "' ' + pickerCourse + ' '" in body)
    c['  so course 1 cannot match course 11'] = (
        "' ' + (o.dataset.recipeCourses || '') + ' '" in body)

    # ---- 4. the count and the empty state
    c['the dialog says how many of how many'] = 'id="pickerCount"' in code
    c['  and names a plain total when nothing is filtered'] = (
        "shown === total" in body)
    c['a filter that matches nothing says so'] = 'id="pickerEmpty"' in code
    c['  rather than looking like a broken dialog'] = (
        'empty.hidden = shown !== 0' in body)

    # ---- 5. every card knows its courses
    c['each card carries its course ids'] = (
        'data-recipe-courses=' in code)
    c['  from a prefetch, not a query per card  [E29]'] = (
        "prefetch_related('courses')" in v)
    c['  and the context hands the strip its courses'] = (
        "'all_courses':" in v)

    # ---- 6. C19, now that there is a second thing to forget
    c['the filter is reset when the dialog opens  [C19]'] = (
        "pickerCourse = '';" in js.split('function openPicker')[-1]
        .split('\\nfunction ')[0])
    c['  and the All button pressed again with it'] = (
        "b.dataset.course ? 'false' : 'true'" in js)"""

PKF_NOW = """    # ---- 2. the filter - FIVE of them since PF-2, 19 Oct 2026
    c['there is a filter'] = 'picker-filter' in code
    c['  five of them, by name'] = (
        all('name=\"%s\"' % n in code
            for n in ('course', 'category', 'protein', 'author'))
        and 'id=\"pickerFav\"' in code)
    c['  and Vegetarian rides in the protein menu'] = (
        'value=\"vegetarian\"' in code)
    # PAIRED WITH THE CONTROL, exactly as PK-1 paired it with the
    # strip. A page that has no filter at all writes no component rule
    # either, so the absence on its own was true before PK-1 and the
    # control section said so.
    c['  and the page writes no .alv-seg rule of its own'] = (
        'class=\"pf-btn\"' in code
        and not re.search(r'(?m)^\\s*\\.alv-seg\\s*\\{', code))
    c['  one entry per course, out of the context'] = (
        '{% for course in courses %}' in code)
    c['  and every menu starts with nothing chosen'] = (
        'All Courses' in code and 'All Authors' in code)

    # ---- 3. the narrowings COMPOSE - on the server since PF-2
    c['the filters and the search compose'] = (
        \"p.append('search'\" in js and \"p.append('course'\" in js)
    c['  the typed text still narrows'] = \"p.append('search'\" in js
    c['  and each of the five narrows too'] = (
        all(\"p.append('%s'\" % n in js
            for n in ('course', 'category', 'protein', 'author'))
        and \"p.append('favourites'\" in js)
    # NEITHER REPLACES THE OTHER, which was PK-1's whole point about
    # composing: every narrowing goes into ONE query string.
    c['  all of them into one request, never one replacing another'] = (
        js.split('function pfFetch(')[-1].split('\\nfunction ')[0]
        .count('fetch(') == 1)
    c['  and only the newest answer is drawn'] = 'mine !== pfSeq' in js

    # ---- 4. the count and the empty state
    c['the dialog says how many of how many'] = 'id=\"pickerCount\"' in code
    c['  and names a plain total when nothing is filtered'] = (
        \"d.total + ' recipe'\" in body)
    c['a filter that matches nothing says so'] = 'id=\"pickerEmpty\"' in code
    c['  rather than looking like a broken dialog'] = (
        'empty.hidden = (d.rows || []).length !== 0' in body)
    # AND A DIALOG THAT CANNOT REACH THE SERVER SAYS THAT TOO - a case
    # that could not exist while the list was in the page.
    c['  and says so differently when the server cannot be reached'] = (
        'could not reach the server' in body)

    # ---- 5. RETIRED BY PF-2, and replaced by what matters now
    #
    # `data-recipe-courses` on every card existed so the BROWSER could
    # match. This round stopped it matching, so the attribute is gone
    # and with it the claim. What took its place is the thing the
    # attribute was costing: the page no longer carries the library.
    c['the page carries no recipe cards at all'] = (
        '{% for recipe in all_recipes %}' not in code
        and 'data-recipe-courses=' not in code)
    c['  the dialog fetches them when it opens'] = (
        '{% url \"picker_recipes\" %}' in js)
    c['  and the view still prefetches courses  [E29]'] = (
        \"prefetch_related('courses')\" in v)

    # ---- 6. C19, now that there are five things to forget
    c['the filters are reset when the dialog opens  [C19]'] = (
        'pfClear(true);' in js.split('function openPicker')[-1]
        .split('\\nfunction ')[0])
    c['  and every menu label goes back to All with them'] = (
        \"span.textContent = 'All ' + plural\" in js)"""


# ---- PK-1's STATE reads a data attribute this round removed.
PKST_WAS = """        shown: [...document.querySelectorAll('.recipe-option')]
                 .filter(o => o.style.display !== 'none')
                 .map(o => o.dataset.recipeName),
        empty: !document.getElementById('pickerEmpty').hidden,
        pressed: [...document.querySelectorAll('.picker-filter button')]
                   .filter(b => b.getAttribute('aria-pressed') === 'true')
                   .map(b => b.textContent.trim())"""
PKROWS_WAS = """    with sync_playwright() as _pw:"""
PKROWS_NOW = """    # THE ROWS THE ENDPOINT WOULD ANSWER - PF-2, 19 Oct 2026, built
    # HERE and not in the block below: a queryset evaluated inside
    # sync_playwright raises SynchronousOnlyOperation, because the
    # sync api runs on an event loop and the ORM refuses to be called
    # from one. Cost one run to find out.
    ROWS = [{'id': r.recipe_id, 'name': r.recipe_name,
             'servings': r.servings, 'minutes': 30, 'photo': ''}
            for r in Recipe.objects.order_by('recipe_name')]
    DRAW = (\'(rows) => pfDraw({rows: rows, total: rows.length, \'
            \'shown: rows.length})\')

    with sync_playwright() as _pw:"""

PKST_NOW = """        // THE NAME COMES OFF THE CARD - PF-2, 19 Oct 2026. It used
        // to come from data-recipe-name, which existed so the browser
        // could match on it. Adding the attribute back for a test to
        // read would be a suite shaping the page it judges.
        shown: [...document.querySelectorAll('.recipe-option')]
                 .filter(o => o.style.display !== 'none')
                 .map(o => o.querySelector('strong').textContent
                            .trim().toLowerCase()),
        empty: !document.getElementById('pickerEmpty').hidden,
        pressed: [...document.querySelectorAll('.picker-filter button')]
                   .filter(b => b.getAttribute('aria-pressed') === 'true')
                   .map(b => b.textContent.trim())"""

# ---- the driven filter checks, which belong to test_pick_filter now
PKD_WAS = """        s = pg.evaluate(STATE)
        ok(len(s['shown']) == 30, 'the dialog opens showing all thirty',
           len(s['shown']))
        ok(s['count'] == '30 recipes',
           '  and says so in words, not as a fraction', s['count'])
        ok(s['pressed'] == ['All'], '  with All pressed', s['pressed'])
        ok(not s['empty'], '  and no empty state')

        # ---- THE FILTER NARROWS
        pg.evaluate(\"\"\"(id) => {
            const b = [...document.querySelectorAll('.picker-filter button')]
                        .find(x => x.dataset.course === String(id));
            pickCourse(b);
        }\"\"\", DESSERT.recipe_course_id)
        s = pg.evaluate(STATE)
        ok(s['pressed'] == ['Dessert'],
           'pressing Dessert presses only Dessert', s['pressed'])
        ok('baklava' in s['shown'],
           '  and Baklava is showing', s['shown'])
        ok(all('avgolemono' != n for n in s['shown']),
           '  while Avgolemono, a Starter, is not', s['shown'])
        ok(s['count'].endswith(' of 30'),
           '  and the count reads as a fraction now - %s' % s['count'],
           s['count'])
        n_dessert = len(s['shown'])

        # ---- AND THE SEARCH COMPOSES WITH IT, which is the claim
        pg.evaluate(\"\"\"() => {
            document.getElementById('pickerSearch').value = 'ba';
            filterPicker();
        }\"\"\")
        s = pg.evaluate(STATE)
        ok(s['shown'] == ['baklava'],
           'typing \"ba\" ON TOP of Dessert leaves Baklava alone - the two '
           'COMPOSE, neither replaces the other', s['shown'])
        ok(s['pressed'] == ['Dessert'],
           '  and Dessert is still pressed - typing did not clear it',
           s['pressed'])

        # ---- EITHER ALONE STILL WORKS
        pg.evaluate(\"\"\"() => {
            const b = [...document.querySelectorAll('.picker-filter button')]
                        .find(x => !x.dataset.course);
            pickCourse(b);
        }\"\"\")
        s = pg.evaluate(STATE)
        ok(s['shown'] == ['baklava'],
           'clearing the course leaves the search doing the work',
           s['shown'])
        pg.evaluate(\"\"\"() => {
            document.getElementById('pickerSearch').value = '';
            filterPicker();
        }\"\"\")
        s = pg.evaluate(STATE)
        ok(len(s['shown']) == 30, '  and clearing both shows all thirty',
           len(s['shown']))

        # ---- A FILTER THAT MATCHES NOTHING SAYS SO
        pg.evaluate(\"\"\"() => {
            document.getElementById('pickerSearch').value = 'zzzzz';
            filterPicker();
        }\"\"\")
        s = pg.evaluate(STATE)
        ok(s['shown'] == [], 'a search that matches nothing hides every card')
        ok(s['empty'],
           '  AND THE DIALOG SAYS SO - an empty grid with no message is '
           'a dialog that looks broken')
        ok(s['count'] == '0 of 30', '  with the count at zero', s['count'])

        # ---- AND THE THING HE ACTUALLY REPORTED
        pg.evaluate(\"\"\"() => {
            document.getElementById('pickerSearch').value = '';
            filterPicker();
            pickRecipe(document.querySelector('.recipe-option'));
        }\"\"\")"""

PKD_NOW = """        # THE DIALOG ARRIVES EMPTY NOW - PF-2, 19 Oct 2026, and this
        # is the whole of what moved.
        #
        # PK-1's picker had every recipe in its markup, so opening it
        # was enough to have thirty cards. PF-2 took them out: the
        # dialog asks picker_recipes, and a page loaded with
        # set_content has no server to ask.
        #
        # THE FILTER'S OWN BEHAVIOUR MOVED WITH IT. Pressing a course
        # button and counting cards tested a matcher that no longer
        # exists in this page. test_pick_filter drives the real
        # endpoint against a real database over fourteen selections,
        # including the three-way protein branch this section could
        # never have reached - so that claim is asked THERE, better,
        # and asking a weaker version of it here as well would be two
        # instruments disagreeing waiting to happen.
        #
        # WHAT STAYS IS WHAT IS STILL PK-1'S: the card, its selected
        # state, the Add Meal button it arms, the empty state, and the
        # grid in section 5. All of it needs cards, so the rows the
        # endpoint really answers are handed to the page's own pfDraw.
        # ROWS and DRAW are built ABOVE this block, never in it: a
        # queryset evaluated inside sync_playwright raises
        # SynchronousOnlyOperation, because the sync api runs on an
        # event loop and the ORM refuses to be called from one.
        pg.evaluate(DRAW, ROWS)
        s = pg.evaluate(STATE)
        ok(len(s['shown']) == 30,
           \"the thirty rows the endpoint answered are drawn by the \"
           \"page's own pfDraw\", len(s['shown']))
        ok(s['count'] == '30 recipes',
           '  and the count says so in words, not as a fraction',
           s['count'])
        ok(not s['empty'], '  and no empty state')

        # ---- A LIST WITH NOTHING IN IT SAYS SO
        pg.evaluate('() => pfDraw({rows: [], total: 0, shown: 0})')
        s = pg.evaluate(STATE)
        ok(s['shown'] == [], 'no rows means no cards')
        ok(s['empty'],
           '  AND THE DIALOG SAYS SO - an empty grid with no message is '
           'a dialog that looks broken')
        ok(s['count'] == '0 recipes', '  with the count at zero',
           s['count'])

        # ---- AND A DIALOG THAT CANNOT REACH THE SERVER, which could
        # not happen at all while the list was in the page.
        pg.evaluate('() => pfDraw({rows: [], total: 0, shown: 0, '
                    'error: true})')
        s = pg.evaluate(STATE)
        ok(s['empty'] and 'server' in s['count'],
           '  and says something DIFFERENT when it could not ask - '
           '%r' % s['count'], s['count'])

        # ---- AND THE THING HE ACTUALLY REPORTED
        pg.evaluate(DRAW, ROWS)
        pg.evaluate(\"\"\"() => {
            pickRecipe(document.querySelector('.recipe-option'));
        }\"\"\")"""

# ---- section 5 needs cards too
PKR_WAS = """            pg.set_content(DRESSED, wait_until='domcontentloaded')
            pg.evaluate(OPEN)
            m = pg.evaluate(\"\"\"() => {
                const cs = [...document.querySelectorAll('.recipe-option')];"""
PKR_NOW = """            pg.set_content(DRESSED, wait_until='domcontentloaded')
            pg.evaluate(OPEN)
            # CARDS FIRST - PF-2, 19 Oct 2026. The grid is measured by
            # what is IN it, and since this round nothing is until the
            # dialog has asked. Same rows, same pfDraw.
            pg.evaluate(DRAW, ROWS)
            m = pg.evaluate(\"\"\"() => {
                const cs = [...document.querySelectorAll('.recipe-option')];"""


# ---- PK-1's own three remaining checks about the control that left
PKQ_WAS = """    body = resp.content.decode('utf-8', 'replace')
    ok(body.count('class="recipe-option"') == 30,
       '  and all thirty cards are drawn',
       body.count('class="recipe-option"'))
    ok(body.count('data-course=') == len(COURSES) + 1,
       '  with %d course buttons - one per course, plus All'
       % (len(COURSES) + 1), body.count('data-course='))"""
PKQ_NOW = """    body = resp.content.decode('utf-8', 'replace')
    # NONE OF THEM ARE DRAWN, WHICH IS THE POINT - PF-2, 19 Oct 2026.
    # This asked for thirty cards in the markup and got them, because
    # PK-1's dialog carried the whole library whether it was opened or
    # not. That is the cost this round removed, so the number it
    # checks for is now zero and the assertion is the opposite one.
    ok(body.count('class="recipe-option"') == 0,
       '  and NOT ONE card is in the page - thirty were, before this '
       'round, on every load whether the dialog opened or not',
       body.count('class="recipe-option"'))
    ok(body.count('data-course=') == 0,
       '  nor a single course id: the browser stopped matching, so the '
       'cards stopped carrying what it matched on',
       body.count('data-course='))
    # AND THE CONTROLS ARE STILL DRAWN, because a few dozen options is
    # not a few hundred recipes - which is the whole shape of the
    # trade this round made.
    ok(body.count('class="pf-btn"') == 4 and 'id="pickerFav"' in body,
       '  while all five filter controls ARE drawn',
       body.count('class="pf-btn"'))"""

PKW_WAS = """for text in ('picker-filter', 'function pickCourse('):"""
PKW_NOW = """# PF-2, 19 Oct 2026 - pfChanged replaced pickCourse. The claim is
# unchanged: whatever drives this filter belongs to one dialog.
for text in ('picker-filter', 'function pfChanged('):"""

PKP_WAS = """for text in ('function pickCourse(', 'id="pickerCount"',
             "prefetch_related('courses')"):"""
PKP_NOW = """# PF-2, 19 Oct 2026 - the gate row moved with the function it pins.
for text in ('function pfChanged(', 'id="pickerCount"',
             "prefetch_related('courses')"):"""


# ========================================== THE ONE TREE-WIDE RE-PIN
# EXPECT_PAIRS COUNTS EVERY RULE IN THE TREE THAT SETS BOTH A
# BACKGROUND AND A COLOUR, and this round adds five:
#
#   .pf-btn, .pf-fav, .pf-clear   one rule, three selectors
#   .pf-btn.is-on                 the accent tint on a narrowed filter
#   .pf-fav.is-on                 the same for Favourites
#
# 695 -> 700. A RE-PIN AND NOT A REPAIR, which is the distinction that
# matters: the AA table below the count is UNTOUCHED, because all five
# are house pairs taken from base's own tokens. Nothing in this round
# reads below AA.
#
# It did once. test_verb_colours caught `.pf-btn .fa-chevron-down` at
# 3.0:1 on the first sweep after this round - --alv-ink-faint on
# paper. That was a REPAIR, not a re-pin: the token changed to
# --alv-ink-soft and the count went back by itself. A number is only
# allowed to move when the thing it counts really grew.
#
# test_recipe_spice reads EXPECT_PAIRS out of this file rather than
# keeping its own copy, so one line moves both.
PAIR = 'test_pair_contrast.py'
PAIR_WAS = """EXPECT_PAIRS = 695   # MO-1, 19 Oct 2026"""
PAIR_NOW = """EXPECT_PAIRS = 700   # PF-2, 19 Oct 2026 - five rules, the picker's five filter controls and the two tints that mark a narrowed one. All house pairs off base's own tokens, so the AA table below is untouched and the gross count is what moved. The one rule in this round that DID read below AA - the chevron at 3.0:1 - was fixed rather than pinned.   # (was 695)   # MO-1, 19 Oct 2026"""

def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pf = os.path.join(root, FILT)
    pc = os.path.join(root, CRUD)
    pmv = os.path.join(root, MEAL)
    pu = os.path.join(root, URLS)
    pt = os.path.join(root, TPL)

    crud = read(pc)
    meal = read(pmv)
    tpl = read(pt)
    tpl_before = tpl

    # ---------------------------------------------------------------- 0
    # ASK THE TREE FIRST.
    if os.path.exists(pf) and 'def picker_recipes(' in meal:
        print('PF-2  already applied - the picker asks the server.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE, and it has two halves: the library owns
    # the only copy of the filter, and the picker has only a course
    # strip. A round that fixes neither is a round whose suite is
    # measuring the weather.
    if CRUD_BLOCK_WAS.replace('\r\n', '\n') not in crud.replace('\r\n', '\n'):
        refuse('%s does not hold the filter block this round moves - it '
               'may already have been changed by hand' % CRUD)
    if 'all_recipes' not in meal:
        refuse('%s does not pass all_recipes, so there is nothing to take '
               'off the planner page' % MEAL)
    n_cards = tpl.count('{% for recipe in all_recipes %}')
    if n_cards != 1:
        refuse('%s renders all_recipes %d time(s), expected exactly 1'
               % (TPL, n_cards))
    if os.path.exists(pf):
        refuse('%s already exists' % FILT)

    # ---------------------------------------------------------------- 2
    out[pf] = MODULE

    crud = swap(crud, CRUD_IMP_WAS, CRUD_IMP_NOW, '%s (the import)' % CRUD)
    crud = swap(crud, CRUD_WAS, CRUD_NOW, '%s (the reading)' % CRUD)
    crud = swap(crud, CRUD_BLOCK_WAS, CRUD_BLOCK_NOW,
                '%s (the filter block)' % CRUD)
    out[pc] = crud

    meal = swap(meal, MEAL_IMP_WAS, MEAL_IMP_NOW, '%s (the import)' % MEAL)
    meal = swap(meal, MEAL_CTX_WAS, MEAL_CTX_NOW, '%s (the context)' % MEAL)
    out[pmv] = meal.rstrip('\r\n') + fit(meal, ENDPOINT)

    out[pu] = swap(read(pu), URL_WAS, URL_NOW, '%s (the route)' % URLS)

    tpl = swap(tpl, FILTER_WAS, FILTER_NOW, '%s (the filter strip)' % TPL)
    tpl = swap(tpl, LIST_WAS, LIST_NOW, '%s (the list)' % TPL)
    tpl = swap(tpl, CSS_WAS, CSS_NOW, '%s (the strip CSS)' % TPL)
    tpl = swap(tpl, CSS_PHONE_WAS, CSS_PHONE_NOW, '%s (the phone CSS)' % TPL)
    tpl = swap(tpl, JS_WAS, JS_NOW, '%s (the picker JS)' % TPL)
    out[pt] = tpl

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, PK1_WAS, PK1_NOW, '%s (PK-1 pickCourse sentinel)' % PS1)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- 3b
    # PK-1'S SUITE. Carried by the round that superseded it, so a
    # half-applied tree stays green either way round.
    pk = os.path.join(root, PKS)
    k = read(pk)
    k = swap(k, PKC_WAS, PKC_NOW, '%s (the claims docstring)' % PKS)
    k = swap(k, PKF_WAS, PKF_NOW, '%s (the superseded claims)' % PKS)
    k = swap(k, PKST_WAS, PKST_NOW, '%s (STATE)' % PKS)
    k = swap(k, PKROWS_WAS, PKROWS_NOW, '%s (the rows)' % PKS)
    k = swap(k, PKD_WAS, PKD_NOW, '%s (the driven filter)' % PKS)
    k = swap(k, PKR_WAS, PKR_NOW, '%s (the render needs cards)' % PKS)
    k = swap(k, PKQ_WAS, PKQ_NOW, '%s (the page census)' % PKS)
    k = swap(k, PKW_WAS, PKW_NOW, '%s (the wide check)' % PKS)
    k = swap(k, PKP_WAS, PKP_NOW, '%s (its own sentinels)' % PKS)
    out[pk] = k

    pc = os.path.join(root, PAIR)
    out[pc] = swap(read(pc), PAIR_WAS, PAIR_NOW,
                   '%s (EXPECT_PAIRS)' % PAIR)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    # THE SHARED FUNCTION IS THE ONLY COPY. This is the whole round:
    # if the library kept its own filter the two would drift, which is
    # what choosing the server over JavaScript was meant to prevent.
    sys.path.insert(0, root)
    import alv_tree as T
    ccode = T.python_code_only(out[pc], payloads=True)
    for clause, why in (
            ('courses__recipe_course_id__in', 'the course clause'),
            ('categories__recipe_category_id__in', 'the category clause'),
            ('proteins__custom_protein_id__in', 'the protein clause'),
            ('favourited_by__user', 'the favourites clause')):
        if clause in ccode:
            refuse('%s still contains %s after the move - there would be '
                   'TWO descriptions of what a filter selects, which is '
                   'the fault this round exists to remove' % (CRUD, why))
    fcode = T.python_code_only(out[pf], payloads=True)
    for clause in ('recipe_name__icontains',
                   'recipe_ingredients__ingredient__name__icontains',
                   'courses__recipe_course_id__in',
                   'categories__recipe_category_id__in',
                   'proteins__custom_protein_id__in',
                   'is_vegetarian=True', 'author__in',
                   'favourited_by__user', '.distinct()'):
        if clause not in fcode:
            refuse('%s is missing %r - every clause the library had must '
                   'be in the shared function' % (FILT, clause))

    # THE PLANNER PAGE NO LONGER CARRIES THE LIBRARY.
    if 'all_recipes' in T.python_code_only(out[pmv], payloads=True):
        refuse('%s still names all_recipes in code' % MEAL)
    nt = out[pt]
    if 'all_recipes' in T.code_only(nt):
        refuse('%s still renders all_recipes' % TPL)

    # ALL FIVE FILTERS ARE REALLY THERE, asked of the markup with
    # comments blanked - a comment about a filter is not a filter.
    markup = T.code_only(nt)
    for nm in ('course', 'category', 'protein', 'author'):
        if 'name="%s"' % nm not in markup:
            refuse('%s: no control writes name="%s"' % (TPL, nm))
    if 'value="vegetarian"' not in markup:
        refuse('%s: the vegetarian entry is missing from the protein '
               'menu - it is a column and not a row, so it cannot have '
               'an id and must travel as the literal' % TPL)
    if 'id="pickerFav"' not in markup:
        refuse('%s: no favourites control' % TPL)

    # AND THE OLD ONES ARE GONE, so nothing calls a function that
    # left. An onclick naming a deleted function is a dead control
    # that looks alive.
    js = T.code_only_js(nt)
    # THE OLD GLOBAL AND ITS HANDLER, by their declarations - not by
    # their names as substrings. `pickerCourse` is a substring of
    # `pickerCourseBtn`, which is an id this round ADDS, and the first
    # cut of this gate refused the round over its own markup.
    for dead in ('var pickerCourse', 'function pickCourse('):
        if dead in js:
            refuse('%s: %r survives the rewrite' % (TPL, dead))
    if 'onclick="pickCourse(' in markup:
        refuse('%s: a control still calls pickCourse()' % TPL)
    for live in ('pfToggle(', 'pfChanged(', 'pfFav(', 'pfClear(',
                 'pfFetch(', 'pfDraw('):
        if live not in js:
            refuse('%s: %r is missing' % (TPL, live))

    # EVERY onclick NAMES A FUNCTION THAT EXISTS. PK-1's dialog could
    # not open at all for a release because of a call that was never
    # defined on this page.
    for fn in sorted(set(re.findall(r'onclick="(\w+)\(', markup))):
        if ('function %s(' % fn) not in js:
            refuse('%s: onclick calls %s() and this page does not define '
                   'it' % (TPL, fn))

    # TEMPLATE TAGS BALANCE.
    for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
        if (nt.count(a) - tpl_before.count(a)
                != nt.count(b) - tpl_before.count(b)):
            refuse('%s: this round added %d %s and %d %s'
                   % (TPL, nt.count(a) - tpl_before.count(a), a,
                      nt.count(b) - tpl_before.count(b), b))
    o, c = nt.count('/*'), nt.count('*/')
    if o != c:
        refuse('%s: %d /* against %d */' % (TPL, o, c))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('PF-2 --check')
        print('  shared     %s (%d lines)'
              % (os.path.basename(FILT), MODULE.count('\n')))
        print('  library    its own filter block removed, calls the '
              'shared one')
        print('  endpoint   picker_recipes, GET, read tier')
        print('  page       all_recipes gone - %d recipe cards leave '
              'the planner markup' % 336)
        print('  filters    course, category, protein (+vegetarian), '
              'author, favourites')
        print('  repairs    %s - its course filter is what this '
              'round replaced' % PKS)
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        if os.path.exists(q):
            backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('PF-2  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('   %s is NEW and has no backup - there was no before.'
          % os.path.basename(FILT))
    print('Now run:  python test_pick_filter.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
