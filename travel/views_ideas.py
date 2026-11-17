"""TR-12, 17 Nov 2026 - Suggest things to do: the pages.

setup    which cities (from the hotel stays, all ticked; + Another city for
         a day trip) and what you like (Demetri: "Museums, parks,
         Neighbourhoods, streets, Buildings, Tourist Attractions, etc.").
ideas    while they are found, then the suggestions to read and tick
         (Demetri: "The user must then read up on these (short blurb) and
         then tick which ones they want to add to their Things to Do").
add      the ticked ones into Things to do, each looked up on the web.
hide     Not interested - and Show them, to bring one back.
more     Show me more for one city - never repeating one.
The rules are in travel/ideas.py.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import ideas as ID
from .models import Idea
from .views import span, travel_view
from .views_places import _trip


def _phone(request):
    return request.resolver_match.url_name.startswith('m_')


def _show(request, name, ctx):
    if _phone(request):
        from .phone import page
        return page(request, 'travel/m/%s' % name, ctx)
    return render(request, 'travel/%s' % name, ctx)


def _url(request, name, *args):
    return reverse('travel:%s%s' % ('m_' if _phone(request) else '', name),
                   args=args)


def _wish_url(request, t):
    if _phone(request):
        return reverse('travel:m_trip', args=[t.pk]) + '?tab=wish'
    return reverse('travel:trip_wishlist', args=[t.pk])


def _base(request, t):
    return {'trip': t, 'tab': 'wish', 'sub': 'wish',
            'back': _wish_url(request, t), 'per_city': ID.PER_CITY,
            'setup_url': _url(request, 'ideas_setup', t.pk),
            'add_url': _url(request, 'ideas_add', t.pk),
            'hide_url': _url(request, 'ideas_hide', t.pk),
            'more_url': _url(request, 'ideas_more', t.pk)}


def _city_rows(t, answers):
    bookings = list(t.bookings.all())
    start, end = span(t, bookings)
    rows = []
    chosen = set(c.lower() for c in answers.get('cities') or [])
    for c in ID.cities_of(t, bookings):
        c = dict(c)
        c['on'] = not chosen or c['name'].lower() in chosen
        rows.append(c)
    names = set(c['name'].lower() for c in rows)
    extra = [x for x in answers.get('cities') or [] if x.lower() not in
             names]
    return rows, extra, start, end


@travel_view
def setup(request, trip_id):
    t = _trip(request, trip_id)
    last = ID.last_answers(t)
    if request.method == 'POST':
        P = request.POST
        cities = [c.strip()[:80] for c in P.getlist('city') if c.strip()]
        for c in (P.get('other') or '').replace(';', ',').split(','):
            c = ' '.join(c.split())[:80]
            if c and c.lower() not in [x.lower() for x in cities]:
                cities.append(c)
        answers = {
            'cities': cities[:8],
            'interests': [k for k in P.getlist('interest')
                          if k in ID.LABEL] or list(ID.DEFAULT),
            'style': P.get('style') if P.get('style') in dict(
                (k, n) for k, n, _s in ID.STYLES) else 'mix',
            'extra': ' '.join((P.get('extra') or '').split())[:200],
        }
        if not answers['cities']:
            messages.error(request, 'Tick a city, or type one under '
                                    '+ Another city.')
            return redirect(_url(request, 'ideas_setup', t.pk))
        job = ID.begin(t, request.user, answers)
        ID.start(job)
        return redirect(_url(request, 'ideas', t.pk))
    rows, extra, start, end = _city_rows(t, last)
    on = set(last.get('interests') or ID.DEFAULT)
    ctx = _base(request, t)
    ctx.update({
        'cities': rows, 'extra_cities': extra,
        'interests': [{'key': k, 'name': n, 'on': k in on}
                      for k, n, _w in ID.INTERESTS],
        'styles': ID.STYLES, 'style': last.get('style') or 'mix',
        'extra': last.get('extra') or '',
        'again': bool(last),
        'trip_start': start, 'trip_end': end})
    return _show(request, 'ideas_setup.html', ctx)


@travel_view
def ideas(request, trip_id):
    t = _trip(request, trip_id)
    ctx = _base(request, t)
    job = ID.open_run(t)
    if job is not None:
        prog = job.progress or {}
        ctx.update({'job': job, 'rows': [
            {'city': c, 'state': s, 'count': t.ideas.filter(
                run=job, city=c).count()} for c, s in prog.items()]})
        return _show(request, 'ideas_working.html', ctx)
    all_ideas = list(t.ideas.all())
    if not all_ideas and not t.idea_runs.exists():
        return redirect(_url(request, 'ideas_setup', t.pk))
    show_hidden = request.GET.get('hidden') == '1'
    city = request.GET.get('city') or ''
    ticked = set(x for x in (request.GET.get('t') or '').split(',')
                 if x.isdigit())
    order = []
    for i in all_ideas:
        if i.city not in order:
            order.append(i.city)
    shown = [i for i in all_ideas if i.state == '']
    # TR-14 (Demetri, 17 Nov: "it is not clear which ones are new? Maybe we
    # should always mark the new ones added with a new label each time"):
    # what the latest Show me more brought is marked New - until the next.
    latest = t.idea_runs.first()
    fresh = latest.pk if latest and latest.more else None
    first_new = None
    for i in all_ideas:
        i.new = fresh is not None and i.run_id == fresh
        if i.new and i.state == '' and first_new is None:
            first_new = i.pk
    counts = [{'city': c, 'n': sum(1 for i in shown if i.city == c)}
              for c in order]
    groups = []
    for c in order:
        if city and c != city:
            continue
        mine = [i for i in all_ideas if i.city == c and (
            i.state == '' or (show_hidden and i.state == 'hidden'))]
        by = []
        for k, n, _w in ID.INTERESTS + [('', 'Other', '')]:
            these = [i for i in mine if (i.interest or '') == k or (
                k == '' and i.interest not in ID.LABEL)]
            for i in these:
                i.ticked = str(i.pk) in ticked
            if these:
                by.append({'name': n, 'ideas': these})
        groups.append({'city': c, 'by': by,
                       'n': sum(1 for i in mine if i.state == ''),
                       'added': sum(1 for i in all_ideas if i.city == c
                                    and i.state == 'added')})
    last = t.idea_runs.first()
    failed = []
    if last and last.progress:
        failed = [c for c, s in last.progress.items() if s == 'failed']
    ctx.update({
        'groups': groups, 'counts': counts, 'city': city,
        'hidden': sum(1 for i in all_ideas if i.state == 'hidden'),
        'show_hidden': show_hidden, 'left': len(shown),
        'failed': failed, 'error': last.error if last and failed else '',
        'saved': last.created_at if last else None,
        'ticked_n': len(ticked),
        'n_new': sum(1 for i in shown if i.new), 'first_new': first_new,
        'new_city': (latest.answers or {}).get('more') or
        next(iter(latest.progress or {}), '') if fresh else ''})
    return _show(request, 'ideas.html', ctx)


def _back(request, t, extra='', anchor=''):
    q = []
    c = request.POST.get('city_f') or ''
    if c:
        from urllib.parse import quote
        q.append('city=' + quote(c))
    if request.POST.get('hidden_f') == '1':
        q.append('hidden=1')
    keep = [x for x in request.POST.getlist('idea') if x.isdigit()]
    if keep:
        q.append('t=' + ','.join(keep))
    if extra:
        q.append(extra)
    return redirect(_url(request, 'ideas', t.pk) + ('?' + '&'.join(q)
                                                    if q else '') +
                    ('#' + anchor if anchor else ''))


@require_POST
@travel_view
def add(request, trip_id):
    t = _trip(request, trip_id)
    ids = [int(x) for x in request.POST.getlist('idea') if x.isdigit()]
    if not ids:
        messages.error(request, 'Tick the ones you want first.')
        return _back(request, t)
    n = ID.add(t, ids, request.user)
    return redirect(_wish_url(request, t) + ('&' if _phone(request) else
                                             '?') + 'added=%d' % n)


@require_POST
@travel_view
def hide(request, trip_id):
    t = _trip(request, trip_id)
    pk = request.POST.get('hide') or request.POST.get('unhide') or ''
    i = get_object_or_404(Idea.objects.filter(trip=t), pk=int(pk)) \
        if pk.isdigit() else None
    if i is None:
        return _back(request, t)
    if request.POST.get('hide') and i.state == '':
        i.state = 'hidden'
    elif request.POST.get('unhide') and i.state == 'hidden':
        i.state = ''
    i.save(update_fields=['state'])
    return _back(request, t)


@require_POST
@travel_view
def more(request, trip_id):
    t = _trip(request, trip_id)
    city = (request.POST.get('more') or '').strip()[:80]
    if not city or not t.ideas.filter(city=city).exists():
        return _back(request, t)
    answers = ID.last_answers(t) or {'interests': list(ID.DEFAULT),
                                     'style': 'mix'}
    job = ID.begin(t, request.user, answers, more=city)
    ID.start(job)
    # TR-14 (Demetri, 17 Nov: "the ones I ticked must remain ticked, even
    # though new ones are added"): back with what was ticked, at the new.
    return _back(request, t, anchor='new')
