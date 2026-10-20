# -*- coding: utf-8 -*-
"""apply_recipe_modal.py - round RD-1, 19 Oct 2026.

RELEASE 4, PUSH 2. A RECIPE WITHOUT LEAVING THE CALENDAR.

Demetri, answering Q2 of the Release 4 questions: clicking a meal
should offer "to view the recipe (a detailed view of the recipe in a
modal) or to remove the recipe". This is the modal. RD-2 is the menu
that opens it; RD-3 puts it on the library's cards as well.

AND THE DECISIONS DOC WAS WRONG ABOUT THE COST. It recorded that "no
recipe modal exists anywhere in the application" and priced one at two
hours. `wcim_recipe_quick_view` has returned a recipe partial into a
Bootstrap dialog since What Can I Make? shipped. This round generalises
that shape rather than inventing a second one - and WCIM keeps its own
partial, because its ingredient list says have / substitute / missing,
which is a different thing said about the same rows.

THE READ IS EXTRACTED, NOT COPIED - AND THERE WERE THREE COPIES.

This round was written believing there were two. Its own suite counted
them, in the control section, and found a third:

  recipe_book_detail  asks get_preferred_weight_conversion - THE
                      AUTHORITY. Right answer, one query per ingredient.
  view_recipe         builds a bulk map. One query, wrong answer.
  recipe_pdf          builds its own bulk map. One query, wrong answer.

So the fast path and the correct path were both already in this file,
in different functions, and nothing reconciled them. The extracted
module is the first one that is both, and the modal would have been a
fourth.

THE SUITE FOUND IT, NOT THE SURVEY. The survey read the two functions
it had been told about; the control section asked the file how many
copies of `weight_amount = round(amount` it held and was answered 3.
Asking the tree beats reading the part of it you went looking in.

The three are now one module, `_recipe_read.py`, whose docstring
records the faults that asking the question properly turned up. Two of
them are fixed here, because a round that must choose ONE answer for
four screens has to choose the right one:

  * a conversion to a NON-WEIGHT unit could win and be presented as a
    weight. Two onions at 50ml each read `100ml` as a weight
    equivalent.
  * where a unit has more than one weight conversion - legal, because
    unique_together is (from_unit, to_unit, specific_ingredient) - the
    winner was whichever row the database handed back first. Ten cups
    of flour read `1.2kg` on the page while the rest of the package,
    asked properly, says `1200g`.

The third is the arithmetic, `round(amount * multiplier, 1)`, which is
one decimal place OF THE TARGET UNIT and so rounds kilograms to the
nearest 100g. **That one is RW-1**, deliberately a round of its own
and in this same push, because it changes numbers on a screen rather
than choosing between two the application already held.

Idempotent. Every file backed up to .bak_recipemodal.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_recipemodal'
READ = os.path.join('pages', 'views', 'recipes', '_recipe_read.py')
CRUD = os.path.join('pages', 'views', 'recipes', 'recipe_crud.py')
URLS = os.path.join('pages', 'urls.py')
# THE NAME OF A FILE AND THE CONTENTS OF A FILE ARE DIFFERENT THINGS,
# and this round proved it the hard way: SHELL was the path here and the
# template text four hundred lines down, so the second definition won and
# the applier tried to write a file whose NAME was five kilobytes of HTML.
# The paths end in P; the texts do not. And the gate at the foot of main()
# now asks whether every template this round RENDERS is one it WRITES.
PARTP = os.path.join('pages', 'templates', 'recipe_quicklook.html')
SHELLP = os.path.join('pages', 'templates', 'recipe_quicklook_shell.html')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_recipe_modal.py'
PATCHER = 'apply_recipe_modal.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
STAGE = 'stage_round.py'
MARK = 'RD-1, 19 Oct 2026'
CHECK = False

# WHAT THIS ROUND CREATES, declared here because nothing else can know.
#
# stage_round.py enumerates a round's files FROM ITS BACKUPS, and a file
# that did not exist has no backup - so the three files below were
# invisible to it. PF-2 shipped _recipe_filter.py on 19 Oct only because
# its name happened to get typed on the staging command line, which is
# precisely the hand-written list the 17 October push failed on.
#
# Worse than the staging: revert_all.sh restores from backups too, so
# reverting this round would have LEFT these three files in the tree -
# a module nothing imports and two templates nothing renders.
#
# So the round says so, in the round, and stage_round.py asks the
# patcher instead of asking whoever typed the command.
CREATES = (READ, PARTP, SHELLP)


# ======================================================= THE SHARED READ
# Written as a repr because the module has its own docstring. The
# suite asks this constant and the file on disk the same questions,
# so the two cannot drift.
MODULE = '"""Reading a recipe whole - the one read behind every screen that shows one.\n\nRD-1, 19 Oct 2026. This is an EXTRACTION, not a new idea: it is the\nblock `view_recipe` and `recipe_pdf` were each already carrying, and the\nrecipe modal would have been the third copy of it.\n\nTHERE WERE THREE COPIES, AND ONLY ONE OF THEM WAS RIGHT.\n\n  recipe_book_detail  asked get_preferred_weight_conversion - the\n                      authority. Correct, and one query per ingredient.\n  view_recipe         built a bulk map. One query, and it could choose\n                      a conversion the authority would never have.\n  recipe_pdf          built its own bulk map, differing from\n                      view_recipe\'s in three places under a comment\n                      claiming to mirror it.\n\nSo the fast path and the correct path were both already in that file,\nin different functions, and nothing reconciled them. This module is\nthe first one that is both. Both build a bulk map of unit conversions - one query\ninstead of one per ingredient, which is what the comment above the\noriginal was written for - and then both take whichever row the database\nhappened to hand back first:\n\n    conversion_map.setdefault((conv.from_unit_id,\n                               conv.specific_ingredient_id), conv)\n\n`unit_conversions` is unique on (from_unit, to_unit, specific_ingredient),\nso one `(from_unit, ingredient)` pair can legitimately hold SEVERAL rows -\none per target unit. A cup of flour may be recorded as 120g and again as\n0.12kg, both true. Which one is read decides what the screen says, and\nfor ten cups the two answers are `1200g` and `1.2kg`.\n\n`view_recipe` ordered that query and `recipe_pdf` did not, which looks\nlike the fix and is not one: the ordering is\n\n    .order_by(\'specific_ingredient\', \'from_unit\')\n\nand those are the two columns the rival rows SHARE. It groups them and\nleaves the tie exactly as undecided as before.\n\nTHE APPLICATION ALREADY HAD THE ANSWER. `_helpers.\nget_preferred_weight_conversion` resolves the same question properly -\ningredient-specific before generic, then `WEIGHT_UNIT_PRIORITY`, which is\n`[\'g\', \'kg\', \'oz\', \'lb\']` - and it is what the rest of the recipes\npackage asks. It is simply one query per unit per ingredient, which is\nthe N+1 the bulk map exists to avoid.\n\nSo this module keeps the one query AND the helper\'s answer: it ranks the\nrows it fetched by the same priority and takes the best. The page, the\nPDF and the modal now say the same thing, and it is the thing the rest of\nthe application would have said.\n\nTWO MORE FAULTS FALL OUT OF ASKING THE HELPER WHAT IT DOES.\n\n  * The old bulk query did not constrain `to_unit`, so a conversion to a\n    non-weight unit could be fetched and its product then presented as a\n    `weight_equivalent`. The helper filters `to_unit__unit_type=\'weight\'`.\n    So does this.\n  * A conversion to a weight unit outside the priority list could win\n    over one inside it. The helper can never reach such a row, because it\n    only ever asks for those four abbreviations. Neither can this.\n\nRead-only. Nothing here writes.\n"""\nfrom ._helpers import WEIGHT_UNIT_PRIORITY, format_quantity\n\nfrom pages.models import RecipeIngredient, RecipeInstruction, UnitConversion\n\n\n# The helper tries the abbreviations in this order and returns the first\n# hit, so its position in the list IS its rank. Built once, from the same\n# constant, so the two can never drift apart.\nWEIGHT_RANK = {abbr: i for i, abbr in enumerate(WEIGHT_UNIT_PRIORITY)}\n\n\ndef _units_needing_weight(ingredients):\n    """The units whose amounts could be shown as a weight.\n\n    A weight unit needs no equivalent - it already is one - and an\n    ingredient with no amount has nothing to convert.\n    """\n    needed = set()\n    for ing in ingredients:\n        if ing.unit and ing.unit.unit_type != \'weight\' and ing.amount:\n            needed.add(ing.unit_id)\n    return needed\n\n\ndef weight_conversions(unit_ids):\n    """One query, and the same answer get_preferred_weight_conversion gives.\n\n    Returns {(from_unit_id, ingredient_id or None): UnitConversion},\n    holding the BEST row for each key rather than the first one back.\n    """\n    if not unit_ids:\n        # NOT A QUERY WITH AN EMPTY `__in`. `view_recipe` issued one of\n        # those on every recipe whose ingredients were all weights -\n        # a round trip to be told nothing. `recipe_pdf` guarded it.\n        return {}\n\n    rows = UnitConversion.objects.filter(\n        from_unit_id__in=unit_ids,\n        to_unit__unit_type=\'weight\',\n    ).select_related(\'to_unit\', \'specific_ingredient\')\n\n    best = {}\n    for conv in rows:\n        rank = WEIGHT_RANK.get(conv.to_unit.abbreviation)\n        if rank is None:\n            # A weight unit the helper would never ask for. It cannot\n            # win here either.\n            continue\n        key = (conv.from_unit_id, conv.specific_ingredient_id)\n        held = best.get(key)\n        if held is None or rank < held[0]:\n            best[key] = (rank, conv)\n    return {k: v[1] for k, v in best.items()}\n\n\ndef weight_equivalent(ing, conversions):\n    """What this much of this ingredient weighs, as a string, or None.\n\n    The arithmetic and the kilogram rule are the original\'s, unchanged.\n    """\n    if not ing.unit or ing.unit.unit_type == \'weight\':\n        return None\n    try:\n        amount = float(ing.amount) if ing.amount else 0\n    except (TypeError, ValueError):\n        return None\n    if amount <= 0:\n        return None\n\n    # SPECIFIC BEFORE GENERIC, which is the helper\'s order too.\n    conversion = (conversions.get((ing.unit_id, ing.ingredient_id)) or\n                  conversions.get((ing.unit_id, None)))\n    if not conversion:\n        return None\n\n    try:\n        weight_amount = round(amount * float(conversion.multiplier), 1)\n    except (TypeError, ValueError):\n        return None\n    if weight_amount == int(weight_amount):\n        weight_amount = int(weight_amount)\n    if weight_amount <= 0:\n        return None\n\n    weight_unit = (conversion.to_unit.abbreviation or\n                   conversion.to_unit.name)\n    # UNDER A KILO IS GRAMS. Nobody writes 0.4kg of flour.\n    if weight_unit == \'kg\' and weight_amount < 1:\n        weight_amount = round(weight_amount * 1000)\n        weight_unit = \'g\'\n    return \'%s%s\' % (weight_amount, weight_unit)\n\n\ndef ingredient_rows(recipe):\n    """This recipe\'s ingredients, in order, each decorated for display.\n\n    Two queries: the ingredients, and the conversions they need.\n    """\n    ingredients = list(\n        RecipeIngredient.objects.filter(recipe=recipe).select_related(\n            \'ingredient\',\n            \'ingredient__category\',\n            \'unit\',\n            \'preparation\',\n        ).order_by(\'ingredient_group\', \'ingredient_order\')\n    )\n    conversions = weight_conversions(_units_needing_weight(ingredients))\n    for ing in ingredients:\n        ing.formatted_amount = format_quantity(ing.amount)\n        ing.weight_equivalent = weight_equivalent(ing, conversions)\n    return ingredients\n\n\ndef instruction_rows(recipe):\n    """The method, in step order."""\n    return RecipeInstruction.objects.filter(\n        recipe=recipe).order_by(\'step_number\')\n'


