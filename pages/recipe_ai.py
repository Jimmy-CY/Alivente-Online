"""
============================================================================
Recipe AI Suggestions — Core module
============================================================================

Self-contained business logic for generating ingredient-level recipe
modification suggestions via the Anthropic API. No view/URL code here —
just the building blocks.

Public entry point:
    suggest_modifications(recipe, goal) -> dict

This is what the view calls. It handles:
  - Payload build from your existing nutrition calculator
  - Version-hash-based caching against RecipeModificationSuggestion rows
  - API call with prompt caching for cost efficiency
  - JSON extraction (robust to model preamble/fences)
  - Pydantic schema validation
  - Optional retry on validation failure
  - Persistence to the cache table

Configuration via environment / settings:
  ANTHROPIC_API_KEY     — required, set in Railway env
  RECIPE_AI_MODEL       — optional, defaults to claude-sonnet-4-6

Goals supported:
  reduce_carbs, reduce_calories, increase_protein, reduce_fat
============================================================================
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from decimal import Decimal
from typing import Literal

from django.db import transaction
from pydantic import BaseModel, Field, ValidationError

from .models import (
    Recipe,
    RecipeModificationSuggestion,
    Ingredient,
)
from .nutrition_calc import calculate_recipe_nutrition

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS — tweakable
# ============================================================================
DEFAULT_MODEL = os.environ.get("RECIPE_AI_MODEL", "claude-sonnet-4-6")
MAX_OUTPUT_TOKENS = 2000

VALID_GOALS = ("reduce_carbs", "reduce_calories", "increase_protein", "reduce_fat")

# Map goal -> the metric it targets (per-100g field name)
GOAL_TO_METRIC = {
    "reduce_carbs":     "carbs_per_100g",
    "reduce_calories":  "calories_per_100g",
    "reduce_fat":       "fat_per_100g",
    "increase_protein": "protein_per_100g",
}

# Map goal -> the per-ingredient contribution field used in the payload.
# These mirror the metric names but are scoped to "this ingredient
# contributes X to the recipe's total".
GOAL_TO_CONTRIBUTION_FIELD = {
    "reduce_carbs":     "carbs_contribution_g",
    "reduce_calories":  "calories_contribution_kcal",
    "reduce_fat":       "fat_contribution_g",
    "increase_protein": "protein_contribution_g",
}


# ============================================================================
# SYSTEM PROMPT — locked in via test harness, see recipe_ai_test_harness/
# ============================================================================
SYSTEM_PROMPT = """\
You are a recipe modification assistant for a home-cooking app. Users have
nutrition-tracked recipes and occasionally want lower-carb, lower-calorie,
higher-protein, or lower-fat versions of dishes they already cook.

When the user requests modifications for a recipe, you receive a structured
JSON payload describing the recipe and its ingredients with full nutrition
breakdowns. Your job is to suggest 1 to 4 concrete ingredient-level changes
that meaningfully advance the goal while keeping the dish recognizable as
the same dish.

# Important: per-100g, never per-serving

All nutrition values are expressed per 100 grams of the finished dish. This
is the only metric that matters here. Don't reason about "per serving" —
serving sizes in this system are estimates and not reliable. Per-100g is
calculated from actual ingredient weights and is correct.

# What "good" looks like

Each suggestion must be one of:

- substitute: replace an ingredient with a different ingredient
  (e.g., white rice -> cauliflower rice, regular pasta -> lentil pasta)
- reduce: keep the ingredient but use less of it
  (e.g., 200g cheese -> 100g cheese)
- remove: remove the ingredient entirely
  (only suggest this for ingredients that are clearly not structural to the dish)

Prioritize substitutions over reductions, and reductions over removals.
A substitution preserves the dish; a reduction shrinks it; a removal
changes it. Use the lightest-touch change that moves the needle.

# How to choose what to change

Look at the pct_of_recipe_<metric> fields in the payload. They tell you
which ingredients are driving the metric. Focus your suggestions on the
top contributors.

Hard rule: do not suggest changes to ingredients contributing less than
5% of the metric, regardless of suggestion type. If only one ingredient
in the recipe is worth changing, return ONE suggestion, not multiple. A
single high-leverage change is better than padding the response with
trivial ones. The "1 to 4 suggestions" range is a maximum, not a target.

# How to estimate impact

