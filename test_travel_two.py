# -*- coding: utf-8 -*-
"""test_travel_two.py - round TR-2, 15 Nov 2026.

RELEASE 83 - TRAVEL, STAGE 2: BOOKINGS READ FROM FORWARDED EMAILS.
Demetri, 15 Nov: emails forwarded from his, his wife's and daughters'
mailboxes to the trips address (Cloudflare); "if two or three mails are
received for one booking with changes, it needs to take the details of the
latest email ... have a place where somebody can click to view changes";
"An owner should be asked before merging ... or before somebody joins
their trip."
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_travel2'
ME = 'test_travel_two.py'
PATCHER = 'apply_travel_two.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)






print(__doc__.strip().splitlines()[0])
TA = J(ROOT, 'travel')
TT = J(TA, 'templates', 'travel')
# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
u = read(J(TA, 'urls.py'))
ok("path('inbound/', views_inbox.inbound_view, name='inbound')" in u and
   "path('check/', views_inbox.check, name='check')" in u and
   "name='forwarding'" in u and "name='trip_merge'" in u,
   'routes: the email door, To check, Forwarding, Merge')
mw = read(J(ROOT, 'pages', 'middleware.py'))
ok("'travel/inbound/'," in mw and "'travel/'," not in mw,
   'the middleware lets the email door through - that one path only')
vi = read(J(TA, 'views_inbox.py'))
ok("hmac.compare_digest(key.encode(), given.encode())" in vi and
   "os.environ.get('TRAVEL_INBOUND_KEY', '')" in vi and '@csrf_exempt' in vi,
   'the door checks a shared key from the environment, never a typed one')
ex = read(J(TA, 'extract.py'))
ok("MODEL = os.environ.get('TRAVEL_AI_MODEL', 'claude-sonnet-4-6')" in ex,
   'Claude reads the email: one model constant, from the environment')
ok("'travel/extract.py'" in read(J(ROOT, 'test_ai_models.py')),
   '  and the Anthropic census in test_ai_models knows the new call site')
ix = read(J(TA, 'inbox.py'))
ok('forget_raw(e)' in ix and ix.count('forget_raw(e)') >= 2,
   'the email itself is deleted once read (it can hold a PIN)')
ok(os.path.isfile(J(TA, 'migrations', '0002_email_reading.py')),
   'migration travel 0002')
for name in ('check', 'forwarding', 'merge', '_requests'):
    ok(os.path.isfile(J(TT, name + '.html')), 'template %s.html' % name)
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('data-tab-slug="tr-email"' in hp and 'data-tab-slug="tr-join"' in hp and
   'never deleted' in hp and 'The owner is always asked first' in hp,
   'HELP: an Emails tab and a Joining & Merging tab')

# ==========================================================================
head('2. TAKING AN EMAIL APART - no database')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import base64                                               # noqa: E402
import io                                                   # noqa: E402
import json                                                 # noqa: E402
import zipfile                                              # noqa: E402
from email.message import EmailMessage                      # noqa: E402
from travel import extract as EX, inbound as IN             # noqa: E402

ok(IN.plain('Demetri+caf_=trips=alivente.online@Gmail.com') ==
   'demetri@gmail.com', 'Gmail\'s automatic forward: +caf_ tag undone')
ok(IN.plain('SRS0=Ab12=XY=gmail.com=angy@relay.example') == 'angy@gmail.com',
   'a rewritten (SRS) sender undone')
ARC = ('i=1; mx.cloudflare.net; dkim=pass header.d=gmail.com header.s=x; '
       'dmarc=pass header.from=gmail.com; spf=pass (mx.cloudflare.net: '
       'domain of tva@gmail.com designates 1.2.3.4) '
       'smtp.mailfrom=tva+caf_=trips=alivente.online@gmail.com')


def mail(subject, frm='tva@gmail.com', date='Mon, 01 Jul 2030 09:00:00 +0000',
         mid=None, html=None, text='See below.', arc=True, files=(),
         extra=None):
    m = EmailMessage()
    m['Subject'] = subject
    m['From'] = frm
    m['To'] = 'trips@alivente.online'
    m['Date'] = date
    m['Message-ID'] = '<%s@test>' % (mid or subject.replace(' ', '-'))
    if arc:
        m['ARC-Authentication-Results'] = ARC
    for k, v in (extra or {}).items():
        m[k] = v
    m.set_content(text)
    if html:
        m.add_alternative(html, subtype='html')
    for name, ctype, data in files:
        mt, st = ctype.split('/')
        m.add_attachment(data, maintype=mt, subtype=st, filename=name)
    return m.as_bytes()


msg = IN.parse(mail('x'))
ok(IN.trusted(msg, 'tva@gmail.com'), 'TRUSTED: Cloudflare\'s SPF/DKIM pass '
   'for the sender\'s domain')
ok(not IN.trusted(IN.parse(mail('x', arc=False)), 'tva@gmail.com'),
   '  no Cloudflare verdict, not trusted')
fake = IN.parse(mail('x', arc=False, extra={
    'Authentication-Results': 'evil.example; dkim=pass header.d=gmail.com'}))
ok(not IN.trusted(fake, 'tva@gmail.com'),
   '  and a verdict the SENDER wrote counts for nothing')
html = ('<html><head><script type="application/ld+json">{"@type":'
        '"FlightReservation","reservationNumber":"ABC123","ticketToken":'
        '"aztecCode:M1TEST/PASSENGER EABC123 LCAATHCY 0326"}</script></head>'
        '<body><p>Your flight</p><span itemprop="checkinTime" '
        'content="2030-07-03T15:00"></span><a href="https://pay.google.com/'
        'gp/v/save/abc">Add to Google Wallet</a></body></html>')
info = IN.read(mail('Boarding pass', html=html))
ok(info['pass'] == {'text': 'M1TEST/PASSENGER EABC123 LCAATHCY 0326',
                    'format': 'aztec'},
   'BOARDING PASS: the barcode text read from the email\'s JSON-LD',
   info['pass'])
ok('[checkinTime: 2030-07-03T15:00]' in info['body'] and info['ld'] and
   info['wallet'] == ['https://pay.google.com/gp/v/save/abc'],
   '  microdata kept for Claude, and the Google Wallet link found')
zb = io.BytesIO()
with zipfile.ZipFile(zb, 'w') as z:
    z.writestr('pass.json', json.dumps({'barcodes': [{
        'format': 'PKBarcodeFormatAztec', 'message': 'M1PK'}],
        'boardingPass': {'primaryFields': [{'label': 'FROM',
                                            'value': 'LCA'}]}}))
info = IN.read(mail('pk', files=[('pass.pkpass', 'application/octet-stream',
                                  zb.getvalue()),
                                 ('logo.png', 'image/png', b'x' * 100)]))
ok(info['pass'] == {'text': 'M1PK', 'format': 'aztec'} and
   'FROM: LCA' in info['extra'][0] and
   [f['name'] for f in info['files']] == ['pass.pkpass'],
   'an Apple Wallet pass read; a tiny logo image not kept', info['files'])
gm = IN.gmail_confirmation(IN.parse(mail(
    '(#123456789) Gmail Forwarding Confirmation - Receive Mail from '
    'tvb@gmail.com', frm='Gmail Team <forwarding-noreply@google.com>')),
    'tvb@gmail.com has requested to automatically forward mail.\n'
    'Confirmation code: 123456789\n'
    'https://mail-settings.google.com/mail/vf-%5Babc%5D-xyz\n')
ok(gm == {'who': 'tvb@gmail.com', 'code': '123456789',
          'link': 'https://mail-settings.google.com/mail/vf-%5Babc%5D-xyz'},
   'GMAIL asks to confirm forwarding: the address, code and link', gm)
c = EX.clean({'bookings': [{
    'kind': 'stay', 'title': 'Hotel', 'reference': 'R 1',
    'start_date': '2030-07-03T00:00', 'start_time': '3:05 pm',
    'link': 'http://x.example', 'amount': '100.456', 'currency': 'eur',
    'details': 'PIN: 9876\nPaid with Visa ending 4242\nCard 4111 1111 1111 '
               '1111\nE-ticket 0482412345678\nmail me at a@b.com',
    'travellers': ['DEMETRI MANIAS'], 'kind2': 'x'}, 'nonsense']})[0]
ok(c['reference'] == 'R1' and c['start_date'] == '2030-07-03' and
   c['start_time'] == '03:05' and c['link'] == '' and
   c['amount'] == '100.46' and c['currency'] == 'EUR',
   'CLEAN: dates, times, money made exact; only an https link kept', c)
ok('9876' not in c['details'] and '4242' not in c['details'] and
   '4111' not in c['details'] and '@' not in c['details'] and
   '0482412345678' in c['details'],
   'NEVER KEPT: a PIN, card digits, an email address - an e-ticket number '
   'is kept', c['details'])

# ==========================================================================
head('3. DRIVEN - forwarded, read, routed')
# ==========================================================================
from decimal import Decimal                                 # noqa: E402
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import UserProfile
    from travel.models import (Booking, BookingChange, BookingFile,
                               CheckItem, InboundEmail, JoinRequest,
                               TravelAddress, Trip)
    connection.ensure_connection()
    CheckItem.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])


class Block(object):
    def __init__(self, data):
        self.type = 'tool_use'
        self.input = data


class Reply(object):
    def __init__(self, data):
        self.content = [Block(data)]


class FakeClaude(object):
    """Answers by the email's subject; records what it was sent."""
    def __init__(self):
        self.answers = {}
        self.sent = []
        self.messages = self

    def create(self, **kw):
        self.sent.append(kw)
        text = kw['messages'][0]['content'][0]['text']
        subj = text.split('\n', 1)[0].replace('Subject: ', '')
        a = self.answers.get(subj)
        if isinstance(a, Exception):
            raise a
        return Reply(a or {'is_travel': False, 'bookings': []})


