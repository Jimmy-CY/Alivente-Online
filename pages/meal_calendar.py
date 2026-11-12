# -*- coding: utf-8 -*-
"""pages/meal_calendar.py - MS-1, 12 Nov 2026. Whose meal plan this is.

Demetri, 14:38-14:44: "just one meal plan per person. It doesn't need a
name. It can be the 'User's Name' Meal Plan. They can select who to share
the meal plan with. If another person is added to someone's meal plan,
they must be able to view their own meal plan, or the one that they have
been added to. They must also be able to edit the meal plan that they
have been added to."

THE MODEL. One MealCalendar per person (created the first time they open
the planner), and a list of people it is shared with. Every MealEntry
belongs to one calendar.

THE MEALS THAT CAME BEFORE. Until `manage.py meal_calendar_backfill
--apply` is run, the meals already on the planner have no calendar, and
every calendar shows them - so nobody loses anything between the deploy
and the backfill. The backfill puts them in Demetri's plan, shared with
Angy, after a dry run he has seen.

WHICH PLAN A REQUEST IS ABOUT. Chosen in the planner (?calendar=<id>) and
remembered in the session; one's own by default. MealCalendarMiddleware
works it out for every meal_plans/ address and sets it for the length of
the request, so the planner's helpers - day_payload, week_entries, the
copy and menu code - ask entries() and get the right meals without each
being handed a request. Outside a request (a suite calling a helper
directly) nothing is set and entries() is every meal, as before.
"""
import contextvars

from django.db.models import Q

_CURRENT = contextvars.ContextVar('meal_calendar', default=None)
SESSION_KEY = 'meal_calendar_id'


def can_plan(user):
    return bool(user and user.is_authenticated and
                user.has_perm('auth.can_access_recipes'))


def own(user):
    """The person's own calendar, made on first use."""
    from .models import MealCalendar
    cal, _ = MealCalendar.objects.get_or_create(owner=user)
    return cal


def accessible(user):
    """Their own first, then the ones shared with them, by owner name."""
    from .models import MealCalendar
    mine = own(user)
    shared = list(MealCalendar.objects.filter(shared_with=user)
                  .exclude(pk=mine.pk).select_related('owner')
                  .order_by('owner__first_name', 'owner__username'))
    return [mine] + shared


def choose(request):
    """The calendar this request is about: ?calendar= if it is one of
    theirs, else the one remembered in the session, else their own."""
    cals = accessible(request.user)
    by_id = {c.pk: c for c in cals}
    want = request.GET.get('calendar') or request.session.get(SESSION_KEY)
    try:
        cal = by_id[int(want)]
    except (TypeError, ValueError, KeyError):
        cal = cals[0]
    if request.session.get(SESSION_KEY) != cal.pk:
        request.session[SESSION_KEY] = cal.pk
    return cal, cals


def current():
    return _CURRENT.get()


def entries():
    """MealEntry rows of the current calendar - and, until the backfill,
    the meals that have none yet. Every meal when no calendar is set."""
    from .models import MealEntry
    cal = _CURRENT.get()
    if cal is None:
        return MealEntry.objects.all()
    return MealEntry.objects.filter(Q(calendar=cal) | Q(calendar__isnull=True))


class MealCalendarMiddleware:
    """Sets the current calendar for meal_plans/ addresses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        if not path.startswith('meal_plans') or not can_plan(
                getattr(request, 'user', None)):
            return self.get_response(request)
        cal, cals = choose(request)
        request.meal_calendar = cal
        request.meal_calendars = cals
        token = _CURRENT.set(cal)
        try:
            return self.get_response(request)
        finally:
            _CURRENT.reset(token)