# ============================================================ recipe_crud
IMP_WAS = """from pages.views.recipes._recipe_filter import (
    filter_recipes,
    selected_from,
)
"""
IMP_NOW = """from pages.views.recipes._recipe_filter import (
    filter_recipes,
    selected_from,
)
# RD-1, 19 Oct 2026 - the shared read. One description of what a whole
# recipe is, asked by the page, by the PDF, by the book detail and by
# the quick-look dialog. Those four held THREE copies of it between
# them - see _recipe_read's docstring for which one was right.
from pages.views.recipes._recipe_read import (
    ingredient_rows,
    instruction_rows,
    weight_conversions,
    weight_equivalent,
)
"""

# The seventy lines view_recipe carried. Replaced by two calls.
VR_WAS = """    # Get ingredients with all related data in a single query
    ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related(
        'ingredient',
        'ingredient__category',
        'unit',
        'preparation',
    ).order_by('ingredient_group', 'ingredient_order')

    # Pre-fetch all unit conversions needed for weight equivalents in bulk
    # to avoid one DB hit per ingredient inside the loop
    units_needed = set()
    for ing in ingredients:
        if ing.unit and ing.unit.unit_type != 'weight' and ing.amount:
            units_needed.add(ing.unit_id)

    # Bulk fetch all relevant conversions once
    conversions_qs = UnitConversion.objects.filter(
        from_unit_id__in=units_needed
    ).select_related('from_unit', 'to_unit', 'specific_ingredient').order_by('specific_ingredient', 'from_unit')

    # Build a lookup dict: (from_unit_id, specific_ingredient_id) -> conversion
    #                   and (from_unit_id, None) -> conversion as fallback
    conversion_map = {}
    for conv in conversions_qs:
        key_specific = (conv.from_unit_id, conv.specific_ingredient_id)
        key_generic  = (conv.from_unit_id, None)
        if key_specific not in conversion_map:
            conversion_map[key_specific] = conv
        if conv.specific_ingredient_id is None and key_generic not in conversion_map:
            conversion_map[key_generic] = conv

    # Format amounts and compute weight equivalents from the in-memory map
    for ing in ingredients:
        ing.formatted_amount = format_quantity(ing.amount)
        ing.weight_equivalent = None
        if ing.unit and ing.unit.unit_type != 'weight':
            try:
                amount = float(ing.amount) if ing.amount else 0
                if amount > 0:
                    # Look up specific ingredient first, then generic fallback
                    conversion = (
                        conversion_map.get((ing.unit_id, ing.ingredient_id)) or
                        conversion_map.get((ing.unit_id, None))
                    )
                    if conversion:
                        weight_amount = round(amount * float(conversion.multiplier), 1)
                        if weight_amount == int(weight_amount):
                            weight_amount = int(weight_amount)
                        if weight_amount > 0:
                            weight_unit = conversion.to_unit.abbreviation or conversion.to_unit.name
                            if weight_unit == 'kg' and weight_amount < 1:
                                weight_amount = round(weight_amount * 1000)
                                weight_unit = 'g'
                            ing.weight_equivalent = f"{weight_amount}{weight_unit}"
            except Exception:
                pass

    # Get instructions
    instructions = RecipeInstruction.objects.filter(recipe=recipe).order_by('step_number')"""
VR_NOW = """    # ONE READ, SHARED - RD-1, 19 Oct 2026. Seventy lines stood here
    # and fifty-one more of the same stood in recipe_pdf, and the
    # quick-look dialog would have been the third copy. _recipe_read
    # holds it now, and it resolves a weight the way the rest of this
    # package does rather than the way the database happened to.
    ingredients = ingredient_rows(recipe)
    instructions = instruction_rows(recipe)"""

