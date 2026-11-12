# -*- coding: utf-8 -*-
"""wellness/views_workouts.py - WL-3, 30 Oct 2026. Workouts.

Every lookup filtered by request.user, as in views.py. The library
exercises (user=None) are shared and read-only; a person's own exercises,
routines and sessions are theirs alone.
"""
import datetime as dt
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import training as TR
from .models import (Exercise, Habit, HabitLog, Routine, RoutineItem,
                     WorkoutSession, WorkoutSet)
from .views import _profile, _tip, _today, wellness_view

WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _exercises(user):
    """What can be picked: the library and your own, less the hidden."""
    return Exercise.objects.filter(Q(user__isnull=True) | Q(user=user),
                                   hidden_at__isnull=True)


def _my_exercise(user, pk):
    """Any exercise you can see - a hidden one of yours too, for its
    history."""
    return get_object_or_404(
        Exercise.objects.filter(Q(user__isnull=True) | Q(user=user)), pk=pk)


# WL-17, 12 Nov 2026 - a new exercise in a routine opens asking for its
# starting numbers (Demetri, 08:01-08:05), with these filled in to change.
def _starting(ex):
    """{sets, rep_min, rep_max, seconds, rest} for a newly added one."""
    if ex.kind in ('time', 'distance'):
        if TR.in_minutes(ex):
            return {'sets': 1, 'rep_min': 1, 'rep_max': 1, 'seconds': 30 * 60,
                    'rest': 0}
        return {'sets': 3, 'rep_min': 1, 'rep_max': 1, 'seconds': 30,
                'rest': 30}
    return {'sets': 3, 'rep_min': 10, 'rep_max': 10, 'seconds': None,
            'rest': 90 if ex.kind == 'weight' else 60}


def _done_sets(user, exercise, exclude_session=None):
    qs = WorkoutSet.objects.filter(session__user=user, exercise=exercise,
                                   done=True)
    if exclude_session is not None:
        qs = qs.exclude(session=exclude_session)
    return qs


def _last_sets(user, exercise, before_session=None):
    """The done sets of this exercise in the most recent other session."""
    qs = _done_sets(user, exercise, before_session).select_related('session')
    last = qs.order_by('-session__started_at').first()
    if not last:
        return []
    return list(qs.filter(session=last.session).order_by('set_no'))


def _best(user, exercise, exclude_session=None):
    return TR.records([(s.weight, s.reps, s.seconds, s.distance_m)
                       for s in _done_sets(user, exercise, exclude_session)])


# ----------------------------------------------------------------- HOME
@wellness_view
def home(request):
    profile = _profile(request.user)
    day = _today()
    routines = list(Routine.objects.filter(user=request.user,
                                           archived=False))
    today_routines = [r for r in routines if day.weekday() in r.weekday_set()]
    open_session = WorkoutSession.objects.filter(
        user=request.user, finished_at__isnull=True).first()
    recent = list(WorkoutSession.objects.filter(
        user=request.user, finished_at__isnull=False)[:8])
    week_start = day - dt.timedelta(days=day.weekday())
    this_week = WorkoutSession.objects.filter(
        user=request.user, finished_at__isnull=False,
        date__gte=week_start).count()
    week_cal = sum(WorkoutSession.objects.filter(
        user=request.user, finished_at__isnull=False,
        date__gte=week_start, calories__isnull=False)
        .values_list('calories', flat=True))
    prs = WorkoutSet.objects.filter(session__user=request.user,
                                    is_pr=True).select_related(
        'exercise', 'session').order_by('-session__started_at')[:5]
    return render(request, 'wellness/workouts.html', {
        'tab': 'workouts', 'routines': routines,
        'today_routines': today_routines, 'open_session': open_session,
        'recent': recent, 'this_week': this_week, 'prs': prs,
        'week_cal': week_cal,
        'weekday_names': WEEKDAYS,
        'tip': _tip(profile, ['workout_routine']) if not routines else None,
    })


