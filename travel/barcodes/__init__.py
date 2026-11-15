# -*- coding: utf-8 -*-
"""travel/barcodes - TR-3, 15 Nov 2026. A boarding pass's barcode, drawn.

The airline's barcode is text - for a flight, the IATA Bar Coded Boarding
Pass (BCBP) string "M1MANIAS/DIMITRIOS EABC123 ATHLCACY 0313 ..." - in one
of three symbologies. Stage 2 keeps the text and the symbology; this draws
it again as an SVG the gate scanner reads off the phone's screen, and
reads the flight, seat and passenger back out of the BCBP itself.

    aztec   - aztec.py, vendored (aztec_code_generator 0.12, MIT)
    pdf417  - pdf417/, vendored (pdf417gen 0.8.1, MIT)
    qr      - reportlab's own QR encoder, already installed

Pure Python, no new package. Checked by decoding each drawing with ZXing
(test_travel_three.py records the round trip).
"""
import datetime as dt
import re

FORMATS = ('aztec', 'pdf417', 'qr')


def matrix(text, fmt):
    """Rows of booleans, dark = True; None when it cannot be drawn."""
    fmt = (fmt or '').lower()
    try:
        if fmt == 'aztec':
            from .aztec import AztecCode
            return [[bool(v) for v in row] for row in AztecCode(text).matrix]
        if fmt == 'pdf417':
            from .pdf417 import encode
            rows = []
            for row in encode(text, columns=6, security_level=2):
                bits = ''.join(format(v, 'b') for v in row)
                rows.append([b == '1' for b in bits])
            return rows
        if fmt == 'qr':
            from reportlab.graphics.barcode import qr
            w = qr.QrCodeWidget(text, barLevel='M')
            w.qr.make()
            return [[bool(v) for v in row] for row in w.qr.modules]
    except Exception:                                   # noqa: BLE001
        return None
    return None


def svg(text, fmt, label='Boarding pass barcode'):
    """The barcode as inline SVG markup, or '' when it cannot be drawn.
    PDF417 rows are drawn three modules tall, as the standard asks."""
    m = matrix(text or '', fmt)
    if not m:
        return ''
    tall = 3 if (fmt or '').lower() == 'pdf417' else 1
    quiet = 2 if tall == 1 else 2
    w = max(len(r) for r in m) + 2 * quiet
    h = len(m) * tall + 2 * quiet
    parts = []
    for y, row in enumerate(m):
        x = 0
        while x < len(row):
            if row[x]:
                s = x
                while x < len(row) and row[x]:
                    x += 1
                parts.append('M%d %dh%dv%dh-%dz' % (s + quiet,
                                                    y * tall + quiet,
                                                    x - s, tall, x - s))
            else:
                x += 1
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'shape-rendering="crispEdges" role="img" aria-label="%s">'
            '<rect width="%d" height="%d" fill="#fff"/>'
            '<path d="%s" fill="#000"/></svg>'
            % (w, h, label.replace('"', ''), w, h, ''.join(parts)))


def bcbp(text, year=None):
    """What a flight boarding pass's own code says (IATA Resolution 792,
    mandatory items of the first leg). {} when it is not a BCBP."""
    t = text or ''
    if len(t) < 58 or not t.startswith('M'):
        return {}
    name = t[2:22].strip()
    last, _, first = name.partition('/')
    out = {
        'name': ('%s %s' % (first.strip(), last.strip())).strip().title(),
        'pnr': t[23:30].strip(),
        'from': t[30:33].strip(),
        'to': t[33:36].strip(),
        'carrier': t[36:39].strip(),
        'flight': t[39:44].strip().lstrip('0'),
        'cabin': t[47:48].strip(),
        'seat': t[48:52].strip().lstrip('0'),
        'seq': t[52:57].strip().lstrip('0'),
    }
    jd = t[44:47].strip()
    if jd.isdigit() and 1 <= int(jd) <= 366:
        y = year or dt.date.today().year
        try:
            out['date'] = dt.date(y, 1, 1) + dt.timedelta(days=int(jd) - 1)
        except ValueError:
            pass
    if not re.match(r'^[A-Z]{3}$', out['from'] or '') or \
            not re.match(r'^[A-Z]{3}$', out['to'] or ''):
        return {}
    return out
