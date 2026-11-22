# -*- coding: utf-8 -*-
"""travel/views_budget.py - RA05, 19 Nov 2026. Set a trip's daily spending
budget; add and delete spending (travel/budget.py). The owner only - shared travellers
may see the budget and the costs when the owner shares them, but never
add spending (Demetri, 19 Nov)."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from . import budget as B
from . import fx
from .models import Spend
from .views import _date, _money, _trip, span, travel_view


def _phone(request):
    return (request.resolver_match.url_name or '').startswith('m_')


def _back(request, t):
    if _phone(request):
        return redirect('/travel/m/trip/%d/?tab=costs' % t.pk)
    return redirect('/travel/%d/costs/' % t.pk)


def _owned(request, trip_id):
    t = _trip(request, trip_id)
    if not B.can_spend(t, request.user):
        raise Http404
    return t


@travel_view
@require_POST
def budget_save(request, trip_id):
    """A day's budget or the holiday's (Demetri: "Let's have both options -
    Add Total and calculate daily or vice versa"); Remove clears it."""
    t = _owned(request, trip_id)
    P = request.POST
    if P.get('clear'):
        t.budget = None
        t.save(update_fields=['budget'])
        messages.success(request, 'Budget removed.')
        return _back(request, t)
    by = 'total' if P.get('by') == 'total' else 'day'
    amount = _money(P.get('budget_' + by))
    if not amount:
        messages.error(request, 'Type a day\'s budget or the holiday\'s.')
        return _back(request, t)
    t.budget, t.budget_by = amount, by
    t.save(update_fields=['budget', 'budget_by'])
    start, end = span(t, list(t.bookings.all()))
    day, total = B.amounts(t, B.trip_days(start, end))
    messages.success(request, 'Budget saved - %s a day, %s for the holiday.'
                     % (B.whole(day) or '?', B.whole(total) or '?')
                     if day is not None else 'Budget saved.')
    return _back(request, t)


def _read_spend(request, t, s):
    """Fill a Spend from the form; '' or the problem. RA07, 19 Nov 2026 -
    only a day of the trip (Demetri: "Should I be able to add Spending to
    days outside of my trip dates? I don't think so...")."""
    P = request.POST
    amount = _money(P.get('amount'))
    if not amount:
        return 'Type how much was spent.'
    start, end = span(t, list(t.bookings.all()))
    if not start:
        return ('The trip needs its dates first - add a booking, or set '
                'From and To under Edit trip.')
    end = end or start
    day = _date(P.get('day')) or B.default_day(start, end)
    if not B.inside(day, start, end):
        return 'Pick a day of the trip (%s - %s).' % (_d(start), _d(end))
    cur = (P.get('currency') or 'EUR').upper()
    s.amount, s.day = amount, day
    s.currency = cur if cur in fx.CURRENCIES else 'EUR'
    s.what = (P.get('what') or '').strip()[:120]
    B.convert(s)
    return ''


def _d(day):
    return '%s %d %s' % (day.strftime('%a'), day.day, day.strftime('%b'))


@travel_view
@require_POST
def spend_add(request, trip_id):
    t = _owned(request, trip_id)
    s = Spend(trip=t, added_by=request.user)
    problem = _read_spend(request, t, s)
    if problem:
        messages.error(request, problem)
        return _back(request, t)
    s.save()
    messages.success(request, '%s added to daily spending.' % (
        B.eur(s.amount_eur) if s.amount_eur is not None else
        '%s %s' % (s.amount, s.currency)))
    return _back(request, t)


@travel_view
@require_POST
def spend_edit(request, spend_id):
    """RA07 - change a spending entry's amount, currency, day or note."""
    s = get_object_or_404(Spend.objects.select_related('trip'), pk=spend_id)
    t = _owned(request, s.trip_id)
    problem = _read_spend(request, t, s)
    if problem:
        messages.error(request, problem)
        return _back(request, t)
    s.save()
    messages.success(request, 'Spending saved.')
    return _back(request, t)


@travel_view
@require_POST
def spend_delete(request, spend_id):
    s = get_object_or_404(Spend.objects.select_related('trip'), pk=spend_id)
    t = _owned(request, s.trip_id)
    s.delete()
    messages.success(request, 'Spending deleted.')
    return _back(request, t)


# ------------------------------------------------------------- the phone
@travel_view
def m_spend_form(request, trip_id, spend_id=None):
    """+ Spending on the phone: the amount first, euros and today already
    there (Demetri: "+Spending should default to Euros, today's date, and
    optional note blank - for quick entry"). RA07 - only the trip's days,
    and the same page changes one already added."""
    from .phone import page
    t = _owned(request, trip_id)
    s = get_object_or_404(Spend, pk=spend_id, trip=t) if spend_id else None
    start, end = span(t, list(t.bookings.all()))
    return page(request, 'travel/m/spend.html', {
        'trip': t, 'tab': 'trips', 'currencies': fx.CURRENCIES, 's': s,
        'today': (s.day if s else B.default_day(start, end)),
        'trip_start': start, 'trip_end': end or start})


@travel_view
def m_budget_form(request, trip_id):
    from .phone import page
    t = _owned(request, trip_id)
    start, end = span(t, list(t.bookings.all()))
    return page(request, 'travel/m/budget.html', {
        'trip': t, 'tab': 'trips', 'days': B.trip_days(start, end),
        'bud': B.summary(t, [], start, end)})


# ------------------------------------------------ RA09: Google allowance
@travel_view
def google_allowance(request):
    """RA09, 21 Nov 2026 - a superuser sets how many Google searches
    Alivente may make in a month and in a day (travel/gquota.py)."""
    from django.shortcuts import render
    from . import gquota
    if not request.user.is_superuser:
        raise Http404
    a = gquota.allowance()
    if request.method == 'POST':
        def whole(v, lo, hi):
            try:
                n = int(str(v).replace(',', '').strip())
            except (TypeError, ValueError):
                return None
            return n if lo <= n <= hi else None
        m = whole(request.POST.get('per_month'), 0, 100000)
        d = whole(request.POST.get('per_day'), 0, 10000)
        if m is None or d is None:
            messages.error(request, 'Type whole numbers: a month up to '
                           '100,000, a day up to 10,000.')
        else:
            a.per_month, a.per_day = m, d
            a.save(update_fields=['per_month', 'per_day'])
            messages.success(request, 'Google allowance saved - %d a month, '
                             '%d a day.' % (m, d))
            return redirect('travel:google_allowance')
    try:                                # RA10 - who used them
        used = gquota.used_by()
    except Exception:                                   # noqa: BLE001
        used = {'today': [], 'month': []}
    return render(request, 'travel/google_allowance.html', {
        'a': a, 'gq': gquota.usage(), 'used': used,
        'back': request.GET.get('back') or '/travel/'})


# ------------------------------------------------- RA12 - a receipt photo
@travel_view
@require_POST
def spend_receipt(request, trip_id):
    """RA12, 22 Nov 2026 - + Spending from a receipt photo (Demetri: "The
    user should have the option to manually capture or to take a photo").
    Claude reads it; the form comes back filled in to check and Add. The
    photo is never kept ("Let's not keep the receipt photo")."""
    from django.shortcuts import render
    from . import receipt
    t = _owned(request, trip_id)
    f = request.FILES.get('photo')
    start, end = span(t, list(t.bookings.all()))
    if not start:
        messages.error(request, 'The trip needs its dates first.')
        return _back(request, t)
    end = end or start
    try:
        if f is None:
            raise receipt.LookupError_('Take or choose a photo first.')
        got = receipt.read(f.read(), getattr(f, 'content_type', ''))
    except Exception as e:                              # noqa: BLE001
        messages.error(request, 'The receipt could not be read - %s Type '
                       'it in instead.' % (str(e).rstrip('.') + '.'
                                           if str(e) else ''))
        if _phone(request):
            return redirect('travel:m_spend', trip_id=t.pk)
        return _back(request, t)
    finally:
        if f is not None:
            f.close()
    notes = []
    day = _date(got['date']) if got['date'] else None
    if day and not B.inside(day, start, end):
        notes.append('The receipt is dated %s, outside the trip - pick the '
                     'day.' % _d(day))
        day = None
    cur = got['currency'] if got['currency'] in fx.CURRENCIES else 'EUR'
    if got['currency'] and got['currency'] != cur:
        notes.append('%s cannot be converted here - pick the currency.'
                     % got['currency'])
    if got['amount'] is None:
        notes.append('The total could not be read - type it.')
    pre = {'amount': got['amount'] or '', 'currency': cur,
           'day': day or B.default_day(start, end), 'what': got['merchant'],
           'notes': notes, 'read': got['amount'] is not None}
    if _phone(request):
        from .phone import page
        return page(request, 'travel/m/spend.html', {
            'trip': t, 'tab': 'trips', 'currencies': fx.CURRENCIES,
            's': None, 'pre': pre, 'today': pre['day'],
            'trip_start': start, 'trip_end': end})
    return render(request, 'travel/spend_receipt.html', {
        'trip': t, 'pre': pre, 'currencies': fx.CURRENCIES,
        'trip_start': start, 'trip_end': end})


# ------------------------------------------------- RA12 - Good to know
@travel_view
@require_POST
def city_refresh(request, trip_id, info_id):
    """Refresh a city's Good to know card: Claude writes it again."""
    from . import cityinfo
    from .models import CityInfo
    t = _trip(request, trip_id)
    row = get_object_or_404(CityInfo, pk=info_id)
    cityinfo.refresh(row)
    messages.success(request, 'Good to know for %s is being written again '
                     '- it shows in a moment.' % row.city)
    if (request.POST.get('phone') or '') == '1':
        return redirect('/travel/m/trip/%d/?tab=info' % t.pk)
    return redirect('travel:trip_info', trip_id=t.pk)