# ------------------------------------------------------------- ROUTINES
@wellness_view
def routine_edit(request, pk=None):
    routine = (get_object_or_404(Routine, pk=pk, user=request.user)
               if pk else None)
    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        if routine is None:
            name = (request.POST.get('name') or '').strip()[:80]
            if not name:
                return _routine_page(request, None, 'Give it a short name.')
            routine = Routine.objects.create(user=request.user, name=name)
        new_item = None
        if action == 'add':
            ex = _my_exercise(request.user, request.POST.get('exercise'))
            new_item = RoutineItem.objects.create(
                routine=routine, exercise=ex,
                position=routine.items.count(), **_starting(ex))
        elif action.startswith('remove:'):
            routine.items.filter(pk=action.split(':')[1]).delete()
        elif action.startswith('up:') or action.startswith('down:'):
            _move(routine, action)
        elif action == 'order':
            _order(routine, request.POST.get('order', ''))
        if action in ('save', 'add', 'add-first', 'order') or ':' in action:
            routine.name = ((request.POST.get('name') or routine.name)
                            .strip()[:80] or routine.name)
            routine.weekdays = ''.join(sorted({
                d for d in request.POST.getlist('weekdays')
                if len(d) == 1 and d in '0123456'}))
            routine.save()
            for item in routine.items.select_related('exercise'):
                if new_item is not None and item.pk == new_item.pk:
                    continue
                _save_item(item, request.POST)
        if action == 'save':
            return redirect('wellness:workouts')
        if (action == 'order' and
                request.headers.get('x-requested-with') == 'fetch'):
            return JsonResponse({'ok': True, 'order': [
                i.pk for i in routine.items.all()]})
        if new_item is not None:
            return redirect('%s?new=%d#item-%d' % (
                reverse('wellness:routine_edit', args=[routine.pk]),
                new_item.pk, new_item.pk))
        return redirect('wellness:routine_edit', pk=routine.pk)
    return _routine_page(request, routine, '')


def _save_item(item, post):
    """WL-17 - one exercise's numbers from the routine form: sets, reps
    (one number - or a range, if it shows one), a starting weight, time in
    minutes (cardio, dance, sports) or seconds (a hold), and rest."""
    def got(name, lo, hi, cls=int):
        v = post.get('%s_%d' % (name, item.pk))
        if v in (None, ''):
            return None
        try:
            return max(lo, min(hi, cls(str(v).replace(',', '.'))))
        except (ValueError, InvalidOperation):
            return None
    minutes = TR.in_minutes(item.exercise)
    n = got('sets', 1, 20)
    if n is not None:
        item.sets = n
    one = got('reps', 1, 100)
    if one is not None:
        item.rep_min = item.rep_max = one
    lo, hi = got('rep_min', 1, 100), got('rep_max', 1, 100)
    if lo is not None:
        item.rep_min = lo
    if hi is not None:
        item.rep_max = hi
    if item.rep_max < item.rep_min:
        item.rep_max = item.rep_min
    if '%s_%d' % ('weight', item.pk) in post:
        item.weight = got('weight', Decimal('0'), Decimal('1000'), Decimal)
    if minutes:
        m = got('minutes', 1, 600)
        if m is not None:
            item.seconds = m * 60
        r = got('rest_min', 0, 60)
        if r is not None:
            item.rest = r * 60
    else:
        s = got('seconds', 1, 7200)
        if s is not None:
            item.seconds = s
        r = got('rest', 0, 600)
        if r is not None:
            item.rest = r
    item.save()


def _order(routine, text):
    """WL-18 - the order the exercises were dragged into: their ids,
    comma separated. Applied only when it names exactly this routine's
    exercises, each once."""
    try:
        ids = [int(x) for x in text.split(',') if x.strip()]
    except ValueError:
        return False
    items = {i.pk: i for i in routine.items.all()}
    if sorted(ids) != sorted(items):
        return False
    for n, pk in enumerate(ids):
        if items[pk].position != n:
            items[pk].position = n
            items[pk].save(update_fields=['position'])
    return True


def _move(routine, action):
    way, pk = action.split(':')
    items = list(routine.items.all())
    ids = [i.pk for i in items]
    try:
        i = ids.index(int(pk))
    except ValueError:
        return
    j = i - 1 if way == 'up' else i + 1
    if 0 <= j < len(items):
        items[i], items[j] = items[j], items[i]
    for n, item in enumerate(items):
        if item.position != n:
            item.position = n
            item.save(update_fields=['position'])


