# -*- coding: utf-8 -*-
"""travel/gquota.py - RA09, 21 Nov 2026. Google's allowance, kept by
Alivente.

Google lets a project cap Places searches only per day (100 on the key's
project). Demetri: "In reality a monthly limit would work better for me" -
and a count of what is left, before a Suggest run.

  Counted   every Google Places search Alivente sends: each suggestion
            checked, each city centre, the key watch's rare retry.
  Allowance a month's (default 1,000 - about Google's free amount for
            these searches) and a day's (default 100 - Google's own cap);
            changed by a superuser under Travel > Google allowance.
  Used up   suggestions still come, unchecked on Google, until the next
            day or month; the Suggest page says so.
  Warning   one email in a month, to KEY_ALERT_EMAIL (else the first
            superuser), when 80% of the month's allowance is used.

The day and month are Cyprus time (the site's time zone). Never from a
test unless a test asks (every suite is a test_*.py script).
"""
import logging

logger = logging.getLogger(__name__)
WARN_AT = 80


def _today():
    from django.utils import timezone
    return timezone.localdate()


def allowance():
    from .models import GoogleAllowance
    row = GoogleAllowance.objects.filter(pk=1).first()
    if row is None:
        row, _ = GoogleAllowance.objects.get_or_create(pk=1)
    return row


def usage(today=None):
    """What is used and left, today and this month."""
    from django.db.models import Sum
    from .models import GoogleUse
    today = today or _today()
    a = allowance()
    first = today.replace(day=1)
    month = GoogleUse.objects.filter(day__gte=first, day__lte=today) \
        .aggregate(n=Sum('searches'))['n'] or 0
    row = GoogleUse.objects.filter(day=today).first()
    day = row.searches if row else 0
    return {
        'month_used': month, 'month_limit': a.per_month,
        'month_left': max(a.per_month - month, 0),
        'day_used': day, 'day_limit': a.per_day,
        'day_left': max(a.per_day - day, 0),
        'pct': int(month * 100 / a.per_month) if a.per_month else 100,
        'room': month < a.per_month and day < a.per_day,
        'month_out': month >= a.per_month,
        'day_out': day >= a.per_day,
    }


def has_room(today=None):
    """May Alivente ask Google now? A database that cannot answer never
    stops the checks."""
    try:
        return usage(today)['room']
    except Exception:                                   # noqa: BLE001
        logger.exception('google allowance')
        return True


def note(today=None, send=None):
    """Count one search; warn once a month at 80%."""
    from django.db.models import F
    from .models import GoogleUse
    today = today or _today()
    try:
        GoogleUse.objects.get_or_create(day=today)
        GoogleUse.objects.filter(day=today).update(
            searches=F('searches') + 1)
        warn(today, send=send)
    except Exception:                                   # noqa: BLE001
        logger.exception('google allowance count')


def warn(today=None, send=None):
    """One email in a month, once 80% of the month's allowance is used.
    True if sent."""
    from .models import GoogleAllowance
    today = today or _today()
    u = usage(today)
    tag = today.strftime('%Y-%m')
    if u['pct'] < WARN_AT:
        return False
    # One sender, however many workers notice at once.
    if not GoogleAllowance.objects.filter(pk=1).exclude(
            warned_month=tag).update(warned_month=tag):
        return False
    from django.core.mail import EmailMessage
    from pages import key_health as KH
    to = KH.recipient()
    if not to:
        return False
    body = '\n'.join([
        'Alivente has used %d of this month\'s %d Google Places searches '
        '(%d%%).' % (u['month_used'], u['month_limit'], u['pct']),
        '',
        'These are the Google checks on Suggest things to do: opening days, '
        'distance, rating and price. When the month\'s allowance is used '
        'up, suggestions still come, just not checked on Google, until the '
        '1st.',
        '',
        'To change the allowance: Travel > Google allowance (on the '
        'computer).', '', 'Alivente Online'])
    msg = EmailMessage(subject='Alivente Online - %d%% of this month\'s '
                       'Google searches used' % u['pct'],
                       body=body, to=[to])
    (send or (lambda m: m.send(fail_silently=True)))(msg)
    return True


# --------------------------------------------- the morning catch-up
AFTER_HOUR = 10       # Google's day starts at midnight Pacific: 10:00 here
SHARE = 2             # use at most half of the day's allowance


def daily_recheck(now=None):
    """RA09 - once a day, after Google's day has begun: check suggestions
    made while the allowance was used up, with at most half of today's
    allowance (the rest stays for new Suggest runs). Run by the key watch
    on Railway. Returns the number checked, or None when not its time."""
    from django.utils import timezone
    from .models import GoogleAllowance, Trip
    from . import gplaces as G
    from . import ideas as ID
    now = timezone.localtime(now or timezone.now())
    today = now.date()
    if now.hour < AFTER_HOUR or not G.key():
        return None
    # One worker, once a day.
    allowance()
    if not GoogleAllowance.objects.filter(pk=1).exclude(
            rechecked_on=today).update(rechecked_on=today):
        return None
    u = usage(today)
    limit = min(u['day_left'] // SHARE, u['month_left'])
    trips = Trip.objects.filter(ideas__checked=False,
                                ideas__state='').distinct()
    if limit <= 0 or not trips.exists():
        return 0
    used, done = ID.recheck(list(trips), limit, today)
    logger.info('travel ideas checked later: %d (%d searches)', done, used)
    return done
