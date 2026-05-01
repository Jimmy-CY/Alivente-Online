"""
Recipe nutrition calculator.

Pure Python — no API calls. Reads:
    - Recipe + RecipeIngredient (amounts, units, ingredients)
    - Ingredient (per-100g nutrient values)
    - UnitConversion (specific + generic, for converting amounts to grams)

Returns a dict with:
    - per_serving: {calories, protein, carbs, fat, fiber, sugar, sodium}
    - per_100g:    same shape
    - total:       same shape (sum across all ingredients)
    - total_weight_g
    - servings
    - ingredient_breakdown:
        - mapped: ingredients that contributed to totals (with per-line nutrients)
        - unmapped: ingredients with no nutrition data
        - unconvertible: ingredients with nutrition but no path to grams
        - contributions: unified list for the UI breakdown panel
            (mapped first with values, then unconvertible/unmapped with N/A)
    - is_complete: True if every ingredient contributed
    - macro_split: {protein_pct, carbs_pct, fat_pct} percentage of calories

Workflow:
    1. For each RecipeIngredient line:
        a. Look up the Ingredient + its per-100g nutrition
        b. Convert (amount, unit) to grams using UnitConversion
        c. Multiply per-100g values by (grams / 100)
        d. Add to running totals (or flag as unmapped/unconvertible)
    2. Compute per-serving (total / servings)
    3. Compute per-100g (total / total_weight_g * 100)
    4. Compute macro_split from calories breakdown
"""

from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from .models import RecipeIngredient, UnitConversion, MeasurementUnit


# Atwater factors for energy calculation (kcal per gram)
KCAL_PER_G_PROTEIN = Decimal('4')
KCAL_PER_G_CARBS = Decimal('4')
KCAL_PER_G_FAT = Decimal('9')


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def calculate_recipe_nutrition(recipe) -> Dict:
    """
    Main entry point. Pass a Recipe instance, get back nutrition totals.
    
    Returns a dict (see module docstring for shape). Always returns a
    well-formed dict even if no ingredients are mapped — the caller is
    responsible for displaying the "no data" state appropriately.
    """
    servings = max(int(recipe.servings or 1), 1)
    
    # Pre-fetch the gram unit ID once
    gram_unit_id = _find_gram_unit_id()
    
    # Pre-fetch unit types so we can gate cross-category conversions.
    # Generic conversions are only safe within the same physical category
    # (e.g. weight↔weight). Volume→mass and count→mass require a density,
    # which is always ingredient-specific.
    unit_types = dict(
        MeasurementUnit.objects.values_list('measurement_unit_id', 'unit_type')
    )
    
    # Pre-fetch all generic conversions (unit_a -> unit_b without specific ingredient)
    # This avoids N queries during the loop.
    generic_conversions = _load_generic_conversions()
    
    # Initialise running totals
    totals = _zero_nutrients()
    total_weight_g = Decimal('0')
    
    mapped = []
    unmapped = []
    unconvertible = []
    
    # Walk every ingredient line in the recipe
    recipe_ingredients = (
        RecipeIngredient.objects
        .filter(recipe=recipe)
        .select_related('ingredient', 'unit')
        .prefetch_related('ingredient__specific_conversions')
    )
    
    for ri in recipe_ingredients:
        ingredient = ri.ingredient
        amount = ri.amount or Decimal('0')
        
        # Skip lines with no amount (rare, but possible)
        if amount <= 0:
            continue
        
        # ----- Step 1: Is this ingredient mapped to nutrition data? -----
        if ingredient.calories_per_100g is None:
            unmapped.append({
                'ingredient_id': ingredient.ingredient_id,
                'name': ingredient.name,
                'amount_display': ri.get_amount_display(),
                'unit_name': ri.unit.name if ri.unit else None,
                'reason': 'not_mapped',
            })
            continue
        
        # ----- Step 2: Convert amount to grams -----
        grams = _convert_to_grams(
            amount=amount,
            unit=ri.unit,
            ingredient=ingredient,
            gram_unit_id=gram_unit_id,
            generic_conversions=generic_conversions,
            unit_types=unit_types,
        )
        
        if grams is None or grams <= 0:
            unconvertible.append({
                'ingredient_id': ingredient.ingredient_id,
                'name': ingredient.name,
                'amount_display': ri.get_amount_display(),
                'unit_name': ri.unit.name if ri.unit else 'no unit',
                'reason': 'no_conversion',
            })
            continue
        
        # ----- Step 3: Compute this line's contribution -----
        scale = grams / Decimal('100')
        line_contrib = _scale_nutrients(_nutrients_from_ingredient(ingredient), scale)
        
        # Accumulate
        totals = _add_nutrients(totals, line_contrib)
        total_weight_g += grams
        
        mapped.append({
            'ingredient_id': ingredient.ingredient_id,
            'name': ingredient.name,
            'amount_display': ri.get_amount_display(),
            'unit_name': ri.unit.name if ri.unit else None,
            'grams': float(grams),
            'calories': float(line_contrib['calories']),
            'carbs':    float(line_contrib['carbs']),
            'fat':      float(line_contrib['fat']),
            'protein':  float(line_contrib['protein']),
        })
    
    # ----- Step 4: Compute per-serving and per-100g -----
    per_serving = _scale_nutrients(totals, Decimal('1') / Decimal(servings))
    
    if total_weight_g > 0:
        per_100g = _scale_nutrients(totals, Decimal('100') / total_weight_g)
    else:
        per_100g = _zero_nutrients()
    
    # ----- Step 5: Macro percentage split (from total calories) -----
    macro_split = _compute_macro_split(totals)
    
    is_complete = (len(unmapped) == 0 and len(unconvertible) == 0)
    has_any_data = (len(mapped) > 0)
    
    # ----- Step 6: Build a unified contributions list for the UI panel -----
    # Mapped entries first (with real values), then unconvertible (N/A),
    # then unmapped (N/A). The UI sorts these by calorie contribution and
    # shows N/A entries at the bottom.
    contributions = _build_contributions(mapped, unconvertible, unmapped)
    
    return {
        'has_any_data': has_any_data,
        'is_complete': is_complete,
        'servings': servings,
        'total_weight_g': float(total_weight_g),
        'total_ingredient_count': recipe_ingredients.count(),
        'mapped_count': len(mapped),
        'unmapped_count': len(unmapped),
        'unconvertible_count': len(unconvertible),
        'per_serving': _nutrients_to_floats(per_serving),
        'per_100g':    _nutrients_to_floats(per_100g),
        'total':       _nutrients_to_floats(totals),
        'macro_split': macro_split,
        'ingredient_breakdown': {
            'mapped': mapped,
            'unmapped': unmapped,
            'unconvertible': unconvertible,
            'contributions': contributions,
        },
    }


