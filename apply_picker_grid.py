# -*- coding: utf-8 -*-
"""apply_picker_grid.py - round PK-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE PICKER IS A GRID.

Demetri, 19 Oct, on the Add-a-Meal picker on the live site:

    "There is no search or filtering.... also there is so much wasted
     space on the right of each recipe. Should it not be a grid?"
    "Also, I am not able to select a recipe"

FOUR THINGS, AND THEY HAVE ONE ROOT. `.recipe-option` HAS NEVER HAD A
CSS RULE. Not on this page, not in base.html, not in any of the
twenty-seven backups of this template or of the calendar it descends
from. The markup is an image and a block of text side by side with
nothing laying them out, inside a container with nothing laying IT out,
and pickRecipe() has added a `.selected` class since the picker was
written with nothing anywhere drawing it.

    NOT ABLE TO SELECT     He almost certainly could. The click lands,
                           the class goes on, and NOTHING CHANGES on
                           screen - the only signal is the Add Meal
                           button un-greying at the foot of a list he
                           has scrolled past. MW-1 fixed this half
                           this morning, after he chose to fold it in.

    WASTED SPACE / A GRID  One column in a modal-lg, because there was
                           no layout rule at all. This round.

    NO SEARCH              There IS a search box and it works. What is
                           missing is anything to narrow BY, which is
                           the next line.

    NO FILTERING           Correct. Recipes carry courses already -
                           Starter, Main, Dessert - and the picker
                           ignored them, so finding a dinner meant
                           reading past every cake in the book.

WHAT THIS ROUND DOES. The list becomes a grid of cards that fills the
dialog's width; a house .alv-seg above it filters by course; the search
and the filter compose rather than fight; and a line says how many of
how many are showing, so a filter that hides everything says so instead
of looking like a bug.

IT BUILDS ON MW-1 RATHER THAN REPLACING IT. MW-1 gave .recipe-option
the row layout and the two-signal selected state it never had - that is
what unblocks him and it is already in this push. This round turns the
LIST into a grid and adds the filter; the row inside each card is
MW-1's, unchanged.

ONE QUERY, NOT ONE PER CARD. Each card carries the course ids it
belongs to so the filter can work in the browser with no round trip,
and reading those ids is a query per recipe unless the view asks for
them - so all_recipes gains prefetch_related('courses'). E29 spent a
round taking that fault off four screens.

NO MIGRATION. RecipeCourse and Recipe.courses have been in the model
since long before release 3.

Idempotent. Every file backed up to .bak_pickergrid.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_pickergrid'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_picker_grid.py'
PATCHER = 'apply_picker_grid.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PK-1, 19 Oct 2026'
CHECK = False


# ========================================================== THE CONTEXT
CTX_WAS = """        'all_recipes': Recipe.objects.all().order_by('recipe_name'),"""
CTX_NOW = """        # PK-1, 19 Oct 2026 - prefetch_related('courses'), because
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


# =============================================================== THE CSS
# THE LIST BECOMES A GRID. MW-1's rules for the ROW inside each card
# stay exactly as they are; what changes is the container and the one
# rule that only made sense in a single column.
CSS_WAS = """#pickerList {
    max-height: 320px;
    overflow-y: auto;
}"""
CSS_NOW = """/* THE PICKER IS A GRID - PK-1, 19 Oct 2026. Demetri: "there is so
   much wasted space on the right of each recipe. Should it not be a
   grid?" It should: this is a modal-lg and the list was one column.

   auto-fill with a 240px floor, so the dialog decides how many columns
   fit rather than this rule deciding for it - three on a desktop, two
   on a tablet, one on a phone, and nothing to re-pin when the dialog
   width changes. The cap grows from 320px to 420px because a grid is
   three times shorter than the column it replaces. */
#pickerList {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 8px;
    max-height: 420px;
    overflow-y: auto;
    align-content: start;
}

/* THE FILTER STRIP. base owns .alv-seg - its CSS, its pressed state
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
}

/* HOW MANY OF HOW MANY. A filter that hides everything has to say so,
   or it reads as a broken dialog - which is the same class of fault as
   the selected state nothing drew. */
.picker-count {
    font-size: 12px;
    color: var(--alv-ink-soft);
    margin-left: auto;
}

.picker-empty {
    grid-column: 1 / -1;
    text-align: center;
    padding: 24px 12px;
    color: var(--alv-ink-faint);
}"""