# And the fifty-one recipe_pdf carried.
PDF_WAS = """    # Ingredients with formatted amounts + weight equivalents (mirrors view_recipe)
    ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related(
        'ingredient', 'ingredient__category', 'unit', 'preparation',
    ).order_by('ingredient_group', 'ingredient_order')

    units_needed = set()
    for ing in ingredients:
        if ing.unit and ing.unit.unit_type != 'weight' and ing.amount:
            units_needed.add(ing.unit_id)

    conversion_map = {}
    if units_needed:
        conversions_qs = UnitConversion.objects.filter(
            from_unit_id__in=units_needed
        ).select_related('from_unit', 'to_unit', 'specific_ingredient')
        for conv in conversions_qs:
            conversion_map.setdefault((conv.from_unit_id, conv.specific_ingredient_id), conv)
            if conv.specific_ingredient_id is None:
                conversion_map.setdefault((conv.from_unit_id, None), conv)

    for ing in ingredients:
        ing.formatted_amount = format_quantity(ing.amount)
        ing.weight_equivalent = None
        if ing.unit and ing.unit.unit_type != 'weight':
            try:
                amount = float(ing.amount) if ing.amount else 0
                if amount > 0:
                    conversion = (
                        conversion_map.get((ing.unit_id, ing.ingredient_id)) or
                        conversion_map.get((ing.unit_id, None))
                    )
                    if conversion:
                        weight_amount = round(amount * float(conversion.multiplier), 1)
                        if weight_amount == int(weight_amount):
                            weight_amount = int(weight_amount)
                        if weight_amount > 0:
                            weight_unit = conversion.to_unit.abbreviation or conversion.to_unit.name
                            if weight_unit == 'kg' and weight_amount < 1:
                                weight_amount = round(weight_amount * 1000)
                                weight_unit = 'g'
                            ing.weight_equivalent = f"{weight_amount}{weight_unit}"
            except Exception:
                pass

    instructions = RecipeInstruction.objects.filter(recipe=recipe).order_by('step_number')"""
PDF_NOW = """    # THE SAME READ THE PAGE USES - RD-1, 19 Oct 2026. This had its
    # own copy, and the comment above it claimed to mirror view_recipe
    # while differing from it in three places. A mirror nobody checks
    # is a second implementation.
    ingredients = ingredient_rows(recipe)
    instructions = instruction_rows(recipe)"""


# ================================================== THE NEW ENDPOINT
DOC_WAS = """- view_recipe            : Recipe detail page. Read-tier."""
DOC_NOW = """- view_recipe            : Recipe detail page. Read-tier.
- recipe_quicklook       : The same recipe as an HTML partial, for the
                           quick-look dialog. Read-tier.
- recipe_pdf             : A shareable PDF of one recipe. Read-tier."""

END_WAS = """# ============================================
# VIEW: Create Recipe
# ============================================"""
END_NOW = """# ============================================
# VIEW: Recipe quick-look - the partial behind the dialog
# ============================================

@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def recipe_quicklook(request, recipe_id):
    \"\"\"One recipe as an HTML partial, for the quick-look dialog.

    RD-1, 19 Oct 2026. Demetri, on clicking a meal in the calendar:
    he wanted "a detailed view of the recipe in a modal" rather than
    losing the calendar to a page load.

    SAME SHAPE AS wcim_recipe_quick_view, which has returned a recipe
    partial into a dialog since What Can I Make? shipped - a GET, a
    partial, no layout. WCIM keeps its own template because its
    ingredient list says have / substitute / missing, which is a
    different thing said about the same rows.

    READ-TIER, matching view_recipe and recipe_pdf. A dialog that
    showed a recipe to somebody who may not open its page would be a
    way round the permission rather than a convenience.
    \"\"\"
    recipe = get_object_or_404(
        Recipe.objects.prefetch_related('courses', 'categories', 'proteins'),
        recipe_id=recipe_id,
    )
    return render(request, 'recipe_quicklook.html', {
        'recipe': recipe,
        'ingredients': ingredient_rows(recipe),
        'instructions': instruction_rows(recipe),
    })


# ============================================
# VIEW: Create Recipe
# ============================================"""


# ===================================================================== urls
URL_WAS = """    path('recipe/<int:recipe_id>/pdf/', views.recipe_pdf, name='recipe_pdf'),"""
URL_NOW = """    path('recipe/<int:recipe_id>/pdf/', views.recipe_pdf, name='recipe_pdf'),
    # RD-1, 19 Oct 2026 - the quick-look partial. Beside view_recipe
    # and the PDF, because it is the same recipe in a third shape.
    path('recipe/<int:recipe_id>/quick-look/', views.recipe_quicklook,
         name='recipe_quicklook'),"""


