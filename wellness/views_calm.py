# -*- coding: utf-8 -*-
"""wellness/views_calm.py - WL-7, 31 Oct 2026. The Calm tab.

Breathe, Sit and Guided run entirely on the phone (wellness.js); these
views only draw the pages and keep how long a session lasted when it ends.
See calm.py for what is said and why.
"""
import datetime as dt

from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import calm as C
from .models import Habit
from .views import wellness_view

# A session finished without a connection is sent when Calm next opens;
# one older than this is let go.
LATE_DAYS = 7


def _ticks(user):
    """The habit Calm ticks, if any (the first one)."""
    return Habit.objects.filter(user=user, auto_from='calm',
                                archived_at__isnull=True).first()


def _tick_words(h):
    if not h:
        return ''
    if h.kind == h.KIND_DURATION and h.target:
        return 'Ticks your habit %s after %d minute%s in a day.' % (
            h.name, h.target, '' if h.target == 1 else 's')
    return 'Ticks your habit %s.' % h.name


@wellness_view
def home(request):
    day = timezone.localdate()
    s = C.summary(C.sessions_for(request.user), day)
    h = _ticks(request.user)
    return render(request, 'wellness/calm.html', {
        'tab': 'calm', 'date': day, 'week': s, 'tick_habit': h,
        'tick_words': _tick_words(h),
    })


def _patterns():
    return [{'key': k, 'name': n, 'for': w, 'words': C.pattern_words(st),
             'steps': [[ph, sec] for ph, sec in st]}
            for k, n, w, st in C.PATTERNS]


@wellness_view
def breathe(request):
    pats = _patterns()
    return render(request, 'wellness/calm_breathe.html', {
        'tab': 'calm', 'patterns': pats, 'minutes': C.BREATHE_MINUTES,
        'calm_data': {'kind': 'breathe', 'patterns': pats},
    })


@wellness_view
def sit(request):
    return render(request, 'wellness/calm_sit.html', {
        'tab': 'calm', 'minutes': C.SIT_MINUTES, 'bells': C.SIT_BELLS,
        'calm_data': {'kind': 'sit'},
    })


@wellness_view
def guided(request):
    return render(request, 'wellness/calm_guided.html', {
        'tab': 'calm', 'practices': C.GUIDED,
    })


@wellness_view
def practice(request, key):
    g = C.GUIDED_BY_KEY.get(key)
    if not g:
        raise Http404('no such practice')
    return render(request, 'wellness/calm_practice.html', {
        'tab': 'calm', 'g': g,
        'calm_data': {'kind': 'guided', 'key': g['key'], 'name': g['name'],
                      'seconds': g['minutes'] * 60,
                      'lines': [[at, words] for at, words in g['lines']]},
    })


@wellness_view
@require_POST
def done(request):
    """Keep one finished session. Answers JSON: the week's minutes, and the
    habit ticked, if one was."""
    day = timezone.localdate()
    on = day
    if request.POST.get('date'):
        try:
            on = dt.date.fromisoformat(request.POST['date'])
        except ValueError:
            return HttpResponseBadRequest('bad date')
        if on > day or (day - on).days > LATE_DAYS:
            return JsonResponse({'ok': False, 'kept': False})
    s = C.record(request.user, on, request.POST.get('kind'),
                 request.POST.get('practice'), request.POST.get('seconds'))
    week = C.summary(C.sessions_for(request.user), day)
    names = [h.name for h in Habit.objects.filter(
        user=request.user, auto_from='calm', archived_at__isnull=True,
        logs__date=on, logs__done=True)] if s else []
    return JsonResponse({'ok': True, 'kept': bool(s),
                         'minutes_week': week['minutes'],
                         'ticked': ' and '.join(names)})