# AND THE PHONE OVERRIDE HAS TO GO WITH IT.
#
# MW-1 restored `#pickerList { max-height: none !important; }` inside
# the under-768px block, on the reasoning that the override had been
# written to undo a desktop cap and should be kept now that there was
# a cap to undo. That was right for a COLUMN and is wrong for a GRID:
# this round's suite measured the phone list at 2,572px, which puts
# the Servings field and the Add Meal button two and a half thousand
# pixels below the fold on the screen a week is usually planned on.
#
# 50vh, so the cap is half of whatever screen it is on rather than a
# number that is right on one handset. The list scrolls; the controls
# under it stay reachable, which is the whole reason a cap exists.
PHONE_WAS = """    #pickerList {
        max-height: none !important;
    }"""
PHONE_NOW = """    /* HALF THE SCREEN, NOT NO LIMIT - PK-1, 19 Oct 2026. MW-1 put
       `max-height: none !important` back here when it gave the list
       its first desktop cap, and that was right while the list was
       one column of rows. It is a GRID now, and a one-column grid of
       thirty cards measured 2,572px on a phone - the Servings field
       and the Add Meal button both below the fold, with nothing on
       screen to say they were there. */
    #pickerList {
        max-height: 50vh;
    }"""


# THE CARD LOSES ITS BOTTOM MARGIN. In a column that margin was the
# gap; in a grid the gap is the gap, and the margin would add to it on
# every row but the last.
MARGIN_WAS = """.recipe-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
    background: var(--alv-paper);"""
MARGIN_NOW = """.recipe-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    /* NO margin-bottom - PK-1, 19 Oct 2026. MW-1 gave this row an 8px
       bottom margin because it sat in a column and that margin was the
       gap between cards. #pickerList is a grid now and `gap` does
       that; a margin as well would show on every row but the last. */
    background: var(--alv-paper);"""

LAST_WAS = """.recipe-option:last-child {
    margin-bottom: 0;
}

.recipe-option:hover {
    border-color: var(--alv-accent);
}"""
LAST_NOW = """/* .recipe-option:last-child went with the margin - PK-1. */

.recipe-option:hover {
    border-color: var(--alv-accent);
}

/* A CARD IS AS TALL AS THE TALLEST IN ITS ROW, and the text inside it
   has to survive that: a recipe name of four words in a 240px column
   wraps, and the thumbnail must not shrink to make room for it. */
.recipe-option > div {
    min-width: 0;
}

.recipe-option > div strong {
    overflow-wrap: break-word;
}"""


# ============================================================ THE MARKUP
# THE FILTER STRIP, above the list, and the count beside it.
LIST_WAS = """                    <div class="form-group">
                        <label for="pickerList"><strong>Choose one</strong></label>
                        <div id="pickerList">"""
LIST_NOW = """                    <div class="form-group">
                        <label for="pickerList"><strong>Choose one</strong></label>
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
                        </div>
                        <div id="pickerList">"""

# AND EVERY CARD SAYS WHICH COURSES IT IS IN, so the filter needs no
# round trip. The ids, not the names - a course that gets renamed
# should not silently stop matching.
CARD_WAS = """                            <div class="recipe-option"
                                 data-recipe-id="{{ recipe.recipe_id }}"
                                 data-recipe-servings="{{ recipe.servings|default:4 }}"
                                 data-recipe-name="{{ recipe.recipe_name|lower }}"
                                 onclick="pickRecipe(this)">"""
