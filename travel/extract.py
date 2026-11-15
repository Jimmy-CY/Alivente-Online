# -*- coding: utf-8 -*-
"""travel/extract.py - TR-2, 15 Nov 2026. Claude reads a booking email.

One call per email. The email's text, any structured booking data the
sender put in it (JSON-LD), an Apple Wallet pass if there was one, and the
PDF and picture attachments go in; a list of bookings comes back through a
tool whose schema IS the Booking model's fields - so the answer is checked
by shape before any of it is used.

Tested on 15 Nov 2026 against seven of the family's real emails (Cyprus
Airways booking and boarding pass, Ryanair, three Booking.com hotels,
Booking.com Cars): every field the app keeps was there.

WHAT IS NEVER KEPT (Demetri's rule): a PIN, any card digits, and the
traveller's own email address or phone number. The prompt says so, and
clean() drops anything that looks like them on the way out regardless.

The model is read once, from TRAVEL_AI_MODEL, with a current default - the
census in test_ai_models.py checks it.
"""
import base64
import datetime as dt
import json
import logging
import os
import re
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

MODEL = os.environ.get('TRAVEL_AI_MODEL', 'claude-sonnet-4-6')
MAX_TOKENS = 4000
MAX_DOCS = 4
MAX_SEND = 22 * 1024 * 1024         # the request stays under 32 MB


class ExtractError(Exception):
    """Reading failed; the message says why, in words a person can use."""


KINDS = ['flight', 'stay', 'car', 'train', 'ferry', 'transfer', 'activity',
         'other']

BOOKING = {
    'type': 'object',
    'properties': {
        'kind': {'type': 'string', 'enum': KINDS},
        'title': {'type': 'string', 'description':
                  'Short name: "Cyprus Airways CY 326", "PAREA Athens", '
                  '"Enterprise car hire Dublin".'},
        'provider': {'type': 'string', 'description':
                     'Who it is with: the airline, hotel or company (and '
                     'the site booked through in brackets if different).'},
        'reference': {'type': 'string', 'description':
                      'The booking reference / confirmation number / PNR. '
                      'Never a PIN.'},
        'segment': {'type': 'string', 'description':
                    'For one of several parts under one reference: the '
                    'flight or train number ("CY 326"), else "LCA-ATH". '
                    'Empty for a single hotel or car.'},
        'status': {'type': 'string',
                   'enum': ['confirmed', 'changed', 'cancelled']},
        'boarding_pass': {'type': 'boolean', 'description':
                          'True if this email is a boarding pass / '
                          'check-in confirmation for this flight.'},
        'start_date': {'type': 'string', 'description': 'YYYY-MM-DD'},
        'start_time': {'type': 'string', 'description':
                       'HH:MM local time at the place'},
        'end_date': {'type': 'string', 'description': 'YYYY-MM-DD'},
        'end_time': {'type': 'string', 'description': 'HH:MM'},
        'from_place': {'type': 'string', 'description':
                       'Departure airport/station/pick-up, e.g. '
                       '"Larnaca (LCA)".'},
        'to_place': {'type': 'string'},
        'address': {'type': 'string', 'description':
                    'Street address of the hotel / pick-up desk.'},
        'phone': {'type': 'string', 'description':
                  "The provider's phone number. Never the traveller's."},
        'link': {'type': 'string', 'description':
                 'The manage-booking link, if there is one.'},
        'details': {'type': 'string', 'description':
                    'A few short lines worth having on the day: seats, '
                    'baggage, room type, board, check-in times, car class, '
                    'terminal, gate, fare breakdown.'},
        'currency': {'type': 'string', 'description': 'ISO code, e.g. EUR'},
        'amount': {'type': 'number', 'description':
                   'Total price. For several parts under one reference put '
                   'it on the FIRST part only.'},
        'paid': {'type': 'string', 'enum': ['paid', 'part', 'due', '']},
        'paid_amount': {'type': 'number', 'description':
                        'Paid so far, when part paid.'},
        'pay_by': {'type': 'string', 'description':
                   'YYYY-MM-DD the balance is due'},
        'cancel_until': {'type': 'string', 'description':
                         'YYYY-MM-DD free cancellation ends'},
        'travellers': {'type': 'array', 'items': {'type': 'string'},
                       'description': 'Full names of the people travelling.'},
        'city': {'type': 'string', 'description':
                 'The destination city of this part.'},
        'country': {'type': 'string', 'description':
                    'The destination country, in English.'},
    },
    'required': ['kind', 'title'],
}

