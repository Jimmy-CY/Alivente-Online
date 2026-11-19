# -*- coding: utf-8 -*-
"""travel/report.py - TR-4, 15 Nov 2026. A trip as a PDF.

Demetri, 15 Nov: "Can I have a PDF Report option for a trip. I must have
the option to generate a summarised or detailed PDF. Summarised is as we
see [on the trip page]. Detailed includes all of the information per
reservation. Then I need to have the ability to email, WhatsApp, etc.
(we can use our existing functionality)."

    /travel/<id>/pdf/?kind=summary    day by day, one line a booking, the
                                      places planned, the costs
    /travel/<id>/pdf/?kind=detailed   the same, then every booking in full

Rendered with xhtml2pdf, as the recipe PDF is; shown and shared through
the house PDF viewer (components/pdf_viewer.html: Download, and Share on
a phone - WhatsApp, Mail...). On the Travel phone app the PDF goes straight
to the phone's share sheet. Only people on the trip can open it.
"""
import datetime as dt

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.utils import timezone
from django.utils.text import slugify

from . import fx
from .models import trips_for
from .views import included, shape, span, totals, travel_view

KINDS = ('summary', 'detailed')


def plain(s):
    """The PDF's standard fonts have no arrows: "LCA -> ATH" reads fine."""
    return (s or '').replace('→', '->').replace('–', '-').replace(
        '—', '-').replace('’', "'").replace('‘', "'").replace(
        '“', '"').replace('”', '"').replace('…', '...')


def budget_for(t, start, end):
    from .budget import summary
    b = summary(t, list(t.spends.all()), start, end)
    return b if b['set'] else None


def context(t, kind, user=None):
    bs = list(t.bookings.prefetch_related('travellers', 'files', 'passes'))
    fx.convert_pending(bs, limit=5)
    bs = included([shape(b) for b in bs])
    # RA05, 19 Nov 2026 - no costs for someone they are not shared with.
    from .budget import hide
    show_money = hide(t, user, bs) if user is not None else True
    for b in bs:
        b.route = plain(b.route)
    start, end = span(t, bs)
    from .phone import itinerary
    pl = list(t.places.all())
    days = itinerary(t, bs, pl)
    if kind == 'summary':
        # As on the trip page: only the days with something starting.
        days = [(d, rows) for d, rows in days
                if any(getattr(r, 'is_place', False) or
                       getattr(r, 'what', '') == 'start' for r in rows)]
    undated = [b for b in bs if not b.start_date]
    return {
        'trip': t, 'kind': kind, 'start': start, 'end': end,
        'nights': (end - start).days if start and end else None,
        'days': days, 'undated': undated,
        'bookings': sorted(bs, key=lambda b: (b.start_date or dt.date.max,
                                              b.start_time or dt.time(0))),
        'wish': [p for p in pl if not p.day],
        # RA05 - the daily spending is part of the trip's costs.
        'money': totals(bs, list(t.spends.all())) if show_money
        else totals([]),
        'bud': budget_for(t, start, end) if show_money else None,
        'people': [t.owner] + list(t.shared_with.all()),
        'made': timezone.localtime(),
    }


@travel_view
def trip_pdf(request, trip_id):
    from xhtml2pdf import pisa  # local import, as recipe_pdf does
    t = get_object_or_404(trips_for(request.user), pk=trip_id)
    kind = request.GET.get('kind')
    if kind not in KINDS:
        kind = 'summary'
    html = get_template('travel/trip_pdf.html').render(context(t, kind, request.user))
    name = 'trip_%s_%s.pdf' % (slugify(t.name) or t.pk, kind)
    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="%s"' % name
    status = pisa.CreatePDF(plain(html), dest=resp, encoding='utf-8')
    if status.err:
        return HttpResponse('The trip PDF could not be made.', status=500)
    return resp