CARD_NOW = """                            <div class="recipe-option"
                                 data-recipe-id="{{ recipe.recipe_id }}"
                                 data-recipe-servings="{{ recipe.servings|default:4 }}"
                                 data-recipe-name="{{ recipe.recipe_name|lower }}"
                                 {# PK-1, 19 Oct 2026 - the ids, not the   #}
                                 {# names: a course that is renamed should #}
                                 {# not silently stop matching. Read from  #}
                                 {# a prefetch, so this is not a query per #}
                                 {# card.                                  #}
                                 data-recipe-courses="{% for c in recipe.courses.all %}{{ c.recipe_course_id }} {% endfor %}"
                                 onclick="pickRecipe(this)">"""

# THE EMPTY STATE, inside the grid so it is centred across it.
EMPTY_WAS = """                            {% endfor %}
                        </div>
                    </div>"""
EMPTY_NOW = """                            {% endfor %}
                            {# A FILTER THAT HIDES EVERYTHING SAYS SO -  #}
                            {# PK-1. Otherwise an empty dialog reads as  #}
                            {# a broken one, which is the same class of  #}
                            {# fault as a selected state nothing drew.   #}
                            <div class="picker-empty" id="pickerEmpty" hidden>
                                <i class="fas fa-search"></i>
                                <p>No recipe matches that.</p>
                            </div>
                        </div>
                    </div>"""


# ================================================================ THE JS
JS_WAS = """function filterPicker() {
    var q = document.getElementById('pickerSearch').value.toLowerCase();
    document.querySelectorAll('.recipe-option').forEach(function (o) {
        o.style.display = o.dataset.recipeName.indexOf(q) >= 0 ? '' : 'none';
    });
}"""
JS_NOW = """// PK-1, 19 Oct 2026 - the search and the course filter COMPOSE.
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

# AND THE PICKER RESETS ITS FILTER AS IT OPENS, like everything else on
# this page - C19, which this screen paid for once already.
OPEN_WAS = """    document.getElementById('pickerSearch').value = '';
    document.getElementById('pickerAdd').disabled = true;"""
OPEN_NOW = """    document.getElementById('pickerSearch').value = '';
    // C19 AGAIN, now that there is a second thing to forget. A dialog
    // that opens still filtered to Dessert, three days after you last
    // used it, is a dialog with no recipes in it.
    pickerCourse = '';
    document.querySelectorAll('.picker-filter .alv-seg button').forEach(
        function (b) {
            b.setAttribute('aria-pressed',
                           b.dataset.course ? 'false' : 'true');
        });
    document.getElementById('pickerAdd').disabled = true;"""


# ========================================================== THE IMPORT
IMP_WAS = """    Recipe,
    RecipeCategory,
    RecipeCourse,"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'mini-calendar-grid - MC-4'; What = 'MC-4: and the grid closes AFTER the loop that fills it' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'mini-calendar-grid - MC-4'; What = 'MC-4: and the grid closes AFTER the loop that fills it' },
    # ------------------------------------------------- PK-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: repeat(auto-fill, minmax(240px, 1fr))'; What = 'PK-1: the recipe picker is a grid, not one column in a wide dialog' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'function pickCourse('; What = 'PK-1: and it filters by course, composing with the search rather than replacing it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerCount"'; What = 'PK-1: and says how many of how many are showing' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "prefetch_related('courses')"; What = 'PK-1: the course ids come from one query, not one per card' },"""

SUITE_WAS = """    'test_mini_grid.py'
)"""
SUITE_NOW = """    'test_mini_grid.py',
    # PK-1, 19 Oct 2026 - the picker is a grid, and it filters.
    # Demetri on the live dialog: "there is so much wasted space
    # on the right of each recipe. Should it not be a grid?"
    'test_picker_grid.py'
)"""

TREE_WAS = """    'test_mini_grid.py',
]"""
TREE_NOW = """    'test_mini_grid.py',
    # PK-1, 19 Oct 2026 - the picker is a grid, and it filters by
    # course. Wide from birth: section 5 asks every page in both
    # roots whether any other one grew a copy of the filter strip.
    'test_picker_grid.py',
]"""