For each suggestion, compute estimated_impact_per_100g — the change to the
recipe's per-100g density of the targeted nutrient if this single
suggestion were applied alone.

To do this correctly:

1. Compute the change in total nutrient grams (original ingredient's
   contribution minus replacement's contribution, if any).
2. The new total recipe weight may change too — if you swap 500g pasta
   for 1000g courgette, the dish gets heavier.
3. Per-100g impact = change_in_nutrient_grams / new_total_weight_g * 100,
   compared to the original per-100g.

Be honest about uncertainty — if you don't know the macros of a substitute
confidently, say so in the rationale and use a conservative estimate.

# Math rules

estimated_new_state values cannot go below zero. If your suggestions would
take a metric below zero per 100g, your impact estimates are too aggressive
or you're proposing changes that exceed the dish's nutrient content.

CRITICAL — derive the forecast from the impacts, don't compute it
independently:

  estimated_new_state.<metric>_per_100g = current_state.<metric>_per_100g
                                          - sum(estimated_impact_per_100g)
                                            for reduce_* goals
  
  estimated_new_state.<metric>_per_100g = current_state.<metric>_per_100g
                                          + sum(estimated_impact_per_100g)
                                            for increase_protein

This is the only correct way. Do not compute the forecast by reasoning
about the entire recipe's new composition — that's where errors creep in.
The forecast is mechanically derived from current_state and the sum of
your suggestions' impacts. Your job is to estimate each ingredient
change's individual impact correctly; the forecast follows from that.

If you're recommending changes that change a metric by more than ~70%,
double-check in your summary that the dish is still recognizable as the
same dish. A lasagne with courgette sheets is still a lasagne; a lasagne
with no pasta or bechamel is something else.

# What NOT to do

- Don't suggest extreme reductions (e.g., "remove all the cheese from a
  cheese-based dish"). The dish must remain itself.
- Don't suggest unfamiliar or hard-to-source ingredients without a common
  alternative ("monk fruit erythritol blend" -- bad; "honey or sugar" -- fine).
- Don't make medical or weight-loss claims. Talk about the food, not the
  eater.
- Don't suggest changes that hurt other macros significantly without
  flagging the tradeoff.
- Don't recommend a specific quantity that's wildly different from the
  original (e.g., "use 50g of pasta instead of 500g" -- that's a reduction
  framed as a substitution, and the dish becomes something else).
- Don't pad with low-impact suggestions just to fill the array. One
  high-impact suggestion is better than four trivial ones.
- Don't suggest adding new ingredients not in the original recipe (e.g.,
  "add 200g cottage cheese as a side"). That's a different recipe, not
  a modification.
- Don't reason about per-serving values. The metric is per-100g.

# Output format

Return ONLY valid JSON matching the schema below. NO prose before or
after the JSON. NO "let me work through this" or "thinking it through"
preamble. NO markdown fences. Your entire response must start with `{`
and end with `}`. Reasoning belongs INSIDE each suggestion's rationale
field, not before or after the JSON object.

All metrics in current_state and estimated_new_state use the exact suffix
`_per_100g`. Don't shorten to `_g`. Match the field names below exactly.

{
  "current_state": {
    "calories_per_100g": <number>,
    "protein_per_100g": <number>,
    "carbs_per_100g": <number>,
    "fat_per_100g": <number>
  },
  "suggestions": [
    {
      "type": "substitute" | "reduce" | "remove",
      "target_ingredient_id": <int>,
      "original": { "name": <str>, "quantity": <number>, "unit": <str> },
      "replacement": { "name": <str>, "quantity": <number>, "unit": <str> } | null,
      "estimated_impact_per_100g": <number>,
      "rationale": <str, max 800 chars — aim for ~300, be concise>,
      "tradeoffs": <str, max 800 chars — aim for ~300, be concise>
    }
  ],
  "estimated_new_state": {
    "<metric>_per_100g": <number>
  },
  "summary": <str, max 200 chars, one sentence>
}

