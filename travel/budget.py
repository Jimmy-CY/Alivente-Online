# -*- coding: utf-8 -*-
"""travel/budget.py - RA05, 19 Nov 2026. A trip's daily spending budget,
its spending, and who may see the money.

Demetri, 19 Nov: "What if our budget didn't include budgeting for Hotel,
Car Rental and Flights. These were just actuals that came in from the
Booking and contributed to the costs. Then we only had the ability to set
a budget for total holiday spend (which would be a calculation based on
average daily spend). Then it keeps track of my actual daily spend vs. the
budgeted one and shows me if I am ahead or behind the schedule. Obviously
these daily spends get added to the trip costs so that I can analyse my
complete trip costs. Also I can see where I have spent more on a day";
"Let's have both options - Add Total and calculate daily or vice versa";
restaurant meals are added by hand, booked activity tickets stay with the
bookings; and: "shared travellers should be able to see the budget and the
costs, but should not be able to add spending" - when the owner shares
them at all.

  The budget   a day's or the holiday's, in euros (Trip.budget_by); the
               other is worked out from the trip's days.
  Planned      a day's budget for every day so far, today counted.
  Ahead        spent less than planned; Behind - more.
  To go        what is left over the days after today: what a day keeps
               you on budget.
"""
import datetime as dt
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal('0')
CENT = Decimal('0.01')
ONE = Decimal('1')


# ------------------------------------------------------- who sees money
def money_ok(trip, user):
    """The owner always; the people it is shared with only when the owner
    shares the costs and budget."""
    return trip.owner_id == user.id or bool(trip.share_money)


def can_spend(trip, user):
    """Only the owner adds spending or sets the budget."""
    return trip.owner_id == user.id


def hide(trip, user, bookings):
    """Blank the costs on these (already shaped) bookings for someone who
    may not see them. True when the money may be shown. The blanked
    objects refuse to be saved (Booking.save)."""
    if money_ok(trip, user):
        return True
    for b in bookings:
        b.amount = b.amount_eur = b.paid_amount = b.fx_rate = None
        b.pay_by = None
        b.eur_label = b.orig_label = ''
        b._money_hidden = True
    return False


# -------------------------------------------------------------- spending
def convert(s):
    """Fill a Spend's amount_eur at the ECB rate for its day (not saved)."""
    from . import fx
    if s.currency == 'EUR':
        s.amount_eur, s.fx_rate = s.amount, None
        return s
    rate = fx.rate_for(s.day, s.currency)
    s.fx_rate = rate
    s.amount_eur = (s.amount / rate).quantize(CENT, ROUND_HALF_UP) \
        if rate else None
    return s


def convert_pending(spends, limit=3):
    done = 0
    for s in spends:
        if done >= limit:
            break
        if s.amount_eur is None:
            convert(s)
            done += 1
            if s.amount_eur is not None:
                s.save(update_fields=['amount_eur', 'fx_rate'])


def eur(v):
    from .views import eur as E
    return E(v)


def whole(v):
    """€1,234 - budgets read in whole euros."""
    return eur(v.quantize(ONE, ROUND_HALF_UP)) if v is not None else ''


def trip_days(start, end):
    if not start:
        return 0
    return ((end or start) - start).days + 1


def amounts(trip, days):
    """(a day, the holiday) in euros, or (None, None) with no budget."""
    if trip.budget is None:
        return None, None
    if trip.budget_by == 'total':
        total = trip.budget
        day = (total / days).quantize(CENT, ROUND_HALF_UP) if days else None
    else:
        day = trip.budget
        total = day * days if days else None
    return day, total