RD_WAS = """    '.bak_minigrid',
]"""
RD_NOW = """    '.bak_minigrid',
    # PK-1, 19 Oct 2026 - the Add-a-Meal picker becomes a grid with a
    # course filter. Demetri's finding, the same hour as MC-4 and from
    # the same root: .recipe-option has never had a CSS rule anywhere.
    '.bak_pickergrid',
]"""

WD_WAS = """CONVERTED_N = 111   # MC-4, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 112   # PK-1, 19 Oct 2026 - this round own suite   # (was 111)   # MC-4, 19 Oct 2026 - this round own suite"""


# ================================================== THE !important PIN
# test_important_base counts every !important declaration in
# every <style> in the tree and pins the total. This round
# DELETES one: the #pickerList max-height phone override.
#
# Split with MW-1 rather than moved once at the end, for the
# same reason as the footer pin - the gate runs on whatever is
# on disk, so a tree with only one of the two applied has to be
# green too.
IB = 'test_important_base.py'
IB_WAS = "IMP_TREE = 805   # MW-1, 19 Oct 2026 - one went with the dead phone rule .recipe-option > div { padding: 10px 12px !important }, written for a two-level nesting the row does not have and matching nothing since MN-1.   # (was 806)   # RT-1, 18 Oct 2026 - twenty went with the four meal-plan screens MN-1 retired, and the planner that replaced them declares none: measured, not deduced.   # (was 826)   # SB-1, 17 Oct 2026 - the hover that forced --alv-good-ink on the invoice icon. The icon is not green any more, so nothing needed forcing.   # (was 827)   # CC-2, 17 Oct 2026 - the one that forced .contact-details open inside an expanded card. Nothing expands now, so the rule had no element left.   # (was 828)   # DT-1, 16 Oct 2026 - fourteen went with the two table-as-cards blocks on home and notifications. Each was a copy of a declaration base already makes, with the same !important.   # (was 842)   # NV-1b, 16 Oct 2026 - thirteen of them went with the title deeds phone card block. Every one was a copy of a declaration base already makes, with the same !important, so nothing changed about what wins - there is simply one copy of each now. The page goes from 14 to 1.   # (was 855)   # PV-1, 15 Oct 2026 - three !important declarations went with the two hand-rolled viewers: an iframe height, an img max-height and a phone-only body height. The component sizes its own body.   # (was 858)   # PH-2, 14 Oct 2026 - the .bg-light line in base   # (was 857)   # MH-2, 13 Oct 2026 - suppliers' one"
IB_NOW = "IMP_TREE = 804   # PK-1, 19 Oct 2026 - and one more with #pickerList { max-height: none !important }. That override un-capped the list on a phone, which was right while the list was a column and wrong once it was a grid: thirty cards measured 2,572px.   # (was 805)   # MW-1, 19 Oct 2026 - one went with the dead phone rule .recipe-option > div { padding: 10px 12px !important }, written for a two-level nesting the row does not have and matching nothing since MN-1.   # (was 806)   # RT-1, 18 Oct 2026 - twenty went with the four meal-plan screens MN-1 retired, and the planner that replaced them declares none: measured, not deduced.   # (was 826)   # SB-1, 17 Oct 2026 - the hover that forced --alv-good-ink on the invoice icon. The icon is not green any more, so nothing needed forcing.   # (was 827)   # CC-2, 17 Oct 2026 - the one that forced .contact-details open inside an expanded card. Nothing expands now, so the rule had no element left.   # (was 828)   # DT-1, 16 Oct 2026 - fourteen went with the two table-as-cards blocks on home and notifications. Each was a copy of a declaration base already makes, with the same !important.   # (was 842)   # NV-1b, 16 Oct 2026 - thirteen of them went with the title deeds phone card block. Every one was a copy of a declaration base already makes, with the same !important, so nothing changed about what wins - there is simply one copy of each now. The page goes from 14 to 1.   # (was 855)   # PV-1, 15 Oct 2026 - three !important declarations went with the two hand-rolled viewers: an iframe height, an img max-height and a phone-only body height. The component sizes its own body.   # (was 858)   # PH-2, 14 Oct 2026 - the .bg-light line in base   # (was 857)   # MH-2, 13 Oct 2026 - suppliers' one"