def _routine_page(request, routine, error):
    lib = list(_exercises(request.user))
    groups = []
    for code, label in Exercise.MUSCLES:
        xs = [e for e in lib if e.muscle == code]
        if xs:
            groups.append({'label': label, 'exercises': xs})
    items = list(routine.items.select_related('exercise')) if routine else []
    rng = request.GET.get('range', '')
    for it in items:
        it.in_min = TR.in_minutes(it.exercise)
        it.minutes = (it.seconds or 0) // 60
        it.rest_min = (it.rest or 0) // 60
        it.show_range = it.rep_min != it.rep_max or rng == str(it.pk)
    return render(request, 'wellness/routine_form.html', {
        'tab': 'workouts', 'routine': routine, 'error': error,
        'items': items, 'new_pk': request.GET.get('new', ''),
        'groups': groups,
        'weekdays': [{'num': str(i), 'name': n,
                      'on': routine and str(i) in routine.weekdays}
                     for i, n in enumerate(WEEKDAYS)],
    })


@wellness_view
@require_POST
def routine_delete(request, pk):
    routine = get_object_or_404(Routine, pk=pk, user=request.user)
    if request.POST.get('confirm') != 'yes':
        return HttpResponseBadRequest('not confirmed')
    routine.archived = True
    routine.save(update_fields=['archived', 'updated_at'])
    return redirect('wellness:workouts')


# ------------------------------------------------------------- SESSIONS
@wellness_view
@require_POST
def session_start(request):
    open_s = WorkoutSession.objects.filter(
        user=request.user, finished_at__isnull=True).first()
    if open_s:
        return redirect('wellness:session_live', pk=open_s.pk)
    profile = _profile(request.user)
    routine = None
    if request.POST.get('routine'):
        routine = get_object_or_404(Routine, pk=request.POST['routine'],
                                    user=request.user)
    now = timezone.now()
    s = WorkoutSession.objects.create(
        user=request.user, routine=routine,
        name=routine.name if routine else 'Workout',
        date=timezone.localdate(), started_at=now)
    if routine:
        for pos, item in enumerate(routine.items.select_related('exercise')):
            last = _last_sets(request.user, item.exercise, s)
            sug = TR.suggest(item.rep_min, item.rep_max,
                             [(x.weight, x.reps) for x in last],
                             item.exercise.equipment, profile.equipment)
            # WL-17 - the very first time, the routine's starting weight.
            weight = sug['weight']
            if sug['why'] == 'first' and item.weight is not None:
                weight = item.weight
            secs = item.seconds
            if item.exercise.kind == 'time' and \
                    not TR.in_minutes(item.exercise):
                secs, _w = TR.suggest_hold(item.seconds,
                                           [x.seconds for x in last])
            for n in range(1, item.sets + 1):
                WorkoutSet.objects.create(
                    session=s, exercise=item.exercise, position=pos,
                    set_no=n,
                    weight=(Decimal(str(weight))
                            if weight is not None else None),
                    reps=sug['reps'] if item.exercise.kind in
                    ('weight', 'reps') else None,
                    seconds=secs if item.exercise.kind == 'time'
                    else None)
    return redirect('wellness:session_live', pk=s.pk)


def _session_blocks(request, s):
    """The sets grouped by exercise, each with last time's numbers, the
    rest to use, and the progression hint."""
    profile = _profile(request.user)
    items = {}
    if s.routine_id:
        for it in s.routine.items.all():
            items.setdefault(it.exercise_id, it)
    blocks = []
    by_ex = {}
    for st in s.sets.select_related('exercise').order_by('position',
                                                          'set_no'):
        b = by_ex.get(st.exercise_id)
        if b is None:
            last = _last_sets(request.user, st.exercise, s)
            it = items.get(st.exercise_id)
            sug = TR.suggest(it.rep_min if it else 8,
                             it.rep_max if it else 12,
                             [(x.weight, x.reps) for x in last],
                             st.exercise.equipment, profile.equipment)
            mins = TR.in_minutes(st.exercise)
            hint = _hint(sug, it)
            if st.exercise.kind == 'time' and not mins and it:
                secs, why = TR.suggest_hold(it.seconds,
                                            [x.seconds for x in last])
                if why:
                    hint = 'You held it every set last time - try %d s.' % secs
            elif mins:
                done_m = sum((x.seconds or 0) for x in last) // 60
                hint = ('Last time: %d min. No pushing here - just enjoy '
                        'it.' % done_m) if done_m else ''
            b = {'exercise': st.exercise, 'rows': [], 'item': it,
                 'rest': it.rest if it else 60, 'last': last,
                 'hint': hint, 'position': st.position, 'in_min': mins,
                 'words': TR.item_words(it) if it else '',
                 'rest_words': TR.rest_words(it.rest if it else 60, mins)}
            by_ex[st.exercise_id] = b
            blocks.append(b)
        prev = b['last'][len(b['rows'])] if len(b['last']) > len(
            b['rows']) else None
        b['rows'].append({'set': st, 'prev': prev})
    return blocks


