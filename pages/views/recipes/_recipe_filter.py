# -*- coding: utf-8 -*-
"""_recipe_filter.py - ONE place that decides what a filter selects.

PF-2, 19 Oct 2026. Demetri, testing the planner: "It only allows you
to choose Course. We need to be able to select Author, Favorites,
Category and Protein (or vegetarian)."

All four already existed in recipe_management, with these exact GET
parameter names, and the picker was ignoring them. The cheap fix was
to re-implement the matching in JavaScript against data- attributes.
The honest one is this: both screens ask the same function, and a
suite replays them side by side to prove they agree.

THE THREE PIECES, kept apart on purpose:

    vocabulary(user)   what the controls are allowed to offer
    selected_from(q)   what the person chose, read out of a QueryDict
    filter_recipes()   what that selects

A caller that only draws the controls needs the first. A caller that
only answers a fetch needs the last two. Nothing needs all three to
do one job, and splitting them is what lets the planner page stop
carrying 336 recipes it may never show.

THE `vegetarian` MAGIC VALUE IS LOAD-BEARING AND IT IS NOT NEW.
`is_vegetarian` is a boolean column, not a CustomProtein row, so it
cannot have an id - and a separate checkbox for it would read as a
fifth filter rather than one more answer to "what protein?".
recipe_management solved that on its own by putting the literal
string 'vegetarian' in the protein list. That decision is kept here
exactly, because changing it would silently break every saved link
anyone has to a filtered library.
"""
from django.db.models import Q

from pages.models import (
    CustomProtein,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
)

# THE PARAMETER NAMES, IN ONE PLACE. Both callers read these and the
# suite checks the library's own template still writes them, so a
# rename cannot quietly orphan the controls.
PARAMS = ('search', 'search_type', 'course', 'category', 'protein',
          'author', 'favourites')

VEGETARIAN = 'vegetarian'


def vocabulary():
    """What the five controls may offer.

    RecipeCourse orders itself by display_order then name, which is
    why the course list reads Starter, Main, Dessert rather than
    alphabetically; the others are alphabetical because nothing
    better is defined for them.
    """
    return {
        'courses': RecipeCourse.objects.all().order_by('name'),
        'categories': RecipeCategory.objects.all().order_by('name'),
        'proteins': CustomProtein.objects.all().order_by('name'),
        'authors': [{'value': v, 'name': n}
                    for v, n in Recipe.AUTHOR_CHOICES],
    }


def selected_from(params):
    """Read the five filters out of a GET QueryDict. One reading.

    Returns plain Python, so a caller can log it, compare it or put
    it in a template context without going near the database.
    """
    return {
        'search': params.get('search', ''),
        'search_type': params.get('search_type', 'name'),
        'courses': params.getlist('course'),
        'categories': params.getlist('category'),
        'proteins': params.getlist('protein'),
        'authors': params.getlist('author'),
        'favourites': params.get('favourites') == '1',
    }


def filter_recipes(recipes, sel, user):
    """Apply the five filters. THE ONE PLACE.

    Lifted from recipe_management unchanged - every clause, in the
    same order, including the three-way protein branch. It is not an
    improvement on that code and must not become one without the
    suite being told, because the suite's whole job is to prove the
    library still selects exactly what it selected before.
    """
    search_query = sel.get('search') or ''
    if search_query:
        if sel.get('search_type') == 'ingredient':
            recipes = recipes.filter(
                recipe_ingredients__ingredient__name__icontains=search_query
            )
        else:
            recipes = recipes.filter(recipe_name__icontains=search_query)

    if sel.get('courses'):
        recipes = recipes.filter(
            courses__recipe_course_id__in=sel['courses'])

    if sel.get('categories'):
        recipes = recipes.filter(
            categories__recipe_category_id__in=sel['categories'])

    if sel.get('proteins'):
        selected_proteins = sel['proteins']
        if VEGETARIAN in selected_proteins:
            protein_ids = [p for p in selected_proteins if p != VEGETARIAN]
            if protein_ids:
                recipes = recipes.filter(
                    Q(is_vegetarian=True) |
                    Q(proteins__custom_protein_id__in=protein_ids)
                )
            else:
                recipes = recipes.filter(is_vegetarian=True)
        else:
            recipes = recipes.filter(
                proteins__custom_protein_id__in=selected_proteins)

    if sel.get('authors'):
        recipes = recipes.filter(author__in=sel['authors'])

    if sel.get('favourites'):
        recipes = recipes.filter(favourited_by__user=user)

    # DISTINCT, ALWAYS. Four of the five filters join a many-to-many,
    # and a recipe in two selected categories comes back twice
    # without it. recipe_management has called this since before the
    # planner existed.
    return recipes.distinct()


def favourite_ids(user):
    """The user's favourites, as a set, for a fast `in` on a card."""
    return set(RecipeFavourite.objects.filter(user=user)
               .values_list('recipe_id', flat=True))