For reduce or remove, replacement is null.
The current_state values come from the payload -- copy them directly.
The estimated_new_state contains only the metric relevant to the goal
(e.g., for reduce_carbs return only carbs_per_100g; for increase_protein
return only protein_per_100g).
estimated_impact_per_100g is the change to the targeted metric if this
single suggestion were applied alone — positive for reduce_* goals (saved)
and positive for increase_protein (gained).
"""


# ============================================================================
# RESPONSE SCHEMAS (Pydantic — validates structured output)
# ============================================================================
class _Quantity(BaseModel):
    name: str
    quantity: float
    unit: str


class _Suggestion(BaseModel):
    type: Literal["substitute", "reduce", "remove"]
    target_ingredient_id: int
    original: _Quantity
    replacement: _Quantity | None = None
    estimated_impact_per_100g: float
    rationale: str = Field(max_length=800)
    tradeoffs: str = Field(max_length=800)


class _CurrentState(BaseModel):
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float


class _EstimatedNewState(BaseModel):
    calories_per_100g: float | None = None
    protein_per_100g: float | None = None
    carbs_per_100g: float | None = None
    fat_per_100g: float | None = None


class _ResponseSchema(BaseModel):
    current_state: _CurrentState
    suggestions: list[_Suggestion] = Field(min_length=1, max_length=4)
    estimated_new_state: _EstimatedNewState
    summary: str = Field(max_length=300)


# ============================================================================
# Custom exceptions
# ============================================================================
class RecipeAIError(Exception):
    """Base exception for all recipe-AI failures."""


class RecipeNotEligibleError(RecipeAIError):
    """Recipe doesn't meet preconditions (no nutrition cache, not complete, etc.)."""


class APICallError(RecipeAIError):
    """Anthropic API call failed (network, auth, rate limit, etc.)."""


class ResponseValidationError(RecipeAIError):
    """Model returned invalid JSON or schema-non-conforming output even after retry."""


# ============================================================================
# PAYLOAD BUILDER
# ============================================================================
def build_modification_payload(recipe: Recipe, goal: str) -> dict:
    """
    Build the JSON payload sent to the LLM.
    
    Reads from your existing calculate_recipe_nutrition() output. The
    'ingredient_breakdown' key on that result is a dict with sub-lists
    keyed by mapping status; we read the 'mapped' bucket, which contains
    every ingredient when is_complete=True.
    """
    if goal not in VALID_GOALS:
        raise RecipeAIError(f"Unknown goal: {goal!r}. Must be one of {VALID_GOALS}")
    
    nutrition_result = calculate_recipe_nutrition(recipe)
    
    if not nutrition_result.get("is_complete"):
        raise RecipeNotEligibleError(
            f"Recipe '{recipe.recipe_name}' has unmapped or unconvertible ingredients. "
            f"Suggestions are only available for fully-completed recipes."
        )
    
    per_100g = nutrition_result.get("per_100g", {})
    total_grams = float(nutrition_result.get("total_weight_g") or 0)
    if total_grams <= 0:
        raise RecipeNotEligibleError(
            f"Recipe '{recipe.recipe_name}' has no calculable total weight."
        )
    
    # Per-100g totals — passed through to the prompt.
    nutrition_per_100g = {
        "calories":  float(per_100g.get("calories") or 0),
        "protein_g": float(per_100g.get("protein") or 0),
        "carbs_g":   float(per_100g.get("carbs") or 0),
        "fat_g":     float(per_100g.get("fat") or 0),
    }
    
    # Read the mapped-ingredient breakdown. is_complete=True guarantees
    # this contains every ingredient.
    breakdown = nutrition_result.get("ingredient_breakdown") or {}
    mapped_entries = breakdown.get("mapped") or []
    
    if not mapped_entries:
        raise RecipeNotEligibleError(
            f"Recipe '{recipe.recipe_name}' returned no mapped ingredients despite "
            f"is_complete=True. Calculator may need re-running."
        )
    
    # Map goal -> the per-ingredient field name in the breakdown.
    # Calculator emits these as bare names (no _g/_kcal suffix).
    goal_short = goal.split("_")[1]  # 'carbs' / 'calories' / 'fat' / 'protein'
    contrib_field_in_breakdown = {
        "carbs":     "carbs",
        "calories":  "calories",
        "fat":       "fat",
        "protein":   "protein",
    }[goal_short]
    
    # Total of the targeted metric across all ingredients (for percentage calc).
    metric_total = sum(
        float(b.get(contrib_field_in_breakdown) or 0) for b in mapped_entries
    )
    
    # Bulk-fetch fdc_description so the LLM knows what each ingredient was
    # mapped to in USDA. One query, not N.
    ingredient_ids = [int(b["ingredient_id"]) for b in mapped_entries]
    fdc_descriptions = dict(
        Ingredient.objects
        .filter(ingredient_id__in=ingredient_ids)
        .values_list('ingredient_id', 'fdc_description')
    )
    
    # Build per-ingredient entries in the payload.
    payload_ingredients = []
    contribution_field_name = GOAL_TO_CONTRIBUTION_FIELD[goal]
    
    for b in mapped_entries:
        ing_id = int(b["ingredient_id"])
        contribution = float(b.get(contrib_field_in_breakdown) or 0)
        pct = (contribution / metric_total * 100) if metric_total > 0 else 0
        
        payload_ingredients.append({
            "ingredient_id": ing_id,
            "name": b.get("name") or "",
            "mapped_food_name": fdc_descriptions.get(ing_id) or "",
            "quantity": b.get("amount_display") or "",  # e.g. "1", "1.5", "½"
            "unit": b.get("unit_name") or "",
            "quantity_in_grams": round(float(b.get("grams") or 0), 1),
            contribution_field_name: round(contribution, 2),
            f"pct_of_recipe_{goal_short}": round(pct, 1),
        })
    
    return {
        "recipe_name": recipe.recipe_name,
        "total_grams": round(total_grams, 1),
        "nutrition_per_100g": {
            "calories":  round(nutrition_per_100g["calories"], 1),
            "protein_g": round(nutrition_per_100g["protein_g"], 1),
            "carbs_g":   round(nutrition_per_100g["carbs_g"], 1),
            "fat_g":     round(nutrition_per_100g["fat_g"], 1),
        },
        "ingredients": payload_ingredients,
        "goal": goal,
    }