def _hint(sug, item):
    if sug['why'] == 'up':
        return ('You did every rep last time - try %s kg today, the next '
                'weight you own.' % TR._kg(sug['weight']))
    if sug['why'] == 'more_reps':
        return 'Every rep last time - aim for %d today.' % sug['reps']
    if sug['why'] == 'reps' and sug['weight'] is not None:
        return 'Same weight, aim for %d reps.' % sug['reps']
    if sug['why'] == 'top':
        return 'Top of your weights - add a rep or slow the lowering.'
    return ''


@wellness_view
def session_live(request, pk):
    s = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    if s.finished_at:
        return redirect('wellness:session_detail', pk=s.pk)
    profile = _profile(request.user)
    return render(request, 'wellness/session_live.html', {
        'tab': 'workouts', 's': s, 'blocks': _session_blocks(request, s),
        'groups': _routine_page_groups(request.user),
        'started_ms': int(s.started_at.timestamp() * 1000),
        'tip': _tip(profile, ['workout_previous']),
    })


def _routine_page_groups(user):
    lib = list(_exercises(user))
    return [{'label': label, 'exercises': [e for e in lib
                                           if e.muscle == code]}
            for code, label in Exercise.MUSCLES
            if any(e.muscle == code for e in lib)]


def _num(v, cls=int, lo=0, hi=100000):
    if v in (None, ''):
        return None
    try:
        n = cls(str(v).replace(',', '.'))
    except (ValueError, InvalidOperation):
        raise ValueError(v)
    if n < lo or n > hi:
        raise ValueError(v)
    return n


@wellness_view
@require_POST
def set_save(request, pk):
    """Save one set's numbers and tick it (or untick). Answers with the
    record it set, if any, and the rest to start."""
    st = get_object_or_404(WorkoutSet, pk=pk, session__user=request.user)
    if st.session.finished_at:
        return HttpResponseBadRequest('that workout is finished')
    try:
        st.weight = _num(request.POST.get('weight'), Decimal, 0, 1000)
        st.reps = _num(request.POST.get('reps'), int, 0, 1000)
        st.seconds = _num(request.POST.get('seconds'), int, 0, 86400)
        mins = _num(request.POST.get('minutes'), int, 0, 1440)
        if mins is not None:
            st.seconds = mins * 60
        km = _num(request.POST.get('km'), Decimal, 0, 1000)
        st.distance_m = int(km * 1000) if km is not None else None
    except ValueError:
        return HttpResponseBadRequest('those numbers do not look right')
    st.done = request.POST.get('done', '1') == '1'
    st.is_pr = False
    reason = ''
    if st.done:
        # Earlier sets of THIS session count too: beating your own first
        # set is not a record, beating your best ever is.
        mine = [(x.weight, x.reps, x.seconds, x.distance_m)
                for x in st.session.sets.filter(exercise=st.exercise,
                                                done=True).exclude(pk=st.pk)]
        best = TR.records([(x.weight, x.reps, x.seconds, x.distance_m)
                           for x in _done_sets(request.user, st.exercise,
                                               st.session)] + mine)
        reason = TR.is_record((st.weight, st.reps, st.seconds,
                               st.distance_m), best)
        st.is_pr = bool(reason)
    st.save()
    item = None
    if st.session.routine_id:
        item = st.session.routine.items.filter(
            exercise=st.exercise).first()
    if request.headers.get('x-requested-with') != 'fetch':
        return redirect('wellness:session_live', pk=st.session_id)
    return JsonResponse({'done': st.done, 'record': reason,
                         'rest': item.rest if item else 60})


@wellness_view
@require_POST
def set_add(request, pk):
    s = get_object_or_404(WorkoutSession, pk=pk, user=request.user,
                          finished_at__isnull=True)
    ex = _my_exercise(request.user, request.POST.get('exercise'))
    last = s.sets.filter(exercise=ex).order_by('-set_no').first()
    if last:
        pos, n = last.position, last.set_no + 1
    else:
        top = s.sets.order_by('-position').first()
        pos, n = (top.position + 1 if top else 0), 1
    WorkoutSet.objects.create(session=s, exercise=ex, position=pos,
                              set_no=n,
                              weight=last.weight if last else None,
                              reps=last.reps if last else None,
                              seconds=last.seconds if last else None)
    return redirect('wellness:session_live', pk=s.pk)