def _build_contributions(mapped: List[Dict], unconvertible: List[Dict],
                         unmapped: List[Dict]) -> List[Dict]:
    """
    Build a unified list combining mapped + unconvertible + unmapped
    ingredients in the shape the UI expects:
    
        {
            'name', 'amount_display', 'amount_g',
            'is_mapped', 'is_convertible',
            'calories', 'carbs', 'fat', 'protein',
        }
    
    Mapped entries carry real numbers; unconvertible/unmapped carry None
    for nutrient values so the UI renders them as "N/A".
    """
    rows = []
    
    for m in mapped:
        rows.append({
            'name': m['name'],
            'amount_display': m.get('amount_display'),
            'amount_g': m.get('grams'),
            'is_mapped': True,
            'is_convertible': True,
            'calories': m['calories'],
            'carbs':    m['carbs'],
            'fat':      m['fat'],
            'protein':  m['protein'],
        })
    
    for u in unconvertible:
        rows.append({
            'name': u['name'],
            'amount_display': u.get('amount_display'),
            'amount_g': None,
            'is_mapped': True,
            'is_convertible': False,
            'calories': None,
            'carbs':    None,
            'fat':      None,
            'protein':  None,
        })
    
    for u in unmapped:
        rows.append({
            'name': u['name'],
            'amount_display': u.get('amount_display'),
            'amount_g': None,
            'is_mapped': False,
            'is_convertible': False,
            'calories': None,
            'carbs':    None,
            'fat':      None,
            'protein':  None,
        })
    
    return rows


# --------------------------------------------------------------------------- #
# Unit conversion logic
# --------------------------------------------------------------------------- #

def _convert_to_grams(amount, unit, ingredient, gram_unit_id,
                      generic_conversions, unit_types) -> Optional[Decimal]:
    """
    Convert (amount, unit) to grams.
    
    Resolution order:
        1. unit is already grams           → return amount.
        2. Ingredient-specific row exists  → use it (any category — density is
                                              implicit in the stored multiplier).
        3. Generic row exists AND source unit is also 'weight'
                                           → use it (mass↔mass only).
        4. Otherwise                       → None (caller flags unconvertible).
    
    We deliberately do NOT fall back to a generic volume→mass or count→mass
    conversion: those need a density, which is ingredient-specific. Letting
    them through cross-contaminates ingredients (e.g. Garlic Salt's tsp→g
    rate getting applied to Garlic).
    """
    if unit is None:
        # Some recipes have ingredients with no unit ("a pinch", "to taste").
        # We can't convert these. Caller will flag as unconvertible.
        return None
    
    unit_id = unit.measurement_unit_id
    
    # Case 1: already grams
    if gram_unit_id and unit_id == gram_unit_id:
        return Decimal(str(amount))
    
    # Case 2: ingredient-specific conversion (always honoured — the density
    # is implicit in the stored multiplier, so cross-category is safe here)
    specific = (
        ingredient.specific_conversions
        .filter(from_unit_id=unit_id, to_unit_id=gram_unit_id)
        .first()
    )
    if specific:
        try:
            return Decimal(str(amount)) * specific.multiplier
        except (InvalidOperation, TypeError):
            pass
    
    # Case 3: generic conversion — but only within the same physical category.
    # Weight→weight (kg→g, oz→g, lb→g) is fine because mass is mass regardless
    # of substance. Volume→mass and count→mass are NOT — those need an
    # ingredient-specific row.
    source_type = unit_types.get(unit_id)
    if source_type == 'weight' and gram_unit_id:
        multiplier = generic_conversions.get((unit_id, gram_unit_id))
        if multiplier is not None:
            try:
                return Decimal(str(amount)) * multiplier
            except (InvalidOperation, TypeError):
                pass
    
    # No safe path to grams. Caller will mark this line as unconvertible.
    return None