# ================================================= THE PARTIAL AND THE SHELL
#
# TWO FILES, AND THE SPLIT IS NOT ARBITRARY. The shell is included ONCE
# per page and holds the dialog, its stylesheet and its one handler. The
# partial is what the endpoint returns, so it is fetched on every open
# and holds nothing but the recipe. WCIM's quick view put a stylesheet
# in the fetched half, which means re-sending it every time a recipe is
# looked at.
PARTIAL = """{# recipe_quicklook.html - RD-1, 19 Oct 2026.                      #}
{#                                                                 #}
{# The whole recipe, read-only, as a partial for the quick-look     #}
{# dialog. Demetri asked for "a detailed view of the recipe in a    #}
{# modal" so that clicking a meal in the calendar does not cost him #}
{# the calendar.                                                    #}
{#                                                                  #}
{# NO STYLESHEET HERE. This arrives on every open; the rules live in #}
{# recipe_quicklook_shell.html, which arrives once.                  #}
{#                                                                  #}
{# NO INLINE STYLE AND NO LITERAL COLOUR. Every colour is a token,   #}
{# because a hex here is a hex the standards suites cannot reason    #}
{# about and the dark ground would keep.                             #}
<div class="modal-header alv-modal-head">
    <h5 class="modal-title" id="quickLookTitle">
        <i class="fas fa-utensils"></i> {{ recipe.recipe_name }}
    </h5>
    <button type="button" class="close" data-dismiss="modal"
            aria-label="Close">
        <span aria-hidden="true">&times;</span>
    </button>
</div>
<div class="modal-body ql-body">
    {# NOT LAZY - RD-1, 19 Oct 2026. This is the ONE picture in the   #}
    {# dialog and the thing you opened it to see; it was written with  #}
    {# loading="lazy" out of habit and test_lazy_images refused it.    #}
    {# Its rule is that a lazy image is one of a LIST - a card in a    #}
    {# loop, below the fold - and a hero that waits is a hero you are  #}
    {# looking at a gap where.                                         #}
    {% if recipe.recipe_image %}
    <img decoding="async" src="{{ recipe.photo_url }}"
         alt="" class="ql-photo">
    {% endif %}

    {# WHAT IT COSTS YOU AND WHAT IT FEEDS, on one line. These are the #}
    {# four facts somebody deciding whether to cook it needs.          #}
    <div class="ql-facts">
        {% if recipe.servings %}
        <span class="ql-fact"><i class="fas fa-users"></i>
            Serves {{ recipe.servings }}</span>
        {% endif %}
        {% if recipe.prep_time %}
        <span class="ql-fact"><i class="far fa-clock"></i>
            {{ recipe.prep_time }} min prep</span>
        {% endif %}
        {% if recipe.cook_time %}
        <span class="ql-fact"><i class="fas fa-fire"></i>
            {{ recipe.cook_time }} min cook</span>
        {% endif %}
        {% if recipe.author %}
        <span class="ql-fact"><i class="fas fa-user-edit"></i>
            {{ recipe.author }}</span>
        {% endif %}
    </div>

    {% if recipe.courses.all or recipe.categories.all or recipe.is_vegetarian %}
    <div class="ql-tags">
        {% for c in recipe.courses.all %}
        <span class="ql-tag">{{ c.name }}</span>
        {% endfor %}
        {% for c in recipe.categories.all %}
        <span class="ql-tag">{{ c.name }}</span>
        {% endfor %}
        {% if recipe.is_vegetarian %}
        <span class="ql-tag ql-tag-veg">Vegetarian</span>
        {% endif %}
    </div>
    {% endif %}

    {% if recipe.recipe_description %}
    <p class="ql-desc">{{ recipe.recipe_description }}</p>
    {% endif %}

    <h6 class="ql-head"><i class="fas fa-list-ul"></i> Ingredients</h6>
    {% regroup ingredients by ingredient_group as ingredient_groups %}
    {% for group in ingredient_groups %}
    {% if group.grouper %}<p class="ql-group">{{ group.grouper }}</p>{% endif %}
    <ul class="ql-ings">
        {% for ing in group.list %}
        <li class="ql-ing">
            <span class="ql-amount">{% if ing.formatted_amount %}{{ ing.formatted_amount }}{% endif %}{% if ing.unit %} {{ ing.unit.abbreviation|default:ing.unit.name }}{% endif %}</span>
            <span class="ql-name">{{ ing.ingredient.name }}{% if ing.preparation %}, {{ ing.preparation.name }}{% endif %}{% if ing.weight_equivalent %} <span class="ql-weight">({{ ing.weight_equivalent }})</span>{% endif %}</span>
        </li>
        {% endfor %}
    </ul>
    {% empty %}
    <p class="ql-none">No ingredients recorded for this recipe.</p>
    {% endfor %}

    <h6 class="ql-head"><i class="fas fa-tasks"></i> Method</h6>
    {% regroup instructions by instruction_group as instruction_groups %}
    {% for group in instruction_groups %}
    {% if group.grouper %}<p class="ql-group">{{ group.grouper }}</p>{% endif %}
    <ol class="ql-steps">
        {% for step in group.list %}
        <li class="ql-step">{{ step.instruction_text }}</li>
        {% endfor %}
    </ol>
    {% empty %}
    <p class="ql-none">No method recorded for this recipe.</p>
    {% endfor %}
</div>
<div class="modal-footer">
    {# THE WAY OUT TO THE WHOLE PAGE. The dialog is a look, not a    #}
    {# replacement: scaling, nutrition, the shopping list and every  #}
    {# edit control live on view_recipe and stay there.              #}
    {# HOUSE TONES, NOT BOOTSTRAP'S - RS-1a took all 35 Bootstrap-  #}
    {# toned buttons off the recipe side and this round put two      #}
    {# back. test_recipe_tones counted 37 and refused it.            #}
    {#                                                               #}
    {# AND PRIMARY, BECAUSE wcim_recipe_quick_view's IS. That dialog #}
    {# is the one this round was modelled on, and its footer already #}
    {# carries an Open full recipe as a solid primary link -         #}
    {# test_recipe_side_b pins exactly those. Going to the recipe IS #}
    {# the forward action here; Close is the quiet one.              #}
    <a href="{% url 'view_recipe' recipe.recipe_id %}"
       class="btn action-primary">Open full recipe</a>
    <button type="button" class="btn action-secondary"
            data-dismiss="modal">Close</button>
</div>
"""


SHELL = """{# recipe_quicklook_shell.html - RD-1, 19 Oct 2026.                #}
{#                                                                 #}
{# The dialog, its rules and its one handler. INCLUDED ONCE per    #}
{# page; recipe_quicklook.html is what arrives inside it on each   #}
{# open and carries no rules of its own.                            #}
{#                                                                  #}
{# A TRIGGER IS A LINK THAT STILL WORKS. Anything carrying           #}
{# data-quicklook opens the dialog, and its href is left pointing at #}
{# view_recipe - so with JavaScript off, with the fetch failing, or  #}
{# on a middle-click, the recipe page is still what you get. The URL #}
{# is rendered by the server onto each trigger, which is why there   #}
{# is no path spelled out in the JavaScript below. WCIM's quick view #}
{# built '/recipes/wcim/recipe/' + id + '/quick-view/' by hand, and  #}
{# a route that moves takes that with it silently.                   #}
<div class="modal fade" id="quickLookModal" tabindex="-1" role="dialog"
     aria-labelledby="quickLookTitle" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content" id="quickLookContent"></div>
    </div>
</div>

<style>
/* THE QUICK-LOOK - RD-1, 19 Oct 2026. base owns .modal-overlay,
   .modal-content and .alv-modal-head; these are the rules for what
   goes INSIDE one, and there is no colour here that is not a token. */
.ql-photo {
    width: 100%;
    max-height: 260px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 14px;
}
.ql-facts {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 18px;
    margin-bottom: 12px;
}
.ql-fact {
    font-size: 13px;
    color: var(--alv-ink-soft);
}
/* A WORD SOMEBODY READS GETS ink-soft; a mark may stay faint. The
   icon beside each fact is a mark, the fact is a word. */
.ql-fact i { color: var(--alv-ink-faint); margin-right: 4px; }
.ql-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.ql-tag {
    font-size: 12px;
    padding: 3px 9px;
    border-radius: 11px;
    background: var(--alv-surface);
    border: 1px solid var(--alv-line);
    color: var(--alv-ink-soft);
}
.ql-tag-veg {
    background: var(--alv-good-soft);
    border-color: var(--alv-good-line);
    color: var(--alv-good-ink);
}
.ql-desc { color: var(--alv-ink-soft); font-size: 14px; }
.ql-head {
    margin: 20px 0 8px;
    color: var(--alv-ink);
    font-size: 15px;
    font-weight: 600;
}
.ql-head i { color: var(--alv-ink-faint); margin-right: 6px; }
.ql-group {
    margin: 12px 0 4px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--alv-ink-strong);
}
.ql-ings { list-style: none; padding: 0; margin: 0; }
.ql-ing {
    display: flex;
    gap: 10px;
    padding: 5px 0;
    border-bottom: 1px solid var(--alv-line-soft);
    font-size: 14px;
}
.ql-ing:last-child { border-bottom: none; }
/* THE AMOUNTS LINE UP, which is what a column of numbers is for. */
.ql-amount {
    flex: 0 0 88px;
    text-align: right;
    font-variant-numeric: tabular-nums;
    color: var(--alv-ink);
    font-weight: 600;
}
.ql-name { color: var(--alv-ink); }
.ql-weight { color: var(--alv-ink-soft); font-size: 13px; }
.ql-steps { padding-left: 22px; margin: 0; }
.ql-step {
    padding: 4px 0;
    font-size: 14px;
    color: var(--alv-ink);
    line-height: 1.5;
}
.ql-none { color: var(--alv-ink-soft); font-size: 14px; font-style: italic; }

/* AND screen, NOT a bare max-width. A clause naming no media type
   matches print too - the 21 Sep print-leak round, which test_print_queries
   has enforced ever since. */
@media screen and (max-width: 767px) {
    .ql-photo { max-height: 180px; }
    .ql-amount { flex: 0 0 68px; }
    /* 44px, because a footer button on a phone is a thumb target. */
    #quickLookModal .modal-footer .btn { min-height: 44px; }
}
</style>

<script>
(function () {
    // ONE DELEGATED HANDLER, because the triggers are rendered inside
    // loops and some of them arrive after this runs - the picker's
    // grid and the month's chips are both built or replaced later.
    document.addEventListener('click', function (e) {
        var trigger = e.target.closest('[data-quicklook]');
        if (!trigger) { return; }

        // A MODIFIED CLICK IS A REQUEST FOR A TAB. Swallowing it would
        // take away something the plain link could already do.
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) { return; }

        var url = trigger.getAttribute('data-quicklook');
        if (!url) { return; }
        e.preventDefault();

        var box = document.getElementById('quickLookContent');
        box.innerHTML = '<div class="modal-body text-center ql-none">' +
            '<i class="fas fa-spinner fa-spin fa-2x"></i></div>';
        $('#quickLookModal').modal('show');

        fetch(url, {credentials: 'same-origin'})
            .then(function (r) {
                if (!r.ok) { throw new Error(r.status); }
                return r.text();
            })
            .then(function (html) { box.innerHTML = html; })
            .catch(function () {
                // THE FALLBACK IS THE PAGE THE LINK ALREADY POINTED AT.
                // A dialog that cannot load a recipe should hand you
                // the recipe, not an apology.
                box.innerHTML =
                    '<div class="modal-body ql-none">Could not load ' +
                    'the recipe. <a href="' + trigger.getAttribute('href') +
                    '">Open the full recipe page</a> instead.</div>';
            });
    });
})();
</script>
"""