@wellness_view
@require_POST
def set_delete(request, pk):
    st = get_object_or_404(WorkoutSet, pk=pk, session__user=request.user,
                           session__finished_at__isnull=True)
    sid = st.session_id
    st.delete()
    return redirect('wellness:session_live', pk=sid)


@wellness_view
@require_POST
def session_finish(request, pk):
    s = get_object_or_404(WorkoutSession, pk=pk, user=request.user,
                          finished_at__isnull=True)
    if request.POST.get('discard') == 'yes':
        s.delete()
        return redirect('wellness:workouts')
    s.sets.filter(done=False).delete()
    s.finished_at = timezone.now()
    try:
        s.effort = _num(request.POST.get('effort'), int, 1, 10)
    except ValueError:
        s.effort = None
    s.note = (request.POST.get('note') or '').strip()[:280]
    s.save()
    # A habit set to tick itself from a workout is done today.
    if s.sets.exists():
        for h in Habit.objects.filter(user=request.user,
                                      auto_from='workout',
                                      archived_at__isnull=True):
            HabitLog.objects.get_or_create(
                habit=h, date=s.date,
                defaults={'done': True,
                          'value': h.target if h.measured else None})
            if h.started_on > s.date:
                h.started_on = s.date
                h.save(update_fields=['started_on', 'updated_at'])
    return redirect('wellness:session_detail', pk=s.pk)


@wellness_view
def session_detail(request, pk):
    s = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    sets = list(s.sets.select_related('exercise'))
    blocks = []
    for st in sets:
        if not blocks or blocks[-1]['exercise'].pk != st.exercise_id:
            blocks.append({'exercise': st.exercise, 'sets': []})
        blocks[-1]['sets'].append(st)
    secs = ((s.finished_at - s.started_at).total_seconds()
            if s.finished_at else 0)
    return render(request, 'wellness/session_detail.html', {
        'tab': 'workouts', 's': s, 'blocks': blocks,
        'duration': TR.duration(secs),
        'volume': int(TR.volume([(x.weight, x.reps) for x in sets])),
        'records': [x for x in sets if x.is_pr],
        'cal_open': request.GET.get('calories') == '1' or bool(
            request.GET.get('cal_error')),
        'cal_error': request.GET.get('cal_error') == '1',
        'cal_max': CAL_MAX,
    })


# WL-11, 1 Nov 2026. Demetri: "When I do a workout I want to be able to
# optionally capture the Calories that I burnt during that workout."
# Typed in from the watch (a web app cannot read the watch, and an estimate
# from weight and time is far rougher than the watch's heart-rate figure).
# Blank clears it. Can be added or changed any time after.
CAL_MAX = 5000


def clean_calories(raw):
    """'285' -> 285, '' -> None; ValueError for anything else."""
    raw = (raw or '').strip().replace(',', '').replace(' ', '')
    if raw.lower().endswith('kcal'):
        raw = raw[:-4]
    if not raw:
        return None
    if not raw.isdigit():
        raise ValueError('not a whole number')
    n = int(raw)
    if n < 1 or n > CAL_MAX:
        raise ValueError('out of range')
    return n


@wellness_view
@require_POST
def session_calories(request, pk):
    s = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    try:
        s.calories = clean_calories(request.POST.get('calories'))
    except ValueError:
        return redirect(reverse('wellness:session_detail', args=[s.pk]) +
                        '?cal_error=1#w-cal')
    s.save(update_fields=['calories'])
    return redirect('wellness:session_detail', pk=s.pk)


@wellness_view
@require_POST
def session_delete(request, pk):
    s = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    if request.POST.get('confirm') != 'yes':
        return HttpResponseBadRequest('not confirmed')
    s.delete()
    return redirect('wellness:workouts')