def _find_gram_unit_id() -> Optional[int]:
    """Find the measurement_unit_id for grams."""
    candidates = MeasurementUnit.objects.filter(unit_type='weight').values(
        'measurement_unit_id', 'name', 'abbreviation'
    )
    for u in candidates:
        name = (u.get('name') or '').strip().lower()
        abbr = (u.get('abbreviation') or '').strip().lower()
        if name in ('gram', 'grams', 'g') or abbr == 'g':
            return u['measurement_unit_id']
    return None


def _load_generic_conversions() -> Dict:
    """
    Load all UnitConversion rows where specific_ingredient is NULL.
    Returns a dict {(from_unit_id, to_unit_id): multiplier}.
    """
    rows = UnitConversion.objects.filter(specific_ingredient__isnull=True).values(
        'from_unit_id', 'to_unit_id', 'multiplier'
    )
    return {
        (r['from_unit_id'], r['to_unit_id']): r['multiplier']
        for r in rows
    }


# --------------------------------------------------------------------------- #
# Nutrient arithmetic helpers
# --------------------------------------------------------------------------- #

NUTRIENT_KEYS = ('calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium')


def _zero_nutrients() -> Dict[str, Decimal]:
    return {k: Decimal('0') for k in NUTRIENT_KEYS}


def _nutrients_from_ingredient(ingredient) -> Dict[str, Decimal]:
    """Pull the per-100g values off an Ingredient as a {key: Decimal} dict."""
    return {
        'calories': ingredient.calories_per_100g or Decimal('0'),
        'protein':  ingredient.protein_per_100g  or Decimal('0'),
        'carbs':    ingredient.carbs_per_100g    or Decimal('0'),
        'fat':      ingredient.fat_per_100g      or Decimal('0'),
        'fiber':    ingredient.fiber_per_100g    or Decimal('0'),
        'sugar':    ingredient.sugar_per_100g    or Decimal('0'),
        'sodium':   ingredient.sodium_per_100g   or Decimal('0'),
    }


def _scale_nutrients(nutrients: Dict[str, Decimal], scale: Decimal) -> Dict[str, Decimal]:
    return {k: (v * scale) for k, v in nutrients.items()}


def _add_nutrients(a: Dict[str, Decimal], b: Dict[str, Decimal]) -> Dict[str, Decimal]:
    return {k: (a[k] + b[k]) for k in NUTRIENT_KEYS}


def _nutrients_to_floats(nutrients: Dict[str, Decimal]) -> Dict[str, float]:
    """Convert Decimal values to floats (for JSON serialisation)."""
    return {k: float(v) for k, v in nutrients.items()}


def _compute_macro_split(totals: Dict[str, Decimal]) -> Dict:
    """
    Compute the percentage of calories coming from protein, carbs, and fat.
    
    Uses Atwater factors: 4 kcal/g protein, 4 kcal/g carbs, 9 kcal/g fat.
    
    These rarely sum to exactly 100% because there's also alcohol (7 kcal/g)
    and some calorie reporting variance — but they should be close.
    """
    protein_kcal = totals['protein'] * KCAL_PER_G_PROTEIN
    carbs_kcal   = totals['carbs']   * KCAL_PER_G_CARBS
    fat_kcal     = totals['fat']     * KCAL_PER_G_FAT
    
    macro_kcal_total = protein_kcal + carbs_kcal + fat_kcal
    
    if macro_kcal_total <= 0:
        return {'protein_pct': 0, 'carbs_pct': 0, 'fat_pct': 0}
    
    return {
        'protein_pct': round(float(protein_kcal / macro_kcal_total * 100), 1),
        'carbs_pct':   round(float(carbs_kcal   / macro_kcal_total * 100), 1),
        'fat_pct':     round(float(fat_kcal     / macro_kcal_total * 100), 1),
    }