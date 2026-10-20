# -*- coding: utf-8 -*-
"""apply_recipe_weight.py - round RW-1, 19 Oct 2026.

RELEASE 4, PUSH 2. THE WEIGHT IS WORKED OUT IN GRAMS.

Found while surveying for RD-1, and shown to Demetri with the numbers
before a line of it was written. He chose to have it fixed in the same
push, so the page, the PDF, the book detail and the dialog are never
inconsistent with each other.

THE FAULT IS ONE CALL.

    weight_amount = round(amount * float(conversion.multiplier), 1)

One decimal place OF THE TARGET UNIT. In grams that is a tenth of a
gram, which is finer than anybody needs. In kilograms it is 100g.

So for every ingredient whose conversion is recorded in kg:

    1 cup flour @ 0.120 kg      120g true        shown 100g   -17%
    1 cup       @ 0.250 kg      250g true        shown 200g   -20%
    1 cup       @ 0.160 kg      160g true        shown 200g   +25%
    4 cup       @ 0.160 kg      640g true        shown 600g    -6%
    1 cup       @ 0.030 kg       30g true        shown NOTHING

That last row is the worst of them and the easiest to miss: 0.03
rounds to 0.0, the `weight_amount <= 0` guard then returns None, and
the ingredient simply has no weight beside it. Nothing on the screen
says a number was lost.

RD-1 DID NOT FIX THIS, ON PURPOSE. RD-1 had to choose ONE conversion
for four screens that disagreed, so it chose - and it carried this
arithmetic across unchanged rather than quietly altering numbers on a
page. Choosing a row and changing a sum are different jobs and they
get different rounds.

WHAT CHANGES, AND WHAT DELIBERATELY DOES NOT.

The sum is done in GRAMS, exactly, in Decimal - `multiplier` is a
DecimalField and `amount` is a Decimal, so there was never a reason to
go through float.

The DISPLAY UNIT does not change. A conversion recorded in grams still
reads in grams however large it gets, so ten cups of flour stays
`1200g` and does not become `1.2kg`; a conversion recorded in kg still
promotes to grams under a kilo, which is the rule that was already
there and is what makes `120g` and `30g` correct. Only the precision
moves, which is the fault Demetri was shown.

    'g'            whole grams
    'kg' < 1000g   whole grams - the existing promotion, now accurate
    'kg' >= 1000g  kilograms, to the nearest gram, trailing zeros gone
    'oz' / 'lb'    the recorded unit, to the nearest gram

Idempotent. Every file backed up to .bak_recipeweight.
"""
import ast
import os
import sys

SUFFIX = '.bak_recipeweight'
READ = os.path.join('pages', 'views', 'recipes', '_recipe_read.py')
ME = 'test_recipe_weight.py'
PATCHER = 'apply_recipe_weight.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RW-1, 19 Oct 2026'
CHECK = False
CREATES = ()


# ===================================================== THE ARITHMETIC
IMP_WAS = """from ._helpers import WEIGHT_UNIT_PRIORITY, format_quantity

from pages.models import RecipeIngredient, RecipeInstruction, UnitConversion
"""
IMP_NOW = """from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ._helpers import WEIGHT_UNIT_PRIORITY, format_quantity

from pages.models import RecipeIngredient, RecipeInstruction, UnitConversion
"""

RANK_WAS = """WEIGHT_RANK = {abbr: i for i, abbr in enumerate(WEIGHT_UNIT_PRIORITY)}
"""
RANK_NOW = """WEIGHT_RANK = {abbr: i for i, abbr in enumerate(WEIGHT_UNIT_PRIORITY)}

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
"""

MATH_WAS = """    try:
        weight_amount = round(amount * float(conversion.multiplier), 1)
    except (TypeError, ValueError):
        return None
    if weight_amount == int(weight_amount):
        weight_amount = int(weight_amount)
    if weight_amount <= 0:
        return None

    weight_unit = (conversion.to_unit.abbreviation or
                   conversion.to_unit.name)
    # UNDER A KILO IS GRAMS. Nobody writes 0.4kg of flour.
    if weight_unit == 'kg' and weight_amount < 1:
        weight_amount = round(weight_amount * 1000)
        weight_unit = 'g'
    return '%s%s' % (weight_amount, weight_unit)
"""
MATH_NOW = """    # IN GRAMS, EXACTLY - RW-1, 19 Oct 2026. This was
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
"""

DOC_WAS = """Read-only. Nothing here writes.
"""
DOC_NOW = """THE ARITHMETIC WAS WRONG TOO, and RW-1 is the round that fixed it -
separately, on 19 Oct 2026, because choosing which conversion wins and
changing the sum are different jobs. `round(amount * multiplier, 1)` is
one decimal place of the TARGET unit: a tenth of a gram in grams, and
100g in kilograms. See apply_recipe_weight.py for the five rows of
arithmetic that says it better than a paragraph can.

Read-only. Nothing here writes.
"""


# ===================================================== THE REGISTRATIONS
SENT_WAS = """    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'def ingredient_rows('; What = 'RD-1: ONE read of a whole recipe, asked by the page, the PDF and the dialog - they held two copies of it and the two disagreed' },"""
SENT_NOW = """    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'def ingredient_rows('; What = 'RD-1: ONE read of a whole recipe, asked by the page, the PDF and the dialog - they held two copies of it and the two disagreed' },
    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'GRAMS_PER'; What = 'RW-1: the weight is worked out in grams - round(x, 1) is 100g of precision in kilograms, and a cup of flour at 0.120kg was reading 100g' },"""

