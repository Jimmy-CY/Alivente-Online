# -*- coding: utf-8 -*-
"""wellness/views_recipe.py - PT-2, 12 Nov 2026. A recipe, inside Wellness.

Demetri, 21:45: today's recipes on the card, and "when clicking on any one
of them, it should show the recipe details, without exiting to the recipe
module. Can we activate the Cook Mode for that Recipe as well here?"

The same read as Recipes (ingredient_rows, instruction_rows - RD-1's one
read, now its fourth reader), in the Wellness look, with Cook mode and
Cooked it. Only for someone who can open Recipes. "‹ Today" goes back.
"""
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from .views import _today, wellness_view

PERM = 'auth.can_access_recipes'


@wellness_view
def recipe(request, recipe_id):
    if not request.user.has_perm(PERM):
        raise PermissionDenied
    from pages.models import Recipe, RecipeCook
    from pages.views.recipes._recipe_read import (ingredient_rows,
                                                  instruction_rows)
    r = get_object_or_404(Recipe, recipe_id=recipe_id)
    cooks = list(RecipeCook.objects.filter(recipe=r, user=request.user))
    rated = [c.rating for c in cooks if c.rating]
    return render(request, 'wellness/recipe.html', {
        'tab': 'today', 'recipe': r,
        'ingredients': ingredient_rows(r),
        'instructions': list(instruction_rows(r)),
        'cooks': cooks[:6], 'cooks_total': len(cooks),
        'last_cook': cooks[0] if cooks else None,
        'cook_avg': (round(sum(rated) / len(rated), 1) if rated else None),
        'today': _today(),
    })
