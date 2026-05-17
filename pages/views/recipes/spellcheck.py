"""
Recipe-instruction spell checking.

A single AJAX endpoint that spell-checks a list of recipe instruction
strings, ignoring common cooking terms, and returns per-step misspellings
with suggestions.

Functions
---------
- spell_check_instructions : POST AJAX. Read-tier (auth.can_access_personal).
                             Returns JSON {success, errors, total_errors}.

Note
----
Extracted from main.py in Phase 11a. Not recipe-CRUD; kept as its own small
module for cohesion (it spell-checks recipe instruction text). 100% ASCII.
Inline imports (re, SpellChecker, traceback) hoisted to module top per the
normalization standard.
"""

import json
import re
import traceback

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from spellchecker import SpellChecker


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
@require_POST
def spell_check_instructions(request):
    """Spell check recipe instructions"""
    try:
        data = json.loads(request.body)
        instructions = data.get('instructions', [])

        if not instructions:
            return JsonResponse({'success': False, 'error': 'No instructions provided'})

        # Initialize spell checker
        spell = SpellChecker()

        # Common cooking terms to ignore
        cooking_terms = {
            'tsp', 'tbsp', 'mins', 'hrs', 'preheat', 'saute', 'sauteed',
            'broil', 'simmer', 'whisk', 'preheated',
            'mins', 'secs', 'ml', 'oz', 'fahrenheit', 'celsius'
        }
        spell.word_frequency.load_words(cooking_terms)

        errors = []

        for idx, instruction in enumerate(instructions):
            if not instruction.strip():
                continue

            # Remove common cooking abbreviations and numbers
            text = instruction.lower()

            # Split into words, removing punctuation
            words = re.findall(r'\b[a-z]+\b', text)

            # Find misspelled words
            misspelled = spell.unknown(words)

            if misspelled:
                for word in misspelled:
                    # Get suggestions - handle None case
                    candidates = spell.candidates(word)

                    # Convert to list and handle None
                    if candidates is None:
                        suggestions = []
                    else:
                        suggestions = list(candidates)[:5]

                    errors.append({
                        'step': idx + 1,
                        'word': word,
                        'suggestions': suggestions,  # Will be empty list if no suggestions
                        'context': instruction
                    })

        return JsonResponse({
            'success': True,
            'errors': errors,
            'total_errors': len(errors)
        })

    except Exception as e:
        traceback.print_exc()  # Print full error to console for debugging
        return JsonResponse({'success': False, 'error': str(e)}, status=500)