SUITE_WAS = """    'test_recipe_modal.py'
)"""
SUITE_NOW = """    'test_recipe_modal.py',
    # RW-1, 19 Oct 2026 - the weight in grams. Section 3 asks a real
    # database for the five quantities that were wrong, and section 1
    # asks the function directly for the one that was invisible.
    'test_recipe_weight.py'
)"""

TREE_WAS = """    # RD-1, 19 Oct 2026 - the recipe modal and the shared read behind
    # it. Section 3 replays the block it replaced beside the helper
    # the rest of the package asks, over every ingredient.
    'test_recipe_modal.py',
]"""
TREE_NOW = """    # RD-1, 19 Oct 2026 - the recipe modal and the shared read behind
    # it. Section 3 replays the block it replaced beside the helper
    # the rest of the package asks, over every ingredient.
    'test_recipe_modal.py',
    # RW-1, 19 Oct 2026 - and then the sum itself, in grams. The five
    # quantities it repairs are in the suite as cases, with the true
    # weight beside what the page used to show.
    'test_recipe_weight.py',
]"""

RD_WAS = """    '.bak_recipemodal',
]"""
RD_NOW = """    '.bak_recipemodal',
    # RW-1, 19 Oct 2026 - the weight worked out in grams rather than to
    # one decimal place of whatever unit it was recorded in. It edits
    # the module RD-1 created, so it reverts first.
    '.bak_recipeweight',
]"""

WD_WAS = """CONVERTED_N = 119   # RD-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 120   # RW-1, 19 Oct 2026 - this round own suite   # (was 119)"""


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
    raise SystemExit('RW-1 REFUSED: %s' % msg)


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

    prd = os.path.join(root, READ)

    # ---------------------------------------------------------------- 0
    if not os.path.exists(prd):
        refuse('%s does not exist. RW-1 edits the module RD-1 creates, so '
               'RD-1 goes first.' % READ)
    rd = read(prd)
    if 'GRAMS_PER' in rd:
        print('RW-1  already applied - the weight is worked out in grams.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE, and asked of the code rather than of a
    # comment about it.
    sys.path.insert(0, root)
    import alv_tree as T
    code = T.python_code_only(rd, payloads=True)
    if 'round(amount * float(conversion.multiplier), 1)' not in code:
        refuse('%s does not hold the one-decimal-place round this round '
               'replaces - it may already have been changed by hand'
               % READ)

    # ---------------------------------------------------------------- 2
    rd = swap(rd, IMP_WAS, IMP_NOW, '%s (the import)' % READ)
    rd = swap(rd, RANK_WAS, RANK_NOW, '%s (grams per unit)' % READ)
    rd = swap(rd, MATH_WAS, MATH_NOW, '%s (the arithmetic)' % READ)
    rd = swap(rd, DOC_WAS, DOC_NOW, '%s (the docstring)' % READ)
    out[prd] = rd

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

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nr = T.python_code_only(out[prd], payloads=True)

    # NO FLOAT ANYWHERE IN THE SUM. A Decimal multiplied by a float is
    # a float, so one of them is enough to put the fault back.
    if 'float(conversion.multiplier)' in nr:
        refuse('%s still takes float(multiplier) - the field is a '
               'DecimalField and going through float is how the ends of '
               'it were lost' % READ)
    if 'round(amount' in nr:
        refuse('%s still rounds in the target unit' % READ)

    import re as _re

    # THE FACTORS ARE THE PRIORITY LIST'S. A unit in one and not the
    # other is a unit that can be chosen and not converted, or
    # converted and never chosen.
    keys = set(_re.findall(r"^    '(\w+)': Decimal\(", nr, _re.M))
    # READ OUT OF THE FILE, NOT IMPORTED.
    #
    # The first spelling of this check imported _helpers, which needs
    # Django settings configured - so it raised, fell through to a
    # hardcoded {'g','kg','oz','lb'} and compared the table against a
    # copy of itself. A check that cannot fail is not a check, and this
    # one was comparing two spellings of my own expectation rather than
    # asking the tree.
    helpers = os.path.join(root, 'pages', 'views', 'recipes',
                           '_helpers.py')
    m = _re.search(r'^WEIGHT_UNIT_PRIORITY\s*=\s*\[([^\]]*)\]',
                   read(helpers), _re.M)
    if not m:
        refuse('_helpers.py no longer declares WEIGHT_UNIT_PRIORITY as a '
               'literal list, so the factor table cannot be checked '
               'against it')
    want = set(_re.findall(r"'(\w+)'", m.group(1)))
    if keys != want:
        refuse('%s converts %r and WEIGHT_UNIT_PRIORITY asks for %r. A '
               'unit in one and not the other is a unit that can be '
               'chosen and not converted.' % (READ, sorted(keys),
                                              sorted(want)))

    # AND THE PROMOTION THAT WAS ALREADY THERE IS STILL THERE. Demetri
    # was shown 120g and 30g; a round that dropped the under-a-kilo
    # rule would show 0.12kg and be a different change from the one he
    # agreed to.
    # SHOWN FROM THE PRODUCT. Dividing the rounded grams back by the
    # factor turned an exact 0.25lb into 0.249lb.
    if 'product.quantize' not in nr:
        refuse('%s builds its display value from the rounded grams '
               'rather than from the exact product - that is how a '
               'quarter pound reads as 0.249lb' % READ)
    if "weight_unit == 'kg' and grams < 1000" not in nr:
        refuse('%s has lost the under-a-kilo promotion. The numbers '
               'Demetri agreed to were 120g and 30g, not 0.12kg.' % READ)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('RW-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)

    print('RW-1  applied - the weight is worked out in grams.')
    print('      a cup of flour at 0.120kg read 100g and now reads 120g;')
    print('      at 0.030kg it read nothing at all and now reads 30g.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