def flight(seg, day, time, amount=None, ref='ABC123', status='confirmed',
           bp=False, who=('TVA ONE', 'Maria Papa')):
    d = {'kind': 'flight', 'title': 'Cyprus Airways ' + seg,
         'provider': 'Cyprus Airways', 'reference': ref, 'segment': seg,
         'status': status, 'boarding_pass': bp, 'start_date': day,
         'start_time': time, 'from_place': 'Larnaca (LCA)',
         'to_place': 'Athens (ATH)', 'city': 'Athens', 'country': 'Greece',
         'travellers': list(who)}
    if amount:
        d.update(amount=amount, currency='EUR', paid='paid')
    return d


# TR-14, 17 Nov 2026 (Demetri: "Please stub those out"): a test never
# looks anything up on the web for real. Opening a trip with a hotel looks
# up the hotel's missing details, and adding a place looks the place up -
# both paid Claude calls with web search on a machine with the Anthropic
# key. A suite that wants one stubs it again below, over these.
try:
    from travel import places as _no_web

    def _no_web_call(*_a, **_k):
        raise _no_web.LookupError_('no web look-ups in tests')
    _no_web.call_details = _no_web_call
    _no_web.call = _no_web_call
except Exception:                                             # noqa: BLE001
    pass

if have_db:
    import tempfile
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    _dj.MEDIA_ROOT = tempfile.mkdtemp(prefix='tv2-')
    from pages.workspace import ensure_workspace
    import travel.fx as FX
    import travel.inbox as IB
    FX.fetch = lambda day, cur: {'GBP': Decimal('0.80')}.get(cur)
    IB.SYNC = True
    AI = FakeClaude()
    _real_call = EX.call
    EX.call = lambda info, client=None: _real_call(info, client=AI)

    class Rollback(Exception):
        pass
    saved_key = os.environ.pop('TRAVEL_INBOUND_KEY', None)
    try:
        with transaction.atomic():
            p, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            us = {}
            for n, first, last in (('tva', 'Tva', 'One'),
                                   ('tvb', 'Tvb', 'Two'),
                                   ('tvc', 'Tvc', 'Three'),
                                   ('tvd', 'Tvd', 'Four')):
                usr = User.objects.create_user(n, n + '@gmail.com', 'x',
                                               first_name=first,
                                               last_name=last)
                if n != 'tvd':
                    usr.user_permissions.add(p)
                us[n] = usr
            ws = ensure_workspace(us['tva'])
            cl = {}
            for n, usr in us.items():
                UserProfile.objects.update_or_create(
                    user=usr, defaults={'workspace': ws})
                c = Client(SERVER_NAME='localhost')
                c.force_login(usr)
                cl[n] = c
            A, B, C = cl['tva'], cl['tvb'], cl['tvc']
            anon = Client(SERVER_NAME='localhost')

            def post(raw, key='k-test', env_from='tva+caf_=trips=alivente.'
                     'online@gmail.com'):
                return anon.post('/travel/inbound/', data=raw,
                                 content_type='message/rfc822',
                                 HTTP_X_TRAVEL_KEY=key,
                                 HTTP_X_ENVELOPE_FROM=env_from)

            raw1 = mail('CY booking', html='<p>Booking ABC123</p>',
                        files=[('eticket.pdf', 'application/pdf',
                                b'%PDF-1.4 ticket' * 2000)])
            r = post(raw1)
            ok(r.status_code == 503, 'THE DOOR: shut until the server has '
               'its key', r.status_code)
            os.environ['TRAVEL_INBOUND_KEY'] = 'k-test'
            ok(post(raw1, key='wrong').status_code == 401 and
               anon.get('/travel/inbound/').status_code == 405,
               '  a wrong key is refused, and nothing answers a GET')
            ok(anon.get('/travel/check/').status_code == 302,
               '  every other Travel page still wants a login')

            r = post(mail('Spam', frm='someone@else.example'),
                     env_from='someone@else.example')
            e = InboundEmail.objects.get(subject='Spam')
            ok(r.status_code == 200 and e.state == 'ignored' and not e.raw
               and not CheckItem.objects.filter(email=e).exists(),
               'UNKNOWN SENDER: ignored, and nothing of it kept')

            AI.answers['CY booking'] = {'is_travel': True, 'bookings': [
                flight('CY 326', '2030-07-03', '06:40', amount='420'),
                flight('CY 327', '2030-07-10', '21:15')]}
            r = post(raw1)
            e1 = InboundEmail.objects.get(subject='CY booking')
            items = list(CheckItem.objects.filter(email=e1).order_by('id'))
            ok(r.status_code == 200 and e1.state == 'done' and e1.trusted
               and e1.user == us['tva'],
               'FORWARDED by A (Gmail\'s +caf_ sender): read, trusted, A\'s',
               (r.status_code, e1.state, e1.trusted, e1.user))
            ok(len(items) == 2 and all(i.what == 'new' and i.trip is None
                                       for i in items),
               '  two flights on one reference: two new bookings to check')
            ok(not e1.raw, '  and the email itself is gone once read')
            sent = AI.sent[-1]
            blocks = sent['messages'][0]['content']
            ok(sent['tool_choice'] == {'type': 'tool',
                                       'name': 'record_bookings'} and
               blocks[1]['type'] == 'document' and
               base64.b64decode(blocks[1]['source']['data']).startswith(
                   b'%PDF'), 'Claude was sent the text and the PDF ticket')
            n = len(AI.sent)
            r = post(raw1)
            ok(json.loads(r.content)['duplicate'] and len(AI.sent) == n and
               CheckItem.objects.filter(email=e1).count() == 2,
               'THE SAME EMAIL AGAIN: taken once, not read twice')

            h = A.get('/travel/').content.decode()
            ok('data-to-check' in h and 'tv-count">2<' in h,
               'TRAVEL shows To check with 2 waiting')
            h = A.get('/travel/check/').content.decode()
            ok(h.count('data-check-item') == 2 and 'Athens Jul 2030' in h,
               'TO CHECK: both, with a new trip named for the place and month')
            A.post('/travel/check/%d/add/' % items[0].pk,
                   {'trip': 'new', 'name': 'Athens Jul 2030'})
            t = Trip.objects.get(name='Athens Jul 2030', owner=us['tva'])
            A.post('/travel/check/%d/add/' % items[1].pk, {'trip': t.pk})
            bs = list(t.bookings.order_by('start_date'))
            out, back = bs
            ok(len(bs) == 2 and out.segment == 'CY 326' and
               out.amount_eur == Decimal('420.00') and back.amount is None and
               out.source == 'email' and out.added_by == us['tva'],
               'ADDED: both flights on the trip, the price on the first')
            ok(out.files.get().name == 'eticket.pdf' and
               back.files.get().file.name == out.files.get().file.name,
               '  the e-ticket on both - one stored file')
            ok(list(out.travellers.all()) == [us['tva']] and
               out.traveller_names == 'Maria Papa',
               'WHO\'S TRAVELLING: A matched by name, Maria kept as written',
               (list(out.travellers.all()), out.traveller_names))
            h = A.get('/travel/booking/%d/' % out.pk).content.decode()
            ok('data-who' in h and 'Tva One, Maria Papa' in h and
               'from an email' in h, '  shown on the booking')

            # ---- a later email: the latest wins
            AI.answers['CY change'] = {'is_travel': True, 'bookings': [
                flight('CY 326', '2030-07-03', '07:10', status='changed')]}
            post(mail('CY change', date='Tue, 02 Jul 2030 09:00:00 +0000'))
            out.refresh_from_db()
            ch = out.changes.first()
            it = CheckItem.objects.get(email__subject='CY change')
            ok(out.start_time.strftime('%H:%M') == '07:10' and
               ch.source == 'email' and
               {'label': 'Start time', 'old': '06:40', 'new': '07:10'} in
               ch.changes and it.state == 'done' and
               it.note == 'Updated: Start time',
               'A CHANGE: same reference and flight - updated by itself, '
               'and the trail says what', (out.start_time, ch.changes,
                                           it.note))
            ok(back.start_time.strftime('%H:%M') == '21:15',
               '  the other flight on the reference untouched')
            AI.answers['CY old'] = {'is_travel': True, 'bookings': [
                flight('CY 326', '2030-07-03', '05:00')]}
            post(mail('CY old', date='Sun, 30 Jun 2030 09:00:00 +0000'))
            out.refresh_from_db()
            ok(out.start_time.strftime('%H:%M') == '07:10' and
               out.changes.first().note.startswith('An older email'),
               'AN OLDER EMAIL arriving late changes nothing')

            # ---- boarding pass
            AI.answers['CY boarding'] = {'is_travel': True, 'bookings': [
                flight('CY 326', '2030-07-03', '07:10', bp=True)]}
            post(mail('CY boarding', html=html,
                      date='Wed, 03 Jul 2030 03:00:00 +0000',
                      files=[('boardingpass.pdf', 'application/pdf',
                              b'%PDF-1.4 bp' * 2000)]))
            out.refresh_from_db()
            ok(out.pass_code.startswith('M1TEST') and
               out.pass_format == 'aztec' and
               out.wallet_link.startswith('https://pay.google.com') and
               set(out.files.values_list('name', flat=True)) ==
               {'eticket.pdf', 'boardingpass.pdf'},
               'BOARDING PASS attaches to its flight - barcode, Wallet link, '
               'the PDF')
            h = A.get('/travel/booking/%d/' % out.pk).content.decode()
            ok('data-boarding-pass' in h and 'Add to Google Wallet' in h,
               '  and the booking shows it')

            # ---- cancellation
            AI.answers['CY cancel'] = {'is_travel': True, 'bookings': [
                flight('CY 327', '2030-07-10', '21:15', status='cancelled')]}
            post(mail('CY cancel', date='Thu, 04 Jul 2030 09:00:00 +0000'))
            back.refresh_from_db()
            ok(back.status == 'cancelled' and
               Booking.objects.filter(pk=back.pk).exists(),
               'A CANCELLATION marks it Cancelled - not deleted')
            h = A.get('/travel/%d/' % t.pk).content.decode()
            ok('tv-off' in h and 'Cancelled' in h, '  struck through on the '
               'trip')

            # ---- not confirmed: waits
            AI.answers['CY spoof'] = {'is_travel': True, 'bookings': [
                flight('CY 326', '2030-07-03', '23:59')]}
            post(mail('CY spoof', arc=False,
                      date='Fri, 05 Jul 2030 09:00:00 +0000'))
            out.refresh_from_db()
            it = CheckItem.objects.get(email__subject='CY spoof')
            ok(out.start_time.strftime('%H:%M') == '07:10' and
               it.what == 'update' and it.state == 'open',
               'SENDER NOT CONFIRMED: the update waits in To check')
            A.post('/travel/check/%d/merge/' % it.pk)
            out.refresh_from_db()
            ok(out.start_time.strftime('%H:%M') == '23:59',
               '  and is applied when A says so')

            # ---- no reference, same day, same place
            A.post('/travel/%d/booking/new/' % t.pk, {
                'kind': 'stay', 'title': 'Hotel Parea', 'currency': 'EUR',
                'start_date': '2030-07-03', 'end_date': '2030-07-10',
                'to_place': 'Athens'})
            AI.answers['Parea'] = {'is_travel': True, 'bookings': [{
                'kind': 'stay', 'title': 'PAREA Athens', 'start_date':
                '2030-07-03', 'end_date': '2030-07-10', 'amount': '400',
                'currency': 'GBP', 'paid': 'due', 'city': 'Athens'}]}
            post(mail('Parea'))
            it = CheckItem.objects.get(email__subject='Parea')
            ok(it.what == 'maybe' and it.booking.title == 'Hotel Parea',
               'NO REFERENCE but the same day, kind and place: "Merge or '
               'keep both?"')
            A.post('/travel/check/%d/merge/' % it.pk)
            hb = Booking.objects.get(pk=it.booking.pk)
            ok(hb.title == 'PAREA Athens' and hb.currency == 'GBP' and
               hb.amount_eur == Decimal('500.00') and
               t.bookings.filter(kind='stay').count() == 1,
               '  merged: one booking, £400 = €500 at the email\'s day',
               (hb.title, hb.amount_eur))

            # ---- forwarding addresses
            r = B.post('/travel/forwarding/', {'email': 'tva@gmail.com'})
            ok(not TravelAddress.objects.exists(),
               'FORWARDING: nobody can add another person\'s login email')
            B.post('/travel/forwarding/', {'email': 'B.Work@Example.com'})
            ok(TravelAddress.objects.get().email == 'b.work@example.com',
               '  B adds a second address of her own')

            # ---- B's email for A's trip: ask to join
            AI.answers['B hotel'] = {'is_travel': True, 'bookings': [{
                'kind': 'stay', 'title': 'Athens Suites', 'reference': 'H9',
                'start_date': '2030-07-04', 'end_date': '2030-07-06',
                'city': 'Athens', 'country': 'Greece', 'amount': '90',
                'currency': 'EUR', 'travellers': ['Tvb Two']}]}
            post(mail('B hotel', frm='b.work@example.com'),
                 env_from='b.work@example.com')
            it = CheckItem.objects.get(email__subject='B hotel')
            ok(it.user == us['tvb'] and it.what == 'join' and
               it.other_trip == t,
               'B FORWARDS from her added address: it belongs with A\'s '
               'trip, which is not shared with her - "Ask to join"')
            ok(B.get('/travel/%d/' % t.pk).status_code == 404,
               '  and she still cannot open A\'s trip')
            B.post('/travel/check/%d/ask/' % it.pk)
            jr = JoinRequest.objects.get(item=it)
            it.refresh_from_db()
            ok(jr.state == 'open' and jr.asks == us['tva'] and
               it.state == 'asked' and not t.shared_with.exists() and
               B.get('/travel/%d/' % t.pk).status_code == 404,
               'THE OWNER IS ASKED: nothing moves until A answers')
            h = A.get('/travel/').content.decode()
            ok('data-join-request' in h and 'Share the trip and add it' in h,
               '  A sees the request on Travel')
            ok(C.post('/travel/request/%d/' % jr.pk,
                      {'answer': 'yes'}).status_code == 404,
               '  nobody else can answer it')
            A.post('/travel/request/%d/' % jr.pk, {'answer': 'yes'})
            it.refresh_from_db()
            nb = t.bookings.get(title='Athens Suites')
            ok(t.shared_with.filter(pk=us['tvb'].pk).exists() and
               nb.added_by == us['tvb'] and it.state == 'done' and
               list(nb.travellers.all()) == [us['tvb']],
               'A SAYS YES: the trip is shared with B, her booking on it, '
               'added by her')

            AI.answers['C hotel'] = {'is_travel': True, 'bookings': [{
                'kind': 'activity', 'title': 'Acropolis tour',
                'reference': 'H9X', 'start_date': '2030-07-05',
                'city': 'Athens'}]}
            post(mail('C hotel', frm='tvc@gmail.com'),
                 env_from='tvc@gmail.com')
            it = CheckItem.objects.get(email__subject='C hotel')
            C.post('/travel/check/%d/ask/' % it.pk)
            jr = JoinRequest.objects.get(item=it)
            A.post('/travel/request/%d/' % jr.pk, {'answer': 'no'})
            it.refresh_from_db()
            ok(it.state == 'open' and it.what == 'new' and
               'kept the trip' in it.note and
               not t.shared_with.filter(pk=us['tvc'].pk).exists(),
               'A SAYS NO: C keeps it to add to a trip of her own')

            # ---- merge trips
            y = Trip.objects.create(owner=us['tva'], name='Athens extra')
            Booking.objects.create(trip=y, title='Dup flight', kind='flight',
                                   reference='ABC123', segment='CY 326',
                                   added_by=us['tva'])
            Booking.objects.create(trip=y, title='Ferry', kind='ferry',
                                   added_by=us['tva'])
            h = A.get('/travel/%d/merge/?from=%d' % (t.pk, y.pk)).content \
                .decode()
            ok('data-merge-preview' in h and 'becomes one' in h and
               'moves across' in h,
               'MERGE: a preview - what moves, what is already there')
            ok(B.get('/travel/%d/merge/' % t.pk).status_code == 404,
               '  only the owner merges into a trip')
            A.post('/travel/%d/merge/' % t.pk, {'from': y.pk})
            ok(not Trip.objects.filter(pk=y.pk).exists() and
               t.bookings.filter(title='Ferry').exists() and
               t.bookings.filter(reference='ABC123',
                                 segment='CY 326').count() == 1,
               '  merged: the ferry moved, the same flight became one')
            z = Trip.objects.create(owner=us['tvb'], name='B Crete')
            z.shared_with.add(us['tva'])
            Booking.objects.create(trip=z, title='Crete car', kind='car',
                                   added_by=us['tvb'])
            A.post('/travel/%d/merge/' % t.pk, {'from': z.pk})
            jr = JoinRequest.objects.get(from_trip=z)
            ok(Trip.objects.filter(pk=z.pk).exists() and jr.asks ==
               us['tvb'], 'SOMEONE ELSE\'S TRIP: its owner is asked first')
            B.post('/travel/request/%d/' % jr.pk, {'answer': 'yes'})
            cc = t.bookings.get(title='Crete car')
            ok(not Trip.objects.filter(pk=z.pk).exists() and
               cc.added_by == us['tvb'],
               '  B says yes: merged, and who added it is kept')

            # ---- Gmail confirmation, failure, nothing in it
            post(mail('(#555666777) Gmail Forwarding Confirmation - Receive '
                      'Mail from b.work@example.com',
                      frm='forwarding-noreply@google.com',
                      text='b.work@example.com has requested to '
                           'automatically forward mail to your email '
                           'address trips@alivente.online.\nConfirmation '
                           'code: 555666777\nhttps://mail-settings.google.'
                           'com/mail/vf-%5Bx%5D-y\n'),
                 env_from='forwarding-noreply@google.com')
            gi = CheckItem.objects.get(what='gmail')
            h = B.get('/travel/forwarding/').content.decode()
            ok(gi.user == us['tvb'] and '555666777' in h and
               'Confirm in Gmail' in h,
               'GMAIL\'S CONFIRMATION reaches the person who set it up, with '
               'the code')
            AI.answers['Broken'] = RuntimeError('overloaded')
            for k in range(3):
                if k == 0:
                    post(mail('Broken'))
                else:
                    IB.process_pending()
            e = InboundEmail.objects.get(subject='Broken')
            ok(e.state == 'failed' and e.tries == 3 and not e.raw and
               CheckItem.objects.filter(email=e, what='failed').exists(),
               'CLAUDE UNREACHABLE: tried three times, then "could not be '
               'read" in To check', (e.state, e.tries))
            post(mail('Newsletter'))
            ok(CheckItem.objects.get(email__subject='Newsletter').what ==
               'none', 'AN EMAIL WITH NO BOOKING says so')

            # ---- shared files survive one booking's deletion
            fname = out.files.get(name='eticket.pdf').file.name
            back_files = back.files.count()
            A.post('/travel/booking/%d/delete/' % back.pk)
            ok(back_files == 1 and
               out.files.filter(name='eticket.pdf').exists() and
               out.files.get(name='eticket.pdf').file.storage.exists(fname),
               'DELETING one flight keeps the e-ticket its partner shares')

            # ---- totals leave cancelled out
            from travel.views import totals
            cx = Booking(trip=t, title='x', amount=Decimal('1000'),
                         amount_eur=Decimal('1000'), status='cancelled')
            ok(totals([cx])['total'] == '€0',
               'A CANCELLED booking is out of the costs')
            raise Rollback
    except Rollback:
        pass
    finally:
        EX.call = _real_call
        IB.SYNC = False
        if saved_key is None:
            os.environ.pop('TRAVEL_INBOUND_KEY', None)
        else:
            os.environ['TRAVEL_INBOUND_KEY'] = saved_key

# ==========================================================================
head('4. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok("'travel/inbound/'," not in was(J(ROOT, 'pages', 'middleware.py')),
       'before this round: no email door')
except IOError as _e:
    skip('control', str(_e))
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
