"""
AI-powered recipe modification suggestions.

Exposes ONE view (suggest_recipe_modification) plus two private helpers
for rate limiting. The view is the public endpoint for JSON POST
requests that ask an AI for recipe modification suggestions
(reduce_carbs, reduce_calories, increase_protein, reduce_fat).

Flow:
    1. Validate JSON body and goal
    2. Lookup the Recipe; require it to be fully nutrition-mapped
    3. Apply per-user rate limit (10/hour via Django cache)
    4. Check the persistent cache (RecipeModificationSuggestion table)
       by (recipe, goal, version_hash); refund rate-limit slot on hit
    5. On cache miss, call recipe_ai.suggest_modifications() and return

Errors return JSON with appropriate HTTP status codes
(400 validation, 404 not found, 429 rate-limited, 502/503 AI service).

The recipe_ai module (pages/recipe_ai.py) owns the actual AI call
logic; this view is the HTTP + persistence + rate-limit shell around it.

Extracted from pages/views/main.py as part of the modular views
migration (### RECIPE MANAGEMENT ### -> recipes/ sub-package, phase 2).
The original inline `from ..models import RecipeModificationSuggestion`
has been hoisted to module-level imports for cleanliness.
"""

import json
import time

from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ... import recipe_ai
from ...models import Recipe, RecipeModificationSuggestion


# ============================================================================
# RATE LIMIT — 10 requests per user per hour
# ============================================================================
def _check_rate_limit(user, max_per_hour: int = 10) -> tuple[bool, int]:
    """
    Simple cache-based rate limit.
    Returns (allowed, remaining). On allowed=False, remaining is 0.

    Uses Django's cache backend. Falls back to per-process memory if you
    haven't configured a real cache backend (works fine for low traffic).
    """
    cache_key = f"recipe_ai_throttle:{user.pk}"
    history = cache.get(cache_key) or []
    now = time.time()
    one_hour_ago = now - 3600

    # Trim entries older than 1 hour
    history = [t for t in history if t > one_hour_ago]

    if len(history) >= max_per_hour:
        return False, 0

    history.append(now)
    cache.set(cache_key, history, 3600)
    return True, max_per_hour - len(history)


# ============================================================================
# THE VIEW
# ============================================================================
@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
@require_POST
def suggest_recipe_modification(request, recipe_id):
    """
    POST /recipes/<recipe_id>/suggest_modification/

    Body (JSON): { "goal": "reduce_carbs" | "reduce_calories" | "increase_protein" | "reduce_fat" }

    Response (200): {
        "success": true,
        "suggestions": <full validated suggestion dict>,
        "from_cache": <bool>,
        "rate_limit_remaining": <int>
    }

    Response (4xx/5xx): { "success": false, "error": <str> }
    """
    # Parse body
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON body'}, status=400)

    goal = data.get('goal')
    if goal not in recipe_ai.VALID_GOALS:
        return JsonResponse({
            'success': False,
            'error': f'Invalid goal. Must be one of: {", ".join(recipe_ai.VALID_GOALS)}',
        }, status=400)

    # Recipe must exist
    try:
        recipe = Recipe.objects.get(recipe_id=recipe_id)
    except Recipe.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Recipe not found'}, status=404)

    # is_complete gate — only completed recipes can be analyzed
    nutrition_cache = getattr(recipe, 'nutrition_cache', None)
    if not nutrition_cache or not nutrition_cache.is_complete:
        return JsonResponse({
            'success': False,
            'error': 'This recipe is not fully nutrition-mapped yet. Suggestions are available once all ingredients are mapped and convertible.',
        }, status=400)

    # Rate limit (10/hour per user)
    allowed, remaining = _check_rate_limit(request.user)
    if not allowed:
        return JsonResponse({
            'success': False,
            'error': "You've reached the suggestion limit (10 per hour). Try again later.",
        }, status=429)

    # Generate (or return from cache)
    try:
        # Check cache first WITHOUT counting against the rate limit — cache hits are free
        version_hash = recipe_ai.compute_recipe_version_hash(recipe)
        cached = (
            RecipeModificationSuggestion.objects
            .filter(recipe=recipe, goal_type=goal, recipe_version_hash=version_hash)
            .first()
        )
        if cached:
            # Refund the rate-limit slot we just consumed — cache hit doesn't cost the API
            _refund_rate_limit_slot(request.user)
            return JsonResponse({
                'success': True,
                'suggestions': cached.suggestions_json,
                'from_cache': True,
                'rate_limit_remaining': remaining + 1,
            })

        # Cache miss — full call
        suggestions = recipe_ai.suggest_modifications(recipe, goal)

    except recipe_ai.RecipeNotEligibleError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except recipe_ai.APICallError as e:
        return JsonResponse({
            'success': False,
            'error': "Couldn't reach the AI service. Try again in a moment.",
            'detail': str(e),
        }, status=503)
    except recipe_ai.ResponseValidationError as e:
        return JsonResponse({
            'success': False,
            'error': "The AI returned an unexpected response. Try again.",
            'detail': str(e),
        }, status=502)

    return JsonResponse({
        'success': True,
        'suggestions': suggestions,
        'from_cache': False,
        'rate_limit_remaining': remaining,
    })


def _refund_rate_limit_slot(user):
    """Cache hits shouldn't count against the rate limit — pop the most recent entry."""
    cache_key = f"recipe_ai_throttle:{user.pk}"
    history = cache.get(cache_key) or []
    if history:
        history.pop()
        cache.set(cache_key, history, 3600)