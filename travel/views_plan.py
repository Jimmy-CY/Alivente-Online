"""TR-11, 17 Nov 2026 - Plan my days: the pages.

setup    the three questions (Demetri, 17 Nov: "it needs to ask if there
         any days or mornings/afternoons where we don't want activities";
         and for a place already on a day, "the user needs to be asked if
         a place on a day can be moved").
working  while it is worked out; the page refreshes itself.
review   the proposal; a planned place can be put on another day first.
accept   puts it on the trip. undo puts it back - for as long as the trip
         lasts, and only what nobody has moved since (Demetri: "Undo plan
         must stay available for longer").
The rules are in travel/planner.py.
"""
import datetime as dt

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import planner as PL
from .models import TripPlan
from .views import travel_view
from .views_places import _trip, trip_days


def _phone(request):
    return request.resolver_match.url_name.startswith('m_')


def _show(request, desk, phone, ctx):
    if _phone(request):
        from .phone import page
        return page(request, 'travel/m/%s' % phone, ctx)
    return render(request, 'travel/%s' % desk, ctx)


def _url(request, name, *args):
    return reverse('travel:%s%s' % ('m_' if _phone(request) else '', name),
                   args=args)


def _trip_url(request, t, tab):
    if _phone(request):
        return reverse('travel:m_trip', args=[t.pk]) + '?tab=' + tab
    return reverse('travel:trip_itinerary' if tab == 'itinerary'
                   else 'travel:trip_wishlist', args=[t.pk])


def _plan(request, t, plan_id):
    return get_object_or_404(TripPlan.objects.filter(trip=t), pk=plan_id)


def setup_ctx(t, days, answers=None):
    answers = answers or {}
    bookings = list(t.bookings.all())
    places = list(t.places.all())
    todo = [p for p in places if not p.day and not p.done]
    on_day = sorted([p for p in places if p.day and not p.done],
                    key=lambda p: (p.day, p.time or dt.time(0)))
    keep = answers.get('keep') or {}
    for p in on_day:
        p.locked = bool(p.booking_id)
        p.choice = keep.get(str(p.pk), 'keep')
    cars = [b for b in bookings if b.kind == 'car' and
            b.status != 'cancelled']
    musts = set(int(x) for x in answers.get('must') or [])
    for p in todo + on_day:
        p.must = p.pk in musts
    # Planned by the last accepted plan: grouped, with one switch for all
    # (Demetri agreed: "Planned last time - Keep all / Allow moving").
    last = PL.last_applied(t)
    lastp = set(int(k) for k in (last.applied or {})) if last else set()
    movable = [p for p in on_day if not p.locked]
    return {
        'trip': t, 'todo': todo, 'on_day': on_day,
        'movable': movable,
        'planned_last': [p for p in movable if p.pk in lastp],
        'movable_other': [p for p in movable if p.pk not in lastp],
        'locked': [p for p in on_day if p.locked],
        'grid': PL.grid(t, bookings, days, set(answers.get('off') or [])),
        'pace': answers.get('pace') or 'normal',
        'mode': answers.get('mode') or ('car' if cars else 'transit'),
        'has_car': bool(cars),
        'plannable': todo + [p for p in on_day if not p.locked],
        'paces': PACES, 'modes': MODES,
    }


PACES = [('relaxed', 'Relaxed', 'about 2 a day'),
         ('normal', 'Normal', '3 - 4 a day'),
         ('packed', 'Packed', 'as many as fit')]
MODES = [('walk', 'Walk', 'mostly'),
         ('transit', 'Public transport', 'metro, bus'),
         ('car', 'Car', 'drive')]


def _begin(request, t, answers):
    t.plans.filter(status__in=('working', 'ready', 'failed')).update(
        status='discarded')
    tp = TripPlan.objects.create(trip=t, answers=answers,
                                 created_by=request.user,
                                 progress={'step': 0})
    PL.start(tp)
    return redirect(_url(request, 'plan_view', t.pk, tp.pk))


@travel_view
def setup(request, trip_id):
    t = _trip(request, trip_id)
    days = trip_days(t)
    last = PL.last_applied(t)
    if request.method == 'POST' and days and request.POST.get('fit') \
            and last is not None:
        answers = PL.fit_answers(t, last)
        return _begin(request, t, answers)
    if request.method == 'POST' and days:
        P = request.POST
        answers = {
            'keep': {k[5:]: v for k, v in P.items()
                     if k.startswith('keep_') and v in ('keep', 'move')},
            'off': [x for x in P.getlist('off') if len(x) == 12],
            'pace': P.get('pace') if P.get('pace') in PL.PACE else 'normal',
            'mode': P.get('mode') if P.get('mode') in PL.MODES
            else 'transit',
            'must': [int(x) for x in P.getlist('must') if x.isdigit()],
        }
        # A place a booking holds never moves, whatever was sent.
        locked = set(str(pk) for pk in t.places.filter(
            booking__isnull=False).values_list('pk', flat=True))
        answers['keep'] = {k: v for k, v in answers['keep'].items()
                           if k not in locked}
        return _begin(request, t, answers)
    if request.GET.get('fit') and last is not None:
        # Fit them in: the last answers shown once, Change for the rest.
        a = last.answers or {}
        off = sorted(a.get('off') or [])
        ctx = {'trip': t, 'tab': 'wish', 'sub': 'wish', 'last': last,
               'new': PL.new_since(t, last),
               'todo': [p for p in t.places.filter(day__isnull=True,
                                                   done=False)],
               'off': [(dt.date.fromisoformat(x[:10]),
                        PL.SLOT_NAMES.get(x[11:], '')) for x in off],
               'pace': dict((k, n) for k, n, _s in PACES).get(
                   a.get('pace'), 'Normal'),
               'mode': dict((k, n) for k, n, _s in MODES).get(
                   a.get('mode'), 'Public transport'),
               'back': _trip_url(request, t, 'wish')}
        return _show(request, 'plan_fit.html', 'plan_fit.html', ctx)
    ctx = setup_ctx(t, days, last.answers if last else None)
    ctx.update({'days': days, 'tab': 'wish', 'sub': 'wish',
                'back': _trip_url(request, t, 'wish')})
    return _show(request, 'plan_setup.html', 'plan_setup.html', ctx)