# ================================================= THE PLANNER'S OWN WIRING
#
# TWO ROWS, NOT ONE. The eye appears twice in this template - once on a
# leftover row and once on a recipe row - and both want the same change,
# so this is asked with a count of exactly 2. A third would refuse, and
# should: it would be a row somebody added without a dialog.
EYE_WAS = """                                    <a href="{% url 'view_recipe' entry.recipe.recipe_id %}"
                                       class="icon-action-btn icon-view" title="View recipe"
                                       aria-label="View the recipe {{ entry.recipe.recipe_name }}"><i class="fas fa-eye"></i></a>"""
EYE_NOW = """                                    {# THE EYE OPENS A DIALOG - RD-1, 19 Oct 2026, and #}
                                    {# IT IS STILL A LINK. The href stays pointing at  #}
                                    {# view_recipe, so with JavaScript off, on a        #}
                                    {# middle-click, or when the fetch fails, the page  #}
                                    {# is what you get.                                #}
                                    <a href="{% url 'view_recipe' entry.recipe.recipe_id %}"
                                       data-quicklook="{% url 'recipe_quicklook' entry.recipe.recipe_id %}"
                                       class="icon-action-btn icon-view" title="View recipe"
                                       aria-label="View the recipe {{ entry.recipe.recipe_name }}"><i class="fas fa-eye"></i></a>"""

INC_WAS = """<form method="POST" action="{% url 'remove_meal_entry' %}" id="removeForm" hidden>"""
INC_NOW = """{# THE QUICK-LOOK DIALOG - RD-1, 19 Oct 2026. One include,   #}
{# and every trigger on the page carrying data-quicklook opens #}
{# it. RD-3 includes the same file on the library's cards.     #}
{#                                                             #}
{# ONE COMMENT PER LINE, which is a house rule with a suite     #}
{# behind it. This was first written as one comment across     #}
{# three lines and test_crs_comment_fix refused it: a comment  #}
{# that outlives its line swallows whatever follows if its     #}
{# closer is ever edited away.                                 #}
{% include 'recipe_quicklook_shell.html' %}

<form method="POST" action="{% url 'remove_meal_entry' %}" id="removeForm" hidden>"""


# ===================================================== THE REGISTRATIONS
SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE DAY HAS ITS OWN NAV'; What = 'MV-4: and the Day view moves by days, because week arrows above one Tuesday move you seven' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE DAY HAS ITS OWN NAV'; What = 'MV-4: and the Day view moves by days, because week arrows above one Tuesday move you seven' },
    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'def ingredient_rows('; What = 'RD-1: ONE read of a whole recipe, asked by the page, the PDF and the dialog - they held two copies of it and the two disagreed' },
    @{ File = 'pages/views/recipes/recipe_crud.py'; Text = 'def recipe_quicklook('; What = 'RD-1: the recipe as a partial, so clicking a meal in the calendar does not cost you the calendar' },
    @{ File = 'pages/templates/recipe_quicklook_shell.html'; Text = 'data-quicklook'; What = 'RD-1: a trigger is a link that still works - the href stays pointing at view_recipe for JavaScript-off and middle-click' },"""

SUITE_WAS = """    'test_day_view.py'
)"""
SUITE_NOW = """    'test_day_view.py',
    # RD-1, 19 Oct 2026 - the recipe modal, and the one read behind
    # it. Section 3 asks a real database whether the extracted read
    # gives the same answer as get_preferred_weight_conversion, which
    # is the authority the rest of the package already asks, on every
    # ingredient of every recipe it builds.
    'test_recipe_modal.py'
)"""

TREE_WAS = """    # MV-4, 19 Oct 2026 - one day card instead of seven, and the Day
    # view's own nav. Section 3 renders all three views and counts.
    'test_day_view.py',
]"""
TREE_NOW = """    # MV-4, 19 Oct 2026 - one day card instead of seven, and the Day
    # view's own nav. Section 3 renders all three views and counts.
    'test_day_view.py',
    # RD-1, 19 Oct 2026 - the recipe modal and the shared read behind
    # it. Section 3 replays the block it replaced beside the helper
    # the rest of the package asks, over every ingredient.
    'test_recipe_modal.py',
]"""

RD_WAS = """    '.bak_dayview',
]"""
RD_NOW = """    '.bak_dayview',
    # RD-1, 19 Oct 2026 - a recipe without leaving the calendar, and
    # the extraction that had to happen first: view_recipe and
    # recipe_pdf each carried their own copy of the read, and the two
    # did not agree about which weight conversion wins.
    '.bak_recipemodal',
]"""

WD_WAS = """CONVERTED_N = 118   # MV-4, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 119   # RD-1, 19 Oct 2026 - this round own suite   # (was 118)"""


# ================================================ THE THIRD COPY
#
# recipe_book_detail's nested get_weight_equivalent is the one that was
# already RIGHT: it asks get_preferred_weight_conversion. It is also one
# query per ingredient, which is why nobody copied it into the page. The
# extracted module keeps its answer at the bulk map's cost, so this call
# site loses nothing and gains the query count.
BOOK_WAS = """    ingredients = recipe.recipe_ingredients.select_related(
        'ingredient', 'unit', 'preparation'
    ).order_by('ingredient_group', 'ingredient_order')
    instructions = recipe.instructions.all().order_by('step_number')

    def get_weight_equivalent(ing):
        \"\"\"Return weight equivalent string or None\"\"\"
        if not ing.unit:
            return None
        if ing.unit.unit_type == 'weight':
            return None
        try:
            amount = float(ing.amount) if ing.amount else 0
            if amount <= 0:
                return None
            conversion = get_preferred_weight_conversion(ing.unit, ing.ingredient)
            if not conversion:
                return None
            weight_amount = round(amount * float(conversion.multiplier), 1)
            if weight_amount == int(weight_amount):
                weight_amount = int(weight_amount)
            if weight_amount <= 0:
                return None
            weight_unit = conversion.to_unit.abbreviation or conversion.to_unit.name
            # If result is kg but less than 1, convert to grams
            if weight_unit == 'kg' and weight_amount < 1:
                weight_amount = round(weight_amount * 1000)
                weight_unit = 'g'
            return f"{weight_amount}{weight_unit}"
        except Exception:
            return None
"""
BOOK_NOW = """    # A LIST, NOT A QUERYSET - RD-1, 19 Oct 2026. It is walked twice
    # below: once to collect the units a weight is wanted for, and once
    # to build the rows. A queryset walked twice is queried twice.
    ingredients = list(recipe.recipe_ingredients.select_related(
        'ingredient', 'unit', 'preparation'
    ).order_by('ingredient_group', 'ingredient_order'))
    instructions = recipe.instructions.all().order_by('step_number')

    # THE THIRD COPY OF THE WEIGHT WAS HERE - RD-1, 19 Oct 2026, and it
    # was the only one that was already RIGHT: it asked
    # get_preferred_weight_conversion, the authority the rest of this
    # package asks, while view_recipe and recipe_pdf each built a bulk
    # map that did not. It was simply one query per ingredient, which is
    # why neither of them copied it.
    #
    # _recipe_read keeps this answer at that bulk map's cost, so this
    # call site loses nothing.
    _convs = weight_conversions(
        {i.unit_id for i in ingredients
         if i.unit and i.unit.unit_type != 'weight' and i.amount})
"""