# ------------------------------------------------------------ EXERCISES
@wellness_view
def exercise_detail(request, pk):
    ex = _my_exercise(request.user, pk)
    sets = list(_done_sets(request.user, ex).select_related('session')
                .order_by('session__started_at', 'set_no'))
    per = {}
    for st in sets:
        d = per.setdefault(st.session_id, {'date': st.session.date,
                                           'best': None, 'sets': []})
        d['sets'].append(st)
        e = TR.e1rm(st.weight, st.reps)
        val = e if e is not None else (st.reps or st.seconds or
                                       (st.distance_m or 0) / 1000.0)
        if val and (d['best'] is None or val > d['best']):
            d['best'] = val
    pts = [d for d in per.values() if d['best']]
    chart = None
    if len(pts) >= 2:
        lo = min(p['best'] for p in pts)
        hi = max(p['best'] for p in pts)
        if hi - lo < 1e-9:
            lo, hi = lo - 1, hi + 1
        w, h, pad = 320, 140, 12
        n = len(pts)
        coords = [(pad + (w - 2 * pad) * i / float(n - 1),
                   pad + (h - 2 * pad) * (hi - p['best']) / (hi - lo))
                  for i, p in enumerate(pts)]
        chart = {'line': ''.join('%s%.1f %.1f' % ('M' if i == 0 else 'L',
                                                  x, y)
                                 for i, (x, y) in enumerate(coords)),
                 'dots': ''.join('M%.1f %.1fa3 3 0 1 0 6 0a3 3 0 1 0 -6 0'
                                 % (x - 3, y) for x, y in coords),
                 'lo': lo, 'hi': hi, 'w': w, 'h': h}
    best = TR.records([(s.weight, s.reps, s.seconds, s.distance_m)
                       for s in sets])
    return render(request, 'wellness/exercise_detail.html', {
        'tab': 'workouts', 'ex': ex, 'chart': chart, 'best': best,
        'history': list(reversed(list(per.values())))[:12],
        'measure': ('Estimated one-rep max' if ex.kind == 'weight'
                    else {'reps': 'Most reps', 'time': 'Longest',
                          'distance': 'Furthest'}.get(ex.kind, '')),
    })


@wellness_view
def exercise_new(request):
    error = ''
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:80]
        kind = request.POST.get('kind')
        muscle = request.POST.get('muscle')
        equip = request.POST.get('equipment')
        if not name:
            error = 'Give it a name.'
        elif (kind not in dict(Exercise.TYPES) or muscle not in
              dict(Exercise.MUSCLES) or equip not in dict(Exercise.EQUIPMENT)):
            error = 'Choose how it is counted, the muscles and the kit.'
        else:
            Exercise.objects.create(user=request.user, name=name, kind=kind,
                                    muscle=muscle, equipment=equip)
            nxt = request.POST.get('next') or ''
            if nxt.startswith('/wellness/'):
                return redirect(nxt)
            return redirect('wellness:workouts')
    return render(request, 'wellness/exercise_form.html', {
        'tab': 'workouts', 'error': error, 'types': Exercise.TYPES,
        'muscles': Exercise.MUSCLES, 'equipment': Exercise.EQUIPMENT,
        'next': request.GET.get('next', ''),
    })


# --------------------------------------------------------------------------
# WL-17, 12 Nov 2026 - your own exercises: edited, deleted or hidden.
# Demetri, 07:54: "once I have create my own exercise, then I should have
# the ability to Edit it and to Delete it (with the appropriate checks)".
#
#   - Only your own; the library stays as it is.
#   - Name, group and kit can always change. How it is counted can change
#     only until it is logged - a past 3 x 10 at 20 kg means nothing as
#     "time".
#   - Delete says where it is used first:
#       never used            -> gone;
#       in routines only      -> taken out of them, once you tick that;
#       logged in workouts    -> cannot be deleted without losing them, so
#                                Hide it: off every list and routine, still
#                                in the workouts, back any time.
# --------------------------------------------------------------------------
def _own(user, pk):
    return get_object_or_404(Exercise, pk=pk, user=user)


def _uses(ex):
    """(routines it is in, number of workouts it was logged in)."""
    routines = list(Routine.objects.filter(items__exercise=ex,
                                           archived=False).distinct())
    logged = WorkoutSession.objects.filter(sets__exercise=ex).distinct() \
        .count()
    return routines, logged