def summary(trip, spends, start, end, today=None):
    """Everything the budget card and the day chart show."""
    today = today or dt.date.today()
    days = trip_days(start, end)
    per_day, total = amounts(trip, days)
    by_day = {}
    pending = 0
    for s in spends:
        if s.amount_eur is None:
            pending += 1
            continue
        by_day[s.day] = by_day.get(s.day, ZERO) + s.amount_eur
    spent = sum(by_day.values(), ZERO)
    when = 'before' if start and today < start else (
        'after' if end and today > end else ('on' if start else 'none'))
    elapsed = {'before': 0, 'after': days, 'on': (today - start).days + 1
               if start else 0, 'none': 0}[when]
    to_go = days - elapsed
    planned = per_day * elapsed if per_day is not None else None
    ahead = planned - spent if planned is not None else None
    left = total - spent if total is not None else None
    keep = None
    if left is not None and to_go > 0 and left > 0:
        keep = (left / to_go).quantize(ONE, ROUND_HALF_UP)
    # Each day of the trip, with any spending outside it too.
    chart = []
    all_days = []
    if start:
        all_days = [start + dt.timedelta(days=i) for i in range(days)]
    for d in sorted(set(by_day) - set(all_days)):
        all_days.append(d)
    all_days.sort()
    top = max([by_day.get(d, ZERO) for d in all_days] +
              [per_day or ZERO]) or ONE
    for d in all_days:
        v = by_day.get(d, ZERO)
        chart.append({
            'day': d, 'eur': v, 'label': whole(v) if v else '',
            'pct': int(v / top * 100), 'today': d == today,
            'future': d > today,
            # RA06 - a day of the trip so far with nothing recorded.
            'empty': not v and d <= today and start is not None and
            start <= d <= (end or start),
            'over': per_day is not None and v > per_day,
            'over_by': whole(v - per_day) if per_day is not None and
            v > per_day else ''})
    # RA06, 19 Nov 2026 - days so far with no spending recorded (Demetri,
    # on "Under budget, €780" for a trip with one day filled in: "What is
    # it actually telling us?").
    so_far = [c for c in chart if not c['future'] and start and
              start <= c['day'] <= (end or start)]
    empty = [c for c in so_far if c['empty']]
    return {
        'empty_days': len(empty), 'days_so_far': len(so_far),
        'set': trip.budget is not None, 'by': trip.budget_by,
        'per_day': per_day, 'per_day_label': whole(per_day),
        'total': total, 'total_label': whole(total), 'days': days,
        'when': when, 'elapsed': elapsed, 'to_go': to_go,
        'spent': spent, 'spent_label': whole(spent) or '€0',
        'avg_label': whole(spent / elapsed) if elapsed and spent else '',
        'planned': planned, 'planned_label': whole(planned) or '€0',
        'ahead': ahead is not None and ahead >= 0,
        'gap_label': whole(abs(ahead)) if ahead is not None else '',
        'left': left, 'left_label': whole(abs(left)) if left is not None
        else '', 'over': left is not None and left < 0,
        'keep_label': whole(keep) if keep else '',
        'pct': min(int(spent / total * 100), 100) if total else 0,
        'line_pct': int(per_day / top * 100) if per_day else 0,
        'today_spent': by_day.get(today, ZERO),
        'today_label': whole(by_day.get(today, ZERO)) or '€0',
        'today_over': per_day is not None and
        by_day.get(today, ZERO) > per_day,
        'chart': chart, 'pending': pending,
        'show_chart': bool(per_day is not None or by_day)}


def spend_days(spends, per_day=None):
    """Spending by day, the latest first: [{day, rows, label, over}]."""
    out = {}
    for s in spends:
        out.setdefault(s.day, []).append(s)
    rows = []
    for d in sorted(out, reverse=True):
        tot = sum((s.amount_eur or ZERO) for s in out[d])
        for s in out[d]:
            s.eur_label = eur(s.amount_eur) if s.amount_eur is not None \
                else 'rate pending'
            s.orig_label = '' if s.currency == 'EUR' else \
                '%s %s' % ('{:,.2f}'.format(s.amount), s.currency)
        rows.append({'day': d, 'rows': out[d], 'label': eur(tot) or '€0',
                     'over': per_day is not None and tot > per_day,
                     'over_by': whole(tot - per_day)
                     if per_day is not None and tot > per_day else ''})
    return rows
