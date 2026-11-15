# -*- coding: utf-8 -*-
"""travel/inbound.py - TR-2, 15 Nov 2026. Taking an email apart.

Cloudflare Email Routing hands every message sent to the trips address to
a small Worker, which posts the raw message here (see
cloudflare/travel-email-worker.js). Nothing in this file talks to Claude:
it reads the MIME, decides WHO forwarded it, whether Cloudflare could
confirm that sender, and pulls out what Claude will read - the text, any
structured booking data the airline or hotel put in it, and the
attachments worth keeping.

Standard library only: the email package and html.parser.
"""
import email
import email.policy
import email.utils
import hashlib
import io
import json
import re
import zipfile
from html.parser import HTMLParser

MAX_RAW = 26 * 1024 * 1024          # Cloudflare Email Routing takes 25 MiB
KEEP_TYPES = ('application/pdf', 'image/jpeg', 'image/png', 'image/gif',
              'image/webp', 'application/vnd.apple.pkpass')
MAX_FILE = 15 * 1024 * 1024
SMALL_IMAGE = 15 * 1024             # logos and spacers, not tickets
ADDR = re.compile(r'[A-Za-z0-9._%+\'=-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def parse(raw):
    return email.message_from_bytes(raw, policy=email.policy.default)


def message_id(msg, raw):
    mid = (msg.get('Message-ID') or '').strip().strip('<>')
    if not mid:
        mid = 'sha256:' + hashlib.sha256(raw).hexdigest()
    if len(mid) > 190:
        mid = 'sha256:' + hashlib.sha256(mid.encode()).hexdigest()
    return mid


def sent_at(msg):
    try:
        d = email.utils.parsedate_to_datetime(msg.get('Date'))
    except (TypeError, ValueError, IndexError):
        return None
    if d is not None and d.tzinfo is None:
        import datetime as dt
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def plain(addr):
    """x+caf_=trips=alivente.online@gmail.com -> x@gmail.com.

    Gmail's automatic forwarding sends from the forwarding person's own
    address with a +caf_ tag; a forwarding rule elsewhere may rewrite the
    sender in SRS form (SRS0=hash=tt=domain=local@relay). Both are undone
    so the address compares with the one the person gave."""
    a = (addr or '').strip().strip('<>').lower()
    m = re.match(r'srs[01][=+-][^=]*=[^=]*=([^=]+)=([^@]+)@', a)
    if m:
        a = '%s@%s' % (m.group(2), m.group(1))
    if '@' not in a:
        return ''
    local, dom = a.rsplit('@', 1)
    return '%s@%s' % (local.split('+', 1)[0], dom)


def candidates(msg, envelope_from=''):
    """Addresses that may be the person who forwarded it, best first: the
    envelope sender (who actually sent it to us), what forwarding headers
    say, then the From line - which, for a forward typed by hand, is the
    person themselves."""
    out = []

    def add(v):
        for a in ADDR.findall(v or ''):
            p = plain(a)
            if p and p not in out:
                out.append(p)
    add(envelope_from)
    for h in ('X-Forwarded-For', 'X-Forwarded-From', 'Resent-From',
              'Resent-Sender', 'From', 'Sender', 'Return-Path'):
        for v in msg.get_all(h, []) or []:
            add(str(v))
    return out


def auth_results(msg):
    """Cloudflare's verdicts on the sender, as one lower-case string. Only
    headers Cloudflare itself wrote count (mx.cloudflare.net): anything
    else in the message came from whoever sent it."""
    got = []
    for h in ('ARC-Authentication-Results', 'Authentication-Results'):
        for v in msg.get_all(h, []) or []:
            s = ' '.join(str(v).split()).lower()
            if 'mx.cloudflare.net' in s:
                got.append(s)
    return ' '.join(got)


def trusted(msg, address):
    """Did Cloudflare confirm mail from this address's domain? SPF for the
    envelope sender, a DKIM signature by the domain, or DMARC for From."""
    if not address or '@' not in address:
        return False
    dom = address.rsplit('@', 1)[1]
    a = auth_results(msg)
    if not a:
        return False
    pats = [r'spf=pass[^;]*smtp\.mailfrom=[^;\s]*@?%s\b' % re.escape(dom),
            r'dkim=pass[^;]*header\.d=%s\b' % re.escape(dom),
            r'dmarc=pass[^;]*header\.from=%s\b' % re.escape(dom)]
    return any(re.search(p, a) for p in pats)


class _Text(HTMLParser):
    SKIP = {'script', 'style', 'head', 'title'}
    BLOCK = {'p', 'div', 'br', 'tr', 'li', 'h1', 'h2', 'h3', 'h4', 'h5',
             'h6', 'table', 'section', 'td'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.links = [], 0, []
        self.ld, self._ld = [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and (a.get('type') or '').lower() == \
                'application/ld+json':
            self._ld = []
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BLOCK:
            self.out.append('\n')
        if tag == 'a' and a.get('href', '').startswith('http'):
            self.links.append(a['href'])
        # Microdata (Ryanair, some hotels): itemprop + content
        if a.get('itemprop') and a.get('content'):
            self.out.append(' [%s: %s] ' % (a['itemprop'], a['content']))

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        if tag == 'script' and self._ld is not None:
            self.ld.append(''.join(self._ld))
            self._ld = None
        if tag in ('td', 'th'):
            self.out.append(' ')

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
            return
        if not self.skip:
            self.out.append(data)


def html_text(html):
    p = _Text()
    try:
        p.feed(html)
        p.close()
    except Exception:                                   # noqa: BLE001
        pass
    text = ''.join(p.out)
    text = re.sub(r'[ \t\r\f\v\u00a0]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    return text.strip(), p.ld, p.links


def pkpass(data):
    """An Apple Wallet pass: pass.json holds the barcode text and what the
    pass shows. Returned as plain text for Claude, and the barcode."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        j = json.loads(z.read('pass.json').decode('utf-8', 'replace'))
    except Exception:                                   # noqa: BLE001
        return '', None
    codes = j.get('barcodes') or ([j['barcode']] if j.get('barcode') else [])
    code = None
    if codes:
        c = codes[0]
        fmt = (c.get('format') or '').replace('PKBarcodeFormat', '').lower()
        code = {'text': c.get('message') or '', 'format': fmt}
    lines = []
    for sect in ('boardingPass', 'eventTicket', 'generic'):
        s = j.get(sect) or {}
        for k in ('headerFields', 'primaryFields', 'secondaryFields',
                  'auxiliaryFields'):
            for f in s.get(k) or []:
                lines.append('%s: %s' % (f.get('label') or f.get('key'),
                                         f.get('value')))
    return '\n'.join(lines), code


def pass_from_ld(blocks):
    """A boarding pass in the email's JSON-LD (Cyprus Airways sends one):
    FlightReservation.ticketToken 'aztecCode:M1...' or 'qrCode:...'."""
    for b in blocks:
        try:
            j = json.loads(b)
        except ValueError:
            continue
        for item in (j if isinstance(j, list) else [j]):
            if not isinstance(item, dict):
                continue
            tok = item.get('ticketToken') or ''
            if isinstance(tok, str) and ':' in tok:
                fmt, text = tok.split(':', 1)
                fmt = fmt.lower().replace('code', '').replace('barcode', '')
                fmt = {'aztec': 'aztec', 'qr': 'qr', 'pdf417': 'pdf417',
                       'barcode128': 'code128'}.get(fmt, fmt)
                return {'text': text, 'format': fmt}
    return None


def wallet_links(links):
    """The airline's own "Add to Google Wallet" link: Google's save URL,
    or the airline's (Cyprus Airways: ...get-document?...type=googleWallet)."""
    return [u for u in links if 'pay.google.com/gp/v/save' in u or
            re.search(r'(?i)google[-_]?wallet', u)]


def read(raw):
    """Everything the next steps need from one raw email."""
    msg = parse(raw)
    text, html, ld, links, files, extra = '', '', [], [], [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disp = (part.get_content_disposition() or '').lower()
        name = part.get_filename() or ''
        if ctype == 'message/rfc822':
            continue
        try:
            payload = part.get_payload(decode=True) or b''
        except Exception:                               # noqa: BLE001
            payload = b''
        if ctype == 'text/plain' and disp != 'attachment' and not text:
            text = part.get_content() if hasattr(part, 'get_content') else \
                payload.decode('utf-8', 'replace')
            continue
        if ctype == 'text/html' and disp != 'attachment' and not html:
            try:
                html = part.get_content()
            except Exception:                           # noqa: BLE001
                html = payload.decode('utf-8', 'replace')
            continue
        if name.lower().endswith('.pkpass'):
            ctype = 'application/vnd.apple.pkpass'
        if ctype not in KEEP_TYPES or not payload or len(payload) > MAX_FILE:
            continue
        if ctype.startswith('image/') and (len(payload) < SMALL_IMAGE or
                                           (disp != 'attachment' and
                                            part.get('Content-ID'))):
            continue
        if not name:
            name = 'attachment.' + ctype.split('/')[-1]
        files.append({'name': name[-160:], 'type': ctype, 'data': payload})
    html_plain = ''
    if html:
        html_plain, ld, links = html_text(html)
    body = html_plain if len(html_plain) > len(text or '') else (text or '')
    # PICTURES ONLY WHEN THE PICTURE IS THE BOOKING. A confirmation with a
    # PDF ticket or a page of text carries banner images (Cyprus Airways
    # attaches header-larnaca-EN.png); a screenshot forwarded with a line
    # of text is the booking itself.
    if any(not f['type'].startswith('image/') for f in files) or \
            len(body.strip()) > 400:
        files = [f for f in files if not f['type'].startswith('image/')]
    code = pass_from_ld(ld)
    for f in files:
        if f['type'] == 'application/vnd.apple.pkpass':
            t, c = pkpass(f['data'])
            if t:
                extra.append('Apple Wallet pass %s:\n%s' % (f['name'], t))
            code = code or c
    return {
        'msg': msg,
        'subject': str(msg.get('Subject') or '')[:255],
        'from': str(msg.get('From') or '')[:190],
        'date': sent_at(msg),
        'body': body[:60000],
        'ld': [b[:20000] for b in ld[:6]],
        'files': files,
        'extra': extra,
        'pass': code,
        'wallet': wallet_links(links)[:1],
    }


GMAIL_FROM = 'forwarding-noreply@google.com'


def gmail_confirmation(msg, body):
    """Gmail asks the trips address to confirm automatic forwarding before
    it will forward anything. That email names the Gmail address asking,
    a confirmation code and a link - shown to that person in Travel so
    they can finish the set-up."""
    frm = plain(email.utils.parseaddr(str(msg.get('From') or ''))[1])
    if frm != GMAIL_FROM:
        return None
    subject = str(msg.get('Subject') or '')
    code = re.search(r'#(\d{6,12})', subject) or \
        re.search(r'(?i)confirmation code:\s*(\d{6,12})', body or '')
    who = None
    m = re.search(r'(?i)from\s+(\S+@\S+)\s*$', subject.strip())
    if m:
        who = plain(m.group(1).strip('.,;:()'))
    if not who:
        found = [plain(a) for a in ADDR.findall(body or '')]
        found = [a for a in found if not a.endswith('alivente.online') and
                 a != GMAIL_FROM]
        who = found[0] if found else None
    link = re.search(r'https://mail(?:-settings)?\.google\.com/mail/\S+',
                     body or '')
    return {'who': who, 'code': code.group(1) if code else '',
            'link': link.group(0).rstrip('.,)>') if link else ''}
