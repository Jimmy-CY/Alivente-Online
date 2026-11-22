# -*- coding: utf-8 -*-
"""travel/receipt.py - RA12, 22 Nov 2026. A receipt photo to + Spending.

Demetri, 22 Nov: "I like 11 - Receipt photo to spending. The user should
have the option to manually capture or to take a photo." - "Let's not keep
the receipt photo."

Claude reads the total, the currency, the day and the shop's name from the
photo; the + Spending form comes back filled in, to check and Add. The
photo is read in memory and dropped - never saved (receipts can carry a
card's last digits).

Never from a test unless a test hands in its own client.
"""
import base64
import io
import logging
import os
import sys
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)
MODEL = os.environ.get('TRAVEL_RECEIPT_MODEL', 'claude-haiku-4-5')
BIGGEST = 12 * 1024 * 1024      # bytes a photo may be
SIDE = 1600                     # pixels on the long side sent to Claude
TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}


class LookupError_(Exception):
    pass


def off():
    """Never from a test."""
    return os.path.basename(sys.argv[0] or '').startswith('test_')


SYSTEM = (
    "You read a photo of a till receipt or bill. Give the TOTAL actually "
    "paid (after any discount, including service and tax), its currency as "
    "an ISO 4217 code (from the symbol, the words or the country), the date "
    "on it, and the shop's or restaurant's name. If something cannot be "
    "read, leave it empty - never guess a total.")

TOOL = {
    'name': 'record_receipt',
    'description': 'What the receipt says.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'total': {'type': 'string',
                      'description': 'e.g. 53.50 - digits and one dot'},
            'currency': {'type': 'string', 'description': 'e.g. EUR'},
            'date': {'type': 'string', 'description': 'YYYY-MM-DD or empty'},
            'merchant': {'type': 'string'},
        },
        'required': ['total', 'currency', 'date', 'merchant'],
    },
}


def prepare(data, content_type=''):
    """(media type, base64) small enough to send - JPEG at most SIDE px."""
    if not data:
        raise LookupError_('The photo was empty.')
    if len(data) > BIGGEST:
        raise LookupError_('The photo is too big (12 MB at most).')
    try:
        from PIL import Image, ImageOps
        im = Image.open(io.BytesIO(data))
        im = ImageOps.exif_transpose(im)
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        im.thumbnail((SIDE, SIDE))
        out = io.BytesIO()
        im.save(out, 'JPEG', quality=85)
        return 'image/jpeg', base64.b64encode(out.getvalue()).decode('ascii')
    except Exception:                                   # noqa: BLE001
        ct = (content_type or '').split(';')[0].strip().lower()
        if ct in TYPES:
            return ct, base64.b64encode(data).decode('ascii')
    raise LookupError_('That file could not be opened as a photo.')


def _client(client):
    if client is not None:
        return client
    if off():
        raise LookupError_('Not from a test.')
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise LookupError_('The Anthropic key is not set on the server.')
    import anthropic
    return anthropic.Anthropic(api_key=key, timeout=60.0, max_retries=1)


def call(media, b64, client=None):
    client = _client(client)
    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=300, system=SYSTEM, tools=[TOOL],
            tool_choice={'type': 'tool', 'name': 'record_receipt'},
            messages=[{'role': 'user', 'content': [
                {'type': 'image', 'source': {'type': 'base64',
                                             'media_type': media,
                                             'data': b64}},
                {'type': 'text', 'text': 'Read this receipt.'}]}])
    except Exception as e:                              # noqa: BLE001
        logger.warning('travel receipt: %s', e)
        raise LookupError_('Claude could not be reached (%s).'
                           % type(e).__name__)
    for block in getattr(msg, 'content', None) or []:
        if getattr(block, 'type', '') == 'tool_use' and \
                isinstance(getattr(block, 'input', None), dict):
            return block.input
    raise LookupError_('Nothing came back.')


def money(s):
    """'1.234,50' / '1,234.50' / '53.50' -> Decimal, or None."""
    s = ''.join(ch for ch in str(s or '') if ch.isdigit() or ch in '.,')
    if not s:
        return None
    if ',' in s and '.' in s:
        s = s.replace(',', '') if s.rfind('.') > s.rfind(',') else \
            s.replace('.', '').replace(',', '.')
    elif ',' in s:
        head, _, tail = s.rpartition(',')
        s = (head.replace(',', '') + '.' + tail) if len(tail) == 2 else \
            s.replace(',', '')
    try:
        v = Decimal(s).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
    return v if v > 0 else None


def read(data, content_type='', client=None):
    """{amount (Decimal or None), currency, date (ISO or ''), merchant}."""
    import datetime as dt
    media, b64 = prepare(data, content_type)
    got = call(media, b64, client)
    day = str(got.get('date') or '').strip()[:10]
    try:
        dt.date.fromisoformat(day)
    except ValueError:
        day = ''
    return {'amount': money(got.get('total')),
            'currency': str(got.get('currency') or '').strip().upper()[:3],
            'date': day,
            'merchant': str(got.get('merchant') or '').strip()[:120]}