BOOKCALL_WAS = """                'weight_equivalent': get_weight_equivalent(ing)"""
BOOKCALL_NOW = """                'weight_equivalent': weight_equivalent(ing, _convs)"""

# AND THE HELPER IT ASKED COMES OUT OF THE IMPORT, because nothing in
# this file asks it any more. An import nobody uses is a claim that
# something here still does.
HELP_WAS = """from ._helpers import (
    convert_to_decimal,
    format_quantity,
    get_or_create_ingredient,
    get_or_create_preparation,
    get_or_create_unit,
    get_preferred_weight_conversion,
)"""
HELP_NOW = """from ._helpers import (
    convert_to_decimal,
    format_quantity,
    get_or_create_ingredient,
    get_or_create_preparation,
    get_or_create_unit,
)"""
HELPDOC_WAS = """  ._helpers   : convert_to_decimal, format_quantity,
                get_or_create_ingredient, get_or_create_preparation,
                get_or_create_unit, get_preferred_weight_conversion"""
HELPDOC_NOW = """  ._helpers   : convert_to_decimal, format_quantity,
                get_or_create_ingredient, get_or_create_preparation,
                get_or_create_unit
                RD-1 took get_preferred_weight_conversion off this list:
                _recipe_read asks WEIGHT_UNIT_PRIORITY itself, in bulk,
                and is now the only thing in the package that resolves
                a weight.
  ._recipe_read : ingredient_rows, instruction_rows, weight_conversions,
                weight_equivalent. ONE read of a whole recipe."""


# ============================================ AND THE TOOL THAT STAGES IT
#
# stage_round.py enumerates from backups, and a created file has none.
# This teaches it to ASK THE PATCHER - which is the only thing that
# knows - rather than trusting whatever was typed after the suite name.
STAGE_WAS = """    live = [p for p in applied if os.path.isfile(p)]

    files = live + [os.path.join(root, e) for e in extra]
    for e in extra:
        if not os.path.isfile(os.path.join(root, e)):
            raise SystemExit('stage_round: %s is not in the tree' % e)
"""
STAGE_NOW = """    live = [p for p in applied if os.path.isfile(p)]

    # A FILE THE ROUND CREATED HAS NO BACKUP, SO ASK THE PATCHER.
    #
    # RD-1, 19 Oct 2026. Everything above enumerates from .bak files,
    # which is right for a file the round CHANGED and blind to one it
    # INVENTED. PF-2 created pages/views/recipes/_recipe_filter.py on
    # 19 October and it shipped only because its name happened to get
    # typed on this command line - a hand-written list, which is the
    # exact failure the docstring above says this tool exists to
    # prevent.
    #
    # So a patcher may declare CREATES, a tuple of repo-relative paths,
    # and that declaration is read from the patcher itself. It lives
    # with the round, it is covered by the round's own suite, and it
    # cannot disagree with what the round writes - the patcher's gate
    # refuses if it does.
    created = []
    for e in extra:
        if not os.path.basename(e).startswith('apply_'):
            continue
        mod = os.path.basename(e)[:-3]
        try:
            sys.path.insert(0, root)
            patcher = __import__(mod)
        except Exception as exc:
            raise SystemExit('stage_round: %s would not import, so its '
                             'CREATES cannot be read: %s' % (e, exc))
        for rel in getattr(patcher, 'CREATES', ()):
            full = os.path.join(root, rel)
            if not os.path.isfile(full):
                raise SystemExit(
                    'stage_round: %s declares it creates %s and that '
                    'file is not in the tree. Either the round is not '
                    'applied or the declaration is wrong, and both ship '
                    'a broken import.' % (e, rel))
            created.append(full)

    files = live + created + [os.path.join(root, e) for e in extra]
    for e in extra:
        if not os.path.isfile(os.path.join(root, e)):
            raise SystemExit('stage_round: %s is not in the tree' % e)
"""
STAGEOUT_WAS = """    print('  ROUND    %d (patcher and suite)' % len(extra))"""
STAGEOUT_NOW = """    if created:
        print('  CREATED  %d (declared by the patcher - no backup '
              'exists, because there was nothing there)' % len(created))
        for p in created:
            print('    %s  (NEW)' % os.path.relpath(p, root))
    print('  ROUND    %d (patcher and suite)' % len(extra))"""


# ============ AND A SENTINEL ON A FILE THIS ROUND CREATES IS BLIND
#
# test_sentinels asks that every pinned string DISCRIMINATES: revert
# the round and the sentinel must stop matching. A sentinel on a file
# the round CREATED cannot be shown to do that - there is no earlier
# version to compare against, because there was no earlier version.
#
# It is the same story the list already tells about PLANTERS, which
# GT-2 wrote on a file it had just created. Revealed, not broken: the
# row is checkable the moment a later round gives _recipe_read.py a
# backup.
BLIND_WAS = """    'PLANTERS':
        'the fifteen suites that must not share a tree, backed up once '
        'by AR-1',
}"""
BLIND_NOW = """    'PLANTERS':
        'the fifteen suites that must not share a tree, backed up once '
        'by AR-1',
    # THE EIGHTH, 19 Oct 2026, and the same story a third time. RD-1
    # pinned `def ingredient_rows(` on _recipe_read.py, which RD-1
    # CREATES - so there is no earlier version to revert to and the
    # row has one version to try. It becomes checkable the moment any
    # later round backs that file up.
    'ingredient_rows':
        'the shared recipe read, on a file RD-1 created - no earlier '
        'version exists to discriminate against',
}"""
BLIND = 'test_sentinels.py'


