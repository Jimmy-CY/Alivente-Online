"""
USDA FoodData Central API client.

Free public API — sign up at https://fdc.nal.usda.gov/api-key-signup/
Documentation: https://fdc.nal.usda.gov/api-guide.html

Two main functions:
    - search_foods(query, page_size=5) -> list of match dicts
    - get_food_details(fdc_id) -> dict with calories/protein/carbs/etc per 100g

Nutrient extraction is hard-coded to the 7 nutrients we care about:
    Calories, Protein, Carbohydrates, Total Fat, Fiber, Total Sugars, Sodium

The FDC API returns nutrients in a list, identified by `nutrient.number`
(USDA's stable nutrient code) in detail responses, and `nutrientNumber`
in search responses.

v2 changes (vs v1):
    - Removed dataType=[...] query param — was causing 400s on certain queries
    - For Branded foods, prefer labelNutrients (per-serving) and rescale to
      per-100g using servingSize/servingSizeUnit. Fixes the "5100 kcal/100g"
      bug from v1 that came from misinterpreting branded foodNutrients.
    - Better 404 error message for known USDA Foundation-vs-detail index drift.
"""

import logging
import re
from decimal import Decimal
from typing import List, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
HTTP_TIMEOUT = 10  # seconds

# USDA nutrient numbers we care about
NUTRIENT_CODES = {
    'energy_kcal':     '208',  # Energy (Atwater General Factors), kcal
    'energy_kcal_alt': '1008', # Energy (Atwater Specific Factors)
    'protein':         '203',
    'fat':             '204',
    'carbs':           '205',
    'fiber':           '291',
    'sugar':           '269',
    'sodium':          '307',  # mg
}

# Map nutrient codes to keys in the `labelNutrients` block (Branded foods).
# labelNutrients reports per-serving values reliably.
LABEL_NUTRIENT_KEYS = {
    'energy_kcal': 'calories',
    'protein':     'protein',
    'fat':         'fat',
    'carbs':       'carbohydrates',
    'fiber':       'fiber',
    'sugar':       'sugars',
    'sodium':      'sodium',
}


class USDAClientError(Exception):
    """Raised on USDA API errors (network, auth, rate-limit, parsing)."""
    pass


def _get_api_key() -> str:
    key = getattr(settings, 'USDA_API_KEY', None)
    if not key:
        raise USDAClientError(
            "USDA_API_KEY is not configured in Django settings. "
            "Sign up at https://fdc.nal.usda.gov/api-key-signup/"
        )
    return key