# ==================================================== THE QUERY PIN
# test_planner pins the planner's query count. MW-1 took it to
# 13 for the Menus the Apply dialog lists; this round asks for
# one more thing, the courses the filter strip is built from.
#
# BOTH ARE ONE QUERY EACH, HOWEVER MUCH DATA THERE IS, and the
# check above this line is what proves it: the number does not
# move between one meal and eighty-four. A filter that read its
# courses per card would be the E29 fault, which is why this
# round prefetches them.
PL = 'test_planner.py'
PQ_WAS = "    ok(q_big <= 13, '  and that number is under 13', q_big)"
PQ_NOW = "    # PK-1, 19 Oct 2026 - fourteen. One more, for the courses the\n    # picker's filter strip is built from. One query, not one per\n    # course and not one per card.\n    ok(q_big <= 14, '  and that number is under 14', q_big)"


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
    raise SystemExit('PK-1 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    pt = os.path.join(root, TPL)
    v, t = read(pv), read(pt)
    t_before = t

    # ---------------------------------------------------------------- 0
    if 'function pickCourse(' in t:
        print('PK-1  already applied - the picker is a grid.')
        return 0

    # ---------------------------------------------------------------- 1
    # MW-1 MUST BE APPLIED. This round changes the LIST; the row inside
    # each card is MW-1's and this round anchors on it.
    if '.recipe-option {' not in t:
        refuse('%s has no .recipe-option rule. PK-1 turns the LIST into '
               'a grid and leaves MW-1\'s card alone; apply MW-1 first.'
               % TPL)
    if 'RecipeCourse' not in v:
        refuse('%s does not import RecipeCourse, which the filter strip '
               'is built from.' % VIEW)
    if 'courses = models.ManyToManyField' not in read(
            os.path.join(root, 'pages', 'models.py')):
        refuse('Recipe has no courses field, so there is nothing to '
               'filter by. This round writes no migration.')

    # ---------------------------------------------------------------- 2
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the planner context)' % VIEW)
    out[pv] = v

    t = swap(t, CSS_WAS, CSS_NOW, '%s (the grid)' % TPL)
    t = swap(t, MARGIN_WAS, MARGIN_NOW, '%s (the card margin)' % TPL)
    t = swap(t, LAST_WAS, LAST_NOW, '%s (the last-child rule)' % TPL)
    t = swap(t, PHONE_WAS, PHONE_NOW, '%s (the phone cap)' % TPL)
    t = swap(t, LIST_WAS, LIST_NOW, '%s (the filter strip)' % TPL)
    t = swap(t, CARD_WAS, CARD_NOW, '%s (the card courses)' % TPL)
    t = swap(t, EMPTY_WAS, EMPTY_NOW, '%s (the empty state)' % TPL)
    t = swap(t, JS_WAS, JS_NOW, '%s (the filter)' % TPL)
    t = swap(t, OPEN_WAS, OPEN_NOW, '%s (the reset on open)' % TPL)
    out[pt] = t

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    pr = os.path.join(root, TREE)
    out[pr] = swap(read(pr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    pib = os.path.join(root, IB)
    out[pib] = swap(read(pib), IB_WAS, IB_NOW,
                    '%s (the !important pin)' % IB)

    ppl = os.path.join(root, PL)
    out[ppl] = swap(read(ppl), PQ_WAS, PQ_NOW,
                    '%s (the query pin)' % PL)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    import alv_tree
    nt = out[pt]
    tcode = alv_tree.code_only_js(nt)

    # THE COMPONENT IS BASE'S. A page that wrote its own .alv-seg rules
    # would be the fault H8 spent a round removing from 31 pages, one
    # component along.
    if re.search(r'(?m)^\s*\.alv-seg\s*\{', alv_tree.code_only(nt)):
        refuse('%s writes its own .alv-seg rule. base owns that '
               'component; this round may only say that the strip wraps.'
               % TPL)

    # THE FILTER AND THE SEARCH COMPOSE. A filter that replaced the
    # search would be a dialog that forgets what you typed.
    # SPLIT ON A TOP-LEVEL DECLARATION, not on the word. The first cut
    # cut at `forEach(function (o)` - three lines into the body it was
    # trying to read - and refused the round for not containing what it
    # had just thrown away.
    body = re.split(r'\n(?=function )',
                    tcode.split('function filterPicker()')[-1])[0]
    for needed, why in (('byName', 'the typed text'),
                        ('byCourse', 'the chosen course'),
                        ('byName && byCourse', 'both together')):
        if needed not in body:
            refuse('%s: filterPicker does not read %s - the search and '
                   'the filter have to compose' % (TPL, why))

    # SPACE-PADDED ON BOTH SIDES, or course 1 matches course 11 and the
    # filter is wrong in a way nobody would see until a tree has eleven
    # courses in it.
    if "' ' + pickerCourse + ' '" not in body:
        refuse('%s: the course match is not padded on both sides, so '
               'course 1 would match course 11' % TPL)

    # THE COUNT, AND THE EMPTY STATE.
    for text, why in (('id="pickerCount"', 'the count'),
                      ('id="pickerEmpty"', 'the empty state')):
        if tcode.count(text) != 1:
            refuse('%s: %d of %s, expected 1'
                   % (TPL, tcode.count(text), why))

    # ONE QUERY. The cards print course ids; without the prefetch that
    # is a query per card.
    vcode = alv_tree.python_code_only(out[pv])
    if "prefetch_related('courses')" not in vcode:
        refuse('%s: all_recipes has no prefetch_related(\'courses\') and '
               'every card reads them - one query per recipe. [E29]'
               % VIEW)
    if "'all_courses':" not in vcode:
        refuse('%s: the context has no all_courses, so the filter strip '
               'would render with one button' % VIEW)

    # AND THE PHONE DOES NOT UN-CAP IT. The one that got away first
    # time: an !important that undid the cap this round had just added.
    if 'max-height: none !important' in alv_tree.code_only(nt):
        refuse('%s still un-caps #pickerList on a phone. A one-column '
               'grid of thirty cards is 2,572px, which puts Add Meal '
               'below the fold.' % TPL)
    if 'max-height: 50vh;' not in alv_tree.code_only(nt):
        refuse('%s: the phone block does not cap the list at all' % TPL)

    # THE GRID IS AUTO-FILL. A fixed column count is a number to
    # re-pin every time the dialog changes width.
    if 'repeat(auto-fill, minmax(240px, 1fr))' not in alv_tree.code_only(nt):
        refuse('%s: #pickerList is not an auto-fill grid' % TPL)

    # AND MW-1'S CARD IS UNTOUCHED. This round changes the LIST.
    for kept in ('.recipe-option.selected {',
                 'box-shadow: 0 0 0 2px var(--alv-accent-ring);',
                 'display: flex;'):
        if kept not in alv_tree.code_only(nt):
            refuse('%s: MW-1\'s card rule lost %r. This round turns the '
                   'list into a grid; the row inside a card is not its '
                   'business.' % (TPL, kept))

    o, c = nt.count('/*'), nt.count('*/')
    if o != c:
        refuse('%s: %d /* against %d */' % (TPL, o, c))
    for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
        if (nt.count(a) - t_before.count(a)
                != nt.count(b) - t_before.count(b)):
            refuse('%s: this round added %d %s and %d %s'
                   % (TPL, nt.count(a) - t_before.count(a), a,
                      nt.count(b) - t_before.count(b), b))
    if nt.count('<div') - t_before.count('<div') != \
            nt.count('</div>') - t_before.count('</div>'):
        refuse('%s: this round opens %d <div> and closes %d'
               % (TPL, nt.count('<div') - t_before.count('<div'),
                  nt.count('</div>') - t_before.count('</div>')))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('PK-1 --check')
        print('  the list    : one column -> auto-fill grid, 240px floor')
        print('  the filter  : base .alv-seg, one button per course')
        print('  files       : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('PK-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_picker_grid.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
