# -*- coding: utf-8 -*-
"""travel/fx.py - TR-1, 15 Nov 2026. Euro conversion at the ECB rate.

Demetri, 15 Nov: keep the original currency, and show it in euros too. The
rate is the European Central Bank's reference rate for the day, read
through Frankfurter (a free service that republishes it), and STORED -
FxRate for the day, and on the booking the rate and day it was converted
at - so a total never moves when a later rate comes out. A weekend or a
holiday gives the last working day's rate, as the ECB publishes none.

When the service cannot be reached the euro amount stays empty and the
page says the rate is pending; the next look at the trip tries again
(convert_pending). A euro amount typed from the card statement is never
replaced.
"""
import datetime as dt
import json
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

from .models import FxRate

# The currencies the ECB publishes a reference rate for, euro first.
CURRENCIES = ['EUR', 'GBP', 'USD', 'CHF', 'SEK', 'NOK', 'DKK', 'CZK',
              'HUF', 'PLN', 'RON', 'BGN', 'ISK', 'TRY', 'ZAR', 'AUD', 'CAD',
              'NZD', 'JPY', 'CNY', 'HKD', 'SGD', 'KRW', 'INR', 'IDR', 'MYR',
              'PHP', 'THB', 'ILS', 'MXN', 'BRL']
URLS = ['https://api.frankfurter.dev/v1/%s?base=EUR&symbols=%s',
        'https://api.frankfurter.app/%s?from=EUR&to=%s']
TIMEOUT = 6
CENT = Decimal('0.01')


def fetch(day, currency):
    """The rate from the service, or None. Kept apart so tests replace it."""
    for url in URLS:
        try:
            req = urllib.request.Request(
                url % (day.isoformat(), currency),
                headers={'User-Agent': 'Alivente-Travel/1'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = json.loads(r.read().decode('utf-8'))
            value = (data.get('rates') or {}).get(currency)
            if value:
                return Decimal(str(value))
        except Exception:                                   # noqa: BLE001
            continue
    return None


def rate_for(day, currency):
    """Units of `currency` per euro on `day` (stored once found)."""
    if currency == 'EUR':
        return Decimal('1')
    day = min(day, dt.date.today())
    row = FxRate.objects.filter(day=day, currency=currency).first()
    if row:
        return row.rate
    value = fetch(day, currency)
    if value:
        FxRate.objects.update_or_create(day=day, currency=currency,
                                        defaults={'rate': value})
    return value


def convert(booking, today=None):
    """Fill booking.amount_eur (not saved). A typed euro amount stays."""
    if booking.eur_typed:
        return booking
    if booking.amount is None:
        booking.amount_eur = booking.fx_rate = None
        return booking
    if booking.currency == 'EUR':
        booking.amount_eur = booking.amount
        booking.fx_rate = None
        booking.fx_date = None
        return booking
    day = booking.fx_date or today or dt.date.today()
    rate = rate_for(day, booking.currency)
    booking.fx_date = day
    booking.fx_rate = rate
    booking.amount_eur = (booking.amount / rate).quantize(
        CENT, ROUND_HALF_UP) if rate else None
    return booking


def convert_pending(bookings, limit=5):
    """Try again for bookings still waiting for a rate. A few per look."""
    done = 0
    for b in bookings:
        if done >= limit:
            break
        if b.amount is not None and b.amount_eur is None and not b.eur_typed:
            convert(b)
            done += 1
            if b.amount_eur is not None:
                b.save(update_fields=['amount_eur', 'fx_rate', 'fx_date'])