@wellness_view
def my_exercises(request):
    rows = []
    for ex in Exercise.objects.filter(user=request.user).order_by(
            'hidden_at', 'name'):
        routines, logged = _uses(ex)
        rows.append({'ex': ex, 'routines': len(routines), 'logged': logged,
                     'group': dict(Exercise.MUSCLES).get(ex.muscle, ''),
                     'counted': dict(Exercise.TYPES).get(ex.kind, '').lower()})
    return render(request, 'wellness/my_exercises.html', {
        'tab': 'workouts', 'rows': rows,
    })


@wellness_view
def exercise_edit(request, pk):
    ex = _own(request.user, pk)
    routines, logged = _uses(ex)
    error = ''
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:80]
        kind = request.POST.get('kind') or ex.kind
        muscle = request.POST.get('muscle')
        equip = request.POST.get('equipment')
        if not name:
            error = 'Give it a name.'
        elif (kind not in dict(Exercise.TYPES) or muscle not in
              dict(Exercise.MUSCLES) or equip not in dict(Exercise.EQUIPMENT)):
            error = 'Choose how it is counted, the group and the kit.'
        elif logged and kind != ex.kind:
            error = ('It is logged in %d workout%s, so how it is counted '
                     'stays as it is.' % (logged, '' if logged == 1 else 's'))
        else:
            ex.name, ex.kind, ex.muscle, ex.equipment = name, kind, muscle, \
                equip
            ex.save()
            return redirect('wellness:my_exercises')
    return render(request, 'wellness/exercise_form.html', {
        'tab': 'workouts', 'error': error, 'types': Exercise.TYPES,
        'muscles': Exercise.MUSCLES, 'equipment': Exercise.EQUIPMENT,
        'ex': ex, 'logged': logged, 'routines': routines,
        'next': '',
    })


@wellness_view
@require_POST
def exercise_delete(request, pk):
    ex = _own(request.user, pk)
    routines, logged = _uses(ex)
    if logged:
        return HttpResponseBadRequest('logged in workouts - hide it instead')
    if routines and request.POST.get('confirm') != 'yes':
        return HttpResponseBadRequest('not confirmed')
    RoutineItem.objects.filter(exercise=ex).delete()
    ex.delete()
    return redirect('wellness:my_exercises')


@wellness_view
@require_POST
def exercise_hide(request, pk):
    ex = _own(request.user, pk)
    if request.POST.get('back') == '1':
        ex.hidden_at = None
    else:
        ex.hidden_at = timezone.now()
        RoutineItem.objects.filter(exercise=ex).delete()
    ex.save(update_fields=['hidden_at'])
    return redirect('wellness:my_exercises')


@wellness_view
def kit(request):
    profile = _profile(request.user)
    error = ''
    if request.method == 'POST':
        try:
            dbs = sorted({float(x) for x in (request.POST.get('dumbbells')
                                             or '').replace(',', ' ').split()
                          if 0 < float(x) <= 200})
            kbs = sorted({float(x) for x in (request.POST.get('kettlebells')
                                             or '').replace(',', ' ').split()
                          if 0 < float(x) <= 200})
            bmax = request.POST.get('barbell_max') or ''
            bmax = float(bmax) if bmax.strip() else None
            step = float(request.POST.get('plate_step') or 2.5)
        except ValueError:
            error = 'Weights in kilos, separated by spaces.'
        else:
            profile.equipment = {'dumbbells': dbs, 'kettlebells': kbs,
                                 'barbell_max': bmax, 'plate_step': step}
            profile.save(update_fields=['equipment', 'updated_at'])
            return redirect('wellness:workouts')
    eq = profile.equipment or {}

    def words(xs):
        return ' '.join(TR._kg(x) for x in xs or [])
    return render(request, 'wellness/kit.html', {
        'tab': 'workouts', 'error': error,
        'dumbbells': words(eq.get('dumbbells')),
        'kettlebells': words(eq.get('kettlebells')),
        'barbell_max': '' if eq.get('barbell_max') is None
        else TR._kg(eq['barbell_max']),
        'plate_step': TR._kg(eq.get('plate_step') or 2.5),
    })


def today_card(user, day):
    """What Today shows about workouts."""
    open_s = WorkoutSession.objects.filter(user=user,
                                           finished_at__isnull=True).first()
    done = WorkoutSession.objects.filter(user=user, date=day,
                                         finished_at__isnull=False).first()
    planned = [r for r in Routine.objects.filter(user=user, archived=False)
               if day.weekday() in r.weekday_set()]
    return {'open': open_s, 'done': done, 'planned': planned[:1]}