def search_foods(query: str, page_size: int = 5) -> List[Dict]:
    """
    Search USDA FoodData Central for foods matching the query.
    
    Returns a list of dicts (up to page_size), each with:
        - fdc_id              (int)
        - description         (str)
        - data_type           (str)
        - brand_owner         (str|None)
        - calories_per_100g   (Decimal|None)
    
    Foundation > SR Legacy > Survey (FNDDS) > Branded by post-fetch sort.
    """
    if not query or not query.strip():
        return []
    
    api_key = _get_api_key()
    url = f"{USDA_BASE_URL}/foods/search"
    
    # Sanitise the query — strip slashes, commas, brackets and other special
    # characters that USDA's Elasticsearch sometimes chokes on. Parenthetical
    # content is kept (e.g., "(smoked)" → "smoked") because it adds meaning.
    sanitised_query = _sanitize_query(query)
    
    # IMPORTANT: do NOT pass dataType as a list — the USDA API 400s on certain
    # queries when dataType is provided as repeated params. We over-fetch and
    # sort/filter in Python instead.
    params = {
        'api_key': api_key,
        'query': sanitised_query,
        'pageSize': max(page_size * 4, 25),
    }
    
    try:
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        if response.status_code == 403:
            raise USDAClientError("USDA API key is invalid or expired.") from exc
        if response.status_code == 429:
            raise USDAClientError("USDA API rate limit exceeded. Try again later.") from exc
        if response.status_code >= 500:
            raise USDAClientError(
                "USDA's servers are having a momentary problem. "
                "Wait 30 seconds and try the search again."
            ) from exc
        raise USDAClientError(
            f"USDA API error {response.status_code}: {response.text[:200]}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise USDAClientError(f"Network error contacting USDA: {exc}") from exc
    
    try:
        data = response.json()
    except ValueError as exc:
        raise USDAClientError("USDA returned non-JSON response.") from exc
    
    foods = data.get('foods', [])
    
    # Sort by data type preference (most curated first)
    type_priority = {
        'Foundation': 0,
        'SR Legacy': 1,
        'Survey (FNDDS)': 2,
        'Branded': 3,
    }
    foods.sort(key=lambda f: type_priority.get(f.get('dataType', 'Branded'), 99))
    
    results = []
    for food in foods[:page_size]:
        calories = _extract_calories_from_search_result(food)
        
        results.append({
            'fdc_id': food.get('fdcId'),
            'description': food.get('description', '').strip(),
            'data_type': food.get('dataType', ''),
            'brand_owner': food.get('brandOwner'),
            'calories_per_100g': calories,
        })
    
    return results


def get_food_details(fdc_id: int) -> Dict:
    """
    Fetch full nutrient profile for a given FDC ID.
    
    Returns a dict with per-100g values:
        - fdc_id, description, data_type
        - calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g
        - fiber_per_100g, sugar_per_100g, sodium_per_100g  (sodium in mg)
    
    For Branded foods we prefer `labelNutrients` (per-serving) and rescale
    to per-100g using `servingSize` + `servingSizeUnit`. If serving unit
    isn't grams, we fall back to whatever `foodNutrients` provides.
    
    For Foundation/SR Legacy/Survey, `foodNutrients` is already per-100g.
    """
    if not fdc_id:
        raise USDAClientError("fdc_id is required.")
    
    api_key = _get_api_key()
    url = f"{USDA_BASE_URL}/food/{fdc_id}"
    params = {'api_key': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        if response.status_code == 404:
            raise USDAClientError(
                f"USDA food {fdc_id} not available in detail endpoint. "
                "This is a known USDA quirk — try a different match."
            ) from exc
        if response.status_code == 403:
            raise USDAClientError("USDA API key is invalid or expired.") from exc
        if response.status_code == 429:
            raise USDAClientError("USDA API rate limit exceeded. Try again later.") from exc
        if response.status_code >= 500:
            raise USDAClientError(
                "USDA's servers are having a momentary problem. "
                "Wait 30 seconds and try again."
            ) from exc
        raise USDAClientError(f"USDA API error {response.status_code}") from exc
    except requests.exceptions.RequestException as exc:
        raise USDAClientError(f"Network error contacting USDA: {exc}") from exc
    
    food = response.json()
    data_type = food.get('dataType', '')
    
    # Branded foods: prefer labelNutrients with servingSize rescaling
    if data_type == 'Branded':
        nutrients = _extract_branded_nutrients(food)
    else:
        # Foundation, SR Legacy, Survey (FNDDS): foodNutrients is per-100g
        nutrients = {
            'calories_per_100g': _extract_unbranded_nutrient(food, [NUTRIENT_CODES['energy_kcal'], NUTRIENT_CODES['energy_kcal_alt']]),
            'protein_per_100g':  _extract_unbranded_nutrient(food, [NUTRIENT_CODES['protein']]),
            'carbs_per_100g':    _extract_unbranded_nutrient(food, [NUTRIENT_CODES['carbs']]),
            'fat_per_100g':      _extract_unbranded_nutrient(food, [NUTRIENT_CODES['fat']]),
            'fiber_per_100g':    _extract_unbranded_nutrient(food, [NUTRIENT_CODES['fiber']]),
            'sugar_per_100g':    _extract_unbranded_nutrient(food, [NUTRIENT_CODES['sugar']]),
            'sodium_per_100g':   _extract_unbranded_nutrient(food, [NUTRIENT_CODES['sodium']]),
        }
    
    # Some Foundation foods publish macros but not calories.
    # Fall back to the Atwater General Factors formula:
    #     kcal = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
    # This is the standard food-science approach and is how USDA itself
    # computes "Energy (Atwater General Factors)" — code 208.
    if nutrients.get('calories_per_100g') is None:
        protein = nutrients.get('protein_per_100g')
        carbs   = nutrients.get('carbs_per_100g')
        fat     = nutrients.get('fat_per_100g')
        if protein is not None and carbs is not None and fat is not None:
            try:
                computed = (
                    protein * Decimal('4')
                    + carbs * Decimal('4')
                    + fat * Decimal('9')
                ).quantize(Decimal('0.01'))
                nutrients['calories_per_100g'] = computed
            except (TypeError, ValueError):
                pass
    
    return {
        'fdc_id': food.get('fdcId'),
        'description': food.get('description', '').strip(),
        'data_type': data_type,
        **nutrients,
    }


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

def _extract_unbranded_nutrient(food: Dict, nutrient_numbers: List[str]) -> Optional[Decimal]:
    """
    Extract a per-100g nutrient value from a Foundation/SR Legacy/Survey food.
    These data types report nutrients per 100g directly in `foodNutrients`.
    
    Detail-endpoint shape:
        {
            "nutrient": {"number": "203", "name": "Protein", "unitName": "G"},
            "amount": 12.5
        }
    """
    nutrients = food.get('foodNutrients', [])
    
    for n in nutrients:
        nutrient_obj = n.get('nutrient') or {}
        number = str(nutrient_obj.get('number', '')).strip()
        if number not in nutrient_numbers:
            continue
        
        amount = n.get('amount')
        if amount is None:
            continue
        
        try:
            return Decimal(str(amount)).quantize(Decimal('0.01'))
        except (TypeError, ValueError):
            continue
    
    return None


def _extract_branded_nutrients(food: Dict) -> Dict[str, Optional[Decimal]]:
    """
    Branded foods have a `labelNutrients` block with per-serving values:
        "labelNutrients": {
            "fat":           {"value": 81.1},
            "calories":      {"value": 717},
            "protein":       {"value": 0.85},
            "carbohydrates": {"value": 0.06},
            "sodium":        {"value": 0.011},   <-- in grams!
            ...
        }
    
    These values correspond to a serving of size `servingSize` (in `servingSizeUnit`).
    We rescale each value to per-100g.
    
    Quirks:
        - Sodium in labelNutrients is in grams; we convert to mg.
        - If serving unit isn't grams, we fall back to foodNutrients.
    """
    label = food.get('labelNutrients') or {}
    serving_size = food.get('servingSize')
    serving_unit = (food.get('servingSizeUnit') or '').lower().strip()
    
    # Need gram-based serving size to rescale
    valid_gram_units = {'g', 'grm', 'gr', 'gram', 'grams'}
    can_rescale = (
        serving_size is not None
        and serving_unit in valid_gram_units
        and bool(label)
    )
    
    if not can_rescale:
        logger.info(
            "Branded food %s has serving size %s%s — cannot rescale to per-100g. "
            "Falling back to foodNutrients.",
            food.get('fdcId'), serving_size, serving_unit
        )
        return {
            'calories_per_100g': _extract_unbranded_nutrient(food, [NUTRIENT_CODES['energy_kcal'], NUTRIENT_CODES['energy_kcal_alt']]),
            'protein_per_100g':  _extract_unbranded_nutrient(food, [NUTRIENT_CODES['protein']]),
            'carbs_per_100g':    _extract_unbranded_nutrient(food, [NUTRIENT_CODES['carbs']]),
            'fat_per_100g':      _extract_unbranded_nutrient(food, [NUTRIENT_CODES['fat']]),
            'fiber_per_100g':    _extract_unbranded_nutrient(food, [NUTRIENT_CODES['fiber']]),
            'sugar_per_100g':    _extract_unbranded_nutrient(food, [NUTRIENT_CODES['sugar']]),
            'sodium_per_100g':   _extract_unbranded_nutrient(food, [NUTRIENT_CODES['sodium']]),
        }
    
    try:
        serving_size_dec = Decimal(str(serving_size))
    except (TypeError, ValueError):
        return _empty_nutrients()
    
    if serving_size_dec <= 0:
        return _empty_nutrients()
    
    scale = Decimal('100') / serving_size_dec
    
    result = _empty_nutrients()
    
    mapping = {
        'calories_per_100g': LABEL_NUTRIENT_KEYS['energy_kcal'],
        'protein_per_100g':  LABEL_NUTRIENT_KEYS['protein'],
        'carbs_per_100g':    LABEL_NUTRIENT_KEYS['carbs'],
        'fat_per_100g':      LABEL_NUTRIENT_KEYS['fat'],
        'fiber_per_100g':    LABEL_NUTRIENT_KEYS['fiber'],
        'sugar_per_100g':    LABEL_NUTRIENT_KEYS['sugar'],
        'sodium_per_100g':   LABEL_NUTRIENT_KEYS['sodium'],
    }
    
    for result_key, label_key in mapping.items():
        block = label.get(label_key)
        if not isinstance(block, dict):
            continue
        value = block.get('value')
        if value is None:
            continue
        try:
            per_100g = (Decimal(str(value)) * scale).quantize(Decimal('0.01'))
            # labelNutrients sodium is in grams; convert to mg
            if result_key == 'sodium_per_100g':
                per_100g = (per_100g * Decimal('1000')).quantize(Decimal('0.01'))
            result[result_key] = per_100g
        except (TypeError, ValueError):
            continue
    
    return result


def _empty_nutrients() -> Dict[str, Optional[Decimal]]:
    return {
        'calories_per_100g': None,
        'protein_per_100g':  None,
        'carbs_per_100g':    None,
        'fat_per_100g':      None,
        'fiber_per_100g':    None,
        'sugar_per_100g':    None,
        'sodium_per_100g':   None,
    }


def _extract_calories_from_search_result(food: Dict) -> Optional[Decimal]:
    """
    Search-result nutrient shape (flatter than detail):
        {
            "nutrientId": 1008,
            "nutrientName": "Energy",
            "nutrientNumber": "208",
            "unitName": "KCAL",
            "value": 364
        }
    
    If no published energy value (common for newer Foundation foods),
    fall back to Atwater factors using protein/carbs/fat.
    """
    nutrients = food.get('foodNutrients', [])
    target_codes = {NUTRIENT_CODES['energy_kcal'], NUTRIENT_CODES['energy_kcal_alt']}
    
    for n in nutrients:
        number = str(n.get('nutrientNumber', '')).strip()
        if number in target_codes:
            value = n.get('value')
            if value is not None:
                try:
                    return Decimal(str(value)).quantize(Decimal('0.01'))
                except (TypeError, ValueError):
                    pass
    
    # No published energy — try Atwater fallback
    macros = {}
    macro_codes = {
        'protein': NUTRIENT_CODES['protein'],
        'carbs':   NUTRIENT_CODES['carbs'],
        'fat':     NUTRIENT_CODES['fat'],
    }
    for n in nutrients:
        number = str(n.get('nutrientNumber', '')).strip()
        for macro_name, macro_code in macro_codes.items():
            if number == macro_code:
                value = n.get('value')
                if value is not None:
                    try:
                        macros[macro_name] = Decimal(str(value))
                    except (TypeError, ValueError):
                        pass
    
    if all(k in macros for k in ('protein', 'carbs', 'fat')):
        try:
            kcal = (
                macros['protein'] * Decimal('4')
                + macros['carbs'] * Decimal('4')
                + macros['fat'] * Decimal('9')
            ).quantize(Decimal('0.01'))
            return kcal
        except (TypeError, ValueError):
            pass
    
    return None


# Pattern for characters to strip / replace before sending to USDA.
# We keep letters, numbers, spaces, and parentheses (so "Paprika (smoked)"
# becomes "Paprika  smoked" rather than dropping the parenthetical).
_SPECIAL_CHARS_RE = re.compile(r"[\\/,;:!?@#&$%^*+=<>{}\[\]\"'`~|]")
_MULTI_SPACE_RE = re.compile(r"\s+")


def _sanitize_query(query: str) -> str:
    """
    Clean an ingredient name before sending to USDA search.
    
    Rules:
        - Slashes, commas, semicolons, brackets and other punctuation → space
        - Parentheses themselves get stripped, but the content is kept
          (e.g., "Paprika (smoked)" → "Paprika smoked")
        - Multiple spaces collapsed to one
        - Leading/trailing whitespace stripped
    
    Examples:
        "Carrot/s"           → "Carrot s"
        "Paprika (smoked)"   → "Paprika smoked"
        "Pasta, dry"         → "Pasta dry"
        "Olive oil — extra"  → "Olive oil — extra"   (em-dash kept; harmless)
    """
    if not query:
        return ""
    
    # Replace parentheses with spaces (keeps the content)
    cleaned = query.replace("(", " ").replace(")", " ")
    
    # Replace other special characters with spaces
    cleaned = _SPECIAL_CHARS_RE.sub(" ", cleaned)
    
    # Collapse multiple spaces
    cleaned = _MULTI_SPACE_RE.sub(" ", cleaned)
    
    return cleaned.strip()