TOOL = {
    'name': 'record_bookings',
    'description': 'Record every travel booking in the email.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'is_travel': {'type': 'boolean', 'description':
                          'False if the email holds no travel booking '
                          '(an advert, a newsletter, a receipt for '
                          'something else).'},
            'bookings': {'type': 'array', 'items': BOOKING},
        },
        'required': ['is_travel', 'bookings'],
    },
}

SYSTEM = """You read travel booking emails for a family's trip planner and \
record each booking with the record_bookings tool.

- One entry per thing booked. A return flight is two entries (one per \
flight) with the same reference and their own segment; a hotel is one; a \
car hire is one.
- Copy dates and times exactly as local times. Dates as YYYY-MM-DD, times \
as HH:MM. Never invent a value: leave out what the email does not say.
- If the email is a change, give the booking as it now stands and set \
status "changed". If it is a cancellation, set status "cancelled".
- A boarding pass or check-in confirmation: set boarding_pass true and \
fill seat, gate, terminal and boarding time in details.
- Amount is the total price in the currency charged. paid is "paid" if \
fully prepaid, "part" if a deposit was taken (paid_amount = deposit), \
"due" if it is paid later (at the hotel, at the desk).
- NEVER record a PIN or security code, any card number or card digits, \
or the traveller's own email address or phone number - anywhere, \
including details.
- The email may be forwarded: read the forwarded booking, not the \
forwarding note."""


def _text_block(info):
    parts = ['Subject: %s' % info['subject'], 'From: %s' % info['from']]
    if info.get('date'):
        parts.append('Date: %s' % info['date'].isoformat())
    if info.get('ld'):
        parts.append('Structured booking data in the email (JSON-LD):\n' +
                     '\n'.join(info['ld']))
    for e in info.get('extra') or []:
        parts.append(e)
    parts.append('The email:\n' + (info.get('body') or '(no text)'))
    return '\n\n'.join(parts)


def content(info):
    """The message content for one email: text first, then documents."""
    blocks = [{'type': 'text', 'text': _text_block(info)}]
    sent = 0
    n = 0
    for f in info.get('files') or []:
        if n >= MAX_DOCS:
            break
        if f['type'] == 'application/pdf':
            kind = 'document'
        elif f['type'] in ('image/jpeg', 'image/png', 'image/gif',
                           'image/webp'):
            kind = 'image'
        else:
            continue
        size = len(f['data']) * 4 // 3
        if sent + size > MAX_SEND:
            continue
        sent += size
        n += 1
        blocks.append({'type': kind, 'source': {
            'type': 'base64', 'media_type': f['type'],
            'data': base64.b64encode(f['data']).decode('ascii')}})
    return blocks


def call(info, client=None):
    """Ask Claude. Returns the tool input: {is_travel, bookings}."""
    if client is None:
        key = os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            raise ExtractError('The Anthropic key is not set on the server '
                               '(ANTHROPIC_API_KEY).')
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=120.0,
                                     max_retries=2)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            tools=[TOOL],
            tool_choice={'type': 'tool', 'name': 'record_bookings'},
            messages=[{'role': 'user', 'content': content(info)}],
        )
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel extract: %s', e)
        raise ExtractError('Claude could not be reached (%s).'
                           % type(e).__name__)
    for block in getattr(msg, 'content', None) or []:
        if getattr(block, 'type', '') == 'tool_use':
            data = getattr(block, 'input', None)
            if isinstance(data, dict):
                return data
    raise ExtractError('Claude did not return the bookings.')


