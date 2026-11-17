"""travel/calendar_view.py - TR-14, 17 Nov 2026. The trips on a calendar.

Demetri, 17 Nov: "Would it make sense to have a monthly calendar view with
the trips being displayed on the calendar. It should default to today on
opening and then the user should the ability to scroll month and year?
The calendar should just be another view that the user can activate."
Decided: the trips as bars with a plane on the days you fly; a bar opens
the trip's itinerary; a month at a time.
"""
import calendar
import datetime as dt

# Eight colours that each carry white text (4.5:1 or better), told apart
# by lightness as well as hue.
COLOURS = ['#0F7480', '#B35400', '#5B4BB7', '#2E7D32', '#B0175A',
           '#1565C0', '#6D4C41', '#455A64']
MONTHS = [(i, calendar.month_name[i]) for i in range(1, 13)]


def month_of(text, today):
    """The month asked for ("2027-03"), else this one."""
    try:
        y, m = [int(x) for x in (text or '').split('-')[:2]]
        if 2000 <= y <= 2100 and 1 <= m <= 12:
            return dt.date(y, m, 1)
    except ValueError:
        pass
    return today.replace(day=1)


def _shift(first, n):
    m = first.month - 1 + n
    return dt.date(first.year + m // 12, m % 12 + 1, 1)


def flights_of(t):
    """The days this trip flies (cancelled flights left out)."""
    return {b.start_date for b in t.bookings.all()
            if b.kind == 'flight' and b.status != 'cancelled' and
            b.start_date}


def build(trips, first, today):
    """The month: its weeks (Monday first), each with its days and the
    trips across them as bars, stacked where they overlap."""
    dated = sorted([t for t in trips if t.start],
                   key=lambda t: (t.start, t.pk))
    colour = {t.pk: COLOURS[i % len(COLOURS)]
              for i, t in enumerate(sorted(trips, key=lambda t: t.pk))}
    weeks = []
    month_trips = []
    last = _shift(first, 1) - dt.timedelta(days=1)
    for week in calendar.Calendar(0).monthdatescalendar(first.year,
                                                        first.month):
        w0, w6 = week[0], week[-1]
        bars, lanes = [], []
        planes = {d: [] for d in week}
        for t in dated:
            end = t.end or t.start
            if end < w0 or t.start > w6:
                continue
            a, b = max(t.start, w0), min(end, w6)
            lane = 0
            while lane < len(lanes) and lanes[lane] >= a:
                lane += 1
            if lane == len(lanes):
                lanes.append(b)
            else:
                lanes[lane] = b
            bars.append({
                'trip': t, 'col': (a - w0).days + 1,
                'span': (b - a).days + 1, 'lane': lane + 2,
                'more_left': t.start < w0, 'more_right': end > w6,
                'colour': colour[t.pk], 'past': end < today})
            for d in flights_of(t):
                if w0 <= d <= w6:
                    planes[d].append(colour[t.pk])
        weeks.append({
            'days': [{'date': d, 'in_month': d.month == first.month,
                      'today': d == today, 'planes': planes[d]}
                      for d in week],
            'bars': bars, 'rows': max(1, len(lanes))})
    for t in dated:
        end = t.end or t.start
        if t.start <= last and end >= first:
            t.colour = colour[t.pk]
            t.cal_past = end < today
            month_trips.append(t)
    return {
        'first': first, 'weeks': weeks, 'trips': month_trips,
        'prev': _shift(first, -1).strftime('%Y-%m'),
        'next': _shift(first, 1).strftime('%Y-%m'),
        'this': today.strftime('%Y-%m'),
        'is_this': first == today.replace(day=1),
        'months': MONTHS,
        'years': list(range(min([first.year, today.year] +
                                [t.start.year for t in dated]) - 1,
                            max([first.year, today.year] +
                                [(t.end or t.start).year for t in dated])
                            + 3)),
        'undated': [t for t in trips if not t.start],
    }


def view_of(request):
    """'calendar' or 'list': asked for now, else as last chosen here."""
    v = request.GET.get('view')
    if v in ('list', 'calendar'):
        return v, True
    v = request.COOKIES.get('tv_view')
    return (v if v in ('list', 'calendar') else 'list'), False


def remember(response, view, asked):
    if asked:
        response.set_cookie('tv_view', view, max_age=365 * 24 * 3600,
                            samesite='Lax')
    return response