# ============================================================================
# VERSION HASH — invalidates cache when recipe data changes
# ============================================================================
def compute_recipe_version_hash(recipe: Recipe) -> str:
    """
    Hash of all the data that affects the LLM's answer for this recipe.
    
    Includes recipe identity + every ingredient's nutrition state. So a manual
    edit to ingredient nutrition (which doesn't change the recipe row) still
    invalidates this hash, since the per-100g values shift.
    
    The cache lookup is (recipe, goal_type, hash). When ANY of these inputs
    differ, we re-call the LLM.
    """
    parts = [
        f"recipe_id={recipe.recipe_id}",
        f"recipe_name={recipe.recipe_name}",
    ]
    
    # Each ingredient's identity, quantity, and current nutrition state.
    # Order matters — sort by recipe_ingredient_id (insertion order) for
    # consistency.
    ris = recipe.recipe_ingredients.select_related(
        'ingredient', 'unit',
    ).order_by('ingredient_order', 'recipe_ingredient_id')
    
    for ri in ris:
        ing = ri.ingredient
        unit_id = ri.unit.measurement_unit_id if ri.unit else None
        # Decimals stringify reliably; floats can be flaky for hashing
        parts.append(
            f"ri:ing={ing.ingredient_id},"
            f"qty={ri.amount},"
            f"unit={unit_id},"
            f"cal={ing.calories_per_100g},"
            f"pro={ing.protein_per_100g},"
            f"car={ing.carbs_per_100g},"
            f"fat={ing.fat_per_100g},"
            f"src={ing.nutrition_source or ''}"
        )
    
    blob = "|".join(parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ============================================================================
# JSON EXTRACTION — robust to model preamble/fences
# ============================================================================
def extract_json_object(text: str) -> str:
    """
    Pull the JSON object out of a model response.
    
    Models occasionally emit prose before/after the JSON or wrap it in
    markdown fences, despite explicit instructions not to. This finds the
    first '{' and the matching closing '}' (handling nesting and string
    literals correctly) and returns just that.
    """
    text = text.strip()
    start = text.find("{")
    if start == -1:
        return text
    
    depth = 0
    in_string = False
    escape = False
    
    for i in range(start, len(text)):
        ch = text[i]
        
        if escape:
            escape = False
            continue
        
        if in_string:
            if ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    
    return text[start:]


# ============================================================================
# API CALL
# ============================================================================
def _call_claude(payload: dict, retry_hint: str | None = None) -> str:
    """
    Call the Anthropic API and return the raw text response.
    
    Uses prompt caching on the system prompt so subsequent calls within ~5 min
    pay only ~10% of the input tokens for the static system block.
    
    retry_hint is appended to the user message on retry so the model knows
    what was wrong with the previous response.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        raise APICallError(
            "anthropic package not installed. Add 'anthropic>=0.40.0' to requirements.txt"
        )
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise APICallError("ANTHROPIC_API_KEY environment variable not set")
    
    client = Anthropic(api_key=api_key)
    
    user_message_text = (
        f"Suggest modifications for this recipe with goal '{payload['goal']}'.\n\n"
        f"<recipe_payload>\n{json.dumps(payload, indent=2)}\n</recipe_payload>"
    )
    if retry_hint:
        user_message_text += (
            f"\n\nNote: Your previous response had a problem: {retry_hint}\n"
            f"Please correct it in this response."
        )
    
    try:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
            # cache_control marks the system prompt as cacheable. First call
            # in a 5-minute window writes the cache; subsequent calls read
            # from it at ~10% of fresh input cost.
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message_text}],
        )
    except Exception as e:
        logger.exception("Anthropic API call failed")
        raise APICallError(f"API call failed: {e}") from e
    
    text_blocks = [b.text for b in response.content if b.type == "text"]
    return "".join(text_blocks).strip()


# ============================================================================
# PUBLIC ENTRY POINT
# ============================================================================
def suggest_modifications(recipe: Recipe, goal: str) -> dict:
    """
    Return suggestions as a dict (already-validated against the schema).
    
    Cache lookup first; only calls the LLM on cache miss.
    Persists successful results to RecipeModificationSuggestion.
    
    Raises:
        RecipeNotEligibleError — recipe isn't fully nutrition-mapped
        APICallError — API call failed
        ResponseValidationError — model returned invalid output even after retry
    """
    if goal not in VALID_GOALS:
        raise RecipeAIError(f"Unknown goal: {goal!r}")
    
    version_hash = compute_recipe_version_hash(recipe)
    
    # Cache hit?
    cached = (
        RecipeModificationSuggestion.objects
        .filter(recipe=recipe, goal_type=goal, recipe_version_hash=version_hash)
        .first()
    )
    if cached:
        logger.info(
            "Cache hit for recipe=%s goal=%s hash=%s",
            recipe.recipe_id, goal, version_hash[:8],
        )
        return cached.suggestions_json
    
    # Cache miss — build payload and call the API
    payload = build_modification_payload(recipe, goal)
    
    parsed_dict, attempts = _call_and_validate(payload)
    
    # Persist
    with transaction.atomic():
        # Race-safe: another request may have written this exact key while we were
        # waiting on the API. unique_together would raise IntegrityError; we just
        # return what's there.
        from django.db import IntegrityError
        try:
            RecipeModificationSuggestion.objects.create(
                recipe=recipe,
                goal_type=goal,
                suggestions_json=parsed_dict,
                recipe_version_hash=version_hash,
            )
        except IntegrityError:
            logger.info("Race: another request cached this key first; using theirs")
            existing = (
                RecipeModificationSuggestion.objects
                .filter(recipe=recipe, goal_type=goal, recipe_version_hash=version_hash)
                .first()
            )
            if existing:
                return existing.suggestions_json
            raise
    
    logger.info(
        "Cached new suggestion: recipe=%s goal=%s attempts=%d",
        recipe.recipe_id, goal, attempts,
    )
    return parsed_dict


def _call_and_validate(payload: dict) -> tuple[dict, int]:
    """
    Internal: API call + validation, with one retry if validation fails.
    Returns (parsed_dict, attempts).
    """
    last_validation_error: str | None = None
    
    for attempt in (1, 2):
        try:
            raw = _call_claude(payload, retry_hint=last_validation_error)
        except APICallError:
            raise  # bubble up directly
        
        # Extract JSON, even if model added preamble or fences
        cleaned = extract_json_object(raw)
        
        try:
            parsed_json = json.loads(cleaned)
        except json.JSONDecodeError as e:
            last_validation_error = f"JSON parse failed at attempt {attempt}: {e}"
            logger.warning(last_validation_error)
            continue
        
        try:
            validated = _ResponseSchema(**parsed_json)
        except ValidationError as e:
            last_validation_error = f"Schema validation failed at attempt {attempt}: {e}"
            logger.warning(last_validation_error)
            continue
        
        return validated.model_dump(), attempt
    
    raise ResponseValidationError(
        f"Model returned invalid output across 2 attempts. Last error: {last_validation_error}"
    )