# ======================= THE CENSUSES THIS ROUND'S TWO TEMPLATES MOVE
#
# recipe_quicklook.html and its shell are the first templates added to
# this tree since MN-1, and eleven suites count templates. Every one
# of these is GROWTH - the thing being counted really grew - and every
# one is carried HERE rather than edited by hand, because a re-pin
# that belongs to no round survives a revert and then fails against
# the tree it was reverted to.
#
# They were edited by hand first. stage_round found no backups for
# them and the push would have shipped eleven suites nothing could
# take back.
CENSUS = [
 ('test_tree_roots.py',
  'MAIN_N = 140   # RT-1, 18 Oct 2026',
  'MAIN_N = 142   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:\n'
  '               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026'),
 ('test_subtree_tones.py',
  "ok(len(tree) == 148, 'a WALK finds 148 templates', len(tree))",
  "# 148 -> 150 - RD-1, 19 Oct 2026, the quick-look pair.\n"
  "ok(len(tree) == 150, 'a WALK finds 150 templates', len(tree))"),
 ('test_subtree_tones.py',
  "ok(len(top) == 122, '  a flat listing finds 122 - 120 was what H7 counted',",
  "ok(len(top) == 124, '  a flat listing finds 124 - 120 was what H7 '\n"
  "   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',"),
 ('test_colour_tokens.py', 'ok(len(STAND) == 12,',
  '# 12 -> 14 - RD-1, 19 Oct 2026. The quick-look partial and its shell\n'
  "# have no {% extends %}, which is what standalone() means by it: its\n"
  '# own docstring names "a modal shell" and "detail fragments".\n'
  'ok(len(STAND) == 14,'),
 ('test_important_base.py',
  "ok(len(stand) == 12, '  twelve templates are standalone', sorted(stand))",
  "# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\n"
  "ok(len(stand) == 14, '  fourteen templates are standalone',\n"
  "   sorted(stand))"),
 ('test_css_standalone.py', 'ok(len(sa) == 12,',
  '# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\n'
  'ok(len(sa) == 14,'),
 ('test_js_buttons.py',
  'CENSUS_NARROW, CENSUS_WIDE = 117, 139   # (wide was 142)',
  'CENSUS_NARROW, CENSUS_WIDE = 117, 141   # RD-1, 19 Oct 2026 - the\n'
  '# quick-look pair. (wide was 139, and 142 before MN-1 retired four\n'
  '# meal-plan screens.)'),
 ('test_js_buttons.py',
  'HITS_LOOSE, HITS_TIGHT = 673, 671   # RT-1, 18 Oct 2026',
  'HITS_LOOSE, HITS_TIGHT = 675, 673   # RD-1, 19 Oct 2026 - one scanner\n'
  '# hit per new template, and BOTH matchers rise by the same two.\n'
  '# (was 673, 671)   # RT-1, 18 Oct 2026'),
 ('test_pair_contrast.py',
  'EXPECT_PAIRS = 706   # MV-3, 19 Oct 2026',
  'EXPECT_PAIRS = 713   # RD-1 and PS-1, 19 Oct 2026 - the quick-look\n'
  '# dialog and the picker strip set both a ground and an ink on seven\n'
  '# more rules between them. (was 706)   # MV-3, 19 Oct 2026'),
 ('test_recipe_tones.py',
  "ok(len(sb.templates(False)) == 117 and len(sb.templates(True)) == 139,\n"
  "   '  which is %d of %d' % (117, 139),",
  "# 139 -> 141 - RD-1, 19 Oct 2026, the quick-look pair. The narrow\n"
  "# half does not move: neither is a recipe-side page.\n"
  "ok(len(sb.templates(False)) == 117 and len(sb.templates(True)) == 141,\n"
  "   '  which is %d of %d' % (117, 141),"),
 ('test_recipe_side_b.py',
  'GATE_WAS, GATE_NOW = 117, 139   # RT-1, 18 Oct 2026',
  'GATE_WAS, GATE_NOW = 117, 141   # RD-1, 19 Oct 2026 - the quick-look\n'
  '# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026'),
 ('test_recipe_side_b.py',
  "ok(len(foot_links) == 2,\n"
  "   'exactly 2 modal-footer primaries in the application are a link to '\n"
  "   'another page', foot_links)",
  "# 2 -> 3 - RD-1, 19 Oct 2026. The quick-look dialog is modelled on\n"
  "# wcim_recipe_quick_view and carries the same Open full recipe in its\n"
  "# footer for the same reason, so it joins this list rather than being\n"
  "# an exception to it.\n"
  "ok(len(foot_links) == 3,\n"
  "   'exactly 3 modal-footer primaries in the application are a link to '\n"
  "   'another page', foot_links)"),
 ('test_recipe_side_b.py',
  "   == ['properties_edit.html', 'wcim_recipe_quick_view.html'],",
  "   == ['properties_edit.html', 'recipe_quicklook.html',\n"
  "       'wcim_recipe_quick_view.html'],"),
 # AND TWO SUITES WERE ON THE WRONG SIDE OF RT-1's SPLIT.
 #
 # RT-1's thesis: twenty-two suites are HISTORICAL - their numbers are
 # claims about the past - while twenty-eight count the tree as it
 # stands. test_colour_tail and test_colour_neutrals are in the frozen
 # list and both assert len(alv_tree.standalone()) == 12, which reads
 # the LIVE tree. The freeze then forbids correcting a number that any
 # new standalone template makes wrong. They move to the list they
 # always belonged in.
 ('test_retired.py',
  "    'test_colour_neutrals.py', 'test_colour_tail.py',\n"
  "    'test_colour_tokens.py', 'test_dr2_values.py',",
  "    # test_colour_neutrals.py and test_colour_tail.py were HERE and\n"
  "    # are not historical - RD-1, 19 Oct 2026. Both assert\n"
  "    # len(alv_tree.standalone()) == 12, and standalone() reads the\n"
  "    # LIVE tree, so the number moves whenever a template with no\n"
  "    # {% extends %} is added. They are in MOVED, with the other live\n"
  "    # censuses.\n"
  "    'test_dr2_values.py',"),
 ('test_retired.py', 'MOVED = (',
  "MOVED = (\n"
  "    # RD-1, 19 Oct 2026 - moved out of KEPT, where RT-1 filed them.\n"
  "    # Their standalone() count is a census of the tree as it stands,\n"
  "    # not a claim about what CS-2 did.\n"
  "    'test_colour_neutrals.py', 'test_colour_tail.py',\n"
  "    'test_colour_tokens.py',"),
 ('test_colour_tail.py', 'ok(len(STAND) == 12,',
  '# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\n'
  'ok(len(STAND) == 14,'),
 ('test_colour_neutrals.py', 'ok(len(STAND) == 12,',
  '# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\n'
  'ok(len(STAND) == 14,'),
]


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
    raise SystemExit('RD-1 REFUSED: %s' % msg)


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