# ---------------------------------------------------------------- cleaning
CARD = re.compile(r'\b(?:\d[ -]?){13,19}\b')
ENDING = re.compile(r'(?i)(card|visa|mastercard|amex)[^\n]{0,30}?\b\d{4}\b')
PIN = re.compile(r'(?i)\b(pin|security code|pin code)\b[^\n]*')
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def _date(v):
    try:
        return dt.date.fromisoformat(str(v)[:10]).isoformat()
    except (TypeError, ValueError):
        return ''


def _time(v):
    m = re.match(r'^\s*(\d{1,2}):(\d{2})', str(v or ''))
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        return ''
    return '%02d:%s' % (int(m.group(1)), m.group(2))


def _num(v):
    if v in (None, ''):
        return None
    try:
        d = Decimal(str(v)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None
    return str(d) if d >= 0 else None


def luhn(s):
    """A card number passes the Luhn check; an e-ticket number usually
    does not, and is kept."""
    d = [int(c) for c in s if c.isdigit()]
    tot = 0
    for i, x in enumerate(reversed(d)):
        if i % 2:
            x *= 2
            if x > 9:
                x -= 9
        tot += x
    return tot % 10 == 0


def scrub(text, own=()):
    """No PIN line, no card number or card ending, no email address, and
    none of the person's own phone numbers."""
    t = PIN.sub('', text or '')
    t = CARD.sub(lambda m: '' if luhn(m.group(0)) else m.group(0), t)
    t = ENDING.sub(lambda m: m.group(1), t)
    t = EMAIL.sub('', t)
    for p in own:
        if p:
            t = t.replace(p, '')
    return re.sub(r'[ \t]+\n', '\n', t).strip()


def clean(raw, own_phones=()):
    """The tool's answer, made safe and exact: known kinds, real dates and
    times, numbers as strings, text cut to the column sizes."""
    out = []
    for b in (raw or {}).get('bookings') or []:
        if not isinstance(b, dict):
            continue
        kind = b.get('kind') if b.get('kind') in KINDS else 'other'
        s = lambda k, n: scrub(str(b.get(k) or ''), own_phones)[:n]  # noqa
        cur = str(b.get('currency') or 'EUR').upper()[:3]
        status = b.get('status') if b.get('status') in (
            'confirmed', 'changed', 'cancelled') else 'confirmed'
        phone = s('phone', 40)
        if phone and any(p and p.replace(' ', '') in phone.replace(' ', '')
                         for p in own_phones):
            phone = ''
        link = str(b.get('link') or '')[:500]
        if not link.startswith('https://'):
            link = ''
        item = {
            'kind': kind, 'title': s('title', 160) or kind.title(),
            'provider': s('provider', 120),
            'reference': re.sub(r'\s+', '', s('reference', 60)),
            'segment': s('segment', 40), 'status': status,
            'boarding_pass': bool(b.get('boarding_pass')),
            'start_date': _date(b.get('start_date')),
            'start_time': _time(b.get('start_time')),
            'end_date': _date(b.get('end_date')),
            'end_time': _time(b.get('end_time')),
            'from_place': s('from_place', 120), 'to_place': s('to_place', 120),
            'address': s('address', 255), 'phone': phone, 'link': link,
            'details': s('details', 2000), 'currency': cur,
            'amount': _num(b.get('amount')),
            'paid': b.get('paid') if b.get('paid') in ('paid', 'part',
                                                       'due') else '',
            'paid_amount': _num(b.get('paid_amount')),
            'pay_by': _date(b.get('pay_by')),
            'cancel_until': _date(b.get('cancel_until')),
            'travellers': [scrub(str(x))[:80] for x in
                           (b.get('travellers') or [])[:9] if str(x).strip()],
            'city': s('city', 80), 'country': s('country', 60),
        }
        out.append(item)
    return out


def as_json(v):
    return json.loads(json.dumps(v, default=str))
