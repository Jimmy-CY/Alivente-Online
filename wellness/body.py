# -*- coding: utf-8 -*-
"""wellness/body.py - WL-2, 30 Oct 2026. Trend weight.

THE HEADLINE IS THE TREND, NOT THE SCALE. Day to day a body swings by a
kilo or more with water, salt and food (the proposal's research; MacroFactor
does the same). So:

    1. Days between two weigh-ins are filled in a straight line.
    2. A weighted moving average runs over every day: each day the trend
       moves ALPHA of the way towards that day's weight. Recent days count
       most; one heavy morning moves it a tenth as much.
    3. The trend stops at the last weigh-in - it is never guessed forward.

Pure functions over {date: kg}, so the suite drives every rule without a
database.
"""
import datetime as dt
from decimal import Decimal

ALPHA = 0.1
ONE = dt.timedelta(days=1)


def daily(readings):
    """{date: kg} with the gaps filled in a straight line."""
    if not readings:
        return {}
    days = sorted(readings)
    out = {}
    for a, b in zip(days, days[1:]):
        va, vb = float(readings[a]), float(readings[b])
        span = (b - a).days
        for i in range(span):
            out[a + dt.timedelta(days=i)] = va + (vb - va) * i / span
    out[days[-1]] = float(readings[days[-1]])
    return out


def trend(readings):
    """{date: trend kg} from the first weigh-in to the last."""
    filled = daily(readings)
    out = {}
    t = None
    for d in sorted(filled):
        t = filled[d] if t is None else t + ALPHA * (filled[d] - t)
        out[d] = t
    return out


def change(tr, days):
    """Trend now minus trend `days` ago, or None without that history."""
    if not tr:
        return None
    last = max(tr)
    back = last - dt.timedelta(days=days)
    if back not in tr:
        return None
    return tr[last] - tr[back]


def weekly_rate(tr, window=14):
    """kg per week from a straight line through the last `window` days of
    the trend; None with fewer than 7 days."""
    if not tr:
        return None
    last = max(tr)
    pts = [(-(last - d).days, v) for d, v in tr.items()
           if (last - d).days < window]
    if len(pts) < 7:
        return None
    n = float(len(pts))
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    den = sum((x - mx) ** 2 for x, _ in pts)
    if not den:
        return None
    slope = sum((x - mx) * (y - my) for x, y in pts) / den
    return slope * 7


def pace(current, goal, rate, today):
    """The date the goal is reached at this rate, or None if the trend is
    flat or going the other way."""
    if current is None or goal is None or not rate:
        return None
    gap = float(goal) - current
    if gap == 0:
        return today
    if (gap > 0) != (rate > 0):
        return None
    weeks = gap / rate
    if weeks > 520:
        return None
    return today + dt.timedelta(days=int(round(weeks * 7)))


def progress(start, current, goal):
    """0..1 of the way from the first trend value to the goal."""
    if start is None or current is None or goal is None:
        return None
    total = float(goal) - start
    if total == 0:
        return 1.0
    return max(0.0, min(1.0, (current - start) / total))


def chart(readings, tr, days, width=320, height=150, pad=10):
    """SVG geometry for the last `days` days: raw dots and the trend line.
    Returns {'dots': path, 'line': path, 'lo', 'hi'} or None."""
    if not tr:
        return None
    last = max(tr)
    first = last - dt.timedelta(days=days - 1)
    pts = {d: v for d, v in tr.items() if d >= first}
    raw = {d: float(v) for d, v in readings.items() if d >= first}
    vals = list(pts.values()) + list(raw.values())
    lo, hi = min(vals), max(vals)
    if hi - lo < 1:
        mid = (hi + lo) / 2
        lo, hi = mid - 0.5, mid + 0.5
    span = max(1, days - 1)

    def x(d):
        return pad + (width - 2 * pad) * (d - first).days / span

    def y(v):
        return pad + (height - 2 * pad) * (hi - v) / (hi - lo)

    line = ''.join('%s%.1f %.1f' % ('M' if i == 0 else 'L', x(d), y(v))
                   for i, (d, v) in enumerate(sorted(pts.items())))
    dots = ''.join('M%.1f %.1fa2.6 2.6 0 1 0 5.2 0a2.6 2.6 0 1 0 -5.2 0'
                   % (x(d) - 2.6, y(v)) for d, v in sorted(raw.items()))
    return {'dots': dots, 'line': line, 'lo': lo, 'hi': hi,
            'w': width, 'h': height}


def kg(v):
    return None if v is None else Decimal('%.1f' % v)
