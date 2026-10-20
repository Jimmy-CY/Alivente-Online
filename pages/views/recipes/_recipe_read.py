"""Reading a recipe whole - the one read behind every screen that shows one.

RD-1, 19 Oct 2026. This is an EXTRACTION, not a new idea: it is the
block `view_recipe` and `recipe_pdf` were each already carrying, and the
recipe modal would have been the third copy of it.

THERE WERE THREE COPIES, AND ONLY ONE OF THEM WAS RIGHT.

  recipe_book_detail  asked get_preferred_weight_conversion - the
                      authority. Correct, and one query per ingredient.
  view_recipe         built a bulk map. One query, and it could choose
                      a conversion the authority would never have.
  recipe_pdf          built its own bulk map, differing from
                      view_recipe's in three places under a comment
                      claiming to mirror it.

So the fast path and the correct path were both already in that file,
in different functions, and nothing reconciled them. This module is
the first one that is both. Both build a bulk map of unit conversions - one query
instead of one per ingredient, which is what the comment above the
original was written for - and then both take whichever row the database
happened to hand back first:

    conversion_map.setdefault((conv.from_unit_id,
                               conv.specific_ingredient_id), conv)

`unit_conversions` is unique on (from_unit, to_unit, specific_ingredient),
so one `(from_unit, ingredient)` pair can legitimately hold SEVERAL rows -
one per target unit. A cup of flour may be recorded as 120g and again as
0.12kg, both true. Which one is read decides what the screen says, and
for ten cups the two answers are `1200g` and `1.2kg`.

`view_recipe` ordered that query and `recipe_pdf` did not, which looks
like the fix and is not one: the ordering is

    .order_by('specific_ingredient', 'from_unit')

and those are the two columns the rival rows SHARE. It groups them and
leaves the tie exactly as undecided as before.

THE APPLICATION ALREADY HAD THE ANSWER. `_helpers.
get_preferred_weight_conversion` resolves the same question properly -
ingredient-specific before generic, then `WEIGHT_UNIT_PRIORITY`, which is
`['g', 'kg', 'oz', 'lb']` - and it is what the rest of the recipes
package asks. It is simply one query per unit per ingredient, which is
the N+1 the bulk map exists to avoid.

So this module keeps the one query AND the helper's answer: it ranks the
rows it fetched by the same priority and takes the best. The page, the
PDF and the modal now say the same thing, and it is the thing the rest of
the application would have said.

TWO MORE FAULTS FALL OUT OF ASKING THE HELPER WHAT IT DOES.

  * The old bulk query did not constrain `to_unit`, so a conversion to a
    non-weight unit could be fetched and its product then presented as a
    `weight_equivalent`. The helper filters `to_unit__unit_type='weight'`.
    So does this.
  * A conversion to a weight unit outside the priority list could win
    over one inside it. The helper can never reach such a row, because it
    only ever asks for those four abbreviations. Neither can this.

THE ARITHMETIC WAS WRONG TOO, and RW-1 is the round that fixed it -
separately, on 19 Oct 2026, because choosing which conversion wins and
changing the sum are different jobs. `round(amount * multiplier, 1)` is
one decimal place of the TARGET unit: a tenth of a gram in grams, and
100g in kilograms. See apply_recipe_weight.py for the five rows of
arithmetic that says it better than a paragraph can.

Read-only. Nothing here writes.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ._helpers import WEIGHT_UNIT_PRIORITY, format_quantity

from pages.models import RecipeIngredient, RecipeInstruction, UnitConversion


# The helper tries the abbreviations in this order and returns the first
# hit, so its position in the list IS its rank. Built once, from the same
# constant, so the two can never drift apart.
WEIGHT_RANK = {abbr: i for i, abbr in enumerate(WEIGHT_UNIT_PRIORITY)}

# WHAT EACH OF THOSE FOUR WEIGHS IN GRAMS - RW-1, 19 Oct 2026.
#
# The sum is done in grams and presented afterwards, because
# `round(x, 1)` is one decimal place OF THE TARGET UNIT and in
# kilograms that is 100g. A cup of flour at 0.120kg was reading 100g on
# the recipe page, and at 0.030kg it was reading nothing at all.
#
# EXACT, for the two that matter. Decimal, not float: `multiplier` is a
# DecimalField and `amount` is a Decimal, so going through float was
# only ever a way to lose the ends of them. The avoirdupois ounce and
# pound are exact too - they are DEFINED as 28.349523125g and
# 453.59237g, not approximated.
#
# THE KEYS ARE WEIGHT_UNIT_PRIORITY's, not a list of their own. A unit
# the priority list never asks for can never be chosen, so a unit
# missing from here would be a unit missing from there.
GRAMS_PER = {
    'g': Decimal('1'),
    'kg': Decimal('1000'),
    'oz': Decimal('28.349523125'),
    'lb': Decimal('453.59237'),
}


def _units_needing_weight(ingredients):
    """The units whose amounts could be shown as a weight.

    A weight unit needs no equivalent - it already is one - and an
    ingredient with no amount has nothing to convert.
    """
    needed = set()
    for ing in ingredients:
        if ing.unit and ing.unit.unit_type != 'weight' and ing.amount:
            needed.add(ing.unit_id)
    return needed


def weight_conversions(unit_ids):
    """One query, and the same answer get_preferred_weight_conversion gives.

    Returns {(from_unit_id, ingredient_id or None): UnitConversion},
    holding the BEST row for each key rather than the first one back.
    """
    if not unit_ids:
        # NOT A QUERY WITH AN EMPTY `__in`. `view_recipe` issued one of
        # those on every recipe whose ingredients were all weights -
        # a round trip to be told nothing. `recipe_pdf` guarded it.
        return {}

    rows = UnitConversion.objects.filter(
        from_unit_id__in=unit_ids,
        to_unit__unit_type='weight',
    ).select_related('to_unit', 'specific_ingredient')

    best = {}
    for conv in rows:
        rank = WEIGHT_RANK.get(conv.to_unit.abbreviation)
        if rank is None:
            # A weight unit the helper would never ask for. It cannot
            # win here either.
            continue
        key = (conv.from_unit_id, conv.specific_ingredient_id)
        held = best.get(key)
        if held is None or rank < held[0]:
            best[key] = (rank, conv)
    return {k: v[1] for k, v in best.items()}


def weight_equivalent(ing, conversions):
    """What this much of this ingredient weighs, as a string, or None.

    The arithmetic and the kilogram rule are the original's, unchanged.
    """
    if not ing.unit or ing.unit.unit_type == 'weight':
        return None
    try:
        amount = float(ing.amount) if ing.amount else 0
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None

    # SPECIFIC BEFORE GENERIC, which is the helper's order too.
    conversion = (conversions.get((ing.unit_id, ing.ingredient_id)) or
                  conversions.get((ing.unit_id, None)))
    if not conversion:
        return None

    # IN GRAMS, EXACTLY - RW-1, 19 Oct 2026. This was
    # `round(amount * float(multiplier), 1)`, which is one decimal
    # place of the TARGET unit: a tenth of a gram in grams and 100g in
    # kilograms. A cup of flour recorded as 0.120kg read 100g, and one
    # recorded as 0.030kg read nothing, because 0.03 rounded to 0.0 and
    # the greater-than-zero guard then dropped it.
    weight_unit = (conversion.to_unit.abbreviation or
                   conversion.to_unit.name)
    per_gram = GRAMS_PER.get(weight_unit)
    if per_gram is None:
        # A unit WEIGHT_UNIT_PRIORITY never asks for cannot have been
        # chosen, so this is unreachable by the selection above. It
        # returns rather than guessing a factor.
        return None
    try:
        # THE PRODUCT, IN THE UNIT IT WAS RECORDED IN, exactly.
        product = Decimal(str(ing.amount)) * Decimal(conversion.multiplier)
        grams = product * per_gram
    except (TypeError, ValueError, ArithmeticError, InvalidOperation):
        return None
    grams = int(grams.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    if grams <= 0:
        return None

    # AND THE DISPLAY UNIT IS UNCHANGED, deliberately. A conversion
    # recorded in grams reads in grams however large it gets - ten cups
    # of flour is 1200g, not 1.2kg - and one recorded in kilograms
    # still promotes to grams under a kilo, which is the rule that was
    # already here. Only the precision moved.
    if weight_unit == 'g' or (weight_unit == 'kg' and grams < 1000):
        return '%dg' % grams

    # SHOWN FROM THE PRODUCT, NOT FROM THE GRAMS.
    #
    # The first cut of this round reconstructed the display value by
    # dividing the integer grams back by the factor, and a quarter of a
    # pound - recorded as exactly 0.25 - came out as `0.249lb`. A
    # round-trip through a rounded integer cannot be more faithful than
    # the integer, and printing three decimals of it claims a precision
    # that was thrown away one line earlier.
    #
    # The product is already exact. Three decimal places of a kilogram
    # is a gram, and of a pound is half a gram, so this is finer than
    # the sum needs either way.
    shown = product.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    # TRAILING ZEROS GO, but through a format rather than normalize():
    # Decimal('1000').normalize() is Decimal('1E+3'), and '1E+3kg' is
    # not a weight anybody reads.
    text = ('%.3f' % shown).rstrip('0').rstrip('.')
    return '%s%s' % (text, weight_unit)


def ingredient_rows(recipe):
    """This recipe's ingredients, in order, each decorated for display.

    Two queries: the ingredients, and the conversions they need.
    """
    ingredients = list(
        RecipeIngredient.objects.filter(recipe=recipe).select_related(
            'ingredient',
            'ingredient__category',
            'unit',
            'preparation',
        ).order_by('ingredient_group', 'ingredient_order')
    )
    conversions = weight_conversions(_units_needing_weight(ingredients))
    for ing in ingredients:
        ing.formatted_amount = format_quantity(ing.amount)
        ing.weight_equivalent = weight_equivalent(ing, conversions)
    return ingredients


def instruction_rows(recipe):
    """The method, in step order."""
    return RecipeInstruction.objects.filter(
        recipe=recipe).order_by('step_number')