STEPS = ['Found where each place is', 'Read the opening hours',
         'Looking up busy times and visit lengths',
         'Grouping places that are close together',
         'Fitting them into your free slots',
         'Writing a line about each day']


@travel_view
def view(request, trip_id, plan_id):
    t = _trip(request, trip_id)
    tp = _plan(request, t, plan_id)
    if tp.status == 'applied':
        return redirect(_trip_url(request, t, 'itinerary'))
    ctx = {'trip': t, 'tp': tp, 'tab': 'wish', 'sub': 'wish',
           'back': _trip_url(request, t, 'wish')}
    if tp.status == 'working':
        pr = tp.progress or {}
        step = int(pr.get('step') or 0)
        # The planner's steps 1-5 on the six lines the screen shows.
        at = {0: 0, 1: 2, 2: 3, 3: 4, 4: 4, 5: 5}.get(step, 5)
        ctx['steps'] = [{'text': s, 'state': 'done' if i < at else
                         'now' if i == at else 'todo'}
                        for i, s in enumerate(STEPS)]
        ctx['note'] = pr.get('note') or ''
        ctx['count'] = '%s of %s' % (pr.get('done'), pr.get('total')) \
            if pr.get('total') else ''
        ctx['pct'] = min(95, 8 + at * 16)
        return _show(request, 'plan_working.html', 'plan_working.html', ctx)
    if tp.status != 'ready':
        return _show(request, 'plan_failed.html', 'plan_failed.html', ctx)
    res = tp.result or {}
    days = []
    for d in res.get('days') or []:
        day = dt.date.fromisoformat(d['day'])
        rows = []
        for r in d['items']:
            r = dict(r)
            if r.get('moved_from'):
                r['moved_from_date'] = dt.date.fromisoformat(r['moved_from'])
            rows.append(r)
        # One timeline: what stays (grey) and what is planned, by time.
        line = [dict(f, fixed=True) for f in d.get('fixed') or []] + \
            [dict(r, fixed=False) for r in rows]
        line.sort(key=lambda r: r.get('time') or '99')
        days.append({'day': day, 'iso': d['day'], 'items': rows,
                     'line': line,
                     'fixed': d.get('fixed') or [], 'why': d.get('why', ''),
                     'hours': round((d.get('minutes') or 0) / 60.0, 1)})
    n = sum(len(d['items']) for d in days)
    moved = sum(1 for d in days for r in d['items'] if r.get('moved_from'))
    ctx.update({'days': days, 'planned': n, 'moved': moved,
                'unfit': res.get('unfit') or [],
                'notes': res.get('notes') or [],
                'total': n + len(res.get('unfit') or []),
                'note_count': len(res.get('notes') or []) +
                len(res.get('unfit') or []),
                'choices': [(d['iso'], d['day']) for d in days]})
    return _show(request, 'plan_review.html', 'plan_review.html', ctx)


@require_POST
@travel_view
def move(request, trip_id, plan_id):
    t = _trip(request, trip_id)
    tp = _plan(request, t, plan_id)
    if tp.status != 'ready':
        raise Http404
    try:
        pk = int(request.POST.get('place') or 0)
    except ValueError:
        pk = 0
    PL.move(tp, pk, (request.POST.get('day') or '')[:10])
    if request.headers.get('x-requested-with') == 'fetch':
        from django.http import JsonResponse
        return JsonResponse({'ok': True})
    return redirect(_url(request, 'plan_view', t.pk, tp.pk))


@require_POST
@travel_view
def accept(request, trip_id, plan_id):
    t = _trip(request, trip_id)
    tp = _plan(request, t, plan_id)
    if tp.status != 'ready':
        raise Http404
    PL.apply(tp, request.user)
    return redirect(_trip_url(request, t, 'itinerary') +
                    ('&' if _phone(request) else '?') + 'planned=%d' % tp.pk)


@require_POST
@travel_view
def undo(request, trip_id, plan_id):
    t = _trip(request, trip_id)
    tp = _plan(request, t, plan_id)
    if tp.status != 'applied':
        raise Http404
    back, kept = PL.undo(tp)
    url = _trip_url(request, t, 'itinerary')
    return redirect(url + ('&' if _phone(request) else '?') +
                    'undone=%d&kept=%d' % (back, len(kept)))


@require_POST
@travel_view
def discard(request, trip_id, plan_id):
    t = _trip(request, trip_id)
    tp = _plan(request, t, plan_id)
    if tp.status in ('working', 'ready', 'failed'):
        tp.status = 'discarded'
        tp.save(update_fields=['status', 'updated_at'])
    return redirect(_trip_url(request, t, 'wish'))