def swap_n(text, old, new, n, where):
    """For an anchor that is MEANT to be there more than once.

    The eye is on two rows of the day card - a leftover row and a
    recipe row - and both want the dialog. A blind replace-all would
    also take a third nobody had looked at, so the count is stated.
    """
    got = text.count(fit(text, old))
    if got != n:
        refuse('%s: the anchor appears %d time(s), expected exactly %d - %r'
               % (where, got, n, old[:72]))
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    prd = os.path.join(root, READ)
    pc = os.path.join(root, CRUD)
    pu = os.path.join(root, URLS)
    ppa = os.path.join(root, PARTP)
    psh = os.path.join(root, SHELLP)
    pt = os.path.join(root, TPL)

    crud = read(pc)
    urls = read(pu)
    tpl = read(pt)

    # ---------------------------------------------------------------- 0
    # ASK THE TREE FIRST, and ask it about the thing rather than about a
    # name that mentions it.
    if os.path.exists(prd) and 'def recipe_quicklook(' in crud:
        print('RD-1  already applied - a recipe opens without the page.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE. Two halves: the read is duplicated, and
    # there is no dialog on this screen. A round that fixes neither is a
    # round whose suite is measuring the weather.
    sys.path.insert(0, root)
    import alv_tree as T

    flat_crud = crud.replace('\r\n', '\n')
    if VR_WAS not in flat_crud:
        refuse('%s does not hold view_recipe\'s copy of the read - it may '
               'already have been changed by hand' % CRUD)
    if PDF_WAS not in flat_crud:
        refuse('%s does not hold recipe_pdf\'s copy of the read' % CRUD)
    if BOOK_WAS not in flat_crud:
        refuse('%s does not hold recipe_book_detail\'s copy - the third, '
               'and the only one that was already right' % CRUD)
    # ASKED BY COUNT, NOT BY NAME. The survey found two copies because
    # it read the two functions it had been told about; the suite's
    # control counted them and found three. A round that moves "the
    # duplicated read" has to know how many there are.
    n_arith = flat_crud.count('weight_amount = round(amount')
    if n_arith != 3:
        refuse('%s holds the weight arithmetic %d time(s), and this '
               'round is written for exactly 3. A fourth is a call site '
               'nobody has repointed.' % (CRUD, n_arith))
    if os.path.exists(prd):
        refuse('%s already exists' % READ)
    if os.path.exists(ppa) or os.path.exists(psh):
        refuse('%s or %s already exists' % (PARTP, SHELLP))
    # ASKED OF THE MARKUP, NOT OF THE WHOLE FILE. A comment about a
    # dialog is not a dialog, and this screen's JavaScript mentions
    # several.
    if 'data-quicklook' in T.code_only(tpl):
        refuse('%s already carries a quick-look trigger' % TPL)

    # ---------------------------------------------------------------- 2
    # KEYED OFF THE DECLARATION, so a file added here without being
    # declared cannot be shipped and cannot be reverted.
    made = dict(zip(CREATES, (MODULE, PARTIAL, SHELL)))
    for rel, text in made.items():
        out[os.path.join(root, rel)] = text

    crud = swap(crud, DOC_WAS, DOC_NOW, '%s (the module docstring)' % CRUD)
    crud = swap(crud, IMP_WAS, IMP_NOW, '%s (the import)' % CRUD)
    crud = swap(crud, VR_WAS, VR_NOW, '%s (view_recipe\'s read)' % CRUD)
    crud = swap(crud, PDF_WAS, PDF_NOW, '%s (recipe_pdf\'s read)' % CRUD)
    crud = swap(crud, BOOK_WAS, BOOK_NOW,
                '%s (the book detail\'s read - the third copy)' % CRUD)
    crud = swap(crud, BOOKCALL_WAS, BOOKCALL_NOW,
                '%s (the book detail\'s call site)' % CRUD)
    crud = swap(crud, HELP_WAS, HELP_NOW,
                '%s (the helpers import)' % CRUD)
    crud = swap(crud, HELPDOC_WAS, HELPDOC_NOW,
                '%s (the import note)' % CRUD)
    crud = swap(crud, END_WAS, END_NOW, '%s (the endpoint)' % CRUD)
    out[pc] = crud

    out[pu] = swap(urls, URL_WAS, URL_NOW, '%s (the route)' % URLS)

    tpl = swap_n(tpl, EYE_WAS, EYE_NOW, 2, '%s (the eye)' % TPL)
    tpl = swap(tpl, INC_WAS, INC_NOW, '%s (the include)' % TPL)
    out[pt] = tpl

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    for _f, _was, _now in CENSUS:
        _p = os.path.join(root, _f)
        _cur = out.get(_p, read(_p))
        out[_p] = swap(_cur, _was, _now, '%s (a census this round moves)'
                       % _f)

    pbl = os.path.join(root, BLIND)
    out[pbl] = swap(read(pbl), BLIND_WAS, BLIND_NOW,
                    '%s (a sentinel on a created file)' % BLIND)

    pst = os.path.join(root, STAGE)
    s2 = read(pst)
    s2 = swap(s2, STAGE_WAS, STAGE_NOW, '%s (created files)' % STAGE)
    s2 = swap(s2, STAGEOUT_WAS, STAGEOUT_NOW, '%s (the report)' % STAGE)
    out[pst] = s2

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    # THE READ IS ONE READ. If either copy survived, this round has
    # written a THIRD rather than replaced two.
    nc = T.python_code_only(out[pc], payloads=True)
    for dead in ('conversion_map', 'units_needed', 'conversions_qs',
                 'get_weight_equivalent', 'weight_amount = round'):
        if dead in nc:
            refuse('%s still holds %r - the read was meant to MOVE, and a '
                   'copy left behind is the drift this round exists to '
                   'end' % (CRUD, dead))
    if nc.count('ingredient_rows(recipe)') != 3:
        refuse('%s calls ingredient_rows %d time(s), expected 3 - the '
               'page, the PDF and the dialog'
               % (CRUD, nc.count('ingredient_rows(recipe)')))
    # AND THE FOURTH CALL SITE, which wants the two halves rather than
    # the whole read: recipe_book_detail builds plain values for JSON,
    # not decorated model rows.
    if nc.count('weight_equivalent(ing, _convs)') != 1:
        refuse('%s does not call weight_equivalent once for the book '
               'detail - that was the third copy of the arithmetic'
               % CRUD)
    if 'get_preferred_weight_conversion' in nc:
        refuse('%s still imports or calls get_preferred_weight_conversion. '
               'Nothing here asks it now, and an import nobody uses is a '
               'claim that something still does.' % CRUD)

    # THE MODULE ASKS THE SAME AUTHORITY THE HELPER DOES. A second
    # priority order would be the same drift in a new place.
    nr = T.python_code_only(out[prd], payloads=True)
    if 'WEIGHT_UNIT_PRIORITY' not in nr:
        refuse('%s does not use WEIGHT_UNIT_PRIORITY, so it has invented '
               'its own order and get_preferred_weight_conversion will '
               'disagree with it' % READ)
    if "to_unit__unit_type='weight'" not in nr:
        refuse('%s does not constrain to_unit to a weight - a volume '
               'presented as a weight equivalent is the fault this round '
               'is fixing' % READ)

    # THE TRIGGER IS STILL A LINK. A dialog that replaces the link
    # takes away the tab, the middle-click and the JavaScript-off path.
    markup = T.code_only(out[pt])
    eyes = re.findall(
        r'<a href="\{% url \'view_recipe\'[^>]*?data-quicklook=', markup,
        re.S)
    if len(eyes) != 2:
        refuse('%s: %d of the two eyes is an anchor that also carries '
               'data-quicklook. A button would lose the tab and the '
               'JavaScript-off path' % (TPL, len(eyes)))
    shell_markup = T.code_only(out[psh])
    if 'quick-look/' in shell_markup or 'quicklook/' in shell_markup:
        refuse('%s spells a path out in its JavaScript. The URL is '
               'rendered onto each trigger by the server, which is what '
               "WCIM's hand-built '/recipes/wcim/recipe/' + id did not "
               'do' % SHELLP)
    if '@media (max-width' in shell_markup:
        refuse('%s has a bare max-width clause. It names no media type, '
               'so it matches print too - the 21 Sep print-leak round'
               % SHELLP)

    # EVERY TEMPLATE THIS ROUND NAMES IS ONE IT WRITES.
    #
    # This round shipped three spellings of two files: the path
    # constants said _recipe_quicklook.html and _quicklook_shell.html,
    # the view rendered recipe_quicklook.html and the template included
    # recipe_quicklook_shell.html. Nothing would have refused it. The
    # dialog would simply have raised TemplateDoesNotExist the first
    # time Demetri clicked an eye - on production, because the suite
    # would have been asking the constants, which agreed with
    # themselves.
    #
    # So the question is asked of the TREE: the names in the code,
    # against the names on disk.
    # THE FILES THIS ROUND CREATES, not every template it touches:
    # meal_planner.html is EDITED, and asking whether this round wrote
    # it is a different question from whether it invented it. The gate
    # refused over exactly that on its first run, which is the cheapest
    # possible place for it to have happened.
    if set(made) != set(CREATES):
        refuse('%s writes %r but declares %r - stage_round.py and '
               'revert_all.sh both read the declaration, so a file '
               'missing from it ships unreverted or does not ship at '
               'all' % (PATCHER, sorted(made), sorted(CREATES)))
    written = {os.path.basename(ppa), os.path.basename(psh)}
    named = set(re.findall(r"render\(request, '([\w./]+\.html)'", nc))
    named |= set(re.findall(r"\{%\s*include '([\w./]+\.html)'",
                            out[pt]))
    new_names = {n for n in named
                 if n.startswith('recipe_quicklook')}
    missing = sorted(new_names - written)
    if missing:
        refuse('%s: this round renders or includes %s, and writes %s. A '
               'template nobody wrote raises TemplateDoesNotExist the '
               'first time somebody clicks the thing.'
               % (PATCHER, missing, sorted(written)))
    if written != new_names:
        refuse('%s: it writes %s but names %s - a file nothing reaches '
               'is dead weight in the tree'
               % (PATCHER, sorted(written), sorted(new_names)))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('RD-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        if os.path.exists(k):
            backup(k)
        write(k, val)

    print('RD-1  applied - a recipe opens without leaving the calendar.')
    print('      %s is new: ONE read, where this file held THREE'
          % READ)
    print('      and only one of the three asked the authority.')
    print('      %d file(s) written, %d backed up to %s'
          % (len(out),
             sum(1 for k in out if os.path.exists(k + SUFFIX)), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
